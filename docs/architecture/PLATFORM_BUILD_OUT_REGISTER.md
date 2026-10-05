# Platform Build-Out Register

| Attribute | Value |
|-----------|--------|
| Status | Tactical construction register |
| Date | 2026-10-01 |
| Repository | `/Users/joelbrayman/Desktop/Brayman-Estimator` |
| Inspected HEAD | This documentation commit. It is not deployed. |
| Live product SHA | **VERIFIED** `8fa27f4d2b176bb21d770a0dfd339749ca140b01`. Deploy `dep-dav7umm0tbcc73e2fneg`. Auto-deploy off. The 8-inch ICF quantity service was first deployed as `dep-dav7o7p42hec73dbraag` at `1ca26d99c1d95a297bfdf42ad6f07dbb6b0c749e`. |
| Hosted database | **VERIFIED** `m3f4a5b6c7d8`. Not migrated in the 1 Oct acceptance walk. |
| Mac primary | Last verified `h8c9d0e1f2a3`. Not migrated. Not used for this walk. |

This register is the tactical source of truth for what gets built next. The lifecycle blueprint remains the strategic reference. A row is not closed because a route, an architecture note, or a local test exists.

Allowed statuses:

| Status | Meaning |
|--------|---------|
| CLOSED — LIVE VERIFIED | Implemented, tested, documented, committed, pushed, deployed, and checked on the live surface named in the row. |
| BLOCKED — DEPENDENCY IDENTIFIED | Work cannot finish until the named dependency is available. |
| NOT STARTED | The complete capability is not built. An earlier partial foundation may be named in the row. |
| DEFERRED | Intentionally later. Not the current build. |

A missing value is not a development blocker when an authorized contractor or instance owner can supply it. Classify each missing input as exactly one of:

| Class | Meaning |
|-------|---------|
| RUNTIME INPUT | The contractor supplies it in the workflow. The status is input required, not blocked. |
| INSTANCE-OWNER INPUT | The company owner sets it in governed configuration. Absence does not block the engine. |
| TRUE PLATFORM DEPENDENCY | The platform lacks the formula, contract, service, or safe architecture. Only this class uses BLOCKED — DEPENDENCY IDENTIFIED. |

## Occupancy used for this record

The 1 Oct 2026 live acceptance walk used deploy `dep-dav6kt8jo6nc73fpglg0` at `ae115059d96028d0e3adf11d20c6ab7d5731901d`. Hosted revision was `m3f4a5b6c7d8`. Auto-deploy stayed off. The walk used synthetic project 51 and synthetic client 46. It did not change product code and it did not deploy the later documentation commit.

Concrete and Stair are closed on the public Website, not in this repository. Website Version 31 SHA `5dcb4f2b9cc0a291a16375f06ce89f09a02262cf` is the recorded live public checkpoint.

---

## A. Project lifecycle

### START PROJECT

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — start |
| Purpose | Open a project for a client in this company and land on setup. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for opening a project and landing on Continue setup. |
| Existing implementation | `/projects/new` redirects to Continue setup. SNP-1 resolver, SNP-2 entry, and the new-client then existing-client path are on the live SHA. |
| What is missing | Nothing for this start. The future readiness model is a separate row. |
| Build acceptance criteria | Met. A synthetic project opened Continue setup for that same project. |
| Live verification requirement | Met on 1 Oct 2026. Project 51, client 46, number `UAT-2026-1001-WALK`, stage Lead. One project row. One client row. |
| Commit / deployed SHA when closed | Deployed SHA `ae115059d96028d0e3adf11d20c6ab7d5731901d`. Deploy `dep-dav6kt8jo6nc73fpglg0`. Hosted revision `m3f4a5b6c7d8`. |

### GUIDED PROJECT SETUP

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — guided setup |
| Purpose | Read the project and open the existing page for the first gap. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for the first-gap resume. |
| Existing implementation | `GET /projects/<id>/setup` in `app/routes/project_setup.py`. First gap in `app/services/start_project_walk.py`. SNP-2 re-entry, SNP-4 Return to setup, and SNP-6 estimate handoff are on the live SHA. No stored wizard step. |
| What is missing | Nothing for this first-gap resume. The future readiness model is a separate row. |
| Build acceptance criteria | Met. Continue setup named project 51 and the current next page after each saved record. |
| Live verification requirement | Met on 1 Oct 2026. Leaving and reopening setup recalculated location, drawings, scope, one estimate, and then two estimates. |
| Commit / deployed SHA when closed | Deployed SHA `ae115059d96028d0e3adf11d20c6ab7d5731901d`. Deploy `dep-dav6kt8jo6nc73fpglg0`. Hosted revision `m3f4a5b6c7d8`. |

### READY TO PRICE

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — ready to price |
| Purpose | Tell the contractor the project is ready to price, including more than the first missing fact. |
| Current status | NOT STARTED |
| Required dependencies | None named beyond the first-gap foundation that already exists in git. |
| Existing implementation | First-gap foundation only. Client, location, drawings, scope, then one estimate action. The future readiness model is not implemented. |
| What is missing | The complete ready-to-price capability. No readiness table, cursor, or multi-action resolver is authorized by this row. |
| Build acceptance criteria | A later accepted design, then a live walk that shows readiness without a second estimate. |
| Live verification requirement | Live office, after that later build is deployed. |
| Commit / deployed SHA when closed | Not closed. |

### ESTIMATE

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — estimate |
| Purpose | Price the project on the ordinary estimate. Company cost and margin stay here. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for the ordinary estimate already on the live office. |
| Existing implementation | Estimates, versions, sections, and lines. Hosted read-only UAT on 26 Sep 2026 opened Estimates and one Estimate. Later deploys through `ca37d8b6939f6494b6ff415bad17953886366728` kept that office. |
| What is missing | Nothing for the ordinary estimate or the guided handoff. Workflow consumption of an engine is not this row. |
| Build acceptance criteria | Already met for the ordinary estimate on the live office. |
| Live verification requirement | Ordinary estimate remains on the live office. The 1 Oct 2026 walk also created synthetic estimates 38 and 39 and returned to them from Continue setup. |
| Commit / deployed SHA when closed | Live SHA `ca37d8b6939f6494b6ff415bad17953886366728`. |

### PROPOSAL

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — proposal |
| Purpose | Issue a proposal from the estimate without rewriting an accepted proposal. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for the proposal office already live. |
| Existing implementation | Proposals and accepted-proposal immutability. Hosted read-only UAT on 26 Sep 2026 opened Proposals. |
| What is missing | A fresh 1 Oct live walk was not performed. |
| Build acceptance criteria | Already met for the live proposal list and record. |
| Live verification requirement | Met by that hosted UAT and the current live SHA. |
| Commit / deployed SHA when closed | Live SHA `ca37d8b6939f6494b6ff415bad17953886366728`. |

### CONTRACT SIGNING

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — contract signing |
| Purpose | Produce and sign the contract the contractor will build from. |
| Current status | BLOCKED — DEPENDENCY IDENTIFIED |
| Dependency class | TRUE PLATFORM DEPENDENCY |
| Required dependencies | A counsel-approved production contract package. A contractor cannot type that package into existence. |
| Existing implementation | FG-024 slices and FG-033 native signing exist in the repository. Production customer signing is not complete. Real iPhone signing UAT was deferred. |
| What is missing | The finished contract-signing capability. |
| Build acceptance criteria | A later accepted slice that a contractor can sign on the live office. |
| Live verification requirement | Live signed artifact on the deployed SHA. |
| Commit / deployed SHA when closed | Not closed. |

