# Implementation Plan: Feature 004 Corpus Scaling

**Branch**: `feature/004-corpus-scaling` | **Date**: 2026-10-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature 004 specification and two recorded clarifications. Planning creates no candidates and changes no production code.

## Summary

Add a small file-backed production-run layer around closed Feature 003 policy v3.1. One Feature 004 run owns the coverage plan, requested candidate count (100 for the first run), cross-slice identity, state, monitoring, brakes, and final report. It coordinates sequential Feature 003 curation slices of at most 12 candidates, reuses their existing generation/verification/evidence artifacts, and promotes through the existing guarded export after each slice is closed and cleared. The parent run stays open until its random-QA sample and final report are complete. No v3.1 policy, Anki schema, or identity rule changes.

## Technical Context

**Language/Version**: Python 3.12 or newer, per `pyproject.toml`.

**Primary Dependencies**: Existing standard-library file/CLI workflow, `genanki` for deck packaging, configured Codex CLI provider for curation, and existing Feature 003 evidence adapters. No new mandatory runtime dependency.

**Storage**: Version-controlled `data/vocabulary.tsv`, `curation/id-ledger.json`, existing `curation/batches/<slice>/` records, and new file-backed `curation/production-runs/<run>/` state. Atomic JSON writes and append-only events follow existing `BatchStore` patterns.

**Testing**: Existing `pytest` and `ruff`; new unit, contract, and integration coverage for allocation, redundancy, state transitions, replay, guarded promotion, QA, brakes, report reconciliation, and offline deck identity.

**Target Platform**: Local command-line workflow on supported Python environments; built `.apkg` remains compatible with offline Anki clients.

**Project Type**: File-backed Python CLI and deterministic deck builder.

**Performance Goals**: Process one run of 100 admitted candidates using bounded slices; measure proposed/admitted/promoted cards and end-to-end time. No unproven cards/hour target or human benchmark gate. Avoid unnecessary model/retrieval calls through staged screening and checkpoint reuse.

**Constraints**: Feature 003's `BatchManifest` permits 1–12 candidates and `export_batches` requires a closed slice and current v3.1 eligibility. The normal build must remain offline and deterministic. The first run is exactly one 100-candidate production run, with a declared proposal cap and documented shortfall if 100 cannot be obtained without padding.

**Scale/Scope**: Baseline 137 canonical cards; first run 100 admitted candidate concepts; reusable workflow intended for later staged growth toward 500–1,000 useful concepts, without producing later batches now.

## Constitution Check

*GATE: Passed before research and re-checked after design.*

| Principle/gate | Plan and post-design assessment |
| --- | --- |
| Versioned source is authoritative | Pass: production manifests, records, category map, corrections, TSV, and ledger are inspectable repository files; `.apkg` remains output. |
| One concept, one note/card; neutral cue; both answers | Pass: no Anki note or card changes; existing loader, validator, and builder remain authoritative. |
| Stable identity and compatible import | Pass: permanent IDs allocated only by guarded export through existing ledger; GUID remains derived from ID alone; retry compares existing assignment/source. |
| Correctness over volume | Pass: staged redundancy checks, frozen v3.1 curation, required risk audit, and guarded eligibility precede promotion; 100 is candidate count, not a card acceptance quota. |
| Validation and offline build | Pass: existing source validation and builder run after promotion without live AI/research. Curation/provider work remains separate. |
| Simple, inspectable technology | Pass: small modules, explicit category aliases, JSON/TSV and local CLI; no database, service, dashboard, or ontology engine. |
| Testable behavior | Pass: deterministic fixtures and interruption tests protect duplicate, ledger, export, report, QA, and stable-ID behavior. |

No constitutional exception is needed. Additive orchestration does not revise Feature 003 policy v3.1 or its legacy batch/export contract. The design preserves constitution version 1.2.0.

## Project Structure

### Documentation (this feature)

```text
specs/004-corpus-scaling/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── production-run-cli.md
│   └── audit-record.md
└── tasks.md                 # Created later by speckit-tasks
```

### Source Code (planned additions and reused paths)

```text
src/indo_malay_anki/
├── scaling/                 # New parent-run orchestration only
│   ├── __main__.py          # Resumable commands and status
│   ├── coverage.py          # Category aliases, inventory, allocation draft
│   ├── redundancy.py        # Staged cross-run proposal screening
│   ├── store.py             # Parent manifest/events/checkpoints
│   ├── workflow.py          # Slice scheduling and lifecycle
│   ├── audit.py             # Independent audit record and route adapter
│   ├── promotion.py         # Eligibility-record generation and guarded export call
│   ├── qa.py                # Reproducible monitoring sample/findings/brakes
│   └── report.py            # Reconciled run and longitudinal metrics
├── curation/                # Reuse v3.1 workflow, store, gate, evidence, export, IDs
├── builder.py              # Reuse unchanged
└── validator.py            # Reuse unchanged
curation/
├── config.json             # Keep active policy 3.1.0 and 12-candidate slice cap
├── batches/                # Existing Feature 003 slice records
├── id-ledger.json           # Existing permanent-ID ledger
└── production-runs/        # New parent-run manifests, events, reports
data/vocabulary.tsv         # Canonical learner source; guarded export only
tests/
├── unit/                   # Coverage, screening, sample, metric denominators
├── contract/               # CLI and state/manifest contract
└── integration/            # Interruption, audit/promotion, build identity
```

