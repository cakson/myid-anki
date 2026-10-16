"""Deterministic random monitoring after production decisions settle."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter

from indo_malay_anki.curation.export import _projected_row
from indo_malay_anki.curation.store import BatchStore, atomic_json, read_json
from indo_malay_anki.curation.workflow import current_results

from .audit import current_audit, selection_reasons
from .promotion import withdraw_candidate
from .provider import call_model
from .store import RunError, RunStore, digest, utc_now


def clean_population(store: RunStore) -> list[dict]:
    manifest = store.load()
    population = []
    for item in manifest["slices"]:
        if not item["candidate_ids"]:
            continue
        slice_store = BatchStore(store.root, item["slice_id"])
        report = read_json(slice_store.path / "report.json")
        if report.get("pending"):
            raise RunError("random QA requires settled production decisions")
        for decision in report["decisions"]:
            if decision["outcome"] != "accepted":
                continue
            candidate_id = decision["candidate_id"]
            reasons = selection_reasons(decision)
            audit = (
                current_audit(store, item["slice_id"], candidate_id, decision) if reasons else None
            )
            if reasons and (audit is None or audit["verdict"] != "cleared"):
                raise RunError("random QA requires settled risk-audit dispositions")
            population.append(
                {
                    "slice_id": item["slice_id"],
                    "candidate_id": candidate_id,
                    "confidence": decision.get("confidence_tier", "unknown"),
                    "risk_path": decision.get("risk", {}).get("path", "unknown"),
                    "decision_digest": digest(decision),
                }
            )
    return sorted(population, key=lambda item: (item["slice_id"], item["candidate_id"]))


def select_sample(store: RunStore) -> dict:
    population = clean_population(store)
    population_digest = digest(population)
    path = store.path / "qa" / "roster.json"
    if path.exists():
        prior = read_json(path)
        if prior["population_digest"] == population_digest:
            return prior
        archive = store.path / "qa" / f"roster-{prior['population_digest'][:12]}.json"
        atomic_json(archive, prior)
    size = min(len(population), max(5, math.ceil(len(population) * 0.1)))
    seed = int(hashlib.sha256(f"{store.run_id}:{population_digest}".encode()).hexdigest()[:16], 16)
    rng = random.Random(seed)
    strata = {}
    for item in population:
        key = f"{item['risk_path']}:{item['confidence']}"
        strata.setdefault(key, []).append(item)
    chosen = []
    for key in sorted(strata):
        if len(chosen) >= size:
            break
        chosen.append(rng.choice(strata[key]))
    remaining = [item for item in population if item not in chosen]
    chosen.extend(rng.sample(remaining, size - len(chosen)))
    roster = {
        "schema_version": 1,
        "run_id": store.run_id,
        "created_at": utc_now(),
        "population_digest": population_digest,
        "population_count": len(population),
        "strategy": "stratified-10-percent-min5-v1",
        "seed": seed,
        "strata": {key: len(value) for key, value in strata.items()},
        "sample_count": size,
        "sample": sorted(chosen, key=lambda item: (item["slice_id"], item["candidate_id"])),
    }
    atomic_json(path, roster)
    store.append_event(
        "qa-select",
        "complete",
        details={
            "population_digest": population_digest,
            "sample_count": size,
        },
    )
    return roster


def record_finding(
    store: RunStore, slice_id: str, candidate_id: str, finding: dict, *, usage: dict | None = None
) -> dict:
    roster = select_sample(store)
    sampled = next(
        (
            item
            for item in roster["sample"]
            if item["slice_id"] == slice_id and item["candidate_id"] == candidate_id
        ),
        None,
    )
    if sampled is None:
        raise RunError("candidate is not in current QA sample")
    if (
        finding.get("finding_class")
        not in {"none", "learner-critical-answer", "cue-content", "metadata-only"}
        or not str(finding.get("rationale", "")).strip()
    ):
        raise RunError("invalid QA finding")
    path = store.path / "qa" / "findings" / f"{slice_id}--{candidate_id}.json"
    if path.exists():
        old = read_json(path)
        if (
            old["finding_class"] != finding["finding_class"]
            or old["rationale"] != finding["rationale"]
        ):
            raise RunError("conflicting QA finding replay")
        return old
    withdrawal = None
    if finding["finding_class"] in {"learner-critical-answer", "cue-content"}:
        from indo_malay_anki.curation.ids import assigned_id, load_ledger

        if assigned_id(load_ledger(store.root), slice_id, candidate_id):
            withdrawal = withdraw_candidate(
                store, slice_id, candidate_id, reason="material random-QA finding"
            )
    record = {
        "schema_version": 1,
        "slice_id": slice_id,
        "candidate_id": candidate_id,
        "population_digest": roster["population_digest"],
        "original_decision_digest": sampled["decision_digest"],
        "finding_class": finding["finding_class"],
        "rationale": finding["rationale"],
        "error_category": finding.get("error_category"),
        "claim_reviews": finding.get("claim_reviews", []),
        "withdrawal": withdrawal,
        "resolved": finding["finding_class"] in {"none", "metadata-only"},
        "recorded_at": utc_now(),
        "usage": usage,
    }
    atomic_json(path, record)
    store.append_event(
        "qa-finding",
        "complete",
        details={
            "slice_id": slice_id,
            "candidate_id": candidate_id,
            "finding_class": record["finding_class"],
            "usage": usage,
        },
    )
    evaluate_brakes(store)
    return record


def resolve_finding(store: RunStore, slice_id: str, candidate_id: str, reason: str) -> dict:
    if not reason.strip():
        raise RunError("QA resolution requires a reason")
    path = store.path / "qa" / "findings" / f"{slice_id}--{candidate_id}.json"
    if not path.exists():
        raise RunError("QA finding does not exist")
    finding = read_json(path)
    if finding["resolved"]:
        return finding
    slice_store = BatchStore(store.root, slice_id)
    report = read_json(slice_store.path / "report.json")
    decision = next(
        (item for item in report["decisions"] if item["candidate_id"] == candidate_id), None
    )
    if not decision or decision["outcome"] != "accepted":
        raise RunError("QA resolution requires a current accepted decision")
    if digest(decision) == finding["original_decision_digest"]:
        raise RunError("QA resolution requires a corrected current decision")
    reasons = selection_reasons(decision)
    audit = current_audit(store, slice_id, candidate_id, decision) if reasons else None
    if reasons and (audit is None or audit["verdict"] != "cleared"):
        raise RunError("QA resolution requires current risk audit clearance")
    finding.update(
        resolved=True,
        resolution=reason,
        resolved_at=utc_now(),
        corrected_decision_digest=digest(decision),
    )
    atomic_json(path, finding)
    store.append_event(
        "qa-resolution",
        "complete",
        details={
            "slice_id": slice_id,
            "candidate_id": candidate_id,
            "reason": reason,
        },
    )
    return finding


def evaluate_brakes(store: RunStore) -> list[dict]:
    manifest = store.load()
    findings_folder = store.path / "qa" / "findings"
    findings = (
        [
            read_json(path)
            for path in findings_folder.glob("*.json")
            if not path.name.endswith(".response.json")
        ]
        if findings_folder.exists()
        else []
    )
    audits_folder = store.path / "audits"
    audit_findings = (
        [
            read_json(path)
            for path in audits_folder.glob("*/*.json")
            if not path.name.endswith((".response.json", ".packet.json"))
        ]
        if audits_folder.exists()
        else []
    )
    critical = [
        item
        for item in [*findings, *audit_findings]
        if item["finding_class"] == "learner-critical-answer"
    ]
    patterns = Counter(
        item.get("error_category") for item in critical if item.get("error_category")
    )
    triggered = []
    if len(critical) >= 2:
        triggered.append("two-learner-critical-errors")
    if any(count >= 2 for count in patterns.values()):
        triggered.append("repeated-learner-critical-pattern")
    if manifest.get("proposed_count", 0) >= 20:
        proposed = manifest["proposed_count"]
        reasons = Counter(
            screen["reason"] for item in manifest["slices"] for screen in item["screened"]
        )
        curated_no_contrast = 0
        curated_duplicates = 0
        for item in manifest["slices"]:
            path = store.root / "curation" / "batches" / item["slice_id"] / "report.json"
            if path.exists():
                report = read_json(path)
                curated_no_contrast += report.get("no_contrast_rejected", 0)
                curated_duplicates += sum(
                    "confirmed-duplicate" in decision.get("reason_codes", [])
                    for decision in report.get("decisions", [])
                )
        if (
            sum(reasons[key] for key in ("duplicate", "redundant")) + curated_duplicates
        ) / proposed > 0.2:
            triggered.append("duplicate-generation-spike")
        if (reasons["prior-same"] + curated_no_contrast) / proposed > 0.3:
            triggered.append("no-contrast-generation-spike")
    curated = 0
    held = 0
    for item in manifest["slices"]:
        path = store.root / "curation" / "batches" / item["slice_id"] / "report.json"
        if path.exists():
            report = read_json(path)
            curated += report.get("generated", 0) - report.get("pending", 0)
            held += report.get("held", 0)
    if curated >= manifest["brake_thresholds"]["minimum_observations"] and held / curated > 0.30:
        triggered.append("high-hold-rate")
    current = {item["reason"] for item in manifest.get("brakes", []) if item["active"]}
    newly_triggered = []
    for reason in triggered:
        if reason in current:
            continue
        prior = [item for item in manifest["brakes"] if item["reason"] == reason]
        if prior:
            if reason not in {
                "two-learner-critical-errors",
                "repeated-learner-critical-pattern",
            } or len(critical) <= max(item.get("observed_critical_count", 0) for item in prior):
                continue
        manifest["brakes"].append({"reason": reason, "active": True, "triggered_at": utc_now()})
        newly_triggered.append(reason)
    if newly_triggered:
        store.save(manifest, expected_digest=store.manifest_digest())
        store.append_event(
            "safety-brake", "complete", details={"triggers": sorted(newly_triggered)}
        )
    return manifest["brakes"]


def dispose_brake(store: RunStore, reason: str, resolution: str) -> dict:
    if not resolution.strip():
        raise RunError("brake disposition requires an investigation resolution")
    manifest = store.load()
    match = next(
        (item for item in manifest["brakes"] if item["reason"] == reason and item["active"]),
        None,
    )
    if match is None:
        raise RunError("no active brake with that reason")
    finding_paths = list((store.path / "qa" / "findings").glob("*.json")) + list(
        (store.path / "audits").glob("*/*.json")
    )
    observed_critical_count = sum(
        read_json(path).get("finding_class") == "learner-critical-answer"
        for path in finding_paths
        if not path.name.endswith((".packet.json", ".response.json"))
    )
    match.update(
        active=False,
        disposition=resolution,
        resolved_at=utc_now(),
        observed_critical_count=observed_critical_count,
    )
    store.save(manifest, expected_digest=store.manifest_digest())
    store.append_event(
        "brake-disposition",
        "complete",
        details={
            "reason": reason,
            "resolution": resolution,
        },
    )
    return store.load()


def review_sample(store: RunStore, *, provider=call_model) -> dict:
    roster = select_sample(store)
    summary = {"sample_count": roster["sample_count"], "reviewed": 0, "findings": []}
    for item in roster["sample"]:
        slice_id, candidate_id = item["slice_id"], item["candidate_id"]
        path = store.path / "qa" / "findings" / f"{slice_id}--{candidate_id}.json"
        if path.exists():
            record = read_json(path)
        else:
            slice_store = BatchStore(store.root, slice_id)
            report = read_json(slice_store.path / "report.json")
            decision = next(d for d in report["decisions"] if d["candidate_id"] == candidate_id)
            row = _projected_row(
                slice_store.candidate(candidate_id),
                current_results(slice_store, candidate_id),
                decision,
            )
            packet = {
                "candidate": slice_store.candidate(candidate_id),
                "decision": decision,
                "learner_content": row,
                "qa_route": "random-monitoring",
            }
            prompt = (
                "Independent random QA of Indonesian and Malaysian Malay learner content. "
                "Check English sense, both answers, relation and cue. Return only JSON with "
                "finding_class (none, learner-critical-answer, cue-content, metadata-only), "
                "rationale, optional error_category, and claim_reviews list. "
                "This is monitoring, not universal release clearance.\n"
                + json.dumps(packet, ensure_ascii=False)
            )
            captured_path = path.with_suffix(".response.json")
            if captured_path.exists():
                captured = read_json(captured_path)
            else:
                captured = provider(store.root, "independent-verification", prompt)
                atomic_json(captured_path, captured)
            try:
                record = record_finding(
                    store,
                    slice_id,
                    candidate_id,
                    captured["response"],
                    usage={
                        key: captured.get(key)
                        for key in (
                            "elapsed_ms",
                            "model_calls",
                            "input_tokens",
                            "output_tokens",
                            "retrievals",
                        )
                    },
                )
            except (KeyError, TypeError, ValueError) as exc:
                from .workflow import _archive_failed_capture

                _archive_failed_capture(store, captured_path, kind="qa-response", error=exc)
                raise
        summary["reviewed"] += 1
        if record["finding_class"] != "none":
            summary["findings"].append(record)
    return summary
