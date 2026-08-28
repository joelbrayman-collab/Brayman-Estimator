# Architecture Decision Records

| Attribute | Value |
|-----------|--------|
| Status | Active |
| Updated | 2026-08-28 |

## When an ADR is required

See [platform-governance.md](../platform-governance.md). In short: principles changes, ownership transfers, schema policy, immutability/audit/financial controls, integrations, or material roadmap deviations.

## Status discipline

**Proposed** is not **Accepted**. Citing a Proposed ADR in a module, Feature Gate, or roadmap does not change its status. Implementation still requires Feature Gate + accepted decisions where the ADR itself requires acceptance.

**Accepted in this repository today:** ADR-002 (M003); ADR-017, ADR-018 (Sheet workflow/uniqueness; implemented in M009); ADR-019, ADR-020, ADR-022, ADR-023, ADR-024 (CAR-001 architectural direction).

## Process

1. Copy [ADR-000-template.md](ADR-000-template.md) to `ADR-NNN-short-title.md`
2. Set Status to Proposed → Accepted / Rejected / Superseded
3. Obtain Joel approval for Accepted decisions
4. Link from module docs, architecture.md, feature gates, and chat-workflow-log

## Index

### Proposals (Milestone 002–003)

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](ADR-001-proposal-snapshot-ownership.md) | Proposal Snapshot Ownership | Proposed |
| [ADR-002](ADR-002-accepted-proposal-immutability.md) | Accepted Proposal Immutability | **Accepted** (M003) |
| [ADR-003](ADR-003-optional-crm-foreign-keys.md) | Optional CRM Foreign Keys on Proposals | Proposed |
| [ADR-004](ADR-004-proposal-acceptance-workflow.md) | Proposal Acceptance Workflow | Proposed |

### Plan Intelligence / Document Intelligence (Milestone 004–007)

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-005](ADR-005-ai-takeoff-traceability.md) | AI Take-Off Source Traceability | Proposed |
| [ADR-006](ADR-006-human-approval-before-estimate-insertion.md) | Human Approval Before Estimate Insertion | Proposed |
| [ADR-007](ADR-007-plan-and-estimate-version-ownership.md) | Plan and Estimate Version Ownership | Proposed |
| [ADR-009](ADR-009-pdf-first-versus-cad-first.md) | PDF-First versus CAD-First Ingestion | Proposed |
| [ADR-011](ADR-011-ai-confidence-threshold-policy.md) | AI Confidence Threshold Policy | Proposed |
| [ADR-010](ADR-010-build-versus-buy-document-processing.md) | Build versus Buy for CAD and Document Processing | Proposed |
| [ADR-012](ADR-012-plan-document-version-ownership.md) | Plan Document Version Ownership | Proposed |
| [ADR-013](ADR-013-document-intelligence-layer-boundary.md) | Document Intelligence Layer Boundary | Proposed |
| [ADR-014](ADR-014-sheet-identity-and-page-mapping.md) | Sheet Identity and Page Mapping | Proposed |
| [ADR-015](ADR-015-extracted-metadata-ownership-and-provenance.md) | Extracted Metadata Ownership and Provenance | Proposed |
| [ADR-016](ADR-016-document-intelligence-search-strategy.md) | Document Intelligence Search Strategy | Proposed |

### Sheet Intelligence (Milestone 008 — architecture only)

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-017](ADR-017-sheet-metadata-suggestion-and-review-workflow.md) | Sheet Metadata Suggestion and Review Workflow | **Accepted** (2026-08-28; FG-004; implemented in M009) |
| [ADR-018](ADR-018-sheet-uniqueness-duplicates-and-supersession.md) | Sheet Uniqueness, Duplicates, and Supersession | **Accepted** (2026-08-28; FG-004; implemented in M009) |

### Scale Calibration & Measurement (Milestone 010)

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-026](ADR-026-scale-ownership-and-calibration-provenance.md) | Scale Ownership, Multi-Scale Viewports, and Calibration Provenance | **Proposed** (FG-005) |
| [ADR-027](ADR-027-pdf-rendering-and-normalized-coordinate-system.md) | PDF Rendering and Normalized Document Coordinate System | **Proposed** (FG-005) |

### Supplier (strategic)

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-008](ADR-008-supplier-price-snapshotting.md) | Supplier Price Snapshotting | Proposed |

### CalibAi / CAR-001 (2026-08-28)

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md) | CalibAi Lifecycle and Project Hub | **Accepted** (direction; no schema change) |
| [ADR-020](ADR-020-build-module-boundary.md) | BUILD Module Boundary vs Project Controls | **Accepted** (boundary; not implemented) |
| [ADR-021](ADR-021-monitor-commercial-baseline.md) | MONITOR Commercial Baseline | **Proposed** |
| [ADR-022](ADR-022-field-client-and-shared-api.md) | Field Client and Shared API | **Accepted** (direction; no API/mobile code) |
| [ADR-023](ADR-023-field-evidence-provenance.md) | Field Evidence Original vs Derived | **Accepted** (rules; no voice/photo code) |
| [ADR-024](ADR-024-learn-recommendation-boundary.md) | LEARN Recommendation Boundary | **Accepted** (boundary; no ML) |
| [ADR-025](ADR-025-pricing-policy-versus-estimate-markup-stack.md) | Gross-Margin Policy vs Markup Stack | **Proposed** |

CAR-001 record: [../architecture/CAR-001-calibai-product-architecture-reconciliation.md](../architecture/CAR-001-calibai-product-architecture-reconciliation.md).

Related Feature Gates: [FG-001 Proposals Module](../feature-gates/FG-001-proposals-module.md) · [FG-002 Plan Intelligence Phase A](../feature-gates/FG-002-plan-intelligence-phase-a.md) · [FG-003 Document Intelligence Readiness](../feature-gates/FG-003-document-intelligence-readiness.md).
Strategic architecture: [../architecture/](../architecture/).
M004 readiness: [../architecture/M004-plan-intelligence-readiness-report.md](../architecture/M004-plan-intelligence-readiness-report.md).
M006 readiness: [../architecture/M006-document-intelligence-readiness-report.md](../architecture/M006-document-intelligence-readiness-report.md).
M008 readiness: [../architecture/M008-sheet-intelligence-readiness-report.md](../architecture/M008-sheet-intelligence-readiness-report.md).

> ADR-017/018 are **Accepted** and implemented in [M009](../feature-gates/FG-004-m009-sheet-classification.md). M010 Scale Calibration is governed by [FG-005](../feature-gates/FG-005-m010-scale-calibration.md) with Proposed ADR-026 and ADR-027. Implementation requires a dedicated implementation prompt.
