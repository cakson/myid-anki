# Feature 003: optimistic replay linguistic audit

## Scope and method

This audit covers **all 24 provisional ACCEPTs** in the frozen 26-candidate replay, the remaining pencil HOLD, and the known no-contrast camera REJECT. It generated no candidates, changed no historical decision or policy, and promoted no row to `data/vocabulary.tsv`. Candidate IDs and archived events remain intact. The complete [independent reviewer output](optimistic-audit-model.json) is retained alongside the [provisional replay](optimistic-replay-report.json).

A separate `gpt-5.6-sol` reviewer received candidate fields, archived usage and evidence summaries, and concrete historical objections. It was **not** shown the Luna provisional verdict, confidence tier, or confidence rationale. The audit then inspected all 25 responses against the replay and targeted primary-source lookups for disputed Malay usage. A model judgment alone is not proof of ordinary preference; this is a bounded quality sample, not a production gate or a statistical accuracy estimate.

`confirmed-good` means no correction was found. `needs-correction` identifies an exact cue or metadata change; the pair can remain useful. `should-hold` and `should-reject` would identify a material unresolved issue or affirmative defect in a provisional accept. “Material false positive” means the current learner card should not reasonably be shown in its current form. The audit considers visible learner fields separately from internal curation notes.

## Results

| Measure | Count |
| --- | ---: |
| Provisional ACCEPTs audited | 24 / 24 |
| Confirmed good | 17 |
| Needs correction | 7 |
| Of those, minor cue/metadata corrections | 7 |
| Materially misleading false-positive cards found | 0 |
| Should HOLD | 0 |
| Should REJECT | 0 |
| Other frozen cases inspected | pencil HOLD; camera REJECT |

The seven corrections are mostly to historical alternatives or preference notes, which are **not learner card fields**. The `chat` cue needs semantic tightening before promotion. The independent reviewer agreed with all 24 proposed relation classifications and found no accepted `same` pair. There is no evidence here that the 24 pairs are interchangeable across every context or that this sample establishes a population error rate.

| Provisional tier | Audited | Confirmed good | Needs correction | Should HOLD | Should REJECT |
| --- | ---: | ---: | ---: | ---: | ---: |
| very-low | 5 | 4 | 1 | 0 | 0 |
| low | 6 | 3 | 3 | 0 | 0 |
| medium | 12 | 9 | 3 | 0 | 0 |
| high | 1 | 1 | 0 | 0 | 0 |

The low tier had more corrections (3/6) than medium (3/12), and the one high card was clean. Very-low had fewer corrections (1/5) than low, so the full four-tier ordering is **not demonstrated**. No tier contained a material false positive in this small cohort. The present tiers mainly reflect sparse evidence and historical verifier flags, not measured linguistic error probability. The replay's repeated “independent verifier supports the shared sense” rationale is too generic: it does not say which lexical issue warrants future review. The card-specific audit notes below supply proposed replacement rationales. Confidence changes should be considered in a later metadata update, not silently applied to the frozen replay.

## Card-by-card assessment and rationale corrections

