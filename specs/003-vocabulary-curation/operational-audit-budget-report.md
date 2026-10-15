# Feature 003 operational audit-budget calibration

Date: 2026-10-15. Production policy v3.1, its verifier, and the current deterministic audit router were frozen. No new candidates, linguistic calls, risk detectors, or source research were used for this calibration. Reproduce the cohort and simulations with `PYTHONPATH=src python scripts/calibrate_operational_audit_budget.py`. The frozen cohort and 4,096-seed output are in `operational-audit-cohort.json` and `operational-audit-budget-simulation.json`.

## Evaluation set and labels

| Fresh cohort | Production ACCEPTs | Independently audited | Known critical | Deterministically routed | Critical caught by deterministic router |
|---|---:|---:|---:|---:|---:|
| Batch 1 | 44 | 44 | 3 | 18 | 3 |
| Batch 2 | 40 | 40 | 6 | 36 | 6 |
| Final 50 | 38 | 27 | 3 | 20 | 2 |
| Prospective preference 50 | 38 | 27 | 3 | 21 | 3 |
| Technical borrowing 25 | 22 | 15 | 5 | 12 | 4 |
| **Total** | **182** | **153** | **20** | **107** | **18** |

The 153 labeled accepts comprise 85 confirmed good, 48 correctable but publishable, and 20 critical (9 materially misleading, 6 should reject, 5 should hold). A material wrong answer or semantic mismatch is critical. Minor cue and metadata corrections are separate. The other 29 accepts are **unlabeled**, never counted as safe. Each cohort record retains its originating batch, relation, confidence, production review flags, preference-risk and technical-risk flags, verifier concerns, source types where recorded, and its independent audit label. Only production fields enter routing. Source artifact SHA-256 digests freeze the cohort.

The fixed deterministic router audits false friends, low and very-low confidence cards, existing strong review flags, preference-evidence flags, and the existing technical-borrowing flag. Its 107/182 selections equal **58.8%** of all accepts, including 53 confirmed-good, 36 correctable, and 18 critical cards. The two known critical cases left in its otherwise-clean pool are `cal3-technology-001:technology-05` (flash drive) and `tb25-home-001:home-01` (socks). Both were found through random audit. The high Batch 2 deterministic load (36/40) reflects its historical confidence collapse; it is not a forecast of future tier distribution.

## Residual random-budget simulation

Each rate samples the otherwise-clean pool separately within each cohort, without replacement. Pure random is uniform. The stratified variant assigns half its slots uniformly to **all** clean cards, then weights the remaining slots 2× for `different-common-word` and 1.5× for medium confidence. This retains a genuinely random floor for apparently safe high-confidence cards. We used 4,096 reproducible seeds per rate and variant; no audit label influences selection.

| Residual sample | Total audits / 182 | Uniform mean critical caught / 20 | Uniform all-known-critical catch | Stratified mean / 20 | Stratified all-known-critical catch | Stratified ≥1 known critical missed | Stratified confirmed-good audited, mean |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5% | 113 (62.1%) | 18.151 | 0.5% | 18.154 | 0.4% | 99.6% | 55.9 |
| 10% | 116 (63.7%) | 18.214 | 1.2% | 18.222 | 1.4% | 98.6% | 57.0 |
| 15% | 120 (65.9%) | 18.370 | 3.4% | 18.391 | 3.6% | 96.4% | 58.4 |
| 20% | 124 (68.1%) | 18.411 | 4.2% | 18.457 | 5.2% | 94.8% | 60.3 |
| 25% | 128 (70.3%) | 18.555 | 8.0% | 18.607 | 9.1% | 90.9% | 61.6 |
| 30% | 132 (72.5%) | 18.635 | 10.3% | 18.666 | 11.0% | 89.0% | 63.5 |

The worst observed coverage at **every** rate and for both variants was 18/20. The simulated fraction missing at least one known critical case is one minus the all-caught fraction in the table. The confirmed-good column is the count audited across all cohorts, including deterministic selections; it measures work spent on known-good cards rather than calling those audits mistakes. Stratification gives only a small improvement at equal workload.

Pooled sampling as one large cohort slightly lowers rounding cost: at 20%, 122/182 (67.0%) audited, and stratified all-caught frequency 4.6% versus 5.2% when sampling separately by batch. Batchwise sampling is the operationally relevant estimate. At 20% stratified, the held-out cohort summaries are: Batch 1, 24/44 audited and no residual critical; Batch 2, 37/40 and no residual critical; final 50, 24/38 and flash-drive catch in 25.7% of seeds; prospective 50, 25/38 and no residual critical; technical 25, 14/22 and socks catch in 21.7%. A fixed router and fixed sampling weights were evaluated on each held-out batch; no rule was trained on the other four. This is a stability check, not blind predictive validation.

These frequencies describe selection of **known** historical critical cards only. The cohorts had nonrandom historical audit selection, 29 accepts lack labels, and future candidate distributions can differ. Do not interpret the numbers as future error probabilities or as measured corpus accuracy. The simulations also do not credit expanded audit after a safety brake; that could improve final catch at extra workload.

## Audit economics