### BUILD / MANAGE

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — build and manage |
| Purpose | Run the job after the contract: field, schedule, and production. |
| Current status | BLOCKED — DEPENDENCY IDENTIFIED |
| Dependency class | TRUE PLATFORM DEPENDENCY |
| Required dependencies | An accepted specification for the finished build-and-manage stage. Field, calendar, and schedule pieces already exist and are not this gap. |
| Existing implementation | Field Web v1, field observations, company calendar, and schedule hubs are operational pieces. They are not this lifecycle stage closed. |
| What is missing | The complete build-and-manage capability. |
| Build acceptance criteria | A later accepted production slice, then a live job walk. |
| Live verification requirement | Live office and field, after that slice is deployed. |
| Commit / deployed SHA when closed | Not closed. |

### CHANGE ORDERS

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — change orders |
| Purpose | Authorize a change and keep the estimate and the job in agreement. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for the change-order record already in the live office. |
| Existing implementation | Change orders are on the project hub in the live product. Extra-work internal cost capture is in that product line. |
| What is missing | The separate change-order document family is not implemented. This row closes the existing record, not that future document. |
| Build acceptance criteria | Already met for the live change-order record. |
| Live verification requirement | The live SHA contains the office that has been carrying change orders since before the 30 Sep deploy. Not re-walked on 1 Oct 2026. |
| Commit / deployed SHA when closed | Live SHA `ca37d8b6939f6494b6ff415bad17953886366728`. |

### COMPLETE / CLOSE

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — complete and close |
| Purpose | Close the job, including sign-off. |
| Current status | BLOCKED — DEPENDENCY IDENTIFIED |
| Dependency class | TRUE PLATFORM DEPENDENCY |
| Required dependencies | An accepted completion sign-off. Closing a project record already exists. The missing piece is the sign-off capability, not a company setting. |
| Existing implementation | Project lifecycle ACTIVE / CLOSED and a punch list exist. Core close remains partial. Client walkthrough has an empty live baseline and was not live-tested with client data. |
| What is missing | The complete close capability, including completion sign-off. |
| Build acceptance criteria | A later accepted close slice and a live close walk. |
| Live verification requirement | Live project closed on the deployed SHA. |
| Commit / deployed SHA when closed | Not closed. |

### ACTUALS

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — actuals |
| Purpose | Record what the job actually cost and used. |
| Current status | NOT STARTED |
| Dependency class | RUNTIME INPUT for a direct-cost amount on the existing project screen. TRUE PLATFORM DEPENDENCY for a finished quantity-actuals product, because that specification is not accepted. |
| Existing implementation | FG-023 direct-cost actuals and Monitor v1 are operational for an earlier office UAT. That is not the complete actuals capability. |
| What is missing | Quantities and costs as a finished learning input for the live job. |
| Build acceptance criteria | A later accepted actuals slice. |
| Live verification requirement | Live actual recorded and visible on Monitor after deploy. |
| Commit / deployed SHA when closed | Not closed. |

### LEARN & IMPROVE

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — learn and improve |
| Purpose | Compare actuals with the estimate and propose a calibration a person can approve. |
| Current status | BLOCKED — DEPENDENCY IDENTIFIED |
| Dependency class | TRUE PLATFORM DEPENDENCY |
| Required dependencies | The learning product itself. A company rate is not the missing piece. One project must not silently change a formula. |
| Existing implementation | Checklist learning law only. One project must not silently change a formula, cost, rate, or margin. |
| What is missing | The learning product. |
| Build acceptance criteria | A person reviews and approves a proposed calibration. |
| Live verification requirement | Live approval that does not silently change a default. |
| Commit / deployed SHA when closed | Not closed. |

### ANALYTICS / REPORTING

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — analytics and reporting |
| Purpose | Report across jobs. |
| Current status | BLOCKED — DEPENDENCY IDENTIFIED |
| Dependency class | TRUE PLATFORM DEPENDENCY |
| Required dependencies | An accepted reporting specification. Missing report numbers are not the gap. |
| Existing implementation | No cross-job analytics product was found. |
| What is missing | The reporting capability. |
| Build acceptance criteria | A later accepted report a contractor can open on the live office. |
| Live verification requirement | Live report on the deployed SHA. |
| Commit / deployed SHA when closed | Not closed. |

---

## B. Construction intelligence engines

The same engine serves independent use and workflow use. Do not build a second engine for the public Website.

### CONCRETE

| Field | Record |
|-------|--------|
| Diagram location | Construction intelligence — concrete |
| Purpose | Governed slab quantities. Standard slab and thickened edge. |
| Independent use | CLOSED — LIVE VERIFIED |
| Workflow use | BLOCKED — DEPENDENCY IDENTIFIED |
| Dependency class | TRUE PLATFORM DEPENDENCY for a platform copy. The public formula stays on the Website. |
| Required dependencies | An accepted project-consumption slice that uses the Website result through the mapper. Do not copy the formula into this repository. |
| Existing implementation | Public authority `lib/calculation-engine/concrete-slab.ts` in the Website repository. Not copied here. |
| What is missing | Platform workflow consumption. Footings, walls, columns, and concrete stairs are not current public modes. |
| Build acceptance criteria | Independent use is already closed on the Website. Workflow use needs a later slice that consumes the same result through the mapper. |
| Live verification requirement | Independent use: Website Version 31 parity PASS. Workflow use: not closed. |
| Commit / deployed SHA when closed | Independent use: Website SHA `5dcb4f2b9cc0a291a16375f06ce89f09a02262cf`. |

### STAIR

| Field | Record |
|-------|--------|
| Diagram location | Construction intelligence — stair |
| Purpose | Governed stair geometry and quantities. |
| Independent use | CLOSED — LIVE VERIFIED |
| Workflow use | BLOCKED — DEPENDENCY IDENTIFIED |
| Dependency class | TRUE PLATFORM DEPENDENCY for a second stair formula. |
| Required dependencies | An accepted project-consumption slice. Bushel scripts are not that formula. |
| Existing implementation | One public stair formula on the Website. Bushel scripts are case evidence, not a second engine. No stair engine is in this repository. |
| What is missing | Platform workflow consumption. |
| Build acceptance criteria | Independent use is already closed. Workflow use must not create a second stair formula. |
| Live verification requirement | Independent use: Website calculation PASS, visual PASS, pin PASS at Version 31. |
| Commit / deployed SHA when closed | Independent use: Website SHA `5dcb4f2b9cc0a291a16375f06ce89f09a02262cf`. |

### ICF MANUFACTURER PROFILE REGISTRY

