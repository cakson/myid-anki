# Feature Specification: AI-First Contrastive Vocabulary Curation

**Feature Branch**: `003-vocabulary-curation`
**Created**: 2026-10-03
**Revised**: 2026-10-15
**Status**: Converged architecture — production policy v3.1; two general-export safeguards remain open
**Input**: Revise the existing Feature 003 to accept useful ordinary Indonesian–Malaysian Malay contrasts optimistically, retain stronger false-friend review, and track explainable confidence and throughput.

## Clarifications

### Convergence decision (2026-10-15)

- The implemented production path is bounded candidate generation → deterministic validation, duplicate and no-contrast filtering → policy v3.1 lightweight independent verification → ACCEPT/HOLD/REJECT with confidence and structured risk metadata → risk-selected independent pre-promotion audit → correction or withholding → guarded promotion; random/stratified audit is ongoing QA monitoring, not a release gate for otherwise eligible cards. Random audit is a deliberate quality control, not a temporary defect.
- The canonical source contains **137 concepts and 137 cards**. AI-produced ordinary contrasts can be useful, but production verification has missed materially misleading everyday preference, localized-versus-borrowed usage, answer precision, and unexpected ordinary vocabulary problems. Feature 003 does **not** claim safe unaudited autonomous release of large batches.
- The competing-form challenge, universal localized-standard or technical-borrowing gates, revised Luna verifier, default Sol escalation, and cheap universal Luna audit screen remain disabled experiments. Their artifacts remain available for study. The active `curation/config.json` policy is `3.1.0`.
- The earlier conservative policy produced excessive HOLD outcomes. Optimistic acceptance increased usable output across bounded batches, but audited quality and audit work must accompany throughput claims. Production decision rates of approximately 298 and 509 provisional ACCEPTs/hour are **not** released-card throughput.
- The 50× expert-human throughput objective remains aspirational. No observed human benchmark or comparable end-to-end quality-adjusted AI/human ratio exists. Feature 003 completion does not require meeting that target or eliminating independent audit. The unresolved product question is the acceptable quality/cost tradeoff for larger releases. See [convergence report](convergence-report.md).

### Decisions retained from 2026-10-03 and 2026-10-05

- The front remains a neutral English or image cue. A concise evidence-backed false-friend explanation appears only on the back. One concept has one permanent ID, one Anki note, and one card.
- Indonesian and Malaysian Malay forms that are effectively identical in spelling, meaning, and normal use are outside the contrastive deck. `same` remains an internal classification and is excluded from learner data.
- False friends retain independent meaning and contrast support, independent verification, and adversarial or equivalent high-risk review.

### Supersession of earlier ordinary-card rules (2026-10-13)

- The 2026-10-03 answer requiring two independent external evidence signals for **every ordinary acceptance** is superseded. Claim-relevant external evidence is targeted to actual uncertainty, disputed preference, high-risk cases, calibration, and audit. Independent model verification and model linguistic knowledge may suffice for ordinary common vocabulary.
- The 2026-10-12 evidence-backed ordinary fast path and the historical `HOLD unless proven` interpretation are superseded. Ordinary candidates with a useful contrast are accepted when a separate verifier raises no material objection and no concrete blocking issue exists, even when external corroboration is absent. Lack of perfect certainty lowers confidence; it does not by itself cause HOLD.
- `different-common-word` remains a stronger normal-preference claim than `similar`, but exhaustive source research is not a universal prerequisite. Targeted usage investigation is required when preference is materially disputed.
- The prior provisional 24-card capacity estimate is not an acceptance quota or a release gate. The approximately 50× expert-human throughput ratio is a long-term ordinary-card objective, not an immediate release gate.
- Historical decisions and objections remain inspectable. An old HOLD is not evidence of incorrect language; a concrete old objection must be reevaluated on its merits, not silently discarded.

### Session 2026-10-13

- Q: When a `different-common-word` candidate has a plausible pair and an independent verifier agrees, should an unproven preference over a named synonym block acceptance? → A: Hold only when the verifier identifies a concrete, plausible preference problem likely to mislead learners. A named synonym or missing frequency proof alone permits acceptance with lower confidence and a review flag.

### Implementation evidence informing this revision

