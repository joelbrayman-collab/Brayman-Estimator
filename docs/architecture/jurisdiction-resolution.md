# Architecture — Project Location and Jurisdiction Resolution

| Attribute | Value |
|-----------|--------|
| Status | **FUTURE / NOT IMPLEMENTED** — architecture **Accepted** ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)) |
| Date | 2026-08-30 |
| Product | The Estimator / CalibAi |
| Canonical ADR | [ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted** |
| Related | [permit-and-approvals-report.md](permit-and-approvals-report.md) · [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) · [modules/projects.md](../modules/projects.md) |

**Current vs future:** Live `Project.address` is free text. `Organization.tax_jurisdiction` is a tax label, not municipal/AHJ identity. Nothing below is implemented. Accepting ADR-037 does **not** authorize schema, a Feature Gate, live geocoding, or incomplete-location enforcement.

---

## Purpose

Project location is a foundational CalibAi project fact. For an active construction project, location must eventually be sufficient to resolve **jurisdiction**.

There is **one** reusable jurisdiction-resolution architecture. Do not create independent mechanisms inside Permit Intelligence, contracts, tax, code/compliance, or supplier geography.

---

## Project location

**Owner:** Projects ([ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md)).

Distinct from `ProjectCommercialContext` estimating posture ([ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md)).

Normal case: **civic address**.

Also anticipate:

- vacant / rural parcel
- legal description
- parcel identifier
- municipality
- province / state
- country

A legitimate early project may be **LOCATION INCOMPLETE**. Do not implement enforcement yet.

---

## Jurisdiction resolver

```text
PROJECT LOCATION
→ COUNTRY
→ PROVINCE / STATE
→ MUNICIPALITY / COUNTY
→ APPLICABLE AHJ(S)
```

Future consumers (none implemented):

- Permit Intelligence
- jurisdictional contracts
- tax
- code / compliance
- supplier geography

Current `Organization.tax_jurisdiction` remains tax policy. Later tax may **consume** this resolver; it must not fork a second AHJ model.

---

## Implementation strategy

Architect **globally / jurisdictionally**. Implement later in **bounded** jurisdictions.

| Layer | First reference (not universal default) |
|-------|----------------------------------------|
| Country / province | Canada / Ontario |
| Municipality | City of Ottawa / North Gower |
| Project | Mike Pratt Coach House, 2562 Church Street, North Gower, Ontario |

Do **not** hard-code Ottawa as the universal architecture. Do **not** attempt a national library in the first product gate.

---

## This architecture does not authorize

- schema or migration
- Feature Gate
- live web lookup / geocoding service
- incomplete-location enforcement
- Permit Intelligence implementation ([permit-and-approvals-report.md](permit-and-approvals-report.md))
