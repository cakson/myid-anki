# Data Model: AI-First Vocabulary Curation

## Overview

The authoritative active learner source is `data/vocabulary.tsv`. Curation records explain how candidates reached a decision but are never inputs to `myid-anki build`. The ID ledger preserves assignments even when an active concept is removed. All records are UTF-8 and version-controlled.

## Batch manifest

One record per bounded curation run under `curation/batches/<batch-id>/manifest.json`.

| Field | Meaning | Rule |
|---|---|---|
| `batch_id` | Stable run label | Unique, filesystem-safe |
| `topic` | Practical vocabulary category | Nonempty |
| `scope` | Included senses and excluded specialties | Explicit |
| `candidate_limit` | Maximum proposed candidates | Historical batches retain their original caps; new batches stay bounded |
| `prompt_set_version` | Version of role instructions | Required |
| `created_at` | UTC curation timestamp | Required |
| `status` | `open` or `closed` | Closed only after all candidates have deliberately finalized outcomes and report reconciles; any pending candidate keeps it open |

## Candidate and claim records

Each generated candidate has a batch-local `candidate_id` such as `transport-01`. Its stable identity is `(batch_id, candidate_id)`; the same local ID in another batch is valid. It has no permanent `id` until accepted and exported. Record the raw proposal, normalized comparison keys, English sense description, suggested Indonesian/Malaysian terms, proposed relation, alternatives, and topic tags. Normalized keys aid duplicate search only; they never silently replace learner text.

For each important claim, maintain `claim_id`, `claim_type` (`meaning`, `locale-usage`, `preferred-choice`, `relation`, or `misleading-contrast`), language/locale, exact proposition, and links to supporting or contradicting evidence IDs. A `different-common-word` proposal needs within-locale comparison claims for both languages. A `false-friend` proposal needs two meaning claims and a misleading-contrast claim. Its structured contrast has `misleading_form`, `misleading_language`, `actual_meaning`, and supporting claim IDs; the concise learner `contrast` is derived only after these components are evidenced.

## Stage result

Each executed role result is separate and append-only within the candidate record. The role sequence is `generate`, `normalize-and-dedupe`, `indonesian-usage`, `malaysian-usage`, `relation-proposal`, `evidence-audit`, `independent-verification`, `adversarial-review`, and `decision`; only roles required by the recorded risk path must complete for acceptance. Record role, prompt version, model/tool identifier, timestamp, input artifact digest, consumed upstream record versions, structured output, and any parse or verification failure. For an early final `hold` or `rejected`, the decision lists every uncompleted role and whether it was skipped, failed, or interrupted; a status is not a fabricated role result. Fast-path acceptance records adversarial review as `skipped-low-risk` with policy version and reason, not as a fabricated role result. The verifier cannot receive the generator's rationale or proposed verdict. A completed stage may be reused after interruption only while its input digest, prompt version, and upstream versions still match; failed, malformed, missing, or dependency-invalidated stages must be rerun according to the workflow contract's cue, answer, relation, and evidence invalidation rules. Prior revisions remain inspectable.

## Evidence record

| Field | Meaning | Rule |
|---|---|---|
| `evidence_id` | Candidate-local reference | Unique |
| `claim_ids` | Claims addressed | At least one |
| `source_group` | Independent underlying publisher/corpus | Used for two-signal count |
| `source_title`, `publisher` | Identifiable provenance | Required |
| `url_or_query` | Direct page or reproducible corpus query | Required |
| `accessed_at` | UTC date/time of inspection | Required |
| `observation` | Short paraphrase or small excerpt | Claim-specific; avoid copying long source text |
| `locale`, `register`, `genre` | Applicability of evidence | Record known limitations |
| `stance` | `supports`, `contradicts`, `inconclusive` | Required |
| `audit_method` | How the page or corpus result was inspected | `retrieved-page`, `corpus-query`, or `manual-inspection` |
| `audit_observation_ref` | Separate evidence-audit stage record and observed page location/query result | Required before support counts; cannot be set by an unverified model citation |
| `audited` | Derived state from a completed separate audit record | Not accepted as a bare AI-supplied boolean |
| `limitations` | Access, age, scope, or ambiguity | Required when material |