- The first archived retrospective covered 102 generated candidates in 14 non-fixture batches: 6 historically accepted, 87 held, and 9 rejected. Three historical `same` acceptances were later excluded by the contrast-only rule, leaving 3 released learner cards. These are process counts, not linguistic accuracy estimates. Active curation time and historical per-card cost cannot be reconstructed reliably from those records. The detailed stage and source counts remain in [validation results](validation-results.md) and the existing batch artifacts.
- The frozen 26-hold policy replay accepted 0, held 25, and affirmatively rejected 1 no-contrast candidate. A later claim-evidence replay accepted 1 ordinary candidate (`lunch → makan siang / makan tengah hari`), held 24, and reaffirmed 1 no-contrast reject (`kamera / kamera`). That acceptance was experimental and did not modify the learner TSV. Three bounded verifier calls and the local replay were timed, but original research time was unavailable. See [historical-hold experiment](historical-hold-experiment.md) and [claim-evidence replay](historical-evidence-replay.md).
- The five diagnostic historical pairs—`celana/seluar`, `biskuit/biskut`, `kulkas/peti sejuk`, `mobil/kereta`, and `beasiswa/biasiswa`—remain useful reevaluation cases, not preapproved learner cards. Prior holds involved missing claim-linked stages, preference concerns, relation-label disagreement, and concrete reviewer objections. The new policy must distinguish material misteaching risk from requests for ever more proof.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Grow Useful Contrasts Quickly (Priority: P1)

A maintainer starts a manageable topic batch. AI proposes practical cross-language differences, obvious no-contrast proposals are filtered early, and a separate linguistic verifier checks ordinary candidates. Publishable contrasts receive a confidence tier and may enter the learner source without universal external research or adversarial review.

**Why this priority**: AI is the primary growth mechanism. A pipeline that holds almost every useful candidate produces too little learning value.

**Independent Test**: Run a bounded representative scratch batch with ordinary similar and different-word pairs, identical pairs, duplicates, an ambiguous cue, and a disputed usage claim. Inspect accepted batch decisions, confidence reasons, review flags, and elapsed time without changing canonical learner data. User Story 2 independently tests promotion and learner-card output.

**Acceptance Scenarios**:

1. **Given** an ordinary candidate with a clear shared sense, natural forms, useful contrast, no duplicate, and a separate verifier with no material objection, **when** the decision is made, **then** it may be accepted through the low-risk path without external research or adversarial review and receives exactly one explained confidence tier.
2. **Given** identical forms with the same normal meaning and usage, **when** the early filter can safely establish no contrast, **then** the candidate is rejected as `same` before expensive review, gets no accepted-card confidence tier, and never enters learner data.
3. **Given** recognizably related but useful different forms such as `biskuit/biskut`, **when** classification runs, **then** spelling difference alone does not collapse them into `same`; the separate verifier judges whether `similar` is useful and semantically aligned.
4. **Given** a tentative relation label that a verifier corrects, **when** both agree on the actual concepts and no material objection remains, **then** the relation can be corrected and recorded without automatically holding the candidate.
5. **Given** a concrete semantic, usage, register, regional, or duplicate objection, **when** risk is classified, **then** the candidate takes a targeted investigation path and is held if the material issue remains unresolved.
6. **Given** an agreed `different-common-word` pair with a named alternative but no concrete reason the proposed answer is misleading, **when** preference is assessed, **then** it may be accepted with lower confidence and a review flag; a specific plausible preference problem triggers targeted investigation and HOLD if unresolved.

---

### User Story 2 - Study a Neutral, Stable Card (Priority: P1)

An Indonesian or Malaysian learner sees a neutral English cue or available image and recalls the relevant term before revealing both answers. Corrections in later releases retain their review history.

**Why this priority**: The deck teaches differences between closely related languages without giving away an answer on the front.

**Independent Test**: Inspect a built package and an update import for an ordinary contrast and a false friend, including front/back rendering, ID/GUID stability, and one-card identity.

**Acceptance Scenarios**:

1. **Given** an accepted concept, **when** its card is shown, **then** the front displays the neutral cue and neither target answer nor relation; the back displays labeled Indonesian and Malaysian Malay answers.
2. **Given** an accepted false friend, **when** its back is revealed, **then** it includes a concise verified explanation of the misleading form without exposing it on the front.
3. **Given** an accepted card whose answer, relation, or confidence later changes, **when** a new deck is built, **then** its permanent concept ID, note GUID, one-note/one-card structure, and compatible note schema remain stable.
4. **Given** a `same` candidate, **when** learner source is inspected, **then** that concept is absent.

---

