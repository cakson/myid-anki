# Implementation Plan: Build Local Anki Deck

**Branch**: `001-build-anki-deck` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-build-anki-deck/spec.md`

## Summary

Build a small Python 3.12 command-line project that reads one strict UTF-8 TSV vocabulary source,
validates every concept and media reference, and uses `genanki` to write one offline-importable
Anki package. The design freezes deck, note-model, field-schema, template-count, and GUID-namespace
compatibility contracts. A note GUID is derived only from its six-digit concept ID. Validation is
shared by the standalone validation command and the build command, and successful builds replace
the output atomically only after validation and package creation succeed.

## Technical Context

**Language/Version**: Python 3.12 or later

**Primary Dependencies**: `genanki>=0.13.1,<0.14`; Python standard library (`argparse`, `csv`,
`dataclasses`, `html`, `pathlib`, `tempfile`) where practical; setuptools build backend

**Storage**: Version-controlled UTF-8 TSV, HTML/CSS templates, filesystem media, and generated
`dist/indo-malay.apkg`; no database or persistent service

**Testing**: `pytest` with unit, CLI, contract, and package-integration tests; `ruff check` and
`ruff format --check`

**Target Platform**: Local macOS, Linux, or Windows development environment with Python 3.12+;
generated package targets currently supported official Anki desktop and mobile clients

**Project Type**: Single Python CLI project using a `src/` package layout

**Performance Goals**: Validate and build 1,000 concepts in less than 60 seconds on a supported
developer machine

**Constraints**: Normal validation and build are offline; one concept produces one note and card;
no JavaScript; immutable stable identities; no output replacement after validation or generation
failure; semantic rather than byte-for-byte determinism

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
| Validation precedes generation | Both CLI paths use the same validator; build stops before output work on errors | PASS |
| Deterministic offline build | No runtime network calls; semantic manifest comparison protects stable content and identities | PASS |
| Mobile-first package | Simple HTML/CSS, no JavaScript, standard `.apkg`, responsive card layout | PASS |
| Optional safe media | Containment, existence, file-type, and packaged-basename collision checks precede bundling | PASS |
| Simple inspectable technology | One Python package, standard-library CLI/parser, filesystem inputs, no services or database | PASS |
| Generated files need no editing | All changes occur in TSV, media, templates, configuration, or Python source | PASS |
| Critical behavior is testable | Unit, contract, integration, CLI, atomic-output, and manual Anki re-import checks are defined | PASS |
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
