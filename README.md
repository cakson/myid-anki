# MYID Anki

MYID Anki builds a standard, offline-ready Anki package for learning curated Indonesian and
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

The vocabulary relationship is not simply “same” versus “different.” Some concepts use the same
ordinary word in both languages; this contrast-only deck excludes those. Other concepts use
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
SPOON

Answer in Bahasa Indonesia
or Bahasa Melayu
```

After the learner attempts an answer, the back reveals both forms together:

```text
SPOON

Bahasa Indonesia
sendok

Bahasa Melayu
sudu
```

The comparison is part of the learning experience: the learner can notice whether the words are
similar, commonly different, or potentially misleading. This is one shared deck for
learners in either direction. An Indonesian speaker learning Malaysian Malay (Bahasa Melayu as used
in Malaysia) can use SPOON to recall “sudu”; a speaker of that variety learning Indonesian can use
the same cue to recall “sendok.”
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

The sole learner vocabulary source is `data/vocabulary.tsv`, encoded as UTF-8. It has exactly these eight
tab-separated columns in this order:

```tsv
id	english	indonesian	malaysian	relation	image	tags	contrast
```

Each data row is one semantic concept. `id`, `english`, `indonesian`, and `malaysian` are required;
`relation` in learner source is one of `similar`, `different-common-word`, or `false-friend`.
The `same` classification is retained in curation records to explain rejected candidates.
`image` and
`tags` may be empty; tags are whitespace-separated Anki tags. `contrast` is required only for a
false friend and appears only on the back. It briefly names the misleading lookalike and its
actual meaning. The build copies accepted source content; it never translates, generates,
researches, or repairs language content.

Accepted vocabulary comes from the AI-first curation workflow below. Keep IDs
as text, including leading zeroes (for example, `000001`). An ID is permanent: do not change or reuse it when correcting a
translation, changing English, adding/removing an image, or editing tags. Reintroducing the same
concept later must use its original ID; it will recover the same Anki note identity. A different
semantic concept needs a different ID.
The original `000001` car proposal is retired after the independent reviews found its everyday
preference claim insufficiently supported. Former shared-vocabulary entries `000002` (kitchen),
`000006` (computer), and `000007` (corn) are also retired under the contrast-only policy. Their
assignments remain in the ledger and are never reused.

## AI-first vocabulary curation

AI performs most discovery, usage analysis, relation proposal, evidence gathering, verification,
and later library growth. A single AI answer is a candidate, never an accepted row. The project
uses separate role prompts for candidate generation, semantic overlap, Indonesian and Malaysian
usage, relation proposal, evidence audit, independent verification, and adversarial challenge.
AI can make plausible language mistakes; the quality claim rests on inspectable evidence, role
separation, conservative decisions, and corrections over time.

Work in topic batches of at most 12 candidates. For example:

```sh
python -m indo_malay_anki.curation init --batch home-002 --topic home --limit 12
python -m indo_malay_anki.curation packet --batch home-002 --role generate
python -m indo_malay_anki.curation ingest --batch home-002 --role generate --response response.json
python -m indo_malay_anki.curation report --batch home-002
```

Use `packet` and `ingest` for each later role and candidate; `bundle` and `ingest-bundle` group
one role across a bounded batch while retaining separate candidate stage records. The prompts,
provider configuration, ID ledger, batch manifests, raw responses, inspected source observations,
decisions, and reports live under `curation/`. The [Feature 003 quickstart](specs/003-vocabulary-curation/quickstart.md)
shows the full sequence and failure checks. Prompt packets and stage inputs carry digests so an
affected verification stage must be rerun after a material edit.
New batches pin a prompt-set version and a compact snapshot of already investigated concepts.
The generator sees that snapshot to avoid proposing the same concept again; normalization still
checks semantic overlap independently. Historical prompt text remains under
`curation/prompts/versions/` so later prompt improvements do not alter an earlier batch's stage
digests.

The `reserve` cost policy in `curation/config.json` routes every curation role to
`gpt-5.6-luna`. Verification and adversarial review remain separate calls with separate
prompts and medium reasoning effort. Check a stage's route with
`python -m indo_malay_anki.curation route --role ROLE` and pass that model and reasoning effort
to the AI tool. This policy is a repository convention, not a Codex CLI service tier. Stage
records keep the actual model identifier; pass `--actual-model` when ingesting a response because
an AI response can mislabel itself. Learner builds do not read this setting. The evidence packet
precheck rejects duplicate claim IDs, unresolved overlap, and cue mismatch. Verification and
adversarial packets are withheld when the evidence or verifier gate already fails.
For `1.2.0`, `1.3.0`, `1.4.0`, and `1.5.0` batches, inspect promising external sources before locale analysis and save
the observations using `curation/source-inspection-template.json`. Locale packets are withheld
until both languages have inspected leads from at least two underlying source groups. Luna
uses those leads at low reasoning effort; the later evidence audit independently checks
whether they support each claim. Older batches keep their pinned prompt behavior.

Important claims need at least two independent, claim-relevant external signals, inspected during
curation. A dictionary can show a word exists or has a meaning; it does not by itself show that it
is the normal everyday choice in a country. For `different-common-word`, compare natural use and
register on both sides for the same neutral English sense. False friends need stronger evidence
for both meanings and the misleading contrast, plus independent verification and adversarial
agreement. Evidence from mirrors of one publisher does not count twice. Disagreements, weak
sources, ambiguous cues, and unresolved semantic overlap go on hold or are rejected. Model
self-confidence never overrides a failed gate.

Use `check` and `report` to inspect accepted, held, rejected, and pending counts, relation
distribution, duplicate findings, and evidence or verification failures. A batch closes only when
no candidate is pending. `finalize-hold` records why an investigation stopped; `reopen` can resume
it later without deleting its prior records. Only accepted candidates from closed batches may be
promoted with `curation export --batch BATCH`; a closed batch with zero accepted candidates is a
valid quality outcome. The guarded export screens overlaps again, assigns
permanent IDs, validates the prospective TSV, and recovers interrupted writes. Held, rejected,
and partial batches never modify the learner TSV. The normal `validate`, `build`, CI, and release
paths use the accepted TSV only and make no AI or live-research calls.

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
2. Create a new, unused numeric `vMAJOR.MINOR.PATCH` tag, for example `git tag v0.2.0`, then push it
   with `git push origin v0.2.0`. Do not move an existing release tag.
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
