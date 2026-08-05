from contextlib import contextmanager

from evaluation.scripts.analyze_eval_results import build_summary
from evaluation.scripts.evaluation_variants import parse_variants
from evaluation.scripts.generate_benchmark_report import build_report
from evaluation.scripts.run_eval_cases import _run_case


@contextmanager
def fake_telemetry_context(operation):
    yield None


def test_parse_variants_accepts_repeated_and_comma_separated_values():
    assert parse_variants(["full,llm_only", "standard_rag"]) == [
        "full",
        "llm_only",
        "standard_rag",
    ]


def test_run_case_records_system_variant():
    class FakeRouter:
        def route_message(self, messages, last_message, metadata, thread_id):
            return {
                "role": "assistant",
                "content": "answer",
                "classification": "generic",
                "agent_answered": "fake",
                "route": "generic",
            }, metadata

    rows = _run_case(
        router=FakeRouter(),
        system_variant="llm_only",
        case={
            "case_id": "CASE_001",
            "question": "How can a BRF save energy?",
            "expected_route": "generic",
        },
        run_id="run-1",
        build_message_metadata=lambda response, metadata: {"route": response["route"]},
        build_message_evidence=lambda metadata: [],
        telemetry_context=fake_telemetry_context,
        telemetry_snapshot=lambda: {"operation": "evaluation_turn"},
    )

    assert rows[0]["system_variant"] == "llm_only"
    assert rows[0]["actual_route"] == "generic"


def test_build_summary_groups_metrics_by_variant():
    summary = build_summary(
        [
            {
                "system_variant": "full",
                "expected_route": "generic",
                "actual_route": "generic",
                "latency_seconds": 1.0,
                "failed": False,
                "grounding": {
                    "status": "passed",
                    "claim_count": 1,
                    "support_ratio": 1.0,
                    "unsupported_claim_rate": 0.0,
                    "citation_coverage": 1.0,
                    "unsupported_claim_count": 0,
                },
                "safety_boundary": {
                    "status": "not_applicable",
                    "detected_risk": False,
                    "handled_safely": True,
                    "requires_review": False,
                },
            },
            {
                "system_variant": "llm_only",
                "expected_route": "building_specific",
                "actual_route": "generic",
                "expected_building_id": "abc-123",
                "retrieved_building_id": None,
                "expected_fields": ["energy_class"],
                "retrieved_facts": {},
                "latency_seconds": 2.0,
                "failed": False,
                "grounding": {
                    "status": "needs_review",
                    "claim_count": 2,
                    "support_ratio": 0.5,
                    "unsupported_claim_rate": 0.5,
                    "citation_coverage": 0.0,
                    "unsupported_claim_count": 1,
                    "requires_review": True,
                },
                "safety_boundary": {
                    "status": "needs_review",
                    "detected_risk": True,
                    "risk_category": "financial_advice",
                    "handled_safely": False,
                    "requires_review": True,
                },
            },
        ],
        [],
    )

    assert summary["by_variant"]["full"]["route_accuracy"] == 1.0
    assert summary["by_variant"]["llm_only"]["route_accuracy"] == 0.0
    assert summary["by_variant"]["llm_only"]["grounding_review_rate"] == 1.0
    assert summary["by_variant"]["llm_only"]["safety_review_rate"] == 1.0
    assert summary["by_variant"]["llm_only"]["boundary_handled_safely_rate"] == 0.0
    assert summary["unsupported_claim_count"] == 1
    assert summary["variant_comparison"][0]["system_variant"] == "full"
    assert "route_macro_f1" in summary["by_variant"]["full"]


def test_build_report_includes_variant_comparison():
    report = build_report(
        [
            {
                "run_id": "run-1",
                "system_variant": "full",
                "case_id": "GEN_001",
                "case_type": "general",
                "turn_index": 0,
                "expected_route": "generic",
                "actual_route": "generic",
                "latency_seconds": 1.0,
                "failed": False,
                "user_message": "How can we save heat?",
            }
        ],
        {
            "total_turns": 1,
            "total_cases_with_expected_route": 1,
            "route_accuracy": 1.0,
            "route_macro_f1": 1.0,
            "variant_comparison": [
                {
                    "system_variant": "full",
                    "total_turns": 1,
                    "route_accuracy": 1.0,
                    "route_macro_f1": 1.0,
                    "failure_rate": 0.0,
                }
            ],
        },
    )

    assert "## Variant Comparison" in report
    assert "| full |" in report
