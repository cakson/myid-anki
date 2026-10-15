#!/usr/bin/env python3
"""One bounded Luna evidence-interpretation call on a frozen, evidence-complete hold."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from compare_historical_verifiers import call_model

from indo_malay_anki.curation.gate import preverification_reasons
from indo_malay_anki.curation.store import BatchStore, atomic_json
from indo_malay_anki.curation.workflow import current_results

REFS = (
    "university-001:university-study-03",
    "food-001:foods-01",
    "home-001:topic-08",
)


def main() -> None:
    root = Path.cwd()
    output = root / "specs/003-vocabulary-curation/evidence-verifier-results.json"
    state = (
        json.loads(output.read_text(encoding="utf-8"))
        if output.exists()
        else {"schema_version": 1, "purpose": "Bounded evidence interpreter", "results": []}
    )
    config = json.loads((root / "curation/config.json").read_text())
    model = config["role_models"]["independent-verification"]["model"]
    for ref in REFS:
        if any(item["candidate_ref"] == ref for item in state["results"]):
            continue
        batch, candidate_id = ref.split(":", 1)
        store = BatchStore(root, batch)
        candidate = store.candidate(candidate_id)
        stages = current_results(store, candidate_id)
        if preverification_reasons(candidate, stages):
            raise SystemExit(f"claim evidence gate is incomplete for {ref}")
        context = {
            "candidate": candidate,
            "indonesian_usage": stages["indonesian-usage"],
            "malaysian_usage": stages["malaysian-usage"],
            "relation_proposal": stages["relation-proposal"],
            "audited_observations": stages["evidence-audit"]["observations"],
        }
        prompt = (
            "Independently interpret these inspected sources for one vocabulary card. "
            "Use only supplied evidence; do not browse. Judge neutral English sense, "
            "common use in each country, and independently classify relation as same, "
            "similar, different-common-word, or false-friend. Related expressions with "
            "recognizable form and same sense may be similar even when the full phrases "
            "are not identical. For domain-specific concepts, judge normal use within that "
            "domain; unrestricted casual frequency is not required. Dictionary presence "
            "alone does not prove everyday preference. Separate concrete material risks "
            "that would mislead a learner from general study limitations. Return one JSON "
            "object with verdict ('agree' or 'object'), relation, concerns (array of all "
            "limitations), material_concerns (array of concrete unresolved risks only), "
            "and rationale. Do not approve to meet a corpus target.\n"
            + json.dumps(context, ensure_ascii=False, sort_keys=True)
        )
        with tempfile.TemporaryDirectory(prefix="myid-evidence-verifier-") as temporary:
            result = call_model(root, Path(temporary), ref, model, prompt)
        result["prompt_sha256"] = hashlib.sha256(prompt.encode()).hexdigest()
        result["evidence_digest"] = hashlib.sha256(
            json.dumps(context["audited_observations"], sort_keys=True).encode()
        ).hexdigest()
        state["results"].append(result)
        atomic_json(output, state)
        print(json.dumps({key: value for key, value in result.items() if key != "response_text"}))


if __name__ == "__main__":
    main()
