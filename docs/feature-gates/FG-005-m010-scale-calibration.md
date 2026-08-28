# Feature Gate — M010 Scale Calibration / Measurement Tools

| Attribute | Value |
|-----------|--------|
| ID | **FG-005** |
| Milestone | **M010** — Scale Calibration / Measurement Tools |
| Module | Plan Intelligence |
| Date | 2026-08-28 |
| Approved baseline | `main` @ `13ac5fd` (Review Turnover Reconciliation); intended Alembic head `b8d9f0a1c2e3` (M009) |
| Architecture | [sheet-intelligence.md](../architecture/sheet-intelligence.md) · [plan-intelligence-and-automated-takeoff.md](../architecture/plan-intelligence-and-automated-takeoff.md) |
| Module doc | [modules/plan-intelligence.md](../modules/plan-intelligence.md) |
| Related ADRs | [ADR-026](../adr/ADR-026-scale-ownership-and-calibration-provenance.md) **Accepted** · [ADR-027](../adr/ADR-027-pdf-rendering-and-normalized-coordinate-system.md) **Accepted** · [ADR-014](../adr/ADR-014-sheet-identity-and-page-mapping.md) · [ADR-015](../adr/ADR-015-extracted-metadata-ownership-and-provenance.md) · [ADR-017](../adr/ADR-017-sheet-metadata-suggestion-and-review-workflow.md) · [ADR-018](../adr/ADR-018-sheet-uniqueness-duplicates-and-supersession.md) |
| CAR | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |

---

## Status

| Layer | State |
|-------|--------|
| Architecture (M010) | **APPROVED** (Measurement & Calibration architecture defined) |
| Feature Gate (this document) | **APPROVED** (2026-08-28, Joel via prompt) |
| Implementation | **IMPLEMENTED & VERIFIED** (2026-08-28; migration `c9e0f1a2b3d4`; 19 focused tests, 140 total pytest passed) |

---

## Objective

Extend Plan Intelligence to provide an interactive, high-precision **drawing scale calibration and manual measurement foundation** on reviewed `PlanSheet` entities. Estimators can calibrate drawing scales using known 2-point reference dimensions or standard ratios, define multi-scale viewports, and take manual linear, polyline, area, and count measurements with normalized coordinate stability, establishing trustworthy measurement primitives for downstream M011+ quantity take-off.

---

## Feature Gate Answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Reviewed construction drawing sheets require verified physical scale and interactive measurement tools so estimators can take defensible linear, perimeter, area, and count measurements before automated take-off. |
| 2 | Who is the user? | Estimators and take-off reviewers working in the office Plan Intelligence web UI on a Project's reviewed plan sheets. |
| 3 | Which module owns it? | **Plan Intelligence** (Measurement & Calibration sub-layer). Do not create a separate measurement module. |
| 4 | What data does it own? | Additive `plan_scale_calibrations` (sheet/viewport scale ratios, 2-point geometry, unit, confirmation state) and `plan_measurements` (geometry points, measurement types, computed values, units, calibration references). |
| 5 | What data does it reference? | `projects` (lifecycle hub); `drawing_revisions`; `plan_sheets`; `plan_sheet_pages`; `plan_documents`; `plan_pages`. |
| 6 | What may implementation change? | Additive models, services, routes, templates, and static assets under `app/plan_intelligence/`; additive Alembic migration for M010 tables; project-scoped measurement UI with PDF.js viewer; focused tests. |
| 7 | What must implementation not change? | M009 Sheet identity/review SoR; PlanDocument binary bytes and checksums; PlanPage extractions; Estimating builder and cost items; Proposals; Change Orders; pricing policy formulas; auth; legal templates. |
| 8 | What are the acceptance criteria? | See **Acceptance criteria** below. |
| 9 | What tests are required? | See **Required implementation tests**. |
| 10 | What documentation must be updated? | This gate; ADR-026/027; ADR index; FG index; Plan Intelligence module doc; current-state; project-state-report; session-handoff; platform-roadmap; milestones; chat-workflow-log. |
| 11 | Which ADRs govern it? | [ADR-026](../adr/ADR-026-scale-ownership-and-calibration-provenance.md) (Scale Ownership & Multi-Scale Provenance); [ADR-027](../adr/ADR-027-pdf-rendering-and-normalized-coordinate-system.md) (PDF Rendering & Normalized Coordinates); [ADR-014](../adr/ADR-014-sheet-identity-and-page-mapping.md); [ADR-017](../adr/ADR-017-sheet-metadata-suggestion-and-review-workflow.md). |
| 12 | Does it require a database migration? | **Yes — future implementation prompt only.** Additive `plan_scale_calibrations` and `plan_measurements` tables. This governance prompt must **not** create migrations. |
| 13 | What rendering/frontend architecture is authorized? | Open-source **Mozilla PDF.js** HTML5 canvas renderer embedded in Flask templates, coupled with an interactive SVG/Canvas geometry overlay. Raw screen clicks are transformed client-side into normalized document coordinates before persistence. |
| 14 | What units are authorized? | Imperial (`in`, `ft`, `sq_ft`, `cu_yd`) and Metric (`mm`, `cm`, `m`, `sq_m`). Canonical mathematical storage in normalized document units with deterministic real-world conversion factors. |
| 15 | What measurement types are authorized? | Linear distance (`linear`), polyline length (`polyline`), polygon area and perimeter (`area`), and item count (`count`). |
| 16 | How are multi-scale / NTS sheets handled? | Primary sheet-level calibration applies by default; named viewport/region calibrations override scale within their bounding boxes. Sheets marked **NTS (Not To Scale)** or uncalibrated fail closed by disabling active measurement. |
| 17 | What is the human approval/calibration rule? | Extracted/suggested scale strings require explicit human confirmation. Measurements are valid **only** when referenced against a Confirmed calibration. Auto-confirmation by heuristic or OCR confidence is strictly prohibited. |
| 18 | What are the stopping conditions? | Stop if PDF coordinate systems vary non-linearly across pages, if migration threatens existing M009 records, or if requirements conflict with source immutability. |

