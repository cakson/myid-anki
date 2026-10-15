# Feature 003 validation status

Status: in progress. The initial corpus gate remains open.

## Cost routing trial

The current central `reserve` cost policy sends every role to `gpt-5.6-luna`, with low reasoning
effort for discovery and locale research and medium effort for relation, evidence, verification,
and adversarial review. These are separate role invocations after deterministic prechecks;
the verifier sees only its isolated packet. `route --role ROLE` exposes the configured model and
reasoning effort. Ingestion records the invoked model separately from the response's claimed
model when `--actual-model` is provided.

The adjective batch exposed two avoidable costs: Luna classified `dingin`/`sejuk` as `similar`
and `sehat`/`sihat` as `different-common-word`, so both were held before evidence research.
Luna also reused claim IDs across roles; the six remaining audit outputs failed the claim-linked
evidence gate. New packets now stop before evidence audit when claim IDs collide, and newly
ingested role claims receive deterministic role prefixes. Verification packets are withheld
when the evidence gate fails. No adjective candidate was promoted to meet a count target.

The car retrospective run used Luna evidence audit, then a blinded Sol verifier and a separate
Sol adversarial reviewer. The reviewer objected to the unproven everyday-preference claim.
`000001` was put on hold and removed from the active source after other accepted entries were
available. Its permanent assignment remains in `curation/id-ledger.json`.

The bounded technology run generated eight candidates. Locale analysis held five before relation
research; a relation correction and a new pre-audit preference-claim check held the screen
candidate before external research. Luna audited computer and camera, and separate isolated Sol
verifier and adversarial calls reviewed each. Computer passed and became `000006`; camera remained
held because the adversary retained a cue-coverage concern. The first generation response had a
mechanical JSON delimiter error; the raw failed response and exact syntax repair are retained.
An initial normalization bundle also exposed self-comparisons. The bundle now explicitly excludes
each item's own archive entry, and ingestion rejects self-overlap before any candidate stage is
recorded. The evidence gate now derives `same` from audited meaning and common-use claims in both
locales, while `different-common-word` still requires preferred-choice claims.

The next communication batch generated eight candidates. Three were held immediately for cue or
register concerns, two more after locale analysis, and three after evidence audit could not
support every key claim. It closed with eight holds and no Sol calls or learner promotions. This
demonstrates that the current evidence discovery approach has a low acceptance yield for everyday
preference contrasts; expanding to 24 accepted concepts requires stronger source discovery, not
weaker gates or filler entries.

The everyday-objects trial generated eight candidates with prompt set `1.0.0`. Normalization
rejected three concepts that had already been investigated, including the accepted spoon.
Five novel concepts were held: the fork and eggplant claims lacked supported everyday-use or
preference observations, watermelon and sweet potato lacked supported national preference,
and the dishwashing-liquid cue did not align cleanly with the proposed Malaysian answer.
The evidence role also produced malformed joined-source records. Raw outputs and failed ingests
remain in the batch archive; no Sol call or learner promotion followed. This trial cost exposed
duplicate discovery and overconfident source descriptions. New batches therefore receive a
frozen concept index at generation, while prompt set `1.1.0` asks locale roles to make only
source-plausible preference claims and asks the audit role to separate sources and report
inaccessible pages honestly. Versions `1.0.0` and `1.1.0` are retained; existing batch decisions
still resolve against their original prompt digests. The effect on acceptance yield remains
unproven at this scale.

The first `1.1.0` produce batch generated six new concepts and found no archive overlaps.
The separate usage roles withheld five concepts because a required meaning or common-use
claim was not established, or a contrast's everyday preference remained uncertain. The
remaining corn concept initially stalled when direct KBBI and DBP pages were inaccessible.
A focused AI-assisted source inspection opened an Indonesian dictionary mirror, an
Indonesian retailer recipe, a Malay Wiktionary definition, and a recipe by a Malaysian
contributor. Each source's limits were recorded separately. A second Luna audit linked those
four observations to the meaning and usage claims. A blinded Sol verifier agreed with
`same`; an independent Sol adversary initially listed frequency limitations as concerns.
A clarification call explicitly separated unresolved objections from nonblocking source
limits, retained both adversarial outputs, and returned agreement with no unresolved
objection. Only then did the gate accept corn. It received `000007`; the other five
candidates remain held. This focused inspection cost substantially less audit output than
unbounded model source exploration, but it still required manual orchestration and has not
yet solved the low overall acceptance yield. The observed Codex CLI usage for this trial was
29,547 and 21,976 tokens for the separate six-item locale calls, 16,216 for an open-ended
corn audit, and 2,895 for the focused audit using recorded source inspections. These are
per-call tool reports, not a calibrated price estimate. The locale calls dominate this
trial's AI work; before scaling toward 24 entries, source discovery should be bounded and
reused across locale, audit, and challenge stages.

