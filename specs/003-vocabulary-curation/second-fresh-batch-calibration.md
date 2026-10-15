# Feature 003: second fresh 50-candidate calibration

**Completed:** 2026-10-14 UTC. This is the second bounded fresh batch, after the 69-card guarded promotion. It generated exactly 50 new candidates across five everyday topic groups. The [frozen production state](second-batch-50-state.json), [separate audit](second-batch-50-audit.json), [read-only promotion preview](second-batch-50-promotion-preview.json), and per-batch `curation/batches/cal2-*/` records retain candidate IDs, raw model output, duplicate decisions, verifier output, timing, and correction history. No Batch 2 candidate was assigned a permanent ID or added to the canonical TSV.

## Targeted changes made before generation

The [root-cause review](batch-2-targeted-improvements.md) classifies all 17 Batch 1 minor corrections: one Malay answer error, one English cue error, and 15 internal sense, rationale, or usage-note errors. The repeating cause was overstating localized or preferred forms as exclusive national vocabulary. Three unsafe Batch 1 accepts exposed shared-synonym and cue-breadth risks. These observations led to prompt set **2.1.0**: generation asks for one exact, concise English sense and avoids formal localized terms against shared ordinary borrowings; the single independent verifier checks both answers against the cue's qualifiers and asks whether a shared synonym defeats the asserted national contrast. The policy-v3 confidence rationale now retains candidate-specific verifier reasoning and materiality-qualified caveats without another model call. Its tier assignment and the optimistic acceptance gate did **not** change. Production remained on centrally configured Luna; Sol was used only for this separate calibration audit.

The first batch's 17 corrections originated mainly in candidate generation and verifier/metadata wording, not promotion formatting. The only learner-answer correction was `sikat rambut` to `sikat`; the only learner-cue correction was `receipt` to `printed receipt`. The other 15 were internal notes/rationales, including one internal sense clarification. No tag or valid relation-enum edit was needed in Batch 1. The second batch tests whether the narrower cue and synonym instructions reduce these defects.

## Frozen production funnel

| Measure | Batch 2 result |
| --- | ---: |
| Generated | **50** |
| Provisional ACCEPT / HOLD / REJECT | **40 / 4 / 6** |
| ACCEPT through ordinary fast path / escalated ACCEPT | **40 / 0** |
| Accepted `different-common-word` / `similar` / `false-friend` | **39 / 1 / 0** |
| Accepted confidence high / medium / low / very-low | **0 / 4 / 0 / 36** |
| Early identical-form no-contrast REJECT | **4** (8% generation waste) |
| Confirmed duplicate REJECT | **0** |
| Other affirmative REJECT | **2** |
| Material HOLD / escalation | **4** |
| Fast-path utilization among accepted ordinary cards | **40/40 = 100%** |

The four early no-contrast forms were `sarung bantal`/`sarung bantal`, `harga`/`harga`, `gaji`/`gaji`, and `laporan`/`laporan`. The other two production rejects were an unrestricted “highway” paired with Indonesian `jalan tol` (a toll-road term), and `tujuan`/`destinasi` as an artificial exclusive destination contrast. Production HOLDs had concrete objections: `ruang keluarga` did not fit a visitors' living-room sense; `minta maaf` is ordinary in Malay too; `hampa` may not fit generic disappointed; and `latihan industri` may be narrower than an unrestricted internship. No false friend passed the ordinary gate.

One normalization model response listed ten shopping candidates as overlaps with themselves. The raw response and `second-normalize-self-overlap-repair.json` are retained; a deterministic repair discarded only those impossible self-references and preserved all other overlap results. This used no additional model call. There were no provider failures or retries in production. The generation archive included the 69-card learner source and historical candidate records; the five normalization groups compared the full new cohort and that archive.

## End-to-end production time and model work

The clock began before the first generation call and ended after all 50 curation decisions were prepared: **282.720 seconds**. This includes generation, duplicate review, verification, local repair, and final decision preparation. It excludes the later audit and any future promotion.

