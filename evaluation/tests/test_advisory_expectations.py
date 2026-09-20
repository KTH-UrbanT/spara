from evaluation.scripts.run_eval_cases import _answer_expectation
from evaluation.scripts.generate_benchmark_report import _answer_expectation_summary


def test_keyword_match_does_not_pass_a_semantic_advisory_contract():
    result = _answer_expectation(
        "Heating can use energy.", must_include=["heating"], must_not_include=[],
        review_criteria=["Identifies what changed before recommending a measure."],
    )
    assert result["automated_status"] == "passed"
    assert result["status"] == "needs_review"
    assert result["requires_advisor_review"] is True


def test_automated_failures_remain_visible_for_advisor_cases():
    result = _answer_expectation(
        "guaranteed savings", must_include=["heating"],
        must_not_include=["guaranteed savings"], review_criteria=["Evidence-based advice"],
    )
    assert result["automated_status"] == "needs_review"
    assert result["missing_required_terms"] == ["heating"]
    assert result["forbidden_terms_present"] == ["guaranteed savings"]


def test_report_labels_keyword_checks_and_advisor_review_separately():
    assert _answer_expectation_summary({"answer_expectation_status": "passed"}) == "keyword checks passed"
    text = _answer_expectation_summary({
        "answer_expectation_status": "needs_review", "requires_advisor_review": True,
        "review_criteria": ["Explains why the next check matters."],
    })
    assert "advisor review required" in text
    assert "Explains why" in text
