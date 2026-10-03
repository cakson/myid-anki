---
description: "Dependency-ordered tasks for GitHub deck CI and release distribution"
---

# Tasks: GitHub Deck CI and Releases

**Input**: Design documents from `specs/002-github-deck-releases/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [workflow contract](contracts/workflow-distribution.md), [quickstart.md](quickstart.md)

**Tests**: Existing project tests remain required gates. Add only a focused tag-independence regression test; use workflow syntax/configuration validation and hosted acceptance instead of a local GitHub Actions emulator.

**Organization**: Tasks are grouped by the four user stories in the specification. Every hosted acceptance task requires at least one maintainer-reviewed concept in `data/vocabulary.tsv`; the current header-only file intentionally fails validation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other marked tasks when prerequisites are complete and files do not overlap.
- **[Story]**: Maps the task to a spec user story.
- Paths are relative to the repository root.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the two explicit workflow files without changing Python application logic.

- [ ] T001 Create `.github/workflows/ci.yml` and `.github/workflows/release.yml` as valid named workflow skeletons with job maps, leaving story-specific triggers and steps for their phases.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Apply the existing project environment consistently before either workflow's gates are added.

- [ ] T002 Set explicit `contents: read` default permissions in `.github/workflows/ci.yml` and `.github/workflows/release.yml`, reserving a job-scoped write override for release publication.
- [ ] T003 Add checkout, Python 3.12 setup, simple pip dependency caching, and `python -m pip install -e '.[dev]'` to the check/build jobs in `.github/workflows/ci.yml` and `.github/workflows/release.yml`; use the existing `pyproject.toml` dependency set.

**Checkpoint**: Both workflows have a supported environment and read-only baseline; no vocabulary, media, model, or builder changes have been made.

---

## Phase 3: User Story 1 - Check Every Proposed Change (Priority: P1) 🎯 MVP

**Goal**: Pull requests and main pushes fail for any bad gate and expose a usable package as an inspectable Actions artifact after success.

**Independent Test**: With reviewed nonempty vocabulary, a PR or main run passes all gates and offers a downloadable `.apkg`; controlled validation, test, lint, formatting, build, missing-output, or upload failures produce failed runs. No Release appears from a normal main push.

- [ ] T004 [P] [US1] Configure `.github/workflows/ci.yml` for pull requests and pushes to `main` only, with no release publication step and no write permission.
- [ ] T005 [US1] Add the five existing local commands in order to `.github/workflows/ci.yml`: validation, `pytest`, `ruff check .`, `ruff format --check .`, and deck build; preserve nonzero exit behavior.
- [ ] T006 [US1] Upload `dist/myid-anki.apkg` as a clearly named run artifact in `.github/workflows/ci.yml`; make a missing file or failed attempted upload fail CI.
- [ ] T007 [US1] Record a passing hosted PR/main run, downloadable artifact, no-main-release outcome, and at least one controlled failing gate in `specs/002-github-deck-releases/validation-results.md`, following `quickstart.md`.

**Checkpoint**: User Story 1 is independently useful as a quality gate and inspectable build, without any Release workflow.

---

## Phase 4: User Story 2 - Publish an Explicit Version (Priority: P1)

**Goal**: A valid pushed version tag publishes the package built and checked from that exact tagged revision as `indonesian-malaysian.apkg`.

**Independent Test**: With valid reviewed source, push a fresh version tag and compare the Release asset with the tagged revision. A malformed tag or failed gate publishes no new asset; a successful rerun leaves one asset with the stable filename.

- [ ] T008 [P] [US2] Configure `.github/workflows/release.yml` for pushed `v*.*.*` tags and add an exact numeric `vMAJOR.MINOR.PATCH` guard; ensure checkout uses the triggering tag revision, not current `main`.
- [ ] T009 [US2] Add the same five documented validation, test, Ruff, formatting, and build commands to the read-only build job in `.github/workflows/release.yml`, stopping publication on any failure.
- [ ] T010 [US2] Upload `dist/myid-anki.apkg` to a named artifact in the current release workflow run in `.github/workflows/release.yml`, failing for missing output or upload error.
- [ ] T011 [US2] Add a dependent publication job in `.github/workflows/release.yml` with only job-scoped `contents: write`; download that same run's named artifact, copy it to `indonesian-malaysian.apkg`, and create/update the pushed tag's GitHub Release using the built-in token.
- [ ] T012 [US2] Configure `.github/workflows/release.yml` so missing release files fail publication and successful reruns replace the stable-named asset without duplicates; keep any prior asset untouched when earlier gates fail.
- [ ] T013 [US2] Record hosted test-tag, exact-revision provenance, Release creation, single downloadable/importable asset, malformed-tag no-publication, and safe rerun outcomes in `specs/002-github-deck-releases/validation-results.md`, following `quickstart.md`.

**Checkpoint**: User Story 2 can publish a learner deck from its own tagged run even if ordinary CI is not used as an artifact source.

---

## Phase 5: User Story 3 - Import an Updated Deck (Priority: P2)

**Goal**: GitHub release versions and asset names have no effect on existing Anki identities or supported update imports.

**Independent Test**: Compare packages built from two revisions with unchanged permanent concept IDs under different release-tag context; deck/model IDs and note GUIDs remain stable, and an update import creates no duplicates for those IDs.

- [ ] T014 [P] [US3] Extend `tests/integration/test_semantic_rebuild.py` with a focused check that distinct release-tag environment values do not change deck ID, note-model ID, or note GUIDs for unchanged concept IDs; retain the existing one-note/one-card checks.
- [ ] T015 [US3] Record a two-package update import and identity comparison, including Anki client/version and duplicate-note result, in `specs/002-github-deck-releases/validation-results.md`; do not change `src/indo_malay_anki/model.py` or concept IDs to encode release versions.

**Checkpoint**: The package's logical Anki identity is independent of GitHub tag and release asset filename.

---

## Phase 6: User Story 4 - Follow the Documented Workflow (Priority: P3)

**Goal**: Contributors, maintainers, and learners can complete their distinct workflows from the README while local build guidance remains intact.

**Independent Test**: Follow the README from a clean checkout and an earlier Anki import; locate the CI artifact, create a version tag, find the latest Release, and import its asset without undocumented steps.

- [ ] T016 [P] [US4] Add contributor guidance to `README.md` for automatic PR/main checks, their five gates, failure meaning, and where to inspect/download the Actions artifact, preserving existing local validation/build commands.
- [ ] T017 [US4] Add maintainer guidance to `README.md` for confirming reviewed, passing `main`, creating/pushing a `vMAJOR.MINOR.PATCH` tag, and finding the resulting Release asset `indonesian-malaysian.apkg`.
- [ ] T018 [US4] Add learner guidance to `README.md` for finding the latest GitHub Release, downloading/importing `indonesian-malaysian.apkg` on desktop or mobile, and importing updates into an existing collection with stable concept IDs and client-dependent update behavior.
- [ ] T019 [US4] Run the README walkthrough in `specs/002-github-deck-releases/quickstart.md` and record contributor/maintainer/learner results and any wording corrections in `specs/002-github-deck-releases/validation-results.md`.

**Checkpoint**: Documentation serves each audience and retains the local path `dist/myid-anki.apkg`.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate the completed configuration and record any acceptance limits.

- [ ] T020 Inspect `.github/workflows/ci.yml` and `.github/workflows/release.yml` with a YAML/workflow syntax checker and focused review of triggers, exact tag guard, five commands, permissions, same-run artifact transfer, missing-file failure, and release filename; record results in `specs/002-github-deck-releases/validation-results.md`.
- [ ] T021 Run `pytest`, `ruff check .`, and `ruff format --check .`; run `python -m indo_malay_anki validate` and `python -m indo_malay_anki build` when reviewed nonempty source is available, and record pass/fail or the header-only prerequisite in `specs/002-github-deck-releases/validation-results.md`.
- [ ] T022 Review `specs/002-github-deck-releases/spec.md`, `contracts/workflow-distribution.md`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`, and `README.md` for matching local/artifact/release filenames, least-privilege permissions, explicit exclusions, and no tag input to Anki identity; record unresolved deviations in `specs/002-github-deck-releases/validation-results.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup T001 precedes foundational T002–T003.
- T002–T003 precede workflow implementation in User Stories 1 and 2.
- User Story 3's automated identity check can proceed after foundation; its hosted update-import evidence requires two valid packages, normally after User Story 2.
- User Story 4's README drafting can proceed after foundation; its walkthrough uses completed workflows.
- Polish follows implementation and any hosted acceptance available with reviewed source.

### User Story Dependencies

- **US1 (P1)**: No dependency on another story after foundation; this is the MVP.
- **US2 (P1)**: No dependency on US1's artifact; it builds and transfers its own tagged package.
- **US3 (P2)**: Automated regression is independent; hosted import acceptance uses releases from US2.
- **US4 (P3)**: Documentation drafting is independent; final walkthrough depends on the relevant workflows.

### Within Each User Story

- US1: trigger/permission configuration → gates → artifact upload → hosted acceptance.
- US2: tag/ref guard → gates → same-run artifact → narrowly scoped publication → rerun/failure behavior → hosted acceptance.
- US3: identity regression → two-package import evidence.
- US4: contributor → maintainer → learner instructions → walkthrough.

### Parallel Opportunities

- After T003, T004 in `ci.yml`, T008 in `release.yml`, T014 in the integration test, and T016 in `README.md` can be assigned independently.
- Hosted acceptance T007 and T013 must wait for their own workflows and reviewed nonempty vocabulary; they can be scheduled separately.

## Parallel Examples

### User Story 1

- T004 in `.github/workflows/ci.yml` can proceed alongside T008 in the separate release file, T014 in the identity test, and T016 in the README. T005–T007 remain ordered within US1.

### User Story 2

- T008 in `.github/workflows/release.yml` can proceed alongside T004 in CI and T014 in tests. T009–T013 remain ordered because they edit the same workflow or depend on its hosted result.

### User Story 3

- T014 in `tests/integration/test_semantic_rebuild.py` can proceed alongside both workflow implementations. T015 waits for two packages and an Anki import.

### User Story 4

- T016 in `README.md` can be drafted alongside workflow implementation. T017–T019 follow it to avoid conflicting edits and to validate the final wording.

## Implementation Strategy

### MVP First (User Story 1)

1. Complete T001–T003.
2. Complete T004–T006 and static/local checks.
3. With reviewed nonempty vocabulary, complete T007 and validate an inspectable CI artifact.
4. Keep Release publication for the next increment.

### Incremental Delivery

1. Add US2 for explicit tag-triggered learner distribution.
2. Add US3 evidence that Anki identity survives release-version changes.
3. Add US4 documentation and complete cross-cutting review.
4. Do not mark hosted acceptance complete until the corresponding GitHub run and Anki import have actually occurred.

## Notes

- The source currently contains only a TSV header. T007, T013, T015, and T019 require maintainer-reviewed nonempty data; no task authorizes invented vocabulary.
- The custom `checklists/ci-release.md` is reviewer-owned and its unchecked items do not mean implementation tasks are complete or incomplete.
- Commit messages for implementation must follow the constitution's Conventional Commits rule.
