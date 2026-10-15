# Feature 003: cross-batch audit-router calibration

Production decision policy remains **3.1.0**. The experimental competing-form
challenge remains disabled. No candidates were generated and no production
ACCEPT/HOLD/REJECT decisions were changed. This phase evaluated post-ACCEPT
audit routing and promoted only cards independently audited as safe.

## Read-only calibration cohort

[The machine-readable cohort and simulations](audit-router-calibration.json)
contain all **122 fresh-batch production ACCEPTs**: 44 from Batch 1, 40 from
Batch 2, and 38 from final calibration. Independent audit labels are known for
109: **65 confirmed safe, 32 correctable but publishable, and 12 critical**.
The remaining 13 final-batch ACCEPTs are explicitly unlabeled. Their missing
audit result is not counted as safe. Batch 1 uses both its original and
completion audit artifacts. Each record keeps its original, richer audit
verdict separately from this three-way routing label.

`production_features` are extracted only from frozen production decisions:
relation, confidence, verifier result and concerns, cue and synonym fields
where present, preference signal and named form where present, review flags,
evidence/risk path, and answer-form equality. Labels are joined afterward.
Batch 1 and Batch 2 did **not** emit the structured `preference_risk` field;
their missing field is recorded as unavailable, never as a no-concern signal.
Later Batch 2 replay outputs are excluded from primary features because they
were produced after the original decision, even though their prompts hid the
independent audit. This prevents post-audit feature leakage.

## Random-only critical case

`cal3-technology-001:technology-05`, **flash drive → `flashdisk` /
`pemacu kilat`**, passed the v3.1 fast path at medium confidence. The verifier
called `pemacu kilat` a Malaysian *standard* term and recorded `flash drive`
as a merely named alternative in both varieties. It supplied no concrete
regional/register or everyday-preference flag. The independent audit found
that the proposed localized term is an unreliable *everyday* Malaysian
default for this concept, so the national preference claim would mislead.
This is a **preferred-everyday-form versus formal/localized-term** failure,
amplified by verifier overconfidence about the English borrowing. The cue
and semantic meaning themselves were not the reported problem.

A reusable *candidate* audit flag would ask whether a
`different-common-word` card presents a localized/standard term as the
everyday default while naming a borrowed, same-sense Malaysian alternative.
One audited critical example matches that pattern, but several still-unaudited
final-batch candidates contain similar wording. Enabling a text proxy now
would be outcome-aware overfitting. The [candidate signal in the calibration
artifact](audit-router-calibration.json) is therefore **diagnostic only**;
it does not change v3.1 or the chosen router. Random sampling remains needed
to find mistakes that the verifier fails to flag.

## Observed signal value

All rates below are **within the audited subset**, subject to targeted-audit
selection bias and small counts. They are not population error estimates.

| Production-time signal | Audited carriers | Critical | Confirmed safe | Correctable | Observed critical precision |
|---|---:|---:|---:|---:|---:|
| Very-low confidence | 54 | 9 | 26 | 19 | 16.7% |
| Verifier concern | 59 | 9 | 31 | 19 | 15.3% |
| Generic limited evidence | 84 | 9 | 48 | 27 | 10.7% |
| Regional/register risk | 6 | 2 | 3 | 1 | 33.3% |
| Shared common form | 7 | 0 | 7 | 0 | 0% |
| Credible competing form | 7 | 0 | 5 | 2 | 0% |
| Named alternative exists | 2 | 1 | 0 | 1 | 50%, highly selected |
| Low confidence | 6 | 1 | 4 | 1 | 16.7% |

Legacy `very-low`, generic limited evidence, and verifier concern overlap
heavily: all 54 audited `very-low` cards also had the other two signals.
Those fields cannot be counted as three independent warnings. Regional/register
risk contributed one critical case not already carried by another listed
signal. `shared-common-form` is noisy in this sample; its seven audited
carriers were all confirmed safe. `credible-competing-form` found no critical
case among seven audited carriers. This is reason to make them conditional
audit signals, not to remove the underlying provenance. Cue risk and relation
instability have too few observed examples for a useful ranking.

## Explainable policy comparison

The simulation uses a fixed hash salt to sample otherwise-clean cards: 10%
of high-confidence cards and 15% of other confidence tiers, rounded up
within each batch/tier. This is a modest *safety sample*, not a promise of
deterministic detection. Sampling is not tuned to make the known flash-drive
case appear selected; with this fixed salt it is **missed**.

- **A, confidence-heavy:** all low/very-low; random medium/high.
- **B, confidence plus broad flags:** A plus all previously designated strong
  semantic, preference, shared-form, and regional/register flags.
- **C, risk-first:** low cards, very-low cards with a verifier concern, and
  concrete cue/relation/regional/preference flags. The observed noisy
  `shared-common-form` and `credible-competing-form` flags alone do not force
  deep audit. Random sampling covers every remaining tier.

| Fixed policy | Batch 1 audits / 44 | Batch 2 audits / 40 | Final audits / 38 | Pooled audits / 122 | Known critical caught |
|---|---:|---:|---:|---:|---:|
| A | 22 | 37 | 11 | 70 (57.4%) | 10/12 |
| B | 22 | 37 | 23 | 82 (67.2%) | 11/12 |
| C | 22 | 37 | 14 | 73 (59.8%) | 11/12 |

