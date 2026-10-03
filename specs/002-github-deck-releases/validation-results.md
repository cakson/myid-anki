# Feature 002 Validation Results

**Reviewed**: 2026-10-03 on `002-github-deck-releases`

## Local quality gates

The local check used an ignored Python 3.12.14 virtual environment with the project's `.[dev]`
dependencies. The additional PyYAML package was used only for this review; it is not a project
dependency.

| Check | Result |
|---|---|
| `pytest` | Pass: 77 tests, including release-tag identity regression |
| `ruff check .` | Pass |
| `ruff format --check .` | Pass: 50 files already formatted |
| `python -m indo_malay_anki validate` | Pass: 1 reviewed concept, 0 media files |
| `python -m indo_malay_anki build` | Pass: `dist/myid-anki.apkg`, 1 note and 1 card |
| `unzip -t dist/myid-anki.apkg` | Pass: Anki collection and media archive entries intact |

Before the maintainer approved the README's `car` example, both validation and build correctly
failed on the header-only source with "At least one vocabulary concept is required." The approved
row is now checked in; no invented placeholder vocabulary was added. The local package SHA-256 was
`f76a585ac46b1b1d15aa91b8b4e64b2748d98617e95eb40e16bdabaed686a48a` for this build. The
package may have different bytes on another build because note modification times advance; Anki
identities remain stable.

## Workflow configuration review

Both workflow files parsed as YAML. A focused configuration check confirmed:

- CI triggers only on pull requests and pushes to `main`; it has only a `contents: read` job and no
  Release step.
- Release triggers only on pushed `v*.*.*` tags. Its first step rejects tags outside the exact
  numeric `vMAJOR.MINOR.PATCH` form before checkout, checks, or publication.
- Both build jobs use Python 3.12, `.[dev]`, and the five documented commands in order. Every
  `run` block also passed `bash -n` syntax checking.
- Both jobs require a nonempty `dist/myid-anki.apkg` and use artifact upload with
  `if-no-files-found: error`. CI names its artifact `indonesian-malaysian-ci-apkg` and leaves
  retention at the repository setting. An upload failure fails the job.
- The release build uses the triggering tag ref and records `git rev-parse HEAD`. Only the
  dependent publication job has `contents: write`; it downloads `indonesian-malaysian-release-apkg`
  from the same workflow run, copies its package to `indonesian-malaysian.apkg`, and uses the built-in
  `github.token` with GitHub CLI. The publication job sets `GH_REPO` because it has no checkout.
- The publication script drafts an existing Release before `--clobber` replacement, or creates a
  new draft. It publishes only after the checked asset upload succeeds. Failed gates cannot start
  publication. A failed upload leaves the Release draft for retry.
- The README, specification, contract, and workflows agree on `dist/myid-anki.apkg` locally,
  `indonesian-malaysian-ci-apkg` for CI inspection, and `indonesian-malaysian.apkg` for learners.
  Release tag values do not enter concept IDs, note GUID derivation, deck ID, or note-model ID.

The Python integration suite confirms tag environment values do not change those Anki identities.
Static review found no remaining deviation from the specified permissions, output names, or scope
exclusions.

## Hosted CI and Release evidence

### Main-branch acceptance (T007/T023)

