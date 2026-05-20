import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_PATH = REPO_ROOT / "evaluation" / "results" / "eval_results.jsonl"
DEFAULT_SUMMARY_PATH = REPO_ROOT / "evaluation" / "results" / "metric_summary.json"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "evaluation" / "results" / "benchmark_report.md"


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


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_metric(value: Any, *, percent: bool = False, seconds: bool = False) -> str:
    if value is None:
        return "n/a"
    if percent:
        return f"{float(value) * 100:.1f}%"
    if seconds:
        return f"{float(value):.2f}s"
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return str(value)


def _short_text(value: Any, limit: int = 160) -> str:
    text = str(value or "").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _list_text(value: Any, limit: int = 120) -> str:
    if value in (None, "", []):
        return ""
    if isinstance(value, list):
        text = ", ".join(str(item) for item in value if str(item))
    else:
        text = str(value)
    return _short_text(text, limit)


def _expected_answer_text(row: Dict[str, Any]) -> str:
    return (
        row.get("expected_answer")
        or row.get("expected_behavior")
        or ""
    )


def _answer_expectation_summary(row: Dict[str, Any]) -> str:
    status = row.get("answer_expectation_status") or "not_checked"
    missing = row.get("missing_required_terms") or []
    forbidden = row.get("forbidden_terms_present") or []
    if status == "passed":
        return "passed"
    if status == "needs_review":
        parts = []
        if missing:
            parts.append("missing: " + _list_text(missing))
        if forbidden:
            parts.append("forbidden: " + _list_text(forbidden))
        return "; ".join(parts) or "needs review"
    return "not checked"


