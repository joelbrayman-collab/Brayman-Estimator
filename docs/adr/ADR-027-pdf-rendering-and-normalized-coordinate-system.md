# ADR-027 — PDF Rendering and Normalized Document Coordinate System

| Field | Value |
|-------|--------|
| Title | ADR-027: PDF Rendering and Normalized Document Coordinate System |
| Status | **Proposed** (governed by Joel approval / Feature Gate FG-005) |
| Date | 2026-08-28 |
| Related | [ADR-005](ADR-005-ai-takeoff-traceability.md) · [ADR-010](ADR-010-build-versus-buy-document-processing.md) · [ADR-014](ADR-014-sheet-identity-and-page-mapping.md) · [ADR-026](ADR-026-scale-ownership-and-calibration-provenance.md) · [FG-005](../feature-gates/FG-005-m010-scale-calibration.md) · [sheet-intelligence.md](../architecture/sheet-intelligence.md) |

## Context

Interactive plan calibration and manual measurement require a frontend viewer capable of rendering large architectural PDF plan sets, supporting smooth pan/zoom, and capturing user click/drag geometry with precision.
Key engineering challenges include:
1. **Screen Resolution Independence:** Screen pixels vary widely across displays (Retina, 4K, mobile, standard 1080p) and change dynamically with browser zoom and container resizing. Storing raw screen coordinates produces corrupted geometry when viewed on a different screen.
2. **PDF Coordinate Standard:** Standard PDF user space operates at 72 points per inch (DPI), with `(0, 0)` typically at the bottom-left or top-left depending on page media box and crop box transformations.
3. **Renderer Strategy:** Browser-native `<embed>` or `<iframe>` PDF viewers do not expose interactive DOM/Canvas event hooks for overlaying measurement geometries or capturing precise click vectors. Server-side full-resolution rasterization generates heavy network payloads and caching overhead.
4. **Technology Selection:** Open-source, widely adopted client-side PDF rendering (Mozilla PDF.js) renders PDF pages directly into HTML5 `<canvas>` elements, enabling custom SVG/Canvas measurement interaction overlays.

## Decision

1. **Rendering Architecture:**
   - Use **PDF.js** (open-source HTML5 Canvas renderer) embedded within the Plan Intelligence Flask template application for sheet viewing, calibration, and measurement.
   - The frontend renders the PDF page to a canvas and overlays an interactive **SVG / HTML5 Canvas Measurement Layer**.
   - The existing project-scoped download/view routes (`/projects/<id>/plans/<doc_id>/download`) serve the raw PDF stream securely with proper authorization headers.

2. **Normalized Document Coordinate System:**
   - Authoritative geometry for calibrations and measurements must **never** be stored as screen pixels.
   - All spatial points are transformed on the client before persistence into **Normalized Document Coordinates**:
     - Normalized ratio: `(x_norm, y_norm)` where `x_norm = x_pt / page_width_pt` and `y_norm = y_pt / page_height_pt` (in range `[0.0, 1.0]`), OR standard PDF User Space points (`pt` at 72 DPI) referencing the page `MediaBox` / `CropBox`.
   - The authoritative backend data model stores normalized coordinates `(x, y)` as floats, ensuring mathematical stability regardless of client display scaling, DPI, or zoom level.

3. **Measurement Transformation Pipeline:**
   - **Click Input:** Client captures mouse/pointer event `(event.clientX, event.clientY)` relative to the viewport canvas.
   - **Viewport Inverse Transform:** Screen pixels are converted to PDF page points via current zoom scale factor `s` and pan translation offsets `(dx, dy)`.
   - **Normalization:** Point coordinates are normalized against standard page dimensions.
   - **Persistence:** Normalized geometry is submitted to the backend service.
   - **Rendering:** When displayed, normalized coordinates are mapped to current viewport canvas pixels: `screen_x = x_norm * canvas_width`.

4. **Measurement Primitives in M010:**
   - **Linear Distance (`linear`):** 2 points `[P1, P2]`. Computed length: \(\text{Euclidean distance} \times \text{scale\_ratio}\).
   - **Polyline / Path (`polyline`):** Ordered list of points `[P1, P2, ..., Pn]`. Computed total length: \(\sum \text{segment lengths} \times \text{scale\_ratio}\).
   - **Area / Perimeter Polygon (`area`):** Closed polygon of points `[P1, P2, ..., Pn, P1]`. Computed area (Shoelace formula) and perimeter.
   - **Point Count (`count`):** Set of single point coordinates `[P1, P2, ...]`.

5. **Unit Representation & Conversions:**
   - Backend persists real-world measurements with explicit unit tags:
     - Imperial: `in`, `ft`, `sq_ft`, `cu_yd`
     - Metric: `mm`, `cm`, `m`, `sq_m`
   - Canonical conversion factors are maintained in service utilities to ensure deterministic, drift-free unit translation.

## Alternatives Considered

- **Server-side rasterization to PNG/JPEG** — Rejected: Inefficient for large 36"x48" architectural sheets; requires generating multiple zoom levels (tiles/pyramids) and adds server disk/RAM load.
- **Store raw screen pixels** — Rejected: Total failure of coordinate stability across different devices and zoom levels.
- **Third-party proprietary SaaS viewer SDK** — Rejected: Introduces vendor lock-in, recurring licensing costs, and data residency conflicts (Rule 11; ADR-010).

## Consequences

**Positive:**
- Complete device, resolution, and zoom independence.
- High-performance vector rendering and snapping capability directly in the browser.
- Open-source, zero-license dependency footprint.

**Negative:**
- Requires clean client-side JavaScript coordinate transformation and event handling.
- Large multi-page PDFs require lazy page rendering.

## Module Ownership Impact

Plan Intelligence owns the viewer frontend and measurement calculation services.

## Data Ownership Impact

Additive `PlanMeasurement` and `PlanScaleCalibration` models storing normalized coordinates.

## Migration Impact

Additive migration authorized under Milestone 010 ([FG-005](../feature-gates/FG-005-m010-scale-calibration.md)).

## Testing Impact

Frontend and backend tests must verify coordinate invariance across zoom levels, Shoelace formula area precision, Euclidean distance scaling, and unit conversions.

## Approval

| Role | Name | Date |
|------|------|------|
| Product Owner | Joel Brayman | Pending |
| Architecture Review | Proposed for M010 Feature Gate FG-005 | 2026-08-28 |
