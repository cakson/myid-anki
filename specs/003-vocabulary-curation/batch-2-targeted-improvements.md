# Feature 003: targeted changes before the second fresh calibration batch

The first fresh batch is frozen: 50 generated, 44 provisional accepts, 41 guarded promotions, and a 69-card canonical deck. Its full [audit and promotion report](fresh-batch-50-final-promotion.md) is the evidence for these changes. The original candidate, audit, and promotion artifacts remain intact.

## All 17 minor corrections, grouped by root cause

| Candidate | Correction type | Primary origin | Concrete cause |
| --- | --- | --- | --- |
| `action-01` download | Metadata / usage note | Verifier judgment and metadata generation | Standard localized forms were described without the shared informal *download* borrowing. |
| `action-02` upload | Metadata / usage note | Verifier judgment and metadata generation | Same pattern for *upload*. |
| `action-03` update | Internal sense and rationale | Candidate generation, then verifier | Sense text awkwardly applied software-version installation to information; shared *update* borrowing omitted. |
| `action-04` password | Metadata / usage note | Verifier judgment and metadata generation | Shared informal *password* borrowing omitted. |
| `action-05` keyboard | Metadata / usage note | Verifier judgment and metadata generation | Standard localized terms were overstated as unqualified everyday defaults; *keyboard* is shared in casual use. |
| `action-09` emergency | Metadata / usage note | Verifier judgment | Malay *darurat* overlap and context were not explained. |
| `action-10` noisy | Metadata / usage note | Verifier judgment | Indonesian *bising* overlap was omitted; the difference is a preference. |
| `food-07` receipt | **English learner cue** plus internal sense | Candidate generation, then verifier | *Struk* fits a printed purchase slip more precisely than the broad cue “receipt.” |
| `home-04` curtain | Metadata / usage note | Verifier judgment | Indonesian *gorden* and Malay *tirai* alternatives were not acknowledged. |
| `home-08` comb | **Malay learner answer** | Candidate generation, then verifier | *Sikat rambut* was less exact for a toothed comb than *sikat*. |
| `travel-02` platform | Metadata / usage note | Verifier judgment | Cross-language alternatives *platform* and *pelantar* were omitted. |
| `travel-10` boat | Metadata / usage note | Verifier judgment | Vessel type and shared Malay *perahu* use were underexplained. |
| `work-01` employee | Metadata / usage note | Verifier judgment | Indonesian *pekerja* overlap and its broader “worker” sense were underexplained. |
| `work-03` homework | Metadata / usage note | Verifier judgment | Abbreviation-versus-phrase contrast and *kerja rumah* housework sense were underexplained. |
| `work-06` presentation | Metadata / usage note | Verifier judgment | Shared professional English borrowing and alternative Indonesian term were omitted. |
| `work-08` job application | Metadata / relation explanation | Verifier judgment | Both forms share *kerja*; a suggested new relation label was outside the project enum and was correctly not applied. |
| `work-09` company | Metadata / confidence rationale | Confidence assignment and metadata generation | Very-low rationale did not distinguish weak comparative evidence from a concrete vocabulary risk. Audit suggested high, but the historical tier was retained for calibration. |

Totals: **1 answer correction**, **1 learner cue correction**, and **15 internal-only corrections** (14 rationale/usage notes plus the `action-03` sense clarification). There were **no tag changes** and **no valid relation-enum changes**. Promotion formatting preserved approved corrections; it did not cause these defects. The recurrent problem was presenting a preferred or standard localized form as if other ordinary forms did not exist. This is primarily a generator/verifier wording issue, not widespread wrong target-language vocabulary.

## Three unsafe or unresolved accepts

`action-07` (*hamil* / *mengandung*) passed because the verifier agreed with the pair and mentioned only polysemy; it missed the shared ordinary pregnancy vocabulary and possible artificial national split. `home-10` (*wajan* / *kuali*) passed because the verifier incorrectly asserted that both broad vessel words matched the cue's **shallow** shape. `travel-03` (*koper* / *beg pakaian*) passed despite a verifier concern that the Malay term was broader than the cue. All three were very-low, audited, and explicitly held after production.

The first batch's 28 nonempty verifier-concern records include many harmless overlaps, so a broad deterministic rule that turns every “broader” or shared-synonym mention into HOLD would create avoidable false negatives. There is no dependable cheap string trigger for the frying-pan error because the verifier asserted the wrong semantic alignment. The smallest justified change is to make the **existing single verifier** check cue qualifiers, cross-language shared synonyms, and whether semantic breadth is material, with no new universal stage. The strict false-friend gate and ordinary optimistic acceptance remain unchanged.

## Changes applied before the second batch

- Prompt set **2.1.0** adds concise cue/sense alignment, shape and subtype checks, cross-language ordinary-synonym checks, and standard-localized versus casual-borrowing distinctions. It keeps four valid relation labels and the current fast path.
- The policy-v3 confidence rationale now uses the verifier's candidate-specific reasoning, appends a concrete nonmaterial verifier caveat when missing, and states when comparative preference evidence was not gathered. This is deterministic metadata assembly, without another AI pass.
- The verifier packet for 2.1.0 keeps the compact policy-v3 context. The central model routing remains Luna for production roles; the CLI helper can use the configured reasoning effort.
- The second calibration audit will cover every accepted `very-low` and `low` card, every accepted false friend, a seeded stratified medium sample, and a smaller seeded high sample with **at least one high card if any exist**. This is a calibration policy, not a permanent audit percentage.

Confidence tiers are not reweighted yet. In Batch 1, all three unsafe/unresolved findings and both learner-facing corrections were very-low, whereas medium contained metadata corrections only. This is a useful directional signal. `limited-evidence` appeared on all 44 accepts and is not independently discriminating; concrete verifier caveats were more informative. The next audit will test whether that pattern repeats without changing historical tiers or correction history.

The next 50-candidate run starts only after tests, Ruff, source validation, and a 69-card/GUID identity snapshot pass. It will remain a provisional production batch until its reduced audit and correction review are complete; no automatic promotion is planned for it.
