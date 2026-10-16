---

description: "Actionable implementation tasks for Feature 004 corpus scaling"
---

# Tasks: Feature 004 Corpus Scaling

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [CLI contract](contracts/production-run-cli.md), [quickstart.md](quickstart.md)

**Tests**: Critical data integrity, resumption, promotion, and Anki identity behavior require automated tests under constitution principle XIV. Tests precede the implementation they protect; they should fail for the missing behavior first.

**Organization**: Shared setup and foundation, then one independently testable phase per user story. The real 100-candidate run is a separate operational phase after the workflow works with fixtures.

## Final task-status reconciliation

`[x]` means **COMPLETE**; `[ ]` is reserved for **REQUIRED-INCOMPLETE** actionable Feature 004 work. All 71 existing tasks, **T001–T071**, were already checked before this reconciliation. Their checkbox case has been normalized; no task was newly marked complete and no original ID or task description was changed. There are no unchecked tasks.

| Allowed status | Task IDs or related work | Terminal disposition |
| --- | --- | --- |
| COMPLETE | T001–T071 | Implemented or executed, including both authorized 100-candidate runs, reports, guarded promotion, QA, and final validation. |
| ALREADY-SATISFIED | None | No unchecked task was found to be satisfied elsewhere. |
| EXPERIMENT-COMPLETED | Fixed Batch 1 efficiency benchmark (separate from T001–T071) | Replay, comparison, and adoption decision are complete in [efficiency-benchmark.md](efficiency-benchmark.md). |
| SUPERSEDED | None | No task requires this disposition. |
| WONT-DO | Archive/context compaction, grouped production verification, and grouped independent risk audit from the completed benchmark | Rejected for changed duplicate decisions or cues and missed learner-critical audit findings; no optimization was adopted. These are not open tasks. |
| DEFERRED | Batch 3, later batches toward 500 or approximately 1,000 cards | Future corpus operation using the converged workflow, not unfinished Feature 004 implementation. No such batch was started here. |
| REQUIRED-INCOMPLETE | None | No actionable Feature 004 task remains. |

Batch 1 promoted 68/100 candidates (137 → 205 cards); Batch 2 promoted 65/100 (205 → **270 cards**). Both runs are complete. Production policy v3.1, required risk-audit clearance, random-QA monitoring, safety brakes, and resumability remain as recorded in the [convergence report](convergence-report.md). High model/token cost is a known operating constraint rather than an open Feature 004 task.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Independent work in different files with no unmet task dependency.
- **[US1]–[US3]**: The matching user story in `spec.md`.
- Paths are relative to the repository root.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the frozen dependency and prepare a clean scaling package without changing v3.1.

- [x] T001 Record the 137-card baseline, current policy `3.1.0`, deck/model IDs, existing GUID derivation, and source/ledger digests in `specs/004-corpus-scaling/baseline.md` using `data/vocabulary.tsv`, `curation/config.json`, and `curation/id-ledger.json`.
- [x] T002 Create the new package skeleton and entrypoint files `src/indo_malay_anki/scaling/__init__.py` and `src/indo_malay_anki/scaling/__main__.py` without changing `src/indo_malay_anki/curation/gate.py` or its policy routes.
- [x] T003 [P] Add a fixed baseline identity fixture and validation helper in `tests/fixtures/corpus_scaling_baseline.json` and `tests/conftest.py` so later tests detect accidental changes to the 137 existing IDs/GUIDs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Persist a parent production run and expose its state before any generation or promotion.

- [x] T004 Write contract tests for unique run IDs, manifest validation, atomic writes, append-only event sequencing, and conflicting replay in `tests/contract/test_scaling_store.py`.
- [x] T005 Implement the versioned parent manifest, slice/candidate references, atomic storage, run lock, append-only events, and checkpoint digests in `src/indo_malay_anki/scaling/store.py` using the existing `src/indo_malay_anki/curation/store.py` conventions.
- [x] T006 [P] Write CLI contract tests for `create`, `status`, `report`, JSON output, nonzero error codes, and idempotent reissue in `tests/contract/test_scaling_cli.py` from `specs/004-corpus-scaling/contracts/production-run-cli.md`.
- [x] T007 Implement the common CLI parser, run lookup, read-only status/report output, and durable command-error reporting in `src/indo_malay_anki/scaling/__main__.py`.
- [x] T008 Implement parent state transition validation, pause/resume with prior state and reason, and checkpoint reconciliation against referenced slice/source artifacts in `src/indo_malay_anki/scaling/workflow.py`; add transition tests in `tests/unit/test_scaling_lifecycle.py`.

