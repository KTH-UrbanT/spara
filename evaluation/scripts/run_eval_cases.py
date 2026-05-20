import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
LLM_SERVICE_ROOT = REPO_ROOT / "llm-service"
SCRIPTS_ROOT = Path(__file__).resolve().parent
DEFAULT_CASES_PATH = REPO_ROOT / "evaluation" / "data" / "evaluation_cases.jsonl"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "evaluation" / "results" / "eval_results.jsonl"

if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from evaluation_variants import (  # noqa: E402
    AVAILABLE_VARIANTS,
    build_variant_router,
    parse_variants,
    variant_runtime_context,
)


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _coerce_list(value: Any) -> List[str]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [part.strip() for part in value.split("|") if part.strip()]
    return [str(value).strip()]


def _turn_value(case: Dict[str, Any], turn: Dict[str, Any], key: str, default: Any = None) -> Any:
    if key in turn:
        return turn.get(key)
    return case.get(key, default)


def _answer_expectation(
    answer_text: str | None,
    *,
    must_include: List[str],
    must_not_include: List[str],
) -> Dict[str, Any]:
    answer_folded = str(answer_text or "").lower()
    missing_required_terms = [
        term for term in must_include if term.lower() not in answer_folded
    ]
    forbidden_terms_present = [
        term for term in must_not_include if term.lower() in answer_folded
    ]

    if not must_include and not must_not_include:
        status = "not_checked"
    elif missing_required_terms or forbidden_terms_present:
        status = "needs_review"
    else:
        status = "passed"

    return {
        "status": status,
        "missing_required_terms": missing_required_terms,
        "forbidden_terms_present": forbidden_terms_present,
    }


def _build_turns(case: Dict[str, Any]) -> List[Dict[str, Any]]:
    turns = case.get("turns")
    if isinstance(turns, list) and turns:
        return turns
    return [
        {
            "user": case["question"],
            "expected_route": case.get("expected_route"),
            "expected_behavior": case.get("expected_behavior"),
            "expected_answer": case.get("expected_answer"),
            "expected_fields": case.get("expected_fields") or [],
            "expected_building_id": case.get("expected_building_id"),
            "expected_building_info": case.get("expected_building_info") or {},
            "must_include": case.get("must_include") or [],
            "must_not_include": case.get("must_not_include") or [],
        }
    ]


def _seed_metadata(case: Dict[str, Any]) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {
        "case_id": case.get("case_id"),
    }
    nested_metadata = case.get("metadata")
    if isinstance(nested_metadata, dict):
        metadata.update(nested_metadata)
    if case.get("brf_name"):
        metadata["brf_name"] = case["brf_name"]
    if case.get("address"):
        metadata["address"] = case["address"]
        metadata["address_from_user"] = case["address"]
    if case.get("city"):
        metadata["city"] = case["city"]
    for key in ("building_id", "byggnadsid", "50a_uuid", "01a_fnr"):
        if case.get(key) not in (None, "", [], {}):
            metadata[key] = case[key]
    return metadata


def _filter_cases(
    cases: List[Dict[str, Any]],
    *,
    case_id: str | None,
    route: str | None,
    limit: int | None,
) -> List[Dict[str, Any]]:
    filtered = []
    for case in cases:
        if case_id and case.get("case_id") != case_id:
            continue
        if route and case.get("expected_route") != route:
            continue
        filtered.append(case)
        if limit is not None and len(filtered) >= limit:
            break
    return filtered


def _import_runtime():
    if str(LLM_SERVICE_ROOT) not in sys.path:
        sys.path.insert(0, str(LLM_SERVICE_ROOT))

    from src.pipeline.agent_router import AgentRouter  # pylint: disable=import-error
    from src.pipeline.evaluation_metadata import (  # pylint: disable=import-error
        build_message_evidence,
        build_message_metadata,
    )
    from src.pipeline.telemetry import telemetry_context, telemetry_snapshot  # pylint: disable=import-error

    return AgentRouter, build_message_metadata, build_message_evidence, telemetry_context, telemetry_snapshot