Two pages from one dictionary or mirrored content share a `source_group` and count as one independent signal. The audit record captures a short observed excerpt or paraphrase, its page location or query, access method, timestamp, and the claim it supports or weakens; the independent verifier can inspect the same reference. AI prose, a bare `audited=true`, or an unchecked URL is not evidence. Dictionary listings may support existence or sense but not everyday preference by themselves.

## Overlap record

Store `other_candidate_id` or `permanent_id`, overlap type (`exact`, `morphology`, `synonym`, `semantic`), reviewer rationale, and resolution (`distinct`, `merge`, `reject`, `unresolved`). An unresolved overlap blocks acceptance. A confirmed duplicate does not receive a new permanent ID.

## Recalibration extensions (policy v2)

These extend existing append-only records; historical files are not rewritten. Fields absent in old records are explicitly `unmeasured`, `not-assessed`, or unknown, never inferred as zero.

| Entity | Required new information | Invariant |
|---|---|---|
| Risk assessment | `policy_version`, `path` (`ordinary-fast`, `escalated`, `false-friend`), risk signals, input/evidence digests, rationale, selected review requirements | Recompute after material input change; no self-approval by generation |
| Decision revision | Original `(batch_id, candidate_id)` ref, previous decision ref, policy version, outcome, typed reason, evidence/defect links, skipped/required stage statuses, reused/rerun work, report version | Only ACCEPT with applicable gate; HOLD for unresolved; REJECT for affirmative exclusion; canonical handoff changes append a revision linked to the preserved pilot verdict |
| Inspected evidence cache | Observation ID; normalized lemma/form, sense, locale, claim/proposition and usage context; canonical source locator/version; access time/method; observed content; publisher/source group; stance and limitations; originating inspection | Reuse means relink to a current claim, recheck relevance and source independence, and preserve lineage; a prior audit verdict or URL alone is insufficient |
| Operation attempt | Unique operation ID, linked candidate and stage IDs, path, UTC start/end, monotonic elapsed, queue/rate-limit wait, status, actual provider/model/request ID, tokens/charge or unavailable reason, retrieval/cache counts, retry number, input/output digest | One bundled provider call has one operation ID even when several candidate events result; partial fan-out resumes by candidate/digest |
| Source-research operation | Unique retrieval operation ID; candidate/claim IDs; source locator or query; UTC/monotonic start/end; status; resulting inspection reference; explicit unavailable reason for unrecorded lookup | Count retrieval attempts from operation IDs, including failures/retries; inspection rows are evidence records and cannot stand in for retrieval attempts or latency |
| Provider invocation | Packet/input digest, configured adapter and argv identity, operation ID, response artifact/digest, parse/ingest status | Measured calls pass through the provider-neutral runner; manual packet/ingest has unavailable provider latency and usage |
| Budget state | Versioned limits and consumed counts for retrieval, verifier, adversary, conflict resolution, malformed-output retry, plus measurable elapsed/token/cost caps | Exhaustion is recorded; it is not linguistic disproof |
| Reconsideration | Original candidate identity and batch, original/updated policy/decision refs, compatible reused stages/evidence, invalidated/rerun stages, old/new relation/outcome, change reason, ID linkage | Never regenerate candidate or allocate another ID for an already assigned concept |
| Comparison cohort | Frozen matching rules, topic allocation, generation prompt/source-access conditions and rubric before generation; after one measured generation per cohort, frozen actual candidate IDs, dedicated ordinary-intent lane IDs, preliminary relation/risk/cue attributes, response digests, generation and ordinary-lane active intervals, logged evaluation-audit pause intervals, cache state, later path changes and matching exceptions | Actual candidate assignments to the dedicated ordinary lane freeze before locale research or policy decisions; later escalation cannot remove candidates or work from its elapsed interval, while elevated-risk cards cannot enter its ordinary numerator. No unrelated candidate work runs inside that interval, no outcome-based replacement occurs, and historical paired-policy replay is reported separately from end-to-end throughput |
| Pilot handoff manifest | Origin workspace/batch, composite `(batch_id, candidate_id)` identities, prompt/policy versions, file digests for candidate/stage events, evidence, operation records and audit refs, import result, handoff/recheck intervals | Reject a conflicting batch ID or duplicate composite identity within its batch; allow local candidate IDs used by other batches. Validate complete files before atomic import; exclude pilot TSV, temporary ledger/journal and provisional IDs; preserve pilot decisions and append linked revisions after canonical recheck |
| Quality audit / human benchmark | Frozen rubric/version; output ID and producing path hidden where practical; digest of evaluated English cue/sense, both answers, relation, applicable false-friend contrast and supporting claim/evidence set; sense/usage/relation/register/source/duplicate/false-friend findings; pass/fail/unresolved outcome with evidence refs; expert curation and independent audit intervals kept separate, raw/audit-passing counts | Same rubric applies to all exported comparator/pilot cards and expert output; a post-audit material digest change requires re-audit or exclusion from the adjusted numerator; audit is evaluation, not routine approval |

