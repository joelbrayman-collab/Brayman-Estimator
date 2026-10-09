# Module — Estimating

| Attribute | Value |
|-----------|--------|
| Status | **Current** (core implemented) |
| Updated | 2026-10-09 |
| Code | `app/models/cost_item.py`, `assembly.py`, `estimate.py`, `project_work_package.py`, `calculation_estimate_mapping.py`, `estimate_scope_delivery.py`, `subcontractor.py`, `estimate_quickbooks.py`; `app/routes/cost_library.py`, `assemblies.py`, `estimates.py`, `project_scope.py`, `calculation_mapping.py`, `scope_delivery.py`, `estimate_quickbooks.py`; `app/services/estimates.py`, `estimate_builder.py`, `project_work_package.py`, `calculation_estimate_mapping.py`, `calculation_result_contract.py`, `estimate_output.py`, `estimate_scope_delivery.py`, `subcontract_quote.py`, `estimate_quickbooks.py` |
| Feature Gate | [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** (internal breakdown + customer consistency). [FG-026](../feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT** (Estimating-owned insertion/citation). [FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT** (costing approval). [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT** (scope-delivery routing + quote evidence). [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT** (QuickBooks-ready package). |

## 9 Oct 2026 — Customer print is not the priced estimate

`print.pdf` on an estimate version is the desk fact sheet. It does not carry the pricing snapshot. The customer estimate is the Proposal PDF. Checklist step 8 stays open. The V1 register was not rescored.

## 9 Oct 2026 — Synthetic priced customer total

Estimate 41 version 47. Costing snapshot 23 approves direct cost 37.50 for line 137. Pricing snapshot 15 stores customer total 49.86 from the active organization gross-margin policy. The quantity remains 3 ea. The customer print PDF does not contain that total. Checklist step 8 stays open. The V1 register was not rescored.

## 9 Oct 2026 — Synthetic live construction acceptance

Synthetic project 46, estimate 41, version 47. Revision 1 offered three joists. Review 2 confirmed quantity 3 onto line 137. Revision 2 stores five joists and leaves that line at 3. Checklist step 8 stays open. The V1 register was not rescored. This is not real contractor UAT.

## 9 Oct 2026 — Live construction release

The office construction path is deployed at `dccd5cac6f7c8c281a312e252fe3aacb15ad3e6b`, deploy `dep-db4h3dks728c73aohka0`. Hosted revision `t0a1b2c3d4e5`. A blank elevation remains unknown. Checklist step 8 stays open. The V1 register was not rescored. Contractor UAT is not accepted.

## 9 Oct 2026 — Unknown level elevation

`assess_construction_model` accepts a level that has an id, a name, and no elevation. The number is omitted. It is not stored as zero. A non-numeric elevation is still refused. `resolve_dimension_chains` refuses a level-height chain until the elevation is a number. `read_stored_member_quantities` still returns a complete member group. The office page shows the blank elevation as missing and can save it. A later revision can fill the number. Checklist step 8 stays open. The V1 register was not rescored.

## 9 Oct 2026 — Member groups and deck levels

The construction page adds rows instead of stopping at eight members or one level. `app/services/construction_model_entry.py` writes those rows into the existing `members` and `levels` lists. A saved group id is reused on the next revision. Two groups with the same role, size, and length stay two groups on the form. `read_stored_member_quantities` still combines equivalent members for Add from calculation. A level without an elevation is refused, because `assess_construction_model` still requires the number. The elevation unit shown on the page is feet or metres from the measurement system. The level record does not gain a new unit field. A member is not given a level. Checklist step 8 stays open. The V1 register was not rescored.

## 9 Oct 2026 — Contractor construction information

`app/services/construction_model_entry.py` turns the project form into the existing deck model and calls `save_construction_model_revision`. The route is `projects.construction_information` at `/projects/<id>/construction`. The project hub links to it as Enter construction information, or Update construction information when a revision exists. The form asks for drawing status, measurement system, one level, member role, member size, length, length unit, known count, and pier or footing count. A blank length is stored without a length. `assess_construction_model` still has to accept the model. A stored model with geometry or other facts this form does not edit is shown read-only and is not replaced. The page links to the existing Add from calculation route. It does not create an estimate line. Official V1 remains **65% / 4 of 11**. Checklist step 8 stays open.

## 9 Oct 2026 — Project-owned model and office member count

`project_construction_model_revisions` stores one immutable construction model per revision. The current model is the highest `revision_number` for that project. `app/services/project_construction_model.py` checks organization ownership, refuses a model the construction-model assessment will not accept, and stores the submitted content with its sha256. Add from calculation reads the current revision through `app/services/estimate_member_counts.py` and can offer one group that has no missing fact. The offer uses `offer_stored_member_count` and records `construction_model_revision_id` on the intake. The existing confirm route still creates the line. A repeated offer of the same group and revision does not create a second review. A later revision can create a new review and does not change a confirmed line. Dict-only offers stay valid with a null revision link. Migration `t0a1b2c3d4e5` was not applied to the hosted database or the Mac office. Official V1 remains **65% / 4 of 11**. Checklist step 8 stays open.

## 8 Oct 2026 — Stored member count through mapper confirmation

`offer_stored_member_count` reads one group from `read_stored_member_quantities` and stores that count on the existing calculation review. The review creates no estimate line. The existing confirm route calls `confirm_quantity_mapping` and inserts one ordinary line. A repeated confirmation is refused by the existing mapper. A group with a missing stored fact is refused. `add_estimate_line_from_requirement` remains the earlier direct path and is not this confirmation. No migration. Official V1 remains **65% / 4 of 11**. Checklist step 8 stays open pending product review.

## 8 Oct 2026 — Construction intelligence

Quantity is read before the cost path is chosen. A stored length and width become a square-foot area. Pitch is not applied, and openings are not deducted. A catalogue sheet size, or a sheet size stored on the fact, converts that area to an exact sheet count and does not round up. A stored product coverage converts an area to an exact unit count. Without either, the area stays known and the purchasing count stays unresolved. A stored window, door, fixture, device, or equipment count stays a count. A drawing opening is not that count. Plumbing, electrical, and HVAC keep the quote or allowance cost path and still carry those stored facts. Excavation uses the rectangular prism only when length, width, and depth are stored. Labour hours stay open. No migration. Official V1 remains **65% / 4 of 11**.

## 8 Oct 2026 — Governed footing volume

A footing with stored length in feet, width in feet, and thickness in inches uses the same rectangular-prism measurement as a slab. The construction unit stays cubic yards. The purchasing unit stays cubic metres. The material is `CAL-CONC`. A second footing stays its own line. A footing missing a dimension stays unresolved and does not stop a slab, an ICF wall, or a member count. A support location is not a footing size. Mix design stays unresolved. Foundation activities exist and no footing production rate is stored, so hours stay open. No migration. Official V1 remains **65% / 4 of 11**.

## 8 Oct 2026 — Canonical concrete material

`CAL-CONC` is the one supplier-neutral concrete identity. Category `CONCRETE`. Purchasing unit `M3`. It is not a slab, an ICF wall, a footing, a supplier, or a price. A dimensioned slab and an ICF concrete volume both use it. The construction quantity stays cubic yards. The material requirement stores the cubic-metre purchasing quantity. Revision `s9f0a1b2c3d4` inserts that one row after `r8e9f0a1b2c3`. The older catalogue migration does not insert it. Official V1 remains **65% / 4 of 11**.

## 8 Oct 2026 — Next coherent quantity batch

`app/services/estimating_quantity.py` now places stored stringer and tread counts on stairs, and stored baluster and gate counts on decks. Both still use the member-count rule. A stored pier or footing location count stays a location count. Shaft, helix, and length stay unresolved, so that count does not become a material requirement. A concrete slab with stored length, width, and thickness uses `rectangular_prism_cubic_yards`. The construction unit stays cubic yards and the purchasing unit stays cubic metres. No canonical concrete identity is stored, so the slab does not become a material requirement. A stored stair result, including a riser count, stays on the result and is not turned into lumber. A footing with width and depth still has no volume rule. Roofing, windows, and the other named scopes without a stored rule stay unresolved. Plumbing, electrical, and HVAC stay quote or allowance scopes. Labour hours stay open. Official V1 remains **65% / 4 of 11**.

## 8 Oct 2026 — Hosted cubic-metre unit check

Revision `r8e9f0a1b2c3` revises `q7d8e9f0a1b2`. It widens the material-requirement unit check and the canonical-material unit and category checks so `M3` and `CONCRETE` can be stored. `EA`, `LF`, `SF`, and `BF` stay valid. Existing rows are not rewritten. The Mac office file is not a target of this revision. Official V1 remains **65% / 4 of 11**.

## 8 Oct 2026 — Construction unit and purchasing unit

A quantity line keeps the construction measurement. `app/services/unit_conversion.py` converts only a stored pair: cubic feet to cubic yards, and cubic yards to cubic metres. The factor is the exact international yard, 0.9144 metres. The result is not rounded in the conversion. `app/services/purchasing_quantity.py` applies a purchasing basis only when one is stored. Concrete volume purchases in cubic metres. Lumber stays on its construction unit. A sheet area with no sheet size stays unresolved and does not become a sheet count. `MaterialRequirement.quantity` stores the purchasing quantity when that unit is already allowed. The note keeps the construction quantity and the conversion rule. The existing quantity column still stores four decimal places, so 45.3069545472 cubic metres is stored as 45.3070. The supplier request shows 45.307 m³ and keeps 59.259 yd³ in the note. A price is read per cubic metre. No migration was added. The hosted check still allows EA, LF, SF, and BF only, so a live concrete requirement cannot be saved until that check is widened. Official V1 remains **65% / 4 of 11**.

## 8 Oct 2026 — Common estimating quantity contract

`app/services/estimating_quantity.py` is the project quantity result. It calls the deck member-count rule and the existing ICF engine. `app/services/estimating_handoff.py` writes supplier-neutral requirements and the existing job supplier request. Plumbing, electrical, and HVAC are quote or allowance scopes. A scope with no stored rule stays unresolved. Official V1 remains **65% / 4 of 11**.

## 8 Oct 2026 — Foundation vertical slice

`app/services/foundation_quantity.py` reads foundation facts and calls `build_icf_standard_quantities` for an ICF wall. `app/services/foundation_handoff.py` writes a supplier-neutral requirement for the 8-inch standard-form count `CAL-ICF-8-STD` and fills the existing job supplier request. Concrete volume stays in cubic yards and does not become a material requirement. A missing wall area, a footing, and a slab stay open. Official V1 remains **65% / 4 of 11**.

## 8 Oct 2026 — Deck and framing vertical slice

`app/services/deck_framing_quantity.py` reads a construction model and returns member counts. A missing fact stays on that member. `app/services/deck_framing_handoff.py` writes a supplier-neutral `MaterialRequirement` for a known count, fills the existing job supplier request, and places that count on an estimate line. Stock length, waste, purchase quantity, and labour hours are not invented. The labour placeholder uses the existing Structure / Framing task. Official V1 remains **65% / 4 of 11**.

## Purpose

Build and version construction estimates from cost libraries and assemblies, scoped to a project. The Estimator must maintain the **authoritative project/estimate record** from which governed outputs derive ([project-document-package.md](../architecture/project-document-package.md)).

`CostItem` is the **organization costing record**. It is **not** CalibAi material identity. Canonical materials (what the project requires) are defined in [material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) (**Intended**; not implemented).

## Responsibilities

- Cost item library (org costing; Material-category items may later link to a canonical material). **R01 (PKG-T01):** `add_cost_item_line` / `add_assembly_line` reload the destination Estimate's Project and the library row against the acting organization before copying commercial identity.
- Assemblies and assembly items (commercial composition; may remain one rolled-up estimate line)
- Estimates and estimate versions. PKG-S16 denormalized `organization_id` + org-scoped unique `uq_estimates_org_estimate_number`. PKG-F14 **working-tree** `suggest_next_estimate_number()` is organization-scoped; format remains `EST-YYYY-NNNN`; max+1 gap-skip preserved.
- Sections and line items
- Version status / locking for issued-like statuses

## Owned data

- `project_work_packages` ([ADR-055](../adr/ADR-055-project-work-package-ownership.md) **Accepted**; confirmed project scope before an estimate; migration **`k1f2a3b4c5d6` in git only**). Mac primary remains **`h8c9d0e1f2a3`**. Hosted validation remains **`j0e1f2a3b4c5`**.
- `cost_items`
- `assemblies`, `assembly_items`
- `estimates`, `estimate_versions`, `estimate_sections`, `estimate_line_items`
- `takeoff_estimate_insertions`, `takeoff_estimate_insertion_citations` (FG-026; Estimating-owned frozen provenance)
- `calculation_result_intakes`, `calculation_quantity_reviews`, `calculation_mapping_acceptances` (calculation review; Estimating-owned; migration **`j0e1f2a3b4c5` applied on the hosted validation database**). Mac primary remains **`h8c9d0e1f2a3`**. A valid Contract V1 result can be reviewed. A person confirms a compatible Cost Item or Assembly. Labour stays deferred. The calculation file is not changed.
- `estimate_costing_snapshots`, `estimate_costing_snapshot_lines` (FG-027; Estimating-owned; additive `a5b6c7d8e9f0` **applied live**)
- `contractor_cost_approvals` (Estimating-owned historical acceptance of a contractor-confirmed cost; cites `SupplierProductPriceEvidence`; not an estimate line; migration **`p6c7d8e9f0a1` in git only**. Mac primary and hosted database are not migrated by this slice.)
- `estimate_line_items.contractor_cost_approval_id` and `estimate_costing_snapshot_lines.contractor_cost_approval_id` ([ADR-056](../adr/ADR-056-approved-contractor-cost-estimate-costing-snapshot.md) **Accepted**; an existing line freezes an APPROVED contractor cost; migration **`q7d8e9f0a1b2` in git only**). The existing costing review reads that frozen citation. It does not resolve a new supplier price. **COSTING REVIEW — CONTRACTOR COST PROVENANCE IMPLEMENTED / TESTED.** **JOB-SPECIFIC SUPPLIER PRICING REQUEST** is the manual supplier-response workflow and is **NOT IMPLEMENTED**. Calibrayt generates the requirement. The supplier confirms product, price, and availability. Brayman approves cost. The 20–30-item synthetic list is withdrawn. BMR remains the first proving supplier. The architecture stays multi-supplier. **REAL PROJECT → MATERIAL REQUIREMENT SET: MATERIAL REQUIREMENT CAPABILITY GAP.** Linda Bushel is the most mature real project. Its Construction Model read does not store a canonical material, member size, or supplied board length. The J1 take-off was not copied into `MaterialRequirement`. No supplier pricing request was sent. **NO-GUESSING ≠ NO-PROGRESS.** **BEST AVAILABLE MATERIAL REQUIREMENT SET** keeps the known Bushel counts and named materials, flags each unresolved fact, and does not block the other items. The read writes no `MaterialRequirement`. **BUSHEL GOVERNED MEMBER FACT COMPLETION IMPLEMENTED / TESTED.** The 1 Oct tread name "Two 5/4 x 6 boards per tread" is the supplier-neutral canonical identity `CAL-LUM-5-4X6`. It carries no stock length, species, treatment, supplier, SKU, or price. Joist, stringer, post, beam, and decking members still have no material, member size, or supplied length. The 29 Sep nominal sizes stay ungoverned. **KNOWN PROJECT FACT ≠ COMPLETE PURCHASE REQUIREMENT.** **NO-GUESSING ≠ NO-PROGRESS.** No purchase quantity was created. **JOB-SPECIFIC SUPPLIER PRICING REQUEST IMPLEMENTED / TESTED.** The Linda Bushel supplier estimate request uses the approved Brayman cost-request page. The earlier pricing-request PDF was visually rejected. Unresolved facts stay TBD. Official V1 remains **65% / 4 of 11**.
- `estimate_scope_deliveries` ([FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) Slice A; [ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**; 1:1 with `EstimateLineItem`; migration **`c7d8e9f0a1b2` applied live**)
- `subcontractors`, `subcontract_quote_evidence` ([FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) Slice B; Estimating-owned; migration **`d8e9f0a1b2c3` applied live**)
- `estimate_quickbooks_packages`, `estimate_quickbooks_sales_lines`, `estimate_quickbooks_cost_class_lines` ([FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) Slices A+B; Estimating-owned freeze copies; migration **`e9f0a1b2c3d4` applied live** 2026-09-11)
- `estimate_quickbooks_entry_events` ([FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) Slice C; append-only ENTERED/REVERSED/CORRECTED; migration **`f0a1b2c3d4e5` applied live** 2026-09-11)
- `estimate_quickbooks_entry_occupancies` ([FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) Slice C repair; at most one active ENTERED per package; migration **`f1a2b3c4d5e6` applied live** 2026-09-11)

## Referenced data

- `projects` (FK)
- Optionally referenced by proposals and change orders via estimate / estimate_version FKs

## Prohibited responsibilities

- Owning CalibAi canonical material identity / taxonomy ([material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md))
- Final client-facing proposal layout/PDF ownership (Proposals module). [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) requires Proposals customer totals to match this module’s authoritative `EstimateVersion` / pricing snapshot; Estimating still does not own the PDF.
- Project change order lifecycle ownership (Project Controls / Projects)
- Accounting system of record / live QuickBooks API / CSV-IIF import. Estimating **owns** the QuickBooks-**ready** office package ([FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) Slices A+B **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**; [ADR-049](../adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**). It must **not** own QuickBooks, invoices, bills, POs, or payroll.
- Auto-creating `EstimateLineItem` rows from Permit Intelligence findings ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md); [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md)). Permit Intelligence may later **identify** cost implications; human-controlled propose-allowance is **not authorized** this pass.
- Storing scope-delivery routing on PLAN takeoff, `CostItem`, `Assembly`, `CanonicalMaterial`, or `MaterialRequirement` ([ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md))

## Current implementation

- Office Estimate screens use **Estimate version** / **Pricing lock** display labels ([FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) Slice 3). Estimate ≠ Proposal. Internal models unchanged.
- Office QuickBooks-ready entry — **live-migrated / bounded office UAT PASS / operational for UAT** ([FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) Slices A+B). Hub PRICE `/projects/<id>/quickbooks-entry`. Private sales PDF and cost-class PDF. Download does not confirm entry. Canonical UAT project **id 26**.
- Office Scope Delivery Review — **live-migrated / office UAT PASS / operational for UAT** ([FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**). Hub PRICE `/projects/<id>/scope-delivery`. Per-row confirm + Approve All Scope Routing. Does **not** approve costing or apply Pricing. FG-027 Costing Approval requires **CONFIRMED** routing (`PROPOSED` is not costing authority).
- Estimate statuses and version statuses defined in `app/models/estimate.py`
- `AUTO_LOCK_VERSION_STATUSES` locks versions when Issued/Accepted/Rejected/Superseded
- Builder service supports structured line construction
- UI under Estimating nav section
- Internal Detailed Cost Breakdown — **implemented / operational for UAT** ([FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**). Office view at `GET /estimates/<id>/versions/<version_id>/internal-breakdown`. Direct Cost = Σ `extended_cost`. Labour snapshots display-only, labeled not in selling-price basis.
- Governed pricing policy application — **implemented / operational for UAT** ([pricing-policy.md](../pricing-policy.md); [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted**; [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **IMPLEMENTED / VERIFIED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**; versions without a snapshot still use markup/overhead/profit stack)
- Deeper productivity tooling — [FG-008](../feature-gates/FG-008-labour-engine-phase-b.md) Labour Engine Phase B **IMPLEMENTED / VERIFIED / LIVE-MIGRATED** (operational for UAT); Estimating does not own canonical tasks or production standards

## Scope of work

The ordinary path is Project → Plans → **Scope of work**.

Scope of work answers what work this project requires and who is doing it. Each row uses a work-catalog element. Delivery is Our crew or Subcontractor. A plan already on the project may be cited. A person confirms the row. The page does not calculate quantities, create estimate lines, choose an engine, or send a quote.

A later internal package may use a calculation engine, Contract V1, and the existing mapper. A later subcontracted package may use My Subcontractors and an RFQ. Those links are not stored yet. `SUGGESTED` is a legal status so a later suggestion can be confirmed by a person. This slice only writes `CONFIRMED`.

## Add from calculation

The estimate version does not offer Add from calculation. Scope of work is where the contractor names the work. The calculation route remains infrastructure. It can still review a Contract V1 result and confirm a quantity onto a cost item or assembly. A person still confirms before a line is added. Add from calculation now opens ICF wall quantities for the 8-inch form count and concrete. That page does not add a line.

Footing and concrete slab / thickened-edge slab remain separate. They are not offered from this page. A StyroRail / BuildBlock 45-degree corner that has no stored coverage is not calculated.

A test page at `/estimates/<id>/versions/<version_id>/calculations/test-load` can still accept a Contract V1 file. It is labeled as testing and is not linked from the estimate version. It is not the normal way to build an estimate.

## Planned capabilities

- Takeoff-to-estimate insertion + frozen citation provenance — [FG-026](../feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Service: `app/services/takeoff_estimate_mapping.py`. UI: `/projects/<id>/plans/takeoff/packages/<package_id>/map`. Plan Intelligence remains owner of the source package. Package approval does **not** insert lines. Live current = heads **`f4a5b6c7d8e9`**.
- Costing approval + immutable costing snapshot — [FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Legacy NULL `library_unit_cost_reference` on CostItem/Assembly Draft edit freezes pre-edit working `unit_cost` (`72949f99da2b56ec06e95e16e29fa194a6730bbd`). [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. Preflight [fg-027-costing-approval-preflight.md](../architecture/fg-027-costing-approval-preflight.md). Approve All = costing approval only. Pricing Engine consumes; does not own costing.
- Scope delivery / make-buy routing — [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. Two stored dimensions; 1:1 `EstimateScopeDelivery` per `EstimateLineItem`. Thin `Subcontractor` + `SubcontractQuoteEvidence`. Hub PRICE Scope Delivery Review. Canonical Slice B UAT project **id 25**.
- Future Material-category `CostItem` → canonical material link ([FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**); assembly components resolvable to canonical materials later; fulfillment uses **exploded** material quantities even when the commercial line stays rolled-up ([material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md)). Identity V1 does not explode Assemblies.
- QuickBooks-ready output / controlled human-entry (V1-05 Option A) — [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-049](../adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**. V1-05 **COMPLETE**. Live QuickBooks API remains **POST-V1**. Ontario contract/warranty remain **Future**.
- Historical estimating intelligence — **Future**

## Dependencies

- Projects (and thus Clients)
- Consumed by Proposals (snapshot source) and Change Orders (optional version link)

## Invariants

- Estimate belongs to a Project
- Versions are numbered per estimate; prefer supersession over silent overwrite (Rule 5)
- Locked versions are read-only in UI/service rules (verify on change)

## Open decisions

- When estimate header status vs version status diverge—canonical source of truth for “accepted bid”
- MONITOR implementation remains **not started**. Estimated baseline for later MONITOR is the locked `EstimateVersion` plus `EstimatePricingSnapshot` when present ([ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted**). Draft versions must not be the committed baseline.
- How (or whether) to migrate estimate markup/overhead/profit to the governing gross-margin formula ([ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** — dual named methods; [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **IMPLEMENTED / VERIFIED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**; existing versions without snapshots remain `COST_PLUS_MARKUP_STACK` and are not backfilled)

## Relevant tests

- `tests/test_project_work_packages.py`
- `tests/test_estimates.py`
- `tests/test_estimate_builder.py`
- `tests/test_service_tenancy_invariant_r01.py` (R01 library attach)
- `tests/test_assemblies.py`
- `tests/test_estimate_output_consistency.py` (FG-012)

## Relevant ADRs

- [ADR-055](../adr/ADR-055-project-work-package-ownership.md) **Accepted**: Estimating owns confirmed project scope before an estimate exists. Migration `k1f2a3b4c5d6` is not live-migrated.
- [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted**
- [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted**
- [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (MONITOR V1 **CLOSED / OPERATIONAL FOR UAT** under [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md); forecast-final GM / cost-to-complete remain out of V1)
- [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted** (LEARN must not mutate cost library / approved estimates)
- [material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) **Intended** ([ADR-034](../adr/ADR-034-canonical-material-identity-and-ownership.md) / [ADR-035](../adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) / [ADR-036](../adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted**; CostItem is not CalibraytAI identity; living supplier evidence is not the identity row)
- [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**: Estimating does **not** own `MaterialRequirement`; V1-03 supplier price is inform-only and must not write `EstimateLineItem` / FG-027 / FG-009. [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**.
- [ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**: Estimating owns project-specific `EstimateScopeDelivery`. [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**.
- [ADR-049](../adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**: Estimating owns the QuickBooks-ready package; QuickBooks is destination not SoR. [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**. V1-05 **COMPLETE**.
- [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** — Estimating owns internal breakdown; Proposal remains the customer-facing estimate
