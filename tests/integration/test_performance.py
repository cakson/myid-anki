"""Local performance acceptance; the recorded measurement includes the runtime and host details."""

import time


def test_validate_and_build_1000_concepts_under_60_seconds(
    repo_factory, monkeypatch, record_property
):
    from indo_malay_anki.cli import main

    rows = tuple(
        (f"{number:06d}", f"cue {number}", f"kata {number}", f"perkataan {number}", "", "test")
        for number in range(1, 1001)
    )
    root = repo_factory(rows=rows)
    monkeypatch.chdir(root)
    started = time.perf_counter()
    assert main(["validate"]) == 0
    assert main(["build"]) == 0
    elapsed = time.perf_counter() - started
    record_property("elapsed_seconds", f"{elapsed:.3f}")
    assert elapsed < 60
