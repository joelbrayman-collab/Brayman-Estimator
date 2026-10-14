# Construction Drawing Provenance — Linda Bushel and the Drawing Engine

| Field | Value |
|-------|--------|
| Status | Record — 14 Oct 2026 |
| Purpose | State where each existing drawing came from and what it does and does not prove |
| Related | [ADR-058](../adr/ADR-058-construction-drawing-engine-renderer.md) · [modules/construction-drawings.md](../modules/construction-drawings.md) |

Classes used below: **historical** (a record of what was issued; not reproducible by the platform), **illustrative** (shows a standard; not generated from project data), **case-specific** (a script written for one case; not a platform capability), **reproducible** (the platform regenerates it from stored data).

| Item | Location | How it was made | Class | What it proves | What it does not prove |
|------|----------|-----------------|-------|----------------|------------------------|
| P1 preliminary set (29 Sep) | `docs/estimating-cases/2026/linda-bushel-pool-deck/drawings/2026-09-29-p1-preliminary-11x17.pdf` | Case script | Historical, case-specific | What was shown to the office on 29 Sep | Nothing about a platform renderer |
| Capability tests (29 Sep): foundation/framing, stair detail, stair detail R2 | same folder, `capability_test_plan.py`, `stair_detail.py`, `stair_detail_r2.py` | Hand-written case scripts | Illustrative, case-specific | That a sheet of that kind can be drawn | Not driven by the construction model |
| J1 preliminary set (1 Oct, 8 sheets) | `.../drawings/2026-10-01-j1-preliminary-11x17.pdf`, review PNGs | `takeoff/issue_j1.py` | Historical, case-specific. **Rejected by Joel (14 Oct) as a drawing standard.** | The J1 facts and quantities issued to Ben | Not a proven renderer; not a quality benchmark |
| `issue_j1.py` | `.../takeoff/issue_j1.py` | Case script mixing J1 numbers, layout and drawing | Case-specific, reproducible only for J1 | The J1 mathematics that `app/services/deck_takeoff/` now owns | Not reusable; not the platform engine |
| Claude's 13 Oct examples (A-1 deck framing plan/section, A-2 interior stair section/detail) | chat `0d461654-…`, copied to scratch as `benchmark-2026-10-13.pdf` | Hand-scripted matplotlib, typed dimensions, generic content (not Bushel) | **Illustrative benchmark only** | The minimum visual standard: line weights, true scale, dimension ticks, title block, notes | Not a Bushel package; not generated from any model; no DXF |
| Old construction model sheet renderer | `app/services/construction_model/sheet.py` | Platform code driven by the stored model | Reproducible, below standard | Model geometry can be drawn | Centreline sticks and X markers; no dimensions, schedules or title block to the standard |
| **Deck drawing set D1 (this work)** | `app/services/drawings/`, `app/services/construction_drawings.py` | Generated from the stored construction model revision, the product facts and the deck takeoff | **Reproducible** — same inputs, byte-identical PDF and DXF | The platform produces a 7-sheet PDF and DXF from stored data, reconciled to the takeoff | Not engineered; PRELIMINARY — NOT FOR CONSTRUCTION |

The 13 Oct examples were never a Bushel package. No claim in this record rests on them beyond visual comparison.
