# Feature 004 second operational batch

## Starting state and frozen plan

- Run ID: `corpus-004-002`; exactly one new 100-admitted-candidate run, proposal cap 200.
- Starting canonical corpus: **205** cards. All 205 ID/GUID pairs were snapshotted in `curation/production-runs/corpus-004-002/baseline-identity.json` before generation.
- Starting source SHA-256: `6de5367ccecb4178db89d59f0577286d1b95893dcdcc4e27c49c91d115512f5d`.
- Starting ID-ledger SHA-256: `318f7694a5c7e670547b8d5c71c3fa16b19d9e99d625632f786ec08d16c436c8`.
- Batch 1 final report SHA-256: `7c0caa6435d685ba1fb6c8f7cf03a5158b5535ad33e1035aea03c3f80d125119`; all 863 Batch 1 run files have a frozen tree digest of `9a72647e334ae4c4dce56137aaa836aa030104df8468a756941323562ee0d02a`.
- `curation/config.json` pins Feature 003 production policy **3.1.0** and prompt set **2.4.0**. The completed efficiency benchmark adopted no model-context or batching changes.
- Pre-run gates: `pytest -q` **270 passed**; `ruff check .` passed; source validation found **205** concepts.

The normal 205-card coverage draft proposed 100 slots across all 20 categories. The reviewed allocation shifted one slot each from family/social and travel into directions/location and services, both still at six current cards. Family/social gained eight cards in Batch 1, while travel already has 15. Emotions remains the smallest category at four cards and receives seven slots. Home, at 27 cards, receives three. The final 100-slot allocation and its edit/approval reasons were frozen before generation in `curation/production-runs/corpus-004-002/manifest.json` (allocation digest `88663154ee47d9f70f30327646c11f5af59d0f22348d11428138f750018bc19b`).

| Category | Before | Frozen slots | After | Added |
| --- | ---: | ---: | ---: | ---: |
| Clothing | 8 | 4 | 12 | 4 |
| Common adjectives | 9 | 7 | 13 | 4 |
| Common verbs | 11 | 6 | 14 | 3 |
| Communication | 8 | 6 | 11 | 3 |
| Daily life | 6 | 6 | 10 | 4 |
| Directions/location | 6 | 6 | 9 | 3 |
| Education | 13 | 4 | 15 | 2 |
| Emotions | 4 | 7 | 4 | 0 |
| Family/social | 8 | 5 | 12 | 4 |
| Finance/administration | 7 | 5 | 11 | 4 |
| Food/cooking | 17 | 4 | 19 | 2 |
| Health/body | 9 | 6 | 14 | 5 |
| Home | 27 | 3 | 28 | 1 |
| Services | 6 | 6 | 12 | 6 |
| Shopping | 14 | 4 | 17 | 3 |
| Technology | 10 | 4 | 13 | 3 |
| Time/date | 8 | 5 | 11 | 3 |
| Transportation | 9 | 5 | 13 | 4 |
| Travel | 15 | 3 | 18 | 3 |
| Work | 10 | 4 | 14 | 4 |
| **Total** | **205** | **100** | **270** | **65** |

## Final funnel and quality disposition

`corpus-004-002` is **complete**. Generation made **100 proposals** and admitted exactly **100** candidates in 20 frozen category slices. None were screened out before admission. Final v3.1 decisions are **65 ACCEPT, 26 HOLD, 9 REJECT**. The 26 HOLD cards include 12 withheld after independent risk-audit findings. The nine REJECT decisions include two confirmed duplicates and two no-meaningful-cross-language-contrast candidates; each is **2% of proposals**. No exact English cue overlapped the 205-card starting source, the 100 Batch 1 candidate proposals, or another Batch 2 proposal. The remaining rejections are recorded in the individual slice reports.

The original production decisions were 77 ACCEPT, 14 HOLD, 9 REJECT. Of those 77 accepted cards, **49** met the unchanged risk-selection rules and received separate independent audits: **37 cleared**, **12 needed correction**. The 12 findings comprise **nine learner-critical answer/contrast** and **three cue/content** issues. All 12 affected cards were changed to HOLD through `scaling resolve`; no uncleared accepted card remains. Final accepted cards comprise 37 risk-cleared and 28 with no risk-audit requirement. Pending current risk audits: **zero**. No candidate received an unreviewed content correction or promotion eligibility override.

Two learner-critical findings triggered the configured `two-learner-critical-errors` promotion brake. Review of all 49 audits found several overstated national vocabulary splits where terms overlap across the two varieties, plus answer-sense and cue-granularity errors. The 12 affected cards were withheld before export. The investigation is recorded in `curation/production-runs/corpus-004-002/brake-investigation.json`; the brake's explicit disposition is in the manifest. Production policy v3.1 and risk selection remained unchanged. Metadata-only findings did not occur in risk audit. The brake was inactive before guarded promotion.

Guarded promotion exported **65** cards across all 20 slices, taking the canonical corpus from **205 to 270**. There were no blocked slices, duplicate permanent IDs, post-promotion withdrawals, or unresolved export journals. Source validation and the offline build both report **270** notes/cards. All 205 starting ID/GUID pairs retain their identity, and deck/model IDs remain fixed.

