---
description: "Dependency-ordered implementation tasks for Feature 003"
---

# Tasks: AI-First Vocabulary Curation

**Input**: Design documents in `specs/003-vocabulary-curation/`: [spec](spec.md), [plan](plan.md), [research](research.md), [data model](data-model.md), [workflow contract](contracts/curation-workflow.md), [learner-source contract](contracts/learner-source.md), and [quickstart](quickstart.md).

**Tests**: Included because the spec's quality gates and constitution require deterministic verification of source parsing, IDs, package identity, and failure behavior. Seeded tests establish that gates reject known bad records; they do not establish linguistic truth.

**Organization**: Tasks are grouped by user story. `[P]` denotes independent work in different files after its stated prerequisites; it does not authorize skipping a dependency or quality gate. All initial-corpus AI research must preserve evidence and stage artifacts.

**Recalibration migration (2026-10-12)**: T001–T036, T038–T048, and T050 remain completed records of the first implementation. Their historical requirement for adversarial review on every accepted ordinary candidate is superseded by T056–T062; it is not an instruction to rerun completed batches. T037 and T049 remain open with revised completion rules. T051 onward are new work against the existing code and artifacts. No previously processed candidate is regenerated solely because the policy changed.

**Completed requirement traceability**: FR-002 → T010–T015; FR-004 → T011–T012/T017; FR-005 → T050; FR-013 → T010/T014; FR-014 → T022–T028; FR-020 → T047–T048; FR-021 → T023/T028; FR-022 → T038; SC-006 → T023/T038. The migration tasks below extend these existing contracts without reopening completed historical work.

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
- [X] T008 [P] [US1] Add seeded decision-gate tests for independent source groups, claim coverage, separate audit observation/method versus a model-supplied flag, dictionary-only preference, conflicting evidence, model self-rating, ambiguous cues, evidenced structured false-friend contrast, and completion of all historically required policy-v1 stages for acceptance versus recorded uncompleted stages for early final decisions in `tests/unit/test_curation_gate.py`. T061 supersedes the universal-stage acceptance expectation for policy v2.
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
- [X] T018 [US1] Implement the historical policy-v1 deterministic `pending`/`accepted`/`hold`/`rejected` gate in `src/indo_malay_anki/curation/gate.py`, including explicit finalization of investigated holds, then-required stage completion, uncompleted-stage statuses and reasons for early holds/rejections without fabricated role outputs, verifier/adversary agreement, contradictions, structured false-friend contrast, and reason codes. T058–T060 supersede its universal-adversary requirement for policy v2.
- [X] T019 [US1] Implement provisional and final batch reports in `src/indo_malay_anki/curation/report.py`; require generated = accepted + held + rejected + pending while open, require pending = 0 and generated = accepted + held + rejected to close, and include relation, duplicate, investigation, and verification summaries even for zero-acceptance batches.
- [X] T020 [US1] Wire the curation subcommands, including `finalize-hold`, to the workflow, gate, and report in `src/indo_malay_anki/curation/__main__.py`; ensure no command except later `export` can alter canonical learner data.
- [X] T021 [US1] Add a full scratch-batch integration scenario with separate stage records, an accepted ordinary concept, held/rejected seeded faults, and no mutation of `data/vocabulary.tsv` in `tests/integration/test_curation_batch.py`.

**Checkpoint**: One batch can be generated, researched, verified, challenged, and closed with auditable outcomes; a single AI pass cannot approve its own content.

---

## Phase 4: User Story 2 — Study the Initial Library (Priority: P1)

**Goal**: Promote only accepted concepts into stable source data, build a useful initial deck, and preserve existing Anki identity and import behavior.

