#!/usr/bin/env python3
"""Build a label-separated audit cohort and compare explainable routing policies."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
OUTPUT = SPEC / "audit-router-calibration.json"
BATCHES = {
    "batch1": (
        "fresh-batch-50-state.json",
        ("fresh-batch-50-audit.json", "fresh-batch-50-audit-completion.json"),
    ),
    "batch2": ("second-batch-50-state.json", ("second-batch-50-audit.json",)),
    "batch3": (
        "final-calibration-50-state.json",
        ("final-calibration-50-audit.json", "final-calibration-router-supplement-audit.json"),
    ),
}
CRITICAL = {"materially-misleading", "should-hold", "should-reject"}
GENERAL_FLAGS = {
    "cue-corrected",
    "cue-sense-ambiguity",
    "relation-corrected",
    "relation-instability",
    "verifier-disagreement",
    "historical-objection",
    "regional-register-risk",
    "credible-competing-form",
    "preference-uncertainty",
    "shared-common-form",
    "concrete-nonblocking-risk",
    "substantial-nonblocking-risk",
}
FOCUSED_FLAGS = GENERAL_FLAGS - {"shared-common-form", "credible-competing-form"}
SIGNALS = (
    "confidence-low",
    "confidence-very-low",
    "verifier-concern",
    "cue-risk",
    "relation-instability",
    "regional-register-risk",
    "credible-competing-form",
    "shared-common-form",
    "preference-uncertainty",
    "named-alternative-exists",
    "standard-vs-everyday-gap",
    "generic-limited-evidence",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label_of(audit: dict | None) -> str | None:
    if audit is None:
        return None
    if audit["verdict"] in CRITICAL or audit.get("material_false_positive"):
        return "critical"
    if audit["verdict"] == "minor-correction":
        return "correctable"
    if audit["verdict"] == "confirmed-good":
        return "confirmed-safe"
    raise ValueError(f"unknown audit verdict: {audit['verdict']}")


def features(row: dict) -> dict:
    """All fields come from frozen production decisions, never audit outputs."""
    verifier = row.get("verifier", {})
    preference = verifier.get("preference_risk")
    flags = set(row.get("review_flags", []))
    rationale = " ".join(
        str(verifier.get(key, ""))
        for key in ("rationale", "risk_rationale", "shared_synonym_rationale")
    ).casefold()
    named_borrowing = (
        isinstance(preference, dict)
        and preference.get("signal") == "named-alternative-exists"
        and preference.get("language") in {"malaysian", "both"}
    )
    # A candidate flag for analysis, not yet a trusted production or audit rule.
    standard_gap = (
        named_borrowing
        and row.get("relation") == "different-common-word"
        and ("standard malaysian" in rationale or "localized" in rationale)
        and any(word in rationale for word in ("english", "borrow", "loan", "usb"))
    )
    signals = {
        "confidence-low": row.get("confidence_tier") == "low",
        "confidence-very-low": row.get("confidence_tier") == "very-low",
        "verifier-concern": bool(verifier.get("concerns")),
        "cue-risk": verifier.get("cue_alignment") in {"correctable", "material-risk"}
        or bool(flags & {"cue-corrected", "cue-sense-ambiguity"}),
        "relation-instability": bool(flags & {"relation-corrected", "relation-instability"}),
        "regional-register-risk": "regional-register-risk" in flags,
        "credible-competing-form": "credible-competing-form" in flags,
        "shared-common-form": "shared-common-form" in flags,
        "preference-uncertainty": "preference-uncertainty" in flags,
        "named-alternative-exists": named_borrowing,
        "standard-vs-everyday-gap": standard_gap,
        "generic-limited-evidence": "limited-evidence" in flags,
    }
    candidate = row["candidate"]
    return {
        "relation": row.get("relation"),
        "confidence_tier": row.get("confidence_tier"),
        "confidence_rationale": row.get("confidence_rationale"),
        "verifier_verdict": verifier.get("verdict"),
        "verifier_concerns": verifier.get("concerns", []),
        "verifier_material_concerns": verifier.get("material_concerns", []),
        "cue_alignment": verifier.get("cue_alignment"),
        "shared_synonym_case": verifier.get("shared_synonym_case"),
        "preference_risk": preference,
        "review_flags": sorted(flags),
        "risk_path": row.get("risk", {}).get("path"),
        "evidence_audited": "limited-evidence" not in flags if flags else None,
        "identical_form": candidate["indonesian"].casefold() == candidate["malaysian"].casefold(),
        "signals": signals,
    }


def load_cohort() -> tuple[list[dict], dict]:
    records: list[dict] = []
    digests: dict[str, str] = {}
    for batch, (state_name, audit_names) in BATCHES.items():
        state_path = SPEC / state_name
        state = json.loads(state_path.read_text())
        digests[state_name] = sha(state_path)
        audits = {}
        for name in audit_names:
            path = SPEC / name
            digests[name] = sha(path)
            for ref, result in json.loads(path.read_text())["results"].items():
                if ref in audits:
                    raise ValueError(f"audit outcome repeated: {ref}")
                audits[ref] = result
        accepted = {
            ref: row
            for ref, row in state["candidate_decisions"].items()
            if row["outcome"] == "accepted"
        }
        if not set(audits) <= set(accepted):
            raise ValueError(f"audit refers to non-accept in {batch}")
        for ref, row in sorted(accepted.items()):
            audit = audits.get(ref)
            records.append(
                {
                    "batch": batch,
                    "candidate_ref": ref,
                    "production_features": features(row),
                    "audit_label": label_of(audit),
                    "original_audit_verdict": audit.get("verdict") if audit else None,
                    "material_false_positive": audit.get("material_false_positive")
                    if audit
                    else None,
                    "audit_observed": audit is not None,
                }
            )
    if Counter(row["batch"] for row in records) != {"batch1": 44, "batch2": 40, "batch3": 38}:
        raise ValueError("fresh-batch cohort identity changed")
    return records, digests


def deterministic_reasons(row: dict, policy: str) -> list[str]:
    features_ = row["production_features"]
    confidence = features_["confidence_tier"]
    flags = set(features_["review_flags"])
    reasons = []
    if features_["relation"] == "false-friend":
        reasons.append("false-friend")
    if policy in {"A-confidence-heavy", "B-confidence-plus-flags"}:
        if confidence in {"low", "very-low"}:
            reasons.append(f"confidence:{confidence}")
    elif policy == "C-risk-first":
        if confidence == "low":
            reasons.append("confidence:low")
        if confidence == "very-low" and features_["signals"]["verifier-concern"]:
            reasons.append("very-low-with-verifier-concern")
    else:
        raise ValueError(policy)
    if policy == "B-confidence-plus-flags":
        reasons += [f"flag:{flag}" for flag in sorted(flags & GENERAL_FLAGS)]
    elif policy == "C-risk-first":
        reasons += [f"flag:{flag}" for flag in sorted(flags & FOCUSED_FLAGS)]
    return reasons


def sample_rate(confidence: str | None) -> float:
    return 0.10 if confidence == "high" else 0.15


def sampled_refs(rows: list[dict], deterministic: dict[str, list[str]], policy: str) -> set[str]:
    """Stable per-batch stratified sampling; salt is fixed before outcome inspection."""
    sampled = set()
    for batch in BATCHES:
        by_tier = defaultdict(list)
        for row in rows:
            ref = row["candidate_ref"]
            if row["batch"] == batch and ref not in deterministic:
                by_tier[row["production_features"]["confidence_tier"]].append(ref)
        for tier, refs in by_tier.items():
            count = math.ceil(sample_rate(tier) * len(refs))
            ranked = sorted(
                refs,
                key=lambda ref: hashlib.sha256(
                    f"feature003-audit-v1|{batch}|{tier}|{ref}".encode()
                ).hexdigest(),
            )
            sampled.update(ranked[:count])
    return sampled


def evaluate(rows: list[dict], policy: str) -> dict:
    deterministic = {
        row["candidate_ref"]: reasons
        for row in rows
        if (reasons := deterministic_reasons(row, policy))
    }
    sampled = sampled_refs(rows, deterministic, policy)
    observed = [row for row in rows if row["audit_observed"]]
    critical = {row["candidate_ref"] for row in observed if row["audit_label"] == "critical"}
    good = {row["candidate_ref"] for row in observed if row["audit_label"] == "confirmed-safe"}
    all_refs = {row["candidate_ref"] for row in rows}
    selected = set(deterministic) | sampled
    return {
        "accept_count": len(rows),
        "labeled_count": len(observed),
        "audit_count": len(selected),
        "audit_percent": round(100 * len(selected) / len(rows), 2) if rows else None,
        "deterministic_count": len(deterministic),
        "random_count": len(sampled),
        "known_critical_total": len(critical),
        "critical_deterministic": len(critical & deterministic.keys()),
        "critical_random_only": len((critical & sampled) - deterministic.keys()),
        "critical_missed": sorted(critical - selected),
        "confirmed_good_audited": len(good & selected),
        "unlabeled_selected": len(selected - {row["candidate_ref"] for row in observed}),
        "deterministic_reasons": {
            ref: reasons for ref, reasons in deterministic.items() if ref in all_refs
        },
        "random_refs": sorted(sampled),
    }


def signal_metrics(rows: list[dict]) -> dict:
    observed = [row for row in rows if row["audit_observed"]]
    critical_all = {row["candidate_ref"] for row in observed if row["audit_label"] == "critical"}
    result = {}
    for signal in SIGNALS:
        carrying = [row for row in observed if row["production_features"]["signals"][signal]]
        crit = {row["candidate_ref"] for row in carrying if row["audit_label"] == "critical"}
        safe = sum(row["audit_label"] == "confirmed-safe" for row in carrying)
        correctable = sum(row["audit_label"] == "correctable" for row in carrying)
        others = [other for other in SIGNALS if other != signal]
        exclusive = sum(
            row["audit_label"] == "critical"
            and not any(row["production_features"]["signals"][other] for other in others)
            for row in carrying
        )
        result[signal] = {
            "audited_carriers": len(carrying),
            "critical": len(crit),
            "confirmed_safe": safe,
            "correctable": correctable,
            "critical_precision": round(len(crit) / len(carrying), 3) if carrying else None,
            "critical_recall_contribution": round(len(crit) / len(critical_all), 3)
            if critical_all
            else None,
            "exclusive_critical": exclusive,
            "batch_carriers": dict(Counter(row["batch"] for row in carrying)),
        }
    return result


def signal_overlap(rows: list[dict]) -> list[dict]:
    """Pairwise overlap of production signals among independently audited cards."""
    observed = [row for row in rows if row["audit_observed"]]
    pairs = []
    for index, left in enumerate(SIGNALS):
        for right in SIGNALS[index + 1 :]:
            both = [
                row
                for row in observed
                if row["production_features"]["signals"][left]
                and row["production_features"]["signals"][right]
            ]
            if both:
                pairs.append(
                    {
                        "left": left,
                        "right": right,
                        "audited_overlap": len(both),
                        "critical_overlap": sum(row["audit_label"] == "critical" for row in both),
                    }
                )
    return sorted(pairs, key=lambda item: (-item["audited_overlap"], item["left"], item["right"]))


def main() -> None:
    records, digests = load_cohort()
    policies = ("A-confidence-heavy", "B-confidence-plus-flags", "C-risk-first")
    pooled = {policy: evaluate(records, policy) for policy in policies}
    by_batch = {
        batch: {
            policy: evaluate([row for row in records if row["batch"] == batch], policy)
            for policy in policies
        }
        for batch in BATCHES
    }
    # Train-only selection illustrates batch separation. Utility rewards caught
    # critical labels, charges audits, and never sees the held-out batch label.
    folds = {}
    for held_out in BATCHES:
        train = [row for row in records if row["batch"] != held_out]
        scores = {}
        for policy in policies:
            metric = evaluate(train, policy)
            caught = metric["critical_deterministic"] + metric["critical_random_only"]
            scores[policy] = (10 * caught - metric["audit_count"], caught, -metric["audit_count"])
        chosen = max(policies, key=lambda policy: scores[policy])
        test = [row for row in records if row["batch"] == held_out]
        folds[held_out] = {
            "training_batches": [batch for batch in BATCHES if batch != held_out],
            "training_scores": {policy: list(score) for policy, score in scores.items()},
            "chosen_policy": chosen,
            "held_out_metrics": evaluate(test, chosen),
        }
    result = {
        "schema_version": 1,
        "purpose": "read-only audit routing calibration; no generation or production changes",
        "input_sha256": digests,
        "feature_provenance": "candidate_decisions in frozen production state only",
        "label_provenance": "independent audit JSON only; never included in production_features",
        "records": records,
        "signal_metrics": signal_metrics(records),
        "signal_pairwise_overlap": signal_overlap(records),
        "pooled_historical_fit": pooled,
        "per_batch_fixed_policy_evaluation": by_batch,
        "leave_one_batch_out_train_selected": folds,
        "sample_rule": (
            "10% of otherwise-clean high; 15% of other otherwise-clean tiers, "
            "ceil within each batch/tier, fixed hash salt"
        ),
        "limitations": [
            "Batch 1/2 lack structured preference_risk; missing is not no-concern.",
            "Batch 3 audited 23/38 accepts; performance against unknown labels is censored.",
            "Exploratory policies: leave-one-out does not erase researcher knowledge of batches.",
        ],
    }
    atomic_json(OUTPUT, result)
    for policy in policies:
        x = pooled[policy]
        print(
            policy,
            x["audit_count"],
            x["known_critical_total"],
            x["critical_deterministic"],
            x["critical_random_only"],
            len(x["critical_missed"]),
        )


if __name__ == "__main__":
    main()
