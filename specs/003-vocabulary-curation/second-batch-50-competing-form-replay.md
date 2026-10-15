# Batch 2 targeted competing-form replay

This is a read-only replay of the same 50 candidates. The prior production decisions, v3.1 replay, independent audit, and 34-card promotion preview remain unchanged.

- Decisions: {'accepted': 36, 'rejected': 6, 'hold': 8}; accepted confidence: {'high': 16, 'medium': 12, 'low': 8}
- Potential named-alternative records inspected: 17; credible everyday competitors: 12
- Challenge outcomes: {'contrast-remains-useful': 5, 'preference-materially-uncertain': 2, 'no-meaningful-preference-contrast': 2, 'contrast-needs-qualification': 3}
- Added model calls: 12; detector elapsed: 90.725 s; independent challenge elapsed: 52.735 s; input/output tokens: 149523/14648; monetary cost unavailable
- Changed decisions from v3.1: 4 — cal2-daily-001:daily-10, cal2-shopping-001:shopping-09, cal2-shopping-001:shopping-10, cal2-travel-001:travel-06

## Six known unsafe or unresolved cards

| Candidate | Original | v3.1 | Trigger | Challenge | v3.2 | Audit agrees? |
|---|---|---|---|---|---|---|
| cal2-daily-001:daily-05 | accepted | accepted | credible-everyday | contrast-remains-useful | accepted / medium | no |
| cal2-shopping-001:shopping-06 | accepted | accepted | credible-everyday | contrast-remains-useful | accepted / low | no |
| cal2-social-001:social-04 | accepted | hold | none | — | hold / — | yes |
| cal2-social-001:social-06 | accepted | hold | none | — | hold / — | yes |
| cal2-travel-001:travel-10 | accepted | accepted | weak-alternative | — | accepted / low | no |
| cal2-work-001:work-08 | accepted | accepted | credible-everyday | contrast-needs-qualification | accepted / low | no |

## Simulated targeted audit

Audit all accepted low/very-low and false friends; audit medium/high with concrete review flags (including a named credible competitor) plus deterministic 25% medium and 10% high samples.

- Accepted routed to audit: 14
- Known unsafe caught by production HOLD/REJECT: 2 / 6
- Remaining known unsafe routed to audit: 4 / 6
- Total known unsafe caught by production plus simulated audit: 6 / 6
- Confirmed-good cards routed to audit: 4 / 24

## Candidate outcomes

| Candidate | v3.1 | Competitor | Challenge | v3.2 | Audit |
|---|---|---|---|---|---|
| cal2-daily-001:daily-01 | accepted | none | — | accepted / high | confirmed-good |
| cal2-daily-001:daily-02 | accepted | none | — | accepted / high | minor-correction |
| cal2-daily-001:daily-03 | accepted | none | — | accepted / medium | minor-correction |
| cal2-daily-001:daily-04 | accepted | none | — | accepted / high | confirmed-good |
| cal2-daily-001:daily-05 | accepted | credible-everyday | contrast-remains-useful | accepted / medium | should-reject |
| cal2-daily-001:daily-06 | rejected | none | — | rejected / — | not audited |
| cal2-daily-001:daily-07 | accepted | none | — | accepted / high | confirmed-good |
| cal2-daily-001:daily-08 | hold | none | — | hold / — | not audited |
| cal2-daily-001:daily-09 | accepted | none | — | accepted / high | minor-correction |
| cal2-daily-001:daily-10 | accepted | credible-everyday | preference-materially-uncertain | hold / — | minor-correction |
| cal2-shopping-001:shopping-01 | rejected | none | — | rejected / — | not audited |
| cal2-shopping-001:shopping-02 | accepted | none | — | accepted / high | minor-correction |
| cal2-shopping-001:shopping-03 | accepted | none | — | accepted / high | confirmed-good |
| cal2-shopping-001:shopping-04 | accepted | none | — | accepted / medium | confirmed-good |
| cal2-shopping-001:shopping-05 | accepted | none | — | accepted / high | confirmed-good |
| cal2-shopping-001:shopping-06 | accepted | credible-everyday | contrast-remains-useful | accepted / low | should-reject |
| cal2-shopping-001:shopping-07 | accepted | none | — | accepted / low | confirmed-good |
| cal2-shopping-001:shopping-08 | accepted | credible-everyday | contrast-remains-useful | accepted / medium | minor-correction |
| cal2-shopping-001:shopping-09 | accepted | credible-everyday | no-meaningful-preference-contrast | rejected / — | confirmed-good |
| cal2-shopping-001:shopping-10 | accepted | credible-everyday | no-meaningful-preference-contrast | rejected / — | confirmed-good |
| cal2-social-001:social-01 | accepted | weak-alternative | — | accepted / medium | confirmed-good |
| cal2-social-001:social-02 | accepted | none | — | accepted / medium | confirmed-good |
| cal2-social-001:social-03 | accepted | weak-alternative | — | accepted / medium | confirmed-good |
| cal2-social-001:social-04 | hold | none | — | hold / — | should-reject |
| cal2-social-001:social-05 | accepted | weak-alternative | — | accepted / medium | confirmed-good |
| cal2-social-001:social-06 | hold | none | — | hold / — | materially-misleading |
| cal2-social-001:social-07 | accepted | none | — | accepted / high | confirmed-good |
| cal2-social-001:social-08 | hold | none | — | hold / — | not audited |
| cal2-social-001:social-09 | accepted | credible-everyday | contrast-remains-useful | accepted / medium | minor-correction |
| cal2-social-001:social-10 | hold | none | — | hold / — | not audited |
| cal2-travel-001:travel-01 | accepted | weak-alternative | — | accepted / medium | confirmed-good |
| cal2-travel-001:travel-02 | accepted | none | — | accepted / medium | confirmed-good |
| cal2-travel-001:travel-03 | hold | none | — | hold / — | not audited |
| cal2-travel-001:travel-04 | accepted | none | — | accepted / high | minor-correction |
| cal2-travel-001:travel-05 | accepted | none | — | accepted / high | confirmed-good |
| cal2-travel-001:travel-06 | accepted | credible-everyday | preference-materially-uncertain | hold / — | confirmed-good |
| cal2-travel-001:travel-07 | accepted | credible-everyday | contrast-needs-qualification | accepted / low | not audited |
| cal2-travel-001:travel-08 | accepted | none | — | accepted / high | confirmed-good |
| cal2-travel-001:travel-09 | accepted | none | — | accepted / high | confirmed-good |
| cal2-travel-001:travel-10 | accepted | weak-alternative | — | accepted / low | should-reject |
| cal2-work-001:work-01 | accepted | none | — | accepted / high | confirmed-good |
| cal2-work-001:work-02 | rejected | none | — | rejected / — | not audited |
| cal2-work-001:work-03 | accepted | none | — | accepted / low | minor-correction |
| cal2-work-001:work-04 | accepted | none | — | accepted / low | confirmed-good |
| cal2-work-001:work-05 | accepted | none | — | accepted / high | confirmed-good |
| cal2-work-001:work-06 | accepted | credible-everyday | contrast-needs-qualification | accepted / low | not audited |
| cal2-work-001:work-07 | accepted | credible-everyday | contrast-remains-useful | accepted / medium | minor-correction |
| cal2-work-001:work-08 | accepted | credible-everyday | contrast-needs-qualification | accepted / low | materially-misleading |
| cal2-work-001:work-09 | rejected | none | — | rejected / — | not audited |
| cal2-work-001:work-10 | accepted | none | — | accepted / high | confirmed-good |
