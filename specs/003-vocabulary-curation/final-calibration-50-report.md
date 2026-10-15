# Feature 003: final 50-candidate calibration

This is one new, bounded cohort. Production used the central Luna routes, prompt set
2.4.0, and **decision policy 3.1.0**. The experimental 3.2.0 competing-form
challenge was not called or enabled. All 50 candidate identities, production
responses, attempts, and decisions, plus the 23 selected audit outcomes, are
retained in the linked JSON artifacts.
The canonical learner TSV remains at **103 cards**; this phase made no promotion.

## Fixed Batch 2 routing check before generation

[The routing simulation](final-calibration-batch2-routing.json) read the saved
v3.1 replay and independent audit, with zero new model calls. Four of six known
unsafe/unresolved candidates were still provisional accepts; two were already
HOLD. Mandatory confidence and flag routing selected all four remaining unsafe
accepts. It also selected 5/24 confirmed-good cards, compared with 4/24 in the
previous simulation. Seeded medium/high sampling added three confirmed-good
cards, for 17 total selections. No known unsafe case was missed. The legacy
preference flag was inferred only from recorded `shared_synonym_case` plus a
concrete nonblocking risk; no Batch 2 audit labels informed the rule.

The new verifier records one compact `preference_risk` signal, a named form where
relevant, language, and rationale. v3.1 uses it for confidence and review flags,
without converting it into a production veto. No extra verifier call or
universal evidence retrieval was added. Older candidate records remain valid.

## Fresh production funnel

| Measure | Result |
|---|---:|
| Generated | 50, across food, home, actions, technology, and health |
| Provisional ACCEPT / HOLD / REJECT | 38 / 7 / 5 |
| Early no-contrast rejects | 3 (6% of generated) |
| Confirmed duplicate rejects | 0 |
| Ordinary fast-path accepts / escalated accepts | 38 / 0 |
| Accepted relation distribution | 35 `different-common-word`, 3 `similar` before preview corrections |
| Accepted confidence | 8 high, 24 medium, 6 low, 0 very-low |
| Accepted preference signals | 11 named alternative, 7 shared common form, 6 no concern, 6 regional/register, 6 credible everyday alternative, 1 same-sense competition, 1 different-sense only |
| Evidence retrievals / cache use | 0 / not applicable on this ordinary path |

The seven HOLDs concern concrete weak contrast or cue/sense alignment; all seven
used the escalated decision path without a second model call. The five
REJECTs comprise three no-contrast, one artificial synonym, and one category
versus subtype mismatch. No false-friend candidate reached acceptance, so this
batch does not test the strict false-friend gate.

### Production time and model work

Timing starts before generation and ends after final decisions in
[the production state](final-calibration-50-state.json). Recorded elapsed wall
time was **4,608.1 seconds**, yielding **29.7 provisional ACCEPTs/hour** or
121.3 wall seconds per ACCEPT. This run was interrupted for output repair and
workflow debugging between stages. Thus the observed wall time includes long
orchestration pauses and is **not a clean unattended pipeline-speed benchmark**.
The 25 recorded model calls consumed 475.8 active call seconds; 38 accepts per
active model-call hour would be 287.5, but that is **not end-to-end throughput**.
One generation call took 151.6 seconds. A future clean unattended run is needed
for a comparable wall-clock throughput figure.

Production recorded 5 generation, 5 normalization, and 15 verifier/repair
calls. Five of those verifier calls were schema/semantic repairs. Tokens:
**389,837 input + 31,231 output**; 0.66 calls and about 11,081
total tokens per provisional ACCEPT. The long archive supplied during generation
contributes substantially to input tokens. Provider monetary cost was not
available. Model-output repairs remain inspectable in batch artifacts; no
candidate was regenerated to recover a partial stage.

## Targeted independent audit

[The frozen audit](final-calibration-50-audit.json) selected 23/38 accepts
(60.5%): all low/very-low and strong-flag cards, plus seeded samples of two
unflagged medium and one unflagged high. The audit was a separate Luna role
call, not a universal production gate. Selection reasons are recorded per card.

| Audit verdict | Count |
|---|---:|
| Confirmed good | 17 |
| Minor correction suggested | 3 |
| Materially misleading | 2 |
| Should reject | 1 |
| Should hold | 0 |

