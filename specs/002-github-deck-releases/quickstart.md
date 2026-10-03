# Quickstart: Validate GitHub Deck CI and Release Distribution

This is an acceptance guide for the implementation. It does not create vocabulary or publish a release by itself.

## Prerequisites

- Have a GitHub repository with Actions enabled and settings that allow the built-in workflow token to create Releases.
- Commit at least one maintainer-reviewed vocabulary concept before expecting a green validation/build. The current header-only source is rejected by design.
- Use a test tag that has not been published, and coordinate its version with maintainers. Do not move an existing tag.
- Have Anki Desktop or an official mobile Anki client available for import acceptance.

## Local gate

From the repository root in the documented Python 3.12 environment:

```sh
python -m indo_malay_anki validate
pytest
ruff check .
ruff format --check .
python -m indo_malay_anki build
```

Expect all commands to succeed and `dist/myid-anki.apkg` to exist. If the source still has only a header, validation must fail; record that as the known prerequisite rather than changing the validator.

## Static workflow review

Inspect `.github/workflows/ci.yml` and `.github/workflows/release.yml` using a YAML parser or focused configuration checks:

1. CI triggers are pull requests and pushes to `main`; release publication triggers only version-style tag pushes.
2. Both workflows use Python 3.12, install the existing dev dependencies, and run the five commands shown above.
3. CI and release build jobs are read-only. Only the release publication job can write release content.
4. Every successful CI run uploads the generated local package, uses repository-configured artifact retention, and fails for a missing file or attempted upload failure.
5. The release job uses the tagged revision and publishes `indonesian-malaysian.apkg` from the package built in the same workflow run.
6. Existing identity tests still pass; no release tag enters the Python identity code.

Avoid a local emulator that claims to reproduce GitHub's permissions, artifacts, and Releases.

## Hosted CI acceptance

1. Open a pull request with valid reviewed inputs. Confirm the CI run passes and offers a clearly named artifact containing the generated `.apkg`.
2. Download the artifact and confirm its package opens in Anki. Record the repository-configured artifact retention setting. Check that a main push produces a CI artifact but no new Release.
3. In isolated test branches or PRs, introduce one controlled failure for each gate: source/media validation, tests, Ruff lint, Ruff formatting, and deck generation. Record the failing run and gate for each, then restore valid inputs. Separately confirm a missing package makes artifact upload fail. If the artifact service itself fails, record that the run fails; do not intentionally disrupt the service.

## Hosted release acceptance

1. Confirm the intended main revision is reviewed and passing CI.
2. Create and push an unused semantic version-style tag such as `v0.1.0` on that revision.
3. Record the tag's target commit SHA and the release build's checked-out commit SHA; they must match. Confirm the release workflow passes its gates and creates the matching GitHub Release.
4. Confirm the Release has exactly one deck asset named `indonesian-malaysian.apkg`; download it and import it in Anki Desktop or an official mobile client without renaming.
5. Download the checked package artifact from that same release run and compare its SHA-256 digest with the downloaded Release asset; they must match byte-for-byte after the filename change. Record both digests and the run ID. Confirm stable concept, note, deck, and model identities with existing integration tests or package inspection.
6. Push a separate test tag at a revision with one deliberately failing quality gate and confirm it creates no new or replacement deck asset. Restore valid inputs for later tests.
7. Rerun the workflow for the same valid tag if safe in the test repository and confirm it updates the single stable-named asset without duplicates.

## Documentation walkthrough timing

Record the elapsed time from checks finishing until a maintainer completes the documented release steps; the target is under 15 minutes. Separately record the time for a learner to locate the latest Release, download its asset, and start import on desktop or mobile; the target is under 5 minutes. Note any undocumented steps encountered.

The [workflow contract](contracts/workflow-distribution.md) defines event and output expectations; [data-model.md](data-model.md) defines the identity and lifecycle relationships.
