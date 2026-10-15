# Batch 2 fixed-corpus policy replay

Historical state and audit were read only. No candidates were generated or promoted.

## Diagnosis and policy delta

The companion [16-card diagnosis](batch-2-replay-diagnosis.md) classifies all ten
minor corrections and six unsafe/unresolved accepts by primary cause: ambiguous
English cue 4, mismatched sense 3, shared synonym 2, wrong preference assumption 2,
relation problem 1, and internal metadata only 4. Some causes overlap. No confirmed
target-language answer correction was found. Prompt 2.2.0 asks for explicit cue/sense
alignment and a three-way shared-synonym judgment. Policy 3.1.0 routes a concrete
weak-contrast concern to HOLD and bases confidence on candidate-specific signals,
without treating missing optional frequency research as `very-low` risk.

The replay reused all original candidate IDs and normalization artifacts. It also
made a separate bounded check of the six non-identical historical HOLD/REJECT
objections. Those objections were supplied verbatim to Luna, and every resulting
assessment was recorded. The independent audit verdicts remained hidden until all
new decisions were made. No historical batch record was overwritten.

- Frozen candidates: 50; model: gpt-5.6-luna; verifier calls: 15
- Replay decisions: {'accepted': 40, 'rejected': 4, 'hold': 6}; accepted confidence: {'high': 16, 'medium': 16, 'low': 8}
- Fast-path accepts: 40; escalations: 6
- Active replay elapsed: 207.787 seconds
- Additional historical-objection assessment: 27.409 seconds; total active time about 235.196 seconds
- Recorded verifier tokens: input 189295, output 26598; cost unavailable (no price recorded)
- Decisions or relations changed: 11 — cal2-daily-001:daily-06, cal2-shopping-001:shopping-01, cal2-social-001:social-04, cal2-social-001:social-06, cal2-social-001:social-08, cal2-travel-001:travel-03, cal2-travel-001:travel-07, cal2-work-001:work-01, cal2-work-001:work-02, cal2-work-001:work-06, cal2-work-001:work-09
- Previously audited unsafe/unresolved: 6; replay HOLD/REJECT: 2; accepted low/very-low: 3; accepted medium/high: 1
- Confirmed-good cards still very-low: 0

Original production was 40 ACCEPT / 4 HOLD / 6 REJECT; replay is 40 / 6 / 4.
Thirty-eight original accepts remain accepted, while two now HOLD for weak
cross-language contrast. Two prior HOLD/REJECT candidates become provisional ACCEPT
after explicit objection assessment. Three prior HOLDs remain held. One prior
REJECT becomes HOLD: its exact semantic mismatch was reconfirmed, but the new
verifier did not express an affirmative defect code. This is a conservative
decision-state difference; the card remains withheld. Four identical-form
no-contrast candidates remain rejected before any new verifier call.

The 15 Luna calls include three structured-output retries: two invalid `verdict`
values and one empty optional affirmative-defect field. Those outputs failed
validation and did not enter decisions. Recorded cost is unavailable because
provider price information was not captured. The approximately 235-second figure
is a **fixed-corpus replay**, not end-to-end generation or operational throughput.

## Audit calibration

| Replay tier or outcome | Audit findings |
|---|---|
| high | {'confirmed-good': 12, 'minor-correction': 4} |
| hold | {'should-reject': 1, 'materially-misleading': 1} |
| low | {'should-reject': 2, 'confirmed-good': 2, 'minor-correction': 1, 'materially-misleading': 1} |
| medium | {'minor-correction': 5, 'should-reject': 1, 'confirmed-good': 10} |

The six independently audited unsafe/unresolved cards now separate as follows:

| Candidate | Audit issue | Replay result | Remaining finding |
|---|---|---|---|
| `daily-05` vacuum cleaner | Unsupported everyday national preference | ACCEPT / medium | The verifier calls a shared English borrowing a useful preference despite a named Malay alternative. |
| `shopping-06` payment | Act versus amount sense mismatch | ACCEPT / low | A narrower cue was proposed, but `bayaran` was still treated as the everyday act term. |
| `social-04` meet someone | Shared ordinary synonym | HOLD | The weak contrast was routed to escalation. |
| `social-06` visit someone | Sense and shared-usage mismatch | HOLD | The weak contrast was routed to escalation. |
| `travel-10` intersection | Shared normal road terms | ACCEPT / low | A concrete cross-border usage concern was recorded but called nonblocking. |
| `work-08` deadline | Date/time and register-sensitive overlap | ACCEPT / low | A cue rewrite helped, but shared borrowing and register risk were understated. |