Historical independent-audit artifacts record 153 audited cards, 36 model calls, 1,320.3 seconds of summed call time, 668,527 input tokens, and 63,217 output tokens. One call lacks token accounting, so 731,744 total tokens is a **lower bound**. These artifacts include different models, prompt sizes, and group sizes; summed call time is not necessarily wall-clock time when calls overlap. Monetary cost is unavailable.

Using historical per-card averages solely as a workload estimate:

| Policy per 100 provisional accepts | Deep audits | Model calls | Recorded tokens, lower-bound estimate | Summed model time estimate |
|---|---:|---:|---:|---:|
| 100% deep audit | 100 | 24 | ≥478,000 | ≈863 s |
| Fixed deterministic router only | 59 | 14 | ≥282,000 | ≈509 s |
| Router + 15% residual stratified sample | 66 | 16 | ≥316,000 | ≈570 s |
| Router + 20% residual stratified sample | 68 | 16 | ≥325,000 | ≈587 s |
| Router + 30% residual stratified sample | 73 | 17 | ≥349,000 | ≈630 s |

Rounding and batching make call counts approximate; model choice and prompt size can move actual tokens and elapsed time substantially. The 20% option saves about one-third of audit work versus full audit, but it is effectively the same 63–68% range already observed in recent batches. It does not establish the sought lower-load operating point, especially if safety brakes expand audit.

## Candidate operating rule and safety brakes

The simplest **candidate** rule, if a future run is authorized after the workload problem is addressed, is: audit every card selected by the frozen deterministic router; for the rest, sample 20% per batch without replacement, reserving half the sample slots for uniform random draws and using the stated relation/confidence weights for the other half. Record seed, candidate IDs, selection reason, and audit outcome. The seed must be fixed before audit labels are known. This is a reproducible fallback, **not an approved proof of adequate safety or a release authorization**.

For a future 100-candidate run, apply these batch-level brakes:

- If **any critical card appears in the random clean-pool sample**, stop automatic promotion and deep-audit all remaining provisional accepts. This is direct evidence that the fixed router missed a failure class.
- If two or more independently audited cards have material answer or semantic errors, or two show the same new learner-critical pattern, stop automatic promotion and expand audit to all remaining accepts.
- If combined production HOLD and REJECT exceed 30/100 generated, pause promotion and inspect the batch funnel. The observed fresh-batch range was 12–24%, so this signals a meaningful shift; metadata-only corrections do not trigger a brake.
- Apply approved cue/answer corrections, withhold audited unsafe cards, and preserve original decision and audit history. Unaudited cards can ship only under an **approved** operational policy with no triggered brake. They are never described as independently cleared.

The first two brakes favor safety but can raise workload to full audit. Their trigger frequency and added cost must be measured prospectively; this historical random-selection simulation does not model them.

## Separate promotion backlog

The current calibration did not use historical backlog as new production. A guarded promotion of 10 independently audited, confirmed-good, uncorrected backlog cards added 8 technical-25 and 2 prospective-50 cards, with archived candidate equality, learner-eligibility, duplicate, ID, and source validation checks. The learner source grew **127 → 137**; the promotion record is `curation/promotions/operational-audit-backlog.json`. Historical unaudited cards remain unpromoted, as do audited cards needing unresolved corrections or further review. Backlog work is excluded from production and audit-budget throughput metrics. Source validation reported 137 concepts; the offline build reported 137 notes and 137 cards. The full automated suite passed (201 tests), and Ruff passed on the new scripts and tests.

## Conditional protocol for one 100-candidate experiment

Do not start the experiment under this calibration task. Once an operational audit budget is approved, freeze the policy/router/prompt versions and record a seed before labels exist. Generate exactly 100 new diverse contrastive candidates, excluding canonical and historical concepts. Run v3.1 production without a new universal call. Record generation-to-decision wall time, generated/ACCEPT/HOLD/REJECT, relations, no-contrast and duplicate rejects, model calls/tokens, evidence calls/cache use, fast-path utilization, and provisional accepts/hour. Apply deterministic audit and the approved random/stratified sample to ACCEPTs; record why each was selected, deep-audit calls/tokens/wall time, critical errors, answer/cue/metadata corrections, and any brake. Correct and promote cleared cards only through guarded ID/GUID-preserving promotion. Report promoted, withheld, unaudited policy-cleared, final yield, and any new systematic failure class. Keep production, audit, and backlog timing separate. The 50× expert-human comparison remains unavailable until a real human benchmark exists.

## Readiness decision

**Not ready for the 100-candidate operational batch under the fixed router and tested budgets.** The quantitative obstacle is that deterministic routing already audits 58.8%; sampling 20–30% of the remainder raises total workload to 68–73%, yet still often misses the two known critical residuals in historical simulations. This is too close to full-audit economics for an autonomous-scale claim, while 29 unlabeled accepts make the measured safety picture incomplete. The specific remaining issue is **audit-routing workload with unpredictable clean-pool critical errors**, not a reason to change the core verifier or add another narrow detector. Preserve v3.1 and the random backstop; do not infer that simply increasing the random percentage solves both safety and cost.
