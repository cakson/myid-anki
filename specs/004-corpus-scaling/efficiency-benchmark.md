# Feature 004 fixed-batch efficiency benchmark

Date: 2026-10-16. Benchmark: completed `corpus-004-001`, policy 3.1.0, 100 admitted candidates, 68 promoted cards. This experiment used saved generation and candidate artifacts. It did not generate concepts, run promotion/export, or change the 205-card source.

## Baseline call and token profile

The report's measured total is **303 model calls, 10,101,339 input tokens, 152,166 output tokens**. Values below include the one counted generation retry and one counted random-QA retry. Mean and median are input tokens per call; output totals are shown separately. Captures and the batch report agree exactly on stage totals.

| Stage | Calls / concepts | Input / output tokens | Mean / median input per call | Mean / median output per call | Input per concept | Model time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Generation | 23 / 103 proposals | 737,542 / 14,873 | 32,067 / 32,712 | 647 / 627 | 7,161/proposal | 3.66 min |
| Semantic admission review | 14 / 14 | 168,021 / 594 | 12,002 / 11,939 | 42 / 39 | 12,002 | 1.16 min |
| Normalize and dedupe | 100 / 100 | 4,502,562 / 14,215 | 45,026 / 45,008 | 142 / 112.5 | 45,026 | 10.16 min |
| Independent production verification | 99 / 99 | 1,417,532 / 55,091 | 14,319 / 14,301 | 556 / 570 | 14,319 | 14.57 min |
| Independent risk audit | 60 / 60 | 3,188,055 / 65,362 | 53,134 / 49,921 | 1,089 / 1,068 | 53,134 | 20.09 min |
| Random QA monitoring | 7 / 7 | 87,627 / 2,031 | 12,518 / 12,407 | 290 / 292 | 12,518 | 0.86 min |

Production curation's **199 calls and 24.72 model-call minutes** are 100 overlap reviews plus 99 verifier reviews. One candidate was rejected after overlap review, so no verifier call followed. The two reviews serve different v3.1 decisions; the verifier already returns relation, cue alignment, shared-synonym assessment, confidence inputs, and review metadata in one response. There is no extra per-candidate interpretation or confidence call to merge. Risk audit separately used **20.09 model-call minutes**. No production or risk-audit response needed a recorded retry. The counted generation and QA retries were recovered from durable captures.

The 60 saved risk audits included 25 `needs-correction` verdicts, with 17 learner-critical answer findings. Their clearance is a substantive gate, so its cost must be evaluated separately from production decision throughput.

Normalization dominates production input. Its average packet is 106,154 bytes, of which the frozen archive is 104,446 bytes across 564 historical entries; the candidate is about 215 bytes. Generation also reuses a prior-concept inventory, averaging 514 entries and 60,237 bytes per call. Semantic admission review passes one new/prior concept pair, without that full inventory. The ordinary verifier packet is about 5,994 bytes, including 5,191 bytes of frozen prompt text that the caller also puts before the JSON packet. The verifier's candidate is about 216 bytes; it receives no full archive or raw evidence payload. The independent audit packet averages 3,010 bytes, including 1,845 bytes of production decision metadata, a candidate, and projected learner content. It receives no raw evidence collection. Random QA's packet averages 2,330 bytes, including 1,848 bytes of decision metadata; it also carries no archive or raw evidence. The audit's measured 53k input tokens per call are much larger than its visible packet; the saved adapter only records aggregate Codex CLI usage, so the remainder cannot be attributed more precisely from these artifacts. Retrieval counts were unavailable.

The archive cannot be replaced by the existing cheap shortlist without losing semantic comparisons. A 20-item shortlist found only **3 of 54** saved overlap pairs; related concepts such as *kindergarten/school* and *arrive/arrival* often have no shared cue token or identical answer pair. The minimum safe overlap context under the current v3.1 route remains a semantically complete comparison inventory. Static prompt duplication is smaller than that archive. Provenance and history remain complete on disk even when a replay prompt is shorter.

## Bounded replay experiments

Size one is the saved original response. Group trials used the same first ten historical candidates for production verification and the same first ten historical risk-selected cards for audit; they made no new candidate proposals. The full 100-candidate normalization replay used all saved candidate/archive snapshots. Every replay response was saved separately under `curation/efficiency-replays/corpus-004-001-v1/captures/`; comparison never ingested a response into the historical batch.

| Trial | Cards / calls | Input tokens | Measured model time | Outcome against saved benchmark |
| --- | ---: | ---: | ---: | --- |
| Normalization, original | 100 / 100 | 4,502,562 | 10.16 min | Reference |
| Normalization, compact archive columns | 100 / 100 | 3,073,520 (−31.7%) | 10.57 min (+4.0%) | 99/100 same disposition; one rejected duplicate became pending |
| Verifier, original sample | 10 / 10 | 142,975 | 88.5 s | Reference |
| Verifier, groups of 5 | 10 / 2 | 27,162 (−81.0%) | 42.0 s | Three candidates changed disposition or resolved cue |
| Verifier, group of 10 | 10 / 1 | 14,260 (−90.0%) | 33.5 s | Two candidates changed disposition or resolved cue |
| Risk audit, original sample | 10 / 10 | 507,515 | 205.8 s | Reference; four learner-critical findings, one metadata finding |
| Risk audit, pairs | 10 / 5 | 224,171 (−55.8%) | 112.1 s | Three critical findings cleared; one downgraded; metadata finding missed |
| Risk audit, groups of 5 | 10 / 2 | 29,363 (−94.2%) | 29.9 s | All four critical findings and the metadata finding missed |

