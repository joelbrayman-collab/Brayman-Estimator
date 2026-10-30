# Estimate-to-Project Platform: Implementation Plan

| Attribute | Value |
|-----------|--------|
| Authority | Joel, 2026-10-30: "BUILD, VERIFY AND DEPLOY THE APPROVED ESTIMATE-TO-PROJECT ARCHITECTURE" (end-to-end execution mandate) |
| Architecture | [estimate-to-project-lifecycle.md](../architecture/estimate-to-project-lifecycle.md) (including the six approved decisions) · [estimate-to-project-stage-outputs.md](../architecture/estimate-to-project-stage-outputs.md) · [governed-scheduling-engine.md](../architecture/governed-scheduling-engine.md) · [fg-035-sch-dynamic-scheduling-preflight.md](../architecture/fg-035-sch-dynamic-scheduling-preflight.md) · [ADR-055](../adr/ADR-055-project-work-package-ownership.md) · [governance/estimate-approval-and-commercial-gates.md](../governance/estimate-approval-and-commercial-gates.md) · [operations/paulusse-rev2-hold-2026-10-30.md](../operations/paulusse-rev2-hold-2026-10-30.md) |
| Branch | `feature/estimate-to-project-2026-10-30`, from origin/main `ed3ff7d6`, with the architecture docs branch and the labour-rate / margin / project-number branch merged in |
| Ledger | [estimate-to-project-ledger.md](estimate-to-project-ledger.md): what is done, the evidence, and the next step. **Resume from the ledger.** |
| Method | Reuse → extend → connect → build only genuine gaps. Test-driven (red → green → refactor) for behaviour changes. One commit per proven slice. Migrations are forward-safe, additive and deterministic, and never destroy data. |

## Order of work

The order follows dependencies: everything downstream hangs off the governed work package, so it comes first.

| Slice | Content | Primary reuse / extension |
|---|---|---|
| **S0** | Baseline: merged branches green; full regression baseline | — |
| **S1** | **Work-package foundation.** `GuidedEstimateStage` gains: commercial status (INCLUDED / EXCLUDED); responsible party (CONTRACTOR / CLIENT / BY_OTHERS / NAMED + name); delivery method (SELF_PERFORMED / SUBCONTRACTED / MATERIAL_ONLY / LABOUR_ONLY / ALLOWANCE, derived from the existing responsibility and split by default); shared participation rule. `EstimateSection.work_package_id` gives a durable link, backfilled deterministically from today's name match; `section_for` uses the link. `ProjectWorkPackage` is folded in: confirmed packages become selected work and the confirm/retire page writes there. | selected work, guided estimating, ADR-055 |
| **S2** | **Non-destructive exclusion and pricing.** Exclude/include work keeping every line, calculation, quote and requirement. Pricing, costing, the allocation of sell price to lines, and section subtotals all count *participating* lines only. Shared/general package rule: default "while any contractor work is included", configurable per project. Customer scope data: Included and Excluded / By Others lists. | estimate_costing, pricing_engine, estimate_builder |
| **S3** | **Paulusse parity in the application.** The REV2 dataset as a synthetic fixture. Exact baseline and exclusion results: $53,106.44 baseline; $49,184.67 with removal excluded; every package toggled; rate $80; margin 20%. | — |
| **S4** | **Gate 1.** `EstimateApproval` record: frozen commercial summary, fingerprint, who and when, extending `sign_off_estimate`. No unlock after approval. Successor version via the existing clone. Estimate Approval Summary output. | proposal_acceptance.sign_off_estimate, estimates.clone_current_version |
| **S5** | **Customer and contractor outputs.** Masters 07 and 08 gain the Excluded / By Others section (approved masters, edited on the Mac master folder; SHA register updated). The proposal PDF shows Included and Excluded from the packages. **Contractor Estimate Package:** a new governed, landscape, generated output from app data. | approved_masters, proposal_pdf, Paulusse builder |
| **S6** | **Labour and execution lineage.** `EstimateLabourSnapshot` created from labour lines (quantity, rate, hours, crew, calculated duration). The work plan is seeded one element per **work package** and one activity per labour line or snapshot, with the source line linked. | labour_engine, work_structure |
| **S7** | **Gate 3: procurement and subcontracts.** PO lines linked to estimate lines and material requirements. Commitment approval before send. **Early Procurement Exception** before Gate 2. `SubcontractCommitment` (work order) from the selected `SubcontractQuoteEvidence`. CaliSIGN SUBCONTRACT family. | supplier_hub, subcontract_quote, signing |
| **S8** | **Scheduling foundation.** Anticipated Construction Start (planning input). Company scheduling templates (phases, durations, dependencies). Preliminary schedule generation (Proposed Initial Gantt). Schedule phases with anticipated and confirmed windows. Project Gantt view and controller over `WorkScheduleItem`. | SCH-A–D |
| **S9** | **Schedule governance.** Proposed change → impact analysis (project, company, external) → automatically calculated downstream proposals → PM commit (project-contained) or Company Schedule Change Request (blocking; ACCEPT / REJECT / PROPOSE NEW TIME as revisions of one request; both authorities) → owner override (audited). External drafts from the existing delivery-change auto-proposal: draft → role approval → send. Subcontract planning windows on RFQs; phase duration and availability evidence. | WorkScheduleHistory, SupplierDeliveryChange, CaliSIGN |
| **S10** | **Change control and cost/margin control.** Change-order items linked to work package and line. Committed cost layer. Actuals attributable to the work package. MONITOR by package. | project_controls, monitor, direct_cost_actuals |
| **S11** | **Closeout and learning.** Estimate vs actual by package; budget → committed → actual; duration evidence chain; calibration evidence through the existing labour calibration approval. | monitor, labour_engine calibration |
| **S12** | **Release.** Full regression; whole-branch review; browser end-to-end walk (desktop and phone); migration rehearsal on a copy of the production backup; release gate and deploy by the established procedure; post-release checks. | tools/release |

## Standing rules carried into the work

- The Paulusse business calculations are acceptance data and are never changed to make a test pass.
- Production data: migrations are additive. Every backfill is deterministic and proven on a copy of the latest production backup before deploy.
- Releases follow `docs/operations/release-procedure.md`. The Mac release gate is run by Joel. The authorization for this scope is given in the mandate.
- Synthetic test data only. No credentials in code, logs or chat.
- Approved masters stay outside Git (ADR-032). The Family 05 master is never committed.