| Candidate ID | Tier | Audit | Specific reason to keep or review |
| --- | --- | --- | --- |
| `clothing-001:clothing-01` | medium | confirmed-good | *Celana/seluar* are natural national defaults for trousers/pants; each can also cover shorter garments, so retain a breadth caveat rather than imply exclusive full-length meaning. |
| `clothing-001:clothing-02` | medium | confirmed-good | *Sepatu/kasut* align for everyday shoes; cross-border recognition of *sepatu* does not remove the normal Malaysian *kasut* contrast. |
| `common-verbs-001:everyday-actions-01` | very-low | confirmed-good | *Kirim/hantar* fit sending an item; Malay *kirim* has narrower/contextual uses. The generic low-evidence flags overstate risk to this specified sense. |
| `communication-001:communication-01` | medium | confirmed-good | *Pesan/mesej* fit a written or digital message; *pesan* also has other senses, which the cue must keep distinct. |
| `communication-001:communication-03` | very-low | needs-correction | *Obrolan/sembang* fit an informal conversation, but the present cue emphasizes text/online chat where shared *chat* is also natural. Narrow the cue; retain a digital-use review flag. |
| `everyday-objects-001:everyday-objects-05` | medium | confirmed-good | *Terong/terung* are standard enough for eggplant and offer a useful spelling contrast; the existence of *terung* in Indonesia does not erase that pattern. |
| `everyday-objects-001:everyday-objects-06` | very-low | confirmed-good | *Semangka/tembikai* are ordinary watermelon terms with a clear lexical contrast; present flags describe missing research rather than an observed linguistic concern. |
| `food-001:foods-01` | medium | confirmed-good | *Makan siang/makan tengah hari* express the midday meal; the shared *makan* supports `similar`, as already established in the archived evidence replay. |
| `food-001:foods-04` | low | needs-correction | *Enak/sedap* are useful defaults, but Malay *enak* is also natural for tasty food. Correct the alternative/preference note rather than claim it is merely recognized. |
| `food-001:foods-06` | low | confirmed-good | *Biskuit/biskut* match the specified small dry baked snack and make a useful spelling contrast; possible cookie/category variation does not defeat the stated sense. |
| `health-001:health-01` | medium | confirmed-good | *Obat/ubat* are neutral medicine terms for the stated treatment sense, including taken or applied substances. |
| `home-001:topic-02` | low | confirmed-good | *Kamar tidur/bilik tidur* naturally denote a bedroom; bare *kamar/bilik* can also work in context, without defeating the phrase contrast. |
| `home-001:topic-03` | low | needs-correction | *Kulkas/peti sejuk* are valid defaults; Malaysian *peti ais* is also common, while *kulkas* should not be listed as an ordinary Malaysian alternative. |
| `home-001:topic-04` | medium | needs-correction | *Jendela/tingkap* are sound defaults; the archived English sense wrongly requires glass. Correct the sense definition. |
| `home-001:topic-05` | medium | confirmed-good | *Tempat sampah/tong sampah* fit a household rubbish bin; cross-border occurrence does not erase the differing usual expressions. |
| `home-001:topic-06` | low | confirmed-good | *Ember/baldi* fit a handled bucket; Malay *timba* is another valid synonym, not a reason to withhold the pair. |
| `home-001:topic-08` | high | confirmed-good | *Kursi/kerusi* give a stable, common spelling contrast for a chair; no material objection was found. |
| `places-001:places-01` | medium | confirmed-good | *Kantor/pejabat* fit an office; Indonesian *pejabat* usually denotes an official, making the national usage contrast especially valuable. |
| `produce-001:produce-03` | very-low | confirmed-good | *Pepaya/betik* are ordinary papaya names; the cue's ripe-fruit restriction is unnecessary but compatible with both terms. |
| `school-001:topic-06` | very-low | confirmed-good | *Penghapus/pemadam* are usable eraser terms in school context; *getah pemadam* is a more explicit Malay variant. |
| `transportation-001:transportation-01` | low | needs-correction | *Mobil/kereta* align for a passenger car; remove broad *kendaraan pribadi* and rare *automobil* from unqualified synonym notes. |
| `transportation-001:transportation-04` | medium | needs-correction | *Bus/bas* give the intended standard spelling contrast; do not present Malay *bus* as an unqualified standard alternative. |
| `transportation-001:transportation-06` | medium | needs-correction | *Truk/lori* align for a goods vehicle; qualify or omit Malay *trak/truk* alternatives and avoid restricting *lori* to very large vehicles. |
| `university-001:university-study-03` | medium | confirmed-good | *Beasiswa/biasiswa* align for educational financial support; their stable spelling contrast is useful, without claiming all grant terms are identical. |

For all 24 cards, the replay rationale should eventually be replaced by the corresponding specific reason above, with the original evidence and objections retained. All 24 current rationales use the same generic template, including the high-tier chair card; none identifies its pair-specific review issue. Review flags should identify the actual residual concern. In particular, `limited-verifier-agreement` appears on cards where an independent verifier did agree; that label describes the historical process poorly and should not be treated as a linguistic objection. Do not remove the historical objection records themselves.

### Exact correction proposals

| Candidate | Proposed change | Severity |
| --- | --- | --- |
| `communication-001:communication-03` | Change English cue from “chat” to **“casual conversation”** and sense to “an informal or relaxed conversation”; note that digital *chat* may be the more idiomatic app term in both languages. Keep `different-common-word`; retain an online-use review flag. | Cue correction before promotion |
| `food-001:foods-04` | Say Malay *enak* is also natural for tasty food; *sedap* remains a characteristic everyday choice. Keep terms and relation. | Curation metadata |
| `home-001:topic-03` | Record Malay *peti ais* as another common term; remove unqualified Malay *kulkas* as an ordinary alternative. Do not claim *peti sejuk* is uniquely preferred. | Curation metadata |
| `home-001:topic-04` | Change internal sense to “opening in a wall or building admitting light or air, usually fitted with glass.” Keep the visible cue “window.” | Internal sense |
| `transportation-001:transportation-01` | Remove or qualify broad Indonesian *kendaraan pribadi*; remove or mark *automobil* rare; do not assert a measured Malaysian recognition rate for *mobil*. | Curation metadata |
| `transportation-001:transportation-04` | Remove Malay *bus* as an unqualified standard alternative; if retained, label it English/code-mixed spelling. | Curation metadata |
| `transportation-001:transportation-06` | Qualify/omit Malay *trak/truk* alternatives; describe *lori* as a goods vehicle without a “very large only” restriction. | Curation metadata |

The reviewer marked seven accepted cards `needs-correction`; the eighth `needs-correction` result in the machine-readable output is the separately inspected pencil HOLD. The machine-readable reviewer output retains the complete proposed field map.

## Required diagnostic cases

