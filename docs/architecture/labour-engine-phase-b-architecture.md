# Labour Engine Phase B — Architecture & Readiness

| Attribute | Value |
|-----------|--------|
| Status | **IMPLEMENTED / VERIFIED** — live development/UAT database migrated to `f2c3d4e5f6a7`; foundation **operational for UAT** |
| Date | 2026-08-29 |
| Feature Gate | [FG-008](../feature-gates/FG-008-labour-engine-phase-b.md) **IMPLEMENTED / VERIFIED** |
| ADR | [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** |
| Baseline | Implementation from `main` @ `820f54afc179279d2435ad3a426b3037548bb45e`; Alembic revision `f2c3d4e5f6a7` (revises `e1b2c3d4e5f6`) |
| Product | The Estimator / CalibAi |
| Implementation | **Implemented & verified.** FG-008 revision `f2c3d4e5f6a7` applied 2026-08-29. Live development/UAT later moved to FG-009 `a3b4c5d6e7f8` (2026-08-29). Labour Engine foundation remains operational for UAT. |

---

## 1. Purpose and current vs intended

This document defines how CalibAi will manage organization-owned labour methodology:

- canonical labour tasks
- production rates
- quantities and man-hours
- direct labour cost rates
- crew assumptions (not a full crew catalog in Phase B)
- duration (planning expression only)
- historical labour evidence
- actual-performance evidence (architecture; field capture out of scope)
- organization-approved labour standards
- calibration candidates
- estimated-vs-actual labour analysis
- project-condition productivity treatment
- provenance, human approval, tenant isolation, and estimate immutability

**Current (implemented):** Historical labour is persisted as **ORG-HISTORICAL evidence** only (`HistoricalLabourItem` via FG-006). Active estimating still uses `CostItem` rows (including category `Labour`) as lump `unit_cost` lines. **FG-008 Labour Engine Phase B** adds organization-owned canonical tasks, human-reviewed mappings, versioned production and direct labour cost rate standards, calibration candidates, explainable resolution, and immutable `EstimateLabourSnapshot` rows. Legacy estimates without snapshots continue to load unchanged. Selling-price math is unchanged (ADR-025 **Accepted**; FG-009 **not implemented**).

**Intended (FG-008 coded slice, implemented & verified):** An organization-scoped Labour Engine that computes:

```text
QUANTITY × PRODUCTION RATE = MAN-HOURS
MAN-HOURS × DIRECT LABOUR COST RATE = DIRECT LABOUR COST
```

Crew planning may also express:

```text
CREW SIZE × HOURS PER DAY × DURATION = MAN-HOURS
```

Crew/duration must **not** replace or hide quantity × production rate.

**Future / out of scope for FG-008:** Pricing-engine selling-price application (ADR-025), payroll burden modeling, Crew Template catalog, mobile/field time capture, MONITOR actuals pipeline, AI take-off, cross-org learning, ML training.

---

## 2. Core CalibAi principle

**CalibAi owns the engine and methodology.**  
**Each customer organization owns its commercial intelligence.**

Brayman Construction Inc. is **ORG-001**. Brayman is the UAT / first-customer organization, **not** the universal CalibAi model.

`$65 CAD / man-hour` and `Selling Price = Direct Cost / 0.85` (15% true gross margin) are **ORG-001** commercial values recorded in [pricing-policy.md](../pricing-policy.md). They must not be hard-coded as platform defaults for other organizations.

No private labour rate, production rate, historical estimate, actual performance, calibration model, or other commercial intelligence from Organization A may automatically influence Organization B. Cross-organization pooled learning remains **NOT AUTHORIZED** ([organization-and-calibration-architecture.md](organization-and-calibration-architecture.md) §16).

---

## 3. Existing-before-new (code audit)

Inspected read-only. **No product code was changed for this architecture pass.**

### 3.1 Historical labour (FG-006) — current evidence store

| Piece | Path |
|-------|------|
| Model | `app/models/historical_estimates.py` — `HistoricalLabourItem` |
| DTO | `app/services/historical_ingestion/adapters/base.py` — `ExtractedLabourItem` |
| Persistence | `app/services/historical_ingestion/engine.py` |
| Adapters | `app/services/historical_ingestion/adapters/family_a.py` … `family_e.py` |
| Review UI | `app/templates/historical_estimates/detail.html` |
| Migration | `migrations/versions/e1b2c3d4e5f6_add_historical_estimate_ingestion_fg006.py` |
| Tests | `tests/test_historical_ingestion.py` |

`HistoricalLabourItem` fields (current):

| Field | Role |
|-------|------|
| `organization_id` | Direct tenant ownership (all 120 rows = `ORG-001`) |
| `historical_estimate_id` | Parent ingested estimate |
| `task_description` | Free-text source label (not canonical) |
| `crew_size` | Optional |
| `duration_days` | Optional |
| `hours_per_day` | Default `8.0` (119 of 120 rows); Alberton Garage = `9.0` |
| `total_man_hours` | Optional |
| `hourly_rate` | Optional numeric; **not always a true $/man-hour** (see §4) |
| `extended_labour_cost` | Optional dollar cost |
| `formula_pattern` | Optional |
| `provenance_observation_id` | FK to `HistoricalSourceObservation` (79 of 120 populated; 41 null) |
| `created_at` | Audit timestamp |

**Absent from the current labour row:** quantity, unit of measure, production rate, production unit, canonical task id, notes field, data-quality flag FK, review-decision FK (review lives on the parent `HistoricalEstimate`).

Family adapters classify labour by **keyword heuristics** (`labour`, `form`, `pour`, `finish`, `strip`, `install`, etc.) and often reconstruct hours as `crew × days × 8` when hours are missing. Workbook-level labour rates are read from COST DATA cells where present (historical values include `$60`, `$62.50`, `$65`).

### 3.2 Active estimating — not a labour engine

| Piece | Current behaviour |
|-------|-------------------|
| `CostItem` | Category may be `Labour`; stores a lump `unit_cost`. No production rate. (`app/models/cost_item.py`) |
| `EstimateLineItem` | `quantity`, `unit`, `unit_cost`, `extended_cost`, `markup_percent`, `sell_price`. No man-hours, no production rate, no labour-standard pin. (`app/models/estimate.py`) |
| `EstimateVersion` | Pins `commercial_context_id` (M011). Does **not** pin labour standards. Locked statuses exist (`AUTO_LOCK_VERSION_STATUSES`). |
| `Organization` | Identity + currency/jurisdiction. **No** `default_labour_rate` column in code (that field exists only as Phase A architecture). (`app/models/organization.py`) |

### 3.3 Governing architecture already in force

- Evidence classes and calibration lifecycle: [organization-and-calibration-architecture.md](organization-and-calibration-architecture.md) §§5–8
- Pricing Posture must not alter true hours/quantities/wage: same document §12; [FG-007](../feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md) invariant 1
- LEARN must not silently mutate standards: [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted**
- Selling-price formula vs estimate markup stack: [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted**; [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **APPROVED FOR IMPLEMENTATION**, **not implemented**
- Organization isolation: [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted**; `get_current_organization_id()` fail-closed queries

**Constraint on org architecture §18:** that section’s example of applying a **silent** `+15%` commercial-profile multiplier to production hours is **not authorized for the Labour Engine**. It conflicts with §12 and FG-007. FG-008 / ADR-029 govern labour-hour treatment: no hidden labour multiplier from Pricing Posture or Execution Risk. See §11.

---

## 4. Historical labour evidence findings (ORG-001, live DB)

Read-only query of `instance/brayman_estimator.db` on 2026-08-29. These are **evidence facts**, not approved standards.

| Metric | Value |
|--------|--------|
| `historical_labour_items` | **120** |
| Owning organization | **ORG-001** only |
| Distinct `task_description` | **73** |
| By family | A 37 / B 43 / C 12 / D 17 / E 11 |
| Parent estimate `review_status` | All 20 still `EXTRACTED` (none promoted to `ACCEPTED_AS_EVIDENCE`) |
| Provenance observation present | 79 / 120 |
| `crew_size` null | 28 |
| `duration_days` null | 75 |
| `total_man_hours` null | 14 |
| `hourly_rate` null | 0 |
| `extended_labour_cost` null | 18 |

**Hourly rate distribution (as stored):** `0.13` × 43; `$60` × 24; `$62.50` × 20; `$65` × 33.

The `0.13` cluster is **not** a credible direct labour cost rate. For those rows where hours and extended cost exist, `total_man_hours × 65` matches `extended_labour_cost`, while `total_man_hours × 0.13` does not. Likely cause: adapter captured a **13% tax/markup fraction** from COST DATA as `hourly_rate`. **Do not rewrite these rows in FG-008.** Treat as ORG-HISTORICAL quality defects; mapping/review must use provenance and extended cost, not blindly trust `hourly_rate`.

**Material misclassification:** keyword heuristics ingested lumber/sheet goods as labour (e.g. `2X6X8`, `2X4X10`, `5/8" T&G OSB`, `Beams`, `2X6 Strong Backs`). These remain historical facts of ingestion. Canonical mapping must allow **reject / not-a-labour-task**. Do not silently delete or recategorize source rows.

**Crew formula:** where crew, duration, and hours are all present, `crew × days × hours_per_day` matched stored hours on 38 rows and mismatched on 7. Incomplete crew inputs on 75 rows.

**No stored quantity or production unit.** Therefore:

```text
PRODUCTION RATE = MAN-HOURS / QUANTITY
```

cannot be derived from `HistoricalLabourItem` alone. Calibration from historical estimates requires a **separately evidenced quantity** (related cost line, take-off, or human-supplied quantity with provenance). Hours, crew, duration, and dollars remain valid evidence even when production rate cannot yet be computed.

**How the 120 rows may inform future calibration**

1. They are **ORG-HISTORICAL evidence**, not ORG-APPROVED.
2. Human-reviewed mappings may group synonymous strings (`ICF Labour`, `Install ICF`, `ICF Walls`, `ICF Install Crew`) onto one canonical task — **never automatically**.
3. Where quantity can be evidenced, a Calibration Candidate may propose a production rate.
4. Where quantity cannot be evidenced, the row may still support crew/hours/cost analysis and must not invent a production rate.
5. `hourly_rate` may support a Direct Labour Cost Rate candidate only after quality review (the `0.13` cluster must not become ORG-APPROVED).
6. Parent review status `EXTRACTED` means the corpus is **not** yet accepted as evidence. FG-008 mapping workflow should require or record historical-estimate review state; it must not treat unreviewed extraction as approved calibration input.

---

## 5. Labour economic model (must not collapse)

Keep these concepts distinct:

| Concept | Meaning | Must not be used as |
|---------|---------|---------------------|
| **Quantity** | Physical take-off amount in a production unit | A commercial lever |
| **Production rate** | Man-hours per production unit (org-owned, versioned) | A margin or posture factor |
| **Man-hours** | Quantity × production rate (true labour content) | Something Pricing Posture may shrink |
| **Direct labour cost rate** | Currency per man-hour (org-owned, versioned) | A production rate |
| **Direct labour cost** | Man-hours × direct labour cost rate | Selling price |
| **Crew size / hours per day / duration** | Planning expression of the same man-hours | A hidden multiplier on economics |
| **Project conditions** | Explicit applicability of a standard, or an explicit documented adjustment | Silent factor |
| **Execution risk** | Delivery uncertainty; may later justify **visible contingency**, not hidden hours | A labour-hour fudge |
| **Pricing posture** | Commercial strategy applied **after** direct cost | A labour or quantity editor |
| **Actual performance** | ORG-ACTUAL evidence | An automatic replacement of ORG-APPROVED |
| **Historical estimate evidence** | ORG-HISTORICAL (past bid intent, not actuals) | Automatic operating standard |

**ORG-001 reference (policy, not platform default):**

- Direct labour cost rate: **$65 CAD / man-hour**
- Target selling formula: **Selling Price = Direct Cost / 0.85** (15% true gross margin)

FG-008 **must not change** that policy. FG-008 **must not** implement selling-price migration (ADR-025 **Accepted**; application is FG-009). The Labour Engine stops at **direct labour cost**.

**No hidden multipliers:** Pricing Posture, Execution Risk, and “commercial profile” must not silently scale true hours, production rates, or direct labour cost.

---

## 6. Canonical Labour Task architecture

Historical strings are **not** equivalent until a human accepts a mapping.

Implemented in `app/models/labour_engine.py` (`labour_tasks`, `labour_task_mappings`).

### 6.1 `LabourTask` (organization-owned)

| Field | Intent |
|-------|--------|
| `organization_id` | Direct ownership; unique `task_code` scoped per org |
| `task_code` | Stable org identifier (e.g. `LT-ICF-INSTALL`) — not a global CalibAi SKU forced on every tenant |
| `canonical_name` | Organization’s preferred name |
| `trade` | e.g. Concrete, ICF, Carpentry |
| `category` | e.g. Formwork, Place, Finish, Strip |
| `description` | Scope notes |
| `production_unit` | What the production rate is measured against (sq ft wall, lf footing, each, …) |
| `unit_of_measure` | UOM aligned to production unit |
| `status` | `DRAFT` / `ACTIVE` / `ARCHIVED` |
| `source` | `MANUAL` / `MAPPED_FROM_HISTORICAL` / `BASELINE_CLONE` |
| `provenance` | Why this task exists |
| `created_by` / `created_at` / `updated_at` | Audit |

CalibAi may ship **optional baseline task dictionaries** as BASELINE reference. Cloning into an org catalog does not make them ORG-APPROVED production standards.

### 6.2 `LabourTaskMapping` (suggestion + human review)

| Field | Intent |
|-------|--------|
| `organization_id` | Direct ownership |
| `source_string` | Exact historical `task_description` (or normalized form stored alongside exact) |
| `labour_task_id` | Target canonical task (nullable until accepted) |
| `historical_labour_item_id` | Optional specific evidence row |
| `mapping_confidence` | Suggestion quality (0–1); never write-authority |
| `review_status` | `SUGGESTED` / `ACCEPTED` / `REJECTED` / `NOT_LABOUR` / `REVOKED` |
| `suggested_by` | `AI` / `RULE` / `HUMAN` |
| `reviewed_by` / `reviewed_at` / `review_notes` | Mandatory on accept/reject |
| `audit` | Immutable suggestion history; new row on remapping (do not silently overwrite accepted maps) |

**Invariant:** `ICF Labour`, `Install ICF`, `ICF Walls`, and `ICF Install Crew` remain distinct source strings until a reviewer accepts a mapping.

---

## 7. Production Rate Standard (versioned, organization-owned)

`ProductionRateStandard` is the ORG-APPROVED (or candidate) operating curve for a task.

| Field | Intent |
|-------|--------|
| `organization_id` | Direct ownership |
| `labour_task_id` | Canonical task |
| `version_number` | Monotonic per org+task (or org+task+condition-set) |
| `production_rate` | Man-hours **per** production unit |
| `production_unit` / `unit_of_measure` | Must match task |
| `man_hour_basis` | Explicit: hours per unit (not dollars per unit) |
| `crew_size_assumption` | Planning metadata; optional numeric |
| `hours_per_day_assumption` | Planning metadata; default documented |
| `applicable_conditions` | Explicit condition keys this version applies to (see §11) |
| `evidence_class` | `ORG-APPROVED` / `BASELINE` / `PROVISIONAL` / etc. |
| `confidence` | Informational |
| `effective_from` / `effective_to` | Inclusive period |
| `approval_status` | `DRAFT` / `APPROVED` / `SUPERSEDED` / `WITHDRAWN` |
| `provenance` | Evidence and approval records |
| `superseded_by_id` | Next version |
| `approved_by` / `approved_at` | Human authority |

**Supersession:** new version; never mutate an approved version in place once referenced by an estimate snapshot.

**Historical estimates** keep their original `HistoricalLabourItem` numbers. They do **not** float to the new standard. If a historical row is later mapped, the mapping is additive evidence, not a rewrite of ingested hours.

---

## 8. Direct Labour Cost Rate (separate standard)

`DirectLabourCostRateStandard` is versioned and organization-owned.

| Invariant | Rule |
|-----------|------|
| Direct labour cost rate ≠ production rate | Separate entities |
| ORG-001 initial approved rate | **$65 CAD / man-hour** per [pricing-policy.md](../pricing-policy.md) — policy unchanged |
| Other orgs | Must set their own approved rate; must not inherit Brayman’s $65 as a silent default |
| Burden / wage / classification | **Deferred** (later Feature Gate). Phase B stores a **blended internal direct cost rate** only |
| Selling price / margin | **Out of scope** (ADR-025) |

Payroll burden, employer costs, worker classification, and blended crew cost **beyond** a single direct rate are documented as future needs, not FG-008 implementation.

---

## 9. Evidence hierarchy (labour)

Reuse the existing classes ([organization-and-calibration-architecture.md](organization-and-calibration-architecture.md) §5). Labour-specific meaning:

| Class | Labour meaning | Authority |
|-------|----------------|-----------|
| **ORG-ACTUAL** | Verified job actuals (timecards / job cost). Strongest **calibration evidence**. | Must not silently replace ORG-APPROVED |
| **ORG-APPROVED** | Human-authorized operating production standard and/or direct labour cost rate | Used in resolution when applicable |
| **CURRENT** | Live quoted labour (rare; e.g. T&M subcontract labour quote) | Project-specific quote, not a production standard |
| **ORG-HISTORICAL** | Ingested `HistoricalLabourItem` / past bid intent | Requires review; not actuals |
| **BASELINE** | Optional CalibAi starter dictionary | Flagged generic |
| **PROVISIONAL** | Unverified suggestion | Not operating standard |
| **MANUAL** | Estimator override on a project/estimate | Reason + audit |

AI cannot independently set ORG-APPROVED.

---

## 10. Calibration Candidate lifecycle

Dedicated entity `LabourCalibrationCandidate` with an explicit state machine. A candidate is **not** raw evidence, **not** the current approved standard, **not** a manual estimate override, and **not** a baseline reference.

```text
EVIDENCE
  → ANALYSIS (org-scoped; explainable)
  → CALIBRATION CANDIDATE (DRAFT / PROPOSED)
  → HUMAN REVIEW (IN_REVIEW)
  → ORG-APPROVED version of ProductionRateStandard (and/or DirectLabourCostRateStandard)
     or REJECTED / WITHDRAWN / SUPERSEDED
```

| State | Meaning |
|-------|---------|
| `DRAFT` | Analyst/AI working notes; not visible as a rate |
| `PROPOSED` | Ready for review; still not ORG-APPROVED |
| `IN_REVIEW` | Assigned reviewer |
| `APPROVED` | Promotes a **new** standard version; candidate remains the decision record |
| `REJECTED` | Not adopted; preserved |
| `WITHDRAWN` | Proposer cancelled |
| `SUPERSEDED` | Replaced by a later candidate |

**Promotion rule:** approval writes a new `ProductionRateStandard` version (and optionally a rate-standard version). It never mutates prior versions or historical labour rows.

Phase B may generate candidates from **ORG-HISTORICAL** mappings plus evidenced quantities. ORG-ACTUAL-driven candidates are architecturally valid but **actual capture is out of scope** until BUILD/MONITOR (or a later gate) persists `LabourActualObservation`.

---

## 11. Project conditions (explicit, auditable)

Examples: restricted access, occupied site, remote, winter, congestion, height, complexity, sequencing constraint, compressed schedule.

**Authorized methods (choose in order):**

1. **Select a different ORG-APPROVED standard** whose `applicable_conditions` match (e.g. `ICF-INSTALL` / `WINTER`).
2. If none exists: **estimator-applied explicit productivity adjustment** with a stored reason, magnitude, and evidence class `MANUAL` (or a new candidate), shown on the labour snapshot.
3. **Require estimator review** before using BASELINE/PROVISIONAL under non-standard conditions.

**Forbidden:** silent adjustment factors; Pricing Posture or Execution Risk as hidden hour multipliers; averaging unlike conditions into one noisy curve (ADR-024).

Existing `ProjectCommercialContext.site_condition` and `schedule_condition` (M011) are **context**, not automatic labour multipliers. They may *inform which standard is offered* and *require review*; they must not rewrite hours by themselves.

Execution Risk contingency (org architecture §13) is a **visible direct-cost buffer** if later Feature-Gated. It is not FG-008 labour-hour math.

---

## 12. Crew architecture — Phase B decision

**Defer** a first-class `Crew` / `Crew Template` model.

Rationale: historical evidence already stores `crew_size`, `duration_days`, and `hours_per_day` on `HistoricalLabourItem`. Phase B only needs those numbers as **assumptions on the Production Rate Standard** and on the estimate labour snapshot. A full catalog (worker categories, equipment dependencies, suitability matrix) is possible later and is **not** required to compute quantity × production rate.

Crew planning identity remains:

```text
CREW SIZE × HOURS PER DAY × DURATION = MAN-HOURS
```

as a **check / planning view** of the same man-hours, not a second economic truth.

---

## 13. Estimated vs actual (architecture)

### 13.1 Estimated labour (Phase B, if implemented)

When an estimate uses the Labour Engine, persist an immutable **labour assumption snapshot** per `EstimateVersion` (new rows; do not overwrite). Conceptual contents:

- organization, project, estimate version
- labour task, quantity, unit
- production standard version id + production rate used
- direct labour cost rate version id + rate used
- computed man-hours and direct labour cost
- crew/duration assumptions if recorded
- project conditions considered
- resolution class, source record, reason selected, override reason
- data quality / confidence
- provenance

Locked `EstimateVersion` rows (`Issued` / `Accepted` / `Rejected` / `Superseded`) must not have snapshots mutated.

### 13.2 Actual labour (architecture now; capture later)

`LabourActualObservation` (conceptual):

- organization, project, optional estimate version
- labour task (canonical; mapping if source string)
- quantity installed (if known)
- actual man-hours, crew, duration, period
- project conditions / abnormal conditions
- variance vs estimated hours and %
- data quality, approved exclusions, confidence, provenance
- evidence class `ORG-ACTUAL` only after human verification

**FG-008 implementation recommendation:** do **not** persist actuals in the first coded slice. Field/mobile capture stays out of scope. MONITOR/BUILD Feature Gates own the write path. Analysis formulas belong in this architecture so they are not reinvented later.

Variance:

```text
VARIANCE_HOURS = ACTUAL_MAN_HOURS − ESTIMATED_MAN_HOURS
VARIANCE_PCT = VARIANCE_HOURS / ESTIMATED_MAN_HOURS  (if estimated ≠ 0)
```

Actuals may generate a Calibration Candidate. They must **not** mutate ORG-APPROVED automatically.

---

## 14. Rate-resolution hierarchy (labour)

Deterministic, explainable, org-scoped. Evaluated for **production standard** and separately for **direct labour cost rate**.

1. **Approved project-specific override** (`MANUAL`) with reason.
2. **Active ORG-APPROVED** organization standard matching task and applicable conditions, in force on the estimate date.
3. **Other reviewed organization evidence** only where the estimator **expressly authorizes** use of a specific reviewed candidate or historical observation for this estimate (still not a silent org standard).
4. **CalibAi BASELINE** (flagged generic).
5. **PROVISIONAL / manual entry** requiring review.

Each resolution record must store: organization, source class, source record id, version, effective date, provenance, reason selected, override reason if applicable.

**No black-box resolution.** CURRENT supplier quotes apply to quoted cost items; they are not a substitute production rate unless the line is actually quoted labour.

This labour cascade **refines** org architecture §8 for labour methodology. It does not authorize using Organization B data for Organization A.

---

## 15. Estimate immutability

Reconcile with existing pins:

| Existing pin | Labour Engine addition |
|--------------|------------------------|
| `EstimateVersion.commercial_context_id` (M011) | Unchanged. Conditions on the context do not rewrite hours. |
| Locked estimate versions | Unchanged. |
| Accepted proposal snapshots (ADR-002) | Unchanged. Labour snapshot lives on the estimate version the proposal copied; proposals must not re-resolve live standards. |
| Historical labour rows (FG-006) | Immutable evidence. Mappings are separate records. |

Later changes to production standards, direct labour rates, crew assumptions, conditions, or calibration models spawn **new versions**. They must not retroactively change an old `EstimateVersion` labour snapshot.

Until an estimate actually uses the Labour Engine, existing `EstimateLineItem.unit_cost` labour lump lines remain valid legacy behaviour (no silent conversion).

---

## 16. Organization isolation

| Concept | Ownership |
|---------|-----------|
| `LabourTask`, mappings, production standards, direct labour cost rate standards, calibration candidates, labour snapshots | **Direct** `organization_id` |
| `HistoricalLabourItem` | Already direct (FG-006); Labour Engine **references**, does not take ownership |
| `EstimateVersion` labour snapshot | Direct org + inherited via Project |
| `LabourActualObservation` | Direct org (when implemented) |

All list/detail queries filter by current organization. Direct PK lookup without org match **fail closed** (404). No cross-org join, embedding, or AI context.

---

## 17. AI authority

**AI MAY:** classify labour descriptions; suggest canonical mappings; identify similar org-scoped observations; calculate variance; detect outliers; summarize supporting evidence; propose calibration candidates; rank confidence / evidence quality.

**AI MAY NOT:** set ORG-APPROVED; silently merge labour evidence; alter approved production rates; change direct labour rates; manipulate Pricing Posture or gross margin; change historic estimates; pool tenant intelligence; silently modify productivity.

Human approval is mandatory before promotion to ORG-APPROVED. Same spirit as ADR-017 (suggestion vs authoritative field) and ADR-024 (LEARN boundary).

---

## 18. Module ownership (intended)

| Module | Owns | References |
|--------|------|------------|
| **Labour Engine** (new; [modules/labour-engine.md](../modules/labour-engine.md)) | Canonical tasks, mappings, production standards, direct labour cost rate standards, calibration candidates, estimate labour snapshots | Historical labour (ingestion), Project commercial context, Organization, EstimateVersion |
| **Estimating** | Cost items, assemblies, estimate lines, selling-price math (unchanged) | May consume Labour Engine **direct labour cost** when a future implementation prompt wires it |
| **Historical ingestion** | `HistoricalLabourItem` and source provenance | Unchanged |
| **Projects** | `ProjectCommercialContext` | Conditions as context only |
| **BUILD / MONITOR** | Future actuals write path | Not FG-008 |

Labour Engine must not take ownership of `cost_items`, proposal snapshots, or pricing-policy.md.

---

## 19. Migration

One additive Alembic revision: `f2c3d4e5f6a7` (revises `e1b2c3d4e5f6`).

Rollback: drop additive Labour Engine tables; no rewrite of `historical_labour_items`, `estimate_versions` commercial context, or proposal snapshots.

Legacy: pre-FG-008 estimates have no labour snapshot; they remain lump-cost lines. Do not backfill invented production rates.

Live development/UAT Alembic current/head later became `a3b4c5d6e7f8` (FG-009). FG-008 tables remain in place. This does **not** populate an operating production-rate catalog. FG-009 selling-price integration consumes Direct Labour Cost read-only and does **not** include labour-snapshot cost in the estimate basis by default.

---

## 20. Implementation boundaries (FG-008 coded)

**In scope (implemented & verified):**

- Org-owned Labour Task catalog + mapping review UI (`/labour-engine/`)
- Versioned Production Rate Standard + Direct Labour Cost Rate Standard
- Calibration Candidate workflow
- Explainable resolution service + estimate labour snapshot (opt-in; not auto-wired into selling-price lines)
- Organization isolation and `LabourAuditEvent`
- Tests in `tests/test_labour_engine.py`

**Out of scope (unchanged):**

AI take-off / M012+, mobile field time capture, payroll integration, QuickBooks API, pricing-engine implementation, ADR-025 calculation change, cross-org benchmarking, autonomous learning, ML training, supplier/material/subcontract calibration, Ontario contract/warranty, full BUILD/MONITOR/LEARN, Crew Template catalog, burden modeling, product/repository rename.

---

## 21. Tests

See [FG-008](../feature-gates/FG-008-labour-engine-phase-b.md) and `tests/test_labour_engine.py`. Dedicated suite **25 passed**. Full suite **195 passed**. Historical ingestion **11 passed**.

---

## 22. Unresolved items (Joel / ChatGPT)

1. Initial ORG-001 canonical **task catalog contents** (human-authored seed vs empty catalog + mapping only). Empty catalog shipped; office UI can create tasks. No Brayman task names hard-coded as CalibAi core.
2. Whether the first implementation prompt includes **office-only manual actuals** or defers all actuals persistence (this architecture recommends **defer**).
3. Exact condition vocabulary vs existing M011 `site_condition` / `schedule_condition` string sets (align, do not invent a second competing enum without a mapping table).
4. ADR-025 is **Accepted**; Labour Engine must not “fix” selling price (FG-009).
5. Historical `hourly_rate = 0.13` and material-as-labour rows: mapping/review only; **no FG-006 data repair** unless separately gated.

---

## 23. Related documents

- [FG-008](../feature-gates/FG-008-labour-engine-phase-b.md)
- [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md)
- [organization-and-calibration-architecture.md](organization-and-calibration-architecture.md)
- [historical-estimate-ingestion-architecture.md](historical-estimate-ingestion-architecture.md)
- [FG-006](../feature-gates/FG-006-historical-estimate-ingestion-phase-b.md)
- [FG-007](../feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md)
- [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) · [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md)
- [pricing-policy.md](../pricing-policy.md)
- [CAR-001](CAR-001-calibai-product-architecture-reconciliation.md)
