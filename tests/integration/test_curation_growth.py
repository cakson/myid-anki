"""Later batches screen accepted and previously withheld concepts before ID allocation."""

import json

from indo_malay_anki.curation.report import batch_report
from indo_malay_anki.curation.workflow import (
    check_candidate,
    ingest_response,
    init_batch,
    packet_for,
)


def response(role, result):
    return json.dumps({"schema_version": 1, "role": role, "model": "fixture", "result": result})


def test_later_batch_surfaces_source_and_prior_hold_then_rejects_duplicate(tmp_path):
    source = tmp_path / "data" / "vocabulary.tsv"
    source.parent.mkdir()
    source.write_text(
        "id\tenglish\tindonesian\tmalaysian\trelation\timage\ttags\tcontrast\n"
        "000001\tspoon\tsendok\tsudu\tdifferent-common-word\t\tfood\t\n",
        encoding="utf-8",
    )
    before = source.read_bytes()
    prior = init_batch(tmp_path, "prior-001", "food", 2)
    prior.save_candidate(
        "earlier-01",
        {
            "candidate_id": "earlier-01",
            "english": "eating spoon",
            "indonesian": "sendok",
            "malaysian": "sudu",
            "sense": "utensil for eating",
        },
    )
    prior.append_event(
        "earlier-01",
        {"role": "explicit-final", "decision": {"outcome": "hold", "reason": "source gap"}},
    )
    prior.save_candidate(
        "earlier-02",
        {
            "candidate_id": "earlier-02",
            "english": "eating utensil",
            "indonesian": "sendok",
            "malaysian": "sudu",
            "sense": "handheld utensil for eating",
        },
    )
    prior.append_event(
        "earlier-02",
        {"role": "explicit-final", "decision": {"outcome": "rejected", "reason": "duplicate"}},
    )
    later = init_batch(tmp_path, "later-001", "food", 1)
    generation_archive = packet_for(later, "generate")["context"][
        "previously_investigated_concepts"
    ]
    assert {"000001", "prior-001:earlier-01", "prior-001:earlier-02"}.issubset(
        {item["reference"] for item in generation_archive}
    )
    assert all(
        set(item) == {"reference", "english", "indonesian", "malaysian"}
        for item in generation_archive
    )
    proposal = {
        "candidate_id": "repeat-01",
        "english": "spoons",
        "indonesian": "sendok",
        "malaysian": "sudu",
        "sense": "utensils for eating",
    }
    ingest_response(later, "generate", response("generate", {"candidates": [proposal]}))
    packet = packet_for(later, "normalize-and-dedupe", "repeat-01")
    archive_ids = {
        item.get("candidate_id") or item.get("id") for item in packet["context"]["archive"]
    }
    assert {"000001", "prior-001:earlier-01", "prior-001:earlier-02"}.issubset(archive_ids)
    warned_ids = {item["other_id"] for item in packet["context"]["deterministic_overlaps"]}
    assert {"000001", "prior-001:earlier-01", "prior-001:earlier-02"}.issubset(warned_ids)
    ingest_response(
        later,
        "normalize-and-dedupe",
        response(
            "normalize-and-dedupe",
            {
                "overlaps": [
                    {
                        "other_id": "000001",
                        "type": "semantic",
                        "resolution": "merge",
                        "rationale": "Same utensil concept despite plural English cue",
                    }
                ]
            },
        ),
        "repeat-01",
    )
    assert check_candidate(later, "repeat-01")["outcome"] == "rejected"
    assert batch_report(later)["status"] == "closed"
    assert source.read_bytes() == before
    assert not (tmp_path / "curation" / "id-ledger.json").exists()


def test_same_english_label_can_be_explicitly_resolved_as_distinct_sense(tmp_path):
    source = tmp_path / "data" / "vocabulary.tsv"
    source.parent.mkdir()
    source.write_text(
        "id\tenglish\tindonesian\tmalaysian\trelation\timage\ttags\tcontrast\n"
        "000001\tbank (financial institution)\tbank\tbank\tsame\t\tfinance\t\n",
        encoding="utf-8",
    )
    store = init_batch(tmp_path, "river-001", "nature", 1)
    proposal = {
        "candidate_id": "river-bank-01",
        "english": "bank (river edge)",
        "indonesian": "tepi sungai",
        "malaysian": "tebing sungai",
        "sense": "land bordering a river",
    }
    ingest_response(store, "generate", response("generate", {"candidates": [proposal]}))
    packet = packet_for(store, "normalize-and-dedupe", "river-bank-01")
    assert any(item["id"] == "000001" for item in packet["context"]["archive"])
    ingest_response(
        store,
        "normalize-and-dedupe",
        response(
            "normalize-and-dedupe",
            {
                "overlaps": [
                    {
                        "other_id": "000001",
                        "type": "semantic",
                        "resolution": "distinct",
                        "rationale": "Financial institution and river edge are separate senses",
                    }
                ]
            },
        ),
        "river-bank-01",
    )
    assert check_candidate(store, "river-bank-01")["outcome"] == "pending"
    assert source.read_text(encoding="utf-8").count("\n") == 2
    assert not (tmp_path / "curation" / "id-ledger.json").exists()


def test_generation_index_and_prompt_version_remain_frozen(tmp_path):
    config = tmp_path / "curation" / "config.json"
    config.parent.mkdir()
    config.write_text('{"prompt_set_version":"1.0.0"}', encoding="utf-8")
    prior = init_batch(tmp_path, "prior-001", "home", 2)
    prior.save_candidate(
        "prior-01",
        {
            "candidate_id": "prior-01",
            "english": "refrigerator",
            "indonesian": "kulkas",
            "malaysian": "peti sejuk",
            "sense": "a food-cooling appliance",
        },
    )
    later = init_batch(tmp_path, "later-001", "home", 2)
    original = packet_for(later, "generate")
    assert original["prompt_set_version"] == "1.0.0"
    assert "prior-001:prior-01" in {
        item["reference"] for item in original["context"]["previously_investigated_concepts"]
    }
    prior.save_candidate(
        "prior-02",
        {
            "candidate_id": "prior-02",
            "english": "lamp",
            "indonesian": "lampu",
            "malaysian": "lampu",
            "sense": "a light source",
        },
    )
    config.write_text('{"prompt_set_version":"1.1.0"}', encoding="utf-8")
    assert packet_for(later, "generate") == original
    future = init_batch(tmp_path, "future-001", "home", 2)
    future_packet = packet_for(future, "generate")
    assert future_packet["prompt_set_version"] == "1.1.0"
    assert "prior-001:prior-02" in {
        item["reference"] for item in future_packet["context"]["previously_investigated_concepts"]
    }