---

## Core Invariants (Must Remain True)

1. **Page ≠ Sheet Preservation:** Scale and measurements attach to logical `PlanSheet` entities (and reference the mapped `PlanDocument` / `page_index`). Raw `PlanPage` records remain immutable source extraction evidence.
2. **Source Immutability:** `PlanDocument` binary bytes, SHA-256 hashes, and `PlanPage` raw extractions must never be mutated to store scale or measurements.
3. **Human Authority:** AI suggestions or regex title-block extractions never auto-confirm a calibration. Measurements derived without a confirmed calibration fail closed.
4. **Coordinate Normalization:** Geometry must be persisted in normalized document coordinates `(0.0 to 1.0)` or standard PDF User Space points (`pt` at 72 DPI), guaranteeing device, screen resolution, and zoom level independence.
5. **Revision & Project Isolation:** Calibrations and measurements are scoped to a single `DrawingRevision` and `Project`. Superseded revision records remain immutable historical evidence.
6. **Commercial Separation:** M010 provides pure geometric and physical measurement primitives. It does **not** create or modify estimate line items, assembly quantities, or pricing rates.

---

## Authorized Data Model (M010 Additive Schema)

### 1. `PlanScaleCalibration` (`plan_scale_calibrations`)
- `id`: Integer primary key
- `sheet_id`: Integer foreign key -> `plan_sheets.id` (required, indexed)
- `plan_document_id`: Integer foreign key -> `plan_documents.id` (required)
- `page_index`: Integer (0-based page index)
- `calibration_type`: String(50) (`sheet_default`, `viewport_region`, `graphic_bar`, `dimension_string`, `preset_ratio`)
- `region_name`: String(100) (optional, e.g. "Detail 3 - Foundation Section")
- `region_box`: JSON (optional bounding box `{"x1": float, "y1": float, "x2": float, "y2": float}`)
- `point1_x`, `point1_y`: Float (normalized coordinate of point 1)
- `point2_x`, `point2_y`: Float (normalized coordinate of point 2)
- `measured_points_distance`: Float (Euclidean distance between points in normalized/PDF units)
- `real_world_distance`: Float (human-entered reference distance)
- `real_world_unit`: String(20) (`ft`, `in`, `mm`, `m`)
- `scale_ratio`: Float (real-world units per normalized PDF document unit)
- `status`: String(50) (`draft`, `confirmed`, `void`, `nts`)
- `notes`: Text (optional)
- `created_at`, `updated_at`: DateTime (required)