**Independent Test**: Review the accepted corpus for useful practical-category and relation coverage against the capacity-based target selected after calibration, record any shortfall without weakening gates, inspect one note/card per ID and back-only false-friend contrasts, then import an old and updated package into the same Anki Desktop test profile.

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
- [X] T033 [P] [US2] Curate up to 12 transportation candidates under historical policy-v1 stage/evidence gates, recording reasons and unfinished-stage statuses for early holds or rejections in `curation/batches/transportation-001/`; preserve these artifacts for recalibration.
- [X] T034 [P] [US2] Curate up to 12 home candidates under historical policy-v1 stage/evidence gates, recording reasons and unfinished-stage statuses for early holds or rejections in `curation/batches/home-001/`; preserve these artifacts for recalibration.
- [X] T035 [P] [US2] Curate up to 12 food candidates under historical policy-v1 stage/evidence gates, recording reasons and unfinished-stage statuses for early holds or rejections in `curation/batches/food-001/`; preserve these artifacts for recalibration.
- [X] T036 [P] [US2] Curate up to 12 common-verb candidates under historical policy-v1 stage/evidence gates, recording reasons and unfinished-stage statuses for early holds or rejections in `curation/batches/common-verbs-001/`; preserve these artifacts for recalibration.
- [ ] T037 [US2] After T079 imports and rechecks pilot artifacts in the canonical workspace, resolve overlap across the full promotion set, then export the frozen ordinary measurement lane in a dedicated guarded transaction before processing unrelated candidates; export only newly gate-valid accepted candidates into `data/vocabulary.tsv`, build `dist/myid-anki.apkg`, and record the candidate-by-candidate reconciliation of provisional pilot exports to canonical promotions/holds/rejections in `specs/003-vocabulary-curation/validation-results.md`. Report audited pilot-cohort canonical throughput after excluding only logged evaluation-audit pauses and including resumed correction, handoff, recheck and export work, using only newly promoted pilot cards whose final content/evidence digest matches a passing frozen T052 audit or passing re-audit; use that cohort's generation-to-canonical-export active interval including handoff/recheck. Separately report the count and category/relation coverage of all newly promoted release cards, including historical recoveries or further batches. Publish a whole-release cards/hour rate only if every included batch/reconsideration has a complete active interval; treat parallel work as one elapsed wall-clock window and otherwise mark the rate unavailable. Exclude unaudited additions from every quality-adjusted numerator. Apply the predeclared T076 intermediate target only to the matched isolated policy comparison. Calculate the canonical AI/expert ratio using only the T055-frozen ordinary-intent lane's audit-passing ordinary-fast canonical promotions and its dedicated active interval against the ordinary expert benchmark; retain later-escalated and discovered false-friend candidate work in that interval, exclude their cards from the ordinary numerator, and report their outcomes separately. Keep unrelated candidate processing outside the lane until its guarded canonical export completes. If the frozen lane is empty, its positive active time is unavailable, or the expert rate is zero/unavailable, mark the ratio undefined and defer practical-success claims. A nonempty measured lane with zero ordinary-fast promotions has a zero ratio against a positive expert rate and fails the success threshold. Require a valid ordinary ratio above 1 and the recorded quality guardrails before claiming practical success. Record held/rejected reasons, quality findings, and shortfalls against the capacity-based target. Do not claim Feature 003 success from isolated pilot exports alone. Curate further bounded batches only within the recorded budget and quality gates; neither the former 24-card estimate nor three-relation coverage forces weak promotion or unbounded work. Preserve retired IDs and prior released cards.
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
- [ ] T049 After T037 and T078, audit `specs/003-vocabulary-curation/quickstart.md` against final policy-v2 commands, risk paths, reconsideration, metrics, and export behavior; record completed initial-corpus, negative-gate, offline-build, and compatibility walkthroughs in `specs/003-vocabulary-curation/validation-results.md`.
- [X] T050 Apply the contrast-only scope correction: retire previously released `same` entries without reusing IDs, reject `same` and mislabeled identical ordinary forms at curation/export/source-validation boundaries, revise versioned prompts and source contracts, close the bounded school trial with auditable decisions, and rerun offline validation/build plus deterministic tests.

---

## Phase 7: Recalibration Baseline and Operation Telemetry

**Purpose**: Establish an honest comparator before changing the decision policy. Historical archives are read-only evidence; missing timing or usage is unavailable, not zero.

