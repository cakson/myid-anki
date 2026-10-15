from pathlib import Path

README = Path(__file__).resolve().parents[2] / "README.md"


def test_readme_documents_local_workflow_and_source_contract():
    text = README.read_text(encoding="utf-8").lower()
    for expected in (
        "python 3.12",
        "conda",
        "python -m indo_malay_anki validate",
        "python -m indo_malay_anki build",
        "dist/myid-anki.apkg",
        "english",
        "indonesian",
        "malaysian",
        "image",
        "tags",
        "000001",
        "permanent",
        "reviewed",
        "offline",
        "bahasa indonesia",
        "bahasa melayu",
        "remov",
        "reintroduc",
    ):
        assert expected in text


def test_readme_documents_card_direction_update_behavior_and_not_editing_packages():
    text = README.read_text(encoding="utf-8").lower()
    assert "one note" in text and "one card" in text
    assert "neutral" in text and "front" in text and "back" in text
    assert "duplicate" in text and "guid" in text
    assert "modification" in text or "newer" in text
    assert "edit" in text and ".apkg" in text


def test_readme_documents_eight_column_accepted_source_and_curation_gate():
    text = README.read_text(encoding="utf-8").lower()
    assert "id\tenglish\tindonesian\tmalaysian\trelation\timage\ttags\tcontrast" in text
    for expected in (
        "ai-first",
        "independent verification",
        "adversarial",
        "dictionary",
        "everyday",
        "false friend",
        "hold",
        "reject",
        "closed batch",
        "random or stratified",
        "guarded promotion",
        "offline",
    ):
        assert expected in text
    assert "000001" in text and "retired" in text
