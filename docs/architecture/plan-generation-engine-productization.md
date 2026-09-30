# Plan Generation Engine — productization plan

| Attribute | Value |
|-----------|--------|
| Status | **IN PRODUCTIZATION.** PGE-1 **CLOSED**. PGE-2 **CLOSED**. PGE-3 **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. Supported profiles: `dimensioned_plan`, `stair_detail`. Neither PDF is a project plan. No migration. |
| Date | 2026-09-30 |
| Drawing law | [construction-drawing-standard.md](construction-drawing-standard.md) |
| Proof | [../estimating-cases/2026/linda-bushel-pool-deck/](../estimating-cases/2026/linda-bushel-pool-deck/) |
| Sequence | [../PROJECT_DEVELOPMENT_CHECKLIST.md](../PROJECT_DEVELOPMENT_CHECKLIST.md) |
| Start New Project | Consumer. [start-project-implementation-plan.md](start-project-implementation-plan.md). SNP-3 stays blocked on this capability. |

The reusable Plan Generation Engine is a CalibraytAI capability. Start New Project may later call it. The engine remains usable when Start New Project does not exist.

## 1. Existing proof inventory

| Record | What it is |
|--------|------------|
| `docs/architecture/construction-drawing-standard.md` | Drawing law. Status: recorded requirement. The reusable engine is not implemented in that record. |
| `docs/estimating-cases/2026/linda-bushel-pool-deck/README.md` | Case index. One project. Not a platform default. |
| `case-record.json` | Machine status. `platform_default` false. `permit_approval` false. `engineering_seal` false. |
| `source/2026-09-29-linda-bushel-pool-deck-design.md` | Unaltered design brief. |
| `learning/project-record.md` | Facts, decisions, and open field items for this job. |
| `takeoff/p1_calculation.py` | Issue P1 arithmetic and an eight-sheet preliminary PDF. Sheets: cover and geometry; pier and foundation plan; framing plan; decking, guards, gate, and skirt; front and side elevations; stair detail; typical details; field verification and supplier notes. |
| `drawings/2026-09-29-p1-preliminary-11x17.pdf` | P1 output. Preliminary. Not sent. Not a permit. Not a seal. |
| `drawings/capability_test_plan.py` | CT-1 vector foundation and framing plan. |
| `drawings/2026-09-29-capability-test-foundation-framing-11x17.pdf` | CT-1 PDF. |
| `drawings/stair_detail.py` | First CT-2 stair proof. |
| `drawings/2026-09-29-capability-test-stair-detail-11x17.pdf` | First CT-2 PDF. Kept. |
| `drawings/stair_detail_r2.py` | CT-2 R2. Imports CT-1 stair geometry. |
| `drawings/2026-09-29-capability-test-stair-detail-r2-11x17.pdf` | CT-2 R2 PDF. |
| `geometry/2026-09-29-governed-geometry-reconciliation.md` | Open conflicts. Piers 12 against 15. Joist lines 16 against 15. Stringers 10 against 9. Throat 4.997 in labeled 5.00 in. No quantity was changed. |
| `takeoff/2026-09-29-drawing-vs-p1-differences.md` | Difference report. P1 quantities stay. |
| `takeoff/2026-09-29-p1-material-takeoff.md` | P1 quantities. |
| `drawings/framing-and-pier-layout-comparison.png` | Framing comparison. Not a construction drawing (`case-record.json`). |
| `costing/2026-09-29-ben-internal-cost.md` | Internal cost sheet. Unsent. |
| Supplier files under `supplier/bmr-winchester/` | Unsent request and difference note. |

Platform drawing authority today is upload and index, not generation:

| Piece | Path | Role |
|-------|------|------|
| `PlanDocument` | `app/plan_intelligence/models.py` | Project PDF. `archived_at` marks a plan that is not current. |
| Upload | `upload_plan` / `upload_plan_pdf` | Creates that PDF record. |
| `DrawingPackage`, `DrawingRevision`, `PlanSheet` | same models file | Uploaded-set package, revision, and sheet classification. |
| `generate_default_sheets_for_revision` | `app/plan_intelligence/sheets.py` | Draft sheets for pages of an uploaded PDF. |
| Project plans page | `GET /projects/<id>/plans` | Lists plans and links to upload. |
| Current-plan query | `project_plans` in `app/services/project_work_package.py` | Non-archived `PlanDocument` rows. |
| SNP-1 | `app/services/start_project_walk.py` | Treats a non-archived plan as drawings satisfied. |

