# Feature Specification: AI-First Vocabulary Curation

**Feature Branch**: `main`
**Created**: 2026-10-03
**Status**: Draft
**Input**: User description: "Build an AI-first vocabulary curation system for the Indonesian–Malaysian Malay Anki deck with independent verification, evidence, adversarial review, conservative acceptance, repeatable batches, and a meaningful initial corpus."

## Clarifications

### Session 2026-10-03

- Q: What minimum external evidence should an ordinary candidate have before automatic acceptance? → A: At least two independent, claim-relevant sources or signals support the key meaning and usage claims; unresolved disputes still block acceptance.
- Q: Should a false-friend card show the misleading lookalike and its actual meaning on the back? → A: Yes; show a concise, evidence-backed contrast on the back while keeping the front neutral.
- Q: What extra proof should a false-friend candidate need beyond the ordinary two-signal evidence gate? → A: Independent evidence must support each language's meaning and the misleading contrast, and separate verification and adversarial review must agree.

### Session 2026-10-05

- The learner deck is contrast-only. A concept whose normal Indonesian and Malaysian Malay forms have effectively identical spelling, meaning, and ordinary usage is excluded, even if it is frequent and well evidenced. `same` remains a curation classification for explaining rejection, not a learner relation. For example, `water → air / air` is excluded.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Curate a Trustworthy Batch (Priority: P1)

A maintainer selects a practical topic. AI discovers candidate concepts, researches usage in both languages, verifies proposed relations independently, challenges weak claims, and accepts only well-supported entries. Routine high-confidence entries do not require item-by-item human review.

**Why this priority**: AI is the main growth mechanism, so its quality gates protect learners from plausible but misleading claims.

**Independent Test**: Curate a bounded batch containing ordinary pairs, an unsupported usage difference, an ambiguous cue, a duplicate, and a suspected false friend. Inspect stage records, evidence, decisions, and accepted output.

**Acceptance Scenarios**:

1. **Given** a topic, **When** a batch is curated, **Then** generation, linguistic comparison, evidence checking, independent verification, adversarial review, duplicate review, and confidence decision are separately recorded before acceptance.
2. **Given** a claim supported only by its generating AI response, **When** quality gates run, **Then** the candidate is held or rejected and is absent from learner data.
3. **Given** credible evidence that both proposed words are normal in both languages, **When** a `different-common-word` claim is challenged, **Then** the relation is corrected if supported or withheld if unresolved.
4. **Given** a suspected false friend without strong independent agreement and evidence of a misleading meaning contrast, **When** its stricter gate runs, **Then** it is held or rejected.
5. **Given** accepted, held, and rejected candidates, **When** a batch closes, **Then** its report reconciles all outcomes and only accepted entries are eligible for release.

---

### User Story 2 - Study the Initial Library (Priority: P1)

An Indonesian or Malaysian learner studies useful vocabulary across practical categories and cross-language relationships. A neutral English cue or image appears on the front; both language answers appear together on the back.

**Why this priority**: The process must produce actual learning content with varied vocabulary patterns.

**Independent Test**: Inspect the initial corpus and built deck for category and relation variety, aligned meanings, one card per ID, stable existing identities, and no answer or relation clue on the front.

**Acceptance Scenarios**:

1. **Given** completed initial batches, **When** the learner source is inspected, **Then** it contains accepted concepts from at least three practical categories and all three eligible learner relations (`similar`, `different-common-word`, `false-friend`), without promoting weak entries to meet a quota.
2. **Given** an accepted concept, **When** its card is studied, **Then** its front reveals neither answer nor relation, and its back shows Bahasa Indonesia and Bahasa Melayu answers together; a false-friend card also gives a brief explanation of the misleading lookalike and its actual meaning.
3. **Given** an existing concept whose wording or relation is corrected, **When** the deck is rebuilt, **Then** its permanent ID and note GUID remain unchanged and it still produces one card.
4. **Given** an identical ordinary vocabulary pair, **When** it is classified as `same`, **Then** it is rejected before expensive evidence and review calls and never appears in the learner TSV.

