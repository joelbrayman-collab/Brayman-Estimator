# Construction drawing standard

| Attribute | Value |
|-----------|--------|
| Status | Recorded product requirement. PGE-1 through PGE-6 remain closed and unchanged. Construction Model completeness, view projection, the governed 11×17 sheet, stair, section, detail, and schedule views, and the Bushel proving slice are **IMPLEMENTED / TESTED**. Construction Model and Drawing Set remains **NOT COMPLETE**. Productization plan: [plan-generation-engine-productization.md](plan-generation-engine-productization.md). Register: [PLATFORM_BUILD_OUT_REGISTER.md](PLATFORM_BUILD_OUT_REGISTER.md). |
| Date | 2026-09-29. Architecture accepted 1 Oct 2026. This file remains the drawing authority. |
| Authority | Joel’s visual standard for CalibraytAI construction drawings. The 1 Oct 2026 Construction Drawing Engine investigation is accepted. Presentation identity is [governed-document-and-drawing-output-standard.md](governed-document-and-drawing-output-standard.md). Engine slices are [plan-generation-engine-productization.md](plan-generation-engine-productization.md). |

## Drawing law

A CalibraytAI construction drawing is a dimensioned geometric representation of the actual structure.

Notes may supplement the geometry. Notes do not substitute for geometry.

The framing plan itself has to show where the structure goes and how the members relate: footprint, each joist, joist direction and spacing, beams, blocking, posts, piers, rims and headers, stairs, landings, callouts, and dimension chains. A carpenter must be able to read those from the sheet without scaling the PDF.

An explanatory member view, of the kind that names a joist, beam, post, and footing on a cutaway, may supplement a set. It is not the framing plan.

## Accepted architecture — 1 Oct 2026

The Construction Drawing Engine investigation of 1 Oct 2026 is accepted. This file remains the single drawing authority. Construction Model completeness, view projection, the governed 11×17 sheet, stair, section, detail, and schedule views, and the Bushel proving slice are **IMPLEMENTED / TESTED**. Code: `app/services/construction_model/`. The proving fixture is `tests/fixtures/construction_model/bushel_proving_fixture.py`. It is labeled BUSHEL PROVING FIXTURE and is not an engine default. Plan, front elevation, side elevation, stair, section, and detail are projections of that one model. Schedules read the same model. The sheet layer composes them at the stated scale and adds a sheet when one page cannot hold the next extra view. The sheet does not scale the drawing to fill the paper. Geometry that does not fit at that scale is refused. A stair fact that is not already supplied is refused. The assessment, the projection, and the sheet write no project, plan, or estimate. The 2 Oct 2026 proving slices did not pass the printed-sheet acceptance test. Construction Model and Drawing Set remains **NOT COMPLETE**.

```text
Calibrayt Construction Model
→ view definitions
→ drawing engine
→ governed 11×17 sheet layer
→ print-ready construction set
```

The Construction Model is the model of record for drawing geometry. The drawing engine projects that model. The sheet layer composes the views. The printed 11×17 sheet is the acceptance standard. The drawing technology is subordinate to that printed result.

The model holds, where the work requires them, geometry, members, supports, relationships, connections, openings, materials, dimensions, levels, elevations, constraints, uncertainty, assumptions, and project document status. A calculation engine may supply a governed domain result. A person may supply a project fact. The model stores the governed value. It does not invent one.

One model produces the plan, the front elevation, the side elevation, sections, details, dimensions, callouts, and schedules. A view is a projection of the model. It does not carry its own geometry. A change in the model regenerates every affected view. A view does not contain a member the model lacks, and it does not contradict the model.

A missing required construction fact is asked for in plain language: “You need to provide this information.” The person supplies the fact. The model validates. Drawing generation stays closed while a required fact is unresolved. The system does not issue a partial set that looks complete. Supplied uncertainty stays visible. Using a drawing does not clear it.

The first proving set, from one model, is the foundation and pier plan, the framing plan, the decking, guard, and gate plan, the front elevation, the side elevation, the stair detail, the typical details, the dimensions, and the schedules. Pier count, joist count, stringer count, levels, and stair geometry agree in every view that shows them.