def _run_case(
    *,
    router,
    system_variant: str,
    case: Dict[str, Any],
    run_id: str,
    build_message_metadata,
    build_message_evidence,
    telemetry_context,
    telemetry_snapshot,
) -> List[Dict[str, Any]]:
    case_results = []
    thread_id = f"eval-{case['case_id'].lower()}-{uuid.uuid4().hex[:8]}"
    session_metadata = _seed_metadata(case)
    messages: List[Dict[str, Any]] = []

    for turn_index, turn in enumerate(_build_turns(case)):
        user_message = turn["user"]
        expected_answer = _turn_value(case, turn, "expected_answer")
        expected_building_info = _turn_value(case, turn, "expected_building_info", {})
        must_include = _coerce_list(_turn_value(case, turn, "must_include", []))
        must_not_include = _coerce_list(_turn_value(case, turn, "must_not_include", []))
        user_payload = {"role": "user", "content": user_message}
        messages.append(user_payload)
        turn_started = time.perf_counter()

        try:
            with telemetry_context("evaluation_turn"):
                response, session_metadata = router.route_message(
                    messages,
                    user_message,
                    session_metadata,
                    thread_id,
                )
                session_metadata = {
                    **(session_metadata or {}),
                    "last_user_message": user_message,
                    "telemetry": telemetry_snapshot(),
                }
            assistant_metadata = build_message_metadata(response, session_metadata)
            evidence = build_message_evidence(assistant_metadata)
            grounding = assistant_metadata.get("grounding") or {}
            safety_boundary = assistant_metadata.get("safety_boundary") or {}
            assistant_payload = {
                **response,
                "role": "assistant",
                "metadata": assistant_metadata,
                "evidence": evidence,
            }
            answer_expectation = _answer_expectation(
                assistant_payload.get("content"),
                must_include=must_include,
                must_not_include=must_not_include,
            )
            messages.append(assistant_payload)
            case_results.append(
                {
                    "run_id": run_id,
                    "system_variant": system_variant,
                    "case_id": case["case_id"],
                    "case_type": case.get("case_type"),
                    "thread_id": thread_id,
                    "turn_index": turn_index,
                    "user_message": user_message,
                    "expected_route": turn.get("expected_route", case.get("expected_route")),
                    "expected_behavior": turn.get("expected_behavior", case.get("expected_behavior")),
                    "expected_answer": expected_answer,
                    "expected_building_info": expected_building_info if isinstance(expected_building_info, dict) else {},
                    "must_include": must_include,
                    "must_not_include": must_not_include,
                    "answer_expectation": answer_expectation,
                    "answer_expectation_status": answer_expectation.get("status"),
                    "missing_required_terms": answer_expectation.get("missing_required_terms") or [],
                    "forbidden_terms_present": answer_expectation.get("forbidden_terms_present") or [],
                    "expected_building_id": turn.get(
                        "expected_building_id",
                        case.get("expected_building_id"),
                    ),
                    "expected_fields": turn.get("expected_fields", case.get("expected_fields") or []),
                    "actual_route": assistant_metadata.get("route"),
                    "actual_agent": assistant_metadata.get("agent"),
                    "classification": assistant_payload.get("classification"),
                    "assistant_content": assistant_payload.get("content"),
                    "retrieved_building_id": assistant_metadata.get("building_id"),
                    "retrieved_facts": assistant_metadata.get("retrieved_facts") or {},
                    "grounding": grounding,
                    "grounding_status": grounding.get("status"),
                    "unsupported_claim_rate": grounding.get("unsupported_claim_rate"),
                    "citation_coverage": grounding.get("citation_coverage"),
                    "unsupported_claim_count": grounding.get("unsupported_claim_count"),
                    "safety_boundary": safety_boundary,
                    "safety_status": safety_boundary.get("status"),
                    "safety_risk_category": safety_boundary.get("risk_category"),
                    "safety_action": safety_boundary.get("action"),
                    "safety_handled_safely": safety_boundary.get("handled_safely"),
                    "safety_requires_review": safety_boundary.get("requires_review"),
                    "safety_redirect_to": safety_boundary.get("redirect_to"),
                    "sources": assistant_payload.get("sources") or [],
                    "metadata": assistant_metadata,
                    "evidence": evidence,
                    "latency_seconds": round(time.perf_counter() - turn_started, 4),
                    "failed": False,
                }
            )
        except Exception as exc:  # pragma: no cover - best-effort runner
            case_results.append(
                {
                    "run_id": run_id,
                    "system_variant": system_variant,
                    "case_id": case["case_id"],
                    "case_type": case.get("case_type"),
                    "thread_id": thread_id,
                    "turn_index": turn_index,
                    "user_message": user_message,
                    "expected_route": turn.get("expected_route", case.get("expected_route")),
                    "expected_behavior": turn.get("expected_behavior", case.get("expected_behavior")),
                    "expected_answer": expected_answer,
                    "expected_building_info": expected_building_info if isinstance(expected_building_info, dict) else {},
                    "must_include": must_include,
                    "must_not_include": must_not_include,
                    "answer_expectation_status": "not_checked",
                    "missing_required_terms": [],
                    "forbidden_terms_present": [],
                    "actual_route": None,
                    "actual_agent": None,
                    "assistant_content": None,
                    "error": str(exc),
                    "metadata": {},
                    "evidence": [],
                    "latency_seconds": round(time.perf_counter() - turn_started, 4),
                    "failed": True,
                }
            )

    return case_results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run evaluation cases through SPARA AgentRouter.")
    parser.add_argument("--input", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--case-id")
    parser.add_argument("--route")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--evaluation-mode", action="store_true")
    parser.add_argument(
        "--variant",
        action="append",
        dest="variants",
        help="Evaluation variant to run. Can be repeated or comma-separated. Defaults to full.",
    )
    parser.add_argument(
        "--variants",
        action="append",
        dest="variants",
        help="Comma-separated evaluation variants to run. Example: full,llm_only,standard_rag.",
    )
    parser.add_argument(
        "--list-variants",
        action="store_true",
        help="Print supported evaluation variants and exit.",
    )
    args = parser.parse_args()

    if args.list_variants:
        print("\n".join(AVAILABLE_VARIANTS))
        return 0

    try:
        variants = parse_variants(args.variants)
    except ValueError as exc:
        parser.error(str(exc))

    if args.evaluation_mode:
        os.environ["EVALUATION_MODE"] = "true"

    (
        AgentRouter,
        build_message_metadata,
        build_message_evidence,
        telemetry_context,
        telemetry_snapshot,
    ) = _import_runtime()
    cases = _filter_cases(
        _load_jsonl(args.input),
        case_id=args.case_id,
        route=args.route,
        limit=args.limit,
    )

    run_id = f"eval-run-{uuid.uuid4().hex[:12]}"
    results: List[Dict[str, Any]] = []
    for variant in variants:
        with variant_runtime_context(variant):
            router = build_variant_router(variant, AgentRouter)
            for case in cases:
                results.extend(
                    _run_case(
                        router=router,
                        system_variant=variant,
                        case=case,
                        run_id=run_id,
                        build_message_metadata=build_message_metadata,
                        build_message_evidence=build_message_evidence,
                        telemetry_context=telemetry_context,
                        telemetry_snapshot=telemetry_snapshot,
                    )
                )

    _write_jsonl(args.output, results)
    print(f"Wrote {len(results)} turn results across {len(variants)} variant(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
