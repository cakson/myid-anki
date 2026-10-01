# Implementation Plan: Build Local Anki Deck

**Branch**: `main` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-build-anki-deck/spec.md`

## Summary

Build a small Python 3.12 command-line project that reads one strict UTF-8 TSV vocabulary source,
validates every concept and media reference, and uses `genanki` to write one offline-importable
Anki package. The design freezes deck, note-model, field-schema, template-count, and GUID-namespace
compatibility contracts. A note GUID is derived only from its six-digit concept ID. Validation is
shared by the standalone validation command and the build command. The build cannot reach package
generation until the complete source and media validation pipeline succeeds; successful builds
replace the output atomically only after validation and temporary package creation succeed.

## Technical Context

**Language/Version**: Python 3.12 or later

**Primary Dependencies**: `genanki>=0.13.1,<0.14`; Python standard library (`argparse`, `csv`,
`dataclasses`, `html`, `pathlib`, `tempfile`) where practical; setuptools build backend

**Storage**: Version-controlled UTF-8 TSV, HTML/CSS templates, filesystem media, and generated
`dist/myid-anki.apkg`; no database or persistent service

**Testing**: `pytest` with unit, CLI, contract, and package-integration tests; `ruff check` and
`ruff format --check`; recorded first-import smoke acceptance in Anki Desktop and one official
mobile Anki client

**Target Platform**: Local macOS, Linux, or Windows development environment with Python 3.12+;
generated package targets Anki Desktop and one official mobile Anki client whose names and versions
are recorded during acceptance

**Project Type**: Single Python CLI project using a `src/` package layout

**Performance Goals**: Validate and build 1,000 concepts in less than 60 seconds on a supported
developer machine

**Constraints**: Normal validation and build are offline; complete source and media validation
precedes every package-generation attempt; validation failure returns nonzero and cannot create,
replace, truncate, or partially write the final package; one concept produces one note and card;
no JavaScript; immutable stable identities; semantic rather than byte-for-byte determinism

**Scale/Scope**: One six-column TSV source, one deck, one note model, one card template, optional
local images, and approximately 1,000 concepts for V1 acceptance testing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Constitutional gate | Design evidence | Status |
|---|---|---|
| Source data remains authoritative | TSV, templates, configuration, code, and media are repository inputs; `.apkg` is ignored output | PASS |
| One concept yields one note and card | One model and one template; integration tests inspect package note/card counts | PASS |
| Neutral cue and joint answer behavior | Native template conditionals select image or English; back exposes both languages | PASS |
| Stable identity | Fixed deck/model IDs and GUID namespace; GUID input is concept ID only | PASS |
| Existing collection compatibility | Frozen model schema plus newer-wins import guidance and re-import acceptance test | PASS |
| Vocabulary is not rewritten | Parser preserves raw content; whitespace and invalid values are rejected rather than normalized | PASS |
| Validation precedes generation | Both CLI paths use the same full source/media validator; build returns nonzero before temporary or final package work on any validation error | PASS |
| Deterministic offline build | No runtime network calls; semantic manifest comparison protects stable content and identities | PASS |
| Mobile-first package | Simple responsive HTML/CSS, no JavaScript, standard `.apkg`, plus recorded text/image smoke acceptance in Anki Desktop and one official mobile client at widths of at least 320 CSS pixels without horizontal overflow | PASS |
| Optional safe media | Containment, existence, file-type, and packaged-basename collision checks precede bundling | PASS |
| Simple inspectable technology | One Python package, standard-library CLI/parser, filesystem inputs, no services or database | PASS |
| Generated files need no editing | All changes occur in TSV, media, templates, configuration, or Python source | PASS |
| Critical behavior is testable | Unit, contract, integration, CLI, atomic-output, desktop/mobile first-import, and manual Anki re-import checks are defined | PASS |
| Scope remains local pipeline only | No publishing, synchronization, generation, translation, audio, UI, or cloud components | PASS |

**Pre-design result**: PASS. No constitutional violation requires justification.

**Post-design result**: PASS. Phase 1 data, CLI, TSV, and package contracts preserve all gates;
no complexity exception was introduced.

## Project Structure

### Documentation (this feature)

```text
specs/001-build-anki-deck/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── validation-results.md     # Created when manual client acceptance is executed
├── contracts/
│   ├── anki-package.md
│   ├── cli.md
│   └── vocabulary-tsv.md
└── tasks.md                 # Created later by $speckit-tasks
```

### Source Code (repository root)

```text
data/
└── vocabulary.tsv
media/
└── .gitkeep
templates/
├── front.html
├── back.html
└── style.css
src/
└── indo_malay_anki/
    ├── __init__.py
    ├── __main__.py
    ├── model.py
    ├── loader.py
    ├── validator.py
    ├── builder.py
    └── cli.py