- [ ] T051 [US1] Inventory the 14 non-fixture batches and separate `growth-audit-001` fixture from checked-in manifests, candidate events, source inspections, reports, and `data/vocabulary.tsv`; recompute current-code outcomes without rewriting archived reports; document 102 generated/6 historical accepts/87 holds/9 rejects, 3 currently released cards, stage stop/failure/repeat distribution, report mismatches, and unavailable active-time/call/token/retrieval/cost fields in `specs/003-vocabulary-curation/validation-results.md`. Cover the inventory and fixture exclusion with a deterministic fixture test in `tests/integration/test_curation_baseline.py`. (FR-030, SC-008)
- [ ] T052 [US1] After T051, create a versioned calibration manifest under `curation/calibration/` referencing original candidate IDs/evidence for accepted contrasts, suspected false negatives, affirmed rejects, duplicates, ambiguous and high-risk cases; label synthetic fixtures and uncertain adjudications. Before T055 generation, freeze a common evidence-based pass/fail/unresolved audit rubric for semantic alignment, ordinary locale usage, relation, register/region, source independence, duplicates and false-friend contrast, including a digest of each card's evaluated cue/sense, both answers, relation, applicable contrast and supporting claims/evidence, plus prospective old/revised cohort-matching rules, topic allocations, generation prompt version and source-access conditions covering category, preliminary relation/risk mix and cue complexity. Predeclare a dedicated ordinary-intent measurement lane for each old/revised cohort, including generation and source-access conditions; T055 freezes its actual generated candidate IDs before either policy researches or decides them. Later-escalated and discovered false-friend candidates remain in their frozen lane and elapsed work but cannot contribute an ordinary card to the human-relative numerator; elevated-risk examples are also reported separately. Record the protocol in `curation/calibration/` and test reference resolution and audit-digest invalidation without candidate regeneration in `tests/unit/test_curation_calibration.py`. (FR-030, FR-031, FR-032, FR-033, SC-014, SC-015)
- [ ] T053 [US1] Extend `src/indo_malay_anki/curation/records.py` and `store.py` with append-only operation-attempt records linked to candidate events: unique operation ID, candidate set, role/path, UTC start/end, monotonic elapsed, queue/rate-limit wait, status, actual provider/model/request ID, nullable tokens/charge with availability reason, retrieval/cache counts, retry number, and input/output digests; preserve old record loading with explicit unmeasured defaults. Add schema/persistence tests in `tests/unit/test_curation_records.py`. (FR-016, FR-031)
- [ ] T054 [US1] Add a provider-neutral instrumented call runner in `src/indo_malay_anki/curation/runner.py` and CLI that consumes a versioned packet, invokes a centrally configured local provider adapter with argument arrays rather than shell interpolation (using `scripts/curation_codex.py` only as a process helper where needed), captures structured response and actual provider/model/request identity, records T053 operation start/end and available token/charge usage, validates/ingests the response, and checkpoints failure/retry state. Preserve manual `packet`/`ingest` with unavailable provider timing/usage. Add a recorded `research-start`/`research-finish` operation or equivalent for external source access, linking operation ID, candidate/claim, query/source, start/end, status and inspected observation; count retrievals only from recorded attempts, marking unrecorded manual research count/latency unavailable rather than counting inspection rows. Instrument `workflow.py`, `bundle.py`, source inspection/retrieval boundaries and `export.py` for batch intervals including queues, rate limits, backoff, retrieval and export; log excluded external pauses, including frozen-rubric evaluation-audit start/end between provisional export and canonical promotion, plus calendar span; include resumed curation work after such pauses; count one provider operation per bundle. Test fake-adapter and research-operation timing, malformed output, missing usage, unrecorded research, and no canonical mutation in `tests/integration/test_curation_metrics.py`. (FR-017, FR-028, FR-031, SC-013)
- [ ] T055 [US1] Using T051–T054, run one dedicated instrumented generation pass for each bounded T052 ordinary-intent cohort in isolated workspaces before locale research or policy-specific decisions; record each generation interval and immediately freeze actual candidate IDs, preliminary matching attributes, response digests and matching exceptions for both cohorts in `curation/calibration/`. Keep each frozen candidate and its work in its original lane after later escalation or false-friend discovery, while excluding such cards from the ordinary numerator. Do not replace candidates after seeing outcomes. Then run the old-policy cohort with equivalent recorded source access; reuse historical artifacts only for separately labeled paired-policy replay, never regenerate already processed candidates. Audit every exported comparator card with the frozen T052 rubric and evaluated content/evidence digest; record raw exported count, audit-passing count, fail/unresolved reasons, category/risk mix, cache state, throughput and stage work in `specs/003-vocabulary-curation/validation-results.md`. Do not change canonical learner data, infer active time from archive timestamps, or declare a speedup yet. (FR-031, FR-032, FR-033, SC-008, SC-014)

