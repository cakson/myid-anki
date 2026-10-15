# Feature 003 convergence report

Date: 2026-10-15. **Feature 003 converges on an AI-first, guarded vocabulary curation architecture with active production policy v3.1.** Its reproducible pipeline and 137-card learner corpus are usable. The general `curation export` command now enforces the remaining T114–T115 promotion safeguards. The feature does not establish safe unaudited autonomous release of large batches or the aspirational 50× expert-human throughput ratio.

## Final architecture

```text
bounded contrastive candidate generation
  → deterministic validation, semantic duplicate and no-contrast filtering
  → separate lightweight v3.1 linguistic verification
  → provisional ACCEPT / HOLD / REJECT with confidence and risk metadata
  → risk-selected independent pre-promotion audit and correction/withholding
  → eligibility-bound, ID-preserving promotion into deterministic learner TSV
  → offline Anki build
  → random/stratified independent QA monitoring and ID-preserving corrections
```

Ordinary useful contrasts may ACCEPT optimistically without universal external research. `same` is rejected as no meaningful contrast. Only `similar`, `different-common-word`, and strictly reviewed `false-friend` relations enter the learner corpus. HOLD names a material unresolved learner risk; REJECT names an affirmative defect or scope reason. Evidence adapters, source-role records, and cache support targeted disputes and false friends. AI output remains fallible, so provisional acceptance and independent audit are deliberately separate. Random auditing of apparently clean accepts is standing post-production QA monitoring, not a mandatory release gate for an otherwise eligible card. This is an intentional optimistic-quality tradeoff; concrete risk-selected review still requires pre-promotion clearance.

The active `curation/config.json` has `decision_policy_version: 3.1.0` and centrally routes curation roles to Luna. The normal Anki build and release require only the version-controlled accepted learner source. Candidate IDs, provenance, prompt/model versions, evidence, audits, correction trails, permanent concept IDs, and ID-only GUID derivation remain preserved.

## Disabled experimental paths

| Mechanism | Disposition and evidence |
|---|---|
| Competing-form challenge | Remains versioned research, not a production gate. It added 12 Luna calls, about 143 seconds and 164,171 tokens, caught no additional unsafe cards, and withheld four audited-safe cards. |
| Universal localized-standard or technical-borrowing gate | Disabled. Official terminology and cheap lexical cues did not reliably distinguish ordinary preferred usage; existing source-role and audit-only signals remain inspectable. |
| Revised Luna verifier | Not a production replacement. It challenged 14/20 known critical cards in an enriched benchmark but challenged only 1/5 in the newest cohort. |
| Default Sol verifier escalation | Not justified: Sol was slower and did not improve the overall quality/audit tradeoff. |
| Universal cheap Luna audit screen | Disabled. At 20 cards/call it cost about 696 tokens/card and found both known router residuals, but cleared 14/20 known critical cards. Router plus screen still deep-audited 116/153 labeled accepts with a 10% random backstop and added 106,546 screen tokens. |

Experimental code and saved inputs, outputs, labels, and reports remain available for reproduction. None of these paths should appear as an equally supported production option. No new curation mechanism was introduced in convergence.

## What the experiments established

- The first conservative retrospective had 102 candidates: 6 historical ACCEPT, 87 HOLD, and 9 REJECT; three accepted `same` entries were later excluded. Its poor ordinary-card recall motivated optimistic v3.1.
- The optimistic frozen replay produced 24 provisional ACCEPT, 1 HOLD, and 1 no-contrast REJECT. Independent audit found 17 confirmed-good and 7 minor-correction accepts, with no materially misleading card in that small sample. The pencil HOLD was later reconsidered, and 25 historical cards entered guarded promotion.
- Fresh Batch 1 generated 50 candidates and promoted 41 after audit; Batch 2 generated 50 and promoted 34. The first full audit found three unsafe/unresolved provisional accepts. Subsequent batches found everyday-preference, localized-versus-borrowed, answer-precision, and unexpected ordinary vocabulary failures such as socks. These errors do not collapse into one reliable lexical detector.
- The fixed deterministic audit router selected 107/182 historical fresh-batch ACCEPTs (58.8%) and caught 18/20 known critical cases. Random auditing discovered the two known residual cases. Sampling 20% of the residual pool raised total deep audit to about 68%; both residual cases were selected together in only 5.2% of 4,096 historical simulations. This is a simulation over known outcomes, **not** a future error probability.
- A cheap screen could flag those two residual examples, but screen-first deep audit missed most other known critical cases. Adding the screen to the router increased work without making deep audit selective. The current evidence therefore supports substantial independent audit rather than an additional universal AI check.

See the [fresh-batch benchmark](fresh-batch-50-benchmark.md), [second-batch calibration](second-fresh-batch-calibration.md), [verifier benchmark](verifier-contract-benchmark-report.md), [audit-budget calibration](operational-audit-budget-report.md), and [cheap-screen benchmark](cheap-audit-screen-benchmark.md). Independent audit labels are useful evaluation evidence, not proof of population accuracy: historical audit selection was nonrandom, 29 fresh-batch ACCEPTs in the audit-budget cohort remain unlabeled, and the verifier benchmark deliberately enriched critical cases.

