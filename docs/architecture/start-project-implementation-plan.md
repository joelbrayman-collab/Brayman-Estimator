# Start New Project — implementation plan

| Attribute | Value |
|-----------|--------|
| Status | **IN IMPLEMENTATION.** SNP-1 **CLOSED AS A SLICE**. SNP-2A **IMPLEMENTED / TESTED**. SNP-2 **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. Rule 16 re-audit 1 Oct 2026: 7 / 7 PASS. SNP-3 **CLOSED AS A SLICE**. Build Drawings for `dimensioned_plan` is on the plans page. Project drawing requirement is implemented. Guided Project Setup **IMPLEMENTED**. Project Readiness remains the first-gap foundation. The future readiness model is not implemented. SNP-4 **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. SNP-6 **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. ESTIMATE HANDOFF **IMPLEMENTED**. MAPPER HANDOFF **VERIFIED / PRESERVED**. The future readiness model is not implemented. |
| Date | 2026-09-30 |
| Product direction | [start-project-guided-wizard-product-direction.md](start-project-guided-wizard-product-direction.md) |
| Sequence | [../PROJECT_DEVELOPMENT_CHECKLIST.md](../PROJECT_DEVELOPMENT_CHECKLIST.md) |
| This record | Planning only. No route, schema, migration, or Guided Project Setup page is created by this file. |

## 1. Purpose

Start New Project — Guided Project Setup is an orchestration layer. The product concept is Project Readiness. A contractor starts or resumes a project and is guided to capabilities that already exist, toward an ordinary estimate. The 30 Sep 2026 contractor experience is in [start-project-guided-wizard-product-direction.md](start-project-guided-wizard-product-direction.md). This plan does not rewrite SNP-1.

It does not replace Clients, Projects, Scope, drawings, calculation engines, Contract V1, the mapper, Estimates, Proposals, Change Orders, Company Calendar, Costs & Pricing, or Company Library.

One CalibraytAI product. One roadmap. One governed implementation of reusable domain logic. The Website and the Platform are consuming surfaces. This plan does not create a second engine, a project-specific formula, or a runtime call between the two repositories.

## 2. Current-state map

A project is created today at `GET/POST /projects/new` (`app/routes/projects.py`, `create_project`). The form is `app/templates/projects/form.html`.

Required: project name and a Client in the current organization. Optional on the same form: project number, address, description, project stage (`Project.status`, default `Lead`), location parts, permit context class, and the commercial decision fields. Save creates one `Project` (`app/models/project.py`), calls `create_initial_commercial_context`, calls `establish_project_location_and_profile`, then redirects to `GET /projects/<id>`.

There is no draft-project type and no resume cursor. A project without scope, drawings, or an estimate is still a real project. Organization scope is `Project.organization_id`. The Client must belong to that organization.

Project stage is `Project.status`. Operating state is separate: `ACTIVE` or `CLOSED`. Company Calendar is `GET /schedule` (`app/routes/schedule.py`, `app/services/schedule.py`). It is not a field on the create form. The commercial field `schedule_condition` is a posture, not a calendar date.

Tests for creation live with the project and commercial-context suites. This plan does not change those tests.

## 3. Guided stages

Stage names are internal. They are not a contractor step counter. Exact screen labels are still not authorized. The opening experience is project name, client, and location or address. Permit class, commercial posture, project stage, and drawings stay off that opening. The current `/projects/new` form still shows those extra fields. This plan does not change that form. Creating a project still requires only a name and an in-organization client.

| Stage | Contractor question | Existing authority |
|-------|---------------------|--------------------|
| Project and client | What are we building? Who is the client? | `Project`, `Client`, `/projects/new`, `/clients/` |
| Location | Where is it? | `ProjectLocation` through `establish_project_location_and_profile` |
| Documents and drawings | Do we have drawings? | `PlanDocument` through `/projects/<id>/plans/upload` |
| Work | What work are we doing? Who is doing each part? | `ProjectWorkPackage` through `GET/POST /projects/<id>/scope` |
| Estimating inputs | What needs to be calculated? | A governed engine and Contract V1, only where one exists. |
| Missing information | What is still missing? | Derived from the records above, plus the thin cursor where a decision cannot be derived. |
| Setup review | Is this ready to estimate? | Read-only view of the same records. |
| Estimate | What needs to be estimated? | Existing `Estimate` and the calculation mapper. |

