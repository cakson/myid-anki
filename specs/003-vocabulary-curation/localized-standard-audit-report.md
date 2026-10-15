# Feature 003: localized-standard versus borrowed-form audit signal

This phase used frozen fresh-batch ACCEPT decisions and existing independent
audits. It did not generate candidates, change production decision policy
**3.1.0**, enable the competing-form challenge, or add a production model call.
The new signal is implemented as a retrospective **audit-routing-only**
classifier in `localized_standard_risk.py`; it is not a production HOLD rule.

## Risk definition and rule

- **Standard and everyday:** the localized term is normal in practical use;
  a borrowed synonym alone does not imply a misleading card.
- **Standard with a competing borrowing:** the localized answer is valid, but
  an English/international same-sense form may be common enough to make an
  unqualified everyday-preference claim worth auditing.
- **Primarily formal or prescriptive:** the proposed answer may be taught as
  everyday despite a much more usual borrowing. This is an especially strong
  audit concern. A production HOLD still requires its own concrete material
  objection; this retrospective classifier never changes an ACCEPT.

The cheap rule requires **all** of: an accepted `different-common-word` card,
an explicit standard/localized/formal characterization of a proposed answer
in the frozen verifier text, and a named alternative tied to English or
borrowing. It returns `possible` or `strong`; `strong` additionally requires
explicit ordinary-use competition language in the verifier risk or alternative
rationale. It does not trigger on foreign etymology or an ordinary borrowing
used as the learner answer. Both levels route to audit. The level is a
review-priority description, not a linguistic verdict or probability.

## Retrospective evidence and counterexamples

[The frozen simulation](localized-standard-audit-simulation.json) evaluated
all **122** fresh-batch ACCEPTs using production-time candidate and verifier
fields. Before the additional audit, **109** had independent outcomes; the
other 13 remained unknown. Six carried the new signal: three `strong`, three
`possible`. Their final known outcomes are **two critical**, **one
correctable**, and **three confirmed good** after the focused supplement.

| Candidate | Signal | Independent result | Meaning for the rule |
|---|---|---|---|
| flash drive → `flashdisk` / `pemacu kilat` | possible | should reject | Known everyday-preference failure; now deterministically routed |
| printer → `printer` / `pencetak` | strong | should hold | Already routed by regional/register risk |
| cutting board → `talenan` / `papan pemotong` | strong | minor correction | Standard term remains usable; existing route caught it |
| clothes hanger → `gantungan baju` / `penyangkut baju` | strong | confirmed good | Localized terms are still useful despite `hanger` |
| software → `perangkat lunak` / `perisian` | possible | confirmed good in new audit | Shared `software` does not erase useful local terms |
| hardware → `perangkat keras` / `perkakasan` | possible | confirmed good in new audit | Shared `hardware` does not erase useful local terms |

The last three rows are essential counterexamples to a borrowing veto. Other
audited-good cards with borrowings, such as airplane and apron, were not
flagged because the verifier did not make the narrower
standard-versus-borrowing claim. The rule still misses cases where the
verifier fails to name the borrowing or fails to characterize the localized
term accurately. It cannot establish actual usage preference by text matching.

### Source-type limits

All **122** saved fast-path ACCEPT decisions are **verifier-only** for this
purpose: they contain no candidate-level external citation or evidence packet
from which to classify support as dictionary, government, publication,
conversation, or corpus evidence. Therefore the historical data cannot test
whether **official-source-only support** predicts this failure. Missing
citations do not mean the words lack real-world usage.

