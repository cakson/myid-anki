# Feature 003: Current curation and validation

Feature 003 uses production policy **v3.1** (`curation/config.json`) and the 137-concept canonical learner source. The [convergence report](convergence-report.md) is the current architecture and benchmark index. Earlier frozen-replay instructions in historical reports are retained for provenance; they are not a request to rerun the experiments or to start a new batch.

## Production and release boundary

A bounded topic batch proposes useful Indonesian–Malaysian Malay contrasts. Safe normalization, duplicate checks, and no-contrast filtering run before a compact independent verifier. Policy v3.1 issues provisional ACCEPT, HOLD, or REJECT and stores confidence, specific rationale, and review flags. Targeted source evidence is used for concrete disputes; false friends keep their stronger evidence and adversarial gates. No single generator response becomes a learner card.

After production, concrete risk signals select candidates for independent pre-promotion audit. Selected cards need recorded clearance; unsafe or unresolved findings remain withheld. The general `curation export` command requires a closed v3.1 report and a batch-local `promotion-eligibility.json` record bound to each eligible candidate's current decision and projected learner content. The record distinguishes `risk-based`, `random-monitoring`, `other`, and `none` routes. A clean card need not be selected for random audit to be eligible. Random/stratified review remains ongoing post-production QA monitoring; later corrections retain the permanent concept ID. A batch safety brake blocks export. Only guarded promotion changes `data/vocabulary.tsv`. This is an intentional optimistic-quality tradeoff; it does not establish safe fully autonomous release of large batches.

Preserve candidate IDs, batch state, prompt/model versions, source-role evidence, cache entries, objections, audit findings, and promotion records. Keep the competing-form challenge, universal localized-standard/technical-borrowing gates, revised verifier, default Sol escalation, and cheap universal screen disabled. Their saved artifacts are research results, not production alternatives.

The curation CLI and versioned prompts are described in the [README](../../README.md). Historical replay and batch reports under this directory show how decisions, corrections, audit cost, and source promotion were recorded. The latest [audit-budget report](operational-audit-budget-report.md) and [cheap-screen benchmark](cheap-audit-screen-benchmark.md) explain why an audit budget for a 100-candidate autonomous run has not yet been approved. Do not infer one from a provisional decision-throughput number.

## Offline checks

Run from the repository root in the configured Python environment:

```sh
python -m pytest
ruff check .
ruff format --check .
python -m indo_malay_anki validate
python -m indo_malay_anki build
```

A successful current build has **137 notes and 137 cards**. The Anki build and GitHub Release read accepted version-controlled source data only; neither performs AI calls or live research. Check permanent IDs, unique ID-derived GUIDs, the neutral front, both labeled back answers, and back-only false-friend contrast before release. These deterministic checks do not prove linguistic truth; independent audit and correction history provide the separate content-quality evidence.

The approximately 50× expert-human accepted-card throughput objective remains aspirational. No observed human baseline or comparable quality-adjusted end-to-end ratio exists. Production decision throughput, audit workload, promotion-adjusted throughput, and actual released-card throughput must be reported separately.