## Current learner source

The earlier source had six accepted concepts: kitchen, spoon, plate, sauce, computer, and corn.
Under the 2026-10-05 contrast-only policy, kitchen, computer, and corn were removed from active
learner data and their IDs retained as retired assignments. The active source now has three
concepts—spoon, plate, and sauce—all in food, with `similar` and `different-common-word`
relations. The initial target of 24 accepted concepts across at least three categories and all
three eligible relation types is not met.

The transportation batch closed with 12 holds after the evidence gate withheld its remaining six
proposals. Four of those six were audited in one Luna call whose response had the wrong bundle
shape. The raw malformed response and failed ingest are retained; a transparent partition by
claim ID and removal of structurally invalid joined-source observations allowed the valid
observations to be inspected. None supplied enough independent support for acceptance, so no Sol
call or learner promotion followed.

| Batch | Generated | Accepted | Held | Rejected | Pending | Status |
|---|---:|---:|---:|---:|---:|---|
| transportation-001 | 12 | 0 | 12 | 0 | 0 | closed |
| home-001 | 8 | 1 | 7 | 0 | 0 | closed |
| food-001 | 8 | 3 | 4 | 1 | 0 | closed |
| common-verbs-001 | 8 | 0 | 7 | 1 | 0 | closed |
| common-adjectives-001 | 8 | 0 | 8 | 0 | 0 | closed |
| technology-001 | 8 | 1 | 7 | 0 | 0 | closed |
| communication-001 | 8 | 0 | 8 | 0 | 0 | closed |
| everyday-objects-001 | 8 | 0 | 5 | 3 | 0 | closed |
| produce-001 | 6 | 1 | 5 | 0 | 0 | closed |
| growth-audit-001 (process fixture) | 1 | 0 | 0 | 1 | 0 | closed |
| school-001 | 6 | 0 | 3 | 3 | 0 | closed |
| clothing-001 | 6 | 0 | 5 | 1 | 0 | closed |
| health-001 | 6 | 0 | 6 | 0 | 0 | closed |

Historical batch decisions in this table record the policy in effect when each batch closed.
They are not the current active learner count.

## Contrast-only corpus correction

The 2026-10-05 scope correction excludes concepts with effectively identical ordinary forms,
meaning, and usage. `same` remains a curation classification, but it now receives deterministic
`no-cross-language-difference` rejection before evidence audit. TSV validation and export also
block a `same` row. `000002`, `000006`, and `000007` were removed from active source;
`curation/retirements.json` records the reason and the permanent ledger assignments remain.
The new prompt set `1.3.0` steers future generation away from shared vocabulary. Historical
batches retain their prompt and model provenance; their previously recorded decisions describe
the earlier policy and are not silently rewritten.

The `school-001` generation pass produced six candidates. All six generated placeholder `topic`
tags were corrected to `school` through recorded proposal revisions before normalization. After
CLI recovery, a separate Luna normalization call found no overlaps. School, teacher, and book
were explicitly rejected early because their proposed ordinary forms were identical. Student
was held because the neutral cue spans school levels and the proposed Malaysian answer was not
established as the normal choice for one precise sense. Pencil had separate locale analyses and
relation proposal, but its source audit found only one supporting observation; the key meaning
and everyday-usage claims lacked two independently inspected supports, so verification was
withheld. Eraser was held after locale analysis because the proposed standalone Malaysian
`pemadam` had an unresolved preferred-form question against `getah pemadam`. Each held or
rejected record names its reason and missing downstream stages. The batch closed with no
accepted entry or learner-source mutation.

CLI recovery investigation on 2026-10-05 found that the shell had no system DNS configuration
(`scutil --dns`), while direct queries to the configured resolver succeeded. CLI 0.160.0 and
0.159.2 failed during managed-preferences synchronization even with user configuration ignored.
Installed CLI 0.153.0 passed a live model call through the process-local
`scripts/curation_codex.py` tunnel with `SSL_CERT_FILE=/etc/ssl/cert.pem`. The current account
catalog listed `gpt-5.6-luna` and `gpt-5.6-sol`, and both returned `OK` in separate read-only
smoke calls. The earlier `gpt-6-luna` and `gpt-6-sol` names returned HTTP 400 unsupported-model
responses with this account. The central role configuration briefly used the working Luna/Sol
pair; the later all-Luna cost decision changed future routes only. Historical stage records
retain their originally invoked model names.
The saved school normalization bundle was then regenerated under the updated route, run through
the launcher with `gpt-5.6-luna`, and ingested for all six candidates. The model response
reported no semantic overlaps. The school batch outcome above supersedes its earlier pending
status.

