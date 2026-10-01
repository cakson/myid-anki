import json
import sqlite3
import zipfile

import pytest

from indo_malay_anki import builder
from indo_malay_anki.cli import main


def package_contents(path):
    with zipfile.ZipFile(path) as package:
        database = package.read("collection.anki2")
        media_map = json.loads(package.read("media"))
        media = {name: package.read(index) for index, name in media_map.items()}
    connection = sqlite3.connect(":memory:")
    connection.deserialize(database)
    return connection, media


def test_build_writes_one_note_and_card_and_bundles_media(
    repo_factory, monkeypatch, package_inspector
):
    root = repo_factory(
        rows=(
            ("000001", "car & van", "mobil", "kereta", "", "transport"),
            ("000002", "office", "kantor", "pejabat", "car.png", "work"),
        ),
        media_files={"car.png": b"image-bytes"},
    )
    monkeypatch.chdir(root)
    assert main(["build"]) == 0
    output = root / "dist" / "myid-anki.apkg"
    assert output.is_file()
    connection, media = package_contents(output)
    assert connection.execute("select count(*) from notes").fetchone()[0] == 2
    assert connection.execute("select count(*) from cards").fetchone()[0] == 2
    notes = connection.execute("select guid, mid, flds, tags from notes order by sfld").fetchall()
    assert all(note[1] == 1942161817 for note in notes)
    manifest, _ = package_inspector(output)
    assert manifest["deck_ids"] == (1242123295,)
    model = manifest["models"]["1942161817"]
    assert model["fields"] == ("ID", "English", "Indonesian", "Malaysian", "Image")
    assert len(model["templates"]) == 1
    assert {note[2].split("\x1f", 1)[0] for note in notes} == {"000001", "000002"}
    assert any("car &amp; van" in note[2] for note in notes)
    assert any('<img src="car.png">' in note[2] for note in notes)
    assert any(" transport " in note[3] for note in notes)
    assert {note[0] for note in notes} == {"D6BBAuKXK", "ux,Mq+23&>"}
    assert "car.png" in media and media["car.png"] == b"image-bytes"
    connection.close()


def test_validation_failure_never_reaches_package_generation(repo_factory, monkeypatch):
    root = repo_factory(rows=(("000001", "", "mobil", "kereta", "", ""),))
    (root / "dist").rmdir()
    monkeypatch.chdir(root)
    monkeypatch.setattr(
        builder, "_write_package_archive", lambda *args, **kwargs: pytest.fail("generated")
    )
    assert main(["build"]) == 1
    assert not (root / "dist").exists()


def test_failed_generation_preserves_existing_package(existing_output, monkeypatch):
    root, output, original = existing_output
    monkeypatch.chdir(root)
    monkeypatch.setattr(
        builder,
        "_write_package_archive",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )
    assert main(["build"]) == 1
    assert output.read_bytes() == original
    assert list(output.parent.glob("*.tmp")) == []


def test_build_and_validation_work_without_network(repo_factory, monkeypatch, package_inspector):
    import socket

    root = repo_factory()
    monkeypatch.chdir(root)
    monkeypatch.setattr(
        socket.socket, "connect", lambda *args, **kwargs: pytest.fail("network used")
    )
    assert main(["validate"]) == 0
    assert main(["build"]) == 0
    manifest, _ = package_inspector(root / "dist" / "myid-anki.apkg")
    assert len(manifest["cards"]) == 1


def test_nested_unicode_media_is_flattened_and_shared_once(repo_factory, monkeypatch):
    root = repo_factory(
        rows=(
            ("000001", "house", "rumah", "rumah", "places/café home.png", "places"),
            ("000002", "home", "rumah", "rumah", "places/café home.png", "places"),
        ),
        media_files={"places/café home.png": b"image-bytes"},
    )
    monkeypatch.chdir(root)
    assert main(["build"]) == 0
    connection, media = package_contents(root / "dist" / "myid-anki.apkg")
    assert media == {"café home.png": b"image-bytes"}
    fields = connection.execute("select flds from notes").fetchall()
    assert all('<img src="café home.png">' in row[0] for row in fields)
    assert connection.execute("select count(*) from cards").fetchone()[0] == 2
    connection.close()


def test_distinct_safe_references_to_same_resolved_media_file_build_once(repo_factory, monkeypatch):
    root = repo_factory(
        rows=(
            ("000001", "car", "mobil", "kereta", "real/car.png", ""),
            ("000002", "auto", "mobil", "kereta", "alias.png", ""),
        ),
        media_files={"real/car.png": b"image-bytes"},
    )
    try:
        (root / "media" / "alias.png").symlink_to(root / "media" / "real" / "car.png")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable")

    monkeypatch.chdir(root)
    assert main(["build"]) == 0
    connection, media = package_contents(root / "dist" / "myid-anki.apkg")
    assert media == {"car.png": b"image-bytes"}
    fields = connection.execute("select flds from notes").fetchall()
    assert len(fields) == 2
    assert all('<img src="car.png">' in row[0] for row in fields)
    connection.close()
