"""Command-line entry points for validation and deck generation."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .builder import OUTPUT_RELATIVE_PATH, BuildError, build_package
from .model import ValidationError
from .validator import validate_vocabulary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myid-anki")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="validate vocabulary source and media")
    commands.add_parser("build", help="validate source and build the Anki package")
    return parser


def _format_issue(issue) -> str:
    row = f":{issue.row}" if issue.row is not None else ""
    concept = issue.concept_id or "?"
    field = issue.field or "source"
    return f"{issue.source}{row} [{concept}] [{field}]: {issue.message}"


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path.cwd()
    try:
        vocabulary = validate_vocabulary(root / "data" / "vocabulary.tsv", root / "media")
    except ValidationError as exc:
        for issue in exc.issues:
            print(_format_issue(issue), file=sys.stderr)
        print(f"Validation failed with {len(exc.issues)} issue(s)", file=sys.stderr)
        return 1

    if args.command == "build":
        try:
            output = build_package(
                vocabulary,
                root / OUTPUT_RELATIVE_PATH,
                root / "templates",
            )
        except BuildError as exc:
            print(f"Build failed: {exc}", file=sys.stderr)
            return 1
        print(
            f"Built {output.relative_to(root)}: {len(vocabulary.concepts)} note(s), "
            f"{len(vocabulary.concepts)} card(s), {len(vocabulary.media)} media file(s)"
        )
        return 0

    concepts = len(vocabulary.concepts)
    media = len(vocabulary.media)
    print(f"Valid: {concepts} concept(s), {media} distinct media file(s)")
    return 0