Commercial posture stays on the existing commercial-context record. Preselected form values are not treated as contractor answers.

## 4. Thin resume cursor

Completion is derived. The cursor does not copy Client, Scope, drawings, calculations, or estimate lines.

Derived next step, in order: project exists with a client; location present; drawing decision recorded; at least one confirmed `ProjectWorkPackage`; if an engine is required and none exists, waiting; an estimate exists or the contractor is at the existing estimate screen; mapper confirmation remains on the estimate.

What existing rows cannot say:

- drawings are present, not required, or required and missing;
- the contractor is waiting, and for which kind of fact.

Proposed storage: one thin orchestration row, one per project, not a second project.

| Field | Role |
|-------|------|
| `project_id` | The only project. Unique. |
| `organization_id` | Same boundary as the project. |
| `drawing_decision` | `PRESENT`, `NOT_REQUIRED`, or `REQUIRED_MISSING`. Null means not yet asked. |
| `waiting_code` | Null, or one token: `CLIENT`, `SITE`, `DRAWINGS`, `MEASUREMENTS`, `ENGINE`, `DATE`, `OWNER`, `SUBCONTRACTOR`, `SUPPLIER`. |
| `updated_at` | When the orchestration decision changed. |

No copied name, address, package, quantity, price, or file. The next stage is computed. If the contractor edits the project outside the walk, the next derived step changes. The cursor is not a lock.

Back and forward movement opens the existing page for that stage. It does not rewrite later records.

## 5. Existing service map

| Capability | Entry | Record / service | What it writes | How the walk uses it |
|------------|-------|------------------|----------------|----------------------|
| Client | `/clients/` and the client form | `Client` | The client row | Select or create. Do not store a second client name. |
| Project | `/projects/new`, `/projects/<id>` | `Project`, `create_project` | The project row | Create once, then resume that id. |
| Project stage | Project form and project detail | `Project.status` | Stage label | Read and update only through the existing project save. |
| Company Calendar | `/schedule` | Schedule services | Schedule items on the project | Link out. Do not create a second calendar. |
| Scope | `/projects/<id>/scope` | `confirm_package`, `retire_package` | `ProjectWorkPackage` | Confirm Our crew (`INTERNAL`) or Subcontractor (`SUBCONTRACT`). |
| Drawings | `/projects/<id>/plans/upload` | `upload_plan_pdf` | `PlanDocument` | Import drawings that exist. |
| Workflow documents | `/projects/<id>/workflow-documents` | Existing project documents | Project files | Resume that page. Do not replace it. |
| Calculation engine | `/estimates/<id>/versions/<version_id>/wall-form-quantities` for `icf_wall` only | `build_icf_standard_quantities` | A Contract V1 result after the contractor enters measurements | The walk opens that page for Our-crew ICF wall. It does not calculate. |
| Contract V1 | [calculation-engine-result-contract-v1.md](calculation-engine-result-contract-v1.md) | Pinned envelope | The result shape | Unchanged. |
| Mapper | `/estimates/<id>/versions/<version_id>/calculations` | `app/services/calculation_estimate_mapping.py` | Confirmed estimate quantities | Send the contractor to that existing gate. |
| Estimate | `/estimates/new` | `Estimate`, `EstimateVersion` | The estimate | Create or resume the project’s estimate. |
| Proposal | `/proposals/` | Existing proposal services | Proposal records | After the estimate. |
| Change order | Existing change-order routes | `ChangeOrder` | Change orders | Later project work. Not part of setup. |
| Costs and pricing | `/costs-and-pricing/`, `/cost-library/`, `/pricing-engine/` | Cost library and pricing | Company cost and price | Applied on the estimate. Not copied into the cursor. |
| Reusable work | `/assemblies/` | Assemblies | Assembly definitions | Selected on the estimate. |
| Labour rates | Existing labour-rates page | Labour book | Rates | Used by estimating when Our crew work needs them. |
| Past jobs | Historical estimates | Company library | Prior jobs | Reference only. Not a second scope. |
| Templates | Proposal templates | Existing templates | Template rows | Not setup state. |

## 6. Calculation-engine entry

The walk does not own construction mathematics.

Path: project intent and geometry → governed calculation engine → Contract V1 result → mapper → ordinary estimate.

Website Concrete (`lib/calculation-engine/concrete-slab.ts` in the Website project) and Website Stair are governed reusable capabilities on the public surface. They are not copied into the Platform, and the Platform does not call the Website at runtime.

