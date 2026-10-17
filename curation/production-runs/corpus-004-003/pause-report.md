# Corpus production run `corpus-004-003` — paused report

**Status: PAUSED, not complete.** The run admitted exactly 500 candidates. It was paused after a learner-critical overlap failure recurred in a fresh independent audit following a QA correction and an earlier safety-brake disposition. The existing brake remains active. No further promotion or batch was started.

## Run and frozen plan

- Starting corpus: **270 cards**. Current canonical source: **539 cards** (269 active new cards).
- Run ID: `corpus-004-003`; Feature 003 production policy **3.1.0**, prompt set **2.4.0**; workflow `004.1`.
- One frozen allocation was used for all five operational checkpoints. Draft review shifted 25 slots from emotions (41 to 16) toward daily life, family/social, communication, common verbs, and common adjectives (+5 each), following seven unusable emotion proposals in Batch 2. The digest is `68844b8556cd1eb7bc4862e04a2f1da149e10c39fcd6a07ac08f1f49a7167a39`. Every frozen category quota was filled; no post-freeze reallocation occurred.
- The original 270 concept ID/GUID pairs remain stable. Active concept IDs and derived GUIDs are unique; all 273 IDs assigned by this run are unique and do not collide with earlier production batches. Deck/model IDs remain `1242123295` / `1942161817`.

| Category | Before | Frozen allocation | Admitted | Current coverage | Net growth |
| --- | ---: | ---: | ---: | ---: | ---: |
| clothing | 12 | 21 | 21 | 20 | +8 |
| common-adjectives | 13 | 36 | 36 | 27 | +14 |
| common-verbs | 14 | 38 | 38 | 24 | +10 |
| communication | 11 | 34 | 34 | 30 | +19 |
| daily-life | 10 | 35 | 35 | 32 | +22 |
| directions-location | 9 | 26 | 26 | 22 | +13 |
| education | 15 | 21 | 21 | 32 | +17 |
| emotions | 4 | 16 | 16 | 5 | +1 |
| family-social | 12 | 33 | 33 | 27 | +15 |
| finance-administration | 11 | 21 | 21 | 25 | +14 |
| food-cooking | 19 | 23 | 23 | 35 | +16 |
| health-body | 14 | 26 | 26 | 27 | +13 |
| home | 28 | 18 | 18 | 42 | +14 |
| services | 12 | 23 | 23 | 24 | +12 |
| shopping | 17 | 20 | 20 | 31 | +14 |
| technology | 13 | 20 | 20 | 24 | +11 |
| time-date | 11 | 26 | 26 | 26 | +15 |
| transportation | 13 | 22 | 22 | 30 | +17 |
| travel | 18 | 19 | 19 | 30 | +12 |
| work | 14 | 22 | 22 | 26 | +12 |

## Generation and production decisions

- Proposals generated: **507**; admitted: **500 exactly** (1.014 proposals per admitted candidate).
- Pre-admission screening rejected **7 semantic redundancies**. Exact duplicates: **0**; historical duplicates: **0**; other screening rejections: **0**.
- Production decisions before independent audit: **364 ACCEPT, 75 HOLD, 61 REJECT**.
- Final current decisions after audit dispositions and the post-correction finding: **272 ACCEPT, 167 HOLD, 61 REJECT**. The final HOLD rate is **33.4%**, above the unchanged 30% safety-brake threshold.
- Rejection detail: **31 no-meaningful-contrast**, **27 artificial-synonym**, **3 confirmed duplicate**. No-contrast count is 31 (6.1% of 507 proposals). Semantic redundancy plus confirmed duplicates total 10 (2.0% of proposals).
- Current accepted relation distribution: **221 different-common-word, 51 similar**. Confidence: **95 high, 123 medium, 54 low**. False-friend accepted: 0.

## Risk audit and safety-brake investigation

