"""Read-only inventory of the historical curation run.

Current-code decisions are replayed in a temporary copy because packet reconstruction can
materialize archive snapshots. The checked-in batches and reports are never rewritten.
"""

from __future__ import annotations

import csv
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from .gate import decide_candidate
from .records import AI_ROLES
from .store import BatchStore, read_json
from .workflow import current_results

PROCESS_FIXTURES = frozenset({"growth-audit-001"})
# Freeze the pre-recalibration machine baseline. Later prospective batches are
# measured in their own reports and must not rewrite these historical counts.
HISTORICAL_BATCHES = frozenset(
    {
        "clothing-001",
        "common-adjectives-001",
        "common-verbs-001",
        "communication-001",
        "everyday-objects-001",
        "food-001",
        "health-001",
        "home-001",
        "places-001",
        "produce-001",
        "school-001",
        "technology-001",
        "transportation-001",
        "university-001",
    }
)


def _last_explicit(events: tuple[dict[str, Any], ...]) -> dict[str, Any] | None:
    event = next((item for item in reversed(events) if item.get("role") == "explicit-final"), None)
    return event.get("decision") if event is not None else None


def _inventory_copy(root: Path) -> dict[str, Any]:
    batches = root / "curation" / "batches"
    totals: Counter[str] = Counter()
    fixture_totals: Counter[str] = Counter()
    archived_totals: Counter[str] = Counter()
    decision_reasons: Counter[str] = Counter()
    first_incomplete: Counter[str] = Counter()
    completed_roles: Counter[str] = Counter()
    repeated_roles: Counter[str] = Counter()
    failures: Counter[str] = Counter()
    reported_mismatches: list[str] = []
    inspected_files = inspected_rows = observations = 0
    event_times: list[str] = []
    batch_rows: list[dict[str, Any]] = []
    for folder in sorted(batches.iterdir()):
        if not (folder.is_dir() and (folder / "manifest.json").exists()):
            continue
        if folder.name not in HISTORICAL_BATCHES | PROCESS_FIXTURES:
            continue
        store = BatchStore(root, folder.name)
        fixture = folder.name in PROCESS_FIXTURES
        counters = fixture_totals if fixture else totals
        current: Counter[str] = Counter()
        for event in store.batch_events():
            if event.get("status") == "failed":
                failures["batch-role"] += 1
            if isinstance(event.get("at"), str):
                event_times.append(event["at"])
        for candidate_id in store.candidate_ids():
            counters["generated"] += 1
            events = store.events(candidate_id)
            stages = current_results(store, candidate_id)
            decision = decide_candidate(
                store.candidate(candidate_id),
                stages,
                explicit_final=_last_explicit(events),
                policy_version=store.manifest().decision_policy_version or "1.0.0",
            )
            counters[decision["outcome"]] += 1
            current[decision["outcome"]] += 1
            if fixture:
                continue
            for reason in decision.get("reason_codes", []):
                decision_reasons[reason] += 1
            if decision["outcome"] == "hold":
                missing = next(
                    (role for role in AI_ROLES[1:] if role not in stages),
                    "all-stages-complete",
                )
                first_incomplete[missing] += 1
            by_role: Counter[str] = Counter()
            for event in events:
                role = event.get("role")
                if isinstance(event.get("at"), str):
                    event_times.append(event["at"])
                if event.get("status") == "failed":
                    failures["candidate-role"] += 1
                if role in AI_ROLES[1:] and event.get("status") == "complete":
                    by_role[role] += 1
                    completed_roles[role] += 1
                    if role == "evidence-audit":
                        observations += len(event.get("result", {}).get("observations", []))
            for role, count in by_role.items():
                repeated_roles[role] += max(0, count - 1)
        for inspection in (folder / "source-inspections").glob("*.json"):
            if fixture:
                break
            inspected_files += 1
            raw = read_json(inspection)
            inspected_rows += len(raw.get("sources", [])) if isinstance(raw, dict) else 0
        report_path = folder / "report.json"
        if report_path.exists():
            report = read_json(report_path)
            for key in ("generated", "accepted", "held", "rejected", "pending"):
                if not fixture:
                    archived_totals[key] += report.get(key, 0)
                outcome = {"held": "hold", "rejected": "rejected"}.get(key, key)
                computed = len(store.candidate_ids()) if key == "generated" else current[outcome]
                if report.get(key) != computed:
                    reported_mismatches.append(f"{folder.name}:{key}")
        batch_rows.append({"batch_id": folder.name, "fixture": fixture, **dict(current)})
    source = root / "data" / "vocabulary.tsv"
    with source.open(encoding="utf-8", newline="") as stream:
        active_rows = list(csv.DictReader(stream, delimiter="\t"))
    return {
        "non_fixture_batches": sum(not row["fixture"] for row in batch_rows),
        "fixture_batches": sum(row["fixture"] for row in batch_rows),
        "historical_archived": dict(sorted(archived_totals.items())),
        "current_policy_replay": {
            "generated": totals["generated"],
            "accepted": totals["accepted"],
            "held": totals["hold"],
            "rejected": totals["rejected"],
            "pending": totals["pending"],
        },
        "fixture": {
            "generated": fixture_totals["generated"],
            "accepted": fixture_totals["accepted"],
            "held": fixture_totals["hold"],
            "rejected": fixture_totals["rejected"],
            "pending": fixture_totals["pending"],
        },
        "active_learner_cards": len(active_rows),
        "first_incomplete_hold_stage": dict(sorted(first_incomplete.items())),
        "current_decision_reason_codes": dict(sorted(decision_reasons.items())),
        "completed_candidate_roles": dict(sorted(completed_roles.items())),
        "repeated_completed_roles": dict(sorted(repeated_roles.items())),
        "failed_events": dict(sorted(failures.items())),
        "source_inspection_files": inspected_files,
        "source_inspection_rows": inspected_rows,
        "evidence_observations_across_attempts": observations,
        "archive_event_span": [min(event_times), max(event_times)] if event_times else None,
        "active_time_seconds": None,
        "provider_calls": None,
        "input_tokens": None,
        "output_tokens": None,
        "research_operations": None,
        "estimated_cost": None,
        "archived_report_mismatches": sorted(reported_mismatches),
        "batches": batch_rows,
    }


def historical_baseline(root: Path) -> dict[str, Any]:
    """Replay a baseline without mutating the repository or claiming archive time is active time."""
    root = Path(root)
    with tempfile.TemporaryDirectory(prefix="myid-curation-baseline-") as temporary:
        mirror = Path(temporary)
        shutil.copytree(root / "curation" / "batches", mirror / "curation" / "batches")
        (mirror / "data").mkdir()
        shutil.copy2(root / "data" / "vocabulary.tsv", mirror / "data" / "vocabulary.tsv")
        return _inventory_copy(mirror)
