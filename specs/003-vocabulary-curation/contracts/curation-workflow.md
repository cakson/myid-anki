# Curation Workflow Contract: Feature 003 Policy V3

This contract records the implemented policy-v3.1 export boundary; older replay instructions below remain historical context. Curation may call AI/research; `python -m indo_malay_anki validate`, `build`, and GitHub releases read only deterministic learner source. Only guarded `export` may change canonical TSV and permanent ID ledger.

## Preserved command surface

| Existing command | Contract retained |
|---|---|
| `init --batch ID --topic TOPIC --limit N` | Bounded unique manifest and stable batch ID. |
| `route --role ROLE` | Central model/provider route; actual invoked model also recorded. |
| `packet`, `bundle`, `ingest`, `ingest-bundle` | Versioned role packets, schema-validated structured output, whole-bundle validation and resumable candidate events. |
| `check`, `finalize-hold`, `finalize-reject`, `report` | Deterministic reconciliation; v3 finalization requires typed material HOLD issue or affirmative REJECT reason. |
| `export --batch ID ...` | Closed, eligibility-bound accepted-only export using final verified content, duplicate screening, and a journaled TSV/ledger transaction; ID assignment after clearance. |

## Planned v3 extensions

| Interface | Input and output |
|---|---|
| `run --batch ID --role ROLE [--candidate ID]` or equivalent runner | Builds a compact versioned packet, invokes central provider via argument array, validates response, checkpoints attempt/result, and records actual model, elapsed, tokens where available. Manual packet/ingest remains supported with external timing/usage marked unavailable. |
| `reconsider --batch ID --candidate ID --policy 3` or equivalent | References original candidate ID/events/evidence and previous decision; records an immutable v3 prompt-set reference for the attempt, reuses only effective-prompt-and-digest-compatible results, reruns invalid stages, and appends risk/decision/confidence revision and old/new reason. It never regenerates the candidate or edits the original manifest/archive in place. |
| `report`/metrics extension | Reconciles outcome, relation, confidence, path, no-contrast, duplicate, escalation, cost/usage availability, and historical recovery. Experimental replay decisions are separate from canonical promotions. |
| Review/audit view | Orders accepted cards very-low → low → medium → high with flags, and selects random/stratified audit samples across every tier. No community workflow or mandatory human approval. |

Command spelling may be resolved during implementation, but the observable inputs/outputs and safety rules above are binding.

## Stage and decision contract

1. Normalize and validate candidate fields. Search exact/morphological and semantic duplicate overlap against batch, archives and learner TSV. Confirmed duplicate REJECTS. Exact same form may early REJECT as no contrast only when same intended sense and ordinary usage are established; a plausible false friend/usage divergence proceeds to linguistic check. `biskuit/biskut` type useful difference remains eligible.
2. Send a **separate** verifier a compact packet: candidate ID, English cue/sense, both forms, proposed relation, concise relevant evidence if needed, concrete historical objections, and exact semantic/relation/risk questions. Exclude generator rationale and old HOLD verdict. A proposed relation correction is retained and may ACCEPT if the corrected card is sound. Record packet digest and prompt version.
3. Classify low/medium/high risk from concrete signals. Low ordinary `similar`/`different-common-word` with no material objection ACCEPTS after independent verification, even without external research. Mark evidence/adversarial stages `skipped-by-policy` rather than producing fake role results. A named synonym or missing frequency evidence alone gives a lower tier/flag, not HOLD. A specific plausible preference problem likely to mislead triggers targeted medium-risk research.
4. Medium risk gets a bounded targeted check, preferably from claim-relevant cache; then ACCEPT if resolved, HOLD if a named material issue persists, or REJECT on affirmative defect. Neutral mention of region/register, generic hesitation or theoretical further research alone does not escalate.
5. False friends and other high risk receive stronger claim-specific support. A false-friend ACCEPT requires support for both locale meanings and misleading contrast, independent verifier agreement, adversarial agreement and a concise evidence-backed back-only contrast. Other high-risk semantic/contradiction disputes need targeted review. Budget exhaustion alone is not negative linguistic evidence.

Decision values are `accepted`, `hold`, `rejected` (plus open `pending`). ACCEPT needs the applicable gate and exactly one explained confidence tier. HOLD needs a specific unresolved issue likely to materially misteach. REJECT needs an affirmative defect/product-scope reason, including confirmed duplicate or `no-meaningful-cross-language-contrast`. Nonaccepted candidates have no accepted-card confidence. A material blocker never becomes accepted/very-low.

