---
description: "Dependency-ordered implementation tasks for Feature 003"
---

# Tasks: AI-First Vocabulary Curation

**Input**: Design documents in `specs/003-vocabulary-curation/`: [spec](spec.md), [plan](plan.md), [research](research.md), [data model](data-model.md), [workflow contract](contracts/curation-workflow.md), [learner-source contract](contracts/learner-source.md), and [quickstart](quickstart.md).

**Tests**: Included because the spec's quality gates and constitution require deterministic verification of source parsing, IDs, package identity, and failure behavior. Seeded tests establish that gates reject known bad records; they do not establish linguistic truth.

**Organization**: Tasks are grouped by user story. `[P]` denotes independent work in different files after its stated prerequisites; it does not authorize skipping a dependency or quality gate. All initial-corpus AI research must preserve evidence and stage artifacts.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish inspectable curation locations and one configuration boundary without changing the offline builder.

- [X] T001 Create the curation package entrypoints and repository directories in `src/indo_malay_anki/curation/__init__.py`, `src/indo_malay_anki/curation/__main__.py`, `curation/prompts/README.md`, and `curation/batches/.gitkeep`.
- [X] T002 [P] Define centralized provider/model, prompt-set version, and batch defaults in `curation/config.json`, keeping credentials and network settings out of the deck build path.
- [X] T003 [P] Define the versioned role inventory and structured-response references in `curation/prompts/manifest.json` for generation, both locale researchers, relation proposal, evidence audit, independent verification, adversarial review, and semantic overlap.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Provide the shared record and persistence rules on which each story depends.

- [X] T004 Implement validated batch, candidate, claim, evidence, overlap, stage-result, per-stage completion status, pending/final decision, and structured false-friend contrast records in `src/indo_malay_anki/curation/records.py`, including candidate-local IDs and no permanent ID before acceptance.
- [X] T005 Implement append-only, atomic stage-record persistence and manifest loading in `src/indo_malay_anki/curation/store.py`, preserving raw malformed responses and prior revisions for audit and resumability.
- [X] T006 Add record/schema tests for missing fields, invalid roles, source-group metadata, candidate limits, and read-after-interruption behavior in `tests/unit/test_curation_records.py`.

**Checkpoint**: Structured, versioned curation records can be created and safely resumed without touching `data/vocabulary.tsv`.

---

## Phase 3: User Story 1 — Curate a Trustworthy Batch (Priority: P1) 🎯 MVP

**Goal**: AI roles produce separately inspectable candidate, research, challenge, and decision artifacts; unsupported or disputed entries are held or rejected.

**Independent Test**: Run a bounded scratch batch with an ordinary supported pair, unsupported everyday preference, ambiguous cue, duplicate, and suspected false friend. Inspect separate role records and evidence, then confirm only fully gated candidates are accepted in the batch decision output.

### Tests for User Story 1

- [X] T007 [P] [US1] Add command-contract tests for `init`, `packet`, `ingest`, `check`, `finalize-hold`, and `report`, including malformed/out-of-order AI output, pending batch closure refusal, and verifier blindness, in `tests/contract/test_curation_cli.py`.
- [X] T008 [P] [US1] Add seeded decision-gate tests for independent source groups, claim coverage, separate audit observation/method versus a model-supplied flag, dictionary-only preference, conflicting evidence, model self-rating, ambiguous cues, evidenced structured false-friend contrast, and all-stage completion for acceptance versus recorded uncompleted stages for early final decisions in `tests/unit/test_curation_gate.py`.
- [X] T009 [P] [US1] Add within-batch exact, morphology, synonym, and semantic-overlap fixtures, including explicit distinct-sense resolution, in `tests/unit/test_curation_duplicates.py`.

### Implementation for User Story 1

