# Supplier Unit Pricing & Conversion

| Attribute | Value |
|---|---|
| Status | **Implemented, tested and browser-verified on branch `feature/supplier-unit-pricing-2026-10-29` (from `main` `ed3ff7d6`). NOT DEPLOYED — held for a separate release.** |
| Governing rule (Joel, 29 Oct 2026) | Calibrayt accepts construction requirements in the units produced by estimating/takeoff and supplier pricing in the units used by the supplier/POS. **Calibrayt owns the governed conversion between those units.** |
| Migration | **None.** Requests and quotes are JSON on the existing `supplier_request_shares` row; a new `source_kind` value `UNIT_PRICING` (not constrained by the schema). |
| Builds on | The Supplier Pricing Request form and template library (`app/services/supplier_pricing_request_form.py`, `app/services/supplier_pricing_templates.py`), the Supplier Connection request workflow (`app/services/supplier_hub.py`) and the production CaliSIGN purchase-order signing (`app/services/supplier_signing.py`). No competing system. |

## 1. The workflow

```
Takeoff measurements (SF, LF)                 office: Project → Supplier requests → Price a package
  → components and requirements               template library (schema 2), app/services/unit_pricing.requirement_lines
  → Supplier Pricing Request                  SupplierRequestShare (MATERIAL, source UNIT_PRICING) — Supplier Hub, or the
                                               approved PDF form for a store with no sign-in
  → the supplier prices each component        in its own sell/POS unit (sheet, 12 ft piece, LF, box, tube…)
  → governed conversion + rounding            unit_pricing.price_package: whole purchasing units, always up
  → line extensions and package price         group totals, subtotal, HST 13 %, total
  → contractor review                         missing conversions shown and blocking; record one (with its source)
                                               or take the line out (with a reason)
  → Approve                                   unit_pricing.approve: lines, quantities, prices and total fixed
  → Purchase Order                            supplier_hub.place_order → order_lines → the approved package
  → existing production CaliSIGN              Sign & Send for E-Signature → the store's Sign & Confirm Order → Executed
```

**Placement (decided from the architecture, not a new place):** the Supplier Connection workflow already lives on the
project's **Supplier requests** page (`/projects/<id>/supplier-requests`): requests go out from there, quotes come back
there, the contractor approves there and places the purchase order there with CaliSIGN. The unit-pricing request is a
third kind of request on that page ("Price a package from the template library"), beside deck/framing material
requests and concrete; in the Supplier Hub it is one more request in the store's inbox.

## 2. Units and conversion

- **Requirement** — per component, in takeoff units: `measure × (1 + waste)` (SF, LF), a fixed count (a kit), or the
  count of pieces it fastens (`pieces_of`, e.g. 61 sheets + 121 battens = 182 PC fastened). Shown with its basis
  ("1,750 SF + 10% waste").
- **Sell units** — each template item lists the units it may be sold in and, for each, its conversion **only where a
  verified basis exists** (the product's own stated size: "4 ft x 8 ft sheet = 32 SF", "12 ft piece = 12 LF"). The
  requirement's own unit is always offered (priced per SF or per LF: 1 = 1). A supplier may also name another unit.
- **Which conversion is used** (most specific first): one the contractor recorded for that line and unit (with its
  source, who and when) → one the supplier stated on its quote → the template's product size → the same unit as the
  requirement. Each is shown with its source on every screen.
- **Purchasing-unit rounding** — a sell unit is not split: `ceil(requirement / per)` (1,925 SF / 32 = 60.16 → 61 sheets;
  1,444.3 LF priced per LF → 1,445 LF). Six decimal places absorb arithmetic noise only (3,520 / 32 = 110 stays 110).
- **Supplier quantity** — where no conversion is known the supplier may state the whole quantity it would supply.
- **Money** — Decimal throughout; extensions rounded half-up to the cent; HST 13 % on the package subtotal.

## 3. Missing product data is never guessed

A line priced in a unit with no known conversion and no supplier quantity has **no quantity and no extension**, says
what is missing ("How many PC fastened one BOX covers is not known (no verified product data)"), and **blocks approval
and the purchase order**. It is resolved only by a person: the contractor records the conversion with its source, the
supplier states its quantity or conversion, or the contractor takes the line out of the order with a reason. The PDF
form leaves such a quantity blank with "quantity to confirm".

**Hardie acceptance scenario.** The template-library v1 (`hardie-vertical-aluminum-v1`) carried three box ratios
(nails per 25 sheets, aluminum nails per 40 pieces, fasteners per 14 soffit panels) and a sealant coverage (25 LF per
tube) that were not verified product data. **v2 (`hardie-vertical-aluminum-v2`) removes them**: Hardie siding nails,
aluminum trim nails and soffit/fascia fasteners are boxes with "pieces fastened per box: no verified product data", and
sealant tubes have "LF sealed per tube: depends on the bead; no verified product data". v1 is marked `superseded`:
not offered, still loadable so the 29 Oct 2026 forms stay reproducible. Every other v2 conversion is the product's
stated size, and reproduces the 29 Oct quantities exactly (61, 121, 22, 1, 28, 29, 14, 19, 11, 8, 12, 29).

## 4. What each side sees

- **Office** (Supplier requests): the request table (requirement, Calibrayt quantity, conversion or "Not set"); the
  approved PDF form; for a store without a sign-in, "Enter the prices the supplier returned"; after the return, the
  priced table (requirement, priced per, conversion and its source, exact → rounded quantity, unit price, extension,
  status), group totals, subtotal, HST, total; what blocks approval; per missing line "Record the conversion" (value +
  source required) and "Do not order this line" (reason required); Approve; then the existing order form with
  CaliSIGN.
- **Supplier Hub**: the request (no customer, job name or address — only the shared fields, as every request), the
  price form (unit, unit price, SKU, and only where not known its quantity or coverage), then the same priced
  calculation read-only. Another store never sees it.
- After approval the prices and conversions are fixed; a revised takeoff for the same supplier and template replaces
  the open request.

## 5. Code

| Part | File |
|---|---|
| Conversion engine, request, prices, review, approval, order lines, PDF data | `app/services/unit_pricing.py` |
| Hardie v2 template (schema 2); v1 superseded | `app/data/supplier_pricing_templates/hardie-vertical-aluminum-v2.json`, `…-v1.json` |
| Library: superseded templates not listed | `app/services/supplier_pricing_templates.py` |
| Order lines dispatch | `app/services/supplier_hub.py` `order_lines` |
| Office routes | `app/routes/supplier_office.py` (`create_unit_pricing`, `unit_pricing_form`, `unit_pricing_prices`, `unit_pricing_conversion`, `unit_pricing_exclude`, `unit_pricing_approve`) |
| Supplier Hub | `app/routes/supplier_portal.py` (`request_detail`, `return_quote`) |
| Screens | `app/templates/suppliers/_unit_pricing.html`, `suppliers/project_requests.html`, `supplier/request.html` |
| Tests | `tests/test_supplier_unit_pricing.py`, `tests/test_supplier_pricing_templates.py` |
| Browser walk (in the release gate) | `tools/release/evidence_unit_pricing.mjs`, `tests/unit_pricing_page_server.py` |

## 6. Not in scope (kept for Joel's walk-through with Kevin, 30 Oct 2026)

Unchanged: the mixed "stage" / "work item" terminology; office terminology on contractor screens; the two
project-creation paths; the separate Estimate / Internal Cost / Pricing / Proposal pages.
