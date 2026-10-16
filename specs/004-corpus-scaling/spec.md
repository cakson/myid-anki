# Feature Specification: Corpus Scaling

**Feature Branch**: `feature/004-corpus-scaling`

**Created**: 2026-10-15

**Status**: Draft

**Input**: Grow the Indonesian ↔ Malaysian Malay learner corpus through repeatable, coverage-led batches using closed Feature 003 v3.1. The first implementation milestone is exactly one new 100-candidate production batch.

## Clarifications

### Session 2026-10-15

- Q: How should each batch's category allocation be chosen? → A: Generate a coverage-based draft that the maintainer can adjust before the batch starts.
- Q: Should a batch be marked complete before its random-QA monitoring sample has been reviewed? → A: Close the batch after random QA is complete; promotion can happen earlier.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plan and produce a useful batch (Priority: P1)

A corpus maintainer reviews current and historical vocabulary coverage, chooses underrepresented everyday concepts, and runs a bounded batch through Feature 003 curation. Proposal waste is visible, and admitted candidates teach useful differences rather than inflate the deck.

**Why this priority**: More suggestions help only if they address coverage gaps and teach real contrasts.

**Independent Test**: Plan and curate a batch against the 137-card baseline and historical candidates; inspect its coverage plan, candidate identities, and decisions without promoting cards.

**Acceptance Scenarios**:

1. **Given** the baseline corpus and candidate history, **when** the first batch is planned, **then** it presents a coverage-based category draft that the maintainer can adjust before starting and records the final targets, selection rationale, and request for 100 distinct new candidates.
2. **Given** a proposal that repeats an existing concept under another English label or inflection, **when** it is screened, **then** its prior concept is linked and it receives no new permanent ID.
3. **Given** a common concept with no useful cross-language contrast, **when** v3.1 evaluates it, **then** it is rejected as `same` and counted separately as generation waste.
4. **Given** eligible concepts, **when** candidates are selected, **then** common `different-common-word` concepts take priority, followed by useful `similar` and valuable `false-friend` concepts, subject to category gaps and v3.1 gates.

---

### User Story 2 - Resume and safely promote (Priority: P1)

A maintainer resumes interrupted generation, evidence work, audit, correction, promotion, or export. Completed work remains attached to the same candidate IDs. Only currently eligible resolved candidates enter the canonical corpus, and the resulting deck keeps stable Anki identities.

**Why this priority**: Large batches must survive ordinary failures without duplicate concepts or manual artifact repair.

**Independent Test**: Interrupt a batch at each stage, resume it, and compare identities, decisions, learner-source changes, and deck output with an uninterrupted equivalent.

**Acceptance Scenarios**:

1. **Given** a partially completed batch, **when** work resumes, **then** completed valid stages are reused and no completed candidate is regenerated.
2. **Given** a model or retrieval failure, **when** the batch resumes, **then** affected candidates remain pending under their existing IDs and no partial result enters learner content.
3. **Given** unresolved required audit or correction, **when** promotion is attempted, **then** guarded promotion withholds the candidate and records why.
4. **Given** eligible candidates, **when** promotion and deck generation run or rerun, **then** each enters learner source once using final verified relation and resolved cue, while existing IDs and GUIDs remain stable.

---

### User Story 3 - Monitor quality and operating cost (Priority: P2)

A maintainer reads a reconciled batch report that separates production from required risk audit and random QA. It shows yield, category coverage, review cost, quality findings, and any safety brake.

**Why this priority**: Sustainable growth depends on visible useful yield, residual errors, and bounded review work.

**Independent Test**: Inspect a completed or paused report and reconcile every candidate with its decision, promotion status, quality findings, and measured or unavailable cost.

**Acceptance Scenarios**:

1. **Given** accepted, held, rejected, and duplicate proposals, **when** a report is produced, **then** all counts reconcile and production time is distinct from audit time.
2. **Given** clean otherwise eligible cards, **when** a random-QA sample is selected, **then** nonsampled cards can still be promoted and later findings remain traceable.
3. **Given** a batch with a pending random-QA sample, **when** a maintainer requests final closure, **then** closure waits for sample review while otherwise eligible promotion may proceed.
4. **Given** a safety-brake trigger, **when** promotion is attempted, **then** the unpromoted remainder pauses until investigation and an explicit disposition are recorded.
5. **Given** a repeated quality issue, **when** a batch closes, **then** the pattern and affected concepts are recorded without automatically changing v3.1.

### Edge Cases

- A cue has multiple senses: preserve the intended sense or withhold; matching words alone do not prove matching concepts.
- Identical written forms can still be a false friend; form equality alone must not discard a genuine meaning contrast.
- A previously rejected `same` concept returns under a new label; link its history unless a materially distinct sense is documented.
- A near-duplicate is found after curation or promotion; prevent a new identity from entering the corpus or correct an existing card under stable identity.
- Model, evidence, audit, or export fails midway; keep completed records, leave affected work pending, and never treat failure alone as linguistic REJECT.
- The requested 100 candidates cannot be found within declared proposal limits; record a shortfall rather than pad with low-value concepts.
- Random QA finds an error after some promotion; correct affected content and apply a safety brake to the remainder if a trigger is met.
- No cards are promoted or timing is unavailable; report zero yield and unavailable throughput explicitly.

