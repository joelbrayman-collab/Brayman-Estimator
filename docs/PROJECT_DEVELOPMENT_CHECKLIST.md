# Project development checklist

| Attribute | Value |
|-----------|--------|
| Status | Project governance. Not an implementation authorization. |
| Date | 2026-09-30 |
| Repository | `/Users/joelbrayman/Desktop/Brayman-Estimator` |
| Resume | [session-handoff.md](session-handoff.md) |

This checklist is the one CalibraytAI development sequence. Chat memory is not. The public Website and the private Platform are separate source and deployment surfaces. They are not separate products and they do not have separate roadmaps.

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

On the private Platform, Start New Project is the guided walk of that spine. The contractor states the construction task. CalibraytAI chooses the internal capability. The contractor does not leave the walk to find a calculator. [architecture/start-project-guided-wizard-product-direction.md](architecture/start-project-guided-wizard-product-direction.md). [architecture/estimating-path-alignment-2026-09-27.md](architecture/estimating-path-alignment-2026-09-27.md).

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

Development freeze: **ACTIVE**. Platform existing-problem stabilization is in progress. No new feature work is current.

| Order | Step | Kind | Status |
|-------|------|------|--------|
| 1 | This unified architecture | Governance | Recorded by this checklist. Not an implementation authorization. |
| 2 | Website Useful Tools stabilization | Website surface | ✅ CLOSED at Version 31. |
| 3 | Platform existing-problem stabilization | In progress | 🟡 IN PROGRESS. PLAT-CLIENT-01 CLOSED: an existing Client can be created, opened, and corrected. Freeze remains ACTIVE. Do not start the next item from this row. |
| 4 | Start New Project implementation plan | Product | ⬜ QUEUED behind the freeze. Map stages, define the thin cursor, and name where a governed engine enters. Do not build it. |
| 5 | Approved Start New Project slices | Product | ⬜ QUEUED behind an accepted plan. |
| 6 | Use the governed engine where the project walk requires it | Product | ⬜ QUEUED. No second formula. |
| 7 | Plan Generation | Product | ⬜ QUEUED. Only when drawings are required and absent. Governed engine → governed geometry → drawing → quantity evidence. [architecture/construction-drawing-standard.md](architecture/construction-drawing-standard.md). |
| 8 | Estimating consumes the governed result | Product | ⬜ QUEUED. The mapper exists. A confirmed Our-crew package does not yet call an engine. |
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

Hosted password authentication remains unresolved. The temporary hosted UAT bypass remains last recorded ON. Controlled hosted end-to-end, cutover, an authorized V1 rescore, and parked FG-039 publication stay later. ICF is not authorized. People & Access UI is not implemented. CORE CLOSE remains partial.

## Real-world learning law

Real project evidence is compared and accumulated. CalibraytAI proposes a calibration. A person reviews it. A person approves it. Only then may a governed default change.

One project does not silently change a formula, a cost, labour productivity, a labour rate, a margin, or a company default.

## What this checklist does not authorize

It does not authorize drawing changes, a take-off change, a price, a send, building the wizard, the Plan Generation Engine, a second calculator, a shared-package decision, ICF, a Website change or rebuild, a migration, a deploy, or a V1 rescore.