**Checkpoint**: Historical outcome counts and a new timed comparator are inspectable; actual provider operations are not confused with candidate events.

---

## Phase 8: Versioned Risk Policy and Bounded Decisions

**Purpose**: Replace uniform maximum review for ordinary cards while preserving the stronger false-friend gate.

- [ ] T056 [US1] Add a decision-policy version and compatible risk/typed-decision records in `records.py` and `curation/config.json`: `ordinary-fast`, `escalated`, `false-friend`; input/evidence digests, trigger codes, required/skipped roles, concrete defect or unresolved-risk refs, and old-record `not-assessed` defaults. Keep historical prompt versions and batch manifests immutable. (FR-003, FR-010, FR-016)
- [ ] T057 [P] [US1] Add new versioned verifier, relation-taxonomy, evidence-audit and adversarial prompt snapshots under `curation/prompts/` and register them in `curation/prompts/manifest.json`; require concrete objection/risk evidence, distinguish `similar` from `same`, preserve verifier blindness, and retain all prior prompt snapshots. Add prompt/packet contract assertions in `tests/contract/test_curation_cli.py`. (FR-003, FR-009, FR-024)
- [ ] T058 [US1] Implement deterministic risk classification in `src/indo_malay_anki/curation/gate.py` for cue/sense alignment, relation, evidence independence/coverage, contradiction, register/region, rarity, semantic overlap, and verifier result; record the chosen path before final decision and recompute after material changes. `different-common-word` must still establish everyday preference in both locales. (FR-006, FR-010, FR-024, SC-010)
- [ ] T059 [US1] Update `gate.py` so an ordinary evidence-sufficient verifier-agreed candidate can ACCEPT with adversarial `skipped-low-risk`; elevated risks require targeted review; false friends still require separately evidenced meanings/contrast and verifier/adversarial agreement. Enforce typed affirmative REJECT grounds, HOLD for plausible missing evidence/outage/hesitation/budget exhaustion, and preservation of concrete contradictions. (FR-007, FR-009, FR-011, FR-024, FR-026)
- [ ] T060 [US1] Update `workflow.py`, `packets.py`, and CLI routing to permit targeted escalation packets when verifier disagrees or evidence conflicts, apply policy-versioned dependencies, reuse a compatible successful stage after a later failed attempt, and record skipped versus uncompleted stages without fabricating role output. Keep generator/verifier separation and archived packet digests. (FR-003, FR-009, FR-016, FR-024)
- [ ] T061 [US1] Extend `tests/unit/test_curation_gate.py` and `tests/unit/test_curation_evidence.py` for every fast-path eligibility and escalation trigger, two independent claim-relevant source groups, dictionary-only preference, missing versus contradictory evidence, concrete versus generic adversarial objections, typed HOLD/REJECT, and mandatory false-friend gates. These fixtures test policy mechanics, not linguistic truth. (SC-001, SC-002, SC-010)
- [ ] T062 [US1] Extend `tests/integration/test_curation_batch.py` and `test_curation_recovery.py` with ordinary fast acceptance without an adversarial call, conflict/disagreement escalation, false-friend mandatory review, changed-input invalidation, partial/failed role states, and accepted-only report/export behavior. (SC-001, SC-004, SC-010)

**Checkpoint**: A single generated response cannot approve itself; low-risk ordinary cases do not pay for routine adversarial review; high-risk cases cannot bypass it.

---

## Phase 9: Evidence Reuse, Cost Bounds, and Safe Parallelism

**Purpose**: Reduce repeated work without broadening evidence claims or weakening deterministic promotion.

