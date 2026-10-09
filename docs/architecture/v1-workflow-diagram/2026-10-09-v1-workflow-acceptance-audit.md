# V1 workflow acceptance audit — 9 October 2026

## 9 Oct 2026 — diagram interpretation

Joel clarified the approved Construction Platform Lifecycle Blueprint. It is a functional completeness reference. It is not a screen design, a navigation specification, or a literal flowchart of pages.

Two tests apply, and they stay separate.

**Functional completeness.** Use the diagram to find the intended capabilities and the handoffs between them. Compare those with the existing platform and with V1 governance. A box that governance has already left for later stays deferred. Do not promote every diagram component into V1.

**Contractor usability.** Judge whether a contractor can find and finish the real task. Do not require the screens, the navigation, or the labels to copy the diagram. Do not rebuild the Project Hub so that its strip matches the diagram’s eleven stages.

Under this clarification, the earlier finding that the hub strip uses different words from the eleven stages is not a defect. The historical finding stays in the UX table below. It is not a reason to redesign the hub. Usability work stays on broken handoffs, missing V1 functions, actions that are hard to find, extra navigation, and instructions a contractor cannot follow. A small wording change matters when it blocks that use.

The User Guide should teach the screens the contractor actually sees. The diagram is the checklist that those capabilities were not dropped. Matching the eleven stage names is not a Guide requirement.

This clarification does not change product code and does not rescore V1.

## 9 Oct 2026 — contractor language correction accepted

ChatGPT accepted the wording. The hub names the internal cost breakdown, the customer estimate, and QuickBooks entry as available. QuickBooks stays hand-typed. A production Ontario contract is stated as not available. Generated contract, supplier package, proposal section, and pricing method replace the contractor-facing labels. Help uses the same generated-contract sentence. The contract document body was not edited. The operator-pack tests now require the hosted office and keep the Mac address only on the backup sheet, where it is the mirror. Focused tests: 100 passed, exit 0. Full suite: 2298 passed, 11 skipped, exit 0. Live deploy `dep-db4kubmi0phs73d30nb0` at `13544f29ee25402d9bf4059556c7b5d0a40909ab`. No migration. Checklist Step 8 stays open. The register was not rescored.



| Attribute | Value |
|-----------|--------|
| Status | Read-only audit. Product implementation is not authorized. |
| Date | 2026-10-09 |
| Approval | Joel approved this diagram as the V1 workflow and UX reference on 9 October 2026. |
| Purpose | Map the approved visual to the existing platform. Do not redesign the flow. |
| Repository at audit | `9b9f09004b0ac112eb9eef28860220664ccc8265` |
| Live application | `dccd5cac6f7c8c281a312e252fe3aacb15ad3e6b` |
| Live deploy | `dep-db4h3dks728c73aohka0` |
| Register | Not rescored. |

## Original diagram

| Field | Value |
|-------|--------|
| Original filename | `CalibraytAI Construction Platform Lifecycle Blueprint(1).png` |
| Desktop source | `/Users/joelbrayman/Desktop/CalibraytAI_20Construction_20Platform_20Lifecycle_20Blueprint_281_29.png` |
| Preserved path | `docs/architecture/v1-workflow-diagram/CalibraytAI Construction Platform Lifecycle Blueprint(1).png` |
| SHA-256 | `0476f6f14dfc6f1eb73da3b30f1a6714c5ed0d7c0911aaf2900591ec2ecf6390` |
| Bytes | 1,898,938 |
| Image | PNG, 1536 × 1024 |
| Desktop file time | 2026-10-09 15:20:27 local |
| Visible title | CalibraytAI Construction Platform Lifecycle Blueprint |
| Visible footer | V1.1, OCT 2026 |
| Source image | Copied unchanged. `cmp` matched the Desktop file. |

The two supporting ChatGPT names, `CalibraytAI Complete Project Lifecycle.png` and `CalibraytAI Construction Workflow Overview.png`, were not on this Mac. This audit uses only the approved primary image.

This session read the image and the repository. It did not click every live screen again. Live evidence below is the recorded 9 October synthetic path and the pages opened on the construction release. Where that evidence is absent, the status is NOT VERIFIED.

## How to read the matrix

Status words: IMPLEMENTED, PARTIAL, MISSING, DEFERRED, NOT VERIFIED.

A passing service test is not contractor acceptance. Governance decides what is V1. The diagram is the workflow picture. A box that governance has already placed after V1 is DEFERRED. It is not a new V1 requirement.

