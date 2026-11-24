# Feature Gate FG-042: Financial Foundation (Living Project P&L, Gate 1)

| Attribute | Value |
|----------|--------|
| Feature Gate ID | `FG-042` |
| Feature Name | Financial Foundation: immutable approved baseline (S1), per-person loaded cost on time (S2), project-performance permission (S2b) |
| Programme | Living Project P&L, five approval gates. This is **Gate 1** of 5. It is not the "Gate 1" in [estimate-approval-and-commercial-gates.md](../governance/estimate-approval-and-commercial-gates.md), which is formal contractor approval. |
| Module | **Estimating** owns the estimate and its approval (referenced, unchanged). **Projects** owns the baseline record. **People & Access** owns employees, cost profiles and the grants store. **BUILD** owns time entries (referenced, unchanged). |
| Date | 2026-11-24 |
| Status | **APPROVED 24 Nov 2026 (design and migrations M1, M2, M3). IMPLEMENTED AND TESTED IN THE REPOSITORY; NOT YET VALIDATED IN PRACTICE; NOT IN PRODUCTION. Production needs Joel's authorization after the validation report.** |
| Governing specification | [Design approvals](../architecture/living-project-pl-design-approvals-2026-11-24.md). S0 Consolidated Package and R5 (held outside this public repository). |
| Repository head at drafting | `1167e203`. Alembic graph head `q1a2b3c4d5e6`. After this gate: `d3b6c9e2f5a7` (M1 `b1f4a9c2d7e3`, M3 `c2a5b8d1e4f6`, M2 `d3b6c9e2f5a7`). |
| Validation project | Geleynse. Its estimate is **not modified** and no unreconciled baseline is frozen. |

## 1. What problem does this solve?

The approved estimate is not yet the project's financial record. Today:

- there is no link between an employee (`OrganizationPerson`) and the user who enters time, so approved hours cannot be priced at that person's loaded rate;
- cost profiles carry no effective date, so a rate cannot be looked up by the date work was done;
- the approved estimate stores a summary and crew **shares**, not per-person per-task hours or itemized material lines, so there is nothing precise to compare actuals against;
- project economics and the Hub Money and labour-cost panels are gated only to Owner or System Administrator, with the Hub panels missing the check, and no project-performance permission exists.

## 2. Who is the user?

Joel and Ben as Owner and System Administrator. Later, authorized project managers (project-performance permission). Field crew are unaffected: they never see cost.

## 3. Which module owns it?

Projects owns the baseline tables. People & Access owns the Person-to-User link, cost-profile dating and the grant. Estimating, BUILD and MONITOR are consumers; their data and behaviour are preserved.

## 4. What data does it own?

New: project baselines (header, labour allocations, person rates, cost lines, open items), markup overrides. New columns: person link, cost-profile effective date, other employment cost.

## 5. What data does it reference?

`Estimate`, `EstimateVersion`, `EstimateApproval`, `OrganizationPerson`, `OrganizationPersonCostProfile`, `User`, `ProjectWorkActivity`, `LabourTimeEntry`, `UserMembershipAccessDomainGrant`.

## 6. What may it change?

Only the additive items in section 12. Behavioural changes, each behind tests:

- one shared materials markup calculation (new module, called by the baseline builder; legacy methods untouched);
- a dated loaded-rate lookup, used by project labour cost when a Person link exists;
- a `PROJECT_PERFORMANCE` access domain recognized in `access_domains.py`;
- permission checks added to the Hub Money and labour-cost panels and their routes, reports, exports and drill-downs.

## 7. What must it not change?

- Any existing estimate, approval, `summary_json`, frozen summary, quotation, signed document or Proposal. The Geleynse estimate is not touched.
- The existing internal financial summary layout (preserved until a revised version is approved).
- Existing time entry, banked hours, QuickBooks Time (stays switched off), payroll time, MONITOR V1 and PERF calculations where no baseline or Person link exists.
- Existing cost-profile rows. The table is insert-only (trigger). No backfill, no update.
- The employee register. No duplicate register and no second rate store.

## 8. Acceptance criteria

### S1: immutable approved baseline