---

### User Story 3 - Grow and Audit Later Batches (Priority: P2)

A maintainer runs another topic batch from documented materials, checks overlap with the released library, and can revisit prior decisions and evidence.

**Why this priority**: Repeatability and duplicate control allow AI to remain the primary long-term growth mechanism.

**Independent Test**: Propose an existing concept under a new English synonym in a later batch and inspect duplicate handling, ID assignment, reporting, and provenance.

**Acceptance Scenarios**:

1. **Given** an existing concept proposed with a synonym, plural, or trivial form variation, **When** duplicate review runs, **Then** the proposal is merged, rejected, or explicitly distinguished before any new ID is assigned.
2. **Given** a held candidate, **When** it is reevaluated, **Then** its prior evidence, conflicts, and hold reason are available and it has not entered learner data.
3. **Given** a completed batch, **When** the report is read, **Then** totals reconcile and relation distribution, duplicates, investigation needs, and verification failures are visible.

### Edge Cases

- A dictionary confirms existence but does not establish preferred everyday usage.
- An English cue has multiple senses and the two answers correspond to different ones.
- A difference reflects register, region, age, or specialty rather than national usage.
- Independent checks disagree, a source is unavailable, or evidence contradicts the proposal.
- A lookalike has multiple meanings, only one of which resembles the other language's meaning.
- A later batch repeats a concept under a synonym, plural, or inflected form.
- Two similar candidates actually represent distinct learner meanings.
- A rejected candidate is proposed again; its prior decision is visible and no automatic acceptance occurs.
- An accepted entry is corrected after release; its ID stays stable unless it was a different semantic concept.
- A batch yields no accepted entries; the report still explains the outcome without weakening gates.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Curation MUST use bounded topic-based batches and be repeatable from repository documentation and retained materials, without relying on an undocumented chat session.
- **FR-002**: AI MUST perform the primary discovery, usage research, classification, verification, and expansion work. Routine high-confidence acceptance MUST NOT require human review of every item.
- **FR-003**: The curation process MUST separately identify generation, linguistic comparison, evidence checking, independent verification, adversarial challenge, semantic duplicate review, confidence assessment, and final decision stages. All applicable stages MUST complete before acceptance; generation MUST NOT approve its own output. A candidate finalized early as `hold` or `rejected` MUST retain the reason and the status of each uncompleted stage, without fabricating a stage result.
- **FR-004**: Curation MUST target contemporary common Indonesian in Indonesia and Malaysian Malay as commonly used in Malaysia, distinguishing existence, comprehension, common use, and preferred everyday use.
- **FR-005**: Each accepted concept MUST have exactly one contrast relation: `similar`, `different-common-word`, or `false-friend`, as defined below. `same` remains a candidate classification but MUST be rejected before promotion. Normal validation and build MUST reject a learner TSV row marked `same`.
- **FR-006**: A `different-common-word` decision MUST establish shared neutral meaning and useful, natural everyday preference in each language, rather than merely different dictionary translations, synonyms, register, or overgeneralized regional use.
- **FR-007**: Beyond the ordinary evidence gate, a `false-friend` decision MUST have independent evidence for each language's relevant meaning and for the misleading contrast, plus agreement from a verifier separate from generation and from adversarial review. Curation records MUST identify the misleading form, the language in which it misleads, and its actual meaning separately from the learner-facing contrast text. Any unresolved disagreement MUST place it on hold or reject it.
- **FR-008**: Each accepted ordinary candidate MUST have at least two independent, claim-relevant external sources or signals supporting its key meaning and usage claims. Evidence MUST be gathered during curation, be inspectable, and identify its source and supported claim. An AI-supplied citation or audit claim MUST NOT count until a separate source inspection records what was observed and how it was accessed. AI assertions do not count as external evidence, and dictionary existence alone MUST NOT establish everyday preference.
- **FR-009**: Independent verification and adversarial review MUST record conflicting evidence and actively challenge semantic alignment, common usage, register, regionality, alternate meanings, and relation classification before acceptance. Unresolved disputes MUST block acceptance even when the minimum evidence count is met.
- **FR-010**: Confidence decisions MUST consider verifier agreement, evidence quality, conflicts, semantic alignment, usage consistency, and relation certainty. Unsupported model self-ratings MUST NOT be sufficient.
- **FR-011**: Every candidate in a closed batch MUST receive one deliberate final outcome: `accepted`, `hold`, or `rejected`. An interrupted or incomplete stage leaves the candidate pending until research resumes or an investigated candidate is explicitly finalized as `hold` or `rejected` with a reason and uncompleted-stage statuses. A batch with pending candidates MUST NOT close or change learner data. Unresolved uncertainty or conflict MUST block acceptance; only accepted entries may enter learner data.
- **FR-012**: Duplicate review MUST compare candidates within a batch, across all batches being promoted together, against earlier candidate archives, and against the released library, including identical cues, singular/plural forms, trivial morphology, synonyms, and alternate English labels. Overlap MUST be merged, rejected, or explicitly distinguished before assigning a new ID.
- **FR-013**: English cues MUST identify one neutral concept shared by both answers, with concise sense clarification where needed and without unnecessary explanatory prose.
- **FR-014**: The learner source MUST remain a human-inspectable version-controlled vocabulary table with `id`, `english`, `indonesian`, `malaysian`, `relation`, `image`, and `tags`; image and tags MAY be empty. It MUST also retain concise learner-facing contrast text for each accepted false friend, with the storage shape decided during planning. Curation provenance MUST be separate.
- **FR-015**: Permanent IDs MUST be assigned only after acceptance, remain unique and stable for the same concept, and alone determine Anki note identity. Curation metadata and other learner fields MUST NOT affect GUID derivation.
- **FR-016**: Curation records MUST retain batch or origin, proposed and final claims, stage outcomes, supporting references, material conflicts, disposition and reason, and curation time or version sufficient for reevaluation.
- **FR-017**: Each batch MUST report generated, accepted, held, rejected, and pending counts; relation distribution; detected duplicates; investigation items; and verification failures. Open reports MUST reconcile all five counts, including pending; closed reports MUST have zero pending and reconcile generated against the three final outcomes.
- **FR-018**: The initial corpus MUST result from fully checked batches, cover at least three practical categories and all three eligible learner relations (`similar`, `different-common-word`, `false-friend`), and support a normal short study session. Planning MUST set a practical batch target after estimating verification effort; the target MUST NOT become an acceptance quota.
- **FR-019**: Decision records MUST preserve enough information to later measure reported errors, relation misclassification, duplicate rate, correction rate, false-friend accuracy, and rejection share, without building feedback collection now.
- **FR-020**: Accepted entries MUST become ordinary deterministic source data before deck generation. Normal validation, local `.apkg` builds, and GitHub release builds MUST NOT invoke AI or live language research; after dependencies are available, validation and package generation MUST work offline.
- **FR-021**: Card fronts MUST use an English cue or image and the existing neutral prompt, revealing neither relation nor answer. Backs MUST show both labeled language answers; for a false friend, the back MUST also identify the misleading lookalike and its actual meaning in a concise evidence-backed contrast. One concept MUST remain one note and one card.
- **FR-022**: The learner-source schema change MUST receive a compatibility assessment and regression verification for permanent IDs, deck and note-model identities, GUID derivation, and any required migration before release.
- **FR-023**: Documentation MUST explain the AI-first rationale and fallibility, separate generation and verification, relation and acceptance rules, evidence and everyday usage expectations, adversarial and duplicate handling, batch growth, neutral cues, and conversion of accepted concepts to deterministic source data.

