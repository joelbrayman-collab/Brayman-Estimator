# Module — Construction Drawings

| Field | Value |
|-------|--------|
| Status | **ACCEPTED by Joel (14 Oct 2026) as the visual standard; released with migration `v2c3d4e5f6a7`** — see current-state for the release record |
| Standard | [construction-drawing-standard.md](construction-drawing-standard.md) (`brayman-drawing-standard-1.1`) |
| Decision | [ADR-058](../adr/ADR-058-construction-drawing-engine-renderer.md) (Proposed) |
| Provenance | [construction-drawing-provenance.md](../architecture/construction-drawing-provenance.md) |
| Migration | `v2c3d4e5f6a7` (down `u1b2c3d4e5f6`) — two new tables; downgrade refuses while drawing sets exist |

## Owns

- `app/services/drawings/core.py` — display list, layers, line weights, helpers.
- `app/services/drawings/pdf.py` — vector PDF / PNG renderer.
- `app/services/drawings/dxf.py` — DXF R2018 renderer.
- `app/services/drawings/deck.py` — pool-deck set composition (7 sheets).
- `app/services/drawings/standard.py` — the versioned drawing standard and the content signature.
- `tests/fixtures/drawings/pool-deck-synthetic-j1/` — accepted standard, signature and sheet previews.
- `app/services/construction_drawings.py` — generate, fingerprint, state, Project Plans, attach, append.
- `app/models/construction_drawing.py` — `ConstructionDrawingSet`, `ConstructionDrawingAttachment`.
- `app/routes/construction_drawings.py` — `/projects/<id>/drawings…`, supplier package route.

## Does not own

Geometry and quantities (deck takeoff), the construction model (Projects), estimate/proposal/supplier-request records. It reads them and appends drawing pages on download only; stored request PDFs are unchanged.

## Workflow

Project → Construction Drawings → choose model revision → Generate (actor required) → preview → PDF / DXF → Save to Project Plans → attach the current set to an estimate version (unlocked), a proposal (Draft/Ready) or a BMR supplier request (same takeoff fingerprint). Estimate print and proposal PDF append the current attachment; the supplier package route appends to the request and its form still reads back.

## Rules

Write-once sets; same fingerprint returns the existing set; outdated sets cannot be attached; newer attachments supersede; organization and project isolation; PRELIMINARY — NOT FOR CONSTRUCTION; open engineering items on every set; no invented product facts.

## Tests

`tests/test_drawing_engine_deck.py` (13: geometry, takeoff parity, stair nosing, accepted standard and signature), `tests/test_construction_drawings.py` (9), `tests/test_construction_drawing_migration.py` (2).

Form 2 (live `a24e3d2`) is preserved: a BMR request with drawings appended keeps its three supplier boxes per line and imports through the server's price intake.
