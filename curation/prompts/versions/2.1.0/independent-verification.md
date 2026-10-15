# Independent lightweight verifier (prompt set 2.1.0)

You did not generate these candidates. For each, independently judge the exact English cue and
`sense`, both natural contemporary answers, and whether the contrast teaches a real difference.
Do not infer exact semantic alignment merely because both terms can translate a broad English
word. Check any cue qualifier such as object shape, school level, printed versus digital format,
or travel purpose against BOTH answers. If one answer is broader or narrower in a way that could
mislead the learner, name that exact mismatch under `material_concerns`; if it is harmless within
the stated sense, explain why under `concerns`.

Choose exactly one relation: `same`, `similar`, `different-common-word`, or `false-friend`.
`same` requires effectively identical ordinary word forms and means no learner contrast; it does
not mean merely that the two answers share a meaning. A useful spelling/form difference is
`similar`. A `different-common-word` is a preferred ordinary-form contrast, not a claim that the
other form is absent. For that relation, ask whether the proposed answer or a shared synonym is
also ordinary in the other country. If a shared ordinary word makes the proposed contrast
artificial, identify a concrete objection. If the pair still teaches a real preference, keep it
and state the overlap as a nonblocking caveat. Standard localized technology terms may coexist
with common English borrowings; do not describe them as exclusive national everyday choices.

Use `verdict=agree` when the card is useful and no material blocker remains. Put ordinary caveats
in `concerns`, with `material_concerns=[]`. Put a specific unresolved learner risk in
`material_concerns`, or an affirmative confirmed defect in `affirmative_defect`. Missing external
frequency evidence by itself is not material. Do not turn generic uncertainty into HOLD.
False friends retain separate evidence and adversarial requirements. Keep `rationale` concise,
candidate-specific, and honest about a real shared synonym, register, or cue caveat. Assess
historical objections only when supplied; otherwise use `objection_assessments=[]`.

Return only versioned verifier JSON with `verdict`, `relation`, `concerns`,
`material_concerns`, `rationale`, and `objection_assessments` for each candidate. Do not invent
new relation labels or research claims.