### User Story 3 - Reconsider and Audit Existing Work (Priority: P2)

A maintainer replays historical holds with their saved evidence and reviewer outputs, accepts publishable ordinary contrasts at an appropriate confidence tier, and keeps concrete unresolved cases on hold. Accepted low-confidence cards can later be reviewed first, while random audits can detect overconfident errors.

**Why this priority**: Existing candidate work is valuable, and iterative quality improvement requires both targeted and cross-tier checks.

**Independent Test**: Reevaluate the frozen historical sample without regenerating candidates; inspect changed decisions, reasons, confidence, old objections, preserved IDs, and an audit sample across tiers.

**Acceptance Scenarios**:

1. **Given** a historical HOLD with no current material blocker, **when** it is reconsidered under the revised rules, **then** it may be accepted with a justified confidence tier and linked prior history without regenerating its candidate ID.
2. **Given** a historical concrete objection, **when** it is reconsidered, **then** the objection is resolved with a reason, remains a specific HOLD issue, or supports an affirmative REJECT; old status alone decides nothing.
3. **Given** accepted cards spanning confidence tiers, **when** future quality review is prioritized, **then** very-low and low cards appear first, and a random or stratified sample can also include medium and high cards.
4. **Given** a correction to an accepted concept, **when** release source changes, **then** the same permanent ID is retained and the correction is traceable.

---

### User Story 4 - Evaluate AI Productivity (Priority: P2)

A maintainer compares accepted-card output and quality against prior AI runs and a small expert-human benchmark, then improves generation and review rules based on observed waste and errors.

**Why this priority**: AI-first curation must improve actual learner-content throughput rather than merely generate many suggestions.

**Independent Test**: Examine a measured batch report containing elapsed accepted-card throughput, path and confidence distributions, no-contrast waste, work per accepted card where available, audit findings, and unavailable fields explicitly marked.

**Acceptance Scenarios**:

1. **Given** a completed measured batch, **when** its report is read, **then** accepted learner cards, elapsed time, fast-path and escalation outcomes, same/no-contrast rejection, and available model/research work are distinguished from raw candidates.
2. **Given** a small comparable expert-human benchmark, **when** an ordinary AI cohort is compared, **then** the ratio uses accepted cards under comparable quality expectations; a missing denominator or incomplete timing produces an unavailable ratio rather than an invented speedup.
3. **Given** correction and audit outcomes across confidence tiers, **when** quality is evaluated, **then** error, removal, and relation-correction rates by tier can be measured without claiming calibration before enough outcomes exist.

### Edge Cases

- Identical spelling may conceal a real false-friend meaning difference. Equality alone cannot reject such a candidate until the claimed usage contrast is safely assessed.
- A word exists in both dictionaries but is normally preferred in only one country. Existence does not settle preference, and cross-dictionary existence alone does not defeat `different-common-word`.
- The English cue has two senses, or one answer refers to a wider/narrower concept. Material mismatch causes targeted investigation or HOLD; a confirmed bad pairing causes REJECT.
- A verifier corrects a relation while agreeing on both words. Record the correction and assess its material effect rather than treating every label difference as linguistic failure.
- A reviewer mentions a possible alternative, missing frequency count, or unmeasured region without explaining learner harm. Such caveats affect confidence or flags; they do not automatically trigger HOLD.
- A reviewer identifies a specific competing everyday form that could make the proposed `different-common-word` pair materially misleading. Investigate the preference claim; keep HOLD if that risk remains unresolved.
- A credible source or reviewer shows a specific misleading alternative, register mismatch, regional restriction, or contradictory meaning. The material issue must be resolved before acceptance.
- A candidate shares a concept with a released card under another English synonym, plural, or trivial morphology. No second permanent ID is assigned.
- An external source is unavailable or an investigation budget expires. Missing research is not contrary evidence; use the ordinary acceptance rule if no material issue remains, otherwise HOLD.
- A false friend has attractive but weak support for the misleading contrast. It remains HOLD or is affirmatively rejected; ordinary optimism does not bypass its stronger gate.
- A low or very-low confidence card has an actual unresolved issue likely to misteach the concept. It is HOLD, not accepted under a low label.

## Requirements *(mandatory)*

### Functional Requirements

#### Corpus and card behavior

