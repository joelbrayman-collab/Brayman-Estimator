# Estimating path — alignment review

| Attribute | Value |
|-----------|--------|
| Status | Recorded. No product change. |
| Date | 2026-09-27 |
| HEAD at review | `0f5f5ca9be9dbd277e9b6214f6da859149e6c760` |
| Purpose | Write down the 26 Sep plan → scope → estimate model against what the repository and the hosted office actually contain. |

This review does not implement, migrate, deploy, or start the Brayman ICF estimator. The ICF specification file was not read. No ICF formula or product rule is stated here.

Signing, punch lists, QuickBooks, Field capture, and the public Website are outside this review.

## A. Settled product model

```text
PROJECT
→ PLANS
→ CONFIRMED SCOPE / WORK
→ INTERNAL OR SUBCONTRACTED
→ ESTIMATE BUILT UNDERNEATH
→ REVIEW
→ COMMERCIAL SETTINGS
→ PROPOSAL
```

Calculation engines are infrastructure. Add from calculation is not the normal way to start an estimate.

## B. What already exists

| Capability | Where it lives | What it does now |
|------------|----------------|------------------|
| Plan PDF upload | `app/plan_intelligence/services.py` (`ALLOWED_EXTENSIONS = {".pdf"}`) | Accepts a PDF on a project. |
| Plan documents, sheets, revisions, scale, measurement | `app/plan_intelligence/models.py`, routes under `/projects/<id>/plans` | A project can hold a PDF, sheets, a scale, and measurements. |
| Takeoff insertion | `app/services/takeoff_estimate_mapping.py` | An approved takeoff package can be placed on an estimate after a person confirms. Package approval alone does not insert lines. |
| Work catalog | `app/models/work_structure.py`, `app/services/work_structure.py` | `WorkType` and `WorkElementTemplate`. Baseline includes Site work, Foundation, and Structure. |
| Scope of work | `app/models/project_work_package.py`, `app/services/project_work_package.py`, `app/routes/project_scope.py`, `app/templates/projects/scope_of_work.html` | A person confirms catalog work on a project as Our crew (`INTERNAL`) or Subcontractor (`SUBCONTRACT`). Optional plan document. [ADR-055](../adr/ADR-055-project-work-package-ownership.md). |
| Estimate structure | `app/models/estimate.py` | `Estimate`, `EstimateVersion`, `EstimateSection`, `EstimateLineItem`. Versions lock. |
| Cost items and assemblies | Cost library and assemblies routes | What we pay, and reusable work. Lines are added from those records. |
| Costs & Pricing | Company costs and pricing screens | What we pay, reusable work, and how we price. Customer price after a company policy is applied comes from `EstimatePricingSnapshot`. |
| Company pricing | `OrganizationPricingPolicy`, `EstimatePricingSnapshot` | Named methods include `TRUE_GROSS_MARGIN`. A snapshot can govern a version. |
| Contract V1 | `docs/architecture/calculation-engine-result-contract-v1.md`, `app/services/calculation_result_contract.py` | Pinned quantity-result shape. A result carries physical quantities. It does not carry company price. |
| Mapper | `app/models/calculation_estimate_mapping.py`, `app/services/calculation_estimate_mapping.py`, `app/routes/calculation_mapping.py` | A person reviews a valid result and confirms a quantity onto a cost item or assembly. Labour is not forced into a cost item. Waste on the result is not applied a second time on the line. |
| Add from calculation page | `app/templates/estimates/calculation_list.html` | Explains the step. Says no calculation can be run from the estimate yet. No calculator button. No file box. |
| Test ingestion | `/estimates/<id>/versions/<version_id>/calculations/test-load` | Accepts a Contract V1 file for testing. Not linked from the ordinary page. |
| Labour book | `app/models/labour_engine.py` | Tasks, production rates, hourly direct-labour rates, calibration candidates, `EstimateLabourSnapshot`. |
| Internal breakdown | `/estimates/<id>/versions/<version_id>/internal-breakdown` | Office cost breakdown. Labour snapshots display and are not in the selling-price basis by default. |
| Customer proposal | Create Proposal from the estimate version | Customer output follows the estimate and the pricing snapshot. |

`ProjectWorkElement` remains the later build and schedule breakdown. `EstimateScopeDelivery` remains the delivery choice on an estimate line that already exists. Neither is the pre-estimate scope record.

## C. Workflow versus infrastructure

Contractor workflow that exists:

- Put a PDF on the project.
- Open Scope of work and confirm what the work is and who does it.
- Build an estimate with cost items, assemblies, company pricing, and a proposal.
- Read the internal breakdown. Issue a proposal from the estimate version.

