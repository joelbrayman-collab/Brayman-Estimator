# Feature Gate FG-008: Labour Engine Phase B / Organization Labour Calibration Foundation

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-008` |
| Feature Name | Labour Engine Phase B — Organization Labour Calibration Foundation |
| Target Milestone | Labour Engine Phase B |
| Module | Labour Engine (Estimating consumes direct labour cost later) |
| Date | 2026-08-29 |
| Status | **CLOSED / OPERATIONAL FOR UAT** (2026-08-29; Joel and ChatGPT; live-migrated; integrity-stabilized) |
| Architecture | [labour-engine-phase-b-architecture.md](../architecture/labour-engine-phase-b-architecture.md) **Approved** |
| Related ADRs | [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** · [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted** · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted** |
| Prerequisites | FG-007 / M011 **implemented**; FG-006 **implemented** |
| Approved baseline | `main` @ `820f54afc179279d2435ad3a426b3037548bb45e` |
| Product code | **Implemented & verified.** Migration `f2c3d4e5f6a7` (in Alembic chain; live graph head is later `b4c5d6e7f8a9`). Tests: `tests/test_labour_engine.py` (**25 passed**). Live development/UAT database upgraded 2026-08-29. Post-UAT integrity stabilization 2026-08-29 (REVOKED mappings; archived tasks excluded from rule suggestion; unknown orgs cannot persist labour audit). |

---

## Status

| Layer | State |
|-------|--------|
| Architecture / readiness | **APPROVED** (2026-08-29; Joel and ChatGPT) |
| Feature Gate (this document) | **IMPLEMENTED / VERIFIED** |
| ADR-029 | **Accepted** |
| Implementation | **Implemented & verified.** FG-008 revision `f2c3d4e5f6a7` is in the live Alembic chain. Live current/head: `b4c5d6e7f8a9`. Foundation **CLOSED / OPERATIONAL FOR UAT**. |

Code paths: `app/models/labour_engine.py`, `app/services/labour_engine.py`, `app/routes/labour_engine.py`, `app/templates/labour_engine/`, `migrations/versions/f2c3d4e5f6a7_add_labour_engine_fg008.py`, `tests/test_labour_engine.py`. Office UI: `/labour-engine/`.

This gate does **not** implement pricing-engine selling-price application, payroll, actuals persistence, or a Crew Template catalog. ADR-025 is **Accepted**. Subsequent status: [FG-009](FG-009-organization-calibrated-pricing-engine.md) and [FG-010](FG-010-ai-takeoff-quantity-extraction-foundation.md) are **CLOSED / OPERATIONAL FOR UAT** and are not part of this gate's original scope.

---

## Purpose and business rationale

CalibAi must own labour **methodology** (how hours and direct labour cost are computed and calibrated) while each organization owns its **commercial labour intelligence** (tasks, production rates, wage rates, evidence, approved standards).

Without this foundation, historical labour evidence (120 ORG-001 rows) cannot be used safely: free-text tasks would be silently merged, Brayman’s $65/hr would become a universal default, and actuals or old bids could overwrite operating standards.

This gate defines that foundation. FG-008 is **implemented, verified, committed, pushed, and live-migrated** on the development/UAT database. It does **not** change pricing policy or mutate historical source workbooks. This does **not** mean the production-rate catalog is populated, historical mappings are approved, actuals are implemented, or selling-price integration is enabled.

---

## Scope (implementation — only after a separate execution prompt)

In-scope capabilities to be built only after a later implementation prompt:

- Organization-owned canonical Labour Tasks
- Human-reviewed mappings from historical (and later actual) source strings
- Versioned Production Rate Standards
- Versioned Direct Labour Cost Rate Standards (blended internal rate; ORG-001 $65 policy unchanged)
- Calibration Candidate entity and review workflow
- Explainable labour-standard resolution
- Immutable labour-assumption snapshot on `EstimateVersion` when the engine is used
- Tenant isolation, provenance, audit
- Explicit project-condition handling (select matching standard **or** documented adjustment — no silent multipliers)

---

## Non-goals

Keep outside FG-008 unless a later gate proves an unavoidable dependency:

- AI quantity take-off / M012+
- Mobile / field time capture
- Payroll integration and burden/wage classification modeling
- QuickBooks API
- Pricing-engine implementation and ADR-025 calculation change
- Cross-org benchmarking / pooled learning / ML training / autonomous learning
- Supplier, material, or subcontract calibration
- Ontario contract/warranty generation
- Full BUILD, MONITOR, or LEARN modules
- Crew Template catalog (deferred; assumptions only)
- Product or repository rename
- Repair/rewrite of FG-006 `HistoricalLabourItem` facts (including stored `hourly_rate = 0.13` and material-as-labour labels)

---

## Architecture summary

See [labour-engine-phase-b-architecture.md](../architecture/labour-engine-phase-b-architecture.md). Binding identities:

```text
QUANTITY × PRODUCTION RATE = MAN-HOURS
MAN-HOURS × DIRECT LABOUR COST RATE = DIRECT LABOUR COST
CREW SIZE × HOURS PER DAY × DURATION = MAN-HOURS   (planning expression; not a second truth)
```

Selling price remains `Direct Cost / 0.85` as **ORG-001 policy text**. Code application of that formula is [FG-009](FG-009-organization-calibrated-pricing-engine.md) (**APPROVED FOR IMPLEMENTATION**, not implemented). Pricing Posture must not manipulate true hours, production rates, direct labour cost, material quantities, or supplier amounts.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | The platform has historical labour **evidence** but no organization-owned canonical tasks, versioned production standards, calibration approval path, or estimate labour snapshots. Without them, calibration would either be impossible or would silently corrupt standards and estimates. |
| 2 | Who is the user? | Office estimators and (later) a chief estimator / approver reviewing mappings and calibration candidates. Not field workers in this gate. |
| 3 | Which module owns it? | **Labour Engine** (new module). Estimating consumes direct labour cost later. Historical ingestion keeps ownership of `HistoricalLabourItem`. |
| 4 | What data does it own? | `LabourTask`, `LabourTaskMapping`, `ProductionRateStandard`, `DirectLabourCostRateStandard`, `LabourCalibrationCandidate`, `EstimateLabourSnapshot`, `LabourAuditEvent` |
| 5 | What data does it reference? | `Organization`, `HistoricalLabourItem` / observations / review decisions, `Project`, `ProjectCommercialContext`, `EstimateVersion`. Future: actuals from BUILD/MONITOR. |
| 6 | What may implementation change? | Additive models/migration, labour review UI, resolution service, tests, docs. May **add** snapshot rows on estimate versions that opt in. Must not change selling-price calculation. |
| 7 | What must implementation not change? | Historical source workbooks; `HistoricalLabourItem` source facts; Plan Intelligence geometry; Accepted proposal snapshots; M011 commercial context math; estimate markup/overhead/profit solver (ADR-025); $65 / 15% policy text; pricing posture behaviour; cross-org data. |
| 8 | What are the acceptance criteria? | See **Acceptance criteria** below. Implementation pass: tests in `tests/test_labour_engine.py` plus full-suite and historical-ingestion non-regression. |
| 9 | What tests are required? | See **Test plan**. Dedicated suite implemented (`tests/test_labour_engine.py`, 22 passed). |
| 10 | What documentation must be updated? | This gate; labour architecture; module stub; current-state; session-handoff; project-state-report; milestones; roadmap; chat-workflow-log. ADR-025 status unchanged. |
| 11 | Does it require an ADR? | **Yes** — [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted**. |
| 12 | Does it require a database migration? | **Yes.** Additive revision `f2c3d4e5f6a7`. |

---

## Canonical entities

Implemented in `app/models/labour_engine.py`.

| Entity | Ownership | Role |
|--------|-----------|------|
| `LabourTask` | Direct `organization_id` | Canonical task identity |
| `LabourTaskMapping` | Direct `organization_id` | Source string → task; human review |
| `ProductionRateStandard` | Direct `organization_id` | Versioned hours per unit |
| `DirectLabourCostRateStandard` | Direct `organization_id` | Versioned $/man-hour |
| `LabourCalibrationCandidate` | Direct `organization_id` | Proposed standard; state machine |
| `EstimateLabourSnapshot` | Direct org + estimate version | Frozen assumptions |
| `LabourActualObservation` | Direct org | Architecture only; persist later |

---

## Production-rate mathematics and labour-cost separation

Production rate is man-hours per production unit. Direct labour cost rate is currency per man-hour. They must not be stored as one number. Crew/duration must not replace quantity × production rate.

ORG-001 direct labour cost rate remains **$65 CAD / man-hour**. Other organizations must not inherit it silently.

---

## Historical evidence

FG-006 rows remain ORG-HISTORICAL. 73 distinct task strings must not auto-merge. Quality issues (stored rate `0.13` vs extended cost implying $65; lumber SKUs classified as labour) are mapping/review inputs, not silent data repairs.

Parent estimates are still `EXTRACTED`, not `ACCEPTED_AS_EVIDENCE`. Calibration must not treat unreviewed extraction as approved input.

---

## Actual-performance evidence

Architected as ORG-ACTUAL. Must not silently replace ORG-APPROVED. Field capture is out of scope. This gate recommends **deferring actuals persistence** to BUILD/MONITOR.

---

## Rate resolution

1. Approved project-specific override (reason required)  
2. Active matching ORG-APPROVED standard  
3. Other reviewed org evidence if expressly authorized for this estimate  
4. CalibAi BASELINE (flagged)  
5. PROVISIONAL / manual requiring review  

Explainable audit on every resolution. Fail-closed across tenants.

---

## Candidate lifecycle and human approval

`DRAFT` → `PROPOSED` → `IN_REVIEW` → `APPROVED` (new standard version) | `REJECTED` | `WITHDRAWN` | `SUPERSEDED`.

Human approval is mandatory before ORG-APPROVED. AI cannot set ORG-APPROVED.

---

## Project conditions

Select a condition-specific ORG-APPROVED standard, or apply an explicit documented adjustment with reason. No silent factors. Commercial context fields do not auto-multiply hours.

---

## Crew decision

**Defer** Crew Template model. Store numeric crew/hours-per-day assumptions on the production standard and snapshot.

---

## Estimate immutability

Labour snapshots pin standard versions. Locked estimate versions, accepted proposals, M011 commercial context pins, and FG-006 historical rows must not be retroactively repriced or rewritten.

---

## Auditability

Suggestions, mappings, candidate transitions, standard approvals, resolution choices, and overrides leave a recoverable trail (Constitution Articles 5–6; Rule 6).

---

## AI authority

**May:** classify, suggest mappings, find similar org-scoped observations, compute variance, flag outliers, summarize evidence, propose candidates, rank confidence.

**Must not:** set ORG-APPROVED, silently merge evidence, alter approved rates, change wage rates, manipulate posture/margin, change historic estimates, pool tenants, silently modify productivity.

---

## Privacy / security / organization isolation

Every labour intelligence query scoped by `organization_id`. Cross-org PK access fail-closed. No cross-org AI context. Historical workbooks remain outside Git.

Unauthenticated office app is a **known existing risk** (same class as M009). FG-008 must not pretend multi-user RBAC exists. Auth remains a separate gate.

---

## Migration

Additive revision `f2c3d4e5f6a7` (revises `e1b2c3d4e5f6`). Rollback drops additive objects. No rewrite of historical labour or commercial context. Legacy estimates without snapshots remain lump-cost lines.

---

## Implementation boundaries

FG-008 stops at **direct labour cost**. It does not change selling-price calculation, markup stack, overhead, profit, or Pricing Posture. No Crew Template catalog. No `LabourActualObservation` persistence.

---

## Rollback approach (future implementation)

Alembic downgrade of the additive revision; application ignores unused snapshot FKs if added as nullable. Historical ingestion and estimating continue as today.

---

## Legacy compatibility

`CostItem` category Labour and existing estimate lines remain valid. Labour Engine is opt-in per new/repriced version until a later gate mandates it. Do not convert historical lump labour into production-rate lines without human mapping and quantity evidence.

---

## Acceptance criteria

### This governance approval pass

1. Architecture document exists and distinguishes Current vs Intended vs Future.  
2. This Feature Gate is **APPROVED FOR IMPLEMENTATION**, **not** marked Implemented.  
3. ADR-029 is **Accepted**.  
4. Stale SHA / ADR-028 index / M009 “not started” documentation discrepancies identified at resume are corrected where evidence supports.  
5. No product code, migration, schema, route, service, or UI changes.  
6. Full pytest and historical ingestion suite still pass.

### Implementation pass (this coded slice)

1. Org isolation tests fail-closed.
2. Mappings cannot auto-accept.
3. Production-rate math matches the identities above.
4. Candidate approval creates a new standard version; prior versions and historical rows unchanged.
5. Estimate labour snapshots immutable; later standard supersession does not alter snapshots.
6. Pricing math and historical ingestion suites non-regress.
7. $65 policy document unchanged; ORG-001 $65 does not leak to other organizations.

---

## Protected areas

- `~/Desktop/CalibAi Historical Estimates` (read-only, outside Git)
- `HistoricalLabourItem` source facts and workbook SHA-256 integrity
- Accepted proposal snapshots
- PlanDocument bytes / PlanPage raw extractions
- M011 commercial context versions
- `docs/pricing-policy.md` rates/formulas (no silent edit)
- Estimate builder markup/overhead/profit until ADR-025 + a pricing Feature Gate
- Other organizations’ future data (none yet besides ORG-001)

---

## Test plan

Covered by `tests/test_labour_engine.py` (22 passed) plus full-suite and historical-ingestion non-regression.

1. Organization isolation of all labour entities  
2. Labour Task ownership and org-scoped unique codes  
3. Production-rate calculations (`qty × rate = hours`)  
4. Unit / production-unit correctness  
5. Historical mapping (accept / reject / not-labour); no auto-merge  
6. Provenance on mappings, standards, snapshots  
7. Rate-resolution order and recorded reason  
8. Candidate lifecycle illegal transitions  
9. Approval control (AI cannot set ORG-APPROVED)  
10. Estimate immutability after standard supersession  
11. Estimated-vs-actual variance formulas when actuals exist  
12. Override audit (reason required)  
13. Legacy estimates without snapshots still load  
14. Pricing-math non-regression (existing estimate builder tests)  
15. Historical-ingestion non-regression (`tests/test_historical_ingestion.py`)  
16. Full suite `./venv/bin/python -m pytest -q`

---

## Blocking / next step

| Item | State |
|------|--------|
| FG-008 implementation | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED.** Foundation operational for UAT. |
| Organization-Calibrated Pricing Engine | [FG-009](FG-009-organization-calibrated-pricing-engine.md) **APPROVED FOR IMPLEMENTATION** — **NOT STARTED** |
| Labour Engine live use in selling-price outputs | **BLOCKED** until FG-009 implementation |

**Next authorized action:** Do **not** implement FG-009 from this document. Issue a separate bounded FG-009 implementation prompt. AI take-off, BUILD/MONITOR/LEARN, historical evidence repair, additional labour features, and cross-org learning remain separately gated.
