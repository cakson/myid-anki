# Feature Specification: Validate and Release Anki Deck

**Feature Branch**: `002-github-deck-releases`

**Created**: 2026-10-03

**Status**: Draft

**Input**: User description: "Add automated validation, deck building, and tag-triggered GitHub Release distribution for the Indonesian–Malaysian Anki deck, with inspectable CI artifacts, stable Anki identities, minimal permissions, and contributor and learner documentation."

## Clarifications

### Session 2026-10-03

- Q: If the deck builds successfully but GitHub cannot upload the CI artifact, should the CI run fail? → A: Yes; fail CI when the artifact upload fails.
- Q: What filename should learners download from a GitHub Release? → A: `indonesian-malaysian.apkg`; the existing local build remains `dist/myid-anki.apkg`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check Every Proposed Change (Priority: P1)

A contributor edits vocabulary, media, templates, or code. A pull request or push to main reports whether that exact revision passes project checks and can produce a valid deck.

**Why this priority**: Every distributed deck must come from checked source.

**Independent Test**: Run checks for one valid revision and revisions with deliberate failures in each required check; inspect run results and a successful build artifact.

**Acceptance Scenarios**:

1. **Given** valid inputs, **When** a pull request or main-branch push runs, **Then** the supported environment and dependencies are prepared, existing validation, tests, Ruff lint, Ruff formatting, and deck build all pass.
2. **Given** invalid vocabulary or media, a failing test, a lint or formatting violation, or a build error, **When** checks run, **Then** the run fails and does not report a successful deck output.
3. **Given** a successful run, **When** a maintainer inspects it during the repository's configured Actions artifact retention period, **Then** the generated `.apkg` is available as a GitHub Actions artifact.
4. **Given** an ordinary push to main, **When** checks complete, **Then** no learner-facing GitHub Release is created solely from that push.

---

### User Story 2 - Publish an Explicit Version (Priority: P1)

A maintainer tags a reviewed revision. The tagged source passes the same checks, and learners can download its deck from the corresponding GitHub Release.

**Why this priority**: A deliberate release gives learners a stable download tied to reviewed source.

**Independent Test**: Push `v0.1.0` at a valid revision, compare the released package with that revision, then rerun publication for the tag.

**Acceptance Scenarios**:

1. **Given** a matching version tag, **When** it is pushed, **Then** the tagged revision is checked out, all required checks pass, and the package built from it is attached to that tag's release.
2. **Given** a tag pointing to revision A while main has advanced to revision B, **When** the release completes, **Then** the recorded build revision is A and the downloaded Release asset is byte-for-byte identical to the checked package from that tagged run.
3. **Given** an existing release for the tag, **When** publication is rerun successfully, **Then** exactly one stable-named deck asset remains and it contains the newly checked build of that tag.
4. **Given** any failed check or build for a tag, **When** the release run stops, **Then** no new or replacement deck asset is published.
5. **Given** a successful release, **When** a learner visits it on desktop or mobile, **Then** the clearly named `.apkg` can be downloaded and imported into Anki without renaming.

---

### User Story 3 - Import an Updated Deck (Priority: P2)

A learner imports a newer release into a collection containing an earlier release. Concepts with unchanged permanent IDs retain their Anki note identity.

**Why this priority**: Versioned distribution must preserve existing notes and review history where Anki's import behavior permits.

**Independent Test**: Compare packages from two tagged revisions that change a concept's content but retain its permanent ID, then re-import into an existing collection.

**Acceptance Scenarios**:

1. **Given** the same permanent concept ID across releases, **When** packages are compared, **Then** its note GUID is unchanged even when release tags differ.
2. **Given** two releases, **When** packages are compared, **Then** the deck ID and note-model ID are unchanged.
3. **Given** an earlier imported deck, **When** the learner imports a newer release using supported Anki update behavior, **Then** unchanged concept IDs are recognized as existing notes instead of creating duplicates.

---

### User Story 4 - Follow the Documented Workflow (Priority: P3)

Maintainers can find check results, inspect artifacts, and create releases. Learners can find the latest deck and import an update. Contributors can still build locally.

**Why this priority**: The workflow must be understandable without private knowledge.

**Independent Test**: Follow the README from a clean checkout and from a prior Anki import without undocumented steps.

**Acceptance Scenarios**:

1. **Given** the README, **When** a maintainer follows it, **Then** they can identify CI checks, locate an artifact, and create a version tag and release.
2. **Given** the README, **When** a learner follows it, **Then** they can locate the latest release asset, download it, and import it into Anki.
3. **Given** a prior import, **When** a learner follows the update instructions, **Then** they can import the newer package into the same collection and understand how permanent concept IDs preserve note identity.
4. **Given** the README, **When** a contributor follows the local instructions, **Then** they can still validate and build using the existing project commands.

### Edge Cases