`PlanDocument` stores filename, stored file, content type, size, SHA-256, page count, PDF title/author/subject/creator, notes, and `archived_at`. It has no uploaded-versus-generated origin.

Contract V1 is **ACCEPTED / PINNED** at `2903a45074df21b1c99390cb9aab68638970a2ff`. It is not edited by this plan. The mapper confirms a result onto an estimate. It does not draw.

## 2. Generic capability extraction

| Capability | Proof source | Project-specific input | Generic rule | Reusable candidate | Uncertainty / limitation |
|------------|--------------|------------------------|--------------|--------------------|--------------------------|
| Vector sheet on a stated paper size | CT-1 and CT-2 R2 use 17×11 in at 72 pt/in | Bushel job name and address in the title block | A sheet has a paper size, a border, and a title block | Sheet frame | P1 uses the same paper size for eight sheets. Paper size is an input, not a universal Bushel constant. |
| Stated scale and named origin | CT-1 scale `3/8 in = 1 ft-0 in`, origin pool centre. CT-2 R2 profile `6.15 pt = 1 in` and plan `26 pt = 1 ft` | Pool centre | Every sheet records the scale and the origin it uses | Scale record on the sheet manifest | Two scales on one stair sheet are proven. A universal scale is not. |
| Imperial dimension text | `ftin` in `capability_test_plan.py` | Bushel feet | A length is labeled in the measurement system of the job | Dimension formatter | CT-1 also prints a millimetre riser in `assert_geometry`. CT-2 R2’s sheet text says one system, imperial. The drawing standard requires one measurement system on the stair sheet. |
| Members drawn from coordinates | `draw_framing`, `piers`, `joist_segments` | 18 ft deck, pool radius 10.5 ft, Option A wings | The sheet draws the members it is given | Member renderer | Pier count, joist count, and stringer count are unresolved between P1 and CT-1. The engine must not choose them. |
| On-centre positions with a closing remainder | `oc_positions` | 16 in, 216 in width, 120 in stair | Spacing plus a start and end produces positions, including a remainder | Layout helper only when the closing rule is an input | The brief does not choose 4 in edge bays against one 8 in bay. That rule is not product law. |
| Dimension chains kept off the title block | `draw_dimensions` exits if a chain hits the title block | CT-1 chain positions | A successful sheet keeps dimensions readable and off the title block | Layout check | The check is local to that script’s coordinates. |
| Callouts and a schedule | `draw_callouts`, `schedule`, pier schedule in P1 sheet 2 | Bushel member names | A plan can name members and list them | Callout and schedule blocks | Schedule content comes from the geometry payload. |
| Exclusion check | CT-1 refuses a pier inside the pool and a header that enters the pool | Pool circle | A named exclusion shape can reject a member that enters it | Validation check when an exclusion is supplied | The circle is this pool. It is not a built-in obstacle. |
| Stair sheet reads the framing stair numbers | `stair_detail_r2.py` imports `capability_test_plan` and `verify()` refuses a drifted rise, run, or stringer count | 38 in, 5 risers, 7.60 in, 4 treads, 11 in, 44 in run, 9 stringers | One geometry source feeds the plan and the detail | Stair profile renderer fed by a geometry result | The script is not the Stair Calculator. Website stair source is outside this repository. |
| Tread under the riser, nosing labeled | CT-2 R2 | 3/4 in nosing, tread overall 12.50 in, riser board 6.60 in | The detail draws the supplied section | Profile geometry consumer | Those section sizes are this proof. |
| Throat shown with an open flag | CT-2 R2 prints 4.997 in as 5.00 in and the words STRUCTURAL VERIFICATION REQUIRED | 11.25 in stringer | A supplied uncertainty is printed. It is not cleared by the sheet | Uncertainty flag on the result | No throat limit was found in the brief, the take-off, or the drawing standard. |
| Notes supplement geometry | Drawing standard; notes on CT-2 R2 and P1 | Code note and kit SKU on this job | Notes do not replace the drawn members | Note block | The Ontario Building Code sentence on the proof is a note. It is not a municipal approval. |
| Sheet identity and a kept prior revision | CT-1, CT-2, CT-2 R2 are separate files. R2 refuses to overwrite the first CT-2 PDF | Those filenames | A new generation does not destroy the prior proof | Revision identity | Platform `DrawingRevision` is for uploaded packages. It is not yet a generation revision. |
| Disclaimer | Title blocks: “Not a permit. Not a seal.” P1: not a permit approval and not an engineering seal | This case | Every generated sheet carries that boundary | Required title-block text | The engine does not certify structure, span, bearing, or permit. |
| Consistency gate before the file is written | `assert_geometry`, `verify` | Bushel expected counts | A sheet is written only after its own checks pass | Validation gate | CT-1’s numeric span limits (`ALLOW_2X8_16` and the related names) are not cited to a code table. They are not an engine rule. |
| Drawing leaves price and take-off alone | Module docstrings; difference report; reconciliation | P1 quantities unchanged | Generation does not price and does not edit a take-off | Boundary | Quantity-from-drawing remains future. The standard records it. This plan does not build it. |

