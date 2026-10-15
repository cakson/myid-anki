# Fixed verifier-contract benchmark

## Decision

**Keep production policy v3.1 and its current Luna verifier for now; retain risk-based and random independent auditing.** The revised Luna contract found many historical errors cheaply, but it missed four of five critical cards in the newest batch, including **socks → kaus kaki / stoking**. Sol was slower and did not produce a better overall quality/audit tradeoff. This is the third decision category in the experiment: neither variant is sufficiently reliable to replace the current production-plus-audit safety system. It does **not** mean the revised Luna prompt showed no signal; it means its gains did not transfer consistently enough to justify a production switch on this evidence. No model or policy configuration changed.

## Fixed data and leakage control

The [benchmark inputs](verifier-contract-benchmark-inputs.json) contain exactly **48** original production-time candidate records: all **20** known independent-audit `materially-misleading`, `should-hold`, or `should-reject` production ACCEPTs with preserved inputs; **20** confirmed-good controls (four per source batch, including four `similar` cards); and **eight** minor-correction controls. Three different-word good controls per batch were selected by relation, category-tag overlap, and deterministic tie break. The set spans five fresh batches, technical and ordinary vocabulary, and preference-sensitive and straightforward contrasts. It is intentionally enriched with unsafe cards, so its critical-card prevalence cannot estimate production prevalence.

The [audit labels](verifier-contract-benchmark-labels.json) are a separate file. The model runner reads only the inputs and [fixed experimental contract](verifier-contract-experiment.md); its prompt builder strips batch names, archived verifier outputs, review flags, audit verdicts, reasons, and corrections. Both revised variants received byte-identical prompts per six-card group and the same structured-output schema. Structured output was validated before storage. The original independent audits are the evaluation reference, not an infallible linguistic gold standard. The user-specified contract was written after the broad failure classes were known, so the batch-separated results below are descriptive validation rather than a blind prospective test.

Variants:

- **A:** archived actual v3.1 Luna production decisions and verifier outputs. All 48 benchmark cards were ordinary production ACCEPTs; no fresh A calls were made.
- **B:** explicit semantic alignment, answer precision, everyday-choice, and concrete-objection contract on Luna medium.
- **C:** the exact B inputs and contract on Sol medium.

The [raw variant outputs](verifier-contract-benchmark-results.json) and [machine-readable evaluation](verifier-contract-benchmark-evaluation.json) preserve every candidate-level action and available call metric. No vocabulary was generated or promoted.

## Independent-audit comparison

| Measure, 48-card enriched set | A: archived v3.1 Luna | B: revised Luna | C: revised Sol |
|---|---:|---:|---:|
| Ordinary ACCEPT | 48 | 32 | 28 |
| ACCEPT_WITH_REVIEW | 0 | 15 | 11 |
| HOLD / REJECT | 0 / 0 | 1 / 0 | 6 / 3 |
| Known critical cards ordinary-ACCEPTed | **20/20** | **6/20** | **8/20** |
| Known critical cards routed to review | 0 | 13 | 6 |
| Known critical cards held or rejected | 0 | 1 | 6 |
| Confirmed-good cards unnecessarily escalated | 0/20 | 2/20 | 3/20 |
| Confirmed-good cards wrongly held/rejected | 0 | 0 | 1 |
| Minor-correction cards challenged | 0/8 | 0/8 | 5/8 |

`ACCEPT_WITH_REVIEW` is a safe escalation only if the downstream audit actually occurs before release. B's 14/20 critical challenges are useful, with two confirmed-good false review routes. C converted more cases to direct HOLD/REJECT, but still left more critical cards as ordinary ACCEPT and wrongly blocked one audited-good technical card. Neither model found every learner-answer problem.

### Batch-separated behavior

| Source batch | Known critical | B ordinary critical ACCEPTs | C ordinary critical ACCEPTs | B confirmed-good escalations | C confirmed-good escalations |
|---|---:|---:|---:|---:|---:|
| Fresh 1 | 3 | 1 | 1 | 0 | 0 |
| Fresh 2 | 6 | 0 | 4 | 1 | 1 |
| Fresh 3 | 3 | 0 | 0 | 1 | 1 |
| Fresh 4 | 3 | 1 | 1 | 0 | 0 |
| Latest technical 25 | 5 | **4** | **2** | 0 | 1 |

