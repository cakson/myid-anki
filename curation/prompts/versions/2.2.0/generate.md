# Generate contrastive candidates (prompt set 2.2.0)

You are the discovery role. Propose only the requested bounded number of NEW Indonesian ↔
Malaysian Malay concepts for the supplied practical topic. Prefer different ordinary
vocabulary and useful form differences. False friends are hypotheses needing a later strict
gate. Exclude identical forms, duplicate concepts, and alternate English labels of any
supplied learner or historical candidate.

For each candidate, choose **one** neutral English concept. The learner-visible `english` cue
must identify the same sense as both language answers. Keep it concise; add a short qualifier
only if needed, such as `school score` rather than broad `grade`. Avoid cues and `sense` values
that join different meanings with “or,” such as the act *or* amount of payment. Do not pair a
general item with a subtype, a final date with an exact clock time, or a formal term with an
everyday term as if register were a national difference. The `sense` is a short internal
clarification of that same cue, not a way to rescue an ambiguous learner-visible cue.

Before proposing `different-common-word`, consider ordinary synonyms in **both** varieties.
A shared synonym does not automatically invalidate a useful preference, but if both proposed
forms are normal on both sides and preference is unclear, propose a different concept. The
mere existence of an alternate in a dictionary is not evidence that it is ordinarily
preferred. Do not fabricate frequency or source claims.

Use a specific category tag and unique temporary candidate IDs. Do not assign permanent IDs
or claim acceptance. Return only the versioned `generate` JSON schema with `candidate_id`,
`english`, `indonesian`, `malaysian`, `sense`, and `tags` for every candidate.
