# The Estimator — Documentation Index

| Attribute | Value |
|-----------|--------|
| Status | Authoritative documentation map |
| Updated | 2026-09-02 |
| Product | The Estimator (Brayman Estimator) |

## Purpose

This folder is the **system of record** for platform vision, architecture, governance, workflow, and session continuity. Chat history is not authoritative.

## Authority layers (do not confuse)

| Layer | Documents | Role |
|-------|-----------|------|
| **Constitutional** | [platform-constitution.md](platform-constitution.md) | Highest-order, rarely changed platform law |
| **Architectural** | [architecture-principles.md](architecture-principles.md), [architecture.md](architecture.md), [adr/](adr/), [modules/](modules/) | Durable rules, structure, decisions, ownership |
| **Operational status** | [project-state-report.md](project-state-report.md), [current-state.md](current-state.md), [session-handoff.md](session-handoff.md) | Milestone state, detailed snapshot, immediate resume |
| **Historical records** | [milestones.md](milestones.md), [chat-workflow-log.md](chat-workflow-log.md) | Append-only milestone and decision history |
| **Reusable templates** | [prompts/](prompts/), [adr/ADR-000-template.md](adr/ADR-000-template.md) | Starting points for Cursor work and ADRs |

## Required reading order (before implementation)

1. [`../AGENTS.md`](../AGENTS.md)
2. [`platform-constitution.md`](platform-constitution.md)
3. [`project-state-report.md`](project-state-report.md)
4. [`current-state.md`](current-state.md)
5. [`platform-vision.md`](platform-vision.md)
6. [`architecture-principles.md`](architecture-principles.md)
7. [`architecture.md`](architecture.md)
8. [`platform-roadmap.md`](platform-roadmap.md)
9. Relevant module document under [`modules/`](modules/)
10. Relevant ADRs under [`adr/`](adr/)
11. Relevant Feature Gate under [`feature-gates/`](feature-gates/)
12. [`session-handoff.md`](session-handoff.md)
13. Relevant prompt template under [`prompts/`](prompts/)

Also read [`platform-governance.md`](platform-governance.md), [`governance/continuity-and-anti-drift.md`](governance/continuity-and-anti-drift.md), [`governance/review-turnover-protocol.md`](governance/review-turnover-protocol.md), and [`definition-of-done.md`](definition-of-done.md) before starting any feature.

## Document catalog

