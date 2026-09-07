# FG-023 MONITOR V1 — Implementation preflight

| Attribute | Value |
|-----------|--------|
| Status | **PREFLIGHT COMPLETE.** [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **APPROVED / OPEN**. Slice A **IMPLEMENTED / NOT LIVE-MIGRATED** (2026-09-06). Hub UI **NOT IMPLEMENTED**. This preflight remains the Slice A mechanics pin. |
| Date | 2026-09-06 |
| Parent | Approval commit `64b6a5472613f00b862170bd57be07486a11f91f` |
| Recon | [monitor-v1-implementation-reconnaissance.md](monitor-v1-implementation-reconnaissance.md) **COMPLETE** |
| Readiness | **B. READY WITH EXPLICIT NON-BLOCKING NOTES** |

```text
FG-023:
APPROVED
IMPLEMENTATION NOT STARTED
NOT AUTHORIZED BY THIS PREFLIGHT
MONITOR V1 NOT IMPLEMENTED
```

This document pins later implementation mechanics. It does **not** amend FG-023. Slice A product code was authorized by a later 6 Sep 2026 implementation prompt. Hub UI, live migrate, and office UAT remain **not** authorized by this preflight.

**Subsequent status (2026-09-06 Slice A):** Model `ProjectDirectCostActual`, additive revision `e3f4a5b6c7d8` (`down_revision = d2e3f4a5b6c7`), BUILD `app/services/direct_cost_actuals.py`, MONITOR `assemble_monitor_v1`, dedicated tests **23 passed**. Live current remains `d2e3f4a5b6c7`. Live Event/Original counts **39 / 39**. No live `ProjectDirectCostActual` rows. Hub `#hub-monitor` **not implemented**. Gate **not closed**.

---

## Inspected gap (2026-09-06)

| Check | Result |
|-------|--------|
| A. `ProjectDirectCostActual` model | **Does not exist** |
| B. `project_direct_cost_actuals` table (code + live SQLite) | **Does not exist** |
| C. MONITOR comparison/projection service | **Does not exist** (recon intended `app/services/monitor.py`) |
| D. `#hub-monitor` | **Non-operational / Future** (`app/templates/projects/detail.html`) |
| E. Field Events as cost | **Not cost inputs** (`app/services/build.py`; Hub lists evidence only) |
| F. Existing durable actual-cost record satisfying FG-023 | **None** |
| G. Existing FG-023 migration | **None**. Head remains `d2e3f4a5b6c7` |
| H. Alembic graph | **One head:** `d2e3f4a5b6c7` current = head |

---

## 1. `ProjectDirectCostActual` field contract (do not create now)

**Owner:** BUILD. **Table:** `project_direct_cost_actuals`. **Class:** `ProjectDirectCostActual`.

Recommended later path: `app/models/direct_cost_actual.py` (do **not** mix into `FieldCaptureEvent`). Import from `app/models/__init__.py`.

Names follow FG-023, not the prompt’s aliases: `incurred_on` not `incurred_date`; `user_id` not `created_by_user_id`; `note` not `description`.

| Exact name | Type | Null | Default | FK | Index | Reason |
|------------|------|------|---------|----|-------|--------|
| `id` | Integer PK | no | autoincrement | — | PK | Durable identity |
| `organization_id` | `String(50)` | no | — | `organizations.id` **ON DELETE RESTRICT** | yes (column + composite) | Org isolation (FG-018) |
| `project_id` | Integer | no | — | `projects.id` **ON DELETE RESTRICT** | yes (column + composite) | Project actuals grain |
| `user_id` | Integer | **yes** | — | `users.id` **ON DELETE SET NULL** | yes (same as Field Events) | Actor when session user exists; nullable if user later removed |
| `actor_display_name` | `String(150)` | no | — | — | no | Durable actor snapshot (`current_actor_display_name` / Field Event analogue) |
| `cost_class` | `String(40)` | no | — | — | no | FG-023 class enum |
| `amount` | `Numeric(14, 2)` | no | — | — | no | Pre-tax incremental Direct Cost; `>= 0` |
| `incurred_on` | `Date` | no | — | — | no | Incurred calendar date (not `created_at`) |
| `note` | Text | **yes** | — | — | no | Optional office note |
| `source` | `String(40)` | no | `'OFFICE_MANUAL'` | — | no | V1 source freeze |
| `supersedes_id` | Integer | **yes** | — | self `project_direct_cost_actuals.id` **ON DELETE RESTRICT** | **UNIQUE** | Correction pointer |
| `created_at` | DateTime | no | `datetime.utcnow` | — | no | Audit timestamp |
| `provenance` | Text | **yes** | — | — | no | Optional structured note; FG-023 field |

**Do not add:** invoice number, vendor ledger, GL account, payment status, tax amount, QuickBooks id, forecast fields, `description` duplicate of `note`, equipment class, payroll burden, PO committed-not-incurred.

Service must require `organization_id == Project.organization_id` (Field Event pattern).

---

## 2. Constraints

**DB CHECK (fail-closed, same style as FG-020 `kind IN (...)`):**

- `ck_project_direct_cost_actuals_amount_nonnegative`: `amount >= 0`
- `ck_project_direct_cost_actuals_cost_class`: `cost_class IN ('labour', 'material', 'subcontract', 'other_direct')`
- `ck_project_direct_cost_actuals_source`: `source = 'OFFICE_MANUAL'`

**DB UNIQUE:**

- `uq_project_direct_cost_actuals_supersedes_id` on `supersedes_id`  
  SQLite allows multiple NULLs → multiple **current** incremental rows are lawful.  
  At most one direct successor per prior row.

**DB indexes:**

- `ix_project_direct_cost_actuals_organization_id`
- `ix_project_direct_cost_actuals_project_id`
- `ix_project_direct_cost_actuals_user_id`
- composite `(organization_id, project_id)` as FG-023 requires
- unique index implied by UNIQUE `supersedes_id`

**Do not add uniqueness** on `(project_id, cost_class, incurred_on, amount)`. Repeated same-day same-class amounts are legitimate incremental entries.

**Service validation (user-facing, both layers):**

- parse `amount` with existing `as_money` (`Decimal` `0.01`, `ROUND_HALF_UP` from `app/services/pricing_engine.py` / `estimate_builder.py`)
- reject negative before flush
- require class enum / `OFFICE_MANUAL`
- require `incurred_on` parseable date
- org/project match; prior row same org+project; no self-supersede; prior has no successor

**Self `id != supersedes_id`:** enforce in service after flush (Field Event analogue). SQLite cannot cheaply CHECK against the new PK before insert.

**Enforcement: both** DB CHECK/UNIQUE and service validation.

---

## 3. Supersession / correction mechanics

Follow `FieldCaptureEvent` (`app/models/build.py`, `app/services/build.py`). Not a general ledger.

| Question | Pin |
|----------|-----|
| A. Successor points at superseded row? | **Yes.** Successor.`supersedes_id` = prior.`id` |
| B. More than one direct successor? | **No** |
| C. How enforced? | UNIQUE `supersedes_id` + service `successor_event` analogue → conflict (HTTP 409 / flash, Field Event 409 pattern) |
| D. Can a successor later be superseded? | **Yes.** Chain: 1 ← 2 ← 3 |
| E. Correction chain | Each successor **restates** that observation (replacement amount / class / date / note). Prior rows remain durable. Active tip is the row with no successor |
| F. Deterministic ACTIVE rule | A row is **ACTIVE** iff no other row has `supersedes_id = that row.id` |
| G. Active rollup | **Yes:** sum `amount` of ACTIVE rows for org+project. Equivalent to “rows for which no valid successor exists” |
| H. Cross-project | Load prior with `organization_id` + `project_id` (Field Event `get_field_event`). Mismatch → not found / 404, not a silent attach |
| I. Cross-organization | Same load is org-scoped. Hub project lookup is `Project.query.filter_by(id=, organization_id=).first_or_404()` |
| J. Self-supersession | Service reject if `supersedes_id == id` |
| K. Cycles | Append-only (no in-place `supersedes_id` mutation) + unique successor + self-id check. A new row can only point at an existing prior. Do not add graph-walk unless an update path is later invented (V1 must not update) |
| L. Service vs DB | UNIQUE + CHECKs required; service for org/project, self, already-superseded, parse errors |
| M. Duplicate vs correction | **CREATE** always inserts a new independent incremental row (even same class/date/amount). **CORRECT** is only POST supersede against a specific prior id |

**No DELETE route. No PUT/PATCH amount edit.** Correction = successor row, including `amount = 0.00`.

---

## 4. Actual-cost ownership

| Pin | Value |
|-----|--------|
| Owner | **BUILD** |
| Source V1 | **OFFICE_MANUAL** only |
| Grain | Incremental incurred Direct Cost (not restated-to-date class balances) |
| Classes | `labour` \| `material` \| `subcontract` \| `other_direct` |
| MONITOR | Reads / rolls only. No MONITOR-owned actual table. No MONITOR snapshot table in V1 |
| Field Events | Evidence only. No conversion |
| Import | None (no QuickBooks, no automatic accounting) |
| Delete / silent rewrite | Forbidden |

---

## 5. Baseline source mapping (from live models)

**Locked source version** = the Accepted Proposal’s `estimate_version_id` (`app/models/proposal.py`). Do **not** use a later Draft `Estimate.current_version`.

**Accepted Proposal** = `Proposal.status == "Accepted"` (`PROPOSAL_STATUSES` includes Draft / Ready / Issued / Accepted / Rejected / Expired / Cancelled / Superseded). Join via `Proposal.estimate_id` → `Estimate.project_id`.

If **zero** Accepted Proposals: `baseline_state` / customer-commitment missing; do not invent revenue.

If **more than one** Accepted Proposal on the project: **STOP in implementation** and surface an incomplete/ambiguous commitment. FG-023 says “the Accepted Proposal” (singular). The schema does not unique that. Do **not** pick “latest.” Non-blocking note for the implementation prompt.

`EstimateVersion` lock: `is_locked` and/or `status in AUTO_LOCK_VERSION_STATUSES` (`Issued`, `Accepted`, `Rejected`, `Superseded`) in `app/models/estimate.py`. Draft / In Review are floating and must not be the committed baseline.

### Original Estimated Direct Cost

1. If locked source version has `EstimatePricingSnapshot` (`version.pricing_snapshot`, table `estimate_pricing_snapshots`): use `direct_cost_basis` (`Numeric(14,2)`).
2. Else: Σ `EstimateLineItem.extended_cost` on that locked version’s sections (`app/services/estimate_output.py` / `pricing_engine.sum` analogue).
3. **Do not** add `EstimateLabourSnapshot.direct_labour_cost`.

Allowances already inside snapshot / `extended_cost` (line_type `Allowance`) stay inside Direct Cost. Do not strip them.

### Original Estimated Pre-Tax Selling Price / Original Authorized Pre-Tax Revenue

These are the **same original pair** for Estimated GM (not Current Authorized Revenue).

1. If the Accepted Proposal’s source version has a snapshot: `EstimatePricingSnapshot.pre_tax_selling_price`.
2. Else: Accepted Proposal `subtotal + overhead_amount + profit_amount` (exclude `tax_amount` and `total`).

### Approved CO pre-tax revenue delta

`ChangeOrder` in `app/project_controls/models.py`.

- Status strings: `Draft`, `Pending Approval`, `Approved`, `Rejected`, `Invoiced`, `Cancelled`.
- **Include:** `Approved` **or** `Invoiced`.
- **Exclude:** `Draft`, `Pending Approval`, `Rejected`, `Cancelled`.
- Amount: `subtotal + markup` (`Numeric(14,2)`). Exclude `tax`. Do not use `total`.
- `Invoiced` is **not** books revenue.
- `ChangeOrderItem.unit_price` is **not** estimated cost.
- CO `total` is **not** actual cost.
- No CO estimated-cost delta in V1.
- **Current Authorized Estimated Cost** = Original Estimated Direct Cost.

`ChangeOrder` has `project_id` only (no `organization_id`); isolate via the Hub project.

### Current Authorized Pre-Tax Revenue

Original Authorized Pre-Tax Revenue + Approved CO Pre-Tax Revenue Delta. No credit instrument.

---

## 6. Project Gross Margin math

Preserve FG-023 / ADR-021. No NET PROFIT. No forecast-final GM.

```text
estimated_gm = 1 − (Original Estimated Direct Cost / Original Estimated Pre-Tax Selling Price)
actual_to_date_gm = 1 − (Actual Direct Cost to date / Current Authorized Pre-Tax Revenue)
gm_variance = actual_to_date_gm − estimated_gm
```

Estimated GM uses the **original** pair. Do **not** recompute Estimated GM against CO-inflated revenue.

| Topic | Pin |
|-------|-----|
| Decimal | `decimal.Decimal` throughout. Money via existing `as_money` (`ROUND_HALF_UP`, quantum `0.01`) |
| Money display | Two decimal places (existing Hub/proposal convention) |
| Internal GM | Unquantized `Decimal` division of money amounts; do not round identities to money scale before the ratio |
| GM display | **Not frozen by FG-023.** Non-blocking note: later Hub may format as percent with `ROUND_HALF_UP`. Do not invent a new money class |
| Zero denominator | Do **not** emit Inf/NaN/fake 100%. Incomplete baseline / incomplete actual GM |
| Null/missing denominator | Incomplete state warning, not silent zero |
| Missing baseline | Warn; no Estimated GM |
| Missing actuals | **`MISSING_ACTUALS`**. Do **not** treat actual cost as `0.00`. Do **not** display Actual GM |
| Overhead / profit / G&A | Not Direct Cost. Optional ORG-001 layers remain `UNSPECIFIED` where current authority says so |
| HST/tax | Outside GM |

---

## 7. MONITOR service contract

**Path:** `app/services/monitor.py` (recon). **Name:** `assemble_monitor_v1(project, organization_id: str) -> dict`.

Read-only. No commit. Call BUILD list/sum helpers; do not own actuals.

**Inputs:** org-scoped `Project`.

**Return (snake_case; omit forecast / LEARN / accounting-system fields):**

- `original_estimated_direct_cost` (`Decimal` or `None`)
- `original_estimated_pre_tax_selling_price` (`Decimal` or `None`)
- `estimated_gm` (`Decimal` or `None`)
- `approved_co_revenue_delta` (`Decimal`; `0.00` if none authorized)
- `authorized_co_ids` / `authorized_co_count`
- `current_authorized_estimated_cost` (equals original DC or `None`)
- `current_authorized_pre_tax_revenue` (`Decimal` or `None`)
- `actual_direct_cost_to_date` (`Decimal` or `None` when missing actuals)
- `actual_cost_by_class` (dict of four classes → `Decimal`, only when actuals exist)
- `actual_to_date_gm` (`Decimal` or `None`)
- `gm_variance` (`Decimal` or `None`)
- `actuals_state`: `MISSING_ACTUALS` \| `PRESENT`
- `baseline_state`: `COMPLETE` \| `MISSING_CUSTOMER_COMMITMENT` \| `MISSING_ORIGINAL_BASELINE` \| `AMBIGUOUS_COMMITMENT`
- `provenance`: `source_estimate_version_id`, `pricing_snapshot_id`, `accepted_proposal_id`, `authorized_co_ids`, `last_actual_created_at`
- `current_actuals`: ACTIVE rows for Hub list
- `co_cost_delta_stored`: always `False` in V1 with explicit copy

Hub calls this from `assemble_project_hub` or the project view; do not write commercial records.

---

## 8. Active actual rollup

```text
Actual Direct Cost to date
  = Σ amount of ACTIVE ProjectDirectCostActual rows
    WHERE organization_id = org AND project_id = project
```

Include `0.00` ACTIVE successors. Exclude superseded rows from the sum; keep them for audit/history.

**Future-dated `incurred_on`:** FG-023 / recon do **not** answer. **Unresolved implementation decision — do not invent.** The later implementation prompt must pin either “any valid date including future” or “reject future dates.” Until pinned, implementation must **STOP** rather than guess.

V1 grain is **to date** as posted observations, not a cutoff filter invented here.

---

## 9. Office write path (do not implement now)

Reuse Flask/Hub conventions. CSRFProtect is global (`app/__init__.py`). Office HTML unauthenticated → `login_manager.unauthorized()` → `/login` (302). Membership via `g.organization_id` / `get_current_organization_id()`. Cross-org project **404**.

| Action | Contract |
|--------|----------|
| CREATE | `POST /projects/<id>/direct-cost-actuals` |
| CORRECT | `POST /projects/<id>/direct-cost-actuals/<actual_id>/supersede` |
| DELETE | **None** |
| PUT/PATCH amount | **None** |

Register on `projects_bp` (`app/routes/projects.py`) so Hub owns UX; handlers call BUILD write service.

**CREATE form fields:** `cost_class`, `amount`, `incurred_on`, `note` (optional), CSRF token.

**CORRECT form fields:** replacement `cost_class`, `amount`, `incurred_on`, `note` (optional), CSRF. Prior id in URL.

**Validation:** flash + re-render / redirect Hub on 400; 409 if already superseded; 404 cross-org / missing prior.

**Success:** PRG redirect to `url_for("projects.view_project", id=project.id) + "#hub-monitor"`.

Actor: `user_id` from session; `actor_display_name` from `current_actor_display_name` / `form_actor` analogue used by Field Events (`app/services/auth.py`, `app/services/build.py` `_actor_snapshot`).

No Field Web MONITOR UI. No `/api/v1` actuals in V1 (FG-023 office Hub only).

---

## 10. Project Hub integration

| Current | Path |
|---------|------|
| Route | `GET /projects/<id>` → `app/routes/projects.py` `view_project` |
| Template | `app/templates/projects/detail.html` |
| Assembly | `app/services/project_hub.py` `assemble_project_hub` |
| Placeholder | `#hub-monitor` + lifecycle chip `MONITOR · Future` |

Later minimum presentation (FG-023 UI list): original DC; original authorized pre-tax revenue; estimated GM or missing-baseline; authorized CO delta + count; current authorized pre-tax revenue; current authorized estimated cost + “CO cost delta not stored”; actuals by class + total **or MISSING ACTUALS**; Actual-to-date PGM only if actuals exist; variance only if both GM exist; provenance; create form; current actuals list with supersede control; superseded history visible as superseded (Field Event analogue).

No health traffic-lights. No NET PROFIT. No industry benchmarks. No separate MONITOR app.

---

## 11. Auth / isolation

Reuse FG-018 / FG-019. No RBAC, invitations, SSO, session revocation.

- Login: `protect_office_routes` in `app/__init__.py`
- Org: `resolve_membership_organization_id` / `get_current_organization_id`
- Hub project: `filter_by(id, organization_id).first_or_404()`
- CSRF: Flask-WTF; tests copy `_csrf_token` from `tests/test_build_field_observation_fg020.py` / `tests/test_auth_fg018.py`

---

## 12. Alembic (do not create / mint now)

Current head **`d2e3f4a5b6c7`**. Expected later `down_revision = d2e3f4a5b6c7`.

**Do not mint a revision id in this preflight.** Filename pattern once authorized: `migrations/versions/<revision>_add_project_direct_cost_actuals_fg023.py`.

| Pin | Value |
|-----|--------|
| Purpose | Additive BUILD office Direct Cost actuals |
| Table | `project_direct_cost_actuals` |
| Columns / FKs / indexes / CHECKs / UNIQUE | As §1–2 |
| Self-FK | `supersedes_id` → same table **ON DELETE RESTRICT** |
| Upgrade | `create_table` only. **No backfill.** Existing projects valid with zero rows |
| Downgrade | Drop that table only |
| Destructive | **No** |
| Live `flask db upgrade` | Only when a later prompt explicitly authorizes live migrate |

---

## 13. Test package (do not write now)

**New dedicated file:** `tests/test_monitor_v1_fg023.py` (name frozen by FG-023).

**Command:** `./venv/bin/python -m pytest -q tests/test_monitor_v1_fg023.py`

**Extend (do not rewrite meaning):** `tests/test_project_hub.py`, `tests/test_auth_fg018.py` CSRF pattern, `tests/test_build_field_observation_fg020.py` supersession analogue, `tests/test_change_orders.py` / `tests/test_pricing_engine.py` / `tests/test_estimate_output_consistency.py` / `tests/test_proposal_immutability.py` as regression sources.

Cover at minimum the lists in the preflight prompt: model CHECKs; `amount > 0`; `amount = 0`; negative rejected; class/source enums; org/project; supersession chain; self/cross-project/cross-org rejected; snapshot vs fallback baseline; Accepted Proposal composition; Approved + Invoiced CO included; unauthorized CO excluded; no CO-cost invention; HST excluded; active rollup; superseded excluded; class rollup; MISSING_ACTUALS; missing baseline; GM identities; zero denominator; Field Events excluded; login/CSRF; create/correct; no delete; no in-place edit; Hub copy; no NET PROFIT; EstimateVersion / snapshot / Accepted Proposal / CO / Field Events unchanged.

Later focused set (implementation close): dedicated FG-023 + Hub + FG-018 + FG-020 + FG-021 as applicable. Exact counts recorded at implementation close, not here.

---

## 14. Office UAT (do not perform now)

Office-only, later close prompt. Minimum:

1. Safe UAT project with locked version + snapshot + Accepted Proposal + one Approved CO.
2. MONITOR shows baseline layers + MISSING ACTUALS; no Actual GM.
3. Add labour actual.
4. Add material actual.
5. Class rollup + total.
6. Actual-to-date PGM appears.
7. Estimated GM remains original pair.
8. Approved/Invoiced CO affects Current Authorized Revenue only.
9. CO does not invent actual or estimated cost.
10. Correct one actual via successor.
11. Prior row durable.
12. Active rollup uses successor only.
13. `0.00` successor works.
14. Baseline records unchanged.
15. Field Events unchanged.
16. No NET PROFIT language.
17. Cross-org isolation (second org 404).
18. Draft-only estimate: committed baseline missing, not a fake number (FG-023 UAT item 7).

---

## 15. Files expected to change **later** (not this pass)

**NEW**

- `app/models/direct_cost_actual.py`
- `app/services/monitor.py`
- `app/services/direct_cost_actuals.py`
- `migrations/versions/<not minted>_add_project_direct_cost_actuals_fg023.py`
- `tests/test_monitor_v1_fg023.py`

**MODIFIED**

- `app/models/__init__.py`
- `app/routes/projects.py`
- `app/services/project_hub.py`
- `app/templates/projects/detail.html`
- possibly `app/static/` only if Hub CSS already used by `#hub-monitor` needs a bounded class (prefer existing Hub styles)

**DOCS (later implementation/close, not this preflight beyond this artifact)**

- FG-023 status when implementation starts/closes
- `docs/modules/monitor.md`, `docs/modules/build.md`
- current-state / handoff / roadmap / log / milestones

**Do not later change:** Field Web templates/JS, FG-021/FG-022 product meaning, Observation Delete, LEARN, QuickBooks.

---

## 16. Implementation slicing

Recommend **three governed slices** after a **separate** implementation authorization. Do not run them from this preflight.

| Slice | Scope | Why |
|-------|--------|-----|
| **A** | Model + additive migration file + BUILD write/list/sum service + MONITOR `assemble_monitor_v1` + dedicated tests | Persistence and math before UI. No live migrate unless that prompt says so |
| **B** | Hub routes/forms/`#hub-monitor` + Hub tests | UX on the frozen service contract |
| **C** | Explicit live `flask db upgrade` + office UAT + FG-023 close governance | Rule 7 / repo live-migrate pattern |

A+B may be one implementation prompt if Joel authorizes that bound. **C must remain separate.**

---

## 17. Non-blocking notes (do not invent policy)

1. **`incurred_on` future dates** — unresolved. Implementation prompt must pin.
2. **GM percent display digits** — unresolved. Money stays `0.01`. Do not invent a new GM column type.
3. **Multiple Accepted Proposals** — schema allows it; FG-023 is singular. Implementation must not pick latest; treat as `AMBIGUOUS_COMMITMENT` / STOP.
4. Labour-apples-to-apples GM remains ADR-021 §9 later issue. Do not “correct” in V1.

None of these reopen FG-023 commercial identities.

---

## 18. Readiness decision

**B. READY WITH EXPLICIT NON-BLOCKING NOTES**

Not C/D/E: live code can implement FG-023 as written using existing Estimate / snapshot / Proposal / Change Order / Hub / Field Event supersession analogues without inventing a new accounting policy, provided the notes above are pinned in the implementation prompt rather than guessed in code.

This preflight **does not** authorize implementation.