An engine enters the walk only when a confirmed Our-crew package names a Platform producer that already emits Contract V1. The handoff is that producer’s existing entry, then the existing calculation intake on an estimate version. The contractor confirms the quantity. The walk does not import it silently.

A package with no valid binding stays `ENGINE_REQUIREMENT_NOT_DERIVABLE`. The walk does not set `waiting` to `ENGINE`. No placeholder quantity is written. Subcontracted packages stay `ENGINE_NOT_APPLICABLE` and do not call an engine.

### Binding — implemented 2026-10-04 for ICF wall only

The binding is one baseline `WorkElementTemplate` code to one Platform `engine_id`, or no binding. It is valid only when the template is a baseline row, the `engine_id` names a producer in this repository, and that producer emits a payload that passes `validate_contract_v1`.

The result already carries `engine_version`, `contract_version`, `result_id`, inputs, and quantities. The work package already carries Our crew or Subcontractor. Those facts stay off the binding.

`WorkElementTemplate.platform_engine_id` is nullable. An empty value means no Platform engine is bound. An organization template does not acquire an engine. A Website calculator name is not a producer.

| Code | Display name | Work type | Meaning | Scope | Status | Order | Binding |
|------|--------------|-----------|---------|-------|--------|-------|---------|
| `ICF` | ICF wall | `GEN` | A contractor-confirmed scope element for ICF wall construction. | The existing `icf_wall` producer. It is not every foundation, every concrete foundation, slab, excavation, reinforcement outside that producer, or every ICF accessory. | `ACTIVE` | 40 | `icf_wall` |
| `SITE` | Site work | `GEN` | Unchanged. | Unchanged. | `ACTIVE` | 10 | none |
| `FOUND` | Foundation | `GEN` | Unchanged. Not an ICF wall. | Unchanged. | `ACTIVE` | 20 | none |
| `STRUCT` | Structure | `GEN` | Unchanged. | Unchanged. | `ACTIVE` | 30 | none |

The only Platform producer remains `icf_wall` in `app/services/icf_quantity.py`. Its existing entry is the estimate wall-form page. `concrete_slab` stays a Contract V1 shape and a Website calculator. It has no producer in this repository, so naming it on a template is not a binding. Plan Generation stair provenance is not a Contract V1 result.

Our-crew `ICF` records `ENGINE_ELIGIBLE` and, when the project has one estimate, Continue setup opens that existing wall-form page. The walk still writes no quantity and does not calculate. Our-crew `SITE`, `FOUND`, and `STRUCT` stay `ENGINE_REQUIREMENT_NOT_DERIVABLE`. Subcontract-only work, including `ICF`, stays `ENGINE_NOT_APPLICABLE`. The mapper confirmation gate stays. A missing measurement stays on the wall-form page.

On 5 Oct 2026 that ICF path was proved through to an ordinary estimate line. The contractor enters the wall measurements. `build_icf_standard_quantities` emits Contract V1. `validate_contract_v1` runs before the result is stored for review. Calculate and review add no estimate line. The contractor confirms one quantity onto a company cost item, and that confirmation creates one ordinary line. The path does not create a `PlanDocument` and does not call drawing generation. This is the ICF path. It is not generic estimating. Checklist step 8 stays open for `SITE`, `FOUND`, and `STRUCT`.

On 5 Oct 2026 the Construction Model stored-fact quantity read was proved. `read_stored_member_quantities` uses the existing `group_member_rows`. It returns a count and the supplied length already stored on equivalent members. A missing length stays a missing schedule fact and names those members. The read does not price, write an estimate line, or compose a sheet. **CONSTRUCTION MODEL STORED-FACT QUANTITY READ IMPLEMENTED / TESTED.** Generic estimating is not complete.

On 5 Oct 2026 the material-requirement boundary was proved. `read_construction_material_requirements` states one requirement for each stored member group. The requirement carries the stored material id, the member count, and the supplied length as separate facts. The persisted `MaterialRequirement` row stays a catalogue quantity in one unit for supplier mapping. This read does not write that row, because one unit would collapse the member count and the supplied length. No stock length, waste, or price is added. **CONSTRUCTION MODEL → MATERIAL REQUIREMENT BOUNDARY IMPLEMENTED / TESTED.**

