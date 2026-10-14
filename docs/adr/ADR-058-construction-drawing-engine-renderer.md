# ADR-058 — Construction drawing engine: one display list, PDF and DXF renderers

| Field | Value |
|-------|--------|
| Title | ADR-058: Construction drawing engine renderer |
| Status | **Accepted** (14 Oct 2026, Joel: the seven-sheet D1 set is the visual standard). Migration `v2c3d4e5f6a7` applied with the release |
| Date | 2026-10-14 |
| Migration | `migrations/versions/v2c3d4e5f6a7_construction_drawing_sets.py` |
| Provenance | [construction-drawing-provenance.md](../architecture/construction-drawing-provenance.md) |

## Context

The office needs professional construction drawings generated from the stored construction model and attached to estimates, proposals, BMR supplier requests and Project Plans. The existing renderer (`app/services/construction_model/sheet.py`) draws centreline sticks and markers and falls well below the 13 Oct visual benchmark. The J1 case drawings were rejected and are case scripts, not a platform capability.

## Decision

1. **Keep** the construction model, the deck geometry (`app/services/deck_takeoff/geometry.py`) and the takeoff as the only authorities. The drawing layer computes no quantity; schedules are the takeoff's rows and member lengths are the takeoff's cuts.
2. **Replace the rendering layer** with `app/services/drawings/`: a renderer-neutral display list (polylines, arcs, circles, hatches, text, dimensions, leaders, views at a true scale, tables, notes, title blocks) in real inches.
3. Two renderers read the same list: matplotlib → vector PDF (11×17, true-scale views) and ezdxf → DXF R2018 (inches, NCS layers, DIMENSION entities, hatches). Output is deterministic.
4. `app/services/drawings/deck.py` composes the pool-deck set (A-1, A-2, S-1, S-2, A-3, A-4, G-1). Anything that needs a missing product fact is labelled as waiting, never invented. Every sheet carries PRELIMINARY — NOT FOR CONSTRUCTION and the open engineering items.
5. Generated sets are **write-once** records (`construction_drawing_sets`) keyed by an input fingerprint (engine version, model revision and SHA, product facts version, takeoff fingerprint, project). A model or facts change marks earlier sets outdated; nothing regenerates silently. Attachments (`construction_drawing_attachments`) supersede rather than overwrite.
6. Primitives are reusable for calculator diagrams later; none are implemented now.
7. The drawing standard is recorded and versioned in `app/services/drawings/standard.py`, with accepted fixtures in `tests/fixtures/drawings/`; see [construction-drawing-standard.md](../modules/construction-drawing-standard.md).

## Alternatives considered

- Extend `construction_model/sheet.py` — rejected: no dimension, scale or title-block model; would be rewritten anyway.
- Promote `issue_j1.py` — rejected by Joel; case-specific.
- ReportLab-only drawing — rejected: no shared DXF path; dimensions would be written twice.
- Raster output — rejected: DXF must be real geometry.

## Consequences

Positive: one geometry source for PDF and DXF; drawings reconcile to the takeoff by construction; immutable, attributable revisions. Negative: two new dependencies (matplotlib, ezdxf); two new tables needing migration approval; deck-specific composition must be written per structure type.
