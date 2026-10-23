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

## Suggested cost from a returned quote (owner decision A)
- A selected labour quote suggests a unit cost (quote amount / line quantity). An approved supplier cost suggests the unit cost of its canonical material. Both show on the Scope Delivery Review line as "Suggested cost", with "Working cost differs from this quote" when they differ.
- Nothing changes until a person clicks **Use this cost on the line**. Labour: sets the line's unit cost and records who, when and the prior unit cost in the line's own override provenance; **Undo** restores the prior cost. Materials use the existing `consume_approved_contractor_cost` (checks and costing freeze unchanged).
- Existing safeguards kept: selecting a quote still does not set cost; humans only (AI refused); locked or non-draft versions refuse; applying a cost makes the costing snapshot stale, so costing is re-approved before pricing.
- No migration: the audit trail is the line's override fields; no table or column added.

## Multi-supplier comparison
Read-only **Compare quotes** page (project supplier requests): returned quotes side by side per line, lowest net unit cost marked, priced total per supplier. Records and approves nothing.

## Click counts (counted from the screens, not a timed walk)
| Task | Before | After |
|---|---|---|
| Framing materials quote to a supplier | 7 (download, email, wait, key in) | 2 (supplier, Request) |
| Deck takeoff to supplier | 5 | 1 |
| Labour quote request | no sheet | 1 |
| Quote cost onto the estimate line | re-key by hand | 1 confirm (1 undo) |
| Compare suppliers | separate pages, by eye | 1 |

## Link point
The permit lookup (address from Start New Project) is untouched; a "next: framing quote" step can link after it.

## Training lesson steps (do not edit training branch yet)
1. Count the wall. 2. Choose the supplier and click Request framing quote. 3. Supplier prices it in Supplier Hub. 4. Review the returned prices on the response page. 5. For labour: Scope Delivery Review, print the labour quote request sheet, record the returned quote.
