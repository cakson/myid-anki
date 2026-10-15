---
description: "Dependency-ordered implementation tasks for Feature 003"
---

# Tasks: AI-First Vocabulary Curation

**Input**: Design documents in `specs/003-vocabulary-curation/`: [spec](spec.md), [plan](plan.md), [research](research.md), [data model](data-model.md), [workflow contract](contracts/curation-workflow.md), [learner-source contract](contracts/learner-source.md), and [quickstart](quickstart.md).

**Tests**: Included because the spec's quality gates and constitution require deterministic verification of source parsing, IDs, package identity, and failure behavior. Seeded tests establish that gates reject known bad records; they do not establish linguistic truth.

**Organization**: Tasks are grouped by user story. `[P]` denotes independent work in different files after its stated prerequisites; it does not authorize skipping a dependency or quality gate. All initial-corpus AI research must preserve evidence and stage artifacts.

**Policy-v3 migration and closure**: Checked policy-v1/v2 tasks remain completed historical work; their old strict ordinary-evidence/hold rules do not govern policy v3.1. The 2026-10-13 delta is retained below with explicit terminal dispositions. Previously open T052–T055, T057, and T061–T079 remain mapped in the historical supersession table; no completed candidate or experiment is regenerated. Preserve all artifacts and candidate IDs.

**Status legend (2026-10-15)**: `[x]` means terminal for Feature 003. Each task has exactly one status: `COMPLETE` (implemented at the time, possibly historical), `ALREADY-SATISFIED` (later work met its intent), `SUPERSEDED` (replaced by the final design), `EXPERIMENT-COMPLETED` (question answered, including negative results), `WONT-DO` (approach rejected), or `DEFERRED` (future scope). Only `[ ] [REQUIRED-INCOMPLETE]` would indicate work blocking Feature 003 closure. The original task text and dependency history remain for traceability; the final spec and convergence report govern current behavior.

**Reconciled inventory**: 91 tasks — 57 `COMPLETE`, 12 `ALREADY-SATISFIED`, 13 `SUPERSEDED`, 2 `EXPERIMENT-COMPLETED`, 2 `WONT-DO`, 5 `DEFERRED`, and 0 `REQUIRED-INCOMPLETE`.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish inspectable curation locations and one configuration boundary without changing the offline builder.

- [x] T001 [COMPLETE] Create the curation package entrypoints and repository directories in `src/indo_malay_anki/curation/__init__.py`, `src/indo_malay_anki/curation/__main__.py`, `curation/prompts/README.md`, and `curation/batches/.gitkeep`.
- [x] T002 [COMPLETE] [P] Define centralized provider/model, prompt-set version, and batch defaults in `curation/config.json`, keeping credentials and network settings out of the deck build path.
- [x] T003 [COMPLETE] [P] Define the versioned role inventory and structured-response references in `curation/prompts/manifest.json` for generation, both locale researchers, relation proposal, evidence audit, independent verification, adversarial review, and semantic overlap.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Provide the shared record and persistence rules on which each story depends.

- [x] T004 [COMPLETE] Implement validated batch, candidate, claim, evidence, overlap, stage-result, per-stage completion status, pending/final decision, and structured false-friend contrast records in `src/indo_malay_anki/curation/records.py`, including candidate-local IDs and no permanent ID before acceptance.
- [x] T005 [COMPLETE] Implement append-only, atomic stage-record persistence and manifest loading in `src/indo_malay_anki/curation/store.py`, preserving raw malformed responses and prior revisions for audit and resumability.
- [x] T006 [COMPLETE] Add record/schema tests for missing fields, invalid roles, source-group metadata, candidate limits, and read-after-interruption behavior in `tests/unit/test_curation_records.py`.

**Checkpoint**: Structured, versioned curation records can be created and safely resumed without touching `data/vocabulary.tsv`.

---

## Phase 3: Historical User Story 1 — Original Batch Pipeline (completed policy v1)

**Historical goal**: The completed v1 pipeline produced separately inspectable candidate, research, challenge, and decision artifacts. Policy v3 changes ordinary acceptance in Phase 8 below.

**Historical independent test**: The completed policy-v1 scratch batch covered separate role records, evidence, ambiguous cues, duplicates and false-friend gates. Current optimistic US1 acceptance is tested in Phase 8.

### Tests for User Story 1

- [x] T007 [COMPLETE] [P] [US1] Add command-contract tests for `init`, `packet`, `ingest`, `check`, `finalize-hold`, and `report`, including malformed/out-of-order AI output, pending batch closure refusal, and verifier blindness, in `tests/contract/test_curation_cli.py`.
- [x] T008 [COMPLETE] [P] [US1] Add historical policy-v1 seeded gate tests for source groups, claim coverage, separate audit observations, dictionary-only preference, contradiction, ambiguous cues, false-friend contrast and then-required stage completion in `tests/unit/test_curation_gate.py`; T084–T094 supersede universal-stage acceptance for policy v3.
- [x] T009 [COMPLETE] [P] [US1] Add within-batch exact, morphology, synonym, and semantic-overlap fixtures, including explicit distinct-sense resolution, in `tests/unit/test_curation_duplicates.py`.

### Implementation for User Story 1

