# Feature 004 Data Model

The Feature 004 parent run stores orchestration state. Feature 003 slice directories remain authoritative for generated candidates, v3.1 stage results, decisions, evidence, and closed reports. `data/vocabulary.tsv` and `curation/id-ledger.json` remain authoritative for promoted concepts and permanent IDs.

## Entities and ownership

| Entity | Planned location | Key fields | Relationship and validation |
| --- | --- | --- | --- |
| Category catalog | `curation/coverage-categories.json` | schema/version, category IDs, label, tag aliases | Small fixed vocabulary. Each known tag maps deterministically to one primary category; unknowns are surfaced for review. Original TSV tags are unchanged. |
| Coverage snapshot | Parent run snapshot | source digest, source card count, per-category counts, unmapped rows, historical no-contrast/duplicate references, recorded_at | Derived from canonical TSV plus relevant history; canonical concept counted once. Freeze baseline at allocation approval and compute an after snapshot at closure. |
| Allocation draft | Parent run manifest | proposed counts, rationale/gaps, inventory digest, edited counts, edit rationale | Draft total equals `requested_count` after edits. Maintainer approves only before generation. |
| Production-run manifest | `curation/production-runs/<run-id>/manifest.json` | schema/workflow version, run ID, timestamps, `requested_count`/admitted count, proposal cap, frozen allocation/digest, state, prior state if paused, slice references, sample seed/target, brake policy, report status | One parent for many Feature 003 slices. Run ID unique; first run requests 100; every run's allocated slots sum to its `requested_count`. Manifest carries references, not copies of decisions. Atomic replacement. |
| Run event/checkpoint | `curation/production-runs/<run-id>/events/` | sequence/event ID, kind, state transition, input digest, output path/digest, timestamp, duration/usage, error if any | Append-only history. A completed checkpoint is reusable only if its input and referenced output digests still match. |
| Slice reference | Parent manifest | slice ID, category/slot range, requested <=12, admitted IDs, current status/report path | References a Feature 003 `BatchStore`. Candidate reference is `(slice_id, candidate_id)` and unique across parent run. |
| Proposal-screen record | Parent run records | proposal ref, attempt ref, cue/sense, category, screening outcome, matched historical/current refs, rationale, admitted candidate ref if any | Outcomes: admitted, duplicate, redundant, prior-same, invalid, distinct-sense-reviewed. An all-screened-out initialized slice has a parent zero-admission attempt record and no Feature 003 candidates or export. Only admitted records occupy a requested candidate slot; no permanent concept ID yet. |
| Risk-audit and correction reference | `curation/production-runs/<run-id>/audits/<slice-id>/<candidate-id>.json` plus parent events | candidate ref, v3.1 selection reasons, current decision/content/packet digests, independent reviewer invocation, claim reviews, verdict, correction refs, usage | Versioned [audit contract](contracts/audit-record.md) is authoritative for risk clearance; Feature 003 stage/decision history remains authoritative for production outcome. |
| Promotion/withdrawal attempt | Parent run records | candidate and slice IDs, operation, input decision/content or finding digest, current unresolved-QA status, eligibility file digest where promoting, source/ledger before/after digests, assigned concept ID, reason, status | Promotion uses guarded Feature 003 export and is blocked by an unresolved material QA finding on that candidate; random-QA selection alone never blocks it. Withdrawal verifies the current assignment and removes only its source row through the existing validated, journaled source/ledger commit. Reconcile after interruption. The ledger assignment survives withdrawal and restoration. |
| QA sample and finding | Parent run records | seed, frozen clean-ACCEPT population digest/count, roster, selected/completed status, candidate ref, finding class, correction ref | Select after all requested candidates have final production outcomes and required risk-audit dispositions. Earlier promotion is allowed. Any later clean-ACCEPT membership change invalidates the roster and requires documented replacement selection before closure; retain prior findings. Content-only corrections retain the roster. Findings classify learner-critical answer, cue/content, metadata-only, or no issue. |
| Safety-brake record | Parent run events | trigger, numerator/denominator, scope, timestamp, affected refs, investigation, release/withhold decision | Promotion brake blocks all new slice exports until resolved. Metadata-only findings cannot create a brake alone. |
| Final run report | `curation/production-runs/<run-id>/report.json` and readable summary | reconciled counts, category before/after, relation/confidence/risk distributions, audit/QA findings, performance, brake dispositions, final corpus count, closure timestamp | Derived from parent events, slice reports, source/ledger and QA records. Mark unavailable measurements explicitly. Finalized only when sample and build are complete. |

