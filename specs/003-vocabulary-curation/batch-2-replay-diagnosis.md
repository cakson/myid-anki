# Batch 2 fixed-corpus diagnosis before policy replay

The frozen inputs are the 50 candidates in `second-batch-50-state.json`, their original
normalization/verifier records, and the independent 40-card audit in
`second-batch-50-audit.json`. This table classifies all 16 non-clean provisional accepts.
The primary labels are mutually exclusive; secondary causes may overlap. They describe
the audit finding, not a new linguistic verdict or a rewrite of historical decisions.

| Candidate | Audit outcome | Primary cause | Secondary signal | What the old fast path missed |
| --- | --- | --- | --- | --- |
| `daily-02` faucet | minor | metadata-only problem | target answer alternative | `paip` was valid; an alternate precise term was treated as a required substitution by the auditor. |
| `daily-03` sink | minor | ambiguous English cue | mismatched sense | `sink` could include a kitchen basin outside usual Indonesian `wastafel` scope. |
| `daily-09` iron clothes | minor | metadata-only problem | shared synonym | Existing `menggosok pakaian` was valid; rationale should note Malay `menyeterika`. |
| `daily-10` tidy up | minor | ambiguous English cue | verb polysemy | A room qualifier secures the household sense of `mengemas`. |
| `shopping-02` cash | minor | relation problem | cognate form | `uang`/`wang` is a useful `similar` form contrast, not unrelated common words. |
| `shopping-08` service | minor | mismatched sense | metadata only | Internal sense text reversed or blurred provider/customer scope; learner answers remained usable. |
| `social-09` confident | minor | metadata-only problem | synonym/phrase variation | Rationale understated Malay syntactic alternatives. |
| `travel-04` traffic jam | minor | ambiguous English cue | register | Standard nouns fit `traffic congestion` more precisely. |
| `work-03` grade | minor | ambiguous English cue | sense mismatch | `markah` fits a numerical school score, not every grade category. |
| `work-07` uniform | minor | metadata-only problem | shared borrowing | Rationale needed to acknowledge alternatives in both languages. |
| `daily-05` vacuum cleaner | unsafe/unresolved | wrong preference assumption | shared English borrowing | Verifier acknowledged alternatives but asserted a localized Malay form as ordinary default without resolving preference. |
| `shopping-06` payment | unsafe/unresolved | mismatched sense | verifier missed concrete risk | Cue/sense combined the *act* of paying with the *amount* paid. |
| `social-04` meet someone | unsafe/unresolved | shared synonym | weak contrast | `bertemu` and `berjumpa` may both be ordinary on both sides. |
| `social-06` visit someone | unsafe/unresolved | mismatched sense | shared synonym/register | Broad social visit and more purpose-specific/formal `melawat` were treated as equivalent defaults. |
| `travel-10` intersection | unsafe/unresolved | shared synonym | weak contrast | `simpang` and `persimpangan` may both be ordinary on both sides. |
| `work-08` deadline | unsafe/unresolved | wrong preference assumption | date/time cue, shared borrowing | Verifier noted the date/time caveat but did not test whether the contrast was reliable in everyday usage. |

**Primary-cause counts (16):** ambiguous English cue 4; mismatched sense 3;
shared synonym 2; wrong preference assumption 2; relation problem 1;
metadata-only problem 4. No confirmed target-language answer correction occurred in
Batch 2. The audited answer substitutions for `daily-02` and `daily-09` were not applied
because the original Malay terms were attested for the intended sense. There were no
promotion-formatting errors in this set.

The reusable patterns are (1) one English cue spanning different senses or scopes,
(2) a shared everyday synonym weakening an asserted national preference, and
(3) confidence flags that encode missing optional research as if it were concrete risk.
The revised verifier must classify the *role* of a shared synonym: a useful preference
despite overlap, a weak or misleading contrast, or an alternate form that merely exists
without being preferred. Dictionary existence alone cannot resolve preference.
