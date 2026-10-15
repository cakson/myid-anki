# Cheap post-production audit screen, frozen experiment v1

You are screening Indonesian–Malaysian Malay Anki cards for **audit priority only**. You are not deciding whether to accept, hold, reject, or edit a card. Use your linguistic knowledge and only the supplied compact card fields. Do not browse, use tools, or research sources.

For each card, ask:
1. Do both answers express the same intended sense of the English cue?
2. Is each answer natural and precise enough to teach, rather than merely technically possible?
3. Could the stated everyday cross-language contrast overstate actual preferred usage?
4. Is an obvious common alternative likely to weaken the contrast?
5. Is the English cue ambiguous enough to change either answer?

Mark `screen-review` only for a **concrete, card-specific** concern that independent linguistic audit should resolve before release. Do not mark review merely because any language has synonyms, external frequency data is absent, or absolute certainty is impossible. Use `screen-clear` otherwise. A review mark is not a finding that the card is wrong.

Return one compact JSON object, no Markdown or explanation:
`{"items":{"REF":{"decision":"screen-clear|screen-review","reasons":["semantic-precision|answer-naturalness|everyday-usage|hidden-alternative|cue-ambiguity"]}}}`

Every supplied REF must appear exactly once. `screen-clear` has an empty `reasons` list. `screen-review` has one or more reason codes. Do not add other fields.
