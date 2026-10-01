"""Domain values and stable Anki compatibility identities."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import genanki

DECK_ID = 1242123295
MODEL_ID = 1942161817
GUID_NAMESPACE = "myid-anki:v1"


@dataclass(frozen=True, slots=True, init=False)
class VocabularyConcept:
    id: str
    english: str
    indonesian: str
    malaysian: str
    image: str | None = None
    source_row: int | None = None
    raw_tags: str | None = field(default=None, repr=False, compare=False)
    _tags: tuple[str, ...] = field(default=(), repr=False)

    def __init__(
        self,
        id: str,
        english: str,
        indonesian: str,
        malaysian: str,
        image: str | None = None,
        tags: list[str] | tuple[str, ...] | None = None,
        source_row: int | None = None,
        raw_tags: str | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "english", english)
        object.__setattr__(self, "indonesian", indonesian)
        object.__setattr__(self, "malaysian", malaysian)
        object.__setattr__(self, "image", image)
        object.__setattr__(self, "source_row", source_row)
        object.__setattr__(self, "raw_tags", raw_tags)
        object.__setattr__(self, "_tags", tuple(tags or ()))

    @property
    def tags(self) -> list[str]:
        """Return tags as a list without exposing mutable internal state."""
        return list(self._tags)


@dataclass(frozen=True, slots=True)
class MediaReference:
    source_value: str
    resolved_path: Path
    package_name: str
    collision_key: str


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    source: Path
    row: int | None = None
    concept_id: str | None = None
    field: str | None = None


class ValidationError(Exception):
    """An aggregate of actionable source or media problems."""

    def __init__(self, issues: tuple[ValidationIssue, ...] | list[ValidationIssue]):
        self.issues = tuple(issues)
        super().__init__("; ".join(issue.message for issue in self.issues))


class _ValidatedToken:
    pass


_VALIDATED_TOKEN = _ValidatedToken()


@dataclass(frozen=True, slots=True, init=False)
class ValidatedVocabulary:
    concepts: tuple[VocabularyConcept, ...]
    media: tuple[MediaReference, ...]

    def __init__(
        self,
        concepts: tuple[VocabularyConcept, ...],
        media: tuple[MediaReference, ...],
        *,
        _token: _ValidatedToken | None = None,
    ):
        if _token is not _VALIDATED_TOKEN:
            raise TypeError("ValidatedVocabulary can only be created by the validator")
        object.__setattr__(self, "concepts", concepts)
        object.__setattr__(self, "media", media)

    @classmethod
    def _from_validator(
        cls,
        concepts: tuple[VocabularyConcept, ...],
        media: tuple[MediaReference, ...],
    ) -> ValidatedVocabulary:
        return cls(concepts, media, _token=_VALIDATED_TOKEN)


def stable_guid(concept_id: str) -> str:
    """Return the Anki GUID derived only from a permanent concept ID."""
    return genanki.guid_for(GUID_NAMESPACE, concept_id)
