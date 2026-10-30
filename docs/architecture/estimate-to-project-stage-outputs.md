# Estimate-to-Project Stage Outputs

| Attribute | Value |
|-----------|--------|
| Status | **DEFINED / ARCHITECTURE REVIEW / NOT IMPLEMENTATION-AUTHORIZED.** Contains no screens and no implementation plan. |
| Date | 2026-10-30 |
| Lifecycle | [estimate-to-project-lifecycle.md](estimate-to-project-lifecycle.md) |
| Gates | [governance/estimate-approval-and-commercial-gates.md](../governance/estimate-approval-and-commercial-gates.md) |
| Scheduling | [governed-scheduling-engine.md](governed-scheduling-engine.md) (five decisions approved 2026-10-30) |
| Document masters | Approved Master Template Family V1 (`app/services/approved_masters.py`): 01 Labour Calculation Detail, 02 Internal Detailed Cost Breakdown, 03 Customer-Facing Estimate, 04 QuickBooks Estimate Entry, 05 Ontario Construction Contract, 06 Door/Window/Skylight Schedule, 07 Client Construction Proposal, 08 Customer Detailed Cost Estimate |
| Verified against | Application code identical to origin/main `ed3ff7d6` |

## How to read this document

**Rows A–J** in each stage table:

| Row | Meaning |
|---|---|
| A | Purpose |
| B | Governed inputs |
| C | Governed outputs (records) |
| D | Human-readable output package |
| E | Approval / gate |
| F | Downstream consumers |
| G | Existing capability |
| H | Classification |
| I | Permanent lineage |
| J | Version / audit |

**Classification codes** (row H): **R** = reuse unchanged · **E** = extend · **C** = connect · **B** = build (genuine gap).

**Every stage:**

- Inherits project identity: the Brayman Project # and the Client Project #.
- Is append-only and audited. History is never overwritten.
- Treats a generated PDF or workbook as a view of governed records, never as the system of record.

---

## Stage 1 — Project & Documents

| | |
|---|---|
| **A** | Establish the project and govern its source documents. |
| **B** | Client; site address; project type; Client Project #; drawings and plans (PDF/CAD); permits context. |
| **C** | Project with its permanent Brayman Project # (BC-YYYY-NNNN). Client Project # (audited). Plan documents and sheets. Permit profile. Project location. |
| **D** | **Project Record Sheet:** identity, client, site, plans register, permit report (FG-016 PDF). |
| **E** | None. Identity changes are audited, not gated. |
| **F** | Every later stage, and every document header. |
| **G** | `Project`; project numbering and Client # (feature branch, **not on main**); `PlanDocument` / sheets (plan intelligence); `ConstructionDrawingSet`; `PermitProfile` and the permit report PDF. |
| **H** | R: plans, permits. E: project identity (merge the feature branch). B: Project Record Sheet (assembly only). |
| **I** | Every downstream record carries `project_id`. Documents carry the project numbers. |
| **J** | `project_identity_events`; plan revisions (ADR-007); permit snapshots (ADR-039). |

## Stage 2 — Scope Definition

| | |
|---|---|
| **A** | Name the work that exists and who is expected to do it, before quantities exist. |
| **B** | Stage 1 plans; contractor knowledge; project-type catalogue. |
| **C** | **Work packages** (extended selected-work items), each carrying: work identity; delivery method; commercial status (default Included); responsible party; source (contractor or plan). The shared **General conditions** package and its participation rule. |
| **D** | **Scope Register:** every package with its delivery method and status. Excluded work stays listed. |
| **E** | Contractor confirms the scope (existing "scope finalized"). |
| **F** | Takeoff, the estimate, subcontract RFQs, scheduling. |
| **G** | `GuidedEstimate` / `GuidedEstimateStage` (selected work, the "one authoritative scope service"); `ProjectWorkPackage` (ADR-055); `WorkElementTemplate` catalogue. |
| **H** | E: selected work gains commercial status, responsible party and delivery method; excluded work is no longer hidden or deleted. C: fold `ProjectWorkPackage` in. B: shared-package participation rule. |
| **I** | Work package → plan document. Work package → catalogue template. |
| **J** | `GuidedEstimateEvent` (append-only); `decided_by` / `decided_at`. |