Operation records use stable IDs and nullable numeric usage fields with an explicit availability reason. Reports count **unique provider operations**, not candidate stage events, and **unique source-research operations**, not source-inspection rows; unrecorded manual retrieval count/latency is unavailable. Label isolated comparator/pilot exports as provisional benchmark output. Keep three distinct numerators: audit-passing isolated exports for the matched policy benchmark; pilot candidates newly promoted to canonical learner data with a passing frozen-rubric audit matching their final content/evidence digest for quality-adjusted canonical pilot throughput; and all newly promoted learner cards for raw release count. Historical recoveries or further-batch cards without the frozen audit remain outside every quality-adjusted numerator. Reconcile each provisional pilot identity to a canonical promotion, hold or rejection. The T076 intermediate target applies only to the like-for-like isolated benchmark. Compute the canonical AI/expert ratio from the frozen ordinary-intent lane's passing ordinary-fast canonical promotions and its dedicated generation-to-canonical-promotion active wall-clock interval against the ordinary expert benchmark. Keep later-escalated or discovered false-friend candidates and their work inside that lane and interval, but exclude their cards from the ordinary numerator and report their outcomes separately. Do not interleave unrelated candidate work; if the lane is empty, positive lane timing cannot be isolated, or the expert rate is zero/unavailable, mark the ratio undefined. A nonempty measured lane with zero ordinary-fast accepted cards yields a zero rate and ratio against a positive expert rate. Do not sum candidate latencies as a wall-clock substitute. A whole-release cards/hour rate requires complete active intervals for every included batch/reconsideration, measured as one wall-clock window for overlapping work; if any are unavailable, show the release count and mark its rate unavailable. Batch wall-clock includes queues, rate limits, retries, retrieval, applicable handoff/recheck and successful canonical export. Only explicitly logged external pauses between resumptions may be excluded; the frozen-rubric evaluation audit between provisional export and canonical promotion is one such pause, recorded with start/end and reason. Include any resumed correction, handoff, recheck and export work; report excluded audit duration and unadjusted calendar span. Keep independent audit time out of expert active curation time as well. Zero promoted cards makes work-per-card measures undefined; zero ordinary-fast cards in a nonempty measured lane still gives a defined zero AI/expert ratio when the expert rate is positive. A versioned rate table may support an estimated monetary cost; unknown price or tokens remains unavailable. Practical success requires the matched ordinary canonical ratio above 1 at equivalent quality; the long-term ratio target remains approximately 50.

## Decision and lifecycle

```text
generated -> researching -> pending | verified/challenged
                         pending -> researching | hold (explicit finalization)
                                      verified/challenged -> accepted | hold | rejected
                                                            accepted -> exported
```

