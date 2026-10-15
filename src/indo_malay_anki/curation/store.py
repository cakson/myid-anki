"""Atomic, append-only batch and stage artifact persistence."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .records import BatchManifest, RecordError, safe_id


def atomic_json(path: Path, value: Any) -> None:
    """Replace one JSON artifact only after the complete new version is durable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecordError(f"Cannot read {path}: {exc}") from exc


@contextmanager
def _folder_lock(folder: Path):
    """Serialize sequence allocation across simultaneous role ingests."""
    with (folder / ".append.lock").open("a+b") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class BatchStore:
    def __init__(self, root: Path, batch_id: str):
        self.root = Path(root)
        self.batch_id = safe_id(batch_id, "batch_id")
        self.path = self.root / "curation" / "batches" / self.batch_id

    def create(self, manifest: BatchManifest) -> None:
        if manifest.batch_id != self.batch_id:
            raise RecordError("manifest batch_id does not match store")
        if self.path.exists():
            raise RecordError(f"batch already exists: {self.batch_id}")
        self.path.mkdir(parents=True)
        atomic_json(self.path / "manifest.json", manifest.as_dict())

    def manifest(self) -> BatchManifest:
        return BatchManifest.from_dict(read_json(self.path / "manifest.json"))

    def save_manifest(self, manifest: BatchManifest) -> None:
        if manifest.batch_id != self.batch_id:
            raise RecordError("manifest batch_id does not match store")
        atomic_json(self.path / "manifest.json", manifest.as_dict())

    def candidate_ids(self) -> tuple[str, ...]:
        folder = self.path / "candidates"
        if not folder.exists():
            return ()
        return tuple(sorted(path.name for path in folder.iterdir() if path.is_dir()))

    def candidate_path(self, candidate_id: str) -> Path:
        return self.path / "candidates" / safe_id(candidate_id, "candidate_id")

    def append_event(self, candidate_id: str, event: dict[str, Any]) -> Path:
        folder = self.candidate_path(candidate_id) / "events"
        return self._append_in_folder(folder, event)

    def append_batch_event(self, event: dict[str, Any]) -> Path:
        return self._append_in_folder(self.path / "batch-events", event)

    @staticmethod
    def _append_in_folder(folder: Path, event: dict[str, Any]) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        with _folder_lock(folder):
            existing = sorted(folder.glob("[0-9][0-9][0-9][0-9][0-9][0-9].json"))
            sequence = int(existing[-1].stem) + 1 if existing else 1
            path = folder / f"{sequence:06d}.json"
            atomic_json(path, event)
        return path

    def events(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return self._events_in_folder(self.candidate_path(candidate_id) / "events")

    def batch_events(self) -> tuple[dict[str, Any], ...]:
        return self._events_in_folder(self.path / "batch-events")

    @staticmethod
    def _events_in_folder(folder: Path) -> tuple[dict[str, Any], ...]:
        if not folder.exists():
            return ()
        events = tuple(read_json(path) for path in sorted(folder.glob("*.json")))
        if any(not isinstance(event, dict) for event in events):
            raise RecordError(f"invalid event in {folder}")
        return events

    def save_candidate(self, candidate_id: str, proposal: dict[str, Any]) -> None:
        path = self.candidate_path(candidate_id) / "proposal.json"
        if path.exists():
            raise RecordError(f"candidate already exists: {candidate_id}")
        atomic_json(path, proposal)

    def candidate(self, candidate_id: str) -> dict[str, Any]:
        value = read_json(self.candidate_path(candidate_id) / "proposal.json")
        if not isinstance(value, dict):
            raise RecordError("candidate proposal must be an object")
        revisions = [
            event
            for event in self.events(candidate_id)
            if event.get("role") == "proposal-revision" and event.get("status") == "complete"
        ]
        if revisions:
            value = revisions[-1]["result"]
        return value