P1 sheet 5 draws a front and side elevation for this deck. The drawing standard says the whole-deck elevations are not a general elevation generator, and the stair side profile is the drawn stair proof. Whole-deck elevations stay outside the first engine version.

## 3. Engine responsibility

The engine consumes governed geometry and drawing instructions and produces a validated drawing result.

It draws. It does not own:

- client records
- company price, margin, or estimate lines
- workflow navigation or Start New Project stage
- commercial approval, a permit, or a professional seal
- construction mathematics that already belongs to a domain capability

Order, from the drawing standard:

calculation or an accepted geometry record, then the drawing, then later quantity evidence.

The drawing consumes that geometry. It does not invent a second shape for the same element.

## 4. Input contract

The first engine accepts a drawing request. Fields below are the ones the proofs actually use. A later drawing type adds fields only when a profile for that type exists.

| Field | Type | Authoritative source | Required | Validation | If missing | Rule 16 path |
|-------|------|----------------------|----------|------------|------------|--------------|
| `drawing_type` | string | The request. First legal value: `dimensioned_plan`. Later: `stair_detail` only after that profile exists. | Required | Must be a supported type | `UNSUPPORTED_DRAWING_TYPE` | Build Drawings is not offered for that type. Upload remains on the project plans page. |
| `measurement_system` | `imperial` or `metric` | The request. Bushel sheets that state a system use imperial. | Required | One system on the sheet | `MISSING_MEASUREMENT_SYSTEM` | The build form asks for it, then the request is evaluated again. |
| `paper` | width and height | The request. Proofs use 11×17 in. | Required | Positive page size | `MISSING_PAPER` | The build form asks for it. |
| `scale` | stated scale and unit | The request. CT-1 and CT-2 R2 each print the scale they use. | Required | Scale is present on the manifest and the sheet | `MISSING_SCALE` | The build form asks for it. |
| `origin` | name of the origin | The request. CT-1 names pool centre. | Required | The sheet states it | `MISSING_ORIGIN` | The build form asks for it. |
| `title` | project or sheet title facts | Project name and location may be read for the title block. They are display context. | Required for a readable title block | Non-empty title | `MISSING_TITLE` | The build form uses the project name when it exists, and asks when the sheet title is still empty. |
| `members` | list of named members with coordinates or segments | Governed geometry payload for `dimensioned_plan` | Required for that type | Each member has an id, a role, and geometry the renderer can draw | `MISSING_GEOMETRY` | The build form collects the payload, or a domain capability supplies it. The renderer does not place piers, choose a closing bay, or apply a span table. |
| `exclusions` | optional shapes members must not enter | The geometry payload, when the job has one | Optional | When present, a member inside an exclusion fails validation | — | — |
| `stair_geometry` | rise, run, counts, section sizes, stringer positions, and any uncertainty flags | A governed stair result. CT-2 R2 reads these from the framing proof rather than a second calculator. | Required only for `stair_detail` | The detail uses this object. It does not recompute rise, run, or throat. | `MISSING_STAIR_GEOMETRY` | Build Drawings for a stair detail stays unavailable until that result is on the request. The stair capability remains the producer. |
| `uncertainty_flags` | list of coded flags | The geometry result. CT-2 R2 uses structural verification required. | Optional | Printed when present. A flag is not deleted by generation. | — | A blocking flag keeps the candidate off current project evidence until the contractor explicitly uses that sheet. Use does not clear the flag and does not certify structure. |
| `assumptions` | coded notes that are not geometry | The request | Optional | Notes do not replace members | — | — |

