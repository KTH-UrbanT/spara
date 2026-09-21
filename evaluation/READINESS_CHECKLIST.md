# SPARA Readiness Checklist

Use this checklist for manual review of SPARAbot behavior before demo or advisor
review. Keep concrete user transcripts, reviewer names, personal names, private
emails, and one-off chat excerpts out of this Markdown file. Put executable
test prompts and exact regression contracts in `data/evaluation_cases.jsonl`.

## Product Rules

- The current implementation and this checklist focus on BRFs/apartment buildings.
  Single-family-house coverage remains a product-scope decision. If both are
  supported, establish building type when it is not already clear; do not ask
  again when the user or a resolved building record has supplied it.
- Answer the direct question as far as the evidence allows, then investigate the
  need behind it when that could change the recommendation. A proposed technology
  is not proof of the user's objective or of the best solution.
- Use ODEN API records for resolved building facts and ask the user about goals,
  symptoms, recent changes and practical constraints that those records do not
  establish. Do not ask again for reliable information already available.
- Building identity is the building ID / `byggnadsid`. Street addresses are
  lookup aliases. If several addresses map to one building ID, SPARA should use
  that building ID and not force the user to pick one address. If addresses map
  to different building IDs, SPARA should ask the user to choose the correct
  building, entrance, address, or building ID.
- Heating-cost, energy-efficiency, retrofit, optimization, and priority-setting
  questions are Energy Conservation Measures (ECM) questions. These can be
  generic or building-specific:
  - If the building is known, SPARA should provide prioritized ECMs grounded in
    known facts.
  - If the building is unknown and the user asks broad advice, SPARA should give
    general low-regret ECM guidance and offer to personalize it with a BRF name,
    address, or building ID.
  - If the user voluntarily provides a concrete BRF name, SPARA should try to
    resolve that BRF to building ID(s). If it resolves to one building ID, answer
    building-specifically; if it resolves to multiple building IDs, ask the user
    to choose; if it is not found, ask for an address/building ID and avoid
    claiming building-specific facts.
  - If the user asks for personalized prioritization or the building's own facts,
    SPARA should ask for identity instead of guessing.
- SPARA should not require a user name, contact details, BRF name, address, or
  building ID for general energy advice. Identity is optional unless the user
  asks for building-specific facts, database values, documents, calculations, or
  tailored prioritization. If the user already provides a concrete BRF name,
  use it as an optional identifier rather than ignoring it.
- SPARA must not invent energy-declaration text, energy-audit measures, OVK
  conclusions, exact U-values, vendors, prices, legal outcomes, or guaranteed
  savings.
- Handover behavior must never be silent. If advisor handoff is enabled, SPARA
  must explain what will be sent and ask for confirmation before sending. If it
  is not enabled, SPARA should provide a copyable summary and tell the user how
  to contact an appropriate advisor.

## Review Areas

### Advisory Conversation

- Give a useful direct answer before follow-up questions whenever possible.
- Ask one or two questions at a time that could materially change the next step;
  avoid a compulsory questionnaire or an address gate for general advice.
- Distinguish the proposed measure from the underlying objective and symptoms.
  Do not invent hidden problems or claim another measure saves more without evidence.
- Explain the relevant interaction of heating, ventilation, controls and the
  building envelope in plain language when it helps the user decide.
- Use the advisory hierarchy to reason about priorities. A focused answer or
  diagnostic follow-up does not need all hierarchy headings or a fixed bullet count.
- Explain why a measure fits, what must be checked first, and what would change
  its priority. Respect requested scope and distinguish an investigation from an
  investment recommendation.
- Finish with an actionable next step or a targeted question. Revise advice when
  new evidence or constraints arrive instead of repeating a broad list.

### Clarification And Building Identification

- Unknown BRF/building: ask for a BRF name, address, organisation number, or
  building ID before giving building-specific facts. Do not require identity
  before answering broad/general energy-advice questions.
- Ambiguous address: ask for city, postcode, municipality, BRF, or building ID
  before selecting a record.
- Multiple addresses: map addresses to building records and use building ID as
  the source of truth.
- Multiple candidate buildings: ask the user to select by number, address, or
  building ID.
- Explicit building ID: accept it as authoritative when it maps to a valid
  building and continue the original request.

### Building-Specific Facts

- Resolve ODEN records to the selected building ID before using them. Document
  which fields actually exist; do not infer an audit or OVK report from EPC data.
