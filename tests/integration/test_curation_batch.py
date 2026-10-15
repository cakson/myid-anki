"""A complete scratch curation batch never mutates learner data."""

import json

from indo_malay_anki.curation.export import export_batches
from indo_malay_anki.curation.report import batch_report
from indo_malay_anki.curation.workflow import finalize_hold, ingest_response, init_batch


def send(store, role, result, candidate_id=None):
    response = {"schema_version": 1, "role": role, "model": f"fixture-{role}", "result": result}
    ingest_response(store, role, json.dumps(response), candidate_id)


def test_complete_batch_reconciles_accepted_hold_and_rejected_without_source_mutation(tmp_path):
    config = tmp_path / "curation" / "config.json"
    config.parent.mkdir()
    config.write_text(
        '{"prompt_set_version":"1.1.0","decision_policy_version":"2.0.0"}',
        encoding="utf-8",
    )
    source = tmp_path / "data" / "vocabulary.tsv"
    source.parent.mkdir()
    source.write_text(
        "id\tenglish\tindonesian\tmalaysian\timage\ttags\n"
        "000001\tcar\tmobil\tkereta\t\ttransport\n",
        encoding="utf-8",
    )
    original = source.read_bytes()
    store = init_batch(tmp_path, "home-001", "home", 3)
    proposals = [
        {
            "candidate_id": cid,
            "english": english,
            "indonesian": indonesian,
            "malaysian": malaysian,
            "sense": sense,
            "tags": ["home"],
        }
        for cid, english, indonesian, malaysian, sense in (
            ("house-01", "sauce", "saus", "sos", "condiment served with food"),
            ("tree-02", "tree", "pohon", "pokok", "woody plant"),
            ("airplane-03", "airplane", "pesawat", "kapal terbang", "flying vehicle"),
        )
    ]
    send(store, "generate", {"candidates": proposals})
    send(store, "normalize-and-dedupe", {"overlaps": []}, "house-01")
    claims = [
        {"claim_id": "id-meaning", "claim_type": "meaning", "proposition": "Indonesian sense"},
        {"claim_id": "my-meaning", "claim_type": "meaning", "proposition": "Malay sense"},
        {"claim_id": "relation", "claim_type": "relation", "proposition": "Similar forms"},
    ]
    for role, claim, locale in (
        ("indonesian-usage", claims[0], "Indonesia"),
        ("malaysian-usage", claims[1], "Malaysia"),
    ):
        send(
            store,
            role,
            {
                "meaning": "condiment served with food",
                "common_use": "common",
                "preferred": "everyday",
                "register": "neutral",
                "region": locale,
                "alternatives": [],
                "claims": [claim],
            },
            "house-01",
        )
    send(
        store,
        "relation-proposal",
        {
            "english": "sauce",
            "relation": "similar",
            "semantic_alignment": "same condiment sense",
            "aligned": True,
            "claims": [claims[2]],
        },
        "house-01",
    )
    observations = [
        {
            "evidence_id": f"{group}-{claim['claim_id']}",
            "claim_id": f"{role}:{claim['claim_id']}",
            "source_group": group,
            "source_title": group,
            "publisher": group,
            "url_or_query": f"https://{group}.test/house",
            "accessed_at": "2026-10-03T00:00:00Z",
            "observation": "Observed sauce sense",
            "page_location_or_query": "sauce entry",
            "audit_method": "retrieved-page",
            "stance": "supports",
            "claim_type": claim["claim_type"],
        }
        for group in ("source-a", "source-b")
        for role, claim in zip(
            ("indonesian-usage", "malaysian-usage", "relation-proposal"), claims, strict=True
        )
    ]
    send(store, "evidence-audit", {"observations": observations}, "house-01")
    send(
        store,
        "independent-verification",
        {
            "verdict": "agree",
            "relation": "similar",
            "concerns": [],
            "rationale": "Aligned evidence",
        },
        "house-01",
    )
    finalize_hold(store, "tree-02", "Insufficient source access")
    send(
        store,
        "normalize-and-dedupe",
        {
            "overlaps": [
                {
                    "other_id": "old-airplane",
                    "type": "semantic",
                    "resolution": "reject",
                    "rationale": "Confirmed duplicate concept",
                }
            ]
        },
        "airplane-03",
    )
    report = batch_report(store)
    assert (
        report["generated"],
        report["accepted"],
        report["held"],
        report["rejected"],
        report["pending"],
    ) == (3, 1, 1, 1, 0)
    assert report["status"] == "closed"
    assert report["outcomes_by_relation"] == {"similar": {"accepted": 1}}
    assert report["reason_code_distribution"]["confirmed-duplicate"] == 1
    assert report["corrections"] == 0
    assert source.read_bytes() == original
    ledger = tmp_path / "curation" / "id-ledger.json"
    ledger.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "assignments": [
                    {
                        "id": "000001",
                        "batch_id": "legacy-car-001",
                        "candidate_id": "car-01",
                        "assigned_at": "2026-10-02",
                        "semantic_concept_key": "road passenger vehicle",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert export_batches(tmp_path, ["home-001"]) == ["000002"]
    assert "000002\tsauce\tsaus\tsos\tsimilar" in source.read_text(encoding="utf-8")
    assert "000001" not in source.read_text(encoding="utf-8")
    assert export_batches(tmp_path, ["home-001"]) == ["000002"]
    assert len(json.loads(ledger.read_text(encoding="utf-8"))["assignments"]) == 2