Infrastructure underneath, not the front door:

- Contract V1.
- Calculation intake, quantity review, and mapping acceptance.
- Add from calculation, including its test-load page.
- Labour rates, production standards, and `EstimateLabourSnapshot`.
- Pricing snapshot math.

Scope of work does not call an engine, create an estimate line, or send a quote. A later internal package is what should call an engine. That call is not built.

## D. Live, in git only, or absent

| Item | State |
|------|--------|
| Plan PDF, sheets, scale, measurement | In git and on the hosted office. |
| Costs & Pricing, estimates, proposals, company pricing snapshots | In git and on the hosted office. |
| Contract V1 validator and mapper code | In git. Mapper tables are on the hosted validation database at Alembic `j0e1f2a3b4c5`. |
| Add from calculation page | In git and on the hosted office. Last hosted deploy of this page is the entry-experience correction, commit `0928c30`. The page says no calculation can be run yet. |
| Scope of work / `ProjectWorkPackage` | In git at `0f5f5ca`. Not deployed. Migration `k1f2a3b4c5d6` is not applied. |
| Mac primary | Alembic `h8c9d0e1f2a3`. Pre-mapper and pre-work-package schema. |
| Hosted validation | Alembic `j0e1f2a3b4c5`. Mapper schema. No work-package table. |
| CAD, DWG, OCR, automatic plan-to-scope | Absent. |
| Engine invoked from a confirmed work package | Absent. |
| Estimate section or line stored on a work package | Absent. |
| RFQ send from a subcontracted package | Absent. |
| ICF estimator | Absent. Specification file not read. |
| `LabourActualObservation` | Absent. |
| Researched industry labour benchmark as its own approved class | Absent. |

The Mac primary and the hosted validation database are schema-divergent on purpose.

## Subsequent status (2026-09-27 hosted alignment)

The estimate version no longer shows Add from calculation. The estimating module no longer says a future engine appears on that page. Footing, ICF wall, and concrete slab / thickened-edge slab remain separate engines. No formula was added. Hosted validation is Alembic `k1f2a3b4c5d6`. Deploy `dep-dasmtgp7lnhs739t87g0` is commit `ad4b912a7532de61e0b994237d61f8d71a7f2149`. The Mac primary remains `h8c9d0e1f2a3`. The findings above stay as the review that authorized the correction.

## E. Conflicts with the settled model

These were the conflicts at the time of the review. They were not changed in that review.

1. The estimate version page still shows **Add from calculation** as a button next to Create Proposal (`app/templates/estimates/version_detail.html`). On the hosted office a contractor can open that page as if it were a normal estimate action. The page itself says no calculation can be run yet. The settled model says this is not how an estimate starts.

2. `docs/modules/estimating.md` says that when a real engine exists, it appears on the Add from calculation page. The settled model says a confirmed internal work package is what later uses an engine. The page can remain the review step. It is not the start of the job.

3. The hosted office does not yet offer Scope of work. The settled first step after plans is in git only. Until a later deploy, the office a contractor opens still has the calculation button and does not have the scope page.

`docs/modules/estimating.md` also says the ordinary path is Project → Plans → Scope of work, and that Add from calculation is not the normal way to start. That sentence matches the settled model. The button and the “engine appears on this page” sentence do not.

## F. What the ICF estimator must reuse

After the specification is read, a private Brayman ICF estimator should use the path above. It should not open a second way to build an estimate.

Reuse:

- Project plans already stored on the project.
- Scope of work, with the ICF work identified in the work catalog and confirmed as Our crew or Subcontractor.
- Contract V1 for physical quantities only, still company-price neutral.
- The existing mapper, after a person confirms the quantity onto a company cost or reusable work.
- Company costs, supplier-price evidence, and the pricing snapshot for money.
- The labour book and `EstimateLabourSnapshot` for labour, with a person approving any change to company standards.
- Estimate versions, sections, lines, and version locking.
- The internal breakdown and the proposal for what the office and the customer see.

Brayman manufacturer rules, Brayman costs, Brayman margins, and Brayman history stay inside the authenticated platform. They do not go on the public Website.

If the specification requires a Contract V1 change, that change stops for Architect review. Contract V1 was not changed here.

## G. What this review does not authorize

- Implementing the ICF estimator.
- Removing or rewriting Add from calculation.
- Changing Contract V1.
- A migration, a hosted deploy, or a Mac primary migration.
- Engine orchestration, RFQ, labour formulas, or estimate-specific commercial settings.
- A V1 rescore.
- Any change to the public Website.
