# Research and Design Decisions: AI-First Vocabulary Curation

**Date**: 2026-10-03
**Basis**: [feature spec](spec.md), constitution v1.2.0, current source and package contracts, and primary language/Anki references.

## 2026-10-12 implementation-driven decisions (supersede conflicting 2026-10-03 decisions below)

These decisions use the checked-in retrospective in [spec.md](spec.md) and the existing `gate.py`, `workflow.py`, `evidence.py`, `packets.py`, `bundle.py`, `store.py`, and batch artifacts. Older sections below document the original architecture; their universal-adversarial and hard corpus-quota rules are historical, not the revised policy.

1. **Keep the existing artifact and promotion architecture.** Candidate/claim schemas, inspected sources, underlying-source independence, prompt digests, append-only events, batch bundles, deterministic duplicate screening, guarded ID/export transaction, and offline builder are working assets. Modify decision/orchestration/measurement rather than rebuilding them. Alternative: greenfield pipeline; rejected because it discards provenance and makes historical reevaluation expensive.
2. **Version decision policy separately from prompt sets.** Historical manifests and prompt snapshots stay pinned. A policy-v2 decision can reuse matching prior stage outputs; only changed claim/prompt/dependency work reruns. A later failed attempt must not mask a compatible successful one. Alternative: repin all old batches to a new prompt set; rejected because packet digests would invalidate useful work.
3. **Make adversarial review conditional for ordinary cards.** Ordinary fast acceptance still needs a neutral aligned cue, no unresolved overlap/contradiction, two inspected independent claim-relevant signals, and separate verifier agreement. A concrete risk escalates to targeted review; every false friend retains mandatory adversarial agreement. Alternative: universal maximum review; the first run yielded 87 holds from 102 product candidates and repeated stages without measured throughput benefit.
4. **Distinguish unknown from false.** Missing evidence, source outage, generic model hesitation, and budget exhaustion yield HOLD when a material question remains; REJECT needs an affirmative typed basis. Concrete contradictory evidence remains visible and can defeat the claim. Alternative: interpret missing support as negative evidence; rejected because source access failures do not establish incorrect vocabulary.
5. **Cache inspected claim-scoped observations.** Reuse facts by lemma/sense, locale, proposition/usage context, and source identity/version, with raw observation, limitations and access time; relink to current claims and rerun independence/coverage checks. Alternative: cache an old candidate's accepted audit verdict or key only by URL; rejected because claims and source passages differ.
6. **Measure provider operations and active time separately from candidate events.** Bundles fan one call out to multiple records; old timestamps include idle time. An append-only operation ledger records call/retrieval identity, duration, usage availability, retries, and cache work. Alternative: infer calls from stage records or time from first/last archive timestamps; rejected as inaccurate.
7. **Bound and parallelize independent work.** Use centrally configured caps and provider/candidate worker limits, same-candidate leases, serialized shared-state closure/export, and resumable bundle fan-out. Alternative: unbounded sequential retries; rejected for cost and elapsed throughput.
8. **Calibrate before setting intermediate speed goals.** Non-fixture baseline is 102 generated, 6 historical accepts, 87 holds, 9 rejects, with 3 currently released cards. The 103rd candidate/10th reject belongs to `growth-audit-001` fixture. Active runtime, exact calls/tokens/retrievals/cost are unavailable. Use a bounded timed old-policy comparator and the historical outcome calibration set, then choose an intermediate improvement target. Keep the long-term ordinary-path 50× expert throughput objective; derive expert throughput from a small quality-matched timed benchmark. Alternative: invent a human rate or treat 24 cards as a reason to weaken gates; rejected.
9. **Instrument the provider invocation boundary.** The implemented CLI exchanges packets and responses; external model calls are not currently made by `workflow.py` or `bundle.py`. Add a provider-neutral runner for measured calls, linking packet, invocation, response and operation ID. Keep manual exchange, with provider latency/usage explicitly unavailable. Initial work-budget values come from the timed old-policy comparator, not the later revised pilot. Alternative: count ingested candidate events as provider calls; rejected because bundles fan out and external call time is invisible.
10. **Predeclare a comparable quality-adjusted evaluation.** Freeze matched prospective old/revised cohorts by category, preliminary relation/risk, cue complexity and source access, plus one evidence-backed pass/fail/unresolved audit rubric before timed runs. Apply that rubric to every exported card in the bounded old-policy comparator, revised pilot and expert exercise; report raw and audit-passing counts separately. Historical fixed-artifact replay remains a separate decision-policy comparison. Alternative: compare unrelated batches or audit only expert cards; rejected because either can create a false speed or quality advantage.

