# Feature 004 Production Run Guide

This guide describes the implemented Feature 004 production workflow. The parent run coordinates bounded Feature 003 v3.1 slices and keeps its own allocation, screening, audit, QA, and metrics records.

## Prerequisites

1. Use the project environment (`conda activate myid-anki`) with Python 3.12+, `pytest`, `ruff`, and the configured Feature 003 curation provider available for the operational run.
2. Before a future run, snapshot the current `data/vocabulary.tsv`, `curation/id-ledger.json`, and deck/model identity. The two completed operational runs grew the source from 137 to 205 to **270** cards; convergence does not start another run.
3. Confirm `curation/config.json` still selects production policy `3.1.0`; no experimental verifier or audit screen is enabled.
4. Review [data model](data-model.md), especially the parent/slice boundary and permanent-ID rules.

## Deterministic validation before provider calls

```sh
myid-anki validate
pytest -q tests/unit tests/contract tests/integration/test_curation_growth.py tests/integration/test_curation_recovery.py tests/integration/test_curation_export.py
ruff check src tests
```

Expected at convergence: source validation reports **270** concepts, all relevant tests pass, and lint succeeds. The existing Feature 004 tests cover category alias/unknown-tag accounting, allocation edit/freeze, staged redundancy, bounded sequential slices, restart, risk audit routing, eligibility generation, safety brakes, random sample reproducibility, report denominators, and stable IDs/GUIDs.

## Dry-run the workflow with fixtures

1. Create a temporary repository fixture with a small canonical corpus and historical candidates, including an exact cue, synonym, singular/plural pair, prior `same`, and a true distinct sense.
2. Create a parent run and inspect the coverage-based category draft; edit targets before approval. Confirm the approved target is frozen and totals the requested fixture count.
3. Simulate interrupted generation after provider response capture, interrupted curation/evidence, partial risk audit/correction, export or withdrawal after ledger replacement, and partial random QA. Resume each; confirm no completed candidate is regenerated and canonical source changes only after guarded export or withdrawal.
4. Seed a false friend, a clean ordinary contrast, a material HOLD, a rejected `same`, an audit-withheld candidate, and a metadata-only correction. Confirm correct v3.1 outcomes, required audit gating, no-brake metadata behavior, and report reconciliation. Promote a fixture card, then record an unsafe QA finding and verify guarded withdrawal removes its source row, keeps its ledger ID, survives interruption, and restores that ID only after correction and current eligibility.
5. Promote a cleared closed slice before random QA finishes. Select QA only after final production decisions and required risk-audit dispositions establish the clean-ACCEPT population. Confirm parent status remains open, random QA does not block the export, and closure fails until the sample matches the final population and its review, corrections, report, and build pass.

## Future corpus-growth run

The workflow is repeatable and does not require another architectural calibration before a new batch. A future maintainer should choose a new run ID and requested candidate count, inspect the current 270-card coverage inventory, review and optionally adjust the generated allocation, then freeze it before generation. The commands below illustrate a future 100-candidate run; **do not execute them during Feature 004 convergence**.

```sh
BATCH_RUN_ID="replace-with-unique-run-id"
python -m indo_malay_anki.scaling create --run "$BATCH_RUN_ID" --count 100 --proposal-cap 200
python -m indo_malay_anki.scaling allocation --run "$BATCH_RUN_ID"
# Optional: allocation --run "$BATCH_RUN_ID" --set category=count --reason "Reviewed current gaps"
python -m indo_malay_anki.scaling approve --run "$BATCH_RUN_ID" --reason "Reviewed current coverage and allocation"
python -m indo_malay_anki.scaling generate --run "$BATCH_RUN_ID"
python -m indo_malay_anki.scaling curate --run "$BATCH_RUN_ID"
python -m indo_malay_anki.scaling risk-audit --run "$BATCH_RUN_ID"
python -m indo_malay_anki.scaling status --run "$BATCH_RUN_ID"
# Resolve required audit findings and any active brake through the commands below before export.
python -m indo_malay_anki.scaling promote --run "$BATCH_RUN_ID"
python -m indo_malay_anki.scaling build --run "$BATCH_RUN_ID"
python -m indo_malay_anki.scaling qa-select --run "$BATCH_RUN_ID"
python -m indo_malay_anki.scaling qa-run --run "$BATCH_RUN_ID"
python -m indo_malay_anki.scaling close --run "$BATCH_RUN_ID"
python -m indo_malay_anki.scaling report --run "$BATCH_RUN_ID" --json
```