### 2. `PlanMeasurement` (`plan_measurements`)
- `id`: Integer primary key
- `sheet_id`: Integer foreign key -> `plan_sheets.id` (required, indexed)
- `scale_calibration_id`: Integer foreign key -> `plan_scale_calibrations.id` (required)
- `measurement_type`: String(50) (`linear`, `polyline`, `area`, `count`)
- `label`: String(255) (optional descriptive tag, e.g. "North Foundation Wall")
- `geometry_data`: JSON (ordered array of normalized coordinate points `[{"x": float, "y": float}, ...]`)
- `computed_value`: Float (computed length, area, or count)
- `computed_unit`: String(20) (`ft`, `sq_ft`, `m`, `sq_m`, `count`)
- `status`: String(50) (`active`, `void`)
- `created_at`, `updated_at`: DateTime (required)

---

## Acceptance Criteria

1. **2-Point Calibration:** Estimator can select two points on a displayed plan sheet, input a known reference dimension (e.g. 24'-6" or 7500 mm), and confirm the derived scale ratio.
2. **Standard Ratio Selection:** Estimator can choose standard architectural/engineering ratios (e.g. 1/4" = 1'-0", 1:50) as initial calibration.
3. **Multi-Scale Viewports:** Estimator can draw a bounding box region, assign a distinct scale calibration to that region, and take measurements that compute against that region's scale.
4. **Interactive Measurement Primitives:**
   - Linear Distance: 2-point line showing real-time dimension.
   - Polyline: Multi-segment path showing total cumulative length.
   - Area: Closed polygon showing calculated surface area and perimeter.
   - Count: Placed point markers showing total item count.
5. **Coordinate Stability:** Zooming in/out, resizing the browser window, or reopening the sheet on different screen resolutions maintains exact geometric alignment with the underlying drawing elements.
6. **Fail-Closed NTS/Uncalibrated Handling:** If a sheet is uncalibrated or flagged NTS, measurement actions are disabled or clearly flagged as uncalibrated.
7. **Revision Scoping:** Calibrations and measurements are sealed under their `DrawingRevision`. Uploading a new revision preserves prior measurements as historical records.
8. **Isolation & Security:** All calibration and measurement API routes enforce strict Project -> DrawingRevision -> Sheet hierarchy checks.

---

## Required Implementation Tests

1. `test_two_point_calibration_computes_exact_scale_ratio`: Validates Euclidean distance to real-world scaling math.
2. `test_human_confirmation_required_before_measurement`: Asserts that measurements cannot be created against unconfirmed or draft calibrations.
3. `test_linear_measurement_calculation`: Verifies linear distance calculation against calibrated scale.
4. `test_polyline_measurement_cumulative_length`: Verifies multi-segment polyline path calculation.
5. `test_polygon_area_shoelace_calculation`: Verifies polygon area and perimeter computation.
6. `test_normalized_coordinate_zoom_invariance`: Asserts that normalized coordinate points remain identical across different client canvas dimensions.
7. `test_multi_scale_viewport_calibration_scoping`: Verifies that measurements within a defined viewport use the viewport scale rather than the sheet default scale.
8. `test_nts_sheet_fails_closed`: Verifies that marking a sheet NTS prevents active take-off measurements.
9. `test_superseded_revision_calibration_immutable`: Asserts that prior revision calibrations/measurements are unchanged when a new revision is created.
10. `test_project_and_revision_isolation`: Verifies cross-project calibration access fails closed (404/403).
11. `test_source_plandocument_and_page_immutability`: Confirms that `PlanDocument` binary bytes, SHA-256 hash, and `PlanPage` raw extractions are untouched by calibration.
12. `test_existing_estimating_proposals_change_orders_unaffected`: Regresses existing commercial modules.

---

## Migration Plan (M010 Implementation Prompt)

- **Starting Alembic Head:** `b8d9f0a1c2e3` (M009)
- **Authorized Migration:** Additive migration creating `plan_scale_calibrations` and `plan_measurements` tables with proper foreign keys and indexes.
- **Data Integrity:** No existing tables or columns may be dropped or renamed.

---

## Approval & Authority

| Role | Name | Status | Date |
|------|------|--------|------|
| Product Vision & Approval | Joel Brayman | **APPROVED** (via this prompt) | 2026-08-28 |
| Architecture & Governance | Proposed Architecture | **APPROVED** (CAR-001 aligned) | 2026-08-28 |
| Implementation | Coded Implementation | **NOT STARTED** (Awaits dedicated implementation prompt) | — |