| Measure | Result |
| --- | ---: |
| Provisional ACCEPT decisions per production hour | **509.34** |
| Production seconds per provisional ACCEPT | **7.07** |
| Model calls: generation / normalization / verifier | **5 / 5 / 10** |
| Total model calls; calls per provisional ACCEPT | **20; 0.50** |
| Input / output tokens | **306,279 / 16,172** |
| Total tokens per provisional ACCEPT | **8,061** |
| Sum of recorded model-call elapsed time | **248.566 seconds** |
| Evidence retrievals; cache hits/misses | **0; 0/0** (ordinary fast path) |
| Provider retries / failures | **0 / 0** |
| Approximate monetary cost | **Unavailable**: no versioned provider price/accounting record |

The call latency sums were 65.025 seconds for generation, 46.832 for normalization, and 136.709 for verification. The production rate counts provisional decisions, not promoted learner cards. The empirical expert-human benchmark is still unavailable, so no 50× comparison can be calculated.

## Separate calibration audit and adjudication

The predeclared rule selected every accepted `very-low`, `low`, and false-friend card, plus a seeded sample of up to five `medium` and two `high` cards. Because 36/40 accepts were `very-low` and only four were `medium`, this rule selected **all 40 provisional accepts**. The intended sampling rule therefore did **not** reduce the audit coverage in this batch. That is a confidence-distribution defect to address before routine larger batches, rather than a reason to silently retier the frozen cohort.

| Confidence tier | Audited | Confirmed good | Minor correction | Materially misleading | Should REJECT | Should HOLD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| high | 0 | 0 | 0 | 0 | 0 | 0 |
| medium | 4 | 3 | 1 | 0 | 0 | 0 |
| low | 0 | 0 | 0 | 0 | 0 | 0 |
| very-low | 36 | 21 | 9 | 2 | 4 | 0 |
| **Total** | **40** | **24** | **10** | **2** | **4** | **0** |

All six unsafe audit findings were `very-low`, so the tier identified risk directionally. It was also too broad to save audit work: every ordinary accept had `limited-evidence`; 39/40 had `usage-preference-weak`, and 37/40 had `limited-verifier-agreement`. The three flags together forced 36 cards into `very-low`, including 21 audited good cards. There were no `high` or `low` accepts to calibrate. No tier was changed after seeing the outcomes.

The audit's **six unsafe or unresolved accepts are withheld** from the preview:

