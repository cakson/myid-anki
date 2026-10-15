# Quickstart and Validation: AI-First Vocabulary Curation

This guide describes the workflow to validate once Feature 003 is implemented. See [curation workflow](contracts/curation-workflow.md) for command behavior and [learner source](contracts/learner-source.md) for TSV and Anki contracts.

## Prerequisites

- Python 3.12 or newer and the project's documented local environment.
- An AI tool that can follow each role prompt and return structured UTF-8 output.
- Access to claim-relevant Indonesian and Malaysian Malay references during curation.
- Anki Desktop for the pre-release old-to-new import check.

The curation tool may use the network while researching. `validate` and `build` must also work with network access disabled.

## Run one bounded batch

From the repository root, create a topic batch:

```sh
python -m indo_malay_anki.curation init --batch transportation-002 --topic transportation --limit 12
python -m indo_malay_anki.curation packet --batch transportation-002 --role generate
```

Run the generated prompt through an AI agent and save its structured response. Ingest it, then use `packet` and `ingest` for each required role and candidate in the order in [the workflow contract](contracts/curation-workflow.md). Keep Indonesian and Malaysian usage research separate. Give the independent verifier only the packet prepared for that role; do not append the generator's rationale or preferred acceptance result. Inspect cited source pages or corpus queries and record the access method, page location or query, and actual observation before evidence audit counts support. An AI-supplied audit flag alone does not count.
The generation packet contains a frozen list of previously investigated concepts. Its prompt
version is pinned in the batch manifest; old batches continue to use their archived prompt text.
For prompt sets `1.2.0`, `1.3.0`, `1.4.0`, and `1.5.0`, normalize candidates first, then inspect sources for promising
distinct candidates. Save each candidate's notes at
`curation/batches/BATCH/source-inspections/CANDIDATE.json` using
`curation/source-inspection-template.json`. Both locales and at least two independent
underlying source groups are required before either locale packet is available. Record
only pages or corpus results actually inspected; source notes do not count as audited
support until the evidence-audit stage tests each claim. Candidates without adequate
leads can be held before spending locale-role calls.
For several promising candidates, `bundle --role ROLE --candidate CID --candidate CID` and
`ingest-bundle` run one role over only those selected candidates. Keep Indonesian and Malaysian
usage in separate bundles. Do not include early held or rejected candidates in later bundles.

Before each role call, query `python -m indo_malay_anki.curation route --role ROLE` and use its
`model` and `reasoning_effort` for the Codex CLI invocation. The configured reserve policy uses
Luna for every role. Run independent verification and adversarial review as separate calls only
after the deterministic overlap, semantic alignment, and evidence checks leave a candidate
eligible. Give the verifier its packet in an isolated packet-only working directory so it cannot
inspect the relation proposal or previous answers through repository search. Sharing a model
across roles does not relax the evidence or disagreement gates.
Use `--actual-model MODEL/codex-cli` with `ingest` or `ingest-bundle` to record the invoked model
separately from the model name generated in the response. The evidence-audit packet is withheld
when claim IDs collide across roles or the cue/overlap screen fails.

### Local Codex CLI recovery on this macOS host

The installed CLI 0.160.0 currently fails before a model call because macOS managed preferences
cannot synchronize in this execution environment. The shell also lacks system DNS configuration.
The process-local launcher `scripts/curation_codex.py` starts a localhost HTTPS CONNECT tunnel,
resolves OpenAI hosts through the nameserver in `/etc/resolv.conf`, and supplies the local CA
bundle. It changes no system network settings. On this host, use the installed 0.153.0 binary:

```sh
python scripts/curation_codex.py \
  --codex-bin "$HOME/.codex/packages/standalone/releases/0.153.0-aarch64-apple-darwin/bin/codex" \
  -- exec -C /tmp -s read-only --skip-git-repo-check --ephemeral \
  -m gpt-5.6-luna -c 'model_reasoning_effort="low"' 'Reply with OK.'
```