**Structure Decision**: A sibling `scaling` package owns Feature 004 state. Existing `curation` files remain the source of v3.1 decisions and export behavior. The parent manifest references slice/candidate records instead of copying them.

## Design and integration

### Coverage and frozen allocation

Use a small versioned category list and alias mapping from existing freeform TSV tags. Count each canonical concept in one primary category for allocation and reporting; retain original tags. Mark unknown tags for maintainer mapping rather than silently discarding cards. Historical candidates and prior `same` rejections inform exclusions and waste estimates, not the promoted coverage count. Produce an inspectable draft from gaps and common-vocabulary priorities, show counts/rationale, allow a maintainer-edited allocation, validate that nonnegative category targets total the run's `requested_count`, then freeze its digest and baseline corpus snapshot before generation. Later category edits require a new run or an explicit pre-generation revision; no edits after generation begins. The first run uses `requested_count=100`; subsequent runs use the same rules with their own declared count.

### One run over bounded slices

Feature 003 caps generation at 12 candidates. The first parent run targets ten 10-candidate slices; screened-out proposals may require additional slices, all at most 12, until the parent has its `requested_count` admitted candidates (100 in the first run). Each slice targets one category or a documented compatible grouping from the frozen allocation. Create slices sequentially so `init_batch` snapshots include earlier generated candidates. Capture and validate the raw model response, screen its proposals against the parent exclusion index, and ingest only admitted proposals into the Feature 003 slice; retain screened-out raw proposals and reasons in parent records. If every proposal in an initialized slice is screened out, retain its parent zero-admission attempt record, leave its Feature 003 slice with no candidates and no export, and schedule another attempt within the proposal cap. The parent index includes earlier unpromoted slices. Slice IDs are deterministic from run ID and ordinal; retries reuse them. A declared proposal cap (first-run default: 200, adjustable before freeze) bounds replacement attempts; reaching it with fewer than `requested_count` admissions pauses the run with a shortfall report. Do not silently start another run. Generation selection uses the frozen category targets and prefers common `different-common-word`, then useful `similar`, then valuable `false-friend` proposals; v3.1 still decides their final relation and eligibility.

### Staged redundancy control

Before model work, index canonical TSV, Feature 003 historical proposals/decisions, earlier slices in this run, and prior no-contrast rejections. Use normalized English cue, simple inflection key, and exact bilingual answer pair first; pass a compact exclusion list into generation. For remaining proposals, retrieve a small candidate shortlist by aliases/word overlap and request semantic resolution only for plausible same-sense or near-synonym matches. Record `duplicate`, `redundant`, `prior-same`, or `distinct-sense` with the linked reference and rationale. No permanent ID is assigned at this stage. Keep Feature 003 normalize/dedupe and final live export overlap checks as independent backstops. Identical forms with a possible meaning divergence proceed to v3.1 false-friend assessment.

### Lifecycle, checkpoints, and resume

Parent states are `draft`, `allocation-approved`, `generating`, `curating`, `awaiting-risk-audit`, `promotion-ready`, `promoting`, `qa-monitoring`, `complete`, and `paused`. `paused` records the prior state and reason, then resumes only through an explicit command. Failed operations remain pending with an event and can be retried; they are not linguistic REJECT. Stage checkpoints record input digest, output reference/digest, started/completed time, and usage where available. The runner first reconciles parent checkpoints with Feature 003 slice records and canonical source/ledger, then repeats only incomplete or invalidated work. Persist provider response before ingest to survive a crash between model completion and ingest. Serialize slot admission, archive updates, audit disposition, export, and ledger changes; independent candidate curation may use bounded concurrency through the existing workflow.

### Audit, eligibility, promotion, and QA

Route required independent audits using the same v3.1 risk predicate enforced by Feature 003 export, without treating random QA as required risk audit. Feature 004 defines the versioned [audit record contract](contracts/audit-record.md): a separate review invocation, current decision/content digests, claim-specific finding, evidence references, verdict, reviewer identity, and usage. Reject stale, incomplete, or non-independent audit records. Feature 003 `batch_report` can auto-close a slice as soon as generation is complete and no decisions are pending, before audit. Audit then clears the closed slice. A material finding reopens the affected candidate, applies correction or HOLD/REJECT, reruns invalidated decisions, and refreshes the closed report. The existing `reopen_candidate` handles only explicit HOLD/REJECT and cannot reopen an auto-accepted candidate in a closed slice; this is a genuine blocking defect for required audit and post-promotion QA corrections. Add a narrow, event-recorded correction reopen operation to Feature 003 workflow, with compatibility tests, while leaving v3.1 decisions and export rules untouched. Feature 004 creates `promotion-eligibility.json` only from current decision/content digests, audit verdicts, absence of unresolved material QA findings, and brake state; this removes manual artifact surgery. Call existing `export_batches` only when each current ACCEPT in that closed slice is eligible. It rechecks report freshness, eligibility, duplicate overlaps, permanent IDs, and uses journaled TSV/ledger commit. Other cleared slices may promote while the parent run remains open. A slice with unresolved accepted candidate waits. This preserves Feature 003's all-accepted slice export contract.