| Candidate | Audit finding | Adjudicated action |
| --- | --- | --- |
| `cal2-daily-001:daily-05` — vacuum cleaner, `penyedot debu` / `pembersih vakum` | `should-reject`: possible formal calque and artificial everyday preference | **Withhold** pending usage-preference evidence. DBP does list *pembersih vakum* for “vacuum cleaner,” so dictionary existence does not establish either everyday preference or the auditor's categorical rejection ([DBP vacuum cleaner](https://prpm.dbp.gov.my/Cari1?d=72508&keyword=vacuum)). |
| `cal2-shopping-001:shopping-06` — payment, `pembayaran` / `bayaran` | `should-reject`: cue/sense combines the act and the amount paid | **Withhold**. DBP explicitly distinguishes *pembayaran* as the paying process from *bayaran* as money paid; the current pairing could misteach that distinction ([DBP bayaran](https://prpm.dbp.gov.my/Cari1?d=175768&keyword=Bayaran)). |
| `cal2-social-001:social-04` — to meet someone, `bertemu` / `berjumpa` | `should-reject`: shared normal synonyms create little national contrast | **Withhold**. DBP gives both as Malay equivalents of “meet,” supporting the overlap concern; the proposed country split lacks comparative support ([DBP meet](https://prpm.dbp.gov.my/Cari1?d=175768&keyword=meet)). |
| `cal2-social-001:social-06` — to visit someone, `berkunjung` / `melawat` | `materially-misleading`: broad social cue may hide register/purpose differences and shared *berkunjung* | **Withhold** pending targeted contextual comparison. DBP gives *melawat* several visit senses, so the auditor's narrower sick-visit interpretation is not by itself decisive ([DBP melawat](https://prpm.dbp.gov.my/Cari1?d=73980&keyword=melawat)). |
| `cal2-travel-001:travel-10` — intersection, `persimpangan` / `simpang` | `should-reject`: both forms may be ordinary on both sides | **Withhold** pending comparative-usage evidence; a real preference contrast has not been established by this batch. |
| `cal2-work-001:work-08` — deadline, `tenggat waktu` / `tarikh akhir` | `materially-misleading`: cue says latest *time* while Malay term foregrounds a date; register and shared borrowing remain unresolved | **Withhold** pending cue/preference adjudication. DBP does translate “deadline” as *tarikh akhir* among other choices, which supports meaning but does not settle the everyday contrast ([DBP deadline](https://prpm.dbp.gov.my/cari1?keyword=deadline)). |

The audit's model verdict is retained verbatim in JSON. Withholding is the release recommendation; it does not promote an unproven model accusation into a confirmed linguistic error. This matters particularly for *pembersih vakum*, *melawat*, and *tarikh akhir*, for which official lexical evidence establishes meaning but not the contested preference claim.

### Corrections prepared for safe cards

Ten audited cards had `minor-correction` verdicts. The read-only preview makes **four learner-cue corrections**, **zero target-language answer corrections**, and **six internal-only edits** among those ten:

| Correction class | Candidate IDs | Adjudicated change |
| --- | --- | --- |
| English cue / sense | `daily-03`, `daily-10`, `travel-04`, `work-03` | Narrow to **washbasin**, **to tidy a room**, **traffic congestion**, and **school score**. The first cue is supported by the Indonesian language authority's *wastafel = washbasin* terminology ([Badan Bahasa dictionary](https://badanbahasa.kemendikdasmen.go.id/resource/doc/files/Kamus_Perhotelan.pdf)). |
| Answer | none | Keep the original terms. DBP supports Malay *paip* as a tap and *menggosok* as ironing clothes; the auditor's proposed *pili* and *menggosok baju* were alternatives, not necessary corrections ([DBP paip](https://prpm.dbp.gov.my/Cari1?d=72508&keyword=paip), [DBP menggosok](https://prpm.dbp.gov.my/Cari1?d=73980&keyword=menggosok)). |
| Relation metadata | `shopping-02` | `uang tunai` / `wang tunai` is `similar`, replacing the less precise `different-common-word`. The auditor's proposed cognate label was outside the allowed enum. |
| Internal sense/rationale | `shopping-08` and the other five minor cards | Clarify scope or synonym overlap without adding another model pass. |

Four `confirmed-good` cards also had an inadequate confidence rationale according to the auditor. The preview improves those **four additional internal rationales** (`daily-07`, `social-07`, `travel-01`, `travel-06`). Thus **10 safe cards receive an internal-only edit** when reporting actual applied edits, versus six internal-only `minor-correction` verdicts. Invalid suggested relation labels and slash-separated answer variants remain only in the raw audit artifact. No correction overwrote the original candidate, verifier decision, confidence tier, or audit history.

The [preview](second-batch-50-promotion-preview.json) recommends **34/50 = 68%** of generated candidates as ready for a later guarded promotion check: 32 `different-common-word` and 2 `similar`. It withholds six audited accepts plus four production HOLDs and six production REJECTs. Its deterministic overlap preflight found no duplicate against the 69-card learner source or among ready candidates. It assigns no permanent IDs, writes no learner rows, and does not run a release.

The audit used **8 successful Sol calls plus one failed call**, with 113,145 recorded input tokens, 18,927 output tokens, and 511.070 seconds of recorded call elapsed time. The failed call exposed no token usage. The raw audit timestamp span is 21,360 seconds because the run was interrupted between turns; it is **not** an active-audit runtime. Full active audit wall time, including human source adjudication, is unavailable. There were zero production research calls; later DBP and Badan Bahasa checks were audit-only. Monetary audit cost is unavailable.

## Batch 1 versus Batch 2

All error rates below use the audited provisional accepts as denominator (44 in Batch 1; 40 in Batch 2). The learner-critical proxy counts cards withheld after audit plus corrected target-language answers; it is **not** a confirmed population false-positive estimate. Batch 2's final count is a promotion recommendation, not an actual promotion.

| Measure | Batch 1 | Batch 2 |
| --- | ---: | ---: |
| Generated | 50 | 50 |
| Provisional ACCEPT / HOLD / REJECT | 44 / 2 / 4 | 40 / 4 / 6 |
| Provisional acceptance rate | 88% | 80% |
| Final promoted / recommended ready | 41 promoted | 34 ready, unpromoted |
| Final promotable yield | 82% | 68% |
| Production elapsed | 531.0 s | 282.7 s |
| Provisional ACCEPT decisions per production hour | 298.31 | 509.34 |
| Final promotable cards per original production hour, **audit excluded** | 277.97 | 432.94 |
| Production calls; input + output tokens | 22; 331,739 | 20; 322,451 |
| Calls / total tokens per provisional ACCEPT | 0.50 / 7,540 | 0.50 / 8,061 |
| Learner-critical or unresolved accepted-card findings | 4/44 = 9.1% (3 unsafe + 1 answer edit) | 6/40 = 15.0% (6 withheld + 0 answer edits) |
| Target-language answer corrections | 1/44 = 2.3% | 0/40 = 0% |
| English cue corrections | 1/44 = 2.3% | 4/40 = 10% |
| Internal-only edits actually prepared | 15/44 = 34.1% | 10/40 = 25% |
| HOLD / REJECT rates among generated | 4% / 8% | 8% / 12% |
| No-contrast generation waste | 0% | 8% |
| Confirmed duplicate rejects | 0 | 0 |
| Audit calls; known input + output tokens | 10; 154,374 | 9 attempts (8 success); 132,072 |
| Audit tokens per final promotable/recommended card | 3,765 | 3,884 |

The second production path was faster, but the first run included diagnosis and a verifier repair, and provider latency varied. The observed 509/hour is provisional decision throughput. The 432.94/hour figure is **promotion-adjusted production throughput excluding separate audit and promotion work**; it is not full operational throughput. The audit did not become cheaper per ready card, and learner-cue/unsafe findings rose. These two small batches do not establish a causal quality trend or statistical accuracy. They do show that the specific prompt changes reduced some internal metadata cleanup while leaving cue precision and artificial preferred-form contrasts as material problems.

## Source compatibility and next decision

The canonical learner source and ID ledger hashes are unchanged from before this batch: `4cb9304f5cbbb3d30fe9c931afa43a9ec2083794614994d15e9fac4e418b9ab8` for `data/vocabulary.tsv` and `397318679b919159319b74592d9d955fa9514b97078372a4db10b2bcae52205c` for `curation/id-ledger.json`. Offline validation reports **69 concepts**. The rebuilt `.apkg` contains **69 notes, 69 cards, and 69 unique GUIDs**, exactly matching GUIDs derived from the 69 permanent IDs. The full suite passed **171 tests**; Ruff lint and formatting passed.

**Recommendation:** the **34 preview cards can proceed to a separate guarded promotion** using the explicit corrections and duplicate preflight. Feature 003 is **not yet ready for 100–250-card autonomous batches**. A focused next calibration should address the two observed bottlenecks: (1) one cue must denote one sense, especially act-versus-amount and general-versus-subtype distinctions; (2) the ordinary verifier must treat a shared everyday synonym as a concrete risk when the card asserts a national preference. Confidence rules also need recalibration because generic lack-of-evidence flags placed 90% of accepts in `very-low`, defeating reduced auditing. A future audit policy should be measured against actual tier distribution before another 50-card or larger run. No third batch was started.
