# Feature Specification: Build Local Anki Deck

**Feature Branch**: `main`

**Created**: 2026-10-01

**Status**: Draft

**Input**: User description: "Build the first usable local Indonesian–Malaysian vocabulary Anki
deck generator from a reviewed UTF-8 TSV source, with validation, optional images, stable note
identity, repeatable imports, tests, and contributor documentation."

## Clarifications

### Session 2026-10-01

- Q: What format and comparison rules should permanent concept IDs follow? → A: Exactly six ASCII
  digits, such as `000001`.
- Q: Should a vocabulary source with a valid header but zero concept rows be accepted? → A: No;
  validation and build both fail when there are zero concepts.
- Q: When a concept is removed from the TSV, what should happen after the rebuilt deck is imported
  into an existing Anki collection? → A: Omit it from new packages; do not delete existing
  collection notes.
- Q: If two image references use different relative paths but share the same filename, what should
  the build do? → A: Reject the build and report both conflicting references.
- Q: How should leading or trailing whitespace in non-empty TSV field values be handled? → A:
  Reject it and require the source to be corrected.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate and Study a Vocabulary Deck (Priority: P1)

A deck maintainer builds a standard Anki package from valid vocabulary source data, imports it into
Anki, and studies one card for each vocabulary concept. Each card presents a neutral cue and reveals
both language answers together.

**Why this priority**: Producing a usable deck from reviewed source data is the feature's primary
value and establishes the minimum viable local workflow.

**Independent Test**: Create a valid source containing concepts with and without images, build the
deck, import it into an official Anki client, and verify the note count, card count, media, front,
and back of every card.

**Acceptance Scenarios**:

1. **Given** a valid source with three concepts, **When** the maintainer builds the deck, **Then**
   exactly one package is produced containing three notes and three cards.
2. **Given** a concept without an image, **When** its card is shown, **Then** the front prominently
   displays the English cue and asks for an answer in Bahasa Indonesia or Bahasa Malaysia.
3. **Given** any generated card, **When** the answer is revealed, **Then** both the Bahasa Indonesia
   and Bahasa Malaysia answers are clearly displayed on the same card.
4. **Given** the generated package, **When** it is imported into an official desktop or mobile Anki
   client, **Then** its cards and bundled media remain usable without network access.

---

### User Story 2 - Reject Invalid Vocabulary Safely (Priority: P2)

A deck maintainer validates edited vocabulary before distribution and receives actionable errors
for invalid rows or unsafe media references without producing a misleading new package.

**Why this priority**: Early rejection protects reviewed vocabulary, prevents broken decks, and
makes source errors straightforward to correct.

**Independent Test**: Run validation separately against one valid fixture and fixtures covering
each required failure type, then confirm that failures name the affected row or concept and that a
build attempt does not create or replace an output package.

**Acceptance Scenarios**:

1. **Given** a source with an empty required value or duplicate concept ID, **When** validation
   runs, **Then** it fails and identifies the affected row or concept.
2. **Given** a malformed row whose field count does not match the declared schema, **When**
   validation runs, **Then** it fails with the source row number.
3. **Given** a missing image, absolute media path, or media path that resolves outside the media
   directory, **When** validation runs, **Then** it fails before generation.
4. **Given** any validation failure, **When** the build command runs, **Then** no output package is
   created or overwritten by that invocation.
5. **Given** a valid header with no concept rows, **When** validation or build runs, **Then** it fails
   and reports that at least one vocabulary concept is required.
6. **Given** two image references with different relative paths but the same filename, **When**
   validation runs, **Then** it fails and reports both conflicting references.
7. **Given** any field value with leading or trailing whitespace, **When** validation runs, **Then**
   it fails and identifies the affected row and field without rewriting the value.

---

### User Story 3 - Regenerate Without Duplicating Concepts (Priority: P2)

A deck maintainer corrects vocabulary, tags, imagery, or presentation, rebuilds the package, and
re-imports it while unchanged permanent concept IDs continue to identify the existing Anki notes.