- A project baseline can be created as **PROVISIONAL** from an estimate version, holding per-person per-task hours, itemized cost lines, the labour selling rate, and the pricing basis.
- Outstanding commercial items are recorded as **open items** and carried as provisional lines. A baseline with any open item **cannot be frozen** (enforced in service and database).
- Freezing is a deliberate act by Owner or System Administrator. It records who, when, and a SHA-256 of the canonical baseline content.
- Once **FROZEN**, no baseline row, allocation, rate or line can be updated or deleted (database triggers, as for `organization_person_cost_profiles`). Only the header may move to SUPERSEDED. A change is a new baseline version, never an edit.
- Only one baseline is FROZEN per project. For the validation project only the accepted roofing option becomes the baseline.
- Baseline totals reproduce the approved totals **to the cent** through deterministic, traceable rounding. A reconciliation report shows source against baseline and any difference, and a difference blocks freezing.
- Labour allocations tie to the source Labour Calculation Detail by Person: per task and per person, and in total.
- Selling price per material line follows the shared markup rule. A quoted-price override is stored with its reason and shown.
- Allocation schedules display hours and assignments only. Financial summaries order Revenue, Cost, Profit, Profit Margin.
- Existing estimates, approvals and frozen summaries are byte-identical before and after.

### S2: per-person loaded cost applied to time

- An Owner or System Administrator can link a Person to a User. One User per Person and one Person per User within an organization.
- Loaded rate for a person **on a work date** resolves from the cost profile in force that day (effective-dated, deterministic, tie-broken by id). A later rate change never alters an earlier date's rate.
- Approved time entries for a linked person are priced at that person's dated loaded rate. Entries for an **unlinked** user are **not** silently priced at another rate: they appear under an explicit "unlinked time" line using the existing company rate, labelled as such.
- Other employment cost is part of the loaded rate when present and zero when absent, so every existing loaded rate is unchanged.
- Project labour cost shown in MONITOR and performance uses the dated person rate where linked, with unchanged results for projects with no linked people.

### S2b: permissions

- A `PROJECT_PERFORMANCE` grant lets a person view project economics (cost, price, profit, forecast) without employee compensation detail. It is independent of `can_view_employee_cost`.
- Without either permission, no financial figure appears anywhere: Hub Money panel, labour-cost panel and table, MONITOR financial blocks, reports, exports, document downloads and drill-down routes.
- Every route and export that returns financial data enforces the check server-side, not only by hiding UI. A direct URL or POST by an unauthorized user returns refusal, and tests cover each route.
- Ben's actual permissions are set at onboarding, not by this gate.

## 9. Tests required

Retain every existing regression test. Add, at minimum:

- markup calculation and rounding: line level, package level and project level reconcile; discount derivation reconciles to the quoted discount; override with reason;
- baseline: create, open-item freeze block, freeze, then update and delete each refused at the database level; one frozen baseline per project; SHA reproducible; approval and summary bytes unchanged;
- labour allocation tie-out per task, person and total; hours-only rendering;
- effective-dated rates: rate on a date before, on and after a change; same-day tie-break; no change to existing loaded rates when new columns are null;
- Person-to-User link uniqueness and organization isolation; unlinked-time behaviour;
- permissions matrix (Owner, SysAdmin, `PROJECT_PERFORMANCE` holder, ordinary office user, field-only user) against every financial route, report, export and drill-down;
- migration up and down on a copy of the Production SQLite backup, preserving all existing row counts and values.

Commands will be reported exactly, with results, in the validation report.

## 10. Documentation to update

`docs/current-state.md`, `docs/session-handoff.md`, `docs/chat-workflow-log.md`, `docs/feature-gates/README.md`, `docs/project-state-report.md`, `docs/modules/` (Projects, People & Access), a new ADR (section 11), and the permission map in `docs/security/`.

## 11. Does it require an ADR?

Yes. **ADR-059 (accepted 24 Nov 2026; numbered 059 because ADR-054 was already taken): Project baseline snapshot ownership and immutability.** It records that the baseline is a Projects-owned immutable snapshot, why actuals, forecasts and calibration live outside it, and the Person-to-User and dated-rate decisions. It is drafted with the code and presented for Joel's acceptance. It does not supersede ADR-021 (MONITOR commercial baseline); it extends it.

