# Feature 003 guarded historical promotion

## Decision and correction trail

The frozen optimistic replay proposed 24 ACCEPT, one pencil HOLD, and one camera REJECT. The [independent audit](optimistic-policy-audit.md) found 17 of the 24 accepted candidates good as recorded, seven requiring minor cue or curation-note corrections, zero materially misleading false positives, and no accepted card requiring HOLD or REJECT. This sample is encouraging but too small to establish global linguistic accuracy or calibrate the four confidence tiers.

The guarded promotion applied all seven accepted-card corrections before export. The only learner-visible change was `chat` → **`casual conversation`** for *obrolan / sembang*; the associated sense now means an informal or relaxed conversation. `window` received a broader internal sense. *Enak/sedap*, *kulkas/peti sejuk*, *mobil/kereta*, *bus/bas*, and *truk/lori* kept their displayed answers while their alternative, preference, or meaning notes were corrected. No audit relation correction was needed. Candidate-specific confidence rationales replaced all 24 generic replay rationales, and review flags were made more specific; the existing tiers were preserved.

The pencil HOLD changed to ACCEPT after separate reconsideration. The earlier verifier worried that Malaysian *pensil* might compete with *pensel*. The audit treated that as a nonblocking variant, and Malaysia's [DBP spelling guidance](https://prpm.dbp.gov.my/Cari1?d=175768&keyword=pensil) explicitly identifies *pensel* as correct. No concrete material learner risk remained. Pencil was assigned **medium** confidence, with a candidate-specific rationale and a spelling-variant review flag. Its old HOLD and verifier concern remain in historical artifacts; the [promotion record](../../curation/promotions/optimistic-audit-001.json) records the changed decision and corrected usage notes. `kamera / kamera` stayed rejected for no meaningful contrast and was not promoted.

The promotion record is the complete machine-readable trail for each candidate: original/final decision and confidence, original/final flags, rationale, audit verdict, exact corrections, corrected usage, archived batch/event reference, relation, and permanent concept ID. Original candidate proposals and event histories were not rewritten. The selected-candidate export preflight checked the frozen 26-ID replay against all 25 independent audit results, compared each archived candidate with its replay copy, screened selected and active concepts for deterministic duplicates, validated eligible relations, reused ledger identity, and committed the learner TSV and ID ledger through the existing crash-recoverable transaction.

| Candidate ID | Permanent ID | Learner cue → Indonesian / Malaysian | Relation | Confidence | Audit result |
| --- | --- | --- | --- | --- | --- |
| `clothing-001:clothing-01` | `000008` | trousers → celana / seluar | different-common-word | medium → medium | confirmed-good |
| `clothing-001:clothing-02` | `000009` | shoes → sepatu / kasut | different-common-word | medium → medium | confirmed-good |
| `common-verbs-001:everyday-actions-01` | `000010` | send → kirim / hantar | different-common-word | very-low → very-low | confirmed-good |
| `communication-001:communication-01` | `000011` | message → pesan / mesej | different-common-word | medium → medium | confirmed-good |
| `communication-001:communication-03` | `000012` | casual conversation → obrolan / sembang | different-common-word | very-low → very-low | corrected cue |
| `everyday-objects-001:everyday-objects-05` | `000013` | eggplant → terong / terung | similar | medium → medium | confirmed-good |
| `everyday-objects-001:everyday-objects-06` | `000014` | watermelon → semangka / tembikai | different-common-word | very-low → very-low | confirmed-good |
| `food-001:foods-01` | `000015` | lunch → makan siang / makan tengah hari | similar | medium → medium | confirmed-good |
| `food-001:foods-04` | `000016` | tasty → enak / sedap | different-common-word | low → low | corrected notes |
| `food-001:foods-06` | `000017` | biscuit → biskuit / biskut | similar | low → low | confirmed-good |
| `health-001:health-01` | `000018` | medicine (to treat illness) → obat / ubat | similar | medium → medium | confirmed-good |
| `home-001:topic-02` | `000019` | bedroom → kamar tidur / bilik tidur | different-common-word | low → low | confirmed-good |
| `home-001:topic-03` | `000020` | refrigerator → kulkas / peti sejuk | different-common-word | low → low | corrected notes |
| `home-001:topic-04` | `000021` | window → jendela / tingkap | different-common-word | medium → medium | corrected internal sense |
| `home-001:topic-05` | `000022` | trash can → tempat sampah / tong sampah | different-common-word | medium → medium | confirmed-good |
| `home-001:topic-06` | `000023` | bucket → ember / baldi | different-common-word | low → low | confirmed-good |
| `home-001:topic-08` | `000024` | chair → kursi / kerusi | similar | high → high | confirmed-good |
| `places-001:places-01` | `000025` | office → kantor / pejabat | different-common-word | medium → medium | confirmed-good |
| `produce-001:produce-03` | `000026` | papaya → pepaya / betik | different-common-word | very-low → very-low | confirmed-good |
| `school-001:topic-06` | `000027` | eraser → penghapus / pemadam | different-common-word | very-low → very-low | confirmed-good |
| `transportation-001:transportation-01` | `000001` | car → mobil / kereta | different-common-word | low → low | corrected notes; retained retired ID |
| `transportation-001:transportation-04` | `000028` | bus → bus / bas | similar | medium → medium | corrected notes |
| `transportation-001:transportation-06` | `000029` | truck → truk / lori | different-common-word | medium → medium | corrected notes |
| `university-001:university-study-03` | `000030` | scholarship → beasiswa / biasiswa | similar | medium → medium | confirmed-good |
| `school-001:topic-05` | `000031` | pencil → pensil / pensel | similar | HOLD → medium ACCEPT | corrected notes; resolved spelling objection |

## Canonical source and package validation

| Measure | Result |
| --- | ---: |
| Learner rows before | 3 |
| Rows added | 25 |
| Active rows corrected in place | 0 |
| Learner rows after | 28 |
| `different-common-word` rows after | 19 |
| `similar` rows after | 9 |
| `false-friend` rows after | 0 |
| Promoted high / medium / low / very-low | 1 / 13 / 6 / 5 |
| Intentionally not promoted | `technology-001:technology-07` camera (`same`, no contrast) |

The former car concept `000001` was absent from the three-row active source but remained permanently assigned in the ledger. Promotion restored that same ID, with GUID `D6BBAuKXK`; it did not issue a new car identity. New IDs `000008`–`000031` were assigned once to the other 24 candidates. The retired IDs `000002`, `000006`, and `000007` were not reused.

The normal **offline** validator reported 28 concepts. The normal `.apkg` build produced **28 notes and 28 cards**. Direct SQLite inspection of the built package confirmed 28 unique GUIDs, one note/card for each source ID, `same` absent, corrected `casual conversation` on the front, intact *obrolan/sembang* and *pensil/pensel* answers, and unchanged deck/model IDs `1242123295`/`1942161817`. The established Anki Desktop old-to-new import compatibility exercise remains documented in [validation results](validation-results.md#anki-desktop-import-compatibility); this phase did not change the note model or deck identity and did not repeat a GUI import.

The full Python test suite passed **169 tests**. Ruff lint and format checks passed. A dry run and an isolated-copy transaction test showed 3 → 28 rows, clean export-journal removal, and idempotent repeat execution. The export transaction also preserves normal readable file modes for the learner TSV and ID ledger. No new vocabulary batch was generated. Audit time remains separate from ordinary production throughput; the four confidence tiers remain provisional review-priority labels until later corrections and stratified audits provide calibration evidence.
