# Architecture Domain Index

| Attribute | Value |
|-----------|--------|
| Status | Active |
| Updated | 2026-09-10 |

Domain architecture documents describe **intended** systems. They are not claims of current implementation unless explicitly marked Current.

| Document | Status |
|----------|--------|
| [CAR-001-calibai-product-architecture-reconciliation.md](CAR-001-calibai-product-architecture-reconciliation.md) | **Approved architectural direction** (2026-08-28); implementation not authorized |
| [plan-intelligence-and-automated-takeoff.md](plan-intelligence-and-automated-takeoff.md) | Future + Phase A / M007 page indexing current |
| [document-intelligence.md](document-intelligence.md) | Architecture (M006); upload/pages/processing **Current** (M007) |
| [sheet-intelligence.md](sheet-intelligence.md) | **Architecture (M008) + FG-004 approved** — Sheets / review **not implemented** |
| [project-document-package.md](project-document-package.md) | **Intended** — authoritative record + four outputs (1–2 Current under FG-012; output 3 Slices A+B under [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **IMPLEMENTED / NOT LIVE-MIGRATED / NOT CLOSED**; output 4 Future); Permit & Approvals Report is a **core project document** (ADR-039 **Accepted**; Pass 2 [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**); Change Order is a **transaction-document family** pin, not a numbered core output; contract/warranty generation [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED** |
| [permit-and-approvals-report.md](permit-and-approvals-report.md) | **Pass 2 CLOSED / OPERATIONAL FOR UAT** ([FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md)) — ADR-037/038/039 **Accepted**; [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT** (foundation) |
| [permit-rules-library.md](permit-rules-library.md) | **CLOSED / OPERATIONAL FOR UAT** — Permit Rules Library V1 (Ontario / Ottawa POC); [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md); [permit-rules-ontario-ottawa-sources.md](permit-rules-ontario-ottawa-sources.md) |
| [jurisdiction-resolution.md](jurisdiction-resolution.md) | **Current (FG-015 civic foundation)** — **CLOSED / OPERATIONAL FOR UAT** — project location + reusable jurisdiction resolver; [ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted**; reused by [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) |
| [organization-brand-profile.md](organization-brand-profile.md) | **CLOSED / OPERATIONAL FOR UAT** — [ADR-040](../adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) |
| [approved-document-presentation-reference-baseline.md](approved-document-presentation-reference-baseline.md) | **Governing for immutable source / provenance** — SOURCE CUSTODY **CLOSED**; [FG-022](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1** |
| [change-order-document-family.md](change-order-document-family.md) | **FUTURE / NOT IMPLEMENTED** — governed Change Order document family + email pin; existing Change Order record remains authoritative; not a Feature Gate |
| [contract-esignature-and-signed-change-order.md](contract-esignature-and-signed-change-order.md) | **ARCHITECTURE RECONNAISSANCE COMPLETE / NOT IMPLEMENTED** — Native Signing V1 recommended; counsel spec **PREPARED**; **development may proceed under separate governance**; **production activation blocked pending counsel**; no Feature Gate in this pass |
| [field-web-today-and-capture.md](field-web-today-and-capture.md) | **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN** — Item 12 Field Web / Today + Capture; [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) gate **NOT CLOSED** |
| [fg-021-field-web-v1-implementation-reconnaissance.md](fg-021-field-web-v1-implementation-reconnaissance.md) | **COMPLETE** — FG-021 file/API/schema freeze; live current = head `d2e3f4a5b6c7` |
| [fg-021-recent-observation-delete-requirement-capture.md](fg-021-recent-observation-delete-requirement-capture.md) | **CAPTURED / QUEUED / NOT AUTHORIZED** — Recent Observation Delete + iPhone swipe-left UX; retention model not chosen |
| [quickbooks-integration.md](quickbooks-integration.md) | **Intended V1 Option A Slices A+B implemented / not live-migrated** — [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md); [ADR-049](../adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**; Option B API POST-V1 |
| [fg-032-quickbooks-option-a-preflight.md](fg-032-quickbooks-option-a-preflight.md) | **RECONCILED** with Slices A+B. Migration **`e9f0a1b2c3d4`** not applied live. |
| [M004-plan-intelligence-readiness-report.md](M004-plan-intelligence-readiness-report.md) | Milestone 004 report |
| [M006-document-intelligence-readiness-report.md](M006-document-intelligence-readiness-report.md) | Milestone 006 report |
| [M008-sheet-intelligence-readiness-report.md](M008-sheet-intelligence-readiness-report.md) | Milestone 008 readiness (architecture) |
| [material-catalogue-architecture.md](material-catalogue-architecture.md) | **Partial Current** — [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**; ADR-034/035/036 **Accepted**; [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted** (MaterialRequirement ownership; FG-029 **CLOSED / OPERATIONAL FOR UAT**) |
| [fg-029-bmr-supplier-workflow-v1-preflight.md](fg-029-bmr-supplier-workflow-v1-preflight.md) | **COMPLETE.** [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| [fg-030-supplier-identity-and-access-isolation.md](fg-030-supplier-identity-and-access-isolation.md) | **RECORDED / NOT IMPLEMENTATION-AUTHORIZED.** [FG-030](../feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) |
| [fg-031-scope-delivery-make-buy-procurement-routing-preflight.md](fg-031-scope-delivery-make-buy-procurement-routing-preflight.md) | **COMPLETE (architecture recording).** [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| [architecture/supplier-catalogue-inventory-pricing.md](supplier-catalogue-inventory-pricing.md) | Future — supplier SKU/price/inventory; maps to Material Catalogue; **bulk onboarding pin FUTURE / NOT IMPLEMENTED**; does **not** own CalibraytAI identity |
| [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md) | **Partial Current** — [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**; [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT** |

Platform map: [../architecture.md](../architecture.md).
Principles: [../architecture-principles.md](../architecture-principles.md).
Roadmap: [../platform-roadmap.md](../platform-roadmap.md).
Module: [../modules/plan-intelligence.md](../modules/plan-intelligence.md).
Feature Gates: [../feature-gates/FG-002-plan-intelligence-phase-a.md](../feature-gates/FG-002-plan-intelligence-phase-a.md) · [../feature-gates/FG-003-document-intelligence-readiness.md](../feature-gates/FG-003-document-intelligence-readiness.md).
