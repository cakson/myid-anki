# MYID Anki

MYID Anki builds a standard, offline-ready Anki package for learning reviewed Indonesian and
Malaysian Malay—Bahasa Melayu as used in Malaysia—from repository-managed source data. It targets
this variety, not all Malay varieties. The repository is authoritative: edit the TSV, templates,
configuration, or media, then rebuild. Never maintain vocabulary by editing a generated `.apkg`
file.

## Why this deck exists

Indonesian and Malaysian Malay are closely related, with highly similar grammar and sentence
structure and a large amount of shared vocabulary. That closeness can make it relatively quick for
a speaker of one language to recognize or partly understand the other. Everyday vocabulary is
still a major practical area of cross-learning that this deck is designed to exercise—not a claim
that vocabulary is universally the hardest part of learning either language.

The vocabulary relationship is not simply “same” versus “different.” A concept may use the same or
almost the same word in both languages; speakers may recognize a word but ordinarily prefer
different everyday words; a shared-looking word may differ in frequency, register, or normal usage;
or similar-looking words may carry different meanings. More rarely, a familiar-looking word can
mislead a learner toward the wrong meaning. Repeatedly recalling and comparing reviewed examples
helps make these patterns more familiar.

## A neutral cue, shared answers

The front deliberately shows neither Indonesian nor Malaysian Malay. A word from one language
could give away the other because many words are cognates or otherwise recognizable across the two.
Instead, the initial deck uses an English cue, or an image when one is available. This asks for
genuine recall rather than inference from the related language.

For example, the front may show:

```text
CAR

Answer in Bahasa Indonesia
or Bahasa Melayu
```

After the learner attempts an answer, the back reveals both forms together:

```text
CAR

Bahasa Indonesia
mobil

Bahasa Melayu
kereta
```

The comparison is part of the learning experience: the learner can notice whether the words are
the same, similar, commonly different, or potentially misleading. This is one shared deck for
learners in either direction. An Indonesian speaker learning Malaysian Malay (Bahasa Melayu as used
in Malaysia) can use CAR to recall “kereta”; a speaker of that variety learning Indonesian can use
the same cue to recall “mobil.”
The card does not encode a direction or create separate schedules. Rate the concept based on your
recall of the language you are practicing. If you want to maintain both vocabularies actively, try
to recall both answers before revealing the card.

## How to use this deck

1. Look only at the neutral English or image cue.
2. Recall the word in the language you are learning.
3. Optionally, try to recall both languages.
4. Reveal the card.
5. Compare the Indonesian and Malaysian Malay (Bahasa Melayu as used in Malaysia) forms.
6. Notice when the commonly used words differ, or when a familiar-looking word might mislead you.

## Set up

Install Conda, then create and activate the project environment:

```sh
conda env create -f environment.yml
conda activate myid-anki
```

The project requires Python 3.12 or newer. The environment installs the local package, `genanki`,
`pytest`, and `ruff`. No network access is needed for validation, building, importing, or studying
after dependencies and media are present locally.

## Vocabulary source

The sole vocabulary source is `data/vocabulary.tsv`, encoded as UTF-8. It has exactly these six
tab-separated columns in this order:

```tsv
id	english	indonesian	malaysian	image	tags
```

Each data row is one semantic concept. `id`, `english`, `indonesian`, and `malaysian` are required;
`image` and `tags` may be empty. Tags are whitespace-separated Anki tags. Vocabulary must be
reviewed and entered by maintainers; the build never translates, generates, normalizes, or repairs
language content. The checked-in `car` example was approved as the first reviewed concept.

To add a concept, append one TSV row with a new six-digit ASCII ID and its reviewed values. Keep IDs
as text, including leading zeroes (for example, `000001`). An ID is permanent: do not change or reuse it when correcting a
translation, changing English, adding/removing an image, or editing tags. Reintroducing the same
concept later must use its original ID; it will recover the same Anki note identity. A different
semantic concept needs a different ID.

## Optional images

Place image files under the repository's `media/` directory and put a safe relative path in the
`image` column, using `/` separators. For example, a file at `media/places/house photo.jpg` is
referenced as `places/house photo.jpg`. Do not put image binaries or remote URLs in the TSV. Every
referenced file must exist and resolve inside `media/`; absolute paths, traversal, directory
references, symlink escapes, and remote URLs are rejected. Distinct files whose packaged basenames
collide under Unicode case folding are also rejected; the exact same file may be referenced by
multiple concepts. Referenced images are bundled in the package. Image download, search, scraping,
generation, and optimization are not part of V1.

