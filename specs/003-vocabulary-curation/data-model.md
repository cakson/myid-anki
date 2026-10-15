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
| `candidate_limit` | Maximum proposed candidates | Initial batches: at most 12 |
| `prompt_set_version` | Version of role instructions | Required |
| `created_at` | UTC curation timestamp | Required |
| `status` | `open` or `closed` | Closed only after all candidates have deliberately finalized outcomes and report reconciles; any pending candidate keeps it open |

## Candidate and claim records

Each generated candidate has a batch-local `candidate_id` such as `transport-01`. It has no permanent `id` until accepted and exported. Record the raw proposal, normalized comparison keys, English sense description, suggested Indonesian/Malaysian terms, proposed relation, alternatives, and topic tags. Normalized keys aid duplicate search only; they never silently replace learner text.

For each important claim, maintain `claim_id`, `claim_type` (`meaning`, `locale-usage`, `preferred-choice`, `relation`, or `misleading-contrast`), language/locale, exact proposition, and links to supporting or contradicting evidence IDs. A `different-common-word` proposal needs within-locale comparison claims for both languages. A `false-friend` proposal needs two meaning claims and a misleading-contrast claim. Its structured contrast has `misleading_form`, `misleading_language`, `actual_meaning`, and supporting claim IDs; the concise learner `contrast` is derived only after these components are evidenced.

## Stage result

Each executed role result is separate and append-only within the candidate record. The role sequence is `generate`, `normalize-and-dedupe`, `indonesian-usage`, `malaysian-usage`, `relation-proposal`, `evidence-audit`, `independent-verification`, `adversarial-review`, and `decision`; all applicable roles must complete for acceptance. Record role, prompt version, model/tool identifier, timestamp, input artifact digest, consumed upstream record versions, structured output, and any parse or verification failure. For an early final `hold` or `rejected`, the decision lists every uncompleted role and whether it was skipped, failed, or interrupted; a status is not a fabricated role result. The verifier cannot receive the generator's rationale or proposed verdict. A completed stage may be reused after interruption only while its input digest, prompt version, and upstream versions still match; failed, malformed, missing, or dependency-invalidated stages must be rerun according to the workflow contract's cue, answer, relation, and evidence invalidation rules. Prior revisions remain inspectable.

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

## Decision and lifecycle

```text
generated -> researching -> pending | verified/challenged
                         pending -> researching | hold (explicit finalization)
                                      verified/challenged -> accepted | hold | rejected
                                                            accepted -> exported
```

Every candidate in a closed batch has exactly one deliberate final outcome. A missing, malformed, or interrupted stage leaves the candidate `pending` unless an investigated candidate is explicitly finalized as `hold` or `rejected` with a reason and uncompleted-stage statuses. A `same` relation with identical ordinary forms is rejected early as outside the contrast-only scope. `pending` blocks batch closure/export. `accepted` requires all mandatory stages, an unambiguous shared cue, two independent audited external signals covering key meaning/usage claims, no unresolved contradiction or duplicate, verifier approval, and resolved adversarial concerns. `false-friend` also needs independently evidenced meanings in both languages, an evidenced structured misleading contrast, and explicit agreement of verifier and adversary. A candidate can be explicitly finalized as `hold` with reason after investigation identifies missing evidence or unresolved disagreement; `rejected` records a disproven claim, confirmed duplicate, or unsuitable concept. Neither can be exported. Later reevaluation creates a new decision revision preserving the original.

The decision stores `outcome`, `relation` when supported, `confidence_basis` as named gate findings rather than an arbitrary score, `reason_codes`, `rationale`, and `decided_at`. A changed relation or cue invalidates prior approval and requires new verification.

## Learner concept

The strict TSV header is:

```tsv
id	english	indonesian	malaysian	relation	image	tags	contrast
```

| Column | Rule |
|---|---|
| `id` | Exactly six ASCII digits, unique, permanent; `000001` remains the existing car concept |
| `english` | Nonempty concise neutral sense cue |
| `indonesian` | Nonempty contemporary common Indonesian answer |
| `malaysian` | Nonempty contemporary Malaysian Malay answer |
| `relation` | Exactly one of the four specified relation values |
| `image` | Empty or existing safe repository media reference |
| `tags` | Empty or existing whitespace-separated tag tokens |
| `contrast` | Required only for `false-friend`; empty for all other relations; concise misleading form and actual meaning |

Existing rejection of malformed rows, empty required values, outer whitespace, invalid IDs, duplicate IDs, and unsafe media remains. No curation evidence or source URLs go into this table.

## ID ledger

`curation/id-ledger.json` records each ever-assigned six-digit ID, originating candidate or prior source row, first assignment date, and semantic concept key. Assignment records are logically append-only: they are never changed, deleted, or reused, including after a learner row is removed. `active` is derived when the ID is present in the current TSV; otherwise it is `retired`. The initial `000001` row is backfilled as an existing assignment. An export that updates an accepted concept keeps its ID. An export of a new concept allocates the next unused ID only after all gates and duplicate checks pass. The TSV IDs must be a subset of ledger IDs after recovery.

The existing `000001` row must receive the same retrospective evidence and decision review as new concepts. Backfilling the ledger is not acceptance by itself; if the row fails, retire the ID and remove the row only when other accepted source data makes the deck nonempty.

## Batch report

`report.json` and a readable summary contain generated, accepted, held, rejected, and pending counts; relation distribution among accepted entries and, separately, all proposals; duplicate detections/resolutions; investigation items; verification/evidence failures; and reasons. Every open report requires generated = accepted + held + rejected + pending and cannot authorize export. A closed report requires pending = 0 and generated = accepted + held + rejected. The report retains enough coded outcomes to compute future rejection, duplicate, correction, and false-friend error rates after feedback data becomes available.

## Export recovery journal

`curation/export-journal.json` exists only while export is in progress or needs recovery. It identifies the batch set, prior TSV/ledger backup locations and digests, prospective digests, and transaction phase. Export validates prospective files, writes recoverable backups and journal, replaces the ledger first and TSV last, and clears the journal only after both agree. Handled errors roll back both. On interruption, the next curation operation must finish or roll back recovery before another export; release is blocked while the journal exists. The deck builder still reads only the learner TSV and never consults this curation journal.
