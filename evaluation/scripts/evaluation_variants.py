from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, List


AVAILABLE_VARIANTS = (
    "full",
    "llm_only",
    "standard_rag",
    "sql_only",
    "no_router",
    "no_vector",
    "no_sql",
    "no_clarification",
)

DEFAULT_VARIANTS = ("full",)


def parse_variants(raw_values: Iterable[str] | None) -> List[str]:
    variants: List[str] = []
    for raw_value in raw_values or []:
        for part in str(raw_value or "").split(","):
            variant = part.strip()
            if variant and variant not in variants:
                variants.append(variant)
    if not variants:
        variants = list(DEFAULT_VARIANTS)

    unknown = [variant for variant in variants if variant not in AVAILABLE_VARIANTS]
    if unknown:
        supported = ", ".join(AVAILABLE_VARIANTS)
        raise ValueError(f"Unsupported evaluation variant(s): {', '.join(unknown)}. Supported: {supported}")
    return variants


class FullSystemVariant:
    def __init__(self, AgentRouter, *, variant_name: str = "full"):
        self.variant_name = variant_name
        self.router = AgentRouter()

    def route_message(self, messages, last_message, metadata, thread_id):
        return self.router.route_message(messages, last_message, metadata, thread_id)


class LLMOnlyVariant:
    def __init__(self):
        from src.agents.openai_agent import OpenAIResponseAgent

        self.agent = OpenAIResponseAgent()

    def route_message(self, messages, last_message, metadata, thread_id):
        response_text = self.agent.generate_response(last_message, messages)
        return {
            "role": "assistant",
            "content": response_text,
            "classification": "baseline",
            "agent_answered": "LLMOnlyBaseline",
            "route": "generic",
        }, metadata or {}


class StandardRAGVariant:
    def __init__(self):
        from src.agents.generic_agent import GenericAgent

        self.agent = GenericAgent()

    def route_message(self, messages, last_message, metadata, thread_id):
        response = self.agent.handle_generic_input(last_message, messages)
        if isinstance(response, dict):
            content = response.get("content") or ""
            sources = response.get("sources") or []
        else:
            content = response or ""
            sources = []

        payload = {
            "role": "assistant",
            "content": content,
            "classification": "baseline",
            "agent_answered": "StandardRAGBaseline",
            "route": "generic",
        }
        if sources:
            payload["sources"] = sources
        return payload, metadata or {}


class SQLOnlyVariant:
    def __init__(self):
        from src.agents.generic_sql_layer import SQL_Mapper_Layer
        from src.agents.openai_agent import OpenAIResponseAgent

        self.sql_layer = SQL_Mapper_Layer()
        self.response_agent = OpenAIResponseAgent()

    def route_message(self, messages, last_message, metadata, thread_id):
        from src.pipeline.safety_analysis import extract_retrieved_facts

        base_metadata = dict(metadata or {})
        decision = self.sql_layer.route(
            {
                "last_message": last_message,
                "messages": messages,
                "metadata": base_metadata,
            }
        )
        result = self.sql_layer.execute(decision.op, **decision.kwargs)
        retrieved_facts = extract_retrieved_facts(result.get("data"))
        sql_trace = result.get("trace") or {
            "query_type": decision.op,
            "execution_status": "unknown",
            "error_message": result.get("message"),
        }
        updated_metadata = {
            **base_metadata,
            "retrieved_facts": retrieved_facts,
            "sql_trace": sql_trace,
        }

        if not result.get("ok") or not result.get("data"):
            updated_metadata["clarification"] = {
                "needed": True,
                "reason": "missing_building_data",
                "question_asked": "I need an address or matching building data before I can answer from the structured database.",
                "resolved": False,
                "resolved_after_turns": None,
            }
            return {
                "role": "assistant",
                "content": updated_metadata["clarification"]["question_asked"],
                "classification": "baseline",
                "agent_answered": "SQLOnlyBaseline",
                "route": "clarification",
            }, updated_metadata

        user_prompt = (
            "Answer the user's question using only the structured building data below. "
            "If the data does not support a claim, say that it is not available.\n\n"
            f"Question:\n{last_message}\n\n"
            "Structured building data:\n"
            f"{json.dumps(result.get('data'), ensure_ascii=False, indent=2)}"
        )
        response_text = self.response_agent.generate_response(user_prompt, [])
        return {
            "role": "assistant",
            "content": response_text,
            "classification": "baseline",
            "agent_answered": "SQLOnlyBaseline",
            "route": "building_specific",
        }, updated_metadata