**Why this priority**: Safe repeated imports are essential to maintaining the deck without losing
learner history or accumulating duplicate cards.

**Independent Test**: Build a package, record its deck, note-type, note, and card identities, change
every mutable field and presentation independently, rebuild, and verify that identities tied to the
same concept IDs remain unchanged and each concept still produces one note and one card.

**Acceptance Scenarios**:

1. **Given** two consecutive builds from unchanged source, **When** their logical contents are
   compared, **Then** the deck identity, note-type identity, note identities, and one-card-per-note
   structure are unchanged.
2. **Given** an existing concept whose English, Indonesian, Malaysian, image, or tags value changes,
   **When** the deck is rebuilt, **Then** the note retains the identity derived from its permanent ID.
3. **Given** a concept with ID `000001`, **When** its source is parsed and built, **Then** the leading
   zeroes remain part of the concept identity.
4. **Given** a previously imported deck and a rebuilt package with the same stable identities,
   **When** the learner re-imports it using supported Anki update behavior, **Then** unchanged concept
   IDs are recognized as existing notes rather than introduced as distinct notes.
5. **Given** a concept is removed from the TSV after an earlier package was imported, **When** a new
   package is built and imported, **Then** the concept is absent from the new package and the import
   does not request deletion of its existing note from the learner's collection.

---

### User Story 4 - Maintain Optional Images (Priority: P3)

A deck maintainer can add or remove a repository-managed image reference without changing the
concept identity. A referenced image replaces the English text as the primary front cue and is
included in the package.

**Why this priority**: Images improve neutral recall cues, but text-only vocabulary must remain fully
usable and image handling must not weaken identity or safety guarantees.

**Independent Test**: Build a concept first without an image, then with a valid nested media
reference, and finally without it again; verify cue selection, packaged media, and stable identity.

**Acceptance Scenarios**:

1. **Given** a concept with a valid image reference, **When** its card front is shown, **Then** the
   image is the primary cue, the English word is not the primary front cue, and neither target
   language answer appears.
2. **Given** that image-backed card, **When** its answer is revealed, **Then** the English cue is
   available as secondary context and both target-language answers are shown.
3. **Given** an image is added to or removed from an existing concept, **When** the deck is rebuilt,
   **Then** the concept's note identity remains unchanged.

---

### User Story 5 - Follow the Documented Local Workflow (Priority: P3)

A new contributor can understand the source format, add a concept or image correctly, validate the
source, build the deck, and locate the result using repository documentation alone.

**Why this priority**: The source-controlled workflow is maintainable only when contributors can
repeat it without hidden knowledge or manual package editing.

**Independent Test**: Give the repository documentation to a developer unfamiliar with the project
and observe whether they can complete the documented workflow without external guidance.

**Acceptance Scenarios**:

1. **Given** a new contributor and a prepared local environment, **When** they follow the README,
   **Then** they can add one concept, validate it, build the deck, and locate the output package.
2. **Given** the README, **When** the contributor reviews identity guidance, **Then** they can explain
   why an existing concept ID must not be changed when its other fields change.

### Edge Cases

- The source file is empty, contains only a header, has a missing or repeated header, or contains an
  unexpected column; each case is invalid.
- A field contains leading or trailing whitespace, a required value is empty, or a row has too few
  or too many tab-separated fields.
- A concept ID has fewer or more than six characters, contains non-ASCII digits, or contains any
  non-digit character.
- Multiple validation problems occur in one row or across several rows.
- The optional image or tags column is blank.
- An image reference is absolute, contains parent-directory traversal, resolves through a symbolic
  link outside the media directory, points to a directory, or uses a missing file.
- Two concepts reference the same valid image.
- Two distinct image references have the same filename and would collide in the package media
  namespace.
- A media filename contains spaces or non-ASCII characters supported by the local filesystem.
- A failed build occurs when an older package already exists in the output directory.
- Source rows are reordered without changing concept IDs.
- Mutable vocabulary fields or card styling change while IDs remain unchanged.
- A concept is removed after an earlier package containing it has already been imported.
- A valid source contains characters used in Indonesian, Malaysian, or English orthography and is
  read without character corruption.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST use exactly one version-controlled UTF-8 TSV file as the vocabulary
  source for this feature.
