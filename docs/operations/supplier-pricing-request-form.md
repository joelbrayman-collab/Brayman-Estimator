# Supplier Pricing Request form — the approved request-for-estimate template (28 Oct 2026)

Joel approved the fillable Supplier Pricing Request (dark Brayman and CalibraytAI logos on the navy header) on
28 Oct 2026: "DO NOT change the form or calculations", "use the approved branding logo's from the repo", and enter
it in the repository "as the request for estimate template". Then: "blank master so the important fields can be
filled ... not only values but contact info for the supplier", "yes fillable boxes", "The form should be filled by
the workflow if a supplier is chosen."

| Piece | Where |
|---|---|
| The form, drawn from data | `app/services/supplier_pricing_request_form.py` — `render_supplier_pricing_request_form(request)` |
| The blank master | `render_blank_supplier_pricing_request_form()`; `tools/documents/supplier_pricing_request_form.py --blank OUT.pdf` |
| Filled when a supplier is chosen | `request_for_supplier_account(account, project=..., items=..., groups=..., requested=...)`: supplier name and branch from the supplier account, the contact from the supplier's Supplier Hub user |
| Logos | `app/static/branding/brayman-construction-logo-dark.png`, `calibraytai-logo-v1-dark.png` (the approved dark variants; no white plate) |
| Tests | `tests/test_supplier_pricing_request_form.py` (the approved 49 fields in the approved places, the approved text, the calculation, the contact, the blank master, more than ten items) |

Unchanged from the approved form: page size, colours (navy #1F3A5F, gold #C79A2B, muted #5B6877, panel #F4F6F8,
rule #B9C4CF), Helvetica, every position, every field name and box, the calculation (quantity x Ben unit cost,
subtotal, HST 13 %, total, the page-2 summary and group totals, Prepared by and Quote # copied to page 2).

Additions approved by Joel: the supplier's contact (name · phone, then email) in small grey type under the
supplier's name on both pages, only when there is a contact; the blank master (header values, items, Calibrayt
quantities and units as fillable boxes; group totals typed by hand). More than ten items continue on a further page
of the same table, with the totals after the last item; the summary takes one to four groups.

Not changed: the supplier response request that Field material requests and the takeoffs send through the Supplier
Hub (`brayman_supplier_estimate.render_supplier_response_request`), whose returned PDF CalibraytAI reads back. Which
workflow screens offer this form is Joel's decision.

Real job files (the approved filled PDF, the Paulusse/Lockwood takeoff) stay outside Git.