- [x] T010 [COMPLETE] [P] [US1] Write versioned candidate-generation and normalization/overlap role prompts with structured output requirements in `curation/prompts/generate.md` and `curation/prompts/overlap.md`.
- [x] T011 [COMPLETE] [P] [US1] Write separate Indonesian-usage and Malaysian-usage role prompts covering contemporary common use, sense, register, region, alternatives, and evidence needs in `curation/prompts/indonesian-usage.md` and `curation/prompts/malaysian-usage.md`.
- [x] T012 [COMPLETE] [P] [US1] Write relation-proposal and evidence-audit role prompts that distinguish existence from preference and require inspection of claim-specific external sources in `curation/prompts/relation-proposal.md` and `curation/prompts/evidence-audit.md`.
- [x] T013 [COMPLETE] [P] [US1] Write blinded independent-verification and adversarial-review role prompts, including false-friend counterexamples and explicit agreement or objection outputs, in `curation/prompts/independent-verification.md` and `curation/prompts/adversarial-review.md`.
- [x] T014 [COMPLETE] [US1] Implement prompt packet construction and role-specific context allowlists in `src/indo_malay_anki/curation/packets.py`; omit generator rationale and preferred verdict from independent-verifier packets, record input/upstream digests, and invalidate stale downstream results after cue, answer, relation, evidence, or prompt-version changes.
- [x] T015 [COMPLETE] [US1] Implement batch initialization, structured response ingestion, ordering checks, prompt/model/tool provenance, and resumable failure records in `src/indo_malay_anki/curation/workflow.py`.
- [x] T016 [COMPLETE] [US1] Implement deterministic comparison keys and within-batch exact/morphology screening, with AI-reviewed semantic-overlap resolutions and unresolved-overlap blocking, in `src/indo_malay_anki/curation/duplicates.py`.
- [x] T017 [COMPLETE] [US1] Implement claim-to-evidence auditing and independent underlying-source counting in `src/indo_malay_anki/curation/evidence.py`; require a separate audit record with access method, page location/query, observed content, timestamp, and claim linkage before support counts, so bare AI flags, copied sources, and dictionary-only preference cannot pass.
- [x] T018 [COMPLETE] [US1] Implement the historical policy-v1 deterministic `pending`/`accepted`/`hold`/`rejected` gate in `src/indo_malay_anki/curation/gate.py`, including then-required stages, uncompleted-stage statuses, verifier/adversary agreement, contradictions, false-friend contrast and reasons; T090–T092 supersede its ordinary acceptance and universal-adversary rules for policy v3.
- [x] T019 [COMPLETE] [US1] Implement provisional and final batch reports in `src/indo_malay_anki/curation/report.py`; require generated = accepted + held + rejected + pending while open, require pending = 0 and generated = accepted + held + rejected to close, and include relation, duplicate, investigation, and verification summaries even for zero-acceptance batches.
- [x] T020 [COMPLETE] [US1] Wire the curation subcommands, including `finalize-hold`, to the workflow, gate, and report in `src/indo_malay_anki/curation/__main__.py`; ensure no command except later `export` can alter canonical learner data.
- [x] T021 [COMPLETE] [US1] Add a full scratch-batch integration scenario with separate stage records, an accepted ordinary concept, held/rejected seeded faults, and no mutation of `data/vocabulary.tsv` in `tests/integration/test_curation_batch.py`.

**Checkpoint**: One batch can be generated, researched, verified, challenged, and closed with auditable outcomes; a single AI pass cannot approve its own content.

---

## Phase 4: User Story 2 — Study the Initial Library (Priority: P1)

**Goal**: Promote only current policy-v3 ACCEPT concepts into stable source data, build a useful contrast deck, and preserve existing Anki identity and import behavior.

**Independent Test**: After bounded replay, promote only gate-valid accepted concepts; inspect useful contrast/category coverage without a quota, one note/card per ID and back-only false-friend contrast, and verify old-to-new Anki import compatibility if schema/rendering changes.

### Tests for User Story 2

- [x] T022 [COMPLETE] [P] [US2] Add strict eight-column learner-source tests for relation enum, false-friend contrast required/otherwise empty, legacy ID preservation, whitespace, malformed rows, and existing media rules in `tests/unit/test_loader.py` and `tests/unit/test_validator.py`.
- [x] T023 [COMPLETE] [P] [US2] Add package tests for unchanged five-field note schema, deck/model IDs, `000001 -> D6BBAuKXK`, one note/card, neutral front, escaped back-only contrast, and ordinary answer purity in `tests/integration/test_build_package.py` and `tests/integration/test_semantic_rebuild.py`.
- [x] T024 [COMPLETE] [P] [US2] Add export tests for accepted-only promotion, pending-batch refusal, cross-batch semantic overlap, retired-ID non-reuse, idempotent re-export, injected failure at each TSV/ledger replacement, and interrupted-journal recovery in `tests/integration/test_curation_export.py`.

### Implementation for User Story 2

- [x] T025 [COMPLETE] [US2] Extend `VocabularyConcept` with relation and contrast while preserving ID-only GUID constants and existing field behavior in `src/indo_malay_anki/model.py`.
- [x] T026 [COMPLETE] [US2] Parse the exact `id,english,indonesian,malaysian,relation,image,tags,contrast` header and values without linguistic normalization in `src/indo_malay_anki/loader.py`.
- [x] T027 [COMPLETE] [US2] Validate relation values and contrast rules before package generation while retaining existing ID, whitespace, and media checks in `src/indo_malay_anki/validator.py`.
- [x] T028 [COMPLETE] [US2] Project an escaped false-friend contrast as a secondary back-only block in the existing `Malaysian` note field, leaving the five Anki field names/order, front template, model ID, deck ID, GUID namespace, and one-card template unchanged in `src/indo_malay_anki/builder.py`.
- [x] T029 [COMPLETE] [US2] Implement logically append-only assignment records, legacy `000001` backfill, and active/retired status derived from current TSV membership in `src/indo_malay_anki/curation/ids.py` and `curation/id-ledger.json`.
- [x] T030 [COMPLETE] [US2] Implement guarded accepted-only, idempotent multi-batch export in `src/indo_malay_anki/curation/export.py`: screen all promotion batches against one another and archives before ID allocation, refuse pending or newly overlapping candidates until decisions/reports are revised, validate prospective `data/vocabulary.tsv` and `curation/id-ledger.json`, use `curation/export-journal.json` with backups, replace ledger then TSV, roll back handled failures, and recover interruptions before another export.
- [x] T031 [COMPLETE] [US2] Add repeatable `--batch` export inputs and recovery behavior to `src/indo_malay_anki/curation/__main__.py` and update exact TSV/package interface expectations in `tests/contract/test_cli_contract.py` and `tests/conftest.py`.
- [x] T032 [COMPLETE] [US2] Retrospectively curate the existing car concept through all gates in `curation/batches/transportation-001/`; retain `000001` only if accepted, otherwise retire it after other accepted rows exist.
- [x] T033 [COMPLETE] [P] [US2] Curate up to 12 transportation candidates under historical policy-v1 stage/evidence gates, recording reasons and unfinished-stage statuses for early holds or rejections in `curation/batches/transportation-001/`; preserve these artifacts for recalibration.
- [x] T034 [COMPLETE] [P] [US2] Curate up to 12 home candidates under historical policy-v1 stage/evidence gates, recording reasons and unfinished-stage statuses for early holds or rejections in `curation/batches/home-001/`; preserve these artifacts for recalibration.
- [x] T035 [COMPLETE] [P] [US2] Curate up to 12 food candidates under historical policy-v1 stage/evidence gates, recording reasons and unfinished-stage statuses for early holds or rejections in `curation/batches/food-001/`; preserve these artifacts for recalibration.
- [x] T036 [COMPLETE] [P] [US2] Curate up to 12 common-verb candidates under historical policy-v1 stage/evidence gates, recording reasons and unfinished-stage statuses for early holds or rejections in `curation/batches/common-verbs-001/`; preserve these artifacts for recalibration.
- [x] T037 [ALREADY-SATISFIED] [US2] After T096–T104 frozen replay and v3 export checks, screen all proposed promotions against current `data/vocabulary.tsv`, archives and `curation/id-ledger.json`; promote only current policy-v3 ACCEPT candidates through guarded `src/indo_malay_anki/curation/export.py`, retaining any existing permanent ID, then run offline validate/build and record per-candidate reconciliation plus actual canonical throughput availability in `specs/003-vocabulary-curation/validation-results.md`. Do not promote a replay verdict automatically or generate filler to meet a count.
  - Closure: The audited historical cohort and later fresh cohorts were guarded-promoted; the canonical deck now has 137 stable-ID cards. See guarded-promotion.md and convergence-report.md.
