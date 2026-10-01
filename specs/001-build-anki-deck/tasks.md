---

description: "Dependency-ordered implementation tasks for the MYID Anki local deck generator"
---

# Tasks: Build Local Anki Deck

**Input**: Design documents from `specs/001-build-anki-deck/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`,
`quickstart.md`

**Tests**: Automated tests are required by FR-029 and Constitution Principle XIV. Write each listed
test before its corresponding implementation and observe the relevant failure.

**Organization**: Shared validation is foundational because every build must complete the full
source and media validation pipeline before package generation. After that gate, tasks are grouped
by user story so every story has a single traceability label and an independent checkpoint.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel after its stated prerequisites because it targets different files
- **[Story]**: Maps a user-story-phase task to `US1` through `US5`
- Setup, foundational, and polish tasks have no story label
- Every task names the exact file or directory it changes or validates

## Phase 1: Setup

**Purpose**: Create the small Python project skeleton and version-controlled source layout.

- [X] T001 Create Python 3.12 project metadata, setuptools src-layout discovery, `genanki` runtime dependency, dev extras, console script, pytest configuration, and Ruff configuration in `pyproject.toml`
- [X] T002 Create the Conda-compatible Python 3.12 editable development environment in `environment.yml`
- [X] T003 [P] Create package and test scaffolding in `src/indo_malay_anki/__init__.py`, `src/indo_malay_anki/__main__.py`, `tests/conftest.py`, `tests/unit/.gitkeep`, `tests/contract/.gitkeep`, `tests/integration/.gitkeep`, and `tests/fixtures/.gitkeep`
- [X] T004 [P] Add Python-tooling and generated-artifact exclusions plus repository placeholders in `.gitignore`, `data/vocabulary.tsv`, `media/.gitkeep`, and `dist/.gitkeep` without adding unreviewed production vocabulary

**Checkpoint**: The project installs locally, authoritative inputs are version controlled, and
generated `.apkg` files remain untracked.

---

## Phase 2: Foundational Validation and Identity Gate

**Purpose**: Complete immutable identities, strict parsing, full source/media validation, and the
standalone validation command before any package-generation implementation begins.

**⚠️ CRITICAL**: No builder, temporary-package, or user-story generation task may begin until this
phase passes. Only `ValidatedVocabulary` may cross into later package generation.

### Foundational Tests

- [X] T005 Write failing domain contract tests for six-digit string IDs, frozen deck/model IDs, GUID namespace, golden GUID `000001 -> D6BBAuKXK`, immutable values, and builder-only `ValidatedVocabulary` input in `tests/unit/test_model.py`
- [X] T006 [P] Add reusable strict-TSV, media-tree, template-tree, existing-output, and output-path fixture factories without real vocabulary generation in `tests/conftest.py`
- [X] T007 [P] Write failing UTF-8 TSV loader tests for valid field mapping, native tag tokenization, leading-zero preservation, exact headers, strict CSV failures, wrong field counts, blank rows, and zero concepts in `tests/unit/test_loader.py`
- [X] T008 [P] Write failing content-validation tests for required values, leading/trailing whitespace, six-ASCII-digit IDs, duplicate IDs, and row/concept/field issue context in `tests/unit/test_validator.py`
- [X] T009 Write failing media-validation tests for absolute paths, URLs, backslashes, empty/dot/parent components, missing paths, directories, symlink escapes, safe nested paths, exact same-file reuse, and Unicode-case-folded packaged-basename collisions with complete conflict reporting in `tests/unit/test_validator.py`
- [X] T010 [P] Write failing validate-command contract tests for success/failure status, basic source/row/concept/field diagnostic shape, stdout/stderr separation, no `dist/` creation, help, and exit codes 0/1/2 in `tests/contract/test_cli_contract.py`

### Foundational Implementation

