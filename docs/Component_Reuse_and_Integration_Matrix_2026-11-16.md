# AI Estimating Assistant — Component Reuse and Integration Matrix
Date 2026-11-16. Source: repository at the deployed version (read in full for the files named; line numbers are as of this copy).

## Verdict on the architecture
The architecture in the directive holds. Everything the assistant must do already exists as a deterministic service; **no LLM call exists anywhere in the app today** (`openai` is pinned in requirements.txt but unused), so the assistant is a thin orchestration layer over existing services, not a new engine. Four things are genuinely new: (1) a QUOTATION CaliSIGN document family (needs a migration), (2) a per-project Sync export queue, (3) the orchestration/intake layer, (4) cost-library entries for items the calculators emit but the library lacks. Everything else is reuse or a small extension.

## Matrix
| # | Requirement | Existing component (source) | Decision | What changes |
|---|---|---|---|---|
| A1 | Quantities from calculators | `services/calculation_result_contract.py`, `calculator_contracts.py`, `icf_quantity.py`, `foundation_quantity.py`, `foundation_handoff.py`; `plan_intelligence/takeoff.py` (no external AI) | Reuse | None |
| A2 | Calculator result to estimate line | `services/calculation_estimate_mapping.py`: `ingest_contract_result` (222), `_suggest` (184), `confirm_quantity_mapping` (505), `defer_labour_quantity` (623) | Reuse + data | `_suggest` only auto-maps when exactly one active CostItem/Assembly has the same code and canonical unit. Doxey needed hand-entered lines because the library lacks entries. Add the missing library items (B1) so mapping resolves automatically |
| B1 | Missing cost-library items | `CostItem` / `Assembly` models; library screens | Data work | Seed items with approved provisional prices (Milne historical, labelled); no code change |
| B2 | Calculator-to-cost-line workflow | `guided_estimating.py`: `stage_action` (406) add_cost, complete_next, set_aside; scope routing at `/projects/<id>/scope-delivery` | Reuse | Orchestration calls these in order; no new route logic |
| B3 | Wall height / two-stage pour rule (>10 ft = 2 stages, 2 pumps) | Not present. `foundation_quantity.py` takes a single height | Extend | Add per-run deep/shallow length split and rule output (extra pump line, pour labour). Pure function with tests |
| B4 | Labour rate and margin changes without justification | `estimate_economics.py` `set_project_pricing`; route `estimates.py` `update_project_pricing` | Done (patch ready) | Reason optional; refusal message visible. 82 tests pass here |
| C1 | Consolidated internal cost review | `guided_estimating.py` `internal_cost` (503) and `internal_cost_pdf` (511); templates in `templates/guided/` | Reuse | Add the assumptions and quantity report block to this page; no new engine |
| C2 | First approval (costing) | `estimate_costing.py` `approve_all_costing` (501); gate in `guided_tasks.approve_estimate`; immutable `EstimateApproval` in `estimate_approval.py` (`record_approval` 88, `create_successor_version` 143) | Reuse | None. Approval stays human (`assert_human_actor`) |
| C3 | Pricing application | `pricing_engine.py` `apply_resolved_pricing_to_version`, `estimate_economics.py` `set_project_pricing` | Reuse | None |
| D1 | Quotation snapshot | `proposals.py` `build_proposal_snapshot` (258); `proposal_pdf.py`; branded template 07 | Reuse | None |
| D2 | Second, separate approval before sending | `internal_approval.py` (`send_for_internal_approval` 343, `freeze_revision` 258) is the existing two-step pattern for the internal financial summary | Extend | Reuse the same pattern for the quotation: Ben/Joel approve the quotation as a document, separately from the cost approval |
| D3 | QUOTATION CaliSIGN document family | `models/signing.py` lines 24-30: families CHANGE_ORDER, CONTRACT, SUPPLIER_ORDER, SUPPLIER_DELIVERY_CHANGE, SUBCONTRACT, INTERNAL_APPROVAL; `DOCUMENT_FAMILY_CHECK` constraint; `signing.py` create/approve/issue/accept (604/671/894/1075); `_require_human` (244) blocks AI and automation | **New (migration)** | Add QUOTATION to the constant and CHECK constraint; migration reviewed and approved by you (AGENTS.md rule); existing families untouched |
| D4 | Authorized email send, approved recipients only | `signing_mail.py` (165, 188), `transactional_email.py` (allowlist at 122: `TRANSACTIONAL_UAT_ALLOWLIST`), `email_delivery.py` (Postmark) | Reuse | Quotation uses the same path; test sends only to allow-listed addresses. Sending remains a human click |
| D5 | Click-accept to contract | `proposal_acceptance.py` (`send_proposal_to_client` 226, `sign_off_estimate` 118), `contract_generation.py` | Reuse | None |
| E1 | Sync.com export, per project | `document_storage.py` stores hashed files in `instance/documents` (1 GB Render disk). The cloud app cannot reach the Mac, and Sync is a Mac-side folder | **New** | Export queue table plus a Mac-side pull: the app lists pending exports; a small script on the Mac downloads and files them into `01 - Projects/<ID> - <Customer>/` using the approved naming, never overwriting (new revision letter), then reports status back. Retries, status and the Project Index are tracked in the queue |
| E2 | Project Index document | Built by script this session (`index.py`) from template 02 | Extend | Move into a service that regenerates the index when the queue changes |
| F1 | AI orchestration "Prepare my estimate" | None | **New** | Thin layer: reads the project and drawing, calls the calculators and routes above in order, stops at every approval. Deterministic engines do all arithmetic |
| F2 | AI model usage and cost | `openai` pinned, no usage in code | **Decision for you** | No paid API will be enabled until you approve a dollar figure (see below) |
| G | Validation with Doxey | Production Project 30 holds the real Doxey estimate | Test on Practice | Copy Doxey data to Practice; do not touch the live Production Doxey estimate |

## Costing the AI step (decision needed before any paid call)
Interpretation work is small text: reading a drawing's notes, choosing which calculator and which cost item. Rough size per estimate is 20 to 40 model calls of about 3,000 tokens in and 500 out. At current mid-tier model pricing that is on the order of $0.50 to $2 per estimate, not per month. I have not verified current prices, so I will bring the exact figure for the model chosen before writing any call to it. Until you approve, the assistant runs in a mode where every choice is a rules-based suggestion you confirm.

## Build order (each slice tested before the next)
1. B3 two-stage rule + B1 cost-library items (data and pure functions, fully testable here).
2. C1 review page additions.
3. D3 migration and QUOTATION family, then D2 and D4.
4. E1 export queue and Mac-side script.
5. F1 orchestration in rules-only mode.
6. G Doxey acceptance on Practice.

Tests: baseline run in this environment is green for the pricing suites touched (82 passed). The full suite and Practice run still happen through your release gate.
