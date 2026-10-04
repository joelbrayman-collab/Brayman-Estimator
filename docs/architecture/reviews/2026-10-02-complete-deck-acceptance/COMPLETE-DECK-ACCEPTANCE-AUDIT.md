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

## Slice 13 disposition — 2 Oct 2026

Slice 13 presents facts the model and the view definitions already held. It does not add fixture geometry. It does not close this drawing set. V1 is not rescored. One-model and no-guessing stay **PARTIAL**. Bearing fidelity stays **COMPLETE** for its recorded criteria.

| ID | Slice 13 result |
|----|-----------------|
| D10 | Addressed for the views that exist. Plans draw the section cut from the section request and name that section’s sheet. Plans and elevations draw a detail reference when the detail’s members are in the view. The sheet number comes from the composed set. |
| D12 | Addressed for grouped members. One callout per construction class names the member ids, and a paper-space leader goes to a point on those members. A leader that would cross another leader is omitted. Elevations remain crowded. |
| D13 | Addressed. Each member pair has one bearing state. Post-1 to beam-front is supplied, with the 3 inch contact. Other pairs that have no bearing surface say bearing not supplied. |
| D14 | Addressed for column alignment and repeated headings. Schedule columns are drawn at fixed positions. A continued section repeats its heading. The schedule is not a price. |
| D15 | Distinguished, not hidden. The guard-and-gate sheet still names the missing connection and is marked NOT ISSUED. The set is still produced. The drawing law’s “no PDF” sentence is not met. |
| D1–D9, D11 | Open at the close of Slice 13. No new fixture facts then. No connector drawing then. No new stair field. |

## Slice 14 disposition — 2 Oct 2026

Slice 14 draws connector geometry only when the model supplies it. V1 is not rescored. One-model and no-guessing stay **PARTIAL**. Bearing fidelity stays **COMPLETE** for its recorded criteria.

| ID | Slice 14 result |
|----|-----------------|
| D11 | Addressed for supplied geometry. The fixture post cap is a generic plate on `rel-bear-post-1-beam-front`, with a 3 inch width, a 1/4 inch thickness, a 1/2 inch bolt diameter, and two fastener locations. The post-and-beam detail and section A project those same coordinates. The fixture tread clip remains metadata only and gains no shape. A product name does not become a connector. |
| D1–D9, D15 | Open. Missing dimension chains, missing members and connections, and the missing guard connection stay unnamed facts. The guard sheet stays NOT ISSUED. The set is still produced. |

Would we hand this to the crew? No. Would the post-and-beam drawing tell a carpenter what that connector is? Yes, for the supplied plate and the two bolt locations. Would the stringer drawing tell a carpenter what the tread clip is? No — geometry not supplied. That is the correct result.

The inspected set is 14 sheets. The fourteenth is the drawing index. Guard and gate is NOT ISSUED. The other sheets are GENERATED. Would we hand this to the crew? No.

## Slice 15 disposition — 2 Oct 2026

Slice 15 puts explicit fixture facts on the same complete-deck model and stores a stair riser count on the stair result. The values are fixture input. They are not Calibrayt defaults, organization defaults, Bushel values, or construction rules. Provenance stays `instance_configuration` with reference `COMPLETE DECK DRAWING ENGINE FIXTURE`, except the stair result, which stays `governed_calculation_result` with reference `COMPLETE DECK DRAWING ENGINE FIXTURE stair result`. V1 is not rescored. One-model and no-guessing stay **PARTIAL**. Bearing fidelity stays **COMPLETE** for its recorded criteria. The drawing set stays **OPEN / NOT COMPLETE**.

