"""Offline probes of SPARA's current Swedish helpers and active prompt policies.

No model, credentials, database, or network is used. Compile only the named pure
functions/methods from the actual source AST, avoiding module import side effects.
This is a diagnostic baseline, not an end-to-end or semantic language evaluation.
Exit 1 means a probe failed; exit 0 does not certify Swedish readiness.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]


def load_functions(path, names, class_name=None, namespace=None):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    nodes = tree.body
    if class_name:
        nodes = next(n.body for n in nodes if isinstance(n, ast.ClassDef) and n.name == class_name)
    selected = [n for n in nodes if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in selected} != set(names):
        raise ValueError(f"Probe source changed; review named functions in {path}")
    # Postpone annotations, as the source module's imports are deliberately skipped.
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *selected], type_ignores=[])
    namespace = {"re": re, **(namespace or {})}
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/pilot_sv/results/offline_readiness.json")
    args = parser.parse_args()
    rows = []

    def record(check_id, source, utterance, expected, actual, scope="pure_function"):
        rows.append(dict(check_id=check_id, source=source, input=utterance,
                         expected=expected, actual=actual, passed=actual == expected, scope=scope))

    router_path = ROOT / "llm-service/src/agents/router_agent.py"
    safety_path = ROOT / "llm-service/src/pipeline/safety_analysis.py"
    document_helper = load_functions(safety_path, ["requests_existing_document"])
    helpers = load_functions(router_path, ["_requested_action_clauses"], namespace=document_helper)
    names = ["_normalize_binary_reply", "is_confirmation", "is_rejection", "wants_draft_report", "wants_expert_handoff"]
    methods = load_functions(router_path, names, "RouterAgent", helpers)
    router = SimpleNamespace()
    for name in names:
        setattr(router, name, methods[name].__get__(router))
    for index, reply in enumerate(["ja", "Ja tack!", "Ja, skicka det.", "Skicka mejlet."]):
        record(f"CONFIRM_{index + 1}", str(router_path.relative_to(ROOT)), reply, True, router.is_confirmation(reply))
    for index, reply in enumerate(["nej", "Nej tack.", "Avbryt", "Skicka inte", "Inte nu"]):
        record(f"CANCEL_{index + 1}", str(router_path.relative_to(ROOT)), reply, True, router.is_rejection(reply))
    for index, reply in enumerate(["Ja, men ta bort kontaktuppgifterna först.", "Skicka inte", "Vad kommer att skickas?", "Jag är inte säker."]):
        record(f"NO_CONSENT_{index + 1}", str(router_path.relative_to(ROOT)), reply, False, router.is_confirmation(reply))
    for index, (utterance, expected) in enumerate([
        ("Skapa en kort rapport till styrelsen.", True),
        ("Kan du sammanfatta samtalet i en rapport?", True),
        ("Vad innehåller en energirapport?", False),
        ("Skapa ingen rapport ännu.", False),
    ]):
        record(f"REPORT_{index + 1}", str(router_path.relative_to(ROOT)), utterance, expected, router.wants_draft_report(utterance))
    for index, (utterance, expected) in enumerate([
        ("Skicka detta till en energirådgivare.", True),
        ("Kan du kontakta en energi- och klimatrådgivare åt oss?", True),
        ("Vad gör en energirådgivare?", False),
        ("Skicka inte detta till en energirådgivare.", False),
    ]):
        record(f"HANDOFF_{index + 1}", str(router_path.relative_to(ROOT)), utterance, expected, router.wants_expert_handoff(utterance))
    path = ROOT / "llm-service/src/pipeline/agent_router.py"
    fast = load_functions(path, ["_fast_conversational_response"])
    answer = fast["_fast_conversational_response"]("Hej")
    # Only identifies the known English greeting; not a general language detector.
    record("GREETING", str(path.relative_to(ROOT)), "Hej", False,
           bool(answer and answer.startswith("Hi!")))
    rows[-1]["observed_text"] = answer
    for filename in ["generic_prompt.txt", "openai_response_prompt.txt",
                     "building_response_generation_prompt.txt", "clarification_prompt.txt",
                     "expert_handoff_summary_prompt.txt"]:
        path = ROOT / "llm-service/src/prompts" / filename
        matches = [dict(line=i, text=line) for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
                   if re.search(r"\b(?:in (?:clear |plain )?English|short English question|English at all times)\b", line)]
        record(f"PROMPT_{filename}", str(path.relative_to(ROOT)),
               "English-only output instruction conflicts with Swedish conversation", [], matches, "static_prompt_scan")
    output = dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),
                  scope="Local pure-function execution and static prompt scan; no live model or UI",
                  total=len(rows), passed=sum(r["passed"] for r in rows),
                  failed=sum(not r["passed"] for r in rows), checks=rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{output['passed']}/{output['total']} probes passed; {output['failed']} failed. {args.output}")
    return 1 if output["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