- [X] T010 [P] [US1] Write versioned candidate-generation and normalization/overlap role prompts with structured output requirements in `curation/prompts/generate.md` and `curation/prompts/overlap.md`.
- [X] T011 [P] [US1] Write separate Indonesian-usage and Malaysian-usage role prompts covering contemporary common use, sense, register, region, alternatives, and evidence needs in `curation/prompts/indonesian-usage.md` and `curation/prompts/malaysian-usage.md`.
- [X] T012 [P] [US1] Write relation-proposal and evidence-audit role prompts that distinguish existence from preference and require inspection of claim-specific external sources in `curation/prompts/relation-proposal.md` and `curation/prompts/evidence-audit.md`.
- [X] T013 [P] [US1] Write blinded independent-verification and adversarial-review role prompts, including false-friend counterexamples and explicit agreement or objection outputs, in `curation/prompts/independent-verification.md` and `curation/prompts/adversarial-review.md`.
- [X] T014 [US1] Implement prompt packet construction and role-specific context allowlists in `src/indo_malay_anki/curation/packets.py`; omit generator rationale and preferred verdict from independent-verifier packets, record input/upstream digests, and invalidate stale downstream results after cue, answer, relation, evidence, or prompt-version changes.
- [X] T015 [US1] Implement batch initialization, structured response ingestion, ordering checks, prompt/model/tool provenance, and resumable failure records in `src/indo_malay_anki/curation/workflow.py`.
- [X] T016 [US1] Implement deterministic comparison keys and within-batch exact/morphology screening, with AI-reviewed semantic-overlap resolutions and unresolved-overlap blocking, in `src/indo_malay_anki/curation/duplicates.py`.
- [X] T017 [US1] Implement claim-to-evidence auditing and independent underlying-source counting in `src/indo_malay_anki/curation/evidence.py`; require a separate audit record with access method, page location/query, observed content, timestamp, and claim linkage before support counts, so bare AI flags, copied sources, and dictionary-only preference cannot pass.
- [X] T018 [US1] Implement the deterministic `pending`/`accepted`/`hold`/`rejected` gate in `src/indo_malay_anki/curation/gate.py`, including explicit finalization of investigated holds, completed stages for acceptance, uncompleted-stage statuses and reasons for early holds/rejections without fabricated role outputs, verifier/adversary agreement, contradictions, structured false-friend contrast, and reason codes.
- [X] T019 [US1] Implement provisional and final batch reports in `src/indo_malay_anki/curation/report.py`; require generated = accepted + held + rejected + pending while open, require pending = 0 and generated = accepted + held + rejected to close, and include relation, duplicate, investigation, and verification summaries even for zero-acceptance batches.
- [X] T020 [US1] Wire the curation subcommands, including `finalize-hold`, to the workflow, gate, and report in `src/indo_malay_anki/curation/__main__.py`; ensure no command except later `export` can alter canonical learner data.
- [X] T021 [US1] Add a full scratch-batch integration scenario with separate stage records, an accepted ordinary concept, held/rejected seeded faults, and no mutation of `data/vocabulary.tsv` in `tests/integration/test_curation_batch.py`.

**Checkpoint**: One batch can be generated, researched, verified, challenged, and closed with auditable outcomes; a single AI pass cannot approve its own content.

---

## Phase 4: User Story 2 — Study the Initial Library (Priority: P1)

**Goal**: Promote only accepted concepts into stable source data, build a useful initial deck, and preserve existing Anki identity and import behavior.

**Independent Test**: Review the accepted corpus for at least three practical categories and all three eligible learner relations, inspect the package for one note/card per ID and back-only false-friend contrasts, then import an old and updated package into the same Anki Desktop test profile.

### Tests for User Story 2

- [X] T022 [P] [US2] Add strict eight-column learner-source tests for relation enum, false-friend contrast required/otherwise empty, legacy ID preservation, whitespace, malformed rows, and existing media rules in `tests/unit/test_loader.py` and `tests/unit/test_validator.py`.
- [X] T023 [P] [US2] Add package tests for unchanged five-field note schema, deck/model IDs, `000001 -> D6BBAuKXK`, one note/card, neutral front, escaped back-only contrast, and ordinary answer purity in `tests/integration/test_build_package.py` and `tests/integration/test_semantic_rebuild.py`.
- [X] T024 [P] [US2] Add export tests for accepted-only promotion, pending-batch refusal, cross-batch semantic overlap, retired-ID non-reuse, idempotent re-export, injected failure at each TSV/ledger replacement, and interrupted-journal recovery in `tests/integration/test_curation_export.py`.