Client identity, prices, estimate ids, and Start New Project stage are not inputs.

Span allowables from CT-1 are case data. They are not request fields until a governed span source exists. No such source is in this repository.

## 5. Rule 16 prerequisites

Every missing required input returns a stable code, a sentence the contractor can read, and a place to supply the fact. After the fact is saved, the same request is evaluated again.

| Code | Contractor sees | Where it is resolved |
|------|-----------------|----------------------|
| `UNSUPPORTED_DRAWING_TYPE` | This drawing type cannot be built here. | Upload on `GET /projects/<id>/plans`. Build Drawings is absent for that type. |
| `MISSING_MEASUREMENT_SYSTEM` | Choose imperial or metric. | Build form on that plans page. |
| `MISSING_PAPER` | Choose the sheet size. | Build form. |
| `MISSING_SCALE` | State the scale. | Build form. |
| `MISSING_ORIGIN` | Name the origin. | Build form. |
| `MISSING_TITLE` | Name the sheet. | Build form, prefilled from the project name when the project has one. |
| `MISSING_GEOMETRY` | The members to draw are not on this request. | Build form, or the domain capability that owns that shape. |
| `MISSING_STAIR_GEOMETRY` | The stair detail needs a stair geometry result. | The stair capability’s result, once that result can be stored on the project. Until then, stair-detail Build Drawings is not offered. |
| `BLOCKING_UNCERTAINTY` | The sheet has an open verification flag. | Review. The contractor may hold it or explicitly use it as the current drawing. The flag remains on the record. |

A missing input must not end as an uncaught exception with no page.

## 6. Calculator / Contract V1 relationship

Domain capabilities own construction mathematics. Plan Generation consumes their geometry or their Contract V1 result.

```text
stair capability → governed stair geometry → plan generation → stair detail
concrete capability → governed concrete result → plan generation → slab drawing, later
```

Contract V1 carries `inputs`, `assumptions`, `components`, and `quantities` as coded length, area, volume, or count, plus `product_specification`. It does not carry member coordinates, a sheet, a scale, or a stringer polygon.

Plan Generation may read a valid Contract V1 result when a drawn label is one of those coded values. It must not treat the envelope as a framing layout.

Gap, recorded and not fixed here: a drawing that needs placed members needs a geometry payload Contract V1 does not define. This plan does not add that field to the contract.

The concrete and stair engines named in Contract V1’s “first proving engines” and later-engine notes are not implemented in this repository. The public Stair Calculator and Concrete Calculator live on the Website. Their formulas are not copied here.

PGE-3 copies `result_id`, `engine_id`, `engine_version`, and a calculation fingerprint only when the supplied stair geometry already carries them. It does not call `calculation_fingerprint`. A stair profile is not a Contract V1 envelope, because that contract still has no stringer polygon. Contract V1 was not edited.

CT-1’s span numbers and CT-2 R2’s throat arithmetic stay inside the Bushel scripts. The product engine prints a throat only when the stair geometry result already contains it.

## 7. Output contract

A successful generation returns:

| Piece | Proven by |
|-------|-----------|
| PDF bytes for the sheet | CT-1, CT-2, CT-2 R2, and P1 write PDFs |
| Sheet manifest: paper, scale, origin, measurement system, drawing type | Printed on those title blocks |
| Member ids that were drawn | Pier names, joists, and stringers in the proofs |
| Source input fingerprint | The proofs are deterministic for their own constants. The product result records the fingerprint of the request. |
| Uncertainty flags that were supplied | STRUCTURAL VERIFICATION REQUIRED on CT-2 R2 |
| Generator identity and version | Sheet marks CT-1, CT-2, and CT-2 R2 |
| Validation result | `assert_geometry` and `verify` run before save |
| Disclaimer | “Not a permit. Not a seal.” |

