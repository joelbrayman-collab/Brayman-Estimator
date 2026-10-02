# Complete deck acceptance audit — 2 Oct 2026

| Field | Record |
|-------|--------|
| Slice | 12. Audit only. No drawing change. |
| Date | 2026-10-02 |
| Fixture | COMPLETE DECK DRAWING ENGINE FIXTURE |
| Source | `tests/fixtures/construction_model/complete_deck_fixture.py` |
| Product commit audited | `2c52a70a967c187e32bdb579901098238b79e747` |
| Drawing-set version | Engine `cm-1`. Projection `cm-2`. Sheet `cm-3`. Wave `cm-5`. |
| Paper | 11×17 landscape |
| Sheets | 13. Foundation plan, framing plan, decking/guard/gate plan, front elevation, side elevation, stair, section A, post-and-beam detail, stringer-and-tread detail, guard-and-gate detail, three schedule sheets. |
| Scales | 1/2 in = 1 ft on the plans, elevations, and section. 1 in = 1 ft on the stair. 3 in = 1 ft on the post/beam and stringer details. 3/2 in = 1 ft on the guard and gate detail. Schedules are not scaled views. |
| Inspection PDF sha256 | `91038a06da8db8632b402bc8eccd870b74d6c982b4ec16a38699a15dd9d1086a` |
| Bushel | Not used. Not modified. Not the acceptance fixture. |
| Would we hand this to the crew? | No. |

Authorities used: [construction-drawing-standard.md](../../construction-drawing-standard.md) and [v1-completion-register.md](../../../v1-completion-register.md) section 2.1. Recalled for this component: the one-model rule (**PARTIAL**), no-guessing / refusal (**PARTIAL**), and bearing / relationship fidelity (**COMPLETE** for the criteria on that row). This audit does not rescore V1. Official readiness stays 65% / 4 of 11.

Classification used below, one class per deficiency:

| Class | Meaning |
|-------|---------|
| A | FIXTURE DATA ONLY. The engine can already carry the fact. This fixture does not supply it. |
| B | CONSTRUCTION MODEL CAPABILITY. The model cannot represent the fact. |
| C | DRAWING ENGINE CAPABILITY. The model can hold the fact, and the drawing does not project it. |
| D | SHEET / DOCUMENT OUTPUT CAPABILITY. The view exists, and the sheet does not present it as a construction document. |
| E | TRUE ARCHITECTURAL DEPENDENCY. A capability must be designed before it can be built. |

No deficiency in this audit is class E. An unknown value is not a platform dependency.

## What the set already does

The model is complete for the facts it contains. Assessment issues are empty. The composed set is 13 sheets. Plan, elevations, stair, section, details, and schedules read that one model.

Counts agree: 4 piers, 4 posts, 2 beams, 8 joists, 5 rims, 1 header, 20 deck boards, 6 guard rails, 82 balusters, 1 gate, 3 stringers, 5 treads. Width is 12'-0". Depth is 10'-0". Joist spacing is 1'-4". Beam length is 10'-0". Grade is 0'-0". Walking surface is 3'-6". Stair unit rise 7", unit run 11", total rise 3'-6", total run 4'-7", three stringers, five treads, width 36", throat 5", nosing 1". Those figures are the same on the drawing that shows them and on the schedule.

The framing plan shows the footprint, the joists, the spacing chain, the beams, the posts, the rims, the stair header, and the stair opening. The stringer detail shows the tread on the supplied seat. The post-and-beam detail shows the supplied 3 inch contact. The guard detail names the missing connection and does not invent one. The title block is the same on every sheet: Brayman Construction, the fixture name, revision A, 2026-10-02, sheet number of 13, the preliminary status, and the scale. The scale is not fitted to the paper.

Large empty margins on the plan sheets are the stated 1/2 in = 1 ft scale on a 12 ft by 10 ft deck. They are not a defect and they are not to be closed by auto-fitting.

## Sheet-by-sheet constructability