- **FR-001**: AI MUST perform the majority of candidate discovery, comparison, classification, verification, and expansion in normal batches. Routine human approval MUST NOT be required per card.
- **FR-002**: The learner corpus MUST contain meaningful Indonesian–Malaysian Malay contrasts only. Eligible relations are `similar`, `different-common-word`, and `false-friend`; `same` MUST never be promoted.
- **FR-003**: A neutral English cue or available image MUST appear on the front without either answer, relation, or false-friend clue. The back MUST show both labeled answers and, for accepted false friends, a concise verified misleading-form explanation.
- **FR-004**: Each learner concept MUST have one permanent ID, one note, and one card. Content, relation, confidence, evidence, and review changes MUST NOT change its ID-derived Anki GUID. Existing deck, model, field, and import compatibility constraints remain binding.
- **FR-005**: Canonical learner source MUST remain deterministic, version controlled, and easy to inspect. Curation metadata, including confidence, MUST remain separate from card content by default. Normal validation, `.apkg` generation, and releases MUST require no live AI or external research.

#### Candidate and relation decisions

- **FR-006**: Candidate generation MUST favor practical contrastive vocabulary and bounded topic batches, while recording generated, promoted, held, rejected, and no-contrast counts by batch. It MUST NOT generate uncontrolled volumes to compensate for low acceptance.
- **FR-007**: The ordinary path MUST separate raw generation from lightweight independent linguistic verification. One generation response alone MUST NOT promote a learner card.
- **FR-008**: Before expensive research or review, safe normalization, exact-form checks, and duplicate/semantic-overlap checks MUST filter obvious no-contrast and duplicate proposals. Identical forms with a plausible meaning or usage contrast MUST receive enough linguistic judgment to avoid wrongly discarding a false friend.
- **FR-009**: `same` means no meaningful cross-language recall challenge for the intended sense and normal usage. A confirmed `same` candidate MUST be REJECTED with a distinct `no-meaningful-cross-language-contrast` reason and no accepted-card confidence tier.
- **FR-010**: `similar` means recognizably related forms with a useful spelling, morphology, or form distinction for the same concept. Straightforward `similar` candidates MUST NOT require synonym-preference research merely because such research is possible.
- **FR-011**: `different-common-word` means noticeably different forms are normally preferred for the same concept. A separate verifier's informed linguistic judgment MAY support an ordinary case. A named synonym or lack of direct frequency comparison alone MUST NOT block acceptance; these lower confidence and may add a review flag. If the verifier identifies a concrete, plausible preference problem likely to mislead learners, targeted usage evidence MUST be sought and the candidate MUST remain HOLD if that material problem remains unresolved. Dictionary existence alone MUST NOT prove or disprove preference.
- **FR-012**: Generation's relation is provisional. Independent verification MAY correct it without automatic HOLD when semantic alignment and publishability remain intact. The old and corrected relation and reason MUST be retained.
- **FR-013**: English cues MUST identify the same intended sense for both answers and be concise enough for recall. Material ambiguity MUST be resolved before acceptance.
- **FR-014**: Deterministic and semantic duplicate review MUST prevent accidental separate IDs for the same learning concept, including synonyms, plurals, and trivial morphology. A genuine semantic distinction MUST be recorded before a new ID is permitted.

#### Risk, decision, and evidence

- **FR-015**: Learner-relevant candidates MUST be classified low, medium, or high processing risk from concrete signals. Low risk takes the ordinary fast path; medium risk receives a bounded targeted check where needed; high risk receives stronger verification. Risk and escalation reasons MUST be inspectable.
- **FR-016**: An ordinary candidate MAY be ACCEPTED without external evidence when naturalness, shared sense, useful contrast, duplicate status, and relation are plausible, a separate verifier has no material objection, and no concrete contradiction or high-risk signal exists. Absence of research alone MUST NOT cause HOLD.
- **FR-017**: HOLD MUST be reserved for a specific unresolved issue likely to materially misteach learners, such as semantic mismatch concern, a concrete plausible preference problem, contradictory signal, significant register/region ambiguity, unresolved duplicate identity, or meaningful verifier disagreement. A merely named synonym, missing frequency proof, generic hesitation, theoretical further research, and old HOLD status MUST NOT independently cause HOLD.
- **FR-018**: REJECT MUST have an affirmative defect or product-scope reason, including confirmed duplicate, wrong or unnatural pairing, materially misleading relation, low learning value, or confirmed no contrast. Missing evidence, provider failure, and budget exhaustion alone MUST NOT cause REJECT.
- **FR-019**: A review objection MUST state the concrete defect or learner risk. Review flags and nonmaterial caveats MAY lower accepted-card confidence; they MUST NOT act as unexplained vetoes. Existing historical objections MUST be retained and explicitly assessed rather than erased.
- **FR-020**: External evidence MUST be used where needed to resolve material uncertainty, verify contested preference, review high-risk vocabulary, calibrate AI judgments, or audit accepted cards. Retrieved evidence MUST remain claim relevant, source identifiable, and reusable without counting the same underlying source twice. Evidence of lexical existence MUST NOT be treated as proof of ordinary preference.
- **FR-021**: False friends MUST receive stronger claim-specific support for each language's relevant meaning and for the misleading contrast, separate independent verifier agreement, and adversarial or equivalent high-risk review agreement before ACCEPT. Their back-side contrast MUST be grounded in that review. Ordinary evidence and fast-path rules MUST NOT bypass these gates.
- **FR-022**: Expensive investigation MUST have bounded retries and escalation. At the limit, apply the current risk-tier gate: ACCEPT if its ordinary criteria pass, HOLD if a material question remains, or REJECT only for an affirmative defect.

