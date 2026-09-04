# UAT Reference Cases — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Governing test / UAT reference |
| Updated | 2026-09-03 |

## Purpose

Record real or representative projects used to validate estimator outputs, reconciliation, and the four-output document package ([project-document-package.md](../architecture/project-document-package.md)). Reference cases are **not** final pricing authority — they exercise workflow and consistency.

The **Permit & Approvals Report** is a governed project document ([permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md)). FG-016 office HTML/PDF snapshot is **CLOSED / OPERATIONAL FOR UAT**. It is **not** one of the four estimate outputs. Do not treat ChatGPT or other preliminary research as an AHJ determination. Pratt live office UAT **PASSED** on port **5009** (project id 9).

## Reference case — 3415 Roger Stevens Road (Detached Garage)

| Field | Value |
|-------|--------|
| Project | Detached Garage |
| Address | 3415 Roger Stevens Road, North Gower, Ontario |
| Contractor | Brayman Construction Inc., 411 St. John Street, Merrickville, ON K0G 1N0 |
| Status | **Reference / UAT.** Commercial numbers in recovered 2026-08-31 package are **project-specific**, not a reusable price. **Presentation design** of that package is the approved document-presentation baseline ([approved-document-presentation-reference-baseline.md](../architecture/approved-document-presentation-reference-baseline.md)). |
| Recorded | 2026-08-25; presentation baseline recovered 2026-09-03 |

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

The recovered 2026-08-31 Desktop ZIP is the **first project package** using the Joel-approved presentation family (seven DOCX/PDF pairs + three source-quote PDFs). Identity: [allen-jacques-garage-presentation-baseline-manifest.md](allen-jacques-garage-presentation-baseline-manifest.md). Bytes remain **outside Git**.

The seven presentation families are **not** the FG-012 HTML/PDF renderers. Pricing in that package **must not** be copied into another project. Document **04** is an **INTERNAL ENTRY REFERENCE**, not a customer deliverable (recovered customer-facing folder is provenance only).

**Do not treat recovered project pricing as a template.** Document 05 remains **COMMERCIAL_DRAFT** (Legal Content Gate not populated).

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
| Status | **FG-016 UAT reference** — live labeled project **id 9** (`FG016-UAT-PRATT`) on port **5009**. Advisory only. Not a permit determination. |
| Recorded | 2026-08-30 |
| Canonical pin | [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) · [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) · [permit-rules-library.md](../architecture/permit-rules-library.md) · [jurisdiction-resolution.md](../architecture/jurisdiction-resolution.md) |
| Architecture | ADR-037 / ADR-038 / ADR-039 **Accepted**. [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT** (foundation). [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. Live Pratt office UAT **PASSED** on port **5009**. |

This case is the **permit-preflight** reference. The 3415 Roger Stevens Road case remains the commercial/document-package UAT reference.

Live analysis **v3** (project id 9) finding-status summary — advisory only; **not** a municipal determination:

| Status | Count | Governed meaning in this UAT |
|--------|------:|------------------------------|
| PASS | 1 | OTT-CH-002 same-lot applicability only. **PASS** means no issue identified against that governed check — never zoning/AHJ/permit approved. |
| VERIFY | 3 | OTT-CH-003 dual-compliance; OTT-CH-006 height 6.096 m vs 6.1 m ceiling; OTT-CH-007 ambiguous setback |
| MISSING_INFORMATION | 4 | OTT-CH-004 servicing/lot area; OTT-CH-008 septic class; OTT-CH-009 grading; OTT-CH-010 bounded site-plan completeness |
| POTENTIAL_NON_CONFORMANCE | 1 | OTT-CH-005 footprint 121.35 m² vs 95 m² ceiling — **advisory only**. Do not state the project fails zoning or requires a variance unless separately governed evidence supports that. |
| ADDITIONAL_APPROVAL_LIKELY | 1 | OTT-CH-001 building-permit application evidence absent |
| NOT_APPLICABLE | 0 | — |

Use the existing signed plan set and site plan as reference evidence. Do **not** seed conversational ChatGPT conclusions as product facts. Do **not** claim municipal approval.

Preliminary review (outside this repository, **not** governed evidence) has already shown useful preflight questions, including coach-house footprint, building height, setbacks, private servicing/septic, rural grading-plan requirements, and zoning/site-plan submission completeness.

**Do not treat that preliminary ChatGPT research as an authoritative project permit determination.** Architecture is **governed** (ADR-037/038/039 **Accepted**). [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) is **CLOSED / OPERATIONAL FOR UAT**. [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) created this labeled live UAT project **id 9**. Isolated tests also use a synthetic labeled coach-house project.

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