### Relation Rules

- **`same`**: The same or effectively identical form is commonly used for the intended concept in both languages. Classify and reject; this relation is never learner-facing source data.
- **`similar`**: Commonly used forms are recognizably related but differ enough for useful recall practice.
- **`different-common-word`**: Different words are normally preferred in everyday usage for the same neutral concept; dictionary possibility alone is insufficient.
- **`false-friend`**: A similar or identical-looking form may cause incorrect interpretation because its common meaning or usage differs significantly between the languages.

### Key Entities *(include if feature involves data)*

- **Candidate**: A proposed neutral concept and language pair tied to a batch, not yet eligible for release.
- **Evidence Record**: An inspectable reference linked to a particular meaning, usage, existence, or preference claim, including contradictions.
- **Curation Decision**: Stage results, relation, confidence rationale, final outcome, and reason.
- **Batch**: A bounded category-focused curation run with candidate records and an aggregate quality report.
- **Learner Concept**: An accepted neutral concept with permanent ID, English cue, both answers, one relation, optional image and tags, and a required concise back-side contrast when its relation is `false-friend`.
- **Deck Card**: The existing single-card learning unit built from a learner concept with stable identity.

### Dependencies and Scope

- This feature extends the existing version-controlled source and deterministic Anki build. Its current six-column source contract must be deliberately updated for `relation`; identity guarantees remain binding.
- External research is a curation input. Source suitability depends on the claim; no single named dictionary, corpus, or provider is mandated.
- Community voting, formal reviewer roles, reputation, moderation UI, learner feedback collection, runtime AI in Anki, AI or network calls during build, automatic images, audio, pronunciation, and uncontrolled bulk generation are out of scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For 100% of accepted entries in a completed batch, a reviewer can locate separate generation and verification records, claim-specific evidence, adversarial and duplicate outcomes, and an acceptance rationale; zero held or rejected entries enter learner data.
- **SC-002**: In a seeded quality exercise containing an ambiguous cue, unsupported usage preference, duplicate, and unverified false friend, 100% are held, rejected, or corrected before release.
- **SC-003**: The initial library has at least 24 accepted concepts from at least three practical categories and all three eligible contrast relations (`similar`, `different-common-word`, `false-friend`), matching the capacity-based target set during planning. If those conditions are not met, report the shortfall and continue with bounded batches; this success criterion remains unmet until enough entries pass the unchanged quality gates. No entry is promoted solely to meet the target.
- **SC-004**: Every open-batch report reconciles 100% of generated candidates across accepted, held, rejected, and pending counts. Every closed-batch report has zero pending candidates, reconciles 100% across accepted, held, and rejected outcomes, and includes all required quality measures.
- **SC-005**: In a later-batch duplicate exercise using an existing concept under another English label, zero accidental duplicate IDs are assigned, and the merge, rejection, or semantic distinction is recorded.
- **SC-006**: For 100% of unchanged permanent IDs in a rebuild, note GUIDs remain unchanged; every accepted concept produces one note and one card with no relation clue on the front, and every false-friend card shows its verified misleading lookalike and actual meaning on the back.
- **SC-007**: A maintainer familiar with the repository can run and audit a later bounded batch from documented materials without the original curation session and can find the rationale and evidence for each decision.

## Assumptions

- The existing card learning model remains intact. Displaying relation on the back is optional and can be decided during planning after compatibility review.
- Planning set a capacity-based initial corpus target of 24 accepted concepts after estimating full verification effort across bounded batches; quality gates take precedence, and additional batches may be needed to meet the target.
- Meaning and everyday preference claims may need different evidence sources.
- `hold` allows investigation and later reevaluation; `rejected` requires a substantive new basis before reconsideration.
- Human attention may focus on disputes, sensitive cases, and process improvement while routine acceptance follows the documented AI quality process.
