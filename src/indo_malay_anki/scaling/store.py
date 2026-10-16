"""Durable parent-run manifest, events, locks, and replay checkpoints."""

from __future__ import annotations

import fcntl
import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from indo_malay_anki.curation.records import RecordError, safe_id
from indo_malay_anki.curation.store import atomic_json, read_json

from . import WORKFLOW_VERSION


class RunError(ValueError):
    """An invalid production-run state or conflicting replay."""


def digest(value: Any) -> str:
    """Stable digest of a JSON-compatible value."""
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class RunStore:
    def __init__(self, root: Path, run_id: str):
        try:
            self.run_id = safe_id(run_id, "run_id")
        except RecordError as exc:
            raise RunError(str(exc)) from exc
        self.root = Path(root)
        self.path = self.root / "curation" / "production-runs" / self.run_id

    @property
    def manifest_path(self) -> Path:
        return self.path / "manifest.json"

    @contextmanager
    def lock(self) -> Iterator[None]:
        if not self.path.is_dir():
            raise RunError(f"run does not exist: {self.run_id}")
        with (self.path / ".run.lock").open("a+b") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    @contextmanager
    def operation_lock(self) -> Iterator[None]:
        """Serialize complete mutating CLI operations, including external calls."""
        if not self.path.is_dir():
            raise RunError(f"run does not exist: {self.run_id}")
        with (self.path / ".operation.lock").open("a+b") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def create(self, *, requested_count: int, proposal_cap: int, baseline_count: int) -> dict:
        if type(requested_count) is not int or requested_count < 1:
            raise RunError("requested_count must be a positive integer")
        if type(proposal_cap) is not int or proposal_cap < requested_count:
            raise RunError("proposal_cap must be at least requested_count")
        if type(baseline_count) is not int or baseline_count < 0:
            raise RunError("baseline_count must be nonnegative")
        try:
            self.path.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise RunError(f"run already exists: {self.run_id}") from exc
        manifest = {
            "schema_version": 1,
            "workflow_version": WORKFLOW_VERSION,
            "run_id": self.run_id,
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "state": "draft",
            "prior_state": None,
            "requested_count": requested_count,
            "proposal_cap": proposal_cap,
            "baseline_count": baseline_count,
            "allocation_draft": {},
            "allocation": None,
            "allocation_digest": None,
            "baseline_source_digest": None,
            "slices": [],
            "admitted_count": 0,
            "qa": None,
            "brakes": [],
            "brake_thresholds": {
                "learner_critical_count": 2,
                "repeated_learner_critical_pattern_count": 2,
                "hold_rate": 0.30,
                "no_contrast_generation_rate": 0.30,
                "duplicate_generation_rate": 0.20,
                "minimum_observations": 20,
                "identity_export_inconsistency": "immediate",
            },
            "report_status": "provisional",
        }
        atomic_json(self.manifest_path, manifest)
        return manifest

    def load(self) -> dict:
        try:
            manifest = read_json(self.manifest_path)
        except RecordError as exc:
            raise RunError(str(exc)) from exc
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
            raise RunError("invalid production-run manifest")
        if manifest.get("run_id") != self.run_id:
            raise RunError("production-run manifest ID mismatch")
        if manifest.get("workflow_version") != WORKFLOW_VERSION:
            raise RunError("unsupported workflow version")
        if manifest.get("requested_count", 0) < 1:
            raise RunError("invalid requested_count")
        return manifest

    def manifest_digest(self) -> str:
        return file_digest(self.manifest_path)

    def save(self, manifest: dict, *, expected_digest: str | None = None) -> None:
        with self.lock():
            if expected_digest is not None and expected_digest != self.manifest_digest():
                raise RunError("conflicting manifest revision")
            if manifest.get("run_id") != self.run_id or manifest.get("schema_version") != 1:
                raise RunError("manifest identity/schema mismatch")
            atomic_json(self.manifest_path, {**manifest, "updated_at": utc_now()})

    def append_event(
        self,
        kind: str,
        status: str,
        *,
        input_digest: str | None = None,
        output_digest: str | None = None,
        output_path: str | None = None,
        details: dict | None = None,
    ) -> Path:
        folder = self.path / "events"
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / ".append.lock").open("a+b") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                prior = sorted(folder.glob("[0-9][0-9][0-9][0-9][0-9][0-9].json"))
                ordinal = int(prior[-1].stem) + 1 if prior else 1
                path = folder / f"{ordinal:06d}.json"
                atomic_json(
                    path,
                    {
                        "sequence": ordinal,
                        "kind": kind,
                        "status": status,
                        "input_digest": input_digest,
                        "output_digest": output_digest,
                        "output_path": output_path,
                        "details": details or {},
                        "at": utc_now(),
                    },
                )
                return path
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def events(self) -> tuple[dict, ...]:
        folder = self.path / "events"
        if not folder.exists():
            return ()
        return tuple(read_json(path) for path in sorted(folder.glob("[0-9]*.json")))

    def completed_checkpoint(
        self, kind: str, input_digest: str, output_digest: str | None = None
    ) -> dict | None:
        for event in reversed(self.events()):
            if (
                event["kind"] != kind
                or event["status"] != "complete"
                or event["input_digest"] != input_digest
            ):
                continue
            if output_digest is not None and event["output_digest"] != output_digest:
                continue
            if event["output_path"]:
                path = self.root / event["output_path"]
                if not path.exists() or file_digest(path) != event["output_digest"]:
                    continue
            return event
        return None

    def add_brake(self, reason: str, *, detail: str | None = None) -> dict:
        manifest = self.load()
        if any(item["reason"] == reason and item.get("active") for item in manifest["brakes"]):
            return manifest
        manifest["brakes"].append(
            {
                "reason": reason,
                "detail": detail,
                "active": True,
                "triggered_at": utc_now(),
            }
        )
        self.save(manifest, expected_digest=self.manifest_digest())
        self.append_event("safety-brake", "complete", details={"reason": reason, "detail": detail})
        return self.load()
