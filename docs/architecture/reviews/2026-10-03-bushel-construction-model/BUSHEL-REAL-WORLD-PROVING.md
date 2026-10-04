# Bushel real-world proving pass

| Field | Value |
|-------|--------|
| Date | 2026-10-03 |
| Slice | 19 |
| Model | `tests/fixtures/construction_model/bushel_proving_fixture.py` |
| Engine | `app/services/construction_model/` |
| Case authority | [linda-bushel-pool-deck/case-record.json](../../../estimating-cases/2026/linda-bushel-pool-deck/case-record.json) `governed_decisions_2026_10_01` |
| Scale | 1/4 in = 1 ft (18 points per foot) |
| Paper | 11×17 landscape, 1224 × 792 pt |
| Sheet count | 7 |
| Preview PDF sha256 | `ff6d8bead713eeee5731a031922f1883b2009243366cdc729653fcfc810a3b0e` |
| Would we hand this to the boys? | No |

This file is a review of one proving run. It is not a second project record and it is not a drawing standard. The Linda Bushel production package was not modified. The engine was not given Bushel values.

The earlier proving review remains [2026-10-02-bushel-proving/BUSHEL-CONSTRUCTION-MODEL-REVIEW.md](../2026-10-02-bushel-proving/BUSHEL-CONSTRUCTION-MODEL-REVIEW.md). That run used the same fixture. This run uses the engine after Slice 18.

## What was loaded

The 1 Oct 2026 governed decisions match the fixture:

| Fact | Value | Source | Provenance | Status |
|------|-------|--------|------------|--------|
| Address | 12 D'Arcy's Way, Kemptville, ON K0G 1J0 | Case record | Sheet project input | Present |
| Piers | 15, CT-1 coordinates, z = 0 | Joel, 2026-10-01 | `source_document` | Present as points |
| Joist lines | 16, P1 stations, front edge Y = 15.5 ft | Joel, 2026-10-01 | `source_document` | Present as plan stations. Z unknown |
| Stringers | 10, P1 stations, same front edge | Joel, 2026-10-01 | `source_document` | Present as plan stations. Z unknown |
| Working throat | 5.00 in | Joel, 2026-10-01 | `project_input` on the stair result | Present. Not a certification |
| Lower walking surface | 12 in, 10 ft × 3 ft outline | Joel, 2026-10-01, on the selected lower pier coordinates | `project_input` for the level; `source_document` for the outline | Present at z = 1 ft |
| Tread boards | Two 5/4 × 6 boards per tread | Joel, 2026-10-01 | Material name | Present as a name |
| Guard kit | 37 in Veranda rail kit | Joel, 2026-10-01 | Material name | Present as a name |
| Gate clear | 42 in | Joel, 2026-10-01 | Dimension | Present as a dimension |
| Stair width | 10 ft | Design brief, cited on the stair result | `project_input` | Present as a number |
| Front pier chain | 6 ft + 6 ft + 6 ft, overall 18 ft | CT-1 coordinates P1–P4 | `governed_calculation_result` | Present |

Post, beam, guard, and gate are slots. They have no location, size, or length. Provenance is `project_input`. Status is `field_verification_required`.

## What was not loaded

These appear in older case text. They were not copied into the model.

| Fact | Where it appears | Why it stayed out | Class |
|------|------------------|-------------------|-------|
| Helical shaft, helix, torque, capacity | 1 Oct decision says they are not specified | No value exists to store | A. Project input |
| Sonotube diameter and 48 in depth | 29 Sep design brief | Superseded by the helical decision | Not a current fact |
| Stair rise, run, nosing, tread count, riser count | Brief says approximately 38 in, five field-adjusted risers at approximately 7.6 in, and approximately 11 in treads | Approximate and field-adjusted. Not an exact construction fact | A. Project input |
| Joist elevation, stringer elevation, stringer cuts | Not in the 1 Oct selection | Stations have X and Y only | A. Project input |
| Upper-deck polygon and pool curve | Brief says the pool edge follows the curve | Curve coordinates are not a 1 Oct selection | C. Source coordinates are not in the governed case |
| Beam and wing coordinates | Brief names Option A in words | No governed coordinate pair | C. Source coordinates are not in the governed case |
| Nominal sizes in the brief (2×8 joists, double 2×10 beams, 2×12 stringers, 6×6 posts, 4×4 guard posts) | 29 Sep design basis | The 1 Oct selection does not restate them onto the located stations | A. Project confirmation before they become member attributes |
| Bracket, post cut, baluster layout, hinge, latch, bottom rail, connector shape | Named as absent, or absent | Not supplied | A. Project input |
| J1 stair profile, connector counts, and schematic helix | J1 drawings | J1 is comparison evidence. It is not the model | Not carried forward |

No missing fact is class D. The engine can store a point, a polyline, a level, a dimension, a stair result, and a relationship when the project supplies them.

## Sheets

Every page was rendered and read. Scale stayed 1/4 in = 1 ft.