- [x] T038 [COMPLETE] [US2] Perform and record old-to-new Anki Desktop import/update acceptance for retained `000001` or a controlled same-ID fixture if it is retired, including client version, import settings, note/card counts, unchanged GUID, updated content, and scheduling in `specs/003-vocabulary-curation/validation-results.md`; validate back-only contrast with an accepted false friend or separate fixture, never promote weak content for the check, and block release if existing-note updates fail.

**Checkpoint**: The initial corpus is useful and varied, every released row has accepted provenance, and a previously imported concept remains the same Anki note.

---

## Phase 5: Historical User Story 3 — Later Batch Recovery (completed policy v1)

**Goal**: Run subsequent batches without semantic duplicate IDs, recover from interrupted research, and inspect why each candidate was accepted or withheld.

**Independent Test**: Propose a released concept under a new English synonym in a later batch, interrupt a stage, resume, and inspect its overlap resolution, report, retained provenance, and unchanged canonical data until export.

### Tests for User Story 3

- [x] T039 [COMPLETE] [P] [US3] Add later-batch tests for cross-batch synonyms, prior held/rejected matches, explicit distinct meanings, and zero accidental ID assignment to duplicates in `tests/integration/test_curation_growth.py`.
- [x] T040 [COMPLETE] [P] [US3] Add interruption-to-pending, early final hold/rejection with uncompleted-stage status, malformed-output, unchanged-stage reuse, stale-verification after cue/answer/relation/evidence or prompt changes, zero-acceptance, open/closed report-reconciliation, and canonical-source-immutability cases in `tests/integration/test_curation_recovery.py`.

### Implementation for User Story 3

- [x] T041 [COMPLETE] [US3] Add early cross-batch overlap warnings while a later candidate is researched, comparing accepted TSV concepts and prior candidate archives in `src/indo_malay_anki/curation/duplicates.py`; preserve merge/reject/distinct rationale, while T030 remains the mandatory final pre-ID safeguard.
- [x] T042 [COMPLETE] [US3] Make interrupted-stage replay and material-edit invalidation explicit and idempotent, without losing prior responses, in `src/indo_malay_anki/curation/workflow.py` and `src/indo_malay_anki/curation/store.py`.
- [x] T043 [COMPLETE] [US3] Extend `report.json` with open-batch pending counts, per-relation final outcomes, duplicate and correction counts, evidence failures, and stable reason codes that can support later quality metrics in `src/indo_malay_anki/curation/report.py`.
- [x] T044 [COMPLETE] [US3] Add a documented later-batch duplicate/recovery example with retained stage artifacts in `curation/batches/growth-audit-001/`; keep it out of learner data unless its candidates independently pass all gates.

**Checkpoint**: A second batch can reuse the same process, explain its decisions, and avoid accidental duplicate concept IDs.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Make the workflow understandable and complete the project-wide gates.

- [x] T045 [COMPLETE] [P] Update `README.md` with AI-first rationale and fallibility, stage roles, evidence and common-use rules, false-friend and duplicate handling, source schema, batch commands, hold/reject semantics, and the offline build boundary.
- [x] T046 [COMPLETE] [P] Update source/package contract tests and contributor wording for the eight-column accepted source while preserving historical Feature 001 artifacts in `tests/contract/test_readme_contract.py` and `tests/contract/test_template_contract.py`.
- [x] T047 [COMPLETE] Add a deterministic preflight for tracked or incomplete `curation/export-journal.json`, keep `.github/workflows/release.yml` limited to accepted-source validation/build with no AI or live research calls, ignore transient journal/backups in `.gitignore`, and cover the workflow boundary in `tests/contract/test_release_workflow_contract.py`.
- [x] T048 [COMPLETE] Run `pytest`, `ruff check .`, `ruff format --check .`, offline `python -m indo_malay_anki validate`, and offline `python -m indo_malay_anki build`; confirm the release workflow invokes neither curation nor AI/live research, and record results plus 12-candidate curation-check timing in `specs/003-vocabulary-curation/validation-results.md`.
- [x] T049 [SUPERSEDED] After T037, T110, T112 and T113, execute the policy-v3 walkthrough in `specs/003-vocabulary-curation/quickstart.md`: verify no-contrast exclusion, confidence/rationale, false-friend gate, frozen replay lineage, guarded export, measured pilot result, unchanged Anki identity, and offline `validate`/`build`; record results and limitations in `specs/003-vocabulary-curation/validation-results.md`. If SC-006 or SC-009 fails, retain this task open, document the specific blocker and add bounded corrective delta tasks rather than claiming Feature 003 complete.
  - Closure: The matched T110 pilot ceased to be a closure gate. The converged v3.1 walkthrough and 137-card offline validation are recorded in convergence-report.md.