- [X] T011 Implement `VocabularyConcept`, `MediaReference`, `ValidationIssue`, `ValidatedVocabulary`, fixed compatibility constants, and `stable_guid()` in `src/indo_malay_anki/model.py`
- [X] T012 Implement strict UTF-8 TSV decoding and `csv.reader` parsing with exact ordered headers, six-field row preservation, physical row context, string IDs, and tag tokenization in `src/indo_malay_anki/loader.py`
- [X] T013 Implement required-field, whitespace, six-ASCII-digit ID, duplicate-ID, exact-schema, non-empty-dataset, and structured issue creation in `src/indo_malay_anki/validator.py`
- [X] T014 Implement lexical and resolved media containment, existence/type, remote-reference rejection, exact same-file reuse, Unicode-case-folded packaged-basename collision detection, and complete conflicting-reference diagnostics in `src/indo_malay_anki/validator.py`
- [X] T015 Implement the importable `main(argv=None) -> int` dispatcher, `validate` command, basic diagnostic context, exit codes, and module delegation in `src/indo_malay_anki/cli.py` and `src/indo_malay_anki/__main__.py`

**Checkpoint**: Full source and media validation passes its unit and CLI contracts. Invalid input
cannot become `ValidatedVocabulary`, and no package-generation code exists yet.

---

## Phase 3: User Story 1 - Generate and Study a Vocabulary Deck (Priority: P1) 🎯 MVP

**Goal**: Build one validated offline package containing complete text and image cue behavior, one
note/card per concept, bundled media, joint answers, atomic output, and recorded desktop/mobile
first-import acceptance.

**Independent Test**: Build a valid fixture containing text-only and image-backed concepts; prove
validation completes before any temporary package is created; inspect one note and card per concept
and bundled media; then import the package into Anki Desktop and one official mobile client and
study both cue types offline at viewport widths of at least 320 CSS pixels without JavaScript or
network access, including long text and images without horizontal overflow.

### Tests for User Story 1

- [X] T016 [P] [US1] Write failing template contract tests for an English cue at least 1.5 times the prompt font size and weight 600 or heavier, CSS-only display casing, image replacement, neutral prompt text, answer non-leakage, both labeled back answers, secondary English context, one template, bounded images, long-value wrapping and no horizontal overflow at widths of at least 320 CSS pixels, no interaction/custom zoom, and no JavaScript or remote resources in `tests/contract/test_template_contract.py`
- [X] T017 [P] [US1] Write failing package integration tests for fixed deck/model identity, five-field schema, exact preservation of the source English note value regardless of displayed casing, one note/card per concept, stable GUID assignment, native tags, HTML escaping, bundled media, and canonical `dist/myid-anki.apkg` output in `tests/integration/test_build_package.py`
- [X] T018 [US1] Add failing build-gate and failure-atomicity cases proving full validation precedes temporary-package creation, validation/generation failures return nonzero, prior output bytes remain unchanged, and invocation-owned temporary files are removed in `tests/integration/test_build_package.py`
- [X] T019 [US1] Add a failing offline regression case that denies network access during normal validation, build, package inspection, and card-resource verification in `tests/integration/test_build_package.py`

### Implementation for User Story 1

- [X] T020 [P] [US1] Create the conditional English-or-image neutral front cue with no Indonesian or Malaysian answer fields in `templates/front.html`
- [X] T021 [P] [US1] Create cue context plus jointly labeled Bahasa Indonesia and Bahasa Melayu answers in `templates/back.html`
- [X] T022 [P] [US1] Create simple no-JavaScript responsive styling with the English cue at least 1.5 times the prompt font size and weight 600 or heavier, optional CSS-only display casing, long-value wrapping, images constrained to the viewport, distinguishable language labels, and no horizontal overflow at widths of at least 320 CSS pixels without interaction/custom zoom in `templates/style.css`
- [X] T023 [US1] Implement fixed model/deck factories, escaped five-field note projection, native tags, deterministic GUIDs, one-template construction, safe image HTML, resolved-media deduplication, and sorted media inputs in `src/indo_malay_anki/builder.py`
- [X] T024 [US1] Implement `build` so it accepts only `ValidatedVocabulary`, completes validation before temporary-package creation, writes in `dist/`, atomically replaces `dist/myid-anki.apkg` only after success, preserves prior output on failure, removes owned temporary files, and reports exit status/counts in `src/indo_malay_anki/cli.py` and `src/indo_malay_anki/builder.py`
- [X] T025 [US1] Execute the quickstart first-import smoke acceptance for text-cue and image-cue cards in Anki Desktop and one official mobile Anki client, recording client versions, operating systems, note/card counts, offline study, bundled media, long text and oversized-image behavior with no horizontal overflow at widths of at least 320 CSS pixels, visible labels/answers, and no JavaScript/network dependency in `specs/001-build-anki-deck/validation-results.md`

