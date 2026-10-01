# Phase 0 Research: Build Local Anki Deck

## Python Packaging and Development Environment

**Decision**: Use Python 3.12+, a single `pyproject.toml`, setuptools, and the
`src/indo_malay_anki/` layout. Declare `genanki` as the runtime dependency and `pytest` plus `ruff`
as a development extra. Provide `environment.yml` with Python 3.12, pip, and an editable install of
the development extra.

**Rationale**: The `src/` layout prevents accidental imports from the checkout and makes tests use
the installed package. One dependency authority avoids drift between Conda and Python metadata;
normal validation and build need no network after environment setup.

**Alternatives considered**: A flat package layout was rejected because it can hide packaging
errors. Duplicate dependency lists in Conda and Python files were rejected because they drift.
Separate requirements files were rejected because `pyproject.toml` already expresses runtime and
development needs.

**Sources**: [Python Packaging User Guide](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/),
[pytest good practices](https://docs.pytest.org/en/9.0.x/explanation/goodpractices.html),
[Conda environment management](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html)

## Command-Line Interface

**Decision**: Implement `main(argv=None) -> int` with standard-library `argparse` subcommands.
Canonical commands are `python -m indo_malay_anki validate` and
`python -m indo_malay_anki build`; a `myid-anki` console script may call the same function.

**Rationale**: One importable entry point is directly testable, works through both `python -m` and
an installed console command, and requires no CLI framework.

**Alternatives considered**: A third-party CLI library adds no V1 value. Executing `cli.py`
directly was rejected because package-relative imports become fragile. A console-script-only
workflow was rejected because the module command is clearer during local development.

**Sources**: [Python `-m` command](https://docs.python.org/3.12/using/cmdline.html),
[Python `__main__`](https://docs.python.org/3/library/__main__.html)

## TSV Parsing and Validation Boundary

**Decision**: Open the source with `encoding="utf-8"` and `newline=""`; parse with
`csv.reader(delimiter="\t", strict=True)`. Require the exact ordered six-column header and exactly
six values per row before constructing a concept. Preserve raw strings, reject any non-empty value
whose `strip()` result differs, validate IDs with ASCII `[0-9]{6}`, then split non-empty tags on
whitespace.

**Rationale**: Explicit row length checks expose extra and missing fields that `DictReader` can
otherwise absorb. Rejecting rather than trimming keeps corrections reviewable and preserves the
constitution's vocabulary-integrity guarantee.

**Alternatives considered**: `DictReader` is workable with explicit rest-key/rest-value checks but
less direct for strict row-shape diagnostics. Manual tab splitting mishandles quoting and embedded
delimiters. Automatic trimming was rejected because it mutates reviewed input.

**Source**: [Python `csv` documentation](https://docs.python.org/3.12/library/csv.html)

## Stable Deck, Model, and Note Identity

**Decision**: Freeze `DECK_ID = 1242123295`, `MODEL_ID = 1942161817`, and
`GUID_NAMESPACE = "myid-anki:v1"`. Construct every note with
`guid=genanki.guid_for(GUID_NAMESPACE, concept.id)`. Lock the golden vector
`000001 -> D6BBAuKXK` in tests.

**Rationale**: genanki recommends choosing deck/model numeric IDs once and hardcoding them. An
explicit project namespace isolates this deck from unrelated GUID domains, while using only the
permanent ID prevents mutable vocabulary, tags, images, or styling from changing note identity.

**Alternatives considered**: genanki's default GUID was rejected because it hashes all fields. A
raw ID GUID was rejected because it lacks project isolation. Random identifiers at build time are
constitutionally prohibited. Changing the namespace or algorithm is a breaking migration.

**Sources**: [genanki README](https://github.com/kerrickstaley/genanki/blob/main/README.md),
[genanki GUID implementation](https://github.com/kerrickstaley/genanki/blob/main/genanki/util.py),
[genanki Note implementation](https://github.com/kerrickstaley/genanki/blob/main/genanki/note.py)

## Note Schema and Templates

**Decision**: Freeze field names and order as `ID`, `English`, `Indonesian`, `Malaysian`, `Image`;
use `ID` as the sort field, normal Anki note tags, and one fixed-name card template. Use Anki native
`{{#Image}}` and `{{^Image}}` conditionals so image-backed cards show generated image HTML and
text-only cards show escaped English. The back shows cue context and both labeled answers. Use no
JavaScript.

**Rationale**: A stable model schema is necessary for repeat imports. Native conditionals express
the cue choice without scripts and work across desktop and mobile clients. Normal tags avoid a
redundant model field.

**Alternatives considered**: Separate Indonesian/Malaysian templates violate the one-card rule.
A dedicated Tags field duplicates Anki behavior. Template JavaScript is unnecessary and weakens
mobile compatibility. Schema changes require a future compatibility assessment and migration.

**Sources**: [Anki conditional replacement](https://docs.ankiweb.net/templates/generation.html#conditional-replacement),
[Anki packaged-deck updating](https://docs.ankiweb.net/importing/packaged-decks.html#updating)

## HTML and Media Representation

**Decision**: HTML-escape English, Indonesian, Malaysian, and generated media filenames before
placing them into note fields. Store the Image field as complete `<img src="basename">` HTML.
Pass resolved source paths to `Package.media_files`, but render basenames only. Reusing the exact
same resolved image is valid; distinct resolved images whose packaged basenames compare equal after
Unicode case folding are rejected, with every conflicting source reference reported.

**Rationale**: Anki fields contain HTML, so escaping prevents source text from changing markup.
Anki media references must be present directly in fields for media discovery, and genanki flattens
filesystem paths to basenames. Case-folded collision checks protect case-insensitive platforms and
prevent silent substitution.

**Alternatives considered**: Putting a bare filename in Image and composing `<img>` in the template
was rejected because Anki may not discover the media reference. Keeping subdirectories in rendered
paths is unsupported. Automatic file renaming adds an unnecessary V1 mapping layer.

**Sources**: [genanki media guidance](https://github.com/kerrickstaley/genanki/blob/main/README.md),
[genanki Package implementation](https://github.com/kerrickstaley/genanki/blob/main/genanki/package.py),
[Anki media](https://docs.ankiweb.net/media.html)

## Media Path Safety

**Decision**: Treat source image references as repository-relative, POSIX-style paths under
`media/`. Reject absolute paths, empty components, `.` or `..` components, backslashes, missing
files, directories, and any path whose strict resolved target is outside the strict resolved media
root. Validate packaged-basename collisions after resolution.

**Rationale**: Lexical checks produce clear diagnostics while resolved containment closes symlink
escapes. A single portable separator keeps source data consistent across developer platforms.

**Alternatives considered**: Lexical `..` checks alone do not prevent symlink escape. Silently
rewriting separators or unsafe paths would hide source errors. Copying or optimizing images is out
of scope.

## Package Output and Failure Atomicity

**Decision**: The full source and media validation pipeline completes before creating a temporary
package or invoking genanki. After successful validation, generate into a uniquely named temporary
`.apkg` in `dist/`, then replace `dist/myid-anki.apkg` only after genanki closes the package
successfully. Validation or generation failure returns nonzero, removes only invocation-owned
temporary output, and never creates, replaces, truncates, or partially writes the final path.

**Rationale**: genanki writes directly to its target archive. Same-directory temporary output plus
`Path.replace()` avoids exposing a partially written final artifact and keeps replacement on one
filesystem.

**Alternatives considered**: Writing directly to the final path can truncate a previously valid
artifact. Starting package work before validation completes risks misleading partial output. A
system temporary directory can cross filesystem boundaries. Alternate output names were rejected;
the project-wide canonical artifact is `dist/myid-anki.apkg`.

**Sources**: [genanki Package implementation](https://github.com/kerrickstaley/genanki/blob/main/genanki/package.py),
[Python `pathlib`](https://docs.python.org/3.12/library/pathlib.html)

## Desktop and Mobile Acceptance Boundary

**Decision**: Automated tests verify all project-controlled package, template, media, offline, and
responsive-layout contracts. Initial smoke acceptance additionally imports the same package into
Anki Desktop and one official mobile Anki client, records both client names and versions, and
studies text-cue and image-cue cards offline at viewport widths of at least 320 CSS pixels.

**Rationale**: Archive inspection cannot prove behavior inside real Anki clients. A small recorded
client matrix directly checks first import, bundled media, visible language labels and answers,
bounded images, and the absence of JavaScript or network dependencies for core behavior without
expanding V1 into automated device infrastructure.

**Alternatives considered**: Desktop-only acceptance leaves the constitutional mobile requirement
unverified. CSS-only assertions cannot establish client rendering or offline media behavior.
Automated mobile-device farms and publishing infrastructure are outside V1 scope.

## Initial Vocabulary Content

**Decision**: Do not copy prompt examples or generate words for `data/vocabulary.tsv`. If no reviewed
project vocabulary is supplied during implementation, commit only the exact schema header and make
README clear that at least one reviewed concept is required before validation or build can succeed.
Use synthetic records only inside automated test fixtures.

**Rationale**: The build system must package reviewed source exactly and must not turn illustrative
examples into authoritative vocabulary. A header-only production source correctly fails the
zero-concept validation gate until a maintainer supplies reviewed data.

**Alternatives considered**: Seeding the example rows was rejected because the user identified them
as structural examples only. Inventing starter vocabulary or translations is explicitly out of
scope.

## Semantic Determinism and Anki Update Behavior

**Decision**: Require semantic equivalence, not byte-identical archives. For a build that supersedes
an existing local package, assign each note a whole-second modification timestamp at least one
second greater than the greatest note timestamp in that immediately preceding package, or the
current whole-second Unix time if that is greater. Thus successive builds remain newer even in the
same wall-clock second or after a clock rollback; no sleeping is required. The first build uses the
current whole-second Unix time. Timestamps never participate in GUID generation. Tests compare
normalized deck/model IDs, schema, templates, CSS, GUIDs, fields, sorted tags, one-card
relationships, and media names/content hashes while ignoring timestamps, SQLite row IDs, ZIP
metadata, and physical ordering, except in explicit monotonic-timestamp tests.

**Rationale**: genanki and archive/SQLite layers contain volatile timestamps and row details.
Freezing them is unnecessary and could prevent corrected content from updating in Anki. Monotonic
note modification metadata preserves newer-wins updates for immediate rebuilds. Stable GUIDs
identify notes; stable model schema permits updates; absent notes are not deletion requests, and
reintroducing an ID regenerates the same GUID without historical state about its omission.

**Alternatives considered**: Byte-for-byte reproducibility would require controlling packaging
internals with no learner benefit. Relying only on wall-clock seconds was rejected because rapid
successive builds can receive equal modification metadata; sleeping between builds was rejected as
unnecessary and unreliable. Stable database note/card row IDs are not required because import
remaps them.

**Sources**: [Anki packaged-deck updating](https://docs.ankiweb.net/importing/packaged-decks.html#updating),
[Anki package importer](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/apkg/import/notes.rs),
[genanki Package implementation](https://github.com/kerrickstaley/genanki/blob/main/genanki/package.py)

## Test Strategy

**Decision**: Use four automated layers: pure unit tests for models/loading/validation/GUIDs;
contract tests for the CLI, field schema, and templates; package integration tests that inspect the
archive and SQLite collection; and rebuild tests that compare normalized semantic manifests.
Document an additional manual official-Anki re-import scenario in the quickstart.

**Rationale**: Mock-only testing cannot prove the emitted package. Installing Anki as a routine test
dependency is disproportionately heavy, while package inspection protects project-controlled
identities and the manual test verifies client-owned import behavior. An atomic-failure test must
pre-seed the final artifact and prove its bytes remain unchanged.

**Alternatives considered**: Only unit tests miss packaging regressions. Making the full Anki client
a required test dependency is version-sensitive and unnecessary for every developer run. The
1,000-row performance check should be a non-brittle acceptance test rather than a tight unit test.

**Sources**: [pytest good practices](https://docs.pytest.org/en/9.0.x/explanation/goodpractices.html),
[Ruff linter](https://docs.astral.sh/ruff/linter/),
[Ruff formatter](https://docs.astral.sh/ruff/formatter/)