tests/
├── fixtures/
├── unit/
│   ├── test_loader.py
│   ├── test_model.py
│   └── test_validator.py
├── contract/
│   ├── test_cli_contract.py
│   ├── test_readme_contract.py
│   └── test_template_contract.py
└── integration/
    ├── test_build_package.py
    └── test_semantic_rebuild.py
dist/
└── .gitkeep
.gitignore
environment.yml
pyproject.toml
README.md
```

**Structure Decision**: Use one installable `src/`-layout package. `model.py` owns immutable domain
values and compatibility constants; `loader.py` parses without normalizing; `validator.py`
aggregates source and media issues; `builder.py` projects validated concepts into genanki objects
and atomically writes the package; `cli.py` provides `validate` and `build`; `__main__.py` delegates
to the CLI. Templates and vocabulary remain visible repository files rather than Python literals.
Tests are separated by unit, external contract, and generated-package integration concerns. The
implementation MUST NOT promote prompt examples or synthetic fixtures into authoritative production
vocabulary; `data/vocabulary.tsv` receives only reviewed maintainer-provided rows.

## Delivery Sequence and Story Boundaries

1. Establish immutable identity constants, strict TSV parsing, and the complete source and media
   validation pipeline.
2. Gate the build entry point on a successful `ValidatedVocabulary` result. No package-generation
   code or temporary package path is reached after a validation error.
3. Complete US1 as the usable MVP: text and image cue rendering, bundled media, one note and card
   per concept, joint Indonesian/Malaysian answers, atomic output at `dist/myid-anki.apkg`, and
   recorded initial smoke acceptance in Anki Desktop and one official mobile Anki client.
4. Add rebuild/re-import identity coverage, followed by add/change/remove image lifecycle coverage.
5. Finish contributor documentation, performance checks, and cross-cutting regression checks.

US1 is not complete merely because a happy-path package can be written. Its completion gate includes
full validation and failure atomicity plus the initial desktop/mobile smoke acceptance. Later image
lifecycle work verifies that adding, changing, or removing an image preserves note identity; it
does not defer initial image rendering or packaging from US1.

## Client Acceptance Strategy

Automated tests inspect package structure, media, templates, responsive CSS contracts, and the
absence of JavaScript or remote resources. Manual acceptance uses a disposable collection and
records the Anki Desktop and official mobile client names and versions. On both clients it studies
at least one text-cue card and one image-cue card offline, confirms bundled media, checks both
language labels and answers, and evaluates readability at viewport widths of at least 320 CSS
pixels. Mobile acceptance also uses long uninterrupted English, Indonesian, and Malaysian values
and an image wider than the viewport: content must wrap or scale within the viewport without
horizontal scrolling, interaction, or custom zooming. Results belong in `validation-results.md`,
keeping `quickstart.md` as reusable instructions.

Rebuild identity tests control the wall clock: after package A, mutate a field and immediately
build B in the same simulated wall-clock second. B must retain the GUID and have note modification
metadata strictly newer than A. For successive real builds, derive the next timestamp from the
preceding package's greatest note timestamp, bounded below by current whole-second Unix time; do
not sleep between builds. A remove/build/reintroduce/build test verifies that a permanent ID always
recreates its original deterministic GUID, independently of intermediate omissions.