## Bushel proving slice — 2 Oct 2026

The proving slice is **IMPLEMENTED / TESTED**. It is not a close of this component.

The fixture uses the 1 Oct 2026 decisions: 15 helical pier locations from the CT-1 coordinates, 16 joist stations and 10 stringer stations from the selected layouts, a 5.00 in stringer throat, a 12 in lower-deck walking surface, 12 D'Arcy's Way, two 5/4 × 6 boards per tread, the 37 in Veranda kit, and a 42 in clear gate. Shaft length, helix, torque, bracket height, lower post cut, baluster layout, stringer plumb cuts, upper-deck elevation, stair rise, stair run, nosing, and tread count are withheld. The fixture does not invent them.

Slice 6 stores a known plan station without an elevation. The plan can draw that station. An elevation, section, or stair that needs the missing elevation refuses that member and names it. A view that does not fit the principal viewport moves to another 11×17 sheet at the same scale. Dimensions print in construction notation. A level is a datum.

Slice 7 adds paper-space callouts, dimension chains, and required-view placement. A callout names the model elements it refers to. Moving it does not move those elements. Members that land on the same or a nearby paper point stay on their coordinates and share one callout. The same missing fact is one note, and the note keeps the member ids. A dimension chain reads coordinates from the model. A missing station refuses that dimension. A level dimension uses the model level, so the displayed value changes when the level changes. A required view that fits another 11×17 sheet is placed there. A required view that fits no sheet returns `VIEW_CANNOT_BE_PLACED_AT_REQUESTED_SCALE` and “You need to provide a different sheet arrangement or scale.” The scale is not changed.

Slice 8 is the deck component model. A member can be a joist, beam, rim, header, stringer, tread, decking, guard, baluster, gate, or post. A support can be a pier or a footing. Geometry, elevation, length, member size, orientation, material, and construction status are stored only when supplied. A pier does not need a shaft length to appear on the plan. A view that needs a missing axis or a missing requested fact still refuses that part. A segment with two fully known endpoints receives a derived length and records that the length came from those endpoints. A supplied length that disagrees with those endpoints is a conflict. A length alone does not create the missing endpoint. Relationships are `supports` or `protects` and are stored only when supplied. A connection can name its type, connector, fastener, and quantity only when those are supplied.

Plan needs x and y. Front elevation needs x and z. Side elevation needs y and z. A section needs the cut axis and the projected axes. The stair view needs y and z for its named members and uses the supplied stair result without calculating rise, run, nosing, tread count, throat, stringer count, or width. The schedule shows a supplied or endpoint-derived length and does not invent one. A detail asks only for the requirement it names.

Slice 9 draws a complete generic deck from one model. The fixture is named COMPLETE DECK DRAWING ENGINE FIXTURE. Its values are fixture input. They are not Calibrayt defaults and they are not Bushel. A sheet program asks for a foundation plan, a framing plan, a decking plan, elevations, a stair, a section, details, and schedules. Each sheet filters that same model. The scale is the scale named for that sheet. It is not fitted to the paper.

Slice 10 draws a supplied rectangular profile, including a sloped member, and groups construction schedules from that same model. A 2×12 stringer with a top edge and a section depth is the board, not only its centerline. A tread with a supplied thickness is a ribbon. A detail may name an extent, which is the camera window around the members. It is not new geometry. If the window cannot fit at the named scale, the detail is refused. Equivalent members group by role, size, material, profile, length class, and status. Different lengths stay different rows. Connections and materials are schedules of the model. They are not a price.

Slice 11 stores construction relationships on that same model. A relationship is `supports`, `protects`, `bears_on`, `connects_to`, or `fastened_to`, and only when it is supplied. It names the two members, and it may carry provenance, uncertainty, a bearing surface, a bearing location, a bearing depth, and other relative geometry. Proximity does not create a relationship. A declared bearing whose points are not on both members, or whose depth exceeds the supplied depth, is `CONFLICTING_GEOMETRY`. The members are not moved and the coordinates are not repaired. A detail may name a relationship. It still does not own members. The section and the stair draw the bearing lines that belong to members in that view. A connection may carry connector geometry, fastener locations, bolt diameter, bolt count, and bracket size only when those are supplied. A product name does not become a shape. The schedule can say whether a bearing was supplied and whether a connection has geometry or metadata only. It is not a price.