## Identity and references

- Parent run ID and slice IDs use the existing safe-ID convention. Use deterministic slice IDs such as `<run-id>-s01`, with ordinal assigned once; retries reuse the same ID.
- Candidate IDs remain Feature 003 slice-local IDs. The stable parent reference is `<slice-id>:<candidate-id>`. Parent slot identity is assigned before a model call so retries do not produce a new slot.
- A proposal screened out before Feature 003 admission has a parent proposal ID and disposition but no Feature 003 candidate ID or permanent concept ID. Preserve its link to the captured raw generation response and any matched historical reference. Only admitted proposals are passed to Feature 003 generation ingest.
- Permanent concept IDs are assigned only at guarded promotion by `curation/ids.py`, never at proposal screening, generation, or QA selection. Withdrawal preserves the assignment; guarded restoration reuses it. Existing IDs/GUID derivation are immutable.
- Parent records store paths/digests to authoritative Feature 003 candidate, report, audit, eligibility, and source artifacts. A digest mismatch invalidates downstream parent checkpoints and blocks promotion/closure until reconciled.

## Parent state transitions

| From | To | Guard |
| --- | --- | --- |
| New | `draft` | Unique run ID, baseline inventory captured, requested count and proposal cap valid. |
| `draft` | `allocation-approved` | Maintainer reviewed/edited allocation; category counts sum to requested count; baseline and final allocation frozen. |
| `allocation-approved` | `generating` | Generation strategy/prompt pin and slice schedule recorded. |
| `generating` | `curating` | `requested_count` distinct admitted candidates across slices (100 for the first run), or pause with shortfall after proposal cap. |
| `curating` | `awaiting-risk-audit` | Current v3.1 decisions available; required audit roster computed. |
| `awaiting-risk-audit` | `promotion-ready` | At least one closed slice has current accepted eligible candidates, all accepted in that slice cleared or given a current HOLD/REJECT; no active promotion brake. Other slices may remain under review. |
| `promotion-ready` | `promoting` | Promotion attempt checkpoint and current eligibility digests recorded. |
| `promoting` | `promotion-ready` or `qa-monitoring` | Journal recovery and source/ledger reconciliation finished; more slices may become ready, or production promotion phase ends. |
| `qa-monitoring` | `complete` | QA sample reviewed or no clean accepted population, findings/corrections/brakes resolved, build verified, final report reconciled. |
| Any noncomplete state | `paused` | Explicit user pause, provider failure requiring intervention, proposal shortfall, safety brake, or identity/export inconsistency; prior state and reason stored. |
| `paused` | Prior state | Explicit resume after precondition check and recorded investigation/disposition if brake triggered. |

State is a human-readable summary, not the sole truth. Per-slice and per-candidate checkpoints permit overlap between curation, audits, and already cleared slice promotion. An individual provider failure stays pending; the parent state moves to `paused` only when forward progress requires intervention. `complete` is terminal for the first run; later corrections are separate recorded maintenance events, not a rewrite of completed history.

## Reconciliation and invariant rules

1. `requested_count = admitted_count + unfilled_slots`; a run may close only when admitted count equals its requested count (100 for the first run). If the target cannot be reached at the proposal cap, it pauses and records the shortfall rather than pretending success.
2. `admitted_count = accepted + hold + reject + pending` at each current decision snapshot. At a reconciled checkpoint, active promoted candidates are a subset of current accepted outcomes with valid audit clearance and no unresolved material finding. A batch brake blocks new promotion; it does not by itself remove cards promoted earlier. Ever-assigned but withdrawn IDs are counted separately.
3. `proposed_count = admitted_count + screened_out_count + pending_proposal_count`; screened-out reasons are disjoint and recorded even if a provider call failed after response capture.
4. A category's admitted count cannot exceed its frozen allocation. If a category cannot fill its slots within the proposal cap, pause with a documented shortfall; do not silently alter the frozen plan or substitute low-value candidates.
5. A candidate origin has at most one ledger assignment, and a permanent ID appears at most once in canonical source. Repeated export or restoration of an existing assignment counts zero new IDs; final active corpus growth excludes withdrawn rows.
6. At closure, the QA sample population matches the final clean-ACCEPT roster, every sampled item has an outcome, every withdrawal and brake has a disposition, the report totals reconcile, and the final source passes validation and offline deck build.