**Checkpoint**: US1 is a usable MVP: invalid input cannot reach generation, valid text/image input
produces `dist/myid-anki.apkg`, automated contracts pass, and desktop/mobile first import is recorded.

---

## Phase 4: User Story 2 - Reject Invalid Vocabulary Safely (Priority: P2)

**Goal**: Demonstrate complete, actionable diagnostics and safe aggregation for every specified
invalid source or media category using the foundational validator.

**Independent Test**: Run `validate` and `build` against fixtures for every invalid category;
confirm row/concept/field diagnostics, complete case-fold collision reporting, nonzero status, and
an absent or byte-for-byte unchanged final package.

### Tests for User Story 2

- [X] T026 [US2] Write failing advanced-diagnostic tests for deterministic aggregation of simultaneous independent issues, fatal-error stopping boundaries, duplicate suppression, and complete multi-row collision participants in `tests/unit/test_loader.py` and `tests/unit/test_validator.py`
- [X] T027 [US2] Write failing CLI acceptance tests for deterministic diagnostic ordering, actionable correction context, aggregation summaries, expected-error output without tracebacks, and unchanged final-package bytes in `tests/contract/test_cli_contract.py`

### Implementation for User Story 2

- [X] T028 [US2] Implement deterministic fatal/recoverable issue aggregation, duplicate suppression, stopping boundaries, and complete multi-row collision participant retention in `src/indo_malay_anki/loader.py` and `src/indo_malay_anki/validator.py`
- [X] T029 [US2] Implement deterministic diagnostic ordering, actionable correction context, aggregation summaries, stdout/stderr separation, and expected-error handling without tracebacks in `src/indo_malay_anki/cli.py`

**Checkpoint**: US2 independently demonstrates every validation failure and recovery guarantee
without generating or corrupting a package.

---

## Phase 5: User Story 3 - Regenerate Without Duplicating Concepts (Priority: P2)

**Goal**: Preserve project-controlled identity across all mutable content, styling, media, and row
order changes so supported Anki re-import updates unchanged concept IDs without duplicates.

**Independent Test**: Build normalized package manifests before and after each mutable change;
verify stable deck/model/GUID/template/card relationships and then perform a recorded disposable-
profile desktop re-import and removal walkthrough.

### Tests for User Story 3

- [X] T030 [US3] Add reusable `.apkg` archive/SQLite semantic-manifest inspection for IDs, schema, templates, notes, cards, tags, timestamps, and media hashes in `tests/conftest.py`
- [X] T031 [P] [US3] Write failing parameterized GUID tests proving English, Indonesian, Malaysian, image, tags, styling, and row order do not affect identity while distinct IDs remain distinct in `tests/unit/test_model.py`
- [X] T032 [P] [US3] Write failing two-build semantic-equivalence tests that ignore volatile ZIP/SQLite metadata, including note modification timestamps, while locking semantic content and identities; leave monotonic timestamp assertions to T033 in `tests/integration/test_semantic_rebuild.py`
- [X] T033 [US3] Add failing rebuild cases for every mutable field, presentation, row order, unchanged note/card counts, and zero duplicate GUIDs; include an immediate same-whole-second A/mutate/B sequence proving equal GUID and strictly newer note `mod` without sleeping in `tests/integration/test_semantic_rebuild.py`
- [X] T034 [US3] Add failing omission and reintroduction cases proving a removed concept is absent without a deletion request and that restoring the same permanent ID after one or more omitted builds restores its original GUID in `tests/integration/test_semantic_rebuild.py`

