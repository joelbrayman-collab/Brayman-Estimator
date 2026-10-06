# Project development checklist

| Attribute | Value |
|-----------|--------|
| Status | Project governance. Not an implementation authorization. |
| Date | 2026-09-30 |
| Repository | `/Users/joelbrayman/Desktop/Brayman-Estimator` |
| Resume | [session-handoff.md](session-handoff.md) |

The Darcy / BMR meeting package is recorded at [architecture/darcy-bmr-meeting-readiness-2026-10.md](architecture/darcy-bmr-meeting-readiness-2026-10.md). It does not change this sequence and it does not authorize a build.

This checklist is the one CalibraytAI development sequence. Chat memory is not. The public Website and the private Platform are separate source and deployment surfaces. They are not separate products and they do not have separate roadmaps.

NEW MATERIAL REQUIREMENTS ARE CLASSIFIED AND ASSIGNED TO THE APPROPRIATE V1 COMPLETION COMPONENT SO THEY ARE RECALLABLE AT THE CORRECT DEVELOPMENT STAGE.

The recall list is [v1-completion-register.md](v1-completion-register.md) section 2.1. This checklist does not keep a second ideas list. A new requirement does not change the current step unless it is a genuine dependency of that step. When a step becomes the authorized build, its prompt recalls every register row for that component.

## One product

ONE CALIBRAYTAI PRODUCT. ONE MASTER DEVELOPMENT ROADMAP. ONE GOVERNED IMPLEMENTATION OF REUSABLE DOMAIN LOGIC. MULTIPLE CONSUMING SURFACES.

A separate screen does not justify a second copy of the mathematics. A separate repository does not justify a competing construction rule. This checklist does not create a runtime call between the Website and the Platform, and it does not choose where a shared package would live. [architecture/calculation-engine-result-contract-v1.md](architecture/calculation-engine-result-contract-v1.md) already pins that boundary. Contract V1 stays **ACCEPTED / PINNED** at `2903a45074df21b1c99390cb9aab68638970a2ff`. It is not edited here.

## Status law

| Mark | Meaning |
|------|---------|
| ✅ COMPLETE / STABLE | Implementation and evidence are complete, and Human UAT has occurred where it is required. |
| 🟡 CURRENT | The one current product objective. |
| ⬜ QUEUED | Sequenced. Not started. |
| ⛔ BLOCKED | That item cannot proceed until a real dependency is resolved. An operational block is not a second product roadmap. A case conflict is not a blocker unless a product step actually depends on it. |

## Product spine

USER / PROJECT INTENT → REQUIRED CAPABILITY → GOVERNED DOMAIN / CALCULATION ENGINE → GOVERNED RESULT / GEOMETRY → DRAWING / TAKE-OFF / ESTIMATE → BUILD / MONITOR → ACTUALS → LEARNING.

On the private Platform, Start New Project — Guided Project Setup is the readiness walk of that spine. The product concept is Project Readiness. The contractor states the construction task. CalibraytAI chooses the internal capability. The contractor does not leave the walk to find a calculator. [architecture/start-project-guided-wizard-product-direction.md](architecture/start-project-guided-wizard-product-direction.md). [architecture/estimating-path-alignment-2026-09-27.md](architecture/estimating-path-alignment-2026-09-27.md).

## Surfaces

Consumers. Not roadmaps.

| Surface | Role |
|---------|------|
| Public Website / Useful Tools | Presents a governed result to the public. Does not own company price, margin, or the private estimate. |
| Private Platform | Project, scope, price, and the estimate. Consumes a governed result through the accepted mapper. Does not keep a second formula. |
| Plan Generation | Draws governed geometry when required drawings are absent. Does not recalculate the same element. |
| Estimating / take-off | Uses governed quantities. Company pricing stays here. |
| Later Field / PWA | Reads the same project state. Field Web v1 is already closed and is not this phase. |

## Product inventory — existing calculators

