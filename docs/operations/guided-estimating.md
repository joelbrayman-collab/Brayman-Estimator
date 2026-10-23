# Guided Project Estimating & Universal Calculator Integration (V1, 23 Oct 2026)

Branch `v1/guided-estimating-2026-10-23`, built on the pinned v1rel8 candidate `6adf757` plus the framing quote
workflow (`e1c4b58`, Pricing Decision A). One additive migration: `g5e7c2a9d1b4` (follows `u7b3d9f2a4c6`).

## What it connects (no second engine, store or work structure)

| Step | Existing service it uses |
| --- | --- |
| Start New Estimate (Home), New Project with project type and contractor role | New Project form, commercial context (type pre-filled, editable) |
| Construction scope: Internal • Subcontracted • N/A per stage and part | `guided_estimate_stages` (orchestration only) |
| Each included stage or part = one estimate section | `EstimateSection` on the project's estimate |
| Internal stage: calculator, review, labour | calculator pages with project/stage chosen → `project_calculations` → Contract V1 calculation intake → a person confirms each quantity (`confirm_quantity_mapping`); labour hours (`estimate_labour_hours`, approved company rate); governed manual lines (`add_manual_line`) |
| Subcontracted stage: scope, request, record, compare, select, use cost | subcontract quote evidence (`receive_quote`, `select_quote`), printable labour quote request sheet, framing quote request, Pricing Decision A (`apply_labour_suggestion` with undo and who/when) |
| Who supplies and builds each line | scope-delivery routing, confirmed by a person (`save_scope_delivery` + `confirm_scope_delivery`) |
| Complete | only with confirmed costs, an approved allowance (an ordinary Allowance line) or an authorized no-cost decision |
| Internal cost estimate (HTML and PDF), marked INTERNAL — NOT FOR CUSTOMER DISTRIBUTION | read-only view of the estimate's own lines and evidence; ReportLab |
| Review Pricing & Prepare Proposal | costing approval, pricing engine (true gross margin, HST), proposal creation; proposal issue refused while a guided stage is unresolved |
| Revisions | `clone_current_version` (issued/locked versions untouched), version comparison by stage |
| Into the build | the existing work-structure seed turns the stage sections and their labour lines into the project's work items |

Every calculator (platform, Useful Calculators on the iPhone, from a guided stage) offers after a result:
**Use Result Only**, **Add to Existing Project** (the existing "Link to a project" record, now carrying the Contract V1
result and an optional stage; never doubled) and **Create New Project** (`calculator_result_carries`; Cancel returns
to the calculator with the same result). Field-only crew see the result only.

## Database (one migration, `g5e7c2a9d1b4`)

New tables: `guided_estimates`, `guided_estimate_stages`, `guided_estimate_events`, `calculator_result_carries`.
New nullable columns on `project_calculations`: `result_id`, `engine_id`, `engine_version`, `payload`, `source`,
`guided_stage_id`, `review_status`, `estimate_version_id`, `calculation_result_intake_id`, `sent_to_review_at`,
`sent_to_review_by`. Existing rows unchanged (NULL in the new columns). Downgrade refuses while any of it is used.
Release gate: `--migration-to g5e7c2a9d1b4 --new-tables guided_estimates,guided_estimate_stages,guided_estimate_events,calculator_result_carries --altered-tables project_calculations`.

## Decisions for Joel (nothing below was changed without him)

1. **Allowance and no-cost authority** uses the existing costing-approval authority (the signed-in approver), not a
   new permission. A stricter owner-only rule would be a permission change.
2. **Proposal issue** of a guided estimate now also waits for every included stage (brief section 9); non-guided
   estimates are unchanged.
3. **Labour-rate notes**: the existing labour-hours lines carried the company labour rate in their notes, which the
   customer proposal printed. Those provenance notes (and the guided manual-line note) are now treated like the other
   platform provenance notes and kept off customer documents. Typed notes are still shown.
4. **Revisions re-confirm routing**: a cloned version's lines need "who supplies and builds" confirmed again
   (existing clone rule); guided stages show Needs Review until then.
5. **Stairs** has no material quantities (it checks a stair design), so its result is kept on the project as a
   record and the stair materials are entered as lines.
6. **Kevin's Contractor Review** uses an office (not Field-only) training account, like Olivia's; his Field Crew
   pathway uses his Field account.
