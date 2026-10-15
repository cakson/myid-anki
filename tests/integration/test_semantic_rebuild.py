import csv
from pathlib import Path

import pytest

from indo_malay_anki.builder import build_package
from indo_malay_anki.loader import HEADER
from indo_malay_anki.model import VocabularyConcept, stable_guid
from indo_malay_anki.validator import validate_vocabulary


def write_rows(root: Path, rows):
    with (root / "data" / "vocabulary.tsv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(HEADER)
        for row in rows:
            if len(row) == 6:
                relation = "same" if row[2] == row[3] else "different-common-word"
                row = (*row[:4], relation, *row[4:], "")
            writer.writerow(row)


def make_build(root, *, clock=lambda: 2_000_000_000):
    vocabulary = validate_vocabulary(root / "data" / "vocabulary.tsv", root / "media")
    return build_package(
        vocabulary, root / "dist" / "myid-anki.apkg", root / "templates", clock=clock
    )


def test_repeated_builds_are_semantically_equivalent_except_mod(repo_factory, package_inspector):
    root = repo_factory()
    first = make_build(root, clock=lambda: 2_000_000_000)
    first_manifest, first_mods = package_inspector(first)
    second = make_build(root, clock=lambda: 2_000_000_001)
    second_manifest, second_mods = package_inspector(second)
    assert first_manifest == second_manifest
    assert second_mods["D6BBAuKXK"] > first_mods["D6BBAuKXK"]


def test_release_tag_does_not_change_anki_identity(repo_factory, package_inspector, monkeypatch):
    root = repo_factory()
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v0.1.0")
    monkeypatch.setenv("GITHUB_REF_NAME", "v0.1.0")
    before, _ = package_inspector(make_build(root))

    write_rows(root, (("000001", "automobile", "mobil", "kereta", "", "transport"),))
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v9.8.7")
    monkeypatch.setenv("GITHUB_REF_NAME", "v9.8.7")
    after, _ = package_inspector(make_build(root))

    assert before["deck_ids"] == after["deck_ids"]
    assert set(before["models"]) == set(after["models"])
    assert [note[0] for note in before["notes"]] == [note[0] for note in after["notes"]]
    assert len(after["notes"]) == len(after["cards"]) == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("english", "automobile"),
        ("indonesian", "otomobil"),
        ("malaysian", "auto"),
        ("image", "first.png"),
        ("tags", "vehicles"),
    ],
)
def test_each_mutable_field_preserves_one_note_and_card(
    repo_factory, package_inspector, field, value
):
    root = repo_factory(media_files={"first.png": b"image", "second.png": b"other"})
    before, _ = package_inspector(make_build(root))
    guid = before["notes"][0][0]
    row = ["000001", "car", "mobil", "kereta", "", "transport"]
    column = {"english": 1, "indonesian": 2, "malaysian": 3, "image": 4, "tags": 5}[field]
    row[column] = value
    write_rows(root, (tuple(row),))
    after, _ = package_inspector(make_build(root))
    assert after["notes"][0][0] == guid
    assert len(after["notes"]) == len(after["cards"]) == 1


def test_styling_change_preserves_note_identity(repo_factory, package_inspector):
    root = repo_factory()
    before, _ = package_inspector(make_build(root))
    css_path = root / "templates" / "style.css"
    css_path.write_text(
        css_path.read_text(encoding="utf-8") + "\n/* presentation change */\n", encoding="utf-8"
    )
    after, _ = package_inspector(make_build(root))
    assert before["notes"][0][0] == after["notes"][0][0]
    assert len(after["notes"]) == len(after["cards"]) == 1


@pytest.mark.parametrize(
    "mutable_fields",
    [
        {"english": "automobile"},
        {"indonesian": "otomobil"},
        {"malaysian": "auto"},
        {"tags": ["vehicles"]},
        {"image": "car.png"},
    ],
)
def test_mutable_concept_fields_do_not_change_guid(mutable_fields):
    original = VocabularyConcept("000001", "car", "mobil", "kereta")
    changed = VocabularyConcept(
        "000001",
        mutable_fields.get("english", original.english),
        mutable_fields.get("indonesian", original.indonesian),
        mutable_fields.get("malaysian", original.malaysian),
        mutable_fields.get("image", original.image),
        mutable_fields.get("tags", original.tags),
    )
    assert stable_guid(original.id) == stable_guid(changed.id) == "D6BBAuKXK"


