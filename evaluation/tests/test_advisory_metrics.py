import csv
import json
import pytest

from evaluation.scripts.analyze_eval_results import build_summary
from evaluation.scripts.export_advisor_review_sheet import main as export_review_sheet
from evaluation.scripts import analyze_eval_results as analyzer


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
    assert summary["advisor_review_pending_count"] == 1
    assert summary["advisor_review_completed_count"] == 0


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
    current = {**_advisory_result(), "run_id": "current-run", "assistant_content": "Current answer"}
    rows = [current, {"case_id": "LEGACY", "answer_expectation_status": "passed"}]
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
    assert exported[0]["run_id"] == "current-run"
    assert exported[0]["assistant_content"] == "Current answer"
    assert exported[1]["answer_automated_status"] == "passed"
    assert exported[1]["requires_advisor_review"] == "False"
    assert json.loads(exported[1]["review_criteria"]) == []


def _completed_review(**overrides):
    return {"case_id": "ADVISORY_TEST", "system_variant": "full", "turn_index": 0,
            "run_id": "current-run", "assistant_content": "Current answer",
            "technical_correctness_score": "4", "usefulness_score": "4", "clarity_score": "4",
            "useful": "true", "unsafe_or_misleading": "false", **overrides}


def _current_result(**overrides):
    return {**_advisory_result(), "run_id": "current-run", "assistant_content": "Current answer", **overrides}


def test_blank_export_rows_do_not_count_as_completed_advisor_reviews():
    blank = {"case_id": "ADVISORY_TEST", "system_variant": "full", "turn_index": "0",
             "run_id": "current-run", "assistant_content": "Current answer"}
    summary = build_summary([_current_result()], [blank])
    assert summary["advisor_review_input_count"] == summary["advisor_review_blank_count"] == 1
    assert summary["advisor_review_count"] == summary["advisor_review_completed_count"] == 0
    assert summary["advisor_review_pending_count"] == 1


def test_only_full_current_rubric_clears_required_pending_review():
    summary = build_summary([_current_result()], [_completed_review()])
    assert summary["advisor_review_count"] == summary["advisor_review_completed_count"] == 1
    assert summary["advisor_review_pending_count"] == summary["advisor_review_partial_count"] == 0
    assert summary["by_variant"]["full"]["advisor_review_pending_count"] == 0
    # Completion records a filled rubric, including a bad answer, not approval.
    unsafe = build_summary([_current_result()], [_completed_review(unsafe_or_misleading="true", needs_major_edit="true")])
    assert unsafe["advisor_review_completed_count"] == unsafe["unsafe_or_misleading_count"] == unsafe["needs_major_edit_count"] == 1


def test_partial_grades_remain_pending_without_losing_recorded_scores():
    summary = build_summary([_current_result()], [_completed_review(clarity_score="")])
    assert summary["advisor_review_partial_count"] == summary["advisor_review_pending_count"] == 1
    assert summary["advisor_review_completed_count"] == 0
    assert summary["advisor_average_usefulness"] == 4.0


@pytest.mark.parametrize("overrides", [
    {"run_id": "old-run"}, {"case_id": "OTHER"}, {"system_variant": "llm_only"},
    {"turn_index": 1}, {"turn_index": 0.5}, {"assistant_content": "Another answer"},
])
def test_unmatched_or_stale_reviews_cannot_clear_pending_turns(overrides):
    summary = build_summary([_current_result()], [_completed_review(**overrides)])
    assert summary["advisor_review_unmatched_count"] == summary["advisor_review_pending_count"] == 1
    assert summary["advisor_review_completed_count"] == summary["advisor_review_count"] == 0


@pytest.mark.parametrize("with_snapshot", [False, True])
def test_legacy_reviews_without_current_run_provenance_remain_pending(with_snapshot):
    review = _completed_review()
    review.pop("run_id")
    if not with_snapshot:
        review.pop("assistant_content")
    summary = build_summary([_current_result()], [review])
    assert summary["advisor_review_unverified_legacy_count"] == 1
    assert summary["advisor_review_pending_count"] == 1
    assert summary["advisor_review_completed_count"] == 0


@pytest.mark.parametrize("invalid_score", ["", "bad", "nan", "inf", "0", "6", True])
def test_invalid_or_missing_rubric_scores_do_not_complete_reviews(invalid_score):
    summary = build_summary([_current_result()], [_completed_review(technical_correctness_score=invalid_score)])
    assert summary["advisor_review_pending_count"] == 1
    assert summary["advisor_review_completed_count"] == 0


def test_duplicate_reviews_do_not_complete_other_required_turns():
    summary = build_summary([_current_result(), _current_result(turn_index=1)], [_completed_review(), _completed_review()])
    assert summary["advisor_review_required_count"] == 2
    assert summary["advisor_review_completed_count"] == summary["advisor_review_pending_count"] == 1


def test_failure_contracts_keep_identity_and_field_denominators_visible():
    summary = build_summary([
        {"expected_route": "building_specific", "actual_route": None, "failed": True,
         "expected_building_id": "building-A", "expected_fields": ["energy_class"],
         "retrieved_building_id": None, "retrieved_facts": {}},
        {"actual_route": "generic", "grounding": {"status": "not_assessed"}},
    ], [])
    assert summary["failure_count"] == 1
    assert summary["route_checked_count"] == summary["route_unchecked_count"] == 1
    assert summary["building_identification_checked_count"] == summary["building_identification_unchecked_count"] == 1
    assert summary["building_identification_match_count"] == summary["field_found_count"] == 0
    assert summary["field_expected_count"] == 1
    assert summary["grounding_evaluated_turns"] == 0
    assert summary["grounding_unassessed_turns"] == 2


@pytest.mark.parametrize("input_kind", ["missing_results", "empty_results", "missing_reviews"])
def test_analyzer_rejects_missing_or_empty_explicit_inputs(tmp_path, monkeypatch, input_kind):
    results, output = tmp_path / "results.jsonl", tmp_path / "summary.json"
    if input_kind != "missing_results":
        results.write_text("" if input_kind == "empty_results" else json.dumps(_current_result()) + "\n", encoding="utf-8")
    argv = ["analyze_eval_results", "--results", str(results), "--output", str(output)]
    if input_kind == "missing_reviews":
        argv += ["--reviews", str(tmp_path / "missing.csv")]
    monkeypatch.setattr("sys.argv", argv)
    with pytest.raises(SystemExit) as exc:
        analyzer.main()
    assert exc.value.code == 2
    assert not output.exists()


def test_optional_absent_review_file_reports_pending_instead_of_a_pass(tmp_path, monkeypatch):
    results, output = tmp_path / "results.jsonl", tmp_path / "summary.json"
    results.write_text(json.dumps(_current_result()) + "\n", encoding="utf-8")
    monkeypatch.setattr(analyzer, "DEFAULT_REVIEWS_PATH", tmp_path / "not-provided.csv")
    monkeypatch.setattr("sys.argv", ["analyze_eval_results", "--results", str(results), "--output", str(output)])
    assert analyzer.main() == 0
    summary = json.loads(output.read_text(encoding="utf-8"))
    assert summary["advisor_reviews_input_status"] == "not_provided"
    assert summary["advisor_review_required_count"] == summary["advisor_review_pending_count"] == 1