Migration `n4a5b6c7d8e9` adds the nullable column and the baseline `ICF` row. It is not applied to the Mac primary database and it is not applied to the hosted database. Checklist step 8 stays open for every work element that still has no producer.

## 7. Plan Generation entry

The reusable Plan Generation Engine is in productization. PGE-1 through PGE-6 are closed as slices. Build Drawings for `dimensioned_plan` is on the existing plans page. The plan is [plan-generation-engine-productization.md](plan-generation-engine-productization.md). Start New Project does not own it. SNP-3 is closed as a slice. `projects.drawing_requirement` stores `UNKNOWN`, `REQUIRED`, or `NOT_REQUIRED`.

Invoke it only when drawings are required and no current drawing is on the project. A current drawing is a non-archived `PlanDocument`. SNP-1 already treats that row as drawings satisfied.

| Derived or recorded fact | Walk |
|--------------------------|------|
| A current non-archived plan exists | `PRESENT`. Continue. This is true even when `drawing_requirement` is `UNKNOWN`. |
| Drawings are not required, and no current plan exists | `NOT_REQUIRED`. Continue. No plan is created. |
| Drawings are required and no current plan exists | `REQUIRED_MISSING`. The existing plans page offers Upload and Build Drawings. |
| The stored choice is unknown, and no current plan exists | `UNKNOWN`. The contractor chooses required or not required. Unknown does not become not required. |

Drawings that are required and missing use the existing project plans page. That page remains a direct entry. Build Drawings creates a candidate. Explicit use creates the plan. The engine draws governed geometry. It does not recalculate the element. The engine design lives in the productization plan, not in this walk.

## 8. Scope relationship

Reuse `/projects/<id>/scope` and `ProjectWorkPackage`. Scope answers what work is required and who does it: Our crew or Subcontractor. It does not price, send, or estimate.

An existing row is removed and added again. Inline edit is non-blocking polish and is not part of this plan. There is no second scope model. `EstimateScopeDelivery` stays the delivery choice on an estimate line that already exists.

## 9. Estimate and mapper relationship

Ready to price is a review of authoritative client, project, location, our work, subcontracted work, drawings, governed results, and remaining blocking items. Build Estimate then enters the ordinary estimate. `POST /estimates/new` already accepts a project id. If the project has an estimate, resume it. If not, open the existing create form with that project. Do not create a Guided Project Setup estimate.

Sections and lines stay estimate records. Calculation results enter only through the mapper confirmation gate. Company cost, reusable work, and custom lines stay on that estimate. True gross margin and pricing authority stay where they are. The contractor is ready to review when the derived gaps for client, location, drawing decision, and at least one confirmed package are clear, and any `waiting_code` is null. An estimate may still be opened earlier; the walk must not block the existing estimate screens.

Mapper path, unchanged: engine → Contract V1 result → company cost or reusable work selection → ordinary estimate line. The confirmation gate stays. No silent import.

## 10. Waiting states

`waiting_code` is the only waiting representation. The project remains a normal project. No fake client, address, drawing, measurement, price, or date is required to leave a stage.

The walk can wait for client detail, site, drawings, measurements, an engine, a date, an owner decision, a subcontractor, or supplier information. Resume reads the project and the cursor and opens the existing page that can receive the missing fact.

## 11. Existing-project reconciliation

Any existing project can be opened in the walk. The resolver reads what is already there.

A client on the project is not asked again. Confirmed packages are not re-entered. Plan documents already stored count once the contractor accepts them as current. An existing estimate is resumed. Work done outside the walk counts. The walk must not create a second project, client, package, or estimate to represent the same facts.

## 12. Change and re-entry model

Client, scope, drawing, measurement, stage, and schedule edits outside the walk remain on their own records. The next derived step follows those records. The cursor is not a snapshot of them.

A stale calculation is an estimate concern. Accepted mapper lines are not rewritten by the walk. A new result goes through the existing confirmation gate. Leaving and returning recomputes the next step. Nothing in the walk deletes scope, drawings, or estimate lines in order to move stages.

## 13. Minimum data-model delta

No new table is required for the derived next step.

30 Sep 2026 correction: the drawing requirement is a project fact, `UNKNOWN`, `REQUIRED`, or `NOT_REQUIRED`, on `Project` when a later migration is approved. It is not a workflow-state table. Presence stays a non-archived `PlanDocument`. That delta is specified in [plan-generation-engine-productization.md](plan-generation-engine-productization.md) and is not migrated here. A general waiting-token table is not part of that correction.

