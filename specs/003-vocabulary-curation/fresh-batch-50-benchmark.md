# Feature 003: first fresh 50-candidate benchmark

**Run:** 2026-10-14 UTC. **Scope:** five new ten-candidate category batches, generated after the 28-card guarded promotion. This is a bounded calibration run; none of its decisions changed `data/vocabulary.tsv`. Raw candidate, normalizer, verifier, repair, operation, audit, and corrected promotion-preview artifacts remain in `curation/batches/fresh-*/` and the adjacent JSON files.

## Production decisions

| Measure | Result |
| --- | ---: |
| Generated new concepts | 50 exactly |
| ACCEPT, provisional | 44 |
| HOLD | 2 |
| REJECT | 4 |
| Accepted relation: `different-common-word` / `similar` / `false-friend` | 38 / 6 / 0 |
| Accepted confidence: high / medium / low / very-low | 0 / 26 / 0 / 18 |
| Fast-path / escalated accepts | 44 / 0 |
| No-contrast / confirmed duplicate rejects | 0 / 0 |
| Fast-path utilization among accepted ordinary candidates | 44/44 = 100% |
| No-contrast generation rate | 0/50 = 0% |
| HOLD / REJECT rates | 4% / 8% |

The two HOLDs have concrete verifier concerns: `food-02` (`daging babi` / `daging khinzir`) may overstate the exclusivity of *khinzir*; `food-04` (`sereal` / `bijirin sarapan`) has a possibly narrower, less casual Malay expression. The four REJECTs are `action-06` (*laman sesawang* may be an artificial everyday preference), `food-05` (the Indonesian cue is semantically too narrow for “groceries”), `home-07` (artificial *pel* / *mop* national contrast), and `work-05` (*guru besar* is associated chiefly with primary schools). The verifier mislabeled `food-05` as `false-friend` even though its forms are dissimilar; the affirmative semantic rejection was retained. This classification error needs a verifier-output check.

The candidates covered food/shopping, home, transport/travel, work/school, and common actions/technology/health. Generation compared each topic against the existing 28-card learner source and historical candidate index; normalization checked the complete new 50-candidate cohort and a 131-entry historical snapshot. No semantic overlap was confirmed. No candidate was forced into ACCEPT to meet a card target.

## End-to-end production performance

The clock started before the first generation call (`00:55:53.869545Z`) and stopped after all 50 decisions were prepared (`01:04:44.867236Z`). The **530.998-second wall-clock interval** includes candidate generation, semantic normalization, verification, a schema-repair call, local validation, and the time spent diagnosing malformed verifier output. It is an honest observed run interval, though implementation/debugging overhead makes it an imperfect steady-state estimate. It excludes the later audit and all future promotion work.

| Measure | Result |
| --- | ---: |
| Provisional accepted decisions per elapsed hour | 298.31 |
| Elapsed seconds per provisional accepted decision | 12.07 |
| Provider calls: generation / semantic normalization / verification / repair | 5 / 5 / 11 / 1 |
| Total model calls; calls per provisional accept | 22; 0.50 |
| Input / output tokens; total tokens per provisional accept | 310,538 / 21,201; 7,539.5 |
| Verifier calls; input / output tokens | 11; 131,590 / 13,067 |
| Research/evidence retrievals and cache hits/misses in production | 0; 0/0 (fast path bypassed external research) |
| Provider failures / provider retries | 0 / 0 |
| Malformed or semantically invalid model-output incidents | 2 verifier groups; one repair call and one rerun |
| Monetary cost/card | Unavailable: no versioned price/accounting record for this run |

The summed provider-call latency was 280.845 seconds (generation 75.774, normalization 40.858, verification 156.165, repair 8.048). The remaining wall-clock interval includes local work, tool orchestration, diagnosis, and waiting. Token counts come from provider operation records and include the Codex CLI wrapper's input context. The 298.31 cards/hour rate is **provisional production decision throughput**, not canonical learner-corpus throughput or an empirically quality-adjusted release rate.

The first verifier response selected `same` for nonidentical forms and invented an invalid historical-objection field. A later response selected `same` for *pel* / *mop*; its repair then used the invalid relation value `artificial-synonym`. The bounded repair normalized that value to the allowed relation plus an affirmative rejection defect. Raw responses, failures, and replacements are retained. These errors reveal avoidable verifier-schema cost and a need for stronger relation-form validation at the AI boundary.

## Separate quality audit

The audit began only after production decisions were frozen. It used an independent Sol review on **all 18 very-low accepted cards** and a seeded five-card sample of the 26 medium cards. There were no low or high accepts or accepted false friends to sample. The selected IDs and individual verdicts are in `fresh-batch-50-audit.json`. Five Sol calls took **340.204 seconds** and used 67,912 input and 10,545 output tokens. Targeted DBP source checks were performed afterward for contested claims; those checks are audit work and are not part of production throughput.

