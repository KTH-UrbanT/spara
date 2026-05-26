import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_PATH = REPO_ROOT / "evaluation" / "results" / "eval_results.jsonl"
DEFAULT_SUMMARY_PATH = REPO_ROOT / "evaluation" / "results" / "metric_summary.json"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "evaluation" / "results" / "cs_paper_analysis.md"

BASELINE_VARIANTS = ("llm_only", "standard_rag", "sql_only")
ABLATION_VARIANTS = (
    "no_router",
    "no_vector",
    "no_sql",
    "no_clarification",
)
PAPER_CORE_VARIANTS = ("full", *BASELINE_VARIANTS, *ABLATION_VARIANTS)


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


def _fmt(value: Any, *, percent: bool = False, seconds: bool = False) -> str:
    if value is None:
        return "n/a"
    if percent:
        return f"{float(value) * 100:.1f}%"
    if seconds:
        return f"{float(value):.2f}s"
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return str(value)


def _short_text(value: Any, limit: int = 120) -> str:
    text = str(value or "").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


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


def _safe_div(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _wilson_interval(successes: int, total: int, z: float = 1.96) -> Tuple[float, float] | None:
    if total == 0:
        return None
    p_hat = successes / total
    denominator = 1 + (z**2 / total)
    center = (p_hat + z**2 / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt((p_hat * (1 - p_hat) / total) + (z**2 / (4 * total**2)))
        / denominator
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def _fmt_ci(successes: int, total: int) -> str:
    interval = _wilson_interval(successes, total)
    if interval is None:
        return "n/a"
    lower, upper = interval
    return f"{successes}/{total} ({successes / total * 100:.1f}%, 95% CI {lower * 100:.1f}-{upper * 100:.1f}%)"


def _variants_from(summary: Dict[str, Any], results: List[Dict[str, Any]]) -> List[str]:
    variants = set()
    variants.update(str(row.get("system_variant") or "full") for row in results)
    variants.update((summary.get("by_variant") or {}).keys())
    variants.update(
        str(row.get("system_variant"))
        for row in summary.get("variant_comparison") or []
        if row.get("system_variant")
    )
    return sorted(variants)


def _route_confusion_pairs(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    pairs = []
    matrix = summary.get("route_confusion_matrix") or {}
    for expected, actual_counts in matrix.items():
        if not isinstance(actual_counts, dict):
            continue
        for actual, count in actual_counts.items():
            if expected == actual:
                continue
            pairs.append(
                {
                    "expected": expected,
                    "actual": actual,
                    "count": int(count),
                }
            )
    return sorted(pairs, key=lambda row: row["count"], reverse=True)


def _result_route_confusion_pairs(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Counter[tuple[str, str]] = Counter()
    for row in results:
        expected = row.get("expected_route")
        actual = row.get("actual_route") or "error"
        if expected and expected != actual:
            counts[(str(expected), str(actual))] += 1
    return [
        {"expected": expected, "actual": actual, "count": count}
        for (expected, actual), count in counts.most_common()
    ]


def _route_class_rows(summary: Dict[str, Any]) -> List[List[Any]]:
    metrics = summary.get("route_class_metrics") or {}
    rows = []
    for label, values in sorted(metrics.items(), key=lambda item: item[0]):
        rows.append(
            [
                label,
                values.get("support"),
                _fmt(values.get("precision"), percent=True),
                _fmt(values.get("recall"), percent=True),
                _fmt(values.get("f1")),
            ]
        )
    return rows


def _case_type_rows(results: List[Dict[str, Any]]) -> List[List[Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in results:
        grouped[str(row.get("case_type") or "unknown")].append(row)

    rows = []
    for case_type, case_rows in sorted(grouped.items(), key=lambda item: item[0]):
        routed = [row for row in case_rows if row.get("expected_route")]
        route_matches = [
            row
            for row in routed
            if row.get("expected_route") == row.get("actual_route")
        ]
        checked = [
            row
            for row in case_rows
            if row.get("answer_expectation_status") in {"passed", "needs_review"}
        ]
        needs_review = [
            row for row in checked if row.get("answer_expectation_status") == "needs_review"
        ]
        latencies = [
            float(row["latency_seconds"])
            for row in case_rows
            if row.get("latency_seconds") not in (None, "")
        ]
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        rows.append(
            [
                case_type,
                len(case_rows),
                _fmt(_safe_div(len(route_matches), len(routed)), percent=True),
                _fmt(_safe_div(len(needs_review), len(checked)), percent=True),
                _fmt(avg_latency, seconds=True),
            ]
        )
    return rows


def _answer_review_rows(results: List[Dict[str, Any]], limit: int = 12) -> List[List[Any]]:
    rows = []
    for row in results:
        if row.get("answer_expectation_status") != "needs_review":
            continue
        missing = ", ".join(str(item) for item in row.get("missing_required_terms") or [])
        forbidden = ", ".join(str(item) for item in row.get("forbidden_terms_present") or [])
        rows.append(
            [
                row.get("case_id"),
                row.get("turn_index"),
                row.get("expected_route"),
                row.get("actual_route") or "error",
                _short_text(row.get("user_message"), 90),
                _short_text(missing or forbidden, 90),
            ]
        )
        if len(rows) >= limit:
            break
    return rows


def _error_taxonomy(summary: Dict[str, Any], results: List[Dict[str, Any]]) -> List[List[Any]]:
    taxonomy: Counter[str] = Counter()

    pairs = (
        _result_route_confusion_pairs(results)
        if results
        else _route_confusion_pairs(summary)
    )
    for pair in pairs:
        expected = pair["expected"]
        actual = pair["actual"]
        count = pair["count"]
        if expected in {"building_specific", "combined"} and actual == "clarification":
            taxonomy["Over-clarification for answerable building-specific query"] += count
        elif expected == "clarification" and actual != "clarification":
            taxonomy["Missed clarification or premature building lookup"] += count
        elif expected in {"building_specific", "combined"} and actual == "generic":
            taxonomy["Lost building-specific route; answered generically"] += count
        elif expected == "generic" and actual == "clarification":
            taxonomy["Over-clarification for generic advisory query"] += count
        else:
            taxonomy[f"Route mismatch: {expected} -> {actual}"] += count

    if results:
        taxonomy["Answer field/content expectation failures"] += sum(
            1 for row in results if row.get("answer_expectation_status") == "needs_review"
        )
        taxonomy["Runtime failures"] += sum(
            1 for row in results if row.get("failed") is True or row.get("error")
        )
        p95 = summary.get("p95_latency_seconds")
        if p95 not in (None, ""):
            taxonomy["Turns at or above p95 latency"] += sum(
                1
                for row in results
                if row.get("latency_seconds") not in (None, "")
                and float(row["latency_seconds"]) >= float(p95)
            )

    return [
        [label, count]
        for label, count in taxonomy.most_common()
        if count > 0
    ]


def _variant_comparison_rows(summary: Dict[str, Any]) -> List[List[Any]]:
    rows = []
    comparison = summary.get("variant_comparison") or []
    by_name = {row.get("system_variant"): row for row in comparison}
    full = by_name.get("full") or {}
    for row in comparison:
        route_delta = None
        answer_delta = None
        latency_delta = None
        if full and row.get("system_variant") != "full":
            if row.get("route_accuracy") is not None and full.get("route_accuracy") is not None:
                route_delta = row["route_accuracy"] - full["route_accuracy"]
            if row.get("answer_expectation_accuracy") is not None and full.get("answer_expectation_accuracy") is not None:
                answer_delta = row["answer_expectation_accuracy"] - full["answer_expectation_accuracy"]
            if row.get("median_latency_seconds") is not None and full.get("median_latency_seconds") is not None:
                latency_delta = row["median_latency_seconds"] - full["median_latency_seconds"]

        rows.append(
            [
                row.get("system_variant"),
                row.get("total_turns"),
                _fmt(row.get("route_accuracy"), percent=True),
                _fmt(route_delta, percent=True) if route_delta is not None else "baseline",
                _fmt(row.get("answer_expectation_accuracy"), percent=True),
                _fmt(answer_delta, percent=True) if answer_delta is not None else "baseline",
                _fmt(row.get("median_latency_seconds"), seconds=True),
                _fmt(latency_delta, seconds=True) if latency_delta is not None else "baseline",
            ]
        )
    return rows


def _readiness_rows(summary: Dict[str, Any], results: List[Dict[str, Any]]) -> List[List[Any]]:
    variants = _variants_from(summary, results)
    missing_baselines = [variant for variant in BASELINE_VARIANTS if variant not in variants]
    missing_ablations = [variant for variant in ABLATION_VARIANTS if variant not in variants]
    route_supports = {
        label: int(values.get("support") or 0)
        for label, values in (summary.get("route_class_metrics") or {}).items()
    }
    low_support = [
        f"{label}={support}"
        for label, support in sorted(route_supports.items())
        if support < 10
    ]

    rows = []
    rows.append(
        [
            "Baselines",
            "ready" if not missing_baselines else "missing",
            ", ".join(variants) or "none",
            "Run " + ", ".join(missing_baselines) if missing_baselines else "Report paired comparisons.",
        ]
    )
    rows.append(
        [
            "Ablations",
            "ready" if not missing_ablations else "missing",
            ", ".join(variants) or "none",
            "Run " + ", ".join(missing_ablations) if missing_ablations else "Report component contribution.",
        ]
    )
    rows.append(
        [
            "Grounding",
            "ready" if int(summary.get("grounding_evaluated_turns") or 0) > 0 else "missing",
            f"{summary.get('grounding_evaluated_turns') or 0} evaluated turns",
            "Add claim/evidence checks for factual and building-specific answers.",
        ]
    )
    rows.append(
        [
            "Advisor review",
            "ready" if int(summary.get("advisor_review_count") or 0) > 0 else "missing",
            f"{summary.get('advisor_review_count') or 0} reviews",
            "Collect blinded expert ratings for correctness, usefulness, trust, and correction severity.",
        ]
    )
    rows.append(
        [
            "Route class support",
            "ready" if not low_support else "thin",
            ", ".join(low_support) if low_support else "all classes >= 10",
            "Increase support for rare classes before making per-class claims.",
        ]
    )
    rows.append(
        [
            "Raw results",
            "ready" if results else "missing",
            f"{len(results)} loaded turns",
            "Keep eval_results.jsonl with the report for reproducible error analysis.",
        ]
    )
    return rows


def _supported_claims(summary: Dict[str, Any], results: List[Dict[str, Any]]) -> List[str]:
    claims = []
    if summary.get("failure_rate") == 0:
        claims.append("The evaluated full system completed the benchmark without runtime failures.")
    if (summary.get("route_accuracy") or 0) >= 0.8:
        claims.append("The full system shows reasonable end-to-end routing accuracy on the current benchmark.")
    generic = (summary.get("route_class_metrics") or {}).get("generic") or {}
    if (generic.get("f1") or 0) >= 0.9:
        claims.append("Generic energy-advisory routing is strong in this run.")
    if (summary.get("out_of_scope_accuracy") or 0) == 1.0:
        claims.append("Out-of-scope handling passed the current small test sample.")
    if (summary.get("clarification_accuracy") or 0) < 0.6:
        claims.append("Clarification and missing-information handling remain a key weakness.")
    if results:
        claims.append("Case-level rows are available for route, answer-expectation, and latency error analysis.")
    return claims


def _unsupported_claims(summary: Dict[str, Any], results: List[Dict[str, Any]]) -> List[str]:
    variants = _variants_from(summary, results)
    claims = []
    if len(variants) <= 1:
        claims.append("Do not claim SPARA outperforms baselines; only one system variant is present.")
    if int(summary.get("grounding_evaluated_turns") or 0) == 0:
        claims.append("Do not claim low hallucination or strong grounding; grounding was not evaluated.")
    if int(summary.get("advisor_review_count") or 0) == 0:
        claims.append("Do not claim advisor trust/usefulness; no advisor reviews are present.")
    if any(
        int(((summary.get("route_class_metrics") or {}).get(label) or {}).get("support") or 0) < 5
        for label in ("out_of_scope", "report_generation", "expert_handoff")
    ):
        claims.append("Do not make strong per-class claims for rare routes with very small support.")
    return claims


def build_analysis(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    total_turns = int(summary.get("total_turns") or len(results) or 0)
    route_total = int(summary.get("total_cases_with_expected_route") or 0)
    route_successes = (
        int(round(float(summary.get("route_accuracy") or 0) * route_total))
        if route_total
        else 0
    )
    answer_total = int(summary.get("answer_expectation_checked_count") or 0)
    answer_successes = (
        int(round(float(summary.get("answer_expectation_accuracy") or 0) * answer_total))
        if answer_total
        else 0
    )

    variants = _variants_from(summary, results)
    missing_core_variants = [variant for variant in PAPER_CORE_VARIANTS if variant not in variants]
    confusion_pairs = (
        _result_route_confusion_pairs(results)
        if results
        else _route_confusion_pairs(summary)
    )

    lines = [
        "# SPARA CS Paper Analysis",
        "",
        f"Generated: {generated_at}",
        "",
        "## Executive Interpretation",
        "",
        (
            "This artifact interprets the benchmark as evidence for a computer-science paper. "
            "It separates current evidence from claims that still require baselines, ablations, "
            "grounding checks, or human review."
        ),
        "",
        *_markdown_table(
            ["Metric", "Paper-useful interpretation"],
            [
                ["Turns", total_turns],
                ["Route accuracy", _fmt_ci(route_successes, route_total) if route_total else "n/a"],
                ["Route macro-F1", _fmt(summary.get("route_macro_f1"))],
                ["Answer expectation pass rate", _fmt_ci(answer_successes, answer_total) if answer_total else "n/a"],
                ["Clarification accuracy", _fmt(summary.get("clarification_accuracy"), percent=True)],
                ["Building identification accuracy", _fmt(summary.get("building_identification_accuracy"), percent=True)],
                ["Field accuracy", _fmt(summary.get("field_accuracy"), percent=True)],
                ["Median / p95 latency", f"{_fmt(summary.get('median_latency_seconds'), seconds=True)} / {_fmt(summary.get('p95_latency_seconds'), seconds=True)}"],
                ["Variants present", ", ".join(variants) or "none"],
                ["Missing for strong CS claim", ", ".join(missing_core_variants) if missing_core_variants else "none"],
            ],
        ),
        "",
        "## Research Readiness",
        "",
        *_markdown_table(["Evidence area", "Status", "Current evidence", "Next action"], _readiness_rows(summary, results)),
        "",
        "## Claims Supported Now",
        "",
        *[f"- {claim}" for claim in _supported_claims(summary, results)],
        "",
        "## Claims Not Yet Supported",
        "",
        *[f"- {claim}" for claim in _unsupported_claims(summary, results)],
        "",
        "## Route Performance By Class",
        "",
        *_markdown_table(["Route", "Support", "Precision", "Recall", "F1"], _route_class_rows(summary)),
        "",
        "## Main Route Confusions",
        "",
    ]

    if confusion_pairs:
        lines.extend(
            _markdown_table(
                ["Expected", "Actual", "Count"],
                [
                    [row["expected"], row["actual"], row["count"]]
                    for row in confusion_pairs[:12]
                ],
            )
        )
    else:
        lines.append("No route confusions available.")

    lines.extend(
        [
            "",
            "## Error Taxonomy",
            "",
            *_markdown_table(["Error type", "Count"], _error_taxonomy(summary, results)),
            "",
        ]
    )

    variant_rows = _variant_comparison_rows(summary)
    lines.extend(["## Variant Comparison", ""])
    if len(variant_rows) > 1:
        lines.extend(
            _markdown_table(
                [
                    "Variant",
                    "Turns",
                    "Route acc.",
                    "Route delta vs full",
                    "Answer pass",
                    "Answer delta vs full",
                    "Median latency",
                    "Latency delta vs full",
                ],
                variant_rows,
            )
        )
    else:
        lines.extend(
            [
                "Only the full system is present. Run a comparison suite before using this as the main CS-paper result:",
                "",
                "```bash",
                "python evaluation/scripts/run_benchmark_suite.py --variants full,llm_only,standard_rag,sql_only,no_router,no_vector,no_sql,no_clarification",
                "```",
            ]
        )

    if results:
        lines.extend(
            [
                "",
                "## Case-Type Breakdown",
                "",
                *_markdown_table(
                    ["Case type", "Turns", "Route acc.", "Answer review rate", "Avg latency"],
                    _case_type_rows(results),
                ),
                "",
            ]
        )
        review_rows = _answer_review_rows(results)
        lines.extend(["## Answer Expectation Failures", ""])
        if review_rows:
            lines.extend(
                _markdown_table(
                    ["Case", "Turn", "Expected route", "Actual route", "Question", "Missing/forbidden terms"],
                    review_rows,
                )
            )
        else:
            lines.append("No answer expectation failures found.")
    else:
        lines.extend(
            [
                "",
                "## Case-Level Analysis",
                "",
                (
                    "Raw `eval_results.jsonl` was not provided, so this report cannot show "
                    "case-type breakdowns, individual answer failures, or slow-turn examples. "
                    "Keep the raw JSONL artifact together with `metric_summary.json` for paper work."
                ),
            ]
        )

    lines.extend(
        [
            "",
            "## Recommended Paper Tables And Figures",
            "",
            *_markdown_table(
                ["Artifact", "Purpose"],
                [
                    ["Dataset composition table", "Show coverage by route, query type, and single/multi-turn setting."],
                    ["Variant comparison table", "Show full SPARA vs LLM-only, standard RAG, SQL-only, and ablations."],
                    ["Route confusion matrix", "Support the architecture/routing claim."],
                    ["Grounding table", "Report unsupported-claim rate, citation coverage, and wrong-field rate."],
                    ["Latency/cost table", "Report median, p95, token use, model calls, and estimated cost/query."],
                    ["Error taxonomy plot", "Explain remaining failures by routing, retrieval, SQL field, clarification, and generation."],
                ],
            ),
            "",
            "## Immediate Next Experiments",
            "",
            "1. Run baselines and ablations on the same cases with the same random/system settings.",
            "2. Add claim-level grounding evaluation for every building-specific factual answer.",
            "3. Increase clarification and out-of-scope support before making per-class claims.",
            "4. Add a small blinded expert review set for answer correctness and usefulness.",
            "5. Report paired deltas and confidence intervals instead of only absolute full-system metrics.",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a paper-oriented CS evaluation analysis from SPARA benchmark artifacts."
    )
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    summary = _load_json(args.summary)
    results = _load_jsonl(args.results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_analysis(results, summary), encoding="utf-8")
    print(f"CS paper analysis written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
