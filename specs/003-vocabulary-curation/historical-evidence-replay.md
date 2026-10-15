# Feature 003: claim-evidence replay of frozen historical holds

## Scope and outcome

The [frozen sample](historical-hold-sample.json) contains the same 26 non-fixture candidate IDs used in the previous policy replay. No candidates were generated, IDs reassigned, archived candidate events rewritten, or learner TSV rows promoted. The [machine-readable result](historical-evidence-replay.json) lists every candidate, its original and new outcome, risk path, unresolved claim types, evidence references for acceptance, cache metrics, and measured processing time. [Verifier results](evidence-verifier-results.json) preserve prompt and evidence digests, Luna output, tokens, and elapsed time. The [cold cache result](historical-evidence-replay-cold.json) is retained for comparison.

| Outcome | Previous policy replay | Evidence replay |
| --- | ---: | ---: |
| Accepted | 0 | 1 |
| Hold | 25 | 24 |
| Affirmative reject | 1 | 1 |
| Ordinary fast-path accept | 0 | 1 |

`food-001:foods-01` (**lunch → makan siang / makan tengah hari**, `similar`) is the recovered historical false negative. Independent current government/hospital meal examples in [Indonesia](https://keslan.kemkes.go.id/view_artikel/4259/obesitas-pada-remaja-dan-cara-mencegahnya) and [Malaysia](https://hkl.moh.gov.my/mengenai-kami/jabatan/perubatan-iii/direktorat-sokongan-klinikal/dietetik-sajian), with a [DBP entry](https://prpm.dbp.gov.my/Cari1?d=72508&keyword=tengah+hari), were already archived as claim-linked evidence. A separate Luna verifier reclassified the relation from `different-common-word` to `similar` and reported no material unresolved concern. The old verifier's relation label, rather than insufficient evidence, blocked this card. It is an **experiment acceptance**, not a promotion to `data/vocabulary.tsv`; canonical release remains unchanged.

The single confirmed reject remains `technology-001:technology-07` (**camera → kamera / kamera**). Identical ordinary forms offer no cross-language contrast under this deck's objective.

## Five diagnostic candidates

| Candidate | Decision | Exact remaining issue |
| --- | --- | --- |
| `clothing-001:clothing-01` trousers → celana / seluar | HOLD | Archived Indonesian retail use and Malaysian PRPM and ministry evidence exist, but neither locale has a claim-linked preferred-form claim. No valid evidence-audit stage or independent verifier was completed. PRPM's listing of *celana* cannot decide ordinary preference. |
| `food-001:foods-06` biscuit → biskuit / biskut | HOLD | The new [PRPM capture](https://prpm.dbp.gov.my/Cari1?d=274052&keyword=biskut) reinforces Malaysian meaning and is counted in the existing DBP source family. It does not resolve the historical concrete objection about the exact Indonesian snack sense or comparative everyday preference. The earlier verifier concern remains material. |
| `home-001:topic-03` refrigerator → kulkas / peti sejuk | HOLD | Existing Electrolux, DBP, and IKEA evidence establishes meaning and consumer use, but the archived adversary identified unresolved *peti sejuk* versus *peti ais* preference and an unsupported claim about Malaysian *kulkas*. More dictionary entries alone would not resolve this. |
| `transportation-001:transportation-01` car → mobil / kereta | HOLD | Existing evidence does not settle ordinary preference and cross-locale alternatives to the level required by `different-common-word`; a concrete historical adversarial objection remains. No new usage comparison was inspected in this replay. |
| `university-001:university-study-03` scholarship → beasiswa / biasiswa | HOLD | Extensive independent government/university evidence supports the student-funding sense. A new Luna verifier agreed on `similar`, but explicitly kept a material concern about extrapolating institutional use to unrestricted everyday preference and broader funding labels. This concern was not silently discarded. |

## Claim taxonomy and retrieval behavior

The new cache stores `lexical-existence`, `semantic-meaning`, `common-usage`, `preferred-everyday-form`, `cross-language-contrast`, and `false-friend` as distinct kinds. Every fact retains locale, form, sense, source identity/family, URL, inspection method, provenance, stance, usage basis, and original candidate/claim. Lookup requires matching locale, form, sense, claim kind, and original claim or exact proposition. Dictionary-only support cannot become a preferred-everyday-form fact. Source-family aliases prevent a DBP capture and its archived copy from becoming two independent signals.

The provider boundary accepts batches of claim queries. This phase imported inspected observations from existing candidate archives and one directly inspected PRPM definition into a persistent cache. Curation commands can import reviewed captures with `cache-evidence` and attach reusable observations with `hydrate-evidence`. Candidate-specific evidence remains visible in the archived stage or replay row. The normal `.apkg` build does not access the cache or call research/AI services.

[PRPM](https://prpm.dbp.gov.my/) has public lexical pages, so inspected page captures are practical. The [current official KBBI site](https://kbbi.kemendikdasmen.go.id/) requires an account for lookup; this phase did not build a login scraper or substitute an older unofficial mirror as authoritative current KBBI. Source captures are explicit, reviewable inputs. No live external retrieval happened in the replay itself.

## Measured work and limits

The first cold replay had **0/115** claim-query cache hits and imported **111** archived observations. A later replay had **85/115** hits before provider access, imported one inspected PRPM capture, and still had **30** unresolved claim queries. The cache reduces repeated access to existing facts; it cannot invent missing preference evidence. The capture supplied meaning only and did not change the biscuit decision.

Three bounded Luna verifier calls consumed **42,675 input tokens**, **1,360 output tokens**, and **26.368 seconds** in recorded model elapsed time. The final local replay took **0.500 seconds**. Their sequential sum is **26.868 seconds**, yielding a *replay-only* observed rate of **133.987 accepted cards/hour** and **26.868 seconds per accepted card**. This is **not** full curation throughput: the original candidate generation, source research/inspection, archived role calls, and time spent preparing this experiment are unavailable and excluded. Approximate monetary cost is unavailable. Only one card was accepted, so the rate is unstable and cannot support the 50× human-relative objective.

The final risk distribution was **1 ordinary fast**, **12 escalated**, **13 not assessed**. Common remaining reasons were missing verifier stages (10 candidates), verifier concerns (11 risk triggers), concrete historical adversarial objections (6), missing evidence-audit stages (3), and missing relation proposals (3). The per-candidate `unresolved_claim_types` and `preverification_issues` fields in the JSON distinguish those from contradictory evidence.

## Next bottleneck

The evidence cache and claim taxonomy are reusable, and one ordinary candidate reached the fast path without a new adversarial pass. Broad throughput remains poor. The next change should focus on **claim-linked preferred-form evidence and completing missing evidence/verifier stages**, especially for ordinary `different-common-word` candidates. It should use repeatable national usage or corpus comparisons where accessible, preserve concrete objections, and rerun this same sample before any new vocabulary batch. The source access strategy for current Indonesian authoritative lexical data needs a reliable permitted path; this phase left that access gap explicit.