## Stage 3 — Takeoff & Construction Requirements

| | |
|---|---|
| **A** | Establish what is built and how much, independent of who pays. |
| **B** | Plans; work packages; calculators and engines (ICF, foundation, deck, framing, siding). |
| **C** | Takeoff packages and candidates; calculation results; reviewed quantities; construction model revisions; material requirements. Each is tied to a **work package**. |
| **D** | **Takeoff Package** per work package: quantities, waste, units and source citations. Uses the existing takeoff and calculator review screens. |
| **E** | Human quantity review before anything is inserted (ADR-006, ADR-054). |
| **F** | Estimate lines; supplier pricing requests; labour quantities. |
| **G** | `TakeoffPackage` / `TakeoffCandidate`; `CalculationResultIntake` → `CalculationQuantityReview` → `CalculationMappingAcceptance`; `TakeoffEstimateInsertion` with citations; `ProjectConstructionModelRevision`; `MaterialRequirement`. |
| **H** | R: the takeoff and calculator review chain. C: takeoff and requirements → work package. |
| **I** | Drawing → takeoff → reviewed quantity → estimate line (exists). Quantity → work package (missing). |
| **J** | Insertion citations; review and acceptance records; construction-model revisions. |

## Stage 4 — Estimate Build

| | |
|---|---|
| **A** | Turn requirements into costed work: materials, labour, subcontract, equipment, allowances, general costs. **Scheduling intelligence starts here.** |
| **B** | Reviewed quantities; work packages; cost library and assemblies; approved contractor costs; supplier prices; labour tasks and production rates; the labour cost rate. |
| **C** | Estimate version with sections linked durably to work packages, and lines. Labour lines carry quantity, production rate, hours and crew. Equipment and other lines. Allowances. Subcontract quote evidence. Supplier pricing requests and returns. **Estimated hours per work package and activity; calculated duration** (hours ÷ crew × hours per day). |
| **D** | **Supplier Pricing Request** (approved form) and **Supplier Package**. **Subcontract RFQ** (later stage-8 evidence; see stage 8). **01 Labour Calculation Detail** (master). |
| **E** | Contractor cost approvals (FG-027) for the costs used. |
| **F** | Stage 5 review; the preliminary schedule. |
| **G** | `EstimateVersion` / `EstimateSection` / `EstimateLineItem`; `EstimateScopeDelivery`; labour engine; `ContractorCostApproval`; `SubcontractQuoteEvidence`; supplier request → quote (`SupplierRequestShare`); supplier pricing request PDF and form; master 01. |
| **H** | R: lines, pricing requests, cost approvals. E: labour lines gain quantity and rate (the Paulusse model); create the labour snapshot. C: section → work package. B: calculated-duration evidence. |
| **I** | Quantity → line; line → work package; supplier return → line cost; subcontract quote → line. |
| **J** | Version per change; costing snapshot (FG-027); labour snapshot; supplier quote events. |

## Stage 5 — Contractor Review

