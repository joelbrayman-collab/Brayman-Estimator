# Feature Gate FG-029: BMR / Supplier Workflow V1

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-029` |
| Feature Name | BMR / Supplier Workflow V1 |
| Target Milestone | **None.** FG-029 is the governing identifier. Do **not** assign a new M0xx number. V1 package **V1-03** in [v1-completion-register.md](../v1-completion-register.md). |
| Module | **Supplier Catalogue** (proposed; not implemented) owns supplier/location/product/mapping/package. **Material Catalogue** owns `CanonicalMaterial` and, under [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md), thin `MaterialRequirement`. Plan Intelligence and Estimating **do not** take supplier SKU ownership. |
| Date | 2026-09-09 |
| Status | **RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** This recording is **not** Feature Gate approval for implementation. |
| Architecture | [fg-029-bmr-supplier-workflow-v1-preflight.md](../architecture/fg-029-bmr-supplier-workflow-v1-preflight.md) · [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted** · [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** · [ADR-034](../adr/ADR-034-canonical-material-identity-and-ownership.md) **Accepted** · [ADR-035](../adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) **Accepted** · [ADR-036](../adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted** · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) **Proposed** · [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted** · [supplier-channel-and-launch-partner.md](../architecture/supplier-channel-and-launch-partner.md) · [supplier-catalogue-inventory-pricing.md](../architecture/supplier-catalogue-inventory-pricing.md) · [material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) |
| Related ADRs | **[ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) Accepted.** Do **not** accept ADR-008 or ADR-010 from this gate. |
| Prerequisites | FG-014 **CLOSED / OPERATIONAL FOR UAT**. FG-026 **CLOSED / OPERATIONAL FOR UAT**. FG-027 **CLOSED / OPERATIONAL FOR UAT**. [FG-028](FG-028-calibai-to-calibraytai-product-identity-transition.md) Slice 3 logo hold **does not block** this recording. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **RECORDED.** **NOT APPROVED FOR IMPLEMENTATION.** |
| Architecture preflight | **COMPLETE** |
| Product code / models | **None** |
| Schema / Alembic | **None.** Proposed later revision `b6c7d8e9f0a1` (`down_revision` `a5b6c7d8e9f0`) — **not created**. |
| Live DB / demo seed | **None** |
| ADR-008 | **Proposed** (unchanged) |

```text
FG-029:
RECORDED
ARCHITECTURE PREFLIGHT COMPLETE
NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
ADR-046 ACCEPTED
ADR-008 REMAINS PROPOSED
NO SCHEMA
NO LIVE DB MUTATION
V1 REMAINS 45% / 2 OF 11
FG-028 UNCHANGED (SLICE 3 HELD)
DO NOT IMPLEMENT FROM THIS RECORDING
```

Joel/ChatGPT recorded this gate on **2026-09-09** as durable product/governance authority only. Recording is **not** implementation approval.

---

## Purpose

Authorize (later) the **smallest honest** BMR Winchester demonstration:

```text
CanonicalMaterial (existing FG-014 identity)
→ thin MaterialRequirement (manual / DEMO_SYNTHETIC)
→ human-reviewed supplier mapping
→ labeled DEMO BMR Winchester products / SKUs
→ supplier price + availability EVIDENCE (inform only)
→ frozen Supplier Package
→ HTML + PDF BMR-facing output
```

The first BMR demo does **not** require: live BMR API; live inventory; live contractor pricing; EDI; live PO submission; live delivery scheduling; bulk catalogue onboarding; a supplier marketplace; real lumber take-off from FG-010.

**FG-010 remains interior-door count only.** Do not claim CalibraytAI performs lumber take-off today.

---

## Feature Gate answers

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | Contractor-reviewed material requirements never reach a supplier-facing package. BMR Winchester cannot be shown an honest path without a second dealer take-off. |
| 2 | Who is the user? | ORG-001 office estimator (creates/reviews requirements and mappings). Darcy / BMR Winchester (receives HTML/PDF package). Not a supplier portal login in V1. |
| 3 | Which module owns it? | Supplier Catalogue (supplier/SKU/mapping/package). Material Catalogue (`CanonicalMaterial` + thin `MaterialRequirement`). |
| 4 | What data does it own? | Future additive tables in the preflight (not created now). |
| 5 | What data does it reference? | `canonical_materials`; `organizations`; `projects`; optional `EstimateLineItem` citation. Must **not** own PLAN package items or costing snapshots. |
| 6 | What may it change? | Later implementation only: new tables, Hub PRICE UI, HTML/PDF, labeled DEMO seed. |
| 7 | What must it not change? | Takeoff schema; FG-026 insertions; FG-027 costing; FG-009 pricing apply; CostItem/Assembly; Brand Profile; office chrome; FG-028; V1 percentages; ADR-008 status; live BMR systems. |
| 8 | What are the acceptance criteria? | Later: mapped vs unresolved; DEMO labels; frozen issued package; no PLAN/costing/pricing mutation; no external order. **This recording does not accept implementation.** |
| 9 | What tests are required? | See preflight test plan. **Do not implement tests now.** |
| 10 | What documentation must be updated? | This gate; ADR-046; preflight; V1-03 register **text** (no rescore); current-state; session-handoff; indexes. |
| 11 | Does it require an ADR? | **Yes — ADR-046.** ADR-008 stays Proposed. |
| 12 | Does it require a database migration? | **Yes, later.** Not in this recording. Proposed `b6c7d8e9f0a1` after `a5b6c7d8e9f0`. |

---

## In scope (when later implemented)

- Thin `MaterialRequirement`
- DEMO supplier + Winchester branch + ORG-001 procurement account
- DEMO SupplierProduct / SKU mapped to existing FG-014 identities
- Human mapping (`UNRESOLVED` / `REVIEW_REQUIRED` / `MAPPED`)
- Inform-only price and availability evidence
- Frozen Supplier Package HTML + PDF
- Delivery-stage grouping and pick/load **columns** (not WMS)

## Out of scope

Live BMR API / EDI / inventory feed · live PO submit · supplier-price → `EstimateLineItem` · ADR-008 acceptance · bulk onboarding · marketplace · Darcy channel economics · relationship **B** · housewrap / drywall identity expansion · lumber take-off extractor · fleet/routing/ERP · FG-024 · FG-025 remaining surfaces · LEARN · FG-028 Slice 3 · website

---

## Demo materials (preflight-approved)

Use **existing FG-014** CanonicalMaterial seeds. Do **not** imply FG-010 extracted these quantities. Requirements are `MANUAL` / `DEMO_SYNTHETIC`.

| Include | Code / name |
|---------|-------------|
| Yes | `CAL-LUM-2X6-12` — 2×6 SPF No.2 or better — 12 ft |
| Yes | `CAL-SHT-OSB-7-16-4X8` — 7/16 in OSB — 4×8 |
| Optional | `CAL-LUM-2X4-STUD-9258` (2×4 stud seed) if a stud line is wanted — **there is no 2×6 stud seed** |
| **No** | Housewrap — outside FG-014 identity domain |
| **No** | ½″ drywall — outside FG-014 identity domain |

Do **not** populate the database in this recording.

---

## BMR demo vs Brayman UAT

| Track | V1-03 bar | After this recording |
|-------|-----------|----------------------|
| BMR DEMO V1 | Requirement → DEMO mapping → frozen package → HTML/PDF | **NO** (architecture only) |
| Brayman real-life UAT | Manual/synthetic supplier workflow is enough; live BMR **not** required | Still **NO** (V1-10 / legal / V1-11 remain) |

Register §10.2 still requires a fail-closed or Ontario contract story for **BMR DEMO READY**. V1-03 architecture recording does **not** flip that flag.

---

## Non-goals

ADR-008 acceptance · live ordering · PLAN mutation · costing/pricing mutation · FG-028 close · V1 rescore · implementation from this document
