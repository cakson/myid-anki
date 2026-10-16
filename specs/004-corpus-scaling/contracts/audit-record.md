# Independent Risk-Audit Record Contract

Feature 004 adds an auditable adapter for required v3.1 risk review. It does not alter the v3.1 decision or export predicate. Records live at `curation/production-runs/<run-id>/audits/<slice-id>/<candidate-id>.json`; the parent manifest references each path and digest. Raw reviewer output and attempt events remain attached to the record for provenance and retry.

## Selection and independence

- Determine mandatory risk audit from the current Feature 003 export rule: escalated or false-friend risk path, `low`/`very-low` confidence, or a strong audit review flag. Record each concrete reason. Do not count the separate random-QA sample as mandatory clearance.
- An audit is a new review invocation with its own prompt/packet and attempt ID. It must not reuse the generation or production-verifier response as its verdict. The same configured model family may be used if the invocation and context are independent. Record reviewer tool/model, prompt version, and prior candidate-stage attempt IDs to make this check inspectable.
- Review current intended English sense, both language answers, final relation, and learner-facing cue/contrast. For a false friend, explicitly inspect each language meaning and the misleading contrast. A finding must name the affected claim or say that no material issue was found.
- An audit record is valid only for the decision and projected learner-content digests it reviewed. Any relevant revision invalidates clearance and requires review again before promotion.

## Required fields

| Field | Type and rule |
| --- | --- |
| `schema_version` | Integer `1`. |
| `run_id`, `slice_id`, `candidate_id` | Nonempty stable IDs matching the referenced parent/slice/candidate. |
| `route`, `selection_reasons` | `route="risk-based"`; nonempty list of current v3.1 trigger reasons. Random QA uses the separate QA record, never this route. |
| `decision_digest`, `content_digest`, `packet_digest` | Digests of current v3.1 decision, final projected learner row, and independent audit packet. |
| `attempt_id`, `reviewer`, `reviewed_at` | Unique attempt ID; reviewer tool/model plus invocation ID and prompt version; timestamp. Invocation ID differs from generation/verifier attempt IDs. |
| `claim_reviews` | Nonempty list of claim IDs/subjects, observed conclusion, evidence references or explicit evidence limitation, and whether a concrete learner risk remains. |
| `verdict` | `cleared`, `needs-correction`, or `withheld`. Only `cleared` can produce the export value `audit_verdict="cleared"`. |
| `finding_class`, `rationale` | `none`, `learner-critical-answer`, `cue-content`, or `metadata-only`; concise claim-specific explanation. `cleared` cannot coexist with an unresolved material learner risk. |
| `correction_refs` | Links to correction/revision events, empty if none. A correction to learner content invalidates this record's digests. |
| `elapsed_ms`, `model_calls`, `input_tokens`, `output_tokens`, `retrievals` | Nonnegative values when measured; otherwise `null` plus an `unavailable_reason`. Separate from production and random-QA costs. |

## State and retry rules

1. Selection creates a pending candidate audit reference. Persist the packet and its digest before the reviewer call; persist raw response before validation/ingest. A failed or malformed attempt records its error and remains pending, without linguistic REJECT.
2. Validate identifiers, independence, claim reviews, verdict consistency, and decision/content digests before marking the audit complete. Repeating the same completed attempt and digests returns the prior result; a conflicting replay is rejected.
3. `needs-correction` or `withheld` blocks eligibility. A material correction uses Feature 003 reopen/revise/finalize and refreshes its report; a changed accepted decision/content gets a new independent audit record before clearance. An unresolved issue remains withheld.
4. The eligibility writer derives `audit_route="risk-based"` and `audit_verdict="cleared"` only from a valid current `cleared` record. It derives `not-required` only when the current v3.1 export predicate requires no risk audit. This writer never treats random-QA selection as required audit clearance.
5. At parent closure, count selected, completed, corrected, withheld, learner-critical, cue/content, and metadata-only audit results and their measured or unavailable costs separately from production curation and random QA.
