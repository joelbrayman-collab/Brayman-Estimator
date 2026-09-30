# Start New Project — Guided Project Setup

| Attribute | Value |
|-----------|--------|
| Status | **RECORDED PRODUCT DIRECTION.** 30 Sep 2026 readiness clarification. Rule 16 recorded. SNP-2A **IMPLEMENTED / TESTED**. SNP-2 **BLOCKED**. SNP-3 **BLOCKED** on the reusable Plan Generation Engine, which is planned and not implemented. Guided Project Setup is not built. |
| Date | 2026-09-29. Clarified 2026-09-30. |
| Authority | Joel, from real estimating with Ben. 30 Sep 2026 contractor-experience clarification. |
| This record | Architecture only. No page, schema, navigation, engine, drawing generator, labour flow, or RFQ. |
| Filename | This file keeps its historical name. “Wizard” in older sentences below means this same capability. |
| Does not finish | The Linda Bushel case. That case is preserved and is not a gate for this direction. |

Exact screen labels are not authorized. The sequence and the ownership rules are.

## 30 Sep 2026 — Guided Project Setup and Project Readiness

“Wizard” was conversational shorthand. The capability is **Start New Project — Guided Project Setup**. The product concept is **Project Readiness**. It is not completion of numbered steps.

Guided Project Setup helps a contractor establish enough authoritative project information for CalibraytAI to understand the job, the client, the place, the work, who does each part, what information already exists, what is missing, which reusable capabilities are required, what can be done now, what is waiting, and what still prevents pricing. It then guides the contractor to the existing capability. It does not own that capability.

Contractor experience:

```text
Start the job
→ Understand the work
→ Assess what we already have
→ Identify what is still needed
→ Guide the contractor to the right capability
→ Track what is waiting
→ Ready to price
→ Ordinary estimate
```

The product understands the project as facts arrive. It does not interrogate the contractor through arbitrary numbered steps. Internal stage names may remain. The contractor sees readiness and useful next actions.

### Start the job

The opening collects project name, client, and project location or address. Client selection uses an existing client. Creating a client uses the existing client capability when that path is offered. The opening does not collect permit administration, pricing configuration, project-stage administration, the drawing workflow, or commercial posture. Creating a `Project` today requires a name and a client in the organization. Address and the commercial fields are optional on the current form. That form still shows the extra fields. This clarification does not change the form.

### What are we doing?

Plain-language description, the work involved, and who does each part reuse `ProjectWorkPackage` and `Project.description`. Contractor-facing delivery stays Our crew (`INTERNAL`) and Subcontractor (`SUBCONTRACT`). The scope model has no third value for “not part of our work.” Retiring a package is the existing way to take work off the confirmed list. This record does not add a delivery.

### What information do we have?

Drawings readiness is Present, Not required, or Missing. Missing drawings resolve by Upload Drawings or Build Drawings. Build Drawings consumes the reusable Plan Generation Engine. Guided Project Setup does not own that engine. Direct use remains Project → Drawings → Build Drawings. PGE-1 is unchanged.

### Reusable capabilities

Concrete, Stair, Plan Generation, Scope, drawing upload, and the ordinary Estimate stay independently usable. Guided Project Setup orchestrates them. When it calls one, project context that the capability can accept may prefill inputs. The contractor does not re-enter a fact CalibraytAI already holds. The capability owns its logic. The setup receives the governed result and continues.

### Project Readiness

Readiness answers what the contractor can do now, what information is still needed, what blocks a particular action, what can wait without blocking other useful work, and what must be complete before the project is ready to price. The first incomplete field is not the whole model.

Unresolved facts are **blocking now**, **waiting / non-blocking now**, or **complete**. An unknown start date can leave scope and drawings available. An outstanding supplier quote can leave other estimate work available. A missing drawing can block a geometry-dependent calculation and still leave unrelated setup available. No placeholder fact is created to advance.

### Rule 16

Rule 16 still means no dead ends. Every identified condition has an explanation, a governed resolution path, an authoritative correction, a re-evaluation, and a continuation. Rule 16 does not mean every missing item blocks all other project work. Rule 16 governs resolution. Project Readiness governs whether that item blocks a particular action.

### Resume

A contractor can leave and return. Return re-reads authoritative project state. The experience is closer to “continue setup” and a count of what is still needed than to “step 4 of 9.”

### SNP-1

SNP-1 remains the first orchestration foundation. It returns one deterministic first gap and writes nothing. First-gap resolution is not the final Project Readiness model. A later readiness result may return completed facts, unresolved items, blocking items, waiting items, and available next actions. That later result still reads authoritative records and still does not mutate them. SNP-1 is not rewritten by this clarification.

