<!--
Sync Impact Report
- Version change: 1.1.0 -> 1.2.0
- Modified principles: II, IV
- Modified sections:
  - Core Principles: learner-facing terminology for the Malaysian Malay answer
- Rationale: Use “Bahasa Melayu” as the learner-facing label while specifying that the deck targets
  Malaysian Malay as used in Malaysia, avoiding an implication that all Malay varieties are covered.
- Compatibility impact: Prompt and answer-label presentation changes only; deck ID, model ID,
  field schema, GUID derivation, and vocabulary data remain unchanged. No note migration is required.
- Added principles: none
- Added sections: none
- Removed sections: none
- Follow-up TODOs: none
-->
# MYID Anki Constitution

## Core Principles

### I. Source Data Is the Source of Truth

Vocabulary entries, card templates, media references, configuration, and build-related source
files MUST live in version control. Generated `.apkg` files are build artifacts and MUST NOT
become the authoritative source of vocabulary data. The repository source MUST be sufficient to
recreate the deck. This ensures that every maintained input is reviewable, reproducible, and
recoverable through version history.

### II. One Vocabulary Concept Produces One Anki Note and One Card

Each vocabulary concept MUST represent one semantic concept and MUST contain a permanent concept
ID, an English cue, a Bahasa Indonesia answer, and a Malaysian Malay answer (Bahasa Melayu as used
in Malaysia). It MAY contain an image reference and tags. Each source concept MUST generate exactly
one Anki note and exactly one card. The generator MUST NOT create separate Indonesian and Malaysian
cards for the same concept. The front MUST instruct the learner to answer in Bahasa Indonesia or
Bahasa Melayu, referring to Malaysian Malay as used in Malaysia. Anki scheduling MUST apply to the
concept as a whole.

### III. Neutral Cue First

The card front MUST use a neutral cue and MUST NOT expose Indonesian or Malaysian vocabulary. The
initial neutral cue is English. When a concept has a valid image, that image MUST replace the
English word as the primary front-side cue; otherwise, the English cue MUST be displayed. The
English cue MUST remain in source data even when an image is used. This keeps recall direction
neutral while preserving a reliable text fallback.

### IV. Both Language Answers Are Revealed Together

The card back MUST clearly display the labels “Bahasa Indonesia” and “Bahasa Melayu” with their
respective answers; the latter answer is Malaysian Malay as used in Malaysia. The learner MUST NOT
be required to choose a target language before answering. The generator MUST NOT create alternate
review directions or independent language schedules. The learner determines the Anki rating based
on their recall of the concept as a whole.

### V. Stable Identity Is Mandatory

Every vocabulary concept MUST have a permanent, unique ID, preserved as a string. Anki note
identity MUST be derived deterministically from that ID alone and MUST NOT depend on English,
Indonesian, or Malaysian text, image filenames, tags, or presentation. Correcting content or
changing optional data MUST NOT produce a different note identity. Deck and note-model identifiers
MUST also remain stable between builds. These rules protect review history and prevent duplicates.

### VI. Preserve Existing Anki Collections Where Practical

Repeated builds and imports of the same deck MUST retain stable identities so Anki can recognize
previously imported notes wherever the package format and client behavior permit. Routine
vocabulary changes MUST NOT unnecessarily generate duplicate cards. Changes to fields, model
identifiers, GUID derivation, or note schemas are compatibility-sensitive and MUST include an
explicit compatibility assessment before adoption.

### VII. Vocabulary Correctness Over Vocabulary Volume

The build system MUST package vocabulary exactly from reviewed source data. It MUST NOT silently
translate, invent, rewrite, normalize linguistic differences, substitute assumed synonyms, infer
missing translations, or automatically correct language content. Linguistic changes MUST be
explicit and reviewable in Git history. Vocabulary generation, AI translation, and language
research remain separate concerns from deck generation.

### VIII. Validation Before Generation

Invalid source data MUST fail the build before a deck is generated. Validation MUST detect missing
or duplicate concept IDs; missing English, Indonesian, or Malaysian text; malformed rows; invalid
image references; missing referenced images; and media paths that escape the intended media
directory. Errors MUST identify the affected row or concept whenever it can be determined. A deck
containing known-invalid source data MUST NOT be emitted.

### IX. Deterministic and Offline Build Process

The normal build MUST work without network access and MUST NOT depend on AI or translation APIs,
image search, remote databases, web services, or external runtime services. Given identical source
data, templates, configuration, and media, builds MUST produce semantically equivalent decks.
Anki identities MUST be deterministic; random identity generation is prohibited.

