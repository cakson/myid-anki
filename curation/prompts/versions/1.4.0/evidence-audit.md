# Audit external evidence (prompt set 1.4.0)

Independently inspect every proposed source or corpus result. A model citation, URL, or dictionary
entry by itself is only a lead. For each observation, state exactly which claim is supported,
contradicted, or left inconclusive. Record the access method, page location or reproducible query,
short observed content, access time, publisher, underlying source group, locale, register, and
limitations. Count mirrors and copied pages as one underlying source. A dictionary listing proves
existence or a sense, not normal everyday preference by itself. Report contrary evidence.
Use one underlying source per observation; never join publishers, domains, or URLs into
one record. Mark a search snippet as inconclusive, not a retrieved page. Do not invent
an access time or claim to have opened a page if only a search result was visible.
For common use, seek an independent contextual source in each locale. For an everyday
preference claim, seek a direct comparison or multiple independent contextual sources
that speak to the exact cue and a normal learner-facing choice. A postal operator's
branch terminology together with independent public instructions about visiting that
facility can support ordinary preference; one institutional name or dictionary
translation cannot. Do not require a numerical frequency study when convergent
real-world usage is sufficient. Record actual alternatives and conflicting examples;
do not treat lack of proof of exclusivity as a conflict by itself.
An inaccessible lead contributes no support; it is acceptable to return fewer observations.
Use the packet's inspected source notes first and cite their actual page locations.
Limit further research to a specific unresolved key claim; avoid open-ended searching.
The source notes are leads, not automatic support: challenge them and omit an observation
if its recorded content does not substantiate the linked claim.

Return JSON only: `{"schema_version":1,"role":"evidence-audit","model":"MODEL/TOOL",
"result":{"observations":[{"evidence_id":"...","claim_id":"...","source_group":"...",
"source_title":"...","publisher":"...","url_or_query":"...","accessed_at":"ISO UTC",
"observation":"...","page_location_or_query":"...",
"audit_method":"retrieved-page|corpus-query|manual-inspection",
"stance":"supports|contradicts|inconclusive","claim_type":"meaning|locale-usage|preferred-choice|relation|misleading-contrast",
"usage_basis":"contextual|comparative|dictionary-only","locale":"...","register":"...",
"limitations":"..."}]}}`.
If a source cannot be inspected, omit it from supporting observations and report the failure.
