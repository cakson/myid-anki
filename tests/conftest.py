from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from indo_malay_anki.model import DECK_ID, MODEL_ID, stable_guid

HEADER = ("id", "english", "indonesian", "malaysian", "relation", "image", "tags", "contrast")
DEFAULT_ROWS = (("000001", "car", "mobil", "kereta", "", "transport"),)


@pytest.fixture
def corpus_scaling_baseline():
    """Frozen pre-Feature-004 Anki identities for regression checks."""
    fixture = Path(__file__).parent / "fixtures" / "corpus_scaling_baseline.json"
    baseline = json.loads(fixture.read_text(encoding="utf-8"))
    assert baseline["count"] == len(baseline["ids_to_guids"]) == 137
    assert baseline["deck_id"] == DECK_ID and baseline["model_id"] == MODEL_ID
    assert all(
        stable_guid(concept_id) == guid for concept_id, guid in baseline["ids_to_guids"].items()
    )
    return baseline


@pytest.fixture
def repo_factory(tmp_path):
    def create(rows=DEFAULT_ROWS, *, media_files=None, templates=True):
        root = tmp_path / "repo"
        (root / "data").mkdir(parents=True)
        (root / "media").mkdir()
        if templates:
            (root / "templates").mkdir()
            source_templates = Path(__file__).resolve().parents[1] / "templates"
            for name in ("front.html", "back.html", "style.css"):
                (root / "templates" / name).write_text(
                    (source_templates / name).read_text(encoding="utf-8"), encoding="utf-8"
                )
        (root / "dist").mkdir()
        with (root / "data" / "vocabulary.tsv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
            writer.writerow(HEADER)
            for row in rows:
                if len(row) == 6:
                    relation = "same" if row[2] == row[3] else "different-common-word"
                    row = (*row[:4], relation, *row[4:], "")
                writer.writerow(row)
        for relative, content in (media_files or {}).items():
            target = root / "media" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        return root

    return create


@pytest.fixture
def existing_output(repo_factory):
    root = repo_factory()
    output = root / "dist" / "myid-anki.apkg"
    output.write_bytes(b"previous-good-package")
    return root, output, output.read_bytes()


@pytest.fixture
def output_paths(repo_factory):
    root = repo_factory()
    return {
        "root": root,
        "source": root / "data" / "vocabulary.tsv",
        "media": root / "media",
        "templates": root / "templates",
        "dist": root / "dist",
        "package": root / "dist" / "myid-anki.apkg",
    }


def inspect_package(path):
    """Return a normalized semantic manifest plus separately inspectable note timestamps."""
    with zipfile.ZipFile(path) as package:
        database = package.read("collection.anki2")
        media_map = json.loads(package.read("media"))
        media_hashes = {
            name: hashlib.sha256(package.read(index)).hexdigest()
            for index, name in media_map.items()
        }
    connection = sqlite3.connect(":memory:")
    try:
        connection.deserialize(database)
        decks = json.loads(connection.execute("select decks from col").fetchone()[0])
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        notes = connection.execute(
            "select id, guid, mid, mod, flds, tags from notes order by guid"
        ).fetchall()
        cards = connection.execute("select nid, ord from cards order by nid, ord").fetchall()
        note_ids = {row[0]: row[1] for row in notes}
        template_models = {
            model_id: {
                "name": value["name"],
                "fields": tuple(field["name"] for field in value["flds"]),
                "css": value["css"],
                "templates": tuple(
                    (template["name"], template["qfmt"], template["afmt"])
                    for template in value["tmpls"]
                ),
            }
            for model_id, value in models.items()
        }
        manifest = {
            # genanki's seed collection contains Anki's built-in default deck (ID 1).
            "deck_ids": tuple(sorted(int(deck_id) for deck_id in decks if int(deck_id) != 1)),
            "models": template_models,
            "notes": tuple(
                (guid, int(model_id), tuple(fields.split("\x1f")), tuple(sorted(tags.split())))
                for _, guid, model_id, _, fields, tags in notes
            ),
            "cards": tuple(sorted((note_ids[note_id], ordinal) for note_id, ordinal in cards)),
            "media_hashes": tuple(sorted(media_hashes.items())),
        }
        timestamps = {guid: int(mod) for _, guid, _, mod, _, _ in notes}
        return manifest, timestamps
    finally:
        connection.close()


@pytest.fixture
def package_inspector():
    return inspect_package