The complete-fixture sheets were inspected again at 11×17. The stair shows the stringer notched for the supplied seats, with the treads sitting on those seats. The stringer detail shows one seat and the tread on it, labeled with the supplied 11 inch bearing. The post-and-beam detail shows the beam on the post and the supplied 3 inch bearing. The connector remains the supplied note, because no connector geometry was supplied. Section A names the same chain for the members in that cut: pier supports post, post bears on beam, beam supports joist, joist supports decking. The stair is not in that cut, so the stringer and tread stay on the stair and the stringer detail. The gate connection is still absent. Visual acceptance of the whole set for handing it to a carpenter is not passed. The stringer/tread and post/beam assemblies on this fixture are readable. Bushel is not the acceptance fixture.

Slice 12 audits that same fixture. The deficiency list is [reviews/2026-10-02-complete-deck-acceptance/COMPLETE-DECK-ACCEPTANCE-AUDIT.md](reviews/2026-10-02-complete-deck-acceptance/COMPLETE-DECK-ACCEPTANCE-AUDIT.md).

Slice 13 presents facts that model and those view definitions already hold. A callout names the member ids in one construction class. Equivalent members share one callout and stay traceable to those ids. A leader stays in paper space and is omitted when it would cross another leader. A plan shows a section cut from the section request: the section id, the direction, the location, the cut depth when it was supplied, and the sheet number of that section. A plan or elevation shows a detail reference when the detail’s members are in the view. The reference carries the detail id, the detail title, and the destination sheet. Those sheet numbers come from the composed set. Changing the first sheet number changes the references. The last sheet is a drawing index of the same pages: number, title, status, and scale. A detail that requires a connection and has none is marked NOT ISSUED. The missing connection is not invented. Schedules use fixed columns. A continued section repeats its heading. A relationship row states one bearing for each member pair. A missing bearing is named on that pair. The schedule is not a price and not a take-off. No separate annotation, schedule, or reference store is kept. The set is not a crew set.

Slice 14 draws a connector only from geometry the model supplies. The geometry stays on the connection and names the relationship it serves. A connector name, a fastener, and a quantity do not create a shape, a bolt circle, or a spacing. Where a plate, a thickness, a bolt diameter, or fastener locations are supplied, the detail and the section project those same coordinates. The schedule says geometry supplied or metadata only. It is not a price. The fixture post cap is generic test geometry. The fixture tread clip remains metadata only. The set is not a crew set.

The proving sheets are still not acceptable construction drawings.

Remaining deficiencies:

- Joist and stringer stations are points on the front edge. Their lengths, cuts, and elevations are still unknown.
- The proving fixture records post, beam, guard, and gate as unsupplied component slots. It does not give them locations, sizes, or cuts.
- Pier shaft length, helix, torque, bracket height, and baluster layout are still absent.
- The stair result still has no rise, run, nosing, or tread count.
- Some front-elevation leaders still reach the pier line.
- On the complete fixture, the stringer detail shows the tread on the supplied seat. The slice 12 audit is the current deficiency list. The set is still not a crew set.
- The post cap and the tread clip are notes. The model has no connector shape.
- The guard and gate sheet shows the rails, the gate, and the balusters. The model has no gate connection. The sheet says that connection is not supplied.
- The section end rims are the end view of the rim at the deck edge. The section has no height dimension.
- The second schedule sheet is the dimension-chain listing and is sparse.

The printed sheet is judged for geometric consistency, structural consistency, dimensional consistency, quantity consistency, revision consistency, and print consistency.

