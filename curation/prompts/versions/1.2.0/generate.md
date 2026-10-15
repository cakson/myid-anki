# Generate candidate concepts (prompt set 1.2.0)

You are the discovery role. Propose at most the packet's candidate limit for its topic and scope.
Prioritize useful false-friend hypotheses, different everyday words, recognizably similar words,
then high-frequency shared words. A hypothesis is not verified. Use contemporary Indonesian in
Indonesia and Malaysian Malay in Malaysia. Keep each English cue tied to one neutral sense.
Do not assign permanent IDs or claim a candidate is accepted. Avoid obvious repeated senses.
The packet may include previously investigated concepts. Do not propose their synonyms,
minor spelling variants, plurals, or equivalent learning concepts, even if those records
were held or rejected. Use the freed slots for genuinely new concepts.

Return JSON only: `{"schema_version":1,"role":"generate","model":"MODEL/TOOL",
"result":{"candidates":[{"candidate_id":"topic-01","english":"...",
"indonesian":"...","malaysian":"...","sense":"...","tags":["topic"]}]}}`.
Use the actual model/tool identifier. Do not invent external evidence in this stage.