The result does not include a price, an estimate line, a permit status, or a seal.

PDF creation alone is not success. Validation has to pass, and a blocking uncertainty keeps the file a candidate until the contractor uses it.

## 8. Project document integration

Current drawing evidence is a non-archived `PlanDocument`. SNP-1 and `project_plans` already use that rule.

```text
request → validate → render candidate → contractor reviews → accept
→ store the PDF through the existing plan-file storage
→ PlanDocument on the same project
→ drawings surface lists it
```

The candidate is not a `PlanDocument` before acceptance. A non-archived `PlanDocument` already satisfies the drawings stage, so an unreviewed file must not be inserted there.

Acceptance uses the existing plan storage and `PlanDocument` row. It does not create a second project-document table for the sheet the contractor uses.

`DrawingPackage` and `DrawingRevision` remain the uploaded-set model. A later slice may attach the accepted file to a revision. That attachment is not required to prove the first sheet.

Generation does not archive, delete, or rewrite an existing upload. CT-2 R2 kept the first stair PDF. A new generation keeps the prior file.

## 9. Provenance

Uploaded and generated drawings are the same kind of project PDF once accepted. The contractor uses one drawings list.

`PlanDocument` cannot say which is which. `pdf_creator` is file metadata, not a governed origin.

Minimum later delta, not migrated here:

- `PlanDocument.origin`: `uploaded` or `generated`. Existing rows mean `uploaded`.
- A generation-candidate record that exists before acceptance: drawing type, input fingerprint, engine version, validation result, uncertainty flags, and the accepted `plan_document_id` once the contractor uses the sheet.

The candidate record is the pre-acceptance hold. It is not a second drawings list.

## 10. Initial supported drawing types

| | |
|--|--|
| Supported in the first engine version | `dimensioned_plan`: one sheet that draws the members, dimension strings, scale, origin, and disclaimer it was given. |
| Supported only after the stair profile slice | `stair_detail`: side profile and labels from a supplied stair geometry result, including a supplied uncertainty flag. |
| Not yet supported | Whole-deck elevations, decking and guard plans, typical details, pier layout chosen by the engine, joist or stringer closing rules, span checks, take-off quantities, permit sets. |
| Requires a future capability | Footing drawing, slab plan, ICF wall drawing, and any type whose geometry producer does not exist yet. The drawing standard names those producers. They are not in this repository. |

Build Drawings is offered only for a supported type. A project that needs another type uses Upload Drawings.

## 11. Validation

Before a candidate exists, all of the following hold:

- required inputs for that drawing type are present
- `drawing_type` is supported
- every member on a `dimensioned_plan` has drawable geometry
- a supplied exclusion contains no member
- a `stair_detail` uses the supplied stair geometry and does not contain a second rise or run
- the PDF contains the title, the scale, the origin, the disclaimer, and the dimension text the manifest lists
- uncertainty flags from the input are present on the manifest
- the result records engine version and input fingerprint

A blocking uncertainty yields a candidate and withholds current `PlanDocument` evidence until the contractor explicitly uses that sheet.

CT-1 span limits are not a validation rule of the product engine.

## 12. Human review

The contractor reviews the candidate on the project drawings surface.

| Action | Effect |
|--------|--------|
| Review | Opens the candidate. Flags stay visible. |
| Use as current drawing | Registers a `PlanDocument`. SNP-1 can then see drawings present. |
| Correct and generate again | A new candidate. The prior candidate and any already accepted PDF remain. |

Use is the contractor’s choice that this sheet is the project drawing. It is not a professional seal, a span approval, or a municipal permit. The Bushel title blocks already say that, and the drawing standard already says it.

## 13. Independent Platform entry

The engine does not require Start New Project.

```text
Project → Drawings (`GET /projects/<id>/plans`) → Build Drawings
```

Build Drawings opens the request for a supported type, shows missing inputs on that same surface, and returns the candidate there. Upload stays the existing upload route.

A project id is required because current drawing evidence is project-scoped `PlanDocument`. The capability is still a project drawings action when the guided walk is absent.

## 14. Start New Project integration interface

Not implemented in this plan.

Later SNP-3, after the engine can complete a supported type:

