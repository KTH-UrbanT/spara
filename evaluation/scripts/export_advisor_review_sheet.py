import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_PATH = REPO_ROOT / "evaluation" / "results" / "eval_results.jsonl"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "evaluation" / "results" / "advisor_reviews.csv"


CSV_HEADERS = [
    "system_variant",
    "case_id",
    "turn_index",
    "message_id",
    "expected_route",
    "actual_route",
    "actual_agent",
    "expected_answer",
    "must_include",
    "must_not_include",
    "answer_expectation_status",
    "missing_required_terms",
    "forbidden_terms_present",
    "grounding_status",
    "unsupported_claim_rate",
    "citation_coverage",
    "unsupported_claim_count",
    "safety_status",
    "safety_risk_category",
    "safety_action",
    "safety_handled_safely",
    "safety_requires_review",
    "safety_redirect_to",
    "assistant_content",
    "route_correct",
    "building_data_correct",
    "recommendation_correct",
    "personalized",
    "useful",
    "too_generic",
    "needs_minor_edit",
    "needs_major_edit",
    "unsafe_or_misleading",
    "should_have_asked_clarification",
    "should_have_escalated",
    "technical_correctness_score",
    "building_specificity_score",
    "personalization_score",
    "usefulness_score",
    "justification_score",
    "clarity_score",
    "trust_score",
    "safety_score",
    "advisor_confidence",
    "error_tags",
    "correction_actions",
    "corrected_answer",
    "correction_summary",
    "comments",
]


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an advisor review CSV from eval results.")
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    rows = _load_jsonl(args.results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "case_id": row.get("case_id"),
                    "system_variant": row.get("system_variant") or "full",
                    "turn_index": row.get("turn_index"),
                    "message_id": row.get("message_id"),
                    "expected_route": row.get("expected_route"),
                    "actual_route": row.get("actual_route"),
                    "actual_agent": row.get("actual_agent"),
                    "expected_answer": row.get("expected_answer"),
                    "must_include": json.dumps(row.get("must_include") or [], ensure_ascii=False),
                    "must_not_include": json.dumps(row.get("must_not_include") or [], ensure_ascii=False),
                    "answer_expectation_status": row.get("answer_expectation_status"),
                    "missing_required_terms": json.dumps(row.get("missing_required_terms") or [], ensure_ascii=False),
                    "forbidden_terms_present": json.dumps(row.get("forbidden_terms_present") or [], ensure_ascii=False),
                    "grounding_status": row.get("grounding_status"),
                    "unsupported_claim_rate": row.get("unsupported_claim_rate"),
                    "citation_coverage": row.get("citation_coverage"),
                    "unsupported_claim_count": row.get("unsupported_claim_count"),
                    "safety_status": row.get("safety_status"),
                    "safety_risk_category": row.get("safety_risk_category"),
                    "safety_action": row.get("safety_action"),
                    "safety_handled_safely": row.get("safety_handled_safely"),
                    "safety_requires_review": row.get("safety_requires_review"),
                    "safety_redirect_to": row.get("safety_redirect_to"),
                    "assistant_content": row.get("assistant_content"),
                }
            )
    print(f"Wrote advisor review sheet to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
