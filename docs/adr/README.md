# Architecture Decision Records

| Attribute | Value |
|-----------|--------|
| Status | Active |
| Updated | 2026-07-25 |

## When an ADR is required

See [platform-governance.md](../platform-governance.md). In short: principles changes, ownership transfers, schema policy, immutability/audit/financial controls, integrations, or material roadmap deviations.

## Process

1. Copy [ADR-000-template.md](ADR-000-template.md) to `ADR-NNN-short-title.md`
2. Set Status to Proposed → Accepted / Rejected / Superseded
3. Obtain Joel approval for Accepted decisions
4. Link from module docs, architecture.md, feature gates, and chat-workflow-log

## Index

### Proposals (Milestone 002)

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](ADR-001-proposal-snapshot-ownership.md) | Proposal Snapshot Ownership | Proposed |
| [ADR-002](ADR-002-accepted-proposal-immutability.md) | Accepted Proposal Immutability | **Accepted** (M003) |
| [ADR-003](ADR-003-optional-crm-foreign-keys.md) | Optional CRM Foreign Keys on Proposals | Proposed |
| [ADR-004](ADR-004-proposal-acceptance-workflow.md) | Proposal Acceptance Workflow | Proposed |

### Plan Intelligence / Take-Off / Supplier (strategic)

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-005](ADR-005-ai-takeoff-traceability.md) | AI-Generated Take-Off Traceability | Proposed |
| [ADR-006](ADR-006-human-approval-before-estimate-insertion.md) | Human Approval Before Estimate Insertion | Proposed |
| [ADR-007](ADR-007-plan-and-estimate-version-ownership.md) | Plan and Estimate Version Ownership | Proposed |
| [ADR-008](ADR-008-supplier-price-snapshotting.md) | Supplier Price Snapshotting | Proposed |
| [ADR-009](ADR-009-pdf-first-versus-cad-first.md) | PDF-First versus CAD-First Ingestion | Proposed |
| [ADR-010](ADR-010-build-versus-buy-document-processing.md) | Build versus Buy for CAD and Document Processing | Proposed |

Related Feature Gate: [FG-001 Proposals Module](../feature-gates/FG-001-proposals-module.md).
Strategic architecture: [../architecture/](../architecture/).