FreeCAD is not adopted for the first implementation. Blender is not integrated. OCCT, CadQuery, and build123d are not the first implementation. A geometric kernel may be evaluated later only when a real native projection cannot be satisfied. If a kernel is introduced, it stays replaceable, it runs out of process, and it is not the Construction Model.

PGE-1 through PGE-6 stay closed. `dimensioned_plan`, `stair_detail`, Contract V1, the candidate and use boundary, Build Drawings, and the drawing requirement are unchanged. This capability sits beside those slices.

Linda Bushel remains a proving fixture. Its scripts are not the engine. Its pool radius, pier count, joist count, stringer count, spans, and other job dimensions are not generic constants. Issue J1 sheet 5, drawn 1 Oct 2026, is rejected as a construction drawing. It invented view geometry the model did not contain. It is not redrawn in the case script. The future engine regenerates the required views from one model.

The model may later become the quantity source. The first construction-model slice does not implement drawing-driven take-off. Current Bushel quantities stay as they are.

The red-box screen is not part of the first slice. The model and the refusal come first. Project UI and Guided Project Setup may consume that refusal later.

A generic Plan Generation artifact may keep the line “Not a permit. Not a seal.” A project construction drawing carries its governed document status, such as “PRELIMINARY CONSTRUCTION DRAWING — SUBJECT TO PERMIT REVIEW AND FIELD VERIFICATION” or “CONSTRUCTION DRAWING — ISSUED FOR PERMIT”. That status does not certify engineering, does not represent a professional seal, does not claim municipal approval, and does not claim that a permit has been issued.

## Elevations

The same geometry that draws the framing plan is the source for every elevation and every section. A filled block is not an elevation. Linda Bushel issue J1, sheet 5, drawn 1 Oct 2026, is rejected. It is a picture. It invented posts, baluster spacing, and a helical pier the model did not define, and it drew the lower frame as if it fit a walking surface it does not fit. It is not redrawn by hand in the case script. The future set comes from one model.

## Crew drawing — Joel, 1 Oct 2026

A drawing handed to the crew, and taken to the municipal office, is a professional construction drawing. It is accurate, it is clear, and it looks right printed on 11×17.

The path is fixed:

1. The platform asks for each missing fact in plain language: “You need to provide this information.” One fact, one box. Nothing is guessed.
2. There is one model. Every plan, section, elevation, and angle is drawn from that data. These are construction drawings, not pictures.
3. A sheet is printed only after the required boxes are clear. A missing required fact means there is no PDF.
4. The pen runs only after that information is in. The standard is the printed sheet. The tool that draws it is not a second authority.

A generic Plan Generation artifact may keep “Not a permit. Not a seal.” A project construction drawing uses its governed document status instead of treating that generic line as the project status. The project status does not certify engineering, represent a professional seal, claim municipal approval, or claim that a permit has been issued. Supplied uncertainty stays visible. Using the sheet does not clear it.

Construction Model completeness, view projection, the governed 11×17 sheet, partial spatial facts, sheet sets, paper-space callouts, dimension chains, required-view placement, the deck component model, the complete deck fixture, stair, section, detail, and schedule views, and the Bushel proving slice are **IMPLEMENTED / TESTED**. Visual acceptance of a crew set is not passed. The complete-fixture review is [reviews/2026-10-02-complete-deck/COMPLETE-DECK-DRAWING-REVIEW.md](reviews/2026-10-02-complete-deck/COMPLETE-DECK-DRAWING-REVIEW.md). The sheet uses the stated scale and does not scale the drawing to fill the paper. A view that misses the principal viewport moves to another 11×17 sheet. A required view that misses a full sheet is refused. It is not omitted. PGE-2 and PGE-3 render the validated request they are given. They do not project this construction model. The stair view consumes a supplied stair result. It does not calculate rise, run, throat, nosing, stringer count, tread count, or stair width. The Bushel proving review is [reviews/2026-10-02-bushel-proving/BUSHEL-CONSTRUCTION-MODEL-REVIEW.md](reviews/2026-10-02-bushel-proving/BUSHEL-CONSTRUCTION-MODEL-REVIEW.md).

