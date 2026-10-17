# `corpus-004-003` recovery completion

**Status: COMPLETE.** The same 500-candidate production run resumed and closed. No vocabulary was generated and no new batch was created.

## Final production state

- Starting corpus: 270 cards.
- Final ACCEPT / HOLD / REJECT: **180 / 259 / 61**.
- Final canonical source and fresh `.apkg`: **450 cards/notes** (270 starting cards + 180 active cards from this run).
- This run assigned permanent IDs to 273 candidates over its lifetime; **180 are active in the final source** and 93 assigned IDs are not active. The 270 starting IDs and GUIDs remain unchanged; active IDs and derived GUIDs are unique.
- Since resuming this investigation, guarded export restored two previously corrected, current-ACCEPT cards. QA then safely withheld five additional cards with material cue findings. The learner source was rebuilt from the final state; no held card was re-promoted.

## QA and overlap incident

- Material QA terminal outcomes: **2 resolved-corrected, 7 resolved-withheld, 0 unresolved**. Withheld resolutions remain bound to the current HOLD/REJECT decision, candidate content, permanent ID, and absence from canonical source. They do not confer promotion eligibility.
- Candidate `000315` (`newspaper`, `koran / akhbar`) remains HOLD and withdrawn. No corrected ACCEPT was invented.
- All 87 candidates materially flagged in the bounded overlap review remain HOLD and absent from source. The other 23 in that review had been cleared; two later random-QA cue findings among those candidates were held, leaving 21 active ACCEPT candidates in the roster.
- The fresh final random-QA sample reviewed **18 cards: 17 clean, 1 metadata-only, 0 unresolved material findings**. Across the persisted QA records, 89 candidates were reviewed: 77 clean, 9 cue/content findings, and 3 metadata findings.
- Both safety brakes are disposed. The high-HOLD disposition remains based on the recorded investigation; the learner-critical brake was disposed only after confirming the bounded roster, terminal QA records, and withdrawn state of affected cards.
- The overlap recurrence was contained through the existing independent review, HOLD, and withdrawal workflow. Production policy v3.1 and the overlap-risk policy are unchanged.

## Validation and build

- Canonical source validation: **450 concepts, valid**.
- Fresh `.apkg`: **450 notes and 450 cards**, matching canonical source. The prior 543-card package was replaced.
- Automated tests: **271 passed**.
- Ruff lint: **passed**; Ruff format check: **330 files already formatted**.
- Starting identity check: all **270/270 IDs and GUIDs stable**; active concept IDs/GUIDs unique; deck/model IDs unchanged.

The machine-readable final report, including coverage, audit, promotion, and cost metrics, is in [`report.json`](report.json). Candidate evidence and resolution history remain in the run QA and overlap-investigation artifacts.