Freeze the random-QA population after generation and all 100 first-run production decisions are final and required risk-audit dispositions have identified otherwise clean ACCEPTs. Earlier eligible cards may already have been promoted. Select once from that frozen population across available confidence/risk strata using a stored seed, population digest, and roster; first-run sample size is max(5, ceiling(10% of clean accepted)), capped by that population. Content-only corrections to sampled cards retain the original roster and record the changed content digest; any later change to clean-ACCEPT membership invalidates the roster and requires a documented replacement selection before closure, preserving prior QA findings. Random QA never sets promotion eligibility. A material finding on an already promoted card starts a pending guarded withdrawal before that QA item can be marked complete; a current HOLD/REJECT on a promoted card also requires withdrawal. Implement a Feature 004 withdrawal operation in `scaling/promotion.py` that verifies the candidate's ledger assignment, current source row/digest, and finding or decision; recovers any export journal; removes only that row through existing `commit_learner_rows` validation and journaled source/ledger commit; and records reason, before/after digests, and retained ID assignment. A retry reconciles the journal and treats an already absent row under the same assignment as completed. Pending withdrawal blocks build, closure, and further promotion until reconciled. For a corrected card, reopen/revise its Feature 003 candidate, refresh decision and report, repeat required risk audit where invalidated, rebuild eligibility, and guardedly re-export through `export_batches` under the retained ledger ID. Verify unchanged permanent ID/GUID and preserve both prior and corrected content in history. Findings may brake remaining unpromoted cards. The parent run reaches `complete` only after every selected QA item has a recorded outcome (or zero eligible sample population), corrections/brakes have dispositions, the offline deck build succeeds, and the final report reconciles.

### Brakes and metrics

Distinguish candidate withholding (individual audit issue), a promotion brake (identity/export inconsistency or multiple learner-critical findings), a parent-run pause for investigation (threshold breach or repeated pattern), and monitoring warnings (isolated noncritical or metadata-only issue). Use spec FR-014 first-run thresholds. Evaluate rate brakes after at least 20 screened proposals for duplicate/no-contrast or 20 curated candidates for HOLD, and again at stage completion; record numerator, denominator, trigger, time, and explicit resume/withhold decision. An unexpectedly high REJECT rate (initial warning at 40% of at least 20 curated candidates) prompts cause review and escalates to a pause if it reflects a repeated systematic failure; individual sound rejections do not by themselves stop work. A brake blocks new promotion across slices; already promoted IDs remain stable and receive corrections if needed.

Derive counts from authoritative slice reports, proposal-screen events, QA records, source/ledger, and operation events. Keep generation, production decision, risk audit, random QA, promotion/build, and end-to-end wall time separately. Report provider calls/tokens/retrievals when captured and `unavailable` otherwise. Report production decisions per hour and active newly promoted cards per end-to-end hour only when measured, naming each numerator and time denominator. Final yield is active newly promoted concepts in canonical source divided by `requested_count` admitted candidates; count ever-assigned IDs and withdrawn rows separately so restoration never inflates growth. Reconcile `admitted_count = ACCEPT + HOLD + REJECT + pending` for the current decision snapshot, with active promoted, withdrawn, withheld, and pending dispositions; never count retry returns as new promotions. Track coverage before/after, baseline 137, final canonical count, and progress toward the approximately 200+, 500, and 1,000-card planning milestones without treating them as acceptance quotas. No 50× or universal quality claim.

## Implementation sequence for later task generation

1. **Reusable scaling infrastructure**: parent storage, references to existing Feature 003 artifacts, command skeleton, crash-safe operation checkpoints.
2. **Coverage and allocation**: category/alias inventory, gap-based draft, maintainer adjustment, frozen `requested_count` allocation (100 slots for the first run).
3. **Manifest, lifecycle, and resumption**: sequential at-most-12 slices, stable slot IDs, retry/reconciliation, bounded proposal cap.
4. **Redundancy filtering**: staged archive index and semantic shortlist, prior-same history, current-run cross-slice checks.
5. **Promotion and QA integration**: audit disposition, eligibility generation, existing guarded exporter, deterministic random sample, brakes, build, reconciled metrics, and maintainer workflow documentation.
6. **First operational execution**: run exactly one 100-candidate parent batch against the 137-card baseline; audit/correct/promote/build/QA/close, run the relevant test gates, and publish the operational report. Do not start batch two.

## Complexity Tracking

No constitution violations or exceptions. The extra parent-run layer is required by the existing 12-candidate Feature 003 cap and separate random-QA closure rule; it keeps the closed curation and Anki architecture intact.
