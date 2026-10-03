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
  `github.token` with GitHub CLI.
- The publication script drafts an existing Release before `--clobber` replacement, or creates a
  new draft. It publishes only after the checked asset upload succeeds. Failed gates cannot start
  publication. A failed upload leaves the Release draft for retry.
- The README, specification, contract, and workflows agree on `dist/myid-anki.apkg` locally,
  `indonesian-malaysian-ci-apkg` for CI inspection, and `indonesian-malaysian.apkg` for learners.
  Release tag values do not enter concept IDs, note GUID derivation, deck ID, or note-model ID.

The Python integration suite confirms tag environment values do not change those Anki identities.
Static review found no deviation from the specified permissions, output names, or scope exclusions.

## Hosted and Anki acceptance still required

The approved source now passes local validation and build. Hosted runs, downloaded artifacts, and
Anki imports still need direct evidence. The following tasks remain unverified:

| Task | Evidence needed |
|---|---|
| T007 | Passing PR and main runs; downloadable CI artifact; no main-push Release; isolated failures for every gate and missing output; record any observed artifact-service failure |
| T013 | Valid and invalid tag runs; tag target and checkout SHAs; release/run IDs; same-run package and downloaded asset SHA-256; single asset; rerun and draft failure behavior; Anki import |
| T015 | Two-package update import in an Anki client, client/version, identity comparison, and duplicate-note count |
| T019 | README walkthrough with contributor, maintainer, and learner observations and the specified 15-minute and 5-minute timings |

Follow [quickstart.md](quickstart.md) with GitHub Actions, Releases, and an Anki client. Do not mark
these hosted tasks complete from static inspection alone.
