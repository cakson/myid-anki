# Quickstart and Validation Guide

This guide describes the runnable checks the implementation must support. See
[the CLI contract](contracts/cli.md), [the TSV contract](contracts/vocabulary-tsv.md), and
[the Anki package contract](contracts/anki-package.md) for exact behavior.

## 1. Create the Local Environment

Prerequisites:

- Conda or a compatible environment manager
- A platform supported by Python 3.12+
- Network access for initial dependency installation only

From the repository root:

```console
conda env create -f environment.yml
conda activate myid-anki
```

After installation, the normal validation, test, and build workflows must run without network
access.

## 2. Inspect the Source Layout

Confirm these repository inputs exist:

```text
data/vocabulary.tsv
media/
templates/front.html
templates/back.html
templates/style.css
```

The TSV must follow [the vocabulary contract](contracts/vocabulary-tsv.md). In particular, IDs are
six-digit strings and must never be renumbered merely because vocabulary content changes.
Prompt examples are not production vocabulary. If the repository source contains only the header,
add at least one reviewed concept before expecting validation or build to succeed.

## 3. Validate Vocabulary

```console
python -m indo_malay_anki validate
```

Expected result for valid source data:

- Exit status is `0`.
- Output reports the concept and distinct-media counts.
- No `dist/` package is created by validation.

Expected result for invalid source data:

- Exit status is `1`.
- Diagnostics identify the row, concept, and field whenever available.
- Package generation is not attempted.
- `dist/myid-anki.apkg` is not created, replaced, truncated, or partially written.
- Any prior successful `dist/myid-anki.apkg` remains byte-for-byte unchanged.

Required negative scenarios are exercised automatically by the test suite rather than by editing
the authoritative vocabulary file during normal use.

## 4. Run Automated Quality Checks

```console
pytest
ruff check .
ruff format --check .
```

The suite must cover:

- Valid TSV parsing and leading-zero preservation
- Exact six-digit ID validation and duplicates
- Required fields, row shape, UTF-8, and whitespace rejection
- Empty/header-only source rejection
- Missing, traversing, symlink-escaping, non-file, and remote media rejection
- Exact same-file reuse and Unicode-case-folded distinct-file basename collisions
- Golden and mutation-invariant GUID behavior
- Fixed deck/model IDs, field schema, template count, note count, and card count
- Image-versus-English front selection and absence of front-side answer leakage
- Package media contents and normalized semantic equivalence across rebuilds
- Preservation of an existing output after validation or package-generation failure

## 5. Build the Deck

```console
python -m indo_malay_anki build
```

Expected result:

- Validation runs first.
- Exit status is `0`.
- The final package is `dist/myid-anki.apkg`.
- Output reports note, card, and media counts.
- No temporary package remains.

The generated `.apkg` is an artifact. Do not edit it manually; change repository source and rebuild.

## 6. Inspect Package Semantics

The integration suite must open the generated archive and its collection database to verify the
semantic manifest in [the package contract](contracts/anki-package.md). At minimum, confirm:

- Deck ID `1242123295`
- Model ID `1942161817`
- GUID `D6BBAuKXK` for concept `000001`
- Exactly five ordered fields and one template
- One note and one card per source row
- Every referenced image is present under its basename

Archive bytes may differ across builds because timestamps and storage layout are not identity.

## 7. Manual Anki Desktop and Mobile Acceptance

Use disposable collections or back up the test collections first. Record dated results in
`specs/001-build-anki-deck/validation-results.md`; keep this quickstart as reusable instructions.
The record must identify the Anki Desktop version, the official mobile Anki client name and version,
the operating systems, and the import settings used.

### Initial Desktop Smoke Acceptance

1. Build and import `dist/myid-anki.apkg` into Anki Desktop.
2. Confirm the imported note and card counts equal the source concept count, with exactly one note
   and one card for each concept.
3. Disable network access or otherwise confirm the collection is being studied offline.
4. Study a text-cue card. Confirm English is the prominent front cue, neither target answer appears
   on the front, and both labeled language answers appear together on the back.
5. Study an image-cue card. Confirm the bundled image is the primary front cue, no target answer
   appears on the front, English is secondary context on the back, and both labeled answers appear.
6. Confirm the two cards require neither JavaScript nor a network connection for core behavior.

### Initial Mobile Smoke Acceptance

1. Import or transfer the same `dist/myid-anki.apkg` into one official mobile Anki client.
2. Study the same text-cue and image-cue cases offline.
3. At a viewport width of 320 CSS pixels or greater, study cards with long English, Indonesian,
   and Malaysian values and an image larger than the viewport. Confirm all text wraps inside the
   card, images remain bounded, and nothing requires horizontal scrolling, custom zooming, or
   interaction; both language labels and answers remain visible and distinguishable.
4. Confirm the image is loaded from bundled media and core behavior requires neither JavaScript nor
   network access.

### Desktop Re-import and Removal Acceptance

1. In the disposable desktop collection, record one concept's note count and review state.
2. Change only that concept's mutable source content while keeping its six-digit ID unchanged.
3. Build a later package and re-import it. If the recorded Anki Desktop version offers import update
   choices, select the option that updates existing notes; otherwise ensure the second build has a
   later timestamp.
4. Confirm the content changed, the collection gained no duplicate note, and review state remains.
5. Remove one test concept from the TSV, rebuild, and re-import. Confirm it is absent from the new
   package but its prior collection note was not automatically deleted.
6. Restore the reviewed source data after the disposable acceptance exercise.

### Rapid Rebuild and Reintroduction Regression Acceptance

Automated same-second test: hold the injected wall clock at one whole-second value, build package A
with a concept, change one mutable field, and immediately build package B. Inspect both package
notes and confirm their GUIDs match and B's note modification timestamp is strictly newer. No sleep
or real-time clock advance is permitted.

Automated identity lifecycle test: build package A with a concept, remove it and build package B,
then reintroduce the same ID and build package C. Confirm the GUID in C exactly matches A. In the
disposable Anki collection, verify import does not duplicate an extant matching note; if the test
note was independently deleted from the collection, re-import creates the note with that same GUID.

The initial desktop and mobile smoke scenarios are part of the usable US1 acceptance gate. The
later re-import scenario validates client-controlled update behavior. Automated tests remain
responsible for every identity and package property controlled by this project.

## 8. Performance Acceptance

Using a generated test fixture rather than committed vocabulary, validate and build 1,000 concepts.
The complete operation must finish in less than 60 seconds on the documented supported development
machine. Record the machine and environment details with the result so the threshold is meaningful
and not enforced as a brittle per-unit-test timeout.