- [x] T050 [COMPLETE] Apply the historical contrast-only scope correction in `src/indo_malay_anki/curation/gate.py`, `src/indo_malay_anki/curation/export.py`, `data/vocabulary.tsv`, and `specs/003-vocabulary-curation/validation-results.md`: retire released `same` entries without reusing IDs and validate the offline build.

---

## Phase 7: Policy-v2 history and v3 foundation (shared prerequisites)

**Purpose**: Keep completed recalibration work checked while establishing a versioned v3 route. Existing uncommitted cache/provider/replay files are partial assets, not automatically complete tasks.

- [x] T051 [COMPLETE] Inventory 14 non-fixture batches, the separate fixture, historical 102/6/87/9 outcomes, three active learner cards, unavailable historical active-time/call/token/cost fields, and baseline tests in `specs/003-vocabulary-curation/validation-results.md` and `tests/integration/test_curation_baseline.py`.
- [x] T056 [COMPLETE] Add policy-v2 risk/typed-decision records with old-record defaults in `src/indo_malay_anki/curation/records.py` and `curation/config.json`; retain this as historical implementation, not the v3 acceptance rule.
- [x] T058 [COMPLETE] Add policy-v2 risk classification in `src/indo_malay_anki/curation/gate.py`; retain the completed code/history while replacing its strict evidence triggers under T090.
- [x] T059 [COMPLETE] Add policy-v2 evidence-sufficient ordinary fast gate and typed outcomes in `src/indo_malay_anki/curation/gate.py`; retain completed history while replacing ordinary acceptance under T090.
- [x] T060 [COMPLETE] Add policy-v2 targeted escalation and compatible-stage reuse in `src/indo_malay_anki/curation/workflow.py` and `src/indo_malay_anki/curation/packets.py`; preserve the work while introducing v3 dependencies under T092.
- [x] T080 [COMPLETE] Validate and freeze the exact 26 historical `(batch_id, candidate_id)` pairs, saved evidence/reviewer refs, five named diagnostic pairs, and baseline 0/25/1 plus later 1/24/1 comparator in `specs/003-vocabulary-curation/historical-hold-sample.json` and `specs/003-vocabulary-curation/validation-results.md`; label `kamera/kamera` outside the denominator if absent.
- [x] T081 [SUPERSEDED] Extend append-only policy-v3 risk, decision revision, accepted-only confidence tier/rationale/flags, relation-correction and legacy-reason alias schemas with old-record `not-assessed` defaults in `src/indo_malay_anki/curation/records.py` and `src/indo_malay_anki/curation/store.py`; add an immutable effective prompt-set reference per historical reconsideration attempt without changing its batch manifest, and preserve v1/v2 event reads and candidate IDs.
  - Closure: The specified generic reconsideration-attempt schema was not adopted. Existing append-only events, manifest pins, packet digests, and saved replay artifacts preserve the required history.
- [x] T082 [SUPERSEDED] [P] Add v3 schema/legacy-load/decision-lineage tests, including no accepted confidence on HOLD/REJECT and no history rewrite, in `tests/unit/test_curation_records.py`.
  - Closure: Tests now cover the active record/recovery behavior; tests for the unused reconsideration-attempt schema are unnecessary.
- [x] T083 [DEFERRED] Define centrally configured v3 per-candidate caps for verifier, targeted retrieval, adversary, conflict pass and malformed-output retry in `curation/config.json` and `src/indo_malay_anki/curation/workflow.py`; preserve Luna route and record cap exhaustion separately from linguistic defects.
  - Closure: Configurable per-candidate budgets belong to a future autonomous corpus-scaling runner. Feature 003 uses bounded one-shot operations, provider timeout, and no automatic recursive escalation.

**Checkpoint**: V3 records coexist with archives; the frozen sample is immutable and no learner data changes.

---

## Phase 8: User Story 1 — Grow Useful Contrasts Quickly (Priority: P1) 🎯 Optimistic MVP

**Goal**: Safe cheap no-contrast/duplicate filtering, compact independent verification, optimistic ordinary acceptance, explainable confidence and targeted high-risk escalation.

**Independent Test**: A seeded batch accepts a valid ordinary `similar` and straightforward `different-common-word` without mandatory source/adversarial calls; rejects confirmed duplicate and no-contrast; holds only a concrete unresolved material issue; keeps a false friend behind its strict gate; canonical TSV stays unchanged before export.

### Tests for User Story 1

- [x] T084 [ALREADY-SATISFIED] [P] [US1] Add deterministic fixtures for exact same ordinary meaning, same-form plausible false friend, useful `biskuit/biskut` similarity, duplicate, ambiguous cue and relation correction in `tests/unit/test_curation_gate.py` and `tests/unit/test_curation_duplicates.py`.
  - Closure: Current gate and duplicate tests cover confirmed same, false-friend exception, useful spelling contrast, cue ambiguity, and relation correction.
- [x] T085 [SUPERSEDED] [P] [US1] Add verifier packet contract tests for omitted generator rationale/old HOLD anchor, included concrete historical objections, bounded relevant evidence, prompt/input digests and schema rejection of malformed output in `tests/contract/test_curation_cli.py`; prove a historical reconsideration packet uses its pinned v3 attempt prompt, a normal new-batch packet uses its batch-manifest prompt, and neither rewrites the historical manifest.
  - Closure: Current verifier packets remain compact and separate from generation; historical replay used saved versioned artifacts instead of the proposed generic attempt-pin contract.
- [x] T086 [ALREADY-SATISFIED] [US1] After T084, add decision fixtures for named synonym versus concrete misleading preference alternative, missing evidence versus contradiction, neutral versus material region/register, generic hesitation, budget exhaustion and mandatory false-friend evidence/verifier/adversary in `tests/unit/test_curation_gate.py` and `tests/unit/test_curation_evidence.py`.
  - Closure: Current gate/evidence tests cover missing versus contradictory evidence, synonym/preference concerns, uncertainty, and strict false-friend gates.

### Implementation for User Story 1

- [x] T087 [ALREADY-SATISFIED] [US1] Implement policy-v3 cheap normalized same/no-contrast prescreen and duplicate handling, with false-friend/usage-divergence exception, legacy reason alias and separately counted `no-meaningful-cross-language-contrast`, in `src/indo_malay_anki/curation/gate.py` and `src/indo_malay_anki/curation/duplicates.py`.
  - Closure: The active gate performs cheap no-contrast rejection and duplicate review without discarding plausible false friends.
