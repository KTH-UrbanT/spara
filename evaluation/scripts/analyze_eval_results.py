import argparse
import csv
import json
import math
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


def _percentile(values: Iterable[float], percentile: float) -> float | None:
    collected = sorted(value for value in values if value is not None)
    if not collected:
        return None
    if len(collected) == 1:
        return round(collected[0], 4)

    rank = (len(collected) - 1) * percentile
    lower_index = math.floor(rank)
    upper_index = math.ceil(rank)
    if lower_index == upper_index:
        return round(collected[lower_index], 4)

    lower_value = collected[lower_index]
    upper_value = collected[upper_index]
    weighted = lower_value + (upper_value - lower_value) * (rank - lower_index)
    return round(weighted, 4)


def _score_from_review(review: Dict[str, Any], key: str) -> float | None:
    raw = review.get(key)
    if raw in (None, ""):
        return None
    return float(raw)


def _float_from_result(row: Dict[str, Any], key: str) -> float | None:
    raw = row.get(key)
    if raw in (None, ""):
        return None
    return float(raw)


def _grounding_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    grounding = row.get("grounding")
    if isinstance(grounding, dict):
        return grounding
    metadata = row.get("metadata") or {}
    if isinstance(metadata, dict) and isinstance(metadata.get("grounding"), dict):
        return metadata["grounding"]
    return {}


def _safety_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    safety_boundary = row.get("safety_boundary")
    if isinstance(safety_boundary, dict):
        return safety_boundary
    metadata = row.get("metadata") or {}
    if isinstance(metadata, dict) and isinstance(metadata.get("safety_boundary"), dict):
        return metadata["safety_boundary"]
    return {}


def _float_from_grounding(row: Dict[str, Any], key: str) -> float | None:
    raw = _grounding_payload(row).get(key)
    if raw in (None, ""):
        return None
    return float(raw)


def _int_from_grounding(row: Dict[str, Any], key: str) -> int:
    raw = _grounding_payload(row).get(key)
    if raw in (None, ""):
        return 0
    return int(raw)