| Sheet | Can a carpenter read the assembly? | Why, when the answer is no |
|-------|------------------------------------|----------------------------|
| 1 Foundation plan | Partly. Four 12 inch squares and a 10'-0" spacing between the front piers. | No depth dimension between the front and back pier lines. No pier-depth dimension. No section mark. Labels sit in a corner list. |
| 2 Framing plan | Partly. This is the strongest sheet. Footprint, joists, spacing, beams, posts, rims, header, and the stair opening are visible. | No blocking, no ledger, no joist connection, no section cut, no detail reference. Most callouts are a corner list with one leader. |
| 3 Decking, guard, and gate | Partly. Boards, baluster marks, the gate gap, and the stair opening match the framing plan. | No dimension on this sheet. No note that sends the carpenter to the framing dimensions. The gate is one rail, not a gate assembly. |
| 4 Front elevation | Partly. Posts, piers, the deck, the guard, grade, and the walking surface agree with the plan. | No height dimension. The stair is not on this view. Balusters read as a band of lines. Callouts are piled at the top. |
| 5 Side elevation | Partly. The same stack, plus the stair, agrees with the stair sheet. | The stair is too small here to build from. Guard height is not dimensioned. Callouts are piled at the top. |
| 6 Stair | Yes, for the stringer and the treads. Five seats, the treads on those seats, rise 3'-6", run 4'-7", and the supplied stair facts. | No upper connection, no lower bearing, no landing, no stair guard. The tread clip is a note. |
| 7 Section A | Partly. Piers, posts, the front beam, joists, and one deck board are the members cut at y = 1 ft. The note states pier supports post, post bears on beam, beam supports joist, joist supports decking. | No height dimension. No cut mark on the plans. Rim and guard cuts read as small unlabeled marks. The stair is outside this cut, which is correct. |
| 8 Post and beam | Yes, for the supplied contact. The beam sits on the post. The bearing is the supplied 3 inches. The post cap and two bolts are named. | No connector shape. The other three posts have no bearing record and no connector. |
| 9 Stringer and tread | Yes, for one seat. The tread sits on the notch. The nosing and the riser are visible. The clip and two screws are named. | No connector shape. The label for the stringer sits off the board. |
| 10 Guard and gate | No. Rails and three balusters are drawn. | The sheet says “You need to provide this information. The connection for this detail.” That refusal is correct. There is no hinge, latch, post, or bottom rail. |
| 11–13 Schedules | No, as a construction schedule. | Member rows match the model. Columns do not align. Relationship rows say bearing is both supplied and not supplied for the same roles. Sheet 13 is one line. |

## Cross-view consistency

Geometry, counts, levels, and the dimensions that exist agree from plan to elevation, from framing to the member schedule, from the stair to the stringer detail, and from the post/beam relationship to that detail. No view keeps its own members.

The relationship schedule does not agree with the drawings. The stair and the stringer detail show a supplied bearing. The schedule also prints `supports / stringer / tread / bearing not supplied` beside `bears_on / stringer / tread / bearing supplied`. The same split appears for post and beam. That is a sheet-presentation contradiction. It is not a second geometry store.

## No-guessing check

The guard-and-gate refusal is legitimate. The connection is absent. The sheet names “The connection for this detail.” It does not draw a hinge or a latch.

The post cap and the tread clip stay notes. A product name did not become a shape.

Bearing points that do not lie on both members are refused as `CONFLICTING_GEOMETRY` by the model. This fixture’s supplied bearings pass that check. Members are not moved.

The set is still issued while that guard connection is missing. The drawing standard says a missing required fact means there is no PDF. The sheet layer prints the refusal and continues. The refusal text meets the no-guessing row. Issuing the set does not meet the drawing law’s “no PDF” sentence. This audit does not change that behavior.

## Deficiency register

