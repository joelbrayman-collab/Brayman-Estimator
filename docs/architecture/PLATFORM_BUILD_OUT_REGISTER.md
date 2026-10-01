# Platform Build-Out Register

| Attribute | Value |
|-----------|--------|
| Status | Tactical construction register |
| Date | 2026-10-01 |
| Repository | `/Users/joelbrayman/Desktop/Brayman-Estimator` |
| Inspected HEAD | `c1ab362` plus this register update. Prior register commit `8b1d883`. |
| Live product SHA | Last recorded `ca37d8b6939f6494b6ff415bad17953886366728`. Deploy `dep-daulf9u0tbcc73bomdgg`. Not re-proved in this recording. |
| Hosted database | Last recorded `k1f2a3b4c5d6`. Not re-proved. Not migrated to repository head `m3f4a5b6c7d8`. |
| Mac primary | Last verified `h8c9d0e1f2a3`. Not migrated. |

This register is the tactical source of truth for what gets built next. The lifecycle blueprint remains the strategic reference. A row is not closed because a route, an architecture note, or a local test exists.

Allowed statuses:

| Status | Meaning |
|--------|---------|
| CLOSED — LIVE VERIFIED | Implemented, tested, documented, committed, pushed, deployed, and checked on the live surface named in the row. |
| BLOCKED — DEPENDENCY IDENTIFIED | Work cannot finish until the named dependency is available. |
| NOT STARTED | The complete capability is not built. An earlier partial foundation may be named in the row. |
| DEFERRED | Intentionally later. Not the current build. |

## Occupancy used for this record

Live office verification already on record is the 30 Sep 2026 deploy of `ca37d8b6939f6494b6ff415bad17953886366728`. That walk covered the office logo, Home, Projects, Clients, What we pay, and Brand Profile. Hosted read-only UAT on 26 Sep 2026 opened Estimates, one Estimate, and Proposals. This 1 Oct recording did not open the live office again.

Start New Project and Guided Project Setup are on `origin/main` and are not in that live SHA. Deployment of those commits was not performed. This register therefore does not mark them CLOSED — LIVE VERIFIED.

Concrete and Stair are closed on the public Website, not in this repository. Website Version 31 SHA `5dcb4f2b9cc0a291a16375f06ce89f09a02262cf` is the recorded live public checkpoint.

---

## A. Project lifecycle

### START PROJECT

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — start |
| Purpose | Open a project for a client in this company and land on setup. |
| Current status | BLOCKED — DEPENDENCY IDENTIFIED |
| Required dependencies | Deploy the accepted product SHA that contains Start New Project, and migrate the hosted database from last recorded `k1f2a3b4c5d6` through `l2f3a4b5c6d7` and `m3f4a5b6c7d8` under the governed sequence. Auto-deploy is off. |
| Existing implementation | `/projects/new` redirects to Continue setup. Code is on `origin/main` at `f82641b81c7c5d8eae96156f0540e410f4073a6a`. Local suite after SNP-6: 1931 passed. |
| What is missing | Live verification. The live SHA is still `ca37d8b6939f6494b6ff415bad17953886366728`. |
| Build acceptance criteria | A new project in the live office opens Continue setup for that project. |
| Live verification requirement | Walk new project on `https://calibryatai.onrender.com` after the deploy of the accepted SHA. |
| Commit / deployed SHA when closed | Not closed. |

### GUIDED PROJECT SETUP

| Field | Record |
|-------|--------|
| Diagram location | Project lifecycle — guided setup |
| Purpose | Read the project and open the existing page for the first gap. |
| Current status | BLOCKED — DEPENDENCY IDENTIFIED |
| Required dependencies | Same deploy and hosted-database dependency as Start Project. |
| Existing implementation | `GET /projects/<id>/setup` in `app/routes/project_setup.py`. First gap in `app/services/start_project_walk.py`. Local end-to-end review on 1 Oct 2026 held through location, drawings, scope, estimate, and mapper confirmation. |
| What is missing | That experience is not on the live SHA. |
| Build acceptance criteria | Continue setup on the live office names the current project and one next existing page. |
| Live verification requirement | Walk an existing project and a new project on the live office after deploy. |
| Commit / deployed SHA when closed | Not closed. |

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
| What is missing | The guided setup handoff is not in the live SHA. That gap is recorded on Guided Project Setup, not as a second estimate. |
| Build acceptance criteria | Already met for the ordinary estimate on the live office. |
| Live verification requirement | Met by the recorded hosted UAT and the live deploy that still contains it. Not re-walked on 1 Oct 2026. |
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
| Current status | NOT STARTED |
| Required dependencies | A complete signing path. Partial library and native-signing slices are not that path. |
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
| Current status | NOT STARTED |
| Required dependencies | None named for a later production-management capability. |
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
| Current status | NOT STARTED |
| Required dependencies | Completion sign-off, which is not implemented. |
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
| Required dependencies | None named beyond the monitor foundation. |
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
| Current status | NOT STARTED |
| Required dependencies | Actuals as a finished input. The learning law is recorded. The product is not built. |
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
| Current status | NOT STARTED |
| Required dependencies | None named. Reports were removed from daily navigation. Routes that remain are not this capability. |
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
| Workflow use | NOT STARTED |
| Required dependencies | Workflow use waits for an accepted project-consumption slice. Checklist row 8. |
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
| Workflow use | NOT STARTED |
| Required dependencies | Workflow use waits for an accepted project-consumption slice. |
| Existing implementation | One public stair formula on the Website. Bushel scripts are case evidence, not a second engine. No stair engine is in this repository. |
| What is missing | Platform workflow consumption. |
| Build acceptance criteria | Independent use is already closed. Workflow use must not create a second stair formula. |
| Live verification requirement | Independent use: Website calculation PASS, visual PASS, pin PASS at Version 31. |
| Commit / deployed SHA when closed | Independent use: Website SHA `5dcb4f2b9cc0a291a16375f06ce89f09a02262cf`. |