- [x] T088 [COMPLETE] [P] [US1] Create complete immutable policy-v3 prompt snapshot under `curation/prompts/versions/2.0.0/` by copying the latest role inventory and changing `independent-verification.md` and `adversarial-review.md` to use compact questions and concrete learner-risk reasons; update `curation/config.json` and `curation/prompts/manifest.json` so new batches select it while historical manifests retain their pinned versions.
- [x] T089 [SUPERSEDED] [US1] Build v3 verifier packets with only candidate fields, proposed relation, short relevant evidence and concrete prior objections in `src/indo_malay_anki/curation/packets.py`; select the reconsideration attempt's immutable v3 prompt reference for historical reruns while keeping manifest-pinned prompts for ordinary batches, retain blinded generation/verifier separation, and invalidate incompatible old results by effective prompt version, questions, input digest and upstream dependencies.
  - Closure: The active packet path is compact and digest-bound; the proposed generic historical attempt-reference route was replaced by frozen replay artifacts.
- [x] T090 [ALREADY-SATISFIED] [US1] Implement low/medium/high risk and ACCEPT/HOLD/REJECT in `src/indo_malay_anki/curation/gate.py`: verifier-agreed ordinary cards may ACCEPT without external evidence; a named synonym or absent frequency proof lowers confidence/flags but does not HOLD; specific plausible misleading preference triggers targeted research; real unresolved blockers HOLD; affirmative defects REJECT; false friends retain strict gates.
  - Closure: Policy v3.1 implements optimistic ordinary ACCEPT, concrete material HOLD, affirmative REJECT, and stronger false-friend review.
- [x] T091 [ALREADY-SATISFIED] [US1] Implement accepted-only high/medium/low/very-low confidence assignment, concise signal-based rationale, small structured review flags and relation-correction lineage in `src/indo_malay_anki/curation/gate.py` and `src/indo_malay_anki/curation/records.py`; never turn material blockers into accepted/very-low.
  - Closure: Accepted decisions carry exactly one explainable confidence tier, specific rationale, review flags, and relation-correction lineage.
- [x] T092 [ALREADY-SATISFIED] [US1] Route v3 low-risk verifier before evidence audit; conditionally invoke cached/targeted research for medium risk and mandatory false-friend review for high risk; record skipped-by-policy versus failed/missing stages and cap outcomes in `src/indo_malay_anki/curation/workflow.py`, `src/indo_malay_anki/curation/__main__.py`, and `src/indo_malay_anki/curation/packets.py` without rewriting v1/v2 history. In `src/indo_malay_anki/curation/bundle.py`, verify existing partial fan-out recovery and implement any missing candidate/input-digest checkpoint so interrupted ingestion resumes without recounting its provider operation or changing canonical data.
  - Closure: The v3.1 workflow supports verifier-first ordinary work, targeted evidence, mandatory false-friend review, skipped-stage status, and resumable bundle records.
- [x] T093 [ALREADY-SATISFIED] [US1] Reuse the existing `src/indo_malay_anki/curation/evidence_cache.py` and `src/indo_malay_anki/curation/evidence.py` only when a claim needs research; verify sense/locale/source-family relevance, preserve observation lineage, avoid mirrored-source double counts and do not infer preference from dictionary existence.
  - Closure: Claim-scoped cache and evidence tests retain source provenance and prevent dictionary existence from becoming preference proof.
- [x] T094 [ALREADY-SATISFIED] [US1] Add integration tests for low-risk no-research acceptance, medium targeted escalation, false-friend strict review, historical objection preservation, relation correction, interrupted/malformed role resume, partial bundle fan-out recovery by candidate/input digest with one provider operation count, budget caps and no canonical mutation in `tests/integration/test_curation_batch.py` and `tests/integration/test_curation_recovery.py`.
  - Closure: Existing batch, recovery, bundle, gate, and export integration tests cover the active failure and no-canonical-mutation paths.
- [x] T095 [ALREADY-SATISFIED] [US1] Expose v3 decisions and confidence in scratch `check`/`report` output, including no-contrast waste and exact HOLD blockers, in `src/indo_malay_anki/curation/report.py` and `src/indo_malay_anki/curation/__main__.py`; ensure the User Story 1 independent fixture passes without export.
  - Closure: The current check/report path exposes decisions, confidence, no-contrast counts, and unresolved reasons.

**Checkpoint**: Ordinary useful contrasts can ACCEPT cheaply; high-risk cases retain real gates; single-pass generation cannot self-approve.

---

## Phase 9: User Story 3 — Reconsider and Audit Existing Work (Priority: P2)

**Goal**: Recover historical false negatives without regeneration and prioritize future review by explained confidence.

**Independent Test**: Replay the same 26 IDs with preserved evidence/objections and no TSV mutation; every outcome has a reason, changed decisions retain lineage, and review selection includes low tiers plus a random/stratified sample of higher tiers.

### Tests for User Story 3

- [x] T096 [SUPERSEDED] [P] [US3] Add historical replay tests for stable `(batch_id, candidate_id)`, old-record defaults, effective-prompt-and-digest-compatible reuse, v3 verifier rerun from an old-version manifest, unchanged manifest and archived packet, legacy no-contrast alias, idempotent revision and no second permanent ID in `tests/integration/test_curation_recovery.py` and `tests/integration/test_historical_hold_experiment.py`.
  - Closure: Frozen historical replay and recovery tests preserve IDs and old artifacts; the prescribed generic v3 attempt-prompt rerun was not adopted.
- [x] T097 [SUPERSEDED] [P] [US3] Add deterministic review-priority, seeded random/stratified audit-selection, selected-card independent audit result persistence and batch-close nonzero-sample tests across available accepted confidence tiers in `tests/unit/test_curation_report.py` and `tests/integration/test_curation_audit.py`.
  - Closure: The mandatory batch-close random sample was replaced by ongoing random QA monitoring. Seeded risk/stratified selection remains implemented and tested.

### Implementation for User Story 3