## 14. Route and service plan

SNP-1 is the resolver only: `resolve_start_project_walk` in `app/services/start_project_walk.py`. It does not add a route. The resume entry below is still not implemented.

SNP-1 reads the organization-scoped project, client, `ProjectLocation.completeness`, non-archived plans through `project_plans`, confirmed packages through `list_confirmed`, and estimate rows. It writes nothing. The first gap wins. That first-gap result is the current foundation. It is not the final Project Readiness model. A later result may also return completed facts, unresolved items, blocking items, waiting items, and available next actions, still without writing project records.

| Condition | Stage | Waiting |
|-----------|-------|---------|
| Client is not in this organization | `PROJECT_CLIENT` | `CLIENT` |
| Location is absent or incomplete | `LOCATION` | `SITE` |
| No current plan, and the stored choice is not `NOT_REQUIRED` | `DOCUMENTS_DRAWINGS` | `DRAWINGS` |
| No confirmed package | `WORK` | None |
| Exactly one estimate, and the gaps above are clear | `ESTIMATE` | None. Destination `ESTIMATE_RESUME`. |
| More than one estimate, and the gaps above are clear | `ESTIMATE` | None. Destination `ESTIMATE_AMBIGUOUS`. No estimate is chosen. |
| Those gaps are clear and there is no estimate | `SETUP_REVIEW` | None. Destination `ESTIMATE_CREATE`. |

A project address is not a complete location. Archived plans are not present drawings. Suggested and retired packages are not scope. An existing estimate does not skip an earlier gap. Its id is returned only when the project has exactly one estimate.

Absence of a plan cannot mean drawings are not required, and it cannot mean they are required. That stored decision is `projects.drawing_requirement`. `UNKNOWN` stays unknown until the contractor chooses. A current plan is `PRESENT` even when that choice is still unknown. Our-crew scope does not by itself mean an engine is required, because the package does not say which element must be calculated. The evidence token is `ENGINE_REQUIREMENT_NOT_DERIVABLE`. Subcontract-only scope uses `ENGINE_NOT_APPLICABLE`. SNP-1 does not call an engine or Plan Generation.

| Piece | Proposal |
|-------|----------|
| Entry | Keep `+ Start New Project` on `/projects/new` for a new project. Add a resume entry from the project that calls the resolver. |
| Resolver | A pure service over existing repositories. No writes except the thin cursor when a decision is saved. |
| Stage pages | Redirect to the existing client, project, scope, plan upload, schedule, estimate, and mapper routes. |
| Return | Those pages already know the project id. A return hint may bring the contractor back to the resolver. It must not fork their save behaviour. |
| Unchanged | `create_project`, `confirm_package`, `upload_plan_pdf`, estimate create, and the mapper. |

## 15. Implementation slices

| ID | Purpose | Likely change | Reused | New data | Acceptance | Human UAT | Depends on | Stop |
|----|---------|---------------|--------|----------|------------|-----------|------------|------|
| SNP-1 | Resolver only | `app/services/start_project_walk.py` and `tests/test_start_project_walk.py` | Project, client, location, packages, plans, estimates | None | **IMPLEMENTED / TESTED.** Given an existing project, the next gap is named and no row is written. No UI. | Not required | None | No schema. No resume route. |
| SNP-2A | Correct the project’s client | `app/services/project_client.py`, `/projects/<id>/client` | Client and Project | None. Uses `Project.client_id`. | **IMPLEMENTED / TESTED.** Same project id. Same-organization client only. Proposal client name stays a snapshot. | Contractor corrects the client and SNP-1 leaves `PROJECT_CLIENT`. | SNP-1 | No schema. No second client editor. |
| SNP-2 | Resume entry | One project link and a read-only next-step page | SNP-1 and existing pages | None | **IMPLEMENTED / TESTED / CLOSED AS A SLICE.** `GET /projects/<id>/setup` re-runs the resolver. New projects from `/projects/new` open that page. | Contractor can leave and return | Rule 16 re-audit 7 / 7 PASS | No schema. Do not ship a known dead end. |
| SNP-3 | Drawings branch | Resolver states and the project drawings decision, calling the reusable engine for Build Drawings | SNP-1, plan upload, Plan Generation Engine | `projects.drawing_requirement` | **CLOSED AS A SLICE.** Stored choice is unknown, required, or not required. Present is derived from a current plan. Required and missing uses the existing plans page. | Present, not required, upload, and build each continue | PGE-6. | Do not build a second drawing engine. Do not implement SNP-2 in that slice. |
| SNP-4 | Scope handoff | Return hint on the existing scope page | `confirm_package` | None | **IMPLEMENTED / TESTED / CLOSED AS A SLICE.** Return to setup opens the same project. Saving work stays on Scope. The resolver names the next page. | Scope page still reads as it does today | SNP-2 | No second scope model. Inline edit not included. |
| SNP-5 | Drawing decision | Uses SNP-3 | Plan upload | Cursor only | Present, not required, and required-missing are distinct | Missing required drawings wait, and do not invent a sheet | SNP-3 | Plan Generation is not called. |
| SNP-6 | Estimate and mapper handoff | Link to existing estimate and calculation review | Estimate create and mapper | None | **IMPLEMENTED / TESTED / CLOSED AS A SLICE.** One estimate opens that estimate. Several estimates open the existing project list. None opens the ordinary create form. Saving it and returning to setup reads the project again. Mapper confirmation stays required. | Contractor reaches the ordinary estimate. Temporary office 1 Oct 2026: one estimate, several estimates, create then return, confirm, no silent line, and another organization rejected. | SNP-2 | No second estimate. No silent import. |

