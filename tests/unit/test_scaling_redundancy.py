from __future__ import annotations

from indo_malay_anki.scaling.redundancy import ExclusionIndex


def _candidate(cue, sense="everyday object", ind="benda", mal="barang"):
    return {"english": cue, "sense": sense, "indonesian": ind, "malaysian": mal}


def test_exact_plural_synonym_and_answer_pair():
    index = ExclusionIndex()
    index.add("old:1", _candidate("mobile phone", "handheld telephone", "ponsel", "telefon bimbit"))
    assert index.screen(_candidate("mobile phones", "handheld telephone"))["outcome"] == "duplicate"
    assert index.screen(_candidate("cell phone", "handheld telephone"))["outcome"] == "redundant"
    assert (
        index.screen(_candidate("handset", ind="ponsel", mal="telefon bimbit"))["outcome"]
        == "duplicate"
    )


def test_historical_same_and_distinct_sense():
    index = ExclusionIndex()
    index.add("old:2", _candidate("bank", "financial institution", "bank", "bank"), prior_same=True)
    assert index.screen(_candidate("bank", "financial institution"))["outcome"] == "prior-same"
    ambiguous = index.screen(_candidate("bank", "river edge", "tebing", "tebing"))
    assert ambiguous["outcome"] == "needs-semantic-review"
    assert (
        index.screen(
            _candidate("bank", "river edge", "tebing", "tebing"),
            resolver=lambda new, old: "distinct",
        )["outcome"]
        == "distinct-sense"
    )


def test_cross_slice_near_equivalence_needs_review():
    index = ExclusionIndex()
    index.add(
        "run:s01:1", _candidate("train station", "place to board a train", "stasiun", "stesen")
    )
    result = index.screen(
        _candidate("railway station", "place to board a train", "stasiun kereta", "stesen kereta")
    )
    assert result["outcome"] == "needs-semantic-review"
    assert result["matches"][0]["ref"] == "run:s01:1"


def test_same_english_cue_with_distinct_sense_can_reach_v31_review():
    index = ExclusionIndex()
    index.add("canonical:car", _candidate("car", "", "mobil", "kereta"))
    candidate = _candidate("car", "railway carriage", "gerbong", "gerabak")
    result = index.screen(candidate, resolver=lambda _new, _old: "distinct")
    assert result["outcome"] == "distinct-sense"
