import json

import pytest

from indo_malay_anki.scaling.prompt_transport import compact_overlap_prompt


def test_compact_overlap_transport_preserves_semantic_inventory_and_packet_digest():
    packet = {
        "batch_id": "slice-1",
        "candidate_id": "new-1",
        "role": "normalize-and-dedupe",
        "prompt_set_version": "2.4.0",
        "prompt": "Frozen reviewer instruction",
        "input_digest": "authoritative-digest",
        "context": {
            "topic": "everyday vocabulary",
            "scope": "Indonesia and Malaysia",
            "candidate": {
                "candidate_id": "new-1",
                "english": "child's school",
                "indonesian": "taman kanak-kanak",
                "malaysian": "tadika",
                "sense": "a school before primary education",
                "tags": ["education"],
            },
            "deterministic_overlaps": [{"other_id": "old-1", "resolution": "unresolved"}],
            "archive": [
                {
                    "candidate_id": "old-1",
                    "english": "school",
                    "indonesian": "sekolah",
                    "malaysian": "sekolah",
                    "sense": "an institution for education",
                    "tags": ["education"],
                },
                {
                    "id": "000137",
                    "english": "preschool",
                    "indonesian": "prasekolah",
                    "malaysian": "prasekolah",
                },
            ],
        },
    }
    original = json.loads(json.dumps(packet))
    prompt = compact_overlap_prompt(packet)
    instruction, encoded = prompt.split("\nCURATION_PACKET_COMPACT_JSON\n", 1)
    data = json.loads(encoded)
    assert instruction == packet["prompt"]
    assert data["input_digest"] == packet["input_digest"]
    assert data["candidate"] == packet["context"]["candidate"]
    assert data["deterministic_overlaps"] == packet["context"]["deterministic_overlaps"]
    assert [
        dict(zip(data["archive_columns"], row, strict=True)) for row in data["archive_rows"]
    ] == [
        {
            "id": "old-1",
            "english": "school",
            "indonesian": "sekolah",
            "malaysian": "sekolah",
            "sense": "an institution for education",
            "tags": ["education"],
        },
        {
            "id": "000137",
            "english": "preschool",
            "indonesian": "prasekolah",
            "malaysian": "prasekolah",
            "sense": "",
            "tags": [],
        },
    ]
    assert packet == original
    assert prompt.count(packet["prompt"]) == 1


def test_compact_overlap_transport_rejects_other_stage():
    with pytest.raises(ValueError, match="normalize-and-dedupe"):
        compact_overlap_prompt({"role": "independent-verification"})
