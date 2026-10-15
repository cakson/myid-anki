# Curation Workflow Contract

## Boundary

The curation command is separate from `python -m indo_malay_anki validate` and `build`. It may use external AI and research tools through role prompt exchange; the two build commands never do. All command failures return nonzero status and identify batch/candidate/stage where possible. Writes to accepted learner source occur only through `export`.

## Commands

The implementation exposes equivalent subcommands under `python -m indo_malay_anki.curation`:

| Command | Input | Output / invariant |
|---|---|---|
| `init --batch ID --topic TOPIC --limit N` | New bounded topic | Creates manifest and empty record area; refuses duplicate ID |
| `packet --batch ID --role ROLE [--candidate CID]` | Existing state | Emits a versioned role prompt with only allowed context; verifier is blinded to generator rationale/verdict |
| `ingest --batch ID --role ROLE [--candidate CID] --response FILE` | Structured AI result | Validates schema, records raw and normalized result, role/tool/time/input digest; rejects malformed or out-of-order output |
| `check --batch ID` | Complete or partial stage records | Performs deterministic gates; incomplete or interrupted candidates remain `pending`, without permanent IDs |
| `finalize-hold --batch ID --candidate CID --reason TEXT` | Investigated candidate that cannot pass | Records an explicit final `hold` decision and reason; does not infer missing research or approve content |
| `report --batch ID` | Current batch decisions | Reports pending separately; closes only when all candidates have deliberate final outcomes, pending is zero, and counts reconcile |
| `export --batch ID [--batch ID ...]` | One or more closed batches and passing decisions | Screens the union for semantic overlap, then assigns IDs only to new accepted concepts and transactionally updates learner TSV and ledger; refuses any unresolved gate |

Exact option spellings may be refined during implementation, but these behaviors and file contracts are required. The README gives a complete repeatable example. Model responses are submitted as UTF-8 structured records; the command never treats free-form prose or a model's self-confidence as a decision.

## Role sequence and isolation

1. **Candidate discovery** proposes no more than the batch limit, with neutral concept senses and rough pair hypotheses, and no permanent IDs.
2. **Normalization and overlap** creates comparison keys and identifies exact, morphological, English-synonym, and semantic overlap against current and prior batches and released concepts. It does not rewrite learner forms.
3. **Indonesian usage** and **Malaysian usage** independently assess senses, commonness, register, alternatives, and evidence needs for their locale.
4. **Relation proposal** aligns one English concept with both usage analyses and selects one tentative relation.
5. **Evidence collector/auditor** gathers and inspects external references for specific claims, including counterevidence. An AI-supplied URL or `audited` flag is not verified until a separate audit record captures access method, observed page location or corpus query, short observation, and claim linkage.
6. **Independent verifier** receives the normalized claim and audited evidence, but not the generator's reasoning, confidence, or proposed approval. It gives its own sense, usage, and relation verdict.
7. **Adversarial reviewer** receives the proposal and evidence, actively searches for counterexamples to shared meaning, common usage, register and regional scope, alternate senses, and relation classification, and records objections or an explicit agreement; its objections must be resolved before acceptance.
8. **Decision gate** is deterministic and records `pending` for incomplete work or a deliberate final `accepted`, `hold`, or `rejected` with reason codes.

Each role has a repository prompt file and structured response schema. Prompt revisions are versioned; records note the exact version used. Every stage record stores a digest of its input packet and the versions of all upstream records it consumed. An unchanged successful stage may be reused after interruption. A failed, malformed, or missing stage must be rerun; changed inputs or a changed prompt version invalidate that stage and every downstream consumer before acceptance. In particular:

- Changing the English cue or intended sense invalidates both locale usage analyses and all later roles.
- Changing an Indonesian or Malaysian answer invalidates that locale's usage analysis, relation proposal, evidence audit, verifier, adversary, and decision.
- Changing the proposed relation invalidates its relation proposal, relevant evidence audit, verifier, adversary, and decision.
- Adding, removing, correcting, or changing the applicability of evidence invalidates its audit, verifier, adversary, and decision; if it changes a usage conclusion or relation claim, those conclusions and their downstream roles must also be rerun.

Prior revisions remain available for audit, but only records whose input digests and upstream versions still match may support acceptance. Resume starts at the earliest missing, failed, or invalidated stage and keeps unaffected completed records.

## Gate rules

- An ordinary `accepted` candidate requires distinct generation and verifier outputs, completed locale analyses and evidence audit, at least two audited independent external source groups covering key meaning and usage claims, a neutral aligned cue, no unresolved contradiction, a resolved overlap check, and no open adversarial objection.
- `different-common-word` additionally needs within-locale comparative usage support at the same sense and register. Existence in two dictionaries is insufficient.
- `false-friend` additionally needs independent evidence for each language's relevant meaning and for the misleading contrast, plus explicit agreement from both verifier and adversary; the final learner contrast is checked against that evidence.
- `pending` applies when a candidate has an interrupted, malformed, or otherwise incomplete stage and no explicit final decision. It is not a final disposition and blocks batch closure and export.
- `hold` is a deliberate final disposition for missing/inaccessible evidence, ambiguous cue, unresolved source conflict, unresolved duplicate, or a disagreement that can be investigated. It requires a recorded reason, including when a candidate is explicitly finalized before every research stage succeeds. The decision records each uncompleted stage as skipped, failed, or interrupted without inventing a role result.
- `rejected` applies to a disproven claim, confirmed accidental duplicate, or unsuitable/low-value concept that should not proceed under current evidence. An early rejection likewise records the reason and statuses of uncompleted stages.
- A model confidence number cannot override any rule. A batch can close with zero accepted entries.
- Before any ID assignment, the promotion set is screened as a whole against itself, prior candidate archives, the assignment ledger, and the released learner source. Any newly found unresolved or confirmed overlap refuses the promotion set until affected decisions are revised and batch reports are reclosed; it cannot silently drop a candidate already counted as accepted.

## Batch report contract

Every open-batch report requires generated = accepted + held + rejected + pending. A closed-batch report requires pending = 0 and generated = accepted + held + rejected. Reports also list accepted and proposed relation counts, duplicate detections and resolutions, verification failures, missing or contradictory evidence, and further-investigation candidate IDs. A failed reconciliation blocks export.

## Failure behavior

Malformed AI output is retained as a stage failure and never silently repaired into an accepted entry. A missing or inaccessible source remains a lead, not support. A network/model outage leaves current records intact and affected candidates pending until research resumes or an explicit hold is recorded. Export validates prospective TSV and ID ledger in temporary files, writes prior-version backups and `curation/export-journal.json`, replaces the ledger first and TSV last, and clears the journal after both agree. Handled failures roll both back. After an interruption, the next curation operation must complete or roll back recovery before export; release is blocked while the journal exists. Running `export` again for an already exported batch is idempotent and never allocates new IDs for the same candidate.