- The frozen initial risk roster selected **221** candidates. All 221 were individually reviewed: **130 initially cleared; 91 required correction or withholding**. No risk-audit finding was approved for direct correction; those 91 were individually set to HOLD.
- QA corrections triggered a fresh independent audit. A corrected newspaper card that had earlier cleared was again found learner-critical because its regional relation overstated overlap. It is now HOLD and withdrawn. The report contains **222 audit records** after that follow-up review; findings total **67 learner-critical, 13 cue-content, 12 metadata-only**. Current risk-selected ACCEPT candidates: **129 required, 129 current-clearance, zero pending**. In total **92 affected candidates are held** across the initial findings and follow-up.
- The first `two-learner-critical-errors` brake was disposed after the full 221-review investigation and withholding all 91 findings. The new overlap finding after that disposition activated the same brake again. The follow-up evidence and the prior archived clearance are in `brake-investigation-followup.json`; the initial full investigation is in `brake-investigation.json`.
- `high-hold-rate` also remains active (the rate first crossed 30% at 166 HOLD candidates). The two currently active brakes are recorded in the manifest. The batch state is `paused`.
- The repeated pattern is an overstated national word split when forms overlap across Indonesian and Malaysian Malay or when accepted alternatives are common. Other audit findings concern answer sense, specificity, cue scope, and unsupported false-friend labels. Policy v3.1 and audit thresholds were not changed.

## Guarded promotion and random QA

- **273** cards were initially eligible and promoted. QA later withdrew **4** material-finding cards; the fresh risk finding is among those already withdrawn. Three corrected cards remain withdrawn and one is held. Current run cards active in source: **269**; ever assigned: 273; withdrawn: 4. Final corpus size is **539**.
- Normal random QA selected **28 of 273** eligible promoted cards using `stratified-10-percent-min5-v1`; all 28 reviews completed. Results: **22 clean, 2 metadata-only, 4 cue-content, 0 learner-critical**. All four cue/content candidates were withdrawn. Narrow corrections were applied to four proposals (three cue clarifications and one Indonesian answer correction), but their QA findings have not been re-cleared or the cards re-promoted. Twenty-four QA records are resolved; four material QA records remain unresolved while withdrawn. No repeated learner-critical QA pattern was found; `missing-cue` occurred three times.
- Random QA is monitoring, not a promotion gate. Here it uncovered findings and triggered the configured high-HOLD brake.

## Operational checkpoints

These are five observations of the same batch, not separate runs. Counts reflect the current candidate decisions in each prefix; model cost is cumulative for each prefix.

| Admitted so far | ACCEPT / HOLD / REJECT | Risk audits reviewed | Active promoted | QA reviewed | Model calls | Input / output tokens | Measured model time |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 107 | 41 / 40 / 26 | 48 | 40 | 2 | 289 | 15,194,413 / 153,145 | 39.1 min |
| 202 | 99 / 70 / 33 | 84 | 97 | 10 | 572 | 28,550,467 / 285,187 | 73.2 min |
| 304 | 151 / 112 / 41 | 135 | 149 | 13 | 887 | 43,539,934 / 441,170 | 114.3 min |
| 402 | 209 / 139 / 54 | 177 | 206 | 19 | 1196 | 57,823,414 / 580,684 | 152.8 min |
| 500 | 272 / 167 / 61 | 222 | 269 | 28 | 1519 | 72,390,851 / 719,667 | 192.6 min |

## Resumability and cost

- Generation had one non-JSON provider failure and resumed in the same run.
- Production curation had **12 command failures/resumes**: four provider errors, seven malformed verifier captures, and one stale capture encountered after a QA correction. The seven malformed responses were preserved and their usage is included below. Seven other stale captures were archived before fresh recuration; their original calls were already counted and are not double-counted.
- Risk audit was interrupted once after the brake activated and four audits were complete, then resumed using persistent candidate records. One in-flight call has unavailable usage. QA completed without interruption. Details and event references are in `resume-incidents.json`.

| Stage | Actual model attempts | Input tokens | Output tokens | Measured model-call time |
| --- | ---: | ---: | ---: | ---: |
| Generation | 53 | 2,951,354 | 59,007 | 9.60 min |
| Semantic/redundancy | 198 | 2,367,772 | 8,250 | 11.23 min |
| Production curation | 1016 | 54,517,752 | 394,182 | 101.99 min |
| Risk audit | 224 | 12,149,559 | 248,974 | 66.51 min |
| Random QA | 28 | 404,414 | 9,254 | 3.27 min |
| **Total** | **1519** | **72,390,851** | **719,667** | **192.61 min** |