#### Accepted-card confidence and future quality

- **FR-023**: Every ACCEPTED candidate MUST have exactly one tier from `high`, `medium`, `low`, `very-low`, plus a concise rationale tied to observable signals. No arbitrary percentage or unsupported claim of calibrated probability is permitted. Nonaccepted candidates MUST NOT receive an accepted-card confidence tier.
- **FR-024**: `high` indicates strong, concordant observable signals; `medium` indicates a publishable card with a meaningful nonblocking caveat; `low` indicates notable nonblocking uncertainty or a corrected relation; `very-low` indicates substantial nonblocking uncertainty but no material unresolved issue. A tier MUST NOT substitute for resolving a likely misteaching risk.
- **FR-025**: Accepted candidates MAY carry a small structured set of future-review flags, including limited evidence, weak usage preference, relation correction, regional/register uncertainty, semantic ambiguity, historical objection, limited verifier agreement, and resolved conflicting signal. Flags MUST preserve their meaning and not silently hide a blocker.
- **FR-026**: Targeted future review MUST prioritize accepted `very-low`, then `low`, then `medium`, then `high`, with risk flags affecting order. The process MUST periodically select a random or stratified audit sample across all tiers, including high confidence, to detect systematic and overconfident errors. No arbitrary audit percentage is required before observed quality data exists.
- **FR-027**: Where correction and audit data become available, reports MUST support correction, removal, relation-change, and audit-failure rates by confidence tier. Tier quality MUST be recalibrated if observed outcomes do not track review risk. Confidence is a review-priority tool, not a learner-facing certainty claim.

#### Continuity, reporting, and productivity

- **FR-028**: Existing candidate IDs, batch state, evidence, source captures, cache, prompt/provider versions, verifier/adversarial output, decisions, metrics, and learner data MUST remain available and linked. Historical reevaluation MUST reuse valid artifacts and rerun only work invalidated by the new policy; it MUST NOT regenerate candidates solely because policy changed.
- **FR-029**: The frozen historical sample and the five named diagnostic pairs MUST be reevaluated under the new rules without preapproval. `kamera/kamera` and other confirmed no-contrast pairs MUST demonstrate early scope rejection. Every changed decision MUST record the old decision, new decision, relation change, concrete blocker or absence of one, confidence if accepted, and retained evidence/history.
- **FR-030**: Every batch and reconsideration report MUST reconcile all candidates and show ACCEPT/HOLD/REJECT, relation and confidence distributions, fast-path/escalation counts, duplicates, no-contrast filtering, verification failures, and remaining material issues. No-contrast waste MUST be reported separately from bad-translation rejects and used to improve later generation.
- **FR-031**: Accepted-card throughput MUST use learner cards reaching canonical source over actual end-to-end elapsed curation time. Reports SHOULD include seconds, model calls, tokens, evidence operations, and approximate cost per accepted card where measurable; unavailable historical or provider data MUST be labeled unavailable. Experimental acceptance MUST NOT be counted as canonical release output.
- **FR-032**: The long-term ordinary-card north star remains approximately `AI accepted-card throughput / expert accepted-card throughput >= 50`. A future comparison MUST first observe a small expert-human benchmark under broadly comparable quality expectations; until then the ratio MUST be reported as unavailable. A human benchmark is neither a routine approval gate nor a Feature 003 completion condition.
- **FR-033**: Quality evaluation MUST combine accepted-card output and speed with audit/correction findings, relation errors, duplicate acceptance, suspected false-negative recovery, and confidence-tier behavior. Higher acceptance alone MUST NOT be reported as better quality. Ordinary cases SHOULD dominate the low-cost path as the process matures; the actual share MUST be measured, not invented.
- **FR-034**: Independent candidates MAY be batched or processed with bounded concurrency where dependencies permit. Reused linguistic facts MUST retain provenance and claim relevance. Interrupted batches MUST resume without partial or failed work altering canonical learner source.
- **FR-035**: Accepted production decisions MUST pass guarded-promotion eligibility before export. Concrete risk selected for independent review requires pre-promotion audit clearance; any recorded unsafe, unresolved, or withheld review result blocks export. Otherwise eligible ordinary cards MAY enter the learner source without random-audit selection. Random/stratified audit is ongoing post-production QA monitoring, not a mandatory release gate; its later corrections MUST preserve permanent concept identity. Export MUST bind eligibility to the current closed decision and final learner content and honor any batch safety brake.
- **FR-036**: Production MUST remain on policy v3.1. Failed or inconclusive experimental gates, verifier variants, model escalations, and universal audit screens MUST stay disabled by default and identifiable as research artifacts. Experimental results MUST NOT be silently promoted into the active decision path.

