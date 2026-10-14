# Brayman Construction Drawing Standard

| Field | Value |
|-------|--------|
| Version | `brayman-drawing-standard-1.1` (`app/services/drawings/standard.py`) |
| Engine | `deck-drawings-1.1` (`app/services/construction_drawings.py`) |
| Accepted fixtures | `tests/fixtures/drawings/pool-deck-synthetic-j1/` |
| Decision | [ADR-058](../adr/ADR-058-construction-drawing-engine-renderer.md) |

This is the permanent record of how CalibraytAI draws. The values live in code and are gathered by `standard()`; this page explains them. Generated PDFs and DXFs are outputs, never the source of the standard.

## What is recorded

| Part | Where it is defined | What it fixes |
|---|---|---|
| Sheet | `core.SHEET_W_IN`, `core.SHEET_H_IN` | 11×17 landscape, 0.3 in border |
| Title block | `pdf.TB_*`, `pdf.render_sheet` | Bottom-right 4.45 × 2.55 in: status banner, logo, company, project, address, title, scale, date, sheet n of N, drawing revision, model revision, set fingerprint |
| Line weights | `core.LW_*` | cut 1.1, object 0.6, medium 0.45, thin 0.3, hair 0.18 (pt) |
| Fills | `core.WOOD` … `core.GRADE` | wood, cut wood, deck boards, steel, water, grade |
| Layers | `dxf.LAYERS` | NCS names (A-DECK, A-STAIR, S-FRAM, S-BEAM, S-COLS, S-FNDN, A-ANNO-DIMS …) with colour and lineweight |
| Dimension style | `pdf._dim`, `dxf` dimstyle `ARCH` | Oblique ticks, feet-inches to 1/16 in, measured from model geometry only |
| Rendering primitives | `core` (`Poly`, `Circle`, `Arc`, `Text`, `Dim`, `Leader`, `View`, `Table`, `Notes`, `ViewTitle`, `TitleBlock`, `Sheet`) | One display list in real inches, rendered by PDF and DXF alike |
| Export rules | `pdf.render_pdf`, `dxf.render_dxf` | PDF: vector, true-scale views, no creation date, deterministic. DXF R2018: inches, DIMENSION entities, hatches, deterministic |
| Templates | `deck.DeckDrawingSet` | Pool-deck set A-1, A-2, S-1, S-2, A-3, A-4, G-1 |

## Stair rule (1.1)

Treads run from the riser board above and project past the riser board below by the nosing product fact (Brayman practice ½–¾ in). The boards the takeoff counts are laid from the nose back; what they leave against the riser above is the back gap, dimensioned on A-3 detail 3 and listed in the stair data. Takeoff formulas and quantities are unchanged.

## Changing the standard

1. Change the code.
2. Bump `STANDARD_VERSION` (and `ENGINE_VERSION` if drawings change), with a one-line reason in `standard.py`.
3. Run `python -m tests.fixtures.drawings.regenerate_accepted_fixtures`.
4. Review the regenerated previews, then commit code and fixtures together.

`tests/test_drawing_engine_deck.py` fails on any drawing change that is not recorded this way. The signature is built from the display list, so it does not depend on matplotlib or ezdxf versions.