| ID | Slice 15 result |
|----|-----------------|
| D1 | Partly satisfied by fixture data. Front-to-back pier spacing is the chain `pier-spacing-y`, pier-1 to pier-3, and the foundation plan prints PIER SPACING 8'-0". Pier depth is the chain `pier-depth`, the length of pier-1, 4'-0". That chain is on the schedule. The front elevation and the section have no clear place for a second height chain, so the sheet refuses to draw it there. The depth was not typed into the PDF. |
| D2 | Partly satisfied by fixture data. Section A prints SECTION HEIGHT 3'-6", the chain from pier-1 at grade to deck-3. The section also shows the pier, the post, the beam, the joist, and the decking in that cut. Pier depth is not on this sheet. |
| D3 | Partly satisfied by fixture data. The side elevation prints GUARD HEIGHT 3'-0", the length of baluster-1. The framing plan prints STAIR OPENING 3'-0", the length of header-stair. Baluster spacing is the chain from baluster-1 to baluster-2, 0'-5", on the schedule. The decking plan and the front elevation have no clear place for that chain. |
| D4 | Partly satisfied by fixture data. Posts 1 through 4 and piers 1 through 4 each have an explicit `bears_on` record, a 3 inch contact, bearing depth 0, and fixture provenance. The beam-to-joist connection is metadata only: fixture joist hanger, fixture nail, quantity 4. No hanger shape was invented. |
| D5 | Partly satisfied by fixture data. The header-to-stringer connection is metadata only: fixture stair hanger. A `fastened_to` record names header-stair and stringer-2. No landing, no stair guard, and no lower bearing member were added. |
| D6 | Partly satisfied by fixture data. The guard-and-gate connection is metadata only: fixture gate latch, fixture screw, quantity 2. The sheet is GENERATED and says GEOMETRY NOT SUPPLIED. No hinge shape, no bottom rail, and no guard posts were added. |
| D7 | Open. Blocking and a ledger are not in the fixture. A ledger would require a wall this fixture does not have. |
| D8 | Unchanged from Slice 14. The post cap still has geometry. The tread clip stays metadata only. |
| D9 | Implemented. A stair result can store `riser_count`. The fixture stores 6. The stair sheet and the stringer detail print `riser count 6`. The drawing does not calculate the count. Removing the field refuses the stair view. Restoring it generates the view again. |
| D15 | The guard sheet is no longer NOT ISSUED, because the connection is now supplied as metadata. The set no longer contains the refusal sentence. That does not make the set a crew set. |

The inspected set is 15 sheets. The fifteenth is the drawing index. Every sheet is GENERATED. Front-to-back pier spacing, the stair opening, the guard height, and the section height are on the drawings. Pier depth and baluster spacing are on the schedule. Connector notes still collide with the framing and the elevations. The post-and-beam detail shows the supplied plate. The guard detail shows rails and balusters and names the latch without drawing one. The stair note says riser count 6 and the picture shows the five supplied treads on the stringer. Would we hand this to the crew? No.

## Slice 16 disposition — 3 Oct 2026

CONSTRUCTION MODEL + DRAWING ANNOTATION LAYOUT: **IMPLEMENTED / TESTED**.

Annotations move in paper space. Member coordinates, relationships, dimension values, and levels do not move. No ledger, landing, stair guard, hinge, bottom rail, guard post, or commercial connector was added. V1 is not rescored. One-model and no-guessing stay **PARTIAL**. Bearing fidelity stays **COMPLETE** for its recorded criteria. The drawing set stays **OPEN / NOT COMPLETE**.

Connector text is no longer drawn on the member. A supplied plate keeps its geometry, and the width, thickness, and bolt note sits beside it. A metadata-only connector stays a note that says GEOMETRY NOT SUPPLIED, with the member ids. Equivalent notes group. Different connectors do not. A leader that would cut through another member is not used, even when that path is shorter. When no clean route exists, the note stays and the leader is omitted. Pier depth 4'-0" now prints on the side elevation, and baluster spacing 0'-5" prints on the front elevation. Those values were already in the model. The dimension text was not retyped.

The inspected set is 15 sheets. Connector notes sit in the open margin. The framing plan keeps the joists, the beams, and the dimension chain readable, with the plate note and the hanger notes at the right. The front elevation keeps the baluster spacing and the member labels off the railing. The side elevation keeps pier depth and guard height off the posts, and the level names stay in the gaps between the connector notes. The stair sheet keeps rise, run, and the riser count off the stringer. The post-and-beam detail keeps the supplied plate and the two bolt marks visible, with the plate note beside them. Section A keeps the section height and the connector notes off the posts and the beam. A leader that would run along a member is omitted. The note stays, with the member ids. Bearing words still sit at the post-to-beam joint. Would we hand the whole set to the crew? No. Missing construction is still missing.

## Slice 17 disposition — 3 Oct 2026