| Field | Record |
|-------|--------|
| Diagram location | Construction intelligence — ICF profiles |
| Purpose | Versioned, source-attributed manufacturer facts for a later ICF engine. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for the registry. Quantity use still waits on the ICF estimator row. |
| Existing implementation | `app/data/icf_manufacturer_profiles_v1.json` and `app/services/icf_manufacturer_profiles.py`. Four profiles, version 1. Missing facts stay `NOT_ESTABLISHED`. No route. No quantity formula. |
| What is missing | Nothing for the registry. Logix still has no per-form concrete volume. The source states an 8-inch cavity width of 0.667 ft instead, and that factor is stored. |
| Build acceptance criteria | Met. Profiles load on the deployed office, sources stay attached, and a missing fact is named. |
| Live verification requirement | Met on deploy `dep-dav6kt8jo6nc73fpglg0` and reconfirmed on that same SHA during the 1 Oct acceptance walk. Four 8-inch profiles loaded. Sources stayed attached. Missing engine fields stayed unnamed as facts. Authenticated `/icf` returned 404. |
| Commit / deployed SHA when closed | Implementation and deployed SHA `ae115059d96028d0e3adf11d20c6ab7d5731901d`. Deploy `dep-dav6kt8jo6nc73fpglg0`, status live, finished 2026-10-01T14:14:45Z. |

### ICF

| Field | Record |
|-------|--------|
| Diagram location | Construction intelligence — ICF |
| Purpose | Internal governed ICF takeoff: materials, labour inputs, and direct-cost inputs. Final selling price stays with estimating. |
| Independent use | CLOSED — LIVE VERIFIED for the internal 8-inch form and concrete service. There is no public page. |
| Workflow use | CLOSED — LIVE VERIFIED |
| Dependency class | RUNTIME INPUT for wall area, corner counts, the reinforcement schedule, and the labour-hour allowance. INSTANCE-OWNER INPUT for the existing $65 CAD man-hour rate and for any later ICF production standard. A requested corner whose coverage is absent from the profile stays a TRUE PLATFORM DEPENDENCY for that configuration only. |
| Required dependencies | Design specification present at commit `c1ab362`. Eight-inch standard form and concrete methods are source-backed. Dollar labour uses ORG-001 at $65 CAD per man-hour. Labour hours are a confirmed allowance. Pratt stays evidence and is not seeded. |
| Existing implementation | `app/services/icf_quantity.py` applies the verified profile methods for 8-inch form count and concrete. `estimates.wall_form_quantities` at `/estimates/<id>/versions/<version_id>/wall-form-quantities` asks for the manufacturer, net wall area, and corner counts, and can offer the result to the existing calculation review. Calculate does not ingest. Review does not confirm a line. Labour hours stay an allowance and are not priced. |
| What is missing | Nothing for the 8-inch form and concrete path. Rebar remains a project schedule. An unestablished package quantity is not invented. A StyroRail / BuildBlock 45-degree corner still has no coverage in the profile, so that one request is not offered for review. |
| Build acceptance criteria | Met. One internal engine, no public page, no second estimate, no silent price, and no line until the existing confirmation. |
| Live verification requirement | Met. Host HEAD `ff9d6791c4bb16ef50d42a9ca71af2a1d6bc051b`. Deploy `dep-dav9uk97lnhs73bj35pg`. Anonymous requests for the estimate path, `/icf`, and `/calculators/icf` returned 302 to `/login`. |
| Commit / deployed SHA when closed | Quantity service `1ca26d99c1d95a297bfdf42ad6f07dbb6b0c749e`, deploy `dep-dav7o7p42hec73dbraag`. Workflow product SHA `ff9d6791c4bb16ef50d42a9ca71af2a1d6bc051b`, deploy `dep-dav9uk97lnhs73bj35pg`. |

Missing manufacturer-profile fields, for StyroRail, Logix, Nudura, and Fox Blocks, each source-attributed and versioned:

- product identifiers
- core sizes actually offered
- standard-unit length, height, and wall coverage
- corner-unit coverage
- brick-ledge unit coverage, and which standard units it replaces
- specialty-unit list
- tie, web, clip, and connector count
- concrete-volume factor
- membrane order-unit size and coverage (the membrane name is already stated)
- packaging quantity and order rounding
- reinforcement bar size and spacing for StyroRail, Logix, and Nudura when no engineered schedule is supplied

Fox Blocks reinforcement is not missing a default. The specification requires a project schedule.

Dollar labour authority, inspected 1 Oct 2026: `app/services/labour_engine.py` seeds ORG-001 `DirectLabourCostRateStandard` at $65 CAD per man-hour from `docs/pricing-policy.md`. That rate is organization policy, not an ICF rate, and not a platform default. ICF must use it. It must not create a second dollar rate.

ICF hours: RUNTIME INPUT. The estimator confirms a labour-hour allowance. `ProductionRateStandard` exists and no ICF standard is seeded. The Pratt record is not that standard. An absent production standard does not block the form and concrete quantities.

Stated defaults that are not a full take-off: 8-inch core, 25 MPa ICF mix, RESISTO except Nudura, ICFVL at 16 inches on centre, anchors at 36 inches on centre, 50 anchors per box, and 10-foot 2×4 plates with a 50 percent purchase allowance.

### FRAMING

| Field | Record |
|-------|--------|
| Diagram location | Construction intelligence — framing |
| Purpose | Governed framing quantities. |
| Independent use | BLOCKED — DEPENDENCY IDENTIFIED |
| Workflow use | BLOCKED — DEPENDENCY IDENTIFIED |
| Dependency class | TRUE PLATFORM DEPENDENCY |
| Required dependencies | An accepted framing formula. Dimensions would be runtime inputs after that formula exists. |
| Existing implementation | None in this repository. Bushel framing sheets are case proofs. |
| What is missing | The engine. |
| Build acceptance criteria | One governed engine, independent and workflow use, no second formula. |
| Live verification requirement | Live internal walk after deploy. |
| Commit / deployed SHA when closed | Not closed. |

### ROOFING

| Field | Record |
|-------|--------|
| Diagram location | Construction intelligence — roofing |
| Purpose | Governed roofing quantities. |
| Independent use | BLOCKED — DEPENDENCY IDENTIFIED |
| Workflow use | BLOCKED — DEPENDENCY IDENTIFIED |
| Dependency class | TRUE PLATFORM DEPENDENCY |
| Required dependencies | An accepted roofing formula. |
| Existing implementation | None. |
| What is missing | The engine. |
| Build acceptance criteria | One governed engine. |
| Live verification requirement | Live internal walk after deploy. |
| Commit / deployed SHA when closed | Not closed. |

### SIDING

| Field | Record |
|-------|--------|
| Diagram location | Construction intelligence — siding |
| Purpose | Governed siding quantities. |
| Independent use | BLOCKED — DEPENDENCY IDENTIFIED |
| Workflow use | BLOCKED — DEPENDENCY IDENTIFIED |
| Dependency class | TRUE PLATFORM DEPENDENCY |
| Required dependencies | An accepted siding formula. |
| Existing implementation | None. |
| What is missing | The engine. |
| Build acceptance criteria | One governed engine. |
| Live verification requirement | Live internal walk after deploy. |
| Commit / deployed SHA when closed | Not closed. |

### DRYWALL

| Field | Record |
|-------|--------|
| Diagram location | Construction intelligence — drywall |
| Purpose | Governed drywall quantities. |
| Independent use | BLOCKED — DEPENDENCY IDENTIFIED |
| Workflow use | BLOCKED — DEPENDENCY IDENTIFIED |
| Dependency class | TRUE PLATFORM DEPENDENCY |
| Required dependencies | An accepted drywall formula. |
| Existing implementation | None. |
| What is missing | The engine. |
| Build acceptance criteria | One governed engine. |
| Live verification requirement | Live internal walk after deploy. |
| Commit / deployed SHA when closed | Not closed. |