Settled decisions kept closed: hosted office is the working office; Mac is the mirror; QuickBooks Option A is complete; the live QuickBooks API is deferred; Ontario legal approval is not a universal commercialization blocker; production contracts stay gated; Help D1–D4 and Voice D5 are built; the synthetic commercial path is accepted; checklist Step 8 stays open; `SITE`, `FOUND`, and `STRUCT` stay unbound; generic estimating stays incomplete; professional drawing production stays deferred; no new formula is authorized.

## Engines on the diagram

| Diagram component | Intended action | Screen and route | Service | Status | Repository evidence | Live evidence | Gap | Governing requirement | Correction |
|-------------------|-----------------|------------------|---------|--------|---------------------|---------------|-----|----------------------|------------|
| Concrete Engine, Public + Platform | Calculate concrete alone, or inside a project | No standalone office page. Slab quantity is inside estimating. | `app/services/foundation_quantity.py` (`concrete_slab`); contract in `app/services/calculation_result_contract.py` | PARTIAL | Contract and quantity service exist. Sidebar has no calculator. | NOT VERIFIED as a contractor page | No office entry that starts concrete without a project | Diagram: public and platform. Checklist: the contractor stays in Guided Project Setup and does not leave to hunt a calculator. | None authorized. Public page is Website evidence, not a new platform formula. |
| Stair Engine, Public + Platform | Calculate a stair alone, or inside a project | None in this repository | None. Drawing proofs are project-specific geometry. | DEFERRED | `docs/current-state.md` records that this repository has no stair engine. Useful Tools HEAD `59e1979e735ec606af341e97e46e112136fbdfa0` is not checked out here. | NOT VERIFIED | Platform stair engine is absent | Later engine. Professional drawing production is deferred. | Do not rebuild a stair formula from the Bushel sheet. |
| ICF Engine, Internal only | Calculate an ICF wall for the company, not the public | `/estimates/<id>/versions/<vid>/wall-form-quantities` | `app/services/icf_quantity.py`, engine id `icf_wall` | PARTIAL | 8-inch wall form offers the existing review. Guided setup opens that page only after an estimate version exists (`app/services/project_setup.py`). | The construction-release calculation page showed ICF. A priced ICF line was not walked on 9 October. | Other cores are not calculable. The page requires an estimate. | Diagram marks ICF internal only. Product direction keeps the running calculator at 8-inch. Manufacturer expansion is not authorized. | None. |
| Framing Engine, Platform | Frame from the same engine, in a project | Construction information stores member counts. It is not a framing engine. | `app/routes/project_construction.py`, `/projects/<id>/construction` | PARTIAL | Stored member count can be offered and confirmed onto one ordinary line. | Project 46: revision, quantity 3, line 137, Proposal 18. | `STRUCT` stays unbound. This page is not the diagram’s Framing Engine. | Step 8 remains open. No new formula. | None. |
| Roofing Engine | Calculate roofing | None | None | DEFERRED | Register: specialized trades are later product direction. | NOT VERIFIED | No roofing engine | Not a V1 package | None. |
| Siding Engine | Calculate siding | None | None | DEFERRED | Same register direction | NOT VERIFIED | No siding engine | Not a V1 package | None. |
| Drywall Engine | Calculate drywall | None | None | DEFERRED | Same register direction | NOT VERIFIED | No drywall engine | Not a V1 package | None. |
| Flooring Engine | Calculate flooring | None | None | DEFERRED | Same register direction | NOT VERIFIED | No flooring engine | Not a V1 package | None. |
| Future Engines, As needed | Add an engine when a real job needs it | None | None | DEFERRED | Diagram label is “As needed.” | NOT VERIFIED | No shelf of future engines | Do not invent engines in this audit | None. |

Diagram rule beside the engines: one engine, consistent results, usable across the lifecycle, independent or project-connected, internal or public by purpose. The platform follows the project-connected office path. Public use is the Website, which this repository does not contain.

## Access paths

| Diagram component | Intended action | Screen and route | Service | Status | Evidence | Gap | Class |
|-------------------|-----------------|------------------|---------|--------|----------|-----|-------|
| Public Useful Tools | Free calculators. Useful answers. No private project data. | Not in this repository | Website. Result contract: `docs/architecture/calculation-engine-result-contract-v1.md` says the Platform does not call the Website and the Website does not call the Platform. | NOT VERIFIED | Checklist step 2 records Website Useful Tools stabilization closed at Version 31. The Site repository is not checked out on this Mac. This session did not open the public site. | Live public inputs, results, and confidentiality were not re-checked. | Acceptance gap for this audit only. Do not modify the Website. |
| Contractor Platform | Signed-in project workflow | Office shell, `app/templates/base.html`, sidebar `app/navigation.py` | Authenticated routes | IMPLEMENTED | Home, Projects, Clients, costs, proposals, company library, crews. | Calculators are not a sidebar item. | Not a defect. Guided setup is the project path. |
| Internal-only | Company capabilities such as ICF stay off the public site | ICF route above, inside an estimate | `icf_quantity.py` | PARTIAL | The wall-form route comment says it does not open a public calculator. | Public-site separation was not opened this session. | F for the platform boundary that exists. Public side NOT VERIFIED. |

