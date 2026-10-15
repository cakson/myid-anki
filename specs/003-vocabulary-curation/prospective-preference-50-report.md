# Feature 003: prospective preference-evidence experiment

Date: 2026-10-15 (Asia/Tokyo). This is one bounded, new 50-candidate batch. The canonical learner TSV remains at **127 cards**; the 11 earlier deferred cards remain unpromoted. Production policy v3.1 and the disabled competing-form challenge were not changed.

## Method and artifacts

The frozen candidate and v3.1 decision record is [`prospective-preference-50-state.json`](prospective-preference-50-state.json). [`prospective-preference-50-research-manifest.json`](prospective-preference-50-research-manifest.json) records the pre-research trigger selection; [`prospective-preference-50-evidence.json`](prospective-preference-50-evidence.json) records source-role observations for the triggered cases. The enriched decisions, independent audit, and read-only promotion preview are separate artifacts. Candidate references retain their `pros4-*` batch IDs. No historical artifact was retrofitted.

The trigger only selects provisional ACCEPTs with a concrete everyday-preference signal or localized/borrowed competition. Ordinary `similar` spelling contrasts and candidates with only speculative or weak alternatives do not require research. The trigger was refined from an initial 24/50 broad selection to **16/50** before source research or audit labels were available; the initial manifest remains archived. The selected candidates all have `different-common-word` relations. Existing evidence cache had 112 facts but **0 exact language/form/sense matches** for these 16, so there were 16 misses. The evidence record distinguishes dictionaries, government/education, mainstream reporting, and product-facing language, and separates meaning from usage. A dictionary entry cannot be tagged as proof of ordinary usage or relative preference.

The frozen enriched-state artifact used an overly broad `borrowed-form-competition` flag for all review-worthy evidence, including nonborrowed synonyms. This was corrected in the evidence finalizer after the audit: review-worthy evidence now receives `preference-uncertainty`, while `borrowed-form-competition` requires an explicit borrowed-form classification. The archived audit retains the original input and must be interpreted as an experiment, not as proof that the borrowed-form flag itself was predictive. The correction does not change v3.1 acceptance or the 24-card audit selection because the general preference-uncertainty flag is also a strong audit route. No linguistic re-audit was spent on a label-only correction.

The bounded source lookup used web research because shell network DNS was unavailable in this environment. It was a supervised curation operation, not a fully autonomous retrieval benchmark. Ten search batches (approximately 40 queries), six recorded batched page-inspection operations, and 16 candidate-level research outcomes were recorded. The 18 source observations comprise 8 commercial/product-facing, 5 government/educational, 4 mainstream-publication, and 1 official-dictionary record. Tool token and monetary accounting is unavailable. Source observations and URLs remain in the evidence JSON for inspection. A small number of observations rely on indexed page excerpts where full pages could not be opened; those establish at most the quoted use, not relative preference. The experiment made **zero additional Luna calls for evidence retrieval**. This does not mean research had zero human or tool cost.

## Production funnel and cost

| Measure | Result |
|---|---:|
| New generated candidates | 50 |
| v3.1 ACCEPT / HOLD / REJECT | 38 / 4 / 8 |
| Ordinary fast-path accepts | 38 |
| Escalated accepts | 0 |
| Accepted relation distribution | 36 `different-common-word`, 2 `similar`, 0 `false-friend` |
| Accepted confidence distribution | 12 high, 18 medium, 8 low, 0 very-low |
| No-contrast / duplicate / other rejects | 3 / 2 / 3 |
| Preference-evidence triggers | 16/50 (32%); 16/38 provisional accepts (42%) |
| Source-role conclusions | 4 low-concern, 12 review-worthy, 0 material-blocker |
| Model calls | 24 Luna calls: 5 generation, 5 normalization, 14 verification |
| Production model tokens | 393,455 input; 32,119 output |
| v3.1 generation-to-decision elapsed | 383.2 seconds; 357 provisional accepts/hour |
| Supervised targeted research window | 274.8 seconds, approximately 17.2 seconds/trigger |
| Generation-to-evidence completion wall time | 721.1 seconds; 190 provisional accepts/hour including supervised research and orchestration gap |