## 12. Does it require a database migration?

**Yes. Three additive revisions are proposed. None is authorized until Joel approves them.** All follow `q1a2b3c4d5e6`. Production is SQLite on the Render disk, so each is additive only (new tables, nullable columns, indexes, triggers), written to run on SQLite, and each has a downgrade that refuses when the new tables hold rows.

### Revision M1: Person link, cost-profile dating, other employment cost

| Change | Detail |
|--------|--------|
| `organization_people.user_id` | INTEGER NULL, FK `users.id` ON DELETE RESTRICT |
| Unique index | `(organization_id, user_id)` where `user_id IS NOT NULL` |
| `organization_person_cost_profiles.effective_from` | DATE NULL. Resolver uses `COALESCE(effective_from, date(created_at))`. **No backfill**, because the table is insert-only. |
| `organization_person_cost_profiles.other_employment_cost_annual` | NUMERIC(12,2) NULL, treated as 0 when null. Decision S0-4, recommended and included here. |
| Index | `(person_id, effective_from, id)` |

### Revision M2: Project baseline

| Table | Key columns and constraints |
|-------|-----------------------------|
| `project_baselines` | id; `organization_id`; `project_id` FK; `estimate_id` FK; `estimate_version_id` FK; `estimate_approval_id` FK NULL (unique when set); `option_label`; `status` CHECK in (`PROVISIONAL`, `FROZEN`, `SUPERSEDED`); `labour_selling_rate` NUMERIC(10,2); `pricing_basis` CHECK = `MARKUP`; `content_sha256`; `frozen_at`; `frozen_by_user_id`; created fields. Partial unique index: one `FROZEN` per project. |
| `project_baseline_labour_allocations` | id; `baseline_id` FK; `group_name`; `task_name`; `sort_order`; `person_id` FK; `hours` NUMERIC(10,2) CHECK >= 0; `project_work_activity_id` NULL FK; UNIQUE `(baseline_id, task_name, person_id)` |
| `project_baseline_person_rates` (owner-only) | id; `baseline_id` FK; `person_id` FK; `cost_profile_id` FK; `loaded_rate` NUMERIC(10,2); UNIQUE `(baseline_id, person_id)` |
| `project_baseline_lines` | id; `baseline_id` FK; `category` CHECK in (`MATERIAL`, `SUBCONTRACT`, `EQUIPMENT`, `OPENING`, `ALLOWANCE`, `OTHER`); `source_ref`; `supplier_name`; `sku`; `description`; `quantity`; `uom`; `list_unit_price`; `discount_amount`; `net_cost`; `markup_rate`; `selling_price`; `price_override_reason`; `is_provisional` BOOLEAN; `provisional_reason`; `sort_order` |
| `project_baseline_open_items` | id; `baseline_id` FK; `description`; `status` CHECK in (`OPEN`, `RESOLVED`); `resolved_by_user_id`; `resolved_at`; `resolution_note` |
| Triggers | Allocations, person rates and lines: BEFORE INSERT, UPDATE and DELETE abort when the parent baseline is `FROZEN` or `SUPERSEDED`. Header: BEFORE UPDATE aborts unless it is the PROVISIONAL-to-FROZEN transition (with no OPEN items) or FROZEN-to-SUPERSEDED. Header DELETE aborts once frozen. |

### Revision M3: Markup overrides

| Table | Key columns and constraints |
|-------|-----------------------------|
| `pricing_markup_overrides` (insert-only) | id; `organization_id`; `scope` CHECK in (`PROJECT`, `SUPPLIER`); `scope_ref`; `markup_rate` NUMERIC(10,6) CHECK >= 0; `reason`; `effective_from`; created fields. Latest row per scope wins. Company markup stays in the existing pricing policy. |

**Not a migration:** the `PROJECT_PERFORMANCE` grant uses the existing `user_membership_access_domain_grants` table (the `domain_key` column is free text with no check constraint). It needs only a code change in `access_domains.py` to recognize the key.

