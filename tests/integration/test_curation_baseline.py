"""Historical counts come from archives without rewriting them or treating idle time as runtime."""

import csv
from pathlib import Path

from indo_malay_anki.curation.baseline import historical_baseline

ROOT = Path(__file__).resolve().parents[2]


def test_baseline_separates_fixture_and_current_policy_replay_without_mutation():
    report = ROOT / "curation" / "batches" / "home-001" / "report.json"
    manifest = ROOT / "curation" / "batches" / "home-001" / "manifest.json"
    before = (report.read_bytes(), manifest.read_bytes())
    result = historical_baseline(ROOT)
    assert result["non_fixture_batches"] == 14
    assert result["fixture_batches"] == 1
    assert result["historical_archived"] == {
        "accepted": 6,
        "generated": 102,
        "held": 87,
        "pending": 0,
        "rejected": 9,
    }
    assert result["current_policy_replay"] == {
        "generated": 102,
        "accepted": 3,
        "held": 87,
        "rejected": 12,
        "pending": 0,
    }
    assert result["fixture"]["generated"] == 1
    with (ROOT / "data" / "vocabulary.tsv").open(encoding="utf-8", newline="") as stream:
        active_rows = list(csv.DictReader(stream, delimiter="\t"))
    assert result["active_learner_cards"] == len(active_rows)
    assert result["active_time_seconds"] is None
    assert result["provider_calls"] is None
    assert (report.read_bytes(), manifest.read_bytes()) == before
