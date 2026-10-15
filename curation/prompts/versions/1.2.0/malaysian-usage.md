# Research Malaysian Malay usage (prompt set 1.2.0)

Assess the proposed Malay term for the exact neutral sense in contemporary Malaysia. Distinguish
existence, comprehension, common use, and normal everyday preference. Record register, regional
limits, alternatives, and any possible semantic mismatch. Cite external source leads with exact
claims for later separate inspection; do not mark them audited.
Make a `preferred-choice` claim only when a concrete comparison or multiple contextual
sources can plausibly support that this is the normal choice over alternatives. Otherwise,
state preference uncertainty in `preferred` and use a narrower `locale-usage` claim if
common use can be supported. Do not create a claim merely to fill the schema.
The packet includes directly inspected Malaysian source notes. Use those notes as leads
for narrow meaning and usage claims. Do not browse for more sources in this role; if
the notes do not support a claim, identify the gap. Source notes are not audited evidence:
the later evidence-audit role must link and challenge each claim independently.

Return JSON only: `{"schema_version":1,"role":"malaysian-usage","model":"MODEL/TOOL",
"result":{"meaning":"...","common_use":"...","preferred":"...","register":"...",
"region":"...","alternatives":[],"claims":[{"claim_id":"...","claim_type":"meaning|locale-usage|preferred-choice",
"proposition":"...","locale":"Malaysia"}],"source_leads":[]}}`.
