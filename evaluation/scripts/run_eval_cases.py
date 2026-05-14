import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
LLM_SERVICE_ROOT = REPO_ROOT / "llm-service"
DEFAULT_CASES_PATH = REPO_ROOT / "evaluation" / "data" / "evaluation_cases.jsonl"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "evaluation" / "results" / "eval_results.jsonl"


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


def _build_turns(case: Dict[str, Any]) -> List[Dict[str, Any]]:
    turns = case.get("turns")
    if isinstance(turns, list) and turns:
        return turns
    return [
        {
            "user": case["question"],
            "expected_route": case.get("expected_route"),
            "expected_behavior": case.get("expected_behavior"),
            "expected_fields": case.get("expected_fields") or [],
            "expected_building_id": case.get("expected_building_id"),
        }
    ]


def _seed_metadata(case: Dict[str, Any]) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {
        "case_id": case.get("case_id"),
    }
    if case.get("brf_name"):
        metadata["brf_name"] = case["brf_name"]
    if case.get("address"):
        metadata["address"] = case["address"]
        metadata["address_from_user"] = case["address"]
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

    return AgentRouter, build_message_metadata, build_message_evidence


def _run_case(
    *,
    router,
    case: Dict[str, Any],
    run_id: str,
    build_message_metadata,
    build_message_evidence,
) -> List[Dict[str, Any]]:
    case_results = []
    thread_id = f"eval-{case['case_id'].lower()}-{uuid.uuid4().hex[:8]}"
    session_metadata = _seed_metadata(case)
    messages: List[Dict[str, Any]] = []

    for turn_index, turn in enumerate(_build_turns(case)):
        user_message = turn["user"]
        user_payload = {"role": "user", "content": user_message}
        messages.append(user_payload)

        try:
            response, session_metadata = router.route_message(
                messages,
                user_message,
                session_metadata,
                thread_id,
            )
            assistant_metadata = build_message_metadata(response, session_metadata)
            evidence = build_message_evidence(assistant_metadata)
            assistant_payload = {
                **response,
                "role": "assistant",
                "metadata": assistant_metadata,
                "evidence": evidence,
            }
            messages.append(assistant_payload)
            case_results.append(
                {
                    "run_id": run_id,
                    "case_id": case["case_id"],
                    "case_type": case.get("case_type"),
                    "thread_id": thread_id,
                    "turn_index": turn_index,
                    "user_message": user_message,
                    "expected_route": turn.get("expected_route", case.get("expected_route")),
                    "expected_behavior": turn.get("expected_behavior", case.get("expected_behavior")),
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
                    "sources": assistant_payload.get("sources") or [],
                    "metadata": assistant_metadata,
                    "evidence": evidence,
                }
            )
        except Exception as exc:  # pragma: no cover - best-effort runner
            case_results.append(
                {
                    "run_id": run_id,
                    "case_id": case["case_id"],
                    "case_type": case.get("case_type"),
                    "thread_id": thread_id,
                    "turn_index": turn_index,
                    "user_message": user_message,
                    "expected_route": turn.get("expected_route", case.get("expected_route")),
                    "actual_route": None,
                    "actual_agent": None,
                    "assistant_content": None,
                    "error": str(exc),
                    "metadata": {},
                    "evidence": [],
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
    args = parser.parse_args()

    if args.evaluation_mode:
        os.environ["EVALUATION_MODE"] = "true"

    AgentRouter, build_message_metadata, build_message_evidence = _import_runtime()
    router = AgentRouter()
    cases = _filter_cases(
        _load_jsonl(args.input),
        case_id=args.case_id,
        route=args.route,
        limit=args.limit,
    )

    run_id = f"eval-run-{uuid.uuid4().hex[:12]}"
    results: List[Dict[str, Any]] = []
    for case in cases:
        results.extend(
            _run_case(
                router=router,
                case=case,
                run_id=run_id,
                build_message_metadata=build_message_metadata,
                build_message_evidence=build_message_evidence,
            )
        )

    _write_jsonl(args.output, results)
    print(f"Wrote {len(results)} turn results to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
