# Feature 002 Validation Results

**Reviewed**: 2026-10-03 on `002-github-deck-releases`

## Local quality gates

The local check used an ignored Python 3.12.14 virtual environment with the project's `.[dev]`
dependencies. The additional PyYAML package was used only for this review; it is not a project
dependency.

| Check | Result |
|---|---|
| `pytest` | Pass: 77 tests, including release-tag identity regression |
| `ruff check .` | Pass |
| `ruff format --check .` | Pass: 50 files already formatted |
| `python -m indo_malay_anki validate` | Pass: 1 reviewed concept, 0 media files |
| `python -m indo_malay_anki build` | Pass: `dist/myid-anki.apkg`, 1 note and 1 card |
| `unzip -t dist/myid-anki.apkg` | Pass: Anki collection and media archive entries intact |

Before the maintainer approved the README's `car` example, both validation and build correctly
failed on the header-only source with "At least one vocabulary concept is required." The approved
row is now checked in; no invented placeholder vocabulary was added. The local package SHA-256 was
`f76a585ac46b1b1d15aa91b8b4e64b2748d98617e95eb40e16bdabaed686a48a` for this build. The
package may have different bytes on another build because note modification times advance; Anki
identities remain stable.

## Workflow configuration review

Both workflow files parsed as YAML. A focused configuration check confirmed:

- CI triggers only on pull requests and pushes to `main`; it has only a `contents: read` job and no
  Release step.
- Release triggers only on pushed `v*.*.*` tags. Its first step rejects tags outside the exact
  numeric `vMAJOR.MINOR.PATCH` form before checkout, checks, or publication.
- Both build jobs use Python 3.12, `.[dev]`, and the five documented commands in order. Every
  `run` block also passed `bash -n` syntax checking.
- Both jobs require a nonempty `dist/myid-anki.apkg` and use artifact upload with
  `if-no-files-found: error`. CI names its artifact `indonesian-malaysian-ci-apkg` and leaves
  retention at the repository setting. An upload failure fails the job.
- The release build uses the triggering tag ref and records `git rev-parse HEAD`. Only the
  dependent publication job has `contents: write`; it downloads `indonesian-malaysian-release-apkg`
  from the same workflow run, copies its package to `indonesian-malaysian.apkg`, and uses the built-in
  `github.token` with GitHub CLI. The publication job sets `GH_REPO` because it has no checkout.
- The publication script drafts an existing Release before `--clobber` replacement, or creates a
  new draft. It publishes only after the checked asset upload succeeds. Failed gates cannot start
  publication. A failed upload leaves the Release draft for retry.
- The README, specification, contract, and workflows agree on `dist/myid-anki.apkg` locally,
  `indonesian-malaysian-ci-apkg` for CI inspection, and `indonesian-malaysian.apkg` for learners.
  Release tag values do not enter concept IDs, note GUID derivation, deck ID, or note-model ID.

The Python integration suite confirms tag environment values do not change those Anki identities.
Static review found no remaining deviation from the specified permissions, output names, or scope
exclusions.

## Hosted CI and Release evidence

- Draft [PR #1](https://github.com/cakson/myid-anki/pull/1) passed CI at commit
  `bb640f4d60f9203731674116c45f807699183b89` in
  [run 37092963340](https://github.com/cakson/myid-anki/actions/runs/37092963340). The named
  `indonesian-malaysian-ci-apkg` artifact downloaded successfully and contained `myid-anki.apkg`.
  Its archive passed `unzip -t`. GitHub reported it unexpired with a 90-day repository retention
  setting and expiry `2027-01-01T03:22:07Z`. The corrected branch passed PR CI again in
  [run 37093321370](https://github.com/cakson/myid-anki/actions/runs/37093321370).
- Pushed `v0.1.0` at the first passing PR commit. Its
  [release run 37093126919](https://github.com/cakson/myid-anki/actions/runs/37093126919)
  passed build and artifact transfer but failed publication: GitHub CLI had no repository context
  in the checkout-free publication job. GitHub reported no Release for this tag. The workflow was
  fixed by setting `GH_REPO` to the built-in `github.repository` value. The existing tag was not
  moved.
- Pushed fresh `v0.1.1` at `e1b6be70829eb86c9683fa53694446dee5fb29d6`. The
  [release run 37093389454](https://github.com/cakson/myid-anki/actions/runs/37093389454)
  passed. Its logged checkout SHA and GitHub run head SHA both equal the tag target, while `main`
  still points to an older revision. The published
  [v0.1.1 Release](https://github.com/cakson/myid-anki/releases/tag/v0.1.1) had exactly one
  `indonesian-malaysian.apkg` asset. The downloaded asset and package from that same run were
  byte-for-byte equal with SHA-256
  `963a606a1db98f63803fd895af547bbbbacd8e38673b0101c95312ed5763fee6`.
- Reran the `v0.1.1` workflow successfully. It drafted the existing Release, replaced the asset,
  and published it again with exactly one deck asset. The rerun's downloaded package and current
  Release asset were byte-for-byte equal with SHA-256
  `0b5732c793e7e2fb02cd228a0b1e21c46e2e60723d4bba69b763d0d83e04db95`.

## Anki import and update evidence

Anki Desktop 26.9.3 is installed locally. Using the matching Anki 26.9.3 import backend and an
isolated temporary collection, the downloaded `v0.1.1` Release asset imported as one note and one
card with GUID `D6BBAuKXK`. Reimporting that asset left one note and one card. A second, local test
package changed only the English cue from `car` to `automobile` while keeping permanent concept ID
`000001`; importing it into the same collection updated the existing note in place. Its database
note ID, GUID, note-model ID, and collection deck ID remained unchanged, and the collection still
had one note and one card. The second package was a temporary test fixture, not a published Release;
no repository vocabulary was changed for this test. A graphical desktop or mobile import was not
performed.

## Acceptance still required

The following task evidence is still incomplete:

| Task | Evidence needed |
|---|---|
| T007 | A main push and no-main-release observation, plus isolated hosted failures for validation, tests, Ruff lint, formatting, build, and missing output. No artifact-service failure was observed. |
| T013 | A malformed tag blocked before publication, a valid tag on a failing revision, and an observed asset-upload failure after draft creation. The successful Release and rerun, provenance, byte comparison, and Anki-core import are recorded above. |
| T019 | Complete contributor, maintainer, and learner README walkthroughs, including the specified 15-minute main-CI-to-release and 5-minute Releases-to-import timings. |

Follow [quickstart.md](quickstart.md) for the remaining hosted checks and graphical import. Do not
mark incomplete tasks complete from static inspection alone.
