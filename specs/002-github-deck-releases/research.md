# Research: GitHub Deck CI and Releases

## Existing project commands and Python environment

**Decision**: Use Python 3.12 and install the existing editable dev dependency set with `python -m pip install -e '.[dev]'`. Invoke `python -m indo_malay_anki validate`, `pytest`, `ruff check .`, `ruff format --check .`, and `python -m indo_malay_anki build`.

**Rationale**: These are the documented local interfaces. `environment.yml` pins Python 3.12 and installs the same editable dev extra; `pyproject.toml` defines project/runtime/test/lint dependencies. The builder already validates before writing `dist/myid-anki.apkg`.

**Alternatives considered**: Conda in Actions adds setup time without changing the supported interpreter or dependency set. Rewriting validation/build logic in YAML risks divergence. A new wrapper script would add an unnecessary second entry point.

## Event filters and exact tagged revision

**Decision**: CI handles pull requests and pushes to `main`. A separate workflow handles pushed `v*.*.*` tags, then checks the tag name against the strict `^v[0-9]+\.[0-9]+\.[0-9]+$` form before publishing. Check out the event's ref in the release workflow.

**Rationale**: GitHub's tag filter uses glob patterns, so `v*.*.*` alone is broader than the required version shape. A tag push event identifies its tag ref and associated commit; checkout of that event ref ties the build to the tagged revision. [Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

**Alternatives considered**: Main-push publication violates the explicit release trigger. A manually selected branch or a package downloaded from an older run can publish the wrong revision. A tag-name guard using only the glob would permit malformed version tags.

## Permissions and release publication

**Decision**: Give CI and the release build job `contents: read`. Give only the dependent release publication job `contents: write`. Use GitHub CLI with the built-in `GITHUB_TOKEN`: create a new release with its asset through the CLI's draft-upload-publish sequence; for an existing release, move it to draft before replacing the asset, then publish only after the replacement is present.

**Rationale**: GitHub supports job-scoped permissions; `contents: write` covers release creation while unspecified permissions can remain disabled. GitHub CLI documents that creating a release with an asset first creates a draft, uploads the asset, and only then publishes it. Its upload command warns that `--clobber` deletes the old asset before uploading the new one, so an existing release is drafted before replacement to avoid leaving an assetless published release after failure. [Workflow permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [release creation](https://cli.github.com/manual/gh_release_create), [release editing](https://cli.github.com/manual/gh_release_edit), [asset replacement](https://cli.github.com/manual/gh_release_upload).

**Alternatives considered**: Workflow-wide write permission gives build steps excess access. A personal access token introduces a secret without need. A one-step release action or `gh release upload --clobber` on a published release can expose an empty release if replacement fails. A custom API script adds code for existing release functionality.

## Artifact transport and names

**Decision**: Every successful CI run uploads `dist/myid-anki.apkg` with a clear run-artifact name and the repository-configured Actions retention period. The release build job uploads the same local package to its own run; the publication job downloads that named artifact from the current run and publishes a renamed copy as `indonesian-malaysian.apkg`. Missing files and attempted upload failures fail their runs.

**Rationale**: Same-run transfer separates read-only checks from write-scoped publication while preserving the exact checked package. The upload action provides `if-no-files-found: error`; a failed upload step fails the job. The user's clarification requires an attempted artifact upload failure to fail CI. Using repository-configured retention avoids an unnecessary feature-specific policy for an inspection artifact; Releases remain the learner distribution. [Upload artifact options](https://github.com/actions/upload-artifact/blob/main/README.md).

**Alternatives considered**: Publishing the local basename would conflict with the latest learner-facing filename request. Rebuilding in the write-scoped job could produce a different package and repeats quality work. Pulling an artifact from an unrelated CI run weakens revision traceability.

## Python setup and verification

**Decision**: Use a versioned `setup-python` action with Python 3.12 and pip caching keyed from `pyproject.toml` (and `environment.yml` if convenient). Verify YAML parsing and key trigger, command, permission, and filename fields with focused checks, then perform hosted manual acceptance.

**Rationale**: Pip caching is supported by the setup action and does not alter the dependency contract. Static checks catch omissions; only a hosted run proves event matching, token permissions, upload, release creation, and learner download. [Setup Python caching](https://github.com/actions/setup-python/blob/main/README.md).

**Alternatives considered**: A local GitHub Actions emulator would be brittle for this small repository and would not fully reproduce hosted permissions or Releases.

## Stable Anki identity

**Decision**: Keep release tags and asset renaming outside the Python model and builder. Reuse existing stable-identity tests and compare package manifests across releases if implementation changes touch packaging.

**Rationale**: Existing code derives the note GUID from the permanent concept ID and uses stable deck/model constants. The release tag has no path into the generator. A change to GUID, deck ID, model ID, field schema, or one-note/one-card behavior would require compatibility review under the constitution.

**Alternatives considered**: Embedding the Git tag as a note or model identity would duplicate cards or disrupt updates; it is explicitly excluded.
