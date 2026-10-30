# Estimate-to-Project: Execution Ledger

The durable progress record for [estimate-to-project-plan-2026-10-30.md](estimate-to-project-plan-2026-10-30.md). **Resume here.**

| Slice | Status | Commit(s) | Evidence |
|---|---|---|---|
| S0 Baseline | DONE | `f7021bb7` | Merged identity, rate and margin tests pass. Full baseline run at `f7021bb7` recorded in the release evidence. |
| S1 Work-package foundation | DONE | `1a7c4146`, `faec5f49`, `0eda3b01` | Commercial status, responsible party, delivery method, shared rule on selected work; durable section link; work page controls; project scope folded into selected work (decision 4). |
| S2 Non-destructive exclusion and pricing | DONE | `1a7c4146` | Costing, pricing, economics and proposals count participating lines only; excluded lines kept, sell price 0 (decision 3). |
| S3 Paulusse parity | DONE | `1a7c4146` | Baseline, all seven single exclusions, rate 80 and margin 20 reproduce REV2 exactly (`tests/test_work_packages_20261030.py`). |
| S4 Gate 1 | DONE | `0eda3b01` | `EstimateApproval` with frozen summary and fingerprint at sign-off; unlock refused; `/revise` makes the successor version (decision 5). |
| S5 Customer and contractor outputs | DONE | `0eda3b01`, `97a7f9d6`, `d60129e7` | Proposal Included / Excluded / By Others (preview and PDF); Contractor Estimate Package (landscape legal); masters 07/08 V2 (decision 1, decision 2). |
| S6 Labour and execution lineage | DONE | `876f03bc` | Work plan seeded per included package; activities link to their labour lines. |
| S7 Gate 3 | DONE | `876f03bc` | Early Procurement Exception before Gate 2 (decision 6); subcontract commitments with approval queue; CaliSIGN SUBCONTRACT family; committed cost by package. |
| S8 Scheduling foundation | DONE | `876f03bc` | Anticipated start (planning input); preliminary schedule from hours; ANTICIPATED / CONFIRMED windows; Gantt; procurement windows (backward planning). |
| S9 Schedule governance | DONE | `876f03bc` | Impact analysis; Company Schedule Change Request with two authorities and owner override; supplier delivery changes drafted, sent by Company Management. |
| S10 Change and cost control | DONE | `a43fdf8a` | Change-order items by package; estimate / change / committed / actual / forecast / margin by package. |
| S11 Closeout and learning | DONE | `a43fdf8a` | Closeout report, recorded closeouts, calibration proposals (never applied automatically). |
| S12 Release | IN PROGRESS | | Migration rehearsed on the 29 Oct 21:48 production backup (upgrade, downgrade, re-upgrade, integrity ok). Full regression running. |

## Rulings made during implementation

Routine architecture rulings, recorded as they are made.

1. **Labour-rate test, 2026-10-30.** The supplier form's PROJECT box holds 52 characters, so the Client # appears only when it fits. The test was corrected to match this; it was a wrong expectation, not a defect.
2. **Migration reference columns, 2026-10-30.** New reference columns on existing tables are plain integers with an index, no database foreign key (SQLite cannot ALTER a constraint), as in the guided-estimating migration. The models declare the relationships where needed.
3. **Project scope before an estimate, 2026-10-30.** Confirming project scope (project setup) writes selected work without starting an estimate. When the person creates the project's one estimate, the guided scope adopts it instead of starting a second.
4. **Excluded work at sign-off, 2026-10-30.** Work excluded from Brayman's price needs no cost confirmation before sign-off: the recorded exclusion is the decision.
5. **Window confirmation history, 2026-10-30.** Confirming an anticipated window is recorded in the append-only schedule history as a DATES_CHANGED entry with unchanged dates and the reason, so no history check constraint is rebuilt.
6. **Gate 2, 2026-10-30.** Gate 2 is passed when a proposal on the project is Accepted.
7. **Masters 07/08, 2026-10-30.** V2 files were written beside V1 on the office Mac; V1 is unchanged. The register points at V2.
8. **Tests changed by approved decisions.** Unlock-withdraws-sign-off became never-unlock (decision 5); supplier ordering tests record an Early Procurement Exception (decision 6); schedule-move tests send the drafted delivery change (decision 4); scope tests count selected work (decision 4); schema tests exclude columns added by later migrations.