- [ ] T063 [US1] Define a versioned inspected-observation cache schema and on-disk store under `curation/evidence-cache/` and `src/indo_malay_anki/curation/`, keyed by lemma/form, sense, locale, proposition/usage context and canonical source locator/version; retain actual observation, method, access time, source group, stance, limitations, and origin/reuse links. Bare URLs and old audit verdicts are not reusable facts. (FR-008, FR-016, FR-027)
- [ ] T064 [US1] Materialize cached observations as new claim-linked evidence in `evidence.py` and `workflow.py`; rerun current-claim relevance, freshness/limitations, independent underlying-source grouping, coverage and contradiction checks before a hit can support acceptance. Support batched retrieval/query reuse while retaining per-candidate attribution. (FR-008, FR-027)
- [ ] T065 [US1] Add cache tests in `tests/unit/test_curation_evidence.py` and integration fixtures for same lemma/different sense, locale/register mismatch, stale source, copied mirrors, contradictory observations, cache hits, and candidate-level lineage; confirm no multiplication of independent signals. (SC-012)
- [ ] T066 [US1] Define centrally configured, policy-versioned per-candidate/batch caps for retrieval, verifier, adversarial, conflict-resolution, malformed-output retry, and available elapsed/token/cost work in `curation/config.json` and route/config parsing; choose recorded starting values from T055 rather than inventing a throughput threshold. (FR-025)
- [ ] T067 [US1] Enforce the T066 budgets in `workflow.py`/`gate.py`, recording consumed attempts, rate-limit waits and cap reason; at a cap ACCEPT only if the applicable gate already passes, otherwise HOLD plausible unresolved work or REJECT a separately documented affirmative defect. A timeout or inaccessible source is never negative linguistic evidence. (FR-011, FR-025, FR-026)
- [ ] T068 [US1] Test retrieval failure, malformed responses, retry exhaustion, verifier disagreement, concrete contradiction, and false-friend budget limits in `tests/unit/test_curation_gate.py` and `tests/integration/test_curation_recovery.py`; verify retryable state and no canonical TSV mutation. (SC-002, SC-011)
- [ ] T069 [US1] Add bounded candidate workers around the T054 instrumented runner, per-provider concurrency/rate-limit handling, backoff and same-candidate stage leases in `runner.py`/`workflow.py`/`bundle.py`; keep candidate stage order, duplicate resolution, report closure, manifest mutation, and ID/export transaction serialized. Checkpoint every actual invocation and attempt. (FR-001, FR-028)
- [ ] T070 [US1] Make partial `ingest-bundle` fan-out resumable by candidate/input digest in `bundle.py`/`workflow.py`, so already-ingested members are skipped and the original provider operation ID is counted once; failed or partial work cannot promote learner data. (FR-016, FR-028, FR-031)
- [ ] T071 [US1] Add deterministic bounded-concurrency, rate-limit, same-candidate lease, partial fan-out, no-duplicate-promotion, and export-interruption tests in `tests/integration/test_curation_recovery.py`, `test_curation_growth.py`, and `test_curation_export.py`. (SC-005, SC-012, SC-016)

**Checkpoint**: Reused inspected facts retain claim scope; independent work overlaps safely; provider failures and partial batches do not change the learner source.

---

## Phase 10: Reconsideration, Reporting, and Quality Evaluation

**Purpose**: Recover valid historical work and measure useful output rather than generated candidates.

