# Start New Project — implementation plan

| Attribute | Value |
|-----------|--------|
| Status | **IN IMPLEMENTATION.** SNP-1 **CLOSED AS A SLICE**. SNP-2A **IMPLEMENTED / TESTED**. SNP-2 **BLOCKED**. SNP-3 **BLOCKED** on the reusable Plan Generation Engine. Wizard **NOT BUILT**. |
| Date | 2026-09-30 |
| Product direction | [start-project-guided-wizard-product-direction.md](start-project-guided-wizard-product-direction.md) |
| Sequence | [../PROJECT_DEVELOPMENT_CHECKLIST.md](../PROJECT_DEVELOPMENT_CHECKLIST.md) |
| This record | Planning only. No route, schema, migration, or wizard page is created by this file. |

## 1. Purpose

Start New Project is an orchestration layer. A contractor starts or resumes a project and is guided through capabilities that already exist, toward an ordinary estimate.

It does not replace Clients, Projects, Scope, drawings, calculation engines, Contract V1, the mapper, Estimates, Proposals, Change Orders, Company Calendar, Costs & Pricing, or Company Library.

One CalibraytAI product. One roadmap. One governed implementation of reusable domain logic. The Website and the Platform are consuming surfaces. This plan does not create a second engine, a project-specific formula, or a runtime call between the two repositories.

## 2. Current-state map

A project is created today at `GET/POST /projects/new` (`app/routes/projects.py`, `create_project`). The form is `app/templates/projects/form.html`.

Required: project name and a Client in the current organization. Optional on the same form: project number, address, description, project stage (`Project.status`, default `Lead`), location parts, permit context class, and the commercial decision fields. Save creates one `Project` (`app/models/project.py`), calls `create_initial_commercial_context`, calls `establish_project_location_and_profile`, then redirects to `GET /projects/<id>`.

There is no draft-project type and no resume cursor. A project without scope, drawings, or an estimate is still a real project. Organization scope is `Project.organization_id`. The Client must belong to that organization.

Project stage is `Project.status`. Operating state is separate: `ACTIVE` or `CLOSED`. Company Calendar is `GET /schedule` (`app/routes/schedule.py`, `app/services/schedule.py`). It is not a field on the create form. The commercial field `schedule_condition` is a posture, not a calendar date.

Tests for creation live with the project and commercial-context suites. This plan does not change those tests.

## 3. Guided stages

Stage names follow the recorded product direction. Contractor questions sit under those stages. Exact screen labels are still not authorized.

| Stage | Contractor question | Existing authority |
|-------|---------------------|--------------------|
| Project and client | What are we building? Who is the client? | `Project`, `Client`, `/projects/new`, `/clients/` |
| Location | Where is it? | `ProjectLocation` through `establish_project_location_and_profile` |
| Documents and drawings | Do we have drawings? | `PlanDocument` through `/projects/<id>/plans/upload` |
| Work | What work are we doing? Who is doing each part? | `ProjectWorkPackage` through `GET/POST /projects/<id>/scope` |
| Estimating inputs | What needs to be calculated? | A governed engine and Contract V1, only where one exists. Not a wizard formula. |
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
| Calculation engine | Not a Platform route today | Contract V1 envelope | A governed result, when an engine exists | The walk does not calculate. |
| Contract V1 | [calculation-engine-result-contract-v1.md](calculation-engine-result-contract-v1.md) | Pinned envelope | The result shape | Unchanged. |
| Mapper | `/estimates/<id>/versions/<version_id>/calculations` | `app/services/calculation_estimate_mapping.py` | Confirmed estimate quantities | Send the contractor to that existing gate. |
| Estimate | `/estimates/new` | `Estimate`, `EstimateVersion` | The estimate | Create or resume the project’s estimate. |
| Proposal | `/proposals/` | Existing proposal services | Proposal records | After the estimate. Not a wizard document. |
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

An engine enters the walk only when a Platform-side governed engine can emit a Contract V1 result for a confirmed Our crew package. Today that handoff is the existing calculation intake on an estimate version. The contractor confirms the quantity. The walk does not import it silently.

If a required element has no Platform engine yet, the cursor records `waiting_code` `ENGINE`. No placeholder quantity is written. Subcontracted packages do not call an engine.

## 7. Plan Generation entry

The reusable Plan Generation Engine is planned and not built. The plan is [plan-generation-engine-productization.md](plan-generation-engine-productization.md). Start New Project does not own it. SNP-3 stays blocked until that engine can finish a supported drawing type.

Invoke it only when drawings are required and no current drawing is on the project. A current drawing is a non-archived `PlanDocument`. SNP-1 already treats that row as drawings satisfied.

