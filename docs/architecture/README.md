# Architecture Domain Index

| Attribute | Value |
|-----------|--------|
| Status | Active |
| Updated | 2026-09-01 |

Domain architecture documents describe **intended** systems. They are not claims of current implementation unless explicitly marked Current.

| Document | Status |
|----------|--------|
| [CAR-001-calibai-product-architecture-reconciliation.md](CAR-001-calibai-product-architecture-reconciliation.md) | **Approved architectural direction** (2026-08-28); implementation not authorized |
| [plan-intelligence-and-automated-takeoff.md](plan-intelligence-and-automated-takeoff.md) | Future + Phase A / M007 page indexing current |
| [document-intelligence.md](document-intelligence.md) | Architecture (M006); upload/pages/processing **Current** (M007) |
| [sheet-intelligence.md](sheet-intelligence.md) | **Architecture (M008) + FG-004 approved** — Sheets / review **not implemented** |
| [project-document-package.md](project-document-package.md) | **Intended** — authoritative record + four outputs (1–2 Current under FG-012; 3–4 Future); Permit & Approvals Report is a **core project document** (ADR-039 **Accepted**; Pass 2 [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**); Change Order is a **transaction-document family** pin, not a numbered core output |
| [permit-and-approvals-report.md](permit-and-approvals-report.md) | **Pass 2 CLOSED / OPERATIONAL FOR UAT** ([FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md)) — ADR-037/038/039 **Accepted**; [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT** (foundation) |
| [permit-rules-library.md](permit-rules-library.md) | **CLOSED / OPERATIONAL FOR UAT** — Permit Rules Library V1 (Ontario / Ottawa POC); [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md); [permit-rules-ontario-ottawa-sources.md](permit-rules-ontario-ottawa-sources.md) |
| [jurisdiction-resolution.md](jurisdiction-resolution.md) | **Current (FG-015 civic foundation)** — **CLOSED / OPERATIONAL FOR UAT** — project location + reusable jurisdiction resolver; [ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted**; reused by [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) |
| [organization-brand-profile.md](organization-brand-profile.md) | **CLOSED / OPERATIONAL FOR UAT** — [ADR-040](../adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) |
| [change-order-document-family.md](change-order-document-family.md) | **FUTURE / NOT IMPLEMENTED** — governed Change Order document family + email pin; existing Change Order record remains authoritative; not a Feature Gate |
| [contract-esignature-and-signed-change-order.md](contract-esignature-and-signed-change-order.md) | **ARCHITECTURE RECONNAISSANCE COMPLETE / NOT IMPLEMENTED** — Native Signing V1 recommended; counsel spec **PREPARED**; **development may proceed under separate governance**; **production activation blocked pending counsel**; no Feature Gate in this pass |
| [field-web-today-and-capture.md](field-web-today-and-capture.md) | **ARCHITECTURE RECONNAISSANCE COMPLETE / NOT IMPLEMENTED** — Item 12 Field Web / Today + Capture; implementation **NOT AUTHORIZED**; no Feature Gate |
| [quickbooks-integration.md](quickbooks-integration.md) | **Future** — export pipeline boundary (not implemented) |
| [M004-plan-intelligence-readiness-report.md](M004-plan-intelligence-readiness-report.md) | Milestone 004 report |
| [M006-document-intelligence-readiness-report.md](M006-document-intelligence-readiness-report.md) | Milestone 006 report |
| [M008-sheet-intelligence-readiness-report.md](M008-sheet-intelligence-readiness-report.md) | Milestone 008 readiness (architecture) |
| [material-catalogue-architecture.md](material-catalogue-architecture.md) | **Partial Current** — [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**; ADR-034/035/036 **Accepted** |
| [architecture/supplier-catalogue-inventory-pricing.md](supplier-catalogue-inventory-pricing.md) | Future — supplier SKU/price/inventory; maps to Material Catalogue; **bulk onboarding pin FUTURE / NOT IMPLEMENTED**; does **not** own CalibAi identity |
| [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md) | **Future** — [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** (direction only; not implemented) |

Platform map: [../architecture.md](../architecture.md).
Principles: [../architecture-principles.md](../architecture-principles.md).
Roadmap: [../platform-roadmap.md](../platform-roadmap.md).
Module: [../modules/plan-intelligence.md](../modules/plan-intelligence.md).
Feature Gates: [../feature-gates/FG-002-plan-intelligence-phase-a.md](../feature-gates/FG-002-plan-intelligence-phase-a.md) · [../feature-gates/FG-003-document-intelligence-readiness.md](../feature-gates/FG-003-document-intelligence-readiness.md).
