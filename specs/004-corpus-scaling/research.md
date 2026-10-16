# Feature 004 Research and Design Decisions

## 1. Run size versus Feature 003 batch limit

**Decision**: One Feature 004 production run coordinates sequential Feature 003 curation slices of at most 12 candidates. Ten 10-candidate slices are the first run's scheduling target; additional bounded slices fill screened-out slots until the manifest's `requested_count` is admitted (100 for the first run). Screen captured raw generation responses before ingesting only admitted proposals into each slice. Keep all-screened-out attempts as zero-admission slice records.

**Rationale**: `curation/records.py` validates `BatchManifest.candidate_limit` in 1–12, and `curation/config.json` sets maximum 12. `workflow.init_batch` freezes archive history for each slice. Sequential slice creation exposes earlier candidates to later slices; a parent exclusion index catches unpromoted cross-slice collisions. A new parent layer preserves v3.1.

**Alternatives considered**: Raising the 12 limit or replacing Feature 003 generation would modify a closed dependency; creating all slices up front would freeze stale archives; 100 one-candidate slices would add avoidable provider/administrative work.

## 2. Coverage model and allocation

**Decision**: Use a small versioned primary-category list and explicit aliases for current freeform tags, producing one primary category per canonical concept. Historical candidates inform exclusions, not learner coverage. Draft category slots from underrepresentation and everyday usefulness; let a maintainer adjust and freeze totals to the manifest's `requested_count` (100 for the first run) before generation.

**Rationale**: `data/vocabulary.tsv` already carries tags but does not have a controlled category field. An explicit mapping is reviewable and adequate for the first 100. It respects the user's chosen editable draft workflow and avoids equal-size quotas.

**Alternatives considered**: A new ontology/database is unnecessary; counting all tags as equal categories would double-count cards and exaggerate coverage; fully automatic allocation contradicts clarification.

## 3. Redundancy screening

**Decision**: Reuse Feature 003 `archive_candidates`, generation archive snapshots, `comparison_key`, `find_deterministic_overlaps`, normalize/dedupe decisions, and final export overlap guard. Add a parent-run index of canonical, historical, and admitted proposals; use deterministic keys first, then bounded semantic resolution of only likely synonyms/near-equivalents.

**Rationale**: Existing keys catch case/punctuation/plural and exact bilingual-answer matches, but not every synonym. `archive_candidates` includes prior HOLD/REJECT and canonical source, so it can also identify repeated no-contrast ideas. Screening early saves provider calls; final guards protect identity if early screening misses a case.

**Alternatives considered**: Semantic review of every proposal is costly; exact matching alone misses alternate English labels; promoting first and deduplicating later risks stable-ID conflicts.

## 4. Resumable storage and operation boundary

**Decision**: Store an atomic parent manifest plus append-only run events and durable response/checkpoint references. Use existing Feature 003 atomic file and candidate-event patterns for slices. On resume, reconcile recorded checkpoints against slice events and source/ledger rather than trust a single status flag.

**Rationale**: `BatchStore` already supplies locked append-only events and atomic JSON; `ingest_response` reuses an identical successful response and rejects changed generation identity. Durable response capture covers the model-return/ingest gap. `export.recover_export` already repairs interrupted source/ledger commits.

**Alternatives considered**: A database introduces needless infrastructure; one monolithic command makes failure recovery and human audit difficult; treating a failed provider call as REJECT would corrupt linguistic metrics.

## 5. Promotion before parent closure

**Decision**: Feature 003 may auto-close a slice report when all production decisions are final, before risk audit. Complete any required independent audit against the current decision and content under the [audit record contract](contracts/audit-record.md). Its current `reopen_candidate` only handles explicit HOLD/REJECT, so an auto-accepted card in a closed slice cannot use `revise_candidate`; add one narrow, event-recorded correction reopen operation with compatibility tests. A material finding then reopens, revises, reruns invalidated stages, and refreshes the slice report. Generate slice eligibility records from current decisions, final projected content, audit clearance, and brake state; invoke existing `export_batches` only for closed slices whose accepted candidates are all ready. The Feature 004 parent may remain in `qa-monitoring`. An unsafe post-promotion QA finding or current HOLD/REJECT uses a separate guarded withdrawal: verify the source row and ledger assignment, remove only that row through existing validated journaled commit, and retain the ID assignment/history. A later corrected card returns through guarded export with the same ID/GUID. Reconcile source/ledger to count active growth separately from ever-assigned IDs.

**Rationale**: `export_batches` requires a closed slice/report, no pending candidates, current v3.1 `promotion-eligibility.json`, and clear audits; it already checks final cue/relation, duplicates, ledger identity, and journaled commit. It never removes a previously promoted row when that candidate later becomes HOLD/REJECT. The existing `commit_learner_rows` provides validated journaled source/ledger replacement for a narrowly guarded withdrawal without changing v3.1's promotion predicate. No production writer currently creates eligibility records, so Feature 004 must make that routine. A parent run can remain open for random QA without weakening export.

**Alternatives considered**: Preview-only fails the feature goal; manual eligibility JSON edits are not repeatable; relaxing the exporter to accept open Feature 003 batches changes its guard; a separate duplicate export implementation would risk identity divergence. Eligible cards in a blocked slice wait until that slice's accepted candidates are resolved, while other slices may promote.

## 6. Random QA and safety brakes

**Decision**: After all requested candidates have final production decisions and required risk-audit dispositions, freeze the clean-ACCEPT population, its digest, a deterministic sample seed, and selection roster. Review max(5, ceil(10% of clean accepted)) first-run candidates, capped by available clean accepts; sampling spans available risk/confidence strata. If a later correction changes clean-ACCEPT membership in either direction, invalidate the roster and document replacement selection before closure while preserving prior findings. Keep QA outside promotion eligibility, but require its findings before parent-run closure. Classify individual withholding, promotion brakes, parent pauses, and warnings separately.

**Rationale**: This follows the clarification that promotion can precede sample completion while the final report must include QA. The sample observes residual quality; it cannot prove unsampled cards are correct. FR-014 sets first-run thresholds. Metadata-only corrections do not halt work.

**Alternatives considered**: Universal pre-promotion random audit contradicts closed Feature 003 policy; closing before QA findings would leave the final batch report incomplete; an audit-screen research cycle is out of scope.

## 7. Throughput and report denominators

**Decision**: Report proposed, screened-out, admitted, curated, accepted, risk-audited, QA-reviewed, promotable, active newly promoted, withdrawn, ever-assigned, withheld, and rejected separately. Active newly promoted/admitted is final batch yield. Separate generation, production decision, risk-audit, QA, promotion/build, and full elapsed time; compute production decisions per hour and active newly promoted cards per end-to-end hour only from measured values and explicit denominators, otherwise mark unavailable.

**Rationale**: Existing `curation/report.py` closes a slice and records decisions but is not a parent-run operations report. `curation/records.py` operation events include elapsed time and token fields. Returning a previously assigned ID on export is not a new card; ledger/source deltas are authoritative.

**Alternatives considered**: ACCEPT/admitted overstates released-card yield; adding audit time to production decision throughput hides audit cost; inferred tokens or human-time comparisons would be unsupported.

## 8. Execution and quality boundary

**Decision**: Planning stops at design artifacts. Implementation tasks will build infrastructure first, then run exactly one 100-admitted-candidate production run and record the resulting deck and operational report.

**Rationale**: The first run is an operational scaling test of frozen v3.1. It must not recalibrate policy or auto-chain toward 500 or 1,000.

**Alternatives considered**: Generating candidates during planning would bypass the implementation and validation gates; an automatic second batch would exceed the user-authorized milestone.
