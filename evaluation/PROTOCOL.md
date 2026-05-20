# SPARA Evaluation Protocol

This protocol is the lightweight version for the demo and near-term advisor
review. It avoids mixing the full computer-science paper plan with the practical
question: does SPARA produce useful, safe advisory answers?

## Goal

Evaluate SPARA as a support tool for energy advisors and BRF/homeowner users.
SPARA is not evaluated as a replacement for EKR advisors.

Main question:

```text
Can SPARA answer common advisory questions accurately enough to support users
and help advisors review or reuse the response?
```

## Track 1: Demo Scenario Run

Purpose: catch obvious system problems before or after pushing to demo.

Run 20-30 scripted scenarios covering:

- generic energy-advice questions
- building-specific questions with an address
- missing-address questions
- multi-turn clarification conversations
- out-of-scope questions
- handoff/report cases if relevant

For each turn, record:

- user question
- expected route
- expected behavior
- actual route
- SPARA answer
- retrieved building data or sources when available
- safety/grounding flags
- latency and failures

Command:

```bash
python evaluation/scripts/run_benchmark_suite.py --email-report
```

Output:

- emailed `benchmark_report.md`
- raw JSONL results
- metric summary

This is the developer/researcher check.

## Track 2: Energy Advisor Review

Purpose: understand whether answers are useful and trustworthy in advisory work.

Advisors should review only a small, curated set of dialogues. They do not need
to inspect technical details like tokens, latency, baselines, or F1 scores.

Recommended size:

- 8-12 dialogues for Hans/EKR review
- include at least one generic, one building-specific, one missing-info, one
  multi-turn, and one boundary/out-of-scope case

Advisor rubric:

| Question | Scale |
| --- | --- |
| Is the answer technically correct? | 1-5 |
| Is it useful for the homeowner or BRF? | 1-5 |
| Is it clear and actionable? | 1-5 |
| Is the answer trustworthy and sufficiently justified? | 1-5 |
| Would you use it? | as-is / minor edits / major edits / no |
| What should be corrected? | free text |

Optional issue tags:

- wrong building
- wrong or missing data
- wrong document/source
- unsupported claim
- too vague
- too technical
- should have asked for clarification
- should have escalated

This is the energy-advisor evaluation.

## Track 3: Later Research Benchmark

Keep this separate from the demo/advisor workflow.

Use it only when preparing a computer-science style result:

- compare SPARA against LLM-only, RAG-only, SQL-only, and ablated systems
- measure routing accuracy, retrieval accuracy, grounding, latency, cost, and
  failure rate
- report ablations such as no router, no SQL, no vector retrieval, and no
  clarification

This is not required for the immediate demo evaluation.

## What Counts As Done For Demo

Demo evaluation is done when:

- the script runs successfully on the chosen scenario set
- the email report is received
- route mismatches and failed turns are visible
- the report includes SPARA answers next to expected behavior
- a small advisor-review set is selected from the results

## What Counts As Done For Advisor Review

Advisor review is done when:

- Hans/EKR have reviewed the selected dialogues
- each reviewed answer has correctness/usefulness/clarity scores
- each reviewed answer is marked as as-is, minor edit, major edit, or no
- important corrections are captured in free text
- recurring issues are summarized for the next SPARA iteration

## Timeline

| Date | Milestone |
| --- | --- |
| May 20, 2026 | Clean protocol and demo run flow ready |
| May 25, 2026 | Internal pilot with colleagues |
| June 1, 2026 | External/user testing starts |
| June 15, 2026 | Reminder and Hans/EKR review material |
| June 20, 2026 | Test closes |
| July 1, 2026 | Rough analysis complete |
