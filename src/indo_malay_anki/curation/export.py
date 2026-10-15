"""Guarded promotion of accepted concepts into canonical learner source."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from indo_malay_anki.loader import HEADER
from indo_malay_anki.validator import validate_vocabulary

from .duplicates import find_deterministic_overlaps
from .gate import decide_candidate
from .ids import allocate_id, append_assignment, assigned_id, load_ledger, validate_ledger
from .records import RecordError
from .store import BatchStore, atomic_json, read_json
from .workflow import archive_candidates, current_results, utc_now


class ExportError(ValueError):
    """A batch cannot safely enter canonical learner data."""


def _sha(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cleanup(journal: Path, backups: list[Path]) -> None:
    for path in backups:
        path.unlink(missing_ok=True)
    journal.unlink(missing_ok=True)


def recover_export(root: Path) -> bool:
    """Finish a completed transaction or restore both prior files after interruption."""
    root = Path(root)
    journal_path = root / "curation" / "export-journal.json"
    if not journal_path.exists():
        return False
    try:
        journal = read_json(journal_path)
        if journal.get("schema_version") != 1:
            raise ExportError("invalid export journal version")
        source = root / "data" / "vocabulary.tsv"
        ledger = root / "curation" / "id-ledger.json"
        source_backup = root / "curation" / "source.backup"
        ledger_backup = root / "curation" / "ledger.backup"
        required = (
            "old_source_digest",
            "old_ledger_digest",
            "new_source_digest",
            "new_ledger_digest",
        )
        if any(key not in journal for key in required):
            raise ExportError("incomplete export journal; manual inspection required")
        if (
            _sha(source) == journal["new_source_digest"]
            and _sha(ledger) == journal["new_ledger_digest"]
        ):
            _cleanup(journal_path, [source_backup, ledger_backup])
            return True
        if journal["old_source_digest"] is not None:
            if _sha(source_backup) != journal["old_source_digest"]:
                raise ExportError("source backup digest mismatch; manual inspection required")
        if journal["old_ledger_digest"] is not None:
            if _sha(ledger_backup) != journal["old_ledger_digest"]:
                raise ExportError("ledger backup digest mismatch; manual inspection required")
        if journal["old_source_digest"] is not None:
            os.replace(source_backup, source)
        else:
            source.unlink(missing_ok=True)
        if journal["old_ledger_digest"] is not None:
            os.replace(ledger_backup, ledger)
        else:
            ledger.unlink(missing_ok=True)
        _cleanup(journal_path, [source_backup, ledger_backup])
        return True
    except (RecordError, OSError, TypeError, AttributeError, KeyError) as exc:
        raise ExportError(f"cannot recover export: {exc}") from exc


def _source_rows(source: Path) -> list[dict[str, str]]:
    if not source.exists():
        return []
    with source.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) == HEADER:
            return list(reader)
        if tuple(reader.fieldnames or ()) == (
            "id",
            "english",
            "indonesian",
            "malaysian",
            "image",
            "tags",
        ):
            return []  # Legacy row is released again only after retrospective acceptance.
    raise ExportError("canonical learner source has an unexpected header")


def _contrast(relation_result: dict[str, Any]) -> str:
    parts = relation_result.get("contrast", {})
    if not isinstance(parts, dict):
        raise ExportError("false-friend contrast is missing")
    language = (
        "Bahasa Indonesia" if parts.get("misleading_language") == "indonesian" else "Bahasa Melayu"
    )
    return f"{parts['misleading_form']} in {language} means {parts['actual_meaning']}."


def _write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADER, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())


def export_batches(root: Path, batch_ids: list[str]) -> list[str]:
    """Export a complete promotion set with pre-ID overlap checks and crash recovery."""
    root = Path(root)
    recover_export(root)
    if not batch_ids or len(batch_ids) != len(set(batch_ids)):
        raise ExportError("export requires unique batch IDs")
    source = root / "data" / "vocabulary.tsv"
    ledger_path = root / "curation" / "id-ledger.json"
    ledger = load_ledger(root)
    stores = [BatchStore(root, batch_id) for batch_id in batch_ids]
    accepted: list[tuple[BatchStore, str, dict[str, Any], dict[str, Any]]] = []
    for store in stores:
        manifest = store.manifest()
        try:
            report = read_json(store.path / "report.json")
        except RecordError as exc:
            raise ExportError(f"batch {store.batch_id} has no readable closed report") from exc
        if manifest.status != "closed" or report.get("status") != "closed" or report.get("pending"):
            raise ExportError(f"batch {store.batch_id} is pending or has no closed report")
        for candidate_id in store.candidate_ids():
            candidate = store.candidate(candidate_id)
            stages = current_results(store, candidate_id)
            explicit = next(
                (
                    event.get("decision")
                    for event in reversed(store.events(candidate_id))
                    if event.get("role") == "explicit-final"
                ),
                None,
            )
            decision = decide_candidate(candidate, stages, explicit_final=explicit)
            recorded = next(
                (item for item in report["decisions"] if item["candidate_id"] == candidate_id), None
            )
            if recorded is None or recorded["outcome"] != decision["outcome"]:
                raise ExportError(f"stale decision/report for {store.batch_id}:{candidate_id}")
            if decision["outcome"] == "pending":
                raise ExportError(f"candidate is pending: {store.batch_id}:{candidate_id}")
            if decision["outcome"] == "accepted":
                accepted.append((store, candidate_id, candidate, stages))
    rows = _source_rows(source)
    row_by_id = {row["id"]: row for row in rows}
    new_ids = []
    for store, candidate_id, candidate, stages in accepted:
        prior = assigned_id(ledger, store.batch_id, candidate_id)
        relation_result = stages["relation-proposal"]
        relation = relation_result["relation"]
        if relation == "same":
            raise ExportError("shared vocabulary cannot enter the contrast deck")
        projected = {
            "id": prior or candidate.get("legacy_id") or "",
            "english": relation_result["english"],
            "indonesian": candidate["indonesian"],
            "malaysian": candidate["malaysian"],
            "relation": relation,
            "image": candidate.get("image", ""),
            "tags": " ".join(candidate.get("tags", [])),
            "contrast": _contrast(relation_result) if relation == "false-friend" else "",
        }
        if prior is None or row_by_id.get(prior) != projected:
            matches = find_deterministic_overlaps(
                candidate, archive_candidates(root, store.batch_id, candidate_id)
            )
            reviewed = {
                item.get("other_id"): item for item in stages["normalize-and-dedupe"]["overlaps"]
            }
            for match in matches:
                other_id = match["other_id"]
                if other_id == prior or other_id == candidate.get("legacy_id"):
                    continue
                if reviewed.get(other_id, {}).get("resolution") != "distinct":
                    raise ExportError(
                        "unresolved promotion overlap: "
                        f"{store.batch_id}:{candidate_id} vs {other_id}"
                    )
        concept_id = prior or candidate.get("legacy_id") or allocate_id(ledger)
        if prior is None and candidate.get("legacy_id"):
            if not any(item["id"] == concept_id for item in ledger["assignments"]):
                raise ExportError("legacy ID is absent from assignment ledger")
            legacy = row_by_id.get(concept_id)
            if legacy is None:
                legacy_source = root / "data" / "vocabulary.tsv"
                with legacy_source.open(encoding="utf-8", newline="") as stream:
                    legacy = next(
                        (
                            row
                            for row in csv.DictReader(stream, delimiter="\t")
                            if row["id"] == concept_id
                        ),
                        None,
                    )
            if legacy is None or any(
                legacy.get(key) != candidate.get(key)
                for key in ("english", "indonesian", "malaysian")
            ):
                raise ExportError("retrospective candidate changes legacy cue or answers")
        elif prior is None:
            append_assignment(
                ledger,
                concept_id=concept_id,
                batch_id=store.batch_id,
                candidate_id=candidate_id,
                assigned_at=utc_now(),
                semantic_concept_key=candidate["sense"],
            )
        row_by_id[concept_id] = {**projected, "id": concept_id}
        new_ids.append(concept_id)
    if not row_by_id:
        raise ExportError("export would produce an empty learner source")
    if not set(row_by_id).issubset({item["id"] for item in ledger["assignments"]}):
        raise ExportError("learner source has IDs missing from ledger")
    validate_ledger(ledger)
    source.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    source_handle, source_name = tempfile.mkstemp(
        prefix=".vocabulary.", suffix=".tmp", dir=source.parent
    )
    os.close(source_handle)
    ledger_handle, ledger_name = tempfile.mkstemp(
        prefix=".id-ledger.", suffix=".tmp", dir=ledger_path.parent
    )
    os.close(ledger_handle)
    source_temp, ledger_temp = Path(source_name), Path(ledger_name)
    journal_path = root / "curation" / "export-journal.json"
    source_backup = root / "curation" / "source.backup"
    ledger_backup = root / "curation" / "ledger.backup"
    try:
        _write_tsv(source_temp, sorted(row_by_id.values(), key=lambda row: row["id"]))
        validate_vocabulary(source_temp, root / "media")
        with ledger_temp.open("w", encoding="utf-8") as stream:
            json.dump(ledger, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if source.exists():
            shutil.copy2(source, source_backup)
        if ledger_path.exists():
            shutil.copy2(ledger_path, ledger_backup)
        new_source_digest = _sha(source_temp)
        new_ledger_digest = _sha(ledger_temp)
        atomic_json(
            journal_path,
            {
                "schema_version": 1,
                "batch_ids": batch_ids,
                "phase": "replacing",
                "old_source_digest": _sha(source),
                "old_ledger_digest": _sha(ledger_path),
                "new_source_digest": new_source_digest,
                "new_ledger_digest": new_ledger_digest,
            },
        )
        os.replace(ledger_temp, ledger_path)
        os.replace(source_temp, source)
        if _sha(source) != new_source_digest or _sha(ledger_path) != new_ledger_digest:
            raise ExportError("export verification failed")
        _cleanup(journal_path, [source_backup, ledger_backup])
    except Exception:
        if journal_path.exists():
            recover_export(root)
        raise
    finally:
        source_temp.unlink(missing_ok=True)
        ledger_temp.unlink(missing_ok=True)
    return new_ids
