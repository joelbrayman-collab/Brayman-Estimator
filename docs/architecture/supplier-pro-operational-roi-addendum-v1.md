# Supplier Pro — operational ROI addendum

| Attribute | Value |
|-----------|--------|
| Status | **CLOSED — LIVE VERIFIED** for the meeting surface. The dashboard is not built. |
| Date | 2026-10-01 |
| Amends | [supplier-pro-platform-partnership-v1.md](supplier-pro-platform-partnership-v1.md) |
| Effect | Adds takeoff-labour value and estimating-capacity value to the existing supplier/OEM economic model. |
| Not this record | A second calculator, a second ROI model, a dashboard, a table, or a price. |

This is an addendum. It does not create a supplier economic model. It does not replace the existing commercial direction.

The same extension is recorded in [supplier-pro-platform-partnership-v1.md](supplier-pro-platform-partnership-v1.md) under EXISTING SUPPLIER / OEM ECONOMIC MODEL — OPERATIONAL ROI EXTENSION. The two writings are one extension.

---

## Existing model location

Primary search terms, 1 Oct 2026: Darcy, BMR Winchester, BMR, supplier economics, supplier partnership, supplier OEM, supplier ROI, supplier program, supplier sponsorship, supplier licence, active contractor, material gross profit, material opportunity, supplier opportunity, supplier value, supplier assumptions, supplier model, partnership economics, economic model, takeoff economics, estimating capacity, takeoff labour, supplier connection, supplier integration, Winchester, and OEM economics. Calculator, ROI calculator, economics calculator, and supplier calculator were secondary terms only.

The existing governed model is [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md), updated 2026-08-30, with [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md), accepted the same day. It is an architecture specification. It is not a live data-entry page. It has no numeric inputs, no calculated outputs, and no commercial formulas. It lists later measurement families, including supplier take-off hours avoided, supplier review time, quote preparation time, captured material spend, and contractor adoption, and it says not to invent those formulas in that pass.

Darcy’s originated-value participation in that specification is a different subject. It has categories and no amounts. This addendum does not set those terms.

A page where Darcy’s operating numbers are entered and results render immediately is the office route `/supplier-program/economic-model`. It was not on the Website. `for-suppliers.html`, `/supplier-integration`, and `/contractor-connection` remain narrative pages. Useful tools remain Employment, Concrete, and Stair.

The office page is the first live use of this extension. It does not create a second model. It does not read contractor records and it does not store a result.

---

## Existing model purpose

The existing specification is the pre-partnership supplier-channel model. BMR Winchester is the launch and reference context. The supplier is not exclusive. A later live meeting can use Darcy’s own numbers once a modelling surface is authorized.

This addendum adds one more source of supplier value to that surface:

**Supplier takeoff labour + estimating capacity value.**

The future Supplier ROI & Opportunity Dashboard must use compatible definitions. The dashboard is not built here.

---

## No-duplicate rule

Do not create a second supplier calculator.

Do not create a second ROI model.

Do not create a second commercial model.

Do not create duplicate program-cost inputs. Keep the existing names for the base supplier platform licence, the active contractor component, the supplier platform fee, and the active contractor fee, using whichever names that calculator already governs.

Do not finalize pricing in this addendum.

If the existing calculator already has active contractors, material demand, material gross profit, a program fee, or an active contractor fee, reuse those fields.

Add a new input only when the concept is absent:

- takeoff requests
- manual takeoff hours
- fully loaded estimator cost per hour
- CalibraytAI takeoff share, where adoption is not already the same input
- validation hours per CalibraytAI takeoff
- average estimator hours per quote
- incremental contribution per additional quote

Do not duplicate equivalent inputs. Eligible contractor population, expected adopting population, and takeoff volume stay separate.

---

## What the value is measuring

Current supplier path: the contractor sends plans, a supplier employee reviews the drawings, performs the takeoff, builds the material list, prices the materials, and produces the quote.

CalibraytAI path: the contractor project and plans go through a CalibraytAI calculation, the contractor reviews the material requirements, the contractor requests supplier pricing, and the supplier receives a structured material requirement, validates or adjusts it, prices it, and quotes it.

The model does not claim that supplier estimating personnel become unnecessary.

It measures four different things:

1. direct takeoff labour value
2. estimator capacity released
3. additional quote capacity that may result
4. commercial material opportunity

---

## Governing separation

**Takeoff labour value and capacity value must remain separate.**

Do not add the same estimator hours twice.

Takeoff labour value is the direct cost comparison between manual takeoff effort and the supplier validation effort that remains.

Capacity value is the economic opportunity if those released hours support additional quote activity.

They are not interchangeable.

---

## Takeoff labour formulas

Annual takeoff volume = takeoff requests per month × 12.

CalibraytAI-originated takeoff volume = annual takeoff volume × CalibraytAI takeoff share.

Non-CalibraytAI takeoff volume = annual takeoff volume − CalibraytAI-originated takeoff volume.

Current manual takeoff hours = annual takeoff volume × average manual hours per takeoff.

That manual-hours figure describes the all-manual baseline. Savings are not claimed on the non-CalibraytAI volume.

Current manual takeoff labour cost, for the originated volume only = CalibraytAI-originated takeoff volume × average manual hours per takeoff × fully loaded estimator cost per hour.

