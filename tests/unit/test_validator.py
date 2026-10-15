import pytest

from indo_malay_anki.model import ValidatedVocabulary
from indo_malay_anki.validator import ValidationError, validate_vocabulary


def source_for(root, lines):
    source = root / "data" / "vocabulary.tsv"
    source.parent.mkdir(parents=True, exist_ok=True)
    converted = []
    for line in lines.splitlines():
        fields = line.split("\t")
        if len(fields) == 6:
            relation = "same" if fields[2] == fields[3] else "different-common-word"
            fields = [*fields[:4], relation, *fields[4:], ""]
        converted.append("\t".join(fields))
    source.write_text(
        "id\tenglish\tindonesian\tmalaysian\trelation\timage\ttags\tcontrast\n"
        + "\n".join(converted)
        + "\n",
        encoding="utf-8",
    )
    (root / "media").mkdir(exist_ok=True)
    return source


@pytest.mark.parametrize(
    ("line", "field"),
    [
        ("\tcar\tmobil\tkereta\t\t\n", "id"),
        ("000001\t\tmobil\tkereta\t\t\n", "english"),
        ("000001\tcar\t\tkereta\t\t\n", "indonesian"),
        ("000001\tcar\tmobil\t\t\t\n", "malaysian"),
    ],
)
def test_rejects_missing_required_values_with_row_field_context(tmp_path, line, field):
    source = source_for(tmp_path, line)
    with pytest.raises(ValidationError) as error:
        validate_vocabulary(source, tmp_path / "media")
    issue = error.value.issues[0]
    assert issue.row == 2
    assert issue.field == field


def test_rejects_duplicate_ids(tmp_path):
    source = source_for(
        tmp_path,
        "000001\tcar\tmobil\tkereta\t\t\n000001\tauto\tmobil\tkereta\t\t\n",
    )
    with pytest.raises(ValidationError) as error:
        validate_vocabulary(source, tmp_path / "media")
    assert any(issue.code == "duplicate_id" and issue.row == 3 for issue in error.value.issues)


def test_rejects_shared_vocabulary_from_contrast_deck(tmp_path):
    source = source_for(tmp_path, "000001\twater\tair\tair\tsame\t\t\t")
    with pytest.raises(ValidationError) as error:
        validate_vocabulary(source, tmp_path / "media")
    assert any(issue.code == "no_cross_language_difference" for issue in error.value.issues)


def test_rejects_shared_vocabulary_mislabeled_as_similar(tmp_path):
    source = source_for(tmp_path, "000001\twater\tair\tAIR\tsimilar\t\t\t")
    with pytest.raises(ValidationError) as error:
        validate_vocabulary(source, tmp_path / "media")
    assert any(issue.code == "no_cross_language_difference" for issue in error.value.issues)


@pytest.mark.parametrize("concept_id", ["1", "0000001", "０００００１", "ABC001"])
def test_rejects_invalid_ids(tmp_path, concept_id):
    source = source_for(tmp_path, f"{concept_id}\tcar\tmobil\tkereta\t\t\n")
    with pytest.raises(ValidationError):
        validate_vocabulary(source, tmp_path / "media")


@pytest.mark.parametrize("value", [" car", "car ", " mobil", "kereta "])
def test_rejects_outer_whitespace_without_rewriting(tmp_path, value):
    source = source_for(tmp_path, f"000001\t{value}\tmobil\tkereta\t\t\n")
    with pytest.raises(ValidationError) as error:
        validate_vocabulary(source, tmp_path / "media")
    assert any(issue.code == "outer_whitespace" for issue in error.value.issues)


def test_accepts_safe_nested_image_and_repeated_same_file(tmp_path):
    (tmp_path / "media" / "places").mkdir(parents=True)
    (tmp_path / "media" / "places" / "car.jpg").write_bytes(b"fake-image")
    source = source_for(
        tmp_path,
        "000001\tcar\tmobil\tkereta\tplaces/car.jpg\t\n"
        "000002\tauto\tmobil\tkereta\tplaces/car.jpg\t\n",
    )
    result = validate_vocabulary(source, tmp_path / "media")
    assert isinstance(result, ValidatedVocabulary)
    assert len(result.media) == 1


@pytest.mark.parametrize(
    "reference",
    [
        "https://example.test/car.jpg",
        "http://[broken",
        "/etc/passwd",
        "../outside.jpg",
        "folder\\car.jpg",
        "missing.jpg",
        "folder//car.jpg",
        "./car.jpg",
        "folder/./car.jpg",
    ],
)
def test_rejects_missing_remote_absolute_or_escaping_media(tmp_path, reference):
    source = source_for(tmp_path, f"000001\tcar\tmobil\tkereta\t{reference}\t\n")
    with pytest.raises(ValidationError):
        validate_vocabulary(source, tmp_path / "media")


