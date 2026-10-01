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
- No prior output package is changed.

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
- Same-image reuse and distinct-file basename collisions
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
- The final package is `dist/indo-malay.apkg`.
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

## 7. Manual Official-Anki Acceptance

Use a disposable Anki profile or back up the test collection first.

1. Build and import `dist/indo-malay.apkg` into official Anki desktop.
2. Confirm the imported note and card counts equal the source concept count.
3. Study a text-only card: English is the front cue and both language answers appear on the back.
4. Study an image-backed card: the image is the front cue; English is secondary on the back; both
   language answers appear together.
5. Record a concept's note count and review state.
6. Change only that concept's mutable source content while keeping its six-digit ID unchanged.
7. Build a later package and re-import it. If the Anki version offers import update choices, select
   the option that updates existing notes; otherwise ensure the second build has a later timestamp.
8. Confirm the content changed, the collection gained no duplicate note, and review state remains.
9. Remove one test concept from the TSV, rebuild, and re-import. Confirm it is absent from the new
   package but its prior collection note was not automatically deleted.
10. Restore the reviewed source data after the disposable acceptance exercise.

The manual scenario validates behavior owned by the Anki client; automated tests remain responsible
for every identity and package property controlled by this project.

## 8. Performance Acceptance

Using a generated test fixture rather than committed vocabulary, validate and build 1,000 concepts.
The complete operation must finish in less than 60 seconds on the documented supported development
machine. Record the machine and environment details with the result so the threshold is meaningful
and not enforced as a brittle per-unit-test timeout.
