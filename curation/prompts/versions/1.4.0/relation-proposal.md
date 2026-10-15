# Propose a relation (prompt set 1.4.0)

Align both terms to one concise English sense. Select exactly one of `same`, `similar`,
`different-common-word`, or `false-friend` from common usage, not dictionary possibility.
Use `same` only when the written everyday forms are identical. Use `similar` for
recognizably related but nonidentical forms, such as a one-letter spelling difference.
Use `different-common-word` for distinct everyday lexemes, not mere spelling variants.
`same` records a detected no-contrast candidate for rejection; it never enters learner data.
Copy the candidate's `english` field exactly into the output. If that cue is too ambiguous,
set `aligned` to false and suggest a concise corrected cue in `semantic_alignment`;
do not silently change the candidate. A corrected cue needs a recorded candidate revision
and fresh downstream research.
For different words, compare everyday alternatives within each locale at the same register.
For a false friend, specify the misleading form, the language in which it misleads, and its
actual meaning as separate facts. This is a proposal, never approval.

Return JSON only: `{"schema_version":1,"role":"relation-proposal","model":"MODEL/TOOL",
"result":{"english":"...","relation":"same|similar|different-common-word|false-friend",
"semantic_alignment":"...","aligned":true,"claims":[{"claim_id":"...","claim_type":"relation",
"proposition":"..."}],"contrast":{"misleading_form":"...",
"misleading_language":"indonesian|malaysian","actual_meaning":"...","claim_ids":[]}}}`.
Omit `contrast` except for false friends.