### Implementation for User Story 2

- [X] T025 [US2] Extend `VocabularyConcept` with relation and contrast while preserving ID-only GUID constants and existing field behavior in `src/indo_malay_anki/model.py`.
- [X] T026 [US2] Parse the exact `id,english,indonesian,malaysian,relation,image,tags,contrast` header and values without linguistic normalization in `src/indo_malay_anki/loader.py`.
- [X] T027 [US2] Validate relation values and contrast rules before package generation while retaining existing ID, whitespace, and media checks in `src/indo_malay_anki/validator.py`.
- [X] T028 [US2] Project an escaped false-friend contrast as a secondary back-only block in the existing `Malaysian` note field, leaving the five Anki field names/order, front template, model ID, deck ID, GUID namespace, and one-card template unchanged in `src/indo_malay_anki/builder.py`.
- [X] T029 [US2] Implement logically append-only assignment records, legacy `000001` backfill, and active/retired status derived from current TSV membership in `src/indo_malay_anki/curation/ids.py` and `curation/id-ledger.json`.
- [X] T030 [US2] Implement guarded accepted-only, idempotent multi-batch export in `src/indo_malay_anki/curation/export.py`: screen all promotion batches against one another and archives before ID allocation, refuse pending or newly overlapping candidates until decisions/reports are revised, validate prospective `data/vocabulary.tsv` and `curation/id-ledger.json`, use `curation/export-journal.json` with backups, replace ledger then TSV, roll back handled failures, and recover interruptions before another export.
- [X] T031 [US2] Add repeatable `--batch` export inputs and recovery behavior to `src/indo_malay_anki/curation/__main__.py` and update exact TSV/package interface expectations in `tests/contract/test_cli_contract.py` and `tests/conftest.py`.
- [X] T032 [US2] Retrospectively curate the existing car concept through all gates in `curation/batches/transportation-001/`; retain `000001` only if accepted, otherwise retire it after other accepted rows exist.
- [X] T033 [P] [US2] Curate up to 12 transportation candidates through applicable curation stages; require every role and evidence gate for acceptance, and record reasons and unfinished-stage statuses for early holds or rejections in `curation/batches/transportation-001/`.
- [X] T034 [P] [US2] Curate up to 12 home candidates through applicable curation stages; require every role and evidence gate for acceptance, and record reasons and unfinished-stage statuses for early holds or rejections in `curation/batches/home-001/`.
- [X] T035 [P] [US2] Curate up to 12 food candidates through applicable curation stages; require every role and evidence gate for acceptance, and record reasons and unfinished-stage statuses for early holds or rejections in `curation/batches/food-001/`.
- [X] T036 [P] [US2] Curate up to 12 common-verb candidates through applicable curation stages; require every role and evidence gate for acceptance, and record reasons and unfinished-stage statuses for early holds or rejections in `curation/batches/common-verbs-001/`.
- [ ] T037 [US2] Resolve overlap across all initial batches, export only accepted candidates into `data/vocabulary.tsv`, build `dist/myid-anki.apkg`, and record accepted count, category/relation coverage, and gate-based exclusions in `specs/003-vocabulary-curation/validation-results.md`; if fewer than 24 accepted concepts or fewer than three categories/relations remain, curate another bounded batch and leave SC-003 incomplete until it passes without weaker gates.
- [X] T038 [US2] Perform and record old-to-new Anki Desktop import/update acceptance for retained `000001` or a controlled same-ID fixture if it is retired, including client version, import settings, note/card counts, unchanged GUID, updated content, and scheduling in `specs/003-vocabulary-curation/validation-results.md`; validate back-only contrast with an accepted false friend or separate fixture, never promote weak content for the check, and block release if existing-note updates fail.

