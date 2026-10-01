# Anki Package Contract

## Artifact

- Format: standard `.apkg`
- Final path: `dist/indo-malay.apkg`
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
- Empty `Image`: render English as the prominent primary cue.
- Both states render “Answer in Bahasa Indonesia” and “or Bahasa Malaysia”.
- Neither state exposes Indonesian or Malaysian answer fields.
- No core behavior depends on JavaScript.

## Back Contract

The back identifies the cue, then clearly renders:

- `Bahasa Indonesia` and the Indonesian value
- `Bahasa Malaysia` and the Malaysian value

For image-backed notes, the image remains visible and English appears as secondary context. For
text-only notes, English remains the cue context. Styling is responsive and remains readable in a
320-pixel-wide display area.

## Media Contract

- Each distinct referenced file is included once.
- Image HTML refers only to its packaged basename.
- The package contains no remote URL dependency.
- Repeated references to one resolved file are valid.
- Distinct files with case-fold-equivalent basenames fail validation before packaging.

## Update and Removal Semantics

Rebuilt packages preserve note GUID, deck ID, model ID, schema, and template count. Official Anki
can therefore recognize notes with unchanged concept IDs. Under newer-wins import settings, a later
package must carry a later modification time to update content; users of supported Anki versions
may choose the client's unconditional update option when appropriate.

A concept absent from the current TSV is absent from the new package. Its absence is not encoded as
a deletion request and importing the new package does not intentionally remove an older note from
the learner's collection.

## Semantic Verification Manifest

Automated integration tests normalize each generated package to these assertions:

- Exact fixed deck/model IDs and names
- Exact ordered field schema, CSS, template name, front, and back
- One note and one `ord=0` card per concept
- Expected GUID and escaped fields for every concept
- Sorted native tag values
- Media basename and content hash for every referenced file

ZIP timestamps/order, SQLite physical layout, internal row IDs, and volatile modification times are
excluded from semantic equality.
