# Data Model: Build Local Anki Deck

## VocabularyConcept

One immutable semantic vocabulary concept parsed from a source row.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `id` | `str` | Yes | Exactly six ASCII digits; unique; preserved with leading zeroes |
| `english` | `str` | Yes | Non-empty; no leading or trailing whitespace; stored verbatim |
| `indonesian` | `str` | Yes | Non-empty; no leading or trailing whitespace; stored verbatim |
| `malaysian` | `str` | Yes | Non-empty; no leading or trailing whitespace; stored verbatim |
| `image` | `str | None` | No | Empty becomes `None`; otherwise a safe POSIX-style path relative to `media/` |
| `tags` | `list[str]` | No | Empty becomes `[]`; otherwise whitespace-separated tokens in source order |
| `source_row` | `int` | Yes | One-based physical source location used only for diagnostics |

The implementation uses an immutable value object (a frozen, slotted dataclass is appropriate).
The permanent identity is `id`; all other values are mutable content. Equality used for note
identity MUST NOT include mutable values.

## MediaReference

A validated relationship between a concept's source image value and a repository file.

| Field | Type | Rules |
|---|---|---|
| `source_value` | `str` | Original repository-relative value from TSV |
| `resolved_path` | `Path` | Existing regular file whose strict resolution remains under resolved `media/` |
| `package_name` | `str` | Final path component used in Anki fields and package media map |
| `collision_key` | `str` | `package_name.casefold()` for cross-platform collision detection |

Relationships:

- Zero or more concepts may reference the same resolved media file.
- Two distinct resolved files may not share a collision key.
- A concept has at most one media reference.
- Media bytes remain repository inputs; the TSV stores only the source reference.

## ValidationIssue

A structured, displayable problem collected during loading or validation.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `code` | `str` | Yes | Stable machine-readable category such as `duplicate_id` or `missing_media` |
| `message` | `str` | Yes | Human-readable rejected condition and correction hint |
| `source` | `Path` | Yes | Affected source or media root |
| `row` | `int | None` | No | Present when a physical TSV row is known |
| `concept_id` | `str | None` | No | Present when the ID can be parsed from the row |
| `field` | `str | None` | No | Present when one schema field is responsible |

Validation accumulates independent issues when continuing is safe. Fatal decoding or CSV syntax
errors stop parsing at the point where row boundaries can no longer be trusted.

## ValidatedVocabulary

The only input accepted by the builder.

| Field | Type | Rules |
|---|---|---|
| `concepts` | `tuple[VocabularyConcept, ...]` | Non-empty; unique IDs; source order retained |
| `media` | `tuple[MediaReference, ...]` | Unique resolved files sorted by package name for stable processing |

Construction is internal to the validator so unvalidated row collections cannot accidentally reach
package generation.

## AnkiNoteProjection

The deterministic projection of one validated concept into the frozen Anki note contract.

| Field | Source | Rules |
|---|---|---|
| `guid` | `guid_for("myid-anki:v1", concept.id)` | Depends only on the permanent ID |
| `ID` | `concept.id` | First field and sort field |
| `English` | `concept.english` | HTML-escaped before field insertion |
| `Indonesian` | `concept.indonesian` | HTML-escaped before field insertion |
| `Malaysian` | `concept.malaysian` | HTML-escaped before field insertion |
| `Image` | media reference | Empty string or generated `<img>` HTML whose filename attribute is escaped |
| tags | `concept.tags` | Supplied through Anki's normal note tags |

The projection uses fixed `MODEL_ID = 1942161817`. Field names, order, GUID namespace, GUID
algorithm, and model ID are compatibility-sensitive and may not change without a migration plan.

## DeckPackage

The generated aggregate delivered to the learner.

| Property | Value or rule |
|---|---|
| Deck ID | `1242123295` |
| Deck name | `MYID Anki` |
| Model ID | `1942161817` |
| Model name | `MYID Anki Vocabulary` |
| Template count | Exactly one |
| Note count | Exactly the number of validated concepts |
| Card count | Exactly the number of validated concepts |
| Media | Every distinct referenced file and no remote resource |
| Final path | `dist/indo-malay.apkg` |

The package omits concepts absent from the current TSV. Omission is not a deletion instruction for
notes already present in a learner's Anki collection.

## State Transitions

```text
TSV bytes
  ├─ decode/CSV failure ───────────────> validation failure
  └─ parsed rows
       ├─ schema/content/media issues ─> validation failure
       └─ ValidatedVocabulary
            ├─ validate command ───────> success report
            └─ build command
                 ├─ projection/package failure -> preserve old final package
                 └─ temporary package complete
                      └─ atomic replace -> dist/indo-malay.apkg
```

No invalid or merely parsed collection can transition to package generation. A failed transition
removes only the invocation's temporary file and never modifies a prior successful artifact.

## Cross-Entity Invariants

1. Each `VocabularyConcept` maps to exactly one `AnkiNoteProjection` and one card.
2. The same concept ID always yields the same GUID regardless of content, tags, media, source order,
   or styling.
3. Distinct valid concept IDs yield distinct GUIDs within the project namespace.
4. Every non-empty Image field names a bundled media file.
5. No two distinct media files share a case-folded package name.
6. Deck ID, model ID, field schema, GUID namespace, and template count remain fixed across builds.
7. Reordering source rows may alter physical package ordering but not semantic content or identity.
