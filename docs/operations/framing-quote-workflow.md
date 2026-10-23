# Framing quote workflow (materials and labour)

Branch: feature/framing-quote-workflow-20261023. Not released.

## What a person does now
| Task | Before | After |
|---|---|---|
| Ask a supplier to price the framing materials of a straight wall | Download the PDF, email it, wait, key the answer in | Estimate framing page: choose supplier, click **Request framing quote** (2 clicks after the count) |
| Ask a supplier to price the deck takeoff | Issue the PDF, go to Supplier requests, pick it, send (4+ clicks) | Deck takeoff: **Request framing quote** (1 click, supplier already chosen) |
| Ask a subcontractor for a labour price | No sheet existed; free-form email | Scope Delivery Review: **Labour quote request sheet** (1 click), print or save as PDF |

## Reused (not rebuilt)
- Supplier request PDF, stored manifest, Supplier Hub share, supplier price return, price evidence: deck takeoff services (`build_request`, `storage`, `supplier_hub.send_material_request`, `return_material_quote`). Only `source_kind` was generalised (`FRAMING_FORM2`), no migration.
- Wall framing count and purchase: `wall_framing`, `wall_framing_purchasing`. No quantity rule added.
- Labour quote receipt/select/reject: existing Scope Delivery routes. Unchanged.

## Not built, needs an owner decision
- **Use this quote in the estimate** (price evidence or selected labour quote becoming an estimate line cost). Today the platform states deliberately that evidence "does not set cost" and cost needs Brayman approval (ADR-036, FG-031). Doing it in one click changes that pricing contract. Not done.
- **Multi-supplier comparison**: no prior work found; not started.
- `estimating_handoff.subcontract_request_from_project` exists but needs a plan-intelligence result, not an estimate; the sheet above is built from the estimate lines instead.

## Link point
The permit lookup (address from Start New Project) is untouched; a "next: framing quote" step can link after it.

## Training lesson steps (do not edit training branch yet)
1. Count the wall. 2. Choose the supplier and click Request framing quote. 3. Supplier prices it in Supplier Hub. 4. Review the returned prices on the response page. 5. For labour: Scope Delivery Review, print the labour quote request sheet, record the returned quote.
