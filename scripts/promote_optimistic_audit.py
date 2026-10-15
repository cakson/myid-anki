#!/usr/bin/env python3
"""Guarded, idempotent promotion of the frozen and independently audited cohort."""
# ruff: noqa: E501

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

from indo_malay_anki.curation.duplicates import find_deterministic_overlaps
from indo_malay_anki.curation.export import _source_rows, commit_learner_rows, recover_export
from indo_malay_anki.curation.ids import allocate_id, append_assignment, assigned_id, load_ledger
from indo_malay_anki.curation.store import BatchStore, atomic_json
from indo_malay_anki.curation.workflow import current_results, utc_now
from indo_malay_anki.validator import validate_vocabulary

SPEC = Path("specs/003-vocabulary-curation")
PENCIL = "school-001:topic-05"
CAMERA = "technology-001:technology-07"
REVIEW_REASONS = {
    "clothing-001:clothing-01": "Celana/seluar are natural trouser terms; medium retains the unresolved breadth of trousers versus shorter garments and limited comparative usage evidence.",
    "clothing-001:clothing-02": "Sepatu/kasut are clear everyday shoe defaults; medium retains limited independent usage corroboration despite a sound lexical contrast.",
    "common-verbs-001:everyday-actions-01": "Kirim/hantar fit sending an item; very-low reflects sparse source corroboration and narrower Malay kirim contexts, not a known translation defect.",
    "communication-001:communication-01": "Pesan/mesej fit a written message; medium flags pesan's other senses and incomplete preference evidence, which the cue resolves.",
    "communication-001:communication-03": "Obrolan/sembang fit a casual conversation; very-low retains the digital-chat overlap and sparse preference evidence after narrowing the cue.",
    "everyday-objects-001:everyday-objects-05": "Terong/terung are useful eggplant spelling defaults; medium retains cross-border variant use without a semantic objection.",
    "everyday-objects-001:everyday-objects-06": "Semangka/tembikai clearly mean watermelon; very-low records sparse archived corroboration, not a concrete rival meaning.",
    "food-001:foods-01": "Makan siang/makan tengah hari both mean lunch; medium retains a previously corrected relation despite aligned government usage examples.",
    "food-001:foods-04": "Enak/sedap are useful tasty-food defaults; low retains the real Malay enak synonym and uncertain comparative preference.",
    "food-001:foods-06": "Biskuit/biskut match a dry baked snack; low retains historical category-boundary concern despite a clear spelling contrast.",
    "health-001:health-01": "Obat/ubat are neutral medicine terms; medium reflects limited audit evidence while the stated treatment sense is aligned.",
    "home-001:topic-02": "Kamar tidur/bilik tidur both mean bedroom; low retains the historical bare-kamar/bilik alternative concern, not a mismatch.",
    "home-001:topic-03": "Kulkas/peti sejuk are valid refrigerator defaults; low retains Malay peti ais as a common alternative and a corrected historical synonym note.",
    "home-001:topic-04": "Jendela/tingkap are useful window defaults; medium records correction of an overly narrow glass-only internal sense.",
    "home-001:topic-05": "Tempat sampah/tong sampah fit a household bin; medium retains limited comparison of cross-border alternatives.",
    "home-001:topic-06": "Ember/baldi fit a handled bucket; low retains the valid Malay timba synonym and earlier preference objection.",
    "home-001:topic-08": "Kursi/kerusi are common matching chair terms with a straightforward spelling contrast and no material objection; high is warranted by these aligned signals.",
    "places-001:places-01": "Kantor/pejabat fit an office; medium keeps attention on Indonesian pejabat's different official-person sense.",
    "produce-001:produce-03": "Pepaya/betik are ordinary papaya names; very-low reflects sparse archived preference evidence, not a contrary meaning.",
    "school-001:topic-06": "Penghapus/pemadam fit a school eraser; very-low retains sparse source comparison and the longer Malay getah pemadam variant.",
    "transportation-001:transportation-01": "Mobil/kereta are everyday passenger-car defaults; low retains corrected overbroad or rare alternative notes and historical usage concern.",
    "transportation-001:transportation-04": "Bus/bas give the standard spelling contrast; medium keeps the English or code-mixed bus spelling distinct from standard Malay bas.",
    "transportation-001:transportation-06": "Truk/lori both name a goods vehicle; medium retains limited preference evidence after correcting Malay alternative and size notes.",
    "university-001:university-study-03": "Beasiswa/biasiswa align for educational financial support; medium retains broader funding-label caveats despite a stable spelling contrast.",
    PENCIL: "Pensil/pensel are matching standard pencil forms; medium retains the attested Malaysian pensil variant while DBP explicitly recommends pensel.",
}