class NoRouterVariant:
    def __init__(self):
        from src.agents.building_agent import BuildingAgent

        self.building_agent = BuildingAgent()

    def route_message(self, messages, last_message, metadata, thread_id):
        response, updated_metadata = self.building_agent.handle_building_query(
            last_message,
            messages,
            metadata or {},
            thread_id,
        )
        response = {
            **response,
            "classification": "baseline",
            "agent_answered": "NoRouterAblation",
        }
        return response, updated_metadata


class NoClarificationVariant:
    def __init__(self, AgentRouter):
        self.router = AgentRouter()
        self._generic_agent = None

    def _generic_fallback(self, messages, last_message):
        if self._generic_agent is None:
            from src.agents.generic_agent import GenericAgent

            self._generic_agent = GenericAgent()
        response = self._generic_agent.handle_generic_input(last_message, messages)
        if isinstance(response, dict):
            return response.get("content") or "", response.get("sources") or []
        return response or "", []

    def route_message(self, messages, last_message, metadata, thread_id):
        response, updated_metadata = self.router.route_message(
            messages,
            last_message,
            metadata or {},
            thread_id,
        )
        clarification = (updated_metadata or {}).get("clarification") or {}
        if response.get("route") != "clarification" and not clarification.get("needed"):
            return response, updated_metadata

        content, sources = self._generic_fallback(messages, last_message)
        updated_metadata = dict(updated_metadata or {})
        updated_metadata["clarification"] = {
            "needed": False,
            "suppressed_by_ablation": True,
            "original_question": response.get("content"),
        }
        payload = {
            "role": "assistant",
            "content": content,
            "classification": "baseline",
            "agent_answered": "NoClarificationAblation",
            "route": "generic",
        }
        if sources:
            payload["sources"] = sources
        return payload, updated_metadata


def build_variant_router(variant: str, AgentRouter):
    if variant == "full":
        return FullSystemVariant(AgentRouter)
    if variant == "llm_only":
        return LLMOnlyVariant()
    if variant == "standard_rag":
        return StandardRAGVariant()
    if variant == "sql_only":
        return SQLOnlyVariant()
    if variant == "no_router":
        return NoRouterVariant()
    if variant in {"no_vector", "no_sql"}:
        return FullSystemVariant(AgentRouter, variant_name=variant)
    if variant == "no_clarification":
        return NoClarificationVariant(AgentRouter)
    raise ValueError(f"Unsupported evaluation variant: {variant}")


@contextmanager
def variant_runtime_context(variant: str) -> Iterator[None]:
    restorers = []

    def restore_attr(target: Any, name: str, original: Any) -> None:
        setattr(target, name, original)

    try:
        if variant == "no_vector":
            from src.database.vector_client import VectorClient

            original_query = VectorClient.query
            VectorClient.query = lambda self, question: []
            restorers.append(lambda: restore_attr(VectorClient, "query", original_query))

            try:
                from src.agents import building_flow_graph

                original_instance_query = building_flow_graph.vector_database.query
                building_flow_graph.vector_database.query = lambda question: []
                restorers.append(
                    lambda: restore_attr(
                        building_flow_graph.vector_database,
                        "query",
                        original_instance_query,
                    )
                )
            except Exception:
                pass

        if variant == "no_sql":
            from src.agents.generic_sql_layer import SQL_Mapper_Layer
            from src.agents.specialized_sql_layer import SpecializedSQLLayer

            original_generic_execute = SQL_Mapper_Layer.execute
            original_specialized_execute = SpecializedSQLLayer.execute

            def disabled_generic_execute(self, op, **kwargs):
                return {
                    "ok": True,
                    "data": None,
                    "message": "SQL disabled by no_sql ablation.",
                    "trace": {
                        "query_type": op,
                        "execution_status": "disabled_by_ablation",
                        "rows_returned": 0,
                        "filters_used": kwargs,
                    },
                }

            def disabled_specialized_execute(self, op, kwargs):
                return {
                    "ok": True,
                    "data": None,
                    "message": "Specialized SQL disabled by no_sql ablation.",
                    "sql_trace": {
                        "query_type": "specialized_sql",
                        "execution_status": "disabled_by_ablation",
                        "rows_returned": 0,
                        "filters_used": kwargs,
                    },
                }

            SQL_Mapper_Layer.execute = disabled_generic_execute
            SpecializedSQLLayer.execute = disabled_specialized_execute
            restorers.append(lambda: restore_attr(SQL_Mapper_Layer, "execute", original_generic_execute))
            restorers.append(lambda: restore_attr(SpecializedSQLLayer, "execute", original_specialized_execute))

        yield
    finally:
        for restore in reversed(restorers):
            restore()
