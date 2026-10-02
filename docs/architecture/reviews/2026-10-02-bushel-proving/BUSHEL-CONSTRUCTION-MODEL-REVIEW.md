# Bushel Construction Model review

| Field | Value |
|-------|--------|
| Label | BUSHEL PROVING FIXTURE |
| Date | 2026-10-02 |
| Slice | 6, after partial coordinates and sheet sets |
| Scale on the generated sheets | 1/4 in = 1 ft |
| Paper | 11×17 landscape, 1224 × 792 pt |
| Sheet count | 5 |
| Would we hand this to the boys? | No |

The fixture is test data. It is not an engine default. The Linda Bushel case folder was not modified. Raster pages and the preview PDF in this directory are inspection copies and are not the product record.

## Generated and refused

| Sheet | Status | Generated / refused | Missing fact if refused | Visual review result |
|-------|--------|---------------------|-------------------------|----------------------|
| 1 of 5, plan | Generated | Generated | Joist and stringer lengths are not drawn. The marks are front-edge stations. | 15 pier marks, 16 joist stations, 10 stringer stations, and the lower outline. Stations that share a point keep that point and carry a count tag. The tags collide along the front edge and are hard to read. |
| 1 of 5, front elevation | Generated for complete geometry | Joist and stringer elevations refused | The elevation of each joist and stringer | Pier marks, the 12 in outline, and the `1'-0"` lower-deck datum. Refusal notes are packed into the frame and overlap one another. Not acceptable. |
| 1 of 5, side elevation | Generated for complete geometry | Joist and stringer elevations refused | The elevation of each joist and stringer | Piers that share a Y stay on that point. A count tag names them. The tag and the refusal notes are crowded. Not acceptable. |
| 2 of 5, section | Generated for the lower outline | Joists and stringers refused | Elevation of those members for the section | One line, the lower walking surface, plus the refusal notes. Not a construction section. |
| 3 of 5, framing detail | Generated | Generated | The detail is one plan station, not a framing plan. | A single station mark. Not a framing plan. |
| Stair | Refused | Refused | Rise, run, nosing, tread count, and the stringer elevation | No stair sheet. |
| Guard, gate, bracket, stringer cut | Refused | Refused | Baluster layout, bracket, and stringer elevation | No sheet. |
| 4 of 5 and 5 of 5, schedule | Generated | Lengths refused where none were supplied | The length of each joist and stringer | Deck outline prints `10'-0", 3'-0"`. Level prints `1'-0" Lower-deck finished walking surface`. Height prints `12"`. Gate prints `42"`. Joist and stringer length cells are blank, and the missing-length lines name each member. |

At 3/8 in = 1 ft the front elevation moves to its own sheet. The scale stays 27 points per foot. The rest of the set is still drawn.

## One-model check

Plan stations and the elevations read the same model. Moving a pier changes the plan and the elevations that include it. Changing a level changes the datum text. Joist elevation is not invented, so those members stay off the elevations.
