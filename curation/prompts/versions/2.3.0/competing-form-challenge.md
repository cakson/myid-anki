# Targeted competing-form challenge (prompt set 2.3.0)

You did not generate or initially verify this vocabulary. A separate verifier named
a specific credible competing everyday form for a proposed `different-common-word`
card. Assess that **one named alternative** in the same intended sense. Do not
research unrelated synonyms or generate new cards. Use concise saved evidence when
present. Dictionary existence alone does not prove everyday preference; lack of a
frequency statistic alone does not defeat a useful contrast.

Answer four questions explicitly in `assessment`:

1. Is the named form normal everyday usage in the indicated language and same sense?
2. Does it materially weaken the proposed Indonesian/Malaysian preference?
3. Does enough practical preference difference remain to teach a useful card?
4. Would the proposed pair, unqualified, likely mislead a learner?

Use these **exact** JSON keys for those four booleans, in this order:
`normal_everyday_same_sense`, `materially_weakens_preference`,
`useful_difference_remains`, `unqualified_card_misleads`. Do not paraphrase
the key names. The output parser rejects any replacement key.

Return exactly one `outcome`:

- `contrast-remains-useful`: the alternative does not defeat a useful practical contrast;
- `contrast-needs-qualification`: a concise cue or internal usage note makes it safe;
- `preference-materially-uncertain`: a concrete unresolved ordinary-preference issue remains;
- `no-meaningful-preference-contrast`: affirmative basis that the proposed national
  preference is not reliable enough to teach.

Return `rationale` with a concrete, candidate-specific reason, `cue_rewrite` (empty
unless a concise corrected English cue is necessary), `usage_note` (empty unless
qualification is needed), and `support` as a short list of saved evidence references
or reasoning signals used. Do not invent source references. If the challenge cannot
decide within this focused pass, use `preference-materially-uncertain`. A challenge
does not itself change accepted learner source data; corrections must be applied
before promotion. False friends continue through their separate strict gate.

If an unqualified card would mislead and only an internal usage note can resolve it,
choose `preference-materially-uncertain`; the usage note is not shown on the current
learner card. Choose `contrast-needs-qualification` with `unqualified_card_misleads=true`
only when a concise **learner-visible English cue rewrite** removes the risk.
