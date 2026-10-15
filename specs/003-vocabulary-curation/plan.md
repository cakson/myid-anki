# Implementation Plan: Feature 003 Optimistic Recalibration

**Branch**: `003-vocabulary-curation` | **Converged**: 2026-10-15 | **Spec**: [spec.md](spec.md) | **Status**: active production architecture

This document retains the original recalibration rationale. The final operational decisions in [convergence report](convergence-report.md) supersede its historical execution schedule and matched-pilot completion gate. Policy v1/v2 records remain historical facts. The canonical learner source contains 137 concepts; no additional candidate promotion is part of convergence.

## Goal and measured baseline

AI remains the normal curator of a contrast-only corpus. Ordinary useful vocabulary should reach learner source quickly after deterministic checks and a separate compact linguistic verifier, with confidence and review flags recorded. External research is reserved for concrete risk; false friends retain strict gates. Count useful output as **new accepted cards promoted to canonical `data/vocabulary.tsv` per end-to-end active wall-clock hour**, with provisional replay decisions reported separately.

The archived non-fixture baseline is 102 candidates: six historical ACCEPT, 87 HOLD, nine REJECT. Three accepted `same` entries were retired, leaving three learner cards. The frozen 26-hold policy-v2 replay yielded zero ACCEPT, 25 HOLD, one affirmative REJECT; a later claim-evidence replay yielded one experimental ACCEPT (`lunch`), 24 HOLD, one no-contrast REJECT. Neither replay promoted cards. The evidence replay used three bounded Luna verifier calls (42,675 input and 1,360 output tokens), imported 111 inspected observations into a cold cache, and later hit 85 of 115 claim queries. Its roughly 0.5-second local replay excluded historical research and provider latency. Historical end-to-end accepted cards/hour, actual calls/card, retrievals/card, and cost/card remain **unavailable**. The empirical problem is that universal proof and broad risk triggers blocked ordinary cards; additional retrieval alone recovered little. See [validation results](validation-results.md), [hold experiment](historical-hold-experiment.md), and [evidence replay](historical-evidence-replay.md).

## Technical context and constitution check

- Preserve the Python 3.12+ CLI, file-backed records, `genanki` builder, `pytest`, `ruff`, central Luna route in `curation/config.json`, evidence adapters/cache, and existing Anki build.
- Keep the eight-column learner TSV; five Anki note fields; fixed deck/model IDs; neutral front; both answers and optional false-friend contrast on the back; one note/card; permanent ID ledger and ID-only GUID. Confidence/provenance stay outside Anki projection.
- `validate`, `build`, and GitHub release remain independent of live AI/research. Only guarded export changes canonical learner source.
- Constitution quality-over-volume is met by independent verification, specific blocker handling, strict high-risk gates, audits and correction tracking. Optimistic ordinary acceptance does not permit raw generation-to-source promotion. No constitutional exception is needed.
- The recorded old-to-new Anki import test remains relevant while note schema/rendering stay unchanged; repeat it if either changes.

| Constitution gate | Post-design assessment |
|---|---|
| Versioned source; offline deterministic output | Pass: only TSV enters build |
| Neutral one-card concept; stable identity | Pass: schema, IDs, GUID and ledger retained |
| Correctness and testability | Pass: separate verifier, typed decisions, high-risk gates and sampled audits |
| Simple inspectable technology | Pass: append-only files and bounded workers; no new service/database |

## Preserve, change, and bypass

| Disposition | Components |
|---|---|
| **Keep** | `records.py` candidate/claim history; `store.py` atomic events and existing operation metrics; manifests/checkpoints; prompt snapshots/provider route; `duplicates.py`; `evidence.py`, adapters and `evidence_cache.py`; packet digests and bundle validation; reporting foundation; `ids.py`, `export.py` guarded transaction/ledger; learner builder/validator/release and compatibility tests. Preserve candidate IDs, evidence, archived metrics, existing TSV and all prior decisions. |
| **Modify narrowly** | `gate.py` decision/risk/confidence policy; `workflow.py` dependency graph and reconsideration; `packets.py` compact verifier input; prompt version; `records.py` policy-v3 fields/old-record defaults; reporting/CLI and policy tests. `export.py` may need to recognize v3 accepted metadata but must retain its transaction and ID behavior. |
| **Bypass as universal gates** | Two audited external signals for every ordinary card; evidence audit before any verifier; adversarial review for ordinary low risk; HOLD from a merely named synonym, missing frequency proof, generic hesitation, or old HOLD status; escalation from neutral region/register mention; fixed 24-card/three-relation quota; >1 human ratio as launch gate. Keep old records for audit. |
| **Add where incomplete** | Versioned v3 decision revisions, confidence/rationale/flags, safe early no-contrast path, no-contrast waste metric, compact verifier telemetry, targeted escalation, frozen replay report, confidence review queue and end-to-end throughput attribution. Existing cache/runner/budget/concurrency infrastructure is reused, not rewritten. |

## Risk-based policy-v3 orchestration