- Compare newer user-reported changes with the date of the ODEN record. Preserve
  both sources and state the uncertainty until verified.
- Return values with units, date or period, and source where available.
- Distinguish declared, calculated, and measured energy values.
- State when facts are missing instead of guessing.
- Preserve the selected building across follow-up questions.

### Energy Conservation Measures

- Use building context when available.
- Prioritize measures with rationale, dependencies, and next checks.
- Avoid guaranteed savings and exact payback claims unless supported by an
  explicit calculation with stated assumptions.
- Provide general low-regret advice when building identity is still missing and
  the user has not explicitly asked for personalized building prioritization.
- Follow the advisory hierarchy in answers: energy conservation/reduce demand,
  then energy efficiency/improve systems and controls, then renewable energy.

### Routing

- General explanations should stay generic and avoid "your building" claims.
- A user saying "we", "our BRF", "our roof", or "our heating bills" does not by
  itself force building-specific routing. Broad advice should stay generic and
  invite the user to share identity for tailored advice.
- A concrete BRF name such as "BRF Sjöstaden 1" is an identity signal. SPARA
  should try to resolve it to building ID(s) before asking for an address.
- Questions asking for the user's own facts, exact database values, documents,
  declarations, OVK/audit findings, or calculations should enter
  building-specific or clarification flow.
- A concrete street address or building ID should enter building-specific flow.
- Requests for energy advice or recommended measures are core advisory intent,
  not handoff intent.
- Handoff should only happen when the user asks for forwarding, contact, or
  advisor escalation, or when a safety boundary requires it.

### Multi-Turn Behavior

- Carry building identity, facts, and constraints across turns.
- Preserve the original objective and earlier constraints through longer
  conversations. Follow-up retrieval must retain enough context to resolve
  references to earlier questions.
- Recover when the user corrects a mistaken handoff or route.
- Incorporate new constraints instead of restarting the conversation.

### Missing Data And Contradictions

- Validate user claims against available data.
- Explain matching logic when an address or building identity conflicts with a
  previous answer.
- Label estimates clearly and never present typical ranges as exact values.

### Boundaries

- Decline threatening legal drafting, financial guarantees, vendor endorsement,
  specific pricing, and investigative accusations.
- Offer safer alternatives such as documentation steps, neutral summaries,
  quote-comparison criteria, or professional consultation.

### Hallucination Traps

- Quote documents only when document text is available.
- List audit or OVK findings only when those reports are available.
- Separate database fields from document excerpts and from model inference.

### Robustness

- Do not promise timing guarantees.
- Constrain unsupported batch requests.
- Do not time out on common clarification cases such as multiple-address
  questions without actual address values.

### Transparency And Handover

- Explain sources used and what was inferred.
- Acknowledge uncertainty and possible errors.
- Before any handoff, state what will be sent and ask for confirmation.
- Show the actual recipient(s), summary and scope of attached conversation/data
  before confirmation. A direct request to email is not confirmation of a preview
  the user has not yet seen.
- Keep disabled, cancelled, pending, failed, uncertain and submitted states clear.
  SMTP acceptance means submitted; do not claim confirmed inbox delivery.
- Do not duplicate a submission when a confirmation is repeated or retried.
- Provide a copyable summary if sending is unavailable or fails.

### Draft Reports

- Return a working download artifact or an explicit failure with a copyable draft
  when possible. Do not describe an unavailable artifact as successfully generated.
- Include the user's objective and constraints, building identity, available ODEN
  and document evidence, provisional priorities, missing data and next steps.
- Clearly label a report assembled without model-generated analysis and state its
  limitations. Use the actual artifact expiry rather than a hard-coded promise.

## Scoring

- Automated keyword checks are smoke checks, not proof of advisory quality.
  Cases requiring interpretation, diagnostic questioning or reprioritization
  require advisor review even when their keyword checks pass.
- `V` = pass: meets expected behavior.
- `~` = partial: some expected elements are missing, weak, or unclear.
- `X` = fail: violates expected behavior, fabricates information, or behaves
  unsafely.

## Review Notes Template

```text
ID:
Test date:
Reviewer:
Category:

Context:
- Building context:
- Building ID:
- Data source:

Expected behavior:
Observed route:
Answer summary:

Result (V / ~ / X):
Severity:
Failure type:
Groundedness:
Needs human escalation? (Yes/No):

Comments:
```
