# Module — Plan Intelligence

| Attribute | Value |
|-----------|--------|
| Status | **Phase A implemented** (PDF upload/storage); Document Intelligence architecture documented (M006); take-off / AI not started |
| Updated | 2026-07-25 |
| Code | `app/plan_intelligence/` (Phase A only) |
| Feature Gates | [FG-002](../feature-gates/FG-002-plan-intelligence-phase-a.md) · [FG-003](../feature-gates/FG-003-document-intelligence-readiness.md) |
| Architecture | [../architecture/plan-intelligence-and-automated-takeoff.md](../architecture/plan-intelligence-and-automated-takeoff.md) · [../architecture/document-intelligence.md](../architecture/document-intelligence.md) |
| Readiness | [../architecture/M004-plan-intelligence-readiness-report.md](../architecture/M004-plan-intelligence-readiness-report.md) · [../architecture/M006-document-intelligence-readiness-report.md](../architecture/M006-document-intelligence-readiness-report.md) |

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

## Current implementation (Phase A — Milestone 005)

| Capability | Status |
|------------|--------|
| Project-scoped PDF upload | **Done** |
| Private filesystem storage (`instance/plan_uploads/` or `PLAN_UPLOAD_ROOT`) | **Done** |
| Metadata register (`plan_documents`) | **Done** |
| List / detail / download / delete | **Done** |
| Searchable text-layer detection (`has_text_layer`) | **Done** |
| Drawing Set / Revision workflow | **Not implemented** (see ADR-012) |
| Sheet classification, scale, take-off, AI, estimate insert | **Out of scope** |

Routes live under `/projects/<id>/plans…`. Estimating, Proposals, OCR, CAD, AI, and supplier features are unchanged.

## Document Intelligence (architecture — Milestone 006)

Capability layer **inside** Plan Intelligence ([ADR-013](../adr/ADR-013-document-intelligence-layer-boundary.md)), between Phase A storage and take-off:

| Concept | Status |
|---------|--------|
| Drawing Package / Revision | Architecture + ADR-012; **not implemented** |
| Sheet index / discipline / sheet numbers | Architecture + ADR-014; **not implemented** |
| Metadata extraction / search index | Architecture only; **not implemented** |
| OCR / CAD / AI take-off hooks | Documented integration points only |

See [document-intelligence.md](../architecture/document-intelligence.md) and [FG-003](../feature-gates/FG-003-document-intelligence-readiness.md) (**PASS**, implementation not authorized).

## Business goals

1. Reduce manual take-off time while preserving estimator judgment.
2. Make every quantity defensibly traceable to a plan sheet and region.
3. Prevent AI from silently inserting or rewriting estimate lines (Constitution Articles 5–6; Rules 5–6).
4. Create a durable take-off history that survives plan revisions.
5. Feed Estimating without redesigning the estimate builder.

## Supported input types (intended)

| Input | Near-term | Later |
|-------|-----------|-------|
| Searchable PDF | **Phase A** | — |
| Scanned PDF | Stored in Phase A (flagged non-searchable); OCR later | OCR path |
| Architectural plans | Phase A storage | Take-off POC |
| Structural drawings | Later | Expanded vocabulary |
| Civil drawings | Later | — |
| Site plans | Later | — |
| Reflected ceiling plans | Later | — |
| Schedules (door, finish, etc.) | Later / optional cross-check | — |
| Specification documents | Parallel later track | Quantity rules may cite specs |

## Future support (not Phase A)

- DWG / DXF
- IFC / BIM models
- Broader multi-trade automated take-off

(PDF-first strategy: [ADR-009](../adr/ADR-009-pdf-first-versus-cad-first.md).)

## Non-goals (until separately Feature-Gated)

- Redesigning the estimate builder
- Silent auto-insert of AI quantities into estimates
- CAD-first platform strategy
- Supplier catalogue / live pricing / procurement (separate pillars)
- Full OCR optimisation
- Replacing Proposals or Project Controls modules
- Speculative AI pricing
- Drawing Set / Revision management UI (documented in [ADR-012](../adr/ADR-012-plan-document-version-ownership.md) only)

## Success metrics (architecture / product)

| Metric | Intent |
|--------|--------|
| Traceability coverage | % of approved quantities with complete source citations |
| Review completion | Approved take-off packages vs abandoned |
| Insertion discipline | Zero silent estimate inserts (tests + audit) |
| Revision safety | Prior take-off versions unchanged after new plan upload |
| POC accuracy | Human-verified door count (or chosen element) within agreed tolerance |

## Risks

| Risk | Mitigation |
|------|------------|
| False AI quantities | Confidence thresholds (ADR-011); mandatory human approval (ADR-006) |
| Wrong scale | Manual scale confirmation before estimate eligibility |
| Scope explosion | Narrow POC; one discipline; one element |
| Ownership confusion | Plan Intelligence owns take-off; Estimating owns estimate lines (ADR-007) |
| Vendor lock-in | Build-vs-buy ADR-010; Estimator-owned citation records |
| Flat uploads mistaken for final model | ADR-012 documents Drawing Set / Revision ownership before that UI exists |

## Owned data

### Phase A (current)

- `PlanDocument` metadata + stored PDF bytes (project-scoped)

### Intended (later)

Drawing sets, revisions, sheets, viewports/scales, detected elements, measurements, quantities, reviews, approvals, confidence scores, corrections, audit history, mapping proposals (not committed estimate lines).

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

> Note: Milestone 004 Task 7 titles mapped onto existing ADR numbers where already assigned; **ADR-011** is confidence policy. **ADR-012** is Milestone 005 documentation for revision ownership (not implemented in Phase A UI). **ADR-013/014** are Milestone 006 Document Intelligence decisions. ADR-008 remains Supplier Price Snapshotting.