Every candidate in a closed batch has exactly one deliberate final outcome. A missing, malformed, or interrupted stage leaves the candidate `pending` unless an investigated candidate is explicitly finalized as `hold` or `rejected` with a reason and uncompleted-stage statuses. A `same` relation with identical ordinary forms is rejected early as outside the contrast-only scope. `pending` blocks batch closure/export. `accepted` requires all risk-path stages, an unambiguous shared cue, two independent audited external signals covering key meaning/usage claims, no unresolved contradiction or duplicate, and verifier approval; an ordinary low-risk card may bypass adversarial review. `false-friend` also needs independently evidenced meanings in both languages, an evidenced structured misleading contrast, and explicit agreement of verifier and adversary. A candidate can be explicitly finalized as `hold` with reason after investigation identifies missing evidence or unresolved disagreement; `rejected` requires a typed affirmative exclusion basis, such as disproven claim, confirmed duplicate, or identical ordinary vocabulary. Missing evidence, retrieval failure, generic uncertainty, and budget exhaustion alone lead to hold when material uncertainty remains. Neither can be exported. Later reevaluation creates a new decision revision preserving the original.

The decision stores `outcome`, `relation` when supported, `confidence_basis` as named gate findings rather than an arbitrary score, `reason_codes`, `rationale`, and `decided_at`. A changed relation or cue invalidates prior approval and requires new verification.

## Learner concept

The strict TSV header is:

```tsv
id	english	indonesian	malaysian	relation	image	tags	contrast
```

| Column | Rule |
|---|---|
| `id` | Exactly six ASCII digits, unique, permanent; retired `000001` remains reserved for its original car concept |
| `english` | Nonempty concise neutral sense cue |
| `indonesian` | Nonempty contemporary common Indonesian answer |
| `malaysian` | Nonempty contemporary Malaysian Malay answer |
| `relation` | Exactly one of `similar`, `different-common-word`, or `false-friend`; `same` is candidate-only and rejected in learner data |
| `image` | Empty or existing safe repository media reference |
| `tags` | Empty or existing whitespace-separated tag tokens |
| `contrast` | Required only for `false-friend`; empty for all other relations; concise misleading form and actual meaning |

Existing rejection of malformed rows, empty required values, outer whitespace, invalid IDs, duplicate IDs, and unsafe media remains. No curation evidence or source URLs go into this table.

## ID ledger

`curation/id-ledger.json` records each ever-assigned six-digit ID, originating candidate or prior source row, first assignment date, and semantic concept key. Assignment records are logically append-only: they are never changed, deleted, or reused, including after a learner row is removed. `active` is derived when the ID is present in the current TSV; otherwise it is `retired`. The initial `000001` row is backfilled as an existing assignment. An export that updates an accepted concept keeps its ID. An export of a new concept allocates the next unused ID only after all gates and duplicate checks pass. The TSV IDs must be a subset of ledger IDs after recovery.

The original `000001` car row received retrospective review and was withheld; its ID remains retired in the ledger. Reconsideration may revisit its original candidate record, but cannot repurpose its ID for another concept.

## Batch report

`report.json` and a readable summary contain generated, accepted, held, rejected, and pending counts; relation distribution among accepted entries and, separately, all proposals; duplicate detections/resolutions; investigation items; verification/evidence failures; and reasons. Every open report requires generated = accepted + held + rejected + pending and cannot authorize export. A closed report requires pending = 0 and generated = accepted + held + rejected. The report retains enough coded outcomes to compute future rejection, duplicate, correction, and false-friend error rates after feedback data becomes available.

## Export recovery journal

`curation/export-journal.json` exists only while export is in progress or needs recovery. It identifies the batch set, prior TSV/ledger backup locations and digests, prospective digests, and transaction phase. Export validates prospective files, writes recoverable backups and journal, replaces the ledger first and TSV last, and clears the journal only after both agree. Handled errors roll back both. On interruption, the next curation operation must finish or roll back recovery before another export; release is blocked while the journal exists. The deck builder still reads only the learner TSV and never consults this curation journal.
