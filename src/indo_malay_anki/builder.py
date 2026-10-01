"""Projection of validated vocabulary into a standard Anki package."""

from __future__ import annotations

import html
import os
import sqlite3
import tempfile
import time
import zipfile
from collections.abc import Callable
from pathlib import Path

import genanki

from .model import DECK_ID, MODEL_ID, ValidatedVocabulary, VocabularyConcept, stable_guid

OUTPUT_RELATIVE_PATH = Path("dist/myid-anki.apkg")
FIELD_NAMES = ("ID", "English", "Indonesian", "Malaysian", "Image")


class BuildError(Exception):
    """A package generation or output transaction failed."""


def _load_templates(template_dir: Path) -> tuple[str, str, str]:
    try:
        return tuple(
            (template_dir / name).read_text(encoding="utf-8")
            for name in ("front.html", "back.html", "style.css")
        )
    except OSError as exc:
        raise BuildError(f"Cannot read card templates: {exc}") from exc


def make_model(template_dir: Path) -> genanki.Model:
    front, back, css = _load_templates(template_dir)
    return genanki.Model(
        MODEL_ID,
        "MYID Anki Vocabulary",
        fields=[{"name": name} for name in FIELD_NAMES],
        templates=[{"name": "Vocabulary", "qfmt": front, "afmt": back}],
        css=css,
    )


def _image_field(concept: VocabularyConcept, media_by_source: dict[str, str]) -> str:
    if not concept.image:
        return ""
    package_name = media_by_source[concept.image]
    return f'<img src="{html.escape(package_name, quote=True)}">'


def make_note(
    concept: VocabularyConcept,
    model: genanki.Model,
    media_by_source: dict[str, str],
) -> genanki.Note:
    values = [
        concept.id,
        html.escape(concept.english, quote=False),
        html.escape(concept.indonesian, quote=False),
        html.escape(concept.malaysian, quote=False),
        _image_field(concept, media_by_source),
    ]
    return genanki.Note(
        model=model,
        fields=values,
        tags=concept.tags,
        guid=stable_guid(concept.id),
    )


def _max_note_mod(package_path: Path) -> int:
    try:
        with zipfile.ZipFile(package_path) as package:
            data = package.read("collection.anki2")
        connection = sqlite3.connect(":memory:")
        try:
            connection.deserialize(data)
            result = connection.execute("SELECT MAX(mod) FROM notes").fetchone()[0]
            if result is None:
                raise BuildError("Previous package contains no notes")
            return int(result)
        finally:
            connection.close()
    except BuildError:
        raise
    except (OSError, KeyError, zipfile.BadZipFile, sqlite3.Error) as exc:
        raise BuildError(f"Cannot read prior package modification metadata: {exc}") from exc


def _write_package_archive(package: genanki.Package, temporary_path: Path, timestamp: int) -> None:
    package.write_to_file(str(temporary_path), timestamp=float(timestamp))


def build_package(
    vocabulary: ValidatedVocabulary,
    output_path: Path,
    template_dir: Path,
    *,
    clock: Callable[[], float] = time.time,
) -> Path:
    """Build atomically from validated input, advancing Anki note modification metadata."""
    if not isinstance(vocabulary, ValidatedVocabulary):
        raise TypeError("build_package requires ValidatedVocabulary")

    output = Path(output_path)
    templates = Path(template_dir)
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        current_second = int(clock())
        timestamp = current_second
        if output.exists():
            timestamp = max(current_second, _max_note_mod(output) + 1)

        front, back, css = _load_templates(templates)
        model = genanki.Model(
            MODEL_ID,
            "MYID Anki Vocabulary",
            fields=[{"name": name} for name in FIELD_NAMES],
            templates=[{"name": "Vocabulary", "qfmt": front, "afmt": back}],
            css=css,
        )
        deck = genanki.Deck(DECK_ID, "MYID Anki")
        media_by_source = {
            reference.source_value: reference.package_name for reference in vocabulary.media
        }
        for concept in vocabulary.concepts:
            deck.add_note(make_note(concept, model, media_by_source))
        package = genanki.Package(
            deck, media_files=[str(item.resolved_path) for item in vocabulary.media]
        )

        handle, temporary_name = tempfile.mkstemp(
            prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
        )
        os.close(handle)
        temporary_path = Path(temporary_name)
        try:
            _write_package_archive(package, temporary_path, timestamp)
            os.replace(temporary_path, output)
        finally:
            temporary_path.unlink(missing_ok=True)
        return output
    except BuildError:
        raise
    except Exception as exc:
        raise BuildError(f"Unable to build Anki package: {exc}") from exc
