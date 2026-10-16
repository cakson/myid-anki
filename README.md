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

AI performs most vocabulary discovery, comparison, verification, and library growth. A generated
answer is only a candidate. The active production policy is **v3.1** in
`curation/config.json`: bounded contrastive generation → deterministic validation, duplicate and
no-contrast filtering → a separate lightweight linguistic verifier → provisional ACCEPT, HOLD, or
REJECT with confidence and review flags. Ordinary useful contrasts can pass without universal
external research. Concrete usage disputes use targeted evidence and the reusable cache; false
friends require stronger meaning, contrast, verifier, and adversarial support. A named synonym or
missing frequency proof alone does not veto an otherwise natural ordinary pair.

An ACCEPT is **not an automatic learner-source row**. Concrete production risk signals select cards for independent pre-promotion audit; selected cards require clearance. Guarded promotion through export checks closed decisions, final learner content, explicit eligibility, and batch safety brakes. Otherwise eligible clean cards can enter `data/vocabulary.tsv` without random-audit selection. Random or stratified audit remains ongoing QA monitoring and may discover corrections after release; corrections preserve the same concept ID and Anki GUID. This is an intentional optimistic-quality tradeoff. The current canonical learner source contains **270 concepts and 270 cards** after two Feature 004 batches.

Independent verification and adversarial review remain distinct for risky claims. Dictionary
inclusion can establish that a word exists or has a meaning; it does not establish that speakers
prefer it in everyday use. External evidence is targeted to concrete disputes and false friends,
rather than required for every ordinary accepted candidate.

Curation records under `curation/` preserve prompts, model routes, candidate IDs, stage results,
evidence and source roles, cache entries, confidence rationales, audit findings, corrections, and
promotion history. Permanent concept IDs and ID-derived Anki GUIDs survive content corrections.
The normal `validate`, `build`, CI, and release paths read accepted source data only; they make no
AI or live-research calls. A batch with zero promoted cards is a valid quality outcome.

For a small topic batch, the curation CLI begins with:

```sh
python -m indo_malay_anki.curation init --batch home-002 --topic home --limit 12
python -m indo_malay_anki.curation packet --batch home-002 --role generate
python -m indo_malay_anki.curation ingest --batch home-002 --role generate --response response.json
python -m indo_malay_anki.curation report --batch home-002
```

Use `packet`/`ingest` or their bounded bundle forms for later roles. `check`, `report`, `reopen`,
and `finalize-hold` keep decisions and interruptions inspectable. `curation export` guards
each closed batch under v3.1 with current eligibility, required audit clearance, and final verified
learner content. The [Feature 003 quickstart](specs/003-vocabulary-curation/quickstart.md)
and [convergence report](specs/003-vocabulary-curation/convergence-report.md) describe the
current audit and promotion boundary, historical experiments, and limitations.

The competing-form challenge, universal localized-standard or technical-borrowing gates, revised
Luna verifier, default Sol escalation, and universal cheap audit screen were tested but are
**disabled** as production mechanisms. Their saved experiments remain useful research artifacts.
Historical production-decision rates are not released-card throughput: audit, correction,
withholding, and promotion work count too. The approximately 50× expert-human throughput aim is
unproven; no empirical human benchmark exists. Two 100-candidate scaling batches demonstrated a
repeatable workflow, while model and independent-audit cost remain substantial operating constraints.

## Scaling the corpus

Feature 004 coordinates repeatable production runs over the frozen v3.1 curation system.
The maintainer reviews an editable category allocation, freezes it, then generates bounded
slices and screens against canonical and historical concepts. Commands save model responses
before ingest so interrupted work can resume. Risk-selected accepted cards require independent
audit clearance before guarded promotion; random QA monitors a reproducible sample and gates
run closure only. A safety brake pauses later promotion until its finding is investigated.

```sh
python -m indo_malay_anki.scaling create --run <run-id> --count 100 --proposal-cap 200
python -m indo_malay_anki.scaling allocation --run <run-id>
python -m indo_malay_anki.scaling approve --run <run-id> --reason "Reviewed category gaps"
python -m indo_malay_anki.scaling generate --run <run-id>
python -m indo_malay_anki.scaling curate --run <run-id>
python -m indo_malay_anki.scaling risk-audit --run <run-id>
python -m indo_malay_anki.scaling promote --run <run-id>
python -m indo_malay_anki.scaling build --run <run-id>
python -m indo_malay_anki.scaling qa-select --run <run-id>
python -m indo_malay_anki.scaling qa-run --run <run-id>
python -m indo_malay_anki.scaling close --run <run-id>
```

Inspect `status` and `report --json` after each step, and resolve any audit or QA findings
before closure. See the [Feature 004 run guide](specs/004-corpus-scaling/quickstart.md)
for corrections, brakes, and report interpretation. The
[convergence report](specs/004-corpus-scaling/convergence-report.md) records both completed batches,
the rejected efficiency experiments, and the 270-card baseline for future runs.

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