CONSTRUCTION MODEL + BLOCKING: **IMPLEMENTED / TESTED**.

The fixture supplies 18 blocking members. Each is a 2x8 of the fixture joist stock, at the joist elevation, between the joist and rim lines this fixture already places, on the two beam stations this fixture already places. Provenance is `instance_configuration` / `COMPLETE DECK DRAWING ENGINE FIXTURE`. Each piece has an explicit `fastened_to` relationship to the two members it spans. The engine does not insert a piece the fixture omits. No blocking dimension was added. No ledger, landing, stair guard, hinge, bottom rail, guard post, or connector shape was added. V1 is not rescored. One-model and no-guessing stay **PARTIAL**. Bearing fidelity stays **COMPLETE** for its recorded criteria. The drawing set stays **OPEN / NOT COMPLETE**.

| ID | Slice 17 result |
|----|-----------------|
| D7 | Blocking is in the fixture. The framing plan draws both rows and names blocking-1 through blocking-18. Section A cuts the front beam, so it draws blocking-1 through blocking-9 and does not draw the back row. The member schedule groups the 18 pieces as one 2x8 row, length 1'-4". The relationship schedule records blocking fastened to joist (32) and blocking fastened to rim (4). A ledger remains absent. This fixture has no wall to receive one. |
| D5, D6, D8 | Unchanged. Landing, stair guard, hinge, bottom rail, guard posts, tread-clip geometry, joist-hanger geometry, stair-hanger geometry, and latch geometry stay unsupplied. The sheets still say GEOMETRY NOT SUPPLIED for those connectors. |
| Bearing label | Open. The words BEARING 0'-3" still sit on the post-to-beam contact. |

Remaining deficiencies after this slice:

| Item | Class | Disposition |
|------|-------|-------------|
| Ledger | E | This deck stands on four posts. A ledger needs a wall the fixture does not have. |
| Landing | A | The model can store a member. The fixture does not supply a landing. |
| Stair guard | A | The guard role exists. The fixture does not supply a stair guard. |
| Hinges | A | No hinge fact is supplied. |
| Bottom rail | A | No bottom-rail member is supplied. |
| Guard posts | A | No guard-post member is supplied. |
| Tread clip geometry | A | The connection is metadata. The shape is not supplied. |
| Joist hanger geometry | A | The connection is metadata. The shape is not supplied. |
| Stair hanger geometry | A | The connection is metadata. The shape is not supplied. |
| Latch geometry | A | The connection is metadata. The shape is not supplied. |
| Bearing words on the joint | D | The bearing is in the model. The sheet still prints the words on the contact. |

The inspected set is 15 sheets. The framing plan shows the blocking as short marks on the two beam lines, with one note for all 18 pieces. Section A shows the front row as the boards between the joists, above the beam. The back row is on the plan and the schedule, and it is outside this section cut. The member schedule and the relationship schedule name the same pieces. Elevations, the stair, and the three details do not invent blocking. Connector notes stay in the margin. GEOMETRY NOT SUPPLIED stays on the latch, the hangers, and the tread clip. Would we hand this to the crew? No. The blocking is readable. The missing ledger, landing, stair guard, and connector shapes are still missing, and the bearing words still sit on the joint.

## Slice 18 disposition — 3 Oct 2026

CONSTRUCTION MODEL + BEARING ANNOTATION: **IMPLEMENTED / TESTED**.

The bearing words moved in paper space. The contact line stayed on the relationship. No fixture construction data was added. V1 is not rescored. One-model and no-guessing stay **PARTIAL**. Bearing fidelity stays **COMPLETE** for its recorded criteria. The drawing set stays **OPEN / NOT COMPLETE**. No new generic capability is required before the real Bushel model is put through this engine.

| Item | Slice 18 result |
|------|-----------------|
| Bearing words on the joint | Closed as a sheet defect. The post-and-beam detail prints `BEARING 0'-3"`, `post-1 bears on beam-front`, and `rel-bear-post-1-beam-front` in the margin. The 3 inch contact and the two bolt marks stay on the joint. Section A prints the same value for post-1 and post-2 on beam-front, and for pier-1 and pier-2 on the posts, off the members. The stair seats are clear. One note names the 0'-11" bearings and every relationship id. A single bearing may take a leader. A group does not point at one seat. A leader that would cross an unrelated member is omitted. |
| Ledger, landing, stair guard, hinges, bottom rail, guard posts, tread-clip geometry, joist-hanger geometry, stair-hanger geometry, latch geometry | Unchanged fixture inputs. The sheets still say GEOMETRY NOT SUPPLIED where a connection exists and the shape does not. |

