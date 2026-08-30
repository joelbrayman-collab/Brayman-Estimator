# ADR-038 — Permit Intelligence Authority and Rules Library

| Field | Value |
|-------|--------|
| Title | ADR-038: Permit Intelligence Authority and Permit Rules Library Provenance |
| Status | **Accepted** (FG-015 Pass 1 foundation **CLOSED / OPERATIONAL FOR UAT**; Permit Rules Library **not** populated) |
| Date | 2026-08-30 |
| Related | [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) · [jurisdiction-resolution.md](../architecture/jurisdiction-resolution.md) · [legal-content-and-templates.md](../governance/legal-content-and-templates.md) · [ADR-006](ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-010](ADR-010-build-versus-buy-document-processing.md) **Proposed** · [ADR-020](ADR-020-build-module-boundary.md) **Accepted** · [ADR-037](ADR-037-project-location-and-jurisdiction-resolution.md) · [ADR-039](ADR-039-permit-report-snapshot-immutability-and-workflow.md) |

## Context

The Permit & Approvals Report pin recorded an advisory preflight document. Reconnaissance confirmed nothing is implemented. Meaningful Permit Intelligence requires a **governed rules library** distinct from Ontario contract/warranty templates, and a hard authority boundary: CalibAi advises; the AHJ decides.

This ADR does **not** authorize implementation, schema, a Feature Gate, live scraping, external AI, automatic zoning conclusions, municipal submissions, or a national library.

## Decision

### 1. Permit Intelligence is a project capability

**Permit Intelligence** is the analysis / preflight capability.

The **Permit & Approvals Report** is its governed document output.

Do **not** reduce Permit Intelligence to a PDF form.

Projects owns the project-tied capability and report snapshot ([ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md)). Plan Intelligence owns plan/site-plan versions (read-through). BUILD may later own **post-issuance** operational evidence (permit number, inspections, occupancy) ([ADR-020](ADR-020-build-module-boundary.md)); it does **not** own preflight analysis.

### 2. Advisory vs AHJ

| Layer | Authority |
|-------|-----------|
| CalibAi Permit Intelligence | **Advisory preflight / project intelligence** |
| AHJ / municipality / regulated professional | **Final authority** |

**PASS** means only: **no issue identified against the governed checks performed.**

**PASS** must never mean: permit approved, zoning approved, or AHJ approved.

Preserve explicit advisory labeling. ChatGPT, Cursor, live web research, and AI output are **not** determinations.

### 3. Permit / Planning / Approval Rules Library

A governed **Permit Rules Library** is required for meaningful analysis. It is **separate** from the Contract / Warranty Legal Content Gate.

Future governed rule evidence should support:

- jurisdiction
- authority / source
- rule category
- citation / source location
- effective-from
- effective-to / superseded
- reviewed / retrieved date
- provenance
- applicability
- approval / review state

Do **not** populate the library in this pass. Do **not** use live scraping. AI **cannot** mark regulatory content approved (same spirit as the Legal Content Gate).

Architect globally. Implement later in **bounded** jurisdictions. First reference: **Ontario**; first municipal case: **City of Ottawa / North Gower**. Do not hard-code Ottawa as universal architecture. Do not attempt a national library in the first product gate.

### 4. Two-pass model

**Pass 1:** location + project type → **preliminary Permit Profile** (may be LOCATION INCOMPLETE).

**Pass 2:** plans + site plan + project facts + governed requirements → project-specific Permit Intelligence → Permit & Approvals Report.

Plan / take-off work may proceed concurrently where permit findings are not material blockers.

### 5. Plan Intelligence is read-through

Future Permit Intelligence may consume reviewed plan/site facts with provenance (footprint, height, setbacks, site dimensions, use evidence, plan/site-plan identity).

This does **not** authorize Phase D, mutation of take-off evidence, automatic estimate insertion ([ADR-006](ADR-006-human-approval-before-estimate-insertion.md)), or a real external AI provider ([ADR-010](ADR-010-build-versus-buy-document-processing.md) remains Proposed).

### 6. Estimating and contracts

Permit Intelligence may later **identify** scope/cost implications (survey, grading, septic, engineering, variance, entrance permit, conservation, municipal fees). It must **not** auto-create `EstimateLineItem` rows. Future user-controlled action may propose adding allowance/cost. Human authority remains required.

Permit findings may later **inform** contract assumptions, qualifications, exclusions, and conditions precedent. Do **not** generate legal language here. The contract/warranty library remains separate.

### 7. No implementation from this ADR

Accepting this ADR does **not** authorize product code, schema, migration, a Feature Gate, library population, live lookup, or external AI.

## Alternatives Considered

- **PDF-only form with no engine** — Rejected: the report is an output, not the capability.
- **Reuse Legal Content Gate as the zoning/permit library** — Rejected: contract/warranty ≠ municipal/AHJ rules.
- **Live scrape / external AI as V1 truth** — Rejected: not authorized; provenance and human review required.
- **National rules library in the first gate** — Rejected: unbounded; Ontario-first.
- **Permit Intelligence owns BUILD inspections** — Rejected: post-issuance operational evidence is BUILD ([ADR-020](ADR-020-build-module-boundary.md)).

## Consequences

**Positive:** Hard AHJ boundary; distinct rules library; two-pass workflow; no silent commercial or legal generation.  
**Negative:** Capability remains unimplemented; first useful report needs a later bounded curated Ontario/Ottawa gate.

## Module Ownership Impact

Projects owns the project-tied Permit Intelligence capability and report snapshot. Plan Intelligence remains plan/site-plan owner (read-through). Legal Content Gate unchanged. BUILD unchanged except the post-issuance boundary. Permit Rules Library is a **platform governed source**, not org commercial intelligence.

## Data Ownership Impact

Rules library records are platform-governed, versioned, and provenance-bearing. Project analyses and reports are organization-scoped and project-tied. Do not pool one contractor’s permit analyses as another’s defaults.

## Migration Impact

Deferred. None in this pass.

## Testing Impact

None in this pass.

## Documentation Impact

[permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md); [modules/permit-intelligence.md](../modules/permit-intelligence.md); [legal-content-and-templates.md](../governance/legal-content-and-templates.md); Plan Intelligence / Projects / BUILD cross-links.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-30 |
| ChatGPT review | Permit Intelligence architecture governance pass | 2026-08-30 |
| Cursor implementation note | FG-015 preliminary profile **CLOSED / OPERATIONAL FOR UAT**; Pass 2 / rules library not implemented | 2026-08-30 |
