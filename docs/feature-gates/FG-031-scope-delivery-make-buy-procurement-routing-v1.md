# Feature Gate FG-031: Scope Delivery / Make-Buy / Procurement Routing V1

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-031` |
| Feature Name | Scope Delivery / Make-Buy / Procurement Routing V1 |
| Target Milestone | **None.** FG-031 is a **supporting V1 gate**. It is **not** a 12th major V1 package. Recording or later implementation **does not** rescore [v1-completion-register.md](../v1-completion-register.md). Preserve **55% / 3 of 11 COMPLETE**. |
| Module | **Estimating** owns `EstimateScopeDelivery` (Slice A) and later thin Subcontractor identity + `SubcontractQuoteEvidence` (Slice B). Supplier Catalogue **filters** Supplier Package eligibility from routing. Material Catalogue continues to own `CanonicalMaterial` and thin `MaterialRequirement`. Labour Engine continues to own opt-in snapshots. PLAN does **not** own routing. |
| Date | 2026-09-09 |
| Status | **FUTURE / RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** [ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted** (architecture only). |
| Architecture | [fg-031-scope-delivery-make-buy-procurement-routing-preflight.md](../architecture/fg-031-scope-delivery-make-buy-procurement-routing-preflight.md) · [ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted** · [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md) **Accepted** · [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** · [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted** · [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted** · [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted** · [FG-027](FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-029](FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-030](FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED** |
| Related ADRs | **[ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) Accepted** (architecture). Do **not** accept ADR-008 from this gate. Do **not** reopen FG-027. |
| Prerequisites | FG-027 costing **CLOSED / OPERATIONAL FOR UAT**. FG-029 contractor-office Supplier Package **CLOSED / OPERATIONAL FOR UAT**. This gate does **not** implement FG-030, V1-04, FG-024, LEARN, QuickBooks, or contracts. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **RECORDED.** **ARCHITECTURE PREFLIGHT COMPLETE.** **NOT APPROVED FOR IMPLEMENTATION.** |
| Slice A routing core | **NOT AUTHORIZED** |
| Slice B subcontract quote evidence | **NOT AUTHORIZED** |
| Schema / Alembic | **None.** Later Slice A needs one additive migration after `b6c7d8e9f0a1`. Do **not** create a revision from this recording. |
| Product code | **None.** |
| V1 scoring | **Unchanged.** **55% / 3 of 11 COMPLETE.** Not a 12th package. |

```text
FG-031:
RECORDED
ARCHITECTURE PREFLIGHT COMPLETE
NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
ADR-048 ACCEPTED (ARCHITECTURE ONLY)
NO SCHEMA
NO LIVE DB MUTATION
NOT A 12TH MAJOR V1 PACKAGE
DO NOT RESCORE V1 (REMAINS 55% / 3 OF 11)
FG-027 UNCHANGED (FINAL COSTING AUTHORITY)
FG-029 UNCHANGED (SUPPLIER PRICE INFORM ONLY)
FG-030 UNCHANGED (RECORDED / NOT IMPLEMENTATION-AUTHORIZED)
DO NOT IMPLEMENT FROM THIS GATE
DO NOT BEGIN V1-04 FROM THIS GATE
```

Joel directed this architecture on **2026-09-09**. Recording is **not** implementation approval.

---

## Purpose

Make the project commercially honest about **who supplies material** and **who performs labour** before final costing approval, without contaminating PLAN, catalogues, or customer-facing selling-price documents.

FG-031 defines **WHAT** may enter or share a Supplier Package. [FG-030](FG-030-supplier-identity-authentication-and-access-isolation.md) later governs **WHO** may see an issued package. Subcontractor future access is **separate** from `SupplierUserMembership`.

---

## Feature Gate answers

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | Without line-level delivery routing, subcontract HVAC (or any subcontract material) can leak into BMR Supplier Packages, hybrid scopes cannot be stated honestly, and FG-027 costing can lock while WHO still performs the work is unresolved. |
| 2 | Who is the user? | Contractor office estimators / cost reviewers on Project Hub PRICE. Not the customer. Not a supplier named-user. Not a subcontractor portal user. |
| 3 | Which module owns it? | Estimating owns routing (and later Slice B Subcontractor + quote evidence). Supplier Catalogue filters packages. Material Catalogue / Labour Engine / PLAN do not own routing. |
| 4 | What data does it own? | Future Slice A: `estimate_scope_deliveries` (1:1 with `EstimateLineItem`). Future Slice B: thin org-scoped Subcontractor + `SubcontractQuoteEvidence`. Not CanonicalMaterial, not CostItem/Assembly masters, not takeoff items. |
| 5 | What data does it reference? | `organizations`, `projects`, `estimates`, `estimate_versions`, `estimate_line_items`. Later: selected quote identity frozen onto costing snapshot lines. |
| 6 | What may it change? | This recording changes **docs/governance only**. Later Slice A may add routing table, Hub PRICE Scope Delivery Review, per-row confirm, Approve All Scope Routing, `SCOPE_DELIVERY_UNRESOLVED` BLOCK on FG-027 (Allowance exception), and CONTRACTOR_PURCHASED Supplier Package filter. |
| 7 | What must it not change? | Product code now; live DB; PLAN; CostItem/Assembly/CanonicalMaterial schemas; FG-027 source kinds; supplier-price INFORM ONLY; customer estimate privacy; FG-030 status; V1 55% / 3 of 11; branding; FG-024; remaining FG-025; LEARN; QuickBooks; contracts; Native Signing; Observation Delete. |
| 8 | What are the acceptance criteria? | Architecture recorded; two stored dimensions; 1:1 EstimateLineItem; no HYBRID enum; human confirmation; Approve All design authorized for Slice A; fail-closed costing BLOCK specified; Supplier Package filter specified. Later implementation (separate prompt): tests in the preflight PASS. |
| 9 | What tests are required? | None in this recording. Later tests are listed in the preflight § Test plan. |
| 10 | What documentation must be updated? | ADR-048; this gate; preflight; current-state; session-handoff; indexes; V1 register **status text only** (do **not** rescore). |
| 11 | Does it require an ADR? | **Yes — ADR-048.** |
| 12 | Does it require a database migration? | **Not in this recording.** Later Slice A implementation requires one additive migration after live head `b6c7d8e9f0a1` (not created here). |

---

## Two stored dimensions (authoritative)

Do **not** store a HYBRID enum. Hybrid is derived.

**Material procurement:** `CONTRACTOR_PURCHASED` · `SUBCONTRACTOR_SUPPLIED` · `OWNER_SUPPLIED` · `NO_MATERIAL` · `UNRESOLVED`

**Labour delivery:** `INTERNAL` · `SUBCONTRACT` · `OWNER_THIRD_PARTY` · `NO_LABOUR` · `UNRESOLVED`

User-facing summaries (Internal, Subcontract, Material only, Hybrid, Unresolved, Allowance) are **display language**, not stored commercial authority.

`OWNER_SUPPLIED` and `OWNER_THIRD_PARTY` remain valid architecture values. First Slice A UI **may hide** them as reserved/advanced contractor-facing choices. Do **not** remove them from the CHECK lists.

---

## Slice A — Routing core (later implementation; not authorized now)

Objective: make WHO supplies material and WHO performs labour commercially honest before costing approval.

Later implement:

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
12. Fail-closed costing: once Slice A is live, `SCOPE_DELIVERY_UNRESOLVED` **BLOCKS** FG-027 Costing Approval except legitimate Allowance (`NO_MATERIAL` + `NO_LABOUR` on an Allowance line remains WARN, not BLOCK).
13. Supplier Package eligibility: only MaterialRequirements associated with `CONTRACTOR_PURCHASED` routing are automatically eligible. Exclude `SUBCONTRACTOR_SUPPLIED`, `OWNER_SUPPLIED`, `NO_MATERIAL`, `UNRESOLVED`.
14. Uncited MANUAL / DEMO MaterialRequirements must **not** silently enter a Supplier Package; they require explicit contractor-purchased designation/reconciliation first.
15. Preserve FG-029: supplier price INFORM ONLY.
16. No automatic MaterialRequirement creation from routing.
17. No automatic LabourTask / LabourSnapshot creation.
18. No PLAN mutation.

Human review remains explicit in early V1. CalibraytAI may later suggest routing as history grows. Exception-based review is Future. No confidence-based auto-approval. No LEARN.

---

## Slice B — Subcontract cost evidence (later; required before Brayman real-life UAT unless a later architecture proves a smaller safe boundary)

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

Do **not** add costing source kinds `SOURCE_SUPPLIER_PRICE` or `SOURCE_SUBCONTRACT_QUOTE` in Slice A. Slice B quote evidence remains provenance behind working cost and frozen costing facts.

---

## Interactions (do not reopen closed gates)

| Gate / surface | Interaction |
|----------------|-------------|
| FG-027 | Remains final costing authority. Later Slice A adds upstream `SCOPE_DELIVERY_UNRESOLVED` BLOCK (Allowance exception). Existing source kinds unchanged in Slice A. |
| Pricing / ADR-044 | Routing does not apply Pricing. If later routing/quote/labour changes working direct cost, FG-027 recost is required and existing Pricing becomes STALE / REQUIRES RE-APPLY. No automatic Pricing. |
| Labour | `INTERNAL` **permits** existing Labour Engine workflow. Routing does **not** auto-create LabourTask, ProductionRateStandard, or LabourSnapshot. `LABOUR_EVIDENCE_ABSENT` remains a warning unless separately governed. Do not silently include labour-snapshot direct cost in selling-price basis. |
| Customer Estimate / V1-04 | Delivery-blind. Do not expose routing enums, internal labour rates, supplier prices/identity (unless later commercially authorized), subcontract quote cost, margin, or markup. Internal Detailed Cost Breakdown may later display internal delivery class. |
| Supplier Package | Supplier sees only material routed to that supplier. `CONTRACTOR_PURCHASED` → eligible, subject to human mapping. Do not expose internal labour, subcontract quotes, customer selling price, GM, markup, other suppliers. |
| FG-030 | Remains **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. FG-031 = what may enter a package. FG-030 = who may see the issued package. |
| Subcontract RFQ/package | **Not required** for BMR Demo Ready. Strong candidate before/during Brayman real-life UAT. Not in Slice A. Portal is POST-V1. |
| BUILD / MONITOR | No implementation in initial slices. Later map INTERNAL labour → planned labour; CONTRACTOR_PURCHASED → planned material; SUBCONTRACT / SUBCONTRACTOR_SUPPLIED → planned subcontract. Actuals remain independent. Do not double-count hybrid selling price. Consume **frozen** approved routing, not floating Draft. |
| QuickBooks / V1-05 | Dependency only. Future output needs planned cost-class split (material/vendor, subcontract, internal labour). No QuickBooks in this recording. |

---

## V1 boundary

**Required before BMR Demo Ready:** two-dimension routing; human Scope Delivery Review; contractor-purchased Supplier Package filtering; no subcontract material leakage to BMR; INFORM ONLY supplier pricing; no RFQ requirement.

**Required before Brayman real-life UAT:** unresolved routing BLOCK; Approve All Scope Routing; thin Subcontractor party; selected quote evidence / costing freeze; hybrid contractor-material + sub-labour; org isolation; customer estimate delivery-blind.

**Maturation during UAT:** org routing defaults; subcontract RFQ/package HTML/PDF; owner-supplied/third-party UX; historical suggestions; exception-based review.

**POST-V1:** LEARN/ML; component-level Assembly routing; subcontractor portal; supplier price → estimate cost; live BMR / PO; vendor marketplace; BUILD execution-plan expansion; MONITOR routing-vs-actual reconciliation.

If one Assembly requires component-level mixed delivery in V1, split it into separate commercial `EstimateLineItem` rows.

---

## Non-goals

Product implementation from this recording · FG-030 · V1-04 · FG-024 · remaining FG-025 · LEARN · QuickBooks · contracts · Native Signing · Observation Delete · website · live BMR · PO · marketplace · collapsing Subcontractor into Supplier · storing routing on PLAN/catalogues · HYBRID enum · silent ML auto-approval

---

## Current vs intended vs future

| Layer | State |
|-------|--------|
| **Current** | No `EstimateScopeDelivery`. FG-027 costing exists. FG-029 packages all project MaterialRequirements for a supplier/location. Customer Proposal is selling-price-oriented. |
| **Intended (this gate, not implemented)** | Two-dimension EstimateVersion-scoped routing; human Scope Delivery Review; Approve All Scope Routing; unresolved BLOCK on costing; CONTRACTOR_PURCHASED package filter; Slice B quote evidence before real-life UAT. |
| **Future** | Org defaults; exception-based review; RFQ/package; owner UX; portal; LEARN; component Assembly routing. |