### FLOORING

| Field | Record |
|-------|--------|
| Diagram location | Construction intelligence — flooring |
| Purpose | Governed flooring quantities. |
| Independent use | BLOCKED — DEPENDENCY IDENTIFIED |
| Workflow use | BLOCKED — DEPENDENCY IDENTIFIED |
| Dependency class | TRUE PLATFORM DEPENDENCY |
| Required dependencies | An accepted flooring formula. |
| Existing implementation | None. |
| What is missing | The engine. |
| Build acceptance criteria | One governed engine. |
| Live verification requirement | Live internal walk after deploy. |
| Commit / deployed SHA when closed | Not closed. |

### FUTURE ENGINES

| Field | Record |
|-------|--------|
| Diagram location | Construction intelligence — later engines |
| Purpose | Engines not yet named as a build. |
| Independent use | DEFERRED |
| Workflow use | DEFERRED |
| Required dependencies | A later named specification. |
| Existing implementation | None. |
| What is missing | Not in the current build. |
| Build acceptance criteria | Not set. |
| Live verification requirement | Not set. |
| Commit / deployed SHA when closed | Not closed. |

---

## C. Core platform capabilities

A route is not a complete capability. Status uses the same four values.

### Project Management

| Field | Record |
|-------|--------|
| Diagram location | Core — project management |
| Purpose | Hold the job: client, location, stage, and the project page. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for the live project hub. |
| Existing implementation | Projects, clients, and the project hub are on the live office. Home and Projects were checked on 30 Sep 2026. |
| What is missing | Guided setup is not on that live SHA. Production management is a separate row. |
| Build acceptance criteria | Met for the live project record. |
| Live verification requirement | Met at live SHA `ca37d8b6939f6494b6ff415bad17953886366728`. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Scope & Work Definition

| Field | Record |
|-------|--------|
| Diagram location | Core — scope |
| Purpose | Confirm what work is needed and who does it. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for the live scope page. |
| Existing implementation | Scope of work is on the hosted office. Catalog remains Site work, Foundation, and Structure. Confirming work does not price it. |
| What is missing | A confirmed package does not call an engine. |
| Build acceptance criteria | Met for confirming work on the live office. |
| Live verification requirement | Re-walked 1 Oct 2026 on synthetic project 51. Foundation / Subcontractor confirmed. Return to setup recalculated. Direct Scope remained available. |
| Commit / deployed SHA when closed | Live SHA `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Drawings & Documents

| Field | Record |
|-------|--------|
| Diagram location | Core — drawings and documents |
| Purpose | Hold the project drawings and the document families. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for upload and the drawings list already live. |
| Existing implementation | Drawings list and upload are on the live office. Seven document families are registered. Most families are not yet available. |
| What is missing | Nothing for the drawings list, the drawing decision, or Build Drawings. See Plan Generation for the candidate and Use result. |
| Build acceptance criteria | Met for the live drawings list. |
| Live verification requirement | Drawings presentation deploy is inside the current live line. |
| Commit / deployed SHA when closed | Live SHA `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Plan Generation

| Field | Record |
|-------|--------|
| Diagram location | Core — plan generation |
| Purpose | Build a dimensioned-plan candidate and register it only when the contractor uses it. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for dimensioned-plan Build Drawings. PGE-1 through PGE-6 are on this live SHA. |
| Existing implementation | Build Drawings for `dimensioned_plan`, candidate, explicit use, and `projects.drawing_requirement`. `stair_detail` is refused on the plans page. |
| What is missing | Nothing for this dimensioned-plan path. Other drawing types are not this row. |
| Build acceptance criteria | Met. A candidate was generated and became a project drawing only after explicit Use. |
| Live verification requirement | Met on 1 Oct 2026. Candidate 1 was not a drawing until Use. Plan document 4 has origin `generated`. Unsupported and incomplete requests were rejected. |
| Commit / deployed SHA when closed | Deployed SHA `ae115059d96028d0e3adf11d20c6ab7d5731901d`. Deploy `dep-dav6kt8jo6nc73fpglg0`. Hosted revision `m3f4a5b6c7d8`. |

### Cost Management

| Field | Record |
|-------|--------|
| Diagram location | Core — cost management |
| Purpose | Company costs used to build estimates. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None. |
| Existing implementation | What we pay. Checked on the live office on 30 Sep 2026. |
| What is missing | Supplier price feeds are not this row. |
| Build acceptance criteria | Met. |
| Live verification requirement | Met at the 30 Sep live walk. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Estimating

| Field | Record |
|-------|--------|
| Diagram location | Core — estimating |
| Purpose | The ordinary estimate. Same capability as the lifecycle Estimate row. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for the ordinary estimate. |
| Existing implementation | See lifecycle Estimate. |
| What is missing | Workflow consumption of an engine is not built. The guided handoff was live-verified on 1 Oct 2026. |
| Build acceptance criteria | Met for the ordinary estimate. |
| Live verification requirement | Hosted UAT 26 Sep 2026, still in the live SHA. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Proposals

| Field | Record |
|-------|--------|
| Diagram location | Core — proposals |
| Purpose | Same capability as the lifecycle Proposal row. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None. |
| Existing implementation | See lifecycle Proposal. |
| What is missing | Not re-walked on 1 Oct 2026. |
| Build acceptance criteria | Met. |
| Live verification requirement | Hosted UAT 26 Sep 2026. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Contracts

| Field | Record |
|-------|--------|
| Diagram location | Core — contracts |
| Purpose | Same unfinished capability as Contract Signing. |
| Current status | NOT STARTED |
| Required dependencies | See Contract Signing. |
| Existing implementation | Partial FG-024 and FG-033. Not the finished contractor path. |
| What is missing | The complete contract capability. |
| Build acceptance criteria | See Contract Signing. |
| Live verification requirement | Live signed contract. |
| Commit / deployed SHA when closed | Not closed. |

### Change Orders

| Field | Record |
|-------|--------|
| Diagram location | Core — change orders |
| Purpose | Same capability as the lifecycle Change Orders row. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for the existing record. |
| Existing implementation | See lifecycle Change Orders. |
| What is missing | Future change-order document family. |
| Build acceptance criteria | Met for the live record. |
| Live verification requirement | Included in the live office SHA. Not re-walked on 1 Oct 2026. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Production Management

| Field | Record |
|-------|--------|
| Diagram location | Core — production management |
| Purpose | Same unfinished capability as Build / Manage. |
| Current status | NOT STARTED |
| Required dependencies | See Build / Manage. |
| Existing implementation | Field, calendar, and schedule pieces only. |
| What is missing | The complete production capability. |
| Build acceptance criteria | See Build / Manage. |
| Live verification requirement | Live production walk. |
| Commit / deployed SHA when closed | Not closed. |

### Analytics & Reporting

| Field | Record |
|-------|--------|
| Diagram location | Core — analytics |
| Purpose | Same unfinished capability as Analytics / Reporting. |
| Current status | NOT STARTED |
| Required dependencies | None named. |
| Existing implementation | None found as a product. |
| What is missing | The capability. |
| Build acceptance criteria | A live report. |
| Live verification requirement | Live office. |
| Commit / deployed SHA when closed | Not closed. |

### Calendar