def _build_confusion_matrix(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    matrix: Dict[str, Dict[str, int]] = {}
    for row in results:
        expected = row.get("expected_route")
        actual = row.get("actual_route") or "error"
        if not expected:
            continue
        matrix.setdefault(expected, {})
        matrix[expected][actual] = matrix[expected].get(actual, 0) + 1
    return matrix


def _count_by_key(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = row.get(key) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return counts


def _load_error_tags(review: Dict[str, Any]) -> List[str]:
    raw = review.get("error_tags")
    if raw in (None, ""):
        return []
    if isinstance(raw, list):
        return [str(tag) for tag in raw if tag]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return [raw]
        if isinstance(parsed, list):
            return [str(tag) for tag in parsed if tag]
    return []


def _load_json_list_field(review: Dict[str, Any], key: str) -> List[Any]:
    raw = review.get(key)
    if raw in (None, ""):
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _build_route_class_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    labelled = [row for row in results if row.get("expected_route")]
    labels = sorted(
        {
            str(row.get("expected_route"))
            for row in labelled
            if row.get("expected_route")
        }
        | {
            str(row.get("actual_route"))
            for row in labelled
            if row.get("actual_route")
        }
    )
    class_metrics: Dict[str, Dict[str, float | int | None]] = {}
    f1_values = []

    for label in labels:
        tp = sum(
            1
            for row in labelled
            if row.get("expected_route") == label and row.get("actual_route") == label
        )
        fp = sum(
            1
            for row in labelled
            if row.get("expected_route") != label and row.get("actual_route") == label
        )
        fn = sum(
            1
            for row in labelled
            if row.get("expected_route") == label and row.get("actual_route") != label
        )
        support = sum(1 for row in labelled if row.get("expected_route") == label)
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        if support == 0:
            f1 = None
        else:
            precision_for_f1 = precision if precision is not None else 0.0
            recall_for_f1 = recall if recall is not None else 0.0
            if precision_for_f1 + recall_for_f1 == 0:
                f1 = 0.0
            else:
                f1 = round(
                    (2 * precision_for_f1 * recall_for_f1)
                    / (precision_for_f1 + recall_for_f1),
                    4,
                )
            f1_values.append(f1)
        class_metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

    return {
        "route_class_metrics": class_metrics,
        "route_macro_f1": _average(f1_values),
    }


def _build_summary_payload(results: List[Dict[str, Any]], reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
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
    answer_checked_rows = [
        row
        for row in results
        if row.get("answer_expectation_status") in {"passed", "needs_review"}
    ]
    answer_passed_rows = [
        row
        for row in answer_checked_rows
        if row.get("answer_expectation_status") == "passed"
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
    failed_results = [
        row
        for row in results
        if row.get("failed") is True or row.get("error")
    ]
    latencies = [
        value
        for value in (_float_from_result(row, "latency_seconds") for row in results)
        if value is not None
    ]
    grounding_rows = [
        row
        for row in results
        if _grounding_payload(row).get("status") not in (None, "", "not_applicable")
    ]
    grounded_claim_rows = [
        row
        for row in grounding_rows
        if _int_from_grounding(row, "claim_count") > 0
    ]
    grounding_review_rows = [
        row
        for row in grounding_rows
        if _grounding_payload(row).get("requires_review") is True
        or _grounding_payload(row).get("status") == "needs_review"
    ]
    unsupported_claim_count = sum(
        _int_from_grounding(row, "unsupported_claim_count")
        for row in grounding_rows
    )
    safety_rows = [
        row
        for row in results
        if _safety_payload(row).get("status") not in (None, "", "not_applicable")
    ]
    safety_review_rows = [
        row
        for row in safety_rows
        if _safety_payload(row).get("requires_review") is True
        or _safety_payload(row).get("status") == "needs_review"
    ]
    detected_risk_rows = [
        row
        for row in safety_rows
        if _safety_payload(row).get("detected_risk") is True
    ]
    safely_handled_rows = [
        row
        for row in detected_risk_rows
        if _safety_payload(row).get("handled_safely") is True
    ]
    error_tag_counts: Dict[str, int] = {}
    for review in reviews:
        for tag in _load_error_tags(review):
            error_tag_counts[tag] = error_tag_counts.get(tag, 0) + 1
    correction_action_counts: Dict[str, int] = {}
    correction_review_count = 0
    for review in reviews:
        actions = _load_json_list_field(review, "correction_actions")
        if actions or review.get("corrected_answer") or review.get("correction_summary"):
            correction_review_count += 1
        for action in actions:
            if isinstance(action, dict):
                action_type = str(action.get("type") or action.get("action") or "unspecified")
            else:
                action_type = str(action or "unspecified")
            correction_action_counts[action_type] = correction_action_counts.get(action_type, 0) + 1

    route_metrics = _build_route_class_metrics(results)
    return {
        "total_turns": len(results),
        "total_cases_with_expected_route": len(routed),
        "route_accuracy": _safe_div(len(route_matches), len(routed)),
        "route_macro_f1": route_metrics["route_macro_f1"],
        "route_class_metrics": route_metrics["route_class_metrics"],
        "route_confusion_matrix": _build_confusion_matrix(results),
        "turns_by_case_type": _count_by_key(results, "case_type"),
        "building_identification_accuracy": _safe_div(len(building_matches), len(building_cases)),
        "field_accuracy": _safe_div(field_found, field_expected),
        "clarification_accuracy": _safe_div(len(clarification_matches), len(clarification_cases)),
        "out_of_scope_accuracy": _safe_div(len(out_of_scope_matches), len(out_of_scope_cases)),
        "answer_expectation_accuracy": _safe_div(len(answer_passed_rows), len(answer_checked_rows)),
        "answer_expectation_checked_count": len(answer_checked_rows),
        "answer_expectation_review_count": len(answer_checked_rows) - len(answer_passed_rows),
        "failure_rate": _safe_div(len(failed_results), len(results)),
        "failure_count": len(failed_results),
        "average_latency_seconds": _average(latencies),
        "median_latency_seconds": _percentile(latencies, 0.5),
        "p95_latency_seconds": _percentile(latencies, 0.95),
        "grounding_evaluated_turns": len(grounding_rows),
        "grounding_claim_turns": len(grounded_claim_rows),
        "grounding_review_rate": _safe_div(len(grounding_review_rows), len(grounding_rows)),
        "unsupported_claim_count": unsupported_claim_count,
        "average_support_ratio": _average(
            _float_from_grounding(row, "support_ratio") for row in grounded_claim_rows
        ),
        "average_unsupported_claim_rate": _average(
            _float_from_grounding(row, "unsupported_claim_rate") for row in grounded_claim_rows
        ),
        "average_citation_coverage": _average(
            _float_from_grounding(row, "citation_coverage") for row in grounded_claim_rows
        ),
        "safety_evaluated_turns": len(safety_rows),
        "safety_detected_risk_turns": len(detected_risk_rows),
        "safety_review_rate": _safe_div(len(safety_review_rows), len(safety_rows)),
        "boundary_handled_safely_rate": _safe_div(len(safely_handled_rows), len(detected_risk_rows)),
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
        "advisor_error_tag_counts": error_tag_counts,
        "advisor_correction_review_count": correction_review_count,
        "advisor_correction_action_counts": correction_action_counts,
    }


def _variant_for_row(row: Dict[str, Any]) -> str:
    return str(row.get("system_variant") or "full")


def build_summary(results: List[Dict[str, Any]], reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = _build_summary_payload(results, reviews)
    variants = sorted({_variant_for_row(row) for row in results})
    if not variants:
        return summary

    by_variant = {}
    comparison = []
    for variant in variants:
        variant_results = [row for row in results if _variant_for_row(row) == variant]
        variant_reviews = [
            review
            for review in reviews
            if str(review.get("system_variant") or "full") == variant
        ]
        variant_summary = _build_summary_payload(variant_results, variant_reviews)
        by_variant[variant] = variant_summary
        comparison.append(
            {
                "system_variant": variant,
                "total_turns": variant_summary.get("total_turns"),
                "route_accuracy": variant_summary.get("route_accuracy"),
                "route_macro_f1": variant_summary.get("route_macro_f1"),
                "building_identification_accuracy": variant_summary.get("building_identification_accuracy"),
                "field_accuracy": variant_summary.get("field_accuracy"),
                "clarification_accuracy": variant_summary.get("clarification_accuracy"),
                "out_of_scope_accuracy": variant_summary.get("out_of_scope_accuracy"),
                "answer_expectation_accuracy": variant_summary.get("answer_expectation_accuracy"),
                "answer_expectation_review_count": variant_summary.get("answer_expectation_review_count"),
                "failure_rate": variant_summary.get("failure_rate"),
                "grounding_review_rate": variant_summary.get("grounding_review_rate"),
                "average_unsupported_claim_rate": variant_summary.get("average_unsupported_claim_rate"),
                "average_citation_coverage": variant_summary.get("average_citation_coverage"),
                "safety_review_rate": variant_summary.get("safety_review_rate"),
                "boundary_handled_safely_rate": variant_summary.get("boundary_handled_safely_rate"),
                "median_latency_seconds": variant_summary.get("median_latency_seconds"),
                "p95_latency_seconds": variant_summary.get("p95_latency_seconds"),
            }
        )

    summary["by_variant"] = by_variant
    summary["variant_comparison"] = comparison
    return summary


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