This is a local recovery path, not a replacement for the centrally configured role routes.
Query `route` before each real stage and use its model and reasoning effort. The current ChatGPT
CLI model catalog lists `gpt-5.6-luna` and `gpt-5.6-sol`; earlier `gpt-6-*` routes now return
an unsupported-model error for this account. Keep the exact invoked model in the stage record.

After stage results are present:

```sh
python -m indo_malay_anki.curation check --batch transportation-002
python -m indo_malay_anki.curation report --batch transportation-002
```

Expected: a candidate with a deliberate final decision receives `accepted`, `hold`, or `rejected`; interrupted or malformed work remains `pending` until resumed or explicitly finalized, and pending candidates keep the batch open. To stop investigation deliberately, record a reason with `finalize-hold --batch transportation-002 --candidate CID --reason TEXT`; use `finalize-reject` for a disproven or unsuitable concept, then rerun `report`. An early final hold or rejection records uncompleted-stage statuses without invented role results. Open reports reconcile generated = accepted + held + rejected + pending; closed reports require pending = 0 and reconcile the three final outcomes before export. A closed batch with no accepted entries remains valid.

## Exercise the negative gates

In isolated test fixtures or a scratch batch, submit:

1. A proposed everyday preference backed only by dictionary existence.
2. A cue whose Indonesian and Malaysian answers use different English senses.
3. A plural or English synonym of an existing concept.
4. A false-friend claim without evidence for both meanings and the misleading contrast.
5. An inaccessible reference, contradictory usage observation, or verifier/challenger disagreement.

Run `check`. Expected: all are pending, deliberately held, rejected, or corrected and reverified before acceptance. No permanent IDs are allocated. A relation or cue correction invalidates stale verifier and adversarial results; an unfinished batch cannot close or export.

## Export only accepted entries

For the initial library, complete bounded category batches and inspect their reports. Submit only
closed batches for guarded cross-batch export; the following is a command pattern using batches
that have already been curated:

```sh
python -m indo_malay_anki.curation export --batch home-001 --batch food-001
python -m indo_malay_anki validate
python -m indo_malay_anki build
```

Expected: accepted new concepts receive unused six-digit IDs, held/rejected records stay outside `data/vocabulary.tsv`, and the ledger contains every active TSV ID. A repeated export allocates no further IDs. Export clears its recovery journal only after both source files agree; after interruption, recover before any later export or release. The build produces `dist/myid-anki.apkg` without model or network calls.

At least 24 accepted contrasts across three categories and all three eligible learner relations are required for initial-corpus completion. `same` candidates are rejected before evidence audit and never enter the TSV. Report any shortfall and curate another bounded batch; never weaken an acceptance gate or invent filler to meet it.

The original `000001` car concept was retrospectively held after independent verification and
adversarial review. It is retired from the active learner TSV, and its assignment remains in the
ledger. Shared ordinary entries `000002`, `000006`, and `000007` are retired under the contrast-only
policy. The current learner source has three accepted concepts, all in food; the 24-concept,
three-category, and three-relation target is still open. `growth-audit-001` is a non-learner fixture showing
malformed-output recovery and later-batch duplicate rejection.

## Verify identity and card behavior

Run the project test, lint, and format checks plus focused curation tests:

```sh
pytest
ruff check .
ruff format --check .
```

Inspect the generated package: one note/card per accepted ID; deck ID, model ID, five note field names/order, and `000001 -> D6BBAuKXK` unchanged. Confirm an ordinary card has a neutral front and both labeled answers on the back. For any accepted false friend, confirm its concise misleading-lookalike contrast appears only on the back; if none passes, use a separate validated fixture for that rendering check. Compare a package built before Feature 003 with the updated package by importing both in sequence into a test Anki Desktop profile. Confirm no duplicate notes, updated content for the same ID, and preserved scheduling; record the client version and import settings before release.

Finally, disable network access and rerun `python -m indo_malay_anki validate` and `build`. Both must succeed using the accepted TSV alone. Inspect `.github/workflows/release.yml` to ensure the release build invokes only accepted-source validation/build and never curation, AI, or live language research.