Visual reassessment of all 15 sheets. This is a quality reading, not a new feature list.

| Sheet | Could a carpenter use it without guessing what the drawing means? |
|-------|-------------------------------------------------------------------|
| Foundation plan | Yes, for the four piers and the two spacing chains. The sheet is sparse because the scale is 1/2 in = 1 ft. |
| Framing plan | Yes, for the frame that is in the model: joists, beams, posts, rims, header, blocking, stair opening, and the dimension chains. Connector notes sit in the margin. Hanger shapes are not supplied. |
| Decking, guard, and gate | Yes, for the boards, the rails, the balusters, the gate, and the opening. The latch shape is not supplied. |
| Front elevation | Yes, for the posts, the beams, the guard, grade, the walking surface, and baluster spacing. Member labels sit in the open bay. They do not cover the bearing. |
| Side elevation | Yes, for the same stack plus the stair, pier depth, and guard height. Connector notes stay in the margin. |
| Stair | Yes, for the stringers, the treads, the seats, rise, run, and riser count 6. The bearing value is one note. There is no landing and no stair guard in the model. |
| Section A | Yes, for the cut at the front beam: posts, beam, joists, blocking, decking, piers, and section height. The bearing notes name the relationships. |
| Post and beam | Yes, for the supplied contact, the plate, and the two bolts. The bearing words are off the joint. The joist hanger on this sheet is metadata only. |
| Stringer and tread | Yes, for the seat and the 0'-11" bearing. The tread clip stays GEOMETRY NOT SUPPLIED. |
| Guard and gate | Yes, for the rails and balusters that exist. The latch is named and not drawn. |
| Schedules and index | The rows match the model. They are not a price. The index lists the 15 sheets. |

Engine deficiencies versus fixture inputs:

| Question | Answer |
|----------|--------|
| Genuine engine deficiency left? | No construction-fact gap. Elevation callouts are still dense, and a leader is omitted when every route would cross another member. Those are presentation limits of the paper-space rules already in force. |
| Missing fixture inputs? | Ledger, landing, stair guard, hinges, bottom rail, guard posts, and the four connector shapes. |
| Acceptable unresolved content? | Yes. GEOMETRY NOT SUPPLIED is the governed sentence. The renderer does not invent the shape. |
| What still blocks a crew set? | The missing project facts above. A carpenter cannot build a latch, a landing, or a ledger from a sheet that truthfully says those facts were not supplied. |
| Another generic engine slice? | No. The engine can store a member, a relationship, a bearing, and connector geometry when a project supplies them. |

Would we hand this generic set to the crew? No. The drawing engine is ready to accept the real Bushel model as a proving pass. Bushel facts that are absent stay refused. They are not filled in from this fixture.

## Slice 19 disposition — 3 Oct 2026

The Bushel proving fixture was read by this engine. No Bushel value was added to the engine. No generic fixture value was copied into the Bushel model. The review is [../2026-10-03-bushel-construction-model/BUSHEL-REAL-WORLD-PROVING.md](../2026-10-03-bushel-construction-model/BUSHEL-REAL-WORLD-PROVING.md).

Missing Bushel elevations, lengths, and stair facts refuse. None of those gaps is an engine deficiency. An unprojected stair is named on the compose result and is not given a drawing-index line. That is a presentation gap. It does not require a Bushel-specific drawing path. The drawing set stays **OPEN / NOT COMPLETE**. V1 is not rescored.

## Slice 20 disposition — 4 Oct 2026

No new generic drawing feature. The 1 Oct governed decisions were already in the proving fixture. Nominal sizes, beam coordinates, and the pool curve stay in the 29 Sep brief and were not loaded. Regeneration matched the Slice 19 PDF. The input matrix is in [../2026-10-03-bushel-construction-model/BUSHEL-REAL-WORLD-PROVING.md](../2026-10-03-bushel-construction-model/BUSHEL-REAL-WORLD-PROVING.md).