- **FR-002**: The source schema MUST contain the columns `id`, `english`, `indonesian`, `malaysian`,
  `image`, and `tags`, with one data row representing one semantic vocabulary concept.
- **FR-003**: The `id`, `english`, `indonesian`, and `malaysian` values MUST be non-empty; `image`
  and `tags` values MAY be empty. Every non-empty field value MUST be rejected if it contains
  leading or trailing whitespace, and the system MUST NOT silently trim it.
- **FR-004**: Every concept ID MUST consist of exactly six ASCII digits (`0` through `9`), MUST be
  preserved as text including leading zeroes, and MUST serve as the permanent concept identity.
- **FR-005**: The system MUST reject empty, malformed, and duplicate concept IDs.
- **FR-006**: The system MUST reject malformed source headers, rows with a field count different
  from the declared schema, source content that cannot be read as UTF-8, and sources containing zero
  vocabulary concepts.
- **FR-007**: The system MUST NOT translate, invent, rewrite, normalize, infer, or automatically
  correct any vocabulary content.
- **FR-008**: The system MUST offer a documented local validation command that reports all detected
  validation errors in a run when continued checking is safe.
- **FR-009**: Each validation error MUST identify the source row and concept ID when those values can
  be determined, and MUST state the rejected condition.
- **FR-010**: Image values MUST be interpreted only as relative references within the repository's
  designated media directory.
- **FR-011**: Validation MUST reject image references that are absolute, escape the media directory
  lexically or after path resolution, resolve to a directory, or refer to a nonexistent file.
- **FR-012**: The system MUST offer a documented local build command that performs the complete
  validation step before attempting generation.
- **FR-013**: A build with any validation error MUST fail and MUST NOT create or overwrite an Anki
  package during that invocation.
- **FR-014**: A successful build MUST create exactly one standard Anki `.apkg` package in the local
  `dist/` directory.
- **FR-015**: The package MUST contain exactly one stable deck identity, one stable custom note-type
  identity, and one card template.
- **FR-016**: Each source concept MUST generate exactly one Anki note and exactly one Anki card.
- **FR-017**: The Anki note identity MUST be derived deterministically from only the permanent
  concept ID and MUST remain unchanged when any other field, card styling, or source-row order
  changes.
- **FR-018**: Randomly generated deck, note-type, or note identities MUST NOT be used.
- **FR-019**: Repeated builds from identical inputs MUST be semantically equivalent, including deck,
  note-type, note, card-template, field, tag, and packaged-media content.
- **FR-020**: The generated package MUST support Anki's available recognition and update behavior
  for previously imported notes by preserving all project-controlled identities across builds.
- **FR-021**: A card front without an image MUST display the English cue prominently and the prompt
  "Answer in Bahasa Indonesia or Bahasa Malaysia" without displaying either target-language answer.
- **FR-022**: The stored English value MUST remain unchanged; any capitalization on a card MUST be
  presentation-only.
- **FR-023**: A card front with a valid image MUST display that image as the primary cue instead of
  the English word and MUST display the same neutral-language prompt.
- **FR-024**: Every card back MUST clearly label and display both the Bahasa Indonesia and Bahasa
  Malaysia answers together; image-backed cards MUST also display the English cue as secondary
  context.
- **FR-025**: Cards MUST provide only one review direction and MUST NOT create separate schedules
  for Indonesian and Malaysian recall.
- **FR-026**: Every valid referenced image MUST be bundled in the generated package, and multiple
  concepts MAY reference the same packaged image.
- **FR-027**: Cards MUST remain readable on phone-sized screens, work without network access after
  import, and provide all core behavior without client-side scripting.
- **FR-028**: The normal validation and build workflow MUST work without network access or external
  runtime services.