- Per initially promoted card (273): **5.56 calls**, **267,804 input+output tokens**, **42.33 seconds** measured model time. Against 269 currently active cards, that is 5.65 calls, 271,786 tokens, and 42.96 seconds per active promoted card.
- Six failed attempts have unavailable usage: one generation, four provider curation failures, and one interrupted risk-audit call. Model time excludes idle wall time; retrieval counts are unavailable from the local adapter. Promotion took 95.16 seconds and build took 0.019 seconds; neither makes model calls.

## Comparison with previous operational batches

| Measure | Batch 1 | Batch 2 | This run at pause |
| --- | ---: | ---: | ---: |
| Admitted | 100 | 100 | 500 |
| Initially promoted | 68 | 65 | 273 (54.6%) |
| Currently active from run | 68 | 65 | 269 (53.8%) |
| Final HOLD / REJECT | 29 / 3 | 26 / 9 | 167 / 61 |
| Initial risk audits / admitted | 60 / 100 | 49 / 100 | 221 / 500 |
| Initial audit findings | 25 | 12 | 91, plus one repeated critical finding after correction |
| Learner-critical audit findings | 17 | 9 | 67 recorded after follow-up |
| Random QA | 7; 1 metadata | 7; 0 findings | 28; 4 cue, 2 metadata |
| Duplicate / no-contrast waste | 1 / 0 | 2 / 2 | 10 duplicates / 31 no-contrast |
| Model attempts | 303 | 303 | 1,519 |
| Calls per initially promoted card | 4.46 | 4.66 | 5.56 |
| Input+output tokens per initially promoted card | 150,787 | 163,887 | 267,804 |
| Measured time per initially promoted card | 44.55 sec | 45.92 sec | 42.33 sec |
| Coverage categories that grew | 20 / 20 | 19 / 20 | 20 / 20 |

The initial promotion yield fell by 10.4 percentage points versus Batch 2. The increase in HOLD/REJECT and audit findings is driven by this run's observed content and the unchanged audit workflow; it is recorded as a safety event, not treated as normal large-sample variation. Call rate per admitted candidate (3.04) is close to Batch 2 (3.03); input tokens per promoted card are higher. No production policy change is proposed here.

## Validation and stop state

- Source validation completed: **539 concepts**, no validation errors.
- The 270 starting ID/GUID pairs are preserved; active IDs and GUIDs are unique; all 273 run assignments are unique and have no collision with earlier production batches. Deck/model IDs remain stable.
- The last successful `.apkg` build contains **543 cards** and is stale after four QA withdrawals. A final build, automated test suite, and Ruff checks were not run after the safety-brake recurrence.
- Current status is **PAUSED / INCOMPLETE**. Random QA completed, but four material QA findings remain unresolved, two safety brakes are active, and the package is stale. The exact 500-candidate admission target was reached, but the operational run did not complete its final build, tests, lint, and closure gates.
- No additional production batch was started. Resume only through the existing run’s investigation and safety-brake procedures; do not create a new run to bypass the pause.


## Recovery investigation update — 2026-10-17

Fresh one-at-a-time independent review of the bounded 110-candidate `shared-synonym-preference` roster completed. It produced 87 material findings and 23 cleared results. All 87 materially flagged candidates are now held; 86 active rows were withdrawn and one candidate was already inactive. Thirty-one responses labeled metadata-only had material learner-risk claims and were treated as material. Three of four material QA findings were resolved after corrections; the held newspaper candidate (ID 000315) remains unresolved.

Final candidate outcomes are 185 ACCEPT / 254 HOLD / 61 REJECT. The high-HOLD brake was investigated independently and disposed; its updated rationale is in the manifest. The learner-critical brake remains active. Working canonical source is 453 cards, including 183 active cards from this run. The `.apkg` at 543 cards is stale. The run remains PAUSED; no promotion, final validation, build, tests, Ruff checks, or closure were performed. See [recovery-investigation-report.md](recovery-investigation-report.md) and [overlap-investigation.json](overlap-investigation.json).


## Recovery completion update — 2026-10-17

This pause report records the earlier incomplete state. The run has since completed using the same batch manifest. See [recovery-completion.md](recovery-completion.md) for final candidate decisions, QA dispositions, source/build counts, validation, and brake state; [`report.json`](report.json) is the final machine-readable report.
