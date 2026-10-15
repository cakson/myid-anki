# Implementation Plan: AI-First Vocabulary Curation

**Branch**: `main` (feature directory `003-vocabulary-curation`) | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature 003 specification and the planning direction to use reusable role-specific AI prompts with a separate evidence-driven verification pipeline.

## Summary

Build a repository-based, AI-assisted curation workflow that produces only verified cross-language contrasts as deterministic learner source data. Small topic batches move through distinct prompt roles and mechanically checked gates. External research and AI happen only during curation. Accepted entries receive permanent IDs, enter an eight-column TSV, and pass the existing offline Anki builder. Shared ordinary vocabulary is rejected. Preserve the current five-field Anki note schema and stable identities; render concise false-friend contrast on the back through an existing back-only answer field.

## Technical Context

**Language/Version**: Python 3.12 or newer, matching `pyproject.toml`

**Primary Dependencies**: Existing `genanki`; Python standard library for curation records, CLI, TSV, and reports; existing `pytest` and `ruff` for development. No mandatory model SDK or hosted service.

**Storage**: Version-controlled UTF-8 `data/vocabulary.tsv`, append-only ID assignment ledger, centralized `curation/config.json` for provider/model and batch defaults, versioned prompt files, and per-batch structured curation records/reports. No database.

**Testing**: Deterministic unit/contract/integration tests for stage schemas, gates, duplicates, export, loader/validator, package contents, and identity; old-to-new package reimport in Anki Desktop before release.

**Target Platform**: Local repository workflow on supported Python platforms; standard offline `.apkg` for Anki Desktop and official mobile clients.

**Project Type**: Python CLI and repository-managed content pipeline.

**Performance Goals**: Curation checks and export finish in under 10 seconds for a 12-candidate batch after AI/evidence artifacts exist; existing 1,000-concept local build target remains under 60 seconds. External research and model latency are excluded.

**Constraints**: No AI/network during validate/build; no runtime AI in Anki; one note/card per concept; no front-side relation or contrast; permanent six-digit ID and GUID derive from ID alone; reject weak content; retain inspectable provenance.

**Scale/Scope**: Initial four batches of at most 12 generated candidates each, followed by further bounded batches if needed to reach 24 accepted concepts across at least three categories and all three eligible contrast relations. Shared ordinary vocabulary is excluded. The target is a completion criterion, never permission to relax acceptance gates.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle / constraint | Pre-design | Post-design |
|---|---|---|
| I, XIII: Source data and generated-output boundary | Pass | Pass: only version-controlled accepted TSV is build input; `.apkg` stays generated |
| II–IV: One concept, neutral front, both answers | Pass | Pass: one note/card; no front leak; contrast is back-only |
| V–VI: Permanent identity and import compatibility | Pass | Pass with release gate: ID-only GUID, fixed deck/model IDs, unchanged five Anki note fields; old-to-new client import must be recorded |
| VII: Correctness over volume and no build-time content inference | Pass | Pass: AI research is separate, acceptance is evidence-gated, build copies approved content |
| VIII–IX: Validation and offline deterministic build | Pass | Pass: new TSV fields validated before build; curation records/models are never build dependencies |
| X–XI: Mobile-compatible cards and optional images | Pass | Pass: existing card model remains; no automatic image work |
| XII: Simple, inspectable technology | Pass | Pass: local Python and text records; no server, database, required SDK, or cloud service |
| XIV: Critical behavior testable | Pass | Pass: seeded negative cases, identity regression, package/client import verification |
| Architectural scope | Pass | Pass: this explicit future feature adds curation before source data, without changing the core build pipeline |
| Governance and schema compatibility | Pass | Pass with release gate: eight-column TSV change is documented; existing note-field schema is preserved and import behavior tested |

No constitutional amendment is required. The compatibility gate is mandatory before publishing a deck built from the expanded source.

## Project Structure

### Documentation (this feature)

```text
specs/003-vocabulary-curation/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── curation-workflow.md
│   └── learner-source.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
curation/
├── prompts/                    # versioned, role-specific instructions and schemas
├── batches/<batch-id>/         # manifest, candidate/stage records, report
└── id-ledger.json              # every permanent assignment, including retired IDs
data/vocabulary.tsv             # accepted learner source only
src/indo_malay_anki/
├── curation/                   # prompt packets, record validation, gates, dedupe, reporting, export
├── loader.py                   # strict eight-column learner-source parser
├── validator.py                # relation and contrast validation plus existing rules
├── model.py                    # learner concept adds relation and contrast; identity untouched
└── builder.py                  # existing five note fields, back-only contrast projection
tests/
├── unit/                       # gate and parsing edge cases
├── contract/                   # curation and learner-source interfaces
└── integration/                # export/build/identity and package regression
README.md                       # learner and maintainer workflow
.github/workflows/release.yml   # accepted-source release build; no AI/research invocation
.gitignore                      # transient export journal and backups are not committed
```

**Structure Decision**: Keep curation as a sibling workflow inside the existing Python package and repository. Versioned prompts and records are plain files. A separate curation command prepares role packets and ingests structured AI results; deterministic code makes acceptance and export decisions. The existing `myid-anki validate` and `build` commands remain AI-free.

## Phase 0: Research Decisions

See [research.md](research.md). The decisions are:

