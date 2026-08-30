# Architecture pin — Organization Brand Profile

| Attribute | Value |
|-----------|--------|
| Status | **FUTURE / NOT IMPLEMENTED** — requirement pin only |
| Date | 2026-08-30 |
| Product | The Estimator / CalibAi |
| Canonical record | This document |
| Related | [change-order-document-family.md](change-order-document-family.md) · [project-document-package.md](project-document-package.md) · [permit-and-approvals-report.md](permit-and-approvals-report.md) · [organization-and-calibration-architecture.md](organization-and-calibration-architecture.md) · [modules/proposals.md](../modules/proposals.md) · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) |

**Current vs future:** The live `Organization` row has `legal_name`, `display_name`, and `primary_address` ([`app/models/organization.py`](../../app/models/organization.py)). There is **no** Organization Brand Profile entity, **no** organization-owned logo upload, and **no** app-managed private logo store. Today, customer PDFs use a **static** Brayman Construction asset (`app/static/branding/brayman-construction-logo.png`) and optional per-template `ProposalTemplate.logo_path`. Nothing below is implemented. This pin does **not** reopen [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) (**CLOSED / OPERATIONAL FOR UAT**). Brand Profile is **not** a prerequisite for Permit Foundation V1 ([FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**) or for [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) (**APPROVED FOR IMPLEMENTATION** / **NOT STARTED**). FG-016 Permit Report PDF, if produced, uses a **neutral CalibAi** layout — do not use the static Brayman proposal logo and do not create a separate Permit-logo configuration. Later customer-facing permit PDFs consume this **one** Brand Profile.

---

## Purpose

Every contractor organization must eventually have one governed **ORGANIZATION BRAND PROFILE** used consistently by CalibAi-generated organization/customer documents.

The contractor should configure branding during **onboarding / settings**, not by repeatedly supplying branding inside each module.

---

## This pin does not authorize

- Organization Brand Profile schema
- logo storage / upload implementation
- document-template engine changes
- Change Order schema or PDF changes
- email service
- electronic signatures
- auth
- public / self-service onboarding
- Permit Intelligence
- Phase D
- supplier onboarding / BMR / Winchester
- ADR-008 acceptance
- BUILD expansion
- MONITOR / LEARN
- Feature Gate
- ADR
- migration

A later repository-first architecture assessment must decide whether branding becomes a small **platform prerequisite Feature Gate** before further customer-facing document generation. This pin does not make that decision.

---

## Minimum future brand identity (anticipate)

Do **not** invent licensing or registration fields in this pin.

- organization / legal business name
- customer-facing business name where separately governed
- logo
- address
- phone
- email
- website
- other governed organization identifiers where later required

Current `Organization.legal_name` / `display_name` / `primary_address` are **not** a Brand Profile. Do not treat them as complete branding.

The conceptual `branding_config` JSON on the intended Organization entity in [organization-and-calibration-architecture.md](organization-and-calibration-architecture.md) is **not implemented**. This pin is the governing future branding requirement; do not implement that JSON column from this pin.

---

## Logo upload (future)

A contractor must eventually be able to upload its organization logo during onboarding/settings.

The logo should be:

- organization-owned
- privately / app-managed
- safe-file validated
- stored under controlled naming
- reusable by governed document renderers
- replaceable through **explicit organization action**
- historically preservable for documents already issued

Do not implement storage or schema under this pin. Do not use remote URL-following for logo resolution as the future source of truth.

---

## Branding source of truth

The Organization Brand Profile should become the **single authoritative branding source** for future generated documents.

Potential consumers (none of these get independent logo/header settings under this pin):

- Customer Estimate / Proposal
- Change Order
- Permit & Approvals Report
- Contract
- Warranty
- Material / Procurement documents
- project reports
- QuickBooks-facing / export documents where appropriate
- other future governed PDFs / documents

**Do not** create independent logo/header settings inside each module.

Current `ProposalTemplate.logo_path` and the hardcoded static Brayman asset are **not** the intended long-term source of truth. Do not expand per-module branding under this pin.

---

## Template governance

CalibAi should continue to govern document **structure / layout**.

Organization branding should customize **identity**, not permit arbitrary uncontrolled template redesign.

Future model:

```text
CALIBAI-GOVERNED DOCUMENT TEMPLATE
+
ORGANIZATION BRAND PROFILE
+
AUTHORITATIVE PROJECT / COMMERCIAL DATA
→
GENERATED DOCUMENT SNAPSHOT
```

Do **not** create arbitrary user-uploaded Word-template support under this requirement.

---

## Brand snapshot / immutability

Later organization branding changes must **not** silently mutate historical issued documents.

Example: an organization changes its logo in 2028. That must **not** alter:

- a Proposal issued in 2026
- an Accepted Change Order issued in 2027
- an executed Contract from an earlier project

Generated / issued document snapshots must preserve the branding **actually used when issued**.

This is consistent with Constitution Article 5 (no silent overwrite of accepted commercial records) and existing Proposal Accepted immutability ([ADR-002](../adr/ADR-002-accepted-proposal-immutability.md)). Do not implement snapshot columns here.

---

## Future onboarding relationship (concept only)

Record as a future onboarding concept. **Do not reorder** the current roadmap from this pin. Sequencing is determined later through repository-first architecture governance.

```text
ORGANIZATION SETUP
→ BUSINESS IDENTITY / BRANDING
→ HISTORICAL ESTIMATE ONBOARDING
→ LABOUR / PRICING CALIBRATION
→ MATERIAL / OTHER CONFIGURATION
→ PROJECT OPERATIONS
```

[FG-013](../feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) historical-upload UX is already **CLOSED / OPERATIONAL FOR UAT**. This concept does not reopen FG-013 or FG-014.

---

## Related current code (do not change under this pin)

- [`app/models/organization.py`](../../app/models/organization.py) — identity fields only
- [`app/models/proposal.py`](../../app/models/proposal.py) — `ProposalTemplate.logo_path`
- [`app/services/proposal_pdf.py`](../../app/services/proposal_pdf.py) — template logo then default static Brayman asset
- [`app/project_controls/pdf.py`](../../app/project_controls/pdf.py) — hardcoded static Brayman logo
- [`app/templates/partials/sidebar.html`](../../app/templates/partials/sidebar.html) — app-shell Brayman logo

---

## Related

- [change-order-document-family.md](change-order-document-family.md)
- [project-document-package.md](project-document-package.md)
- [permit-and-approvals-report.md](permit-and-approvals-report.md)
- [organization-and-calibration-architecture.md](organization-and-calibration-architecture.md)
- [modules/proposals.md](../modules/proposals.md)
- [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md)
- [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md)