**Unresolved until measured**: exact operational caps, safe worker/provider concurrency on the configured service, historical false-negative truth for suspected examples, timed old-policy baseline, and capacity-based corpus release target. These are planned calibration outputs, not reasons to reset completed work.

## Original 2026-10-03 decisions (historical architecture record)

The sections below describe the first implementation. Where they require every ordinary candidate to pass adversarial review or require 24 accepted cards for completion, the 2026-10-12 decisions and revised [plan](plan.md) take precedence.

## 1. Separate curation from the deck build

**Decision**: Keep a network-enabled, AI-assisted curation workspace distinct from the deterministic `data/vocabulary.tsv -> validate -> .apkg` path. The build reads approved source data only; it never reads candidate records, invokes a model, or fetches evidence.

**Rationale**: The constitution requires offline builds and source review. Curation can change as AI tools evolve without changing note identity or making a release dependent on external services.

**Alternatives considered**: Generate cards at build time (violates offline determinism); accept a model's batch output directly (violates independent verification); create a hosted curation service (unneeded for bounded repository batches).

## 2. Use role-specific prompt exchange with deterministic gates

**Decision**: Version prompts for candidate discovery, Indonesian usage, Malaysian usage, relation proposal, evidence audit, blinded independent verification, adversarial challenge, and semantic overlap review. A local curation command prepares structured prompt packets, validates returned records, computes the final disposition, and exports accepted entries. Each AI stage produces a separate persisted response with role, prompt version, model/tool identifier, timestamp, input reference, and output. The verifier receives the normalized candidate and evidence but not the generator's reasoning or preferred verdict. The challenger receives the proposed claim and evidence and tries to defeat it.

**Rationale**: Provider-neutral file exchange lets available AI agents perform most linguistic work without binding the repository to one model API or storing credentials. Mechanical gates prevent a single generated response from approving itself. Exact stochastic replay is unnecessary; the prompts, stage order, input/output records, and rules make the process repeatable.

**Alternatives considered**: One all-purpose prompt (self-approval risk); model API integration as a prerequisite (vendor and secret management before the quality method is proven); unstructured chat logs (hard to audit or rerun).

## 3. Evidence standards and source limitations

**Decision**: Every accepted ordinary candidate has at least two independent, claim-relevant external evidence signals. Count underlying sources, not two pages from one dictionary or a copied derivative. At least one claim-specific meaning signal is needed for each language; preference claims additionally need contextual or comparative usage evidence. AI assertions and fabricated-looking citations count as zero until the cited material is actually inspected. Record URL or corpus query, title/publisher, access date, short observation, locale, register, claim supported, limitations, and a source-group identifier. A missing or inaccessible source leaves work pending until replaced, rechecked, or deliberately finalized as hold with a reason.

For `different-common-word`, compare alternatives within each country for the same sense and comparable context; a bilingual dictionary's two glosses do not prove everyday preference. For `false-friend`, independently support each relevant meaning and the misleading cross-language contrast, then require separate verifier and adversarial agreement. Shared alternate senses, regional labels, or unresolved counterexamples cause `hold` or `rejected`.

**Primary reference candidates**:

