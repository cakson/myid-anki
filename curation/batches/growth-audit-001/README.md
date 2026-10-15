# Later-batch duplicate and recovery audit

This is a controlled process fixture, not an AI-curated learner-content batch. It
replays a plural cue for the already accepted `000003` spoon concept. The
`generation-response.json` fixture creates one candidate without a permanent ID.

The first normalization response (`malformed-overlap-response.txt`) is invalid
JSON. Its failed event retains the raw text. A corrected normalization response
(`corrected-overlap-response.json`) records a semantic merge with the accepted
concept. The packet's deterministic archive also warns about the existing TSV
row and prior batch candidates. The resulting `report.json` closes with one
rejected candidate and zero accepted entries. No learner TSV row or ID assignment
is created.

The fixture exercises recovery and duplicate gates. It makes no linguistic claim
about a new vocabulary concept.