### Rollback and safety

- Before any Production migration: a timestamped backup of the Production database on the Mac backup path, verified, and a migration rehearsal on a copy.
- Downgrades refuse when the new tables hold rows, as in earlier revisions.
- Nothing is applied to Production until Joel approves the Practice validation report.

## 13. Reuse and what is not rebuilt

| Existing | Use in this gate |
|----------|------------------|
| `OrganizationPerson`, `OrganizationPersonCostProfile`, `labour_cost_profile.calculate` and `loaded_rate_for` | The only source of loaded rates. Gains a dated lookup and the optional other-cost term. |
| `EstimateApproval`, `freeze_for_approval`, `internal_financial_summary` | Unchanged. The baseline references the approval. |
| `pricing_engine`, `OrganizationPricingPolicy`, `markup_rate` columns | Company markup. One shared calculation added for line-level markup. |
| Supplier pricing and price evidence | Source of net cost and discount for baseline material lines. |
| `ProjectWorkActivity` | Optional link from allocation rows. |
| `LabourTimeEntry`, `time_entry` services | Unchanged. Pricing is applied on read. |
| `project_performance._RateBook` and `assemble_project_labour_cost` | Extended to prefer the dated person rate when linked. Otherwise unchanged. |
| `financial_access`, `access_domains`, grants table | Extended, not replaced. |
| `u8b9c0d1e2f3` insert-only trigger pattern | Reused for baseline immutability. |

Baseline data entry reuses the source documents: the Labour Calculation Detail by Person is imported (CSV) into a PROVISIONAL baseline through an Owner-only page on the Project. The estimating engine is not rebuilt or modified.

## 14. Order of work (after migration approval)

1. M1 and S2 (Person link, dated rate, unlinked-time handling) with tests.
2. S2b (grant, Hub Money and labour-cost gating, route, report, export and drill-down enforcement) with the permissions matrix.
3. M3 and the shared markup calculation with tests.
4. M2 and S1 (baseline, import, reconciliation, open items, freeze, triggers) with tests.
5. Full suite, migration rehearsal on a Production backup copy, then **Practice validation** against the Geleynse validation project with the baseline left PROVISIONAL because of the open commercial items.
6. Validation report to Joel. **Production deployment only after his approval.**

## 15. Carried commercial items (do not block code, do block freezing the Geleynse baseline)

Quotation roofing-line exclusion confirmation; whether installation labour is inside the estimated hours; window count; Brayman cost on the window and door quote and installation pricing; current crane quote; roofing line detail and porch roof inclusion; unpriced materials; hatch fire rating; quotation expiry date; employee loaded rates at onboarding.

## 16. Out of scope

Percent complete, remaining hours, material actuals, change orders, forecast, dashboard and report assembler (Gate 2); alerts and Sync snapshots (Gate 3); closeout and LEARN (Gate 4); QuickBooks Time activation (Gate 5); Brayman onboarding.

## 17. Disclosed implementation notes (24 Nov 2026)

Two additive columns beyond the tables as first described, both nullable and tied to approved fields:

- `organization_person_cost_profiles.other_employment_cost_note` (M1): the plain description of the optional "other employment cost". It is required when the amount is above zero and is checked against the cost already counted elsewhere in the profile (wages, vacation, holiday pay, CPP, EI, WSIB, EHT, RRSP, truck, fuel, tools, health and other premiums); a note that names one of those is refused. A blank or zero amount changes no loaded rate.
- `project_baselines.reconciliation_json` (M2): the source figures and result a freeze relied on.

Also: the immutability triggers cover open items as well as the three tables listed in section 12, and a baseline with a provisional line cannot be frozen. The decision record is [ADR-059](../adr/ADR-059-project-baseline-snapshot-ownership-and-immutability.md).

Behaviour to know: when a time entry's worker is linked to an employee, actual labour cost uses that employee's dated loaded rate; the estimated side still uses the estimate's company rate, so estimated and actual labour cost can differ in basis until Gate 2 reports them side by side. Changing or removing a person-to-user link is refused once that user has time entries, so past cost cannot be silently re-priced.