| Derived or recorded fact | Walk |
|--------------------------|------|
| Drawings exist and are accepted | `PRESENT`. Continue. |
| Drawings are not required | `NOT_REQUIRED`. Continue. |
| Drawings are required and missing | `REQUIRED_MISSING`. Wait. |
| Plan Generation does not exist yet | Stay in `REQUIRED_MISSING`. Do not invent sheets. |

When the reusable engine later exists, drawings missing can call it from the project plans page. That page remains a direct entry. The engine draws governed geometry. It does not recalculate the element. The engine design lives in the productization plan, not in this walk.

## 8. Scope relationship

Reuse `/projects/<id>/scope` and `ProjectWorkPackage`. Scope answers what work is required and who does it: Our crew or Subcontractor. It does not price, send, or estimate.

An existing row is removed and added again. Inline edit is non-blocking polish and is not part of this plan. There is no second scope model. `EstimateScopeDelivery` stays the delivery choice on an estimate line that already exists.

## 9. Estimate and mapper relationship

The walk ends on the ordinary estimate. `POST /estimates/new` already accepts a project id. If the project has an estimate, resume it. If not, open the existing create form with that project. Do not create a wizard estimate table.

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

SNP-1 reads the organization-scoped project, client, `ProjectLocation.completeness`, non-archived plans through `project_plans`, confirmed packages through `list_confirmed`, and estimate rows. It writes nothing. The first gap wins:

| Condition | Stage | Waiting |
|-----------|-------|---------|
| Client is not in this organization | `PROJECT_CLIENT` | `CLIENT` |
| Location is absent or incomplete | `LOCATION` | `SITE` |
| No non-archived plan | `DOCUMENTS_DRAWINGS` | `DRAWINGS` |
| No confirmed package | `WORK` | None |
| Exactly one estimate, and the gaps above are clear | `ESTIMATE` | None. Destination `ESTIMATE_RESUME`. |
| More than one estimate, and the gaps above are clear | `ESTIMATE` | None. Destination `ESTIMATE_AMBIGUOUS`. No estimate is chosen. |
| Those gaps are clear and there is no estimate | `SETUP_REVIEW` | None. Destination `ESTIMATE_CREATE`. |

A project address is not a complete location. Archived plans are not present drawings. Suggested and retired packages are not scope. An existing estimate does not skip an earlier gap. Its id is returned only when the project has exactly one estimate.

Absence of a plan cannot mean drawings are not required, and it cannot mean they are required. That stored decision remains SNP-3. Our-crew scope does not by itself mean an engine is required, because the package does not say which element must be calculated. The evidence token is `ENGINE_REQUIREMENT_NOT_DERIVABLE`. Subcontract-only scope uses `ENGINE_NOT_APPLICABLE`. SNP-1 does not call an engine or Plan Generation.

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
| SNP-2 | Resume entry | One project link and a read-only next-step page | SNP-1 and existing pages | None | **BLOCKED.** `DRAWINGS` has no governed “not required” path and no reusable Build Drawings action. | Contractor can leave and return | Rule 16 pass for every destination, including SNP-3 for drawings | No schema. Do not ship a known dead end. |
| SNP-3 | Drawings branch | Resolver states and the project drawings decision, calling the reusable engine for Build Drawings | SNP-1, plan upload, Plan Generation Engine | `projects.drawing_requirement` when separately approved | **BLOCKED** until the Plan Generation Engine can complete a supported type. | Present, not required, upload, and build each continue | The engine productization plan. Separate migration approval for the decision column. | Do not build a second drawing engine. Do not implement SNP-2 in that slice. |
| SNP-4 | Scope handoff | Return hint on the existing scope page | `confirm_package` | None | Confirm Our crew or Subcontractor and return to the walk | Scope page still reads as it does today | SNP-2 | No second scope model. Inline edit not included. |
| SNP-5 | Drawing decision | Uses SNP-3 | Plan upload | Cursor only | Present, not required, and required-missing are distinct | Missing required drawings wait, and do not invent a sheet | SNP-3 | Plan Generation is not called. |
| SNP-6 | Estimate and mapper handoff | Link to existing estimate and calculation review | Estimate create and mapper | None | Existing estimate is resumed; a new one uses the existing form; confirmation stays manual | Contractor reaches the ordinary estimate | SNP-2 | No wizard estimate. No silent import. |

## 16. Dependencies

SNP-2 and SNP-3 stay blocked until the drawings branch can pass Rule 16. Build Drawings is part of that branch and waits for the reusable engine. SNP-4 and SNP-6 still depend on SNP-2.

Website stabilization, hosted password verification, bypass removal, production cutover, hosted database re-proof, PLAT-UX-02, PLAT-UX-03, PLAT-UX-04, and scope inline edit are outside these slices.

