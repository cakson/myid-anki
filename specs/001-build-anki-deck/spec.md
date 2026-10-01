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
- Q: If distinct image files would be packaged under case-equivalent basenames, what should the
  build do? → A: Reject distinct resolved files whose packaged basenames are equal after Unicode
  case folding and report every conflicting reference; repeated references to the exact same
  resolved file remain valid.
- Q: How should leading or trailing whitespace in non-empty TSV field values be handled? → A:
  Reject it and require the source to be corrected.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate and Study a Vocabulary Deck (Priority: P1)

A deck maintainer builds a standard Anki package from valid vocabulary source data, imports it into
Anki, and studies one card for each vocabulary concept. Each card presents a neutral cue and reveals
both language answers together.

**Why this priority**: Producing a usable deck from reviewed source data is the feature's primary
value and establishes the minimum viable local workflow.

**Independent Test**: Create a valid source containing text-only and image-backed concepts, run the
build, and verify that the complete source and media validation pipeline finishes before package
generation. Verify one note and one card per concept, bundled image media, English-versus-image
front cue selection, and both labeled language answers on the back. Import the package into Anki
Desktop and one official mobile Anki client, then study both cue types offline at a viewport width
of at least 320 CSS pixels without JavaScript or network access; long values and images must not
cause horizontal scrolling.

**Acceptance Scenarios**:

1. **Given** a valid source with three concepts, **When** the maintainer builds the deck, **Then**
   the complete source and media validation pipeline runs first and exactly one package is produced
   at `dist/myid-anki.apkg` containing three notes and three cards.
2. **Given** a concept without an image, **When** its card is shown, **Then** the front displays the
   English cue at least 1.5 times the prompt's font size and at font weight 600 or heavier, and asks
   for an answer in Bahasa Indonesia or Bahasa Melayu as used in Malaysia.
3. **Given** a concept with a valid image, **When** its card is shown, **Then** the bundled image is
   the primary front cue and neither target-language answer appears.
4. **Given** any generated card, **When** the answer is revealed, **Then** both the Bahasa Indonesia
   and Bahasa Melayu labels and answers are visible together on the same card.
5. **Given** any source or media validation error, **When** the build runs, **Then** it exits with a
   nonzero status before package generation and does not create, replace, truncate, or partially
   write `dist/myid-anki.apkg`.
6. **Given** the generated package, **When** it is imported into Anki Desktop and one official
   mobile Anki client, **Then** text-cue and image-cue cards, bundled media, language labels, and
   both answers remain readable and usable offline at viewport widths of 320 CSS pixels or greater
   without JavaScript or network access for core behavior.
7. **Given** cards containing long English, Indonesian, and Malaysian values and an image larger
   than the viewport, **When** the standard templates are studied at 320 CSS pixels or greater,
   **Then** all ordinary text wraps within the card viewport and the image is constrained to it,
   with no horizontal scrolling, custom zooming, or other user interaction required.

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
4. **Given** any validation failure, **When** the build command runs, **Then** it returns a nonzero
   status and does not create, replace, truncate, or partially write the final package; any prior
   successful package remains byte-for-byte unchanged.
5. **Given** a valid header with no concept rows, **When** validation or build runs, **Then** it fails
   and reports that at least one vocabulary concept is required.
6. **Given** distinct resolved image files whose packaged basenames are equal after Unicode case
   folding, **When** validation runs, **Then** it fails and reports every conflicting reference;
   repeated references to the exact same resolved image file remain valid.
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
6. **Given** concept `000001` was included in package A, **When** it is removed and package B is
   built, then reintroduced with the same ID and package C is built, **Then** package C has the same
   deterministic GUID as package A; an existing collection note remains the same logical note
   without duplication, and a note independently deleted by the learner can be imported again with
   that same identity.
7. **Given** package A contains a concept, **When** one mutable field changes and package B is built
   immediately within the same wall-clock second, **Then** the note GUID is unchanged and B's Anki
   note modification metadata is strictly newer than A's, without waiting between builds.

---

### User Story 4 - Maintain the Optional-Image Identity Lifecycle (Priority: P3)

A deck maintainer can add, change, or remove a repository-managed image reference without changing
the concept identity. Image cue rendering and first-import packaging are already part of the usable
US1 pipeline; this story protects identity and package behavior across later image lifecycle edits.

**Why this priority**: Images improve neutral recall cues, but text-only vocabulary must remain fully
usable and image handling must not weaken identity or safety guarantees.