## Project lifecycle

| Stage | Intended action | Screen and route | What is saved / produced | Status | Live evidence | Gap | Class |
|-------|-----------------|------------------|--------------------------|--------|---------------|-----|-------|
| 1 Start Project | Create a project and set the job | `/projects/new` | Project and client link | IMPLEMENTED | Projects list and synthetic projects 46 and 47 opened on the release. A new customer project was not created. | None on the create route itself | F |
| 2 Guided Project Setup | Answer what the job needs | `/projects/<id>/setup` | Reads readiness. Opens the existing next page. | IMPLEMENTED | Repository resolver in `app/services/project_setup.py` | The future readiness model is not implemented. Checklist step 4 records that limit. | E for the future model. The current walk is not a defect. |
| 3 Ready to Price | Confirm scope and prepare the estimate | Setup next action, then scope `/projects/<id>/scope` and hub | Scope confirmation, drawing choice, estimate create or resume | PARTIAL | Synthetic project already had an estimate before today’s commercial walk. | `SITE`, `FOUND`, and `STRUCT` stay unbound. Generic estimating stays incomplete. Step 8 stays open. | E. Do not bind those areas from this audit. |
| 4 Estimate | Use engines and produce a profitable estimate | `/estimates/<id>/versions/<vid>` and `/calculations` | Confirmed quantity becomes one ordinary line. Costing and pricing are separate approvals. | PARTIAL | Project 46, estimate 41, version 47, line 137 quantity 3, costing snapshot 23, pricing snapshot 15, customer total 49.86 | The walked quantity is a stored member count, not every engine on the diagram. | The accepted path is F. Unbound areas stay E. |
| 5 Proposal | Create and refine the customer proposal | `/estimates/<id>/versions/<vid>/proposals/new`, `/proposals/<id>/preview`, `/proposals/<id>/pdf` | Draft proposal copies the frozen pricing snapshot. Customer title is Construction Estimate. | IMPLEMENTED for the draft path | Proposal 18, `PROP-2026-0007`, grand total 49.86. Not sent. Not signed. | Send and signature were outside the accepted walk. | F for the accepted document. Send remains a later contractor action. |
| Revise / negotiate | Move between estimate and proposal | Version and a new or existing proposal | A later construction revision does not change a confirmed line. | IMPLEMENTED as explicit confirmation | Revision 2 stored five joists. Line 137 stayed at 3. | There is no separate “negotiate” screen. The return path is the version and the proposal draft. | F |
| 6 Contract Signing | Authorize the work | `/projects/<id>/contract` | Generator and fail-closed review exist. Production packages stay at zero until approved legal content. | PARTIAL | Repository and prior contract gates. Not re-walked on project 46. | Production issuance still requires the legal-content gate. | E for counsel text. The screen is not a missing generator. |
| 7 Build / Manage | Do the work, track progress | Hub project work, `/work-structure/projects/<id>`, `/field/...`, schedule and time links on the hub | Work plan, schedule, time, field observations | PARTIAL | Field Web is a closed V1 surface in the register. This audit did not open Field on a phone. | Hours stay hours. They do not become labour dollars. That payroll gap is not authorized. | E for payroll. Field route existence is F. Phone use this session is NOT VERIFIED. |
| 8 Change Orders | Change scope, cost, and schedule, then continue | Hub “New Change Order”; `/projects/<id>` change-order list via `project_controls` | Change-order records. Work-structure links exist. | PARTIAL | Routes in `app/routes/work_structure.py` and the hub. | Change-order document family is future. Not walked on project 46. | E for the document family. Record routes are not missing. |
| 9 Complete / Close | Finish and close | `/projects/<id>/close` and reopen | Close and reopen exist. Punch list and client walkthrough exist. | PARTIAL | Register: Completion Sign-Off is not implemented and waits on whole-product UAT. | Closeout is not a finished contractor ending. | C until sign-off is in scope. Do not build it from this audit. |
| 10 Actuals | Record actual cost, quantity, and performance | Hub money / direct-cost actuals POST `/build/projects/<id>/direct-cost-actuals` | Actual cost rows. Estimated-versus-actual monitor was closed under its own gate. | PARTIAL | Gate record exists. Project 46 actuals were not entered in this audit. | Live actuals on the synthetic commercial project are NOT VERIFIED. | C for a fresh live walk. The feature is not missing. |
| 11 Learn & Improve | Turn finished jobs into the next job | Hub section `#hub-learn` | The hub states that LEARN is not operational. | DEFERRED | `app/templates/projects/detail.html` marks LEARN Future. Checklist step 9 is queued. | No learning recommendation is produced. | E |
| Continuous learning arrow | Learning runs along the whole job | Same LEARN section | No operating loop writes historical performance back into the next estimate. | DEFERRED | Same hub copy | The arrow is not an office action | E |