B challenged 13/15 critical cards in the first four batches but only 1/5 in the newest cohort. This is the decisive transfer failure. C challenged 3/5 in the newest cohort but performed worse on Fresh 2 and overall. The latest cohort contains confirmed-good controls, so this is not solely a negative-only holdout, although the benchmark and contract were informed by previously observed failure classes.

The latest critical misses under **both** B and C include **socks** and **job training**. Both models called *stoking* a natural ordinary Malaysian answer for socks, despite the independent audit finding it materially misleading against *stokin* and potentially suggestive of stockings. Both considered *latihan kerja* a straightforward everyday job-training contrast, while the independent audit held the preference/sense claim unresolved. B also ordinary-ACCEPTed **pajamas** and **bandage**; C routed both to review. Earlier shared misses include **measuring cup**. These are generalized semantic and everyday-choice judgment failures, not evidence that a new clothing or technology flag should be added.

## Audit-routing simulation

The simulation routes every `ACCEPT_WITH_REVIEW` card to independent audit, with a fixed-hash random sample of remaining ordinary ACCEPTs. HOLD/REJECT cases are caught directly and do not consume post-accept audit slots. Random sampling remains necessary because both revised models miss socks.

| Variant | Random fraction among ordinary ACCEPTs | Deep audits / 48 | Known critical caught by gate or audit / 20 | Confirmed-good audited |
|---|---:|---:|---:|---:|
| B Luna | 0% | 15 (31.3%) | 14 | 2 |
| B Luna | 10% | 19 (39.6%) | 15 | 3 |
| B Luna | 15% | 20 (41.7%) | 15 | 4 |
| C Sol | 0% | 11 (22.9%) | 12 | 2 |
| C Sol | 10% | 14 (29.2%) | 12 | 5 |
| C Sol | 15% | 16 (33.3%) | 12 | 7 |

These audit fractions are **benchmark workloads**, not projected population workloads: 20/48 selected cards are known critical failures. They cannot be compared as an unbiased operational estimate against the previous 63–68% deep-audit coverage. The same fixed hash ranks otherwise ordinary ACCEPTs across variants. Even at 15% random sampling, B misses five known critical cards and C misses eight in this draw. Raising sampling alone within this small enriched set does not establish a safe release rate. A production audit budget must be calibrated on future routine batches and quality outcomes, with random and stratified coverage maintained.

## Model and time cost

| Cost on 48 fixed cards | B Luna | C Sol |
|---|---:|---:|
| Calls / failed calls | 8 / 0 | 8 / 0 |
| Model-call elapsed time | 97.3 s | 167.4 s |
| Input tokens | 97,432 | 109,568 |
| Output tokens | 7,457 | 6,990 |
| Total tokens per candidate | 2,185 | 2,428 |

Sol took **1.72×** Luna's model-call time and used about **11%** more total tokens. The project does not have CLI billing or a reliable model-price table configured, so monetary cost is unavailable. A incurred **zero new benchmark calls**; four archived v3.1 cohorts with role-tagged verifier attempts recorded 45 verifier calls over 175 generated candidates, 701.4 seconds, at least 543,985 input and 70,945 output tokens (one call has unavailable token usage). Those group calls also covered unselected cards; the first fresh batch lacks role-tagged verifier attempts. Thus A's exact cost for these 48 selected cards cannot be recovered or compared directly with B/C's matched live calls.

Selective Sol use after Luna marks `ACCEPT_WITH_REVIEW` is not justified by this benchmark: those cards already enter audit, while the remaining Luna ordinary ACCEPTs include socks and other critical misses. A Sol pass over ordinary Luna ACCEPTs would add material cost and still missed socks, job training, and measuring cup in the matched outputs.

## Next operational step

Stop the verifier-prompt and narrow-heuristic cycle. Keep v3.1 as production baseline and require the independent risk-plus-random audit before guarded promotion. The next measurement should set a concrete routine random/stratified audit budget from ordinary batch outcomes, track critical escapes and correction cost, and avoid treating this enriched benchmark's audit percentage as a production estimate. The current 127-card canonical deck is unchanged; no 100-card run was started.

Validation: 199 project tests passed; Ruff passed on the new benchmark code; offline source validation found 127 concepts. The experimental prompt, benchmark inputs, labels, outputs, and evaluation remain versioned and inspectable under Feature 003.
