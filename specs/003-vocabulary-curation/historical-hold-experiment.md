# Feature 003: bounded historical hold experiment

Date: 2026-10-13. Scope: 26 frozen historical holds from non-fixture batches. The exact
selection is in [historical-hold-sample.json](historical-hold-sample.json); per-candidate
decisions and instrumentation are in [historical-hold-replay.json](historical-hold-replay.json).
The replay copied all batch artifacts to a temporary workspace, ignored only the historical
explicit hold while computing a counterfactual policy-v2 decision, and reused compatible
candidate, evidence, verifier, adversarial, and overlap records. It did not regenerate
candidates, retrieve new evidence, change historical decisions, assign IDs, or promote cards.
The sample was purposive and stratified before inspecting policy-v2 outcomes; it cannot
estimate a population false-negative rate.
The read-only replay can be repeated with
`PYTHONPATH=src python scripts/historical_hold_experiment.py`; the model comparison is
checkpointed by `scripts/compare_historical_verifiers.py` and must be run deliberately
because it makes paid provider calls.

## Outcomes

| Measure | Result |
|---|---:|
| Historical decisions | 0 accept / 26 hold / 0 reject |
| Revised replay dispositions | 0 accept / 25 hold / 1 reject |
| Recovered false negatives | 0 |
| Genuine scope rejection | 1 (`technology-001:technology-07`, identical `kamera`) |
| Remaining plausible or disputed holds | 25 |
| Accepted through ordinary fast path / escalation | 0 / 0 |
| Ordinary-intent candidate fast-path usage | 0 of 25 (0%); 0 of 12 with assessable risk |
| Risk classification | 13 escalated / 13 not yet assessable |

The 25 replay holds are computed from policy-v2 `pending` results because their questions
remain unresolved. They are **experiment dispositions**, not new explicit final events in
the archived batches. The one rejection has an affirmative `no-cross-language-difference`
reason and is already outside this contrast-only deck's intended scope.

### Frozen candidate IDs and replay dispositions

| Candidate ID | Prior → replay | Main remaining gate |
|---|---|---|
| `clothing-001:clothing-01` | hold → hold | Evidence audit and verifier absent |
| `clothing-001:clothing-02` | hold → hold | Unsupported locale claims; verifier absent |
| `common-verbs-001:everyday-actions-01` | hold → hold | Evidence audit and verifier absent |
| `communication-001:communication-01` | hold → hold | Unsupported claims; verifier absent |
| `communication-001:communication-03` | hold → hold | Relation, audit, and verifier absent |
| `everyday-objects-001:everyday-objects-05` | hold → hold | Dictionary-only preference; verifier absent |
| `everyday-objects-001:everyday-objects-06` | hold → hold | Evidence audit and verifier absent |
| `food-001:foods-01` | hold → hold | Verifier disagrees; escalation unresolved |
| `food-001:foods-04` | hold → hold | Verifier concern and concrete prior preference objection |
| `food-001:foods-06` | hold → hold | Sense/preference objection; matched model disagreement |
| `health-001:health-01` | hold → hold | Verifier relation disagreement |
| `home-001:topic-02` | hold → hold | Prior adversary questions breadth of preference evidence |
| `home-001:topic-03` | hold → hold | Alternative Malaysian term and preference unresolved |
| `home-001:topic-04` | hold → hold | Verifier concern and relation disagreement |
| `home-001:topic-05` | hold → hold | One independent source group; verifier absent |
| `home-001:topic-06` | hold → hold | Single-retailer preference and alternatives unresolved |
| `home-001:topic-08` | hold → hold | Verifier disagrees |
| `places-001:places-01` | hold → hold | Preferred-use claims unsupported; verifier absent |
| `produce-001:produce-03` | hold → hold | Relation, audit, and verifier absent |
| `school-001:topic-05` | hold → hold | Independent evidence lacking; verifier absent |
| `school-001:topic-06` | hold → hold | Relation, audit, and verifier absent |
| `technology-001:technology-07` | hold → reject | Same ordinary form `kamera` in both languages |
| `transportation-001:transportation-01` | hold → hold | Legacy ID; prior objection to everyday-preference evidence |
| `transportation-001:transportation-04` | hold → hold | Verifier disagrees |
| `transportation-001:transportation-06` | hold → hold | Preferred-use evidence lacking; verifier absent |
| `university-001:university-study-03` | hold → hold | Verifier relation disagreement and context/frequency concern |

The sample covers completed independent reviews, evidence insufficiency, relation
uncertainty, a legacy-ID overlap concern (`transportation-01`), shared-form scope risk,
and harder semantic/preference disputes. It excludes the known malformed adjective
claim-ID cohort. The frozen source contains no accepted false friend in this sample;
the stronger false-friend gate was not measured here.

## Fast-path and escalation diagnosis

