import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_PATH = REPO_ROOT / "evaluation" / "results" / "eval_results.jsonl"
DEFAULT_REVIEWS_PATH = REPO_ROOT / "evaluation" / "results" / "advisor_reviews.csv"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "evaluation" / "results" / "metric_summary.json"


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


def _load_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _safe_div(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def _average(values: Iterable[float]) -> float | None:
    collected = [value for value in values if value is not None]
    if not collected:
        return None
    return round(sum(collected) / len(collected), 4)


def _score_from_review(review: Dict[str, Any], key: str) -> float | None:
    raw = review.get(key)
    if raw in (None, ""):
        return None
    return float(raw)


def build_summary(results: List[Dict[str, Any]], reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    routed = [row for row in results if row.get("expected_route")]
    route_matches = [row for row in routed if row.get("expected_route") == row.get("actual_route")]

    building_cases = [row for row in results if row.get("expected_building_id")]
    building_matches = [
        row
        for row in building_cases
        if row.get("expected_building_id") == row.get("retrieved_building_id")
    ]

    clarification_cases = [row for row in routed if row.get("expected_route") == "clarification"]
    clarification_matches = [
        row
        for row in clarification_cases
        if row.get("actual_route") == "clarification"
    ]

    out_of_scope_cases = [row for row in routed if row.get("expected_route") == "out_of_scope"]
    out_of_scope_matches = [
        row
        for row in out_of_scope_cases
        if row.get("actual_route") == "out_of_scope"
    ]

    field_expected = 0
    field_found = 0
    for row in results:
        expected_fields = row.get("expected_fields") or []
        retrieved_facts = row.get("retrieved_facts") or {}
        if not isinstance(expected_fields, list) or not isinstance(retrieved_facts, dict):
            continue
        field_expected += len(expected_fields)
        for field_name in expected_fields:
            if field_name in retrieved_facts and retrieved_facts[field_name] not in (None, "", [], {}):
                field_found += 1

    unsafe_reviews = sum(
        1
        for review in reviews
        if str(review.get("unsafe_or_misleading") or "").strip().lower() == "true"
    )
    major_edit_reviews = sum(
        1
        for review in reviews
        if str(review.get("needs_major_edit") or "").strip().lower() == "true"
    )

    return {
        "total_turns": len(results),
        "total_cases_with_expected_route": len(routed),
        "route_accuracy": _safe_div(len(route_matches), len(routed)),
        "building_identification_accuracy": _safe_div(len(building_matches), len(building_cases)),
        "field_accuracy": _safe_div(field_found, field_expected),
        "clarification_accuracy": _safe_div(len(clarification_matches), len(clarification_cases)),
        "out_of_scope_accuracy": _safe_div(len(out_of_scope_matches), len(out_of_scope_cases)),
        "advisor_review_count": len(reviews),
        "advisor_average_usefulness": _average(
            _score_from_review(review, "usefulness_score") for review in reviews
        ),
        "advisor_average_personalization": _average(
            _score_from_review(review, "personalization_score") for review in reviews
        ),
        "advisor_average_confidence": _average(
            _score_from_review(review, "advisor_confidence") for review in reviews
        ),
        "unsafe_or_misleading_count": unsafe_reviews,
        "needs_major_edit_count": major_edit_reviews,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize SPARA evaluation outputs.")
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--reviews", type=Path, default=DEFAULT_REVIEWS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    summary = build_summary(_load_jsonl(args.results), _load_csv(args.reviews))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
