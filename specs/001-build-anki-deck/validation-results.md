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

Client names/versions, operating systems, and results for image-cue/bundled-media and long-text /
oversized-image cases were not included in the report. No more specific client or viewport details
are claimed here.

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

The client version, import settings, exact counts, review-state behavior, and behavior after the
user independently deletes a note were not included in the report; no results for those details are
claimed here.

## Contributor Walkthrough

**Status: Passed (user-reported manual acceptance, 2026-10-02).** An unfamiliar contributor was
able to understand the project's purpose and Indonesian ↔ Malaysian Malay learning model from the
README; set up the project; find and edit the vocabulary TSV; add a concept with a permanent ID;
validate the data; build and locate the `.apkg`; understand optional media; and follow the edit →
validate → build workflow.

The README also explains the deck's contrastive-learning purpose, neutral English/image cues,
bidirectional use, and why both language answers are shown. The contributor's operating system,
elapsed time, any undocumented assistance, and whether an image-backed concept was built were not
specified in the report; no outcomes for those details are claimed here.