### ICF

| Field | Record |
|-------|--------|
| Diagram location | Construction intelligence — ICF |
| Purpose | Internal governed ICF takeoff: materials, labour inputs, and direct-cost inputs. Final selling price stays with estimating. |
| Independent use | BLOCKED — DEPENDENCY IDENTIFIED |
| Workflow use | BLOCKED — DEPENDENCY IDENTIFIED |
| Required dependencies | The design specification is present: `docs/architecture/Brayman_ICF_Estimator_V1_Design_Specification.md`, commit `c1ab362`. The quantity engine remains blocked. Missing from that file: versioned manufacturer profiles with block dimensions, wall coverage, concrete-volume factors, and packaging, each tied to approved primary documentation; approved reinforcement defaults for StyroRail, Logix, and Nudura when no engineered schedule is supplied; a governed labour rate. The Mike Pratt note, 200 hours for about 1,680 square feet and a planning range of 220–240 hours, is evidence, not a rate. Fox Blocks already requires a project schedule. Contract V1 can carry `icf_wall`. It does not supply these numbers. |
| Existing implementation | The design specification only. No ICF calculator, route, or formula. |
| What is missing | The profile numbers and the engine. Stated defaults that are not a full take-off: 8-inch core, 25 MPa ICF mix, RESISTO membrane except Nudura, ICFVL at 16 inches on centre, anchors at 36 inches on centre, 50 anchors per box, and 10-foot 2×4 plates with a 50 percent purchase allowance. |
| Build acceptance criteria | After the specification is in the repository: one internal engine, two fixtures, no public page, no second estimate, no silent price, no project or estimate mutation during calculation. |
| Live verification requirement | After implementation, deploy, and a live internal walk. Not available while the specification is missing. |
| Commit / deployed SHA when closed | Not closed. No ICF commit. |

The 1 Oct 2026 continuous wave read the design specification. It authorizes no public calculator and no second estimate. It does not contain block geometry or a labour formula. Those numbers were not invented. Anchor spacing, the 2×4 allowance, and the membrane names are in the specification and are not sufficient for the required take-off.

### FRAMING