The 383-second figure is the reusable automated decision benchmark. The 721-second figure includes this experiment's supervised research, with a roughly 63-second gap between the frozen decision and evidence-research windows; it is **not** evidence of autonomous end-to-end throughput. Provider monetary cost is unavailable. A 100-card scaling claim cannot be made from this supervised evidence collection.

The failed competing-form challenge added 12 Luna calls, about 143 seconds, and 164,171 tokens for 12 challenged candidates, with no additional unsafe card caught. This experiment added no Luna evidence calls but selected 16 candidates and consumed about 275 seconds of supervised research. It therefore supplied source-role information, but has **not** established a cheaper autonomous replacement for the challenge.

## What the source roles showed

| Candidate | Inspected source mix and bounded conclusion | Audit consequence |
|---|---|---|
| `blender / pengisar` | A Malaysian [appliance listing](https://www.snfonline.com.my/products/midea-pengisar-power-blender-mbl100dhbgg) uses both terms. `pengisar` is product-facing, while borrowed `blender` competes. | Routed; minor metadata qualification, no answer change. |
| `menyiram toilet / mengepam tandas` | Malaysian [municipal rules](https://www.mbpg.gov.my/sites/default/files/uuk_tandas_awam_mppg_page_7.pdf) use `mengepam`; a [plumbing business](https://www.plumbingservices.my/ms/post/servis-baiki-flush-tandas-rosak-di-kuala-lumpur-2026-pantas-berkualiti) uses borrowed `flush tandas`. Official use establishes meaning, not everyday preference. | Routed by new evidence flag; minor metadata qualification. |
| `menopause / putus haid` | A Malaysian [university health source](https://care.upm.edu.my/kandungan/rawatan_kanser_payudara-26820%20%20?L=bm) relates `menopaus` and `putus haid`. | Routed; minor nonexclusive-usage note. |
| `merek / jenama` | A Malaysian [mainstream retail article](https://www.sinarharian.com.my/article/114657/house-brand-pilihan-utama-pengguna) repeatedly uses `jenama`; borrowed `house brand` does not displace it. | Confirmed good: useful counterexample to a blanket localized-term warning. |
| `notifikasi / pemberitahuan` | Malaysian [app support](https://help.shopee.com.my/portal/4/article/155934-%5BNotifikasi%5D-Kenapa-saya-tidak-menerima-pemberitahuan-tolak-%28Push-Notification%29-daripada-aplikasi-Shopee) uses both in one title. | Routed; audit called it a minor relation issue, but guarded preview withholds it because the national preference contrast remains unclear. |
| `penyimpanan awan / storan awan` | **No trigger fired**: verifier said there was no concrete competitor. The independent audit, reached by stratified sampling, noted common borrowed `cloud` in Indonesian use. | Withheld for a targeted usage check. This is the key localized/borrowed blind spot of this experiment. |

Source type was useful for interpreting the *strength* of a claim. It did not itself establish relative frequency. Product-facing coexistence of localized and borrowed forms is a review signal, not an automatic HOLD. The prospective batch did not include an independently confirmed unsafe localized-versus-borrowed card whose release was newly prevented by this evidence. The hypothesis is therefore **not validated** as a production safety improvement. In particular, the cloud-storage case shows that a verifier-only trigger can miss a relevant localized coinage.

## Targeted and random audit

The explainable router selected **24/38 provisional accepts (63%)**: 21 via confidence or concrete risk/evidence flags and 3 via fixed-hash stratified random sampling. All 16 evidence-triggered cards were selected, but only **2** were selected solely because of new evidence flags; existing flags already routed the others. Fourteen provisional accepts remain unaudited. The 24 independent Luna audits took **108.2 seconds**, 5 model calls, 265,139 input tokens, and 10,451 output tokens. Audit cost is separate from the production figures above. This selection rate is slightly above the preceding calibration's 23/38 (61%), so audit workload did **not** materially improve.

Raw audit outcomes: 7 confirmed good, 14 minor correction, 2 materially misleading, 1 should-HOLD. The three unsafe/unresolved cases were routed by existing production signals, not newly by source-role evidence: `chopsticks` (regional/register flag), `measuring cup` (credible competing form), and `vocational training` (low confidence/cue correction). None was found only randomly in this sample. Random sampling remains necessary because it found the cloud-storage concern and because 14 accepts were not deep-audited. No claim about the unseen 14 is possible.

The measuring-cup audit deserves explicit adjudication. The auditor considered Indonesian `gelas ukur` unsafe for everyday cooking, but an Indonesian [retail guide](https://azko.id/en/inspiration/gelas-takar) explicitly calls `gelas takar` also `gelas ukur`, and an [IKEA Indonesia cooking product](https://www.ikea.co.id/in/produk/peralatan-memasak/peralatan-memanggang/vardagen-art-10323306) uses `gelas ukur` for cooking. The raw audit result is preserved, while promotion is withheld pending resolution. Conversely, Malaysian `penyepit makanan` is also used for [food tongs](https://shopee.com.my/list/penyepit/makanan), supporting the chopsticks HOLD.

## Guarded promotion recommendation

[`prospective-preference-50-promotion-preview.json`](prospective-preference-50-promotion-preview.json) is read-only and does not allocate permanent IDs. It records candidate-level audit verdicts, straightforward corrections, and withheld reasons.

- **18** audited cards are clear after approved corrections: 7 confirmed good and 11 minor corrections. Among the 11, one learner-answer correction changes Malaysian refund to `bayaran balik`, two narrow internal senses, and eight add nonexclusive-usage metadata. Parenthetical synonym suggestions were retained as metadata rather than inserted into Anki answers; an audit suggestion for an unsupported relation value was not applied.
- **14** additional provisional accepts were outside the targeted/random deep-audit selection. They are *not* labeled independently confirmed good. They are conditionally eligible under the sampled-audit process, subject to normal duplicate/source validation at actual promotion.
- **6** are withheld: the three raw unsafe/unresolved audits, plus cloud storage, app notification, and résumé due remaining practical-preference or sense concerns. The résumé case is especially sensitive because Indonesian [Prakerja guidance](https://www.prakerja.go.id/artikel/insight/panduan-lengkap-membuat-curriculum-vitae-cv-untuk-segala-kebutuhan) distinguishes CV and résumé while also using `daftar riwayat hidup`.

Thus **32/38** have a conditional promotion path, including 14 not deep-audited. This is not a promotion or a claim that all 32 are error-free. The canonical deck remains 127 cards, and the 11 historical deferred cards remain untouched.

## Readiness decision

**Do not start the 100-card autonomous batch yet.** This experiment preserved the fast v3.1 path and made source-role evidence inspectable, but it did not demonstrate incremental unsafe-card capture, still routed 63% of accepts to deep audit, required supervised external research, and missed the cloud-storage localized/borrowed concern at trigger time. The specific remaining failure mode is a translated technical term whose verifier names no borrowing competitor even though common borrowed usage may matter. The next focused change should make that candidate class discoverable with a cheap, generalizable *pre-audit trigger*, then test it prospectively with actual source retrieval and audit workload measurement. Keep random sampling and keep v3.1 acceptance unchanged.

Validation: the canonical source validated at 127 concepts; the offline build produced 127 notes and 127 cards; the full test suite passed (192 tests); Ruff lint and formatting pass for the new code. No 100-card batch, learner-source promotion, or historical backlog clearance occurred.
