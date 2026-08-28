# Module — Plan Intelligence

| Attribute | Value |
|-----------|--------|
| Status | **Phase A + M007 indexing + M009 Sheet classification implemented**; Scale / take-off / AI not started |
| Updated | 2026-08-28 |
| Code | `app/plan_intelligence/` |
| Feature Gates | [FG-002](../feature-gates/FG-002-plan-intelligence-phase-a.md) · [FG-003](../feature-gates/FG-003-document-intelligence-readiness.md) · [FG-004](../feature-gates/FG-004-m009-sheet-classification.md) · [FG-005](../feature-gates/FG-005-m010-scale-calibration.md) |
| Architecture | [../architecture/plan-intelligence-and-automated-takeoff.md](../architecture/plan-intelligence-and-automated-takeoff.md) · [../architecture/document-intelligence.md](../architecture/document-intelligence.md) · [../architecture/sheet-intelligence.md](../architecture/sheet-intelligence.md) |
| Readiness | [../architecture/M004-plan-intelligence-readiness-report.md](../architecture/M004-plan-intelligence-readiness-report.md) · [../architecture/M006-document-intelligence-readiness-report.md](../architecture/M006-document-intelligence-readiness-report.md) · [../architecture/M008-sheet-intelligence-readiness-report.md](../architecture/M008-sheet-intelligence-readiness-report.md) |

## Purpose

Plan Intelligence is the strategic upstream capability of The Estimator. It turns construction plan sets into **source-traceable, human-approved quantity take-offs** that feed the existing Estimating module (assemblies, labour, materials, markups) and, downstream, Proposals and procurement—without silently inventing commercial numbers.

**Long-term flow (differentiator):**

```text
Construction Plans
        ↓
AI-assisted Quantity Take-Off  ← Plan Intelligence (this module)
        ↓
Estimate Assemblies            ← Estimating (existing)
        ↓
Labour / Material Pricing
        ↓
Proposal                       ← Proposals (existing)
        ↓
Procurement
        ↓
Project Cost Tracking
```

Proposal generation already exists. Plan Intelligence is the next major platform capability.

## Current implementation (Phase A + Milestone 007 + Milestone 009)

| Capability | Status |
|------------|--------|
| Project-scoped PDF upload | **Done** (M005) |
| Private filesystem storage | **Done** (M005) |
| Metadata register (`plan_documents`) | **Done** (M005) |
| List / detail / download | **Done** |
| Archive-over-delete | **Done** (M007) |
| Default Drawing Package + active Revision membership | **Done** (M007 minimal) |
| Page indexing (0-based) | **Done** (M007) |
| Deterministic PDF metadata + embedded text | **Done** (M007) |
| ProcessingAttempt / ProcessingResult + raw payload | **Done** (M007) |
| Idempotent reprocessing | **Done** (M007) |
| Append-only plan audit events | **Done** (M007 + M009 `sheet_id`) |
| Project-scoped relational search/filter | **Done** (M007) |
| Sheet classification / human review | **Done** (M009; `plan_sheets`, `plan_sheet_pages`, `plan_sheet_suggestions`, human accept/edit/reject, uniqueness validation) |
| Scale calibration / measurement | **Feature Gate Approved** (M010; [FG-005](../feature-gates/FG-005-m010-scale-calibration.md); ADR-026/027; code not started) |
| OCR / CAD / AI take-off | **Out of scope** until Feature-Gated |

Routes live under `/projects/<id>/plans…`. Estimating, Proposals, OCR, CAD, AI, and supplier features are unchanged.

## Document Intelligence (architecture — Milestone 006; partial code in M007; sheets in M009)

Capability layer **inside** Plan Intelligence ([ADR-013](../adr/ADR-013-document-intelligence-layer-boundary.md)), between Phase A storage and take-off:

| Concept | Status |
|---------|--------|
| Drawing Package / Revision (minimal default) | **Implemented** (M007) |
| Page indexing / deterministic extraction | **Implemented** (M007) |
| Processing provenance + relational search | **Implemented** (M007); ADR-015 / ADR-016 |
| Sheet index / discipline / human review | **Implemented** (M009; ADR-014, ADR-017, ADR-018) |
| OCR / CAD / AI take-off hooks | Documented integration points only |

See [document-intelligence.md](../architecture/document-intelligence.md) and [FG-003](../feature-gates/FG-003-document-intelligence-readiness.md).

## Business goals

1. Reduce manual take-off time while preserving estimator judgment.
2. Make every quantity defensibly traceable to a plan sheet and region.
3. Prevent AI from silently inserting or rewriting estimate lines (Constitution Articles 5–6; Rules 5–6).
4. Create a durable take-off history that survives plan revisions.
5. Feed Estimating without redesigning the estimate builder.

## Supported input types (intended)

| Input | Near-term | Later |
|-------|-----------|-------|
| Searchable PDF | **Phase A + M007** | — |
| Scanned PDF | Stored (flagged non-searchable); OCR later | OCR path |
| Architectural plans | Storage + page index | Take-off POC |
| Structural / civil / other | Later | Expanded vocabulary |

## Non-goals (until separately Feature-Gated)

- Redesigning the estimate builder
- Silent auto-insert of AI quantities into estimates
- CAD-first platform strategy
- Supplier catalogue / live pricing / procurement
- Full OCR optimisation
- Speculative AI pricing

## Owned data

### Current (M005 + M007)

- `PlanDocument` metadata + stored PDF bytes
- Minimal `DrawingPackage` / `DrawingRevision` membership
- `PlanPage` index + extracted text
- `ProcessingAttempt` / `ProcessingResult` (incl. raw payload)
- `PlanAuditEvent`

### Intended (later)

Sheets, disciplines, take-off quantities, reviews, approvals, mapping proposals (not committed estimate lines).

## Referenced data

- `Project` (scope)
- Estimating `Assembly` / `CostItem` / `EstimateVersion` (mapping targets only — future)

## Prohibited responsibilities

- Owning live estimate line items
- Silent estimate mutation
- Supplier catalogue / PO ownership
- Proposal snapshot ownership

## Relevant ADRs

| Need | ADR |
|------|-----|
| Source traceability | [ADR-005](../adr/ADR-005-ai-takeoff-traceability.md) |
| Human approval before estimate insert | [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) |
| Plan vs estimate version ownership | [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md) |
| PDF-first vs CAD-first | [ADR-009](../adr/ADR-009-pdf-first-versus-cad-first.md) |
| AI confidence threshold policy | [ADR-011](../adr/ADR-011-ai-confidence-threshold-policy.md) |
| Build vs buy | [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) |
| Plan document / revision ownership | [ADR-012](../adr/ADR-012-plan-document-version-ownership.md) |
| Document Intelligence layer boundary | [ADR-013](../adr/ADR-013-document-intelligence-layer-boundary.md) |
| Sheet identity vs PDF page mapping | [ADR-014](../adr/ADR-014-sheet-identity-and-page-mapping.md) |
| Extracted metadata ownership / provenance | [ADR-015](../adr/ADR-015-extracted-metadata-ownership-and-provenance.md) |
| Document Intelligence search strategy | [ADR-016](../adr/ADR-016-document-intelligence-search-strategy.md) |

> ADR-008 remains Supplier Price Snapshotting. Sheet-review ADRs (if any) belong to the Sheet Intelligence architecture milestone, not M007 code.