- [KBBI VI](https://kbbi.kemdikbud.go.id/) for Indonesian senses and labels. Its [usage guide](https://kbbi.kemdikbud.go.id/Content/Files/Petunjuk%20Pemakaian.PDF) describes labels including non-general usage; listing alone does not show everyday preference.
- [DBP PRPM](https://prpm.dbp.gov.my/) for Malaysian Malay senses and labels.
- [DBP corpus](https://dbp.gov.my/pangkalan-data-korpus/) for Malay concordance and, where accessible, frequency evidence. DBP states that its corpus is currently concentrated on written material; public concordance and registered frequency access differ.
- [Indonesian idTenTen](https://www.sketchengine.eu/idtenten-indonesian-corpus/) and [Malay msTenTen](https://www.sketchengine.eu/mstenten-malay-corpus/) as supplemental usage corpora when access is available. Malay-wide results require a Malaysia filter or corroboration because the corpus includes other countries.

**Alternatives considered**: Require one named source for every entry (poor coverage and single-source bias); treat dictionary presence as common use (false national contrasts); scrape entire sources into the repository (access, rights, and maintenance problems).

## 4. Preserve the existing Anki note schema

**Decision**: Expand the learner TSV to eight columns, in order: `id,english,indonesian,malaysian,relation,image,tags,contrast`. `contrast` is empty except for accepted false friends, where it is required, concise, and evidence-backed. Keep the existing five Anki note fields in their exact order, plus deck ID, model ID, and GUID namespace. Do not add a sixth Anki field. At package build time, escape the Malaysian answer and contrast separately, then append the contrast as a clearly styled, back-only HTML block within the existing Malaysian field; the front never references that field. Keep `relation` source-only for the MVP.

**Rationale**: The [Anki packaged-deck manual](https://docs.ankiweb.net/importing/packaged-decks.html) says adding a note-type field generally prevents existing notes from updating during reimport, although newer Anki versions offer import choices. Preserving the five-field schema avoids that migration risk while meeting the clarified false-friend back requirement. The Anki field is a presentation container; the authoritative TSV still stores the answer and contrast separately. Confirm the old-package-to-new-package import in Anki Desktop before release.

**Alternatives considered**: Append a sixth `Contrast` field (cleaner note internals but breaks normal update compatibility); embed contrast in the English or image field (could leak on the front); store a sidecar keyed by ID (splits learner-facing source across files).

## 5. File-backed records, state machine, and ID safety

**Decision**: Store bounded batch manifests, candidate/stage records, and reports under `curation/batches/<batch-id>/`. Use structured UTF-8 records with candidate-local IDs; permanent six-digit IDs are assigned only to accepted concepts during export. Keep logically append-only assignment records for all ever-assigned concept IDs, including removed concepts; derive active/retired status from the learner TSV rather than mutating assignments. Before export, screen all batches in the promotion set against each other and prior records. Use a recovery journal and prior-version backups for the two-file TSV/ledger replacement; block release until any interrupted transaction is recovered. A released correction keeps its ID; a genuinely distinct concept gets a new one.

**Rationale**: Candidate IDs must not accidentally become Anki identities. The ledger prevents reuse after a concept is removed from active source. Source remains inspectable, and version control records corrections.

**Alternatives considered**: Derive ID from words (unstable under correction); scan only current TSV for next ID (can reuse deleted IDs); database (unnecessary at current scale).

## 6. Confidence and disposition

**Decision**: Use a deterministic outcome gate with reasons rather than a model confidence percentage. `accepted` requires valid schema, clear shared cue, mandatory stage records, verified independent evidence, verifier agreement, resolved adversarial objections, and no unresolved duplicate. A disproven claim or confirmed duplicate is `rejected`; missing evidence or unresolved disagreement can be deliberately finalized as `hold`. An interrupted or malformed stage is `pending`, not an automatic final hold, and prevents batch closure/export. Relation changes trigger a fresh verification/challenge pass. Closed reports count each generated candidate exactly once in its final batch outcome and preserve stage failure reasons.

**Rationale**: Model self-confidence is not calibrated evidence. A conservative gate is inspectable and reproducible.

**Alternatives considered**: Numeric model score cutoff (false precision); automatic majority vote without evidence (correlated errors); forcing a decision for every candidate (weak content).

## 7. Initial corpus target and verification effort

**Decision**: Start with four bounded batches, each proposing at most 12 candidates: transportation, home, food, and common verbs. This caps the first pass at 48 candidates and roughly 96 minimum external evidence signals before stricter false-friend checks. Set a capacity-based completion target of 24 accepted concepts across at least three categories and all three eligible learner relations (`similar`, `different-common-word`, `false-friend`), reflecting enough variety for a short study session. The 2026-10-05 contrast-only correction excludes `same` entries and requires at least one fully verified false friend for this coverage target. The target is never a reason to relax gates. If fewer than 24 pass, or relation/category coverage is incomplete, run another bounded batch and report the shortfall; initial-corpus completion remains unmet until the target passes.

**Alternatives considered**: A single large generated list (hard to verify or deduplicate); an arbitrary fixed relation quota (pressures weak acceptance); one category only (cannot evaluate generality).

## 8. Verification and release gates

**Decision**: Test deterministic rules with seeded ambiguous cues, unsupported preferences, duplicates, false friends, missing evidence, and contradictory verifiers. Run existing validation, package, identity, and offline checks after export. Compare old and new packages and perform an actual Anki Desktop reimport with the old `000001` concept to verify that unchanged IDs update without duplicates and the note type remains compatible. Document the tested client/version and result; do not claim full compatibility from GUID equality alone.

**Rationale**: The TSV schema changes, while the note schema deliberately does not. Source-level and client-level checks cover different failure modes.

**Alternatives considered**: Only inspect package contents (cannot prove import/update behavior); silently change model ID (creates migration and duplicate risk).