### Implementation for User Story 3

- [X] T035 [US3] Add an injectable whole-second build clock for deterministic tests and assign each build note `mod=max(current_epoch_second, greatest_prior_package_note_mod + 1)` when a prior local package exists; use current time for the first build and never sleep in `src/indo_malay_anki/builder.py`
- [X] T036 [US3] Lock GUID input to the permanent ID alone, field order, deck/model IDs, template count, one-card schema, monotonic update metadata independent of identity, absent-concept omission, and same-GUID reintroduction until semantic rebuild tests pass in `src/indo_malay_anki/model.py` and `src/indo_malay_anki/builder.py`
- [X] T037 [US3] Execute the quickstart disposable-profile Anki Desktop re-import/removal/reintroduction walkthrough and record client version, import settings, mutable update, note/card counts, duplicate-note result, review-state result, omission behavior, and reintroduced identity for extant/deleted collection notes in `specs/001-build-anki-deck/validation-results.md`

**Checkpoint**: US3 proves stable project-controlled identities automatically and records the
client-controlled re-import behavior without deleting omitted collection notes.

---

## Phase 6: User Story 4 - Maintain the Optional-Image Identity Lifecycle (Priority: P3)

**Goal**: Preserve note identity and one-card scheduling when a concept gains, changes, or loses an
optional image while package media follows the current source exactly.

**Independent Test**: Build one concept without an image, add image A, change to image B, and remove
the image; compare every GUID, card count, cue state, and packaged-media manifest.

### Tests for User Story 4

- [X] T038 [P] [US4] Write failing no-image/add-image/change-image/remove-image rebuild cases proving unchanged GUIDs, one-card counts, correct cue selection, and secondary back English in `tests/integration/test_semantic_rebuild.py`
- [X] T039 [P] [US4] Write failing media-transition cases for nested paths, basename packaging, exact same-file reuse, old-media omission, spaces/non-ASCII names, and payload hashes in `tests/integration/test_build_package.py`

### Implementation for User Story 4

- [X] T040 [US4] Complete current-source-only image projection, media replacement/omission, safe basename references, and identity-preserving empty/image transitions in `src/indo_malay_anki/builder.py`

**Checkpoint**: US4 independently proves the add/change/remove image lifecycle without changing
concept identity or creating another card.

---

## Phase 7: User Story 5 - Follow the Documented Local Workflow (Priority: P3)

**Goal**: Let an unfamiliar contributor prepare the environment, add reviewed text/image concepts,
validate, build, find the output, and explain permanent identity without undocumented assistance.

**Independent Test**: After environment setup, an unfamiliar contributor follows only the README
and completes the specified text/image workflow within 15 minutes; record elapsed time, assistance,
outcome, and their explanation of the permanent-ID rule.

### Tests for User Story 5

- [X] T041 [US5] Write failing documentation contract checks for setup and quality commands, canonical paths, six TSV columns, reviewed-vocabulary policy, optional images, card behavior, permanent-ID warning, update/removal behavior, and output location in `tests/contract/test_readme_contract.py`

### Implementation for User Story 5

- [X] T042 [US5] Write project purpose, Conda setup, local installation, validation, build, lint, test, canonical output, offline operation, and generated-artifact guidance in `README.md`
- [X] T043 [US5] Document the exact TSV schema, reviewed-vocabulary-only policy, six-digit permanent-ID lifecycle, tags, safe optional-image references, same-file reuse, and case-fold collision examples in `README.md`
- [X] T044 [US5] Document front/back behavior, one-note/one-card scheduling, desktop/mobile first import, update/import settings, duplicate prevention, removal semantics, and no-manual-`.apkg` maintenance in `README.md`
- [X] T045 [US5] Conduct the observed unfamiliar-contributor quickstart walkthrough and record participant assumptions, start/end conditions, elapsed time, undocumented assistance, text/image outcomes, output discovery, and permanent-ID explanation in `specs/001-build-anki-deck/validation-results.md`