For the final batch alone, C routes **10 deterministic + 4 random = 14/38
(36.8%)**, compared with the earlier 23/38 (60.5%) targeted audit. It
deterministically routes the drinking-straw and printer critical cases and
misses the flash-drive case under the fixed random draw. Among its routed
final-batch cards, nine independently audited cards are confirmed good.
The flash-drive card is an otherwise-clean medium card; a 15% medium sample
has about a **15% inclusion chance** for any one such card, not guaranteed
capture. Increasing the clean-card sample to 20% would improve that chance
to about 20% while raising the final-batch audit workload from roughly
14/38 to 16/38; 10% would yield about 13/38 but less residual protection.
The 10% high / 15% other-tier rule is a transparent middle choice, not a
calibrated error-probability guarantee.

The first two batches retain costly legacy confidence behavior. Policy C
would audit 22/44 in Batch 1 and **37/40 in Batch 2** because 36 Batch 2
cards were originally `very-low` with verifier concerns. These figures
should not be used to claim that the new structured router works cheaply
on old schemas.

### Batch-separated check

The calibration script selects a policy using the other two batches' labels
and evaluates it on the held-out batch. The train-only utility rewards a
known critical catch and charges for each audit. It selects C when holding
out Batch 1 or Batch 2, where all known critical cases are routed but Batch
2 still requires 37/40 audits. It selects **A** when holding out the final
batch; A audits 11/38 and misses both medium-confidence critical cases.
Thus pooled fit is more reassuring than held-out behavior. The policy family
was developed with knowledge of these batches, so this is an exploratory
stability check rather than unbiased prospective validation. The final batch
also has 13 unknown labels, making its measured recall a lower-information
partial outcome.

### Audit-budget estimate

At a crude constant-tokens-per-card assumption, C would use half of Batch
1's full-audit workload, about **77k versus 154,374** recorded audit tokens.
For Batch 2 it would use about **122k versus 132,072**, only a 7.5% reduction.
For the final batch, using the first audit's 70,222 tokens over 23 cards as
a rough unit cost, C's 14 selections project about **43k tokens**, versus
70,222 tokens already spent on 23 and about 116k for an extrapolated full
38-card audit. Batching and candidate complexity make these estimates
approximate; the historical audit tokens cannot be undone. The realistic
20–40% routine-audit range appears possible for current structured
vocabulary, but **not established across all three schema generations**.

## Final-batch additional audit and guarded promotion

Under C's frozen routing and random rule, two previously unaudited cards
were newly selected: `cal3-actions-001:actions-04` and
`cal3-food-001:food-04`. [The supplemental independent Luna audit](final-calibration-router-supplement-audit.json)
found both publishable with metadata-only corrections. The repair pair's
confidence rationale now explains cross-variety overlap, retaining the
production relation also chosen by the independent auditor. The ladle card
has an unsupported alternate-form flag removed. No learner answer or cue
changed. The additional audit required **one Luna call, 13.75 seconds,
12,960 input tokens, and 1,052 output tokens**. These costs are reported
separately from all production throughput metrics.

The prior 23-card audit and this two-card supplement provide 25 independent
audit outcomes for the final batch: 17 confirmed good, five minor and safe
after metadata adjudication, and three critical withheld. The remaining
**13 ACCEPTs have no deep-audit label**; C did not select them. The original
35-card read-only preview remains archived. The [new guarded preview](final-calibration-50-guarded-preview.json)
splits it into **22 audited-and-cleared**, **13 deferred unaudited**, and
**three audited unsafe**. This intentionally avoids treating unsampled cards
as audited-good.

The 22 cleared cards were promoted through an atomic learner-source and
permanent-ID transaction. [The promotion record](../../curation/promotions/final-calibration-50.json)
retains original production and audit references, original candidates,
approved corrections, final relation, confidence, IDs, and the excluded
candidates. The canonical deck grew from **103 to 125** cards. The 13
deferred candidates retain their original batch identities and can be
reconsidered later without regeneration. The three audited unsafe cards,
seven production HOLDs, and five production REJECTs were not promoted.

Source validation passed for 125 concepts. The offline `.apkg` build has
125 notes and 125 cards, 125 unique GUIDs derived from permanent IDs, and
the established deck/note-model IDs. The full test suite passed **184 tests**,
and Ruff passed. No normal build step made AI or research calls.

## Readiness decision

**Do not start a 100-card autonomous batch yet.** The remaining systematic
failure mode is the verifier's tendency to describe a localized standard
term as an everyday national preference while downgrading a common
English-based same-sense alternative to a harmless named synonym. One such
card was found only by random audit; the current fixed risk-first sample
would miss it. Moreover, batch-separated selection chose the cheap
confidence-heavy rule for the final batch and missed two known medium-risk
cards, while older schemas still imply near-full Batch 2 audit.

The next focused test should validate a *structured standard-versus-everyday
borrowing* review signal on the 13 deferred cards and other saved candidates,
without changing v3.1 acceptance, adding a universal model call, or
generating new vocabulary. Only after that signal and the random backstop
show stable held-out routing cost and catch behavior should autonomous
100-card production be considered.