No candidate reached `ordinary-fast`. Of the 26 candidates, 13 lack at least one stage
required before a risk assessment. Among the 13 classified as escalated, all 13 carry
`register-ambiguity`, 10 carry `verifier-concern`, six carry `verifier-disagreement`, and
two carry `regional-ambiguity`. Trigger counts overlap. Six replay holds require an
adversarial result under the current rule; six have a prior adversarial objection without
the policy-v2 structured objection field and remain unresolved.

The register rule is over-broad: values such as `Neutral.` and `Neutral everyday usage`
are flagged because they do not exactly match a short whitelist. The region rule likewise
flags `No material regional restriction identified` because it omits the country name.
These are procedural false escalations. They must be corrected using parsed/structured
register and region judgments. A simple removal of those triggers would be unsafe:
`home-001:topic-02` would become fast-path eligible even though its saved adversary raised
a concrete unresolved question about normal everyday preference. Prior concrete objections
need a migration-aware risk signal until answered or shown immaterial.

## Work and throughput measurement

The policy replay itself performed **zero** new evidence retrievals and **zero** model calls.
It took 0.081 seconds summed across 26 local decisions. This measures deterministic replay
only, not the original curation work or an accepted-card production rate. Ten new model
calls were made solely for the separate matched verifier comparison below. Those successful
calls took 77.86 seconds in total; two additional startup attempts failed before reaching
a model (0.157 seconds) because CLI 0.160.0 could not load managed preferences. The
comparison then used the existing 0.153.0 CLI and repository connection helper. The
observed sampled work totals about 78.10 seconds including replay. There were no new
adversarial calls and no retries of linguistic review; the two tool startup failures are
recorded as retries separately.

Provider-reported successful-call usage totals **146,763 input tokens** and **2,777 output
tokens**. These Codex CLI counts can include session/system overhead and must not be read
as raw evidence-packet size. Request IDs and monetary charges were unavailable. Historic
model calls, retrievals, retries, tokens, cost, and active processing time remain unknown.
Because **zero** cards were accepted, average/median elapsed time and model calls *per
accepted card* are undefined; no accepted-cards/hour or AI/expert ratio is claimed.
Per-candidate counts, elapsed time, token availability, and final gate reasons appear in
the replay JSON. `observed_experiment_elapsed_ms` includes only newly measured replay and
comparison work; `full_curation_elapsed_ms` is null for every candidate.

## Matched Luna versus Sol verifier comparison

Five candidates were selected from the same sample before model responses were inspected.
Each model saw byte-identical candidate, locale-analysis, relation-proposal, and saved
evidence input for its pair, without prior verifier/adversarial output or live research.
The experiment capped each model/candidate pair at two CLI launch attempts and each
attempt at 180 seconds; after a successful response it made no further call. This was a
comparison stage, not an automatic override of the policy decision.
The comparison results and prompt digests are in
[historical-model-comparison.json](historical-model-comparison.json). The project-wide
curation route remains `gpt-5.6-luna`; `gpt-5.6-sol` was a local comparison only.

| Candidate | Luna | Sol | Gate implication |
|---|---|---|---|
| `food-001:foods-06` | supported | unresolved | Sol retained the Indonesian sense/preference gap |
| `home-001:topic-02` | unresolved | unresolved | Both seek broader everyday-preference evidence |
| `home-001:topic-03` | supported | unresolved | Sol retained source-independence/preference concerns |
| `transportation-001:transportation-01` | unresolved | supported | Sol found the saved passenger-car contrast sufficient |
| `university-001:university-study-03` | unresolved | unresolved | Both see a relation/context issue |

Luna used 32.27 seconds and 70,213 input / 1,523 output tokens across five successful
calls. Sol used 45.59 seconds and 76,550 input / 1,254 output tokens. The stronger model
resolved one Luna-unresolved case, but Luna supported two cases Sol held; agreement was
limited and no comparison response alone satisfies the independent curation gate. This
small, purposive subset provides no evidence that changing the global model would improve
accepted-card yield or cost per accepted card. Model prices were not available, so monetary
comparison is unavailable.

## Quality finding and next change

There are **no newly accepted cards** to audit for suspicious quality. Three model
responses marked a candidate supported, but each remains held by the actual policy replay
and/or saved concrete objections. The previous holds cannot yet be labeled recovered
false negatives. The single rejection is a genuine contrast-only scope failure; the other
25 are legitimate unresolved dispositions under the evidence currently stored, although
some escalation triggers are plainly mechanical false positives.

The next pipeline change should focus on **claim-relevant evidence retrieval and reuse**,
with a small policy correction first: normalize neutral register/region statements,
distinguish verifier hesitation from concrete concern, and carry forward prior concrete
objections when evaluating fast-path eligibility. Then collect the missing independent
usage/preference evidence for this same frozen sample under bounded calls and rerun it.
Do not globally switch from Luna, relax the two-independent-signal gate, or launch a larger
batch based on this zero-acceptance experiment.