| Condition | Walk |
|-----------|------|
| Non-archived `PlanDocument` exists | Drawings present. Continue. |
| `drawing_requirement` is `NOT_REQUIRED` | Continue. No placeholder PDF. |
| `drawing_requirement` is `REQUIRED` and no current plan exists | Drawings missing. Open `/projects/<id>/plans`. |
| `drawing_requirement` is `UNKNOWN` and no current plan exists | Unresolved. The contractor chooses required or not required. Unknown is not stored as not required. |
| `drawing_requirement` is `UNKNOWN` and a current plan exists | SNP-1 already treats that plan as drawings satisfied. This plan adds no second acceptance flag. |

On drawings missing, the plans page offers Upload Drawings and, for a supported type only, Build Drawings. Build Drawings calls this engine. After the contractor uses the sheet, the resolver runs again and drawings are present.

SNP-1 does not generate a drawing. SNP-2 stays blocked until every resolver destination passes Rule 16, including this drawings branch.

## 15. Drawing requirement authority

`Project` has no column for required versus not required. Presence stays derived from non-archived `PlanDocument` rows.

Minimum later column, not migrated here:

`projects.drawing_requirement` — `UNKNOWN`, `REQUIRED`, or `NOT_REQUIRED`. Existing projects stay `UNKNOWN`.

`BUILD_DRAWINGS` is an action. `PRESENT` is derived. Neither is stored on that column.

Changing the decision does not delete plan history.

## 16. Engine architecture

Proposed home: `app/services/plan_generation/`. Projects and Start New Project call it. They do not contain sheet mathematics.

| Piece | Responsibility |
|-------|----------------|
| Request model | The input contract in section 4. |
| Validation | Section 11, including missing-input codes. |
| Profiles | One profile per supported drawing type. No Bushel profile. |
| Renderer | ReportLab sheet from a validated request. New code. It does not import the Bushel scripts. |
| Candidate store | Holds the PDF and manifest until the contractor uses it. |
| Project adapter | On use, writes a `PlanDocument` through existing plan storage and sets origin `generated`. |
| Fixtures | Data files. Bushel numbers appear only in the Bushel fixture. |

No `start_project_walk` drawing code. No service named for Linda Bushel.

## 17. Implementation slices

| ID | Purpose | Generic capability | Bushel proof used | Likely files | Schema | Acceptance | Human UAT | Rule 16 | Stop |
|----|---------|--------------------|-------------------|--------------|--------|------------|-----------|---------|------|
| PGE-1 | Request, validation, missing-input result. No PDF. | The engine accepts a geometry payload and names every missing field. | Fixture data taken from the shared datum in the geometry reconciliation. The second fixture uses other dimensions. | `app/services/plan_generation/`, `tests/test_plan_generation_request.py`, fixture JSON | None | **IMPLEMENTED / TESTED / CLOSED AS A SLICE.** A complete request validates. Missing geometry returns `MISSING_GEOMETRY`. An unsupported type returns `UNSUPPORTED_DRAWING_TYPE`. | Not required. No page. | Missing inputs are structured codes, not exceptions. | Stop if the slice renders, writes a `PlanDocument`, or imports a Bushel script. |
| PGE-2 | Render `dimensioned_plan` | One PDF and manifest from a validated payload. | Bushel fixture must show its own member count, scale sentence, and disclaimer. | `app/services/plan_generation/render.py` and `tests/test_plan_generation_render.py` | None | **IMPLEMENTED / TESTED / CLOSED AS A SLICE.** The PDF is not current project evidence. Manifest matches the request. | Both fixture sheets were read. Members, the exclusion, scale, origin, and the disclaimer are readable. The two sheets differ. | Unsupported types produce no file. | Stop if pier counts or pool radius are constants in the renderer. |
| PGE-3 | `stair_detail` profile | Stair sheet from supplied stair geometry. | Recorded rise, run, and counts are fixture data. A second fixture uses other geometry. | `app/services/plan_generation/render.py` and `tests/test_plan_generation_stair.py` | None | **IMPLEMENTED / TESTED / CLOSED AS A SLICE.** Throat and nosing text appear only when the geometry result includes them. The PDF is not a project plan. | Both stair sheets were read. The flights differ. Title, scale, origin, and the disclaimer are readable. | `MISSING_STAIR_GEOMETRY` produces no PDF. | Stop if the profile recalculates rise, run, or throat, or copies Website stair code. |
| PGE-4 | Candidate, review, and `PlanDocument` on use | Accepted output is a normal project plan. | R2 kept the prior file. The product test keeps the prior `PlanDocument`. | Adapter, plans route, template, tests | Candidate record and `PlanDocument.origin`. Separate migration approval before the revision is written. | Use creates one non-archived plan. A second generation does not delete it. Another organization cannot read it. | Contractor uses a sheet and sees it on the plans list. | Unaccepted candidates do not satisfy SNP-1. | Stop if acceptance needs a second document product, or if the migration is not separately approved. |
| PGE-5 | Build Drawings on the existing plans page | Direct project entry. | None as a layout. | Plans page and route | None beyond PGE-4 | The action appears for `dimensioned_plan` only. Upload is unchanged. | Phone and desktop: missing geometry shows the form; a supported build returns a candidate. | No dead end on a missing input. No button for an unsupported type. | Stop if the page is a Start New Project wizard. |
| PGE-6 | SNP-3 drawings decision | Resolver names unknown, not required, required-missing, and present. | None | `start_project_walk.py`, project field, tests | `drawing_requirement` column. Separate migration approval. | Tests A–F from the SNP-3 stop. Build path uses PGE-5. | Present, not required, upload, and build each continue the walk. | All seven SNP destinations pass, or SNP-2 stays blocked. | Stop if the slice builds another engine or implements SNP-2. |

