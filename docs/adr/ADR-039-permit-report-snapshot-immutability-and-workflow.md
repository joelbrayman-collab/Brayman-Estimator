# ADR-039 — Permit Report Snapshot, Immutability, and Workflow Effect

| Field | Value |
|-------|--------|
| Title | ADR-039: Permit Report Snapshot Immutability and Workflow Effect |
| Status | **Accepted** (FG-015 versioned preliminary snapshot **CLOSED / OPERATIONAL FOR UAT**; [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) substantive Permit Report **APPROVED FOR IMPLEMENTATION** / **NOT IMPLEMENTED**) |
| Date | 2026-08-30 |
| Related | [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) · [project-document-package.md](../architecture/project-document-package.md) · [ADR-002](ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-005](ADR-005-ai-takeoff-traceability.md) **Accepted** · [ADR-006](ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-038](ADR-038-permit-intelligence-authority-and-rules-library.md) · [organization-brand-profile.md](../architecture/organization-brand-profile.md) · [change-order-document-family.md](../architecture/change-order-document-family.md) |

## Context

Permit, zoning, and approval information is time-sensitive. An issued advisory report must remain historically true. Not every finding should block estimating. The report is a **core project document**, not a Change Order transaction document, and not one of the four estimate-derived commercial outputs.

This ADR does **not** authorize implementation, schema, a Feature Gate, product enums, branding implementation, or Change Order PDF/email work.

## Decision

### 1. Snapshot chain

```text
CURRENT GOVERNING RULES
→ CITED / VERSIONED ANALYSIS
→ PROJECT PERMIT REPORT SNAPSHOT
→ IMMUTABLE HISTORY
```

A report must pin:

- project
- organization
- project location
- jurisdiction
- project type
- plan / version
- site-plan / version
- rule / source versions
- findings
- missing information
- recommended actions
- generated_at
- provenance

Later changes create a **new** report / version. **Never** rewrite historical issued reports (same immutability spirit as [ADR-002](ADR-002-accepted-proposal-immutability.md) and Principle Rule 5).

### 2. Staleness / recheck

Architecture must support **RECHECK REQUIRED / STALE** without silently rewriting the prior report.

Future recheck triggers include: location change; project type change; plan revision; site-plan revision; material site/design fact change; governing requirement change.

### 3. Finding / workflow policy

Permit findings must **not** all block estimating. Architecture should distinguish approximately:

- informational
- verify / missing information
- material risk / potential non-conformance
- blocking commercial commitment **where genuinely warranted**

Do **not** create final product enums in this pass.

A **material feasibility issue** must be capable of being surfaced **before final commercial commitment**. Plan/take-off may proceed concurrently where findings are not material blockers ([ADR-038](ADR-038-permit-intelligence-authority-and-rules-library.md)).

### 4. Document classification

The Permit & Approvals Report is a governed **core project document**.

Do **not** classify it as a Change Order transaction document. Do **not** force arbitrary “Document #7” numbering.

Preferred project-document expression:

```text
CORE DOCUMENTS / PACKAGES
+
TRANSACTION DOCUMENT FAMILIES
```

Estimate outputs 1–4 remain the commercial package ([project-document-package.md](../architecture/project-document-package.md)). Change Orders remain a repeating transaction family ([change-order-document-family.md](../architecture/change-order-document-family.md)).

### 5. Branding

Organization Brand Profile remains **FUTURE / NOT IMPLEMENTED**. It is **not** a prerequisite for implementing Permit Intelligence **data/analysis**.

When customer-facing permit PDFs are later rendered, they consume the **one** Organization Brand Profile. Do **not** create separate Permit-logo configuration.

### 6. Estimating effect

Identified cost implications may later be **proposed** as allowances/costs under explicit user action. Do **not** auto-insert estimate lines ([ADR-006](ADR-006-human-approval-before-estimate-insertion.md)).

### 7. No implementation from this ADR

Accepting this ADR does **not** authorize product code, schema, migration, a Feature Gate, PDF renderer, email, or enums.

## Alternatives Considered

- **Live report that always reflects latest by-laws** — Rejected: silently mutates history.
- **Every finding blocks estimating** — Rejected: over-blocks PLAN/PRICE work.
- **No commercial effect at all** — Rejected: material feasibility issues must be surfaceable before commitment.
- **Treat the report as a Change Order** — Rejected: wrong document family.
- **Require Brand Profile before any permit analysis** — Rejected: branding is for later document identity, not analysis.

## Consequences

**Positive:** Issued reports stay historically true; workflow can distinguish informational vs blocking findings; document family stays clean.  
**Negative:** Snapshot schema, staleness UX, and finding enums remain unimplemented.

## Module Ownership Impact

Projects owns the report snapshot / history. Estimating commits any later cost lines. Proposals/Contracts may later read findings as qualifications — they do not own the report. Plan Intelligence citations remain Plan Intelligence-owned evidence.

## Data Ownership Impact

Issued report snapshots are immutable historical records. Recheck produces a new version. Rule-library updates do not rewrite prior reports.

## Migration Impact

Deferred. None in this pass.

## Testing Impact

None in this pass.

## Documentation Impact

[permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md); [project-document-package.md](../architecture/project-document-package.md); current-state / handoff / roadmap candidate sequencing.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-30 |
| ChatGPT review | Permit Intelligence architecture governance pass | 2026-08-30 |
| Cursor implementation note | FG-015 versioned preliminary snapshot **CLOSED / OPERATIONAL FOR UAT**; FG-016 substantive report **APPROVED FOR IMPLEMENTATION** / **NOT STARTED** | 2026-08-30 |
