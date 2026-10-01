# Vocabulary TSV Contract

## File Encoding and Shape

- Path: `data/vocabulary.tsv`
- Encoding: UTF-8, decoded strictly
- Parser: CSV-compatible parsing with tab delimiter and strict syntax
- Header: exactly one first row in this exact order:

```tsv
id	english	indonesian	malaysian	image	tags
```

- Data: at least one concept row, with exactly six fields per logical record
- Unknown, missing, repeated, or reordered columns are invalid in V1

## Field Contract

| Column | Required value | Contract |
|---|---:|---|
| `id` | Yes | Exactly six ASCII digits; unique; kept as text |
| `english` | Yes | Reviewed neutral cue stored verbatim |
| `indonesian` | Yes | Reviewed Bahasa Indonesia answer stored verbatim |
| `malaysian` | Yes | Reviewed Bahasa Malaysia answer stored verbatim |
| `image` | No | Empty or safe POSIX-style relative path under `media/` |
| `tags` | No | Empty or whitespace-separated Anki tag tokens |

Every non-empty field rejects leading or trailing Unicode whitespace. The loader and validator do
not trim, case-fold, translate, normalize, or correct vocabulary content. Internal spaces remain
part of language fields; whitespace separates tag tokens only after the whole field passes the
outer-whitespace rule.

## ID Rules

- Valid: `000001`, `123456`, `999999`
- Invalid: `1`, `0000001`, `０００００１`, `ABC001`, ` 000001`, `000001 `
- Duplicate detection compares the complete six-character value.
- Changing an ID creates a different concept and a different Anki note identity.
- Changing any other column does not change note identity.

## Image Rules

An image reference:

1. Uses `/` as the repository-data separator and contains no backslash.
2. Is relative, with no empty, `.` or `..` component.
3. Resolves strictly to an existing regular file beneath the resolved `media/` root.
4. Is not an HTTP, HTTPS, `file:`, or other URL.
5. May contain spaces or non-ASCII characters supported by the local filesystem.

Different concepts may reuse the exact same resolved file. Distinct resolved files whose final
filenames compare equal after Unicode case-folding are invalid because Anki packages flatten media
to a shared filename namespace. Diagnostics report every conflicting source reference.

## Malformed Input

The following are validation failures:

- Missing, extra, reordered, or repeated header columns
- Empty file or header-only file
- Invalid UTF-8 or strict CSV/TSV syntax
- A row with fewer or more than six fields
- Blank required values
- Leading or trailing whitespace in any non-empty value
- Malformed or duplicate ID
- Missing, non-file, unsafe, escaping, remote, or colliding image reference

When parsing can safely continue, all independent failures are collected and reported with the
physical source row and concept ID when available. If decoding or syntax makes later row boundaries
unreliable, validation stops at that fatal error.

## Valid Example

```tsv
id	english	indonesian	malaysian	image	tags
000001	car	mobil	kereta		transport
000002	office	kantor	pejabat	places/office.jpg	work formal
```