The stair side profile is drawn. It uses the same rise, run, stringer spacing, and landing as the framing plan. The first proof is CT-2. The refinement is CT-2 R2. R2 draws the tread running under the riser, with a 3/4 in nosing past the riser face. The finished 11 in going and 7.60 in rise stay. The sheet shows one measurement system, imperial. It does not add a second stair calculator. Neither sheet is a general elevation generator.

## Drawing completeness

A construction detail is not complete merely because its geometry is drawn.

Each construction element needs a governed drawing-completeness profile:

geometry, the required dimensions, the required member callouts, the required connection information, the required guard information where a guard applies, and the field-verification items.

For a stair, the minimum profile is the rise, the run, the riser count, the tread count, the total rise, the total run, the stringer geometry, the stringer length, the width, the stringer spacing, the upper connection, the lower bearing, the landing, the riser, the nosing reveal, and the guard. This requirement is recorded from the Bushel stair. PGE-3 draws the supplied profile, stringer, and the supplied labels. Width, spacing, connections, landing, and guard are drawn only when a later geometry result supplies them.

## Calculation to drawing

Where a construction element has a calculated shape, the order is:

calculation, then governed geometry, then the construction drawing, then quantity evidence.

The drawing consumes that geometry. It does not invent a second shape for the same element.

A stair is the first proof. `stair_detail_r2.py` is project-specific proving geometry for Linda Bushel. It is not the reusable Stair Engine. The Stair Calculator source is recovered in the Useful Tools Site repository at `59e1979e735ec606af341e97e46e112136fbdfa0`. It is not checked out on this Mac and it is not authority inside this repository. It is not rebuilt from the Bushel sheet. A later engine must feed the drawing in this order:

stair engine, then stair geometry result, then plan generation, then the stair construction detail.

The same rule is recorded for other elements, and it is not implemented:

- a footing engine exposes footing geometry and quantities for the foundation drawing
- a stair engine exposes rise, run, and stringer geometry for the stair detail
- an ICF wall engine exposes wall and opening geometry for the wall drawing
- a slab engine exposes slab and edge geometry for the slab plan and section

## Drawing to take-off

The construction geometry is the authoritative evidence for material quantities.

Counts and lengths on the drawing are the counts and lengths in the take-off. A joist drawn on the plan is a joist in the take-off. A pier drawn on the plan is a pier in the take-off. A beam run drawn on the plan supplies that beam’s length.

The Bushel capability-test sheet does not rebuild the take-off. Issue P1 quantities stay as they are. The first construction-model slice does not implement drawing-driven take-off.

## What exists now

The Linda Bushel proof sheet is generated by ReportLab from calculated layout geometry:

`docs/estimating-cases/2026/linda-bushel-pool-deck/drawings/capability_test_plan.py`

That script writes the foundation and framing plan. The stair sheet is a second script, `drawings/stair_detail.py`, and it imports the framing-plan stair geometry rather than keeping a second rise or run. Both are project proofs. Neither is a platform drawing engine, and neither is wired to the take-off.

A reusable construction-drawing engine is in productization. PGE-2 draws a `dimensioned_plan`. PGE-3 draws a `stair_detail` from a supplied stair result and does not calculate the stair. The Bushel scripts remain case proofs. They are not imported by the renderer. This standard does not make that PDF a project drawing.

## Plan creation

Recorded product requirement. Not implemented.

At project intake the contractor says whether plans already exist. Plans that exist can be uploaded. For a bounded, straightforward project such as a deck, a small garage, or an addition, CalibraytAI may create controlled construction drawings. Those drawings go through review and approval before estimating and construction. The capability is not unrestricted engineering and it is not a professional seal or a municipal approval.

The Bushel sheets are the proving case for that later engine. They are not the engine.

## Presentation

Issued drawings use the governed document identity. That authority is [governed-document-and-drawing-output-standard.md](governed-document-and-drawing-output-standard.md). This section does not create a second branding source.