### Relation and Decision Rules

| Relation | Curation meaning | Learner eligibility |
| --- | --- | --- |
| `same` | Effectively identical form, meaning, and ordinary use with no worthwhile recall contrast | REJECT as no contrast; no confidence tier |
| `similar` | Related but usefully different form for the same sense | Eligible through ordinary verification |
| `different-common-word` | Different normal vocabulary preference for the same sense | Eligible; investigate material preference disputes |
| `false-friend` | Similar form creates a real misleading meaning/usage contrast | Eligible only after stronger review |

| Decision | Required meaning |
| --- | --- |
| ACCEPT | Applicable risk-tier checks pass; no material blocker remains; exactly one explained accepted-card confidence tier |
| HOLD | Specific material question remains unresolved and publication could meaningfully misteach |
| REJECT | Affirmative linguistic defect, duplicate/low-value proposal, or no meaningful contrast |

### Key Entities *(include if feature involves data)*

- **Candidate**: A generated or historically retained neutral concept, two forms, proposed relation, stable candidate ID, and batch lineage before promotion.
- **Relation Assessment**: Provisional and verified class, any correction, semantic rationale, and learning-contrast value.
- **Curation Decision**: ACCEPT/HOLD/REJECT, risk tier, concrete reason, applicable checks, and accepted-card confidence where eligible.
- **Confidence Assessment**: One tier, concise rationale, observable signals, and structured future-review flags for an accepted candidate.
- **Evidence Record**: A claim-linked source or observation with provenance, source-family identity, limits, and whether it supports, contradicts, or leaves a claim unresolved.
- **Reconsideration Record**: A link between historical and revised outcomes, retaining candidate identity, prior objections, evidence, model output, and the reason for a changed decision.
- **Batch and Quality Report**: Bounded work unit and aggregate decisions, confidence, no-contrast waste, throughput, escalation, quality findings, and unavailable metrics.
- **Learner Concept**: Canonical accepted source row with permanent concept ID, neutral cue, Indonesian and Malaysian Malay answers, eligible relation, optional image/tags, and existing false-friend back contrast when applicable.
- **Deck Card**: The stable one-note/one-card Anki learning unit built deterministically from a learner concept.

### Dependencies and Scope

