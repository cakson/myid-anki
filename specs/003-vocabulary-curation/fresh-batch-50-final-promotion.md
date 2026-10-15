# Feature 003: complete fresh-batch audit and guarded promotion

**Completed:** 2026-10-14 UTC. This finishes the one-time comprehensive audit of the first genuinely new 50-candidate batch after optimistic-policy recalibration. It does not set a universal deep-audit requirement for future batches. The [production benchmark](fresh-batch-50-benchmark.md), [first 23-card audit](fresh-batch-50-audit.json), [remaining 21-card audit](fresh-batch-50-audit-completion.json), [production decisions](fresh-batch-50-state.json), [corrected preview](fresh-batch-50-promotion-preview.json), and [atomic promotion record](../../curation/promotions/fresh-batch-50.json) retain the full decision and correction trail.

## Fresh-batch funnel

| Stage | Cards |
| --- | ---: |
| Newly generated | 50 |
| Provisional production ACCEPT / HOLD / REJECT | 44 / 2 / 4 |
| Provisionally accepted cards audited | 44/44 |
| Audit confirmed good / minor correction / materially misleading / should HOLD / should REJECT | 24 / 17 / 1 / 1 / 1 |
| Final fresh cards promoted | **41** |
| Final fresh candidates withheld or rejected | **9** (2 production HOLD, 4 production REJECT, 3 audit flags) |

All 41 promoted cards were ordinary learner-eligible relations: 35 `different-common-word`, 6 `similar`, and 0 `false-friend`. No `same` or duplicate candidate was promoted. The first four production rejections and two production holds retain their original decisions; the three newly flagged provisional accepts were not promoted. The promotion record preserves their AI candidate IDs, original decisions, verifier output, audit verdict, correction history, and reasons.

## The three provisional accepts challenged by audit

All three entered the fast path because the independent Luna verifier returned `agree`, an eligible `different-common-word` relation, and no `material_concerns`. They all received `very-low` confidence with `limited-evidence`, `limited-verifier-agreement`, and `usage-preference-weak` flags. Those flags correctly prioritized them for this audit, but did not themselves prevent provisional acceptance.

