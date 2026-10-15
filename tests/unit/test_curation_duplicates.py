"""Duplicate screening distinguishes deterministic matches from semantic judgments."""

from indo_malay_anki.curation.duplicates import (
    comparison_key,
    find_deterministic_overlaps,
    overlap_allows_new_id,
)


def test_exact_plural_and_trivial_morphology_share_comparison_key():
    assert comparison_key("Cars") == comparison_key("car")
    assert comparison_key("  BANK (financial institution) ") == "bank financial institution"
    assert comparison_key("houses") == comparison_key("house")


def test_deterministic_screen_finds_repeated_concepts():
    candidate = {
        "candidate_id": "new-car",
        "english": "cars",
        "indonesian": "mobil",
        "malaysian": "kereta",
    }
    existing = [
        {"candidate_id": "old-car", "english": "car", "indonesian": "mobil", "malaysian": "kereta"}
    ]
    overlaps = find_deterministic_overlaps(candidate, existing)
    assert overlaps[0]["other_id"] == "old-car"
    assert overlaps[0]["resolution"] == "unresolved"


def test_semantic_synonym_requires_explicit_distinct_sense_resolution():
    overlap = {
        "other_id": "000001",
        "type": "synonym",
        "resolution": "unresolved",
        "rationale": "auto/car",
    }
    assert not overlap_allows_new_id([overlap])
    assert overlap_allows_new_id(
        [{**overlap, "resolution": "distinct", "rationale": "Different sense"}]
    )
    assert not overlap_allows_new_id([{**overlap, "resolution": "merge"}])
