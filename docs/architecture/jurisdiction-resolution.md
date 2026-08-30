# Architecture — Project Location and Jurisdiction Resolution

| Attribute | Value |
|-----------|--------|
| Status | **Current (FG-015 civic foundation)** — **CLOSED / OPERATIONAL FOR UAT**. Architecture **Accepted** ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)). Rural/legal UX unused. Pass 2 / geocoder **not** a second resolver. [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **reuses this resolver** (**CLOSED / OPERATIONAL FOR UAT**). |
| Date | 2026-08-30 |
| Product | The Estimator / CalibAi |
| Canonical ADR | [ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted** |
| Related | [permit-and-approvals-report.md](permit-and-approvals-report.md) · [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) · [modules/projects.md](../modules/projects.md) |
| Code | `app/models/jurisdiction.py` · `app/models/project.py` (`ProjectLocation`) · `app/services/jurisdiction.py` · `app/services/permit_foundation.py` |
| Schema | Alembic live current = head `e7f8a9b0c1d2`. |

**Current vs future:** [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) implemented bounded civic `ProjectLocation` (1:1 with `Project`), platform Canada / Ontario / City of Ottawa definitions plus aliases (`Ottawa`, `City of Ottawa`, `North Gower`), and a deterministic resolver. `Project.address` remains free text and is not parsed or overwritten. `Organization.tax_jurisdiction` remains tax policy, not AHJ identity. No geocoder, municipal API, or AI. Live current = head `f8a9b0c1d2e3`. [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **reuses this resolver** (CLOSED / OPERATIONAL FOR UAT). Unknown/unimplemented jurisdictions fail closed to **RULE COVERAGE NOT AVAILABLE**. Do not hard-code Ottawa as universal architecture.

---

## Purpose

Project location is a foundational CalibAi project fact. For an active construction project, location must eventually be sufficient to resolve **jurisdiction**.

There is **one** reusable jurisdiction-resolution architecture. Do not create independent mechanisms inside Permit Intelligence, contracts, tax, code/compliance, or supplier geography.

---

## Project location

**Owner:** Projects ([ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md)).

Distinct from `ProjectCommercialContext` estimating posture ([ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md)).

**V1 civic fields:** street, municipality, province/state, postal/ZIP (optional), country.

**LOCATION COMPLETE** when street, municipality, province/state, and country are present. Postal is not required. Otherwise **LOCATION INCOMPLETE**. Incomplete projects may still be created.

Nullable columns exist for later rural/legal/parcel support (`location_kind`, `legal_description`, `parcel_identifier`, `future_civic_address`). V1 UX is civic only. No GIS.

---

## Jurisdiction resolver

```text
PROJECT LOCATION
→ COUNTRY
→ PROVINCE / STATE
→ MUNICIPALITY / COUNTY
→ APPLICABLE AHJ(S)
```

V1 resolution is **deterministic** from stored civic fields matched to platform `jurisdiction_definitions` / `jurisdiction_aliases` (`app/services/jurisdiction.py` `resolve_jurisdiction`).

**JURISDICTION RESOLVED** only when country, province/state, and municipality are present **and** match a governed node/alias. Otherwise **JURISDICTION UNRESOLVED**. Street/postal are not required for resolution. There is **no** universal Ottawa fallback. Unmatched text (including other Ontario municipalities) stays unresolved.

Seeded V1 nodes: Canada (`CA`) → Ontario (`CA-ON`) → City of Ottawa (`CA-ON-OTTAWA`). Aliases include Canada/CA, Ontario/ON, Ottawa, City of Ottawa, North Gower. Not a national library.

Current `Organization.tax_jurisdiction` remains tax policy and is **not** consulted.

---

## This architecture does not authorize

- live web lookup / geocoding service
- incomplete-location as a blocker to creating a Project
- Permit Rules Library / Pass 2 analysis in this document — [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**; reuse this resolver; no second resolver
- national municipality library
- office CRUD for platform jurisdiction definitions
- parsing historical `Project.address`