| Field | Record |
|-------|--------|
| Diagram location | Core — calendar |
| Purpose | Company calendar for the office. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None. |
| Existing implementation | Company Calendar is the schedule destination. Schedule hubs were live-tested in FG-035. |
| What is missing | Not re-walked on 1 Oct 2026. |
| Build acceptance criteria | Met for the live calendar. |
| Live verification requirement | Included in the live office. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Mapper

| Field | Record |
|-------|--------|
| Diagram location | Core — calculation mapper |
| Purpose | Review a governed result and add a line only after confirmation. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for the existing mapper. |
| Existing implementation | `app/services/calculation_estimate_mapping.py`. Mapper human UAT is recorded PASS. A 30 Sep live smoke passed on the prior deploy, and the current live SHA still contains that office. |
| What is missing | Setup does not start the mapper. A confirmed scope package does not call an engine. |
| Build acceptance criteria | Met: nothing is added until confirmation. |
| Live verification requirement | Re-walked 1 Oct 2026. A thickened-edge result showed 0 added before confirmation. After an explicit confirm, line 135 held 9.45 m3. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Company Library

| Field | Record |
|-------|--------|
| Diagram location | Core — company library |
| Purpose | Past jobs and company records the office reuses. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for historical estimate review already in the office. |
| Existing implementation | Historical estimate ingestion and review. Brand profile entry was checked live on 30 Sep 2026. |
| What is missing | Learning that writes back into defaults. |
| Build acceptance criteria | Met for the existing library surfaces. |
| Live verification requirement | Brand profile live walk 30 Sep 2026. Historical review is in that office. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Reusable Work

| Field | Record |
|-------|--------|
| Diagram location | Core — reusable work |
| Purpose | Assemblies the estimate can use. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for the existing assembly list. |
| Existing implementation | Reusable work lists assemblies. The mapper can confirm a quantity onto an assembly. |
| What is missing | An engine does not fill an assembly by itself. |
| Build acceptance criteria | Met for the live list and mapper target. |
| Live verification requirement | Included in the live office. The 30 Sep walk checked What we pay, not a separate reusable-work click. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Labour / Pricing Intelligence

| Field | Record |
|-------|--------|
| Diagram location | Core — labour and pricing |
| Purpose | Company labour rates and the pricing policy that turns direct cost into a price. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for the office foundations already live. |
| Existing implementation | FG-008 labour standards and FG-009 pricing policies are in the live office. How we price explains the commercial meaning. |
| What is missing | The contractor labour experience that was recorded as not started. Learning does not change a rate. |
| Build acceptance criteria | Met for the existing rate and pricing foundations, not for a future labour walk. |
| Live verification requirement | Pricing and labour foundations are in the live SHA. Not re-walked on 1 Oct 2026. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

---

## D. Data / learning foundation

Architecture or stored rows are not a finished learning product.

### Projects / Clients / Locations

| Field | Record |
|-------|--------|
| Diagram location | Data — projects, clients, locations |
| Purpose | The records setup and the estimate read. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None. |
| Existing implementation | Clients, projects, and project location are on the live office. |
| What is missing | Nothing for the live client, project, and location records. The 1 Oct walk completed location on project 51 and setup advanced from that record. |
| Build acceptance criteria | Met for the live records. |
| Live verification requirement | Clients checked 30 Sep 2026. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Drawings / Documents

| Field | Record |
|-------|--------|
| Diagram location | Data — drawings and documents |
| Purpose | Stored plans and document families. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | Plan-generation tables are a separate blocked row. |
| Existing implementation | Plan upload and the drawings list are live. |
| What is missing | Nothing for stored plans or the hosted candidate and drawing-requirement revisions. Hosted revision is `m3f4a5b6c7d8`. |
| Build acceptance criteria | Met for documents already on the hosted database. |
| Live verification requirement | Live drawings list is in the current deploy. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Trade Engine Results

| Field | Record |
|-------|--------|
| Diagram location | Data — trade engine results |
| Purpose | Store a Contract V1 result the mapper can review. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for loading a result that already matches the contract. |
| Existing implementation | Mapper intake of a valid Contract V1 result. Concrete and stair results are produced on the Website, not stored here as a workflow. |
| What is missing | ICF results. Workflow production from a project. |
| Build acceptance criteria | Met for review of a loaded result. |
| Live verification requirement | Mapper live smoke recorded. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Estimates / Proposals

| Field | Record |
|-------|--------|
| Diagram location | Data — estimates and proposals |
| Purpose | The commercial records. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None. |
| Existing implementation | See Estimate and Proposal. |
| What is missing | Nothing for the commercial records already live. The 1 Oct walk used synthetic estimates only. |
| Build acceptance criteria | Met. |
| Live verification requirement | Hosted UAT 26 Sep 2026. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Contracts / Change Orders

| Field | Record |
|-------|--------|
| Diagram location | Data — contracts and change orders |
| Purpose | Signed contracts and change-order records. |
| Current status | NOT STARTED |
| Required dependencies | Contract signing is not started as a complete capability. Change-order records exist and are closed on their own row. This combined learning input is not complete without contracts. |
| Existing implementation | Change-order records. Partial contract slices. |
| What is missing | Executed contracts as learning data. |
| Build acceptance criteria | A live signed contract stored with the project. |
| Live verification requirement | Live office. |
| Commit / deployed SHA when closed | Not closed. |

### Actual Costs / Quantities

| Field | Record |
|-------|--------|
| Diagram location | Data — actual costs and quantities |
| Purpose | What the job used. |
| Current status | NOT STARTED |
| Required dependencies | See Actuals. |
| Existing implementation | FG-023 direct-cost actuals only. |
| What is missing | The finished actuals record. |
| Build acceptance criteria | See Actuals. |
| Live verification requirement | See Actuals. |
| Commit / deployed SHA when closed | Not closed. |

### Reusable Work / Assumptions