| Sheet | Status | Generated / refused | Missing fact if refused | Visual result | Constructability |
|-------|--------|---------------------|-------------------------|---------------|------------------|
| 1 Plan, front elevation, side elevation | Generated for complete geometry | Joist and stringer elevations refused. Post, beam, guard, and gate positions refused | Elevation of each joist and stringer. Plan position of the four slots | Lower outline, 15 pier marks, front chain `6'-0"` three times and `OVERALL 18'-0"`, datum `1'-0"`. Joists and stringers are one station callout each, `joist-1 to joist-16` and `stringer-1 to stringer-10`. Refusal notes sit in the elevation frames | Readable as a location sheet. Not a framing plan and not an elevation a crew can build from |
| 2 Section lower-surface | Generated for the lower outline | Joists, stringers, and the four slots refused | Their elevations, and plan position where none was stored | One line for the lower surface. Cut text is direction x, location 0, depth 0 | Not a construction section |
| 3 Detail framing-plan | Station generated. Index status NOT ISSUED | Connection refused | The connection for this detail | One mark, `joist-1`. The unresolved banner and the refusal sentence share the corner | Not a framing detail |
| Stair | Refused | Refused | Rise, run, nosing, tread count, riser count, and each stringer elevation | No stair sheet. The refusal is on the compose result, not on the drawing index | A reader of the PDF alone does not see a stair line |
| Pier bracket, guard balusters, stringer cut | Refused | Refused | Bracket, baluster layout, stringer elevation | No sheet | Named on the compose result |
| 4 Schedule | Generated | Lengths blank where none were supplied | Length of each joist, stringer, and slot | Counts match the model: 1 decking, 16 joists, 10 stringers, 1 of each slot, 15 piers. Decking length `10'-0"`. Dimensions `10'-0"`, `3'-0"`, `12"`, `42"`. Materials name the tread boards and the Veranda kit. Connection and relationship tables are empty | The known counts and the known dimensions are usable. The blank size and length cells are the missing facts |
| 5 Schedule | Generated | Chain `joist-elevations` refused | Elevation of joist-1 and joist-2, then the missing lengths | Front pier chain prints `6'-0"` and `OVERALL 18'-0"`. The rest of the page is one refusal sentence per missing length | A refusal list, not a cutting list |
| 6 Schedule | Generated | Continuation of the length refusals | Length of the beam, guard, and gate slots | Three refusal lines. The chain title repeats at the top of the overflow page | Sparse. The repeated chain title does not add a second dimension |
| 7 Drawing index | Generated | Lists the seven sheets | The refused stair and the refused details are not index lines | Sheet 1 is titled orthographic. Sheet 3 is NOT ISSUED. Scale on the index is not a scaled view | The index matches the pages that were drawn |

## One model

Plan, both elevations, the section, the issued detail, and the schedules use the same ids: `P1`–`P15`, `joist-1`–`joist-16`, `stringer-1`–`stringer-10`, and `lower-walking-surface`. Moving pier P8 changes the plan and the front elevation together. No sheet keeps a private Bushel geometry.

## Cross-view

The 15 pier ids match across the plan and both elevations. The lower surface is at 1 ft on the elevations and `1'-0"` on the schedule. The front chain overall of 18 ft is the distance from P1 to P4. Joists and stringers are on the plan and off the elevations, and the sheets say why. The schedule quantities match the model counts. No contradiction was resolved by adding a number.

The stair refusal is not printed on a sheet. That is a sheet-index gap. It is not a second stair.

## J1

J1 remains the production preliminary package. It was not copied and it was not regenerated.

J1 draws joist lines, a stair profile, guards, a gate, and a schematic helix. Those sheets are more picture-complete. They also carry approximate stair figures, connector counts, and a helix the 1 Oct decision does not specify. This proving set does not improve on J1 as a picture. It improves on J1 by refusing those facts instead of drawing them. Plan stations, the 15 pier marks, the 18 ft front chain, the 12 in datum, the 42 in gate dimension, and the schedule counts are the governed residue. Framing lines, elevations of the frame, the stair, sections through the frame, and construction details are not in this set because the facts are not in the model.

## Engine versus project

| Failed output | Class |
|---------------|-------|
| Joist and stringer elevations, lengths, and cuts | Project input missing |
| Stair rise, run, nosing, tread count, riser count | Project input missing |
| Shaft, helix, torque, bracket, post cut, baluster layout, guard and gate location | Project input missing |
| Upper-deck curve and beam coordinates | Source evidence missing |
| Nominal lumber sizes from the 29 Sep brief | Project input, until the 1 Oct selection adopts them |
| Unprojected stair and details absent from the drawing index | Presentation deficiency. The refusal is on the compose result |
| Refusal notes inside the elevation frames, and the unresolved banner on sheet 3 | Presentation deficiency |
| Engine cannot represent a supplied point, polyline, level, or stair result | None found |

## V1

One-model and no-guessing stay **PARTIAL**. This pass shows both rules operating on the Bushel model. It does not close them. Bearing stays **COMPLETE** for its recorded criteria. This model has no bearing relationship to draw. No score was changed.