The two materially misleading cards were `sedotan / penyedut minuman`
(`drinking straw`) and `printer / pencetak` (`printer`): an English borrowing
is ordinary in Malaysian usage, and presenting the localized term as the
normal everyday answer would overstate the national difference. Both were
routed by register/preference flags. `flashdisk / pemacu kilat` (`flash drive`)
was rejected as an unreliable everyday pairing; it had only a harmless-looking
`named-alternative-exists` signal and was found through random medium sampling.
All three are withheld. [DBP's entry for *straw*](https://prpm.dbp.gov.my/Cari1?d=175768&keyword=straw)
confirms that form's Malay meaning. DBP records *pemacu kilat USB* as a
technical translation, which supports the distinction between term existence
and preferred everyday vocabulary, but alone does not measure preference:
[DBP terminology](https://prpm.dbp.gov.my/Cari1?d=371752&keyword=usb).

The three minor suggestions were one proposed Malaysian answer change and two
metadata/relation cleanups. Approved learner-answer corrections: **0**;
approved English cue corrections: **0**; approved relation corrections from
the audited set: **1**; metadata clarification: **1**. The proposed change
from `beg beli-belah` to
`beg membeli-belah` was **not applied**: the original is attested in
[Malaysian reporting](https://www.bernama.com/bm/news.php?id=2488465), and
[DBP's noun-modifier guidance](https://prpm.dbp.gov.my/Cari1?d=175768&keyword=beli)
supports `beli-belah`; both expressions occur in published Malaysian usage.
For `talenan / papan pemotong`, the preview records the English code-switching
alternative as a metadata note. `deterjen / detergen` is revised from
`different-common-word` to `similar` with a candidate-specific rationale.
Two obvious form-pair relation corrections (`memperbaiki / membaiki` and
`ubin / jubin`) are preview-only editorial changes to unaudited cards and
remain visible for guarded promotion review. No Indonesian answer or English
cue correction was approved in the audited set.

By provisional confidence tier, the audit found: high 1 confirmed good;
medium 12 confirmed good, 2 minor, 2 unsafe; low 4 confirmed good, 1 minor,
1 unsafe; very-low 0. The medium unsafe cases show that confidence alone is
insufficient for routing. These counts are too small to calibrate population
error rates.

Audit cost was **73.8 seconds**, 5 Luna calls, **62,544 input + 7,678 output
tokens**. It is excluded from production throughput. Of the three unsafe
cards, two were selected by deterministic risk routing and one only by seeded
sampling; none escaped this particular audit selection. Seventeen confirmed
good cards were audited. The known signal breakdown is instructive:
`shared-common-form` selected seven audited cards and all seven were confirmed
good; `credible-everyday-alternative` selected six, with five confirmed good
and one minor correction; `regional-or-register-competition` selected six,
including both materially misleading cards. `named-alternative-exists` was
treated as weak, yet one of two sampled examples was the flash-drive reject.
This is a concrete under-routing/over-routing pattern, not a reason to turn
all alternatives into production blockers.

## Guarded promotion preview

[The preview](final-calibration-50-promotion-preview.json) recommends **35**
cards under the sampled-audit policy: 20 audited and cleared, 15 ordinary
accepted cards that were not selected for deep audit. Three audited unsafe
accepts are withheld; seven production HOLDs and five production REJECTs are
also excluded. The preview reports its unevaluated cards explicitly and
checks deterministic overlap against the 103-card source and within the new
cohort. Preview relation distribution after corrections is 29
`different-common-word` and 6 `similar`. No ID was assigned and the learner
TSV was not changed. Preview yield is **35/50 = 70%**, not a promoted yield.

## Three-batch comparison

| Metric | Batch 1 | Batch 2 | Final calibration |
|---|---:|---:|---:|
| Generated | 50 | 50 | 50 |
| Provisional ACCEPT | 44 | 40 | 38 |
| Promoted / preview ready | 41 promoted | 34 promoted | 35 preview ready |
| Yield from generated | 82% | 68% | 70% preview |
| Provisional accepts/hour | 298 | 509 | 29.7 observed wall; interrupted run |
| Audit scope | all 44 | all 40 | targeted 23/38 (60.5%) |
| Audit outcome: good / minor / unsafe | 24 / 17 / 3 | 24 / 10 / 6 | 17 / 3 / 3 in sample |
| Audit tokens | 154,374 recorded | 132,072 recorded | 70,222 recorded |
| Audit tokens per promoted or preview-ready card | 3,765 | 3,884 | 2,006 |

The final batch's 3/23 unsafe audit findings are **sample findings**, not a
corpus-wide error rate. The first two batches used complete audits and are not
directly comparable to the targeted sample for correction percentages.
The final audit found no approved learner-answer or English-cue correction;
one proposed answer change was rejected with source evidence. It did find two
materially misleading preference claims and one additional reject. Audit
token usage per preview-ready card decreased, but the router still selected
most provisional accepts, limiting the hoped-for audit-cost reduction.

## Readiness recommendation: run another focused calibration

The next experiment should specifically improve the **preference-risk
signal and audit router**, while preserving v3.1 acceptance. The signal
`shared-common-form` routed seven safe cards, while the unsafe flash-drive
pair carried only `named-alternative-exists` and depended on random sampling.
This is a defined, reusable failure mode. Five of 25 production model calls
were repairs of malformed verifier output, so the compact signal format also
needs refinement. A smaller routing calibration using
saved artifacts and targeted checks should distinguish an everyday competing
borrowing from a merely existing alternative, and should avoid auditing every
useful shared form. Then a clean unattended timed run can establish comparable
end-to-end throughput. Do not turn these signals into a universal HOLD or
another universal model call.

No empirical expert-human benchmark exists, so no 50× comparison is claimed.