**Checkpoint**: US5 passes the documentation contract and the recorded unfamiliar-contributor
walkthrough completes within 15 minutes without undocumented assistance.

---

## Phase 8: Polish and Cross-Cutting Verification

**Purpose**: Finish performance, repository hygiene, and whole-suite verification without adding
new product scope.

- [X] T046 Add a generated 1,000-concept under-60-second validation/build acceptance case with documented machine/environment measurement context in `tests/integration/test_performance.py` and `specs/001-build-anki-deck/validation-results.md`
- [X] T047 Run `pytest`, `ruff check .`, and `ruff format --check .`, fixing findings only in `src/indo_malay_anki/`, `tests/`, and `templates/`
- [X] T048 Audit `.gitignore`, `data/vocabulary.tsv`, `media/`, `templates/`, and `dist/` so authoritative inputs remain version controlled, prompt examples and synthetic fixtures remain non-authoritative, and `.apkg`/temporary outputs remain untracked

**Checkpoint**: All automated gates and recorded acceptance walkthroughs pass, performance is
measured, and the repository contains authoritative inputs rather than generated deck artifacts.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundational)**: Depends on Setup and blocks every user story. It completes all source
  and media validation before any builder or temporary-package task exists.
- **Phase 3 (US1)**: Depends on the full Foundational gate and produces the independently usable MVP.
- **Phase 4 (US2)**: Depends on Foundational validation. It may be implemented after US1 or alongside
  US1 with coordination because both can touch CLI tests/code; it does not weaken the US1 gate.
- **Phase 5 (US3)**: Depends on the completed US1 builder and package.
- **Phase 6 (US4)**: Depends on US1 and follows US3 so it can reuse stable semantic-manifest checks.
- **Phase 7 (US5)**: Depends on finalized behavior from US1–US4.
- **Phase 8 (Polish)**: Depends on all desired stories.

### User Story Dependency Graph

```text
Setup -> Full Validation Foundation -> US1 (MVP)
                                  \-> US2
US1 -> US3 -> US4
US1 + US2 + US3 + US4 -> US5 -> Polish
```

### Within Each Phase

1. Write the listed tests and observe the relevant failures.
2. Implement immutable domain types before loaders and validators.
3. Complete parsing before content/media validation and validation before generation.
4. Complete templates and builder behavior before end-to-end CLI build integration.
5. Run the phase-specific automated subset before its manual acceptance task or checkpoint.
6. Preserve fixed deck/model/GUID/schema compatibility throughout later stories.

### Parallel Opportunities

- **Setup**: T003 and T004 can proceed in parallel after project metadata direction is established.
- **Foundation**: T005 and T006 can start together; after T006, T007, T008, and T010 target separate
  test files and can proceed in parallel.
- **US1**: T016 and T017 target separate test files; T020–T022 target separate templates.
- **US3**: After T030, T031 and T032 target separate test files.
- **US4**: T038 and T039 target separate integration-test files.
- Later implementation tasks that share `builder.py`, `validator.py`, `cli.py`, or `README.md` remain
  sequential even when their conceptual cases are independent.

---

## Parallel Examples by User Story

### User Story 1

```text
T016 tests/contract/test_template_contract.py
T017 tests/integration/test_build_package.py

T020 templates/front.html
T021 templates/back.html
T022 templates/style.css
```

### User Story 2

```text
T026 tests/unit/test_loader.py + tests/unit/test_validator.py
T027 tests/contract/test_cli_contract.py
```

T026 and T027 may be drafted in parallel only after coordinating their shared diagnostic vocabulary.

### User Story 3

```text
T031 tests/unit/test_model.py
T032 tests/integration/test_semantic_rebuild.py
```

### User Story 4

```text
T038 tests/integration/test_semantic_rebuild.py
T039 tests/integration/test_build_package.py
```

### User Story 5

```text
T041 tests/contract/test_readme_contract.py
```

