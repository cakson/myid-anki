# Learner Source and Anki Compatibility Contract

Policy-v3 confidence tier, rationale, review flags, historical objections, evidence, and risk path are curation metadata only. Their addition or correction never changes this source schema, permanent concept ID, note fields, or ID-derived GUID. Promotion still requires a current ACCEPT decision, no unresolved overlap, and the guarded export transaction; provisional historical replay acceptance does not itself enter this file.

## Accepted source

`data/vocabulary.tsv` remains the only vocabulary input to the offline deck builder. It is strict UTF-8 TSV with exactly one header in this order:

```tsv
id	english	indonesian	malaysian	relation	image	tags	contrast
```

Every row is one accepted semantic concept. Required: `id`, `english`, `indonesian`, `malaysian`, `relation`. `image` and `tags` may be empty. `contrast` is required for `false-friend` and must be empty for the other two learner relations. It concisely identifies the misleading lookalike and its actual meaning and is derived from separately evidenced structured contrast components in the curation record. Values with leading or trailing whitespace are invalid. The existing six-digit ASCII ID, strict row/header, media-path, and collision rules remain.

`relation` in learner source must be exactly `similar`, `different-common-word`, or `false-friend`. `same` can classify a curation candidate but is rejected from this contrast-only deck. Relation never appears on the front; it is source-only in the MVP. The original `000001` car proposal was held after independent review and retired from the active learner TSV. Its permanent assignment remains in the ID ledger and may only be reintroduced for that same concept after all gates pass.

## Build projection

The build, including the GitHub release build, does not consult `curation/` or invoke AI or live language research. It projects each validated TSV row into exactly one note and one card. The Anki model still has exactly five fields in this order: `ID`, `English`, `Indonesian`, `Malaysian`, `Image`. The front template remains neutral. The builder escapes all source text; for a false friend only, it appends the escaped `contrast` as a visibly secondary back-only HTML block to the existing `Malaysian` field. Other rows project just the Malaysian answer. The contrast must never enter the English or image fields or the front template.

The deck ID remains `1242123295`, model ID remains `1942161817`, GUID namespace remains `myid-anki:v1`, and `000001` keeps GUID `D6BBAuKXK`. Relation, contrast, evidence, tags, image, and wording do not affect GUID generation. Keep one card template and one card per note.

## Compatibility and release verification

The TSV change is intentional and requires updated loader/validator/tests/README; a six-column source fails with an actionable header error after migration. Curation metadata is never packaged. The Anki note field count and order do not change, avoiding the documented packaged-deck update problem caused by added fields. Still verify by importing a pre-feature package, then a post-feature package with the same `000001` ID into Anki Desktop. Record client version, update setting, note/card count, GUID, changed content, and preserved review history. Do not release if existing notes fail to update or duplicate.

For reference, the [Anki packaged-deck manual](https://docs.ankiweb.net/importing/packaged-decks.html) states that note-type field changes generally prevent updates to already imported notes. This contract deliberately avoids that schema change.