The generator supplies candidate fields and a provisional relation only. Cheap deterministic validation, normalized exact-form comparison, duplicate search and semantic-overlap screen run first. A confirmed duplicate is REJECT. Identical normalized forms are early `same` REJECT only when the intended sense and ordinary usage are also effectively identical; possible false-friend or usage divergence receives linguistic judgment. Preserve historical `no-cross-language-difference` as an alias to the new `no-meaningful-cross-language-contrast` reason without rewriting archives. Useful `biskuit/biskut` type spelling contrast must not collapse into `same`.

The separate verifier receives only candidate ID, concise neutral cue/sense, both terms, proposed relation, relevant short evidence if needed, concrete historical objections, and exact decision questions. Omit generator rationale, old HOLD verdict as an anchor, and unrelated historical payload. Reuse `records.py` verifier relation choice/material-concern schema where possible. Record prompt/input digest, actual model, calls, elapsed and tokens when available. Verifier may correct relation with lineage; correction alone is not failure. A new v3 result is required if an old result's question or dependency digest is incompatible. Generation cannot approve itself.

| Tier/path | Trigger and work | Decision |
|---|---|---|
| **Low / ordinary-fast** | Clear `similar` or straightforward `different-common-word`; aligned cue and natural forms; no unresolved duplicate, concrete contradiction or material objection; separate verifier agreement. External sources optional. | ACCEPT with confidence/rationale/flags; mark evidence and adversary `skipped-by-policy`, never fabricate role output. |
| **Medium / targeted** | Specific plausible preference issue, relation/cue uncertainty, modest material region/register issue, or credible overlap concern. | One bounded targeted check, cached evidence first; ACCEPT if resolved, HOLD if material issue persists, REJECT on affirmative defect. |
| **High / strengthened** | False friend, real contradiction, likely semantic mismatch, strong region/register ambiguity or significant verifier disagreement. | Claim-specific evidence and stronger independent review. False friends require both locale meanings, misleading contrast, verifier agreement and adversarial agreement. |

For `different-common-word`, a verifier's informed judgment may establish an ordinary preference claim. A named synonym or lack of direct frequency comparison alone lowers confidence and adds `usage-preference-weak`; it does **not** force HOLD. A specific plausible competing preference likely to mislead triggers targeted usage evidence and HOLD if unresolved. Dictionary existence alone neither proves nor disproves preference. A neutral mention of region/register is not a risk trigger. Historical concrete objections remain visible and are explicitly reassessed.

ACCEPT means the applicable path passes without a material blocker; HOLD requires a specific unresolved issue likely to misteach; REJECT requires an affirmative defect, duplicate, low learner value or confirmed no contrast. Missing evidence, outage, budget exhaustion, theoretical uncertainty, and prior HOLD alone do not veto an otherwise publishable ordinary card. At a budget cap, apply the available path gate and record the cap reason.

Every ACCEPT gets exactly one explainable tier: `high` for strong concordant signals; `medium` for meaningful nonblocking caveat; `low` for notable nonblocking uncertainty or corrected relation; `very-low` for substantial but still nonblocking uncertainty. No arbitrary probability percentages. Store a concise rationale and structured flags. A material unresolved issue is HOLD regardless of tier. Nonaccepted candidates have no accepted-card tier. A review view prioritizes very-low, low, medium, high. At batch closure, select a nonzero bounded random/stratified sample across available tiers for a separate post-acceptance AI audit, recording selection seed and findings; audit findings do not silently change learner source. Tune sample size from observed quality without fixing a speculative percentage.

## Historical migration, evidence and execution safety

Append v3 risk/decision/confidence records linked to original `(batch_id, candidate_id)`, prior decision, input digest, prompt/provider versions, evidence IDs and current relation. Never rewrite v1/v2 events or invent absent timing. A historical batch manifest keeps its original prompt pin; each policy-v3 reconsideration attempt instead records an explicit immutable v3 prompt-set reference. Packet construction uses that attempt reference for rerun stages and includes it in the input digest, while ordinary new-batch packets continue using their manifest pin. A prior verifier result is reusable only when its effective prompt version, questions, input digest and upstream dependencies match the new packet. Reuse other compatible successful stages; rerun only policy-invalidated work. Current `workflow.py` requires evidence audit before verifier and `gate.py` requires old usage/evidence stages; v3 must have its own dependency route while old-policy replay remains readable. A later failed attempt must not hide a compatible successful result. Historical HOLD is not itself negative evidence. Permanent IDs remain reserved, including retired `000001`; cross-batch duplicate and export/ID transactions stay serialized.

Keep source cache and structured retrieval for disputes, false friends and audits. Relink cached observations to exact claim/sense/locale; retain underlying source family, access provenance, limitations and contradiction. Mirrors count once. Dictionary meaning evidence does not become preference evidence. Batch retrieval/model work may amortize access but retains candidate-level conclusions. Configured caps cover targeted retrieval, verifier, adversary, conflict passes and malformed-output retry. Independent candidate work may use bounded workers and provider throttling; within-candidate order, duplicate resolution, manifest/report closure and export remain serialized. Partial fan-out checkpoints resume without touching TSV.