1. Use provider-neutral prompt exchange and distinct roles for discovery, locale research, relation proposal, evidence audit, independent verification, adversarial review, and semantic overlap.
2. Require two independent external evidence signals for ordinary accepted candidates; source claims must be inspected, with usage evidence beyond dictionary existence for preference claims.
3. Use an explicit stricter false-friend gate and a back-only, evidence-backed contrast.
4. Preserve existing Anki note fields and IDs. Expand the learner TSV, not the note schema. Perform actual old-to-new Anki import acceptance.
5. Use file-backed stage records, a deterministic acceptance gate, an assignment ledger, and transactional export.
6. Start with four bounded 12-candidate batches and a 24-accepted completion target, never an acceptance quota.
7. Use the centralized reserve cost policy: Luna handles every role, including independent verification and adversarial review, in separate calls with separate prompts. Verification and adversarial review run only after deterministic semantic, overlap, and evidence prechecks pass. The role record retains the actual model used, and model routing does not alter learner IDs or packet input digests.

All technical-context unknowns are resolved. The AI provider is intentionally pluggable through structured prompt exchange rather than a required dependency.

## Phase 1: Design

See [data-model.md](data-model.md), [contracts/curation-workflow.md](contracts/curation-workflow.md), [contracts/learner-source.md](contracts/learner-source.md), and [quickstart.md](quickstart.md).

### Curation sequence

1. Create a topic batch with scope, prompt-set version, candidate cap, and source-language policy. The AI discovery role proposes candidate-local records without permanent IDs.
2. Normalize only comparison keys for screening; preserve proposed display text. Deterministically screen exact forms, plural/singular and trivial morphological variants, then use AI review for likely synonym and semantic overlap against this batch, prior decisions, and accepted concepts. Unresolved overlap is held. Before any initial or later multi-batch promotion, repeat overlap review across the union of all batches being promoted.
3. Run separate Indonesian and Malaysian usage research roles. Each records senses, naturalness, register, region, alternatives, and specific evidence needs. A relation proposer prepares one neutral concept and one tentative relation.
4. Collect claim-level external evidence and use a separate evidence audit to verify that the cited material actually supports its claim. Store short observations, URLs/queries, locale, scope, access date, limits, source group, contradiction records, and an audit record naming the access method and inspected observation. An AI-provided `audited` assertion alone cannot count.
5. Run an independent verifier without generator rationale or preferred verdict, then a separate adversarial challenger that tests semantic alignment, common usage, register, region, alternate meanings, and relation claims. Re-run affected roles after a material cue, answer, relation, or evidence change according to their input dependencies. No role can approve its own output.
6. Run deterministic gate checks. An interrupted or malformed stage leaves its candidate `pending` until work resumes or an investigated candidate receives an explicit final decision. A candidate may be deliberately finalized as `hold` with a reason when evidence or disagreement remains unresolved; disproven claims and confirmed duplicates are `rejected`. Record uncompleted stages as such for early final decisions, without inventing role outputs. Only candidates with every required stage complete, supported, and agreed are `accepted`.
7. Generate open reports with generated = accepted + held + rejected + pending. Close a batch only after every candidate has a deliberate final outcome, pending is zero, and generated = accepted + held + rejected. Before assigning IDs, screen accepted candidates across all batches in the promotion set. Export only from closed batches with no unresolved overlap. Validate prospective TSV and ledger, then use a recovery journal and prior-version backups: replace the ledger first and the TSV last, roll back both on a handled failure, and complete or roll back an interrupted transaction before any later export or release. No partially researched batch changes learner data.
8. Run existing offline validation and build. Keep the GitHub release workflow on the accepted-source validation/build path, with no AI or live research calls and a deterministic preflight that refuses a tracked/incomplete export journal. Release only after package identity, recovery-journal clearance, and old-to-new Anki import checks pass.

The existing `000001` car row is an assigned legacy concept, not an exemption from the new quality gates. Include it in a retrospective curation record. If it passes, keep its ID; if it does not, withhold it from the active learner source after other accepted content exists and keep `000001` retired in the ledger.

### Quality boundaries

- Source citation URLs supplied by AI are leads, not evidence until inspected. Model self-confidence is stored only as context, never used as the acceptance gate.
- For `different-common-word`, evidence compares choices within each locale at aligned sense/register; a dictionary's bilingual gloss is insufficient.
- For `false-friend`, each relevant language meaning and the misleading contrast require independent evidence, and verifier and challenger must agree. Curation records separately identify misleading form, language, and actual meaning; the contrast text renders them without a long lesson.
- A research interruption leaves a candidate pending. A deliberate decision may hold it for unresolved evidence, never infer a translation. A closed batch may legitimately accept zero entries.
- The relation stays off the front and is not displayed on the back in the MVP; only false-friend contrast appears there.

### Compatibility assessment

The current source has six columns and the Anki note has five fields. The source becomes eight columns: `id,english,indonesian,malaysian,relation,image,tags,contrast`. Update parser, validation, tests, fixtures, contracts, and README together. The deck ID `1242123295`, model ID `1942161817`, GUID namespace `myid-anki:v1`, five note field names/order, and one-card template remain fixed. Escape the Malaysian answer and contrast separately and render the contrast as a small back-only block within the existing `Malaysian` field. This keeps ordinary Anki note updates possible without requiring a new field. Validate `000001 -> D6BBAuKXK` and perform Anki Desktop reimport from an old package; no duplicate or failed update is acceptable. If that acceptance fails, stop release and document a migration rather than silently changing model identity.

The ID ledger is append-only in its assignment records; `active` and `retired` are derived from whether an assigned ID is present in the current learner TSV. Export uses a recovery journal so two-file replacement cannot silently leave source and ledger divergent. The 24-concept initial target remains unmet if evidence-gated batches fall short; run another bounded batch and report why prior candidates were withheld.

## Complexity Tracking

No constitutional violation requires an exception. The eight-column TSV and separate curation ledger add limited complexity needed for explicit relation, false-friend teaching, and non-reused IDs.