- **FR-029**: Automated tests MUST cover source parsing, required values, malformed rows, duplicate
  IDs, whitespace rejection, string ID preservation, stable deck/note-type/note identity,
  one-note/one-card generation, media safety, existence, and filename collisions, front cue
  selection, and successful package generation.
- **FR-030**: The README MUST explain the project purpose, TSV schema, adding a concept, maintaining
  permanent IDs, adding an optional image, validation and build commands, output location, and card
  front and back behavior.
- **FR-031**: Maintainers MUST be able to make all vocabulary, template, media, configuration, and
  generator changes in repository source and rebuild without manually editing an `.apkg` file.
- **FR-032**: Removing a concept from the TSV MUST omit it from subsequent packages, and generated
  packages MUST NOT request deletion of a previously imported note that is absent from the new
  package.
- **FR-033**: Validation MUST reject distinct image references whose final filenames are identical
  and MUST report every conflicting reference; repeated use of the same image reference remains
  valid.

### Key Entities *(include if feature involves data)*

- **Vocabulary Concept**: One semantic concept identified permanently by an exactly six-digit text
  ID, with required English, Bahasa Indonesia, and Bahasa Malaysia values plus optional image and
  tags values.
- **Media Reference**: An optional safe relative path from a concept to an existing file contained
  by the repository media directory.
- **Anki Note**: The generated representation of one vocabulary concept, retaining a deterministic
  identity based only on the permanent concept ID.
- **Anki Card**: The sole review card produced by a note, with a neutral front cue and a back that
  reveals both target-language answers.
- **Deck Package**: The single offline-importable build artifact containing the stable deck,
  note type, cards, notes, and referenced media.

### Out of Scope

- Generating, translating, researching, correcting, or expanding vocabulary.
- Downloading, searching, scraping, generating, or optimizing images.
- Pronunciation, audio, or example sentences.
- GitHub Actions, releases, automatic publishing, AnkiWeb publishing, or AnkiConnect.
- Web or vocabulary-editor user interfaces, databases, authentication, synchronization, cloud
  services, or any other network-dependent runtime service.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every valid test source, 100% of source concepts appear in the generated package
  as exactly one note and one card, with no extra notes or cards.
- **SC-002**: Across rebuild tests that alter each mutable field, presentation, and row order, 100%
  of unchanged concept IDs retain the same generated note identity, deck identity, and note-type
  identity.
- **SC-003**: All required invalid-source categories are rejected before package creation, and 100%
  of reported errors identify the row or concept whenever that information is available.
- **SC-004**: A maintainer can validate and build a 1,000-concept source locally in under 60 seconds
  on a supported development machine, excluding initial environment setup.
- **SC-005**: Every card in the acceptance deck can be studied offline in official desktop and
  mobile Anki clients, with readable content in a 320-pixel-wide display area.
- **SC-006**: In an observed documentation walkthrough, a new contributor can add one text-only
  concept, add one image-backed concept, validate the source, build the package, and locate the
  output within 15 minutes after environment setup, without undocumented assistance.
- **SC-007**: Re-import testing using supported Anki update behavior produces zero duplicate notes
  for unchanged permanent concept IDs.

## Assumptions

- V1 uses exactly the six declared TSV columns; unexpected columns are rejected so schema mistakes
  are not silently ignored.
- A blank tags value means no tags. A non-blank tags value represents one or more Anki-compatible
  tag tokens separated by whitespace; validation does not reinterpret their linguistic meaning.
- The generated artifact has the fixed documented path `dist/myid-anki.apkg`.
- A failed build leaves any package from an earlier successful build unchanged and clearly reports
  that no new package was generated.
- The English cue is shown on every card back for consistent context, and is visually secondary when
  an image supplied the primary front cue.
- Compatibility verification targets currently supported official Anki desktop and mobile clients;
  exact import prompts and update controls remain client responsibilities.
- Contributors prepare the documented local development environment before running validation or
  build commands.
- The repository, local filesystem, and Anki client are trusted; multi-user access control and
  untrusted remote input are outside this local-only feature.
