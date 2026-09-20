import csv
import json

from evaluation.scripts.analyze_eval_results import build_summary
from evaluation.scripts.export_advisor_review_sheet import main as export_review_sheet


def _advisory_result(automated_status="passed", variant="full"):
    return {
        "case_id": "ADVISORY_TEST",
        "system_variant": variant,
        "turn_index": 0,
        "answer_expectation_status": "needs_review",
        "requires_advisor_review": True,
        "review_criteria": ["Explains why the next check matters."],
        "answer_expectation": {
            "status": "needs_review",
            "automated_status": automated_status,
            "requires_advisor_review": True,
        },
    }


def test_pending_advisory_review_does_not_fail_automated_checks():
    summary = build_summary([_advisory_result()], [])

    assert summary["answer_expectation_accuracy"] == 1.0
    assert summary["answer_expectation_checked_count"] == 1
    assert summary["answer_expectation_review_count"] == 1
    assert summary["answer_automated_review_count"] == 0
    assert summary["advisor_review_required_count"] == 1
    assert summary["by_variant"]["full"]["answer_expectation_accuracy"] == 1.0
    assert summary["variant_comparison"][0]["advisor_review_required_count"] == 1


def test_semantic_only_review_does_not_invent_a_keyword_failure_or_pass():
    summary = build_summary([_advisory_result("not_checked")], [])

    assert summary["answer_expectation_accuracy"] is None
    assert summary["answer_expectation_checked_count"] == 0
    assert summary["answer_automated_review_count"] == 0
    assert summary["advisor_review_required_count"] == 1


def test_actual_keyword_failures_still_count_with_advisory_review():
    summary = build_summary([
        _advisory_result("passed", "full"),
        _advisory_result("needs_review", "llm_only"),
    ], [])

    assert summary["answer_expectation_accuracy"] == 0.5
    assert summary["answer_automated_review_count"] == 1
    assert summary["advisor_review_required_count"] == 2
    assert summary["by_variant"]["llm_only"]["answer_expectation_accuracy"] == 0.0


def test_historical_result_statuses_retain_their_metric_contract():
    summary = build_summary([
        {"answer_expectation_status": "passed"},
        {"answer_expectation_status": "needs_review"},
        {"answer_expectation_status": "not_checked"},
    ], [])

    assert summary["answer_expectation_accuracy"] == 0.5
    assert summary["answer_expectation_checked_count"] == 2
    assert summary["answer_expectation_review_count"] == 1
    assert summary["advisor_review_required_count"] == 0


def test_export_preserves_review_criteria_and_distinct_statuses(tmp_path, monkeypatch):
    results_path = tmp_path / "results.jsonl"
    output_path = tmp_path / "reviews.csv"
    rows = [_advisory_result(), {"case_id": "LEGACY", "answer_expectation_status": "passed"}]
    results_path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    monkeypatch.setattr("sys.argv", [
        "export_advisor_review_sheet", "--results", str(results_path),
        "--output", str(output_path),
    ])

    assert export_review_sheet() == 0
    with output_path.open(encoding="utf-8", newline="") as handle:
        exported = list(csv.DictReader(handle))

    assert exported[0]["answer_expectation_status"] == "needs_review"
    assert exported[0]["answer_automated_status"] == "passed"
    assert exported[0]["requires_advisor_review"] == "True"
    assert json.loads(exported[0]["review_criteria"]) == rows[0]["review_criteria"]
    assert exported[1]["answer_automated_status"] == "passed"
    assert exported[1]["requires_advisor_review"] == "False"
    assert json.loads(exported[1]["review_criteria"]) == []
