# Start a project — guided wizard

| Attribute | Value |
|-----------|--------|
| Status | **RECORDED PRODUCT DIRECTION / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED** |
| Date | 2026-09-29 |
| Authority | Joel, from real estimating with Ben |
| This record | Architecture only. No page, schema, navigation, engine, drawing generator, labour flow, or RFQ. |
| Does not interrupt | Linda Bushel construction-drawing capability test |

Exact screen labels are not authorized. The sequence and the ownership rules are.

## Product law

The contractor does not need to know which CalibraytAI module to open, in which order, or what each later feature needs.

The contractor’s action is: start a project.

CalibraytAI then walks through the information required to establish that project. The wizard orchestrates existing platform capabilities. It does not copy them into a second project.

Broader principle: the user states the construction task. CalibraytAI determines which internal capabilities are required. Calculation engines, mapping, document generation, labour, and RFQ stay Calibrayt responsibilities.

## What Start Project does now

`+ Start New Project` on Home and on the project list opens `projects.create_project` at `/projects/new` (`app/routes/projects.py`, `app/templates/projects/form.html`).

That page is one form. It asks, together, for:

- project name and client (both required);
- project number, status, street address, description;
- location parts: street, municipality, province or state, postal code, country;
- permit context class;
- a commercial decision gate: project type, pricing posture, execution risk, schedule condition, site condition, and related posture fields.

Several commercial selects arrive with a preselected value (for example New Build, Competitive, Normal). Those are form defaults, not a recorded contractor answer.

On save, the route creates one `Project` for the current organization, writes the initial commercial context, and establishes location and permit profile. It then opens the project. It does not open drawings, scope, or an estimate. There is no step cursor and no “continue setting up this project.”

Hosted office, as last recorded in `docs/current-state.md`: Drawings and Scope of work are on the live validation office. Mac primary remains Alembic `h8c9d0e1f2a3`. This record does not migrate either database.

## What the wizard may reuse

| Concern | Existing object or operation | Wizard use |
|---------|------------------------------|------------|
| Client | `Client` | Select or create the client. Do not store a second client name on wizard state. |
| Project | `Project` | The one project record. Name and identity live here. |
| Location and permit profile | `establish_project_location_and_profile` | Location and jurisdiction stay on the project. |
| Commercial posture | Initial commercial context on the project | Ask only when the answer is needed. Do not treat today’s preselected options as answers. |
| Drawings | Plan PDF upload and plan documents under the project | Import drawings that exist. |
| Scope | `ProjectWorkPackage` via `confirm_package` in `app/services/project_work_package.py` | Confirm catalog work. [ADR-055](../adr/ADR-055-project-work-package-ownership.md). |
| Work list | Work catalog `WorkType` / `WorkElementTemplate` | The contractor confirms governed catalog work. No wizard-only work list. Baseline catalog remains Site work, Foundation, and Structure. |
| Who does the work | `ProjectWorkPackage` delivery: Our crew (`INTERNAL`) or Subcontractor (`SUBCONTRACT`) | The existing delivery decision. |
| Estimate | `Estimate`, `EstimateVersion`, sections, lines | Built after setup review, from the confirmed project. |
| Quantities | Contract V1 and the calculation mapper | Infrastructure under Our crew work. Not a button the contractor has to find. |
| Money | Costs & Pricing, cost items, assemblies, pricing snapshot | Applied after quantities exist. |
| Labour | Labour book and `EstimateLabourSnapshot` | Used when Our crew work needs it. Not a manual destination. |
| Subcontractors | `Subcontractor` and quote evidence on an estimate line (`EstimateScopeDelivery`) | Later, for subcontracted work. Distinct from the pre-estimate `ProjectWorkPackage`. |
| Documents after setup | Workflow documents on the project | Normal project records. The wizard does not replace them. |
| Phone and desktop later | [future-interface-guardrail.md](future-interface-guardrail.md) | Setup state must be reusable by a later Field interface. No PWA in this record. |

Settled path already recorded in [estimating-path-alignment-2026-09-27.md](estimating-path-alignment-2026-09-27.md): project, plans, confirmed scope, internal or subcontracted, then the estimate. The wizard is the guided walk along that path.

## What is missing