| Capability | Role | Consumers | Status |
|------------|------|-----------|--------|
| Employment vs. Entrepreneurship | Public decision support. Not forced into the private project walk. Parked FG-039 is a separate Platform record and is not this public tool. | Public Website | ✅ CLOSED at Website Version 31. Quote Win Rate, Seasonality, Slower-Season Approach, and Small Contracting Business are removed. Working Weeks and Winter Protection / Heat remain active. Solo and Owner + Labourer / Helper remain. Helper Wage is an owner estimate. |
| Concrete Calculator | One public formula: `lib/calculation-engine/concrete-slab.ts`. | Useful Tool; later project workflow and Plan Generation only when authorized | ✅ CLOSED. Public modes are Standard Slab and Thickened Edge. The dormant broad implementation is historical compatibility only. Footings, walls, columns, post holes, curbs, and concrete stairs are not current public capabilities. |
| Stair Calculator | One formula. Bushel stair scripts are proving evidence, not another calculator. | Useful Tool; later project workflow, Plan Generation, stair detail, and take-off only when authorized | ✅ CLOSED. Calculation PASS. Visual PASS. Pin PRESENT / PASS. The diagram uses the calculated geometry. |

The reusable stair result and the Bushel finished stair agree on total rise 38 in, 5 risers, 7.60 in rise, 4 treads, 11 in going, and 44 in total run. That agreement is evidence. It does not settle Bushel stringer count or throat.

## Complete / stable

| Item | Status |
|------|--------|
| Private Platform office through the recorded V1 build | ✅ COMPLETE / STABLE as far as the register goes. Official V1 remains **65% / 4 of 11**. Secondary **79% / 22 of 28**. Not rescored. |
| Contract V1 | ✅ COMPLETE / STABLE. **ACCEPTED / PINNED**. Engine owns the mathematics and the structured result. Pricing, margin, and the private estimate stay outside it. |
| Field Web v1 | ✅ COMPLETE / STABLE as its own closed programme. |
| Public Website Version 31 | ✅ CLOSED stabilization. Live `https://calibai.joel-brayman.chatgpt.site/`. Project `appgprj_6a9095543b74819186183f9a522890e5`. SHA `5dcb4f2b9cc0a291a16375f06ce89f09a02262cf`. Version id `appgprj_6a9095543b74819186183f9a522890e5~appgver_ed1a760941b48191badc6ac0c2d5f347`. Deployment `appgdep_6abd379bbb8081918aae3b170706263b`, SUCCEEDED. Source/live parity PASS. |

## One sequence

Development freeze: **LIFTED FOR CONTROLLED START NEW PROJECT DEVELOPMENT.** Plan Generation Engine productization remains in progress. PGE-1 is **CLOSED**. PGE-2 is **CLOSED**. PGE-3 is **CLOSED**. PGE-4 is **CLOSED**. PGE-5 is **CLOSED**. PGE-6 is **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. Rule 16 — no dead ends — is recorded. SNP-1 is **CLOSED AS A SLICE**. SNP-2A is **IMPLEMENTED / TESTED**. SNP-2 is **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. SNP-4 is **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. SNP-6 is **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. ESTIMATE HANDOFF is **IMPLEMENTED**. MAPPER HANDOFF is **VERIFIED / PRESERVED**. The 1 Oct 2026 Rule 16 re-audit is 7 / 7 PASS. SNP-3 is **CLOSED AS A SLICE**. START NEW PROJECT is **IMPLEMENTED**. GUIDED PROJECT SETUP is **IMPLEMENTED**. PROJECT READINESS is **CURRENTLY FIRST-GAP FOUNDATION**. The future readiness model is **NOT YET IMPLEMENTED**. Website stabilization is CLOSED. Platform stabilization is CLOSED and LIVE / VERIFIED. Hosted password verification, bypass removal, and production cutover stay in Later.

