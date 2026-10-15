# Research Indonesian usage (prompt set 1.5.0)

Assess the proposed Indonesian term for the exact neutral sense in contemporary Indonesia.
Distinguish existence, comprehension, common use, and normal everyday preference. Record
register, regional limits, alternatives, and any possible semantic mismatch. Cite external
source leads with exact claims for later separate inspection; do not mark them audited.
Make a `preferred-choice` claim only when a concrete comparison or multiple independent,
claim-relevant contextual sources support the term as the normal choice for this exact
cue. A frequency study is useful but is not mandatory. For named public facilities,
consistent terminology from the operator plus independent instructions to the public
can support ordinary preference if no credible competing everyday term is documented.
Do not infer exclusivity, population frequency, or a countrywide difference from one
institutional label, one dictionary entry, or multiple pages from the same publisher.
Identify actual plausible alternatives and any contrary use; a hypothetical unnamed
alternative alone is not a reason to withhold a claim. Otherwise,
state preference uncertainty in `preferred` and use a narrower `locale-usage` claim if
common use can be supported. Do not create a claim merely to fill the schema.
The packet includes directly inspected Indonesian source notes. Use those notes as leads
for narrow meaning and usage claims. Do not browse for more sources in this role; if
the notes do not support a claim, identify the gap. Source notes are not audited evidence:
the later evidence-audit role must link and challenge each claim independently.

Return JSON only: `{"schema_version":1,"role":"indonesian-usage","model":"MODEL/TOOL",
"result":{"meaning":"...","common_use":"...","preferred":"...","register":"...",
"region":"...","alternatives":[],"claims":[{"claim_id":"...","claim_type":"meaning|locale-usage|preferred-choice",
"proposition":"...","locale":"Indonesia"}],"source_leads":[]}}`.