| | |
|---|---|
| **A** | The contractor decides what Brayman is pricing, who does excluded work, and the commercial terms. **This is where Paulusse REV2 behaviour lives.** |
| **B** | The stage 4 estimate; Anticipated Construction Start; company scheduling template. |
| **C** | Per work package: commercial status (Included/Excluded) and responsible party, with delivery method confirmed. Project labour rate and target margin, with reasons. Selling price and customer allocation, rounded once. **Anticipated Construction Start** (planning input). **Preliminary scheduling intelligence and Proposed Initial Gantt** (proposed, not approved). Preliminary resource demand. **Subcontract planning windows**. |
| **D** | **Contractor Estimate Package**, the dynamic review environment (the in-app equivalent of the Paulusse builder): scope panel, quantities and materials, labour and final cost, settings, a customer preview. Plus **02 Internal Detailed Cost Breakdown** (master) and a **Proposed Initial Gantt** preview. Any exported PDF of it is a worksheet, with a PDF import-and-compare path back in. |
| **E** | None. Review is iterative; every change is audited. |
| **F** | Gate 1; subcontract RFQs (planning windows); preliminary resource demand on the Company Calendar (proposed). |
| **G** | Project rate and margin controls (feature branch, **not on main**); pricing engine and snapshots; master 02; `ProjectCommercialContext`. |
| **H** | E: work-package status and party; pricing over included packages only. B: Contractor Estimate Package view; Anticipated Construction Start; preliminary Gantt generation; planning windows; PDF import-and-compare. C: merge rate/margin. |
| **I** | Package status → included lines → direct cost → selling price → customer allocation. Anticipated start → preliminary schedule. |
| **J** | `PricingAuditEvent` (rate and margin changes); package status history; preliminary-schedule generations kept as calibration evidence. |

## Stage 6 — Contractor Approval (Gate 1)

| | |
|---|---|
| **A** | Brayman formally approves this scope and price for customer issue. |
| **B** | The reviewed version. |
| **C** | **Estimate Approval Record:** approver; date and time; version; the full commercial summary (packages included and excluded, materials, hours, rate, labour, subcontract, equipment, allowances, direct cost, margin, gross profit, selling price, HST, total, exceptions, assumptions). Fingerprint. **Locked version.** |
| **D** | **Estimate Approval Summary**: the concise commercial summary used at APPROVE ESTIMATE. |
| **E** | **Gate 1**: a human contractor approval inside Calibrayt. |
| **F** | Proposal generation; the approved preliminary schedule basis. |
| **G** | `sign_off_estimate` (records who and when, locks, builds the proposal); version locking; `unlock_version` route. |
| **H** | E: approval record with a values snapshot and fingerprint. B: the summary output. Govern: `unlock_version` must not be usable on an approved version; a change means a new version. |
| **I** | Approval → exact version → pricing snapshot. |
| **J** | Immutable approval record; any change creates a new version. |

## Stage 7 — Customer Proposal & Acceptance (Gate 2)

| | |
|---|---|
| **A** | Issue the exact approved version to the customer and record acceptance. |
| **B** | The approved version and its approval record. |
| **C** | Proposal and its lines (from the same package selections). Client link. **Proposal Acceptance** (content fingerprint). Generated contract and **Project Contract Snapshot**. **Project Commercial Baseline**: the accepted version with its pricing snapshot. **Approved project schedule basis**: the preliminary schedule promoted against the accepted scope. |
| **D** | **Customer Package:** **08 Customer Detailed Cost Estimate** (INCLUDED IN BRAYMAN CONSTRUCTION PRICE / EXCLUDED / BY OTHERS), **07 Client Construction Proposal** (Included and Excluded derived from packages), **05 Contract**, **03 Customer-Facing Estimate** and **06 Door/Window/Skylight Schedule** where applicable, **04 QuickBooks Estimate Entry** (internal). Sent through CaliSIGN (CONTRACT) or the proposal client link. |
| **E** | **Gate 2**: customer acceptance. |
| **F** | Execution seeding; MONITOR baseline; procurement; invoicing. |
| **G** | `Proposal` / `ProposalLineItem` (`source_line_item_id`); proposal PDF; `ProposalClientLink`, `ProposalAcceptance`; contract generation and snapshot; masters 03–08; CaliSIGN CONTRACT; MONITOR baseline (ADR-021); QuickBooks estimate. |
| **H** | R: acceptance, contract snapshot, MONITOR baseline. E: masters 07 and 08 gain an Excluded/By Others section (needs master approval; see contradictions). C: proposal scope ← package status. B: the promoted schedule basis. |
| **I** | Acceptance → proposal → version → packages → lines. |
| **J** | Content fingerprints; immutable contract snapshot; CaliSIGN events. |