README tasks T042–T044 remain sequential because they edit the same file.

---

## Implementation Strategy

### MVP First: User Story 1

1. Complete Setup.
2. Complete the full Foundational validation and identity gate.
3. Complete all US1 tests, templates, builder, and build integration.
4. Run the US1 automated subset against text-only and image-backed fixtures.
5. Complete the desktop/mobile first-import smoke record in T025.
6. **STOP and validate**: only now is US1 the usable MVP.

### Incremental Delivery

1. **US1**: Fully validated, failure-atomic text/image deck plus desktop/mobile first import.
2. **US2**: Complete actionable invalid-source diagnostics and aggregation evidence.
3. **US3**: Stable rebuild identity, re-import, and omission behavior.
4. **US4**: Add/change/remove optional-image identity lifecycle.
5. **US5**: Contributor-owned documented workflow and observed 15-minute walkthrough.
6. **Polish**: Performance, whole-suite quality gates, and repository hygiene.

### Commit Strategy

- Use Conventional Commits for each task or coherent test/implementation pair.
- Keep compatibility-sensitive identity changes isolated and explicitly described.
- Never commit generated `.apkg` or invocation-owned temporary package output.

## Notes

- `[P]` tasks target different files and require their stated prerequisites first.
- Every user-story task has exactly one `[US#]` traceability label.
- Setup, foundational, and polish tasks intentionally have no story label.
- Tests precede their corresponding implementation work.
- Stop at each checkpoint and verify that story independently before proceeding.
- Do not add publishing, translation, generated vocabulary, image search, audio, web UI, databases,
  cloud services, or other excluded scope while implementing these tasks.

## Phase 9: Convergence

- [X] T049 CRITICAL Reconcile the approved `Bahasa Melayu` card prompt and answer label with the `Bahasa Malaysia` mandate in `.specify/memory/constitution.md` through its reviewed amendment process; align the conflicting wording in `specs/001-build-anki-deck/spec.md` and preserve the existing five-field note schema and stable identities per Constitution II, IV and FR-021/FR-024 (contradicts)
- [X] T050 Catch malformed image URL parsing errors in `src/indo_malay_anki/validator.py`, report a row/concept/field validation issue without a traceback, and add regression coverage for inputs such as `http://[broken` in `tests/unit/test_validator.py` and `tests/contract/test_cli_contract.py` per FR-009/FR-011 (partial)
- [X] T051 Preserve every safe image-reference-to-packaged-basename mapping when different relative paths resolve to the same source file, while bundling that file once; add a symlink-alias package regression in `tests/integration/test_build_package.py` per FR-026 and US1/AC3 (partial)
- [X] T052 Complete and record first-import smoke acceptance in `specs/001-build-anki-deck/validation-results.md` with Anki Desktop and official mobile client names/versions, text- and image-cue cards, bundled media, offline study, visible labels/answers, and long-text/oversized-image behavior at approximately 320 CSS pixels without horizontal scrolling, JavaScript, or network access per FR-034/SC-005 (partial)
- [X] T053 Complete and record the disposable Anki Desktop re-import walkthrough in `specs/001-build-anki-deck/validation-results.md`, including client version, import settings, exact note/card counts, review-state preservation, and recreation under the same GUID after the collection note is independently deleted per US3/AC6 and SC-009 (partial)
- [X] T054 Complete and record an observed unfamiliar-contributor walkthrough that adds both text-only and image-backed concepts, validates and builds the deck, finds the output within 15 minutes after environment setup, and notes any undocumented assistance in `specs/001-build-anki-deck/validation-results.md` per SC-006 (partial)

## Phase 10: Convergence

- [X] T055 Record the concrete acceptance metadata for the user-reported passing manual checks in `specs/001-build-anki-deck/validation-results.md`: Anki Desktop and official mobile client names/versions and operating systems, import settings, exact note/card counts and review-state outcome, tested mobile viewport width, and contributor walkthrough elapsed-time bound and assistance status per FR-034, SC-005, SC-006 and US3/AC6
