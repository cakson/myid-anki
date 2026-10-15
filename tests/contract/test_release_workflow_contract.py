"""Release builds consume accepted source without invoking curation or live research."""

from pathlib import Path


def test_release_workflow_stays_on_offline_source_build_path():
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "test ! -e curation/export-journal.json" in workflow
    assert "python -m indo_malay_anki validate" in workflow
    assert "python -m indo_malay_anki build" in workflow
    assert "python -m indo_malay_anki.curation" not in workflow
    assert "OPENAI_API_KEY" not in workflow and "ANTHROPIC_API_KEY" not in workflow
