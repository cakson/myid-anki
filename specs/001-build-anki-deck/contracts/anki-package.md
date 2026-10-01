# Anki Package Contract

## Artifact

- Format: standard `.apkg`
- Final path: `dist/myid-anki.apkg`
- Build-time network dependency: none
- Deck count: one
- Note-model count: one custom model
- Card-template count: one
- Note and card count: exactly one each per validated source concept

Byte-for-byte archive equality is not promised. Semantic content and project-controlled identities
are stable for identical inputs.

## Frozen Compatibility Constants

| Item | Value |
|---|---|
| Deck ID | `1242123295` |
| Deck name | `MYID Anki` |
| Model ID | `1942161817` |
| Model name | `MYID Anki Vocabulary` |
| GUID namespace | `myid-anki:v1` |
| Template name | `Indonesian–Malaysian Recall` |

Deck ID, model ID, GUID namespace/algorithm, field schema, and template count are compatibility-
sensitive. Any proposed change requires explicit impact analysis, regression coverage, and a
migration specification.

## Note Contract

Fields are frozen in this order:

1. `ID`
2. `English`
3. `Indonesian`
4. `Malaysian`
5. `Image`

`ID` is the sort field. Tags use Anki's native note tags and are not a sixth field. Text values are
HTML-escaped before insertion. `Image` is either empty or generated `<img>` HTML whose quoted
filename attribute is escaped and references the packaged basename.

For concept ID `x`, note GUID is exactly:

```text
genanki.guid_for("myid-anki:v1", x)
```

The golden compatibility vector is `000001 -> D6BBAuKXK`. Mutable fields, tags, image references,
source order, and card presentation never participate in GUID derivation.

## Front Contract

The sole template uses native Anki conditional replacement:

- Non-empty `Image`: render Image as the primary cue and do not render English as the primary cue.
- Empty `Image`: render English as the primary cue at a font size at least 1.5 times the prompt's
  font size and at font weight 600 or heavier.
- Both states render “Answer in Bahasa Indonesia” and “or Bahasa Melayu”.
- Neither state exposes Indonesian or Malaysian answer fields.
- Stored English remains exactly the reviewed source value; any displayed casing change is applied
  only through CSS and never by changing the note field.
- No core behavior depends on JavaScript.

## Back Contract

The back identifies the cue, then clearly renders:

- `Bahasa Indonesia` and the Indonesian value
- `Bahasa Melayu` and the Malaysian value

For image-backed notes, the image remains visible and English appears as secondary context. For
text-only notes, English remains the cue context. At viewport widths of 320 CSS pixels or greater,
long English, Indonesian, and Malaysian values wrap inside the card viewport, images are constrained
to that viewport, and ordinary content causes no horizontal scrolling. No custom zooming or user
interaction is required.

## Media Contract

- Each distinct referenced file is included once.
- Image HTML refers only to its packaged basename.
- The package contains no remote URL dependency.
- Repeated references to the exact same resolved source file are valid.
- Distinct resolved source files whose packaged basenames compare equal after Unicode case folding
  fail validation before packaging.
- Collision diagnostics report every source reference participating in each conflicting basename.

## Desktop and Mobile First-Import Acceptance

Acceptance records the client name and version for Anki Desktop and one official mobile Anki
client. Using a disposable collection, both clients must demonstrate:

- successful first import of `dist/myid-anki.apkg`;
- exactly one note and one card per source concept;
- offline study of at least one text-cue and one image-cue card;
- bundled image media with no remote dependency;
- both Bahasa Indonesia and Bahasa Melayu labels and answers visible together;
- long-text wrapping and bounded responsive images at viewport widths of 320 CSS pixels or greater,
  with no horizontal scrolling, custom zooming, or interaction;
- all core card behavior working without JavaScript or network access.

Automated tests verify project-controlled package structure and presentation contracts. Recorded
client smoke acceptance verifies behavior owned by the Anki clients.

## Update and Removal Semantics

Rebuilt packages preserve note GUID, deck ID, model ID, schema, and template count. Official Anki
can therefore recognize notes with unchanged concept IDs. Every successful build after a local
package exists assigns notes whole-second modification timestamps strictly greater than the
greatest note timestamp in the immediately preceding package, unless current whole-second Unix time
is already greater. This makes immediate same-second builds newer under newer-wins import behavior,
without sleeping. Timestamps never contribute to GUID identity. Users of supported Anki versions
may choose the client's unconditional update option when appropriate.

A concept absent from the current TSV is absent from the new package. Its absence is not encoded as
a deletion request and importing the new package does not intentionally remove an older note from
the learner's collection. If the same ID is reintroduced later, its deterministic GUID is unchanged:
an extant collection note remains the same logical note and may be updated, while a note independently
deleted by the learner can be imported again under that same identity.

## Semantic Verification Manifest

Automated integration tests normalize each generated package to these assertions:

- Exact fixed deck/model IDs and names
- Exact ordered field schema, CSS, template name, front, and back
- One note and one `ord=0` card per concept
- Expected GUID and escaped fields for every concept
- Note modification metadata, asserted separately as strictly monotonic between successive builds
- Sorted native tag values
- Media basename and content hash for every referenced file

ZIP timestamps/order, SQLite physical layout, internal row IDs, and volatile modification times are
excluded from semantic equality.