| Order | Step | Kind | Status |
|-------|------|------|--------|
| 1 | This unified architecture | Governance | Recorded by this checklist. Not an implementation authorization. |
| 2 | Website Useful Tools stabilization | Website surface | ✅ CLOSED at Version 31. |
| 3 | Platform existing-problem stabilization | Closed | ✅ CLOSED and LIVE / VERIFIED. Current deploy `dep-daulf9u0tbcc73bomdgg` at `ca37d8b6939f6494b6ff415bad17953886366728`, finished 2026-09-30T18:41:57Z. PLAT-LOGO-01 CLOSED / LIVE VERIFIED. Prior deploy `dep-daukqvg473hc73bkouug` at `45ab150aa724f4fa50eb7d496f886bd1a5f2e4e0` is superseded. |
| 4 | Start New Project — Guided Project Setup | Product | SNP-1 **IMPLEMENTED / TESTED**. Rule 16 re-audit 1 Oct 2026: 7 / 7 PASS. SNP-2 **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. Guided Project Setup **IMPLEMENTED**. Project Readiness remains the first-gap foundation. The future readiness model is not implemented. [architecture/start-project-implementation-plan.md](architecture/start-project-implementation-plan.md). |
| 5 | Approved Start New Project slices | Product | SNP-2A **IMPLEMENTED / TESTED**. SNP-2 **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. Rule 16 re-audit 7 / 7 PASS. SNP-3 **CLOSED AS A SLICE**. SNP-4 **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. SNP-6 **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. ESTIMATE HANDOFF **IMPLEMENTED**. MAPPER HANDOFF **VERIFIED / PRESERVED**. The future readiness model is not implemented. |
| 6 | Use the governed engine where the project walk requires it | Product | Engine-boundary explanation is shown on Continue setup. Unbound Our-crew work says no quantity is calculated from the work name. A subcontract-only package says no crew calculation is required. Our-crew ICF wall opens the existing wall-form entry. No second formula. |
| 7 | Plan Generation Engine productization | Product | 🟡 **IN PRODUCTIZATION.** PGE-1 through PGE-5 **CLOSED**. PGE-6 **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. Build Drawings on the plans page supports `dimensioned_plan`. `stair_detail` stays an engine profile. Project-document integration **PARTIALLY IMPLEMENTED**. Project drawing requirement **IMPLEMENTED**. Present is derived. Build Drawings remains an action. SNP-2 **IMPLEMENTED / TESTED / CLOSED AS A SLICE**. Rule 16 re-audit 7 / 7 PASS. SNP-3 **CLOSED AS A SLICE**. Guided Project Setup **IMPLEMENTED**. [architecture/plan-generation-engine-productization.md](architecture/plan-generation-engine-productization.md). |
| 8 | Estimating consumes the governed result | Product | 🟡 OPEN. This is the current commercial priority. Professional construction drawing production is **DEFERRED / SHELVED / NOT V1-CRITICAL** and is not a dependency of this step. **ICF PATH COMPLETE** (5 Oct 2026): our-crew ICF wall opens the existing wall-form page, `build_icf_standard_quantities` emits Contract V1, validation runs before mapping, and one ordinary estimate line is created only after explicit confirmation. No drawing PDF and no `PlanDocument` are required. **CONSTRUCTION MODEL STORED-FACT QUANTITY READ IMPLEMENTED / TESTED** (5 Oct 2026): `read_stored_member_quantities` returns grouped member counts and the supplied length already stored on those members. A missing length stays `MISSING_SCHEDULE_FACT` and names the members. The read does not price, write an estimate line, or compose a sheet. **CONSTRUCTION MODEL → MATERIAL REQUIREMENT BOUNDARY IMPLEMENTED / TESTED** (5 Oct 2026): `read_construction_material_requirements` keeps that member count and supplied length as separate facts, with the stored material id and name. A missing material, size, or length stays missing. It does not write a `MaterialRequirement` row, choose a stock length, add waste, or set a price. **CALIBRAYTAI MULTI-SUPPLIER COST ENGINE** (6 Oct 2026) is the existing FG-029 catalogue: two supplier products can map to one canonical material, and public price evidence stays separate from contractor-account evidence. BMR Winchester is the first proving supplier, not a separate engine. ICF manufacturer profiles stay product-system knowledge. Effective contractor cost is not resolved. ADR-008 stays Proposed. **SUPPLIER PRICE EVIDENCE CLASS + VALIDITY IMPLEMENTED / TESTED** (6 Oct 2026): `price_class` is `PUBLIC_LIST_PRICE` or `CONTRACTOR_CONFIRMED_PRICE`. `captured_at`, `effective_from`, and `effective_to` stay separate. A later row does not rewrite an earlier row. Migration `o5b6c7d8e9f0` is not applied to the Mac primary or the hosted database. Effective contractor cost is still not resolved. **SUPPLIER PRICE EVIDENCE WINDOW IMPLEMENTED / TESTED** (6 Oct 2026): `read_supplier_price_evidence_window` returns the public and contractor-confirmed rows valid at an as-of time. It does not choose a price. **EFFECTIVE CONTRACTOR COST RESOLVER IMPLEMENTED / TESTED** (6 Oct 2026): `resolve_effective_contractor_cost` uses the contractor supplier account as the supplier context. A valid contractor-confirmed price is the result. A public list price is returned only when no confirmed price is valid, and it keeps the public class. No supplier is compared. No estimate line is written. **RESOLVED SUPPLIER COST → FG-027 HUMAN COST APPROVAL: ARCHITECTURAL GAP IDENTIFIED** (6 Oct 2026). `approve_all_costing` freezes existing estimate lines into `EstimateCostingSnapshot`. A snapshot line requires an `EstimateLineItem`. The snapshot has no supplier-product or price-evidence fields. ADR-044 keeps supplier evidence out of V1-02. ADR-008 stays Proposed. No second costing snapshot was created. **CONTRACTOR COST APPROVAL** is a missing organization record, not a supplier act and not the estimate snapshot. `CostItem` is one mutable planning cost. It was not implemented. **CONTRACTOR COST APPROVAL RECORD IMPLEMENTED / TESTED.** `contractor_cost_approvals` stores Brayman's decision and cites supplier evidence. The supplier is provenance only. A public list price stays unapproved. Migration `p6c7d8e9f0a1` is not applied to the Mac primary or the hosted database. **APPROVED CONTRACTOR COST → ESTIMATE COSTING SNAPSHOT IMPLEMENTED / TESTED.** **COSTING REVIEW — CONTRACTOR COST PROVENANCE IMPLEMENTED / TESTED.** The review reads the frozen snapshot citation and does not resolve a new supplier price. The four records stay supplier price evidence, effective contractor cost, Brayman contractor cost approval, and the estimate costing snapshot. **JOB-SPECIFIC SUPPLIER PRICING REQUEST** is the manual supplier-response workflow and is **NOT IMPLEMENTED**. Calibrayt generates the requirement. The supplier confirms product, price, and availability. Brayman approves cost. A later automated supplier integration replaces that response transport and does not replace the cost engine. The 20–30-item synthetic list is withdrawn. On 6 Oct 2026 the Mac office had no real project with a complete canonical material-requirement list. BMR remains the first proving supplier. The architecture stays multi-supplier. **REAL PROJECT → MATERIAL REQUIREMENT SET: MATERIAL REQUIREMENT CAPABILITY GAP.** Linda Bushel is the most mature real project. Its Construction Model read does not store a canonical material, member size, or supplied board length. The J1 take-off was not copied into `MaterialRequirement`. No supplier pricing request was generated. [ADR-056](adr/ADR-056-approved-contractor-cost-estimate-costing-snapshot.md) lets an existing estimate line freeze an APPROVED contractor cost into the existing costing snapshot. ADR-008 stays Proposed. Migration `q7d8e9f0a1b2` is not applied to the Mac primary or the hosted database. **GENERIC ESTIMATING is not complete.** `SITE`, `FOUND`, and `STRUCT` stay unbound and stay `ENGINE_REQUIREMENT_NOT_DERIVABLE`. ICF wall with subcontract stays `ENGINE_NOT_APPLICABLE`. The walk does not calculate. Migration `n4a5b6c7d8e9` is not applied to the Mac primary or the hosted database. |
| 9 | Real-world learning | Product | ⬜ QUEUED. The law below is recorded. The product is not built. |
| 10 | Field app / PWA | Product | ⬜ QUEUED. Same project state. Not Field Web v1. |

