"""Strict UTF-8 TSV parsing without content normalization."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .model import ValidationIssue, VocabularyConcept

HEADER = ("id", "english", "indonesian", "malaysian", "image", "tags")


class SourceFormatError(Exception):
    def __init__(self, issues: tuple[ValidationIssue, ...] | list[ValidationIssue]):
        self.issues = tuple(issues)
        super().__init__("; ".join(issue.message for issue in self.issues))


@dataclass(frozen=True, slots=True)
class ParseResult:
    concepts: tuple[VocabularyConcept, ...]
    issues: tuple[ValidationIssue, ...]


def parse_tsv(path: Path) -> ParseResult:
    source = Path(path)
    try:
        stream = source.open("r", encoding="utf-8", errors="strict", newline="")
    except OSError as exc:
        issue = ValidationIssue("source_read", f"Cannot read source: {exc}", source)
        raise SourceFormatError((issue,)) from exc

    concepts: list[VocabularyConcept] = []
    issues: list[ValidationIssue] = []
    with stream:
        reader = csv.reader(stream, delimiter="\t", strict=True)
        try:
            header = next(reader)
        except StopIteration:
            issue = ValidationIssue("empty_source", "Source file is empty", source, row=1)
            raise SourceFormatError((issue,)) from None
        except (csv.Error, UnicodeDecodeError) as exc:
            issue = ValidationIssue("source_syntax", f"Cannot parse source: {exc}", source, row=1)
            raise SourceFormatError((issue,)) from exc

        if tuple(header) != HEADER:
            issue = ValidationIssue(
                "invalid_header",
                f"Header must contain exactly: {', '.join(HEADER)}",
                source,
                row=1,
            )
            raise SourceFormatError((issue,))

        try:
            for row in reader:
                physical_row = reader.line_num
                if tuple(row) == HEADER:
                    issues.append(
                        ValidationIssue(
                            "repeated_header",
                            "Source header must appear only once",
                            source,
                            row=physical_row,
                        )
                    )
                    continue
                if len(row) != len(HEADER):
                    issues.append(
                        ValidationIssue(
                            "malformed_row",
                            f"Expected {len(HEADER)} fields, found {len(row)}",
                            source,
                            row=physical_row,
                            concept_id=row[0] if row and row[0] else None,
                        )
                    )
                    continue
                concept_id, english, indonesian, malaysian, image, tags = row
                concepts.append(
                    VocabularyConcept(
                        concept_id,
                        english,
                        indonesian,
                        malaysian,
                        image or None,
                        tags.split() if tags else [],
                        physical_row,
                        tags,
                    )
                )
        except (csv.Error, UnicodeDecodeError) as exc:
            issue = ValidationIssue(
                "source_syntax", f"Cannot parse source: {exc}", source, row=reader.line_num
            )
            issues.append(issue)

    if not concepts and not issues:
        issues.append(
            ValidationIssue("empty_dataset", "At least one vocabulary concept is required", source)
        )
    return ParseResult(tuple(concepts), tuple(issues))


def load_tsv(path: Path) -> tuple[VocabularyConcept, ...]:
    result = parse_tsv(path)
    if result.issues:
        raise SourceFormatError(result.issues)
    if not result.concepts:
        issue = ValidationIssue(
            "empty_dataset", "At least one vocabulary concept is required", Path(path)
        )
        raise SourceFormatError((issue,))
    return result.concepts
