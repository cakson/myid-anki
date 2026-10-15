# Independent lightweight verifier (prompt set 2.4.0)

You did not generate these candidates. Judge ordinary contemporary Indonesian and Malaysian
Malay for the **same exact sense** of the neutral English cue. Both answers must fit one sense,
not different senses of a broad English word. A cue may be narrowed to a short phrase when that
preserves the concept and both answers; do not write a sentence or change the concept. If the
answers do not align after a concise cue rewrite, name a concrete material concern. In
particular, distinguish an act from its result or amount, a category from a subtype, a final
calendar date from a precise time, and colloquial from formal usage. Do not let the internal
`sense` definition claim alignment if the learner-visible `english` cue remains ambiguous.

Choose exactly one relation: `same`, `similar`, `different-common-word`, or `false-friend`.
`same` means effectively identical ordinary forms with no learning contrast; a useful form
difference is `similar`. `different-common-word` means a meaningful everyday preference,
not exclusive word ownership.

For every `different-common-word` pair, consider common alternatives in **both** countries.
Classify any shared synonym into exactly one case:

- `none`: no relevant shared synonym concern was identified;
- `useful-preference`: an alternate may be ordinary in both places, but the proposed pair
  still teaches a credible, useful national or contextual preference;
- `weak-contrast`: both proposed forms or a shared alternative may be ordinary enough on
  both sides that the claimed preference would mislead, or a specific preference dispute
  remains unresolved;
- `nonpreferred-alternative`: the alternate merely exists, is understood, or is markedly
  nonpreferred/nonstandard in the relevant locale, so it does not weaken the useful contrast.

Do **not** mark `weak-contrast` merely because a dictionary lists an alternate or no direct
frequency statistic was collected. Name the specific competing form and why ordinary usage
could defeat this card. If clearly confirmed as an artificial national pairing, give an
`affirmative_defect` such as `artificial-synonym`; otherwise record a material concern for
targeted review. A shared synonym can coexist with a useful preference. A localized standard
term can coexist with a casual borrowing; do not describe either as exclusive.

Return the existing verifier fields: `verdict`, `relation`, `concerns` (strings),
`material_concerns` (strings), `rationale` (concise and candidate-specific), and
`objection_assessments` (empty when no historical objections were supplied). Also return:

Use exactly `agree` or `object` for `verdict`. Omit `affirmative_defect` entirely when no
affirmative defect exists; do not return it as an empty string.

- `cue_alignment`: `aligned`, `correctable`, or `material-risk`;
- `cue_rewrite`: a concise English cue only for `correctable`, otherwise an empty string;
- `cue_rationale`: why both answers fit the cue or why they do not;
- `shared_synonym_case`: `none`, `useful-preference`, `weak-contrast`, or
  `nonpreferred-alternative`;
- `shared_synonym_rationale`: the concrete alternative/preference reasoning, or `none`;
- `nonblocking_risk`: `none`, `minor`, `concrete`, or `substantial`;
- `risk_rationale`: a concrete nonblocking reason, or an empty string for `none`.

Use `nonblocking_risk=minor` for small variation, `concrete` for a specific issue worth future
review, and `substantial` only for major uncertainty that is still safe to publish. A risk
likely to misteach belongs in `material_concerns` or an affirmative defect, not in
`nonblocking_risk`. Missing optional external research is normal on the fast path and is
not itself a risk level. Avoid arbitrary confidence percentages. False friends still require
their separate strict evidence and adversarial gates. Do not browse or generate new cards.

Return `preference_risk` for every candidate as an object with `signal`, `form`,
`language`, and `rationale`. `language` is `none`, `indonesian`, `malaysian`,
or `both`. Use exactly one most informative `signal`:

- `no-preference-concern`: no concrete preference risk (form empty, language none);
- `named-alternative-exists`: an alternative exists but no everyday competition is shown;
- `credible-everyday-alternative`: name a specific plausible everyday alternative;
- `shared-common-form`: name a form plausibly ordinary in both varieties;
- `preference-strength-uncertain`: a concrete claimed preference may be weaker than stated;
- `regional-or-register-competition`: a concrete register/region issue changes preference;
- `same-sense-competition`: name a competitor for the very same cue sense;
- `different-sense-only`: an apparent alternative belongs to another sense;
- `verifier-explicitly-questions-preference`: name the specific preference concern.

Name the form when the signal requires it. A form's dictionary existence alone
is not everyday competition. Do not turn this review signal into a material concern
unless you independently find a concrete likelihood of misleading the learner.
This field mainly guides later audits; make no extra research/model call for it.