## Stage 8 — Procurement & Subcontracts (Gate 3)

| | |
|---|---|
| **A** | Turn accepted scope into approved external commitments, with scheduling evidence. |
| **B** | Commercial baseline; packages by delivery method; material requirements; supplier quotes; subcontract quotes; the schedule basis. |
| **C** | Purchase orders with lines linked to estimate lines and material requirements. **Subcontract commitments / work orders** per package. **Subcontract duration and availability evidence**, per phase. Supplier lead times, giving backward-planned latest order dates. **Commitment approval record** per external commitment. Supplier and subcontractor **confirmations**. Committed cost. |
| **D** | **Procurement Package:** PO documents (supplier signing PDF), subcontract work orders, a commitment register, and lead-time / latest-order-date list. |
| **E** | **Gate 3**: contractor approval of each commitment before CaliSIGN sends it. Routine approval follows the responsible procurement or PM role. |
| **F** | The approved project schedule; committed cost; field deliveries. |
| **G** | `SupplierPurchaseOrder` (lines as `lines_json`; `schedule_item_id`); supplier signing; CaliSIGN SUPPLIER_ORDER with APPROVED_FOR_SIGNATURE; `SupplierDeliveryChange`; `SubcontractQuoteEvidence`; `Subcontractor`; supplier package PDF. |
| **H** | R: supplier PO signing, CaliSIGN approval-before-send. E: PO approval queue; CaliSIGN subcontract family. C: PO lines → estimate lines and requirements; quote → commitment. B: subcontract commitment; phase duration and availability evidence; backward planning. |
| **I** | Package → line → requirement → PO line → delivery → schedule activity. Package → subcontract quote → commitment → schedule phases. |
| **J** | CaliSIGN events and executed artifacts; commitment approval records; delivery-change counters. |

## Stage 9 — Execution

| | |
|---|---|
| **A** | Run the accepted scope with no re-keying: work plan, schedule, crews, field work, billing. |
| **B** | Commercial baseline; packages; labour snapshots; commitments; the schedule basis. |
| **C** | Work plan: elements per **package** (not per section name) and activities per labour line or snapshot. **Approved project schedule** and live schedule items (phases). Assignments and crews. **Company Schedule Change Requests** with **impact analyses**. **External schedule-change drafts**. Supplier and subcontractor **confirmations**. **Schedule history**. Time entries and approved hours. Field records (extra work, punch list, final walkthrough). Customer invoices. |
| **D** | **Execution Package:** Project Gantt; Company Calendar and resource views (crew, employee, equipment); work plan; schedule change requests and impact reports; crew schedule notices (SMS); delivery schedule; change order documents; invoice and QuickBooks output. |
| **E** | PM commits project-contained changes. Company Schedule Authority for company-impacting changes (blocking). Responsible role approves external communications. Time approval. |
| **F** | Change control; cost control; closeout. |
| **G** | `ProjectWorkElement` / `ProjectWorkActivity` seed; `WorkScheduleItem`, `WorkScheduleHistory`, assignments, crews, dependencies, conflict facts, project shift; `crew_notices`; `CompanyAppointment` and calendar feeds; time entries and approval; extra-work reports; punch list; final walkthrough; `CustomerInvoice`; accounting export. |
| **H** | R: SCH-A–D, time, field, invoicing. E: schedule phases; anticipated vs confirmed windows; change-request governance; delivery proposals routed through draft → approval. C: element ← package; activity ← line or snapshot. B: Gantt view; impact analysis; Company Schedule Change Request; Company Schedule Authority role; schedule generation. |
| **I** | Accepted scope → work activity → schedule activity → assignment → time → actual hours. |
| **J** | Schedule history (append-only) with request revisions and override audit; time history; scope history. |

## Stage 10 — Closeout & Learning

