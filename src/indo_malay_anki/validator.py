"""Source and media validation performed before package generation."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from .loader import SourceFormatError, parse_tsv
from .model import (
    MediaReference,
    ValidatedVocabulary,
    ValidationError,
    ValidationIssue,
    VocabularyConcept,
)

_ID_PATTERN = re.compile(r"[0-9]{6}\Z", re.ASCII)
_RELATIONS = frozenset({"similar", "different-common-word", "false-friend"})


def _same_answer_form(indonesian: str, malaysian: str) -> bool:
    def normalized(value: str) -> str:
        return " ".join(unicodedata.normalize("NFKC", value).casefold().split())

    return normalized(indonesian) == normalized(malaysian)


def _issue(
    code: str,
    message: str,
    source: Path,
    concept: VocabularyConcept | None = None,
    field: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        code,
        message,
        source,
        concept.source_row if concept else None,
        concept.id if concept and concept.id else None,
        field,
    )


def _media_path_issue(
    concept: VocabularyConcept, source: Path, media_root: Path
) -> tuple[ValidationIssue | None, MediaReference | None]:
    value = concept.image
    if value is None:
        return None, None
    raw_parts = value.split("/")
    parts = PurePosixPath(value).parts
    try:
        parsed = urlsplit(value)
    except ValueError:
        return _issue(
            "unsafe_media_path",
            "Image reference is malformed and must be a safe relative path inside media/",
            source,
            concept,
            "image",
        ), None
    if (
        "\\" in value
        or parsed.scheme
        or parsed.netloc
        or PurePosixPath(value).is_absolute()
        or not parts
        or any(part in ("", ".", "..") for part in raw_parts)
    ):
        return _issue(
            "unsafe_media_path",
            "Image must be a safe relative path inside media/",
            source,
            concept,
            "image",
        ), None

    try:
        root = media_root.resolve(strict=True)
        target = (root / Path(*parts)).resolve(strict=True)
        target.relative_to(root)
    except (OSError, ValueError):
        return _issue(
            "missing_media",
            f"Image reference {value!r} is missing or resolves outside media/",
            source,
            concept,
            "image",
        ), None
    if not target.is_file():
        return _issue(
            "invalid_media_type",
            "Image reference must resolve to a regular file",
            source,
            concept,
            "image",
        ), None
    package_name = target.name
    return None, MediaReference(value, target, package_name, package_name.casefold(), (value,))


def validate_vocabulary(source_path: Path, media_root: Path) -> ValidatedVocabulary:
    source = Path(source_path)
    media_dir = Path(media_root)
    try:
        parsed = parse_tsv(source)
        concepts = parsed.concepts
        issues = list(parsed.issues)
    except SourceFormatError as exc:
        raise ValidationError(exc.issues) from exc

    if not concepts and not issues:
        issues.append(
            ValidationIssue("empty_dataset", "At least one vocabulary concept is required", source)
        )

    seen_ids: set[str] = set()
    resolved_references: list[tuple[VocabularyConcept, MediaReference]] = []
    for concept in concepts:
        if not concept.id:
            issues.append(_issue("missing_id", "Concept ID is required", source, concept, "id"))
        elif not _ID_PATTERN.fullmatch(concept.id):
            issues.append(
                _issue(
                    "invalid_id",
                    "Concept ID must be exactly six ASCII digits",
                    source,
                    concept,
                    "id",
                )
            )
        if concept.id in seen_ids:
            issues.append(
                _issue("duplicate_id", f"Duplicate concept ID {concept.id}", source, concept, "id")
            )
        seen_ids.add(concept.id)

        for field_name in ("english", "indonesian", "malaysian"):
            value = getattr(concept, field_name)
            if not value:
                issues.append(
                    _issue(
                        "missing_required", f"{field_name} is required", source, concept, field_name
                    )
                )

        if concept.relation not in _RELATIONS:
            issues.append(
                _issue(
                    "invalid_relation",
                    "relation must be similar, different-common-word, or false-friend",
                    source,
                    concept,
                    "relation",
                )
            )
        if concept.relation == "same" or (
            concept.relation in {"similar", "different-common-word"}
            and _same_answer_form(concept.indonesian, concept.malaysian)
        ):
            issues.append(
                _issue(
                    "no_cross_language_difference",
                    "Shared ordinary vocabulary is excluded from this contrast deck",
                    source,
                    concept,
                    "relation",
                )
            )
        if concept.relation == "false-friend" and not concept.contrast:
            issues.append(
                _issue(
                    "missing_contrast",
                    "false-friend requires contrast",
                    source,
                    concept,
                    "contrast",
                )
            )
        if concept.relation != "false-friend" and concept.contrast:
            issues.append(
                _issue(
                    "unexpected_contrast",
                    "contrast is only allowed for false-friend",
                    source,
                    concept,
                    "contrast",
                )
            )

        for field_name in (
            "id",
            "english",
            "indonesian",
            "malaysian",
            "relation",
            "image",
            "tags",
            "contrast",
        ):
            value = concept.raw_tags if field_name == "tags" else getattr(concept, field_name)
            if value and value != value.strip():
                issues.append(
                    _issue(
                        "outer_whitespace",
                        f"{field_name} must not have leading or trailing whitespace",
                        source,
                        concept,
                        field_name,
                    )
                )

        media_issue, reference = _media_path_issue(concept, source, media_dir)
        if media_issue:
            issues.append(media_issue)
        elif reference:
            resolved_references.append((concept, reference))

    by_collision_key: dict[str, dict[Path, list[tuple[VocabularyConcept, MediaReference]]]] = (
        defaultdict(lambda: defaultdict(list))
    )
    for concept, reference in resolved_references:
        by_collision_key[reference.collision_key][reference.resolved_path].append(
            (concept, reference)
        )
    for collision_key, by_file in by_collision_key.items():
        if len(by_file) < 2:
            continue
        for references in by_file.values():
            for concept, reference in references:
                issues.append(
                    _issue(
                        "media_basename_collision",
                        (
                            f"Image basename {reference.package_name!r} collides "
                            f"case-insensitively ({collision_key})"
                        ),
                        source,
                        concept,
                        "image",
                    )
                )

    if issues:
        raise ValidationError(issues)

    media_by_path: dict[Path, list[MediaReference]] = defaultdict(list)
    for _, reference in resolved_references:
        media_by_path[reference.resolved_path].append(reference)
    media = tuple(
        sorted(
            (
                MediaReference(
                    references[0].source_value,
                    path,
                    references[0].package_name,
                    references[0].collision_key,
                    tuple(dict.fromkeys(item.source_value for item in references)),
                )
                for path, references in media_by_path.items()
            ),
            key=lambda item: (item.package_name.casefold(), item.package_name),
        )
    )
    return ValidatedVocabulary._from_validator(tuple(concepts), media)