Five of six unsafe/unresolved cards are now either held or accepted at low
confidence; one remains medium. None is high. Among 24 independently confirmed-good
cards, none remains very-low: 12 are high, ten medium, and two low. This is
directionally more useful than the prior 36/40 very-low collapse, but the tiers
are **not calibrated probabilities**. Four known unsafe cards remain provisional
ACCEPT, so the replay is not a guarded-promotion recommendation. The previous
34-card promotion preview remains unchanged.

## Material decision changes

| Candidate | Change | Why |
|---|---|---|
| `social-04` meet someone | ACCEPT → HOLD | Both verbs may be ordinary on both sides, weakening the claimed national preference. |
| `social-06` visit someone | ACCEPT → HOLD | Cross-border synonym use and visit-sense scope remain material. |
| `social-08` apologize | HOLD remains; relation changes to `similar` | The prior objection that `minta maaf` is ordinary in Malaysia remains material; relabeling does not resolve a weak contrast. |
| `travel-03` highway | REJECT → HOLD | The toll-road versus unrestricted-highway mismatch is reconfirmed; the new output marks it material but does not encode an affirmative defect. It stays withheld. |
| `travel-07` destination | REJECT → provisional ACCEPT / low | The new verifier treats `destinasi` overlap as compatible with a contextual preference and explicitly disputes the old objection. This unaudited recovery needs targeted review before promotion. |
| `work-01` coworker | ACCEPT remains; `different-common-word` → `similar` | The forms are recognizably related; no learner-answer change. |
| `work-06` internship | HOLD → provisional ACCEPT / low | The verifier explicitly resolves the old breadth objection with a narrower placement cue; the proposed cue is wordy and requires editorial validation before promotion. |

The other four counted relation changes are bookkeeping: old no-contrast REJECT
records had no relation label, while the replay records `same`. Their decisions
and learner exclusion did not change.

The unresolved pattern is specific: the verifier can label a named competing
ordinary form `useful-preference` and `minor` despite a potentially artificial
national split. A blanket HOLD for every shared synonym would also withhold
several confirmed-good cards. The next focused improvement should test a targeted
preference challenge when a concrete ordinary rival is named or a cue rewrite
changes the claimed sense. It should not add a universal evidence stage. Batch 2
promotion should continue to use the completed independent audit and corrections;
no Batch 3 or larger run is justified by this replay alone.

## Candidate comparison

