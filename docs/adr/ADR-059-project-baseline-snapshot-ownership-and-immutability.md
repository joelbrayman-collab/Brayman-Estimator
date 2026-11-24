# ADR-059 — Project baseline: snapshot ownership and immutability

| Field | Value |
|-------|--------|
| Title | ADR-059: Project baseline snapshot ownership and immutability |
| Status | **Accepted** (24 Nov 2026, Joel: migrations M1, M2 and M3 approved as described in FG-042) |
| Date | 2026-11-24 |
| Migration | `d3b6c9e2f5a7_fg042_m2_project_baseline.py` (follows `c2a5b8d1e4f6` M3 and `b1f4a9c2d7e3` M1) |
| Feature Gate | [FG-042](../feature-gates/FG-042-financial-foundation-immutable-baseline-employee-cost-permissions.md) |

## Context

The Living Project P&L needs a governing starting point for each project: who is expected to do how many hours of which task, what each cost line costs and sells for, and the labour selling rate. The estimate and its approval already exist and must never change. The employee register already owns people and their loaded rates and must not be duplicated.

## Decision

1. **The baseline owns a snapshot, not the sources.** `project_baselines` and four child tables hold the labour allocations (hours and assignments), the loaded rate each person carried (owner-only), itemized cost lines and open commercial items. They reference the estimate, the estimate version and the approval; they never write to them.
2. **Three states.** PROVISIONAL (editable, may carry open items and provisional lines), FROZEN (immutable), SUPERSEDED (replaced by a later frozen baseline). A change to a frozen baseline is a new baseline.
3. **Freezing is deliberate and checked.** Only the owner or a System Administrator may freeze. A baseline with an open item or a provisional line cannot be frozen. The baseline must reconcile to the approved figures to the cent (hours, revenue and cost at least); any difference, a missing source figure, or a person without a loaded rate blocks freezing. Freezing records who, when, a SHA-256 of the canonical content and the reconciliation it relied on (`reconciliation_json`).
4. **Immutability is enforced in the database.** SQLite triggers refuse insert, update and delete on the child rows of a FROZEN or SUPERSEDED baseline, refuse any header change except FROZEN to SUPERSEDED (status only), refuse a PROVISIONAL header to FROZEN without who, when, SHA-256 and reconciliation or with open items or provisional lines, and refuse deletion of a non-provisional header. Partial unique indexes allow one FROZEN baseline per project and one live baseline per approval. The same trigger statements live in the model (so in-memory test databases carry them) and in the migration; a test keeps the two identical.
5. **One shared markup calculation** (`app/services/markup.py`) prices every material line: selling = net cost x (1 + markup), rounded half-up per line; package and project totals are sums of rounded lines; a quoted price replaces the calculated price only with a reason and the difference is shown. Markup precedence: PROJECT override, then SUPPLIER override, then the company default. Overrides are insert-only rows (`pricing_markup_overrides`, M3). Existing pricing methods are untouched.
6. **Labour is imported, not retyped.** The Labour Calculation Detail by Person is imported from CSV (`group, task, person, hours`) through an owner-only page on the Project. People are matched to the employee register; an unknown or ambiguous name refuses the whole file. A person without a loaded rate becomes an open item.
7. **Display rules.** Allocation schedules show hours and assignments only. Financial summaries order Revenue, Cost, Profit, Profit Margin. Loaded rates appear only on the owner-only baseline page.

## Consequences

- The estimate, approval, frozen summary and every existing financial record are byte-identical before and after a baseline is created or frozen (tested).
- A baseline never replaces the estimate's own price; it is the record that Gate 2 measures actuals against.
- Gate 1 freezes no real baseline: the Geleynse baseline stays PROVISIONAL while its carried commercial items are open.

## Alternatives considered

- Store the baseline inside `EstimateApproval.summary_json`: rejected, the approval is frozen and must not carry new meaning.
- Copy person rates into a second rate store: rejected, the employee register is the only rate source; the baseline keeps a reference (`cost_profile_id`) and the value as at the baseline date.
- Enforce immutability in the service only: rejected, Joel's rule is that a frozen record is protected where the data lives.