**Checkpoint**: A draft production run can be created, inspected, paused, and resumed without touching canonical learner source.

---

## Phase 3: User Story 1 - Plan and produce a useful batch (Priority: P1) 🎯 MVP

**Goal**: Draft and approve gap-led category allocation, screen waste before admission, and curate exactly 100 distinct candidates across frozen v3.1 slices without promotion.

**Independent Test**: With the 137-card fixture plus historical candidates, create and approve an editable allocation, generate and curate bounded slices to 100 admitted candidates, and inspect coverage and proposal-waste records while `data/vocabulary.tsv` remains unchanged.

### Tests for User Story 1

- [x] T009 [P] [US1] Write coverage tests for tag aliases, one primary category per canonical card, unknown tags, gap-based draft, manual edits, allocation total equal to `requested_count` (including first-run 100), and post-approval immutability in `tests/unit/test_scaling_coverage.py`.
- [x] T010 [P] [US1] Write staged redundancy tests for exact cue, English synonym, near-equivalent concept, plural, bilingual-answer match, historical candidate, prior `same`, and documented distinct sense in `tests/unit/test_scaling_redundancy.py`.
- [x] T011 [P] [US1] Write an integration test for sequential at-most-12 slices, validated raw-response screening before Feature 003 ingest, all-screened-out initialized slices with parent zero-admission records and no export, cross-slice exclusion, replacement slices, declared proposal cap, relation-value priority, and `requested_count` admitted IDs (100 first run) in `tests/integration/test_scaling_generation.py`.

### Implementation for User Story 1

- [x] T012 [P] [US1] Create the small versioned category catalog and explicit mappings from current freeform TSV tags in `curation/coverage-categories.json`, retaining unmapped-tag visibility and leaving `data/vocabulary.tsv` tags unchanged.
- [x] T013 [US1] Implement canonical and historical coverage inventory, source digest, one-primary-category counts, and unmapped-tag reporting in `src/indo_malay_anki/scaling/coverage.py`.
- [x] T014 [US1] Implement gap-based allocation drafts with category rationale, maintainer edits, total validation against manifest `requested_count`, and frozen approved allocation digest in `src/indo_malay_anki/scaling/coverage.py` and `src/indo_malay_anki/scaling/store.py`.
- [x] T015 [US1] Implement `create`, `allocation`, and `approve` CLI behavior, including edit rationale and prevention of post-generation allocation changes, in `src/indo_malay_anki/scaling/__main__.py`.
- [x] T016 [P] [US1] Build a cumulative exclusion index from `data/vocabulary.tsv`, `curation/batches/`, earlier slices, and prior no-contrast outcomes using existing Feature 003 comparison keys in `src/indo_malay_anki/scaling/redundancy.py`.
- [x] T017 [US1] Add a bounded semantic shortlist and recorded duplicate/redundant/prior-same/distinct-sense disposition to `src/indo_malay_anki/scaling/redundancy.py`; only plausible matches receive semantic review, and identical forms with possible meaning divergence reach v3.1 assessment.
- [x] T018 [US1] Implement sequential category-targeted slice creation (at most 12), deterministic slice IDs, raw response validation/capture, pre-ingest proposal screening, and preference for common `different-common-word`, useful `similar`, then valuable `false-friend` candidates in `src/indo_malay_anki/scaling/workflow.py`.
- [x] T019 [US1] Admit only retained candidates and add replacement slices up to manifest `requested_count` or the declared proposal cap, retaining zero-admission attempt/proposal records and excluding empty initialized Feature 003 slices from curation/export, then pause with a shortfall instead of padding in `src/indo_malay_anki/scaling/workflow.py` and `src/indo_malay_anki/scaling/store.py`.
- [x] T020 [US1] Implement resumable v3.1 curation orchestration through existing Feature 003 packet/ingest/check/report operations, without enabling disabled experiments, in `src/indo_malay_anki/scaling/workflow.py`.
- [x] T021 [US1] Expose `generate` and `curate` CLI commands with pending-work/status output in `src/indo_malay_anki/scaling/__main__.py`.
- [x] T022 [US1] Add an inspectable pre-promotion summary of category allocation, proposals, admitted refs, duplicate/no-contrast waste, and current ACCEPT/HOLD/REJECT in `src/indo_malay_anki/scaling/report.py`.
- [x] T023 [US1] Run the US1 fixture path and document its independent result without promoting cards in `specs/004-corpus-scaling/validation-results.md`, using `tests/integration/test_scaling_generation.py` and `data/vocabulary.tsv` as checks.