- [x] T098 [SUPERSEDED] [US3] Add a policy-v3 `reconsider` route or equivalent in `src/indo_malay_anki/curation/workflow.py` and `src/indo_malay_anki/curation/__main__.py` that records/selects the immutable v3 attempt prompt reference without repinning the historical manifest, reuses saved candidate/evidence/objection IDs, reruns only effective-prompt/question/digest-incompatible stages, appends old/new outcome, risk, relation, confidence, flags and changed-decision reason, and exposes a reconciled current-decision/report view for closed historical batches without rewriting archived reports or regenerating a candidate.
  - Closure: The bounded historical reconsideration was completed through saved replay artifacts; a permanent generic reconsider CLI route was not adopted.
- [x] T099 [SUPERSEDED] [US3] Implement confidence-priority review listing and a batch-close reproducible nonzero bounded random/stratified sample across available accepted tiers in `src/indo_malay_anki/curation/report.py` and `src/indo_malay_anki/curation/workflow.py`; route selected cards to a separate post-acceptance AI audit, recording seed, eligible universe, selected IDs, audit result/evidence and empty-tier reasons separately from mandatory curation decisions. Make sample size configurable from observed quality rather than a fixed percentage, and never silently change canonical TSV from an audit result.
  - Closure: Confidence-priority and reproducible selection exist, but random review is ongoing QA rather than a mandatory batch-close promotion stage.
- [x] T100 [SUPERSEDED] [US3] Before T101 or T037, instrument the minimum replay-to-export wall-clock interval, per-candidate duration, unique provider operation IDs, verifier/adversarial call counts, token-availability fields, retrieval/cache counts and export timing in `src/indo_malay_anki/curation/store.py`, `src/indo_malay_anki/curation/workflow.py`, and `src/indo_malay_anki/curation/export.py`; add a fake-provider/partial-bundle check in `tests/integration/test_curation_metrics.py`. Mark historical unmeasured work unavailable.
  - Closure: Measured experiments used their saved operation/timing artifacts and labeled unrecoverable history unavailable; the old matched replay-to-export interval was not adopted.
- [x] T101 [EXPERIMENT-COMPLETED] [US3] After T100, run the bounded v3 replay on exactly the T080 frozen 26 IDs and write per-candidate outcomes, five diagnostics, separate `kamera/kamera` scope check if needed, recovered/held/rejected counts, exact remaining blockers, suspicious accepts, reused/new work, full experiment wall-clock, per-candidate durations, unique calls, available tokens and retrieval/cache counts to `specs/003-vocabulary-curation/validation-results.md` and a versioned replay artifact under `specs/003-vocabulary-curation/`; do not call `export` or generate a new batch.
  - Closure: The frozen 26-ID optimistic replay ran without generation or promotion; see optimistic-policy-replay.md and optimistic-replay-report.json.

**Checkpoint**: Historical recovery is measured on the same sample before any new generation or canonical promotion.

---

## Phase 10: User Story 2 — Study a Neutral, Stable Card (Priority: P1)

**Goal**: Promote only current v3 ACCEPT concepts after replay review, preserving deterministic source and Anki identity.

**Independent Test**: An isolated accepted-only export rejects duplicate/same/HOLD input, preserves assigned IDs and note GUIDs, and builds an offline package with a neutral front and both back answers; false-friend contrast remains back-only.

### Tests for User Story 2

- [x] T102 [ALREADY-SATISFIED] [P] [US2] Extend accepted-only export and learner-source tests for v3 confidence metadata exclusion, same/duplicate rejection, replay acceptance requiring current decision recheck, unchanged ID/GUID and interrupted transaction recovery in `tests/integration/test_curation_export.py`, `tests/unit/test_validator.py`, and `tests/integration/test_semantic_rebuild.py`.
  - Closure: Current export, validator, semantic-rebuild, and T114–T115 regressions cover accepted-only source, same/duplicate refusal, stable IDs/GUIDs, and transaction recovery.

### Implementation for User Story 2

- [x] T103 [SUPERSEDED] [US2] Adapt current-decision/report checks in `src/indo_malay_anki/curation/export.py` to consume T098's reconciled policy-v3 decision view for closed historical batches while retaining the existing ledger/journal transaction, cross-batch overlap screen, back-only contrast projection and no curation metadata in `data/vocabulary.tsv`; do not assign a second ID to a recovered concept, and reject stale or unreconciled report versions.
  - Closure: Historical cohorts used separately guarded promotion; T114–T115 now bind general v3.1 export to the closed decision, final content, audit eligibility, and existing journal/ledger checks.
- [x] T104 [EXPERIMENT-COMPLETED] [US2] Add a controlled end-to-end promotion walkthrough for only gate-valid recovered concepts, canonical versus experimental count reconciliation, unchanged concept IDs and offline package assertions in `tests/integration/test_curation_export.py` and `specs/003-vocabulary-curation/validation-results.md`; run actual guarded promotion under T037 after inspecting T101.
  - Closure: The audited historical cohort was corrected, guarded-promoted, and verified by an offline package build; see guarded-promotion.md.

**Checkpoint**: Learner data changes only through guarded export, and package identity remains stable.

---

## Phase 11: User Story 4 — Evaluate AI Productivity (Priority: P2)

**Goal**: Measure accepted-card throughput and cost together with quality, without making human review a routine gate.

**Independent Test**: A report distinguishes experimental replay accepts from canonical promotions, gives real elapsed/card work where measured, marks unavailable fields honestly, and includes confidence/no-contrast/fast-path distribution; a small expert benchmark supplies a comparable future ratio denominator.

### Tests for User Story 4

- [x] T105 [DEFERRED] [P] [US4] Add metric fixtures for unique bundled operation counts, cache hits/misses, replay-only versus canonical cards, zero-card undefined work/card, unavailable historical/provider fields, overlapping wall-clock work, confidence/no-contrast/path distributions, and correction/removal/relation-change/audit-failure rates by confidence tier when outcome data exists in `tests/unit/test_curation_report.py` and `tests/integration/test_curation_metrics.py`.
  - Closure: A reusable all-metrics fixture matrix belongs to future scaling telemetry. Saved Feature 003 batch reports distinguish observed, estimated, and unavailable measures.

### Implementation for User Story 4