All 100 compact normalization responses and all group responses passed their respective JSON schema and candidate-ID checks; there were no model request/retry failures in the replay. Reliability failed at the decision level. The full normalization replay changed 41 overlap lists, mostly extra or omitted `distinct` comparisons. Forty of those changes were equivalent for the v3.1 gate; one removed a blocking merge. A compact prompt reduced input tokens but increased normalization output tokens from 14,215 to 17,964 and did not reduce measured model-call time.

### Candidate-level decision differences

All listed changes are **quality regressions relative to the fixed benchmark** for adoption purposes. This classification is about preserving the completed batch's decisions; it does not assert that the saved linguistic judgment is infallible. No corrected defect was confirmed. No final relation changed in these replays.

| Trial | Candidate | Saved outcome / cue | Replay outcome / cue |
| --- | --- | --- | --- |
| Compact normalization | `tmp-common-verbs-s003-003` | REJECT `arrive` as redundant with `arrival` | pending after both archive overlaps became `distinct` |
| Verifier 5 and 10 | `clothing-contrast-001` | ACCEPT, cue `necktie` | ACCEPT, cue `tie` |
| Verifier 5 and 10 | `clothing-contrast-004` | REJECT `underwear` | HOLD `underwear` |
| Verifier 5 | `common-adjectives-contrast-006` | HOLD `crowded` | ACCEPT, cue `crowded with people` |

The candidate-level risk-audit differences are below. `needs-correction` remains a withheld disposition; `cleared` would permit promotion if every other gate passed. Grouped auditing therefore cannot be substituted for the saved individual audits.

| Candidate | Saved finding | Pair replay | Five-card replay |
| --- | --- | --- | --- |
| `common-adjectives-contrast-004` | learner-critical, needs correction | cleared | cleared |
| `common-adjectives-contrast-005` | learner-critical, needs correction | metadata-only, needs correction | cleared |
| `tmp-common-verbs-s003-002` | learner-critical, needs correction | cleared | cleared |
| `tmp-common-verbs-s003-004` | metadata-only, needs correction | cleared | cleared |
| `tmp-common-verbs-s003-006` | learner-critical, needs correction | cleared | cleared |

The remaining tested candidate-level dispositions, relations, resolved cues, and audit clearances agreed with the saved reference. The full stage-level comparison is in `comparison.json`. Because bounded batching already missed critical errors, no full 99-card verifier or 60-card audit batch replay was run; the table reports measured sample savings, not a projected adoption.

## Adoption and operational conclusion

**No model-context or batching optimization was adopted.** Quality-adjusted savings for the deployed workflow are therefore **0%**: the measured baseline remains 303 calls and 10,101,339 input tokens. The production route, v3.1 prompt/policy, risk selection, individual independent audit, random-QA monitoring role, guarded promotion, and export remain unchanged.

The compact normalization experiment would have reduced hypothetical total batch input from 10,101,339 to 8,672,297 tokens (−14.1%) with the same 303 calls. It would have increased total output from 152,166 to 155,915 (+2.5%) and summed model-call time from 50.49 to 50.90 minutes (+0.8%). The 68 promoted-card denominator gives 148,549 baseline input tokens per promoted card versus 127,534 hypothetical; **no replay card was promoted**. Its duplicate-control regression makes those savings ineligible. Grouped verifier and audit calls offered larger sample savings but unacceptable decision and audit sensitivity changes. Removing only duplicated static prose would offer a small fraction of total batch cost and was not pursued as a complex new transport path.

The historical batch remains a durable, candidate-level benchmark. The replay runner checks fixed SHA-256 digests for the source, ID ledger, and historical report before reading, requires frozen archive snapshots, writes only to its separate replay directory, and refuses stale candidate identities or prompt sizes/digests. A completed full-normalization replay was resumed a second time: all 110 saved trial captures stayed byte-identical and no model request was made. The hypothetical grouped-call recovery design was not integrated because both group sizes failed the quality criterion. Current production resumability and guarded-export semantics remain intact.

Validation: **270 tests passed**; Ruff lint and formatting passed; source validation found **205 concepts**; package build produced **205 notes and 205 cards**. The canonical source, ID ledger, and historical report retained their pre-experiment SHA-256 digests. The existing identity test checked stable deck/model IDs and Anki GUIDs for the 205-card source. No vocabulary batch, export, promotion, or second operational run occurred.

Feature 004 is operationally capable of a second batch, but this experiment did **not** make its model cost cheaper. A second run should be budgeted against the measured first-batch level, about 303 calls and 10.1 million input tokens per 100 admitted candidates, until a separately validated optimization preserves duplicate judgments and audit sensitivity. Do not start Batch 2 automatically.
