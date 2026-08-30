# Feature Gate FG-011: Project Hub UX

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-011` |
| Feature Name | Project Hub UX |
| Target Milestone | **None.** FG-011 is the governing identifier. Do not assign a new M0xx number. |
| Module | **Projects** |
| Date | 2026-08-30 |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Architecture | Evolve existing `/projects/<id>` project detail. [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** (`Project` remains the lifecycle hub). No new ADR for this scope. |
| Related ADRs | [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted** · [ADR-031](../adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md) **Accepted** · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** |
| Prerequisites | M005–M012 / FG-006–FG-010 as recorded. FG-008 / FG-009 / FG-010 **CLOSED / OPERATIONAL FOR UAT**. |
| Approved baseline | `main` @ `49c490852fa5b129da7bd32fc7e446539140f30b`. Alembic current/head `b4c5d6e7f8a9`. Full suite **251 passed**. |

---

## Status

| Layer | State |
|-------|--------|
| Architecture (read-only assessment 2026-08-30) | **Accepted by Joel** as the basis for this gate |
| Feature Gate (this document) | **CLOSED / OPERATIONAL FOR UAT** |
| Implementation | **IMPLEMENTED / VERIFIED** — `app/routes/projects.py`, `app/templates/projects/detail.html`, read-only `app/services/project_hub.py`, `tests/test_project_hub.py` |
| Schema / Alembic | **NO** change |
| New ADR | **None** |
| New module / Job entity | **None** |

This gate authorized a **Projects UX / navigation layer** only. It does **not** authorize Phase D, external AI, authentication, BUILD field capture, MONITOR, LEARN, QuickBooks, contracts, or four-output product. Those remain unauthorized.

---

## Purpose and business rationale

Office estimators need **one project screen** that shows where a job sits in PLAN → PRICE → CONTRACT (and later BUILD / MONITOR / LEARN) and that **links into owning modules**, instead of hunting disconnected sidebar lists.

`/projects/<id>` already functions as a de facto hub (identity, commercial context, plan filenames, related estimates, related proposals via estimates, related change orders). FG-011 evolves that surface. It must not become a second source of truth.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Fragmented project lifecycle navigation. Estimators cannot see PLAN / PRICE / CONTRACT status for one `Project` without leaving the project detail and assembling the picture themselves. |
| 2 | Who is the user? | Office estimators / chief estimator on the current unauthenticated office app. Not field. |
| 3 | Which module owns it? | **Projects.** Not a new module. |
| 4 | What data does it own? | **No new records.** Continues to own `projects`, `project_commercial_contexts`, and Change Orders as today. |
| 5 | What data does it reference? | `Client` (CRM); `Estimate` / versions / lines (Estimating); `EstimatePricingSnapshot` (Pricing Engine, read presence/method); `EstimateLabourSnapshot` (Labour Engine, read presence); `Proposal` (Proposals, via estimates); Plan documents / sheets / measurements / take-off runs and packages (Plan Intelligence). |
| 6 | What may implementation change? | `app/routes/projects.py`, `app/templates/projects/detail.html` (optional hub partials), dedicated tests, governed docs. Org-scoped **reads** and **links** only toward other modules. |
| 7 | What must implementation not change? | Other modules’ write paths; schemas; migrations; FG-008 / FG-009 / FG-010 behaviour; Accepted proposals; approved take-off packages; snapshots; historical evidence; PlanDocument bytes; Dashboard counts; auth; Phase D; external AI. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. |
| 9 | Tests required? | Dedicated Project Hub tests; org-isolation tests; immutability non-regression (proposals, take-off, labour, pricing, historical); full suite. |
| 10 | Documentation? | This gate; `modules/projects.md`; feature-gate index; current-state; project-state-report; roadmap; session-handoff; chat-workflow-log; architecture.md UX boundary only. |
| 11 | ADR required? | **No** for this UX scope. ADR-019 already establishes `Project` as the lifecycle hub. Stop and return if implementation would need a new module, durable hub entity, schema-level hub state, project-health methodology, ownership transfer, or new invariant. |
| 12 | Migration? | **No.** If a schema change appears required, **STOP**. Do not create a migration. Return for governance review. |

---

## Architecture (binding)

1. Evolve existing **`/projects/<id>`**. Do not create a Project Hub module, parallel Hub entity, CalibAi Job entity, duplicate project CRUD, or separate source of truth.
2. `Project` remains the CalibAi lifecycle hub ([ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md)).
3. Hub **reads and links**. It does not take ownership of other modules’ records.
4. Organize the page around PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN.
5. Only existing operational capabilities may appear as operational.
6. Future domains may appear as **disabled / clearly labeled FUTURE**. They must not imply implementation, contain fabricated metrics or fake workflows, create records, or expose placeholder controls that look functional.

### Ownership (authoritative)

| Record | Owner | Hub |
|--------|--------|-----|
| `Project` / `ProjectCommercialContext` | Projects | Own existing CRUD / versioned context |
| `Client` | CRM | Read / link |
| Estimates / versions / lines | Estimating | Read / link |
| Pricing snapshots | Pricing Engine | Read presence / stored method only |
| Labour snapshots | Labour Engine | Read presence only |
| Proposals | Proposals | Read / link |
| Change Orders | Project Controls / Projects | Read / existing create link |
| Plans / sheets / measurements / take-off | Plan Intelligence | Read / link |
| Historical evidence | Historical Ingestion | **Out of hub** |

### Lifecycle presentation

| Domain | Operational content | Future / prohibited |
|--------|---------------------|---------------------|
| PLAN | Stored facts and links: plan documents, sheets, scale/measurement, take-off, stored run/package status | Phase D mapping; real external AI as a product |
| PRICE | Estimates / versions; stored pricing-snapshot presence; stored pricing method where useful; stored labour-snapshot presence; links to authoritative screens | Recompute selling price; new margin/health/profit KPIs; silent policy apply; silent labour-snapshot cost inclusion |
| CONTRACT | Proposals; stored status including Accepted | Proposal acceptance workflow (ADR-004) |
| BUILD | Existing Change Orders | Field BUILD capture (label Future) |
| MONITOR | Label Future | No fake actuals/forecasts |
| LEARN | Label Future | No ML / recommendations |
| Other | — | QuickBooks, four-output package, Ontario contract/warranty, real external AI must **not** appear operational |

### Pricing / labour presentation (conservative)

**Permitted:** snapshot present / absent; stored pricing method where useful; labour snapshot present / absent; links to estimate / pricing / labour screens.

**Not permitted:** recomputing selling price; new margin calculations; project-health calculations; invented profitability indicators; new labour calculations; silent application of pricing policy; silent inclusion of labour snapshot cost.

### Tenant / immutability

- All hub reads **organization-scoped**. Cross-org fail-closed.
- Do **not** copy Dashboard unscoped `Model.query.count()` (Dashboard debt is **out of scope**).
- ORG-001 commercial intelligence remains organization-specific.
- Hub must **not mutate:** Accepted proposals; locked estimate versions; `EstimatePricingSnapshot`; `EstimateLabourSnapshot`; approved `TakeoffPackage`; PlanDocument bytes; historical labour/source evidence; append-only audit history.
- Do not invent a Project Hub audit system.

### Explicit non-goals

Phase D; real external AI; authentication / User model; BUILD field capture; MONITOR; LEARN; QuickBooks; Ontario contract/warranty; four-output package; Rule 4 project-from-accepted-proposal; historical evidence repair; Dashboard count repair; new Alembic revision.

---

## Scope

### In (implementation, after a separate approved Cursor prompt)

- Evolve `projects.view_project` + `detail.html` into an explicit Project Hub
- Add missing **links and stored-status summaries** (take-off, sheets/scale, snapshot presence)
- Label unimplemented lifecycle domains Future
- Org-scoped reads only
- Dedicated tests and docs closure

### Out

- New module, entity, or schema
- Writes to other modules’ records
- Take-off → estimate insertion
- Recomputed commercial numbers
- Fake KPIs / AI summaries
- Auth, BUILD field, MONITOR, LEARN, QB, contracts, four-output, external AI

---

## Acceptance criteria

1. `/projects/<id>` becomes the single Project Hub UX; no parallel Job/Hub entity.
2. Hub surfaces only stored facts from authoritative owning modules.
3. No invented KPIs, scores, summaries, or workflow states.
4. Links exist to appropriate existing plan, take-off, estimate, proposal, change-order, and commercial-context surfaces.
5. Organization isolation is preserved and tested.
6. Hub performs no unauthorized writes to records owned by other modules.
7. Accepted Proposal immutability remains intact.
8. Approved TakeoffPackage immutability remains intact.
9. Estimate pricing/labour snapshots remain immutable/read-only.
10. Historical evidence remains untouched.
11. Take-off status does not imply Phase D estimate insertion.
12. BUILD field / MONITOR / LEARN / QuickBooks / contracts / four-output / external AI are not represented as operational.
13. No schema change.
14. No Alembic migration.
15. Dedicated Project Hub tests pass.
16. Relevant existing module regression tests pass.
17. Full suite passes.
18. Required documentation is reconciled before closure.

---

## Test expectations (implementation prompt)

- Dedicated hub render and link tests
- Org-scoped access / fail-closed across orgs
- No mutation of Accepted proposals, approved packages, snapshots, historical labour
- Existing change-order, plan, estimate, proposal, labour, pricing, historical suites still pass
- Full suite (`./venv/bin/python -m pytest -q`) — current baseline **251 passed** until hub tests are added

---

## Implementation boundaries

If implementation discovers a need for schema, a new owning module, a durable hub entity, project-health methodology, ownership transfer, or a new architectural invariant: **STOP**. Do not migrate. Return for ADR / governance review.

**Implementation (2026-08-30):** `/projects/<id>` is the Project Hub. PLAN / PRICE / CONTRACT read stored facts and link to owning modules. BUILD surfaces existing Change Orders; field BUILD / MONITOR / LEARN / QuickBooks / four-output / Ontario contract/warranty / real external AI are labeled Future. Dedicated tests **13 passed**. Full suite **264 passed**. No schema, migration, ADR, Phase D, or external AI.

---

## Closure

Acceptance criteria 1–18 are satisfied. FG-011 is **CLOSED / OPERATIONAL FOR UAT**.

**Next governed action:** STOP. Do not start Phase D or another Feature Gate from this closure. Roadmap item 9 (estimate-output consistency) remains separately gated.
