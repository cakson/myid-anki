"""Feature 004 resumable production-run command line interface."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from indo_malay_anki.curation.store import atomic_json, read_json

from .audit import audit_run
from .coverage import allocation_draft, approve_allocation, inventory, set_draft
from .promotion import promote_run
from .qa import dispose_brake, record_finding, resolve_finding, review_sample, select_sample
from .report import run_report
from .store import RunError, RunStore
from .workflow import (
    build_run,
    close_run,
    curate_run,
    generate_run,
    pause,
    reconcile_artifacts,
    resolve_candidate,
    resume,
)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(prog="python -m indo_malay_anki.scaling")
    sub = command.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--run", required=True)
    create.add_argument("--count", type=int, required=True)
    create.add_argument("--proposal-cap", type=int)
    create.add_argument("--json", action="store_true")
    allocation = sub.add_parser("allocation")
    allocation.add_argument("--run", required=True)
    allocation.add_argument("--set", action="append", default=[])
    allocation.add_argument("--reason")
    allocation.add_argument("--json", action="store_true")
    approve = sub.add_parser("approve")
    approve.add_argument("--run", required=True)
    approve.add_argument("--reason")
    approve.add_argument("--json", action="store_true")
    for name in ("status", "report"):
        item = sub.add_parser(name)
        item.add_argument("--run", required=True)
        item.add_argument("--json", action="store_true")
    for name in (
        "generate",
        "curate",
        "risk-audit",
        "promote",
        "build",
        "qa-select",
        "qa-run",
        "close",
    ):
        item = sub.add_parser(name)
        item.add_argument("--run", required=True)
        item.add_argument("--resume", action="store_true")
        item.add_argument("--json", action="store_true")
    paused = sub.add_parser("pause")
    paused.add_argument("--run", required=True)
    paused.add_argument("--reason", required=True)
    paused.add_argument("--json", action="store_true")
    resumed = sub.add_parser("resume")
    resumed.add_argument("--run", required=True)
    resumed.add_argument("--resolution", required=True)
    resumed.add_argument("--json", action="store_true")
    disposition = sub.add_parser("brake-disposition")
    disposition.add_argument("--run", required=True)
    disposition.add_argument("--reason", required=True)
    disposition.add_argument("--resolution", required=True)
    disposition.add_argument("--json", action="store_true")
    correction = sub.add_parser("resolve")
    correction.add_argument("--run", required=True)
    correction.add_argument("--candidate", required=True)
    correction.add_argument("--action", choices=("correct", "hold", "reject"), required=True)
    correction.add_argument("--reason", required=True)
    correction.add_argument("--record", type=Path)
    correction.add_argument("--reason-code")
    correction.add_argument("--json", action="store_true")
    qa_record = sub.add_parser("qa-record")
    qa_record.add_argument("--run", required=True)
    qa_record.add_argument("--candidate", required=True)
    qa_record.add_argument("--record", type=Path, required=True)
    qa_record.add_argument("--json", action="store_true")
    qa_resolve = sub.add_parser("qa-resolve")
    qa_resolve.add_argument("--run", required=True)
    qa_resolve.add_argument("--candidate", required=True)
    qa_resolve.add_argument("--reason", required=True)
    qa_resolve.add_argument("--json", action="store_true")
    return command


def _baseline_count(root: Path) -> int:
    source = root / "data" / "vocabulary.tsv"
    if not source.exists():
        return 0
    with source.open(encoding="utf-8", newline="") as stream:
        return sum(1 for _ in csv.DictReader(stream, delimiter="\t"))


def _create(root: Path, args: argparse.Namespace) -> dict:
    store = RunStore(root, args.run)
    cap = args.proposal_cap if args.proposal_cap is not None else args.count * 2
    if store.manifest_path.exists():
        prior = store.load()
        if prior["requested_count"] != args.count or prior["proposal_cap"] != cap:
            raise RunError("conflicting create replay")
        return prior
    manifest = store.create(
        requested_count=args.count, proposal_cap=cap, baseline_count=_baseline_count(root)
    )
    snapshot = inventory(root)
    draft = allocation_draft(snapshot, args.count, root)
    atomic_json(store.path / "coverage-draft.json", snapshot)
    updated = {
        **manifest,
        "allocation_proposal": draft["counts"],
        "allocation_draft": draft["counts"],
        "allocation_rationale": draft["rationale"],
        "category_strategy_version": draft["strategy_version"],
    }
    store.save(updated, expected_digest=store.manifest_digest())
    return store.load()


def _allocation(root: Path, args: argparse.Namespace) -> dict:
    store = RunStore(root, args.run)
    manifest = store.load()
    if args.set:
        counts = dict(manifest["allocation_draft"])
        for item in args.set:
            name, separator, raw_count = item.partition("=")
            if not separator:
                raise RunError("--set requires category=count")
            try:
                counts[name] = int(raw_count)
            except ValueError as exc:
                raise RunError("--set count must be an integer") from exc
        manifest = set_draft(store, counts, reason=args.reason or "maintainer edit")
    return {
        "run_id": args.run,
        "state": manifest["state"],
        "draft": manifest["allocation_draft"],
        "rationale": manifest.get("allocation_rationale", []),
    }


def _approve(root: Path, args: argparse.Namespace) -> dict:
    store = RunStore(root, args.run)
    manifest = store.load()
    if manifest["state"] != "draft":
        raise RunError("approval requires draft state")
    if manifest["allocation_draft"] != manifest.get("allocation_proposal") and not args.reason:
        raise RunError("edited allocation approval requires --reason")
    snapshot = read_json(store.path / "coverage-draft.json")
    return approve_allocation(
        store,
        manifest["allocation_draft"],
        snapshot,
        reason=args.reason or "coverage draft accepted",
    )


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path.cwd()
    try:
        if args.command == "create":
            result = _create(root, args)
        elif args.command == "allocation":
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = _allocation(root, args)
        elif args.command == "approve":
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = _approve(root, args)
        elif args.command == "generate":
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = generate_run(store)
        elif args.command == "curate":
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = curate_run(store)
        elif args.command == "risk-audit":
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = audit_run(store)
        elif args.command == "promote":
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = promote_run(store)
        elif args.command == "build":
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = build_run(store)
        elif args.command == "qa-select":
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = select_sample(store)
        elif args.command == "qa-run":
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = review_sample(store)
        elif args.command == "close":
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = close_run(store)
        elif args.command == "pause":
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = pause(store, args.reason)
        elif args.command == "resume":
            store = RunStore(root, args.run)
            with store.operation_lock():
                mismatches = reconcile_artifacts(store)
                if mismatches:
                    raise RunError(f"artifact mismatch on resume: {mismatches}")
                result = resume(store, args.resolution)
        elif args.command == "brake-disposition":
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = dispose_brake(store, args.reason, args.resolution)
        elif args.command == "resolve":
            changes = read_json(args.record) if args.record else None
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = resolve_candidate(
                    store,
                    args.candidate,
                    args.action,
                    args.reason,
                    changes=changes,
                    reason_code=args.reason_code,
                )
        elif args.command == "qa-record":
            slice_id, separator, candidate_id = args.candidate.partition(":")
            if not separator:
                raise RunError("qa-record requires slice:candidate")
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = record_finding(store, slice_id, candidate_id, read_json(args.record))
        elif args.command == "qa-resolve":
            slice_id, separator, candidate_id = args.candidate.partition(":")
            if not separator:
                raise RunError("qa-resolve requires slice:candidate")
            store = RunStore(root, args.run)
            with store.operation_lock():
                result = resolve_finding(store, slice_id, candidate_id, args.reason)
        else:
            store = RunStore(root, args.run)
            result = store.load()
            if args.command == "report":
                result = run_report(store)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            state = result.get("state") or RunStore(root, args.run).load()["state"]
            print(f"{args.run}: {state} ({root / 'curation/production-runs' / args.run})")
        return 0
    except (RunError, OSError, ValueError) as exc:
        try:
            store = RunStore(root, args.run)
            if store.manifest_path.exists():
                store.append_event(args.command, "failed", details={"error": str(exc)})
        except (RunError, OSError):
            pass
        print(f"scaling {args.command}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
