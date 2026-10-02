# Bushel Construction Model review

| Field | Value |
|-------|--------|
| Label | BUSHEL PROVING FIXTURE |
| Date | 2026-10-02 |
| Scale on the generated sheets | 1/4 in = 1 ft |
| Paper | 11×17 landscape, 1224 × 792 pt |
| Would we hand this to the boys? | No |

The fixture is test data. It is not an engine default. The Linda Bushel case folder was not modified. Raster pages and the preview PDF in this directory are inspection copies and are not the product record.

## Generated and refused

| Sheet | Status | Generated / refused | Missing fact if refused | Visual review result |
|-------|--------|---------------------|-------------------------|----------------------|
| Pier / foundation plan | Generated on sheet 1, plan view | Generated | Shaft length, helix, torque, and bracket height are not drawn. The marks are plan locations at grade. | 15 pier marks and the lower outline agree with the model. No shaft is drawn. Not a foundation plan a crew can build from. |
| Framing plan | Refused | Refused | Upper-deck elevation. The 16 joist stations and the beam layout are recorded and were not given a vertical coordinate. | No framing sheet. |
| Decking / guard / gate plan | Refused | Refused | Veranda baluster layout. The 42 in clear gate is a model dimension and is not drawn. | No guard or gate sheet. |
| Front elevation | Generated on sheet 1 | Generated | Lower post cut. Helical shaft length. | Pier marks at grade and the 12 in lower outline. No posts. The 12 in separation is a quarter inch on the sheet. Not acceptable. |
| Side elevation | Generated on sheet 1 | Generated | Lower post cut. Helical shaft length. | Piers that share a Y coordinate stack on one mark. The count is not readable from this view alone. Not acceptable. |
| Stair view | Refused | Refused | Stair rise, stair run, stair nosing, tread count, and the stringer members. Throat 5.00 in, 10 stringers, and the 10 ft stair width stay on the model and are not drawn. Stringer plumb cuts are not confirmed. | No stair sheet. |
| Section | Generated on sheet 2 | Generated | Joists, posts, helical shafts, and stringer cuts are not in the model, so the cut cannot show them. | One line, the lower walking-surface outline. Not a construction section. |
| Detail | Refused | Refused | Bracket for the pier detail. Baluster layout for the guard detail. Stringer member for the cut detail. | No detail sheet. |
| Dimensions | Partial, on the schedule | Generated for the lower outline only | Gate clear and the 12 in height are model dimensions on the level. The schedule does not print level dimensions or units. | No dimension lines on the plan. |
| Schedule | Generated on sheet 3 | Generated | Joist lengths and stringer lengths. Those members were not created. | One decking row, lengths 10.0 and 3.0, fifteen piers, the tread boards, and the Veranda kit name. Readable. Not a build schedule. |

## Stated scale that does not fit

At 3/8 in = 1 ft the front elevation of the 18 ft pier span does not fit its viewport. The composer refuses the whole PDF, including the schedule. It does not move the front elevation onto another sheet.

## One-model check

The plan, the front elevation, and the side elevation list the same element ids. Moving pier P8 changes those views together. The section shows only the lower walking surface. Refused views add no geometry.