- [x] T106 [DEFERRED] [US4] Extend the minimum T100 instrumentation into complete provider/retrieval operation records and compact verifier call/timing/token capture where available in `src/indo_malay_anki/curation/store.py`, `src/indo_malay_anki/curation/workflow.py`, and `src/indo_malay_anki/curation/__main__.py`; count unique provider operations rather than bundle fan-out events, mark unrecorded manual work unavailable, and record generation-to-guarded-export intervals for matched policy lanes.
  - Closure: A generic provider/retrieval telemetry layer is future autonomous-run infrastructure. Bounded experiments saved available call, token, timing, and audit work separately.
- [x] T107 [DEFERRED] [US4] Extend `src/indo_malay_anki/curation/report.py` with decision, relation, risk/path, confidence, no-contrast, escalation, recovery, cache, calls/tokens/retrievals and canonical accepted-card throughput; use a single measured generation-to-export wall-clock interval, explicit pause accounting, a labeled price table only if available, and separate ordinary/escalated/false-friend views. Join recorded corrections, removals, relation changes and T099 audit findings to the accepted concept ID and its tier at the relevant release; report per-tier rates with eligible denominators or explicit unavailable values when lineage/outcomes are absent.
  - Closure: A consolidated generic CLI throughput report is future scaling work. Feature 003 saved batch reports distinguish provisional decisions, audit, promotion, and unavailable end-to-end measures.
- [x] T108 [DEFERRED] [US4] Freeze a versioned pass/fail/unresolved quality rubric and matched category/risk/source-access protocol before either timed AI lane or the expert exercise, then conduct and report a small observed experienced-human benchmark on representative unseen ordinary concepts in `specs/003-vocabulary-curation/validation-results.md`; record expert active time, accepted and independently audit-passing card counts, findings and audit time separately, without making human approval a per-card workflow gate.
  - Closure: An empirical expert-human benchmark belongs to later product-economics evaluation; FR-032 and SC-010 explicitly exclude it from Feature 003 closure.
- [x] T109 [WONT-DO] [US4] Before the measured pilot, implement a digest-manifested atomic handoff for isolated candidate/evidence/operation/audit artifacts in `src/indo_malay_anki/curation/handoff.py` with corrupt/incomplete/conflicting-batch, candidate-local ID reuse, idempotent retry and no-canonical-mutation tests in `tests/integration/test_curation_handoff.py`; exclude pilot TSV, temporary ledger and provisional IDs, preserve original decisions and audit digests, recheck current canonical overlap, and append linked decision revisions when the current gate changes an outcome.
  - Closure: The isolated atomic handoff was solely for the rejected T110 matched-pilot design. Current guarded export retains the required ID/journal safeguards.
- [x] T110 [WONT-DO] [US4] Only in a later user continuation after T101 findings have been reported, T037 and T106–T109, run one bounded matched conservative-policy versus policy-v3 ordinary cohort with candidate IDs and exclusions frozen before decisions, equivalent source/cache access, dedicated noninterleaved generation-to-guarded-export wall-clock intervals, and the T108 frozen quality rubric in isolated workspaces; audit every comparator and v3 exported card under that rubric, bind each finding to a digest of final cue/sense, answers, relation, contrast and supporting claim/evidence set, and count only passing final-digest-matched **canonical pilot** v3 promotions in quality-adjusted output. Use T109 to import and recheck the isolated v3 artifacts, then promote only current v3 gate-valid cards through `src/indo_malay_anki/curation/export.py`; report comparator versus canonical pilot quality-adjusted cards/hour, material defects, recovered false negatives, nonmaterial ordinary HOLD share, cohort mismatches, and AI/expert ratio or unavailable reason in `specs/003-vocabulary-curation/validation-results.md`. Keep historical promotions outside the pilot numerator and interval; start no new cohort before the frozen 26 replay, and do not treat ~50× as a release gate.
  - Closure: Convergence removed the matched conservative-v3 pilot as a completion gate after multiple bounded fresh-batch quality audits. Do not run this pilot to close Feature 003.
- [x] T111 [SUPERSEDED] [US4] Use T110's measured no-contrast rejection rate and examples to copy the complete 2.0.0 role inventory into immutable `curation/prompts/versions/2.1.0/`, revise only its `generate.md` toward useful contrasts, update `curation/config.json` and `curation/prompts/manifest.json` so future batches select the new version without overwriting older snapshots, verify it against a fixed bounded example set in `tests/contract/test_curation_cli.py`, and report before/after no-contrast behavior without claiming general linguistic accuracy.
  - Closure: Later immutable prompt versions and measured no-contrast feedback replaced the T110-dependent generator comparison; production remains on prompt set 2.4.0.

**Checkpoint**: Productivity claims count actual learner cards and include quality context; historical missing time is not fabricated.

---

## Phase 12: Polish and cross-cutting validation

- [x] T112 [SUPERSEDED] After T111, update `README.md`, `specs/003-vocabulary-curation/quickstart.md`, `curation/prompts/README.md`, and affected CLI/readme contract tests for v3 optimistic acceptance, confidence flags, no-contrast filtering, targeted research, measured generator feedback, false-friend strict review, fallibility and the offline build boundary.
  - Closure: The final README, quickstart, spec, and convergence report describe v3.1. The T110-dependent documentation sequence and measured-pilot premise were replaced by convergence documentation.
- [x] T113 [ALREADY-SATISFIED] Run the project test/lint/format suite plus offline `validate`/`build`; inspect policy-v3 end-to-end fixtures, release-workflow AI isolation and unchanged five-field Anki model; record commands/results and remaining limitations in `specs/003-vocabulary-curation/validation-results.md` before completing T049.
  - Closure: Final closure validation recorded 220 tests passing, Ruff checks, source validation, offline 137-card build, and ID/GUID uniqueness; see convergence-report.md.

---

## Supersession map for old open task descriptions

Old open T052–T055 (new calibration/cohort prerequisites) map to T080, T105–T110 after replay. Old T057 and T061–T062 map to T084–T095. Old T063–T071 (cache, budgets, concurrency) map to T083, T092–T094, T106 and later bounded optimization; their existing partial artifacts are retained. Old T072–T074 map to T096–T101. Old T075–T077 (heavy comparator/ratio design) map to T105–T110 after replay. Old T078–T079 map to T103/T109/T112, including T109's guarded isolated handoff. This mapping is historical, not a current dependency graph. The later explicit terminal statuses govern these task IDs; no generation or universal evidence gate is reopened.

## Historical dependencies and execution order (archived, non-executable)