## 18. Proving strategy

After PGE-2, a test loads a Bushel fixture file of member coordinates and expected labels. It calls the product engine. It does not run `capability_test_plan.py` or `stair_detail_r2.py`.

The fixture may carry the shared datum the reconciliation already records: 18 ft width, 16 in spacing, the stair rise and run, and one chosen member list marked as fixture data. Expected checks are characteristics: paper size, scale sentence, disclaimer, and the member count in that fixture. They are not a pixel match to the 29 Sep PDF.

A second fixture is required in PGE-1 and PGE-2. It uses a different width, a different member count, and no pool radius. A renderer that contains Bushel constants fails that fixture.

Bushel geometry conflicts stay unresolved. The fixture does not pick 12 piers over 15, or 9 stringers over 10, as product law. It picks one explicit member list and names it fixture data.

## 19. Test strategy

Future tests, not written by this plan:

- request unit tests for each required field
- unsupported type
- second geometry fixture beside the Bushel fixture
- renderer: scale, disclaimer, and dimension text present
- stair profile: no second rise; throat only from the payload
- validation failure does not write a candidate
- organization boundary on the project adapter
- accept writes one `PlanDocument` and leaves prior plans in place
- candidate absence from `project_plans` and from SNP-1
- missing-input codes
- plans page shows Build Drawings only for a supported type
- responsive check of that page at desktop and 390 px
- contractor UAT on a temporary database for review, correct, and use

PGE-1 needs no browser pass. PGE-5 does.

## 20. Migration strategy

No migration in this planning pass. Repository Alembic head stays `k1f2a3b4c5d6`. Mac primary stays `h8c9d0e1f2a3`. Hosted revision stays last recorded `k1f2a3b4c5d6`.

Later, each revision needs its own approval:

| Delta | When | Why existing tables are not enough |
|-------|------|-------------------------------------|
| Generation candidate, plus `plan_documents.origin` | PGE-4 | An unaccepted PDF cannot be a non-archived `PlanDocument`, because that row already means current drawings. |
| `projects.drawing_requirement` | PGE-6 | No project column stores `UNKNOWN`, `REQUIRED`, and `NOT_REQUIRED`. |

No workflow-state table is added for this decision. Rollback of either revision removes only that addition. Plan history is not deleted.

## 21. Recommended next implementation slice

PGE-1, PGE-2, and PGE-3 are closed as slices. `render_plan_generation` draws an accepted `dimensioned_plan` or `stair_detail`. It does not write a `PlanDocument`. PGE-4, the candidate and project-plan step, is next and is not started. It needs its own migration approval. No project-document integration exists. Build Drawings is not a page. No drawing-requirement migration exists. SNP-2 and SNP-3 stay blocked. Guided Project Setup stays recorded and not built.
