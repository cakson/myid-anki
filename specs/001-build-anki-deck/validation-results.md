# MYID Anki Validation Results

**Updated**: 2026-10-02

## Automated Performance Acceptance

- Fixture: generated 1,000-concept TSV; no generated vocabulary is committed as source data.
- Operation: local `validate` followed by `build` to a temporary repository's canonical output.
- Result: passed the 60-second limit; measured validation-plus-build time was 0.025 seconds in the
  recorded test run (the test case elapsed 0.028 seconds including harness overhead).
- Host: macOS 26.4.1, arm64.
- Runtime: Conda `playground` environment, Python 3.14.4, `genanki` 0.13.1.
- Test command: `conda run -n playground python -m pytest tests/integration/test_performance.py -q`.

This is a local measurement, not a promise that all development machines have identical performance.

## Anki Desktop and Mobile Acceptance

**Status: Passed (user-reported manual acceptance, 2026-10-02).** The user reports that:

- The `.apkg` imported successfully into Anki Desktop and an official mobile Anki client.
- The deck was studyable offline in both clients.
- There was one card per vocabulary concept.
- The front showed the neutral English cue.
- The back revealed both Indonesian and Malaysian Malay answers.
- Mobile study required no horizontal scrolling.

Clients and environment: Anki Desktop 26.09.3 (29bb700b) on macOS 26.4.1 (25E253), and official
AnkiMobile 25.09 on iOS 26.5.2, iPhone 17 Pro Max. The mobile test was in portrait at a 440 CSS-pixel
logical viewport width (approximately 440 × 956 CSS pixels at default scaling). Both clients used
default packaged-deck import settings; no custom options were changed. The imported package had
2 notes and 2 cards. The user confirmed image-cue and bundled-media behavior, offline study, and
mobile readability without horizontal scrolling. Long text and oversized-image behavior passed.

## Anki Desktop Re-import, Removal, and Reintroduction Acceptance

**Status: Passed (user-reported manual acceptance, 2026-10-02).** The user reports that in Anki
Desktop:

- The initial generated deck imported successfully.
- An immediate rebuild after changing a mutable concept field updated the existing note without
  creating a duplicate.
- Importing a deck with a source-omitted concept did not delete that note from the collection.
- Reintroducing the same permanent concept ID updated the extant logical note without creating a
  duplicate.
- Note/card counts remained stable where expected.

The client was Anki Desktop 26.09.3 (29bb700b) on macOS 26.4.1 (25E253), using default packaged-
deck import settings with no custom options changed. Baseline package and collection: 2 notes / 2
cards. After a mutable-field edit with the same permanent ID and immediate rebuild/re-import, the
collection remained at 2 notes / 2 cards; the existing note updated and no duplicate note or card
was created. One card had been reviewed before this update. After re-import it remained the same
note/card with its review/scheduling state preserved, not reset to new/unreviewed; individual
scheduler-field values were not separately recorded. After removing one concept from the source
and importing the reduced package, the collection remained at 2 notes / 2 cards and the omitted
note remained in Anki. After reintroducing the same permanent ID and rebuilding/re-importing, the
collection remained at 2 notes / 2 cards; the same logical note updated without a duplicate.

## Contributor Walkthrough

**Status: Passed (user-reported manual acceptance, 2026-10-02).** An unfamiliar contributor was
able to understand the project's purpose and Indonesian ↔ Malaysian Malay learning model from the
README; set up the project; find and edit the vocabulary TSV; add a concept with a permanent ID;
validate the data; build and locate the `.apkg`; understand optional media; and follow the edit →
validate → build workflow.

The README also explains the deck's contrastive-learning purpose, neutral English/image cues,
bidirectional use, and why both language answers are shown. The user later confirmed the text-only
and image-backed contributor walkthrough passed within the target of 15 minutes or less of active
contributor time. Dependency/environment download time was excluded. The contributor relied only
on the repository README and normal command-line/tool feedback; no additional verbal or written
assistance from an existing contributor was required. Exact elapsed time and the contributor's
operating system were not recorded.

## Convergence Manual Acceptance

**Status: Passed (user-reported manual acceptance, 2026-10-02).** The user confirms the remaining
first-import, Anki Desktop re-import/removal/reintroduction, and unfamiliar-contributor acceptance
checks passed. This includes image-cue study and bundled media in Anki Desktop and an official
mobile client; offline use, visible “Bahasa Melayu” labels and answers, and mobile readability
without horizontal scrolling; update/removal/reintroduction behavior including the independently
deleted-note case; and a contributor completing text-only and image-backed edits, validation,
build, and output discovery. Detailed reported metrics and outcomes follow; no additional values
are inferred.

Client details: Anki Desktop 26.09.3 (29bb700b) on macOS 26.4.1 (25E253), and official AnkiMobile
25.09 on iOS 26.5.2 / iPhone 17 Pro Max. Mobile acceptance was in portrait at 440 CSS pixels
(approximately 440 × 956 CSS pixels at default scaling). Default packaged-deck import settings
were used without custom options. Package/import and all reported re-import stages had 2 notes / 2
cards. The Desktop mutable-field re-import preserved the reviewed card's existing review/scheduling
state and did not reset it; individual scheduler fields were not recorded. The contributor
walkthrough passed within 15 minutes of active time, excluding dependency/environment downloads,
with no additional assistance beyond the README and normal command-line/tool feedback. Exact
contributor elapsed time and OS remain unreported.