Random QA used the configured deterministic stratified sample of **7 of 65** clean promoted cards. All seven reviews recorded `none`; there were no metadata, cue/content, or learner-critical findings, and no new brake. This monitoring sample does not establish that every unsampled card is correct. The batch closed only after all seven findings were recorded and the current build and audit dispositions reconciled.

## Coverage result

Coverage grew in **19 of 20** categories. Services rose from 6 to 12, daily life from 6 to 10, and directions/location from 6 to 9, following the reviewed allocation shift. Home received only three candidate slots and one promoted card despite remaining the largest category at 28, so generation did not cluster there. **Emotions remains the clearest gap at four cards**: all seven emotion proposals became HOLD or REJECT because of shared synonyms, artificial contrasts, or an audit-discovered overstated relation. That is a candidate-selection signal for a later reviewed allocation, not grounds to relax v3.1. Other relatively small areas after the batch are directions/location (9), daily life (10), communication/time-date/finance (11 each). The complete before, frozen-slot, and after distributions are above.

## Measured work and resume behavior

| Stage | Calls | Input tokens | Output tokens | Measured model time |
| --- | ---: | ---: | ---: | ---: |
| Generation | 20 | 801,587 | 14,169 | 3.50 min |
| Semantic/redundancy review | 28 | 334,193 | 1,101 | 2.49 min |
| Production curation | 199 | 6,878,801 | 77,252 | 26.99 min |
| Independent risk audit | 49 | 2,405,625 | 50,833 | 15.95 min |
| Random QA | 7 | 86,854 | 2,213 | 0.83 min |
| **Total measured model work** | **303** | **10,507,060** | **145,568** | **49.75 min** |

The production row includes **one failed verifier response** (one call, 14,292 input tokens, 241 output tokens, 6.864 seconds) whose required preference-risk rationale was blank. The malformed capture was archived, and the same `curate --resume` command completed the missing verification without regenerating any completed candidate. The generated run report counts **198 successful production calls** and **302 successful calls overall**; the table adds the retained failed attempt so actual call and token cost is not understated. No other call failure, CLI interruption, or resume incident occurred. Model retrieval counts are unavailable from the local adapter. Promotion took 9.99 seconds and the offline build 0.01 seconds; neither makes model calls. Wall-clock idle time is excluded from all measured model times above. Production curation and independent audit costs are reported separately.

## Comparison with first operational batch

| Measure | Batch 1 | Batch 2 |
| --- | ---: | ---: |
| Starting / final corpus | 137 / 205 | 205 / 270 |
| Proposals / admitted | 103 / 100 | 100 / 100 |
| Promoted yield | 68 / 100 (68%) | 65 / 100 (65%) |
| Final HOLD / REJECT | 29 / 3 | 26 / 9 |
| Risk audits / admitted | 60 / 100 | 49 / 100 |
| Audit findings needing correction | 25 | 12 |
| Learner-critical audit findings | 17 | 9 |
| Random QA | 7 reviewed; 1 metadata-only | 7 reviewed; 0 findings |
| Confirmed duplicate / no-contrast waste | 1 / 0 | 2 / 2 |
| Total model calls | 303 | 303, including one failed retry |
| Total input / output tokens | 10,101,339 / 152,166 | 10,507,060 / 145,568 |
| Calls per promoted card | 4.46 | 4.66 |
| Input + output tokens per promoted card | 150,787 | 163,887 |
| Measured model time per promoted card | 44.55 sec | 45.92 sec |
| Coverage categories that grew | 20 / 20 | 19 / 20 |

The promotion yield changed by three cards per 100 admitted candidates. Risk-audit volume was lower, while semantic review and production input tokens were higher, leaving total model calls at 303 and measured model time near 50 minutes in both runs. The second run reached more underrepresented categories, with emotions still unresolved. Two batches do not establish a statistical quality or yield trend. The repeated contrast-overstatement finding was caught by the unchanged audit and brake workflow; it remains useful feedback for future corpus-gap selection, without changing policy or weakening review.

## Final gates and recommendation

- Final `pytest -q`: **270 passed**; `ruff check .`: passed; source validation: **270** valid concepts.
- Offline package: **270 notes / 270 cards**. All 205 starting permanent IDs and derived Anki GUIDs are unchanged; deck/model IDs are unchanged. No export journal remains.
- Batch 1 final report still has SHA-256 `7c0caa6435d685ba1fb6c8f7cf03a5158b5535ad33e1035aea03c3f80d125119`. Its 863 run files and 2,230 run-plus-slice files have no modification timestamp after Batch 2 creation; no historical artifact was edited during this run.
- Final lifecycle state: **complete**. Exactly one second 100-candidate batch was run; Batch 3 was not started.

**FEATURE 004 READY TO CONVERGE.** The second independent run completed generation, curation, risk audit, brake disposition, guarded promotion, build, random QA, and closure with candidate-level resume after one malformed response. The measured cost remains high but is consistent with the frozen quality architecture and the completed efficiency benchmark. No correctness, identity, promotion, coverage-state, or resumability blocker appeared.
