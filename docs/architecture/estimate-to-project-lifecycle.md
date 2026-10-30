# Canonical Estimate-to-Project Lifecycle

| Attribute | Value |
|-----------|--------|
| Status | **RECORDED / ARCHITECTURE REVIEW / NOT IMPLEMENTATION-AUTHORIZED.** Stages were proposed by the 2026-10-30 stage and capability audit (against origin/main `ed3ff7d6`) and are the working basis for subsequent architecture records. Exact stage outputs are not yet defined. |
| Date | 2026-10-30 |
| Owner | Joel Brayman |
| Related | [governance/estimate-approval-and-commercial-gates.md](../governance/estimate-approval-and-commercial-gates.md) (three human gates; customer-facing scope clarity) · [operations/paulusse-rev2-hold-2026-10-30.md](../operations/paulusse-rev2-hold-2026-10-30.md) (proven reference behaviour) · [governed-scheduling-engine.md](governed-scheduling-engine.md) · [selected-work-estimating.md](selected-work-estimating.md) · [ADR-055](../adr/ADR-055-project-work-package-ownership.md) · [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) |

**Product objective:** construction drawings go in, and a contractor-ready project comes out.

**Rule:** REUSE → EXTEND → CONNECT → build only genuine gaps. Calibrayt is not rebuilt.

## Stages

| # | Stage | Content | Gate / control |
|---|---|---|---|
| 1 | Project and documents | Project identity and numbers; governed drawings and plans | |
| 2 | Scope definition | The selected work and who does it (Approach B: the contractor names the work first) | |
| 3 | Takeoff and construction requirements | Quantities and construction requirements | |
| 4 | Estimate build | Lines, labour, supplier and subcontract pricing, allowances, shared/general costs | |
| 5 | Contractor scope and pricing review | Included/excluded scope, responsible party, delivery method, labour rate, margin, final price. **Paulusse behaviour lives here.** | |
| 6 | Contractor approval | Approval inside Calibrayt; the version locks | **Gate 1** |
| 7 | Customer proposal and acceptance | Issue and acceptance of the exact approved version. The accepted version becomes the Project Commercial Baseline. | **Gate 2** |
| 8 | Procurement and subcontracts | Each external commitment is approved, then sent by CaliSIGN | **Gate 3** |
| 9 | Execution | Work plan, schedule, crews, field work, billing | |
| 10 | Closeout and learning | Estimate-to-actual comparison; calibration of future estimates | |

Two controls run alongside stages 7–10. They are not sequential stages:

- **Change control:** the accepted baseline is never overwritten.
- **Cost and margin control:** estimate → accepted budget → committed → actual.

### Differences from the 12-stage hypothesis

- **Scope definition is added before takeoff.** The platform already asks for the work first.
- **Customer issue and acceptance are merged into one stage.** They are states of one Proposal record.
- **Change control and cost control are cross-cutting controls, not stages.**
- **Billing sits under execution and closeout.** Customer invoices and the QuickBooks export already exist.
- **Scheduling is not a separate stage.** It develops progressively across stages 4, 5, 7, 8 and 9; see [governed-scheduling-engine.md](governed-scheduling-engine.md).

## Work-package owner (recommended)

Extend the existing selected-work item (`GuidedEstimateStage`, under `app/services/selected_work.py`) to be the governed work package. It would carry four things:

- commercial status (Included or Excluded)
- responsible party
- delivery method
- a durable link to its estimate section(s)

Fold `ProjectWorkPackage` (ADR-055) into that work package rather than running both.

Do **not** create a new work-package table. `EstimateScopeDelivery` (ADR-048) remains the per-line make/buy detail beneath the package.

**Conflict to resolve:** today, marking selected work N/A requires its estimate lines to be removed first, and N/A work is hidden. That contradicts the proven rule "deselecting scope changes responsibility; it does not erase the scope".

## Shared / general costs (recommended)

Shared and general costs get an explicit **shared** work package with a declared participation rule. The default is the Paulusse rule: the package stays while any contractor work remains included.

- The rule is configurable per company and per project, not fixed platform-wide.
- The customer sees these costs as a "General conditions" line.
- Version-level overhead percentages remain an alternative method.

## Lineage

**Exists today:**

- Takeoff to estimate line, through the insertion and calculator-review records.
- Estimate line to:
  - scope delivery
  - subcontract quote evidence
  - costing snapshot line
  - material requirement
  - proposal line
- Version to proposal, acceptance, contract snapshot and the MONITOR baseline.
- Work activity to its source estimate version.
- Change order to its pricing snapshot.
- `ProjectWorkScopeDelta` to work activity.

**Missing:**

- Selected work to estimate section. Today they are matched by name only.
- Package or section to work element. The seed copies the section name.
- Work activity to estimate line. The labour snapshot exists but is never created.
- Purchase order lines to estimate line or material requirement. PO lines are stored as `lines_json`.
- Subcontract quote to a commitment. No commitment record exists.
- Change order item to estimate line or package.
- Direct cost actual to package or line.

## Stage outputs

Defined on 2026-10-30 in [estimate-to-project-stage-outputs.md](estimate-to-project-stage-outputs.md). For each stage it gives purpose, inputs, outputs, package, gate, consumers, existing capability, classification, lineage and audit. It also covers both cross-stage controls.

## Approved decisions (Joel, 2026-10-30) — implementation authorized

The six open contradictions from the stage-output work are decided. Implementation, verification and deployment of this architecture are authorized end to end. The plan and progress ledger are in [docs/implementation/](../implementation/).

1. **Masters 07 and 08: Excluded / By Others.** APPROVED. Both masters gain an Excluded / By Others section. Excluded work stays visible to the customer where commercially relevant, with the responsible party where known. Family V1 standards are otherwise preserved.
2. **Contractor Estimate Package.** APPROVED as a new governed output: a generated contractor-facing working and review view of the governed estimate and work-package data. The application model stays authoritative. Paulusse REV2 is the functional reference. Its orientation follows its purpose (landscape).
3. **Excluded work is non-destructive.** APPROVED. Excluding a work package never destroys any of the following:
   - work package
   - takeoff
   - lines
   - labour
   - material requirements
   - subcontract evidence
   - drawing lineage
   - scheduling intelligence
   - dependencies
   - responsibility

   Only commercial participation and responsibility change. The rule that lines must be deleted before work can be marked N/A or excluded is removed for commercial exclusion.
4. **Single governed scope owner.** APPROVED. Selected Work (`GuidedEstimateStage`) is the governed Work Package and the only scope owner. Confirmed Project Scope (`ProjectWorkPackage`, ADR-055) is folded into it. There is no third table. Downstream lineage originates from the Work Package.
5. **Gate 1 immutability.** APPROVED. A Gate-1-approved version cannot be unlocked or altered. A change creates a successor version. The approved version is preserved permanently, with who approved it, when, and the exact values.
6. **Procurement before Gate 2.** APPROVED rule: customer acceptance precedes external commitments. Exception: a governed **Early Procurement Exception** records:
   - reason
   - proposed commitment
   - financial exposure
   - approving authority
   - approver identity and time
   - resulting commitment
   - permanent audit

   It is never the normal path.