| | |
|---|---|
| **A** | Close the project and turn its results into calibration for future work. |
| **B** | Baseline; change orders; actual costs; approved hours; committed and actual supplier costs; schedule history. |
| **C** | **Estimate-to-actual by work package**: quantity, labour hours, production rate, supplier cost (estimated / committed / actual), margin. **Duration evidence chain**: estimated hours → calculated → proposed → PM-adjusted → approved → actual hours → actual duration. Calibration candidates. The closed project state. |
| **D** | **Closeout Package:** estimate-to-actual report, margin report, production learning report, schedule performance report, final invoice / QuickBooks reconciliation. |
| **E** | Project close (lifecycle authority). Calibration candidates need human approval (labour engine). |
| **F** | Future estimates (rates, production, durations, templates). |
| **G** | Project close and reopen (`project_operating_lifecycle`); MONITOR; `LabourCalibrationCandidate`; `ProjectDirectCostActual`; historical estimates. |
| **H** | R: close, MONITOR, calibration workflow. E: actuals by package; schedule performance into calibration. B: estimate-to-actual by package; closeout package. |
| **I** | Package → estimate → commitment → actual → calibration. |
| **J** | Calibration lifecycle (DRAFT → APPROVED); close events. |

---

## Cross-stage control — Change Control (stages 7–10)

| | |
|---|---|
| **Purpose** | Change the project without overwriting the accepted baseline. |
| **Outputs** | Change order (priced against a pricing snapshot) with **items linked to work packages and lines**. `ProjectWorkScopeDelta` against activities. Revised commercial position (baseline + approved changes). Extra-work conversion. Schedule consequences, which flow through the schedule change-request path. |
| **Package** | Change order PDF (`project_controls/pdf.py`); CaliSIGN CHANGE_ORDER for customer signature; change log. |
| **Approval** | Customer signature on the change order. Contractor approval of the price, reusing the estimate approval pattern. |
| **Classification** | R: change orders, CO signing, scope delta, extra-work reports. C: CO item → package or line. E: revised commercial position. |
| **Audit** | The original baseline is immutable. Changes are additive versions. |

## Cross-stage control — Cost & Margin Control (stages 7–10)

| | |
|---|---|
| **Purpose** | Track estimate → accepted budget → committed → actual, and compare expected with actual margin. |
| **Outputs** | Accepted budget by package (from the baseline). Committed cost (POs, subcontract commitments). Actual cost (direct cost actuals, approved time × rate). Approved change-order revenue and cost. Projected and actual gross margin. |
| **Package** | Margin monitor view and report; budget-vs-committed-vs-actual by package. |
| **Approval** | None: reporting only. Actuals follow their own provenance. |
| **Classification** | R: MONITOR, direct cost actuals, approved time. E: committed-cost layer; package dimension on actuals. C: actual → package or line. |
| **Audit** | Actuals are superseded, never edited (existing rule). |

---

## Summary

### Outputs reusable unchanged

- plan documents and the permit report
- the takeoff and calculator review chain
- estimate lines and costing snapshots
- contractor cost approvals
- the supplier pricing request form and supplier package
- master 01 (labour detail), master 02 (internal cost breakdown) and master 04 (QuickBooks entry)
- proposal acceptance and client link; contract generation and snapshot; master 05
- the MONITOR baseline
- supplier PO signing; CaliSIGN approval-before-send and its families
- the SCH work plan, schedule items, history, assignments, crews, dependencies and conflict facts
- crew notices and calendar feeds
- time entry and approval
- extra work, punch list and final walkthrough
- invoicing and QuickBooks export
- change orders and scope deltas
- project close; labour calibration

### Outputs requiring extension

- **Selected work → governed work package:** commercial status, responsible party and delivery method; excluded work stays visible.
- **Labour lines:** quantity and production rate; the labour snapshot is actually created.
- **Pricing:** priced over included packages only.
- **Gate 1:** the approval record gains a values snapshot and fingerprint; unlocking an approved version is governed.
- **Masters 07 and 08:** an Excluded / By Others section.
- **Purchase orders:** an approval queue.
- **CaliSIGN:** subcontract, company schedule change and external scheduling confirmation families.
- **Schedule items:** phases; anticipated vs confirmed windows; proposed/effective governance.
- **Delivery-change proposals:** draft → approval → send.
- **Actuals:** a work-package dimension.
- **Calibration:** the duration chain.

