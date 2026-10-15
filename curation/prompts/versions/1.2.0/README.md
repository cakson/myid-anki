# Curation prompt exchange

The curation CLI emits versioned, role-specific prompt packets. Run each packet with a configured
AI tool, inspect external sources during curation, and ingest the structured response. Separate
generation, locale analysis, verification, and adversarial stages; the deterministic gate alone
decides whether a candidate can enter learner data. This directory is not read by the deck builder.

Use `python -m indo_malay_anki.curation route --role ROLE` before each AI call. The role routes
in `curation/config.json` use Luna for discovery and research and Sol for independent verification
and adversarial review. The `reserve` label is a repository cost policy, not a provider service
tier. Evidence and alignment checks block expensive review packets when a candidate already fails
an acceptance prerequisite.

`curation/config.json` selects the version for new batches. Each batch manifest pins its
version, and `versions/1.0.0` and `versions/1.1.0` retain the exact prompt text and role
mapping used by those batches. Keep those version directories immutable; create another
version when changing a prompt. The root prompt files mirror the current version for easy
reading. New batch generation packets include a frozen, compact list of previously
investigated concepts so discovery can avoid known duplicates before overlap review.