def test_rejects_directory_and_symlink_escape(tmp_path):
    (tmp_path / "media" / "folder").mkdir(parents=True)
    (tmp_path / "outside.jpg").write_bytes(b"image")
    outside_link = tmp_path / "media" / "outside.jpg"
    try:
        outside_link.symlink_to(tmp_path / "outside.jpg")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable")
    for reference in ("folder", "outside.jpg"):
        source = source_for(tmp_path, f"000001\tcar\tmobil\tkereta\t{reference}\t\n")
        with pytest.raises(ValidationError):
            validate_vocabulary(source, tmp_path / "media")


def test_casefold_basename_collision_reports_every_reference(tmp_path):
    media = tmp_path / "media"
    (media / "a").mkdir(parents=True)
    (media / "b").mkdir()
    (media / "a" / "Straße.png").write_bytes(b"one")
    (media / "b" / "STRASSE.PNG").write_bytes(b"two")
    source = source_for(
        tmp_path,
        "000001\tcar\tmobil\tkereta\ta/Straße.png\t\n"
        "000002\tauto\tmobil\tkereta\tb/STRASSE.PNG\t\n",
    )
    with pytest.raises(ValidationError) as error:
        validate_vocabulary(source, media)
    conflicts = [issue for issue in error.value.issues if issue.code == "media_basename_collision"]
    assert len(conflicts) == 2
    assert {issue.row for issue in conflicts} == {2, 3}


def test_aggregates_independent_row_and_media_issues(tmp_path):
    source = source_for(
        tmp_path,
        "000001\t car\t\tkereta\tmissing.png\t\n"
        "000002\tauto\tmobil\tkereta\t\t\n"
        "000003\ttoo\tfew\n",
    )
    with pytest.raises(ValidationError) as error:
        validate_vocabulary(source, tmp_path / "media")
    codes = {issue.code for issue in error.value.issues}
    assert {"outer_whitespace", "missing_required", "missing_media", "malformed_row"} <= codes
    assert {issue.row for issue in error.value.issues} >= {2, 4}


def test_reports_all_three_references_in_a_casefold_collision(tmp_path):
    media = tmp_path / "media"
    for folder, name, data in (
        ("a", "Straße.png", b"one"),
        ("b", "STRASSE.PNG", b"two"),
        ("c", "strasse.Png", b"three"),
    ):
        (media / folder).mkdir(parents=True)
        (media / folder / name).write_bytes(data)
    source = source_for(
        tmp_path,
        "000001\tcar\tmobil\tkereta\ta/Straße.png\t\n"
        "000002\tauto\tmobil\tkereta\tb/STRASSE.PNG\t\n"
        "000003\tvehicle\tkendaraan\tkenderaan\tc/strasse.Png\t\n",
    )
    with pytest.raises(ValidationError) as error:
        validate_vocabulary(source, media)
    conflicts = [issue for issue in error.value.issues if issue.code == "media_basename_collision"]
    assert {issue.row for issue in conflicts} == {2, 3, 4}


def test_duplicate_diagnostics_are_emitted_once_per_affected_row(tmp_path):
    source = source_for(
        tmp_path,
        "000001\tcar\tmobil\tkereta\t\t\n"
        "000001\tauto\tmobil\tkereta\t\t\n"
        "000001\tvehicle\tkendaraan\tkenderaan\t\t\n",
    )
    with pytest.raises(ValidationError) as error:
        validate_vocabulary(source, tmp_path / "media")
    duplicates = [issue for issue in error.value.issues if issue.code == "duplicate_id"]
    assert [issue.row for issue in duplicates] == [3, 4]
    keys = [(issue.code, issue.row, issue.field, issue.message) for issue in error.value.issues]
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize(
    ("relation", "contrast", "expected"),
    [
        ("unknown", "", "invalid_relation"),
        ("false-friend", "", "missing_contrast"),
        ("same", "Misleading form means something else", "unexpected_contrast"),
    ],
)
def test_relation_and_contrast_are_validated_before_build(tmp_path, relation, contrast, expected):
    source = tmp_path / "data" / "vocabulary.tsv"
    source.parent.mkdir()
    source.write_text(
        "id\tenglish\tindonesian\tmalaysian\trelation\timage\ttags\tcontrast\n"
        f"000001\tcar\tmobil\tkereta\t{relation}\t\ttransport\t{contrast}\n",
        encoding="utf-8",
    )
    (tmp_path / "media").mkdir()
    with pytest.raises(ValidationError) as error:
        validate_vocabulary(source, tmp_path / "media")
    assert any(issue.code == expected and issue.row == 2 for issue in error.value.issues)