USAGE_UPDATES = {
    "communication-001:communication-03": {
        "indonesian": {
            "preferred": "Obrolan is natural for informal conversation; chat is often preferred for a digital app feature."
        },
        "malaysian": {
            "preferred": "Sembang is natural for informal conversation; chat is also common for digital exchanges."
        },
    },
    "food-001:foods-04": {
        "malaysian": {
            "preferred": "Sedap is a characteristic everyday choice for tasty food; enak is also natural in Malay.",
            "alternatives": [
                "enak (also natural for tasty food)",
                "lazat (more emphatic or promotional)",
            ],
        }
    },
    "home-001:topic-03": {
        "malaysian": {
            "preferred": "Peti sejuk is a neutral standard choice; peti ais is also common, so neither is claimed uniquely preferred.",
            "alternatives": ["peti ais", "peti air batu"],
        }
    },
    "transportation-001:transportation-01": {
        "indonesian": {"alternatives": ["oto", "otomobil"]},
        "malaysian": {
            "common_use": "Kereta is the normal everyday Malaysian term for a passenger car; the recognition rate of Indonesian mobil is unmeasured.",
            "alternatives": ["motokar (less conversational)"],
        },
    },
    "transportation-001:transportation-04": {"malaysian": {"alternatives": []}},
    "transportation-001:transportation-06": {
        "malaysian": {
            "meaning": "Lori denotes a road motor vehicle for carrying goods; it need not be very large.",
            "alternatives": [],
        }
    },
    PENCIL: {
        "indonesian": {"preferred": "Pensil is the normal standard and everyday Indonesian term."},
        "malaysian": {
            "preferred": "Pensel is the standard Malaysian spelling and normal learner default; pensil also occurs but does not displace it.",
            "alternatives": ["pensil (attested secondary spelling or variant)"],
        },
    },
}