| Confidence tier | Audited | Confirmed good | Minor correction | Materially misleading | Should HOLD | Should REJECT |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| very-low | 18 | 5 | 10 | 1 | 1 | 1 |
| low | 0 | 0 | 0 | 0 | 0 | 0 |
| medium | 5 | 5 | 0 | 0 | 0 | 0 |
| high | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **23** | **10** | **10** | **1** | **1** | **1** |

The independent auditor marked `action-07` (*hamil* / *mengandung*) **should-reject** as a potentially artificial national contrast, `home-10` (*wajan* / *kuali*) **materially misleading** because the cue specified a shallow frying pan, and `travel-03` (*koper* / *beg pakaian*) **should-hold** pending exact-sense and preference resolution. Thus the audit flagged **two potentially material false positives among 23 sampled accepts**, plus one unresolved card. These are audit findings, not a population error-rate estimate. No accepted `same` card or duplicate escaped filtering in this sample.

The targeted source check supports withholding `home-10`: DBP defines *kuali* broadly and specifically translates a shallow frying pan as *kuali leper* ([DBP kuali](https://prpm.dbp.gov.my/Cari1?d=371752&keyword=kuali)). The other two findings need careful interpretation. DBP lists *hamil* in Malay but also states that *mengandung* is used for the intended pregnancy meaning ([DBP hamil](https://prpm.dbp.gov.my/Cari1?d=24348&keyword=hamil), [DBP mengandung](https://prpm.dbp.gov.my/Cari1?d=175768&keyword=mengandung)); overlap alone does not prove the preferred-form contrast invalid. DBP uses *beg pakaian* to translate “suitcase” in context while also defining the term broadly ([DBP example](https://prpm.dbp.gov.my/cari1?keyword=sachet), [DBP beg](https://prpm.dbp.gov.my/Cari1?d=72508&keyword=beg)). Both remain withheld from the promotion recommendation pending targeted preference/sense adjudication; the auditor's verdicts are preserved rather than silently overwritten.

The ten minor findings concern the precision of cues or explanations and the tendency to portray preferred forms as exclusive national vocabulary. The corrected promotion preview narrows `food-07` to **printed receipt** and changes `home-08` Malaysian *sikat rambut* to *sikat*, with DBP listing *sikat* as a hair comb ([DBP sikat](https://prpm.dbp.gov.my/Cari1?d=72508&keyword=sikat)). Other minor findings update candidate-specific rationale or add qualification. Audit suggestions such as `different-preferred-word` were treated as prose because that string is outside the four relation values. The auditor proposed raising `work-09` from very-low to high; the preview retains the original tier pending broader calibration. No relation enum correction was applied to the 41 preview cards.

The tier pattern is directionally useful in this small sample: all five sampled medium cards were confirmed good, while very-low contained the three unsafe/unresolved flags and every minor correction. The four-tier scheme remains uncalibrated: this batch produced no high or low accepts, and 23 audited cards cannot establish population accuracy. The audit flagged 10/23 for minor correction and 2/23 for potentially material false positives; the one HOLD is reported separately rather than counted as a proven error.

## Promotion recommendation and next change

`fresh-batch-50-promotion-preview.json` contains **41 corrected provisional cards ready for a later guarded promotion check** and **3 withheld cards** (`action-07`, `home-10`, `travel-03`). It preserves every fresh candidate ID, the original decisions, audit results, confidence metadata, and exact corrections. This recommendation is based on the specified stratified audit; 21 accepted cards were not individually deep-audited. No permanent concept IDs or GUIDs were assigned for this fresh batch, and the canonical TSV remains at **28 cards**. The two production HOLDs and four production REJECTs are also excluded.

The next bounded change should improve generation and the verifier prompt around **preferred national forms versus shared normal synonyms**, **cue sense precision**, and **relation-schema adherence**. In particular, generate fewer dubious national contrasts such as *hamil* / *mengandung* and shape-specific cues such as “shallow frying pan” unless the answer forms match that exact sense. Keep the ordinary fast path: it resolved 44/50 candidates without research. Preserve targeted evidence escalation for the six production holds/rejects and the three audit flags; do not impose universal research on the other ordinary candidates. A later, separately authorized guarded promotion can reconsider the three withheld cases and validate all 41 preview entries before canonical export. Do not start a larger vocabulary batch from this report alone.

No empirical expert-human benchmark is recorded for Feature 003, so **AI/expert throughput and progress toward the long-term 50× objective are unavailable**. The batch provides only the AI production measurement and sampled quality findings.