**Independent Test**: Build a concept without an image, add a valid nested media reference, change
it to another valid image, and remove it again; verify each rebuild retains the same note identity
and one-card count while cue selection and packaged media track the current source.

**Acceptance Scenarios**:

1. **Given** a concept with a valid image reference, **When** its card front is shown, **Then** the
   image is the primary cue, the English word is not the primary front cue, and neither target
   language answer appears.
2. **Given** that image-backed card, **When** its answer is revealed, **Then** the English cue is
   available as secondary context and both target-language answers are shown.
3. **Given** an image is added to, changed on, or removed from an existing concept, **When** the deck
   is rebuilt, **Then** the concept's note identity and one-card count remain unchanged.

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
- Two distinct resolved image files have packaged basenames that are equal after Unicode case
  folding and would collide in the package media namespace.
- A media filename contains spaces or non-ASCII characters supported by the local filesystem.
- A failed build occurs when an older package already exists in the output directory.
- Source rows are reordered without changing concept IDs.
- Mutable vocabulary fields or card styling change while IDs remain unchanged.
- A concept is removed after an earlier package containing it has already been imported, then
  reintroduced with the same ID after one or more intermediate packages omitted it.
- Two successive builds occur within the same whole-second clock interval, or the local clock moves
  backward, while the later package is intended to supersede the earlier package.
- Long uninterrupted values or a large image are rendered on a narrow mobile viewport.
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
- **FR-012**: The system MUST offer a documented local build command that completes the full source
  and media validation pipeline before creating any temporary package or attempting package
  generation.
- **FR-013**: A build with any validation error MUST return a nonzero status, MUST NOT create,
  replace, truncate, or partially write `dist/myid-anki.apkg`, and MUST leave any prior successful
  package byte-for-byte unchanged.
- **FR-014**: A successful build MUST create exactly one standard Anki `.apkg` package at the
  canonical path `dist/myid-anki.apkg`.
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
- **FR-021**: A card front without an image MUST display the English cue at a rendered font size at
  least 1.5 times the prompt's font size and at font weight 600 or heavier, followed by the prompt
  "Answer in Bahasa Indonesia or Bahasa Melayu", with Bahasa Melayu referring to Malaysian Malay
  as used in Malaysia, without displaying either target-language answer.
- **FR-022**: The stored English value MUST remain unchanged; any capitalization on a card MUST be
  presentation-only.
- **FR-023**: A card front with a valid image MUST display that image as the primary cue instead of
  the English word and MUST display the same neutral-language prompt.
- **FR-024**: Every card back MUST clearly label and display both the Bahasa Indonesia and Bahasa
  Melayu answers together; the Bahasa Melayu answer represents Malaysian Malay as used in Malaysia.
  Image-backed cards MUST also display the English cue as secondary context.
- **FR-025**: Cards MUST provide only one review direction and MUST NOT create separate schedules
  for Indonesian and Malaysian recall.
- **FR-026**: Every valid referenced image MUST be bundled in the generated package, and multiple
  concepts MAY reference the same packaged image.
- **FR-027**: At viewport widths of 320 CSS pixels or greater, standard card templates MUST NOT
  require horizontal scrolling for ordinary textual content. Long English, Indonesian, and
  Malaysian values MUST wrap within the card viewport, and images MUST be constrained so they
  cannot cause horizontal overflow. These behaviors MUST require no user interaction or custom
  zooming. Cards MUST also show visibly distinct language labels and answers, work without network
  access after import, and provide all core behavior without client-side JavaScript.
- **FR-028**: The normal validation and build workflow MUST work without network access or external
  runtime services.
- **FR-029**: Automated tests MUST cover source parsing, required values, malformed rows, duplicate
  IDs, whitespace rejection, string ID preservation, stable deck/note-type/note identity,
  one-note/one-card generation, media safety, existence, and filename collisions, front cue
  selection, full validation before generation, nonzero validation-failure behavior, preservation
  of any existing final package, and successful package generation.
- **FR-030**: The README MUST explain the project purpose, TSV schema, adding a concept, maintaining
  permanent IDs, adding an optional image, validation and build commands, output location, and card
  front and back behavior.
- **FR-031**: Maintainers MUST be able to make all vocabulary, template, media, configuration, and
  generator changes in repository source and rebuild without manually editing an `.apkg` file.