## 16. Dependencies

SNP-3 is closed as a slice. SNP-2 is implemented, tested, and closed as a slice after the 1 Oct 2026 Rule 16 re-audit, 7 / 7 PASS. SNP-4 is implemented, tested, and closed as a slice. SNP-6 is implemented, tested, and closed as a slice. Build Drawings for `dimensioned_plan` is on the plans page. The drawing-requirement decision is recorded. The future readiness model is not implemented.

Website stabilization, hosted password verification, bypass removal, production cutover, hosted database re-proof, PLAT-UX-02, PLAT-UX-03, PLAT-UX-04, and scope inline edit are outside these slices.

Bushel remains an incomplete proving case. It is not a blocker and is not resumed here.

## 17. Test strategy

When a slice is later authorized: service tests for the resolver; route tests for resume and organization boundaries; tests that an existing client, package, plan, or estimate is reused; tests that `waiting_code` does not invent a fact; tests that a calculation handoff does not write a quantity; tests that mapper confirmation is still required; tests that re-entry does not delete scope or estimate lines; responsive checks on any new resume page. Do not add those tests in this planning pass.

## 18. Migration strategy

The drawing-requirement column is repository revision `m3f4a5b6c7d8`. Existing projects upgrade to `UNKNOWN`. Mac primary stays `h8c9d0e1f2a3`. Hosted revision stays last recorded `k1f2a3b4c5d6` and was not re-proved. Neither database was migrated by PGE-6. No plan file is rewritten by the decision.

## 19. Human UAT plan

After SNP-2, a contractor starts from an existing project and from a new project, leaves, and returns to the same next step. After SNP-4, they confirm work on the existing Scope page. After SNP-5, they mark drawings present, not required, or missing. After SNP-6, they reach the ordinary estimate and the existing mapper confirmation gate. No slice asks them to type a fact the project already has.

## 20. Stop conditions

Stop a slice if it needs a second scope model, a second estimate, a copied Website formula, a runtime Website call, a Plan Generation build inside this plan, an RFQ send, a change to Contract V1, a change to pricing mathematics, or a migration that was not separately approved.

## 21. Recommended first implementation slice

SNP-1 is closed as a slice. SNP-2A closes the client-relationship dead end. SNP-3 is closed as a slice. The drawings gap in section 22 is closed for the requirement decision. As of PGE-5, the earlier PGE-1 recommendation is history. As of PGE-6, the drawing-requirement decision is implemented. The 1 Oct 2026 Rule 16 re-audit passed all seven destinations. SNP-2 is implemented, tested, and closed as a slice. SNP-4 is implemented, tested, and closed as a slice. Guided Project Setup is that resume. SNP-6 is implemented, tested, and closed as a slice. The estimate handoff is implemented. The mapper handoff is verified and preserved. The future readiness model is not implemented. No later slice is authorized by this record.

## 22. Rule 16 — no dead ends