| Candidate | Old | Replay | Old → new relation | Old → new tier | Fast path | Audit | Reason / routing |
|---|---|---|---|---|---|---|---|
| cal2-daily-001:daily-01 | accepted | accepted | different-common-word → different-common-word | very-low → high | True | confirmed-good | ordinary-verifier-agreement; aligned, nonpreferred-alternative, none |
| cal2-daily-001:daily-02 | accepted | accepted | different-common-word → different-common-word | very-low → high | True | minor-correction | ordinary-verifier-agreement; aligned, nonpreferred-alternative, none |
| cal2-daily-001:daily-03 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | minor-correction | ordinary-verifier-agreement; aligned, none, minor |
| cal2-daily-001:daily-04 | accepted | accepted | different-common-word → different-common-word | very-low → high | True | confirmed-good | ordinary-verifier-agreement; aligned, nonpreferred-alternative, none |
| cal2-daily-001:daily-05 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | should-reject | ordinary-verifier-agreement; aligned, useful-preference, minor |
| cal2-daily-001:daily-06 | rejected | rejected | — → same | — → — | False | not audited | no-meaningful-cross-language-contrast;  |
| cal2-daily-001:daily-07 | accepted | accepted | different-common-word → different-common-word | very-low → high | True | confirmed-good | ordinary-verifier-agreement; aligned, nonpreferred-alternative, none |
| cal2-daily-001:daily-08 | hold | hold | different-common-word → different-common-word | — → — | False | not audited | A shared ordinary synonym may defeat the claimed national preference.; The English cue may misalign the two target-language senses.; The Indonesian answer may mean a family room rather than the home's main room for receiving visitors, making the contrast misleading.; Unresolved historical objection: The Indonesian answer does not match the stated receiving-visitors sense and creates a misleading contrast.; material-risk, weak-contrast, none |
| cal2-daily-001:daily-09 | accepted | accepted | different-common-word → different-common-word | very-low → high | True | minor-correction | ordinary-verifier-agreement; aligned, nonpreferred-alternative, none |
| cal2-daily-001:daily-10 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | minor-correction | ordinary-verifier-agreement; aligned, useful-preference, minor |
| cal2-shopping-001:shopping-01 | rejected | rejected | — → same | — → — | False | not audited | no-meaningful-cross-language-contrast;  |
| cal2-shopping-001:shopping-02 | accepted | accepted | different-common-word → different-common-word | medium → high | True | minor-correction | ordinary-verifier-agreement; aligned, none, none |
| cal2-shopping-001:shopping-03 | accepted | accepted | different-common-word → different-common-word | medium → high | True | confirmed-good | ordinary-verifier-agreement; aligned, none, none |
| cal2-shopping-001:shopping-04 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | confirmed-good | ordinary-verifier-agreement; aligned, none, minor |
| cal2-shopping-001:shopping-05 | accepted | accepted | different-common-word → different-common-word | medium → high | True | confirmed-good | ordinary-verifier-agreement; aligned, none, none |
| cal2-shopping-001:shopping-06 | accepted | accepted | different-common-word → different-common-word | very-low → low | True | should-reject | ordinary-verifier-agreement; correctable, useful-preference, minor |
| cal2-shopping-001:shopping-07 | accepted | accepted | different-common-word → different-common-word | very-low → low | True | confirmed-good | ordinary-verifier-agreement; correctable, nonpreferred-alternative, none |
| cal2-shopping-001:shopping-08 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | minor-correction | ordinary-verifier-agreement; aligned, useful-preference, none |
| cal2-shopping-001:shopping-09 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | confirmed-good | ordinary-verifier-agreement; aligned, useful-preference, none |
| cal2-shopping-001:shopping-10 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | confirmed-good | ordinary-verifier-agreement; aligned, useful-preference, none |
| cal2-social-001:social-01 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | confirmed-good | ordinary-verifier-agreement; aligned, useful-preference, minor |
| cal2-social-001:social-02 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | confirmed-good | ordinary-verifier-agreement; aligned, nonpreferred-alternative, minor |
| cal2-social-001:social-03 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | confirmed-good | ordinary-verifier-agreement; aligned, useful-preference, none |
| cal2-social-001:social-04 | accepted | hold | different-common-word → different-common-word | very-low → — | False | should-reject | A shared ordinary synonym may defeat the claimed national preference.; weak-contrast; aligned, weak-contrast, none |
| cal2-social-001:social-05 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | confirmed-good | ordinary-verifier-agreement; aligned, useful-preference, none |
| cal2-social-001:social-06 | accepted | hold | different-common-word → different-common-word | very-low → — | False | materially-misleading | A shared ordinary synonym may defeat the claimed national preference.; weak-contrast; aligned, weak-contrast, none |
| cal2-social-001:social-07 | accepted | accepted | different-common-word → different-common-word | very-low → high | True | confirmed-good | ordinary-verifier-agreement; aligned, none, none |
| cal2-social-001:social-08 | hold | hold | different-common-word → similar | — → — | False | not audited | Minta maaf is also ordinary everyday Malaysian, so labeling memohon maaf as the Malaysian counterpart may mislead learners.; Unresolved historical objection: Minta maaf is also an ordinary everyday expression in Malaysian, so presenting memohon maaf as the Malaysian counterpart creates an artificial country contrast and may mislead learners about ordinary usage.; aligned, none, none |
| cal2-social-001:social-09 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | minor-correction | ordinary-verifier-agreement; aligned, useful-preference, minor |
| cal2-social-001:social-10 | hold | hold | different-common-word → different-common-word | — → — | False | not audited | A shared ordinary synonym may defeat the claimed national preference.; Kecewa is ordinary in Malaysian, while hampa is marked or context-dependent and may suggest emotional emptiness or an unfulfilled state rather than ordinary disappointment.; The English cue may misalign the two target-language senses.; Unresolved historical objection: Hampa is not a clean Malaysian counterpart for the general everyday sense of disappointed: kecewa is also ordinary in Malaysian, and hampa may suggest emotional emptiness rather than simply an unmet expectation.; material-risk, weak-contrast, none |
| cal2-travel-001:travel-01 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | confirmed-good | ordinary-verifier-agreement; aligned, useful-preference, minor |
| cal2-travel-001:travel-02 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | confirmed-good | ordinary-verifier-agreement; aligned, nonpreferred-alternative, minor |
| cal2-travel-001:travel-03 | rejected | hold | different-common-word → different-common-word | — → — | False | not audited | The English cue may misalign the two target-language senses.; The answers do not express the same exact concept: jalan tol is narrower than highway.; Unresolved historical objection: The Indonesian answer does not generally match an unrestricted highway; it specifically denotes a toll road.; material-risk, none, none |
| cal2-travel-001:travel-04 | accepted | accepted | different-common-word → different-common-word | very-low → high | True | minor-correction | ordinary-verifier-agreement; aligned, none, none |
| cal2-travel-001:travel-05 | accepted | accepted | similar → similar | medium → high | True | confirmed-good | ordinary-verifier-agreement; aligned, none, none |
| cal2-travel-001:travel-06 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | confirmed-good | ordinary-verifier-agreement; aligned, useful-preference, minor |
| cal2-travel-001:travel-07 | rejected | accepted | different-common-word → different-common-word | — → low | True | not audited | ordinary-verifier-agreement; aligned, useful-preference, minor |
| cal2-travel-001:travel-08 | accepted | accepted | different-common-word → different-common-word | very-low → high | True | confirmed-good | ordinary-verifier-agreement; aligned, nonpreferred-alternative, none |
| cal2-travel-001:travel-09 | accepted | accepted | different-common-word → different-common-word | very-low → high | True | confirmed-good | ordinary-verifier-agreement; aligned, nonpreferred-alternative, none |
| cal2-travel-001:travel-10 | accepted | accepted | different-common-word → different-common-word | very-low → low | True | should-reject | ordinary-verifier-agreement; aligned, useful-preference, concrete |
| cal2-work-001:work-01 | accepted | accepted | different-common-word → similar | very-low → high | True | confirmed-good | ordinary-verifier-agreement; aligned, none, none |
| cal2-work-001:work-02 | rejected | rejected | — → same | — → — | False | not audited | no-meaningful-cross-language-contrast;  |
| cal2-work-001:work-03 | accepted | accepted | different-common-word → different-common-word | very-low → low | True | minor-correction | ordinary-verifier-agreement; correctable, nonpreferred-alternative, none |
| cal2-work-001:work-04 | accepted | accepted | different-common-word → different-common-word | very-low → low | True | confirmed-good | ordinary-verifier-agreement; correctable, none, minor |
| cal2-work-001:work-05 | accepted | accepted | different-common-word → different-common-word | very-low → high | True | confirmed-good | ordinary-verifier-agreement; aligned, none, none |
| cal2-work-001:work-06 | hold | accepted | different-common-word → different-common-word | — → low | True | not audited | ordinary-verifier-agreement; correctable, useful-preference, minor |
| cal2-work-001:work-07 | accepted | accepted | different-common-word → different-common-word | very-low → medium | True | minor-correction | ordinary-verifier-agreement; aligned, useful-preference, none |
| cal2-work-001:work-08 | accepted | accepted | different-common-word → different-common-word | very-low → low | True | materially-misleading | ordinary-verifier-agreement; correctable, useful-preference, minor |
| cal2-work-001:work-09 | rejected | rejected | — → same | — → — | False | not audited | no-meaningful-cross-language-contrast;  |
| cal2-work-001:work-10 | accepted | accepted | different-common-word → different-common-word | very-low → high | True | confirmed-good | ordinary-verifier-agreement; aligned, nonpreferred-alternative, none |
