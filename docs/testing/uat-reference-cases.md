# UAT Reference Cases — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Governing test / UAT reference |
| Updated | 2026-08-25 |

## Purpose

Record real or representative projects used to validate estimator outputs, reconciliation, and the four-output document package ([project-document-package.md](../architecture/project-document-package.md)). Reference cases are **not** final pricing authority — they exercise workflow and consistency.

## Reference case — 3415 Roger Stevens Road (Detached Garage)

| Field | Value |
|-------|--------|
| Project | Detached Garage |
| Address | 3415 Roger Stevens Road, North Gower, Ontario |
| Contractor | Brayman Construction Inc., 411 St. John Street, Merrickville, ON K0G 1N0 |
| Status | **Reference / UAT — draft outputs not final pricing** |
| Recorded | 2026-08-25 |

### Pricing parameters (reference)

| Parameter | Value |
|-----------|--------|
| Labour direct rate | $65 CAD / hour |
| Target gross margin | 15% ([pricing-policy.md](../pricing-policy.md)) |

### Known reference cost facts (pre-HST unless noted)

| Item | Amount / note |
|------|----------------|
| Winchester material takeoff | $25,151.47 pre-HST |
| Garage doors + three openers | $8,550 pre-HST direct cost |
| Structural system | LVL beams included in Winchester takeoff — **no separate structural steel beams** |
| HSS posts | Two posts at $500 each direct cost |
| Foundation | Thickened-edge slab/foundation separately quoted and **excluded** |
| Cleanup / dump | $1,000 total direct-cost allowance **including** fees and cleanup/haul labour — do not double-count cleanup labour |

### Pending / unresolved (must remain explicit)

- Final D&W supplier cost — **TBD**
- Insulation subcontract quote — **TBD**
- Revised exterior labour — **TBD**
- Drywall / mudding labour — **TBD**

### Draft outputs from reference exercise (not final)

These were created during the reference exercise and must ultimately be **regenerated/reconciled together** from one authoritative estimate record:

1. Internal Detailed Cost Breakdown
2. Customer-Facing Draft Estimate
3. QuickBooks Entry Sheet

**Do not treat current draft pricing as final.**

### UAT expectations (when implemented)

- All four core outputs trace to the same authoritative estimate version
- Internal breakdown shows direct costs and margin math; customer estimate does not expose supplier cost or margin unless authorized
- Placeholders remain labeled until resolved
- QuickBooks output reflects approved customer estimate only
- Contract generation requires approved estimate + governed warranty attachment

## Related

- [pricing-policy.md](../pricing-policy.md)
- [architecture/project-document-package.md](../architecture/project-document-package.md)
- [testing-standards.md](../testing-standards.md)