Physical placement of a shared engine package is not a step in this sequence. Contract V1 already says the Website and the Platform do not call each other at runtime. A later authorization would have to choose a package. This checklist does not.

## Website checkpoint

PUBLIC WEBSITE SOURCE CONTINUITY: RESTORED / VERIFIED.

Current public checkpoint: project `appgprj_6a9095543b74819186183f9a522890e5`, SHA `5dcb4f2b9cc0a291a16375f06ce89f09a02262cf`, Version 31, version id `appgprj_6a9095543b74819186183f9a522890e5~appgver_ed1a760941b48191badc6ac0c2d5f347`, deployment `appgdep_6abd379bbb8081918aae3b170706263b`, SUCCEEDED, live `https://calibai.joel-brayman.chatgpt.site/`, source/live parity PASS.

Website existing-problem stabilization is **CLOSED**. Employment, Concrete, and Stair are closed. Full Website tests **56/56 PASS**. Production build PASS. Desktop QA PASS. Mobile responsive QA PASS. Known open Website problems inside that stabilization scope: none.

The Website project remains the source and deploy authority. This repository does not hold that source. Do not copy it here.

Earlier on 30 Sep 2026 a fresh Website chat missed the public project. That was project selection. The Site was not deleted, and the owning chat still had owner, source, edit, and publish authority. The published baseline at that moment was Version 27, SHA `f4b7f2119c603ee20e3b343114c262bfd4c012d4`, deployment `appgdep_6abc1248f5508191b40fe485302168ef`. Private review project `appgprj_6ab7f4ce8450819198398ba2cd4b43f4`, version 6, SHA `59e1979e735ec606af341e97e46e112136fbdfa0`, was not the public deploy target. The same-day audit then found employment inputs that did not participate, two concrete formula files, a stair diagram that did not follow the calculated slope, and a Website test baseline of 41/43. Version 31 closed that set. Those facts are history. They are not the current Website state.