| ID | Deficiency | Class | Severity | Acceptance impact | V1 requirement |
|----|------------|-------|----------|-------------------|----------------|
| D1 | Front-to-back pier spacing and pier depth are not dimensioned. The model has the pier coordinates and a 48 inch shaft. No chain is supplied for those facts. | A | Limits sheet 1 | A carpenter cannot lay out the pier rectangle from sheet 1 alone. | One-model. The fact can be a chain on the same model. |
| D2 | Section A has no height dimension. Grade and the walking surface are levels. No chain is supplied for the section. | A | Limits sheet 7 | Height is readable only by the datum notes on the elevations. | One-model. |
| D3 | Guard height, baluster spacing, and the stair-opening width are in the geometry and are not dimensioned. | A | Limits sheets 3, 4, and 5 | The carpenter would scale the sheet. | One-model. |
| D4 | Only post-1 to beam-front has a bearing surface and a connector. Posts 2, 3, and 4 are `supports` only. Pier-to-post bearing is not supplied. Beam-to-joist connections are not supplied. | A | Blocks a crew set | Three posts have no shown connection. | Bearing fidelity stays met for the one supplied post bearing. The missing ones are absent facts. |
| D5 | Stair upper connection, lower bearing, landing, and stair guard are not in the fixture. The model can store members, relationships, and connections. | A | Limits the stair | The stair sheet cannot be built from at the top and bottom. | No-guessing. These are not invented. |
| D6 | The gate connection is absent. The detail names it. Also absent: a bottom rail, guard posts, a hinge, and a latch. | A | Blocks sheet 10 | Correct refusal. Not a drawing to build the gate from. | No-guessing. |
| D7 | Blocking and a ledger are not in the fixture. The model can store those members and connections. | A | Blocks a crew set | The framing plan is not a complete frame. | One-model. |
| D8 | Connector geometry is not supplied for the post cap or the tread clip. | A | Limits sheets 8 and 9 | The note is truthful. It is not a connector drawing. | Bearing fidelity. Geometry appears only when supplied. |
| D9 | A stair result has no riser-count field. The stored keys are rise, run, throat, nosing, stringer count, tread count, and stair width. | B | Limits the stair profile in the drawing standard | The carpenter can count the drawn risers. The model cannot store the count as a stair fact. | One-model. |
| D10 | A section location and a detail definition are not drawn back onto the plans. There is no cut mark and no “see sheet” reference. | C | Blocks a crew set | The carpenter cannot find section A or the details from the plan. | One-model. A view is a camera, and the other sheets do not show that camera. |
| D11 | Connection geometry fields can be stored. The sheet does not draw a bracket, a bolt diameter, or fastener locations. The schedule can only change the words to “geometry supplied”. | C | Blocks buildable connection details | Supplying geometry later would not yet produce a connector drawing. | Bearing fidelity. The row is met today because no geometry was invented. The next drawing of a supplied connector is still missing. |
| D12 | Callouts are corner lists. One leader is typical. Individual piers, joists, and balusters are not identified at the member. | D | Limits sheets 1 through 5 | The carpenter cannot match the list to the line without counting. | One-model. The names exist. The sheet does not place them. |
| D13 | The relationship schedule prints `bearing not supplied` on `supports` rows and `bearing supplied` on `bears_on` rows for the same roles. | D | Blocks use of the schedule | The schedule contradicts the stair and the post detail. | Bearing fidelity. The drawings are faithful. The schedule wording is not. |
| D14 | Schedule columns do not align. Later pages have no column headings. Sheet 13 contains one chain line. Grade and walking chains print as empty headings. | D | Blocks use of the schedule | A crew will not use sheets 11–13 as issued. | One-model. The rows match the model. The page does not. |
| D15 | A missing detail connection is named, and the 13-sheet set is still issued. | D | Keeps the set from meeting the drawing law | The refusal sentence is correct. The drawing law says a missing required fact means there is no PDF. | No-guessing stays PARTIAL. |

## V1 acceptance impact

One-model stays **PARTIAL**. The views that exist consume one model and do not contradict its geometry. Plans do not show the section camera or the detail cameras. A missing fact does not withhold the set.

No-guessing stays **PARTIAL**. The guard refusal is legitimate. Connector shapes are not invented. The set is still issued around that refusal.

Bearing / relationship fidelity stays **COMPLETE** for the criteria on that row. The stringer seat is a physical bearing. The post contact is the supplied 3 inch line. A contradictory bearing is refused. This audit does not reopen that row and does not rescore V1.

The Construction Model and Drawing Set stays **OPEN / NOT COMPLETE**.

## Recommended next build slices

Do these in order. Do not add fixture geometry in the same slice as a sheet-engine change.

1. Sheet presentation of facts already in the model. Align the schedule. Keep column headings. Do not leave a one-line sheet. Make a relationship row state one bearing answer for the assembly. Place callouts on the members they name.
2. Plan references. Draw the section cut and the detail references from the view definitions that already exist.
3. Draw connection geometry when the model supplies a bracket, a bolt diameter, or fastener locations. Continue to draw nothing when only a product name is present.
4. After those engines exist, supply the missing fixture facts: the guard connection, the other post bearings, the stair connections, blocking, a ledger, and the missing dimension chains. Keep the guard refusal until the connection is actually supplied.

## Tests at this audit

No product code changed. Construction Model regression: 120 passed, 10 warnings, 3.39s. PGE regression: 61 passed, 79 warnings, 19.01s. Full suite `./venv/bin/python -m pytest -q`: 2087 passed, 6789 warnings, 889.20s, exit 0.