## Validate and build

Run commands from the repository root:

```sh
python -m indo_malay_anki validate
python -m indo_malay_anki build
```

`build` always completes the full source and media validation pipeline before package generation.
Invalid data returns a nonzero exit status and leaves any existing package unchanged. A successful
build writes the generated artifact to:

```text
dist/myid-anki.apkg
```

That package is a build artifact, not source data. Rebuild it after changing repository inputs; do
not open it to make maintenance edits.

The note GUID depends only on the permanent concept ID. Rebuilds preserve the deck, note-model,
field, and template identities. Modification timestamps advance across successive local builds,
including builds in the same wall-clock second, so Anki's normal newer-wins packaged-deck update
behavior can recognize a newer package. Timestamps do not affect note identity. Removing a concept
omits it from new packages but does not request deletion from an existing collection. Reintroducing
the same ID preserves the note GUID and may update an existing note rather than duplicate it.

## Card behavior

Each concept creates exactly one note and one card; Indonesian and Malaysian are not separate review
directions or schedules. On the front, a valid bundled image replaces the English cue. Without an
image, English is the prominent neutral cue. The front asks for an answer in Bahasa Indonesia or
Bahasa Melayu and does not reveal either answer. The back reveals both labeled answers together;
English is included as cue context. Learners rate the concept as a whole.

The standard HTML/CSS templates do not require JavaScript or internet access for core behavior.
Long English, Indonesian, and Malaysian text wraps, and images are bounded so ordinary content does
not require horizontal scrolling at viewport widths of 320 CSS pixels or greater.

## Development checks

```sh
pytest
ruff check .
ruff format --check .
```

The automated tests inspect source parsing and validation, stable Anki identity, package contents,
media, templates, offline behavior, and rebuild compatibility. Initial package acceptance should
also be recorded after importing and studying text-cue and image-cue cards offline in Anki Desktop
and one official mobile Anki client. See
[`specs/001-build-anki-deck/quickstart.md`](specs/001-build-anki-deck/quickstart.md) for the
acceptance procedure.

## GitHub checks for contributors

Pull requests and pushes to `main` automatically install the project's Python 3.12 development
dependencies, validate vocabulary and media, run `pytest`, check Ruff lint and formatting, and build
the deck with the same commands used above. A failure in any step, a missing package, or a failed
artifact upload fails CI. A header-only vocabulary file fails validation; do not add placeholder
vocabulary to make CI pass. Normal pushes to `main` do not create a GitHub Release.

After a successful run, open the repository's **Actions** tab, select the **CI** workflow and the
run, then download `indonesian-malaysian-ci-apkg` from its **Artifacts** section. Extract the
downloaded archive to inspect `myid-anki.apkg`. This temporary artifact is for maintainers and
expires according to the repository's configured Actions artifact retention period. Learners should
use GitHub Releases instead.

## Create a release for maintainers

1. Ensure `main` contains reviewed vocabulary and its CI run is passing. Check that your local
   checkout is clean and at the revision you intend to release.
2. Create a new numeric `vMAJOR.MINOR.PATCH` tag, for example `git tag v0.1.0`, then push it with
   `git push origin v0.1.0`. Do not move an existing release tag.
3. Open **Actions → Release deck** and check that validation, tests, Ruff checks, and the build pass
   for the tagged revision. The workflow records its checked-out commit SHA.
4. Open the matching entry under **Releases**. The workflow creates or updates it only after the
   checked package has been uploaded as `indonesian-malaysian.apkg`. A failed publication remains
   a draft for a later rerun.

The release workflow uses the package built in that tag's run, not an artifact from an earlier CI
run. It uses GitHub's built-in workflow token; no repository release secret is needed. Only the
publication job can write Releases.

## Download and update the deck for learners

Open the [latest GitHub Release](https://github.com/cakson/myid-anki/releases/latest) and download
`indonesian-malaysian.apkg` from **Assets**. On desktop, open the downloaded file with Anki or use
**File → Import**. On a phone, download the file and open/share it with your Anki client. The
filename is ready to import as downloaded.

To update an existing deck, import the newer release into the **same Anki collection**. Permanent
concept IDs keep the note GUID, deck ID, and note-model ID stable across releases, so matching
notes can be updated rather than duplicated where the client's import behavior supports updates.
Follow any import options shown by your client; prompts may differ between desktop and mobile.
Notes omitted from a newer package are not automatically deleted from your collection. GitHub
release version numbers do not change Anki note identity or synchronize anyone's collection.
