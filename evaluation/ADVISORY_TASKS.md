# SPARA advisory improvement tasks

Updated: 2026-09-20.

The local changes below address the advisory requirements and the confirmed
failure paths found during source inspection. **Implemented does not mean
runtime-verified or approved by an energy advisor.** At the user's request, no
tests, model calls, ODEN calls, report downloads, or email submissions were run
for this revision. Credentials were not changed.

| # | Task | Local outcome | Remaining validation or decision |
| --- | --- | --- | --- |
| 1 | Establish product scope | BRFs/apartment buildings remain the working scope; clarify housing type only when unknown and relevant. General advice has no identity requirement. | Confirm whether single-family-house support is wanted; it is not separately validated. |
| 2 | Understand energy advisory practice | [ADVISORY_FRAMEWORK.md](ADVISORY_FRAMEWORK.md) connects Swedish public guidance to objectives, diagnosis, system explanations, maintenance, priorities, and next steps. | Energy-advisor review of the proposed conversation behavior. |
| 3 | Find where useful advice is lost | Removed the building response validator that overwrote useful answers unless four fixed ECM sections appeared. Model failures now produce an explicit unavailable response. | Run focused response and failure regressions. |
| 4 | Use ODEN appropriately | Documented implemented endpoints/fields and their limits; separated declared performance from primary/specific-energy metrics; corrected the construction-year prompt mapping. Prompts distinguish records, user reports, documents, and inference. | Verify remote field meanings, units, dates, coverage, and representative records against the actual ODEN contract. |
| 5 | Discover the underlying objective | Generic and building prompts answer the direct question, then explore the reason for the proposed measure when it affects the advice. | Review whether follow-ups distinguish symptoms, cost, consumption, and maintenance without assuming a diagnosis. |
| 6 | Ask useful follow-up questions | Prompts ask one or two relevant questions, reuse supplied facts, and avoid mandatory questionnaires or identity gates for general help. | Review multi-turn diagnostic conversations. |
| 7 | Explain relevant technical systems | Prompts connect plain-language system explanations to the user's decision and avoid unrelated building profiles. | Check technical correctness with an advisor. |
| 8 | Reconsider priorities using evidence | Prompts require rationale, dependencies, missing evidence, and practical next checks; alternative priorities remain conditional without supporting evidence. | Judge prioritization quality and the conservation/efficiency/renewables hierarchy in representative cases. |
| 9 | Preserve objectives and constraints | Building/report prompts retain supplied conversation history; generic retrieval adds recent user context for recognized follow-ups; the latest user message is not duplicated in the generic model input. | Run longer conversations, corrections, and building-switch cases; retrieval coverage for other short replies remains limited. |
| 10 | Make report generation honest and useful | Report generation preserves objectives, prioritizes current building identity, excludes identified other-building snapshots, creates an expiring artifact when storage succeeds, labels basic fallback summaries, and returns copyable text if storage fails. Missing session history is disclosed. | Verify generation and authenticated download with the deployed Redis/message service, including expiration and building changes. |
| 11 | Make advisor handoff explicit and reliable | Actual recipient/CC, summary, and attachment scope are previewed; matching confirmation is required. Submission is deduplicated and statuses distinguish pending, simulated, submitted, failed, disabled, cancelled, and uncertain. The UI does not infer successful sending from prose. | Verify configured SMTP behavior with authorized recipients. SMTP acceptance is not inbox-delivery confirmation. |
| 12 | Make advisory quality reviewable | Updated [READINESS_CHECKLIST.md](READINESS_CHECKLIST.md), added seven advisory cases and focused unit regressions, and separated keyword checks from required advisor review in results, metrics, reports, and CSV export. | User runs the tests and evaluation cases; advisors score the resulting conversations. No fresh pass rates are claimed. |

## Confirmed failure locations and changes

- `llm-service/src/agents/building_flow_graph.py`: a successful focused answer or
  diagnostic question could be replaced with a generic ECM template. Success is
  preserved; error/empty responses are handled explicitly.
- `llm-service/src/agents/building_response_prompt.py`: truncating history to eight
  messages dropped earlier objectives and constraints. All supplied history now
  reaches the response prompt.
- `llm-service/src/agents/generic_agent.py`: short follow-ups were retrieved in
  isolation and reference placement duplicated the current user turn. Relevant
  recent user context is used for recognized follow-ups and the turn appears once.
- `llm-service/src/pipeline/safety_analysis.py`: missing declared performance could
  be filled with a different energy metric. The metrics now remain separate.
- `llm-service/src/services/draft_report_service.py`: storage failures, unavailable
  report generation, and missing history now have distinct, truthful outcomes.
- `llm-service/src/pipeline/agent_router.py` and
  `llm-service/src/services/expert_handoff_email.py`: explicit email requests now
  enter preview/confirmation; retries, recipient refusal, uncertain submission,
  and service unavailability have defined outcomes.
- `llm-service/src/pipeline/evaluation_metadata.py`,
  `message-service/service/public_messages.py`, and the chat components: safe
  status fields reach the UI without publishing private preview data.
- `evaluation/scripts/`: keyword matches no longer mark the new semantic advisory
  criteria as passed. Report artifact/status details are retained for review.

## Validation handover

The September 20 test update adds coverage for real confirmation/cancellation
parsing, changed preview contents and CC, in-flight duplicate submissions,
lost submission-result storage, malformed conversation entries, combined report
model/storage failures, actual artifact expiry, public status propagation, and
evaluation-runner review contracts. Handoff unit tests use isolated Redis/SMTP
substitutes and do not load local credentials. These tests were written and
statically reviewed, not executed. Runtime validation remains pending.

Reports require the LLM service and message service to use the same Redis store
and `DRAFT_REPORT_KEY_PREFIX` (default `draft_report`). The configured
`DRAFT_REPORT_TTL_SECONDS` determines expiry (default 1800 seconds).

Email handoff uses the existing `EXPERT_EMAIL_SMTP_SERVER`,
`EXPERT_EMAIL_SMTP_PORT`, `EXPERT_EMAIL_ACCOUNT`, `EXPERT_EMAIL_ADDRESS`,
`EXPERT_EMAIL_PASSWORD`, and `EXPERT_EMAIL_RECIPIENT` settings.
`EXPERT_EMAIL_ENABLED=false` explicitly disables submission. Without complete
configuration, the chatbot provides a copyable summary. No values were changed.

Regression fixtures are provided for the user to execute with a working local
environment. [README.md](README.md) describes the evaluation commands. The new
`ADVISORY_01...` through `ADVISORY_07...` cases cover underlying objectives,
cost-versus-consumption reasoning, memory, focused ODEN-grounded advice,
conditional reprioritization, reports, and handoff preview/cancellation.

Use evaluation mode for model-driven scenario runs when email must be simulated;
it still uses the configured model/retrieval services. Any real email test needs
an intended recipient and the normal preview/confirmation flow. Historical result
files are baseline evidence only and have not been regenerated for this revision.

Pending runtime checks and advisor approval remain open. Source review cannot
establish zero errors, deployed service availability, or advisory quality.