- [ ] T072 [US3] Add a policy-versioned `reconsider` CLI/workflow path for selected historical holds and plausible false-negative rejects, preserving original candidate and batch IDs, prior decisions, prompt versions, evidence, and ID linkage. Select compatible successful records by digest; rerun only policy-invalidated stages; append old/new outcome, changed relation, reused/rerun refs and reason. Reconcile new decision view with report/export without rewriting archived reports. (FR-016, FR-029, SC-009)
- [ ] T073 [US3] Extend `tests/integration/test_curation_recovery.py`, `test_curation_growth.py`, and `test_curation_export.py` for old-record defaults, closed-batch review, unchanged candidate identity, idempotent replay, stale-result invalidation, confirmed duplicate non-promotion, and no second permanent ID. (FR-012, FR-015, SC-005, SC-009)
- [ ] T074 [US3] Re-evaluate a bounded representative historical sample from T052 using T072; reuse inspected evidence and candidate records, record recovered accepted, confirmed rejected, still held, relation changes, false-positive checks, and why decisions changed in `curation/calibration/` and `specs/003-vocabulary-curation/validation-results.md`. Do not promote a recovered candidate unless all revised gates pass. (FR-029, FR-030, FR-033, SC-009, SC-015)
- [ ] T075 [US1] Extend `report.py` and CLI reporting to reconcile open/closed counts while adding path distribution, escalation/stage HOLD/REJECT and uniquely found defects, cache/retry/budget work, reconsideration outcomes, historically accepted versus promoted cards, and available wall-clock cards/hour, seconds/card, unique calls/card, input/output tokens/card, retrievals/card and estimated cost/card by path. Separate provisional isolated benchmark exports, audited pilot-cohort canonical promotions, the T055-frozen ordinary-intent lane, escalated/false-friend output, and all newly promoted corpus cards; track handoff/recheck/export time, logged evaluation-audit pause duration, resumed correction work, unadjusted calendar span and candidate-identity reconciliation. Retain all frozen lane candidates and their elapsed work after escalation; count only audit-passing ordinary-fast canonical cards in the human-relative numerator. A quality-adjusted numerator includes only canonical promotions with a passing audit bound to the final learner content/evidence digest; unaudited or stale-audit additions remain in raw counts. Record a dedicated generation-to-canonical-promotion active wall-clock interval for the ordinary lane with no unrelated candidate work inside it; if this interval cannot be isolated, mark its rate and human ratio unavailable rather than summing per-card latencies. For a mixed release, publish a cards/hour rate only if every included batch/reconsideration has measured active intervals; use one elapsed wall-clock window for concurrent work and mark the rate unavailable if any included work is unmeasured. Mark missing values unavailable and zero-card work-per-card ratios undefined; report a zero AI/expert ratio when a nonempty measured ordinary lane yields zero ordinary-fast cards against a positive expert rate, and undefined only for an empty lane, nonpositive/unmeasured lane time or zero/unavailable expert rate; use a versioned price table only for labeled estimates. Test frozen-lane escalation retention, logged audit-pause exclusion with resumed correction time included, ordinary-only ratio attribution, mixed-risk exclusions, unavailable lane time, empty lane versus nonempty zero-acceptance ratio, final-digest mismatch, unmeasured historical recovery, overlapping timed batches, audited-cohort versus mixed-release attribution, provisional-versus-canonical attribution, and bundle call accounting in `tests/unit/test_curation_report.py` and `tests/integration/test_curation_metrics.py`. (FR-017, FR-019, FR-031, FR-032, FR-033, SC-004, SC-013, SC-014)
- [ ] T076 [US1] Conduct a small timed expert benchmark on representative unseen ordinary concepts using the frozen T052 audit rubric, source-access/cue/evidence rules and matched category/risk mix; audit all resulting cards under the same pass/fail/unresolved procedure and content/evidence digest used in T055, preferably blinded to producer. Record expert active curation time and independent quality-audit time separately, raw accepted count, audit-passing count, unresolved/fail reasons and sample limits in `specs/003-vocabulary-curation/validation-results.md`. Before the revised pilot, record the T055 machine comparator, observed human denominator, a numeric intermediate throughput target or absolute cards/hour target if the old comparator is zero **for the matched isolated policy comparison only**, fixed quality guardrails and rationale. Reserve canonical throughput and AI/expert ratio for separate reporting after T037; do not apply the isolated benchmark target to a denominator including canonical handoff/recheck. If cohort matching or runner timing is inadequate, defer a speedup claim. This is evaluation, never routine approval. (FR-032, FR-033, SC-014)
- [ ] T077 [US1] Run the actual ordinary-intent candidate IDs frozen by T055 as a dedicated policy-v2 measurement lane across practical categories using T056–T075 and the instrumented runner in an isolated checkout or fixture output area; do not interleave unrelated candidate work before canonical promotion. Process elevated-risk calibration examples outside this lane; later escalation within it retains the candidate and work interval but does not contribute an ordinary card to the human-relative numerator. Count cards exported there as provisional benchmark output only, leaving canonical learner data unchanged until T037. Preserve batch/candidate events, inspected evidence, research/model operations and audit refs for T079; pilot-only IDs/ledger/TSV are provisional and never transferred. Log a start/end evaluation pause while auditing every exported pilot card with the same frozen rubric as T055/T076, excluding only that audit duration from active AI curation time and counting any resumed correction before handoff; record the evaluated cue/sense, both answers, relation, applicable contrast and supporting claim/evidence digest with each audit result. Compare provisional audit-passing benchmark exports per wall-clock hour with the matched old-policy cohort and predeclared T076 target, reporting raw exports and fail/unresolved counts, cohort mismatches, source/cache conditions, suspected/recovered false negatives, duplicate/relation errors and path share. Label the speed comparison provisional pending T079–T037 canonical reconciliation; select a capacity-based initial-corpus target without quota-driven acceptance in `specs/003-vocabulary-curation/validation-results.md`. (FR-016, FR-018, FR-031, FR-033, SC-003, SC-014, SC-015)
- [ ] T078 [P] Update `README.md`, `specs/003-vocabulary-curation/quickstart.md`, and versioned prompt/process documentation for the implemented provider-neutral runner versus unmeasured manual exchange, fast/escalated/false-friend paths, concrete objection and HOLD/REJECT semantics, evidence reuse, budgets, batch/concurrency/resume behavior, reconsideration, matched-cohort quality-audited throughput, fallibility, and offline build boundary; add README/CLI contract tests where user-facing commands change. (FR-001, FR-023, SC-007)
- [ ] T079 [US2] After T077, add and execute a digest-manifested pilot artifact handoff into the canonical curation workspace: stage batch/candidate events, inspected evidence, research/model operation records and audit refs; validate complete files, references and prompt/policy versions; reject a conflicting `batch_id` or duplicate `(batch_id, candidate_id)` within the imported batch while permitting a candidate-local ID already used by another batch. Atomically import the batch directory, excluding pilot TSV, temporary ID ledger, export journal and provisional IDs. Recompute the current decision/report and cross-batch overlap against canonical learner data; append a versioned decision revision linked to the preserved pilot verdict for every changed outcome, recording reason, current-source reference and report version. Hold or re-evaluate candidates invalidated by changed canonical state; pass only current accepted candidates to T037's guarded canonical ID export. Compare the final learner content and supporting claim/evidence digest with the imported audit digest; flag a material mismatch for frozen-rubric re-audit or exclusion from the quality-adjusted numerator without treating the evaluation audit as a release gate. Record handoff/recheck time and candidate identity mapping for final throughput reconciliation; complete the frozen ordinary lane's handoff without unrelated candidate work during its measured interval. Test corrupt/incomplete/colliding imports, valid cross-batch reuse of a local candidate ID, preserved pilot verdict and changed-decision lineage, audit-digest mismatch and re-audit/exclusion, idempotent retry, no pilot ID reuse, and no canonical learner mutation on failure in `tests/integration/test_curation_handoff.py`. (FR-012, FR-016, FR-018, FR-031, SC-005)

