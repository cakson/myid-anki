# Recovery investigation: corpus-004-003

**State: PAUSED / INCOMPLETE.** The investigation contained the overlap class and removed unsafe promoted cards individually, but the learner-critical brake remains active and one material QA record remains unresolved. No new cards were generated or promoted.

## Failure mechanism

The recurring issue is a relation/contrast overstatement: a pair of ordinary Indonesian and Malaysian Malay preferred forms is labeled `different-common-word` as if each were exclusive to one variety, although the displayed form or a shared accepted alternative is used across both. The newspaper recurrence is concrete: **newspaper — koran / akhbar**. Both target forms are correct, but ordinary **surat kabar / surat khabar** usage crosses the national boundary. The fresh audit still found the relation materially overstates the difference after the cue had been clarified. It is preference/overlap, not a false friend.

This mechanism is not the same as every learner-critical finding. The original 66 learner-critical audits included answer-sense, specificity, cue/contrast, and false-friend issues; the saved investigation identifies 28 as overlap/overstated-split cases. Fresh examples include **shoe sole — sol sepatu / tapak kasut**, **village — desa / kampung**, and **mailbox — kotak surat / peti surat**. Their independent reviews document cross-variety use or shared equivalents. Full candidate-by-candidate original findings and fresh review evidence are in [overlap-investigation.json](overlap-investigation.json).

## Bounded roster and fresh review

The roster used the persisted production-time `shared-synonym-preference` signal with current relation `different-common-word`: **110 candidates**, all initially ACCEPT. Of these, **87** had earlier risk audits that cleared them; **23** had no audit requirement. Thirteen had prior QA review. One-by-one fresh independent review produced:

- **87 needs-correction; 23 cleared.**
- Finding classes: 45 learner-critical-answer, 11 cue-content, 31 metadata-only.
- The 31 metadata-only responses included learner-content claim reviews marked `material_risk=true` about overlap or an overstated national split. They were treated as material findings and held, not cleared as metadata.
- **All 87 materially flagged candidates are now HOLD** through the existing workflow. The remaining 23 are ACCEPT; none of the material roster remains eligible for export.
- Cross-tab: of 87 previously cleared, 70 fresh reviews found material concerns and 17 cleared; of 23 without a prior audit, 17 found material concerns and 6 cleared.

All 110 packets, responses, evidence and usage are persisted under `overlap-reviews/`. The fresh review used 110 individual model calls, 10,986,928 input tokens, 198,506 output tokens, and 49.15 minutes measured model-call time.

## Promoted cards and QA

At the start of this recovery, 109 roster cards were active. The 87 material findings were individually held using their existing IDs; 86 active rows were withdrawn and one candidate was already inactive. No broad rollback occurred. **23 roster cards remain active**, all from the 23 cleared reviews. The batch now has **183 active cards**, and the working canonical source has **453 cards**. IDs/GUID assignments were retained for withdrawals.

Of four material random-QA records, three are resolved after their accepted v3.1 corrections (ironing-board cue, boots cue, and obesity answer); their cards remain withdrawn and were not re-promoted. The newspaper record remains unresolved: candidate `tmp-communication-s012-001`, permanent ID `000315`, is HOLD and withdrawn after the fresh overlap finding. The existing `qa-resolve` workflow requires a corrected current ACCEPT decision and current risk clearance, neither of which exists for this held candidate. The record was not reclassified as metadata.

## Brakes and stop condition

The high-HOLD brake was investigated independently and disposed after investigation. Final candidate outcomes are **185 ACCEPT / 254 HOLD / 61 REJECT**, so HOLD is **50.8% (254/500)**. The 254 comprises 75 original production holds, 92 initial/follow-up audit holds, and 87 fresh-review holds. No counts were lowered or thresholds changed. The disposition is recorded in the manifest.

The `two-learner-critical-errors` brake remains **active**. Although the bounded cohort has no materially flagged ACCEPT remaining, the newspaper QA record remains unresolved and the candidate relation has no safe corrected current decision. Do not promote. The run is not complete.

The stale package still has 543 cards; it does not match the 452-card working source. No final validation, build, automated tests, Ruff checks, or closure were performed.

**Resume evidence required:** resolve the newspaper material QA record through a safe corrected accepted decision plus fresh independent clearance under existing policy, or keep it held and the run paused. Then explicitly dispose the learner brake only after all conditions in the existing workflow are met.


## Completion update — 2026-10-17

The investigation and same-batch recovery completed. See [recovery-completion.md](recovery-completion.md) and the final [`report.json`](report.json). The 110-candidate bounded roster now reconciles to 89 HOLD / 21 ACCEPT; all original 87 material findings remain HOLD and withdrawn. All nine material QA records have current terminal states (2 corrected, 7 withheld). The learner-critical and high-HOLD brakes are disposed, the canonical source and fresh package contain 450 cards, and the run manifest is complete.
