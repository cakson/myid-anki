# Technical borrowing signal: retrospective and bounded prospective test

## Scope and implementation

Production acceptance policy **v3.1 remains unchanged**. The experimental competing-form challenge is still disabled. `technical-borrowing-risk` is a deterministic, pre-audit lexical signal: a `different-common-word` ACCEPT with a technology tag, a modern technical sense, and a localized multiword answer (with a shared component if both answers are compounds). It adds a reason to the existing targeted preference-evidence branch and to audit routing. It never changes ACCEPT to HOLD by itself and adds no model call. The rule uses no known failed cue or answer as a special case. [Implementation](../../src/indo_malay_anki/curation/technical_borrowing_risk.py), [tests](../../tests/unit/test_technical_borrowing_risk.py).

This narrow pattern was chosen after checking audited-good counterexamples: localized technical forms for **software** and **hardware** are usable. Mere technology membership or foreign origin must not route every technical card.

## Retrospective evaluation

The [frozen retrospective artifact](technical-borrowing-retrospective.json) covers 160 historical fresh-batch ACCEPTs, 135 with independent audit labels. The trigger selects **4/160 ACCEPTs**, all audited, including four of 15 technology-tagged ACCEPTs:

| Candidate | Existing preference trigger | New technical trigger | Independent audit | Interpretation |
|---|---|---|---|---|
| flash drive | yes | yes | should-reject | Localized answer was unsafe; revised router selects it deterministically. |
| cloud storage | no | yes | minor-correction; guarded preview withheld | New coverage for the intended failure class, though the independent label is not a critical reject. |
| software | yes | yes | confirmed-good | False route; localized term remains useful. |
| hardware | yes | yes | confirmed-good | False route; localized term remains useful. |

Overlap across 160: both mechanisms 3, existing only 36, technical only 1, neither 120. For **critical** independent labels, the trigger's observed precision is 1/4. Counting the cloud-storage review concern gives 2/4 review-relevant triggers. These are descriptive counts, not population estimates.

The existing explainable router selects 106/160 ACCEPTs (66.3%); adding the technical signal selects 110/160 (68.8%). Batch-specific before/after counts are 22/22 (Batch 1), 37/37 (Batch 2), 23/26 (Batch 3), and 24/25 (prospective Batch 4). The extra routes include flash drive, two audited-good technical counterexamples, and cloud storage moving from random to deterministic selection; fixed-hash resampling also selects one deferred health card. The trigger was designed with known historical examples, so the retrospective is **not held-out predictive validation**. The 25-candidate run below is the bounded prospective check. Random sampling remains enabled.

Source type alone cannot distinguish standard terms from everyday preference. Dictionary or official terminology establishes existence or meaning; current product-facing and ordinary usage can inform everyday choice, but a single example does not establish relative frequency. The previous historical artifacts lack enough source-role evidence for a stronger retrospective claim.

## Prospective 25-candidate production

Exactly 25 new candidates were generated in five five-candidate groups across food, home, actions, technology/work, and health. The [state](technical-borrowing-25-state.json) preserves generation, normalization, verification, decisions, model attempts, and candidate IDs. None came from historical HOLD replay. The canonical source remained at 127 cards.

| Production outcome | Count |
|---|---:|
| Generated | 25 |
| Provisional ACCEPT | 22 |
| HOLD | 3 |
| REJECT, including no-contrast/duplicate | 0 |
| Ordinary fast-path ACCEPT | 22 |
| Technical-borrowing trigger | 1 |
| Existing preference trigger or technical trigger | 12 |
| New trigger only | 0 |

Accepted relations: 21 `different-common-word`, one `similar`. Accepted confidence: two high, 19 medium, one low, zero very-low. The single technical trigger was **database → basis data / pangkalan data**; the existing localized-standard preference trigger already selected it. Thus this prospective sample demonstrates a selective trigger but **no incremental evidence coverage**.

The 12 targeted [evidence records](technical-borrowing-25-evidence.json) contain 12 source observations with claim roles and provenance: three `low-concern`, nine `review-worthy`, zero `material-blocker`. Zero cache hits and 12 cache misses were recorded. The lookup was bounded; these records do not purport to measure comparative frequency. They were attached via the existing [research manifest](technical-borrowing-25-research-manifest.json). No ACCEPT was converted to HOLD solely for absent frequency evidence.