**Checkpoint**: US1 can be demonstrated on fixtures without source mutation. It proves coverage planning and bounded production, but makes no learner release claim.

---

## Phase 4: User Story 2 - Resume and safely promote (Priority: P1)

**Goal**: Recover interrupted work, complete required risk audit/corrections, and guardedly promote currently eligible cards while the parent run remains open for random QA.

**Independent Test**: Interrupt a fixture run during generation, curation, evidence, audit, correction, and export; resume to the same decisions, unique permanent IDs, and semantically equivalent deck as an uninterrupted run, with no random-QA prerequisite for eligible promotion.

### Tests for User Story 2

- [x] T024 [P] [US2] Write recovery tests for captured-but-not-ingested model responses, failed retrieval, digest-matched stage reuse, partial audit/correction, interrupted withdrawal after source/ledger journal replacement, and conflicting replay in `tests/integration/test_scaling_recovery.py`.
- [x] T025 [P] [US2] Write guarded-promotion tests for independent audit attempt/claim/verdict validation, stale clearance, withheld/HOLD/REJECT/`same` exclusion, final relation/cue digests, active brake, correction reopening of a closed auto-accepted slice, repeated export, material post-promotion finding/HOLD/REJECT withdrawal, unresolved-QA restoration block, retained ledger ID, same-ID guarded restoration, and journal recovery in `tests/integration/test_scaling_promotion.py`.
- [x] T026 [P] [US2] Write stable permanent-ID, GUID, deck/model identity, one-note/one-card, and offline build regression tests in `tests/integration/test_scaling_build_identity.py`.

### Implementation for User Story 2

- [x] T027 [US2] Persist external response artifacts before Feature 003 ingest and reconcile completed/failed generation, curation, and evidence attempts by input/output digest in `src/indo_malay_anki/scaling/workflow.py`.
- [x] T028 [US2] Implement the versioned independent risk-audit record, current v3.1 export-predicate selection, separate reviewer invocation/identity validation, claim-specific result ingestion, stale-digest rejection, retry, and work metrics in `src/indo_malay_anki/scaling/audit.py` per `specs/004-corpus-scaling/contracts/audit-record.md`.
- [x] T029 [US2] Add the narrow, event-recorded correction reopen operation for a closed auto-accepted slice in `src/indo_malay_anki/curation/workflow.py` (the evidenced Feature 003 blocker), preserving v3.1 decisions/export rules; implement `resolve` through reopen/revise/finalize, refresh report and invalidated audit, and guardedly restore corrected withdrawn content under the retained ledger ID/GUID in `src/indo_malay_anki/scaling/workflow.py` and `src/indo_malay_anki/scaling/promotion.py`.
- [x] T030 [US2] Generate `curation/batches/<slice-id>/promotion-eligibility.json` from current decision and projected-content digests, required audit verdicts, unresolved material QA-finding status, and parent brake state in `src/indo_malay_anki/scaling/promotion.py`; reject stale or manually inconsistent records, without making random-QA selection a release gate.
- [x] T031 [US2] Recognize Feature 003's automatic slice closure after nonpending decisions; after audit/correction refresh the report and call existing `export_batches` only when every current ACCEPT in that closed slice is eligible, leaving blocked slices pending while other slices promote, in `src/indo_malay_anki/scaling/promotion.py`.
- [x] T032 [US2] Implement guarded withdrawal in `src/indo_malay_anki/scaling/promotion.py`: verify current material finding or HOLD/REJECT, ledger origin and source-row digest; use existing validated `commit_learner_rows` to remove only that row while retaining the ledger assignment; reconcile journal/source/ledger after interruption and make retry idempotent. Track active newly promoted, withdrawn, and ever-assigned counts so restoration does not inflate growth.
- [x] T033 [US2] Implement `risk-audit`, `resolve`, `promote`, `pause`, and `resume` CLI operations and actionable blocked-state output in `src/indo_malay_anki/scaling/__main__.py`.
- [x] T034 [US2] Integrate existing offline source validation and deck build as the `build` operation, blocking while a withdrawal is pending and recording result and note/card count without live curation calls, in `src/indo_malay_anki/scaling/workflow.py` and `src/indo_malay_anki/scaling/__main__.py`.
- [x] T035 [US2] Add promotion safety-brake enforcement and explicit investigation/resume disposition for identity/export inconsistency and learner-critical findings in `src/indo_malay_anki/scaling/promotion.py` and `src/indo_malay_anki/scaling/store.py`.
- [x] T036 [US2] Run recovery/promotion/identity fixture gates, compare uninterrupted versus resumed outputs, and record evidence in `specs/004-corpus-scaling/validation-results.md` using `tests/integration/test_scaling_recovery.py`, `tests/integration/test_scaling_promotion.py`, and `tests/integration/test_scaling_build_identity.py`.

