# Implementation Plan: GitHub Deck CI and Releases

**Branch**: `002-github-deck-releases` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-github-deck-releases/spec.md`, including the latest instruction to publish `indonesian-malaysian.apkg`.

## Summary

Add explicit GitHub Actions workflows for pull request/main checks and version-tag releases. Both use Python 3.12, install the project's `.[dev]` dependency set, and invoke the documented local validation, test, lint, formatting, and build commands. CI uploads the generated local package as a run artifact. The release workflow validates and builds the tagged revision in a read-only job, then passes that same run's package to a narrowly privileged publication job that creates or updates the corresponding Release asset under the learner-facing filename.

## Technical Context

**Language/Version**: Python 3.12 (project's `environment.yml`; `pyproject.toml` permits 3.12 or newer)

**Primary Dependencies**: Existing editable project installation with `.[dev]` (`genanki`, `pytest`, `ruff`); GitHub-hosted Actions and built-in `GITHUB_TOKEN`

**Storage**: Repository-managed TSV/media/templates, run-scoped Actions artifacts, and GitHub Release assets; no database or new service

**Testing**: `python -m indo_malay_anki validate`, `pytest`, `ruff check .`, `ruff format --check .`, `python -m indo_malay_anki build`; focused workflow configuration inspection and manual GitHub acceptance

**Target Platform**: GitHub-hosted Linux runner for automation; resulting standard `.apkg` for Anki Desktop and official mobile clients

**Project Type**: Python CLI repository with repository automation

**Performance Goals**: Existing local 1,000-concept build target of under 60 seconds after setup; no new CI wall-time SLA

**Constraints**: No Docker, new secrets, automatic content generation, AnkiWeb publishing, or release on normal main pushes; preserve concept, GUID, deck, and model identities

**Scale/Scope**: Two workflow files, one README update, and narrow verification; one deck asset per release tag

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle / constraint | Pre-design | Post-design |
|---|---|---|
| I, XIII: Repository source stays authoritative; packages are generated outputs | Pass | Pass: both distribution forms originate from repository inputs |
| V, VI: Stable concept, GUID, deck, and model identity | Pass | Pass: workflows invoke the existing builder and only rename a publication copy; release tags never enter Anki identity code |
| VII, VIII: Reviewed vocabulary and validation before generation | Pass | Pass: existing validation command and build validation run; header-only source remains a failing prerequisite |
| IX: Local build remains offline and deterministic in identity | Pass | Pass: network use is confined to CI setup and distribution, not the generator |
| X, XI: Portable Anki package and repository-managed media | Pass | Pass: same local `.apkg` is distributed without repackaging or image acquisition |
| XII, architectural scope: Simple, inspectable tooling; external distribution requires explicit feature specification | Pass | Pass: this specification explicitly authorizes GitHub CI and Releases; no application server or new runtime service |
| XIV, development gates: Critical behavior stays tested | Pass | Pass: full existing suite runs; focused checks cover workflow contract and tag-independent identity |
| Governance: No identity or schema migration without review | Pass | Pass: no identity or schema change planned |

No constitutional exception or amendment is required.

## Project Structure

### Documentation (this feature)

```text
specs/002-github-deck-releases/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── workflow-distribution.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
.github/workflows/
├── ci.yml                       # pull request and main checks
└── release.yml                  # version-tag build and publication
README.md                       # contributor, maintainer, learner instructions
environment.yml                 # existing Python 3.12 and editable dev install declaration
pyproject.toml                  # existing dependency, pytest, and Ruff configuration
data/vocabulary.tsv             # reviewed source; currently requires at least one valid concept
src/indo_malay_anki/            # existing validation and package generator; no identity changes
tests/
├── contract/                   # existing CLI/README contracts; add focused workflow checks only if useful
├── integration/                # existing package and stable-identity verification
└── unit/
```

**Structure Decision**: Keep automation at the repository boundary. Use direct project commands in each workflow, with limited duplicate quality-gate steps for auditability. No reusable workflow or new Python build wrapper is needed.

## Phase 0: Research Decisions

See [research.md](research.md) for current GitHub behavior and alternatives. The key decisions are:

1. Use separate CI and release workflows. The release has a read-only check/build job and a dependent write-scoped publish job.
2. Filter tag pushes with `v*.*.*`, then strictly guard `v[0-9]+.[0-9]+.[0-9]+` before publication because the event filter is a glob.
3. Use the existing local output path `dist/myid-anki.apkg` for builds and run artifacts. Rename a copy to `indonesian-malaysian.apkg` only when publishing.
4. Transfer the release build with a same-run artifact, never with an artifact from an unrelated CI run.
5. Treat attempted artifact upload failure as a failed run, as clarified in the spec.

## Phase 1: Design

See [data-model.md](data-model.md), [contracts/workflow-distribution.md](contracts/workflow-distribution.md), and [quickstart.md](quickstart.md).

- CI: checkout, set up Python 3.12 with simple pip caching, install `-e .[dev]`, execute the five existing commands in order, and upload `dist/myid-anki.apkg` with a clear artifact name and missing-file failure.
- Release build job: tag checkout, strict tag-name guard, the same environment and five commands, then upload the package to this run for transfer. Keep `contents: read`.
- Release publication job: depend on successful build; download only this run's named artifact; copy to `indonesian-malaysian.apkg`; create/update the release for the triggering tag and overwrite that filename. Scope `contents: write` only to this job. Fail for missing package or publication errors.
- Documentation: retain local commands and output path, add CI artifact location, tag push/release steps, latest-release download, and Anki update guidance with identity limits.
- Verification: inspect workflow syntax and trigger/permission/asset fields using a lightweight parser or targeted checks; reuse existing integration tests for identity. Do not emulate GitHub Actions. Manual acceptance covers a passing PR, downloadable CI artifact, test tag, Release asset, and Anki import.

## Implementation Risks and Prerequisites

- The checked-in vocabulary currently has only its header. Existing validation intentionally rejects zero concepts. A real CI success and test release require a maintainer-reviewed concept committed before acceptance; do not add invented vocabulary to make automation green.
- GitHub repository settings must allow Actions and release creation with the built-in token. This is a repository configuration prerequisite, not a new secret.
- The first remote acceptance run is needed to prove GitHub event filters, artifact transfer, and release publication. Local checks can validate configuration and package identity but cannot prove hosted-service behavior.
