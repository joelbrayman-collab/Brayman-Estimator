# Construction drawing standard

| Attribute | Value |
|-----------|--------|
| Status | Recorded product requirement. PGE-1 through PGE-6 remain closed and unchanged. Construction Model completeness refusal is **IMPLEMENTED / TESTED** as a slice. Construction Model and Drawing Set remains **NOT COMPLETE**. Productization plan: [plan-generation-engine-productization.md](plan-generation-engine-productization.md). Register: [PLATFORM_BUILD_OUT_REGISTER.md](PLATFORM_BUILD_OUT_REGISTER.md). |
| Date | 2026-09-29. Architecture accepted 1 Oct 2026. This file remains the drawing authority. |
| Authority | Joel’s visual standard for CalibraytAI construction drawings. The 1 Oct 2026 Construction Drawing Engine investigation is accepted. Presentation identity is [governed-document-and-drawing-output-standard.md](governed-document-and-drawing-output-standard.md). Engine slices are [plan-generation-engine-productization.md](plan-generation-engine-productization.md). |

## Drawing law

A CalibraytAI construction drawing is a dimensioned geometric representation of the actual structure.

Notes may supplement the geometry. Notes do not substitute for geometry.

The framing plan itself has to show where the structure goes and how the members relate: footprint, each joist, joist direction and spacing, beams, blocking, posts, piers, rims and headers, stairs, landings, callouts, and dimension chains. A carpenter must be able to read those from the sheet without scaling the PDF.

An explanatory member view, of the kind that names a joist, beam, post, and footing on a cutaway, may supplement a set. It is not the framing plan.

## Accepted architecture — 1 Oct 2026

The Construction Drawing Engine investigation of 1 Oct 2026 is accepted. This file remains the single drawing authority. Construction Model completeness refusal is **IMPLEMENTED / TESTED**. Code: `app/services/construction_model/`. The assessment writes no project, plan, or estimate, and it emits no drawing. Construction Model and Drawing Set remains **NOT COMPLETE** until a Bushel-class set is generated from one model and passes the printed-sheet acceptance test.

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

Construction Model completeness refusal is **IMPLEMENTED / TESTED**. PGE-2 and PGE-3 render the validated request they are given. They do not yet project a construction set from one model. Views, sheet composition, and PDF generation for that set are not implemented.

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

Plan Generation, PGE-1 through PGE-6, remains the closed request renderer. Those slices are unchanged. Construction Model completeness refusal is **IMPLEMENTED / TESTED** in `app/services/construction_model/`. The drawing set beside those slices is **NOT COMPLETE**. These rules are the cross-cutting authority. The implementation slices do not replace them.

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