| Field | Record |
|-------|--------|
| Diagram location | Construction intelligence — framing |
| Purpose | Governed framing quantities. |
| Independent use | NOT STARTED |
| Workflow use | NOT STARTED |
| Required dependencies | An accepted framing specification. |
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
| Independent use | NOT STARTED |
| Workflow use | NOT STARTED |
| Required dependencies | An accepted roofing specification. |
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
| Independent use | NOT STARTED |
| Workflow use | NOT STARTED |
| Required dependencies | An accepted siding specification. |
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
| Independent use | NOT STARTED |
| Workflow use | NOT STARTED |
| Required dependencies | An accepted drywall specification. |
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
| Independent use | NOT STARTED |
| Workflow use | NOT STARTED |
| Required dependencies | An accepted flooring specification. |
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
| Live verification requirement | Scope was included in the hosted office before the 30 Sep deploy. Not re-walked on 1 Oct 2026. |
| Commit / deployed SHA when closed | Live SHA `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Drawings & Documents

| Field | Record |
|-------|--------|
| Diagram location | Core — drawings and documents |
| Purpose | Hold the project drawings and the document families. |
| Current status | CLOSED — LIVE VERIFIED |
| Required dependencies | None for upload and the drawings list already live. |
| Existing implementation | Drawings list and upload are on the live office. Seven document families are registered. Most families are not yet available. |
| What is missing | Build Drawings and the drawing-requirement decision are not on the live SHA. See Plan Generation. |
| Build acceptance criteria | Met for the live drawings list. |
| Live verification requirement | Drawings presentation deploy is inside the current live line. |
| Commit / deployed SHA when closed | Live SHA `ca37d8b6939f6494b6ff415bad17953886366728`. |

### Plan Generation

| Field | Record |
|-------|--------|
| Diagram location | Core — plan generation |
| Purpose | Build a dimensioned-plan candidate and register it only when the contractor uses it. |
| Current status | BLOCKED — DEPENDENCY IDENTIFIED |
| Required dependencies | Deploy the product SHA that contains PGE-4 through PGE-6, and migrate the hosted database through `l2f3a4b5c6d7` and `m3f4a5b6c7d8`. Those revisions are not on the hosted database. |
| Existing implementation | In git: Build Drawings for `dimensioned_plan`, candidate, explicit use, and `projects.drawing_requirement`. `stair_detail` is an engine profile and is not on the plans page. |
| What is missing | Live verification. |
| Build acceptance criteria | Live plans page can generate a candidate and register a drawing only on Use. |
| Live verification requirement | Live walk after the governed migration and deploy. |
| Commit / deployed SHA when closed | Not closed. |

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
| What is missing | Guided handoff is not live. Workflow consumption of an engine is not built. |
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
| Live verification requirement | Recorded mapper UAT and live smoke. Not re-walked on 1 Oct 2026. |
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
| What is missing | Guided setup’s location step is not on the live SHA. |
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
| What is missing | Hosted database does not have the PGE-4 candidate revision or the PGE-6 drawing-requirement revision. |
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
| What is missing | Guided handoff not live. |
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

## Dependency graph

```text
ICF engine
  design specification present at c1ab362
  blocked on versioned manufacturer profile numbers
  and a governed labour rate
  Pratt hours in the specification are evidence, not a rate

Framing, Roofing, Siding, Drywall, Flooring
  blocked on a governed V1 specification
  (formula authority, assumptions, inputs, outputs, test vectors,
   Contract V1 compatibility, public/private classification,
   Platform workflow boundary)

Start Project, Guided Project Setup, Plan Generation
  blocked on governed deploy of the accepted product SHA
  and hosted migration from last recorded k1f2a3b4c5d6
  through l2f3a4b5c6d7 and m3f4a5b6c7d8

Contract Signing
  blocked on an empty Legal Content Gate and the absence of
  counsel-approved production contract content
  Family 05 is a commercial draft
  an accepted proposal is not a contract

Build / Manage
  blocked on a governed production-management specification
  Field Web, observations, and the calendar are not that specification

Actuals
  blocked on a governed actuals authority for labour, materials,
  equipment, and subcontract cost
  FG-023 direct-cost actuals are not that authority

Complete / Close
  blocked on a governed closeout decision
  no migration from this row

Learn & Improve
  blocked on Actuals

Ready to Price
  not started
  the first-gap foundation is not the full capability

Analytics / Reporting
  not started

Future engines
  deferred
```

## Ready components

None on 1 Oct 2026. The design specification is present. The manufacturer profile numbers and the labour rate are not.

## Blocked components

| Component | Exact dependency |
|-----------|------------------|
| ICF | Versioned manufacturer block dimensions, wall coverage, concrete-volume factors, packaging, StyroRail/Logix/Nudura reinforcement defaults, and a governed labour rate. |
| Framing | Governed V1 specification: formula authority, assumptions, inputs, outputs, test vectors, Contract V1 compatibility, public/private classification, Platform workflow boundary. |
| Roofing | The same missing set as Framing. |
| Siding | The same missing set as Framing. |
| Drywall | The same missing set as Framing. |
| Flooring | The same missing set as Framing. |
| Start Project | Governed deploy plus hosted migration through `m3f4a5b6c7d8`. Live SHA remains `ca37d8b6939f6494b6ff415bad17953886366728`. |
| Guided Project Setup | Same deploy and hosted-migration dependency. |
| Plan Generation | Same dependency. Revisions `l2f3a4b5c6d7` and `m3f4a5b6c7d8` are not on the hosted database. |
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
| ICF | Profile numbers and a labour rate, as named above. The design specification is present. Classification is internal Platform only. |
| Framing | The full V1 specification set. |
| Roofing | The full V1 specification set. |
| Siding | The full V1 specification set. |
| Drywall | The full V1 specification set. |
| Flooring | The full V1 specification set. |

## Current build

ICF remains BLOCKED — DEPENDENCY IDENTIFIED.

The design specification is in the repository. The manufacturer profile numbers and the labour rate are not. No engine code was written.

No other component was dependency-ready. No migration. No deploy.