### Ready to price

Ready to price is the handoff review: client, project, location, our work, subcontracted work, drawings, governed calculation results, and remaining blocking items, all from existing records. There is no second commercial model. Build Estimate opens or resumes the ordinary estimate. Company cost, reusable work, custom lines, pricing, true gross margin, commercial review, and proposal progression stay on that estimate. Once the contractor is in the estimate, Guided Project Setup no longer leads the work.

## Product law

The contractor does not need to know which CalibraytAI module to open, in which order, or what each later feature needs.

The contractor’s action is: start a project.

CalibraytAI then helps establish the project. Guided Project Setup orchestrates existing platform capabilities. It does not copy them into a second project.

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

## What Guided Project Setup may reuse

| Concern | Existing object or operation | Guided Project Setup use |
|---------|------------------------------|------------|
| Client | `Client` | Select an existing client, or use the existing create-client capability. Do not store a second client name on setup state. |
| Project | `Project` | The one project record. Name and identity live here. |
| Location and permit profile | `establish_project_location_and_profile` | Location and jurisdiction stay on the project. |
| Commercial posture | Initial commercial context on the project | Ask only when the answer is needed. Do not treat today’s preselected options as answers. |
| Drawings | Plan PDF upload and plan documents under the project | Import drawings that exist. |
| Scope | `ProjectWorkPackage` via `confirm_package` in `app/services/project_work_package.py` | Confirm catalog work. [ADR-055](../adr/ADR-055-project-work-package-ownership.md). |
| Work list | Work catalog `WorkType` / `WorkElementTemplate` | The contractor confirms governed catalog work. No second work list. Baseline catalog remains Site work, Foundation, and Structure. |
| Who does the work | `ProjectWorkPackage` delivery: Our crew (`INTERNAL`) or Subcontractor (`SUBCONTRACT`) | The existing delivery decision. |
| Estimate | `Estimate`, `EstimateVersion`, sections, lines | Built after setup review, from the confirmed project. |
| Quantities | Contract V1 and the calculation mapper | Infrastructure under Our crew work. Not a button the contractor has to find. |
| Money | Costs & Pricing, cost items, assemblies, pricing snapshot | Applied after quantities exist. |
| Labour | Labour book and `EstimateLabourSnapshot` | Used when Our crew work needs it. Not a manual destination. |
| Subcontractors | `Subcontractor` and quote evidence on an estimate line (`EstimateScopeDelivery`) | Later, for subcontracted work. Distinct from the pre-estimate `ProjectWorkPackage`. |
| Documents after setup | Workflow documents on the project | Normal project records. Guided Project Setup does not replace them. |
| Phone and desktop later | [future-interface-guardrail.md](future-interface-guardrail.md) | Setup state must be reusable by a later Field interface. No PWA in this record. |

Settled path already recorded in [estimating-path-alignment-2026-09-27.md](estimating-path-alignment-2026-09-27.md): project, plans, confirmed scope, internal or subcontracted, then the estimate. Guided Project Setup is the readiness walk along that path.

## What is missing

| Gap | Why it is not covered today |
|-----|-----------------------------|
| Orchestration | Nothing chooses the next question from prior answers. |
| Progressive disclosure | Start Project is one form. |
| Resume | Nothing yet says continue setup, or names what is still needed. SNP-2 is blocked. |
| One setup cursor | Completeness is not derived and stored as workflow state over the real records. |
| Missing-information register | Nothing distinguishes READY from NEEDS INFORMATION without filling a default. |
| Setup review | Nothing shows client, project, documents, work, delivery, gaps, and what is ready to estimate on one gate. |
| Required inputs per work item | Our crew work does not yet know which geometry, measurement, or engine it needs. |
| Engine handoff | Scope confirmation does not call a calculation engine. |
| RFQ handoff | Subcontract delivery does not start an RFQ. RFQ is not implemented. |
| Drawing generation | The reusable engine is planned and not implemented. PGE-1 is the next slice. Bushel sheets remain proofs. |
| Interface-neutral setup state | Today’s flow is the desktop form and later manual pages. |

## Internal stages

These names are internal. They are not a contractor step counter. The 30 Sep 2026 experience above is the contractor-facing model.

1. Project and client — one `Project`, one `Client`.
2. Location and the basic project facts that are actually required.
3. Documents and drawings — do they exist? If yes, import them onto the project. If no, record whether the job can continue without them or must wait for an authorized plan-generation capability.
4. What work is required — confirm governed catalog work onto `ProjectWorkPackage`.
5. Who is doing each confirmed item — Our crew or Subcontractor on that same package.
6. Estimating inputs — only the inputs that item and that delivery choice require.
7. Missing information — READY versus NEEDS INFORMATION. No invented defaults.
8. Setup review — client, project, documents, work, delivery, gaps, and what is ready.
9. Build the estimate on the existing estimate records.