Help sits on the hub stages that are operational. Voice asks the same Help answers. Voice does not change a project. Those products are already built.

## Core capabilities and data

| Diagram item | Platform home | Status | Note |
|--------------|---------------|--------|------|
| Project Management | `/projects/`, `/projects/<id>` | IMPLEMENTED | Clients and locations have their own screens. |
| Scope & Work Definition | `/projects/<id>/scope`, work structure | PARTIAL | Scope page exists. Unbound elements stay unbound. |
| Drawings & Documents | Plan intelligence upload, sheet index, measure | PARTIAL | Upload and measure exist. Generating a professional set from calculations is deferred. |
| Plan Generation | No contractor generator for a professional set | DEFERRED | Drawing production stays deferred. |
| Cost Management | Cost library, pricing, labour rates | IMPLEMENTED | QuickBooks Option A is the human-typed handoff at `/projects/<id>/quickbooks-entry`. |
| Estimating | Estimate version, calculations, costing, pricing | PARTIAL | Accepted synthetic chain exists. Generic estimating does not. |
| Proposals | Proposal preview and PDF | IMPLEMENTED | Accepted on Proposal 18 as a draft. |
| Contracts | Contract review | PARTIAL | Production content stays gated. |
| Change Orders | Hub and project controls | PARTIAL | Records exist. The document family is future. |
| Production Management | Schedule and work plan | PARTIAL | Company calendar is in the sidebar. This audit did not walk a live schedule. |
| Analytics & Reporting | Monitor comparisons where the monitor gate closed them | PARTIAL | LEARN analytics are future. |
| Projects / Clients / Locations | Project, client, and location screens | IMPLEMENTED | |
| Drawings / Documents data | Plan documents on the project | PARTIAL | Stored uploads. Generated professional sets are deferred. |
| Trade Engine Results | Calculation intake and review | PARTIAL | Member count and 8-inch ICF can enter review. Other engines do not. |
| Estimates / Proposals data | Estimate versions and proposals | IMPLEMENTED | Synthetic chain is the live evidence. |
| Contracts / Change Orders data | Contract snapshot record and change-order records | PARTIAL | Production legal text and the change-order document family stay gated or future. |
| Actual Costs / Quantities | Direct-cost actuals and confirmed quantities | PARTIAL | Quantity path was lived. Actual-cost entry on that project was not. |
| Reusable Work / Assumptions | Assemblies in the sidebar | IMPLEMENTED as a library | Not re-tested this session. |
| Learning / Historical Data | Past jobs / historical estimates | PARTIAL | Ingestion exists. The hub does not turn it into the next project’s operating advice. |

## Perspective A — complete project

A contractor can open Projects, create a project, continue setup, enter construction information, confirm a stored member count, approve costing, apply organization pricing, and open a draft customer PDF. That path was accepted on synthetic project 46 through Proposal 18.

The hub strip the contractor sees is Project, Settings, Money, Documents, Project work, and LEARN · Future. The diagram’s eleven named stages are pages and buttons inside that hub, plus Continue setup. They are not the strip labels.

Return paths that exist: a later construction revision leaves a confirmed line unchanged; setup sends the contractor to the next existing page; change orders return to the hub; close has a reopen page.

Dead ends relative to the diagram: LEARN has no next job. Completion Sign-Off is not on the close path. Production contract generation stops on the legal gate, which is the intended stop. Roofing, siding, drywall, flooring, and a platform stair engine are not steps the contractor can take.

The hub still tells the contractor: “The four-output package remains Future.” Outputs for the internal breakdown, the customer proposal, and QuickBooks Option A are already in the product. That sentence is stale on the working screen (`app/templates/projects/detail.html`).