**Checkpoint**: Eligible fixture cards promote through Feature 003 guarded export while the parent run is still open; no artifact editing or identity change is required.

---

## Phase 5: User Story 3 - Monitor quality and operating cost (Priority: P2)

**Goal**: Sample clean accepted cards for monitoring, apply brakes, reconcile per-batch and longitudinal metrics, and close only after QA findings and final report.

**Independent Test**: Feed a paused or completed fixture run mixed audit/QA findings and measured/missing usage; verify sample reproducibility, brake decisions, all denominators, separate cost categories, and refusal to close with unfinished QA.

### Tests for User Story 3

- [x] T037 [P] [US3] Write QA tests for selection only after all production decisions/risk-audit dispositions, frozen clean-ACCEPT population digest, roster replacement after clean-ACCEPT membership changes in either direction, max(5, ceil(10%)) first-run sample, available strata, post-promotion findings, and metadata-only no-brake behavior in `tests/unit/test_scaling_qa.py`.
- [x] T038 [P] [US3] Write report tests for 100-candidate reconciliation, proposal-waste and active promoted yield denominators, separate ever-assigned/withdrawn counts, distinct generation/production/risk-audit/QA/promotion/build/end-to-end time, production decisions per hour, active promoted cards per end-to-end hour, unavailable usage, coverage before/after, and longitudinal correction rates in `tests/unit/test_scaling_report.py`.
- [x] T039 [P] [US3] Write closure tests for pending QA, pending withdrawal, a stale roster after clean-ACCEPT membership changes, zero clean accepted population, unresolved brake/correction, invalid build, and complete final report in `tests/integration/test_scaling_close.py`.

### Implementation for User Story 3

