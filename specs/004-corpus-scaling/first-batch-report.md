# Feature 004 first operational batch

## Run identity and baseline

- Run ID: `corpus-004-001` (the only operational batch in this iteration).
- Starting learner corpus: **137** cards, verified against the fixed ID/GUID fixture.
- Frozen production policy: **3.1.0**; prompt set **2.4.0**.
- Starting `data/vocabulary.tsv` SHA256: `f7db434226d0e6e036b863026d3bf7a3572f01f75d1cb2e573692744bbfc67ef`.
- Starting `curation/id-ledger.json` SHA256: `e3afcb81b213a060a75030ec2c1f7305acb8a9aae2ffa7b97319de12456a1e89`.
- Permanent-ID and Anki GUID baseline: `tests/fixtures/corpus_scaling_baseline.json`.
- Requested admitted candidates: **100**; proposal cap: **200**.
- The gap-weighted 20-category draft was reviewed and accepted without edits. The approval rationale and frozen counts are in `curation/production-runs/corpus-004-001/manifest.json`.

## Pre-run validation

- `ruff check .`: passed.
- `pytest -q`: 246 tests passed at the pre-run gate.
- `myid-anki validate`: 137 valid concepts, no media.
- Baseline ID/GUID fixture matched all 137 canonical IDs.

## Final result

The only operational batch, `corpus-004-001`, is **complete**. It proposed 103 concepts, admitted exactly 100, and settled all 100 under frozen v3.1. The final decisions were **68 ACCEPT, 29 HOLD, 3 REJECT**. The 29 HOLD decisions include 25 cards withheld after independent audit findings. Guarded promotion assigned 68 new permanent IDs, taking the learner corpus from **137 to 205** cards. All 68 promoted cards remain active; none were withdrawn after promotion. The 200+ planning milestone was reached without an acceptance quota. No second batch was started.

The three screened generation proposals were distinct-sense proposals lost before the admission-rule fix; their saved records and the interruption are retained. One curated proposal was a confirmed duplicate, for a duplicate-generation rate of 1/103 (0.97%). No proposal or curated card was rejected as `same`/no-contrast, so observed no-contrast waste was 0/103. The early distinct-sense loss is a workflow defect and should not be counted as duplicate or no-contrast waste.

## Quality gates and safety brake

The original 93 accepted decisions included 60 risk-selected cards. Independent audit reviewed all 60: **35 cleared** and **25 needed correction** (17 learner-critical answer/contrast findings, 6 cue/content findings, 2 metadata-only findings). All 25 uncleared cards were withheld through closed decision reports. The final 68 ACCEPT cards comprise 35 risk-cleared and 33 with no risk-audit requirement; final current risk-audit pending count is zero.

Two learner-critical findings triggered the configured promotion brake. The run was paused, the scope was investigated, and audit resumed under the active brake. The repeated issue was overstatement of a `different-common-word` contrast when forms overlap across varieties. After all 25 uncleared cards were withheld, the brake was disposed with a recorded investigation; v3.1 policy was unchanged. Metadata-only findings did not themselves trigger a brake.

Random QA selected a deterministic stratified **7 of 68** clean promoted cards, after promotion. It recorded six `none` findings and one metadata-only finding about missing supporting evidence. It found no learner-facing answer or cue error in this sample. The sample is monitoring evidence and does not guarantee the other 61 cards are correct. All seven findings are recorded and resolved for batch closure; no post-promotion withdrawal was needed.

## Coverage change

The reviewed, frozen allocation assigned 100 candidate slots across all 20 categories. Promoted-card coverage changed as follows:

| Category | Before | After | Added |
| --- | ---: | ---: | ---: |
| Clothing | 5 | 8 | 3 |
| Common adjectives | 6 | 9 | 3 |
| Common verbs | 9 | 11 | 2 |
| Communication | 4 | 8 | 4 |
| Daily life | 3 | 6 | 3 |
| Directions/location | 1 | 6 | 5 |
| Education | 11 | 13 | 2 |
| Emotions | 1 | 4 | 3 |
| Family/social | 0 | 8 | 8 |
| Finance/administration | 3 | 7 | 4 |
| Food/cooking | 13 | 17 | 4 |
| Health/body | 5 | 9 | 4 |
| Home | 24 | 27 | 3 |
| Services | 3 | 6 | 3 |
| Shopping | 11 | 14 | 3 |
| Technology | 9 | 10 | 1 |
| Time/date | 1 | 8 | 7 |
| Transportation | 6 | 9 | 3 |
| Travel | 13 | 15 | 2 |
| Work | 9 | 10 | 1 |
| **Total** | **137** | **205** | **68** |

## Measured work and repeatability

| Stage | Model calls | Input / output tokens | Measured elapsed |
| --- | ---: | ---: | ---: |
| Generation | 23 | 737,542 / 14,873 | 3.66 min |
| Semantic review | 14 | 168,021 / 594 | 1.16 min |
| Production curation | 199 | 5,920,094 / 69,306 | 24.72 min |
| Risk audit | 60 | 3,188,055 / 65,362 | 20.09 min |
| Random QA | 7 | 87,627 / 2,031 | 0.86 min |
| **Total measured model work** | **303** | **10,101,339 / 152,166** | **50.49 min** |

Guarded promotion across 22 slices took 7.80 seconds and the offline build took 0.01 seconds. Retrieval counts were unavailable from the local model adapter. Production decision throughput was **242.7 decisions/hour** using measured production-call time as the denominator. The report's **6.28 active newly promoted cards/end-to-end hour** uses 68 cards over 10.83 hours from run creation to closure, including idle time between work sessions and investigation; it should not be read as model-processing speed. The active promoted yield was **68/100 admitted candidates (68%)**.

Generation retained two malformed first-slice response attempts and recovered a compatible saved response after the adapter repair. A planned interruption at 28 admitted candidates resumed in the same run without regenerating completed slices. The risk audit also resumed after a pause with prior reviews intact. Random QA stopped once on a raw-response/finding scanner defect, then resumed the same seven-card roster after a regression-tested fix. These incidents and the brake disposition are recorded in the parent events and final report.

The final source validates at 205 concepts, the offline package has 205 notes and 205 cards, all baseline IDs/GUIDs and deck/model IDs remain stable, and no export journal remains. The workflow completed one repeatable batch with substantial audit cost and a high correction-finding rate. Future candidate selection can use this batch's recorded overlap pattern; no Feature 003 policy change or second production run was made.
