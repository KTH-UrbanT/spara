# SPARA advisory framework and ODEN evidence map

Reviewed: 2026-09-17. This document separates published Swedish guidance,
repository observations, and proposed SPARA behavior. It is a design and review
reference, not proof of live service availability or advisor approval. Executable
prompts and exact regression expectations belong in `data/evaluation_cases.jsonl`.

## Scope

Use BRFs and apartment buildings as the working scope for this improvement.
The current welcome text explicitly describes helping BRFs and energy advisors
(`llm-service/src/pipeline/agent_router.py`, `_fast_conversational_response`), and the building
flow resolves BRFs to buildings. General energy explanations do not require
identity. A general buildings description in the root README is not evidence of
a separately validated single-family-house advisory flow.

If housing type is unknown and materially changes the answer, clarify it before
giving type-specific recommendations. Do not ask again when a BRF/apartment
building is already established. Expanding the product to single-family houses
needs an explicit scope decision and separate evaluation; it is not silently
included in this change.

## What the Swedish guidance supports

The sources below provide the technical and organizational foundation. They do
not prescribe a chatbot script or prove how every advisor conducts a meeting.

| Published guidance | Implication for SPARA |
| --- | --- |
| Municipal energy and climate advice is impartial guidance; the household, association, or business makes the decision. [Energimyndigheten: energy and climate advice](https://www.energimyndigheten.se/effektiv-energianvandning/hushall/energi--och-klimatradgivning/) | Explain options, prerequisites, and next checks. Do not claim to make the BRF's investment decision or endorse vendors. |
| Apartment-building guidance connects resident dialogue, operating measures, and technical measures, and considers indoor conditions alongside energy use. [Energimyndigheten: apartment buildings](https://www.energimyndigheten.se/effektiv-energianvandning/flerbostadshus/) | Discover whether the concern is comfort, consumption, cost, or maintenance. An energy figure alone does not establish the problem. |
| Reliable energy monitoring, maintenance, and adjustment of existing systems are central to operating improvements. Residential ventilation requires continuous air exchange; operating-hour reductions for premises cannot automatically be transferred to apartments. [Energimyndigheten: operating measures](https://www.energimyndigheten.se/effektiv-energianvandning/flerbostadshus/driftatgarder/) | Check actual conditions and operating evidence before proposing replacement. Never use reduced residential ventilation as an unconditional saving measure. |
| Building documentation should be gathered and kept current so owners understand systems and previous work. [Boverket: collect building documentation](https://www.boverket.se/sv/energiguiden/energieffektivisera-flerbostadshus/energiforvalta/samla-dokumentation/) | Use ODEN records as a starting point; ask about changes since the record and request documents only when their contents matter. |
| Energy measures should be considered in ongoing operation and coordinated with planned maintenance, such as roof or window work. [Boverket: energy in operation and maintenance](https://www.boverket.se/sv/energiguiden/energieffektivisera-flerbostadshus/energiforvalta/energi-i-drift-och-underhall/) | Ask about relevant planned work and timing before prioritizing a major measure. Avoid isolated technology rankings. |
| On-site condition assessment and energy mapping help establish the present condition, energy use, and possible measures. [Boverket: check condition](https://www.boverket.se/sv/energiguiden/energieffektivisera-flerbostadshus/energiforvalta/kontrollera-status/) | Distinguish a provisional recommendation from a confirmed diagnosis; identify when a measurement or professional inspection is the next useful step. |
| Suitable renovation depends on building-specific knowledge; existing documents, expert assessment, and proportionate investigation help establish technical conditions. [Boverket: technical prerequisites](https://www.boverket.se/sv/energiguiden/energieffektivisera-flerbostadshus/energirenovera/byggide/klarlagg-forutsattningarna/tekniska-forutsattningar/) | Explain the relevant interaction between systems in plain language and identify missing evidence before suggesting a specific intervention. |

## Proposed SPARA conversation workflow

This workflow is a product design derived from the guidance and the readiness
requirements. The one-or-two-question limit and output structure are SPARA design
choices, not quotations from the sources.

1. **Answer the direct question.** Explain what can be established immediately.
   A simple definition may need no follow-up. Do not withhold general help until
   an address, name, contact detail, or full questionnaire is supplied.
2. **Establish the objective.** Distinguish the requested technology or action
   from the desired outcome. If unclear, ask what prompted the question: comfort,
   increasing consumption, bills, condition, maintenance, or another concern.
   Treat possible underlying causes as hypotheses until supported.
3. **Use available context.** Reuse the selected building ID, ODEN facts, previous
   answers, and known constraints. Resolve a voluntarily supplied concrete BRF
   name. Clarify different building IDs before claiming building-specific facts.
4. **Ask a question that changes the next recommendation.** Usually ask one or
   two related questions per turn. Explain unfamiliar systems only as needed for
   the decision. Do not ask users to repeat available facts unless currentness or
   a conflict needs checking.
5. **Consider priorities conditionally.** Address the proposed measure, then
   explain any better-supported investigation or alternative. Follow the existing
   conservation, efficiency, and renewables hierarchy when relevant; do not force
   every category into every answer. Do not invent comparative savings.
6. **Agree on a practical next step.** State what to check, why it matters, who
   could do it, and what the result would help decide. Give a short prioritized
   plan only when the evidence supports it. Carry unresolved questions forward.
7. **Follow through.** A report request should produce a retrievable report or an
   explicit failure. An external handoff requires a preview of recipient and
   information, confirmation, and an accurate execution status. Generating text
   about an action is not completing the action.

### Investigation areas

These are investigation dimensions, not a mandatory interview checklist. Exact
test dialogues belong in the evaluation dataset.

| Initial topic | Important distinction | Evidence or follow-up that can change advice |
| --- | --- | --- |
| Rising heating bills | Changed consumption versus prices or charging structure | Comparable energy-use periods, invoice components, weather/context, and recent operational changes |
| Windows or insulation | Maintenance need versus discomfort versus energy use | Component condition, where/when discomfort occurs, relevant measurements, ventilation context, and planned renovation |
| Heating replacement | Supply technology versus demand or distribution problems | Existing heat source, energy-use breakdown, symptoms across apartments, operating settings, and scheduled maintenance |
| Ventilation changes | System type versus current functioning | Available system record, recent modifications, actual inspection text, airflow evidence, and indoor-condition concerns |
| Solar energy | Generation objective versus reducing building demand | Purpose, building electricity use, relevant roof plans and technical assessment; no roof-specific claims without evidence |
| A short priority plan | Potential measures versus feasible next decisions | BRF objectives, available budget constraint, timing, completed measures, data gaps, and dependencies |

Explain only the system relationship relevant to the decision. For example,
distinguish producing heat from distributing it through a building, or replacing
windows from understanding ventilation and comfort. A helpful explanation should
allow the user to understand why the next check matters; it should not become a
generic lesson pasted into every answer.

## ODEN capabilities observed in this repository

Evidence here comes from source inspection, without reading credentials or
calling ODEN. These are implemented client expectations, not a published ODEN
schema guarantee. Local fixtures cannot establish production coverage.

### Lookup and identity

`llm-service/src/database/sql_client.py` is an HTTP client despite its name.
`SQL_Mapper_Layer` calls this client; it does not execute SQL against ODEN.

| Operation | Implemented request | Limit or distinction |
| --- | --- | --- |
| BRF to addresses | `GET /brfs/addresses?brf_name=...` | Results are normalized to a list and locally sliced; the default limit is 100. A complete paginated BRF portfolio is not guaranteed. |
| Address lookup | `GET /buildings/address?address=...&case_sensitive=false` | Can return several rows/buildings. Location and identity need disambiguation. |
| Authoritative building ID | `byggnadsid` equality via `/buildings/single_filter`, with `/buildings/?byggnadsid=...` fallback in `buildings_by_building_id` | Distinguish this identifier from ODEN record UUIDs. Default limit is 50. |
| UUID lookup | `GET /buildings/{building_uuid}/` | `building_by_id` is an alias for this UUID operation, not proof that any supplied building identifier is a UUID. |
| Constrained filters | Single-filter and two-field AND queries | Only the explicitly allowed fields and operators are supported. Organization-number lookup is not a separate demonstrated endpoint here. |

The allowed filter fields are `byggnadsid`, `01a_fnr`, `50a_uuid`, `50a_deso`,
`epc_egennybyggar`, `epc_egenbyggnadstyp`, `epc_egenatemp`, `epc_egenantalplan`,
`epc_egenantaltrapphus`, and `epc_idadr`. Do not infer the meaning of every
identifier from its abbreviated name.

The building flow groups BRF address rows by building ID in
`_group_brf_address_rows`, preserves multiple candidate buildings, and selects
latest EPC rows per identity through `_select_latest_epc_rows_preserving_ambiguity`
in `llm-service/src/agents/building_flow_graph.py`. Several addresses for one ID
are aliases; different IDs require selection. The generic mapper separately has
address-first routing, so a retained address and an explicit ID should be tested
together before claiming identity handling is universally correct.

### Fields consumed and normalized

The following mappings are implemented in
`llm-service/src/pipeline/safety_analysis.py` (`_derive_fact_aliases`). Availability
and exact definitions still depend on the actual ODEN record.

| Context | Examples of consumed fields | Interpretation limits |
| --- | --- | --- |
| Identity/location | `byggnadsid`, `50a_uuid`, `epc_idadr`, postal-town/municipality/postcode aliases | Retain identifier type and source. An address does not establish uniqueness. |
| Building characteristics | `epc_egennybyggar`, `epc_egenbyggnadstyp`, `epc_egenatemp`, floor and staircase counts | The UI formats Atemp as m2; this is a local unit assumption, not metadata checked against a remote schema. |
| Heating | `epc_huvudsakliguppvarmning_calc`, `epc_egifjarrvarme`, space-heating and hot-water subfields | Heating type can be inferred from district-heating values; distinguish that inference from an explicit field. |
| Ventilation | `epc_venttypftx`, `epc_venttypft`, `epc_venttypfmed`, `epc_venttypf`, `epc_venttypsjalvdrag` | The helper chooses the first affirmative type. It does not establish current performance or exclude mixed systems. |
| Energy class/performance | `epc_egienergiklass2020_calc`, `epc_egienergiklass2016_calc`, `epc_egienergiprestanda`, primary-energy and specific-energy fields | The previous alias fallback could conflate these metrics; the current change leaves declared performance missing when only primary/specific energy exists. Retain raw fields and their provenance; a calculated class is not automatically a declared class. |
| Electricity/heat | `epc_el_calc`, `epc_egisumma2`, `epc_egifastighet`, district-heat fields | Local answers format annual values as kWh/year. Verify the raw field's scope, unit, and period before comparisons or calculations; these aliases are not all interchangeable meter readings. |
| Record timing | `epc_godkand`, `epc_egiversion`, declaration-year aliases | Helpers infer a year and choose the latest record. A version value is not necessarily a measurement period. |

`src/config/schema.json` describes a separate `dbo` SQL schema with tables such
as `buildingaddress`; it must not be presented as the authoritative ODEN schema.
The specialized Hammarby dataset and vector documents are separate sources.

### Missingness, freshness, and provenance

- `extract_retrieved_facts` flattens scalar values and keeps the first present
  value for a key. It drops null/empty fields and skips document hits. This is
  convenient context packing, not a field-by-field provenance record.
- Zero and false values should remain meaningful. Sentinel strings and
  ambiguous source conventions need validation before they become facts.
- `compute_data_freshness` uses local age bands (up to 3 years, 4-7 years, older)
  and marks unknown dates. These bands are application heuristics, not legal
  validity or proof that equipment is unchanged.
- ODEN EPC fields do not establish the text of an energy declaration, OVK
  conclusions, audit recommendations, component condition, exact U-values,
  contractor prices, or current operating settings. Retrieve the actual document
  or identify the gap before asserting those details.
- The current client accepts lists, `results` envelopes, or individual objects;
  it does not automatically traverse `next` pages. Timeout/retry configuration
  exists, but exception retries are not proof of successful production recovery.
- The conversation must establish goals, current symptoms, recent work, budget
  constraints, board/maintenance timing, and decisions unless supplied evidence
  already contains them. Ask only what is relevant to the next decision.

For a future verified ODEN contract, retain raw field name, value, unit, period,
record date, record identifier, and whether the value is supplied or derived.
Confirm this against a documented schema or an authorized sanitized live sample.

## Conversation memory and evidence checks

The Redis manager retrieves the complete message list; generic answers consume
the provided history. Building answers previously used an eight-message excerpt
in `build_building_response_prompt`, so older user constraints could be absent
even while building facts persisted. Session snapshots and metadata preserve
identity/data, but their existence alone does not prove advisory memory.

Review the following behaviors with multi-turn cases: an early budget limit
survives later clarification; a completed retrofit is not recommended again;
the original question resumes after selecting a building; a correction supersedes
an earlier assumption; and switching buildings cannot reuse the previous
building's facts. Historical evidence and user corrections should remain distinct
until the discrepancy is resolved.

## Definition of useful advice

A successful advisory turn addresses the question, uses the evidence that is
available, and makes the next decision easier. It may be a short explanation, a
single diagnostic question, or a grounded plan. It need not contain every energy
category or a fixed number of bullets. When evidence is insufficient, the useful
output is a conditional recommendation and a specific way to reduce uncertainty.

Advisor review and production integration tests remain necessary. This document
does not claim that a live ODEN lookup, model call, report download, email send,
or professional review has succeeded.