## Requirements *(mandatory)*

### Functional Requirements

#### Coverage and selection

- **FR-001**: The system MUST maintain an inspectable coverage inventory of canonical and relevant historical candidate concepts, grouped by semantic area and identifiable sense.
- **FR-002**: Every batch MUST offer a coverage-based draft category allocation that the maintainer can adjust before starting. The final plan MUST document underrepresented everyday areas, category allocation, selection rationale, exclusions, and any adjustment. Category sizes MAY differ; repeated concentration in represented areas MUST have a stated reason.
- **FR-003**: Selection MUST favor practical contrastive value: common `different-common-word`, useful `similar`, then valuable `false-friend`, subject to category gaps. Obscure or specialist vocabulary MUST require deliberate selection while common gaps remain.
- **FR-004**: Before assigning a new permanent concept ID, proposal screening MUST check canonical and historical candidates for exact cues, semantic equivalents, alternate labels, singular/plural variants, near-synonyms teaching the same contrast, and prior no-contrast rejections. A distinct sense MAY proceed only with a recorded distinction.
- **FR-005**: A batch MUST record proposed, screened-out, and admitted counts separately. The first production run MUST target exactly 100 distinct admitted new candidates in one batch; if it cannot reach 100 within declared proposal limits, it MUST stop with a documented shortfall.

#### Lifecycle and continuity

- **FR-006**: Every batch MUST have a persistent inspectable manifest with batch ID, generation timestamp, strategy/version, requested count, source/category plan, proposal and candidate IDs, decision history, audit requirements/findings, corrections, promotion status, promoted/withheld/rejected counts, and available performance measurements.
- **FR-007**: The batch lifecycle MUST distinguish planning, proposal screening, generation, v3.1 curation, required risk audit, correction/withholding, guarded promotion, deck build, QA monitoring, and metrics update, each with inspectable status. Final batch closure MUST wait for the declared random-QA sample to be reviewed and reflected in the final report; eligible promotion MAY occur earlier.
- **FR-008**: Work MUST resume safely after interruption or failure at any stage: reuse completed valid work and stable IDs, avoid regeneration or duplicate permanent concepts, and keep incomplete or failed work outside learner content.
- **FR-009**: Each candidate MUST reconcile to one current decision or pending state and, if accepted, to audit requirement, correction status, and promotion disposition. Earlier decisions and corrections MUST remain inspectable.

#### Curation, QA, and brakes

- **FR-010**: All candidates MUST use closed Feature 003 production policy v3.1, including validation, independent verification, duplicate and `same` rejection, eligible relation rules, strict false-friend gates, confidence/review metadata, targeted evidence, and required risk audit. Individual imperfect cards alone MUST NOT change that policy.
- **FR-011**: Required risk-selected independent audit MUST clear before promotion. Unresolved, unsafe, or withheld findings MUST block the affected candidate.
- **FR-012**: Each scaled batch MUST select a reproducible random-QA monitoring sample from otherwise clean accepted candidates across confidence/risk strata. For the first batch, sample the greater of 5 or 10% of that population, capped by its size; record the selection basis and actual count. Random QA MUST NOT be a universal pre-promotion gate or be presented as proof that unsampled cards are correct.
- **FR-013**: QA records MUST distinguish learner-critical answer errors, cue/content corrections, and metadata-only corrections, with affected concepts, discovery stage, action, and correction history. Repeated error categories MUST be reported.
- **FR-014**: A batch MUST declare safety-brake thresholds before work begins. In the first batch, pause promotion of the unpromoted remainder for any identity/export inconsistency; two learner-critical audit/QA errors; the same new learner-critical failure pattern on two candidates; HOLD above 30% of curated candidates; no-contrast above 30% of screened proposals; or duplicate/redundancy above 20% of screened proposals. Record investigation and explicit resume/withhold disposition. Metadata-only corrections alone MUST NOT trigger a brake.

#### Promotion and measurement