def test_immediate_same_second_build_has_same_guid_and_newer_mod(repo_factory, package_inspector):
    root = repo_factory()
    output = make_build(root, clock=lambda: 2_000_000_000)
    manifest_a, mods_a = package_inspector(output)
    guid_a = manifest_a["notes"][0][0]

    write_rows(root, (("000001", "car", "automobile", "kereta", "", "transport"),))
    output = make_build(root, clock=lambda: 2_000_000_000)
    manifest_b, mods_b = package_inspector(output)
    assert manifest_b["notes"][0][0] == guid_a
    assert mods_b[guid_a] > mods_a[guid_a]
    assert manifest_b["notes"][0][2][2] == "automobile"


def test_row_order_does_not_change_note_identity(repo_factory, package_inspector):
    root = repo_factory(
        rows=(
            ("000001", "car", "mobil", "kereta", "", "transport"),
            ("000002", "office", "kantor", "pejabat", "", "work"),
        )
    )
    first, _ = package_inspector(make_build(root, clock=lambda: 2_000_000_000))
    write_rows(
        root,
        (
            ("000002", "office", "kantor", "pejabat", "", "work"),
            ("000001", "car", "mobil", "kereta", "", "transport"),
        ),
    )
    second, _ = package_inspector(make_build(root, clock=lambda: 2_000_000_000))
    assert {row[0] for row in first["notes"]} == {row[0] for row in second["notes"]}
    assert first["cards"] == second["cards"]


def test_remove_build_reintroduce_same_id_restores_original_guid(repo_factory, package_inspector):
    root = repo_factory()
    manifest_a, _ = package_inspector(make_build(root, clock=lambda: 2_000_000_000))
    original_guid = manifest_a["notes"][0][0]

    write_rows(root, (("000002", "office", "kantor", "pejabat", "", "work"),))
    manifest_b, _ = package_inspector(make_build(root, clock=lambda: 2_000_000_000))
    assert original_guid not in {row[0] for row in manifest_b["notes"]}

    write_rows(root, (("000001", "car", "mobil", "kereta", "", "transport"),))
    manifest_c, _ = package_inspector(make_build(root, clock=lambda: 2_000_000_000))
    assert manifest_c["notes"][0][0] == original_guid


def test_image_add_change_remove_lifecycle_preserves_guid_and_one_card(
    repo_factory, package_inspector
):
    root = repo_factory()
    (root / "media" / "first.png").write_bytes(b"first image")
    (root / "media" / "second.png").write_bytes(b"second image")
    manifest_text, _ = package_inspector(make_build(root))
    guid = manifest_text["notes"][0][0]
    assert manifest_text["media_hashes"] == ()

    write_rows(root, (("000001", "car", "mobil", "kereta", "first.png", "transport"),))
    manifest_first, _ = package_inspector(make_build(root))
    assert manifest_first["notes"][0][0] == guid
    assert len(manifest_first["cards"]) == 1
    assert {name for name, _ in manifest_first["media_hashes"]} == {"first.png"}

    write_rows(root, (("000001", "car", "mobil", "kereta", "second.png", "transport"),))
    manifest_second, _ = package_inspector(make_build(root))
    assert manifest_second["notes"][0][0] == guid
    assert len(manifest_second["cards"]) == 1
    assert {name for name, _ in manifest_second["media_hashes"]} == {"second.png"}

    write_rows(root, (("000001", "car", "mobil", "kereta", "", "transport"),))
    manifest_removed, _ = package_inspector(make_build(root))
    assert manifest_removed["notes"][0][0] == guid
    assert len(manifest_removed["cards"]) == 1
    assert manifest_removed["media_hashes"] == ()
