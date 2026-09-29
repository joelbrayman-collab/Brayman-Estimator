# Project development checklist

| Attribute | Value |
|-----------|--------|
| Status | Project governance. Not an implementation authorization. |
| Date | 2026-09-29. Confirmed unchanged on 30 Sep 2026. |
| Repository | `/Users/joelbrayman/Desktop/Brayman-Estimator` |
| Resume | [session-handoff.md](session-handoff.md) |

This checklist is the development sequence. Chat memory is not. The 30 Sep 2026 governance pass confirmed this sequence and did not advance the active slice.

## Status law

| Mark | Meaning |
|------|---------|
| ✅ COMPLETE | Implementation and evidence are complete, and Human UAT has occurred where it is required. |
| 🟡 IN PROGRESS | The single current development slice. |
| ⬜ QUEUED | Sequenced. Not started. |
| ⛔ BLOCKED | A real dependency is unresolved. |

## Sequence

| Order | Phase | Status |
|-------|--------|--------|
| 1 | Bushel proving case | 🟡 IN PROGRESS. Not final. Not sent. |
| 1a | Linda Bushel — governed geometry reconciliation | 🟡 IN PROGRESS. This is the active slice. |
| 2 | Plan Generation Engine | ⬜ QUEUED. Recorded. Not built. |
| 3 | Start New Project wizard | ⬜ QUEUED. Recorded. Not implemented. |
| 4 | Estimating intelligence | ⬜ QUEUED. |
| 5 | Real-world learning | ⬜ QUEUED. The law below is recorded. The product is not built. |
| 6 | Field app / PWA | ⬜ QUEUED in this sequence. Field Web v1 is a separate, already closed programme. It is not this phase. |

## Bushel

Proving case. Not final. Not sent.

Present: design brief, framing comparison, issue P1, CT-1, CT-2, CT-2 R2, take-off, unsent Darcy request, difference notes, unpriced Ben cost sheet.

Open conflicts, so the package is not complete. A 29 Sep 2026 trace measured both layouts and did not select either one. Record: [estimating-cases/2026/linda-bushel-pool-deck/geometry/2026-09-29-governed-geometry-reconciliation.md](estimating-cases/2026/linda-bushel-pool-deck/geometry/2026-09-29-governed-geometry-reconciliation.md).

| Item | P1 | Proving drawing | 29 Sep trace |
|------|----|-----------------|--------------|
| Piers | 12 | CT-1 has 15 | Unresolved. The brief does not set the count, and no cited span table chooses the bays. |
| Joist lines | 16 | CT-1 has 15 | Unresolved. Both keep bays at or under 16 in. 216 in is not a whole number of 16 in spaces. |
| Stringers | 10 | CT-2 R2 has 9 | Unresolved. Both keep bays at or under 16 in. 120 in is not a whole number of 16 in spaces. |
| Stringer throat | — | 5.00 in. Not structurally verified. | Unresolved. Calculated 4.997 in. No throat rule is in the repository. |

Case path: [estimating-cases/2026/linda-bushel-pool-deck/](estimating-cases/2026/linda-bushel-pool-deck/).

## Plan Generation Engine

Bushel showed that project geometry can be calculated and drawn as a vector construction plan. The scripts that do that are project-specific. The later engine is reusable. It is not built.

That engine owns governed construction geometry for construction drawings, foundation and pier plans, framing plans, elevations, sections and details, scope intelligence, calculation-engine inputs, material take-off, estimating, and build information. The construction geometry is the source of truth.

A drawing is not complete because the geometry exists. The output needs geometry, dimensions, member callouts, connection information, safety and guard information where a guard applies, and field-verification items. Text supplements the geometry. Text does not replace it.

Detail: [architecture/construction-drawing-standard.md](architecture/construction-drawing-standard.md). Lessons from the proving sheets: [architecture/bushel-critical-path.md](architecture/bushel-critical-path.md).

## Start New Project wizard

Start New Project becomes a guided, resumable walk. The contractor does not have to know which internal module to open.

Project and client, then location and project type, then documents and source information, then whether adequate plans exist, then plan generation only if it is required and authorized, then what work is required, then Our crew or Subcontractor, then the estimating inputs, then missing information, then project setup review, then build the estimate.

Detail: [architecture/start-project-guided-wizard-product-direction.md](architecture/start-project-guided-wizard-product-direction.md). Not implemented.

## Calculation engines

A calculation engine is reusable construction mathematics. It may later serve the public Website Useful Tools, a private Platform or Field tool, and Platform workflows under the hood. It does not own company pricing, company margin, or the private estimate workflow.

Contract V1 is **ACCEPTED / PINNED** at `2903a45074df21b1c99390cb9aab68638970a2ff`. Record: [architecture/calculation-engine-result-contract-v1.md](architecture/calculation-engine-result-contract-v1.md).

Website Version 27 is external. Live site `https://calibai.joel-brayman.chatgpt.site/`. Website source commit `f4b7f2119c603ee20e3b343114c262bfd4c012d4`. Do not copy that source into this repository.

## Real-world learning

Real project evidence is compared and accumulated. CalibraytAI proposes a calibration. A person reviews it. A person approves it. Only then may a governed default change.

One project does not silently change a formula, a cost, labour productivity, a labour rate, a margin, or a company default.

## What this checklist does not authorize

It does not authorize drawing changes, a take-off change, a price, a send, the Plan Generation Engine, the wizard, ICF, a Website change, a migration, or a deploy.