CalibraytAI validation hours = CalibraytAI-originated takeoff volume × average supplier validation time per CalibraytAI takeoff.

CalibraytAI validation labour cost = CalibraytAI validation hours × fully loaded estimator cost per hour.

Direct takeoff labour value created = current manual takeoff labour cost for the originated volume − CalibraytAI validation labour cost.

The model must not claim savings on takeoffs that still occur manually.

Average manual hours per takeoff and average CalibraytAI validation hours per takeoff are separate inputs. Neither number is hard-coded. An example of 3.0 manual hours and 0.5 validation hours is an illustration only. It is not a default and it is not BMR data.

---

## Hours released

Manual hours avoided = CalibraytAI-originated takeoff volume × (manual hours per takeoff − validation hours per takeoff).

This is operational capacity. It is not automatically revenue.

---

## Capacity formulas

Average estimator hours per quote is a supplier-provided input.

Additional quote capacity = manual hours avoided ÷ average estimator hours per quote.

Where the supplier provides an incremental economic contribution per additional quote:

Capacity value = additional quote capacity × incremental contribution per quote.

Label that result **capacity value / economic opportunity**, not direct labour savings.

If the supplier does not provide a valid incremental contribution per quote, do not invent one. The calculator may show hours released and additional quote capacity with no dollar value.

---

## Commercial value

Keep the existing commercial chain:

Material demand → supplier opportunity → supplier quote → supplier order → captured material sales → material gross profit.

Do not create a separate commercial model.

Where material gross profit or material gross margin is an input, the supplier provides it. Do not hard-code an illustrative margin.

The live meeting page estimates commercial gross profit only when the supplier supplies average material value, quote-to-order conversion, and material gross margin:

annual takeoff volume × average material value × quote-to-order conversion × material gross margin.

That uses annual takeoff volume as the opportunity count. It is a scenario, not actual sales. A missing input leaves commercial value unestablished.

---

## Combined view

When the categories that are actually known can be shown:

Operational value = takeoff labour value + capacity value.

Commercial value = the existing material gross profit or captured commercial value.

Program cost = the existing CalibraytAI supplier program cost.

Net supplier value = operational value + commercial value − program cost.

ROI multiple = (operational value + commercial value) ÷ program cost.

If a category is unknown, do not manufacture it. Show the known category alone.

---

## Break-even

Operational break-even remainder = program cost − takeoff labour value.

That remainder is the value still required after direct takeoff labour value.

Where capacity value is supported:

Remaining economic value to break even = program cost − takeoff labour value − capacity value.

If that remainder is zero or below zero, the result is **break-even achieved**. Do not present a negative remainder as a remaining amount still owed.

Where the supplier has supplied a material gross-margin percentage, and remaining economic value is above zero:

Additional material sales required = remaining economic value to break even ÷ material gross margin percent.

This uses margin, not revenue, as the divisor. Do not treat revenue as profit.

If remaining economic value is zero or below zero, additional material sales required = 0.

If the supplier has not supplied the margin, do not calculate additional material sales.

---

## Known and estimated

Every material economic input is marked **known** or **estimated**.

An estimated input must not look like verified supplier data.

An input may later move from estimated, to known or configured, to verified.

That input-quality path is separate from commercial attribution, which may move from potential, to attributed, to verified.

Do not treat those two paths as the same dimension.

---

## Assumptions and later measurements

Before a pilot, the supplier enters assumptions.

During a pilot, operating evidence starts to accumulate.

After a pilot, measured values progressively replace assumptions.

Keep the original assumption and the later measured value. Do not overwrite the historical assumption.

The pre-partnership calculator can keep using values the user types. This record does not add a persistent supplier ROI store. Persistent potential, attributed, and verified measurement belongs to the future Supplier Pro architecture, not to this modelling surface.

---

## Darcy / BMR Winchester

The calculator must be usable in a live supplier conversation. Darcy can supply active PRO contractors, takeoff requests, manual takeoff hours, fully loaded estimator cost per hour, expected CalibraytAI takeoff share, validation time, adoption, average material value, quote-to-order conversion, material gross margin, and supplier program cost.

The model then uses those numbers.

Illustrative values must never be presented as actual BMR data. BMR Winchester remains pilot context. It is not hard-coded into the model.

---

## Dashboard compatibility

The path is:

Assumptions → pilot → measurement → proven economics → expansion.

The future Supplier ROI & Opportunity Dashboard must use compatible definitions for active contractors, projects, calculations and takeoffs, material demand, supplier opportunities, pricing requests, quotes, orders, captured material value, verified value, takeoff hours, validation hours, and hours released.

The dashboard is not built by this addendum.

The BMR PRO Hub, recorded in [supplier-pro-platform-partnership-v1.md](supplier-pro-platform-partnership-v1.md), may later send operational evidence from its Supplier Console into this same model: takeoff activity, pricing requests, quotes, orders, deliveries, captured material value, supplier activity, and contractor adoption. That evidence uses these definitions. It does not create a second economic model. The console and this meeting surface stay separate. The ROI dashboard remains a future measurement surface. Sales are not automatically attributed to CalibraytAI. POTENTIAL, ATTRIBUTED, and VERIFIED stay as recorded.