PR #1 was merged at `2026-10-03T04:20:13Z` as main commit
`41304fd0968680ff427afc6021c8332e017e60b0`. Main-push
[CI run 37096199939](https://github.com/cakson/myid-anki/actions/runs/37096199939) passed at
`2026-10-03T04:20:34Z`. Its `indonesian-malaysian-ci-apkg` artifact downloaded successfully and
passed `unzip -t`; the package SHA-256 was
`61ea55186890710f8151802e407102b23b9542243ca3b8f3fb305b5bbb1a723d`. At that point the Releases
list contained only `v0.1.1`, confirming the ordinary main push created no Release.

The maintainer README steps produced [v0.2.0](https://github.com/cakson/myid-anki/releases/tag/v0.2.0)
from that exact main revision. Main CI completed at 04:20:34 UTC; the release asset was published
at 04:26:07 UTC, **5 minutes 33 seconds** later (within the 15-minute target). Release run
[37096494140](https://github.com/cakson/myid-anki/actions/runs/37096494140) checked out SHA
`41304fd0968680ff427afc6021c8332e017e60b0`, matching the tag target. GitHub Release ID was
`RE_kwDOU3a7lc4X-v21`. The sole `indonesian-malaysian.apkg` asset matched the same-run build
artifact byte-for-byte at SHA-256
`d36cfca0b772ff2d6d8d9aa5e321c1a7e263b3b7d72d49d8eff81daff0470022`; it also passed `unzip -t`.

The learner path was opened at 04:31:36 UTC, but Anki Desktop was already running with the default
profile, and the isolated graphical import could not be confirmed. No learner elapsed time or GUI
import success is claimed. The maintainer was asked to confirm the package import in Anki Desktop.

- Draft [PR #1](https://github.com/cakson/myid-anki/pull/1) passed CI at commit
  `bb640f4d60f9203731674116c45f807699183b89` in
  [run 37092963340](https://github.com/cakson/myid-anki/actions/runs/37092963340). The named
  `indonesian-malaysian-ci-apkg` artifact downloaded successfully and contained `myid-anki.apkg`.
  Its archive passed `unzip -t`. GitHub reported it unexpired with a 90-day repository retention
  setting and expiry `2027-01-01T03:22:07Z`. The corrected branch passed PR CI again in
  [run 37093321370](https://github.com/cakson/myid-anki/actions/runs/37093321370).
- The updated draft PR head `aa500f61deaeba3e1d16b9c5e8f8f9b1acd852b3` passed in
  [run 37095489300](https://github.com/cakson/myid-anki/actions/runs/37095489300). Its
  `indonesian-malaysian-ci-apkg` artifact downloaded and passed `unzip -t`; the contained package
  SHA-256 was `b6c648e5b179397664ee42a942b59c97ce389d97fffd76176eb517df62b0a09d`.
- Pushed `v0.1.0` at the first passing PR commit. Its
  [release run 37093126919](https://github.com/cakson/myid-anki/actions/runs/37093126919)
  passed build and artifact transfer but failed publication: GitHub CLI had no repository context
  in the checkout-free publication job. GitHub reported no Release for this tag. The workflow was
  fixed by setting `GH_REPO` to the built-in `github.repository` value. The existing tag was not
  moved.
- Pushed fresh `v0.1.1` at `e1b6be70829eb86c9683fa53694446dee5fb29d6`. The
  [release run 37093389454](https://github.com/cakson/myid-anki/actions/runs/37093389454)
  passed. Its logged checkout SHA and GitHub run head SHA both equal the tag target, while `main`
  still points to an older revision. The published
  [v0.1.1 Release](https://github.com/cakson/myid-anki/releases/tag/v0.1.1) had exactly one
  `indonesian-malaysian.apkg` asset. The downloaded asset and package from that same run were
  byte-for-byte equal with SHA-256
  `963a606a1db98f63803fd895af547bbbbacd8e38673b0101c95312ed5763fee6`.
- Reran the `v0.1.1` workflow successfully. It drafted the existing Release, replaced the asset,
  and published it again with exactly one deck asset. The rerun's downloaded package and current
  Release asset were byte-for-byte equal with SHA-256
  `0b5732c793e7e2fb02cd228a0b1e21c46e2e60723d4bba69b763d0d83e04db95`. GitHub Release ID:
  `RE_kwDOU3a7lc4X-q-p`; successful release run ID: `37093389454`.

### Isolated hosted failure checks

Each failure was introduced on a temporary draft PR branch, one at a time. The probe PR was based
on the passing feature revision, and each run stopped at the intended gate:

| Deliberate failure | Hosted result |
|---|---|
| Empty required Indonesian field in vocabulary TSV | [Run 37094679719](https://github.com/cakson/myid-anki/actions/runs/37094679719) failed at `Validate vocabulary and media`. |
| Added test that asserts false | [Run 37094734910](https://github.com/cakson/myid-anki/actions/runs/37094734910) failed at `Run tests`; the other 77 tests passed. |
| Unused import | [Run 37094779956](https://github.com/cakson/myid-anki/actions/runs/37094779956) failed at `Check Ruff lint`. |
| Valid test with nonconforming quote formatting | [Run 37094810916](https://github.com/cakson/myid-anki/actions/runs/37094810916) passed tests and lint, then failed at `Check Ruff formatting`. |
| Directory blocks the expected package output path | [Run 37094871722](https://github.com/cakson/myid-anki/actions/runs/37094871722) passed prior gates and failed at `Build deck`. |
| Artifact upload path points to a nonexistent package | [Run 37094907989](https://github.com/cakson/myid-anki/actions/runs/37094907989) passed build and failed upload with `if-no-files-found: error`. |

No artifact-service outage was observed; the last case deliberately tested a missing file and did
not disrupt GitHub's artifact service. The temporary PR is only acceptance evidence and is not a
product change.

### Release trigger and publication failure checks

- The glob-matching malformed tag `v0.2.0-rc.1` pointed at
  `2c2559291f3b95873ebf9751c79cb79de0d6b861`. [Run 37094945489](https://github.com/cakson/myid-anki/actions/runs/37094945489)
  failed the numeric tag guard before checkout or publication. No Release exists for that tag.
- Numeric tag `v0.2.0` pointed at `b6e10bea2aa1d79690bd972539d09dfa3bf91bb3`, a temporary revision
  with a deliberately failing pytest test. [Run 37094973413](https://github.com/cakson/myid-anki/actions/runs/37094973413)
  passed validation and failed at tests; the dependent publication job was skipped and no Release
  exists for the tag. The passing `v0.1.1` Release and its asset were unchanged.
- For the draft failure path, temporary tag `v0.2.1` pointed at
  `9aa4be685212f2a12f314ddf68bed0d1ec03d8b7`. Its build job passed every gate; the test-only
  revision made the publisher request a nonexistent asset. [Run 37095045026](https://github.com/cakson/myid-anki/actions/runs/37095045026)
  failed at asset upload after creating the Release. GitHub shows `v0.2.1` as a draft with zero
  assets, confirming it was not published. This test altered only the temporary tagged workflow;
  the feature workflow remains the passing version used for `v0.1.1`.

## Anki import and update evidence

Anki Desktop 26.9.3 is installed locally. Using the matching Anki 26.9.3 import backend and an
isolated temporary collection, the downloaded `v0.1.1` Release asset imported as one note and one
card with GUID `D6BBAuKXK`. Reimporting that asset left one note and one card. A second, local test
package changed only the English cue from `car` to `automobile` while keeping permanent concept ID
`000001`; importing it into the same collection updated the existing note in place. Its database
note ID, GUID, note-model ID, and collection deck ID remained unchanged, and the collection still
had one note and one card. The second package was a temporary test fixture, not a published Release;
no repository vocabulary was changed for this test. A graphical desktop or mobile import was not
performed.

### Tagged-revision identity and update import (T026)

After approval to use `automobile`, two local-only immutable test tags were created in a temporary
clone; neither was pushed, so no learner-facing Release was published:

| Tag | Checkout/target SHA | Package SHA-256 |
|---|---|---|
| `v0.2.2` | `2c2559291f3b95873ebf9751c79cb79de0d6b861` | `973f7ab7fa7a03811fe06502c35c4027fcbf27390eaaf0ea10ba0ec290278927` |
| `v0.2.3` | `da81016d4d7fba62ac05dec83fc9e9c6e08026e5` | `e977be697bc478726970aeb62f8003b2df432b3403be94624de0a10f16207b86` |

Both packages were built with the documented `python -m indo_malay_anki validate` and `build`
commands from their tagged checkout. The second changed only concept `000001`'s English cue from
`car` to `automobile`. Package inspection found identical deck ID `1242123295`, note-model ID
`1942161817`, and note GUID `D6BBAuKXK` in both archives. Package bytes differ because the English
field and note modification metadata changed.

Anki Desktop 26.9.3's matching import backend imported both packages successively into a fresh
isolated collection. The second import updated the existing note in place: note ID remained
`1791000266000`, GUID remained `D6BBAuKXK`, model ID remained `1942161817`, and collection deck ID
remained `1791000283011`. The final collection had one note and one card, so the update added zero
duplicate notes. This used the same Anki backend as Desktop, but not its graphical UI or a mobile
client.

## Remaining acceptance tasks

Hosted main-branch and end-to-end walkthrough items remain open:

| Task | Evidence needed |
|---|---|
| T007 | Complete: main push CI passed, its artifact downloaded and validated, and no Release was created by the push. All six isolated failure gates are recorded above. No artifact-service outage was observed. |
| T019 | Walk through contributor and learner README steps; record wording corrections and the 5-minute Releases-to-import timing. Maintainer timing passed at 5 minutes 33 seconds. |
| T023 | Complete: main CI passed, the artifact downloaded and validated, and the main push created no Release. |
| T027 | Complete the contributor, maintainer, and learner README walkthrough, including learner timing and graphical import confirmation. |
| T028 | Confirm learner import and update behavior in Anki Desktop or an official mobile client; main CI, artifact, no-main-release, and maintainer timing are now recorded above. |

Follow [quickstart.md](quickstart.md) for the remaining hosted checks and graphical import. Do not
mark incomplete tasks complete from static inspection alone.
