# CLI Contract

## Invocation Context

Commands are run from the repository root after installing the project into a Python 3.12+
environment. All V1 paths are fixed relative to that root:

- Source: `data/vocabulary.tsv`
- Media root: `media/`
- Templates: `templates/front.html`, `templates/back.html`, `templates/style.css`
- Output: `dist/indo-malay.apkg`

No command performs network access.

## Validate Command

```console
python -m indo_malay_anki validate
```

Behavior:

1. Decode and parse the TSV.
2. Run all source, identity, whitespace, and media validations.
3. Report every independent issue that can safely be discovered in the same run.
4. Do not create `dist/` or any package.

Successful result:

- Exit code `0`.
- Standard output contains a summary with concept and distinct-media counts.
- Standard error is empty.

Validation failure:

- Exit code `1`.
- Standard error contains one diagnostic per issue and a failure summary.
- No generated file is created or changed.

Diagnostic shape:

```text
<source>[:<row>] [<concept-id-or-?>] [<field-or-source>]: <message>
```

Exact wording may evolve, but source, known row, known concept ID, field/category, and rejected
condition are part of the stable behavior.

## Build Command

```console
python -m indo_malay_anki build
```

Behavior:

1. Perform the complete validate-command workflow.
2. Stop without creating or replacing output if validation fails.
3. Load repository templates and project compatibility constants.
4. Build a temporary package in `dist/`.
5. Atomically replace `dist/indo-malay.apkg` after successful package completion.

Successful result:

- Exit code `0`.
- Exactly one final `.apkg` exists at `dist/indo-malay.apkg`.
- Standard output reports the final path plus note, card, and media counts.

Build or package failure:

- Exit code `1`.
- Standard error describes the failure without a traceback for expected user-correctable errors.
- Any prior `dist/indo-malay.apkg` remains byte-for-byte unchanged.
- Invocation-owned temporary output is removed.

## Usage Errors

Unknown commands or malformed CLI syntax use `argparse` behavior and exit code `2`. Both commands
support `--help`. Internal reusable functions raise structured domain errors; only the CLI converts
them to user-facing messages and exit codes.

## Optional Installed Alias

An installed console script named `myid-anki` may expose the same subcommands and results:

```console
myid-anki validate
myid-anki build
```

The `python -m indo_malay_anki` form remains canonical in README instructions and tests.
