import pytest

from indo_malay_anki.loader import SourceFormatError, load_tsv


def write_source(path, contents):
    path.write_text(contents, encoding="utf-8", newline="")
    return path


def test_loads_valid_utf8_tsv_and_preserves_id_string(tmp_path):
    source = write_source(
        tmp_path / "vocabulary.tsv",
        "id\tenglish\tindonesian\tmalaysian\timage\ttags\n"
        "000001\tcar\tmobil\tkereta\t\ttransport daily-life\n",
    )
    concept = load_tsv(source)[0]
    assert concept.id == "000001"
    assert concept.tags == ["transport", "daily-life"]
    assert concept.image is None


@pytest.mark.parametrize(
    "contents",
    [
        "",
        "id\tenglish\tindonesian\tmalaysian\timage\ttags\n",
        "id\tenglish\tindonesian\tmalaysian\timage\ttags\n000001\tcar\n",
        "id\tenglish\tindonesian\tmalaysian\timage\ttags\n000001\tcar\tmobil\tkereta\t\t\textra\n",
        "id\tenglish\tindonesian\tmalaysian\timage\ttags\n\n",
    ],
)
def test_rejects_empty_or_malformed_tsv(tmp_path, contents):
    source = write_source(tmp_path / "vocabulary.tsv", contents)
    with pytest.raises(SourceFormatError):
        load_tsv(source)


def test_rejects_wrong_header_order(tmp_path):
    source = write_source(
        tmp_path / "vocabulary.tsv",
        "english\tid\tindonesian\tmalaysian\timage\ttags\n",
    )
    with pytest.raises(SourceFormatError):
        load_tsv(source)


def test_rejects_repeated_header(tmp_path):
    source = write_source(
        tmp_path / "vocabulary.tsv",
        "id\tenglish\tindonesian\tmalaysian\timage\ttags\n"
        "id\tenglish\tindonesian\tmalaysian\timage\ttags\n",
    )
    with pytest.raises(SourceFormatError) as error:
        load_tsv(source)
    assert error.value.issues[0].code == "repeated_header"


def test_rejects_invalid_utf8(tmp_path):
    source = tmp_path / "vocabulary.tsv"
    source.write_bytes(b"id\tenglish\tindonesian\tmalaysian\timage\ttags\n\xff")
    with pytest.raises(SourceFormatError):
        load_tsv(source)


def test_rejects_strict_csv_syntax_errors(tmp_path):
    source = write_source(
        tmp_path / "vocabulary.tsv",
        'id\tenglish\tindonesian\tmalaysian\timage\ttags\n000001\t"car\tmobil\tkereta\t\t\n',
    )
    with pytest.raises(SourceFormatError):
        load_tsv(source)
