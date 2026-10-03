# Contract: Workflow Events and Deck Distribution

## Inputs

| Workflow | Event | Revision used | Required result |
|---|---|---|---|
| `ci.yml` | Pull request | PR event checkout revision | Run all five project checks and upload inspectable deck on success |
| `ci.yml` | Push to `main` | Pushed revision | Same checks and artifact; no Release |
| `release.yml` | Push tag matching `v*.*.*` and exact `v[0-9]+.[0-9]+.[0-9]+` | Tagged revision | Same checks; create/update matching Release asset |
| `release.yml` | Broad glob match that fails exact version form | Event revision | No Release publication |

The five project commands, from repository root and in order, are:

```sh
python -m indo_malay_anki validate
pytest
ruff check .
ruff format --check .
python -m indo_malay_anki build
```

The environment uses Python 3.12 and the project's editable dev dependency set. Both workflows use these commands rather than reproducing validation or generation rules in YAML.

## Outputs

| Output | Filename / location | Consumer |
|---|---|---|
| Local build | `dist/myid-anki.apkg` | Contributor, artifact upload |
| Ordinary CI artifact | Clearly named Actions run artifact containing `myid-anki.apkg`; repository-configured retention | Maintainer inspection |
| Release transfer artifact | Named artifact from the same release workflow run containing `myid-anki.apkg` | Release publication job |
| GitHub Release asset | `indonesian-malaysian.apkg` on the pushed tag's Release | Learner |

The publication filename is a copy/rename only. The `.apkg` bytes and Anki identities remain the builder's output.

## Failure and permission contract

- A failed validation, test, lint, formatting check, or build fails the corresponding job and prevents publication.
- A missing package or failed attempted artifact upload fails the job. The release publication job cannot start after a failed release build job.
- Every successful CI run uploads its package; no successful result may omit the artifact upload step. No feature-specific retention period overrides repository settings.
- A failed publication leaves the workflow failed. A rerun can update the same tag's asset and must leave only one `indonesian-malaysian.apkg` asset.
- The release build records the checked-out commit SHA. Acceptance compares it with the tag target and compares the published asset bytes with the checked package from the same run.
- CI and release build jobs have read-only repository permission. Only the publication job receives release-write permission via `contents: write`.
- The built-in workflow token is sufficient; no new repository secret is part of the contract.

## Compatibility contract

- Concept IDs, note GUID derivation, deck ID, and note-model ID are independent of the tag and release filename.
- Importing a newer release may update matching notes according to the Anki client's supported behavior; package generation does not delete notes omitted from the new source.
