from __future__ import annotations

import csv
from pathlib import Path

from indo_malay_anki.builder import build_package
from indo_malay_anki.model import DECK_ID, MODEL_ID, stable_guid
from indo_malay_anki.validator import validate_vocabulary


def test_canonical_build_keeps_baseline_identity_and_one_card_per_concept(
    tmp_path, corpus_scaling_baseline, package_inspector
):
    root = Path(__file__).resolve().parents[2]
    source = root / "data" / "vocabulary.tsv"
    with source.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))
    assert set(corpus_scaling_baseline["ids_to_guids"]).issubset(ids)
    assert all(row["relation"] != "same" for row in rows)

    vocabulary = validate_vocabulary(source, root / "media")
    output = build_package(vocabulary, tmp_path / "myid-anki.apkg", root / "templates")
    package, _timestamps = package_inspector(output)
    assert package["deck_ids"] == (DECK_ID,)
    assert str(MODEL_ID) in package["models"]
    assert len(package["notes"]) == len(package["cards"]) == len(rows)
    note_guids = {note[0] for note in package["notes"]}
    card_guids = {card[0] for card in package["cards"]}
    assert note_guids == card_guids == {stable_guid(concept_id) for concept_id in ids}
    assert set(corpus_scaling_baseline["ids_to_guids"].values()).issubset(note_guids)