**Checkpoint**: Historical false-negative recovery and new-batch productivity are measured with quality guardrails; the expert benchmark remains evaluation-only.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** has no prerequisite. T002 and T003 can proceed alongside T001 because they write different files.
- **Foundational (Phase 2)** follows setup; record schemas and atomic store must exist before stage workflows.
- **US1 (Phase 3)** follows foundation. The seeded tests describe required failures first; prompt files can be authored in parallel. Packet, ingest, evidence, duplicate, gate, CLI, and integration work then follow their data dependencies.
- **US2 (Phase 4)** depends on US1's accepted decision records. Its parser/build tests and export tests can be prepared in parallel. Four topic batches may be curated in parallel after the pipeline is stable, but T030/T037 must screen their union for semantic overlap before any ID assignment/export.
- **US3 (Phase 5)** depends on the US1 pipeline and a released or fixture-backed US2 corpus for cross-batch duplicate comparisons. Its tests can be prepared in parallel.
- **Polish (Phase 6)** follows the desired stories; documentation tasks may start earlier once interfaces stabilize.
- **Recalibration baseline (Phase 7)** starts from completed T001–T050 artifacts. T051 precedes T052's frozen audit/matching rules; T053 defines operation records, and T054 adds provider and source-research telemetry before timed comparator T055. T055 freezes actual candidate assignments after measured generation and before either cohort's policy decisions. No historical batch is silently rerun.
- **Risk policy (Phase 8)** follows T051–T055. T056 defines policy records, then T058–T060 change classification, gate, and orchestration. T057 prompt snapshots can be prepared after policy shape is known. T061–T062 test the resulting behavior.
- **Reuse and execution (Phase 9)** follows policy contracts: T063–T065 cache inspected facts; T066–T068 set initial bounded work from T055, with pilot-informed tuning deferred to a later version; T069–T071 parallelize T054 runner calls and make fan-out crash-safe. Shared promotion and ID allocation remain serialized.
- **Evaluation (Phase 10)** uses the revised policy and cache: T072–T074 reconsider historical candidates; T075 reports measured work; T076 applies the frozen T052 rubric to the expert cohort and records the numeric intermediate target **before** T077. T077 runs the candidate-frozen revised cohort with the same audit; T079 imports its evidence and candidate history into canonical curation state before T037 export. T049 follows T037 and T078. No unchecked early task can be marked complete merely because an old-policy equivalent passed.