**Checkpoint**: The initial corpus is useful and varied, every released row has accepted provenance, and a previously imported concept remains the same Anki note.

---

## Phase 5: User Story 3 — Grow and Audit Later Batches (Priority: P2)

**Goal**: Run subsequent batches without semantic duplicate IDs, recover from interrupted research, and inspect why each candidate was accepted or withheld.

**Independent Test**: Propose a released concept under a new English synonym in a later batch, interrupt a stage, resume, and inspect its overlap resolution, report, retained provenance, and unchanged canonical data until export.

### Tests for User Story 3

- [X] T039 [P] [US3] Add later-batch tests for cross-batch synonyms, prior held/rejected matches, explicit distinct meanings, and zero accidental ID assignment to duplicates in `tests/integration/test_curation_growth.py`.
- [X] T040 [P] [US3] Add interruption-to-pending, early final hold/rejection with uncompleted-stage status, malformed-output, unchanged-stage reuse, stale-verification after cue/answer/relation/evidence or prompt changes, zero-acceptance, open/closed report-reconciliation, and canonical-source-immutability cases in `tests/integration/test_curation_recovery.py`.

### Implementation for User Story 3

- [X] T041 [US3] Add early cross-batch overlap warnings while a later candidate is researched, comparing accepted TSV concepts and prior candidate archives in `src/indo_malay_anki/curation/duplicates.py`; preserve merge/reject/distinct rationale, while T030 remains the mandatory final pre-ID safeguard.
- [X] T042 [US3] Make interrupted-stage replay and material-edit invalidation explicit and idempotent, without losing prior responses, in `src/indo_malay_anki/curation/workflow.py` and `src/indo_malay_anki/curation/store.py`.
- [X] T043 [US3] Extend `report.json` with open-batch pending counts, per-relation final outcomes, duplicate and correction counts, evidence failures, and stable reason codes that can support later quality metrics in `src/indo_malay_anki/curation/report.py`.
- [X] T044 [US3] Add a documented later-batch duplicate/recovery example with retained stage artifacts in `curation/batches/growth-audit-001/`; keep it out of learner data unless its candidates independently pass all gates.

**Checkpoint**: A second batch can reuse the same process, explain its decisions, and avoid accidental duplicate concept IDs.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Make the workflow understandable and complete the project-wide gates.

- [X] T045 [P] Update `README.md` with AI-first rationale and fallibility, stage roles, evidence and common-use rules, false-friend and duplicate handling, source schema, batch commands, hold/reject semantics, and the offline build boundary.
- [X] T046 [P] Update source/package contract tests and contributor wording for the eight-column accepted source while preserving historical Feature 001 artifacts in `tests/contract/test_readme_contract.py` and `tests/contract/test_template_contract.py`.
- [X] T047 Add a deterministic preflight for tracked or incomplete `curation/export-journal.json`, keep `.github/workflows/release.yml` limited to accepted-source validation/build with no AI or live research calls, ignore transient journal/backups in `.gitignore`, and cover the workflow boundary in `tests/contract/test_release_workflow_contract.py`.
- [X] T048 Run `pytest`, `ruff check .`, `ruff format --check .`, offline `python -m indo_malay_anki validate`, and offline `python -m indo_malay_anki build`; confirm the release workflow invokes neither curation nor AI/live research, and record results plus 12-candidate curation-check timing in `specs/003-vocabulary-curation/validation-results.md`.
- [ ] T049 Audit `specs/003-vocabulary-curation/quickstart.md` against the final command behavior and record the completed initial-corpus, negative-gate, and compatibility walkthroughs in `specs/003-vocabulary-curation/validation-results.md`.
- [X] T050 Apply the contrast-only scope correction: retire previously released `same` entries without reusing IDs, reject `same` and mislabeled identical ordinary forms at curation/export/source-validation boundaries, revise versioned prompts and source contracts, close the bounded school trial with auditable decisions, and rerun offline validation/build plus deterministic tests.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** has no prerequisite. T002 and T003 can proceed alongside T001 because they write different files.
- **Foundational (Phase 2)** follows setup; record schemas and atomic store must exist before stage workflows.
- **US1 (Phase 3)** follows foundation. The seeded tests describe required failures first; prompt files can be authored in parallel. Packet, ingest, evidence, duplicate, gate, CLI, and integration work then follow their data dependencies.
- **US2 (Phase 4)** depends on US1's accepted decision records. Its parser/build tests and export tests can be prepared in parallel. Four topic batches may be curated in parallel after the pipeline is stable, but T030/T037 must screen their union for semantic overlap before any ID assignment/export.
- **US3 (Phase 5)** depends on the US1 pipeline and a released or fixture-backed US2 corpus for cross-batch duplicate comparisons. Its tests can be prepared in parallel.
- **Polish (Phase 6)** follows the desired stories; documentation tasks may start earlier once interfaces stabilize.

