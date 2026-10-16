# Planned Production Run CLI Contract

This is the Feature 004 interface to implement, not a claim that these commands already exist. Commands are local and resumable. They print a concise status and a JSON report path; failures use a nonzero exit code and leave a durable event. Existing `python -m indo_malay_anki.curation` commands remain available and keep their v3.1 semantics.

## Common rules

- Entrypoint: `python -m indo_malay_anki.scaling <command> --run <run-id> ...`.
- A run ID is unique and stable. `--count` becomes the manifest's `requested_count`; the first operational run uses 100, while reusable logic uses the recorded count. Reissuing an already completed command with identical inputs is a no-op or returns the prior result. Conflicting inputs fail with a clear reason; they never silently overwrite a frozen allocation or accepted candidate.
- Each mutating command acquires the parent-run lock, writes a start/completion/failure event, and records input/output digests. External calls persist raw response before ingestion.
- `status` and `report` are read-only. `--json` provides machine-readable output for automation; ordinary output names the next allowed operation.
- The CLI never edits `data/vocabulary.tsv` except via the guarded promotion command. Normal build remains a separate offline operation.

## Commands and guards

| Command | Inputs | Required state / behavior | Durable result |
| --- | --- | --- | --- |
| `create` | `--run`, `--count <positive integer>`, optional `--proposal-cap <integer>` | Unique run ID; snapshot current baseline and coverage; create draft allocation. First milestone invokes this once with `--count 100 --proposal-cap 200`. | Draft manifest, coverage snapshot, suggested allocation/rationale. |
| `allocation` | `--run`, optional `--set category=count` repeated | In `draft`, show or adjust the coverage-based draft; validate category IDs and total. No generation yet. | Revised draft and edit rationale. |
| `approve` | `--run`, `--reason` when allocation differs from draft | In `draft`; final counts sum to manifest `requested_count`; freeze source/category/strategy digests. | `allocation-approved` manifest. |
| `generate` | `--run`, optional `--resume` | Approved/generating; make sequential Feature 003 slices of at most 12, screen validated raw proposals, and fill frozen slots until `requested_count` admitted or cap reached. | Proposal-screen records, slice/candidate refs, generation checkpoints, or a shortfall pause. |
| `curate` | `--run`, optional `--resume` | `requested_count` admitted; call existing v3.1 stages and decision gate, reusing completed work. Feature 003 may auto-close a slice report once no decisions are pending. | Current slice reports and ACCEPT/HOLD/REJECT/pending roster. |
| `risk-audit` | `--run`, optional `--resume`, optional `--record <path>` | Select only v3.1-required risk audits; run a separate reviewer invocation or ingest a versioned [audit record](audit-record.md). Reject stale/non-independent records; incomplete findings stay pending. | Required/cleared/withheld audit refs and separate audit work metrics. |
| `resolve` | `--run`, `--candidate <slice:candidate>`, `--action correct|hold|reject`, `--reason`, optional `--record <path>` | Uses the narrow, event-recorded correction reopen operation for a closed auto-accepted slice, then Feature 003 revise/finalize paths; refreshes report and invalidated audit. An already promoted card with unresolved material risk or current HOLD/REJECT is guardedly withdrawn; a later corrected card restores the same ID only through current guarded export. | Correction/withdrawal history, refreshed eligibility, and unchanged permanent-ID proof. |
| `promote` | `--run`, optional `--resume` | No active promotion brake or pending withdrawal. For each closed slice with all current ACCEPTs eligible, construct eligibility record from decision/content digests, audit outcomes, and absence of unresolved material QA findings, then call guarded export. Does not wait for random QA selection or clean-item review. | Per-slice promotion attempts, source/ledger digests, newly assigned and active IDs. |
| `build` | `--run` | No pending withdrawal; source valid; invoke existing offline validation/build. | Build result and note/card count, without modifying curation decisions. |
| `qa-select` | `--run` | All requested candidates have final production decisions and required risk-audit dispositions. Freeze the current clean-ACCEPT population; promotion may already have happened. If later correction changes clean-ACCEPT membership, invalidate and replace the roster before closure while preserving prior findings. | Population digest, strata, sample roster and count. |
| `qa-record` | `--run`, `--candidate <slice:candidate>`, `--finding <class>`, `--record <path>` | Candidate is on roster; finding class valid. A material finding on an already promoted card starts guarded withdrawal, which must reconcile before the QA item is complete; a later correction links to this record. Metadata-only findings do not withdraw. | QA finding, withdrawal/correction reference if needed, and brake evaluation. |
| `close` | `--run` | All `requested_count` admitted candidates have final outcomes; required audits resolved for active promoted cards; QA roster matches the final clean-ACCEPT population and is fully reviewed (or empty); withdrawals/brakes/corrections disposed; successful offline build; report reconciles. | `complete` manifest and final run report. |
| `pause` / `resume` | `--run`, `--reason` for pause; `--resolution` for brake resume | Preserve prior state; resume checks current artifacts and unresolved triggers. | Pause/resume event and state. |
| `status` / `report` | `--run`, optional `--json` | Any state; read-only. | Current lifecycle, pending work, counts and final/provisional report path. |

## Failure and retry contract

- Provider or retrieval failure creates a failed attempt event and leaves affected candidate work pending; it does not create a linguistic REJECT. A retry checks the prior input digest, durable response, and successful Feature 003 stage event first.
- An interrupted export or withdrawal calls existing `recover_export` before checking source/ledger and retrying. A withdrawal checks the ledger origin and current source row, removes only that row through existing validated journaled commit, and retains its ID assignment. If already absent under that assignment, retry records no second withdrawal; mismatched content or identity triggers a promotion brake. Pending withdrawal blocks promotion, build, and closure.
- A safety brake stops later `promote` calls across all slices. Candidate-level HOLD/REJECT does not stop other cleared slices. Metadata-only QA findings are warnings.
- `close` fails while QA findings, required dispositions, build verification, or report totals are outstanding. It does not retroactively make random QA a gate for an earlier eligible promotion.

## Report contract

The JSON run report contains `run_id`, workflow/policy versions, baseline/final corpus size, frozen allocation and before/after coverage, requested/proposed/screened/admitted counts, current decisions, relation/confidence/risk distributions, duplicate/no-contrast reasons, required audit and random-QA counts/findings, promotable/active-promoted/withdrawn/withheld counts, ever-assigned IDs, safety-brake history, separate generation/production/audit/QA/promotion/build/end-to-end time, provider usage or `unavailable`, production decisions per hour and active newly promoted cards per end-to-end hour where measured with explicit numerators/denominators, final active promoted yield, and progress toward the approximately 200+, 500, and 1,000-card planning milestones. The readable summary uses the same underlying data; milestones are never acceptance quotas.
