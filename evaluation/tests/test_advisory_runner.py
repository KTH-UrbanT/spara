from contextlib import nullcontext
import json

import pytest

from evaluation.scripts.run_eval_cases import _run_case
from evaluation.scripts import run_eval_cases as runner


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


def test_failed_turn_preserves_inherited_and_overridden_identity_field_contracts():
    rows = run_case({"case_id": "FAIL_CONTRACT", "expected_building_id": "building-A",
                     "expected_fields": ["energy_class"], "turns": [
        {"user": "First"},
        {"user": "Second", "expected_building_id": "building-B", "expected_fields": ["heating_system"]},
        {"user": "Third", "expected_building_id": None, "expected_fields": []},
    ]}, [RuntimeError("offline") for _ in range(3)])
    assert [row["expected_building_id"] for row in rows] == ["building-A", "building-B", None]
    assert [row["expected_fields"] for row in rows] == [["energy_class"], ["heating_system"], []]
    assert all(row["retrieved_building_id"] is None and row["retrieved_facts"] == {} and row["failed"] for row in rows)


def test_case_exclusions_are_opt_in_and_do_not_mutate_input():
    cases = [{"case_id": case_id} for case_id in (*runner.RELEASE_EXCLUDED_CASE_IDS, "INCLUDED")]
    assert runner._filter_cases(cases, case_id=None, route=None, limit=None) == cases
    assert runner._filter_cases(cases, case_id=None, route=None, limit=None,
                                exclude_case_ids=runner.RELEASE_EXCLUDED_CASE_IDS) == [{"case_id": "INCLUDED"}]
    assert len(cases) == 3


@pytest.mark.parametrize("release_scope", [False, True])
def test_runner_records_complete_explicit_scope_manifest(tmp_path, monkeypatch, release_scope):
    input_path, output = tmp_path / "cases.jsonl", tmp_path / "results.jsonl"
    cases = [{"case_id": name, "question": "Synthetic question"} for name in (*runner.RELEASE_EXCLUDED_CASE_IDS, "INCLUDED")]
    input_path.write_text("".join(json.dumps(case) + "\n" for case in cases), encoding="utf-8")
    fake = ScriptedRouter([{"content": "Offline answer"} for _ in cases])
    monkeypatch.setattr(runner, "_import_runtime", lambda: (object, lambda response, metadata: {"route": "generic"},
                         lambda metadata: [], lambda operation: nullcontext(), lambda: {}))
    monkeypatch.setattr(runner, "build_variant_router", lambda *args: fake)
    argv = ["run_eval_cases", "--input", str(input_path), "--output", str(output)]
    if release_scope:
        argv.append("--release-scope")
    monkeypatch.setattr("sys.argv", argv)
    assert runner.main() == 0
    scope = json.loads(output.with_suffix(".scope.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert scope["input_cases"] == scope["input_turns"] == 3
    assert scope["expected_result_turns"] == scope["included_cases"] == len(rows) == (1 if release_scope else 3)
    assert len(scope["excluded_cases"]) == (2 if release_scope else 0)
    assert all(row["run_id"] == scope["run_id"] for row in rows)
    assert input_path.read_text(encoding="utf-8") == "".join(json.dumps(case) + "\n" for case in cases)


@pytest.mark.parametrize("options", [["--exclude-case-id", "UNKNOWN"], ["--case-id", "UNKNOWN"], ["--limit", "0"]])
def test_invalid_or_empty_case_selection_fails_before_runtime_import(tmp_path, monkeypatch, options):
    input_path = tmp_path / "cases.jsonl"
    input_path.write_text(json.dumps({"case_id": "CASE", "question": "Offline"}) + "\n", encoding="utf-8")
    monkeypatch.setattr(runner, "_import_runtime", lambda: pytest.fail("Runtime must not be imported"))
    monkeypatch.setattr("sys.argv", ["run_eval_cases", "--input", str(input_path), *options])
    with pytest.raises(SystemExit) as exc:
        runner.main()
    assert exc.value.code == 2