Bushel remains an incomplete proving case. It is not a blocker and is not resumed here.

## 17. Test strategy

When a slice is later authorized: service tests for the resolver; route tests for resume and organization boundaries; tests that an existing client, package, plan, or estimate is reused; tests that `waiting_code` does not invent a fact; tests that a calculation handoff does not write a quantity; tests that mapper confirmation is still required; tests that re-entry does not delete scope or estimate lines; responsive checks on any new resume page. Do not add those tests in this planning pass.

## 18. Migration strategy

The drawing-requirement column is a later migration with its own approval. It is not created here. Mac primary stays `h8c9d0e1f2a3`. Hosted revision stays last recorded `k1f2a3b4c5d6` and was not re-proved. Existing projects remain `UNKNOWN` until that column exists. No plan file is rewritten by the decision.

This plan does not create or run that migration.

## 19. Human UAT plan

After SNP-2, a contractor starts from an existing project and from a new project, leaves, and returns to the same next step. After SNP-4, they confirm work on the existing Scope page. After SNP-5, they mark drawings present, not required, or missing. After SNP-6, they reach the ordinary estimate and the existing mapper confirmation gate. No slice asks them to type a fact the project already has.

## 20. Stop conditions

Stop a slice if it needs a second scope model, a wizard estimate, a copied Website formula, a runtime Website call, a Plan Generation build, an RFQ send, a change to Contract V1, a change to pricing mathematics, or a migration that was not separately approved.

## 21. Recommended first implementation slice

SNP-1 is closed as a slice. SNP-2A closes the client-relationship dead end. SNP-2 stays blocked until the drawings gap in section 22 is closed. SNP-3 stays blocked on the reusable Plan Generation Engine. That engine is planned and not implemented. No schema was added.

## 22. Rule 16 — no dead ends

Every workflow state that can be emitted must have a condition a contractor can understand, a governed action that can resolve it, an authoritative page for that action, a correction path, a re-run of the resolver after the authoritative record changes, and a continuation to the next real condition.

Detecting a condition is not enough. Detection without a way to resolve it is a dead end. A workflow must not tell the contractor to go somewhere else without a governed path, skip a required state, or pick an arbitrary default to escape the condition.

| Destination | Condition | Existing surface | Can the contractor resolve it there? | After the record changes | Rule 16 |
|-------------|---------|------------------|--------------------------------------|--------------------------|---------|
| `PROJECT_CLIENT` | The project’s client is not in this company. | `GET/POST /projects/<id>/client` | Yes. Choose a client from this company. The same project id remains. | SNP-1 no longer returns `PROJECT_CLIENT`. | **PASS** after SNP-2A. |
| `LOCATION` | Structured location is missing or incomplete. | `GET/POST /projects/<id>/location/edit` | Yes. Street, municipality, province, and country complete the existing location record. | SNP-1 leaves `LOCATION`. | **PASS** |
| `DRAWINGS` | No non-archived plan. The resolver cannot tell “not required” from “required and missing.” Build Drawings has no reusable engine to call. | `GET /projects/<id>/plans` | Upload can make drawings present. There is no governed way to say drawings are not required. Build Drawings cannot be offered without inventing an engine. | Upload moves the resolver on. “Not required” cannot be recorded. A generated sheet cannot become current evidence. | **GAP.** SNP-3 is blocked on [plan-generation-engine-productization.md](plan-generation-engine-productization.md). |
| `SCOPE` | No confirmed package. | `GET/POST /projects/<id>/scope` | Yes. Confirm Our crew or Subcontractor. | SNP-1 leaves `WORK` once a confirmed package exists and earlier gaps are clear. | **PASS** |
| `ESTIMATE_RESUME` | Earlier gaps are clear and the project has one estimate. | `GET /estimates/<id>` | Yes. The ordinary estimate is the continuation. | The resolver keeps returning that estimate. | **PASS** |
| `ESTIMATE_AMBIGUOUS` | Earlier gaps are clear and the project has more than one estimate. | Project detail estimates table, `/projects/<id>#hub-price` | Yes. Each estimate is its own link. No estimate is chosen for the contractor. | The resolver stays ambiguous while more than one estimate exists. The contractor continues on the estimate they open. | **PASS** |
| `ESTIMATE_CREATE` | Earlier gaps are clear and the project has no estimate. | `GET/POST /estimates/new?project_id=<id>` | Yes. Saving creates the ordinary estimate. The form does not create it on open. | One estimate, then `ESTIMATE_RESUME`. | **PASS** |

SNP-2 must not ship while a resolver destination fails this rule. The remaining gap is `DRAWINGS`.
