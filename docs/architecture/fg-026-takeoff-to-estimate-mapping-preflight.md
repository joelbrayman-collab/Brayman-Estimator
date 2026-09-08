# FG-026 Takeoff-to-Estimate Mapping V1 — Architecture preflight

| Attribute | Value |
|-----------|--------|
| Status | **PREFLIGHT COMPLETE** (2026-09-08). Subsequent implementation (same date): product **IMPLEMENTED / TESTED / COMMITTED / PUSHED**. Live migrate / UAT **NOT AUTHORIZED / NOT RUN**. [FG-026](../feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **NOT CLOSED**. |
| Date | 2026-09-08 |
| Parent | Review Turnover `1c20100a3838828cdeebece51ed820bcf15063fb` |
| Gate | [FG-026](../feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) |
| Readiness | **B. READY WITH EXPLICIT NON-BLOCKING NOTES** — implementation still requires a separate authorized prompt; commercial-template catalog for doors is empty in live UAT (fail-closed, not a schema blocker). |

```text
FG-026:
RECORDED
ARCHITECTURE PREFLIGHT COMPLETE
IMPLEMENTED / TESTED / COMMITTED / PUSHED (2026-09-08)
NOT LIVE-MIGRATED
UAT NOT RUN
NOT CLOSED
```

This document pins later implementation mechanics. It does **not** amend accepted ADRs. It does **not** authorize implementation.

---

## Inspected existing boundaries (2026-09-08)

| Check | Result |
|-------|--------|
| A. Approved take-off package | **Exists.** `TakeoffPackage` / `TakeoffPackageItem` in `app/plan_intelligence/models.py`. Approve in `app/plan_intelligence/takeoff.py` `approve_package`; immutable via `assert_package_immutable`. Office: `/projects/<id>/plans/takeoff/packages/<package_id>`. |
| B. Package commercial FKs | **None.** Items store quantity, citation, `element_type` only (ADR-035). |
| C. Estimate builder insert | **Exists.** `app/services/estimate_builder.py` `add_cost_item_line` / `add_assembly_line` / `add_manual_line`. Each **commits internally** after flush + `recalculate_version`. |
| D. Editability | `ensure_version_editable` (`app/services/estimates.py`) rejects `is_locked` only. FG-026 V1 additionally requires `status == "Draft"` and not `AUTO_LOCK_VERSION_STATUSES`. |
| E. EstimateLineItem take-off FK | **None.** Fields: section, line_type, cost_item_id, assembly_id, quantity, unit, unit_cost, waste_percent, markup_percent, extended_cost, sell_price. |
| F. Mapping / insertion table | **Does not exist.** |
| G. MaterialRequirement | **Does not exist.** Out of V1. |
| H. Live UAT | Package **1** on project **3**, `INTERIOR_DOOR_OPENING`, approved total **3.0 count**, 3 items. Project 3 has **no** estimate. One Assembly (`FG014-UAT-ASM` framing UAT). Zero labour snapshots. |

---

## 1. Proposed minimal record shape (do not create now)

### 1.1 `TakeoffEstimateInsertion` — Estimating-owned

Recommended later path: `app/models/takeoff_estimate_insertion.py`. Import from `app/models/__init__.py`. Table `takeoff_estimate_insertions`.

| Exact name | Type | Null | Notes |
|------------|------|------|--------|
| `id` | Integer PK | no | Durable identity |
| `organization_id` | `String(50)` | no | FK `organizations.id` **ON DELETE RESTRICT**; indexed |
| `project_id` | Integer | no | FK `projects.id` **ON DELETE RESTRICT**; indexed |
| `estimate_id` | Integer | no | FK `estimates.id` **ON DELETE RESTRICT** |
| `estimate_version_id` | Integer | no | FK `estimate_versions.id` **ON DELETE RESTRICT**; indexed |
| `estimate_section_id` | Integer | no | FK `estimate_sections.id` **ON DELETE RESTRICT** |
| `estimate_line_item_id` | Integer | no | FK `estimate_line_items.id` **ON DELETE RESTRICT**; **UNIQUE** (one insertion → one line) |
| `takeoff_package_id` | Integer | no | FK `takeoff_packages.id` **ON DELETE RESTRICT** (reference; Plan Intelligence still owns the package) |
| `element_type` | `String(80)` | no | Frozen copy of package `element_type` at insert |
| `target_kind` | `String(20)` | no | `'assembly'` or `'cost_item'` CHECK |
| `target_assembly_id` | Integer | yes | FK `assemblies.id` **ON DELETE RESTRICT**; required iff `target_kind='assembly'` |
| `target_cost_item_id` | Integer | yes | FK `cost_items.id` **ON DELETE RESTRICT**; required iff `target_kind='cost_item'` |
| `suggested_quantity` | Numeric(12, 4) | no | Approved package quantity at insert time |
| `suggested_unit` | `String(50)` | no | Package `approved_unit` at insert time |
| `confirmed_quantity` | Numeric(12, 4) | no | User-confirmed estimate-line quantity |
| `confirmed_unit` | `String(50)` | no | User-confirmed estimate-line unit |
| `user_id` | Integer | yes | FK `users.id` **ON DELETE SET NULL** |
| `actor_display_name` | `String(150)` | no | Durable actor snapshot |
| `client_insertion_key` | `String(36)` | no | UUID from the insert POST; **UNIQUE** (idempotent retry) |
| `created_at` | DateTime | no | Insert timestamp |
| `provenance` | JSON | yes | Optional extras; citations live on child rows |

**Do not add** `takeoff_package_id` as the sole provenance on `EstimateLineItem`. A single package FK on the line cannot represent multiple frozen item citations.

**V1 duplicate prevention UNIQUE:**

`(organization_id, takeoff_package_id, element_type, estimate_version_id)`

Accidental double-submit of the same grouping into the same Draft fails closed. Mapping the same package into a **different** Draft version is allowed. A later gate may authorize a second line on the same version; V1 must not.

### 1.2 `TakeoffEstimateInsertionCitation` — Estimating-owned

Table `takeoff_estimate_insertion_citations`. Frozen **copy** of Plan Intelligence item fields at insert time (ADR-005). Not a live pointer.

| Exact name | Type | Null | Notes |
|------------|------|------|--------|
| `id` | Integer PK | no | |
| `insertion_id` | Integer | no | FK parent **ON DELETE RESTRICT**; indexed |
| `takeoff_package_item_id` | Integer | no | Source id at insert; **not** relied on as live SoR |
| `takeoff_candidate_id` | Integer | no | Frozen |
| `takeoff_run_id` | Integer | no | Frozen |
| `plan_document_id` | Integer | no | Frozen |
| `drawing_revision_id` | Integer | no | Frozen |
| `plan_page_id` | Integer | no | Frozen |
| `plan_sheet_id` | Integer | yes | Frozen |
| `page_index` | Integer | no | Frozen |
| `sheet_number` | `String(100)` | yes | Frozen |
| `sheet_name` | `String(255)` | yes | Frozen |
| `review_status` | `String(40)` | no | Frozen |
| `reviewed_quantity` | Float / Numeric | no | Frozen |
| `geometry_data` | JSON | no | Frozen ADR-027 geometry |
| `source_evidence` | Text | yes | Frozen |
| `confidence_numeric` | Float | yes | Frozen advisory |
| `confidence_band` | `String(20)` | yes | Frozen advisory |
| `reviewed_by` | `String(150)` | yes | Frozen |
| `created_at` | DateTime | no | |

**UNIQUE** `(insertion_id, takeoff_package_item_id)`.

After insert, reconstruction must be possible from Estimating rows **even if** a later PLAN rerun occurs. Do not UPDATE these rows. Do not DELETE. Package supersession must not mutate them.

---

## 2. Cardinality

```text
TakeoffPackage (1)
  └── TakeoffPackageItem (many)          PLAN, unchanged
        ╲
         ╲  frozen copy at insert
          ╲
TakeoffEstimateInsertion (many over time; V1 unique per package+element+version)
  ├── EstimateLineItem (1)               Estimating
  └── TakeoffEstimateInsertionCitation (many; ≥1)
```

| Relation | Cardinality | Pin |
|----------|-------------|-----|
| Package → items | 1:N | Existing |
| Package → insertions | 1:N | Same package may map into different Draft versions |
| Insertion → version | N:1 | Same Draft may receive other packages later |
| Insertion → line | 1:1 | UNIQUE `estimate_line_item_id` |
| Insertion → citations | 1:N | Example: 3 door items → 1 Assembly line → 3 citation rows |
| Line → package | none direct | Navigate via insertion |

V1 grouping: all frozen items on the selected APPROVED package (already one `element_type`). Do not require one line per item.

---

## 3. Transaction boundary

**One SQLAlchemy transaction** for:

1. fail-closed validation
2. create `EstimateLineItem` using existing builder **calculations** and catalog copies
3. `recalculate_version` (existing)
4. persist `TakeoffEstimateInsertion`
5. persist citation snapshots
6. **single** `commit`

**Reuse:** `calculate_extended_cost` / `apply_line_item_calculations` / catalog field copies from `add_assembly_line` and `add_cost_item_line` (quantity, unit, unit_cost, `waste_percent=0`, `markup_percent` from the **existing template default**). Mapping UI must **not** collect GM, markup, tax, overhead, profit, contingency, or waste overrides.

**Do not call** `add_assembly_line` / `add_cost_item_line` as they exist today: they `db.session.commit()` before provenance can be written. Later implementation should add a non-committing internal helper (same ownership, same math) used by both the existing UI path (optional later) and FG-026 insert. If the helper is FG-026-only, existing add_* functions remain unchanged for manual builder.

**Rollback:** any validation or flush failure → `rollback`. Source package unchanged. No orphan line. No orphan insertion. No orphan citations.

**Idempotency:** UNIQUE `client_insertion_key` (browser-generated UUID on the insert form). Duplicate POST returns the existing insertion (200/idempotent) **only** when the key matches an already-committed row; do not create a second line. Unique grouping constraint catches missing-key double submits.

---

## 4. Editability and same-project checks

Service must require, fail-closed:

- current org membership matches package, estimate, assembly/cost item
- `TakeoffPackage.status == "approved"`
- `package.project_id == estimate.project_id == version.estimate.project_id`
- `EstimateVersion.status == "Draft"`
- `version.is_locked is False`
- version status not in `AUTO_LOCK_VERSION_STATUSES`
- selected section belongs to that version
- target Assembly or CostItem `is_active` and `organization_id` matches
- confirmed quantity ≥ 0 using existing Numeric validation
- confirmed unit non-empty (user-confirmed; not inferred)
- at least one frozen package item exists
- provenance rows persist with reconstructable package/item identity copies

`ensure_version_editable` is **necessary but not sufficient** (it only checks `is_locked`).

---

## 5. UI location

**Start:** existing package detail `app/templates/plan_intelligence/takeoff_package.html` at `GET /projects/<id>/plans/takeoff/packages/<package_id>`.

**Add (later):** **Map to estimate** only when `package.status == "approved"`. Dedicated GET/POST under the same project, e.g. `/projects/<id>/plans/takeoff/packages/<package_id>/map`.

Estimating picker: existing Draft versions for this project; existing sections; existing org Assemblies and CostItems (active). If no Draft or no section: copy that directs the user to the **existing** estimate create/builder routes. Do not embed a new estimate-create wizard in this gate.

CSRFProtect and office login remain as today (FG-018).

---

## 6. Builder reuse

| Existing | V1 use |
|----------|--------|
| `add_assembly_line` math + catalog copy | Assembly target |
| `add_cost_item_line` math + catalog copy | CostItem target |
| `add_manual_line` | **Not used** |
| `recalculate_version` | After line create, inside the same transaction |
| Pricing snapshot apply | **Not invoked** |
| `create_estimate_labour_snapshot` | **Not invoked** |

Line `unit` on insert = **user-confirmed unit**, not silently the package `approved_unit` and not silently the template unit unless the user confirmed that value. Preview must show template unit vs package unit when they differ.

---

## 7. Migration requirement

**This preflight pass:** none.

**Implementation (2026-09-08):** additive Alembic revision **`f4a5b6c7d8e9`** (`down_revision = e3f4a5b6c7d8`). Tables above only. Do **not** live-upgrade from the implementation package. Live current remains `e3f4a5b6c7d8` until a later authorized migrate.

---

## 8. Test plan (later implementation; not run now)

Dedicated `tests/test_takeoff_estimate_mapping_fg026.py` (name may vary):

- refuse non-approved / superseded package
- refuse cross-project / cross-org
- refuse locked / non-Draft version
- refuse missing target, missing quantity confirmation, missing unit confirmation
- refuse missing section
- Assembly insert creates one line + one insertion + N citations
- CostItem insert analogue
- package bytes/status unchanged
- later package supersede does not mutate insertion/citations
- duplicate grouping+version rejected
- duplicate `client_insertion_key` is idempotent
- transaction rollback leaves zero lines and zero insertions
- `ensure_version_editable` / AUTO_LOCK still protect issued versions
- no labour snapshot row created
- no pricing snapshot created by the insert path

Then focused: `tests/test_takeoff.py` + `tests/test_estimates.py` + `tests/test_estimate_builder.py` + dedicated FG-026. Full suite before claiming done.

**This governance pass:** product tests **not** rerun.

---

## 9. UAT strategy (later; no data now)

| Step | Pin |
|------|-----|
| Source | Existing labeled FG-010 package on **project 3** (preserve; do not delete) |
| Estimate | **A.** Human-created labeled Draft + section on project 3 via existing estimating UI |
| Target | **B.** Human-created labeled UAT Assembly (preferred) or CostItem. Not AI-created. Not `FG014-UAT-ASM` as a door assembly |
| Exercise | Map package 1 (3 items) → one Assembly line qty confirmed (suggest 3) → three citations |
| Prove | Package still approved/immutable; Draft has the line; Hub/estimate detail show the line; pricing not auto-applied |
| Isolation | Do not write actuals or Field Events. Do not use projects 1, 2, 9, 11, 12, 13 as the mapping destination |

---

## 10. Explicit exclusions

MaterialRequirement; labour-from-takeoff; FG-009 apply from this flow; Assembly explosion; pack rounding; SKU; supplier; `PlanMeasurement`; real external AI; OCR/CAD/multi-trade; LEARN; FG-024; Observation Delete; remaining FG-025 surfaces; auto-create Estimate/Version/Project/Proposal; AI-created commercial templates; putting package id alone on `EstimateLineItem`.

---

## 11. Non-blocking notes

1. Live project 3 has no estimate — expected; later UAT creates a Draft there.
2. Live org has no interior-door Assembly — mapping fail-closed until a human creates one. FG-026 does not author templates.
3. `ensure_version_editable` is weaker than FG-026 Draft-only rule — service must add the Draft check.
4. Existing `add_*_line` commit timing is incompatible with atomic provenance — later prompt must use a non-committing helper.
5. FG-025 remaining surfaces and FG-024 remain unauthorized and unrelated.

---

## Related

- [FG-026](../feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md)
- [ADR-005](../adr/ADR-005-ai-takeoff-traceability.md) · [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) · [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md)
