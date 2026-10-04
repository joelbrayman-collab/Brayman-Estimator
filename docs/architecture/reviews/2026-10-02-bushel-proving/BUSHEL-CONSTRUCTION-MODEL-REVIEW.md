# Bushel Construction Model review

| Field | Value |
|-------|--------|
| Label | BUSHEL PROVING FIXTURE |
| Date | 2026-10-02 |
| Slice | 8, after the deck component model |
| Scale on the generated sheets | 1/4 in = 1 ft |
| Paper | 11×17 landscape, 1224 × 792 pt |
| Sheet count | 6 |
| Points per foot | 18 |
| Preview PDF sha256 | `d5d7b8551c3c51b99d20ba6b9b3de412305186cbf7c2fa89333d568772a95f1e` |
| Would we hand this to the boys? | No |

The fixture is test data. It is not an engine default. The Linda Bushel case folder was not modified. Raster pages and the preview PDF in this directory are inspection copies and are not the product record.

Slice 19, 3 Oct 2026, ran this same fixture through the engine after the bearing-annotation slice. The later review is [2026-10-03-bushel-construction-model/BUSHEL-REAL-WORLD-PROVING.md](../2026-10-03-bushel-construction-model/BUSHEL-REAL-WORLD-PROVING.md). The production package was still not modified.

## Generated and refused

| Sheet | Status | Generated / refused | Missing fact if refused | Visual review result |
|-------|--------|---------------------|-------------------------|----------------------|
| 1 of 6, plan | Generated | Generated | Joist and stringer lengths are not drawn. The marks are front-edge stations. | The front-edge stations stay on their coordinates. One callout reads `16 JOISTS`, `joist-1 to joist-16`, `4 PIERS`, `P1 to P4`, and `10 STRINGERS`, `stringer-1 to stringer-10`. The lower outline is called out with pier P10, which shares that corner. The front pier chain prints `6'-0"` three times and `OVERALL 18'-0"`. |
| 1 of 6, front elevation | Generated for complete geometry | Joist and stringer elevations refused | The elevation of each joist and stringer | Pier marks, the `1'-0"` lower-deck datum, and the same `6'-0"` / `18'-0"` chain. One note names joist-1 to joist-16 and stringer-1 to stringer-10. A second note refuses dimension chain `joist-elevations`. Grouped pier callouts name the members that project together. Some leaders still reach the pier line. |
| 1 of 6, side elevation | Generated for complete geometry | Joist and stringer elevations refused | The elevation of each joist and stringer | Piers that share a Y stay on that point. Callouts read `P1 to P4`, `P5 to P7`, `P8 to P9`, `P10 to P12`, and `P13 to P15`. The missing-elevation note is grouped and sits off the marks. |
| 2 of 6, section | Generated for the lower outline | Joists and stringers refused | Elevation of those members for the section | One line, plus one grouped note for joist-1 to joist-16 and stringer-1 to stringer-10. Not a construction section. |
| 3 of 6, framing detail | Generated | Generated | The detail is one plan station, not a framing plan. | A single station mark. Not a framing plan. |
| Stair | Refused | Refused | Rise, run, nosing, tread count, and the stringer elevation | No stair sheet. |
| Guard, gate, bracket, stringer cut | Refused | Refused | Baluster layout, bracket, and stringer elevation | No sheet. |
| 4 of 6 through 6 of 6, schedule | Generated | Lengths refused where none were supplied | The length of each joist and stringer | Deck outline prints `10'-0", 3'-0"`. Level prints `1'-0" Lower-deck finished walking surface`. Height prints `12"`. Gate prints `42"`. Chain `front-pier-stations` prints `6'-0"` and `OVERALL 18'-0"`. Chain `joist-elevations` refuses. Joist and stringer length cells are blank. |

At 3/8 in = 1 ft the front elevation moves to its own sheet. The scale stays 27 points per foot. A view that cannot fit any 11×17 sheet is refused with `VIEW_CANNOT_BE_PLACED_AT_REQUESTED_SCALE`. It is not dropped and it is not shrunk.

## One-model check

Plan stations, the elevations, the callouts, and the pier chain read the same model. Moving a pier changes the plan and the elevations that include it. Changing a level changes the datum text. Joist elevation is not invented, so those members stay off the elevations and the joist elevation chain refuses.

## Component slots

Post, beam, guard, and gate are in the fixture as unsupplied members. They have no location, size, or length. The plan names them in one missing-position note. It does not draw them. Piers still have no shaft length, depth, or capacity. Joist and stringer stations are unchanged.

## Still not a crew set

The sheets are readable enough to see what is known and what is missing. They are not a set to hand to the crew. Lengths, cuts, posts, shafts, guards, and the stair profile are still absent.