## Perspective B — calculators without a full project

The office sidebar has no calculator. Concrete, stair, framing, roofing, siding, drywall, and flooring cannot be opened as independent office tools.

ICF opens only from an estimate version, which Guided Project Setup reaches after the project exists. That matches the internal-only mark and the rule that the contractor stays in the setup walk.

The authorized handoff into an estimate is the existing calculation review. Stored member count was confirmed live. The 8-inch wall form offers that same review. This audit did not confirm an ICF quantity onto a priced proposal.

No new formula is required to explain this. Independent public calculation is the Website path in the next section.

## Perspective C — public Useful Tools

The diagram separates three audiences: public tools, the signed-in contractor platform, and internal-only engines.

This repository holds the separation rule and the Website checkpoint record. It does not hold the Website application. This session did not load the public calculators, so availability, inputs, results, and the absence of company prices, supplier rates, and project files are NOT VERIFIED here.

ICF is marked internal only on the diagram. The platform wall-form page is inside an authenticated estimate. That is the correct side of the line. The public site was not checked for an ICF tool.

## UX and language

| Finding | Where | Class |
|---------|--------|-------|
| Hub stage words differ from the diagram’s eleven stages | `app/templates/projects/detail.html` lifecycle strip | B. The pages exist. The strip is a different map. A Guide written on the strip would not match the approved picture, and a Guide written only on the picture would not match the strip. |
| “The four-output package remains Future.” | Same hub note | B and D. The contractor-facing sentence is behind the product. |
| “Contract snapshot” and package code | `app/templates/projects/contract_review.html` | B and D |
| “Frozen supplier-facing snapshot.” | `app/templates/projects/supplier_package.html` | B and D |
| “Authoritative method” | `app/templates/estimates/version_detail.html` and `app/templates/estimates/detail.html` | B and D |
| “This snapshot section” | `app/templates/proposals/detail.html` | B and D |
| Help still says “contract snapshot.” | `app/presentation/help_content.py` | D. Help D1–D5 stay built. This is leftover wording. |
| Search and notifications | Header buttons are disabled, “coming soon” | E. Not a workflow blocker. |
| Desktop sequence | Continue setup is the early next action. Later work is hub buttons. | F for the accepted commercial path. |
| Mobile | Field Web has an earlier phone record. This audit did not use a phone. | NOT VERIFIED for this audit. |

Missing-fact behaviour that already exists and should stay: a blank elevation is unknown and is not stored as zero; a blank member length is not offered; production contract copy says production is unavailable when the legal gate is closed.

## Acceptance gaps that remain

1. Checklist Step 8 stays open. Generic estimating is incomplete. `SITE`, `FOUND`, and `STRUCT` stay unbound.
2. Real contractor UAT is not accepted. Ben’s hosted sign-in is not verified.
3. Completion Sign-Off is not implemented.
4. Production contract text is not approved, so production issuance stays closed.
5. LEARN is not operational.
6. Public Useful Tools were not opened in this audit.
7. This audit did not repeat a phone pass.
8. Actuals and a change order were not entered on the synthetic commercial project.

## User Guide

The Guide is not ready to write.

The workflow a Guide would teach is split between the approved picture and the hub strip. The hub still calls the four-output package future. Office screens still say snapshot and authoritative method. LEARN, production contracts, unbound elements, and generic estimating are still open or deferred. Public tools were not re-verified. Those are the corrections and boundaries a Guide would have to tell the truth about. Writing the Guide now would freeze the stale sentence and the mismatched stage names.

## Priority

1. Contractor completion of the path that already exists: keep the accepted project → construction quantity → costing → pricing → proposal path intact.
2. Broken handoffs that are already decided: do not bind `SITE`, `FOUND`, or `STRUCT`, and do not add engines the register left for later.
3. Navigation truth: the hub’s “four-output package remains Future” sentence, then the difference between the diagram’s stage names and the hub strip.
4. Office language already found: contract snapshot, supplier snapshot, proposal snapshot, and authoritative method, including the Help line.
5. Mobile: still needs a real pass before anyone claims phone acceptance of this audit.
6. User Guide: after the wording the Guide must repeat is stable.

## One next action

ChatGPT reviews this audit and decides whether the stale hub sentence and the four office labels are one bounded copy correction before any Guide writing.

## Authorization

Product code, formulas, migrations, deployment, a V1 rescore, real customer edits, and User Guide writing are not authorized. Preserving this diagram and this audit is the documentation authorized by the 9 October prompt.
