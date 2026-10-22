# Supplier Pro — storybook economics addendum (model version 2)

| Attribute | Value |
|-----------|--------|
| Status | **BUILT ON BRANCH, NOT DEPLOYED** — `feature/supplier-storybook-editions`. Awaiting Joel's review; no release authorized. |
| Date | 2026-10-22 |
| Amends | [supplier-pro-operational-roi-addendum-v1.md](supplier-pro-operational-roi-addendum-v1.md) |
| Effect | Adds two outputs to the existing supplier economic model at `/supplier-program/economic-model`. |
| Not this record | A second calculator, a supplier-specific calculator, a price, or a measured result. |

## Why

Joel's two-edition storybook brief (BMR Winchester and Kemptville Home Hardware Building Centre, 22 Oct 2026) asks both books to use the same existing Supplier Economics Calculator, with these outputs:

| Brief output | Model result |
|---|---|
| Incremental material gross-profit opportunity | `commercial_value` (existing) |
| Supplier takeoff / quoting capacity recovered | `hours_released`, `takeoff_labour_value`, `additional_quote_capacity`, `capacity_value` (existing) |
| Capacity recovered on unsuccessful quotes | **new** `takeoff_labour_value_unsuccessful_quotes` (with `takeoff_labour_value_won_quotes`) |
| Potential missed material opportunities | **new** `missed_opportunity_value` |
| Supplier sponsorship costs | `program_cost` (existing; base platform cost + active contractor cost), labelled "Sponsorship and program cost" on the page |
| Net program economics | `net_supplier_value` (existing) and **new** `net_supplier_value_with_missed_opportunity` |

## New inputs

| Field | Label | Rule |
|---|---|---|
| `unpriced_requested_value` | Requested material value not priced, per year | Zero or more; blank leaves the missed result not established |
| `missed_capture_percent` | Share of unpriced requests the supplier could capture | 0 to 100 |

## Formulas

- Won / unsuccessful split: `takeoff_labour_value × conversion` and `takeoff_labour_value × (1 − conversion)`. It divides the same value; it is never added to operational or net value again.
- Missed-material opportunity (gross profit): `unpriced_requested_value × missed_capture_percent × material_gross_margin_percent`. `actual_sales` is false.
- Net including the missed opportunity: `net_supplier_value + missed_opportunity_value`. The existing net is unchanged.

Known and estimated classification carries through exactly as before. Every result is a calculation from typed assumptions; measured results come only from the supplier's own Dashboard and Material demand pages.

## Storybooks

The screen storybooks (BMR Winchester and KBC editions) carry a browser copy of these same formulas in the shared storybook engine (`docs/storybook/supplier-editions/src/deck.py`), with the same field names, so a supplier can try numbers without signing in. The storybook build's `docs/storybook/supplier-editions/src/verify_model.py` runs the Python model and the browser copy on the same inputs and requires identical results (22 Oct 2026: 6 cases × 14 results, identical, for all three books). No URL to the office page is printed in either book.

## Tests

`tests/test_supplier_economic_model.py`: 6 new tests (21 total), all passing on 22 Oct 2026.