### X. Mobile-First Anki Compatibility

The primary output MUST be a standard `.apkg` compatible with official Anki clients, including
mobile clients. Cards MUST remain readable and usable on phone-sized screens, MUST work offline
after import, and MUST NOT rely on JavaScript for core behavior. Card presentation SHOULD use
simple, responsive HTML and CSS because these technologies maximize portability across clients.

### XI. Images Are Optional Media, Not Required Vocabulary Data

Images MUST remain optional. Source data MUST reference repository-managed image files rather than
embed image binaries. Every referenced image MUST be packaged into the generated `.apkg`. The
initial system MUST NOT require image downloading, scraping, search, AI generation, or automatic
optimization; any such capability requires a separate future specification.

### XII. Prefer Simple, Inspectable Technology

The implementation SHOULD prefer plain UTF-8 source data, Python, small modules, simple HTML/CSS
templates, filesystem-managed media, command-line tooling, and automated tests because a developer
must be able to understand the project from the repository alone. A local Conda environment MAY
provide dependency isolation. Databases, servers, web or desktop applications, dashboards, cloud
services, and authentication systems MUST NOT be introduced unless an explicit future
specification establishes their necessity.

### XIII. Generated Files Must Not Require Manual Editing

Generated `.apkg` files are outputs and MUST NOT require manual maintenance. All changes MUST be
made in vocabulary source data, templates, media, configuration, or generator code and then rebuilt.
No maintenance workflow may depend on opening or editing the generated package.

### XIV. Important Behavior Must Be Testable

Critical behavior MUST have automated tests wherever it is practical to execute deterministically.
Tests MUST protect source parsing, required-field validation, duplicate-ID detection, preservation
of IDs as strings, stable note identity, stable deck and model identity, media validation,
image-versus-English cue selection, the one-concept/one-card invariant, and successful `.apkg`
generation. Test priority MUST reflect the risk of duplicate cards, broken imports, and corrupted
source interpretation.

## Architectural and Scope Constraints

The initial architecture is limited to a reliable pipeline:

`source vocabulary -> validation -> Anki generation -> .apkg`

Automatic vocabulary generation or translation, AI-generated definitions, automatic image search,
pronunciation generation, audio, example sentences, web-based editing, AnkiConnect integration,
AnkiWeb publishing, synchronization services, databases, and cloud services are outside the core
architecture. Such functionality MUST NOT be added opportunistically and requires an explicit
future specification. Vocabulary data remains plain, reviewable source; media remains
filesystem-based; and the build remains a local command-line operation unless this constitution is
amended.

## Development Workflow and Quality Gates

Every specification and implementation plan MUST demonstrate compliance with this constitution.
Changes MUST flow through version-controlled source and code review. Before generation, the build
MUST run all source and media validation and MUST stop on any known-invalid input. Before merging a
change that affects identity, fields, schemas, templates, or packaging, automated tests MUST verify
the one-note/one-card invariant and all applicable stable-identity guarantees.

Reviewers MUST treat changes to permanent concept IDs, GUID derivation, deck IDs, note-model IDs,
field order, or note schemas as compatibility-sensitive. The change proposal MUST document effects
on existing learner collections and any required migration. Generated packages MUST be verified as
outputs of repository inputs and MUST NOT be accepted as substitutes for source review.

## Governance

This constitution governs the project's architecture and data integrity and supersedes conflicting
project practices. Specifications, plans, tasks, implementation, and reviews MUST comply. If a
proposed feature conflicts with a principle, the conflict MUST be stated explicitly and resolved by
amending the constitution or changing the proposal; a feature MUST NOT silently weaken a principle.

Amendments MUST be made through a reviewed change that documents the rationale, affected principles,
compatibility impact, and any migration required for existing decks or learner collections. Changes
affecting permanent vocabulary identity, Anki note identity, note-model structure, or import/update
compatibility require explicit regression tests and heightened review.

All Git commit messages MUST follow the Conventional Commits specification so that project history
communicates the type and scope of each change consistently.

Constitution versions follow semantic versioning: MAJOR for incompatible governance changes or
principle removals or redefinitions, MINOR for new principles or materially expanded obligations,
and PATCH for clarifications that do not change meaning. Each compliance review MUST confirm that
the constitution version and amendment date are current and that any justified exception is
recorded in the governing specification or plan.

**Version**: 1.2.0 | **Ratified**: 2026-10-01 | **Last Amended**: 2026-10-02
