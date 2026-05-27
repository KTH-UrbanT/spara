# SPARA Evaluation

This folder now has one practical purpose first: run a small, repeatable demo
evaluation and send the answers to the team.

The deeper research evaluation can still be built from these artifacts later,
but the front-door workflow is intentionally small.

## What We Run On Demo

Run a fixed mix of scenarios:

- generic energy-advice questions
- building-specific questions with an address
- missing-address questions where SPARA should ask for clarification
- multi-turn conversations
- out-of-scope or handoff cases
- readiness behavior checks from the readiness cases, including hallucination
  traps, source transparency, stale-context/memory checks, and stress cases

Each case records expected behavior and an expected-answer contract, not a
perfect word-for-word reference answer. Example:

```json
{"case_id":"GEN_001","question":"How can an apartment building reduce heating costs?","expected_route":"generic","expected_answer":"Explain practical heating-cost reduction steps, such as controls, ventilation checks, insulation, and avoiding guaranteed savings.","must_include":["heating"],"must_not_include":["guaranteed savings"],"case_type":"general_energy_advice"}
{"case_id":"CLAR_MULTI_001","turns":[{"user":"What should our building prioritize?","expected_route":"clarification","expected_answer":"Ask for the full building address before giving personalized advice.","must_include":["address"]},{"user":"The address is [street address]","expected_route":"combined","expected_answer":"Use the address to retrieve building data and combine it with general advisory guidance."}],"case_type":"multi_turn_clarification"}
```

Default cases live in:

```text
evaluation/data/evaluation_cases.jsonl
```

## Readiness Behavior Cases

The normal evaluation now includes a focused readiness slice directly in
`evaluation/data/evaluation_cases.jsonl`. These cases use IDs like
`READINESS_A01...` through `READINESS_J02...` and mirror the behavior groups in
`evaluation/READINESS_CHECKLIST.md`:

- clarification and building identification
- multi-address identity where street addresses are aliases and building ID /
  `byggnadsid` is the source of truth
- database lookup and latest building-context use
- combined fact-plus-advice answers, especially Energy Conservation Measures
  (ECMs) for heating-cost and energy-efficiency questions
- routing between generic and building-specific questions
- multi-turn memory
- missing data, contradiction, and identity conflict behavior
- out-of-scope financial/legal/vendor requests
- hallucination traps such as fake quotes, fake audits, and OVK conclusions
- efficiency/stress limits
- source transparency and handover

These rows run as part of the default benchmark suite. The simple
`must_include` and `must_not_include` terms catch obvious failures, while the
`expected_answer` and `expected_behavior` fields tell reviewers what good
behavior should look like.

## EKR Question Bank Questions

Selected translated questions from the EKR question bank are included directly in:

```text
evaluation/data/evaluation_cases.jsonl
```

They use case IDs like `EKR_GEN_001`. Each row keeps:

- the English question used by SPARA
- the expected answer or answer-quality contract
- optional `must_include` and `must_not_include` terms for simple automatic checks
- the original Swedish question
- the original EKR category
- the expected route, currently `generic`

The demo pipeline should keep using the default CI command in `.gitlab-ci.yml`.
Building-specific and multi-turn variants should be added as separate cases in
`evaluation_cases.jsonl`.

Multi-turn scenarios use a `turns` array. Each turn has the user message plus
the expected route, expected-answer contract, and optional simple checks. The
current demo set includes `MULTI_...` scenarios for generic advice, address
clarification, building-specific follow-ups, ambiguous-address resolution, and
expert handoff confirmation.

## ODEN Building-Specific Cases

Building-specific cases can be generated from ODEN address lookups instead of
copying large API responses into the repo:

```bash
python evaluation/scripts/generate_oden_building_cases.py --merge-into evaluation/data/evaluation_cases.jsonl
```

By default this fetches the current demo address set and writes a compact copy to:

```text
evaluation/data/oden_building_specific_cases.jsonl
```

It also replaces old generated `BRF_ODEN...` rows in `evaluation_cases.jsonl`
when `--merge-into` is used. The generated rows keep only the evaluation
contract: address, city, building ID, expected fields, expected answer, and
small automatic checks.

## One Command

From the repo root:

```bash
python evaluation/scripts/run_benchmark_suite.py --email-report
```

This generates and emails:

- `evaluation/results/benchmark_report.md`
- `evaluation/results/metric_summary.json`
- `evaluation/results/eval_results.jsonl`

The report includes:

- headline pass/fail metrics
- a table of questions, expected answers, answer-check status, actual route, and SPARA answer
- route mismatches
- expected-answer review flags
- failures
- grounding and safety flags
- slow turns

## Demo Server

On demo deploy, CI can run the same suite after `deploy_demo`. The report is
written on the demo server at:

```text
/home/gitlab-runner/spara-demo-deploy/current/evaluation/results/benchmark_report.md
```

Email recipients are controlled with:

```text
BENCHMARK_EMAIL_RECIPIENTS
```

It accepts comma, semicolon, or whitespace separated addresses.

## What Energy Advisors Review

Energy advisors do not need the technical benchmark report.

For the manual readiness checklist, use:

```text
evaluation/READINESS_CHECKLIST.md
```

It summarizes the review areas for clarification, building identification,
building facts, combined advice, routing, multi-turn memory, missing data,
out-of-scope requests, hallucination traps, stress cases, transparency, and
handover. Keep exact prompts and private examples in the JSONL cases, not in
Markdown docs.

Pick a small set of representative SPARA dialogues, usually 8-12, and ask
energy advisors to judge advisory quality:

1. Is the answer technically correct? 1-5
2. Is it useful for the homeowner or BRF? 1-5
3. Is it clear and actionable? 1-5
4. Would you use it?
   - yes, as-is
   - yes, with minor edits
   - only with major edits
   - no
5. What should be corrected?

The detailed advisor review sheet can be generated with:

```bash
python evaluation/scripts/run_benchmark_suite.py --export-advisor-sheet
```

Live app advisor reviews are stored through:

```text
POST /evaluation/advisor-review/
GET /evaluation/export/?format=jsonl
GET /evaluation/export/?format=csv
```

## Role Split

- Demo scenario run: checks that the system behaves sensibly.
- Developers/researchers: inspect routing, grounding, latency, safety, and failures.
- Energy advisors: judge correctness, usefulness, clarity, and whether edits are needed.
- BRF/users: provide realistic questions and simple ratings/comments.

## Files

- `data/evaluation_cases.jsonl`: the small demo scenario set.
- `scripts/run_benchmark_suite.py`: one-command run, report, optional email.
- `scripts/run_eval_cases.py`: direct AgentRouter scenario runner.
- `scripts/analyze_eval_results.py`: metrics summary.
- `scripts/generate_benchmark_report.py`: Markdown report for email/demo.
- `scripts/export_advisor_review_sheet.py`: blank review sheet for advisors.
- `forms/advisor_review_template.csv`: rubric columns.
- `PROTOCOL.md`: short human-evaluation protocol.
- `READINESS_CHECKLIST.md`: manual readiness areas and expected behavior.
