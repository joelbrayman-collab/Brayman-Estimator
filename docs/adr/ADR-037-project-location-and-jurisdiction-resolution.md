# ADR-037 — Project Location and Jurisdiction Resolution

| Field | Value |
|-------|--------|
| Title | ADR-037: Project Location and Jurisdiction Resolution Ownership |
| Status | **Accepted** (FG-015 civic location + resolver **CLOSED / OPERATIONAL FOR UAT**; live current=head `e7f8a9b0c1d2`) |
| Date | 2026-08-30 |
| Related | [jurisdiction-resolution.md](../architecture/jurisdiction-resolution.md) · [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) · [ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-038](ADR-038-permit-intelligence-authority-and-rules-library.md) · [ADR-039](ADR-039-permit-report-snapshot-immutability-and-workflow.md) |

## Context

An active construction project must eventually be locatable well enough to resolve **jurisdiction**. Today `Project.address` is a free-text string. `Organization.tax_jurisdiction` is a **tax** label (Ontario HST), not municipal/AHJ identity. `ProjectCommercialContext` records estimating posture (`project_type`, `site_condition`), not parcel or municipality.

Permit Intelligence, future jurisdictional contracts, tax, code/compliance, and supplier geography must not each invent a separate location/jurisdiction mechanism.

This ADR does **not** authorize schema, migration, a Feature Gate, live geocoding, live web lookup, or enforcement of complete location.

## Decision

### 1. Project location is a foundational project fact

Projects owns **project location**. It is a lifecycle fact on the `Project` hub ([ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md)), distinct from `ProjectCommercialContext` commercial posture ([ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md)).

The **normal case** is a civic address.

Architecture must also anticipate:

- vacant / rural parcel
- legal description
- parcel identifier
- municipality
- province / state
- country

A legitimate early project may be **LOCATION INCOMPLETE**. Do not implement enforcement yet.

### 2. One reusable jurisdiction resolver

CalibAi has **one** jurisdiction-resolution architecture:

```text
PROJECT LOCATION
→ COUNTRY
→ PROVINCE / STATE
→ MUNICIPALITY / COUNTY
→ APPLICABLE AHJ(S)
```

Future consumers may include Permit Intelligence, jurisdictional contracts, tax, code/compliance, and supplier geography. **Do not** create independent jurisdiction mechanisms per module.

Current `Organization.tax_jurisdiction` remains a tax-policy field. It is **not** the resolver. Later tax treatment may **consume** the resolver; it must not fork a second AHJ model.

### 3. Architect globally; implement in bounded jurisdictions

The resolver is jurisdictionally general. First **implementation** reference is Ontario; first municipal case is City of Ottawa / North Gower. Do **not** hard-code Ottawa as the universal architecture. Do **not** attempt a national library in a first product gate.

### 4. No implementation from this ADR

Accepting this ADR does **not** authorize product code, schema, migration, a Feature Gate, live lookup, geocoding services, or incomplete-location enforcement.

## Alternatives Considered

- **Reuse `Project.address` forever as the only location fact** — Rejected: insufficient to resolve AHJ for vacant/rural parcels.
- **Treat `Organization.tax_jurisdiction` as municipal jurisdiction** — Rejected: tax ≠ zoning/AHJ.
- **Per-module jurisdiction fields (Permit vs tax vs contract)** — Rejected: duplicate mechanisms will drift.
- **Require complete location before any project record** — Rejected: early projects may be LOCATION INCOMPLETE.

## Consequences

**Positive:** One location/jurisdiction spine for later permit, contract, tax, and geography consumers.  
**Negative:** Structured location and resolver remain unimplemented; current free-text address is unchanged.

## Module Ownership Impact

**Projects** owns project location facts. The jurisdiction resolver is a **reusable platform architecture**, not a second project entity. Permit Intelligence consumes resolved jurisdiction ([ADR-038](ADR-038-permit-intelligence-authority-and-rules-library.md)).

## Data Ownership Impact

Future structured location and resolved-jurisdiction records parent to `projects` unless a later ADR says otherwise. Historical issued documents pin the location/jurisdiction then in force ([ADR-039](ADR-039-permit-report-snapshot-immutability-and-workflow.md)).

## Migration Impact

Deferred. Additive only under a future Feature Gate. None in this pass.

## Testing Impact

None in this pass.

## Documentation Impact

[jurisdiction-resolution.md](../architecture/jurisdiction-resolution.md); [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md); [modules/projects.md](../modules/projects.md); indexes; current-state / handoff.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-30 |
| ChatGPT review | Permit Intelligence architecture governance pass | 2026-08-30 |
| Cursor implementation note | FG-015 foundation implemented (`e7f8a9b0c1d2`); live-migrated and **CLOSED / OPERATIONAL FOR UAT** | 2026-08-30 |