def _markdown_table(headers: List[str], rows: Iterable[List[Any]]) -> List[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cleaned = [
            str(value if value is not None else "n/a").replace("|", "\\|")
            for value in row
        ]
        lines.append("| " + " | ".join(cleaned) + " |")
    return lines


def _group_by_case(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in results:
        key = f"{row.get('system_variant') or 'full'}::{row.get('case_id') or 'unknown'}"
        grouped[key].append(row)

    case_rows = []
    for case_id, rows in grouped.items():
        expected_routes = [row.get("expected_route") for row in rows if row.get("expected_route")]
        route_matches = [
            row
            for row in rows
            if row.get("expected_route") and row.get("expected_route") == row.get("actual_route")
        ]
        failed = [row for row in rows if row.get("failed") is True or row.get("error")]
        latencies = [
            float(row["latency_seconds"])
            for row in rows
            if row.get("latency_seconds") not in (None, "")
        ]
        case_rows.append(
            {
                "system_variant": rows[0].get("system_variant") or "full",
                "case_id": rows[0].get("case_id") or "unknown",
                "case_type": rows[0].get("case_type") or "unknown",
                "turns": len(rows),
                "route_accuracy": (
                    len(route_matches) / len(expected_routes)
                    if expected_routes
                    else None
                ),
                "failed_turns": len(failed),
                "avg_latency": sum(latencies) / len(latencies) if latencies else None,
            }
        )

    return sorted(case_rows, key=lambda row: (row["system_variant"], row["case_id"]))


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


def _route_matrix_lines(matrix: Dict[str, Dict[str, int]]) -> List[str]:
    if not matrix:
        return ["No route labels were available."]

    actual_labels = sorted(
        {
            actual
            for actual_counts in matrix.values()
            for actual in actual_counts.keys()
        }
    )
    rows = []
    for expected in sorted(matrix.keys()):
        rows.append(
            [expected, *[matrix[expected].get(actual, 0) for actual in actual_labels]]
        )
    return _markdown_table(["Expected", *actual_labels], rows)


def _scenario_output_rows(results: List[Dict[str, Any]], limit: int = 40) -> List[List[Any]]:
    rows = []
    for row in results:
        if (row.get("system_variant") or "full") != "full":
            continue
        rows.append(
            [
                row.get("case_id"),
                row.get("turn_index"),
                _short_text(row.get("user_message"), 120),
                row.get("expected_route") or "n/a",
                row.get("actual_route") or "error",
                _short_text(_expected_answer_text(row), 180),
                _answer_expectation_summary(row),
                _short_text(row.get("assistant_content") or row.get("error"), 220),
            ]
        )
        if len(rows) >= limit:
            break
    return rows


def build_report(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    run_ids = sorted({row.get("run_id") for row in results if row.get("run_id")})
    route_mismatches = [
        row
        for row in results
        if row.get("expected_route") and row.get("expected_route") != row.get("actual_route")
    ]
    failed_rows = [
        row for row in results if row.get("failed") is True or row.get("error")
    ]
    slowest_rows = sorted(
        [row for row in results if row.get("latency_seconds") not in (None, "")],
        key=lambda row: float(row.get("latency_seconds") or 0),
        reverse=True,
    )[:10]
    grounding_review_rows = [
        row
        for row in results
        if _grounding_payload(row).get("status") == "needs_review"
        or _grounding_payload(row).get("requires_review") is True
    ]
    safety_review_rows = [
        row
        for row in results
        if _safety_payload(row).get("status") == "needs_review"
        or _safety_payload(row).get("requires_review") is True
    ]
    answer_review_rows = [
        row
        for row in results
        if row.get("answer_expectation_status") == "needs_review"
    ]

    lines = [
        "# SPARA Benchmark Report",
        "",
        f"Generated: {generated_at}",
        f"Run id(s): {', '.join(run_ids) if run_ids else 'n/a'}",
        "",
        "## Headline Metrics",
        "",
        *_markdown_table(
            ["Metric", "Value"],
            [
                ["Total turns", summary.get("total_turns")],
                ["Cases with expected route", summary.get("total_cases_with_expected_route")],
                ["Route accuracy", _fmt_metric(summary.get("route_accuracy"), percent=True)],
                ["Route macro-F1", _fmt_metric(summary.get("route_macro_f1"))],
                ["Building identification accuracy", _fmt_metric(summary.get("building_identification_accuracy"), percent=True)],
                ["Field accuracy", _fmt_metric(summary.get("field_accuracy"), percent=True)],
                ["Clarification accuracy", _fmt_metric(summary.get("clarification_accuracy"), percent=True)],
                ["Out-of-scope accuracy", _fmt_metric(summary.get("out_of_scope_accuracy"), percent=True)],
                ["Answer criteria pass rate", _fmt_metric(summary.get("answer_expectation_accuracy"), percent=True)],
                ["Answer criteria review count", summary.get("answer_expectation_review_count")],
                ["Failure rate", _fmt_metric(summary.get("failure_rate"), percent=True)],
                ["Median latency", _fmt_metric(summary.get("median_latency_seconds"), seconds=True)],
                ["P95 latency", _fmt_metric(summary.get("p95_latency_seconds"), seconds=True)],
                ["Grounding review rate", _fmt_metric(summary.get("grounding_review_rate"), percent=True)],
                ["Avg unsupported-claim rate", _fmt_metric(summary.get("average_unsupported_claim_rate"), percent=True)],
                ["Avg citation coverage", _fmt_metric(summary.get("average_citation_coverage"), percent=True)],
                ["Safety review rate", _fmt_metric(summary.get("safety_review_rate"), percent=True)],
                ["Boundary handled safely", _fmt_metric(summary.get("boundary_handled_safely_rate"), percent=True)],
            ],
        ),
        "",
        "## Demo Scenario Outputs",
        "",
    ]

    scenario_rows = _scenario_output_rows(results)
    if scenario_rows:
        lines.extend(
            _markdown_table(
                [
                    "Case",
                    "Turn",
                    "Question",
                    "Expected route",
                    "Actual route",
                    "Expected answer",
                    "Answer check",
                    "SPARA answer",
                ],
                scenario_rows,
            )
        )
    else:
        lines.append("No full-variant scenario outputs available.")

    lines.extend(
        [
            "",
            "## Variant Comparison",
            "",
        ]
    )

    variant_comparison = summary.get("variant_comparison") or []
    if variant_comparison:
        lines.extend(
            _markdown_table(
                [
                    "Variant",
                    "Turns",
                    "Route acc.",
                    "Macro-F1",
                    "Building ID acc.",
                    "Field acc.",
                    "Clarification acc.",
                    "OOS acc.",
                    "Answer criteria",
                    "Answer reviews",
                    "Failure rate",
                    "Grounding review",
                    "Unsupported claims",
                    "Citation coverage",
                    "Safety review",
                    "Boundary safe",
                    "Median latency",
                    "P95 latency",
                ],
                [
                    [
                        row.get("system_variant"),
                        row.get("total_turns"),
                        _fmt_metric(row.get("route_accuracy"), percent=True),
                        _fmt_metric(row.get("route_macro_f1")),
                        _fmt_metric(row.get("building_identification_accuracy"), percent=True),
                        _fmt_metric(row.get("field_accuracy"), percent=True),
                        _fmt_metric(row.get("clarification_accuracy"), percent=True),
                        _fmt_metric(row.get("out_of_scope_accuracy"), percent=True),
                        _fmt_metric(row.get("answer_expectation_accuracy"), percent=True),
                        row.get("answer_expectation_review_count"),
                        _fmt_metric(row.get("failure_rate"), percent=True),
                        _fmt_metric(row.get("grounding_review_rate"), percent=True),
                        _fmt_metric(row.get("average_unsupported_claim_rate"), percent=True),
                        _fmt_metric(row.get("average_citation_coverage"), percent=True),
                        _fmt_metric(row.get("safety_review_rate"), percent=True),
                        _fmt_metric(row.get("boundary_handled_safely_rate"), percent=True),
                        _fmt_metric(row.get("median_latency_seconds"), seconds=True),
                        _fmt_metric(row.get("p95_latency_seconds"), seconds=True),
                    ]
                    for row in variant_comparison
                ],
            )
        )
    else:
        lines.append("No variant comparison available.")

    lines.extend(
        [
            "",
            "## Route Confusion Matrix",
            "",
            *_route_matrix_lines(summary.get("route_confusion_matrix") or {}),
            "",
            "## Case Summary",
            "",
            *_markdown_table(
                ["Variant", "Case", "Type", "Turns", "Route acc.", "Failed turns", "Avg latency"],
                [
                    [
                        row["system_variant"],
                        row["case_id"],
                        row["case_type"],
                        row["turns"],
                        _fmt_metric(row["route_accuracy"], percent=True),
                        row["failed_turns"],
                        _fmt_metric(row["avg_latency"], seconds=True),
                    ]
                    for row in _group_by_case(results)
                ],
            ),
            "",
            "## Route Mismatches",
            "",
        ]
    )

    if route_mismatches:
        lines.extend(
            _markdown_table(
                ["Variant", "Case", "Turn", "Expected", "Actual", "Question"],
                [
                    [
                        row.get("system_variant") or "full",
                        row.get("case_id"),
                        row.get("turn_index"),
                        row.get("expected_route"),
                        row.get("actual_route") or "error",
                        _short_text(row.get("user_message")),
                    ]
                    for row in route_mismatches[:20]
                ],
            )
        )
    else:
        lines.append("No route mismatches found.")

    lines.extend(["", "## Answer Expectation Review", ""])
    if answer_review_rows:
        lines.extend(
            _markdown_table(
                ["Variant", "Case", "Turn", "Question", "Expected answer", "Missing", "Forbidden", "SPARA answer"],
                [
                    [
                        row.get("system_variant") or "full",
                        row.get("case_id"),
                        row.get("turn_index"),
                        _short_text(row.get("user_message"), 140),
                        _short_text(_expected_answer_text(row), 180),
                        _list_text(row.get("missing_required_terms")),
                        _list_text(row.get("forbidden_terms_present")),
                        _short_text(row.get("assistant_content") or row.get("error"), 220),
                    ]
                    for row in answer_review_rows[:20]
                ],
            )
        )
    else:
        lines.append("No answer expectation review flags found.")

    lines.extend(["", "## Failures", ""])
    if failed_rows:
        lines.extend(
            _markdown_table(
                ["Variant", "Case", "Turn", "Latency", "Error"],
                [
                    [
                        row.get("system_variant") or "full",
                        row.get("case_id"),
                        row.get("turn_index"),
                        _fmt_metric(row.get("latency_seconds"), seconds=True),
                        _short_text(row.get("error"), 220),
                    ]
                    for row in failed_rows[:20]
                ],
            )
        )
    else:
        lines.append("No failed turns found.")

    lines.extend(["", "## Grounding Review", ""])
    if grounding_review_rows:
        lines.extend(
            _markdown_table(
                ["Variant", "Case", "Turn", "Unsupported", "Citation cov.", "Unsupported claim"],
                [
                    [
                        row.get("system_variant") or "full",
                        row.get("case_id"),
                        row.get("turn_index"),
                        _fmt_metric(_grounding_payload(row).get("unsupported_claim_rate"), percent=True),
                        _fmt_metric(_grounding_payload(row).get("citation_coverage"), percent=True),
                        _short_text((_grounding_payload(row).get("unsupported_claims") or [""])[0], 220),
                    ]
                    for row in grounding_review_rows[:20]
                ],
            )
        )
    else:
        lines.append("No grounding review flags found.")

    lines.extend(["", "## Safety Boundary Review", ""])
    if safety_review_rows:
        lines.extend(
            _markdown_table(
                ["Variant", "Case", "Turn", "Risk", "Action", "Reason codes", "Question"],
                [
                    [
                        row.get("system_variant") or "full",
                        row.get("case_id"),
                        row.get("turn_index"),
                        _safety_payload(row).get("risk_category"),
                        _safety_payload(row).get("action"),
                        ", ".join(_safety_payload(row).get("reason_codes") or []),
                        _short_text(row.get("user_message"), 220),
                    ]
                    for row in safety_review_rows[:20]
                ],
            )
        )
    else:
        lines.append("No safety boundary review flags found.")

    lines.extend(["", "## Slowest Turns", ""])
    if slowest_rows:
        lines.extend(
            _markdown_table(
                ["Variant", "Case", "Turn", "Latency", "Route", "Question"],
                [
                    [
                        row.get("system_variant") or "full",
                        row.get("case_id"),
                        row.get("turn_index"),
                        _fmt_metric(row.get("latency_seconds"), seconds=True),
                        row.get("actual_route"),
                        _short_text(row.get("user_message")),
                    ]
                    for row in slowest_rows
                ],
            )
        )
    else:
        lines.append("No latency values found.")

    error_tags = summary.get("advisor_error_tag_counts") or {}
    lines.extend(["", "## Advisor Error Tags", ""])
    if error_tags:
        lines.extend(
            _markdown_table(
                ["Tag", "Count"],
                sorted(error_tags.items(), key=lambda item: item[0]),
            )
        )
    else:
        lines.append("No advisor error tags available.")

    correction_actions = summary.get("advisor_correction_action_counts") or {}
    lines.extend(["", "## Advisor Correction Actions", ""])
    if correction_actions:
        lines.extend(
            _markdown_table(
                ["Action", "Count"],
                sorted(correction_actions.items(), key=lambda item: item[0]),
            )
        )
    else:
        lines.append("No advisor correction actions available.")

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- Raw turn results: `evaluation/results/eval_results.jsonl`",
            "- Metric summary: `evaluation/results/metric_summary.json`",
            "- Advisor review sheet: `evaluation/results/advisor_reviews.csv`",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Markdown report for SPARA benchmark runs.")
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    results = _load_jsonl(args.results)
    summary = _load_json(args.summary)
    report = build_report(results, summary)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote benchmark report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
