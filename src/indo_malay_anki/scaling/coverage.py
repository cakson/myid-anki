"""Inspectable semantic coverage and editable, frozen category allocation."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

from indo_malay_anki.curation.ids import load_ledger
from indo_malay_anki.curation.store import BatchStore, atomic_json, read_json

from .store import RunError, RunStore, digest, file_digest, utc_now


def catalog(root: Path) -> dict:
    path = Path(root) / "curation" / "coverage-categories.json"
    if not path.exists():
        path = Path(__file__).resolve().parents[3] / "curation" / "coverage-categories.json"
    value = read_json(path)
    if value.get("schema_version") != 1 or not isinstance(value.get("categories"), list):
        raise RunError("invalid coverage category catalog")
    return value


def inventory(root: Path) -> dict[str, Any]:
    root = Path(root)
    source = root / "data" / "vocabulary.tsv"
    categories = catalog(root)
    alias_to_category = {
        alias: item["id"] for item in categories["categories"] for alias in item["aliases"]
    }
    counts = {item["id"]: 0 for item in categories["categories"]}
    unknown: set[str] = set()
    unmapped: list[str] = []
    primary: dict[str, str] = {}
    historical_counts = {item["id"]: 0 for item in categories["categories"]}
    historical_refs: list[dict[str, str]] = []
    prior_same_refs: list[str] = []
    rows: list[dict] = []
    slice_category: dict[str, str] = {}
    runs = root / "curation" / "production-runs"
    if runs.exists():
        for folder in sorted(runs.iterdir()):
            path = folder / "manifest.json"
            if path.exists():
                run = read_json(path)
                for slice_ref in run.get("slices", []):
                    slice_category[slice_ref["slice_id"]] = slice_ref["category"]
    assigned_category = {
        item["id"]: slice_category[item["batch_id"]]
        for item in load_ledger(root)["assignments"]
        if item["batch_id"] in slice_category
    }
    if source.exists():
        with source.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter="\t"))
    for row in rows:
        tags = row.get("tags", "").split()
        mapped = [alias_to_category[tag] for tag in tags if tag in alias_to_category]
        unknown.update(
            tag
            for tag in tags
            if tag not in alias_to_category and tag not in categories["ignore_tags"]
        )
        category = assigned_category.get(row["id"]) or (mapped[0] if mapped else None)
        if category:
            primary[row["id"]] = category
            counts[category] += 1
        else:
            unmapped.append(row["id"])
    batches = root / "curation" / "batches"
    if batches.exists():
        for folder in sorted(batches.iterdir()):
            if not folder.is_dir() or not (folder / "manifest.json").exists():
                continue
            store = BatchStore(root, folder.name)
            decisions = {}
            if (folder / "report.json").exists():
                report = read_json(folder / "report.json")
                decisions = {item["candidate_id"]: item for item in report.get("decisions", [])}
            for candidate_id in store.candidate_ids():
                candidate = store.candidate(candidate_id)
                category = next(
                    (
                        alias_to_category[tag]
                        for tag in candidate.get("tags", [])
                        if tag in alias_to_category
                    ),
                    None,
                )
                reference = f"{folder.name}:{candidate_id}"
                if category:
                    historical_counts[category] += 1
                historical_refs.append(
                    {
                        "ref": reference,
                        "category": category or "unmapped",
                        "sense": candidate.get("sense", ""),
                    }
                )
                decision = decisions.get(candidate_id, {})
                if decision.get("relation") == "same" or "no-contrast" in " ".join(
                    decision.get("reason_codes", [])
                ):
                    prior_same_refs.append(reference)
    return {
        "schema_version": 1,
        "recorded_at": utc_now(),
        "source_digest": file_digest(source) if source.exists() else None,
        "category_catalog_digest": digest(categories),
        "card_count": len(rows),
        "counts": counts,
        "primary_by_id": primary,
        "historical_counts": historical_counts,
        "historical_refs": historical_refs,
        "prior_same_refs": prior_same_refs,
        "unmapped_rows": unmapped,
        "unknown_tags": sorted(unknown),
    }


def allocation_draft(snapshot: dict, requested_count: int, root: Path | None = None) -> dict:
    if requested_count < 1:
        raise RunError("requested_count must be positive")
    categories = catalog(root or Path(__file__).resolve().parents[3])["categories"]
    weights = {
        item["id"]: float(item["utility"]) / math.sqrt(snapshot["counts"].get(item["id"], 0) + 3)
        for item in categories
    }
    total_weight = sum(weights.values())
    exact = {key: requested_count * value / total_weight for key, value in weights.items()}
    counts = {key: math.floor(value) for key, value in exact.items()}
    remainder = requested_count - sum(counts.values())
    for key in sorted(exact, key=lambda k: (exact[k] - counts[k], weights[k], k), reverse=True)[
        :remainder
    ]:
        counts[key] += 1
    rationale = [
        {
            "category": item["id"],
            "current_count": snapshot["counts"].get(item["id"], 0),
            "proposed_slots": counts[item["id"]],
            "reason": "gap and common-vocabulary utility weight",
        }
        for item in categories
    ]
    return {"counts": counts, "rationale": rationale, "strategy_version": "gap-weighted-v1"}


def set_draft(store: RunStore, counts: dict[str, int], *, reason: str) -> dict:
    manifest = store.load()
    if manifest["state"] != "draft":
        raise RunError("allocation edits require draft state")
    _validate_counts(store, counts)
    edited = {**manifest, "allocation_draft": counts, "allocation_edit_reason": reason}
    store.save(edited, expected_digest=store.manifest_digest())
    store.append_event("allocation-edit", "complete", details={"counts": counts, "reason": reason})
    return store.load()


def _validate_counts(store: RunStore, counts: dict[str, int]) -> None:
    allowed = {item["id"] for item in catalog(store.root)["categories"]}
    if set(counts) != allowed or any(
        type(value) is not int or value < 0 for value in counts.values()
    ):
        raise RunError("allocation must provide nonnegative counts for all known categories")
    if sum(counts.values()) != store.load()["requested_count"]:
        raise RunError("allocation total must equal requested_count")


def approve_allocation(
    store: RunStore, counts: dict[str, int], snapshot: dict, *, reason: str
) -> dict:
    manifest = store.load()
    if manifest["state"] != "draft":
        raise RunError("allocation approval requires draft state")
    _validate_counts(store, counts)
    if snapshot["card_count"] != manifest["baseline_count"]:
        raise RunError("coverage snapshot differs from baseline count")
    current = inventory(store.root)
    if current["source_digest"] != snapshot["source_digest"]:
        raise RunError("canonical source changed since coverage draft")
    if not reason.strip():
        raise RunError("approval requires a reason")
    atomic_json(store.path / "coverage-before.json", snapshot)
    updated = {
        **manifest,
        "allocation_draft": manifest["allocation_draft"] or counts,
        "allocation": counts,
        "allocation_digest": digest(counts),
        "allocation_approval_reason": reason,
        "baseline_source_digest": snapshot["source_digest"],
        "category_strategy_version": "gap-weighted-v1",
        "generation_started_at": None,
        "state": "allocation-approved",
    }
    store.save(updated, expected_digest=store.manifest_digest())
    store.append_event(
        "allocation-approval", "complete", details={"reason": reason, "counts": counts}
    )
    return store.load()