- **FR-032**: Removing a concept from the TSV MUST omit it from subsequent packages, and generated
  packages MUST NOT request deletion of a previously imported note that is absent from the new
  package.
- **FR-033**: Validation MUST reject distinct resolved image files whose final packaged basenames
  compare equal after Unicode case folding and MUST report every conflicting source reference;
  repeated references to the exact same resolved source file remain valid.
- **FR-034**: First-import acceptance MUST be executed and recorded for Anki Desktop and one
  official mobile Anki client, identified by client name and version. Both clients MUST demonstrate
  offline study of text-cue and image-cue cards, bundled media, 320 CSS-pixel-or-greater viewport
  readability, visible language labels and answers, and no JavaScript or network dependency for
  core card behavior.
- **FR-035**: For each successful build that supersedes a prior local package, every generated
  Anki note's whole-second modification timestamp MUST be strictly greater than the greatest note
  modification timestamp in the immediately preceding package, including when both builds occur
  in the same wall-clock second or the system clock has not advanced. Modification timestamps MUST
  NOT contribute to note identity, which remains derived solely from the permanent concept ID. The
  build MUST NOT sleep or wait for the clock to advance.
- **FR-036**: Reintroducing a previously omitted concept with the same permanent ID MUST produce
  the same deterministic note GUID as before omission, regardless of how many intermediate builds
  omitted it. Package generation MUST NOT encode deletion of omitted notes; re-import may update an
  existing collection note with that identity, while an independently deleted collection note may
  be recreated with the same identity.

### Key Entities *(include if feature involves data)*

- **Vocabulary Concept**: One semantic concept identified permanently by an exactly six-digit text
  ID, with required English, Bahasa Indonesia, and Malaysian Malay (Bahasa Melayu as used in
  Malaysia) values plus optional image and
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
- **SC-003**: All required invalid-source categories are rejected before package creation with a
  nonzero build status; 100% of reported errors identify the row or concept whenever available,
  and the final package is absent or byte-for-byte unchanged from before the failed invocation.
- **SC-004**: A maintainer can validate and build a 1,000-concept source locally in under 60 seconds
  on a supported development machine, excluding initial environment setup.
- **SC-005**: Every text-cue and image-cue card in the acceptance deck can be studied offline in the
  recorded Anki Desktop version and one recorded official mobile Anki client version at viewport
  widths of 320 CSS pixels or greater, with bundled images, both language labels and answers
  visible, and no JavaScript or network dependency for core behavior. Long values wrap and images
  remain within the viewport without horizontal scrolling, custom zooming, or user interaction.
- **SC-006**: In an observed documentation walkthrough, a new contributor can add one text-only
  concept, add one image-backed concept, validate the source, build the package, and locate the
  output within 15 minutes after environment setup, without undocumented assistance.
- **SC-007**: Re-import testing using supported Anki update behavior produces zero duplicate notes
  for unchanged permanent concept IDs.
- **SC-008**: In a controlled same-second test, after package A is built and a mutable field changes,
  an immediate package B build preserves the note GUID and gives every generated note a whole-second
  modification timestamp strictly greater than the maximum note timestamp in A, with no sleep or
  clock wait.
- **SC-009**: In a remove-build-reintroduce-build test, a concept's GUID after reintroduction is
  byte-for-byte the same deterministic GUID as before removal; importing it does not duplicate a
  still-existing matching collection note and can recreate a note independently deleted by the
  learner under that same identity.

## Assumptions

- V1 uses exactly the six declared TSV columns; unexpected columns are rejected so schema mistakes
  are not silently ignored.
- A blank tags value means no tags. A non-blank tags value represents one or more Anki-compatible
  tag tokens separated by whitespace; validation does not reinterpret their linguistic meaning.
- The generated artifact has the fixed documented path `dist/myid-anki.apkg`.
- Any failed build leaves a package from an earlier successful build byte-for-byte unchanged and
  clearly reports that no new package was generated. Validation failures return a nonzero status
  before package generation; later generation failures affect only invocation-owned temporary
  output.
- The English cue is shown on every card back for consistent context, and is visually secondary when
  an image supplied the primary front cue.
- First-import compatibility verification records the name and version of Anki Desktop and one
  official mobile Anki client used for acceptance. Exact import prompts and later update controls
  remain client responsibilities.
- Contributors prepare the documented local development environment before running validation or
  build commands.
- The repository, local filesystem, and Anki client are trusted; multi-user access control and
  untrusted remote input are outside this local-only feature.
