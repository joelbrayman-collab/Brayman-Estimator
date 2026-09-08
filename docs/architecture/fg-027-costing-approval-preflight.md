# FG-027 Automated Costing and Human Cost Approval V1 — Architecture preflight

| Attribute | Value |
|-----------|--------|
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED** (2026-09-08). **NOT LIVE-MIGRATED.** **UAT NOT RUN / NOT AUTHORIZED.** **NOT CLOSED.** **NOT OPERATIONAL FOR UAT.** [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. Live Alembic remains **`f4a5b6c7d8e9`**. Repository graph head **`a5b6c7d8e9f0`**. |
| Date | 2026-09-08 |
| Parent | FG-026 close SHA `bacb5abf574b3dfe30bda4b6d6015026a3946607`. Architecture recording SHA `076e12f022fa5248a34e7baf7d05ae51e9e0ac4b`. Implementation start pin `28fb5c0445fafabb2924d5d43bce46bf5fca3d0e`. |
| Gate | [FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) |
| Readiness | Product implementation complete in repository. Live migrate / office UAT **not authorized**. |

```text
FG-027:
IMPLEMENTED / TESTED / COMMITTED / PUSHED
NOT LIVE-MIGRATED
UAT NOT RUN / NOT AUTHORIZED
NOT CLOSED
NOT OPERATIONAL FOR UAT
ADR-044 ACCEPTED
MIGRATION FILE a5b6c7d8e9f0
DOWN_REVISION f4a5b6c7d8e9
LIVE CURRENT f4a5b6c7d8e9
```

This document pins implementation mechanics. Historical “do not create now” language below is the 2026-09-08 architecture recording. Product code, migration file `a5b6c7d8e9f0`, and tests **were implemented** under the authorized 8 Sep 2026 FG-027 package. Live `flask db upgrade` and office UAT remain **NOT AUTHORIZED**.

---

## Inspected existing boundaries (2026-09-08)

| Check | Result |
|-------|--------|
| A. Working line cost | **Exists.** `EstimateLineItem.unit_cost` / `extended_cost`. Draft edit on `version_detail.html` + `update_line_item`. |
| B. CostItem / Assembly insert copy | **Exists.** `add_cost_item_line_uncommitted` / `add_assembly_line_uncommitted` copy library `unit_cost` at insert. Later library edits do not rewrite lines. |
| C. Assembly rollup | Live `Assembly.base_unit_cost` = Σ component qty × current `CostItem.unit_cost` × (1+waste). Empty assembly → 0. |
| D. Direct cost for Pricing | `version_line_direct_cost` = Σ `extended_cost`. `apply_resolved_pricing_to_version(..., include_labour_snapshot_direct_cost=False)`. |
| E. Apply Pricing UI | `POST /estimates/<id>/versions/<version_id>/apply-org-pricing` on `version_detail.html`. **No costing-approval gate today.** |
| F. `EstimatePricingSnapshot` | Unique per version. **Draft-mutable** (updates in place). Locked versions cannot mutate. |
| G. `EstimateLabourSnapshot` | Immutable (`before_update` / `before_delete` raise). No office pin route. Out of pricing basis by default. |
| H. Costing snapshot | **Does not exist.** |
| I. MaterialRequirement | **Does not exist.** Out of V1-02. |
| J. Supplier price snapshot | **Does not exist.** ADR-008 Proposed. Out of V1-02. |
| K. FG-026 UAT line 7 | Assembly id 2, qty 3 `ea`, `unit_cost` 0 because assembly has 0 components. Do not mutate in this preflight. |

---

## 1. Proposed durable structure (do not create now)

JSON alone is **not** sufficient for financially significant line reconstruction. Prefer relational header + child rows. JSON may hold advisory warning/exception lists at approval.

### 1.1 `EstimateCostingSnapshot` — Estimating-owned

Recommended later path: `app/models/estimate_costing.py`. Import from `app/models/__init__.py`. Table `estimate_costing_snapshots`.

Follow **labour-snapshot immutability**, not Draft-mutable pricing-snapshot mutation: `before_update` / `before_delete` always raise. Recost inserts a **new** row and points the prior row’s `superseded_by_id` at it.

| Exact name | Type | Null | Notes |
|------------|------|------|--------|
| `id` | Integer PK | no | Durable identity |
| `organization_id` | `String(50)` | no | FK `organizations.id` **ON DELETE RESTRICT**; indexed |
| `project_id` | Integer | no | FK `projects.id` **ON DELETE RESTRICT**; indexed |
| `estimate_id` | Integer | no | FK `estimates.id` **ON DELETE RESTRICT** |
| `estimate_version_id` | Integer | no | FK `estimate_versions.id` **ON DELETE RESTRICT**; indexed |
| `status` | `String(20)` | no | `'CURRENT'` or `'SUPERSEDED'` CHECK |
| `superseded_by_id` | Integer | yes | Self-FK `estimate_costing_snapshots.id` **ON DELETE RESTRICT** |
| `approved_direct_cost_total` | Numeric(14, 2) | no | Frozen Σ included `extended_cost` |
| `line_count` | Integer | no | Included lines at approval |
| `warning_codes` | JSON | yes | Advisory list at approval (not financial SoR) |
| `block_codes` | JSON | yes | Must be empty `[]` or null on a successful CURRENT snapshot |
| `actor_user_id` | Integer | yes | FK `users.id` **ON DELETE SET NULL** |
| `actor_display_name` | `String(150)` | no | Durable actor snapshot |
| `approved_at` | DateTime | no | Approval timestamp |
| `provenance` | Text | yes | Short reconstructable summary |
| `created_at` | DateTime | no | Insert timestamp (equals approval) |

**Application-enforced:** at most one `status='CURRENT'` row per `estimate_version_id`. SQLite cannot express a filtered unique easily; enforce in the service the same way other CURRENT-on-save patterns do.

Do **not** DELETE snapshots. Do **not** UPDATE financial columns. Supersession only sets `status` / `superseded_by_id` on the **prior** row inside the same transaction **before** immutability listeners are attached, **or** set those columns only via a dedicated supersede helper that runs before the listener is registered — implementation must match labour-standard supersession (new row first, then point prior `superseded_by_id`). Because labour snapshots themselves never update, costing snapshots should: create new CURRENT row; then a **narrow allowed update** of the prior row’s `status` + `superseded_by_id` only. Document that exception explicitly in implementation. Alternative: store CURRENT solely as `superseded_by_id IS NULL` and never update other columns; a one-column pointer update is the only mutation. **Recommend:** allow update **only** of `status` and `superseded_by_id` on the superseded predecessor; all other columns immutable.

### 1.2 `EstimateCostingSnapshotLine` — Estimating-owned frozen facts

Table `estimate_costing_snapshot_lines`.

| Exact name | Type | Null | Notes |
|------------|------|------|--------|
| `id` | Integer PK | no | |
| `costing_snapshot_id` | Integer | no | FK parent **ON DELETE RESTRICT**; indexed |
| `estimate_line_item_id` | Integer | no | FK `estimate_line_items.id` **ON DELETE RESTRICT**; identity at approval |
| `line_type` | `String(50)` | no | Frozen `Cost Item` / `Assembly` / `Custom` / `Allowance` |
| `source_kind` | `String(40)` | no | See §3 |
| `quantity` | Numeric(12, 4) | no | Frozen |
| `unit` | `String(50)` | no | Frozen |
| `unit_cost` | Numeric(14, 4) | no | Frozen working/approved unit cost |
| `waste_percent` | Numeric(8, 2) | no | Frozen |
| `extended_cost` | Numeric(14, 2) | no | Frozen |
| `cost_item_id` | Integer | yes | FK `cost_items.id` **ON DELETE RESTRICT**; identity only |
| `assembly_id` | Integer | yes | FK `assemblies.id` **ON DELETE RESTRICT**; identity only |
| `library_unit_cost_reference` | Numeric(14, 4) | yes | Library/rollup reference at insert or last governed copy |
| `is_manual_override` | Boolean | no | default False |
| `override_reason` | Text | yes | Required when `is_manual_override` |
| `warning_codes` | JSON | yes | Per-line warnings at approval |
| `sort_order` | Integer | no | Frozen display order |
| `created_at` | DateTime | no | |

**UNIQUE** `(costing_snapshot_id, estimate_line_item_id)`.

After approval, reconstruction of the approved direct-cost basis must be possible from these rows even if CostItem/Assembly library later changes, or if Draft working lines are later edited.

### 1.3 Working-line override provenance on `estimate_line_items`

Existing Draft line edit remains the working-cost editor. Costing Review collects/requires override reason before Approve All. Persist pending reason on the working line so a refresh does not lose it.

Additive nullable columns (later migration):

| Exact name | Type | Null | Notes |
|------------|------|------|--------|
| `costing_source_kind` | `String(40)` | yes | Working classification |
| `library_unit_cost_reference` | Numeric(14, 4) | yes | Copied at CostItem/Assembly insert; not updated by library edits |
| `costing_override_reason` | Text | yes | Required before approval when library-derived `unit_cost` ≠ reference |
| `costing_override_by` | `String(150)` | yes | Actor snapshot |
| `costing_override_at` | DateTime | yes | |

Do **not** write these onto CostItem/Assembly library rows.

### 1.4 Pricing consume reference on `estimate_pricing_snapshots`

Additive nullable column:

| Exact name | Type | Null | Notes |
|------------|------|------|--------|
| `costing_snapshot_id` | Integer | yes | FK `estimate_costing_snapshots.id` **ON DELETE RESTRICT**; indexed |

Existing unique `(estimate_version_id)` on pricing snapshots **stays**. FG-009 still updates the pricing snapshot in place on Draft. V1-02 does not change that mutation model. Staleness is derived:

```text
PRICING IS CURRENT
  iff a CURRENT costing snapshot exists
  and EstimatePricingSnapshot.costing_snapshot_id == that CURRENT snapshot id

PRICING IS STALE / REQUIRES RE-APPLY
  iff a pricing snapshot exists
  and (no CURRENT costing snapshot
       or costing_snapshot_id is null
       or costing_snapshot_id != CURRENT costing snapshot id)

GOVERNED APPLY PRICING FAILS CLOSED
  iff no CURRENT costing snapshot exists
```

Do not duplicate named methods, tax, or GM. Do not add a redundant `pricing_basis_stale` boolean unless UI cannot join; prefer derived state.

Historical pricing snapshots created before FG-027 will have `costing_snapshot_id` NULL. After go-live they are STALE until costing is approved and Pricing is re-applied. Do not backfill.

---

## 2. Proposed later migration

| Field | Value |
|-------|--------|
| Revision id | `a5b6c7d8e9f0` |
| down_revision | `f4a5b6c7d8e9` (current repository / live head) |
| Upgrade | Additive tables + columns + indexes + FKs as §1 |
| Downgrade | Drop new FKs/indexes/columns/tables. Do not drop `estimate_line_items` or `estimate_pricing_snapshots`. |
| Seed | **None.** Do not invent costing snapshots for existing versions. |
| This pass | **Do not create the revision file.** |

Indexes: `organization_id`, `estimate_version_id`, `status` on snapshots; `costing_snapshot_id` on lines; `costing_snapshot_id` on pricing snapshots.

---

## 3. Source classification (V1 operating)

| Kind | When |
|------|------|
| `LIBRARY_COST_ITEM` | `line_type` Cost Item; unit_cost matches `library_unit_cost_reference` |
| `LIBRARY_ASSEMBLY` | `line_type` Assembly; unit_cost matches `library_unit_cost_reference` |
| `MANUAL_CUSTOM` | `line_type` Custom |
| `MANUAL_ALLOWANCE` | `line_type` Allowance |
| `MANUAL_OVERRIDE` | Cost Item or Assembly whose working `unit_cost` ≠ `library_unit_cost_reference` |

**Reserved extension points (not V1-02 operating sources):** `SUPPLIER_SNAPSHOT`, `HISTORICAL_SUGGESTION`, `AI_SUGGESTION`. Do not write these as operating sources in V1-02.

---

## 4. Exception evaluation (service, later)

Evaluate against **working** Draft lines immediately before Approve All.

| Code | Class | Condition |
|------|-------|-----------|
| `MISSING_COST_ITEM_COST` | BLOCK | Cost Item line `unit_cost` is 0/null |
| `MISSING_ASSEMBLY_COST` | BLOCK | Assembly line `unit_cost` is 0/null (includes empty-rollup copy, e.g. UAT line 7) |
| `MISSING_EXTENDED_COST_FACTS` | BLOCK | quantity/unit/unit_cost/waste cannot produce `extended_cost` |
| `VERSION_NOT_EDITABLE` | BLOCK | not Draft, locked, or `AUTO_LOCK_VERSION_STATUSES` |
| `OVERRIDE_REASON_REQUIRED` | BLOCK | library-derived cost changed and reason empty |
| `INCOMPLETE_DIRECT_COST_TOTAL` | BLOCK | any included line cannot contribute a complete total |
| `MANUAL_CUSTOM` | WARN | Custom with valid cost |
| `MANUAL_ALLOWANCE` | WARN | Allowance with valid cost |
| `UNIT_MISMATCH_CONFIRMED` | WARN | FG-026 confirmed unit ≠ package suggested unit |
| `NO_SUPPLIER_EVIDENCE` | WARN | always available today; never BLOCK in V1-02 |
| `CANONICAL_MATERIAL_UNRESOLVED` | WARN | Material CostItem without `canonical_material_id` |
| `HISTORICAL_ONLY` | WARN | if a later suggestion path exists; not an operating source now |
| `LABOUR_EVIDENCE_ABSENT` | WARN | no labour snapshot; labour not in basis |
| `INACTIVE_LIBRARY_RETAINED` | WARN | working copy retained while library target is inactive |
| `INACTIVE_LIBRARY_REFRESH` | BLOCK | attempted refresh from inactive CostItem/Assembly |

Inactive library: **fail-closed refresh**; preserve copied Draft values with WARN until human decision.

---

## 5. Recost / supersession / lock

```text
Editable Draft + costing-relevant working-line change
  → CURRENT costing snapshot becomes SUPERSEDED (or is treated as stale until reapproval)
  → Pricing snapshot, if present, is STALE
  → user must Approve All Costing again (new snapshot on SAME version)
  → user must Apply Pricing again before pricing is current

Locked / Issued / AUTO_LOCK_VERSION_STATUSES
  → no recost
  → no new costing snapshot
  → working lines remain read-only per existing ensure_version_editable
```

Costing-relevant fields: quantity, unit, unit_cost, waste_percent, line add/remove, source kind, override reason that changes approved cost. Markup/sell_price edits are **pricing-adjacent**; V1-02 treats quantity/unit/unit_cost/waste/line membership as costing-relevant. Do not invent markup-as-costing.

A new EstimateVersion is **not** required solely because costing was re-approved.

---

## 6. Pricing integration contract

Reuse `apply_resolved_pricing_to_version` in `app/services/pricing_engine.py`.

Minimum later change (not now):

1. Resolve CURRENT costing snapshot for the version.
2. If none → `PricingEngineError` fail closed (governed Apply Pricing prevented).
3. Use **frozen** `approved_direct_cost_total` as `direct_cost_basis` (not a live re-sum that could drift from the snapshot). Optionally still re-sum working lines and **fail closed** if they differ from the frozen total (detects silent working-line edit after approval).
4. Persist `costing_snapshot_id` on the pricing snapshot.
5. Keep `include_labour_snapshot_direct_cost=False`.
6. Do not change named methods, tax, GM, or contingency ownership.

UI: Costing Review **above** Apply org pricing on `version_detail.html`. Show STALE when pricing snapshot does not match CURRENT costing.

---

## 7. UI (PRICE / EstimateVersion)

Do **not** add a top-level nav module or lifecycle stage.

Reuse:

- `app/templates/estimates/version_detail.html`
- `app/routes/estimates.py` version detail + `update_line_item` + `apply-org-pricing`
- `app/services/estimate_builder.py` calculations
- Cost Items / Assemblies library screens remain library maintenance, not costing approval

Preferred structure:

```text
Estimate Version
→ Costing Review section (#costing-review)
→ exceptions / warnings
→ edit working costs (existing line editor)
→ override reason fields
→ Approve All Costing
→ Apply org pricing policy (existing; later fail-closed / stale)
```

Later routes (same estimate version; not a new module):

- `POST /estimates/<id>/versions/<version_id>/approve-all-costing`
- Existing apply-org-pricing remains; add fail-closed + stale banner

FG-026 map UI is **not** the costing home.

---

## 8. FG-026 line 7 (do not mutate)

EstimateLineItem id 7 / Assembly id 2 / qty 3 `ea` / `unit_cost` 0.

V1-02 must **BLOCK** Approve All until a human enters a cost (or the Assembly gains components **and** the estimator sets a new working cost / override). Mapping provenance stays. Do not invent a door price. Do not change the UAT row in this preflight.

---

## 9. What this preflight does not authorize

Product code; Alembic file `a5b6c7d8e9f0`; live DB writes; UAT data mutation; LEARN; ADR-008; MaterialRequirement; labour-in-basis change; office labour snapshot pin; CostItem auto-update from history.

---

## Related

- [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md)
- [FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md)
- [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md)
- [FG-026](../feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md)