| Gap | Why it is not covered today |
|-----|-----------------------------|
| Orchestration | Nothing chooses the next question from prior answers. |
| Progressive disclosure | Start Project is one form. |
| Resume | Nothing can say “continue setting up this project” or name the next incomplete step. |
| One setup cursor | Completeness is not derived and stored as workflow state over the real records. |
| Missing-information register | Nothing distinguishes READY from NEEDS INFORMATION without filling a default. |
| Setup review | Nothing shows client, project, documents, work, delivery, gaps, and what is ready to estimate on one gate. |
| Required inputs per work item | Our crew work does not yet know which geometry, measurement, or engine it needs. |
| Engine handoff | Scope confirmation does not call a calculation engine. |
| RFQ handoff | Subcontract delivery does not start an RFQ. RFQ is not implemented. |
| Drawing generation | A future plan-generation capability is not a product feature. The Bushel sheet is a proof, not this wizard. |
| Interface-neutral setup state | Today’s flow is the desktop form and later manual pages. |

## Recommended stages

These are architecture stages, not authorized labels.

1. Project and client — one `Project`, one `Client`.
2. Location and the basic project facts that are actually required.
3. Documents and drawings — do they exist? If yes, import them onto the project. If no, record whether the job can continue without them or must wait for an authorized plan-generation capability.
4. What work is required — confirm governed catalog work onto `ProjectWorkPackage`.
5. Who is doing each confirmed item — Our crew or Subcontractor on that same package.
6. Estimating inputs — only the inputs that item and that delivery choice require.
7. Missing information — READY versus NEEDS INFORMATION. No invented defaults.
8. Setup review — client, project, documents, work, delivery, gaps, and what is ready.
9. Build the estimate on the existing estimate records.

After setup, Project, documents, scope, delivery, and estimate inputs stay editable on the normal platform. The wizard is the guided path, not a lock.

## Resumability

A contractor may start on a phone, stop, and continue on a desktop, or the reverse.

Persist a thin workflow cursor on the real project: which stage is next, and which facts are still missing. Derive completeness from the governed records (client, location, plans, packages, delivery, required inputs). Do not copy those facts into a second project database.

The cursor must not depend on a desktop page. [future-interface-guardrail.md](future-interface-guardrail.md) already requires that. No schema is authorized by this file.

## Scope and delivery

Scope uses the governed catalog. The contractor confirms the work. A later plan-intelligence suggestion may propose work. Human confirmation stays authoritative.

Delivery is the existing `ProjectWorkPackage` choice. Our crew collects or derives internal estimating inputs. Subcontractor prepares for subcontractor selection and, later, RFQ. Do not ask internal labour questions for a subcontracted item.

`EstimateScopeDelivery` remains the delivery choice on an estimate line that already exists. The wizard must not create a third delivery store.

## Engine boundary

For Our crew work, the later orchestration is:

work item → required geometry or input → measurements already on the plans → calculation engine where one exists → physical quantities → Costs & Pricing → labour → estimate detail.

The contractor should not have to open the engine. This record does not implement engines, Contract V1 changes, or the mapper.

## Subcontract and RFQ boundary

For subcontracted work, the later path is:

work item → the company’s subcontractors → who will price it → drawings, scope, and quantities that exist → RFQ → quote → estimate.

Until that exists, the wizard may only say what is still needed (for example NEEDS SUBCONTRACTOR, WAITING FOR QUOTE). It must not send an RFQ. RFQ is not implemented.

## Drawing-generation integration point

At the documents step, the wizard records one of:

- drawings exist and are stored on the project;
- the job may proceed without drawings;
- drawings are required and do not exist yet.

The third case is the hook for a later authorized plan-generation capability. The Linda Bushel proof shows that some project classes may need CalibraytAI to produce contractor construction drawings. That capability is not part of this wizard. The Bushel test continues on its own stop. See [construction-drawing-standard.md](construction-drawing-standard.md).

## Desktop and Field

The same setup cursor must be readable later from the office and from a Field or PWA client. This record does not build that client.

## Risks

- A wizard database that copies client, scope, or delivery and then drifts from `Project` and `ProjectWorkPackage`.
- Treating today’s preselected commercial options as the contractor’s answers.
- Hiding a missing wall height, subcontractor, or quote by inventing a default.
- Calling an engine or sending an RFQ from the wizard before those capabilities are authorized.
- A desktop-only step list that a later phone client cannot resume.
- Starting wizard implementation while the Bushel drawing review is still the active stop.
- A migration for wizard state against the Mac primary or the hosted validation database without a separate authorization.

## Timing

Not now. The active stop remains Joel’s visual review of the Bushel framing-plan capability test.

The next authorized step, when Joel and the Architect allow it, is an implementation plan only: map each stage above to the existing service, define the thin cursor without building it, and name what must stay derived from real records. That plan is not authorized by this file. No Feature Gate is opened here.