| Field | Record |
|-------|--------|
| Diagram location | Data — reusable work and assumptions |
| Purpose | Assemblies and the assumptions a result carries. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for assemblies and Contract V1 assumptions already accepted by the mapper. |
| Existing implementation | Assemblies. Contract V1 assumption list on a loaded result. |
| What is missing | Assumptions do not train a default. |
| Build acceptance criteria | Met for storage and review. |
| Live verification requirement | Included in the live mapper office. |
| Commit / deployed SHA when closed | `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Learning / Historical Data

| Field | Record |
|-------|--------|
| Diagram location | Data — learning and historical data |
| Purpose | Historical jobs and a governed way to improve defaults. |
| Current status | NOT STARTED |
| Required dependencies | The learning product. Historical workbooks can be reviewed. They do not change a formula. |
| Existing implementation | FG-006 historical ingestion. Learning law on the checklist. |
| What is missing | Approved calibration. |
| Build acceptance criteria | A person approves a change. One job does not silently change a default. |
| Live verification requirement | Live approval. |
| Commit / deployed SHA when closed | Not closed. |

---

## Supplier commercial layer

This layer does not change the contractor platform. It is not implemented.

### SUPPLIER PRO PLATFORM PARTNERSHIP

| Field | Record |
|-------|--------|
| Diagram location | Around the contractor platform. Not inside organization ownership. |
| Purpose | Supplier sponsorship and entitlement around an existing contractor organization. |
| Current status | NOT STARTED |
| Dependency class | Sequencing only. No item below is BLOCKED. |
| Required dependencies | The contractor organization, project, estimate, and privacy boundary already exist and stay in place. Each later item depends on the item before it. External POS, ERP, and order integration is last and is not required for earlier measurement. |
| Existing implementation | Organization isolation, membership, projects, clients, locations, calculation engines, Contract V1, the mapper, Cost Library, estimates, proposals, and change orders. Supplier Connection direction is already recorded. FG-029 is the closed office package workflow. FG-030 supplier login remains recorded and not authorized. None of that is this partnership. |
| What is missing | The eight queued capabilities below. The BMR PRO Hub is recorded under this row and is also not started. |
| Build acceptance criteria | A later authorized slice for item 1 only, reusing the contractor organization and granting no unrestricted supplier membership. |
| Live verification requirement | Not available. This row is architecture only. |
| Commit / deployed SHA when closed | Not closed. This recording is not deployed. |

Implementation sequence:

1. Supplier identity / hierarchy. Depends on the existing organization boundary. Does not create a second contractor account.
2. Sponsorship / entitlement. Depends on item 1. Ending sponsorship does not end or transfer the contractor account.
3. Supplier permission / privacy foundation. Depends on item 2. Default visibility is aggregated and anonymized.
4. Material Opportunity / attribution. Depends on item 3 and on a project material requirement. Classes are POTENTIAL, ATTRIBUTED, and VERIFIED.
5. Contractor-authorized transaction. Depends on item 4. The contractor starts the share.
6. Supplier ROI & Opportunity Dashboard. Depends on items 3 and 4. It can measure adoption and submitted opportunity before an external integration. It is not a second economic model. It must use the 30 Aug 2026 supplier-channel specification and the operational ROI extension.

Operational ROI / Takeoff Capacity Extension. Subcomponent of this partnership. The formulas are in the architecture. The live meeting surface is the separate row below. It is not a second model and it is not the dashboard.
7. Dealer / store reporting. Depends on items 1 and 6. One dealer does not see another dealer’s private commercial information.
8. POS / ERP / order integrations. Depends on item 5. Later capability.

BMR Winchester is the first pilot context. The row stays supplier-neutral.

### BMR PRO HUB

| Field | Record |
|-------|--------|
| Diagram location | Supplier-side operating surface around the same contractor platform. Not inside the contractor organization. |
| Purpose | The daily environment for an authorized supplier user. Two initial surfaces: OPERATE (Supplier Console / Transaction Workspace) and SELL / SERVE (PRO Tools / Calculator Hub). UNDERSTAND and MEASURE are conceptual only. |
| Current status | **RECORDED / NOT STARTED**. Architecture only. Not implementation-authorized. |
| Dependency class | Sequencing only. This row does not start the eight-item partnership sequence and does not block it. |
| Required dependencies | The eight-item partnership sequence above. The calculator hub reuses existing governed calculation engines. It does not create a BMR calculator. |
| Existing implementation | None. The live meeting page `/supplier-program/economic-model` is the operational ROI surface. It is not the hub, not the console, and not the ROI dashboard. |
| What is missing | All seven components below. |
| Build acceptance criteria | Not available. A later prompt must authorize one component. This row does not. |
| Live verification requirement | Not available. |
| Commit / deployed SHA when closed | Not closed. Not deployed. |

Components, none implemented:

1. Supplier Console / Transaction Workspace. Transaction-centric queues. No uncontrolled feed of contractor activity.
2. PRO Tools / Calculator Hub. The same governed engines in a public, BMR-staff, or contractor context. One engine. No contractor-private access merely because the calculator is open.
3. Supplier permissions / hierarchy. Supplier / Banner → Dealer / Ownership Group → Store → Authorized Supplier User → Sponsored / Authorized Contractor. A store user does not gain network visibility.
4. Authorized transaction firewall. The contractor keeps customers, projects, labour rates, costs, margins, profitability, other suppliers, private estimates, internal notes, and unrelated activity.
5. Acknowledgement / status workflow. Change requested, notified, acknowledged, accepted or rejected, status returned. Text may notify. The transaction system holds the acknowledgement.
6. Material Opportunity integration. Project → material requirement → supplier opportunity → quote → order. Classes remain POTENTIAL, ATTRIBUTED, and VERIFIED.
7. Supplier ROI / measurement integration. Console events may later evidence the existing economic model. No second model. The ROI dashboard stays future.

The hub does not change contractor ownership, sponsorship-as-entitlement, non-exclusivity, or supplier neutrality.

## Supplier economic model — live meeting surface

| | |
|---|---|
| Current status | **CLOSED — LIVE VERIFIED** |
| Dependency class | None. Office login already exists. |
| Required dependencies | The supplier-channel specification, ADR-033, and the operational ROI extension. |
| Existing implementation | `/supplier-program/economic-model`. Typed assumptions. Immediate results. No stored supplier ROI. No contractor project, estimate, margin, or labour-rate read. |
| What is missing | The Supplier ROI & Opportunity Dashboard remains unbuilt. Supplier Pro identity and sponsorship remain not started. |
| Live verification requirement | Met. Anonymous request redirects to login. Hosted file returns labour value 12000.00 for the recorded partial scenario. |
| Commit / deployed SHA when closed | Product SHA `c6aa88a05ed91492160664b2ba110ba6c07adba0`. Deploy `dep-dav8ul7pn0mc739lhfmg`. |

Supplier Pro as a partnership remains **NOT STARTED**.

---

## Dependency graph

```text
ICF manufacturer profile registry
  CLOSED — LIVE VERIFIED
ICF 8-inch form and concrete quantities
  RUNTIME INPUT for area and corner counts
  manufacturer method is already in the profile
  not a development blocker
ICF dollar labour
  INSTANCE-OWNER INPUT
  ORG-001 is $65 CAD per man-hour
ICF labour hours
  RUNTIME INPUT
  confirmed allowance
  Pratt hours stay evidence

Framing, Roofing, Siding, Drywall, Flooring
  TRUE PLATFORM DEPENDENCY
  no accepted formula

Concrete and Stair workflow use
  TRUE PLATFORM DEPENDENCY
  public formulas stay on the Website
  this repository does not copy them

Contract Signing
  TRUE PLATFORM DEPENDENCY
  no counsel-approved production package

Build / Manage
  TRUE PLATFORM DEPENDENCY
  no accepted finished-stage specification

Actuals
  RUNTIME INPUT for a direct-cost amount
  TRUE PLATFORM DEPENDENCY for a finished quantity-actuals product

Complete / Close
  TRUE PLATFORM DEPENDENCY
  no completion sign-off

Learn & Improve
  TRUE PLATFORM DEPENDENCY
  the learning product is not built

Analytics / Reporting
  TRUE PLATFORM DEPENDENCY
  no accepted reporting specification

Future engines
  DEFERRED

Supplier Pro Platform Partnership
  NOT STARTED
  additive sponsorship layer
  sequence is identity, sponsorship, privacy, opportunity,
  authorized transaction, ROI dashboard, dealer reporting,
  then POS/ERP integration
BMR PRO Hub
  RECORDED / NOT STARTED
  supplier-side console and calculator hub
  not implementation-authorized