| Document | Purpose | Authority |
|----------|---------|-----------|
| [platform-constitution.md](platform-constitution.md) | Highest-order platform law (Articles 1–12) | **Constitutional** |
| [project-state-report.md](project-state-report.md) | Milestone-level state + template | Operational (mandatory at milestones) |
| [milestones.md](milestones.md) | Append-only milestone history | Historical |
| [prompts/](prompts/) | Reusable Cursor prompt templates | Templates |
| [platform-vision.md](platform-vision.md) | CalibAi vision + current Estimator core | Product intent (Joel-approved CAR-001) |
| [architecture-principles.md](architecture-principles.md) | Numbered durable platform rules | **Architectural** — changes require ADR + Joel |
| [architecture.md](architecture.md) | Current vs intended vs future architecture | Factual for *current*; aspirational elsewhere |
| [architecture/](architecture/) | Domain architecture (Plan Intelligence, Supplier, …) | Future unless marked Current |
| [architecture/material-catalogue-architecture.md](architecture/material-catalogue-architecture.md) | CalibAi Material Catalogue (what the project requires; CostItem is not identity) | **Partial Current** — [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**; ADR-034/035/036 **Accepted** |
| [adr/ADR-034-canonical-material-identity-and-ownership.md](adr/ADR-034-canonical-material-identity-and-ownership.md) | CalibAi canonical material identity and ownership | **Accepted** (architecture only) |
| [adr/ADR-035-material-quantity-uom-and-requirement-boundary.md](adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) | Material quantity, UOM, and requirement boundary | **Accepted** (architecture only; Phase D / MaterialRequirement not authorized) |
| [adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md](adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) | Material commercial evidence and supplier-neutral mapping | **Accepted** (architecture only; ADR-008 remains Proposed) |
| [architecture/supplier-catalogue-inventory-pricing.md](architecture/supplier-catalogue-inventory-pricing.md) | Supplier catalogue, inventory, pricing; governed bulk onboarding pin | **Future / NOT IMPLEMENTED** — does not own CalibAi identity; bulk onboarding is a requirement pin only |
| [architecture/supplier-channel-and-launch-partner.md](architecture/supplier-channel-and-launch-partner.md) | Supplier channel, Winchester launch/reference, dual relationships | **Future** — [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** (not implemented) |
| [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md) | CalibAi product/architecture reconciliation | **Approved direction** — not implementation |
| [architecture/M004-plan-intelligence-readiness-report.md](architecture/M004-plan-intelligence-readiness-report.md) | Milestone 004 readiness report | Historical / operational |
| [architecture/document-intelligence.md](architecture/document-intelligence.md) | Document Intelligence (packages, pages, search) | Architecture (M006); partial Current (M007) |
| [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md) | Sheet Intelligence (sheet entities, review) | Architecture (M008); **Implemented (M009)** |
| [architecture/project-document-package.md](architecture/project-document-package.md) | Authoritative record + four core outputs | Outputs 1–2: [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**. Outputs 3–4 **Future**. Permit & Approvals Report is a **core project document**; Pass 2 [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT** (ADR-039). Change Order document family pin **FUTURE / NOT IMPLEMENTED**. |
| [architecture/permit-and-approvals-report.md](architecture/permit-and-approvals-report.md) | Permit Intelligence + Permit & Approvals Report | **Pass 2 CLOSED / OPERATIONAL FOR UAT** ([FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md)) — ADR-037/038/039 **Accepted**; [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT** |
| [architecture/permit-rules-library.md](architecture/permit-rules-library.md) | Permit Rules Library V1 (Ontario / Ottawa POC) | **CLOSED / OPERATIONAL FOR UAT** — [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md); 10 APPROVED rules; [sources](architecture/permit-rules-ontario-ottawa-sources.md) |
| [architecture/jurisdiction-resolution.md](architecture/jurisdiction-resolution.md) | Project location and reusable jurisdiction resolver | **Current (FG-015 civic foundation)** — **CLOSED / OPERATIONAL FOR UAT** — [ADR-037](adr/ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted**; reused by [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) |
| [adr/ADR-037-project-location-and-jurisdiction-resolution.md](adr/ADR-037-project-location-and-jurisdiction-resolution.md) | Project location and jurisdiction resolution ownership | **Accepted** (FG-015 civic location + resolver **CLOSED / OPERATIONAL FOR UAT**) |
| [adr/ADR-038-permit-intelligence-authority-and-rules-library.md](adr/ADR-038-permit-intelligence-authority-and-rules-library.md) | Permit Intelligence authority and Permit Rules Library provenance | **Accepted** (FG-015 Pass 1 **CLOSED / OPERATIONAL FOR UAT**; FG-016 **CLOSED / OPERATIONAL FOR UAT**; 10 APPROVED rules) |
| [adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md](adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) | Permit report snapshot immutability and workflow | **Accepted** (FG-015 preliminary snapshot **CLOSED / OPERATIONAL FOR UAT**; FG-016 substantive report **CLOSED / OPERATIONAL FOR UAT**) |
| [modules/permit-intelligence.md](modules/permit-intelligence.md) | Permit Intelligence capability ownership | Pass 1 **Current (FG-015)** **CLOSED / OPERATIONAL FOR UAT**; Pass 2 [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT** |
| [architecture/organization-brand-profile.md](architecture/organization-brand-profile.md) | Organization Brand Profile, logo, brand snapshot | **CLOSED / OPERATIONAL FOR UAT** — [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) |
| [architecture/change-order-document-family.md](architecture/change-order-document-family.md) | Governed Change Order document family (snapshot / preview / email) | **Future / NOT IMPLEMENTED** — requirement pin only; existing Change Order record remains authoritative; not a Feature Gate |
| [architecture/contract-esignature-and-signed-change-order.md](architecture/contract-esignature-and-signed-change-order.md) | Contract, e-signature, and signed Change Orders | **ARCHITECTURE RECONNAISSANCE COMPLETE / NOT IMPLEMENTED** — recommendation **NATIVE V1**; counsel spec **PREPARED**; **development may proceed under separate governance**; **production activation blocked pending counsel**; no Feature Gate in this pass |
| [architecture/field-web-today-and-capture.md](architecture/field-web-today-and-capture.md) | Field Web / Today + Capture (roadmap Item 12) | **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING** — [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) gate **NOT CLOSED** |
| [architecture/fg-021-field-web-v1-implementation-reconnaissance.md](architecture/fg-021-field-web-v1-implementation-reconnaissance.md) | FG-021 Field Web V1 implementation reconnaissance | **COMPLETE** — product **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING**; live current = head `d2e3f4a5b6c7` |
| [legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md) | Native electronic signing Change Order process — counsel review specification | **DRAFT FOR ONTARIO COUNSEL REVIEW / NOT LEGAL APPROVAL / NOT IMPLEMENTED** |
| [architecture/build-media-storage-lifecycle.md](architecture/build-media-storage-lifecycle.md) | BUILD Original Source vs Compatible Rendition vs Closed Project Archive | **Architecture pin** — HEIC/HEIF JPEG renditions **implemented**; Closeout **not implemented**; FG-020 Original Source custody exists |
| [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md) | QuickBooks export pipeline boundary | **Future** — not implemented |
| [architecture/M006-document-intelligence-readiness-report.md](architecture/M006-document-intelligence-readiness-report.md) | Milestone 006 readiness report | Historical / operational |
| [architecture/M008-sheet-intelligence-readiness-report.md](architecture/M008-sheet-intelligence-readiness-report.md) | Milestone 008 readiness report | Historical / operational |
| [architecture/historical-estimates-source-manifest.md](architecture/historical-estimates-source-manifest.md) | Historical estimate source provenance manifest | **Operational / Metadata (Phase A)** |
| [architecture/historical-estimate-ingestion-architecture.md](architecture/historical-estimate-ingestion-architecture.md) | Historical estimate ingestion architecture & audit | **Architecture & Ingestion Specification (Phase A & B Complete)** |
| [architecture/organization-and-calibration-architecture.md](architecture/organization-and-calibration-architecture.md) | Organization & calibration architecture | **Architecture / Governance (Phase A Complete)** |
| [architecture/labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md) | Labour Engine Phase B architecture | **Approved; FG-008 IMPLEMENTED / VERIFIED / LIVE-MIGRATED** (`f2c3d4e5f6a7`) |
| [architecture/organization-calibrated-pricing-engine-architecture.md](architecture/organization-calibrated-pricing-engine-architecture.md) | Organization-Calibrated Pricing Engine architecture | **Approved** — **IMPLEMENTED / VERIFIED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| [feature-gates/FG-009-organization-calibrated-pricing-engine.md](feature-gates/FG-009-organization-calibrated-pricing-engine.md) | Organization-Calibrated Pricing Engine Feature Gate | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| [feature-gates/FG-008-labour-engine-phase-b.md](feature-gates/FG-008-labour-engine-phase-b.md) | Labour Engine Phase B Feature Gate | **IMPLEMENTED / VERIFIED** |
| [architecture/ai-takeoff-quantity-extraction-foundation.md](architecture/ai-takeoff-quantity-extraction-foundation.md) | AI Take-off / Quantity Extraction Foundation architecture | **Approved** — FG-010 **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| [feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) | Contractor Calibration Onboarding / Historical Estimate Upload UX | **CLOSED / OPERATIONAL FOR UAT** |
| [feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) | Material Catalogue V1 — Dimensional Lumber + Sheet Goods | **CLOSED / OPERATIONAL FOR UAT** |
| [feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) | Permit Foundation V1 — Project Location, Jurisdiction & Preliminary Permit Profile | **CLOSED / OPERATIONAL FOR UAT** |
| [feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) | Ontario / Ottawa Permit Intelligence POC — Governed Rules + Mike Pratt Reference | **CLOSED / OPERATIONAL FOR UAT** |
| [feature-gates/FG-017-organization-brand-profile-v1.md](feature-gates/FG-017-organization-brand-profile-v1.md) | Organization Brand Profile V1 — Identity, Logo Custody, and Proposal Brand Snapshot | **CLOSED / OPERATIONAL FOR UAT** |
| [feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) | Organization Authentication, Actor Identity, and Membership V1 | **CLOSED / OPERATIONAL FOR UAT** — [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted** |
| [feature-gates/FG-019-shared-api-foundation-v1.md](feature-gates/FG-019-shared-api-foundation-v1.md) | Shared API Foundation V1 — Authenticated JSON Transport | **CLOSED / OPERATIONAL FOR UAT** — GET-only `/api/v1`; no migration |
| [adr/ADR-040-organization-brand-profile.md](adr/ADR-040-organization-brand-profile.md) | Organization Brand Profile, logo custody, issued-document brand snapshots | **Accepted** — [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| [adr/ADR-041-user-membership-and-office-authentication.md](adr/ADR-041-user-membership-and-office-authentication.md) | Durable User, Organization membership, office authentication | **Accepted** — [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| [adr/ADR-042-build-field-evidence-and-iphone-first-capture.md](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) | BUILD field evidence, original custody, desktop review, iPhone-first capture | **Accepted** — [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT** |
| [feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) | BUILD Field Capture V1 — Project Field Observation Foundation | **CLOSED / OPERATIONAL FOR UAT** |
| [adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) | Field Web capture reliability, local pending capture, idempotent replay | **Accepted** — [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING** |
| [feature-gates/FG-021-field-web-v1-today-and-capture.md](feature-gates/FG-021-field-web-v1-today-and-capture.md) | Field Web V1 — Today + Capture | **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING** |
| [adr/ADR-032-app-managed-historical-workbook-storage.md](adr/ADR-032-app-managed-historical-workbook-storage.md) | App-managed immutable historical workbook storage / source custody | **Accepted** (FG-013 **CLOSED / OPERATIONAL FOR UAT**; revision `c5d6e7f8a9b0` **gate-at-close** live current=head) |
| [adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) | Supplier neutrality and Winchester launch-partner channel | **Accepted** (architecture only; not implemented) |
| [feature-gates/FG-012-estimate-output-consistency.md](feature-gates/FG-012-estimate-output-consistency.md) | Internal Detailed Cost Breakdown + Customer Estimate Consistency | **CLOSED / OPERATIONAL FOR UAT** |
| [feature-gates/FG-011-project-hub-ux.md](feature-gates/FG-011-project-hub-ux.md) | Project Hub UX Feature Gate | **CLOSED / OPERATIONAL FOR UAT** |
| [adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md](adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) | Canonical Labour Task, Production Standard, Calibration Lifecycle | **Accepted** |
| [adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md](adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) | Organization-owned pricing policy and estimate pricing snapshot | **Accepted** |
| [feature-gates/FG-006-historical-estimate-ingestion-phase-b.md](feature-gates/FG-006-historical-estimate-ingestion-phase-b.md) | Historical estimate ingestion Phase B Feature Gate | **Feature Gate (FG-006 Approved & Implemented)** |
| [feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md](feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md) | M011 Organization Foundation & Project Commercial Context Feature Gate | **Feature Gate (M011 Approved & Implemented)** |
| [adr/ADR-028-organization-foundation-and-project-commercial-context.md](adr/ADR-028-organization-foundation-and-project-commercial-context.md) | Organization Foundation, Multi-Tenant Boundary, and Project Commercial Context ADR | **Architecture Decision (ADR-028 Accepted)** |
| [platform-governance.md](platform-governance.md) | Decision authority, Feature Gate, ownership, drift stop | **Governing** |
| [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md) | Continuity, anti-drift, preflight, rollover, protected assets | **Governing** |
| [governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) | Review Turnover procedure, delta ledger, fresh chat startup | **Governing** |
| [pricing-policy.md](pricing-policy.md) | Labour rate, gross margin, placeholder rules | **Governing** (product policy) |
| [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md) | Ontario contract + warranty template governance; Legal Content Gate | **Governing** — templates remain separate from the signing-process counsel draft |
| [development-workflow.md](development-workflow.md) | Joel → ChatGPT → Cursor lifecycle | **Governing** for AI sessions |
| [documentation-standards.md](documentation-standards.md) | How docs are written and updated | Governing for docs |
| [testing-standards.md](testing-standards.md) | Test expectations | Governing for QA |
| [testing/uat-reference-cases.md](testing/uat-reference-cases.md) | UAT reference projects (e.g. 3415 Roger Stevens) | Governing for UAT |
| [git-workflow.md](git-workflow.md) | Branching, commits, migration safety | Governing for git |
| [definition-of-done.md](definition-of-done.md) | Completion checklist | **Governing** |
| [platform-roadmap.md](platform-roadmap.md) | Completed / current / future / deferred | Planning (keep current) |
| [current-state.md](current-state.md) | Verified snapshot of the repo | Operational (refresh often) |
| [session-handoff.md](session-handoff.md) | Recover after chat/context loss | Continuity (update every session) |
| [chat-workflow-log.md](chat-workflow-log.md) | Memorialized decisions & Cursor outcomes | Continuity (append, do not overwrite) |
| [aiRIA-lessons-adopted.md](aiRIA-lessons-adopted.md) | Transferable process lessons | Reference |
| [adr/](adr/) | Architecture Decision Records | Decisions |
| [feature-gates/](feature-gates/) | Feature Gate documents (pre-implementation) | **Governing** for scope |
| [modules/](modules/) | Per-module ownership & boundaries | Ownership |

## Must update after every feature

At minimum:

- [`current-state.md`](current-state.md)
- [`session-handoff.md`](session-handoff.md)
- [`chat-workflow-log.md`](chat-workflow-log.md) (new entry)
- [`platform-roadmap.md`](platform-roadmap.md) (if status changed)
- [`project-state-report.md`](project-state-report.md) (at milestone completion / major interruption)
- [`milestones.md`](milestones.md) (when a milestone completes)
- Relevant [`modules/*.md`](modules/)
- ADR if a decision changed
- Tests (see definition of done)

## Where to begin

| Role | Start here |
|------|------------|
| New developer / AI agent | Reading order above |
| Resume after a pause | [`session-handoff.md`](session-handoff.md) then [`project-state-report.md`](project-state-report.md) and [`current-state.md`](current-state.md) |
| Propose a feature | [`platform-governance.md`](platform-governance.md) Feature Gate + [`prompts/`](prompts/) |
| Implement in Cursor | [`../AGENTS.md`](../AGENTS.md) + `.cursor/rules/` + filled prompt template |
