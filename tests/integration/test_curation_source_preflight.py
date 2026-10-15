"""Source-first packets prevent expensive locale calls before inspected leads exist."""

import json

import pytest

from indo_malay_anki.curation.records import RecordError
from indo_malay_anki.curation.workflow import (
    current_results,
    ingest_response,
    init_batch,
    packet_for,
)


def response(role, result):
    return json.dumps({"schema_version": 1, "role": role, "model": "fixture", "result": result})


def source(locale, group):
    return {
        "locale": locale,
        "source_group": group,
        "publisher": group,
        "url_or_query": f"https://{group}.example/entry",
        "accessed_at": "2026-10-04T10:00:00Z",
        "access_method": "retrieved-page",
        "page_location_or_query": "entry paragraph",
        "source_kind": "dictionary",
        "observation": "The page defines the intended food sense.",
        "limitations": "A dictionary does not prove everyday preference.",
    }


def test_new_locale_packets_require_independent_inspected_sources(tmp_path):
    config = tmp_path / "curation" / "config.json"
    config.parent.mkdir()
    config.write_text(
        '{"prompt_set_version":"1.5.0","decision_policy_version":"2.0.0"}',
        encoding="utf-8",
    )
    store = init_batch(tmp_path, "food-001", "food", 1)
    assert store.manifest().prompt_set_version == "1.5.0"
    candidate = {
        "candidate_id": "food-01",
        "english": "corn",
        "indonesian": "jagung",
        "malaysian": "jagung",
        "sense": "edible maize kernels",
    }
    ingest_response(store, "generate", response("generate", {"candidates": [candidate]}))
    ingest_response(
        store,
        "normalize-and-dedupe",
        response("normalize-and-dedupe", {"overlaps": []}),
        "food-01",
    )
    with pytest.raises(RecordError, match="source preflight is required"):
        packet_for(store, "indonesian-usage", "food-01")

    path = store.path / "source-inspections" / "food-01.json"
    path.parent.mkdir()
    data = {
        "schema_version": 1,
        "recorded_at": "2026-10-04T10:00:00Z",
        "sources": [source("Indonesia", "shared"), source("Malaysia", "shared")],
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RecordError, match="two independent source groups"):
        packet_for(store, "indonesian-usage", "food-01")

    data["sources"][1] = source("Malaysia", "separate")
    path.write_text(json.dumps(data), encoding="utf-8")
    indonesian = packet_for(store, "indonesian-usage", "food-01")
    malaysian = packet_for(store, "malaysian-usage", "food-01")
    assert [item["locale"] for item in indonesian["context"]["source_inspections"]] == ["Indonesia"]
    assert [item["locale"] for item in malaysian["context"]["source_inspections"]] == ["Malaysia"]
    ingest_response(
        store,
        "indonesian-usage",
        response(
            "indonesian-usage",
            {
                "meaning": "edible maize",
                "common_use": "used in food",
                "preferred": "not established",
                "register": "neutral",
                "region": "Indonesia",
                "alternatives": [],
                "claims": [
                    {
                        "claim_id": "meaning",
                        "claim_type": "meaning",
                        "proposition": "jagung means corn",
                        "locale": "Indonesia",
                    }
                ],
            },
        ),
        "food-01",
    )
    assert "indonesian-usage" in current_results(store, "food-01")
    data["sources"][0]["observation"] = "The inspected page describes the plant only."
    path.write_text(json.dumps(data), encoding="utf-8")
    assert "indonesian-usage" not in current_results(store, "food-01")