- [x] T040 [US3] Implement reproducible stratified random-QA selection only after final production/risk-audit dispositions, frozen clean-ACCEPT population digest, and documented roster replacement if a later correction changes clean-ACCEPT membership, retaining prior findings, in `src/indo_malay_anki/scaling/qa.py`.
- [x] T041 [US3] Implement QA finding ingestion and classification as learner-critical answer, cue/content, metadata-only, or no issue; for an already promoted card, start T032 guarded withdrawal on a material finding before marking the QA item complete, then link T029 correction/re-audit/guarded same-ID restoration and record post-promotion status in `src/indo_malay_anki/scaling/qa.py`.
- [x] T042 [US3] Evaluate first-run safety thresholds and denominator floors, distinguish promotion brake, parent pause, and monitoring warning, and preserve investigation/resume history in `src/indo_malay_anki/scaling/qa.py` and `src/indo_malay_anki/scaling/store.py`.
- [x] T043 [US3] Aggregate authoritative slice decisions, proposal-screen records, audit/QA records, source/ledger deltas, and operation events into reconciled counts and separate generation/production-decision/risk-audit/QA/promotion/build/end-to-end time and cost; report production decisions per hour and active newly promoted cards per end-to-end hour with explicit numerators/denominators, model calls, tokens, retrievals, and unavailable reasons in `src/indo_malay_anki/scaling/report.py`.
- [x] T044 [US3] Add longitudinal learner-critical corrections per 100 promoted, post-promotion corrections, QA discoveries, repeated error categories, HOLD/REJECT, duplicate and no-contrast rates with explicit denominators in `src/indo_malay_anki/scaling/report.py`.
- [x] T045 [US3] Enforce final closure only after the QA roster matches the final clean-ACCEPT population, sampled QA outcomes, withdrawal/correction/brake dispositions, valid offline build, and reconciled final report; keep eligible promotion independent of random-QA completion in `src/indo_malay_anki/scaling/workflow.py`.
- [x] T046 [US3] Expose `qa-select`, `qa-record`, `close`, and final `report --json` CLI behavior in `src/indo_malay_anki/scaling/__main__.py`.
- [x] T047 [US3] Document maintainer interpretation of random-QA limits, safety brakes, count denominators, and unavailable cost fields in `specs/004-corpus-scaling/quickstart.md` without claiming unsampled correctness.
- [x] T048 [US3] Run QA/report/closure fixture gates and record independent story results in `specs/004-corpus-scaling/validation-results.md` using `tests/unit/test_scaling_qa.py`, `tests/unit/test_scaling_report.py`, and `tests/integration/test_scaling_close.py`.

**Checkpoint**: A fixture parent run closes only after its QA sample and final report; production promotion remains independent of random QA.

---

## Phase 6: First 100-Candidate Operational Run

**Purpose**: Execute exactly one real production run on frozen v3.1; this phase is separate from infrastructure work and must not auto-start another batch.

- [x] T049 Re-run the complete relevant `pytest`/`ruff` gates, source validation, and baseline identity check from `specs/004-corpus-scaling/quickstart.md`; record starting corpus size 137, policy pin, and command results in `specs/004-corpus-scaling/first-batch-report.md`.
- [x] T050 Create the single production run `corpus-004-001`, inspect/edit the coverage-based draft, freeze exactly 100 category slots and a proposal cap before generation, and retain its manifest in `curation/production-runs/corpus-004-001/manifest.json`.
- [x] T051 Generate sequential bounded Feature 003 slices until exactly 100 distinct new candidates are admitted, or pause with a documented proposal-cap shortfall; retain proposal waste and candidate refs in `curation/production-runs/corpus-004-001/`.
- [x] T052 Run unchanged v3.1 curation on all 100 admitted candidates, resolve current ACCEPT/HOLD/REJECT/pending states, and retain slice reports under `curation/batches/corpus-004-001-s*/report.json`.
- [x] T053 Complete required risk-selected independent audits, apply documented corrections or withholding, and reconcile current eligibility records under `curation/batches/corpus-004-001-s*/promotion-eligibility.json`.
- [x] T054 Guardedly promote currently eligible closed slices into `data/vocabulary.tsv` and `curation/id-ledger.json`, recording assigned IDs, withheld reasons, retries, and actual new-card count under `curation/production-runs/corpus-004-001/`.
- [x] T055 Validate canonical source and build `dist/myid-anki.apkg`; verify one note/card per concept and unchanged baseline IDs/GUIDs, then record build/test results in `specs/004-corpus-scaling/first-batch-report.md`.
- [x] T056 Select and review the declared random-QA monitoring sample, record every finding under `curation/production-runs/corpus-004-001/`, guardedly withdraw any promoted card with unresolved material risk or HOLD/REJECT, apply corrections through `resolve` and renewed risk audit/guarded same-ID restoration where needed, replace an invalidated sample roster, rebuild after source changes, and resolve any promotion brake before closure.
- [x] T057 Close the parent run only after QA completion and final reconciliation; write `curation/production-runs/corpus-004-001/report.json` with baseline 137, 100 admitted candidates, raw proposal count, decisions, audits, active promotions, withdrawals, ever-assigned IDs, final corpus size, coverage change, waste, separate generation/production/risk-audit/random-QA/promotion/build/end-to-end cost and cards-per-hour denominators, resumability incidents, and progress toward the 200+/500/1,000 planning milestones without acceptance quotas.
- [x] T058 Summarize repeatability, throughput limits, quality issues, safety-brake dispositions, and the decision to stop after one run in `specs/004-corpus-scaling/first-batch-report.md` without changing policy v3.1 or starting a second batch.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Confirm documentation, artifact integrity, and compatibility after the operational result.

