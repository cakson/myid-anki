# Feature 003 cheap post-production audit-screen benchmark

Date: 2026-10-15. **Decision: do not deploy the cheap screen or schedule a prospective 50-candidate test.** Production v3.1, the core verifier, and the deterministic audit router remain unchanged. No vocabulary was generated or promoted in this phase; the canonical learner source remains at 137 cards.

## Fixed experiment

The benchmark uses all **153 independently audited** fresh-batch production ACCEPTs in `cheap-audit-screen-inputs.json`, with batch origin and labels sealed separately in `cheap-audit-screen-labels.json`. There are 20 known critical, 48 correctable, and 85 confirmed-good cases. The frozen contract is `cheap-audit-screen-contract.md`. The model received only reference ID, English cue, Indonesian answer, Malaysian Malay answer, intended sense, and production relation. It received no audit outcome, post-audit correction, retrospective diagnosis, or promotion status. The result is only `screen-clear` or `screen-review` with compact reason codes; it never changes ACCEPT/HOLD/REJECT.

The screen used Luna at low reasoning effort, no tools, no external lookup, and no historical evidence packet. Batches of 5, 10, and 20 covered the **same 153 cards** under the **same frozen prompt**. The contract was fixed before running any size or comparing labels. Later cohorts are therefore unchanged-prompt held-out checks, although this historical audited corpus is not a prospective blinded population sample. Results and usage are checkpointed in `cheap-audit-screen-{5,10,20}-results.json`; `cheap-audit-screen-evaluation.json` contains reproducible architecture simulations (4,096 fixed seeds per condition).

## Batch-size quality and cost

| Cards/call | Calls | Summed model-call seconds | Input tokens | Output tokens | Tokens/card | Critical review / 20 | Confirmed-good review / 85 | Correctable review / 48 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 31 | 232.1 | 361,805 | 8,563 | 2,421 | 6 | 6 | 6 |
| 10 | 17 | 140.5 | 202,272 | 7,429 | 1,371 | 5 | 3 | 10 |
| 20 | 8 | 83.7 | 100,140 | 6,406 | 696 | 6 | 7 | 7 |

One 10-card response used an invalid reason code; the unchanged group was retried successfully. Its failed call is included in the call, time, and token totals. No usage field was missing. Summed model-call time is not parallel wall time. Size 20 is clearly cheapest and did not reduce **pooled** critical detection relative to size 5, but pooled detection remains weak. The deep-audit historical average was at least 4,783 recorded tokens per audited card, so the 20-card screen is about 6.9× cheaper per card on tokens. It only pays for universal deployment if it eliminates enough deep audits.

| Originating cohort | Critical total | Size 5 review | Size 10 review | Size 20 review |
|---|---:|---:|---:|---:|
| Fresh Batch 1 | 3 | 1 | 1 | 2 |
| Fresh Batch 2 | 6 | 0 | 1 | 0 |
| Final 50 | 3 | 2 | 1 | 2 |
| Prospective preference 50 | 3 | 1 | 1 | 1 |
| Technical borrowing 25 (newest) | 5 | 2 | 1 | 1 |

The newest-cohort result, **1/5 critical reviewed** at the cheapest size, fails the requirement that screen quality hold up on later batches. A larger 20-card group did not cause a simple monotonic quality decline; all three sizes missed most critical cards. This is one stochastic pass per size, so small differences among sizes should not be treated as precise model-quality estimates.

## Critical cases missed by the existing router

| Candidate | Frozen router | Size 5 | Size 10 | Size 20 | Independent audit |
|---|---|---|---|---|---|
| `cal3-technology-001:technology-05` (flash drive) | clear | review: everyday usage, hidden alternative | review: hidden alternative | review: everyday usage | critical |
| `tb25-home-001:home-01` (socks) | clear | review: answer naturalness, semantic precision | review: semantic precision | review: semantic precision, hidden alternative | critical |

This is genuinely additional historical coverage. It is also narrow: the screen cleared **14/20** known critical cards at sizes 5 and 20, and 15/20 at size 10. The frozen router independently selects 18/20. Seeing both residual examples after the fact is encouraging, but two examples cannot establish future residual-risk recall.

## Architecture comparison

The simulation uses the 153 **labeled** accepts only. All 107 cards selected by the frozen deterministic router happen to be labeled; the 29 ACCEPTs without independent audit were in its clean pool and are excluded from the following denominator. Thus the router is 107/153 (70%) here, versus **107/182 (59%)** in the full production ACCEPT set. The labeled-set workload is selection-biased and must not be projected directly to a new batch.

The table uses the cheapest 20-card screen and 10% uniform random deep audit of each cohort's otherwise-clean pool. Random selection is repeated over 4,096 fixed seeds. The screen-only results are much weaker than router results; the union catches all 20 **known historical** critical cases because it adds both residual cases, but does not establish future perfect recall.

| Architecture | Deterministic deep audits / 153 | Total deep audits / 153 | Mean known critical caught / 20 | Known critical caught before random | Mean confirmed-good deep-audited | Universal screen tokens |
|---|---:|---:|---:|---:|---:|---:|
| A: frozen router + random | 107 | 114 (74.5%) | 18.47 | 18 | 57.9 | 0 |
| B: screen-review + random | 20 | 36 (23.5%) | 7.72 | 6 | 16.4 | 106,546 |
| C: router OR screen-review + random | 109 | 116 (75.8%) | 20.00 | 20 | 58.3 | 106,546 |

Architecture A caught all known critical cases in 4.5% of these labeled-cohort random simulations. Architecture B never caught all 20 at this budget because 14 critical cards were screen-clear. Architecture C caught all known critical cases in every simulation because its deterministic union included the two known router residuals. At a 5% random floor, C still deep-audited 115/153; at 20%, 121/153. It does not make deep audit selective.

Using ≥4,783 historical recorded deep-audit tokens/card as a rough workload estimate, A at 10% costs about **545k** deep-audit tokens on this cohort. B costs about **172k deep + 107k screen = 279k**, but leaves most known critical cases outside targeted audit. C costs about **555k deep + 107k screen = 662k**, roughly **117k more tokens than A**. Using historical summed audit time of 8.63 seconds/card, A is roughly 984 summed model seconds; B is about 311 deep + 84 screen seconds; C is about 1,001 deep + 84 screen seconds. These are estimates from mixed historical audit models and prompts, not monetary costs or future elapsed-time guarantees. They exclude any expanded audit after a safety brake, which would increase work.

## Recommendation

**The cheap screen does not merit a prospective operational test.** Batch size 20 makes screening cheap, and it identified both known router residuals. Yet screen-first auditing would clear most known unsafe cards; combining screen with the router raises cost and leaves deep-audit coverage near the already expensive baseline. Performance on the newest cohort is particularly weak. Keep the current v3.1 production and independent-audit process with a genuinely random backstop. Do not add another screen or case-specific detector based on these results. Under the present models and evidence, maintaining the desired quality still requires substantial independent deep audit, or a separate future change with stronger prospective evidence.