Inspect the frozen allocation and generation/redundancy records before curation. Check every risk-selected card for current independent clearance. Use `resolve --run "$BATCH_RUN_ID" --candidate slice:candidate --action correct|hold|reject --reason ...` for corrections or withholding; a correction may need `--record changes.json`, repeated curation, and a fresh risk audit. A triggered brake blocks promotion until investigation and `brake-disposition --run "$BATCH_RUN_ID" --reason ... --resolution ...`. A stopped command can be retried with the same run ID; completed candidate work is reused. Guarded promotion can precede random QA, but closure waits for the monitoring sample, any material finding resolution, and a current build. Inspect the final report's yield, coverage, audit findings, separate stage costs, and unavailable metrics. See [the convergence report](convergence-report.md) for the operating baseline and known limitations.

## Historical first 100-candidate operational run

The commands below document completed Batch 1, `corpus-004-001`. They are historical and must not be rerun to create a new batch.

```sh
python -m indo_malay_anki.scaling create --run corpus-004-001 --count 100 --proposal-cap 200
python -m indo_malay_anki.scaling allocation --run corpus-004-001
python -m indo_malay_anki.scaling approve --run corpus-004-001 --reason "Reviewed coverage gaps"
python -m indo_malay_anki.scaling generate --run corpus-004-001
python -m indo_malay_anki.scaling curate --run corpus-004-001
python -m indo_malay_anki.scaling risk-audit --run corpus-004-001
python -m indo_malay_anki.scaling status --run corpus-004-001
python -m indo_malay_anki.scaling promote --run corpus-004-001
python -m indo_malay_anki.scaling build --run corpus-004-001
python -m indo_malay_anki.scaling qa-select --run corpus-004-001
python -m indo_malay_anki.scaling qa-run --run corpus-004-001
python -m indo_malay_anki.scaling report --run corpus-004-001
```

Optional `allocation --set category=count` edits must still total 100 before approval. A failed command preserves its captured response and can be retried with the same run ID. Inspect required audit findings before promotion; `needs-correction` and `withheld` block their slice. Use `resolve --candidate slice:candidate --action correct|hold|reject --reason ...` for corrections or withholding, with `--record changes.json` for changed fields. A material QA finding on a promoted card triggers guarded withdrawal. After correction, repeat `curate`, `risk-audit`, `qa-resolve`, `promote`, and `build` as needed. An active safety brake requires investigation and `brake-disposition --reason ... --resolution ...`. Random QA is monitoring; it cannot establish that unsampled cards are correct. Then close:

```sh
python -m indo_malay_anki.scaling close --run corpus-004-001
python -m indo_malay_anki.scaling report --run corpus-004-001 --json
myid-anki validate
myid-anki build
```

The completed Batch 1 admitted exactly 100 candidate references across sequential Feature 003 slices and promoted 68 cards, growing the source from 137 to 205. The separately authorized Batch 2 then grew it to 270. Both runs retained baseline IDs/GUIDs and closed only after random QA.

## Review the final operational report

Verify that it states the run's actual baseline and final size; admitted count and proposal waste; coverage before/after; relation/confidence and fast-path/escalation distributions; audit selected/completed/findings; random QA selected/completed/findings; promotable, active newly promoted, withdrawn, ever-assigned, and withheld counts; separate generation, production decision, risk-audit, random-QA, promotion/build, and end-to-end time; measured production decisions per hour and active promoted cards per end-to-end hour with their denominators; retries or resumability incidents; safety-brake disposition; and build/test results. Missing timing or usage must say `unavailable`. The report must not claim that random QA guarantees unsampled correctness or that a 200/500/1,000-card target justifies weak cards.
