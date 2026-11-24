# Living Project P&L: design approvals and S0 design closure

| Attribute | Value |
|-----------|--------|
| Status | **RECORDED / APPROVED BY JOEL BRAYMAN** (24 Nov 2026) |
| Governing principle | One project. One living record. One dashboard. One source of truth. |
| Confidentiality | This repository is public. Employee loaded rates, wages and project profit are Owner / System Administrator only and are **not** recorded here. The figures live in the S0 Consolidated Package and R5, which are held outside the repository. |

## Approvals recorded (24 Nov 2026)

1. The **R5 Living Project P&L template** is approved.
2. The **Project Dashboard visual master** is approved.
3. The **S0 Consolidated Package** (R5 data pack, consolidated implementation specification, S0 closure register), **R5**, and the approved dashboard requirements together form the **governing implementation specification**.
4. The five-gate plan (S0 to S12) is approved. Each gate needs documented acceptance criteria, Practice validation, then explicit Production authorization. Migrations need explicit approval.

## Approved decisions carried into implementation (not reopened)

- The labour selling rate ($75/h on the validation project) is configurable per project and is not the loaded labour cost.
- Loaded labour cost comes only from the employee cost records in People & Access, Employees. There is no second register and no second rate store.
- A Person is linked to a User so that approved time reaches the cost record.
- Materials are priced by **markup on net cost**. Selling = net x (1 + markup). Profit = selling less net. Margin = profit divided by revenue. Legacy pricing methods stay readable and unchanged. One shared materials calculation. Markup is configurable by company, project and supplier. A previously quoted customer price may override the calculated selling price with a recorded reason. Rounding is deterministic, traceable and reconciles to approved totals.
- Supplier discounts reduce material cost and are independent of contractor markup. A project-specific supplier discount never becomes a default.
- The approved baseline is immutable. Only the accepted roofing option becomes the baseline. Actuals, forecasts and calibration never overwrite it.
- Financial summaries show Revenue, Cost, Profit, Profit Margin in that order. Labour allocation schedules show hours and assignments only.
- The Project Dashboard and the detailed report read one assembler. Operational and financial tiers are separate. The dashboard follows the project lifecycle.
- A **project-performance permission** is independent of employee compensation. The Hub Money and labour-cost visibility gap is closed across UI, routes, reports, exports and drill-downs.
- Window, door and other outstanding estimate items stay **provisional** until confirmed.
- LEARN calibration needs human approval and its own Feature Gate. QuickBooks Time activation is the final gate.
- Brayman Construction onboarding (Ben, employees, suppliers, company settings) is deferred. Missing employee records and live project data are not software deficiencies.

## S0 design requirements: closed

| S0 design requirement | State |
|----------------------|-------|
| R5 reporting template | CLOSED (approved) |
| Project Dashboard visual master | CLOSED (approved) |
| Reconciliation of source hours, rates and totals | CLOSED as a design exercise. The validation project's totals tie to the source documents. |
| Consolidated specification and closure register | CLOSED (approved) |

## Carried as provisional (not closed; do not freeze a baseline until resolved)

These are commercial reconciliation items on the Geleynse validation project, not design requirements:

- Whether the supplier quotation's roofing lines are correctly excluded from Brayman's materials.
- Whether installation labour is inside the estimated labour hours.
- Window count (quote against plan schedule), Brayman's cost on the window and door quote, installation pricing.
- Current crane quote; roofing subcontract line detail and porch roof inclusion; unpriced materials; attic hatch fire rating.
- Supplier quotation expiry date earlier than its issue date.
- Employee loaded rates, until the employee cost profiles are entered at onboarding.

The existing Geleynse estimate is **not modified**. An unreconciled baseline is **not frozen**.

## Authorization boundaries

- Gate 1 (Financial Foundation: S1, S2, S2b) is authorized to proceed as a Feature Gate: [FG-042](../feature-gates/FG-042-financial-foundation-immutable-baseline-employee-cost-permissions.md).
- Migrations are **not** authorized until Joel approves the migration proposal in FG-042.
- Production deployment of Gate 1 needs Joel's approval of the Practice validation results.
- Gates 2 to 5 follow in sequence after Gate 1 approval.