| English → Indonesian / Malaysian | Relation | Provisional tier | Verdict | Linguistic reason and action |
| --- | --- | --- | --- | --- |
| trousers → *celana / seluar* | different-common-word | medium | confirmed-good | Both are natural broad garment words; full-length specificity may require *panjang*. No pair correction. |
| biscuit → *biskuit / biskut* | similar | low | confirmed-good | Forms match the stated dry baked-snack sense; maintain the spelling contrast. |
| refrigerator → *kulkas / peti sejuk* | different-common-word | low | needs-correction | Pair is valid; qualify *peti ais* as another Malaysian term and remove misleading unqualified Malay *kulkas* metadata. |
| car → *mobil / kereta* | different-common-word | low | needs-correction | Pair is valid; clean up broader/rare synonyms in curation notes. |
| scholarship → *beasiswa / biasiswa* | similar | medium | confirmed-good | Both mean educational financial support and differ in useful form. |

The authoritative Malay [DBP entry for *peti sejuk*](https://prpm.dbp.gov.my/Cari1?d=371752&keyword=peti+sejuk) confirms the refrigerator meaning, while a [DBP entry also records *peti ais*](https://prpm.dbp.gov.my/Cari1?d=73980&keyword=penyejuk). The [DBP *kereta* entry](https://prpm.dbp.gov.my/Cari1?d=175768&keyword=kereta) includes passenger-car uses. The [DBP *biskut* entry](https://prpm.dbp.gov.my/Cari1?d=274052&keyword=biskut) fits the dry baked-snack sense. These dictionary entries establish meaning and recognized use, not measured preference frequency.

### Pencil HOLD and camera REJECT

**Pencil → *pensil / pensel*** remains a historical HOLD in the replay; this audit does not silently convert it. The objection that Malaysian *pensil* may also occur is **not a material blocker** to learning the standard *pensel* contrast. DBP explicitly answers that the correct Malaysian spelling is [*pensel*](https://prpm.dbp.gov.my/Cari1?d=175768&keyword=pensil), and its [lexical entry](https://prpm.dbp.gov.my/Cari1?d=371752&keyword=Pensel) defines the pencil sense. The independent reviewer reached the same conclusion. The next controlled reconsideration should assess ACCEPT with a suitable confidence tier, retaining a variant note if useful; the decision is unchanged in this audit phase.

**Camera → *kamera / kamera*** remains the valid early no-contrast REJECT. It was not sent through this costly audit, because identical ordinary forms have no learning contrast and the prior replay already rejected it before new verification. This is a scope rejection, not a translation error.

## Systematic findings and confidence calibration

1. **Visible pairs were stronger than their archived metadata.** Six of the seven accepted-card corrections affect internal usage, alternatives, or sense notes; only `chat` changes the learner-facing cue. The old pipeline's objections to another valid synonym often confused “not the only valid form” with “wrong answer.”
2. **The rationale template is not sufficiently explanatory.** It repeats verifier agreement and flags without naming the relevant word or ambiguity. The card-specific reasons above are better review rationales.
3. **The confidence ordering is only weakly directional.** Low had more cleanup than medium and high, but very-low did not have the highest correction rate. Sparse evidence and historical process flags were sometimes mistaken for linguistic risk. This cohort is too small to recalibrate tier boundaries or infer an error probability. Do not change the policy in this phase.
4. **No material false positive was found in this audit.** The `chat` cue is the closest issue: its “especially by text or online” sense blurs a shared digital loanword with the useful informal-conversation contrast. Tighten the cue before learners see it. A [DBP entry](https://prpm.dbp.gov.my/Cari1?d=371752&keyword=sembang) supports *sembang* for conversation and also recognizes online chat contexts; the audit does not claim that all online contexts prefer it.
5. **The pencil HOLD looks overcautious.** DBP's explicit spelling guidance resolves the named objection better than another generic model hesitation would.

## Audit work and throughput interpretation

| Audit-only metric | Recorded value |
| --- | ---: |
| Independent stronger-model calls | 5 batched calls |
| Automated audit run wall time | 213.820 seconds |
| Provider-reported input tokens | 83,608 |
| Provider-reported output tokens | 8,734 |
| Model retries / failed calls | 0 / 0 |
| Targeted external search queries | 15 across 4 web search calls |
| Direct page opens | 0 |
| Full manual-inspection and report-authoring elapsed time | Not instrumented |
| Monetary model/research cost | Unavailable |

The **907.7 provisional accepted decisions per active replay hour** remains a fast-path decision benchmark, not end-to-end corpus throughput. This audit is separate periodic quality work. Neither its 213.820 seconds nor the earlier historical research belongs automatically in the per-card production fast path. Canonical learner-card throughput for the frozen replay remains zero until guarded promotion actually happens.

## Recommendation and boundary

The optimistic policy appears **safe enough to continue to a guarded promotion preparation step** for this small ordinary-vocabulary cohort: all 24 displayed Indonesian/Malaysian pairs survived independent review, and none was found clearly misleading enough to HOLD or REJECT. **Do not promote the 24 as-is.** Correct the `chat` cue first, attach the six other exact metadata/sense corrections, and ensure promotion validates only accepted contrastive relations and permanent IDs. Keep the original decisions and audit provenance available for comparison. Reconsider the pencil HOLD in a separate bounded decision replay. Future audits should sample across all confidence tiers and compare actual learner corrections; this audit does not establish that the current confidence tiers are calibrated.