### User Story Dependencies

```text
Completed T001–T050 -> T051/T052 baseline -> T053/T054 telemetry -> T055 timed comparator
                  -> T056–T062 risk policy -> T063–T071 reuse/budgets/concurrency
                  -> T072–T075 reconsider/report -> T076 benchmark/target -> T077 pilot
                  -> T079 artifact handoff -> T037 corpus/export -> T049 final walkthrough
```

- **US1** is the MVP process slice: it proves independent, evidence-based decisions without changing learner data.
- **US2** consumes US1 decisions and independently proves source promotion and a studyable deck.
- **US3** consumes the same stable process and independently proves later-batch overlap, audit, and recovery behavior.

### Parallel Opportunities

- In **US1**, T007–T009 test files and T010–T013 prompt groups touch different files; they can progress independently after foundation.
- In **US2**, T022–T024 test areas can be prepared independently. T033–T036 topic batches can run concurrently after the gate is stable, but T030/T037 must reconcile overlap across all four before assigning IDs or updating source.
- In **US3**, T039 and T040 target separate integration scenarios.
- T045 and T046 update separate documentation/test files.
- In recalibration, T052 calibration notes and T053 operation-schema design can proceed after T051 in separate files. T057 prompt snapshots may proceed alongside deterministic policy tests once T056 fixes the policy interface. Independent cache/budget test fixture preparation may overlap, but the same code files and shared promotion are not parallel mutation targets.

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

### Historical MVP (completed or still open as marked above)

1. Complete setup and foundation.
2. Complete US1 and its seeded acceptance/hold/reject exercise. This is the first reviewable process result.
3. Complete US2 before any learner-facing release: migrate source safely, curate and export accepted content, build offline, and record old-to-new Anki import compatibility.
4. Complete US3 to establish repeatable growth and recovery.

### Recalibrated Incremental Delivery

The existing MVP architecture is retained. Execute Phases 7–10 in dependency order, including T079 handoff, then T037 and T049. Pending or partial curation batches never write canonical vocabulary. Accepted concepts are promoted only after complete batch reports reconcile, cross-batch overlap is resolved, and all risk-path evidence gates pass. The former 24-concept target is provisional; T077 selects a measured, capacity-based target. A shortfall is reported and may lead to another bounded batch under the same quality and work limits.

## Notes

- Every AI-generated content task requires inspectable prompt/version, model/tool, evidence, independent verification, applicable adversarial outcome or documented fast-path bypass, overlap, risk, and final-decision records.
- Deterministic tests prove process rules and identities; actual linguistic claims still require source inspection and independent AI challenge.
- Keep curation credentials and network access outside normal `validate`, `build`, and release-build paths.
- The custom `checklists/curation-quality.md` is reviewer-owned and remains unchecked until a reviewer evaluates requirement quality.
