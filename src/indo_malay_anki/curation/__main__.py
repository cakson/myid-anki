"""Separate, file-backed AI curation CLI; ordinary deck builds never import this module."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .bundle import ingest_bundle, packet_bundle
from .export import ExportError, export_batches
from .models import role_route
from .records import AI_ROLES, RecordError
from .report import batch_report
from .store import BatchStore
from .workflow import (
    check_candidate,
    finalize_hold,
    finalize_reject,
    ingest_response,
    init_batch,
    packet_for,
    reopen_candidate,
    revise_candidate,
)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(prog="python -m indo_malay_anki.curation")
    sub = command.add_subparsers(dest="command", required=True)
    create = sub.add_parser("init")
    create.add_argument("--batch", required=True)
    create.add_argument("--topic", required=True)
    create.add_argument("--limit", type=int, default=12)
    create.add_argument("--scope", default="Everyday usage")
    for name in ("packet", "ingest"):
        stage = sub.add_parser(name)
        stage.add_argument("--batch", required=True)
        stage.add_argument("--role", required=True, choices=AI_ROLES)
        stage.add_argument("--candidate")
        if name == "ingest":
            stage.add_argument("--response", type=Path, required=True)
            stage.add_argument("--actual-model")
    for name in ("bundle", "ingest-bundle"):
        stage = sub.add_parser(name)
        stage.add_argument("--batch", required=True)
        stage.add_argument("--role", required=True, choices=AI_ROLES[1:])
        stage.add_argument("--candidate", action="append")
        if name == "ingest-bundle":
            stage.add_argument("--response", type=Path, required=True)
            stage.add_argument("--actual-model")
    for name in ("check", "report"):
        stage = sub.add_parser(name)
        stage.add_argument("--batch", required=True)
    hold = sub.add_parser("finalize-hold")
    hold.add_argument("--batch", required=True)
    hold.add_argument("--candidate", required=True)
    hold.add_argument("--reason", required=True)
    reject = sub.add_parser("finalize-reject")
    reject.add_argument("--batch", required=True)
    reject.add_argument("--candidate", required=True)
    reject.add_argument("--reason", required=True)
    reopen = sub.add_parser("reopen")
    reopen.add_argument("--batch", required=True)
    reopen.add_argument("--candidate", required=True)
    reopen.add_argument("--reason", required=True)
    revise = sub.add_parser("revise")
    revise.add_argument("--batch", required=True)
    revise.add_argument("--candidate", required=True)
    revise.add_argument("--reason", required=True)
    for field in ("english", "indonesian", "malaysian", "sense"):
        revise.add_argument(f"--{field}")
    revise.add_argument("--tags", nargs="+")
    export = sub.add_parser("export")
    export.add_argument("--batch", required=True, action="append")
    route = sub.add_parser("route")
    route.add_argument("--role", required=True, choices=AI_ROLES)
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path.cwd()
    try:
        if args.command == "export":
            result = {"exported_ids": export_batches(root, args.batch)}
        elif args.command == "route":
            result = role_route(root, args.role)
        elif args.command == "init":
            store = init_batch(root, args.batch, args.topic, args.limit, args.scope)
            result = store.manifest().as_dict()
        else:
            store = BatchStore(root, args.batch)
            store.manifest()
            if args.command == "packet":
                result = packet_for(store, args.role, args.candidate)
                if args.role == "generate":
                    result["candidate_limit"] = store.manifest().candidate_limit
            elif args.command == "ingest":
                result = ingest_response(
                    store,
                    args.role,
                    args.response.read_text(encoding="utf-8"),
                    args.candidate,
                    args.actual_model,
                )
            elif args.command == "bundle":
                result = packet_bundle(
                    store, args.role, args.candidate or list(store.candidate_ids())
                )
            elif args.command == "ingest-bundle":
                result = {
                    "ingested": len(
                        ingest_bundle(
                            store,
                            args.role,
                            args.response,
                            args.candidate or list(store.candidate_ids()),
                            args.actual_model,
                        )
                    )
                }
            elif args.command == "check":
                result = {
                    candidate_id: check_candidate(store, candidate_id)
                    for candidate_id in store.candidate_ids()
                }
            elif args.command == "finalize-hold":
                result = finalize_hold(store, args.candidate, args.reason)
            elif args.command == "finalize-reject":
                result = finalize_reject(store, args.candidate, args.reason)
            elif args.command == "reopen":
                result = reopen_candidate(store, args.candidate, args.reason)
            elif args.command == "revise":
                changes = {
                    field: getattr(args, field)
                    for field in ("english", "indonesian", "malaysian", "sense", "tags")
                    if getattr(args, field) is not None
                }
                result = revise_candidate(store, args.candidate, changes, args.reason)
            else:
                result = batch_report(store)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (RecordError, ExportError, OSError, ValueError, KeyError) as exc:
        print(f"curation {args.command}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
