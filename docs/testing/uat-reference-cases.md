# UAT Reference Cases — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Governing test / UAT reference |
| Updated | 2026-08-30 |

## Purpose

Record real or representative projects used to validate estimator outputs, reconciliation, and the four-output document package ([project-document-package.md](../architecture/project-document-package.md)). Reference cases are **not** final pricing authority — they exercise workflow and consistency.

The **Permit & Approvals Report** is a separate **FUTURE / NOT IMPLEMENTED** governed project document ([permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md)). It is **not** one of the four estimate outputs. Do not treat ChatGPT or other preliminary research as an AHJ determination.

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

## FG-016 UAT reference — Mike Pratt Coach House (Permit & Approvals Report)

| Field | Value |
|-------|--------|
| Project | Mike Pratt Coach House |
| Address | 2562 Church Street, North Gower, Ontario |
| Status | **FG-016 UAT reference** — not an in-app project in the governance pass; not a permit determination |
| Recorded | 2026-08-30 |
| Canonical pin | [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) · [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) · [permit-rules-library.md](../architecture/permit-rules-library.md) · [jurisdiction-resolution.md](../architecture/jurisdiction-resolution.md) |
| Architecture | ADR-037 / ADR-038 / ADR-039 **Accepted**. [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT** (foundation). [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED**. |

This case is the **permit-preflight** reference. The 3415 Roger Stevens Road case remains the commercial/document-package UAT reference.

Use the existing signed plan set and site plan as reference evidence. Do **not** seed conversational ChatGPT conclusions as product facts. Do **not** claim municipal approval. Do **not** pre-decide findings.

Preliminary review (outside this repository, **not** governed evidence) has already shown useful preflight questions, including coach-house footprint, building height, setbacks, private servicing/septic, rural grading-plan requirements, and zoning/site-plan submission completeness.

**Do not treat that preliminary ChatGPT research as an authoritative project permit determination.** Architecture is **governed** (ADR-037/038/039 **Accepted**). [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) is **CLOSED / OPERATIONAL FOR UAT** and does **not** create this project. [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) does **not** create this project in the governance pass.

This case remains the **FG-016 UAT reference**. It is **not** a universal rule.

## Related

- [pricing-policy.md](../pricing-policy.md)
- [architecture/project-document-package.md](../architecture/project-document-package.md)
- [architecture/permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md)
- [architecture/permit-rules-library.md](../architecture/permit-rules-library.md)
- [architecture/jurisdiction-resolution.md](../architecture/jurisdiction-resolution.md)
- [feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md)
- [adr/ADR-037-project-location-and-jurisdiction-resolution.md](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)
- [adr/ADR-038-permit-intelligence-authority-and-rules-library.md](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)
- [adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)
- [testing-standards.md](../testing-standards.md)