### Connections required

- `ProjectWorkPackage` → selected work (fold in)
- section → work package (replacing the name match)
- takeoff / requirement → work package
- labour line or snapshot → work activity
- work package → work element
- PO line → estimate line and material requirement
- subcontract quote → commitment → schedule phases
- change order item → package or line
- actual → package or line
- approved time → schedule activity
- the per-project labour rate, margin and project numbers branch → main

### Genuine new outputs

- Project Record Sheet (assembly only)
- Scope Register
- the shared / general-conditions package rule
- Contractor Estimate Package (in-app builder view) and the PDF import-and-compare path
- Anticipated Construction Start
- preliminary scheduling intelligence and Proposed Initial Gantt
- subcontract planning windows
- Estimate Approval Summary
- the promoted schedule basis at acceptance
- subcontract commitments / work orders and the commitment register
- phase duration and availability evidence
- backward planning (latest order date)
- Project Gantt
- Company Schedule Change Request, impact analysis and the Company Schedule Authority role
- external schedule-change drafts
- estimate-to-actual by package
- schedule performance and the duration evidence report
- the Closeout Package

## Contradictions discovered

**All resolved on 2026-10-30.** See [estimate-to-project-lifecycle.md](estimate-to-project-lifecycle.md) § Approved decisions: 1 → decision 1; 2 → decision 2; 3 → decision 3; 4 → decision 4; 5 → decision 5; 6 → decision 6; 7 → already resolved by the scheduling decisions.

1. **Approved masters vs new customer content.** The Master Template Family V1 is mandatory: "data changes by project, the approved document format does not", and any master change needs Joel's explicit approval. Masters 07 and 08 need an Excluded / By Others section to satisfy the customer-facing scope clarity rule. Changing them needs Joel's master approval.
2. **New document type vs "no new layouts".** The Contractor Estimate Package (stage 5) is not one of the eight governed document types. The landscape builder proven in Paulusse needs registering as an approved governed type before it becomes a platform output. The masters' orientation also needs checking against the one-orientation package preference.
3. **Selected-work exclusion vs the scope-clarity rule.** Marking selected work N/A currently requires its estimate lines to be deleted, and N/A work is hidden. That contradicts "deselecting scope changes responsibility; it does not erase the scope".
4. **Two scope sources.** `ProjectWorkPackage` (ADR-055: "confirmed scope before an estimate") and selected work ("the one authoritative scope service") both claim pre-estimate scope. They must be reconciled to one owner.
5. **Unlocking vs Gate 1.** An `unlock_version` route exists. Gate 1 requires approved versions to stay locked, with a change creating a new version.
6. **Ordering before acceptance.** `place_order` places supplier POs with no check of customer acceptance. The governed sequence puts procurement after Gate 2. Early ordering may sometimes be legitimate (for example, long lead items), so this needs an explicit rule.
7. **Superseded rules, now resolved.** The SCH V1 rules "no automatic movement" and the automatic supplier delivery proposal are replaced by approved scheduling decisions 3 and 4. They are recorded in [governed-scheduling-engine.md](governed-scheduling-engine.md) §20; no open decision remains.

## Recommended first implementation slice (recommendation only)

**Governed work package and contractor scope review, proven on Paulusse in the application:**

1. Extend selected work with commercial status, responsible party and delivery method. Keep excluded work and its lines rather than deleting them.
2. Link each section to its work package durably.
3. Price over included packages only, with the shared General-conditions package rule.
4. Merge the per-project labour rate, margin and project-number branch.
5. Acceptance test: recreate the Paulusse REV2 results in the app, matching its baseline and exclusion tests exactly.

Customer masters 07 and 08 are a separate approval step (contradiction 1).
