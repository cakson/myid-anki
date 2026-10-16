# Feature 004 convergence report

Feature 004 has demonstrated a **repeatable, resumable 100-candidate corpus-scaling workflow**. Two independent operational batches completed with guarded promotion and random-QA closure. The canonical learner source is **270 cards**. High model and audit cost is a known operating constraint, not a remaining Feature 004 correctness blocker. This convergence did not generate, curate, or promote any additional vocabulary.

## Converged architecture

The production sequence is:

`coverage inventory → allocation draft → maintainer adjustment → frozen allocation → candidate generation → redundancy screening → Feature 003 v3.1 curation → individual risk-based independent audit → safety-brake disposition → guarded promotion → offline deck build → random QA monitoring → reconciled report and closure`.

Feature 004 owns the coverage model, editable then frozen category allocation, persistent parent manifest and lifecycle, candidate-level checkpoints and idempotent resume, staged cross-run redundancy checks, audit orchestration, safety brakes, guarded-promotion integration, deterministic random-QA sample, and per-batch counts and cost reports. The parent run references bounded Feature 003 slices and their authoritative candidate, decision, evidence, and correction records. Feature 003 production policy **3.1.0**, its guarded export rules, permanent concept IDs, ID-derived Anki GUIDs, and the note/card structure remain the production foundation. Random QA monitors promoted quality and is required for batch closure; it is not a universal pre-promotion gate. Risk-selected cards still need current independent clearance before promotion.

The implementation uses local JSON/TSV artifacts and resumable CLI commands. A failed call leaves completed candidate work intact. An active promotion brake blocks further export until investigation and explicit disposition. Withheld, HOLD, REJECT, stale, or uncleared candidates remain outside learner content. The normal deck build validates reviewed source and runs offline.

## Two completed operational batches

| Measure | Batch 1: `corpus-004-001` | Batch 2: `corpus-004-002` |
| --- | ---: | ---: |
| Starting corpus | 137 | 205 |
| Proposals / admitted candidates | 103 / 100 | 100 / 100 |
| Final ACCEPT / HOLD / REJECT | 68 / 29 / 3 | 65 / 26 / 9 |
| Independent risk audits | 60 | 49 |
| Audit cleared / issues needing correction | 35 / 25 | 37 / 12 |
| Learner-critical audit findings | 17 | 9 |
| Guardedly promoted | 68 | 65 |
| Promoted yield per admitted candidate | 68% | 65% |
| Resulting corpus | 205 | **270** |
| Random QA | 7 reviewed; 6 clean, 1 metadata-only | 7 reviewed; 7 clean |
| Confirmed duplicate / no-contrast waste | 1 / 0 | 2 / 2 |

Both runs triggered the configured promotion brake after learner-critical audit findings. Each completed its required audit scope, withheld uncleared cards, recorded an investigation and explicit brake disposition, and exported only currently eligible cards. Batch 1 exercised generation, audit, and QA recovery. Batch 2 recovered one malformed verifier response through candidate-level resume without regenerating completed candidates. Neither run left a pending audit disposition or export journal at closure. The full evidence is in the [Batch 1 report](first-batch-report.md), [Batch 2 report](second-batch-report.md), and their persistent run manifests and final reports under `curation/production-runs/`.

The 68% and 65% promoted yields, audit workloads, and roughly 50 minutes of measured model work per run are broadly consistent operationally. Two batches are insufficient for a statistical quality or yield claim. The audits materially prevented unsafe promotion: they found 25 issues in Batch 1 and 12 in Batch 2. Random QA found one metadata-only issue in Batch 1 and none in Batch 2; those small samples cannot certify unsampled cards.

## Coverage outcome

