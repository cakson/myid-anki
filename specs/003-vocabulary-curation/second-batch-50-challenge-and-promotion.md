# Feature 003: competing-form challenge and guarded Batch 2 promotion

## Fixed evaluation and implementation

The experiment reused the exact 50 Batch 2 candidate IDs, the saved v3.1 replay,
and the completed independent audit. It did not generate a new candidate or alter
the historical decisions. The 16 non-clean accepted cards and their root causes
remain documented in [the diagnosis](batch-2-replay-diagnosis.md).

The experimental prompt set `2.3.0` adds a structured `competing_form` field to
independent verification: `none`, `weak-alternative`, or `credible-everyday` with
the named form, language, same-sense check, and rationale. Policy `3.2.0` sends
only an accepted `different-common-word` candidate with a credible named rival
to a separate focused challenge. The challenge has four explicit outcomes and
cannot accept a card that needs a learner-visible correction unless it supplies
a concise cue rewrite. No-rival and weak-alternative candidates keep the ordinary
fast path. The existing false-friend gate remains separate.

For the historical v2.2 verifier records, the replay first inspected only the
17 accepted `different-common-word` candidates whose saved verifier mentioned
a potentially useful shared alternative. It found 12 credible same-sense everyday
competitors. A separate Luna call then challenged those 12 using the candidate
and named competitor, without the first verifier's preference conclusion or
independent audit verdict. This preserves the distinction between detection and
challenge. The [machine-readable replay](second-batch-50-competing-form-replay.json)
retains the original detector output, independent challenge, attempts, and decisions.

## Fixed-corpus result

| Measure | v3.1 replay | Experimental v3.2 |
|---|---:|---:|
| ACCEPT | 40 | 36 |
| HOLD | 6 | 8 |
| REJECT | 4 | 6 |
| High / medium / low / very-low accepts | 16 / 16 / 8 / 0 | 16 / 12 / 8 / 0 |
| Known unsafe cards blocked by production | 2 of 6 | 2 of 6 |
| Independently audited good cards newly withheld | — | 4 |

Among the 12 focused challenges, five concluded `contrast-remains-useful`,
three `contrast-needs-qualification`, two `preference-materially-uncertain`,
and two `no-meaningful-preference-contrast`. The four new HOLD/REJECT decisions
were `daily-10` (minor cue correction), `shopping-09` (confirmed good),
`shopping-10` (confirmed good), and `travel-06` (confirmed good). Thus the
challenge did **not** catch more audited unsafe cards and incorrectly withheld
four audited safe cards. It fails the stated production success criterion.

| Audited unsafe candidate | Prior v3.1 | Trigger | Experimental result | Matches audit? |
|---|---|---|---|---|
| `daily-05` vacuum cleaner | ACCEPT / medium | Credible everyday form | ACCEPT / medium | No |
| `shopping-06` payment | ACCEPT / low | Credible everyday form | ACCEPT / low | No |
| `social-04` meet someone | HOLD | No challenge; already held | HOLD | Yes |
| `social-06` visit someone | HOLD | No challenge; already held | HOLD | Yes |
| `travel-10` intersection | ACCEPT / low | Classified weak alternative | ACCEPT / low | No |
| `work-08` deadline | ACCEPT / low | Credible everyday form | ACCEPT / low | No |

The medium-confidence unsafe `daily-05` still passes the challenge. It receives
the concrete `competing-form-reviewed` flag, allowing an audit policy to route
it for inspection, but this does not repair the production judgment. The
challenge also misclassifies the competing road term for `travel-10` as weak.
These are model-judgment limits, not missing general pipeline stages.

The added work was **12 Luna calls**, about **143.5 active seconds** (90.7 for
detection and 52.7 for independent challenge), **149,523 input tokens**, and
**14,648 output tokens**. Provider prices were unavailable. This is a
fixed-corpus diagnostic cost, separate from original Batch 2 production.

## Simulated production plus audit safety

The simulation audits every accepted low/very-low and false friend; medium/high
cards with concrete review flags, including a named credible competitor; and
deterministic 25% medium and 10% high samples. It routes **14 accepted cards**
to audit. Production withholds **2 of 6** known unsafe cards; the simulated
audit routes the other **4 of 6**, for **6 of 6** combined coverage in this
small known set. It also routes **4 of 24** confirmed-good cards to audit.
Audit routing is useful here, but it does not make the expensive experimental
challenge a good default: the prior v3.1 policy can also route flagged low cards,
and the challenge itself created four false HOLD/REJECT decisions.

The central curation configuration therefore remains at prompt set `2.2.0` and
decision policy `3.1.0`. Version `2.3.0` / `3.2.0` and its tests remain available
as a bounded experiment; existing batch manifests and artifacts are untouched.
The next experiment should test a better preference challenge on a separate
calibration set, especially whether evidence or a more capable targeted model
adds unique value without false HOLD inflation. This result does **not** justify
a 100-card autonomous batch yet. A final fresh 50-card calibration is the safer
next batch size after a targeted improvement; no such batch was started here.

## Independently audited Batch 2 promotion

The [audit-based preview](second-batch-50-promotion-preview.json) was revalidated
against the unchanged frozen production and audit digests. It contained exactly
34 corrected, independently audited safe cards and six withheld provisional
accepts. A guarded dry run found no duplicate concept or permanent-ID conflict.
The 34 safe cards were promoted using that preview, **not** experimental replay
decisions. The [promotion record](../../curation/promotions/second-batch-50.json)
retains candidate IDs, original and corrected content, audit reasons, confidence,
provenance, permanent IDs, and the six withheld candidates.

| Learner source | Count |
|---|---:|
| Before | 69 |
| Added | 34 |
| After | **103** |

The additions contain 32 `different-common-word` and two `similar` cards. No
`same`, HOLD, REJECT, or audit-withheld candidate was promoted. Existing learner
rows were carried into the atomic source commit without changing their permanent
IDs. The final `.apkg` has **103 notes and 103 cards**. All 103 GUIDs are unique
and equal the GUID derived from their permanent concept IDs; the existing deck
and note-model IDs are present in the package. Source validation passed at 103
concepts. The complete test suite passed **180 tests**, and Ruff passed.

Batch 2's old confidence metadata remains as recorded: 30 of the promoted cards
are `very-low` and four are `medium`. This preserves the audit and decision
history; those old tiers are not retroactively described as calibrated.
