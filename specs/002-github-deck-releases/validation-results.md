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
| `ruff format --check .` | Pass: 49 files already formatted |
| `python -m indo_malay_anki validate` | Expected failure: source has only a header; at least one concept is required |
| `python -m indo_malay_anki build` | Expected failure at the same validation gate; no package produced |

No placeholder vocabulary was added. A maintainer-reviewed nonempty source is required before CI
or release acceptance can produce a green run.

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

The repository's vocabulary file has no reviewed concepts, so a hosted green PR/main run and a
successful tagged release would currently fail validation by design. No tag was pushed and no
Release was created during this local implementation. The following tasks remain unverified:

| Task | Evidence needed |
|---|---|
| T007 | Passing PR and main runs; downloadable CI artifact; no main-push Release; isolated failures for every gate and missing output; record any observed artifact-service failure |
| T013 | Valid and invalid tag runs; tag target and checkout SHAs; release/run IDs; same-run package and downloaded asset SHA-256; single asset; rerun and draft failure behavior; Anki import |
| T015 | Two-package update import in an Anki client, client/version, identity comparison, and duplicate-note count |
| T019 | README walkthrough with contributor, maintainer, and learner observations and the specified 15-minute and 5-minute timings |

Follow [quickstart.md](quickstart.md) after reviewed vocabulary is committed and GitHub Actions,
Releases, and an Anki client are available. Do not mark these hosted tasks complete from static
inspection alone.