### User Story Dependencies

```text
Setup -> Foundation -> US1 batch decisions -> US2 accepted corpus/package -> US3 repeat growth
                                      \-> US3 recovery design can begin early
```

- **US1** is the MVP process slice: it proves independent, evidence-based decisions without changing learner data.
- **US2** consumes US1 decisions and independently proves source promotion and a studyable deck.
- **US3** consumes the same stable process and independently proves later-batch overlap, audit, and recovery behavior.

### Parallel Opportunities

- In **US1**, T007–T009 test files and T010–T013 prompt groups touch different files; they can progress independently after foundation.
- In **US2**, T022–T024 test areas can be prepared independently. T033–T036 topic batches can run concurrently after the gate is stable, but T030/T037 must reconcile overlap across all four before assigning IDs or updating source.
- In **US3**, T039 and T040 target separate integration scenarios.
- T045 and T046 update separate documentation/test files.

## Parallel Example: User Story 1

```text
Task: T007 curation CLI contract scenarios in tests/contract/test_curation_cli.py
Task: T008 evidence and decision-gate scenarios in tests/unit/test_curation_gate.py
Task: T010 candidate/overlap prompts in curation/prompts/generate.md and overlap.md
Task: T011 locale research prompts in curation/prompts/indonesian-usage.md and malaysian-usage.md
```

## Parallel Example: User Story 2

```text
Task: T033 transportation batch artifacts in curation/batches/transportation-001/
Task: T034 home batch artifacts in curation/batches/home-001/
Task: T035 food batch artifacts in curation/batches/food-001/
Task: T036 common-verbs batch artifacts in curation/batches/common-verbs-001/
```

Each batch remains independent until T030/T037 perform cross-batch overlap review and a single accepted-only promotion and ID allocation.

## Parallel Example: User Story 3

```text
Task: T039 cross-batch duplicate scenarios in tests/integration/test_curation_growth.py
Task: T040 interrupted-run scenarios in tests/integration/test_curation_recovery.py
```

## Implementation Strategy

### MVP First

1. Complete setup and foundation.
2. Complete US1 and its seeded acceptance/hold/reject exercise. This is the first reviewable process result.
3. Complete US2 before any learner-facing release: migrate source safely, curate and export accepted content, build offline, and record old-to-new Anki import compatibility.
4. Complete US3 to establish repeatable growth and recovery.

### Incremental Delivery

Each story ends with its independent test and a checkpoint. Pending or partial curation batches never write canonical vocabulary. Accepted concepts are promoted only after complete batch reports reconcile, cross-batch overlap is resolved, and all relevant evidence gates pass. The 24-concept initial target is a completion criterion; a shortfall keeps SC-003 open and triggers another bounded research batch, never weaker acceptance rules.

## Notes

- Every AI-generated content task requires inspectable prompt/version, model/tool, evidence, verification, adversarial, overlap, and outcome records.
- Deterministic tests prove process rules and identities; actual linguistic claims still require source inspection and independent AI challenge.
- Keep curation credentials and network access outside normal `validate`, `build`, and release-build paths.
- The custom `checklists/curation-quality.md` is reviewer-owned and remains unchecked until a reviewer evaluates requirement quality.