The reviewed allocation started each run from the current corpus inventory rather than repeating the previous allocation. Batch 1 expanded all 20 tracked categories. Batch 2 expanded **19 of 20**, including services from 6 to 12 cards, daily life from 6 to 10, and directions/location from 6 to 9. Home, the largest category, received only three candidate slots in Batch 2. `emotions` remains at **four cards** after seven Batch 2 proposals were held or rejected for shared synonyms, artificial contrasts, or an overstated relation. This is input for future candidate selection, not a reason to weaken v3.1 or a Feature 004 workflow blocker. Category balance is a planning aid, not an acceptance quota; the detailed before/allocation/after table is in the [Batch 2 report](second-batch-report.md).

## Fixed-batch efficiency conclusion

The [completed efficiency benchmark](efficiency-benchmark.md) replayed saved Batch 1 candidates without corpus mutation. **No optimization was adopted.** Compacting the normalization archive reduced input tokens but changed a saved duplicate decision. Grouping production verifier candidates changed decisions or resolved cues. Grouped independent risk audits cleared or missed learner-critical findings. Those savings failed the quality and decision-fidelity rule. The production context remains complete where needed, verification remains at its current candidate-level orchestration, and risk audits remain individual and independent. These are completed negative results, not unfinished optimization tasks. No new efficiency experiment is required for Feature 004 convergence.

Batch 2's measured operating baseline was **303 model calls**, **10,507,060 input tokens**, **145,568 output tokens**, and **49.75 minutes of model-call time**, or about **4.66 calls per promoted card**. That total includes one archived failed verifier call that the machine report's successful-call totals omit. Batch 1 also used **303 calls**, about **4.46 calls per promoted card**, with 10,101,339 input tokens and 50.49 minutes of measured model-call time. Production and independent audit remain separate cost centers in the per-batch reports. The workflow is model-call and token intensive; the benchmark shows that the tested cheaper routes did not preserve the required decisions and audit sensitivity.

## Future production path and boundaries

A future corpus-growth batch can reuse the [production run guide](quickstart.md): inspect current coverage; review and adjust the proposed allocation; freeze it; generate the declared candidate count; run unchanged v3.1 curation; complete every required individual risk audit; correct or withhold findings and dispose any active brake; guardedly promote eligible cards; build the deck; review random QA; then close with a reconciled report. It needs a new run ID, a declared candidate target and proposal cap, and a fresh coverage review. It does **not** need another architectural calibration before every batch. No Batch 3 was started during convergence.

Remaining work belongs to later corpus operation or features: growing toward 500 and approximately 1,000 useful cards, improving difficult coverage areas such as emotions, reducing cost only if a future quality-preserving method is established, community contributions, learner feedback and post-release ingestion, images/audio, and an expert-human throughput benchmark. Feature 004 does not require perfect category balance, autonomous audit removal, lower model cost, or 1,000 generated cards to be complete. The two runs showed recurring overstated national contrasts; the current independent audit and brake process caught and withheld them. That pattern should inform future proposal selection without reopening closed Feature 003 policy for individual errors.

## Final validation and corpus state

The convergence assessment checked **21 functional requirements, 9 success criteria, 13 user-story acceptance scenarios**, the plan's architecture and integration decisions, and the constitution's identity, correctness, validation, offline-build, and inspectability principles against the current code, tests, and two final run records. All **71 implementation tasks** are complete. No remaining buildable gap or constitution violation was found, so `tasks.md` was left unchanged; no unfinished optimization task was added.

Convergence validation: `pytest -q` **270 passed**; `ruff check .` and `ruff format --check .` passed; source validation reported **270 concepts**; the offline `.apkg` build produced **270 notes and 270 cards**. Active concept IDs and derived GUIDs are each unique, and all **137 pre-Feature-004 ID/GUID pairs** remain unchanged. The 205-card pre-Batch-2 snapshot also remains identity-stable. Deck and model IDs are unchanged. There is no unresolved export journal. The canonical corpus remained **exactly 270 cards** throughout convergence.

**Convergence decision: Feature 004 is ready for review.** The specified scaling responsibilities are implemented and have completed two independent 100-candidate cycles. High model/audit cost is the measured operating constraint of the frozen quality architecture, not a remaining correctness or resumability defect.