- This revises Feature 003 in place. Existing implementation, historical artifacts, completed work, cache, tests, and learner data remain inputs to replanning; implementation status is not reset by changing product requirements.
- The existing learner source has `id`, `english`, `indonesian`, `malaysian`, `relation`, `image`, `tags`, and a compatibility-tested `contrast` field. Rich confidence and provenance remain curation metadata. The note schema, deck/model IDs, and ID-derived GUID require explicit compatibility proof before any change.
- Indonesian means contemporary common or standard usage in Indonesia. Malaysian Malay means contemporary common or standard Bahasa Melayu in Malaysia, not all regional Malay varieties.
- Human/community suggestions, votes, contributor reputation, formal moderation/reviewer workflows, learner-feedback collection, runtime AI in Anki, AI or network calls during package builds/releases, automatic images, audio, pronunciation, and unbounded bulk generation are out of scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a representative ordinary batch, 100% of accepted cards have a separate generation record, independent verifier result, duplicate/no-contrast disposition, risk tier, eligible relation, and exactly one explained confidence tier; zero `same`, held, or rejected candidates enter learner source.
- **SC-002**: Seeded no-contrast checks reject 100% of confirmed identical ordinary pairs before expensive research, while a meaning-divergent identical-form false-friend fixture reaches high-risk assessment instead of being discarded by equality alone.
- **SC-003**: A seeded set containing a useful `similar` pair, an agreed `different-common-word` pair with an unranked named synonym, a concrete competing-preference objection, a corrected relation, a duplicate, an ambiguous cue, and a false friend produces the specified ACCEPT/HOLD/REJECT outcomes. The unranked synonym alone does not force HOLD, while an unresolved concrete preference problem does.
- **SC-004**: 100% of accepted false friends in the evaluated set have support for both meanings and misleading contrast, independent verification, high-risk review agreement, and a back-only learner explanation.
- **SC-005**: The same frozen 26 historical candidate IDs can be replayed without regeneration or loss of old evidence/objections; changed outcomes show a reason and confidence if accepted. The five diagnostic pairs and `kamera/kamera` receive individually inspectable decisions rather than automatic acceptance or blanket HOLD.
- **SC-006**: In a measured ordinary cohort, HOLD is no longer the dominant decision for candidates without a concrete material blocker. Every HOLD names a material unresolved issue; every REJECT names an affirmative defect or no-contrast reason. The cohort and any exclusions are fixed before outcomes are known.
- **SC-007**: Batch reports reconcile 100% of candidate outcomes and separately show accepted-card throughput, confidence tiers, low/medium/high risk paths, no-contrast generation waste, and available work/cost metrics. Unknown active time or provider usage is explicitly unavailable, never estimated as fact.
- **SC-008**: Accepted `very-low` and `low` cards are retrievable as the highest-priority future-review queue, and a random or stratified audit can select from every tier. Future corrections and audit findings can be grouped by tier without changing Anki cards solely for metadata.
- **SC-009**: Bounded production and independent-audit reports distinguish provisional decisions, guarded promotions, learner-critical defects, corrections, audit workload, and unavailable timing. No production decision rate or partial replay timer is called released-card throughput. The conservative-policy false-negative history and later optimistic recovery remain inspectable.
- **SC-010**: The approximately 50× ordinary-card objective is documented as an unproven long-term target. Without an observed expert benchmark and comparable quality-adjusted end-to-end intervals, the AI/human ratio is explicitly unavailable and is not a Feature 003 release gate.
- **SC-011**: For 100% of unchanged permanent IDs in a rebuild, note GUIDs remain unchanged; accepted concepts produce one note/card, keep target answers off the front, and preserve compatible imports after corrections.
- **SC-012**: Normal Anki builds and releases run offline from version-controlled accepted learner data, with no AI or live research dependency. Interrupted or partial curation batches cause zero unintended canonical learner-source changes.
- **SC-013**: Later bounded batches can be run from documented process materials, reuse relevant historical evidence, avoid duplicate IDs, and report no-contrast rejection separately so generator quality can improve over time.
- **SC-014**: The active production and audit architecture, disabled experiments, current 137-card corpus, benchmark limits, random-audit requirement, and unresolved scaling tradeoff are documented together. The offline build yields 137 unique concept notes/cards without changing existing permanent IDs or GUID derivation during convergence.

## Assumptions

- A capable model's ordinary-language knowledge is a useful but fallible signal. Separate verification remains required; confidence tiers and later audits make uncertainty visible without pretending model self-scores are calibrated probabilities.
- A nonmaterial caveat is a limitation that does not create a plausible material wrong answer for the intended cue. A material issue is a specific unresolved risk of meaningfully misteaching that cue. Replanning will define the review rubric and record it consistently.
- `very-low` confidence can be published only when no material blocker remains. It is the first future-review priority, not a way to bypass false-friend or contradiction gates.
- Prior source inspection and cache records remain valuable even though ordinary acceptance no longer requires external corroboration universally. Sources used to settle disputed preference must actually speak to preference.
- The existing first-run counts and frozen sample are a retrospective baseline for decision behavior. End-to-end historical active time, a human benchmark, and monetary cost remain unavailable; no credible 50× claim can be made from production decision speed.
