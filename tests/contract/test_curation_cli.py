"""Curation commands preserve stage isolation and batch boundaries."""

import json

from indo_malay_anki.curation.__main__ import main


def test_init_packet_and_pending_report(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--batch", "travel-001", "--topic", "travel", "--limit", "2"]) == 0
    assert main(["packet", "--batch", "travel-001", "--role", "generate"]) == 0
    packet = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert packet["role"] == "generate"
    assert packet["candidate_limit"] == 2
    assert main(["report", "--batch", "travel-001"]) == 0
    report = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert report["generated"] == 0


def test_malformed_ai_response_cannot_become_accepted(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--batch", "travel-001", "--topic", "travel", "--limit", "2"]) == 0
    bad = tmp_path / "bad.json"
    bad.write_text('{"role":"generate","result":"free prose"}', encoding="utf-8")
    assert (
        main(["ingest", "--batch", "travel-001", "--role", "generate", "--response", str(bad)]) == 1
    )
    assert main(["check", "--batch", "travel-001"]) == 0
    assert "Traceback" not in capsys.readouterr().err


def test_verifier_packet_excludes_generator_rationale(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--batch", "travel-001", "--topic", "travel", "--limit", "2"]) == 0
    assert (
        main(
            [
                "packet",
                "--batch",
                "travel-001",
                "--role",
                "independent-verification",
                "--candidate",
                "car-01",
            ]
        )
        == 1
    )
    assert "Traceback" not in capsys.readouterr().err


def test_ingest_records_invoked_model_separately_from_ai_claim(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--batch", "travel-001", "--topic", "travel", "--limit", "1"]) == 0
    answer = tmp_path / "answer.json"
    answer.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "role": "generate",
                "model": "generic AI",
                "result": {
                    "candidates": [
                        {
                            "candidate_id": "car-01",
                            "english": "car",
                            "indonesian": "mobil",
                            "malaysian": "kereta",
                            "sense": "passenger vehicle",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    assert (
        main(
            [
                "ingest",
                "--batch",
                "travel-001",
                "--role",
                "generate",
                "--response",
                str(answer),
                "--actual-model",
                "gpt-6-luna/codex-cli",
            ]
        )
        == 0
    )
    event = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert event["model"] == "gpt-6-luna/codex-cli"
    assert event["reported_model"] == "generic AI"