Every workflow state that can be emitted must have a condition a contractor can understand, a governed action that can resolve it, an authoritative page for that action, a correction path, a re-run of the resolver after the authoritative record changes, and a continuation to the next real condition.

Detecting a condition is not enough. Detection without a way to resolve it is a dead end. A workflow must not tell the contractor to go somewhere else without a governed path, skip a required state, or pick an arbitrary default to escape the condition.

Rule 16 governs resolution. Project Readiness governs whether a missing fact blocks a particular action. A waiting fact still needs a path. It does not have to stop every other useful action. SNP-1’s first gap is stricter than that readiness model, and it stays as implemented.

| Destination | Condition | Existing surface | Can the contractor resolve it there? | After the record changes | Rule 16 |
|-------------|---------|------------------|--------------------------------------|--------------------------|---------|
| `PROJECT_CLIENT` | The project’s client is not in this company. | `GET/POST /projects/<id>/client` | Yes. Choose a client from this company. The same project id remains. | SNP-1 no longer returns `PROJECT_CLIENT`. | **PASS** after SNP-2A. |
| `LOCATION` | Structured location is missing or incomplete. | `GET/POST /projects/<id>/location/edit` | Yes. Street, municipality, province, and country complete the existing location record. | SNP-1 leaves `LOCATION`. | **PASS** |
| `DRAWINGS` | No current plan, and the stored choice is unknown or required. | Project page for the choice. `GET /projects/<id>/plans` when drawings are required and missing. | Yes. Not required clears the gate. Required opens Upload or Build Drawings. A current plan is present without forcing the question. | The resolver re-runs. Archived plans do not count as current. | **PASS** after PGE-6. |
| `SCOPE` | No confirmed package. | `GET/POST /projects/<id>/scope` | Yes. Confirm Our crew or Subcontractor. | SNP-1 leaves `WORK` once a confirmed package exists and earlier gaps are clear. | **PASS** |
| `ESTIMATE_RESUME` | Earlier gaps are clear and the project has one estimate. | `GET /estimates/<id>` | Yes. The ordinary estimate is the continuation. | The resolver keeps returning that estimate. | **PASS** |
| `ESTIMATE_AMBIGUOUS` | Earlier gaps are clear and the project has more than one estimate. | Project detail estimates table, `/projects/<id>#hub-price` | Yes. Each estimate is its own link. No estimate is chosen for the contractor. | The resolver stays ambiguous while more than one estimate exists. The contractor continues on the estimate they open. | **PASS** |
| `ESTIMATE_CREATE` | Earlier gaps are clear and the project has no estimate. | `GET/POST /estimates/new?project_id=<id>` | Yes. Saving creates the ordinary estimate. The form does not create it on open. | One estimate, then `ESTIMATE_RESUME`. | **PASS** |

The 1 Oct 2026 re-audit passed this table, 7 / 7. SNP-2 now opens each of those surfaces from `GET /projects/<id>/setup`. The audit itself did not build that page.

## 23. 30 Sep 2026 readiness reconciliation

Guided Project Setup and Project Readiness are recorded in the product direction. Conflicts with the behaviour already in the repository:

| Topic | Repository today | Intended experience |
|-------|------------------|---------------------|
| Opening form | `/projects/new` shows permit class, commercial posture, and project stage beside name and client. Save requires name and client only. | Start the job collects name, client, and location or address. The extra fields stay off that opening. The form is unchanged. |
| Scope delivery | `INTERNAL` and `SUBCONTRACT` only. | Our crew and Subcontractor. “Not part of our work” has no delivery value. Do not add one here. |
| Resolver | SNP-1 returns one first gap and writes nothing. | That remains the foundation. Readiness later returns completed, unresolved, blocking, waiting, and available actions. SNP-1 is not rewritten. |
| Resume copy | SNP-2 is implemented. The page says Continue setup, What's ready, What's still needed, and names the next action. | Continue setup, and what is still needed. Not “step 4 of 9.” |
| Drawings | The project stores unknown, required, or not required. A current plan is present. Required and missing uses the existing plans page. | Present, Not required, Missing. Missing offers Upload and Build Drawings. |
| Estimate | Ordinary estimate create and resume exist. | Ready to price, then that same estimate. No second estimate. |
| Sequence | PGE-6, SNP-2, SNP-4, and SNP-6 are closed as slices. | The recorded Start New Project slices through the estimate handoff are implemented. The future readiness model is not implemented. |
