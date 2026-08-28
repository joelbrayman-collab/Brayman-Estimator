# ADR-026 — Scale Ownership, Multi-Scale Viewports, and Calibration Provenance

| Field | Value |
|-------|--------|
| Title | ADR-026: Scale Ownership, Multi-Scale Viewports, and Calibration Provenance |
| Status | **Proposed** (governed by Joel approval / Feature Gate FG-005) |
| Date | 2026-08-28 |
| Related | [ADR-014](ADR-014-sheet-identity-and-page-mapping.md) · [ADR-015](ADR-015-extracted-metadata-ownership-and-provenance.md) · [ADR-017](ADR-017-sheet-metadata-suggestion-and-review-workflow.md) · [ADR-018](ADR-018-sheet-uniqueness-duplicates-and-supersession.md) · [FG-005](../feature-gates/FG-005-m010-scale-calibration.md) · [sheet-intelligence.md](../architecture/sheet-intelligence.md) |

## Context

Construction drawing sheets require physical scale calibration so that estimators can take accurate linear, perimeter, and area measurements.
However, drawings present complex real-world conditions:
1. **Multi-scale sheets:** A single architectural sheet (e.g. A101) may feature a primary floor plan at 1/4" = 1'-0" (1:48) alongside enlarged restroom details at 1/2" = 1'-0" (1:24) or wall sections at 1" = 1'-0" (1:12).
2. **NTS & Graphic Distortion:** Drawings marked "NTS" (Not To Scale), scanned sheets with non-uniform optical distortion, or sheets printed with "fit-to-page" margins may render title-block scale strings inaccurate.
3. **Source Immutability & Provenance:** The raw PDF pages (`PlanPage`) and uploaded documents (`PlanDocument`) must remain immutable source evidence.
4. **Human Authority:** Automatic title-block scale text detection or OCR heuristics must never silently set authoritative drawing scale without human confirmation (Constitution Article 5; Rules 5–6).

## Decision

1. **Scale Ownership Hierarchy:**
   - Physical scale is owned by **Plan Intelligence** as a first-class entity (`PlanScaleCalibration`).
   - A `PlanScaleCalibration` is associated with a specific `PlanSheet` (which belongs to a `DrawingRevision`) and references the specific `PlanDocument` and `page_index` where the calibration geometry was established.
   - A `PlanSheet` may have one **Primary (Default) Scale Calibration** for the overall sheet, plus zero or more **Region/Viewport Scale Calibrations** covering specific bounding regions (e.g. enlarged plan details or section callouts).

2. **Calibration Methods:**
   - **Manual 2-Point Calibration (Authoritative Baseline):** User identifies two distinct reference points on the drawing (e.g. a known dimension string or graphic scale bar), inputs the known real-world dimension and unit, and the system computes the exact scale ratio (real-world distance per normalized document unit).
   - **Preset / Ratio Input:** User selects or enters a standard architectural/engineering ratio (e.g., `1/4" = 1'-0"`, `1:50`), which establishes the mathematical ratio against standard PDF 72 DPI point geometry.
   - **Heuristic Suggestions:** Extractors may propose candidate scale strings harvested from title blocks; however, these remain suggestions until explicitly confirmed by a human reviewer.

3. **Human Authority & Fail-Closed Behavior:**
   - Measurements may **only** be created and marked valid against a **Confirmed** `PlanScaleCalibration`.
   - If a sheet has no confirmed calibration or is explicitly flagged as **NTS (Not To Scale)**, measurement creation must fail closed or visibly flag measurements as uncalibrated/draft, preventing downstream take-off usage.
   - AI suggestions or extracted scale text never auto-confirm a calibration.

4. **Multi-Scale Viewport / Region Scoping:**
   - When a measurement is placed inside a defined **Viewport/Region Calibration**, it automatically binds to that region's specific scale ratio.
   - When placed outside defined viewports on a multi-scale sheet, it binds to the sheet-level primary calibration.

5. **Revision Scoping & Historical Immutability:**
   - Calibrations are strictly scoped to a single `DrawingRevision`.
   - Superseded revision sheets and their associated calibrations/measurements remain immutable historical records.
   - If a new revision (Revision B) is uploaded, calibrations do not silently attach; copying calibrations from a prior revision creates a new proposal record requiring human confirmation.

## Alternatives Considered

- **Store scale directly as a simple string column on `PlanSheet`** — Rejected: A simple string (e.g. `"1/4\" = 1'-0\""`) cannot account for optical distortion, cannot store 2-point calibration geometry, and fails on multi-scale sheets.
- **One scale per `PlanPage`** — Rejected: Violates the Page ≠ Sheet invariant (ADR-014) and prevents logical sheet-level and detail-level calibration across multi-page or multi-detail drawings.
- **Auto-apply OCR detected scale** — Rejected: Direct violation of human authority (Rule 5) and creates massive risk of silent estimating error.

## Consequences

**Positive:**
- Defensible mathematical precision and traceability for all downstream take-offs.
- Seamless handling of multi-detail sheets and enlarged viewports.
- Fail-closed protection against uncalibrated and NTS drawings.

**Negative:**
- Requires explicit user interaction to confirm or calibrate scale before measuring.
- Additional database entities for calibrations and measurement regions.

## Module Ownership Impact

Plan Intelligence owns all calibration and measurement records. Estimating, Proposals, and Project Controls remain strictly unchanged.

## Data Ownership Impact

Additive `PlanScaleCalibration` records under `PlanSheet`. Source `PlanDocument` and `PlanPage` records remain immutable.

## Migration Impact

Additive migration authorized under Milestone 010 ([FG-005](../feature-gates/FG-005-m010-scale-calibration.md)).

## Testing Impact

Tests must verify: 2-point calibration derivation, human confirmation requirement, multi-scale viewport scoping, NTS fail-closed behavior, and revision isolation.

## Approval

| Role | Name | Date |
|------|------|------|
| Product Owner | Joel Brayman | Pending |
| Architecture Review | Proposed for M010 Feature Gate FG-005 | 2026-08-28 |
