from evaluation.scripts.run_eval_cases import _answer_expectation
from evaluation.scripts.generate_benchmark_report import _answer_expectation_summary
import json
from pathlib import Path
import re
import pytest


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


@pytest.mark.parametrize(("label", "answer", "status"), [
    ("F", "Energy performance is recorded; ventilation uses FTX.", "needs_review"),
    ("C", "Controls can improve comfort.", "needs_review"),
    ("F", "The declared energy class is F.", "passed"),
    ("C", "The declared energy class is C, according to the record.", "passed"),
    ("A0", "The recorded class is A0.", "passed"),
    ("A", "The recorded class is A0.", "needs_review"),
])
def test_energy_class_keywords_require_a_complete_token(label, answer, status):
    result = _answer_expectation(answer, must_include=[label], must_not_include=[])
    assert result["automated_status"] == status


def _swedish_pilot_cases():
    path = Path(__file__).resolve().parents[1] / "data" / "swedish_pilot_cases.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def test_swedish_regression_inputs_preserve_actual_user_wording():
    cases = {case["case_id"]: case for case in _swedish_pilot_cases()}
    expected_turns = {
        "SV_REG_SOLAR_MISSING_INPUTS": (3, "Kan du ange exakt besparing och återbetalningstid?"),
        "SV_REG_MUNICIPALITY_CORRECTION": (1, "Jönköping."),
        "SV_REG_ADDRESS_ALIAS_FOLLOWUP": (2, "Varför visas Hornsgatan 104 när jag frågade om Ringvägen 10?"),
        "SV_REG_BUILDING_ID_RECOVERY": (4, "Gå tillbaka till 01-80-KAAKENHUSEN40-1 och visa energiklassen."),
        "SV_REG_SWEDISH_REPORT_DRAFT": (2, "Skapa ett nedladdningsbart rapportutkast till styrelsen med underlaget, våra observationer, osäkerheter och nästa steg."),
    }
    for case_id, (turn, text) in expected_turns.items():
        assert cases[case_id]["turns"][turn]["user"] == text


def test_swedish_pilot_cases_have_unique_ids_and_no_corrupted_words():
    cases = _swedish_pilot_cases()
    case_ids = [case["case_id"] for case in cases]
    assert len(case_ids) == len(set(case_ids))
    for case in cases:
        text = json.dumps(case, ensure_ascii=False)
        assert "\ufffd" not in text, case["case_id"]
        assert not re.search(r"\w\?\w", text), case["case_id"]


def test_new_sharing_and_language_cases_require_multi_turn_semantic_review():
    cases = {case["case_id"]: case for case in _swedish_pilot_cases()}
    for case_id in ("SV_REG_HANDOFF_SHARING_SCOPE", "SV_REG_LANGUAGE_SWITCH_CARDS"):
        case = cases[case_id]
        assert len(case["turns"]) >= 3
        assert case["review_criteria"]
    handoff = cases["SV_REG_HANDOFF_SHARING_SCOPE"]
    assert "no-send" in handoff["execution_constraint"]
    assert handoff["turns"][-1]["user"] == "Avbryt. Skicka inget."