The recorded start-to-finish wall interval is **30,286 seconds**, including a long interrupted/idle gap between operations. Consequently its 2.6 provisional ACCEPTs/hour is **not a representative processing-speed benchmark**. The 16 recorded model attempts (15 successful, one transient CLI failure followed by a bounded successful retry) consumed 176.8 seconds of model-call wall time, 287,154 recorded input tokens and 16,544 output tokens. Successful calls comprise five generation, five normalization, and five independent verification calls. Targeted research comprises 12 candidate lookups in batched web research; reliable per-lookup elapsed time and monetary cost were unavailable. The ordinary 13 candidates needed no targeted preference lookup. The feature itself added **zero** calls and **zero** unique targeted lookups over the existing trigger in this run.

## Independent audit and quality

The [targeted and fixed-hash random audit](technical-borrowing-25-audit.json) selected 15/22 ACCEPTs (68.2%). Three were selected solely by stratified random sampling. The separate audit took 64.7 seconds in three Luna calls, with 41,155 input and 6,212 output tokens. It is excluded from production call/time counts.

| Audit verdict | Count | Action |
|---|---:|---|
| confirmed-good | 9 | Independently cleared. |
| minor-correction | 1 | Correct confidence rationale and internal note in read-only preview. |
| materially-misleading | 2 | Withhold. |
| should-hold | 3 | Withhold. |

The two materially misleading cards were **socks → kaus kaki / stoking** (ordinary Malaysian socks should not be taught as *stoking*, which can suggest stockings) and **pajamas → piyama / baju tidur** (specific pajamas versus broader sleepwear, with borrowed *pijama/pyjama* also competing). Socks was found **only by random sampling**; pajamas had structured review flags. The three HOLD cases were bandage, spreadsheet, and job training: the independent auditor identified unresolved everyday-preference or sense claims. Four of five audited unsafe/unresolved cards were routed through structured risk signals, one through random sampling. This is observed coverage among audited cards; the seven unaudited ACCEPTs have unknown independent outcomes.

The database card was the sole prospective technical trigger. Audit found its localized technical forms valid and requested only a candidate-specific rationale and internal note acknowledging that borrowed **database** may be familiar in workplaces. That change appears in the [read-only promotion preview](technical-borrowing-25-promotion-preview.json); learner answers are unchanged. The new source-role record improved explanation, but did not newly identify an unsafe card.

### Promotion recommendation

Ten new cards are independently cleared, including database after the metadata-only preview correction. Five audited cards are withheld. Seven ACCEPTs remain unaudited and are only conditionally eligible under the declared stratified sampling policy; they are **not** described as independently cleared. The preview assigns no permanent IDs and makes no canonical TSV change. A future guarded promotion may include the ten cleared cards and, if the project accepts the routine sampling policy, the seven remaining provisional cards after duplicate/identity checks. This phase makes **no promotion**; the deck remains **127 cards**.

For the older prospective batch, the revised simulation newly selected `pros4-health-001:health-09` (disabled person) through fixed-hash sampling. Its [audit](technical-borrowing-deferred-audit.json) found a metadata-only register qualification. The random backstop then selected two of the other 13 deferred candidates, **to stir food** and **doormat**; both were confirmed-good in [separate audit](technical-borrowing-deferred-random-audit.json). Eleven deferred cards remain unaudited and unpromoted. None of these older cards was promoted.

## Readiness decision

**Do not start the 100-card autonomous batch yet.** The heuristic is selective and cheap, and it captures the historical cloud-storage blind spot in principle. The prospective sample did not show unique evidence coverage, while 5/15 selected ACCEPTs were unsafe or unresolved, including a learner-answer error found only randomly. Audit workload remains high at 68% of provisional accepts. The specific remaining issue is **answer/sense and everyday-preference precision in ordinary `different-common-word` generation and verification**, rather than an absence of another universal evidence stage. The next focused change should improve that cheap first-pass precision and reduce noisy audit routing, then measure it on a bounded new corpus. Keep v3.1, the strict false-friend gate, targeted evidence, and the random backstop.

Validation: 196 tests passed; Ruff passed on changed code; offline source validation found 127 concepts; offline build produced 127 notes and 127 cards. No canonical learner row or permanent identity changed.