Separate post-decision checks show why dictionary existence and everyday
preference must remain distinct. [DBP/PRPM records `perisian`](https://prpm.dbp.gov.my/Cari1?d=74812&keyword=perisian)
and [`perkakasan`](https://prpm.dbp.gov.my/Cari1?d=115704&keyword=perkakasan)
for the intended computer senses; those references establish meaning and
official use, not frequency. Independent mainstream Malaysian news also uses
both words together in [technology reporting](https://bernama.com/bm/news.php?id=2363486)
and [school technology reporting](https://bernama.com/bm/news.php?id=2508373).
That is a distinct usage signal, though these examples still do not quantify
relative everyday frequency against `software` or `hardware`. An Indonesian
government [digital-literacy explanation](https://bpt.komdigi.go.id/Publikasi/detail/urgensi-pengembangan-sdm-bidang-tik-untuk-asn-di-seluruh-indonesia)
uses `perangkat lunak` and `perangkat keras`. These checks were performed
**after** routing and were not allowed into the simulated production features.

## Router simulation

The original risk-first C router retained its fixed hash sampling rule:
10% of otherwise-clean high cards and 15% of other otherwise-clean tiers,
rounded up per batch/tier. Simulated D adds the new `possible` and `strong`
signal to deterministic audit routing while retaining that same random
backstop. It makes no change to production acceptance.

| Batch | C routed | D routed | Known critical routed under D |
|---|---:|---:|---:|
| Fresh 1 | 22/44 | 22/44 | 3/3 |
| Fresh 2 | 37/40 | 37/40 | 6/6 |
| Final calibration | 14/38 | 17/38 | 3/3 |
| **Pooled** | **73/122 (59.8%)** | **76/122 (62.3%)** | **12/12** |

In the final batch, D uses **13 deterministic + 4 random** audits, or
**44.7%** of ACCEPTs, compared with the earlier actual 23/38 (60.5%) audit.
Its three new deterministic selections are flash drive, software, and
hardware. The flash-drive candidate would be audited **deterministically**
instead of depending on chance; the latter two were previously unlabeled
and were audited below. No previously confirmed-good card is newly routed;
the new audit shows both newly routed unlabeled cards are good. The older
batch routing counts are unchanged, but this is **not** independent held-out
validation of the new signal: the earlier schemas did not emit comparable
preference-risk fields and contain no labeled instance of this exact failure.
The rule was designed after seeing flash drive, so its 12/12 historical
critical capture is retrospective fit, not a prospective recall estimate.

The final-batch workload falls below its earlier 61% audit but remains above
the contemplated 20–40% routine range. The legacy Batch 2 schema still
routes 37/40. Random sampling remains mandatory for unknown failure classes.

## Remaining 13 and guarded promotion

D selected two of the previously deferred 13 cards for deep audit:
`cal3-technology-001:technology-03` (software) and
`cal3-technology-001:technology-04` (hardware). The same fixed sampling rule
selected **no additional** deferred card. [The independent Luna supplement](final-calibration-localized-standard-audit.json)
confirmed both good with no learner or metadata correction, in **one call,
7.003 seconds, 12,956 input tokens, and 427 output tokens**. This work is
separate from production throughput and from the previous audit supplement.

[The guarded promotion record](../../curation/promotions/final-calibration-localized-standard.json)
preserves their original candidate IDs, frozen routing and audit digests,
permanent concept IDs, and the **11 still-unaudited** deferred IDs. Only the
two independently cleared cards were promoted, taking the canonical source
from **125 to 127** learner cards. The other 11 remain unpromoted. The three
previously audited unsafe ACCEPTs also remain withheld. This decision does
not treat unselected cards as audited-good.

Source validation and the offline `.apkg` build passed at **127 notes and
127 cards**. All 127 GUIDs are unique and match permanent concept IDs; no
`same` relation entered the deck. The full suite passed **188 tests** and
Ruff passed. Existing IDs were retained by appending only two new rows and
ledger assignments.

## Readiness

**Do not start a 100-card autonomous batch yet.** The focused signal cheaply
catches the known flash-drive failure and routes few additional cards in the
latest batch, but its only newly discovered audit outcomes were good cards.
There is no held-out positive example showing that the rule generalizes,
and archived production has no source-type data to distinguish an official
term that is everyday from one that is primarily prescriptive. The final
batch would still audit 17/38 ACCEPTs, while the older second batch needs
37/40 under its legacy confidence signals.

The specific unresolved failure is **verifier wording as a proxy for actual
everyday preference**. A future focused validation would need independent
usage-oriented evidence for localized terms and their named borrowings, with
candidate-level source provenance, before this text signal could be treated
as a reliable low-cost router. It should remain an audit signal, never a
blanket synonym veto or automatic production HOLD.