## Converged execution architecture

The active production policy is `3.1.0` in `curation/config.json`. Continue to generate bounded contrastive candidate batches, then apply deterministic validation, semantic duplicate and no-contrast filtering, a separate compact verifier, and the policy-v3.1 ACCEPT/HOLD/REJECT gate. Accepted candidates retain confidence rationale and structured risk metadata. Targeted evidence and the cache address concrete disputed claims; false friends keep their stricter claim-specific evidence and adversarial review. Production ACCEPT is provisional until applicable risk-selected independent audit clearance and guarded promotion. Otherwise eligible clean cards do not wait for random selection. Random or stratified review is permanent post-production QA monitoring, with ID-preserving corrections.

The current deterministic audit router is useful but historically selected 107/182 ACCEPTs (59%) and missed two independently identified critical cards, including socks. A 20% sample of its residual pool raised deep-audit coverage to roughly 68%, while both known residual cases were selected together in only 5.2% of historical simulations. This is not a future-risk probability. The prospective screen experiment did not yield a cheaper safe replacement: its cheapest 20-card Luna groups used about 696 tokens/card but marked only 6/20 known critical cards for review. Router plus screen still required 116/153 labeled accepts to receive deep audit at a 10% random backstop and added 106,546 screen tokens. Keep the screen disabled. Preserve random QA monitoring outside the mandatory release gate.

## Active and disabled components

| Production status | Component | Evidence-based decision |
|---|---|---|
| Active | Policy v3.1 optimistic ordinary gate, compact independent verifier, strict false-friend path | Multiple bounded batches produced useful cards; independent audits found correctable and critical errors, so acceptance remains provisional. |
| Active | Risk-selected pre-promotion audit plus random or stratified QA monitoring | Structured signals catch many known defects; random QA found critical errors outside them. |
| Active | Evidence cache, source-role records, targeted evidence, permanent IDs, guarded promotion, offline Anki build | Reusable provenance and deterministic learner source remain necessary. |
| Disabled research | Competing-form challenge | Added 12 Luna calls, about 143 seconds and 164,171 tokens; caught no additional unsafe cases and withheld four audited-safe cards. |
| Disabled as universal gates | Localized-standard and technical-borrowing checks | Source type and lexical heuristics did not reliably distinguish everyday usage; retain audit-only information where already collected. |
| Disabled research | Revised Luna verifier and Sol default escalation | The fixed benchmark showed inconsistent later-batch quality and no sufficient cost/quality advantage for replacement. |
| Disabled research | Universal cheap Luna audit screen | Screen-first missed most known critical cards; router plus screen raised cost without making deep audit selective. |

Experimental code and saved artifacts remain available for reproducibility, but they are not interchangeable production modes. Do not re-enable them through prompt or router changes without a separately justified product decision.

## Measurement and release interpretation

Maintain distinct measures for generation-to-production-decision elapsed time, provisional ACCEPT rate, independent audit calls/tokens/time, correction and withholding, guarded-promotion yield, and complete released-card throughput. Production decision rates of about 298 and 509 provisional ACCEPTs/hour from prior experiments do not include full audit or release work and must never be reported as released-card throughput. Historical 50-candidate batches promoted 41 and 34 audited/corrected cards respectively. The 137-card current corpus is the canonical learning source; held, rejected, unsafe and unaudited backlog artifacts remain separate.

The approximately 50× expert-human accepted-card throughput objective remains an aspiration. No observed expert-human benchmark or comparable quality-adjusted end-to-end AI/human ratio exists. Report the ratio as unavailable. The observed audit burden may make end-to-end throughput much lower than provisional decision throughput. Feature 003 can be complete as an inspectable AI-first curation and guarded-release system without demonstrating 50× or removing independent audit. The remaining scaling decision is the acceptable quality/cost tradeoff for larger corpus production.

## Task and validation disposition

The unchecked 2026-10-13 task delta in [tasks.md](tasks.md) is a historical implementation plan. In particular, its matched conservative-v3 pilot, mandatory expert benchmark, and automatic expansion work are not Feature 003 completion gates under the converged [specification](spec.md). Phase 13 completed T114–T115 for two specific safeguards in the general `curation export` command: audit-clearance enforcement and final verified relation/content projection. These do not alter production linguistic policy or the 137-card source during convergence. Do not run `$speckit-implement` over the old unchecked task list as though it were the current production roadmap. Preserve the checklist for provenance; evaluate any future work from the converged specification and a new explicit product decision. The [convergence report](convergence-report.md) records the benchmark lineage and validation outcome.

Normal source validation and `.apkg` generation remain deterministic and offline. Convergence must retain 137 unique concepts, 137 notes/cards, stable IDs and ID-derived GUIDs, five compatible note fields, the neutral front, and the back-only false-friend contrast. No experimental audit result or curation metadata may alter GUID identity.