After setup, Project, documents, scope, delivery, and estimate inputs stay editable on the normal platform. Guided Project Setup is a path back to those records. It does not lock them.

## Resumability

A contractor may start on a phone, stop, and continue on a desktop, or the reverse.

Persist a thin workflow cursor on the real project: which stage is next, and which facts are still missing. Derive completeness from the governed records (client, location, plans, packages, delivery, required inputs). Do not copy those facts into a second project database.

The cursor must not depend on a desktop page. [future-interface-guardrail.md](future-interface-guardrail.md) already requires that. No schema is authorized by this file.

## Scope and delivery

Scope uses the governed catalog. The contractor confirms the work. A later plan-intelligence suggestion may propose work. Human confirmation stays authoritative.

Delivery is the existing `ProjectWorkPackage` choice. Our crew collects or derives internal estimating inputs. Subcontractor prepares for subcontractor selection and, later, RFQ. Do not ask internal labour questions for a subcontracted item.

`EstimateScopeDelivery` remains the delivery choice on an estimate line that already exists. Guided Project Setup must not create a third delivery store. “Not part of our work” is not a `ProjectWorkPackage` delivery value.

## Engine boundary

For Our crew work, the later orchestration is:

work item → required geometry or input → measurements already on the plans → calculation engine where one exists → physical quantities → Costs & Pricing → labour → estimate detail.

The contractor should not have to open the engine. A public Useful Tool is another consumer of the same mathematics, not a second formula. This record does not implement engines, Contract V1 changes, the mapper, or a choice of where the engine source lives. The one sequence is [../PROJECT_DEVELOPMENT_CHECKLIST.md](../PROJECT_DEVELOPMENT_CHECKLIST.md).

## Subcontract and RFQ boundary

For subcontracted work, the later path is:

work item → the company’s subcontractors → who will price it → drawings, scope, and quantities that exist → RFQ → quote → estimate.

Until that exists, Guided Project Setup may only say what is still needed (for example NEEDS SUBCONTRACTOR, WAITING FOR QUOTE). A waiting quote does not block unrelated project work. Setup must not send an RFQ. RFQ is not implemented.

## Drawing-generation integration point

At drawings readiness, Guided Project Setup records one of:

- drawings exist and are stored on the project;
- the job may proceed without drawings;
- drawings are required and do not exist yet.

The third case is Drawings Missing. Upload Drawings and Build Drawings are the resolution actions. Build Drawings consumes the reusable Plan Generation capability. Where a governed result already exists, Plan Generation draws that geometry. It does not calculate the element again. The Linda Bushel proof shows that some project classes may need CalibraytAI to produce contractor construction drawings. That capability is not owned by Guided Project Setup. The productization plan is [plan-generation-engine-productization.md](plan-generation-engine-productization.md). It is planned and not implemented. PGE-1 is unchanged. The Bushel case stays preserved and incomplete. See [construction-drawing-standard.md](construction-drawing-standard.md).

## Desktop and Field

The same setup cursor must be readable later from the office and from a Field or PWA client. This record does not build that client.

## Risks

- A setup database that copies client, scope, or delivery and then drifts from `Project` and `ProjectWorkPackage`.
- Treating today’s preselected commercial options as the contractor’s answers.
- Hiding a missing wall height, subcontractor, or quote by inventing a default.
- Calling an engine or sending an RFQ from Guided Project Setup before those capabilities are authorized.
- A desktop-only step list that a later phone client cannot resume.
- Treating the Linda Bushel case as a gate for this walk. The 30 Sep 2026 checklist removed that gate.
- A migration for setup state against the Mac primary or the hosted validation database without a separate authorization.

## Timing

The 30 Sep 2026 owner direction removed the Linda Bushel case as the active stop. The sequence is [../PROJECT_DEVELOPMENT_CHECKLIST.md](../PROJECT_DEVELOPMENT_CHECKLIST.md).

The implementation plan is recorded in [start-project-implementation-plan.md](start-project-implementation-plan.md). It maps internal stages to existing services. SNP-1 is the first-gap foundation and is not the final readiness model. Rule 16 prohibits a detected state with no way to resolve it, and it does not make every missing fact a stop to all other work. SNP-2A is implemented. SNP-2 is blocked on drawings. SNP-3 is blocked on Plan Generation. PGE-1 remains the next implementation slice. No Feature Gate is opened in this direction record.