A governed sheet carries the organization identity and approved logo, the governed colours, a title block, the project identity, the customer or project name, the address, the date, the revision, the sheet number, the document status, the paper size, the scale, the origin where the drawing type uses one, and one measurement system. Typography and layout stay consistent. Field and permit notes may supplement the geometry. They do not replace it. The sheet is inspected visually before it is treated as complete.

Customer, internal, supplier, and field documents keep their own information boundaries. Branding does not move those boundaries. An internal sheet may carry cost. A customer sheet and a supplier sheet do not carry margin.

## Drawing engine

Plan Generation, PGE-1 through PGE-6, remains the closed request renderer. Those slices are unchanged. Construction Model completeness, view projection, and the governed 11×17 sheet are **IMPLEMENTED / TESTED** in `app/services/construction_model/`. The drawing set beside those slices is **NOT COMPLETE**. These rules are the cross-cutting authority. The implementation slices do not replace them.

1. Geometry is the source of truth. The engine renders governed geometry. It does not invent geometry.
2. Validation comes before rendering. Only an accepted drawing request is rendered. Invalid geometry produces no governed drawing.
3. The engine renders the members supplied on the request. It does not infer structural members.
4. The same accepted request produces the same governed drawing result.
5. The request sets paper, scale, and origin. The engine does not silently auto-fit or move geometry to improve appearance. Geometry that does not fit the sheet is refused.
6. Dimensions come from the supplied geometry. Labels do not change the geometry.
7. Uncertainty flags and assumption notes that were supplied stay visible. Using a drawing does not remove uncertainty.
8. Excluded geometry is distinguishable from construction members.
9. A generic Plan Generation artifact may carry “Not a permit. Not a seal.” A project construction drawing carries its governed document status. That status does not certify engineering, represent a professional seal, claim municipal approval, or claim that a permit has been issued.
10. The engine does not silently repair missing or contradictory geometry.
11. The engine does not invent spans, structural capacities, reinforcement, footing requirements, pier capacities, member sizes, code compliance, or engineering approvals. Those come from governed inputs or from the appropriate professional authority.
12. The engine does not own clients, projects, prices, estimates, labour rates, supplier pricing, permits, engineering seals, or workflow state.
13. The engine consumes a governed calculation result where one applies. It does not copy Website formulas. It does not recalculate a result that belongs to an authoritative calculation engine.
14. Where this architecture supports it, the drawing geometry is capable of being the source of a governed take-off. Geometry is not copied by hand from the drawing into a second quantity model.
15. Rendering a drawing does not create a `PlanDocument` and does not mutate a `Project`. PGE candidate and explicit use remain the boundary for that step.

## Bushel

Linda Bushel is a proving case. Its scripts are not the reusable Plan Generation Engine.

Pool radius, deck geometry, Option A framing, the pier layout, the stringer layout, and the dimensions of that job stay project-specific. They are not generic engine constants. The case may show a reusable principle. It does not set a universal structural rule.

## Plan Generation slices

These slices implement this standard. They do not replace it.

| Slice | What it is |
|-------|------------|
| PGE-1 | Drawing request and validation |
| PGE-2 | Dimensioned-plan render |
| PGE-3 | Stair-detail render |
| PGE-4 | Candidate persistence and explicit use |
| PGE-5 | Build Drawings on the existing plans page |
| PGE-6 | Drawing-requirement decision |

Code for validation and render: `app/services/plan_generation/validation.py` and `app/services/plan_generation/render.py`. Contract V1 stays pinned and is not a drawing layout. These slices stay closed. Construction Model and Drawing Set does not modify them.

## Calculation, drawing, and commerce

```text
calculation engine → governed domain result
construction model → spatial and structural representation
drawing engine → views of that model
sheet layer → governed 11×17 composition
estimate / mapper → commercial use after explicit review
cost / labour / pricing → company and supplier authority
```

Those layers stay separate.

## Quality gate

A reusable drawing component is not complete because a PDF exists. It is complete only when all of the following hold:

validated input, governed geometry, a deterministic render, visual inspection, the correct document status, governed branding, no invented structure, and no project mutation that the candidate-and-use boundary did not authorize.