## Corpus, throughput, and unresolved scaling

The canonical `data/vocabulary.tsv` contains **137 concepts**. The offline build produces **137 notes and 137 cards**. Unpromoted historical candidates remain in their archives; convergence did not promote any candidate or change learner data. Confidence and curation metadata remain outside the learner TSV. Corrections retain permanent IDs, and note GUIDs derive only from those IDs.

Report four distinct quantities: production decision throughput, promotion-adjusted throughput, independent audit workload, and full end-to-end released-card throughput. Historical rates near 298 and 509 provisional ACCEPTs/hour were production decision measurements and **must not** be called released-card throughput. Audit time and correction/withholding are operational costs. The approximately 50× experienced-human accepted-card target remains an aspiration; no empirical human baseline exists, so no comparable AI/human ratio is available. Feature 003 does not need to eliminate audit or demonstrate this north star to be complete.

The unresolved product question is: **What quality/cost tradeoff should govern larger corpus production when current models still require substantial risk-selected independent audit and ongoing random QA?** The prior audit-budget calibration did not approve a 100-candidate autonomous run. A future product decision should specify the desired risk and audit budget before scaling; it should not be disguised as another Feature 003 lexical heuristic.

## Convergence assessment and task disposition

The revised [specification](spec.md), [plan](plan.md), [quickstart](quickstart.md), and [README](../../README.md) state the active path and benchmark limits. The assessment covered FR-001–FR-036, SC-001–SC-014, four user stories, the plan's source/identity/audit decisions, and the constitution's fourteen principles. The prior convergence pass added **T114–T115 in Phase 13** for two export gaps. Both are now complete. The older 34 unchecked entries document a broader 2026-10-13 plan, including a mandatory matched pilot and expert benchmark that the new convergence decision removes from Feature 003 completion. They are neither silently marked done nor instructions to rerun historical work.

| ID | Closure result | Guarantee |
|---|---|---|
| T114 | Complete | Policy-v3.1 export requires a closed full decision and a batch-local eligibility record. HOLD, REJECT, pending, withheld/unresolved review, stale clearance, and a batch safety brake cannot enter learner data. Concrete risk-selected cards require independent clearance; clean cards do not wait for random QA. |
| T115 | Complete | Export uses the final verified relation and applicable cue correction. Decision and projected-content digests bind clearance to current artifacts before permanent ID assignment. Relation correction leaves concept ID and ID-derived GUID unchanged. |

The batch-local `promotion-eligibility.json` record is schema version 1 with `batch_id`, `batch_safety_brake`, and per-candidate `status`, `audit_route`, `audit_verdict`, `decision_digest`, and `content_digest`. Routes are `risk-based`, `random-monitoring`, `other`, or `none`; this records why review occurred without adding a separate audit subsystem. A random-monitoring finding can withhold an unsafe card, but absence of random selection cannot block an otherwise eligible one. Existing historical audit and promotion artifacts were not rewritten.

| Finding at start of convergence | Classification | Resolution |
|---|---|---|
| Spec/plan/quickstart/README still described the earlier pilot and universal evidence path as current work | Documentation contradiction | Updated to the v3.1 guarded architecture and linked benchmark history. |
| README contract test still expected the superseded two-source ordinary gate | Test contradiction | Aligned the contract test with independent verification, targeted evidence, random audit, and guarded promotion. |
| Five archived experimental scripts failed repository-wide Ruff format check | Formatting only | Reformatted without changing decisions, configuration, or candidate artifacts. |
| Safe autonomous audit budget and 50× human-relative throughput remain unproven | Product/scaling limitation | Explicitly excluded from Feature 003 completion; retained as an open product decision rather than an invented success claim. |

## Validation

Closure preserved the canonical source SHA-256 `f7db434226d0e6e036b863026d3bf7a3572f01f75d1cb2e573692744bbfc67ef` and ID-ledger SHA-256 `e3afcb81b213a060a75030ec2c1f7305acb8a9aae2ffa7b97319de12456a1e89` before and after T114–T115 implementation and documentation.

- Full automated suite: **220 passed**. Its stable-ID and semantic-rebuild tests cover content changes without GUID changes. Dependency code emitted deprecation warnings but no failures.
- `ruff check .`: passed. `ruff format --check .`: passed, 283 files formatted.
- Offline `python -m indo_malay_anki validate`: 137 valid concepts.
- Offline `python -m indo_malay_anki build`: 137 notes, 137 cards, zero media.
- Independent package/source inspection: 137 unique active concept IDs, 137 unique GUIDs matching `stable_guid(id)`, 137 package notes and cards, fixed deck/model IDs, and all active IDs present in the append-only ledger (140 assignments, including retired IDs). No `same` row entered the learner source.

No new vocabulary batch, promotion, production-policy switch, or learner-source edit occurred during closure. Export-specific tests cover clean unaudited eligibility, risk clearance, withheld and stale records, safety brakes, idempotent retry, final verified relation, cue correction, and stable GUID identity.
