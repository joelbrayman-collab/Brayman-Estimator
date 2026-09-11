# FG-031 Scope Delivery / Make-Buy / Procurement Routing — Architecture preflight

| Attribute | Value |
|-----------|--------|
| Status | **COMPLETE (architecture recording).** [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT.** Slice A and Slice B **LIVE-MIGRATED / OFFICE UAT PASS / OPERATIONAL FOR UAT.** |
| Date | 2026-09-09 |
| Gate | [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| ADR | [ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted** (architecture only) |
| Alembic | Live current **`d8e9f0a1b2c3`**. Repository head **`d8e9f0a1b2c3`**. One graph head. Slice A **applied live**. Slice B **`d8e9f0a1b2c3` applied live**. |
| Product | CalibraytAI (formerly CalibAi) |
| Source | Completed SCOPE DELIVERY / MAKE-BUY / PROCUREMENT ROUTING architecture reconciliation + preflight (2026-09-09). This document records that recon; it does **not** redo architecture from scratch. |

```text
FG-031 PREFLIGHT (ORIGINAL ARCHITECTURE RECORDING, 2026-09-09):
COMPLETE
ADR-048 ACCEPTED (ARCHITECTURE ONLY)
NOT IMPLEMENTATION-AUTHORIZED AT RECORDING TIME
V1 REMAINS 55% / 3 OF 11
NOT A 12TH MAJOR PACKAGE

SUBSEQUENT PRODUCT STATE (2026-09-10):
FG-031 CLOSED / OPERATIONAL FOR UAT
SLICE A AND SLICE B LIVE-MIGRATED / OFFICE UAT PASS
RFQ/PACKAGE REMAINS MATURATION / NOT IMPLEMENTED
```

The original pin was **not** an implementation authorization. Subsequent Slice A/B implementation and UAT were separately authorized. This documentation close does **not** authorize RFQ/package, FG-030, or V1-04.

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current** | Estimating-owned `EstimateScopeDelivery` 1:1 with `EstimateLineItem` (Slice A; migration **`c7d8e9f0a1b2` applied live**). Two stored dimensions; Hub PRICE Scope Delivery Review; Approve All Scope Routing; `SCOPE_DELIVERY_UNRESOLVED` BLOCK on editable Draft costing unless routing is **CONFIRMED** (`PROPOSED` is not costing authority; Allowance exception); Supplier Package includes cited requirements only when confirmed `CONTRACTOR_PURCHASED`. Uncited MANUAL/DEMO fail-closed. PLAN remains quantity/evidence. Slice B `Subcontractor` + `SubcontractQuoteEvidence` **live** (migration **`d8e9f0a1b2c3` applied live**). Bounded Slice A and Slice B office UAT **PASS**. Canonical Slice A UAT project **id 19**. Canonical Slice B UAT project **id 25**. Gate **CLOSED / OPERATIONAL FOR UAT**. No subcontract RFQ. No subcontractor portal. |
| **Intended (remaining this gate)** | **None.** Gate closed. Subcontract RFQ/package is maturation during UAT, not a remaining FG-031 product condition. |
| **Future** | Org routing defaults; exception-based review; subcontract RFQ/package HTML/PDF; owner-supplied/third-party UX; LEARN; component-level Assembly routing; subcontractor portal; supplier price → estimate cost; BUILD/MONITOR execution-plan expansion. **Not authorized by FG-031 close.** |

Do **not** treat this close as authorization for RFQ/package, FG-030, V1-04, or Post-V1 maturation.

---

## 2. Ownership (do not store routing on these)

PLAN remains quantity/evidence authority. PLAN does **not** own who performs work, who provides material, subcontractor/supplier identity, delivery routing, margin, or selling price.

**Do not store routing on:** `TakeoffCandidate`, `TakeoffPackage`, `TakeoffPackageItem`, `CostItem`, `Assembly`, `AssemblyItem`, `CanonicalMaterial`, `MaterialRequirement`.

Assemblies and CostItems remain reusable / project-neutral. If one Assembly requires component-level mixed delivery in V1, **split** into separate commercial `EstimateLineItem` rows. Component-level Assembly routing is **POST-V1**.

One `EstimateSection` may contain mixed routing.

Routing is EstimateVersion-scoped. Clone/version operations must copy routing onto cloned commercial lines. Working routing is mutable only on an editable Draft. Issued/locked versions cannot change routing. Historical snapshots remain immutable.

---

## 3. Two independent stored dimensions

### Material procurement

| Value | Meaning |
|-------|---------|
| `CONTRACTOR_PURCHASED` | Contractor buys the material (normally Supplier Package eligible) |
| `SUBCONTRACTOR_SUPPLIED` | Subcontractor supplies the material |
| `OWNER_SUPPLIED` | Owner supplies the material (architecture value; Slice A UI may hide) |
| `NO_MATERIAL` | Line has no material |
| `UNRESOLVED` | Not yet confirmed |

### Labour delivery

| Value | Meaning |
|-------|---------|
| `INTERNAL` | Contractor labour (permits existing Labour Engine; does not auto-create snapshots) |
| `SUBCONTRACT` | Subcontractor performs labour |
| `OWNER_THIRD_PARTY` | Owner's third party performs labour (architecture value; Slice A UI may hide) |
| `NO_LABOUR` | Line has no labour |
| `UNRESOLVED` | Not yet confirmed |

**Do not store HYBRID.** Hybrid is derived (example: `CONTRACTOR_PURCHASED` + `SUBCONTRACT`).

Display-only summaries: Internal · Subcontract · Material only · Hybrid · Unresolved · Allowance.

Human confirmation is required. Deterministic suggestions (`RULE`, `ORG_DEFAULT`, `NONE`) are permitted. No ML/confidence value may silently authorize routing. Future org defaults may suggest but must never rewrite historical project decisions.

---

## 4. Slice A proposed schema (do not create)

Table: `estimate_scope_deliveries`. Estimating-owned. All FKs **ON DELETE RESTRICT**. Do not mutate takeoff, CostItem, Assembly, CanonicalMaterial, or MaterialRequirement schemas in FG-031 Slice A.

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `organization_id` | Integer FK `organizations` | no | Indexed |
| `project_id` | Integer FK `projects` | no | Indexed |
| `estimate_id` | Integer FK `estimates` | no | |
| `estimate_version_id` | Integer FK `estimate_versions` | no | Indexed |
| `estimate_line_item_id` | Integer FK `estimate_line_items` | no | **UNIQUE** |
| `material_procurement` | String | no | CHECK: `CONTRACTOR_PURCHASED` \| `SUBCONTRACTOR_SUPPLIED` \| `OWNER_SUPPLIED` \| `NO_MATERIAL` \| `UNRESOLVED` |
| `labour_delivery` | String | no | CHECK: `INTERNAL` \| `SUBCONTRACT` \| `OWNER_THIRD_PARTY` \| `NO_LABOUR` \| `UNRESOLVED` |
| `status` | String | no | CHECK: `DRAFT` \| `PROPOSED` \| `CONFIRMED` |
| `suggestion_source` | String | yes | CHECK when present: `RULE` \| `ORG_DEFAULT` \| `NONE` |
| `confirmed_by` | Integer / actor id | yes | Required when `status = CONFIRMED` |
| `confirmed_at` | DateTime | yes | Required when `status = CONFIRMED` |
| `actor_display_name` | String | no | Last mutating actor display |
| `created_at` | DateTime | no | |
| `updated_at` | DateTime | no | |

### Tenant / project / version consistency (service-enforced)

The routing row's `organization_id`, `project_id`, `estimate_id`, and `estimate_version_id` **must equal** the commercial line's chain:

`estimate_line_items` → `estimate_sections` → `estimate_versions` → `estimates` → `projects` → `organizations`.

Fail closed on mismatch. Cross-org queries fail closed. One routing row per line (UNIQUE on `estimate_line_item_id`).

Do **not** create this table from this recording.

---

## 5. Snapshot / immutability

Working `EstimateScopeDelivery` is mutable **only** on an editable Draft `EstimateVersion`.

At FG-027 Costing Approval, copy `material_procurement` and `labour_delivery` onto `EstimateCostingSnapshotLine`. Do **not** create a second routing snapshot table for Slice A.

Slice B may also freeze selected quote evidence identity/facts onto the same costing snapshot line.

Issued/locked EstimateVersions cannot change routing.

Version cloning must copy routing against cloned `EstimateLineItem` rows (same commercial identity in the new version).

BUILD/MONITOR must eventually consume **frozen approved** routing, not floating Draft routing.

---

## 6. Slice A UI / Approve All (design; not implemented)

Project Hub PRICE: **Scope Delivery Review**.

Contractor-facing columns: Scope · Material provided by · Labour performed by · Status · Cost evidence · Action.

Human per-row confirmation.

**Approve All Scope Routing** is **AUTHORIZED DESIGN** for Slice A:

- explicit human POST
- confirms only eligible `PROPOSED` rows
- does **not** confirm `UNRESOLVED` rows
- records actor/time
- does **not** approve costing
- does **not** apply Pricing
- does **not** approve supplier mapping

No confidence-based auto-approval. No LEARN.

`OWNER_SUPPLIED` / `OWNER_THIRD_PARTY` remain in architecture CHECKs. First Slice A UI **may hide** them as reserved/advanced.

---

## 7. FG-027 interaction

Do **not** reopen FG-027.

Once Slice A is live: `SCOPE_DELIVERY_UNRESOLVED` **BLOCKS** Costing Approval unless required routing is **CONFIRMED**. Resolved `PROPOSED` / `DRAFT` dimensions are **not** commercial authority.

**Allowance exception:** an Allowance commercial line with no routing row, or with `NO_MATERIAL` + `NO_LABOUR`, remains WARN, not BLOCK. CONFIRMED Allowance routing is also valid.

Do **not** add `SOURCE_SUPPLIER_PRICE` or `SOURCE_SUBCONTRACT_QUOTE` in Slice A.

FG-027 remains final human costing authority.

---

## 8. Pricing interaction

Routing changes do **not** apply Pricing.

If later routing / quote / labour decisions change working direct cost: FG-027 recost is required. Existing Pricing becomes **STALE / REQUIRES RE-APPLY** under [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md). No automatic Pricing.

---

## 9. Labour interaction

`INTERNAL` labour routing **may permit** existing Labour Engine workflow.

It does **not** automatically create `LabourTask`, `ProductionRateStandard`, or `LabourSnapshot`.

Existing `LABOUR_EVIDENCE_ABSENT` remains a warning unless separately governed.

Do **not** silently include labour-snapshot direct cost in selling-price basis (`include_labour_snapshot_direct_cost=False` remains the default).

---

## 10. Supplier Package filter

Only MaterialRequirements associated with routing `CONTRACTOR_PURCHASED` may automatically be Supplier Package eligible, subject to human supplier mapping.

Exclude:

- `SUBCONTRACTOR_SUPPLIED`
- `OWNER_SUPPLIED`
- `NO_MATERIAL`
- `UNRESOLVED`

Uncited MANUAL / DEMO MaterialRequirements must **not** silently enter a Supplier Package. They require explicit contractor-purchased designation/reconciliation under this architecture first.

Supplier price remains INFORM ONLY (ADR-046 / FG-029). Routing does **not** create MaterialRequirements.

FG-031 = **what** may enter a package. [FG-030](../feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) later = **who** may see the issued package (still **not** implementation-authorized).

Supplier must not see: internal labour, subcontract quotes, customer selling price, GM, markup, other suppliers, other supplier prices/availability.

---

## 11. Slice B proposed facts (do not create)

Thin org-scoped Subcontractor (not a marketplace): `id`, `organization_id`, `code`, `legal_name`, `status`, `created_at` / `updated_at`.

Do **not** collapse Subcontractor into `Supplier`.

`SubcontractQuoteEvidence` (Estimating-owned, EstimateVersion-scoped): `organization_id`, `project_id`, `estimate_version_id`, `estimate_line_item_id` or `routing_id`, `subcontractor_id`, `quote_reference`, `amount`, `currency`, `quote_date`, `expires_on`, `included_scope`, `exclusions`, attachment/provenance, actor, `received_at`, `selection_status` (`RECEIVED` · `SELECTED` · `REJECTED` · `SUPERSEDED`).

Quote evidence does not silently set selling price. Selected quote used in working direct cost still requires FG-027 Costing Approval. Freeze selected quote identity/facts into the costing snapshot.

Must work:

- Hybrid: `CONTRACTOR_PURCHASED` + `SUBCONTRACT`
- Complete subcontract: `SUBCONTRACTOR_SUPPLIED` + `SUBCONTRACT`
- Labour-only subcontract: `NO_MATERIAL` + `SUBCONTRACT`

Out of FG-031: Subcontractor Portal, multi-bid marketplace, subcontract EDI/order flow.

Subcontract RFQ/package is **not** required for BMR Demo Ready. Strong candidate before/during Brayman real-life UAT. Not Slice A. HTML/PDF may mature during UAT. Portal is POST-V1.

---

## 12. Customer Estimate / V1-04 / QuickBooks

Customer-facing estimate remains scope-oriented and selling-price-oriented. Do **not** expose routing enums, internal labour rates, supplier pricing, supplier identity unless separately commercially relevant, subcontract quote cost, margin, or markup.

This decision applies to later V1-04 output work. Do **not** begin V1-04 from this recording.

Internal Detailed Cost Breakdown may eventually display internal delivery class.

QuickBooks / V1-05 later consumes planned cost-class split (material/vendor, subcontract, internal labour). Routing provides planned classification. No QuickBooks implementation here.

**Subsequent status (2026-09-10, not authorized by FG-031):** Joel selected V1-05 **Option A**. [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Planned class is consumed from **frozen costing-snapshot routing**, not live Scope Delivery. Amounts remain FG-027 costing authority. Hybrid lines must not double-count. Live QuickBooks API remains POST-V1. This subsequent note does **not** change FG-031 closed product meaning.

**Subsequent status (2026-09-11):** FG-032 Slices A+B are **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / OVERALL NOT CLOSED**. Product SHA **`70e571140e12377aa5bd009b598530576401113b`**. Product parent **`010f6d641a756ceb2ab67475a284d3b8426c7b20`**. [ADR-049](../adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**. Slice C remains **NOT AUTHORIZED**. This subsequent note does **not** change FG-031 closed product meaning.

Contract output remains customer-scope-oriented.

---

## 13. BUILD / MONITOR

No implementation in FG-031 initial slices unless separately authorized.

Later mapping:

- `INTERNAL` labour → planned labour
- `CONTRACTOR_PURCHASED` → planned material
- `SUBCONTRACT` and/or `SUBCONTRACTOR_SUPPLIED` → planned subcontract

Actuals remain independent: labour, material, subcontract, other_direct. Do not double-count hybrid selling price.

---

## 14. Test plan (later implementation; not run now)

Record later tests covering:

- two independent routing dimensions
- internal labour
- contractor-purchased material
- complete subcontract
- contractor-material + subcontract-labour hybrid
- contractor-material + internal-labour hybrid
- subcontractor-material + subcontract-labour
- no-material + subcontract-labour
- no PLAN mutation
- no CostItem / Assembly contamination
- no CanonicalMaterial contamination
- EstimateVersion isolation
- clone-copy routing
- human per-row confirmation
- Approve All eligible rows
- Approve All skips unresolved
- unresolved blocks FG-027 approval
- Allowance exception
- Supplier Package filters by `CONTRACTOR_PURCHASED`
- uncited/manual requirement fail-closed inclusion
- customer estimate privacy
- supplier privacy
- subcontract quote privacy
- no supplier-price cost mutation
- FG-027 remains final authority
- Pricing no-auto-apply
- Pricing STALE after recost
- tenant isolation
- transaction rollback
- historical routing preservation

Product tests are **NOT RERUN** for this recording.

---

## 15. V1 scoring

Supporting architecture. **Not** a 12th major package. Do **not** rescore from this recording.

Preserve: **55%** · **3 / 11 COMPLETE**.

V1-04 remains the current scored package and is **NOT STARTED**.

---

## 16. Stop conditions

Architecture recording is complete. Slice A product is implemented separately.

Do **not** live-migrate FG-031 from this pin.

Do **not** implement Slice B.

Do **not** implement FG-030.

Do **not** begin V1-04.

Do **not** mutate the live database.

**Subsequent status (2026-09-09 Slice A live migrate + office UAT — not authorized by this architecture pin):** [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) Slice A **LIVE-MIGRATED / OFFICE UAT PASS / OPERATIONAL FOR UAT**. Overall **NOT CLOSED**. Evidence: [fg031-live-migrate-bounded-uat-record.md](../testing/fg031-live-migrate-bounded-uat-record.md). Live current after Slice A = **`c7d8e9f0a1b2`**.

**Subsequent status (2026-09-10 Slice B product implementation — not authorized by this architecture pin):** Slice A remains **OPERATIONAL FOR UAT**. Slice B **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED**. Product SHA **`5e1082af68e0eb145d9da01c0fa26585f6b8b9d1`**. Overall **NOT CLOSED**. Live current remains **`c7d8e9f0a1b2`**. Repository head **`d8e9f0a1b2c3`**.

**Subsequent status (2026-09-10 Slice B live migrate + bounded office UAT):** Slice B **LIVE-MIGRATED / OFFICE UAT PASS / OPERATIONAL FOR UAT**. Canonical project **id 25**. Live current **`d8e9f0a1b2c3`**. Overall remained **NOT CLOSED** pending Architect confirmation. Evidence: [fg031-slice-b-live-migrate-bounded-uat-record.md](../testing/fg031-slice-b-live-migrate-bounded-uat-record.md).

**Subsequent status (2026-09-10 documentation-only final governance close):** [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Slice A and Slice B **OPERATIONAL FOR UAT**. Subcontract RFQ/package remains **maturation during UAT / not implemented**. This close does **not** authorize RFQ/package, FG-030, or V1-04.