```

## Ready components

The 8-inch ICF form and concrete service is closed on the live office. Wall area and corner counts are runtime inputs. The dollar rate already exists. Labour hours are a confirmed allowance. The result uses Contract V1 and stays internal. The project workflow that asks for those inputs is the next component.

Framing, Roofing, Siding, Drywall, and Flooring are not build-ready. No accepted formula exists. Concrete and Stair are not rebuilt here.

## Blocked components

| Component | Exact dependency |
|-----------|------------------|
| ICF quantities | CLOSED — LIVE VERIFIED for the internal 8-inch form and concrete service. Deploy `dep-dav7o7p42hec73dbraag`. |
| ICF hours | RUNTIME INPUT. The estimator confirms the allowance. No ICF production standard is seeded. |
| Framing | Governed V1 specification: formula authority, assumptions, inputs, outputs, test vectors, Contract V1 compatibility, public/private classification, Platform workflow boundary. |
| Roofing | The same missing set as Framing. |
| Siding | The same missing set as Framing. |
| Drywall | The same missing set as Framing. |
| Flooring | The same missing set as Framing. |
| Start Project | None. CLOSED — LIVE VERIFIED on deploy `dep-dav6kt8jo6nc73fpglg0`. |
| Guided Project Setup | None. CLOSED — LIVE VERIFIED on that same deploy. |
| Plan Generation | None. CLOSED — LIVE VERIFIED on that same deploy. |
| Contract Signing | Legal Content Gate is empty. Production legal packages are 0. Family 05 is not legally approved. |
| Build / Manage | No governed specification for execution, progress, labour, materials, equipment, issues, and task execution. |
| Actuals | No governed capture of actual labour, materials, equipment, and subcontract cost against the estimate, contract, and change orders. |
| Complete / Close | No accepted decision to extend the existing project lifecycle through completion sign-off. |
| Learn & Improve | Actuals. |

## Deferred components

Future engines.

## Specification factory

No formulas were written.

| Engine | Missing dependency |
|--------|-------------------|
| ICF | Eight-inch form and concrete methods are in the profile. Hours are a runtime allowance. Classification is internal Platform only. |
| Framing | The full V1 specification set. |
| Roofing | The full V1 specification set. |
| Siding | The full V1 specification set. |
| Drywall | The full V1 specification set. |
| Flooring | The full V1 specification set. |

## Cross-cutting constraint — governed document and drawing output

| Field | Record |
|-------|--------|
| Name | GOVERNED DOCUMENT + DRAWING OUTPUT STANDARD |
| Purpose | Every governed issued document and drawing uses the Organization Brand Profile and the existing customer, internal, and supplier information boundaries. |
| Current status | NOT STARTED as a general renderer. The constraint is in force. |
| Dependency class | TRUE PLATFORM DEPENDENCY for a shared renderer. A case may issue an interim file that consumes the existing identity. |
| Existing authority | [governed-document-and-drawing-output-standard.md](governed-document-and-drawing-output-standard.md). [FG-012](../feature-gates/FG-012-estimate-output-consistency.md). [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md). `app/services/proposal_pdf.py`. `app/templates/proposals/preview.html`. `app/templates/estimates/internal_breakdown.html`. |
| What this row is not | A new branding engine, a new database model, or a second customer-estimate PDF generator. |
| Closure rule | No future document-generation component is closed until it meets the standard. |
| Linda Bushel | The generic 1 Oct Markdown-to-PDF package is superseded. Historical case records stay. The replacement J1 files consume the governed identity and remain replaceable. |

## Cross-cutting component — construction model and drawing set

| Field | Record |
|-------|--------|
| Name | CONSTRUCTION MODEL AND DRAWING SET |
| Purpose | One governed Construction Model projects every construction view, and the sheet layer composes those views onto a print-ready 11×17 set. |
| Current status | **OPEN / NOT COMPLETE**. Slices 1 through 11 are **IMPLEMENTED / TESTED**. Slice 12 is the acceptance audit. Slice 13 presents callouts, section and detail references, the drawing index, and construction schedules from that same model. Slice 14 draws connector geometry only when the model supplies it. Slice 15 supplies the remaining generic fixture facts the model can already store, and a stair result can carry a riser count. Slice 16 moves annotations in paper space and does not move the model. Slice 17 stores blocking as fixture members with explicit fastenings. Slice 18 moves bearing notes off the contact. No new generic capability is required before a real project model is read. Slice 19 reads the Bushel proving fixture through that engine. Missing Bushel facts refuse. Slice 20 loads no further governed fact. Visual acceptance for a crew set is not passed. The audit is [reviews/2026-10-02-complete-deck-acceptance/COMPLETE-DECK-ACCEPTANCE-AUDIT.md](reviews/2026-10-02-complete-deck-acceptance/COMPLETE-DECK-ACCEPTANCE-AUDIT.md). Bushel is not the acceptance fixture. Not deployed. |
| Slice 1 | A deck-class model is one element store. A missing required fact returns a stable field and “You need to provide this information.” Uncertainty stays on the model. Optional collections do not block completeness. No project, plan, or estimate write. |
| Slice 2 | Plan, front elevation, and side elevation are projections of that model. A view definition is a camera. It does not own members. An incomplete model returns the slice 1 refusal and no projected elements. |
| Slice 3 | Those three projections are composed on one 11×17 sheet at the stated scale. A scale that does not fit is refused. The project status comes from the model. The generic PGE disclaimer is not printed on that sheet. |
| Slice 4 | Stair, section, detail, and schedule views read the same model. The stair view uses a supplied result and does not calculate rise, run, throat, nosing, stringer count, tread count, or width. A missing fact refuses that view. Extra views use further 11×17 sheets at the same scale. |
| Slice 5 | Bushel proving fixture. Governed decisions only. Missing shaft length, helix, torque, bracket height, post cut, baluster layout, stringer plumb cuts, upper elevation, rise, run, nosing, and tread count refuse the affected views. The generated sheets are not a set to hand to the crew. Review: [reviews/2026-10-02-bushel-proving/BUSHEL-CONSTRUCTION-MODEL-REVIEW.md](reviews/2026-10-02-bushel-proving/BUSHEL-CONSTRUCTION-MODEL-REVIEW.md). |
| Slice 6 | Partial coordinates, view-specific refusal, sheet sets, construction-notation dimensions, level datums, and overlap tags that do not move the model. The proving set was run again. It is still not a crew set. |
| Slice 7 | Paper-space callouts, dimension chains, and required-view placement. Crowded stations keep their coordinates and share a callout. A missing station refuses that dimension. A required view that cannot fit is refused instead of omitted. The proving set was run again. It is still not a crew set. |
| Slice 8 | Deck component model. Roles, support kinds, member size, explicit relationships, and supplied connections. Endpoint length is derived. A conflicting length is refused. A pier can exist without shaft data. The proving set was run again. It is still not a crew set. |
| Slice 9 | Complete generic deck fixture and a governed sheet program. Plans, elevations, stair, section, details, and schedules read one model. The printed fixture set was inspected. It is not a set to hand to the crew. Bushel was not changed. |
| Slice 10 | Rectangular profiles, including a sloped stringer, detail windows at a larger governed scale, and grouped member, connection, and material schedules. The printed fixture set was inspected again. It is not a set to hand to the crew. Bushel was not changed. |
| Slice 11 | Explicit construction relationships and supplied bearing. Kinds are supports, protects, bears_on, connects_to, and fastened_to. A contradictory bearing is refused and the members stay where they were. Connection geometry is drawn only when supplied. The printed fixture set was inspected again. The stringer seat and the post/beam contact read. The whole set is still not a crew set. Bushel was not changed. |
| Slice 12 | Acceptance audit of the complete deck fixture. No drawing change. Fifteen deficiencies, classes A through D. None are a new architectural dependency. The set is not a crew set. |
| Slice 13 | Drawing references and schedule presentation. Member callouts, section cuts, detail references, a sheet index, and schedule columns are derived from the model and the sheet set. One relationship pair has one bearing answer. A required detail with no connection is marked NOT ISSUED. No new fixture facts. The set is still not a crew set. |
| Slice 14 | Governed connector geometry. A supplied plate, thickness, bolt diameter, and fastener locations draw on the relationship they serve. A connector name, fastener, and quantity do not become a shape. The fixture post cap is generic test geometry. The fixture tread clip stays metadata only. The set is still not a crew set. |
| Slice 15 | Complete generic fixture data and a stair riser-count field. The fixture supplies the remaining post and pier bearings, metadata-only guard, joist, and stair connections, and dimension chains on members the model already has. The drawing prints the stored riser count and does not calculate it. Pier depth and baluster spacing stay on the schedule where the sheet has no clear place. The set is still not a crew set. |
| Slice 16 | Drawing annotation layout. Connector notes move off the members. A leader does not cut through another member to take a shorter path. Existing dimension values stay. GEOMETRY NOT SUPPLIED stays a note. The set is still not a crew set. |
| Slice 17 | Blocking. The fixture supplies 18 blocking members on the beam stations it already has, each fastened to the joist or rim it spans. The framing plan, the section cut, and the member schedule read those members. A removed piece is not inferred. No ledger and no connector shape were added. The set is still not a crew set. |
| Slice 18 | Bearing annotation. The words move off the contact. The contact line stays. Equivalent bearings share one note and keep the relationship ids. No fixture fact was added. No new generic capability is required before a real project model is read. The set is still not a crew set. |
| Slice 19 | Bushel proving pass. The proving fixture was read by the generic engine. Missing project facts refuse. No Bushel value was added to the engine. The set is not a crew set. Review: [reviews/2026-10-03-bushel-construction-model/BUSHEL-REAL-WORLD-PROVING.md](reviews/2026-10-03-bushel-construction-model/BUSHEL-REAL-WORLD-PROVING.md). |
| Slice 20 | Bushel input completion. No new governed fact was available to load. The 29 Sep sizes, beam coordinates, and pool curve stay unresolved. The regenerated PDF matches Slice 19. No engine change. The set is not a crew set. |
| Dependency class | PGE-1 through PGE-6 remain **CLOSED** and unchanged. |
| Existing authority | [construction-drawing-standard.md](construction-drawing-standard.md). Branding remains [governed-document-and-drawing-output-standard.md](governed-document-and-drawing-output-standard.md). |
| What this row is not | A change to `dimensioned_plan`, `stair_detail`, Contract V1, the candidate and use boundary, Build Drawings, or the drawing requirement. Not a Bushel script. Not a red-box screen. Not drawing-driven take-off. Slices 1 through 20 are not a FreeCAD integration. |
| Closure rule | A Bushel-class construction set is generated from one governed model. A missing required fact causes refusal. Printed output is 11×17. No view invents geometry. Every view agrees with the model. The printed sheet is acceptable to hand to the crew. |
| Professional sheet engine | Recorded 5 Oct 2026, revised the same day after the proof. FreeCAD TechDraw failed visual acceptance and was not adopted. The recorded architecture is a hybrid: Construction Model authority, headless OpenCASCADE projection out of process, Calibrayt sheet composition, PDF. The ReportLab renderer remains the baseline for diagrams, previews, non-CAD documents, and refusal sheets. Nothing from the reassessment is installed. |

## Current build

ICF PROFILE REGISTRY: CLOSED — LIVE VERIFIED. Deploy `dep-dav6kt8jo6nc73fpglg0`. SHA `ae115059d96028d0e3adf11d20c6ab7d5731901d`. Hosted revision `m3f4a5b6c7d8`.

ICF ESTIMATOR: the internal 8-inch form and concrete service and its estimate workflow are CLOSED — LIVE VERIFIED. Workflow product SHA `ff9d6791c4bb16ef50d42a9ca71af2a1d6bc051b`. Deploy `dep-dav9uk97lnhs73bj35pg`. The earlier quantity-service deploy `dep-dav7o7p42hec73dbraag` remains the calculation ancestor.

ICF LABOUR: RUNTIME INPUT for hours. INSTANCE-OWNER INPUT for the existing ORG-001 dollar rate. No second rate is created.

SUPPLIER PRO PLATFORM PARTNERSHIP: NOT STARTED. Architecture only. Not deployed. It does not change the contractor platform. BMR PRO HUB: RECORDED / NOT STARTED (2026-10-02). Not implementation-authorized. Not deployed.

Start Project, Guided Project Setup, and Plan Generation are CLOSED — LIVE VERIFIED. Checklist step 6 shows the unbound and subcontract boundaries on Continue setup. The first work-element binding is **IMPLEMENTED / TESTED**: baseline `ICF` → `icf_wall`. `SITE`, `FOUND`, and `STRUCT` stay unbound. Migration `n4a5b6c7d8e9` is not applied to the Mac primary or the hosted database. This binding is not deployed. CONSTRUCTION MODEL AND DRAWING SET is **OPEN / NOT COMPLETE**. Slices 1 through 10 are **IMPLEMENTED / TESTED** and not deployed. The sheet does not scale to fit. The proving set does not meet the printed-sheet standard. Visual acceptance for the complete deck fixture is not passed. The 1 Oct live walk also recorded non-blocking table overflow on the project hub at 520 and 390, and on the estimate versions table at 1280 with the sidebar open. That overflow is NON-BLOCKING UX/POLISH and is left for the later UX stitching phase.

Remaining profile gaps that do not block the 8-inch standard quantity start:

| Field | Current value | Required for 8-inch form and concrete? | Classification | Governed path | Blocks the engine? |
|-------|---------------|------------------------------------------|----------------|---------------|---------------------|
| Logix standard coverage | 5.33 sf, verified | Yes | Approved manufacturer source | USA Design Manual | No |
| Logix per-form concrete | NOT_ESTABLISHED | No. The 0.667 ft cavity factor is the stated method | Approved manufacturer source | Use the stored factor | No |
| Nudura standard concrete | 0.306 yd3, verified | Yes | Approved manufacturer source | Installation Manual 2.2.3 | No |
| Corner counts | Supplied per wall | Yes | RUNTIME INPUT | Enter the count, including zero | No |
| Fox packaging | NOT_ESTABLISHED | No for the form count | INSTANCE-OWNER INPUT | Enter a supplier-confirmed bundle quantity | No |
| Approved reinforcement default | NOT_ESTABLISHED | No for form and concrete | RUNTIME INPUT | The project schedule | No |
| ICF labour hours | No production standard | No for form and concrete | RUNTIME INPUT | Confirm a labour-hour allowance | No |
| ICF labour dollar rate | $65 CAD per man-hour | When a price is formed later | INSTANCE-OWNER INPUT | Existing ORG-001 standard | No |