The first `1.3.0` clothing batch produced six contrast hypotheses. A separate Luna
normalization pass found no archive overlap. Source inspection rejected dress because `gaun`
and `baju kurung` do not name the same neutral garment, and held shirt, skirt, and belt because
the proposed Malaysian form or preferred usage was unresolved. Trousers and shoes had directly
retrieved Indonesian retail examples, DBP definitions, and current Malaysian education usage.
Separate Luna locale analyses found the proposed terms natural, and a separate relation pass
proposed `different-common-word`. Neither locale analysis could support a within-country
preferred-choice claim against known synonyms; the deterministic pre-audit withheld the
evidence-audit packet with `missing-within-locale-preference`. Both candidates were held before
verifier or adversary calls. This batch records six generated, five held, one rejected, and zero
accepted; canonical learner data did not change. It shows that source-first research and
selective role bundles save review calls, but comparative everyday-preference evidence remains
the main obstacle to a larger accepted corpus.

The `health-001` batch generated six contrast hypotheses and normalized all six with no
overlap. Four were held after source screening: Malaysian references also admit the proposed
Indonesian terms for diarrhea and allergy, the hospital preference was not established, and
the dizzy cue overlapped headache and spinning senses. Nurse received separate locale and
relation analyses, but the proposed `different-common-word` relation lacked independently
supported preferred-choice claims in both countries; pre-audit withheld evidence review.
Medicine received a narrowed English cue, fresh overlap review, separate locale analyses,
directly inspected Indonesian and Malaysian health references, and a claim-linked evidence
audit. Its blinded Luna verifier objected to the `similar` proposal and called the pair
outside the contrast-only scope. This unresolved disagreement led to hold without a favorable
rerun or adversarial call. The closed report records six holds, zero accepted entries, and one
verification failure. No permanent ID or learner TSV row was created.

## Later claim review and places batch

The reopened common-verbs `coba/cuba` candidate was held after both locale analyses
supported the attempt sense but the relation proposal treated the forms as effectively
the same for this contrast-only deck. The reopened clothing `sepatu/kasut` candidate
gained a directly inspected comparative study and language-course source, but its
claim-linked audit still lacked sufficient Indonesian meaning and Malaysian
preferred-choice support. It remained held.

The `places-001` batch generated and normalized six concepts, then closed with six
holds and zero accepted entries. Office and shop lacked audited preferred-choice
support. Police station had multiple independent current public-service usage sources,
but neither locale analysis established everyday preference over alternatives. Post
office reached a `different-common-word` proposal and evidence audit; the audit found
both preferred-choice claims unsupported by the available institutional usage and
technical comparative evidence, so independent verification was withheld. Airport and
pharmacy were held early because everyday-form or semantic alignment remained
unresolved. None of these candidates received an ID or changed the learner TSV.

Across the 13 non-fixture closed batches, reports now reconcile 98 generated
candidates: six accepted, 83 held, and nine rejected. Three historical accepted
`same` entries (kitchen, corn, computer) predate the contrast-only correction and
remain excluded from the learner source. The current deck still has three cards, all
from the food batch. The 24 accepted contrast target and three-category/three-relation
coverage remain unmet. Future batches need stronger direct evidence of ordinary
preference and at least one false friend that passes its stricter gate.

## University batch and prompt corrections

The `university-001` batch is closed with four generated and four held. A first bundled
normalization response incorrectly treated candidate IDs in its own archive snapshot as
self-duplicates. Atomic ingest rejected that response without changing candidate state.
The bundle packet now excludes those self references and presents other candidates as
peers; a regression test covers the distinction. A fresh bundled normalization passed.

The scholarship candidate (`beasiswa`/`biasiswa`) received directly inspected Indonesian
tax, funding-program, and university sources and independent Malaysian ministry and
university sources. An older comparative dictionary was treated as one underlying source
despite its mirrored PDF. The claim-linked evidence audit passed, but the blinded verifier
classified the pair as `different-common-word` while the relation proposer chose `similar`.
That taxonomy disagreement was held; no favorable verifier rerun or permanent ID was
substituted. Assignment (`tugas`/`tugasan`) and exam (`ujian`/`peperiksaan`) were held before
locale research because normal national preference and exact-sense alignment had not been
established. Faculty (`fakultas`/`fakulti`) had independently inspected university sources
in both countries and separate locale analyses; the Malaysian analysis withheld a
preferred-choice claim, so it was held before relation and evidence stages.