Employment, closed: Quote Win Rate, Seasonality, and Slower-Season Approach removed. Working Weeks remains the annual-work assumption. Winter Protection / Heat remains an operating cost. Solo Business Owner remains. Owner + Labourer / Helper remains. Small Contracting Business was removed. Helper Wage is classified OWNER ESTIMATE. The framing stays neutral decision support. Regression tests cover the inputs that participate.

Concrete, closed: governed authority `lib/calculation-engine/concrete-slab.ts`. Public modes are Standard Slab and Thickened Edge. Contract V1 stays **ACCEPTED / PINNED** and was not changed. The dormant broad implementation is a superseded prototype for historical compatibility only. It is not the public authority.

Stair, closed: calculation PASS, visual PASS, pin PRESENT / PASS. The diagram is drawn from the governed result. The old fixed visual slope is closed. Regression protection covers rise/run, slope, riser and tread counts, stringer alignment, and unit-toggle geometry. Bushel stair scripts remain proving evidence, not a second engine.

Website tests, closed: the development-preview expectation and the catalog animation/scroll expectation were obsolete starter expectations. Full `npm test` is 56/56 PASS. Production build PASS. The final stabilization package changed test and governance expectations and did not change production Website behaviour beyond the closed remediations already recorded.

## Real-world cases

Evidence. Not a gate.

| Case | Status |
|------|--------|
| Linda Bushel pool deck | REAL-WORLD PROVING / ESTIMATING CASE. INCOMPLETE. PRESERVED. NOT A MASTER PRODUCT BLOCKER. Geometry stays unresolved: piers 12 against 15, joist lines 16 against 15, stringers 10 against 9, throat 4.997 in labeled 5.00 in. The architectural lesson is that project-specific proving code must not become a second domain engine. Record: [estimating-cases/2026/linda-bushel-pool-deck/geometry/2026-09-29-governed-geometry-reconciliation.md](estimating-cases/2026/linda-bushel-pool-deck/geometry/2026-09-29-governed-geometry-reconciliation.md). |

## Later

Already governed. Not the current objective.

Hosted password authentication remains unresolved. The temporary hosted UAT bypass remains last recorded ON. Controlled hosted end-to-end, cutover, an authorized V1 rescore, and parked FG-039 publication stay later. People & Access UI is not implemented. CORE CLOSE remains partial. Tactical build status is [architecture/PLATFORM_BUILD_OUT_REGISTER.md](architecture/PLATFORM_BUILD_OUT_REGISTER.md). The internal 8-inch ICF form and concrete service and its estimate workflow are closed on the live office. Framing, roofing, siding, drywall, and flooring remain blocked on a missing formula. Supplier Pro Platform Partnership is ⬜ QUEUED and **NOT STARTED**. Record: [architecture/supplier-pro-platform-partnership-v1.md](architecture/supplier-pro-platform-partnership-v1.md). This checklist does not authorize that implementation.

## Real-world learning law

Real project evidence is compared and accumulated. CalibraytAI proposes a calibration. A person reviews it. A person approves it. Only then may a governed default change.

One project does not silently change a formula, a cost, labour productivity, a labour rate, a margin, or a company default.

## What this checklist does not authorize

It does not authorize drawing changes, a take-off change, a price, a send, building Guided Project Setup, the Plan Generation Engine, a second calculator, a shared-package decision, ICF, a Website change or rebuild, a migration, a deploy, or a V1 rescore.