The following sequence records the abandoned 2026-10-13 implementation schedule. It is not a current instruction to run the matched pilot, mandate random audit before promotion, or generate vocabulary.

```text
Completed T001–T051 and T056/T058–T060
    -> T080–T083 v3 foundation
    -> T084–T095 US1 optimistic gate and tests (MVP process slice)
    -> T096–T099 and T100 minimum telemetry -> T101 US3 frozen 26 replay
    -> T102–T104 and T037 US2 guarded promotion/offline build
    -> T105–T108 US4 complete metrics/observed benchmark
    -> T109 isolated handoff -> T110 measured matched pilot -> T111 generator feedback
    -> T112–T113 and T049 final documentation/validation
```

US1 can be tested on scratch fixtures without US2. US3 depends on the US1 policy but is independently tested using frozen historical artifacts. US2 depends on current US1 decisions and US3 replay review. T100's minimum telemetry precedes T101 and T037; T106 expands it for T110. US4 can prepare metric tests and the benchmark protocol alongside some US1/US3 work, but its new cohort waits until T101 and T037. Shared export and ID allocation remain serialized.

### Parallel opportunities

- T082 and T083 touch different schema/config surfaces after T081; coordinate the shared `workflow.py` edit before concurrent work.
- T084 and T085 test different gate/packet areas and can be prepared in parallel; T086 follows T084 because both edit the gate test file. T088 prompt files can proceed alongside T087 no-contrast code; T089 waits for the prompt contract.
- T096 and T097 target distinct historical-replay and review-priority tests. T102 export tests can be prepared while T101 replay is finishing, but T104 waits for its inspection.
- T105 reporting fixtures and T108 benchmark preparation may proceed after the metric boundary is fixed; T109 handoff can be built from fixtures before T110, which waits for T101, T037 and T106–T109. T111 follows T110's measured no-contrast result.

## Historical implementation strategy (archived, non-executable)

**MVP**: Finish T080–T095 and prove an ordinary verifier-agreed contrast can ACCEPT with explained confidence and without universal research, while confirmed same/duplicates reject and false friends retain strict review. Then stop at the T101 frozen replay checkpoint before any new vocabulary batch.

**Incremental delivery**: Inspect T101 recovery and quality; use T037/T102–T104 for accepted-only canonical promotion; complete T105–T108 observed benchmark and reports; run the bounded matched T110 pilot to evaluate SC-006/SC-009, then T111 generator feedback and T112–T113/T049 offline validation. Later routine batches use the same bounded v3 process and are not a substitute for the frozen replay or measured pilot.

## Notes

- Tests verify process mechanics, not linguistic truth; sampled audits evaluate actual content.
- Checked historical tasks preserve their completion status but do not certify policy-v3 acceptance.
- The former T080–T113 ordering and T037/T049 dependencies describe the old plan only. The terminal dispositions above and the final convergence decision supersede them.
- [P] means different files and no unfinished dependency; shared mutable manifest, duplicate decision and ID/export operations stay serialized.

## Phase 13: Convergence

The 2026-10-15 architecture review froze production policy v3.1. Risk-selected independent audit is pre-promotion; random audit is ongoing QA monitoring, not a mandatory release gate. The earlier task list remains historical; T114–T115 closed the two general guarded-export gaps without changing learner data. See [convergence report](convergence-report.md).

- [x] T114 [COMPLETE] Make the existing `curation export` path require linked independent audit clearance or an explicitly adopted batch audit policy before promoting a policy-v3.1 ACCEPT; refuse unaudited provisional cards by default, unsafe/held/rejected audit results, stale corrections, and batch safety-brake violations, while preserving current ID/journal transactions and archived decisions. Add bypass and idempotent retry tests in `tests/integration/test_curation_export.py` per FR-035 (partial).
  - Closure: Risk-selected candidates require independent clearance; otherwise eligible clean cards do not wait for random QA. Missing, withheld, unresolved, stale, or safety-braked eligibility blocks export.
- [x] T115 [COMPLETE] Make `curation export` project the final verified relation and validated cue/answer/false-friend contrast, and compare current decision plus content digests with the closed report and audit clearance before ID assignment. Do not silently use an earlier `relation-proposal` when verification corrected it; retain original and corrected relation history. Add corrected-relation and stale-content regression tests per FR-012 (partial).
  - Closure: Export uses final verified relation and resolved content, binds clearance to decision/content digests, and preserves ID-derived Anki GUIDs.

Phase 13 closure note (2026-10-15): T114 implements risk-selected pre-promotion clearance and explicit eligibility; clean accepted cards may export without random selection. T115 exports final verified content while preserving permanent identity. Production policy v3.1 and the 137-card corpus remain unchanged.

## Remaining REQUIRED-INCOMPLETE tasks

None.

## Deferred future work (outside Feature 003 closure)

T083 and T105–T108 concern general per-candidate budget controls, consolidated autonomous-run telemetry, and an empirical expert-human benchmark. Future corpus-scaling/product-economics work may also evaluate 100+ candidate runs, audit cost, post-release QA correction rates, and better models. These are not release gates for Feature 003. The approximately 50× expert-human target remains an unmeasured north star; no human rate is invented.

## Experimental disposition and final acceptance

The strict ordinary evidence-heavy policy and universal adversarial review were replaced by optimistic ordinary acceptance plus strict false-friend review. The competing-form challenge, universal localized-standard and technical-borrowing gates, revised Luna verifier, default Sol escalation, and cheap universal audit screen were evaluated and not deployed; their saved benchmark artifacts remain available. Preference-sensitive evidence and structured risk flags remain targeted inputs to curation and audit routing, not universal HOLD rules. The audit-router and random-budget experiments are complete; random QA remains intentional monitoring rather than a pre-promotion condition.

The final specification's mandatory criteria are represented by terminal implementation and validation tasks: AI-first separate verification, contrast-only learner relations, strict false-friend gate, explainable decisions/confidence, historical replay, guarded export, stable ID/GUID identity, risk-selected audit clearance, deterministic offline build, and explicit reporting of quality/throughput limits. Zero linguistic errors, elimination of independent audit, fully autonomous scale, 50× human throughput, and deployment of negative experiments are not Feature 003 closure gates.

**FEATURE 003 TASKS RECONCILED — CLOSURE READY**