Prompt set `1.4.0` clarifies that multiple independent contextual sources can support
ordinary preference for a precise cue without a numeric frequency study, while one
institutional label or dictionary entry cannot. Prompt set `1.5.0` gives the blinded
verifier the same relation definitions as the relation proposer without revealing the
proposal. Both snapshots are immutable; `university-001` remains pinned to `1.4.0`.
New batches use `1.5.0`. Across the 14 non-fixture closed batches, 102 candidates have
been generated: six historically accepted, 87 held, nine rejected. The three historical
`same` acceptances remain excluded under the contrast-only policy. The learner deck still
has three cards in one deck. The initial-corpus target remains unmet.

The held transportation `bus`/`bas` candidate was reopened with directly inspected
Indonesian dictionary, operator, and public-service usage plus independent Malaysian
ministry and city-service usage. A second evidence audit recorded the distinction
between dictionary standardness and contextual preference. This exposed a deterministic
gate defect: a dictionary-only observation for a preference claim vetoed the claim even
when separate contextual observations supported it. The gate now ignores dictionary-only
support for preference and still rejects a preference supported only by dictionaries.
The blinded verifier under that batch's pinned `1.0.0` prompt returned `same` while the
proposal returned `similar`; the candidate remains held without an ID or learner row.

## Automated checks

- `pytest -q`: 143 passed on 2026-10-10 after the bundle fix and university batch closed.
- `ruff check .` and `ruff format --check .`: passed on 2026-10-10 after the bundle fix.
- `python -m indo_malay_anki validate`: 3 valid concepts, zero media on 2026-10-10.
- `python -m indo_malay_anki build`: 3 notes and 3 cards on 2026-10-10.
- `git diff --check`: passed on 2026-10-10 with the TSV's required empty final field covered by a path-specific
  `.gitattributes` whitespace rule.
- Read-only decision checks for all 12 transportation candidates: 0.035 seconds (local Python
  3.14 environment, excluding AI and external research time).
- `curation/export-journal.json` absent, matching the release preflight.

The later-batch `growth-audit-001` process fixture closes with one confirmed duplicate rejected,
zero accepted entries, a retained malformed response, and no new learner ID. A repeat export of
the home, food, and technology batches returned their five existing IDs without treating the
later rejected plural spoon fixture as a new blocker. New promotions still undergo the final
cross-batch overlap screen.

## Anki Desktop import compatibility

The macOS Anki Desktop installation is version 26.9.3. Its bundled Python 3.13 Anki backend
imported a pre-feature package built from repository `HEAD` (one `000001` car note), followed by
a temporary post-feature package with the same ID and a separate false-friend rendering fixture.
The backend was exercised in `/tmp/myid-compat-003/collection.anki2`; this was a temporary test
collection, not the user's normal profile. The package fixture was kept out of learner source.
Because the project's Conda environment uses Python 3.14 and the installed Anki bundle contains
Python 3.13 extension modules, the compatibility check used a temporary Python 3.13 interpreter
installed with `uv` and loaded Anki's own bundled packages.

Import settings were `update_notes=IF_NEWER`, `update_notetypes=IF_NEWER`,
`with_scheduling=false`, `with_deck_configs=false`, and `merge_notetypes=false` (the default).
The old package imported as one note/card. The second import reported one updated note and one
new fixture note, ending with two notes/cards. The retained `000001` note kept GUID
`D6BBAuKXK`, changed English from `car` to `car (passenger vehicle)`, retained its card ID, and
preserved a simulated reviewed state `(reps=3, interval=7, queue=2, type=2, due=7)`. The note
type still had exactly `ID`, `English`, `Indonesian`, `Malaysian`, `Image` and one `Vocabulary`
template; deck/model IDs remained `1242123295`/`1942161817`. The fixture's contrast and both
answers were absent from its rendered front and present on its rendered back. This exercises the
Desktop application's import backend and renderer with explicit settings; no interactive GUI
import was performed.

The complete initial-corpus walkthrough remains pending. Do not release Feature 003 while the
24-accepted-concept gate is unmet.

## Quickstart audit

The documented command sequence matches the current `init`, `packet`, `ingest`, `bundle`,
`ingest-bundle`, `check`, `report`, `reopen`, `finalize-hold`, `export`, `validate`, and `build`
commands. The negative-gate walkthrough is represented by the retained malformed-output and
duplicate fixture, plus the held transportation, adjective, technology, and communication
candidates. The compatibility walkthrough above passed through Anki Desktop's bundled import
backend. The initial-corpus walkthrough cannot be marked complete until at least 24 accepted
concepts pass the same evidence, verifier, adversarial, overlap, and export gates.
