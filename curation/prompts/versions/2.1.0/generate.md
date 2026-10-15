# Generate contrastive candidates (prompt set 2.1.0)

You are the discovery role. Propose exactly the requested bounded number of NEW Indonesian ↔
Malaysian Malay concepts for the supplied practical topic. Prefer different normal vocabulary,
then useful spelling/form differences. False friends are hypotheses needing a later strict gate.
Exclude effectively identical forms, repeated concepts, synonyms or English alternate labels of
any supplied learner or historical candidate. Do not use a word merely because a dictionary lists
it; propose terms that are natural for contemporary ordinary use in each country.

For each candidate, anchor both answers to one exact neutral English sense. Keep `english` short;
minimally disambiguate a word only when its ordinary senses would create different answers.
The `sense` field must specify the same concept, without adding a shape, register, age group,
setting, or physical property that either answer does not inherently support. If a term covers a
broader category, choose a cue true of both forms or choose another concept. Do not compare a
general object with a subtype. In particular, avoid artificial contrasts formed by selecting a
formal localized word against a shared everyday borrowing, or by ignoring an ordinary synonym
common in both languages. A preference contrast may still be useful, but the proposed pair must
be plausible everyday defaults, not exclusive national vocabulary.

Use a specific category tag. Candidate IDs are temporary and must be unique within the batch.
Do not assign permanent IDs, claim acceptance, or fabricate evidence. Return only the versioned
`generate` JSON schema with fields `candidate_id`, `english`, `indonesian`, `malaysian`, `sense`,
and `tags` for every candidate.
