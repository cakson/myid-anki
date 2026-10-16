from __future__ import annotations

import json

from indo_malay_anki.scaling.__main__ import main


def test_create_status_report_and_reissue(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert (
        main(["create", "--run", "first-run", "--count", "2", "--proposal-cap", "4", "--json"]) == 0
    )
    created = json.loads(capsys.readouterr().out)
    assert created["run_id"] == "first-run"
    assert created["state"] == "draft"
    assert (
        main(["create", "--run", "first-run", "--count", "2", "--proposal-cap", "4", "--json"]) == 0
    )
    assert json.loads(capsys.readouterr().out)["run_id"] == "first-run"
    assert main(["status", "--run", "first-run", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "draft"
    assert main(["report", "--run", "first-run", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["requested_count"] == 2


def test_conflicting_reissue_and_missing_run_return_nonzero(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["create", "--run", "first-run", "--count", "2", "--proposal-cap", "4"]) == 0
    capsys.readouterr()
    assert main(["create", "--run", "first-run", "--count", "3", "--proposal-cap", "4"]) != 0
    assert "conflicting" in capsys.readouterr().err
    assert main(["status", "--run", "absent"]) != 0
    assert "absent" in capsys.readouterr().err


def test_allocation_draft_and_approval_freeze(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["create", "--run", "first-run", "--count", "20", "--json"]) == 0
    created = json.loads(capsys.readouterr().out)
    assert sum(created["allocation_draft"].values()) == 20
    assert main(["allocation", "--run", "first-run", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["draft"] == created["allocation_draft"]
    assert main(["approve", "--run", "first-run", "--reason", "reviewed", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "allocation-approved"
    assert main(["allocation", "--run", "first-run", "--set", "home=1"]) != 0
