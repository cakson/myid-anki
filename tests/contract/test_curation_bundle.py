"""Batch role exchange validates all outputs before recording any of them."""

import json

import pytest

from indo_malay_anki.curation.bundle import ingest_bundle, packet_bundle
from indo_malay_anki.curation.records import RecordError
from indo_malay_anki.curation.workflow import ingest_response, init_batch


def test_role_bundle_has_separate_candidate_packets_and_atomic_validation(tmp_path):
    store = init_batch(tmp_path, "home-001", "home", 2)
    candidates = [
        {
            "candidate_id": candidate_id,
            "english": english,
            "indonesian": indonesian,
            "malaysian": malaysian,
            "sense": "a home object",
        }
        for candidate_id, english, indonesian, malaysian in (
            ("chair-01", "chair", "kursi", "kerusi"),
            ("table-02", "table", "meja", "meja"),
        )
    ]
    ingest_response(
        store,
        "generate",
        json.dumps(
            {
                "schema_version": 1,
                "role": "generate",
                "model": "fixture",
                "result": {"candidates": candidates},
            }
        ),
    )
    ids = [candidate["candidate_id"] for candidate in candidates]
    packet = packet_bundle(store, "normalize-and-dedupe", ids)
    assert [item["candidate_id"] for item in packet["items"]] == ids
    assert packet["prompt"].startswith("BUNDLE OUTPUT OVERRIDE")
    assert "Never report a candidate as overlapping itself" in packet["bundle_guidance"]
    assert all(
        item.get("candidate_id") not in {f"home-001:{candidate_id}" for candidate_id in ids}
        for item in packet["shared_archive"]
    )
    for item in packet["items"]:
        peers = item["context"]["peer_candidates"]
        assert {peer["candidate_id"] for peer in peers} == {
            f"home-001:{candidate_id}"
            for candidate_id in ids
            if candidate_id != item["candidate_id"]
        }
    response = tmp_path / "response.json"
    response.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "role": "normalize-and-dedupe",
                "model": "independent-role",
                "results": {ids[0]: {"overlaps": []}, ids[1]: {"overlaps": "bad"}},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RecordError):
        ingest_bundle(store, "normalize-and-dedupe", response, ids)
    assert not store.events(ids[0])
    data = json.loads(response.read_text(encoding="utf-8"))
    data["results"][ids[1]] = {
        "overlaps": [
            {
                "other_id": f"home-001:{ids[1]}",
                "type": "exact",
                "resolution": "merge",
                "rationale": "Accidental self-match",
            }
        ]
    }
    response.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RecordError, match="self-overlap"):
        ingest_bundle(store, "normalize-and-dedupe", response, ids)
    assert not store.events(ids[0]) and not store.events(ids[1])
    data["results"][ids[1]] = {"overlaps": []}
    response.write_text(json.dumps(data), encoding="utf-8")
    assert len(ingest_bundle(store, "normalize-and-dedupe", response, ids)) == 2
    assert all(store.events(candidate_id)[0]["status"] == "complete" for candidate_id in ids)
