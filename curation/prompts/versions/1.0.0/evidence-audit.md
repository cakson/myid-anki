# Audit external evidence (prompt set 1.0.0)

Independently inspect every proposed source or corpus result. A model citation, URL, or dictionary
entry by itself is only a lead. For each observation, state exactly which claim is supported,
contradicted, or left inconclusive. Record the access method, page location or reproducible query,
short observed content, access time, publisher, underlying source group, locale, register, and
limitations. Count mirrors and copied pages as one underlying source. A dictionary listing proves
existence or a sense, not normal everyday preference by itself. Report contrary evidence.

Return JSON only: `{"schema_version":1,"role":"evidence-audit","model":"MODEL/TOOL",
"result":{"observations":[{"evidence_id":"...","claim_id":"...","source_group":"...",
"source_title":"...","publisher":"...","url_or_query":"...","accessed_at":"ISO UTC",
"observation":"...","page_location_or_query":"...",
"audit_method":"retrieved-page|corpus-query|manual-inspection",
"stance":"supports|contradicts|inconclusive","claim_type":"meaning|locale-usage|preferred-choice|relation|misleading-contrast",
"usage_basis":"contextual|comparative|dictionary-only","locale":"...","register":"...",
"limitations":"..."}]}}`.
If a source cannot be inspected, omit it from supporting observations and report the failure.