- A vocabulary file containing only its header has no valid concepts under current rules. Checks and releases fail until reviewed concepts are added; automation does not invent vocabulary.
- A tag points to an invalid revision while main passes. No deck asset is published for that tag.
- A tag such as `test-release` or `v0.1` does not trigger release publication.
- Publication is rerun after partial failure or with an existing asset. A successful rerun leaves exactly one deck asset under the stable filename.
- An artifact upload fails after a successful build. The CI run fails and reports the upload failure, even though the validation and build checks passed.
- A concept is removed or reintroduced between releases. Packages do not request deletion from existing collections, and reintroducing its permanent ID restores the same note GUID.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Pull requests and pushes to main MUST check the exact revision associated with the event.
- **FR-002**: Each check MUST prepare a supported Python environment and install the dependencies required for validation, testing, linting, formatting, and building.
- **FR-003**: Each check MUST run the repository's existing source and media validation command, automated tests, Ruff lint check, Ruff formatting check, and deck build command, failing if any step fails.
- **FR-004**: Automation MUST use the same project validation and build commands used locally, without reimplementing vocabulary rules or deck generation in workflow configuration.
- **FR-005**: Every successful CI run MUST upload its generated `.apkg` as an inspectable GitHub Actions artifact. A missing package or failed upload MUST fail the run. The artifact MUST use the repository-configured Actions artifact retention period, with no feature-specific override; documentation MUST state that this temporary artifact is for maintainer inspection.
- **FR-006**: Pull request and normal main-branch checks MUST NOT create or update a learner-facing release.
- **FR-007**: Only pushed tags in `vMAJOR.MINOR.PATCH` form, with nonnegative decimal integer components, MUST trigger release publication.
- **FR-008**: A release run MUST check out the exact tagged revision and pass the same validation, tests, Ruff lint, Ruff formatting, and build checks before publishing.
- **FR-009**: A successful release run MUST create or update the GitHub Release for its tag and attach the `.apkg` built from that tagged revision. The run MUST record the checked-out commit SHA, and the published asset MUST be byte-for-byte identical to that run's checked package apart from its filename.
- **FR-010**: The release asset MUST use the stable filename `indonesian-malaysian.apkg` and MUST be directly importable into Anki; the local build path remains `dist/myid-anki.apkg`.
- **FR-011**: A successful rerun for an existing tag MUST leave exactly one deck asset with the stable filename, containing that rerun's checked build.
- **FR-012**: A failed release check or build MUST NOT create or replace a release deck asset with an unchecked or incomplete package.
- **FR-013**: Release tags MUST remain independent of permanent concept IDs, note GUID derivation, deck ID, and note-model ID; creating a release alone MUST NOT change these Anki identities.
- **FR-014**: Normal CI jobs MUST have read-only repository permissions. Only the job that creates or updates GitHub Releases MAY receive release-write permission.
- **FR-015**: The workflow MUST use built-in GitHub authorization where sufficient and MUST NOT require a new repository secret solely for release publication.
- **FR-016**: The README MUST explain CI validation, artifact location and purpose, maintainer release steps, learner latest-release download and import, update import into an existing collection, and permanent concept IDs' role in note identity.
- **FR-017**: The README MUST retain the existing local environment, validation, and build instructions.
- **FR-018**: Distribution MUST remain limited to GitHub Actions artifacts for inspection and GitHub Releases for learner downloads. AnkiWeb publishing, collection synchronization, web hosting, package registries, Docker, scheduled releases, automatic vocabulary or image acquisition, and mobile app integration are outside this feature.

### Key Entities *(include if feature involves data)*

- **Repository Revision**: The source snapshot checked or released, including vocabulary, media, templates, and generator code.
- **Release Tag**: A maintainer-selected version label identifying the revision to distribute, separate from Anki identities.
- **Deck Package**: The generated importable `.apkg` from a checked revision, built locally at `dist/myid-anki.apkg` and published as `indonesian-malaysian.apkg` in releases.
- **CI Artifact**: A run-scoped package copy for maintainer inspection.
- **GitHub Release**: The learner-facing entry for one tag, containing one stable-named deck asset.
- **Permanent Concept ID**: A concept's source identity from which its stable Anki note GUID is derived independently of release versions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance runs, 100% of valid pull request, main-branch, and release-tag revisions complete required checks and produce an importable package; each deliberately introduced validation, test, lint, formatting, or build failure fails its run.
- **SC-002**: Every successful release acceptance run exposes exactly one stable-named deck download on that version's release page; the recorded checkout SHA equals the tag's target commit, and the downloaded asset's bytes equal the checked package built in that run rather than a later main-branch build.
- **SC-003**: A release rerun ends with exactly one stable-named deck asset containing the rerun's checked package.
- **SC-004**: Across two release revisions, 100% of unchanged permanent concept IDs retain their note GUID, deck and note-model IDs remain unchanged, and re-import creates zero duplicate notes for those IDs under supported Anki update behavior.
- **SC-005**: In a documentation walkthrough, a maintainer can locate a run artifact and complete a tagged release in under 15 minutes after checks finish; a learner can locate, download, and start importing the latest release on desktop or mobile in under 5 minutes, without undocumented steps.
- **SC-006**: In acceptance runs, zero normal main pushes create learner-facing releases, zero nonmatching tags publish releases, and zero failed tagged builds publish a new or replacement deck asset.

## Assumptions

- The existing local commands remain the source of truth. The generated local package uses `dist/myid-anki.apkg`; release publication changes only the asset filename to `indonesian-malaysian.apkg`.
- The repository is hosted on GitHub; maintainers can push tags and access Actions and Releases.
- GitHub's built-in workflow token and artifact service are available, subject to repository settings that permit workflow release creation.
- Release tags identify reviewed, immutable revisions. Moving an existing tag is outside the normal maintainer workflow.
- A green check or release requires at least one reviewed vocabulary concept under existing validation rules; the current source may still contain only a header.
- Anki import prompts vary by client. Documentation describes supported update behavior without promising deletion of notes omitted from later packages.