## Evidence, history, and concurrency

Existing inspected evidence/cache records remain authoritative for their **specific** claims. Reuse must preserve source family, language, sense, source reference, access context and limitations; mirrored URLs count once. Dictionary existence does not establish everyday preference. Evidence is sought for concrete disputes, false friends and audits rather than universally for ordinary low-risk cards. One lookup may support multiple claim types only when its observation truly does so. Batch retrieval/verification is permitted with candidate-level conclusions and provenance.

Version v3 dependencies must allow verifier execution before evidence audit on the low-risk route; v1/v2 records remain readable. Historical manifest pins remain unchanged: a reconsideration packet selects the attempt's recorded immutable v3 prompt set, whereas a normal new-batch packet selects its manifest pin. Both effective prompt version and questions participate in packet identity. A compatible successful old stage can be reused only if its effective prompt version, questions, input digest and upstream dependencies match; otherwise rerun it under v3. A failed later attempt does not erase an earlier compatible result. Historical HOLD is not a negative signal. Every retry/operation is checkpointed and capped. Independent candidates may run with bounded workers and provider throttling; within-candidate stage order, duplicate resolution, report closure, manifest mutation and ID/export stay serialized. Partial bundle fan-out resumes missing candidate/digest ingests and counts its provider operation once.

## Reporting, replay, and promotion

Open reports reconcile `generated = accepted + held + rejected + pending`; closed reports require zero pending. Report relation and confidence distribution, low/medium/high and fast/escalated paths, same/no-contrast waste separately from bad-translation rejects, duplicates, exact HOLD blockers, false-friend gates, recovery, cache and provider/retrieval work. Count model calls by unique operation ID, not stage records. Use explicit `unavailable` for absent historical/provider token, cost or timing; zero-card work/card is undefined.

The next validation uses the **same frozen 26 historical HOLD IDs**; no new candidate generation. It records original/new decision, risk, confidence, flags, path, reused/rerun evidence/stages, each remaining HOLD reason, and five named diagnostic pairs. `kamera/kamera` is an additional labeled archived scope check if absent from the 26. Replay acceptance is provisional and cannot mutate canonical TSV. Compare directly with the v2 0/25/1 and evidence-replay 1/24/1 distributions, distinguishing changed policy from extra calls/evidence.

Product throughput counts only newly **canonically promoted** accepted cards over an actual generation-to-export active wall-clock interval. Replay-only throughput is labeled experimental; historical end-to-end throughput remains unavailable. The long-term ordinary AI/expert ratio target is approximately 50 under comparable quality/timing, not a launch threshold. A small expert benchmark and sampled/stratified audits support comparison and tier calibration, never routine manual approval. If a pilot/handoff is later used, provisional IDs and TSV never enter canonical state; import candidate/evidence/operation history with digest checks, rerun current overlap/decision checks, then use guarded export. Partial or failed work cannot alter canonical data.

## Current v3.1 guarded export clearance

For each policy-v3.1 accepted candidate, `curation/batches/<batch-id>/promotion-eligibility.json` must contain a schema-1 batch record with `batch_id`, `batch_safety_brake: false`, and a `candidates` map keyed by candidate ID. Each eligible entry records `status: eligible`, `audit_route` (`risk-based`, `random-monitoring`, `other`, or `none`), `audit_verdict` (`cleared` or `not-required`), `decision_digest`, and `content_digest`. Digests use the canonical JSON digest in `curation.packets`: the decision excludes the report-only `candidate_id`; learner content excludes permanent `id`. The full current decision must equal the closed report entry. The content digest binds the final verified relation, resolved cue, target answers, tags, image, and false-friend contrast. A later correction requires fresh clearance for the revised content.

Risk-selected entries, including false friends, low/very-low accepted confidence, and strong review flags, require `risk-based`/`cleared`. Otherwise eligible clean entries may use `none`/`not-required`; random-monitoring is ongoing QA, not a prerequisite for their export. An explicit withheld/unresolved review result or batch safety brake blocks export. Random QA findings after release are corrected under the same permanent concept ID and ID-derived GUID. The general export command does not infer audit clearance from an AI ACCEPT or from historical promotion preview files.