- [x] T059 [P] Update `README.md` with the final Feature 004 CLI lifecycle and link to `specs/004-corpus-scaling/quickstart.md`, clearly separating production risk audit from random QA monitoring.
- [x] T060 Run the deterministic validation and fixture scenarios from `specs/004-corpus-scaling/quickstart.md` plus all relevant tests, including offline Anki package and identity checks, then record exact commands/results in `specs/004-corpus-scaling/validation-results.md` without starting another production run.
- [x] T061 Review `curation/production-runs/corpus-004-001/report.json`, `data/vocabulary.tsv`, and `curation/id-ledger.json` for active-versus-withdrawn count reconciliation, unique IDs, retained withdrawn assignments, provenance, correction history, no `same` learner rows, and zero unresolved export journals; document any discrepancy and resolution in `specs/004-corpus-scaling/validation-results.md`.
- [x] T062 Confirm `curation/config.json`, `src/indo_malay_anki/curation/gate.py`, `src/indo_malay_anki/curation/workflow.py`, `src/indo_malay_anki/model.py`, and the Anki templates retain frozen v3.1 decisions/export behavior and stable note/card identity apart from the narrowly tested correction reopen operation; document the compatibility check in `specs/004-corpus-scaling/validation-results.md`.

---

## Phase 8: Second 100-Candidate Operational Run (authorized continuation)

**Purpose**: Test one fresh corpus-growth cycle from the completed 205-card baseline using the unchanged production workflow. This phase does not authorize Batch 3 or further efficiency experiments.

- [x] T063 Verify the 205-card source, policy/config pins, existing IDs/GUIDs, Batch 1 artifact digests, tests, and the completed efficiency-benchmark conclusion; record the starting state in `specs/004-corpus-scaling/second-batch-report.md`.
- [x] T064 Create `corpus-004-002` with `requested_count=100`, inspect the coverage-based draft against Batch 1 allocation and remaining gaps, make any reasoned maintainer adjustment, and freeze the final allocation in its independent manifest before generation.
- [x] T065 Run the existing generation/screening workflow until exactly 100 new candidates are admitted or a declared shortfall pause occurs; retain raw proposals, redundant/no-contrast screening, candidate IDs, and resume records under `curation/production-runs/corpus-004-002/`.
- [x] T066 Run unchanged v3.1 production curation for all admitted candidates, settle current ACCEPT/HOLD/REJECT, and record measured calls/tokens/time and any failures without applying efficiency-replay transports or batching.
- [x] T067 Complete all individually required independent risk audits; apply corrections or withholding and resolve any safety brake through the existing investigation/disposition commands before promotion.
- [x] T068 Guardedly promote all and only currently eligible cards, validate source/ledger/identity, and build the offline deck; retain HOLD/REJECT/uncleared candidates outside learner content.
- [x] T069 Select and review the configured random-QA monitoring sample, record all findings, correct/withdraw material problems under existing rules, rebuild if content changes, and close only after QA and report reconciliation.
- [x] T070 Produce the final Batch 2 funnel, coverage, operational-cost and interruption report; compare Batch 1 and Batch 2 on yield, rates, findings, waste, calls/tokens/time per promoted card, and category growth in `specs/004-corpus-scaling/second-batch-report.md`.
- [x] T071 Run the final test/lint/source/build/identity gates and confirm Batch 1 artifacts are unchanged and no export journal is unresolved; record `FEATURE 004 READY TO CONVERGE` or a concrete operational blocker. Stop without starting Batch 3.

