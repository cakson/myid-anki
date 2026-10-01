import subprocess
import sys

from indo_malay_anki.cli import main


def test_validate_success_reports_counts_without_creating_dist(repo_factory):
    root = repo_factory()
    (root / "dist").rmdir()
    result = subprocess.run(
        [sys.executable, "-m", "indo_malay_anki", "validate"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "1 concept" in result.stdout
    assert not (root / "dist").exists()
    assert result.stderr == ""


def test_validate_failure_reports_row_and_field_and_returns_one(repo_factory):
    root = repo_factory(rows=(("000001", "", "mobil", "kereta", "", ""),))
    (root / "dist").rmdir()
    result = subprocess.run(
        [sys.executable, "-m", "indo_malay_anki", "validate"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "2" in result.stderr and "english" in result.stderr
    assert not (root / "dist").exists()


def test_malformed_image_url_is_reported_without_traceback(repo_factory):
    root = repo_factory(rows=(("000001", "car", "mobil", "kereta", "http://[broken", ""),))
    result = subprocess.run(
        [sys.executable, "-m", "indo_malay_anki", "validate"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "2" in result.stderr and "000001" in result.stderr and "image" in result.stderr


def test_help_and_unknown_commands_use_expected_exit_codes():
    help_result = subprocess.run(
        [sys.executable, "-m", "indo_malay_anki", "--help"], capture_output=True, text=True
    )
    bad_result = subprocess.run(
        [sys.executable, "-m", "indo_malay_anki", "unknown"], capture_output=True, text=True
    )
    assert help_result.returncode == 0
    assert bad_result.returncode == 2


def test_validate_aggregates_diagnostics_without_traceback(repo_factory, monkeypatch, capsys):
    root = repo_factory(
        rows=(
            ("000001", " car", "", "kereta", "missing.png", ""),
            ("000002", "auto", "mobil", "kereta", "", ""),
        )
    )
    monkeypatch.chdir(root)
    assert main(["validate"]) == 1
    result = capsys.readouterr()
    assert "Traceback" not in result.err
    assert "outer_whitespace" not in result.err
    assert "english" in result.err and "indonesian" in result.err and "missing.png" in result.err
    assert result.out == ""


def test_validate_diagnostic_order_is_stable(repo_factory, monkeypatch, capsys):
    root = repo_factory(
        rows=(
            ("000001", " car", "", "kereta", "missing.png", ""),
            ("000001", "auto", "mobil", "kereta", "", ""),
        )
    )
    monkeypatch.chdir(root)
    assert main(["validate"]) == 1
    first = capsys.readouterr().err
    assert main(["validate"]) == 1
    second = capsys.readouterr().err
    assert first == second