- **FR-015**: Promotion MUST use Feature 003 current guarded eligibility and final resolved learner content. Withheld, rejected, unresolved, `same`, or unpromoted safety-braked candidates MUST stay outside canonical source. If a promoted card gains an unresolved material finding or a current HOLD/REJECT, the workflow MUST guardedly withdraw its row while retaining its permanent ID assignment, provenance, and correction history; a later correction may restore that same ID only through current guarded eligibility. Random-QA selection alone MUST NOT block an otherwise eligible card.
- **FR-016**: Promotion and rebuild MUST preserve existing permanent IDs, Anki GUIDs, deck/model identity, one-concept/one-note/one-card behavior, provenance, and correction history. Deck builds MUST remain deterministic and offline from reviewed source.
- **FR-017**: Every batch report MUST reconcile requested, proposed, screened-out, admitted, curated, promotable, active promoted, withdrawn, withheld, rejected, and pending counts, plus category and final relation distributions. Promoted yield MUST use active newly promoted candidates divided by admitted candidates; proposal waste MUST also be shown. Ever-assigned IDs MUST be reported separately from active corpus growth.
- **FR-018**: Every report MUST show ACCEPT/HOLD/REJECT, fast-path/escalated counts, confidence tiers, risk-audit and random-QA selected/completed/findings, learner-critical and metadata-only corrections, and blockers. Production throughput and audit cost MUST be separate.
- **FR-019**: Where measured, reports MUST show generation, production decision, risk-audit, random-QA, promotion/build, and end-to-end time; model calls, tokens, retrievals, and promoted cards per hour with a clear denominator. Missing or incomparable measurements MUST be marked unavailable.
- **FR-020**: Longitudinal reporting MUST show learner-critical corrections per 100 promoted cards, post-promotion corrections, random-QA discoveries, repeated error categories, HOLD, REJECT, no-contrast, and duplicate-generation rates with counts and denominators. Systematic issues MUST be recorded for improvement without automatically reopening Feature 003 for isolated errors.
- **FR-021**: The first implementation milestone MUST execute exactly one new 100-candidate batch, complete required audits and corrections, promote eligible cards, build the deck, and report reliability, resumption, redundancy control, promotion, yield, audit burden, random-QA findings, cost, coverage change, and repeatability. It MUST NOT start a second batch automatically.

### Key Entities *(include if feature involves data)*

- **Coverage inventory**: Current and historical concept/sense representation by semantic area, including gaps and no-contrast history.
- **Batch plan**: Requested count, coverage-based draft and final category allocation, maintainer adjustments and rationale, proposal limits, QA strategy, and brake thresholds.
- **Batch manifest**: Persistent batch identity, strategy/version and timestamp, candidate lineage, stage status, outcomes, and measured cost.
- **Proposal and candidate**: Intended concept/sense, screening result, category, admitted candidate ID, and links to equivalent historical concepts.
- **Production and audit record**: v3.1 decision, relation, risk/confidence, evidence, audit requirement, finding, correction, and current eligibility.
- **Promotion record**: Final resolved content, permanent concept ID, eligibility, source inclusion or withholding, provenance, and correction lineage.
- **Quality and operations report**: Reconciled counts and denominators, coverage change, timing/usage, findings, and brake disposition.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The first run records one category plan and exactly 100 distinct admitted new candidates, or stops with an explicit shortfall after declared proposal limits; no second production batch starts automatically.
- **SC-002**: In seeded exact-cue, alternate-label, plural, near-synonym, historical-candidate, and prior `same` cases, 100% are identified before a new permanent concept ID is assigned unless a distinct sense is documented.
- **SC-003**: All first-batch candidates have recoverable status and decision lineage; interruption and resumption at generation, evidence, audit, correction, and export produce zero duplicate concepts or unintended learner-source changes.
- **SC-004**: Zero ineligible, unresolved, rejected, or safety-braked candidates enter canonical content; all promoted cards use final verified relation and cue; existing IDs and Anki GUIDs remain unchanged on rebuild.
- **SC-005**: The first report reconciles all candidate outcomes and shows proposal waste, promoted yield, audit workload, random-QA findings, category coverage change, and measured or unavailable end-to-end cost separately from production decision cost.
- **SC-006**: The first batch closes only after its declared random-QA sample is reviewed and reflected in the final report, or records that no clean accepted candidates were available. Otherwise eligible cards are not delayed solely for random QA, and no quality guarantee is inferred for unsampled cards.
- **SC-007**: Every triggered safety brake pauses the unpromoted remainder and has an investigation and resume/withhold decision; metadata-only corrections alone trigger zero brakes.
- **SC-008**: After the first batch, a maintainer can identify represented and underrepresented categories, repeated quality issues, and next high-value coverage gaps from persistent records without reconstructing prior runs manually.
- **SC-009**: Growth progress is recorded from the 137-card baseline toward approximately 200+, 500, and 1,000 useful cards as planning milestones; none requires accepting a low-value or v3.1-ineligible concept.

## Assumptions

- Feature 003 is closed; v3.1 and guarded promotion are authoritative. A genuine blocking defect found during Feature 004 may be fixed with explicit evidence and compatibility review, without reopening policy experimentation.
- The first batch's 100 count means distinct admitted new candidates after proposal screening. Duplicate, redundant, and prior no-contrast proposals are generation waste and do not consume those slots. Proposal effort is bounded by a declared limit.
- The initial coverage taxonomy includes daily life, home, family/social interaction, food/cooking, shopping, clothing, transport, travel, school, work, communication, technology, health/body, emotions, common verbs/adjectives, time/date, directions/location, services, and basic finance/administration. Categories guide planning but are not equal-size quotas.
- The 137-card canonical corpus is the specification-time baseline. Approximately 200+, 500, and 1,000 cards are staged planning goals, not first-batch acceptance thresholds.
- Random-QA findings may arrive after promotion and lead to corrections under stable identity. Required risk audit remains a pre-promotion gate for selected candidates.
- Community contributions, learner feedback intake, images/audio, card redesign, identity changes, a new verifier research program, and an expert-human throughput benchmark are outside Feature 004.
