from contextlib import nullcontext

import pytest

from evaluation.scripts.run_eval_cases import _run_case


class ScriptedRouter:
    def __init__(self, responses):
        self.responses = iter(responses)

    def route_message(self, messages, last_message, metadata, thread_id):
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response, metadata


def run_case(case, responses):
    return _run_case(
        router=ScriptedRouter(responses), system_variant="full", case=case,
        run_id="offline-advisory-test",
        build_message_metadata=lambda response, metadata: {"route": response.get("route", "generic")},
        build_message_evidence=lambda metadata: [],
        telemetry_context=lambda operation: nullcontext(),
        telemetry_snapshot=lambda: {},
    )


def test_single_turn_case_retains_semantic_criteria_after_turn_conversion():
    criteria = ["Explores the objective before proposing equipment."]
    rows = run_case({
        "case_id": "ADVISORY_SINGLE", "question": "Should we replace the windows?",
        "review_criteria": criteria, "must_include": ["windows"],
    }, [{"content": "windows"}])
    assert rows[0]["failed"] is False
    assert rows[0]["review_criteria"] == criteria
    assert rows[0]["answer_expectation"]["automated_status"] == "passed"
    assert rows[0]["answer_expectation_status"] == "needs_review"


def test_turn_specific_review_criteria_override_case_defaults():
    default = ["Uses earlier user constraints."]
    report = ["Produces a report artifact or explains failure."]
    rows = run_case({
        "case_id": "ADVISORY_TURNS", "review_criteria": default,
        "turns": [
            {"user": "We cannot do major renovations."},
            {"user": "Create a report.", "review_criteria": report},
            {"user": "Thanks", "review_criteria": []},
        ],
    }, [{"content": "Advice"}, {"content": "Report"}, {"content": "Welcome"}])
    assert [row["review_criteria"] for row in rows] == [default, report, []]
    assert [row["requires_advisor_review"] for row in rows] == [True, True, False]
    assert rows[2]["answer_expectation_status"] == "not_checked"


@pytest.mark.parametrize("status", ["generated", "fallback", "storage_failed"])
def test_report_execution_evidence_is_retained_for_review(status):
    response = {"content": "Report outcome", "route": "report_generation", "report_status": status}
    artifact = {"report_id": "report-1", "file_name": "draft.txt", "expires_at": "2026-09-20T12:30:00+00:00"}
    if status != "storage_failed":
        response["downloadable_report"] = artifact
    rows = run_case({"case_id": "ADVISORY_REPORT", "question": "Create a draft report."}, [response])
    assert rows[0]["report_status"] == status
    assert rows[0]["downloadable_report"] == (None if status == "storage_failed" else artifact)


def test_router_failure_preserves_review_contract_without_claiming_a_pass():
    criteria = ["Provides a useful next step."]
    rows = run_case({
        "case_id": "ADVISORY_FAILURE", "question": "What next?", "review_criteria": criteria,
    }, [RuntimeError("scripted failure")])
    assert rows[0]["failed"] is True
    assert rows[0]["error"] == "scripted failure"
    assert rows[0]["requires_advisor_review"] is True
    assert rows[0]["review_criteria"] == criteria
    assert rows[0]["answer_expectation_status"] == "not_checked"