FLAG_UPDATES = {
    "communication-001:communication-03": [
        "limited-evidence",
        "semantic-ambiguity",
        "usage-preference-weak",
    ],
    "food-001:foods-04": ["historical-objection", "usage-preference-weak"],
    "home-001:topic-03": ["historical-objection", "usage-preference-weak"],
    "transportation-001:transportation-01": ["historical-objection", "usage-preference-weak"],
    "transportation-001:transportation-04": ["spelling-variant"],
    "transportation-001:transportation-06": ["usage-preference-weak"],
    PENCIL: ["spelling-variant", "historical-objection"],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_inputs(root: Path) -> tuple[dict, dict]:
    replay = json.loads((root / SPEC / "optimistic-replay-report.json").read_text())
    audit = json.loads((root / SPEC / "optimistic-audit-model.json").read_text())
    accepted = [row for row in replay["rows"] if row["outcome"] == "accepted"]
    if len(replay["rows"]) != 26 or len(accepted) != 24 or len(audit["results"]) != 25:
        raise ValueError("frozen replay or full audit cohort changed")
    if {row["candidate_ref"] for row in accepted} | {PENCIL} != set(audit["results"]):
        raise ValueError("audit candidate IDs do not match the frozen promotion cohort")
    if set(REVIEW_REASONS) != set(audit["results"]):
        raise ValueError("candidate-specific rationales are incomplete")
    if next(row for row in replay["rows"] if row["candidate_ref"] == CAMERA)["relation"] != "same":
        raise ValueError("camera must remain a no-contrast reject")
    for row in accepted:
        finding = audit["results"][row["candidate_ref"]]
        if finding["audit_result"] not in {"confirmed-good", "needs-correction"}:
            raise ValueError(f"audit does not clear {row['candidate_ref']}")
        if finding["material_false_positive"] or finding["relation"] != row["relation"]:
            raise ValueError(f"material or relation disagreement: {row['candidate_ref']}")
    return replay, audit


def corrected_item(root: Path, row: dict, finding: dict) -> dict:
    ref = row["candidate_ref"]
    batch_id, candidate_id = ref.split(":", 1)
    store = BatchStore(root, batch_id)
    candidate = copy.deepcopy(store.candidate(candidate_id))
    if candidate != row["candidate"]:
        raise ValueError(f"archived candidate changed since replay: {ref}")
    stages = current_results(store, candidate_id)
    usage = {
        locale: copy.deepcopy(stages.get(role, {}))
        for locale, role in (("indonesian", "indonesian-usage"), ("malaysian", "malaysian-usage"))
    }
    if ref == "communication-001:communication-03":
        candidate["english"] = "casual conversation"
        candidate["sense"] = "an informal or relaxed conversation"
    if ref == "home-001:topic-04":
        candidate["sense"] = (
            "opening in a wall or building admitting light or air, usually fitted with glass"
        )
    for locale, edits in USAGE_UPDATES.get(ref, {}).items():
        usage[locale].update(edits)
    flags = FLAG_UPDATES.get(ref)
    if flags is None:
        flags = [
            flag for flag in row.get("review_flags", []) if flag != "limited-verifier-agreement"
        ]
    if ref == "food-001:foods-01" and "relation-corrected" not in flags:
        flags.append("relation-corrected")
    if ref == "places-001:places-01" and "semantic-ambiguity" not in flags:
        flags.append("semantic-ambiguity")
    return {
        "candidate_ref": ref,
        "candidate": candidate,
        "relation": row["relation"],
        "original_decision": row["outcome"],
        "final_decision": "accepted",
        "original_confidence": row.get("confidence_tier"),
        "confidence": row.get("confidence_tier"),
        "confidence_rationale": REVIEW_REASONS[ref],
        "original_review_flags": row.get("review_flags", []),
        "review_flags": sorted(set(flags)),
        "audit_verdict": finding["audit_result"],
        "audit_reason": finding["reason"],
        "audit_corrections": finding.get("corrections", {}),
        "applied_corrections": {
            "english": candidate["english"]
            if candidate["english"] != row["candidate"]["english"]
            else None,
            "sense": candidate["sense"]
            if candidate["sense"] != row["candidate"]["sense"]
            else None,
            "usage": USAGE_UPDATES.get(ref, {}),
            "confidence_rationale": REVIEW_REASONS[ref],
            "review_flags": sorted(set(flags)),
        },
        "corrected_usage": usage,
        "historical_provenance": {
            "batch_id": batch_id,
            "candidate_id": candidate_id,
            "event_count": len(store.events(candidate_id)),
            "replay_artifact": str(SPEC / "optimistic-replay-report.json"),
            "audit_artifact": str(SPEC / "optimistic-audit-model.json"),
        },
    }


def pencil_item(root: Path, replay: dict, audit: dict) -> dict:
    row = next(row for row in replay["rows"] if row["candidate_ref"] == PENCIL)
    finding = audit["results"][PENCIL]
    if row["outcome"] != "hold" or row["relation"] != "similar":
        raise ValueError("pencil historical decision changed")
    if finding["audit_result"] != "needs-correction" or finding["material_false_positive"]:
        raise ValueError("pencil audit no longer supports reconsideration")
    item = corrected_item(root, row, finding)
    item["confidence"] = "medium"
    item["review_flags"] = FLAG_UPDATES[PENCIL]
    item["decision_change_reason"] = (
        "The historical concern was Malaysian pensil as a rival spelling. DBP explicitly "
        "identifies pensel as correct; the independent audit found the variant nonblocking. "
        "No concrete material learner risk remains."
    )
    item["supporting_references"] = [
        "https://prpm.dbp.gov.my/Cari1?d=175768&keyword=pensil",
        "https://prpm.dbp.gov.my/Cari1?d=371752&keyword=Pensel",
    ]
    item["applied_corrections"]["decision"] = "hold → accepted"
    item["applied_corrections"]["confidence"] = "medium"
    return item


def build_items(root: Path, replay: dict, audit: dict) -> list[dict]:
    items = [
        corrected_item(root, row, audit["results"][row["candidate_ref"]])
        for row in replay["rows"]
        if row["outcome"] == "accepted"
    ]
    items.append(pencil_item(root, replay, audit))
    if len(items) != 25 or len({item["candidate_ref"] for item in items}) != 25:
        raise ValueError("promotion cohort must contain 25 unique audited candidates")
    return items


def promote(root: Path, *, dry_run: bool) -> dict:
    root = Path(root)
    replay, audit = checked_inputs(root)
    recover_export(root)
    existing_record = root / "curation/promotions/optimistic-audit-001.json"
    if existing_record.exists() and not dry_run:
        prior = json.loads(existing_record.read_text())
        if (
            prior.get("status") == "promoted"
            and prior.get("source_digest_after") == sha(root / "data/vocabulary.tsv")
            and prior.get("replay_digest") == sha(root / SPEC / "optimistic-replay-report.json")
            and prior.get("audit_digest") == sha(root / SPEC / "optimistic-audit-model.json")
        ):
            return prior
        raise ValueError("promotion record exists but its source or audit digest differs")
    items = build_items(root, replay, audit)
    source = root / "data/vocabulary.tsv"
    old_digest = sha(source)
    rows = _source_rows(source)
    old_by_id = {row["id"]: row for row in rows}
    ledger = copy.deepcopy(load_ledger(root))
    projected = []
    for item in items:
        candidate = item["candidate"]
        ref = item["candidate_ref"]
        batch_id, candidate_id = ref.split(":", 1)
        if item["relation"] not in {"similar", "different-common-word", "false-friend"}:
            raise ValueError(f"ineligible relation: {ref}")
        if item["relation"] == "false-friend":
            raise ValueError(
                "this ordinary audit cohort contains no verified false-friend contrast"
            )
        prior = assigned_id(ledger, batch_id, candidate_id)
        legacy = candidate.get("legacy_id")
        if legacy and prior and prior != legacy:
            raise ValueError(f"legacy concept identity mismatch: {ref}")
        if legacy and not any(assignment["id"] == legacy for assignment in ledger["assignments"]):
            raise ValueError(f"legacy concept ID is absent from ledger: {ref}")
        if legacy and (candidate["english"], candidate["indonesian"], candidate["malaysian"]) != (
            "car",
            "mobil",
            "kereta",
        ):
            raise ValueError("retired car identity cannot be repurposed")
        concept_id = prior or legacy or allocate_id(ledger)
        if not prior and not legacy:
            append_assignment(
                ledger,
                concept_id=concept_id,
                batch_id=batch_id,
                candidate_id=candidate_id,
                assigned_at=utc_now(),
                semantic_concept_key=candidate["sense"],
            )
        row = {
            "id": concept_id,
            "english": candidate["english"],
            "indonesian": candidate["indonesian"],
            "malaysian": candidate["malaysian"],
            "relation": item["relation"],
            "image": candidate.get("image", ""),
            "tags": " ".join(candidate.get("tags", [])),
            "contrast": "",
        }
        item["concept_id"] = concept_id
        item["learner_row"] = row
        projected.append(row)
    by_id = dict(old_by_id)
    for item in items:
        row = item["learner_row"]
        others = [
            other
            for other in list(by_id.values()) + projected
            if other is not row and other["id"] != row["id"]
        ]
        overlaps = find_deterministic_overlaps(row, others)
        if overlaps:
            raise ValueError(
                f"unresolved duplicate before promotion: {item['candidate_ref']}: {overlaps}"
            )
        by_id[row["id"]] = row
    if sha(source) != old_digest:
        raise ValueError("canonical learner source changed during preflight")
    if not dry_run:
        commit_learner_rows(root, list(by_id.values()), ledger, ["optimistic-audit-001"])
        validate_vocabulary(source, root / "media")
    result = {
        "schema_version": 1,
        "promotion_id": "optimistic-audit-001",
        "status": "dry-run" if dry_run else "promoted",
        "source_digest_before": old_digest,
        "source_digest_after": sha(source) if not dry_run else None,
        "replay_digest": sha(root / SPEC / "optimistic-replay-report.json"),
        "audit_digest": sha(root / SPEC / "optimistic-audit-model.json"),
        "learner_rows_before": len(rows),
        "learner_rows_added": len(set(by_id) - set(old_by_id)),
        "learner_rows_corrected": sum(
            item["id"] in old_by_id and old_by_id[item["id"]] != item for item in projected
        ),
        "learner_rows_after": len(by_id),
        "relation_distribution": dict(Counter(row["relation"] for row in by_id.values())),
        "promoted_confidence_distribution": dict(Counter(item["confidence"] for item in items)),
        "excluded": [{"candidate_ref": CAMERA, "reason": "no-meaningful-cross-language-contrast"}],
        "items": items,
    }
    if not dry_run:
        atomic_json(root / "curation/promotions/optimistic-audit-001.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = promote(Path.cwd(), dry_run=args.dry_run)
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "items"},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
