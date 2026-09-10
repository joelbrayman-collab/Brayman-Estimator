# Feature Gate FG-031: Scope Delivery / Make-Buy / Procurement Routing V1

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-031` |
| Feature Name | Scope Delivery / Make-Buy / Procurement Routing V1 |
| Target Milestone | **None.** FG-031 is a **supporting V1 gate**. It is **not** a 12th major V1 package. Closure **does not** rescore [v1-completion-register.md](../v1-completion-register.md). Preserve **55% / 3 of 11 COMPLETE**. |
| Module | **Estimating** owns `EstimateScopeDelivery` (Slice A) and thin Subcontractor identity + `SubcontractQuoteEvidence` (Slice B). Supplier Catalogue **filters** Supplier Package eligibility from routing. Material Catalogue continues to own `CanonicalMaterial` and thin `MaterialRequirement`. Labour Engine continues to own opt-in snapshots. PLAN does **not** own routing. |
| Date | 2026-09-10 |
| Status | **CLOSED / OPERATIONAL FOR UAT.** Slice A and Slice B are **IMPLEMENTED / TESTED / COMMITTED / PUSHED / LIVE-MIGRATED / OFFICE UAT PASS / OPERATIONAL FOR UAT.** Product SHA **`5e1082af68e0eb145d9da01c0fa26585f6b8b9d1`**. Slice B UAT close **`8629f0459e51a94ee42cb475a536570cfbc21639`**. [ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. Do **not** rescore V1 (**55% / 3 of 11 COMPLETE**). |
| Architecture | [fg-031-scope-delivery-make-buy-procurement-routing-preflight.md](../architecture/fg-031-scope-delivery-make-buy-procurement-routing-preflight.md) · [ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted** · [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md) **Accepted** · [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** · [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted** · [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted** · [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted** · [FG-027](FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-029](FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-030](FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED** |
| Related ADRs | **[ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) Accepted**. Do **not** accept ADR-008 from this gate. Do **not** reopen FG-027. |
| Prerequisites | FG-027 costing **CLOSED / OPERATIONAL FOR UAT**. FG-029 contractor-office Supplier Package **CLOSED / OPERATIONAL FOR UAT**. This gate does **not** implement FG-030, V1-04, FG-024, LEARN, QuickBooks, contracts, or subcontract RFQ/package. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **CLOSED / OPERATIONAL FOR UAT.** |
| Slice A routing core | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / LIVE-MIGRATED / OFFICE UAT PASS / OPERATIONAL FOR UAT.** |
| Slice B subcontract quote evidence | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / LIVE-MIGRATED / OFFICE UAT PASS / OPERATIONAL FOR UAT.** |
| Schema / Alembic | Slice A **`c7d8e9f0a1b2` applied live**. Slice B **`d8e9f0a1b2c3` applied live**. Live current **`d8e9f0a1b2c3`**. Repository graph head **`d8e9f0a1b2c3`**. One graph head. |
| Product code | Slice A routing plus Slice B `Subcontractor` / `SubcontractQuoteEvidence`, human quote selection, selected-quote freeze onto `EstimateCostingSnapshotLine`, Hub PRICE Scope Delivery Review quote evidence. Quote is evidence, not cost authority. |
| V1 scoring | **Unchanged.** **55% / 3 of 11 COMPLETE.** Not a 12th package. Closure does **not** rescore V1. |
| Subcontract RFQ/package | **MATURATION DURING UAT / NOT REQUIRED FOR FG-031 CLOSURE / NOT IMPLEMENTED / NOT AUTHORIZED** by this close. |

```text
FG-031:
CLOSED / OPERATIONAL FOR UAT
SLICE A OPERATIONAL FOR UAT
SLICE B OPERATIONAL FOR UAT
ADR-048 ACCEPTED
NOT A 12TH MAJOR V1 PACKAGE
DO NOT RESCORE V1 (REMAINS 55% / 3 OF 11)
FG-027 REMAINS FINAL COSTING AUTHORITY
FG-029 SUPPLIER PRICE REMAINS INFORM ONLY
FG-030 UNCHANGED (RECORDED / NOT IMPLEMENTATION-AUTHORIZED)
SUBCONTRACT RFQ/PACKAGE = MATURATION DURING UAT / NOT IMPLEMENTED
DO NOT IMPLEMENT FG-030
DO NOT BEGIN V1-04
DO NOT IMPLEMENT SUBCONTRACT RFQ/PACKAGE FROM THIS CLOSE
```

Architect closure recorded 2026-09-10. Slice A UAT evidence: [fg031-live-migrate-bounded-uat-record.md](../testing/fg031-live-migrate-bounded-uat-record.md). Slice B UAT evidence: [fg031-slice-b-live-migrate-bounded-uat-record.md](../testing/fg031-slice-b-live-migrate-bounded-uat-record.md). HISTORICAL focused **83 passed** / full **728 passed** (not rerun on this documentation close).

---

## Purpose

Make the project commercially honest about **who supplies material** and **who performs labour** before final costing approval, without contaminating PLAN, catalogues, or customer-facing selling-price documents.

FG-031 defines **WHAT** may enter or share a Supplier Package. [FG-030](FG-030-supplier-identity-authentication-and-access-isolation.md) later governs **WHO** may see an issued package. Subcontractor future access is **separate** from `SupplierUserMembership`.

---

## Current implemented state

This is the governing product state after close.

- Two independent stored routing dimensions on Estimating-owned `EstimateScopeDelivery` (1:1 with `EstimateLineItem`). **No stored HYBRID enum.** Hybrid is derived display language.
- Explicit human routing confirmation (per-row Confirm and Approve All Scope Routing). `PROPOSED` is not costing authority.
- Unresolved / unconfirmed routing **BLOCKS** FG-027 Costing Approval (`SCOPE_DELIVERY_UNRESOLVED`), with the existing Allowance exception.
- Supplier Package cited-line filter = confirmed `CONTRACTOR_PURCHASED`. Subcontractor-supplied material does not enter the package.
- Thin organization-scoped `Subcontractor` (distinct from `Supplier`).
- EstimateVersion-scoped `SubcontractQuoteEvidence` with human RECEIVED / SELECTED / REJECTED / SUPERSEDED. No lowest-bid or AI selection.
- Quote evidence does **not** mutate working `EstimateLineItem` cost or apply Pricing.
- Selected quote identity and copied facts freeze onto `EstimateCostingSnapshotLine` at human Costing Approval. Frozen facts do not float.
- Complete subcontract, hybrid (`CONTRACTOR_PURCHASED` + `SUBCONTRACT`), and labour-only subcontract are operational.
- Clone copies routing and quote evidence onto new line IDs; copied quotes return to RECEIVED; human reconfirmation is required.
- Locked / issued EstimateVersion quote mutations fail closed.
- Customer Proposal/PDF remains delivery-blind. Supplier Package does not disclose subcontractor or quote internals.
- Tenant isolation fail-closed. PLAN and catalogue ownership preserved.
- Slice A migration **`c7d8e9f0a1b2`** and Slice B migration **`d8e9f0a1b2c3`** applied live.

Canonical DEMO/SYNTHETIC UAT vessels: Slice A project **id 19**; Slice B project **id 25**.

---

## Feature Gate answers

Original recording answers used future tense because Slice A/B were not yet implemented. The answers below are the **current closed state**. Original design requirements are preserved in the Slice A / Slice B design lists that follow.

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | Without line-level delivery routing, subcontract HVAC (or any subcontract material) can leak into BMR Supplier Packages, hybrid scopes cannot be stated honestly, and FG-027 costing can lock while WHO still performs the work is unresolved. |
| 2 | Who is the user? | Contractor office estimators / cost reviewers on Project Hub PRICE. Not the customer. Not a supplier named-user. Not a subcontractor portal user. |
| 3 | Which module owns it? | Estimating owns routing, thin Subcontractor, and quote evidence. Supplier Catalogue filters packages from routing. Material Catalogue / Labour Engine / PLAN do not own routing. |
| 4 | What data does it own? | `estimate_scope_deliveries` (1:1 with `EstimateLineItem`). Thin org-scoped `subcontractors` + `subcontract_quote_evidence`. Not CanonicalMaterial, not CostItem/Assembly masters, not takeoff items. |
| 5 | What data does it reference? | `organizations`, `projects`, `estimates`, `estimate_versions`, `estimate_line_items`. Selected quote identity frozen onto costing snapshot lines. |
| 6 | What may it change? | `estimate_scope_deliveries`; Hub PRICE Scope Delivery Review; per-row confirm; Approve All Scope Routing; `SCOPE_DELIVERY_UNRESOLVED` BLOCK on FG-027 (Allowance exception); CONTRACTOR_PURCHASED Supplier Package filter; EstimateVersion clone copy with conservative reconfirmation; nullable costing-snapshot freeze columns; `subcontractors`; `subcontract_quote_evidence`. |
| 7 | What must it not change? | PLAN; CostItem/Assembly/CanonicalMaterial schemas; FG-027 source kinds; supplier-price INFORM ONLY; customer estimate privacy; FG-030 status; V1 55% / 3 of 11; branding; FG-024; remaining FG-025; LEARN; QuickBooks; contracts; Native Signing; Observation Delete; FG-030; V1-04; subcontract RFQ/package. |
| 8 | What are the acceptance criteria? | Two stored dimensions; 1:1 EstimateLineItem; no HYBRID enum; human confirmation; Approve All; fail-closed costing BLOCK; Supplier Package filter; thin Subcontractor; human quote selection; quote does not mutate cost/Pricing; selected-quote freeze; complete/hybrid/labour-only cases; clone/reconfirm; locked/issued refusal; customer and supplier privacy; tenant isolation; PLAN/catalogue preservation; dedicated + regression tests PASS; live migrate + office UAT PASS. **Met.** |
| 9 | What tests are required? | Dedicated FG-031 Slice A and Slice B tests plus Estimating / FG-026 / FG-027 / FG-029 / Material / Labour / Pricing / output / clone / Hub PRICE regressions. HISTORICAL at Slice B UAT close: focused **83 passed**; full **728 passed**. Not rerun on this documentation close. |
| 10 | What documentation must be updated? | This gate; current-state; session-handoff; indexes; V1 register **status text only** (do **not** rescore). |
| 11 | Does it require an ADR? | **Yes — ADR-048** (Accepted). |
| 12 | Does it require a database migration? | **Yes.** Slice A **`c7d8e9f0a1b2`** applied live 2026-09-09. Slice B **`d8e9f0a1b2c3`** applied live 2026-09-10. No further migration from this close. |

---

## Two stored dimensions (authoritative)

Do **not** store a HYBRID enum. Hybrid is derived.

**Material procurement:** `CONTRACTOR_PURCHASED` · `SUBCONTRACTOR_SUPPLIED` · `OWNER_SUPPLIED` · `NO_MATERIAL` · `UNRESOLVED`

**Labour delivery:** `INTERNAL` · `SUBCONTRACT` · `OWNER_THIRD_PARTY` · `NO_LABOUR` · `UNRESOLVED`

User-facing summaries (Internal, Subcontract, Material only, Hybrid, Unresolved, Allowance) are **display language**, not stored commercial authority.

`OWNER_SUPPLIED` and `OWNER_THIRD_PARTY` remain valid architecture values. First Slice A UI **may hide** them as reserved/advanced contractor-facing choices. Do **not** remove them from the CHECK lists.

---

## Slice A — Routing core (original authorized design; now implemented)

Objective: make WHO supplies material and WHO performs labour commercially honest before costing approval.

Original authorized design (implemented):

1. `EstimateScopeDelivery` model/table.
2. One routing row per `EstimateLineItem`.
3. `material_procurement`.
4. `labour_delivery`.
5. Status: `DRAFT` · `PROPOSED` · `CONFIRMED`.
6. Suggestion provenance: `RULE` · `ORG_DEFAULT` · `NONE` (nullable).
7. Actor / `confirmed_by` / `confirmed_at`.
8. Project Hub PRICE: **Scope Delivery Review**.
9. Contractor-facing columns: Scope · Material provided by · Labour performed by · Status · Cost evidence · Action.
10. Human per-row confirmation.
11. **Approve All Scope Routing** — explicit human POST; confirms only eligible proposed rows; does **not** confirm unresolved rows; records actor/time; does **not** approve costing; does **not** apply Pricing; does **not** approve supplier mapping.
12. Fail-closed costing: `SCOPE_DELIVERY_UNRESOLVED` **BLOCKS** FG-027 Costing Approval unless required routing is **CONFIRMED**. Resolved `PROPOSED` / `DRAFT` dimensions are **not** commercial authority. Legitimate Allowance (`NO_MATERIAL` + `NO_LABOUR`, or no routing row) remains excepted (WARN, not BLOCK).
13. Supplier Package eligibility: only MaterialRequirements associated with `CONTRACTOR_PURCHASED` routing are automatically eligible. Exclude `SUBCONTRACTOR_SUPPLIED`, `OWNER_SUPPLIED`, `NO_MATERIAL`, `UNRESOLVED`.
14. Uncited MANUAL / DEMO MaterialRequirements must **not** silently enter a Supplier Package; they require explicit contractor-purchased designation/reconciliation first.
15. Preserve FG-029: supplier price INFORM ONLY.
16. No automatic MaterialRequirement creation from routing.
17. No automatic LabourTask / LabourSnapshot creation.
18. No PLAN mutation.

Human review remains explicit in early V1. CalibraytAI may later suggest routing as history grows. Exception-based review is Future. No confidence-based auto-approval. No LEARN. Closure does **not** authorize those later suggestions.

---

## Slice B — Subcontract cost evidence (original authorized design; now implemented)

Original authorized design (implemented):

A. Thin organization-scoped Subcontractor identity (not a marketplace): `id`, `organization_id`, `code`, `legal_name`, `status`, `created_at` / `updated_at`.

B. Estimating-owned `SubcontractQuoteEvidence`, EstimateVersion-scoped. Minimum facts: `organization_id`, `project_id`, `estimate_version_id`, `estimate_line_item_id` or `routing_id`, `subcontractor_id`, `quote_reference`, `amount`, `currency`, `quote_date`, `expires_on`, `included_scope`, `exclusions`, attachment/provenance, actor, `received_at`, `selection_status` (`RECEIVED` · `SELECTED` · `REJECTED` · `SUPERSEDED`).

C. Quote evidence remains evidence. It does **not** silently set selling price.

D. If a selected quote is used in working direct cost, FG-027 still requires human Costing Approval.

E. Approved quote identity/facts required for cost provenance must freeze into the costing snapshot.

F. Hybrid contractor-material + subcontract-labour must work (`CONTRACTOR_PURCHASED` + `SUBCONTRACT`).

G. Complete subcontract: `SUBCONTRACTOR_SUPPLIED` + `SUBCONTRACT`.

H. Labour-only subcontract: `NO_MATERIAL` + `SUBCONTRACT`.

I. Do **not** implement Subcontractor Portal.

J. Do **not** implement multi-bid marketplace.

K. Do **not** implement subcontract EDI/order flow.

Do **not** add costing source kinds `SOURCE_SUPPLIER_PRICE` or `SOURCE_SUBCONTRACT_QUOTE`. Slice B quote evidence remains provenance behind working cost and frozen costing facts.

---

## Interactions (do not reopen closed gates)

| Gate / surface | Interaction |
|----------------|-------------|
| FG-027 | Remains final costing authority. Slice A adds upstream `SCOPE_DELIVERY_UNRESOLVED` BLOCK unless routing is **CONFIRMED** (Allowance exception). `PROPOSED` is not costing authority. Existing source kinds unchanged. |
| Pricing / ADR-044 | Routing does not apply Pricing. If later routing/quote/labour changes working direct cost, FG-027 recost is required and existing Pricing becomes STALE / REQUIRES RE-APPLY. No automatic Pricing. |
| Labour | `INTERNAL` **permits** existing Labour Engine workflow. Routing does **not** auto-create LabourTask, ProductionRateStandard, or LabourSnapshot. `LABOUR_EVIDENCE_ABSENT` remains a warning unless separately governed. Do not silently include labour-snapshot direct cost in selling-price basis. |
| Customer Estimate / V1-04 | Delivery-blind. Do not expose routing enums, internal labour rates, supplier prices/identity (unless later commercially authorized), subcontract quote cost, margin, or markup. Internal Detailed Cost Breakdown may later display internal delivery class. V1-04 remains **NOT STARTED**. |
| Supplier Package | Supplier sees only material routed to that supplier. `CONTRACTOR_PURCHASED` → eligible, subject to human mapping. Do not expose internal labour, subcontract quotes, customer selling price, GM, markup, other suppliers. |
| FG-030 | Remains **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. FG-031 = what may enter a package. FG-030 = who may see the issued package. |
| Subcontract RFQ/package | **MATURATION DURING UAT.** **Not required** for FG-031 closure. **Not required** for BMR Demo Ready. **Not implemented.** **Not authorized** by this close. Portal is POST-V1. |
| BUILD / MONITOR | No implementation in this gate. Later map INTERNAL labour → planned labour; CONTRACTOR_PURCHASED → planned material; SUBCONTRACT / SUBCONTRACTOR_SUPPLIED → planned subcontract. Actuals remain independent. Do not double-count hybrid selling price. Consume **frozen** approved routing, not floating Draft. |
| QuickBooks / V1-05 | Dependency only. Future output needs planned cost-class split (material/vendor, subcontract, internal labour). No QuickBooks in this close. |

---

## V1 boundary

**Required before BMR Demo Ready (this gate’s portion):** two-dimension routing; human Scope Delivery Review; contractor-purchased Supplier Package filtering; no subcontract material leakage to BMR; INFORM ONLY supplier pricing; no RFQ requirement. **Met.** Independent remaining BMR Demo Ready blocker: Ontario/fail-closed contract story.

**Required before Brayman real-life UAT (this gate’s portion):** unresolved routing BLOCK; Approve All Scope Routing; thin Subcontractor party; selected quote evidence / costing freeze; hybrid contractor-material + sub-labour; org isolation; customer estimate delivery-blind. **Met.** Brayman Real-Life UAT Ready remains **NO** for independent reasons outside this gate.

**Maturation during UAT (not this close):** org routing defaults; subcontract RFQ/package HTML/PDF; owner-supplied/third-party UX; historical suggestions; exception-based review. Closure does **not** authorize these.

**POST-V1:** LEARN/ML; component-level Assembly routing; subcontractor portal; supplier price → estimate cost; live BMR / PO; vendor marketplace; BUILD execution-plan expansion; MONITOR routing-vs-actual reconciliation.

If one Assembly requires component-level mixed delivery in V1, split it into separate commercial `EstimateLineItem` rows.

---

## Non-goals

Subcontract RFQ/package HTML/PDF · subcontractor portal/login · FG-030 · V1-04 · FG-024 · remaining FG-025 · LEARN · QuickBooks · contracts · Native Signing · Observation Delete · website · live BMR · PO · marketplace · collapsing Subcontractor into Supplier · storing routing on PLAN/catalogues · HYBRID enum · silent ML auto-approval · automatic quote → cost

---

## Current vs intended vs future

| Layer | State |
|-------|--------|
| **Current** | **CLOSED / OPERATIONAL FOR UAT.** Slice A routing and Slice B subcontract quote evidence are live-migrated and office-UAT verified. Canonical Slice A UAT project **id 19**. Canonical Slice B UAT project **id 25**. Live current **`d8e9f0a1b2c3`**. |
| **Intended (remaining this gate)** | **None.** Gate closed. Subcontract RFQ/package is **maturation during UAT**, not a remaining FG-031 product condition. |
| **Future** | Org defaults; exception-based review; RFQ/package HTML/PDF; owner UX; subcontractor portal; LEARN; component Assembly routing; supplier price → estimate cost; live BMR / PO; marketplace; BUILD/MONITOR execution-plan expansion. **Not authorized by this close.** |
