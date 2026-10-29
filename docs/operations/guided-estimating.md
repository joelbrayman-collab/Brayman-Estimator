# Guided Project Estimating & Universal Calculator Integration (V1, 23 Oct 2026)

> **Superseded in part (28 Oct 2026, live 29 Oct 2026):** new estimates use selected-work estimating (Approach B,
> [../architecture/selected-work-estimating.md](../architecture/selected-work-estimating.md)): the scope is only the
> work chosen on **What work are we doing?**, Internal or Subcontracted, with no stage template and no N/A. The
> "Construction scope … N/A per stage" row below describes estimates made before that release. Training module 13
> and its screenshots were reconciled to selected work on 29 Oct 2026.

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

## Decisions (approved by Joel 24 Oct 2026)

1. **Allowances and no-cost decisions.** An authorized costing approver (the signed-in person with the existing
   costing-approval authority) may approve a documented allowance: the amount, a description and a required reason;
   who approved it, when and why are kept in the stage history (`ALLOWANCE_APPROVED` event) and shown on the stage.
   An **explicit zero-cost decision for included work** needs the **instance owner or a System Administrator** (the
   existing delegated equivalent authority, `instance_authority`). Anyone else sees "Only the owner or a System
   Administrator can decide that included work has no cost …" instead of the form, and the service refuses it
   whatever sends it. Field-only crew never reach the stage pages. Tests: `tests/test_guided_owner_decisions_20261024.py`.
2. **Proposal issue** of a guided estimate waits while any included stage has unresolved costing, quotation or scope
   requirements: costing missing, a quote waiting, a quote selected but not used on the line, a stage changed after
   it was completed (Needs Review), or the scope not finalized (an undecided stage). Non-guided estimates are
   unchanged. Tests: the same file.
3. **Internal labour rates and internal costing notes never reach a customer document** (proposal page and PDF, the
   customer's proposal link and PDF, the generated contract, the change order PDF that is also sent for signature;
   the PRO Desk quotation is drawn from its frozen issued record, which carries no contractor notes). The platform's
   provenance notes (labour rate, approved cost, calculator hand-off, guided manual line, guided allowance approval)
   and any note that mentions rates, wages, costs, margin, markup, overhead or supplier/wholesale prices stay on the
   estimate line (the internal costing record and the internal cost estimate) and are left off. A note written for
   the customer is still shown. A change order priced from direct cost or carrying a markup lists its lines without
   internal unit prices and shows one price before tax. Test: `tests/test_customer_documents_no_internal_costing_20261024.py`.
4. **Revisions re-confirm routing**: a cloned version's lines need "who supplies and builds" confirmed again
   (existing clone rule); guided stages show Needs Review until then.
5. **Stairs** has no material quantities (the stair calculator checks a stair design), so its result is kept on the
   project as a record and the stair materials are entered as the governed manual material-cost lines. No stair
   material list is invented.
6. **Kevin's Contractor Review** uses an office (not Field-only) training account, like Olivia's; his Field Crew
   pathway uses his Field account.
7. **Supplier training for training administrators** (training site only): see `docs/operations/training-site.md`,
   "Supplier practice login".
