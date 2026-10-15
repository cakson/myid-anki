# Feature 003 optimistic-policy frozen replay

This is a bounded reconsideration of the same 26 historical HOLD candidate IDs in [the frozen sample](historical-hold-sample.json). The replay reused candidate IDs, archived evidence, and concrete prior objections. It generated no new candidates, did not rewrite checked-in batch histories, and did not promote anything to `data/vocabulary.tsv`. [Machine-readable decisions](optimistic-replay-report.json) and [Luna verifier results](optimistic-verifier-results.json) retain details.

## Outcomes

| Metric | Result |
| --- | ---: |
| Frozen candidates | 26 |
| Provisional ACCEPT | 24 |
| HOLD | 1 |
| REJECT | 1 |
| No-contrast REJECT | 1 |
| Fast-path ACCEPT | 24 |
| Escalated ACCEPT | 0 |
| Fast-path utilization among 25 non-no-contrast candidates | 96% |

Accepted confidence: **high 1, medium 12, low 6, very-low 5**. Every provisional ACCEPT has a signal-based rationale and review flags in the machine-readable report. Five batch Luna verifier calls succeeded; five initial CLI launches failed before reaching the model because the current CLI could not synchronize managed preferences. The successful retry used the previously working standalone CLI through the repository launcher. Failed launches were not counted as linguistic verification.

## Measured replay work

| Metric | Value |
| --- | ---: |
| Successful batched verifier calls | 5 |
| Failed pre-model launches | 5 |
| Mean input tokens per successful batch call | 14,442.2 |
| Median input tokens per successful batch call | 14,222 |
| Measured active replay time, including failed launches | 95.181 seconds |
| Provisional accepted decisions per replay hour | 907.7 |
| Canonical cards promoted | 0 |

The replay rate is **not** end-to-end accepted learner-card throughput. Historical generation, evidence collection, earlier model calls, and canonical export are outside this timer. The current product-output rate for this experiment is zero because no cards were promoted. Token counts are provider-reported; monetary cost is unavailable. The active-time calculation includes measured model attempts and the final local replay, but earlier local troubleshooting intervals are unavailable.

## All frozen candidates

| Candidate ID | English → Indonesian / Malaysian | Decision | Relation | Confidence |
| --- | --- | --- | --- | --- |
| `clothing-001:clothing-01` | trousers → celana / seluar | ACCEPTED | different-common-word | medium |
| `clothing-001:clothing-02` | shoes → sepatu / kasut | ACCEPTED | different-common-word | medium |
| `common-verbs-001:everyday-actions-01` | send → kirim / hantar | ACCEPTED | different-common-word | very-low |
| `communication-001:communication-01` | message → pesan / mesej | ACCEPTED | different-common-word | medium |
| `communication-001:communication-03` | chat → obrolan / sembang | ACCEPTED | different-common-word | very-low |
| `everyday-objects-001:everyday-objects-05` | eggplant → terong / terung | ACCEPTED | similar | medium |
| `everyday-objects-001:everyday-objects-06` | watermelon → semangka / tembikai | ACCEPTED | different-common-word | very-low |
| `food-001:foods-01` | lunch → makan siang / makan tengah hari | ACCEPTED | similar | medium |
| `food-001:foods-04` | tasty → enak / sedap | ACCEPTED | different-common-word | low |
| `food-001:foods-06` | biscuit → biskuit / biskut | ACCEPTED | similar | low |
| `health-001:health-01` | medicine (to treat illness) → obat / ubat | ACCEPTED | similar | medium |
| `home-001:topic-02` | bedroom → kamar tidur / bilik tidur | ACCEPTED | different-common-word | low |
| `home-001:topic-03` | refrigerator → kulkas / peti sejuk | ACCEPTED | different-common-word | low |
| `home-001:topic-04` | window → jendela / tingkap | ACCEPTED | different-common-word | medium |
| `home-001:topic-05` | trash can → tempat sampah / tong sampah | ACCEPTED | different-common-word | medium |
| `home-001:topic-06` | bucket → ember / baldi | ACCEPTED | different-common-word | low |
| `home-001:topic-08` | chair → kursi / kerusi | ACCEPTED | similar | high |
| `places-001:places-01` | office → kantor / pejabat | ACCEPTED | different-common-word | medium |
| `produce-001:produce-03` | papaya → pepaya / betik | ACCEPTED | different-common-word | very-low |
| `school-001:topic-05` | pencil → pensil / pensel | HOLD | similar | — |
| `school-001:topic-06` | eraser → penghapus / pemadam | ACCEPTED | different-common-word | very-low |
| `technology-001:technology-07` | camera → kamera / kamera | REJECTED | same | — |
| `transportation-001:transportation-01` | car → mobil / kereta | ACCEPTED | different-common-word | low |
| `transportation-001:transportation-04` | bus → bus / bas | ACCEPTED | similar | medium |
| `transportation-001:transportation-06` | truck → truk / lori | ACCEPTED | different-common-word | medium |
| `university-001:university-study-03` | scholarship → beasiswa / biasiswa | ACCEPTED | similar | medium |

## Every remaining HOLD and REJECT

- **school-001:topic-05 (HOLD)**: The unresolved Malaysian rival pensil could materially misteach learners if pensel is presented as the categorical normal Malaysian form.
- **technology-001:technology-07 (REJECTED)**: no-meaningful-cross-language-contrast

## Required diagnostic pairs

| Pair | Outcome | Why |
| --- | --- | --- |
| trousers → celana / seluar | ACCEPTED | Independent Luna verifier agreed on different-common-word; no material blocker remained. Confidence medium; review flags: limited-evidence, usage-preference-weak. |
| biscuit → biskuit / biskut | ACCEPTED | Independent Luna verifier agreed on similar; no material blocker remained. Confidence low; review flags: historical-objection, limited-verifier-agreement. |
| refrigerator → kulkas / peti sejuk | ACCEPTED | Independent Luna verifier agreed on different-common-word; no material blocker remained. Confidence low; review flags: historical-objection, limited-verifier-agreement. |
| car → mobil / kereta | ACCEPTED | Independent Luna verifier agreed on different-common-word; no material blocker remained. Confidence low; review flags: historical-objection, limited-verifier-agreement. |
| scholarship → beasiswa / biasiswa | ACCEPTED | Independent Luna verifier agreed on similar; no material blocker remained. Confidence medium; review flags: limited-verifier-agreement. |
| camera → kamera / kamera | REJECTED | Archived aligned `same` assessment plus identical ordinary forms allowed no-contrast rejection before any new verifier call. |

## Quality assessment and next boundary

Compared with the earlier frozen policy-v2 replay (0 ACCEPT, 25 HOLD, 1 REJECT), the optimistic gate recovered 24 provisional ordinary cards and kept one concrete preference dispute on HOLD. The claim-evidence replay had recovered one provisional card. This is a material increase in *candidate decisions*, but linguistic quality and end-to-end canonical throughput remain unproven until independent audit and guarded promotion. The pipeline did not accept `kamera/kamera` merely to raise output.

Priority audit candidates include the five accepted very-low cards and the six low cards, especially `chat → obrolan / sembang`, `tasty → enak / sedap`, `refrigerator → kulkas / peti sejuk`, and `car → mobil / kereta`, where usage breadth or alternatives deserve inspection. The HOLD is `pencil → pensil / pensel`: the verifier identified the concrete possibility that Malaysian `pensil` is also a normal form. No new vocabulary batch should start from this replay.
