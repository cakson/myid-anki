# Feature 004 validation results

## Infrastructure fixture gates

- Coverage inventory maps all 137 baseline learner cards to one primary category and sees 328 historical candidates for exclusion planning. Unknown tags remain visible.
- Generation fixtures exercise 100 admitted candidates across at-most-12 slices, pre-ingest duplicate screening, zero-admission replacement, proposal-cap pause, replay after interrupted ingest, and malformed-response retry.
- Curation fixture exercises the frozen v3.1 optimistic route and confirms no canonical source mutation before promotion.
- Promotion fixtures exercise risk-selected audit clearance, current eligibility, promotion before random QA, offline build, closure after QA, idempotent repeat export, and withdrawal/restoration with a retained permanent ID.
- QA fixtures exercise deterministic stratified sample size, roster replacement, and metadata-only no-brake behavior.
- The initial pre-run gate passed `ruff check .`, `pytest -q` (246 tests), and `myid-anki validate` (137 concepts). The expanded fixture gate passed `pytest -q` (256 tests), including response-capture resume, report reconciliation, closure guards, and offline identity regression.

## Operational recovery observed so far

- Generation admitted exactly 100 candidates from 103 proposals in 22 bounded slices. Two malformed first-slice response attempts were archived; one compatible saved response was recovered after an adapter repair. A planned interruption at 28 admitted candidates resumed into the same parent run without regenerating completed slices.
- Frozen v3.1 curation settled all 100 candidates: 93 ACCEPT, 4 HOLD, 3 REJECT, with no pending decisions. The canonical source still validated at 137 cards at the risk-audit boundary.
- Risk audit was interrupted after the `two-learner-critical-errors` promotion brake. Two affected accepted cards were withheld through `resolve`; the parent run resumed with the brake active and reused completed audit records. The full audit later completed, all 25 uncleared cards were withheld, and the brake disposition was recorded before export.

## Final operational result and gates

- `corpus-004-001` is `complete`, with 100 admitted candidates and 68 guardedly promoted cards. The source grew from 137 to 205. The final parent report is `curation/production-runs/corpus-004-001/report.json`; it reconciles 68 ACCEPT + 29 HOLD + 3 REJECT = 100, 60 performed risk audits, 7 completed random-QA findings, 68 active new IDs, 0 withdrawals, and no pending audit.
- `pytest -q`: **267 passed** after the operational run. This includes the offline package identity regression over the 205-card canonical source, response-capture resume, audit gate, retained-ID restoration, QA brake recurrence, report reconciliation, and closure checks.
- `ruff check .`: passed after import formatting.
- `myid-anki validate`: **205 valid concepts, 0 media**.
- The guarded `scaling build` command wrote `dist/myid-anki.apkg` with **205 notes and 205 cards**; its source and package digests are in `curation/production-runs/corpus-004-001/build.json`.
- Source/ledger/report reconciliation checked 205 unique active source IDs, 68 new Feature 004 ledger assignments present in the source, all 137 baseline IDs and GUIDs unchanged, deck/model IDs unchanged, zero `same` learner rows, and no unresolved `curation/export-journal.json`. The ledger has 208 total assignments because it retains three historical assignments outside the 205 active source rows; this is expected retained identity history, not a duplicate active card.
- Every new active row points to a Feature 004 slice/candidate through the permanent-ID ledger. Each slice retains its generated proposal, v3.1 decisions, correction events where applicable, promotion eligibility, and parent audit references. All 25 uncleared audit cards were moved to HOLD before export; their correction history remains outside learner content.
- `curation/config.json`, `src/indo_malay_anki/curation/gate.py`, `src/indo_malay_anki/model.py`, and the Anki templates have no Feature 004 changes. The only Feature 003 source diff is the narrow `reopen_accepted_for_correction` workflow operation; the frozen v3.1 decision and guarded-export logic were not changed.
- Generation and audit pause/resume reused durable responses/records. Random QA recovered from a response-capture scanner defect without changing the sample. The `two-learner-critical-errors` brake was investigated and disposed after all uncleared cards were withheld. No second operational batch was created.

## Focused fixture checks

- `pytest -q tests/integration/test_scaling_generation.py`: validates exactly 100 admitted candidates across bounded slices, cross-slice duplicate screening/replacement, proposal-cap pause, response recovery, and the generation priority prompt.
- `pytest -q tests/integration/test_scaling_recovery.py tests/integration/test_scaling_curation.py tests/integration/test_scaling_promotion.py tests/integration/test_scaling_build_identity.py`: validates captured response reuse after interruption, audit retry after failed provider call, current audit clearance, active brake and stale digest withholding, guarded promotion and same-ID restoration, and offline baseline identity. Feature 003's `test_curation_export.py` and `test_curation_recovery.py` continue to cover source/ledger journal recovery and dependent-result invalidation without new policy code.
- `pytest -q tests/unit/test_scaling_qa.py tests/unit/test_scaling_report.py tests/integration/test_scaling_close.py`: validates deterministic QA selection/replacement, material withdrawal, metadata-only behavior, brake recurrence after disposition, final 100-candidate report denominators, pending/stale QA guards, invalid build and active brake rejection, and valid zero-clean-population closure.
- The combined eight-file Feature 004 fixture gate passed **28 tests**. The final full suite passed **267 tests**, `ruff check .` passed, and `myid-anki validate` confirmed **205 concepts**.