---

## Dependencies & Execution Order

### Phase dependencies

1. Setup T001–T003 establishes baseline and package paths.
2. Foundational T004–T008 provides durable parent state and command shell; it blocks all user stories.
3. US1 T009–T023 supplies real candidate/slice inputs. US2 can be developed against fixtures after foundation, but operational integration depends on US1 candidate references and v3.1 slice reports.
4. US2 T024–T036 supplies guarded promotion and build. US3 can develop QA/reporting against fixtures after foundation, but final closure depends on actual US1/US2 records.
5. The operational run T049–T058 begins only after all three story checkpoints pass. T049 is a gate before any live generation; T050–T058 execute strictly in order except repeatable correction/audit/build loops.
6. Polish T059–T062 follows the run and final report.
7. The separately authorized second operational run T063–T071 follows the completed efficiency benchmark; it uses the original production orchestration and executes in order, with normal correction/audit/build loops when required.

### User story dependencies and independent tests

| Story | Start condition | Independent proof |
| --- | --- | --- |
| US1 (P1) | Foundation complete | Coverage draft/edit/freeze and 100 admitted fixture candidates through v3.1 with unchanged learner TSV. |
| US2 (P1) | Foundation plus prebuilt slice fixtures; integrate after US1 | Interrupted/resumed fixture promotion matches uninterrupted IDs/source/deck; eligible cards promote before parent QA closure. |
| US3 (P2) | Foundation plus synthetic run/decision fixtures; integrate after US2 | Reproducible QA, threshold outcomes, reconciled costs, and closure blocked until findings/report/build finish. |

### Parallel opportunities

- T003 can prepare the identity fixture while T002 creates the package shell.
- T009–T011 are separate test files; T012 category data and T016 redundancy index can start from the shared foundation in parallel.
- T024–T026 cover distinct recovery, promotion, and build-identity risks in separate test files.
- T037–T039 cover QA, reporting, and closure in separate test files; QA T040–T041 and reporting T043–T044 can proceed in different modules after their inputs are defined.
- T059 documentation can run alongside final nonmutating validation review, but it must use the actual implemented CLI behavior.

## Parallel Example: User Story 1

```text
Task: T009 [US1] tests/unit/test_scaling_coverage.py
Task: T010 [US1] tests/unit/test_scaling_redundancy.py
Task: T011 [US1] tests/integration/test_scaling_generation.py
```

## Parallel Example: User Story 2

```text
Task: T024 [US2] tests/integration/test_scaling_recovery.py
Task: T025 [US2] tests/integration/test_scaling_promotion.py
Task: T026 [US2] tests/integration/test_scaling_build_identity.py
```

## Parallel Example: User Story 3

```text
Task: T037 [US3] tests/unit/test_scaling_qa.py
Task: T038 [US3] tests/unit/test_scaling_report.py
Task: T039 [US3] tests/integration/test_scaling_close.py
```

## Implementation Strategy

### MVP first

Complete setup and foundation, then US1. Demonstrate a frozen category allocation and 100 admitted/curated fixture candidates without learner-source changes. This validates useful candidate production before release integration.

### Incremental delivery

Add US2 guarded, resumable promotion and build; then US3 random QA, brakes, metrics, and closure. Validate each story independently with fixtures. Once all checkpoints pass, execute one live 100-candidate run and finish with compatibility review. The 500/1,000-card milestones are future planning targets, not extra runs in this task list.

## Notes

- Feature 003 production policy `3.1.0`, 12-candidate slice cap, and guarded export checks are frozen dependencies. A genuine blocking defect requires evidence and compatibility review, not a policy research cycle.
- Random QA is monitoring; only completion of the sample gates parent-run closure. It does not gate otherwise eligible promotion.
- Treat source/ledger changes and external model/retrieval calls as operational steps only in Phases 6 and 8; earlier phases use fixtures and controlled tests.
- No task authorizes community features, images/audio, Anki note/card redesign, expert-human benchmarking, or a third production batch.
