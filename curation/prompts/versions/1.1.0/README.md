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