| ID and card | Audit challenge and error type | Final action |
| --- | --- | --- |
| `fresh-actions-001:action-07`: **pregnant** — `hamil` / `mengandung` | Auditor marked **should-reject**: both words also occur for pregnancy across the languages, so the asserted national preference contrast may be artificial. This is a **usage-preference/learning-contrast** question, not a wrong translation. The production verifier mentioned only the other sense of *mengandung* (“containing”) and missed the cross-language synonym concern. DBP defines Malay *hamil* as pregnant and states that *mengandung* is used for that sense, so the auditor's categorical rejection is not independently established by word existence alone ([DBP hamil](https://prpm.dbp.gov.my/Cari1?d=24348&keyword=hamil), [DBP usage advice](https://prpm.dbp.gov.my/Cari1?d=175768&keyword=mengandung)). | **HOLD**, excluded from this release pending a targeted within-language preference check. Original `should-reject` audit verdict stays in the record. |
| `fresh-home-001:home-10`: **frying pan** — `wajan` / `kuali`; sense specified a *shallow* pan | Auditor marked **materially-misleading**: the answers are broader frying vessels and do not inherently identify the specified shallow, flat type. This is an **English cue/sense mismatch**. The production verifier incorrectly asserted exact alignment and failed to challenge the shape qualifier. DBP gives *kuali* a broad definition and specifically translates a shallow frying pan as *kuali leper* ([DBP kuali](https://prpm.dbp.gov.my/Cari1?d=371752&keyword=kuali)). | **HOLD**, excluded until a corrected cue or answer pair is independently validated. The original card must not be shown as written. |
| `fresh-travel-001:travel-03`: **suitcase** — `koper` / `beg pakaian` | Auditor marked **should-hold**: *beg pakaian* can denote a broader clothes bag, so its exactness and preferred everyday use for a suitcase are unresolved. This is a **semantic breadth/usage-preference** concern. The production verifier actually noted the broader sense but treated it as nonmaterial. DBP uses *beg pakaian* to translate “suitcase” in context and also defines the phrase broadly; neither fact settles everyday preference by itself ([DBP example](https://prpm.dbp.gov.my/cari1?keyword=sachet), [DBP beg](https://prpm.dbp.gov.my/Cari1?d=72508&keyword=beg)). | **HOLD**, excluded pending a targeted exact-sense/preference check. |

The smallest reusable risk improvement is to distinguish an actual cue/answer breadth objection from a harmless alternate sense. A verifier concern explicitly saying an answer is *broader/narrower than the cue*, or that a cue's defining physical qualifier is unestablished, should trigger a targeted semantic check before ACCEPT. For `different-common-word`, the verifier should also explicitly check whether the same forms are ordinary in both locales before claiming a preferred national contrast. The *hamil* case shows that asking only whether both supplied answers are plausible can miss shared normal synonyms. These are prompt/risk-trigger changes, not a reason to restore universal evidence research or adversarial review.

The three audit flags were also recorded as **explicit material HOLD events** in their original batches after the frozen production benchmark. Their current batch reports therefore show 41 accepted, 5 held, and 4 rejected across all 50 candidates, while `fresh-batch-50-state.json` preserves the original 44/2/4 production decisions. This prevents a later generic batch export from treating the three audited cards as still releasable.

## Correction taxonomy and confidence calibration

The 17 audit `minor-correction` findings are distinct from the three unsafe findings. The corrected promotion overlay made **one learner-answer correction**: `home-08` Malaysian *sikat rambut* → *sikat* for “comb,” consistent with DBP's hair-comb entry ([DBP sikat](https://prpm.dbp.gov.my/Cari1?d=72508&keyword=sikat)). It made **one learner-cue correction**: `food-07` “receipt” → “printed receipt” and narrowed its sense to a purchase slip; DBP defines Malay *resit* as written proof of payment or receipt of goods ([DBP resit](https://prpm.dbp.gov.my/Cari1?d=175768&keyword=resit)). The other **15 are internal metadata corrections**: 14 confidence-rationale/usage-note clarifications, plus one internal sense clarification for `action-03` (“update”) with its rationale. Tags did not change. No permitted relation value changed. Audit suggestions naming values outside the project's four-relation taxonomy were recorded as notes, not inserted as invalid relation labels. The auditor suggested raising `work-09` from very-low to high; its original tier remains pending broader empirical calibration rather than retrofitting this sample.

The main minor-correction pattern was **overstating exclusive national difference** when a shared synonym or English borrowing also occurs. This was especially visible in localized technology vocabulary (*download*, *upload*, *update*, *password*, *keyboard*). The supplied Indonesian and Malay answers remained valid; their curation rationales now describe a standard/localized or preferred-form contrast more accurately. The learner-facing corrections were 1 answer and 1 English cue among 41 promoted cards. Correction provenance is retained per card in `curation/promotions/fresh-batch-50.json`.

| Accepted confidence tier | Audited | Confirmed good | Learner-answer correction | Learner-cue correction | Metadata-only correction | Should HOLD | Should REJECT | Materially misleading |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| high | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| medium | 26 | 19 | 0 | 0 | 7 | 0 | 0 | 0 |
| low | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| very-low | 18 | 5 | 1 | 1 | 8 | 1 | 1 | 1 |
| **Total** | **44** | **24** | **1** | **1** | **15** | **1** | **1** | **1** |

The tier ordering was **directionally useful** in this batch: all three unsafe/unresolved audit flags and both learner-facing corrections were very-low; all 26 medium cards needed at most metadata cleanup. However, the batch produced no high or low accepts, and one batch cannot calibrate four tiers. The universal `limited-evidence` flag did not discriminate quality (44/44 accepted cards had it); `usage-preference-weak` was also common (38/44). A concrete verifier concern was more informative: all 18 very-low cards had `limited-verifier-agreement`, versus 4/26 medium. Its wording still needs materiality assessment, as many such cards were safe. No tier assignments were changed to manufacture a monotonic pattern.

## Performance and cost

The original production clock and provisional result are unchanged: **531.0 seconds** from generation through decisions, **44 provisional accepts**, **298.31 provisional accepts/hour**, 22 model calls (5 generation, 5 semantic normalization, 11 verification, 1 repair), 310,538 input tokens and 21,201 output tokens. Production had 0 external evidence retrievals and 0 cache hits/misses because all accepted ordinary candidates used the configured fast path. A malformed-output rerun and repair remain included in the production clock and operation records.

The completed audit added a separate **180.445-second** Sol interval, 5 calls, 69,570 input tokens and 6,347 output tokens. Together with the first **340.204-second** Sol interval, the two instrumented audit intervals totaled **520.649 seconds**, **10 calls**, **137,482 input tokens**, and **16,892 output tokens**. Targeted DBP lookups and the later correction/promotion work were separate, and their full wall-clock duration was not instrumented. No monetary per-card cost is reported because a versioned model price/accounting record was unavailable.

The final safe promotion yield is **41/50 = 82%**. For comparison only, 41 cards over the original 530.998-second production interval equals **277.97 promotable cards per production hour**. This is **promotion-adjusted production throughput excluding separate audit and promotion time**; it is not full operational, release, or empirically quality-adjusted canonical throughput. The audit was a one-time comprehensive calibration expense, not a routine per-card gate. The empirical expert-human benchmark has not been measured, so the AI/human ratio and the approximately 50× long-term objective remain unavailable.

## Final deck and validation

The guarded transaction promoted **41** new concepts: **28 → 69** canonical learner rows. It assigned permanent IDs only to the promoted candidates and retained every previously active ID. The generated `dist/myid-anki.apkg` contains **69 notes and 69 cards**, with **69 unique GUIDs**. Every GUID equals the deterministic value derived from its source concept ID, including all 28 previously active IDs. No `same` relation entered the TSV; no duplicate promotion passed the pre-ID overlap check. The corrected “printed receipt” cue and `sisir` / `sikat` answers appear in source and package. Deck and note-model identity were unchanged.

Offline source validation and build passed. The complete automated suite passed **170 tests**; Ruff lint and formatting checks passed. The promotion record includes source and input-artifact digests, individual candidate IDs, original/final learner content, audit verdicts, confidence rationales, and excluded-candidate reasons.

## Recommendation

**Use targeted generator/verifier improvements, then another bounded 50-card calibration batch before larger autonomous batches.** Preserve the fast ordinary path, which produced 41 releasable cards from 50 new concepts. Improve candidate generation and the lightweight verifier around exact English cue qualifiers, shared cross-language synonyms, and standard localized terminology versus everyday borrowings. Add a targeted escalation rule when the verifier itself notes that a term is broader or narrower than the cue. Keep confidence-prioritized plus random/stratified audits for future batches; do not turn this one-time full audit into a universal stage. The three withheld candidates remain available for later targeted reconsideration under their original IDs. No further batch has been started.
