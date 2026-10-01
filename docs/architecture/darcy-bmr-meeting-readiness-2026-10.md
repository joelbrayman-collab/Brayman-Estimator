# Darcy / BMR Winchester — meeting readiness

| Attribute | Value |
|-----------|--------|
| Status | **RECORDED.** Meeting package. Not a new product and not a new economic model. |
| Date | 2026-10-01 |
| Meeting | Next two weeks. 30–45 minutes. The calendar date is not set in this record. |
| Audience | Darcy at BMR Winchester. BMR is the pilot context. It is not hard-coded into the model. |
| Live economic page | `/supplier-program/economic-model` on `https://calibryatai.onrender.com`. Product SHA `c6aa88a05ed91492160664b2ba110ba6c07adba0`. Deploy `dep-dav8ul7pn0mc739lhfmg`. |
| Authority | [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md) · [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) · [supplier-pro-operational-roi-addendum-v1.md](supplier-pro-operational-roi-addendum-v1.md) · [supplier-pro-platform-partnership-v1.md](supplier-pro-platform-partnership-v1.md) |

This record prepares one meeting. It does not authorize Supplier Pro, a supplier dashboard, a live BMR connection, or a change to the economic model.

---

## Objective

Show enough CalibraytAI to establish credibility, then spend most of the meeting on Darcy’s own operating numbers.

Do not tour the platform.

Opening line:

“We don’t want to spend the meeting giving you a software tour. We want to show enough of the technology to understand the opportunity, then use your numbers to see what the economics actually look like.”

Supplier message:

“We don’t want to replace BMR’s pricing system. We want to feed it better information.”

CalibraytAI determines what is required. BMR prices, validates, and fulfils. The contractor reviews, approves, and signs. BMR’s cost and operating platform stays BMR’s authority.

The longer path is project and plans, then governed intelligence, then the right calculation, then a structured result, an estimate, a material requirement, a supplier transaction, fulfilment, field feedback, and learning. This meeting shows only a small part of that path. CalibraytAI is not presented as a set of calculators.

---

## Clock

| Minutes | What happens |
|---------|----------------|
| 0–5 | Business context. Use the opening line. No tour. |
| 5–12 | Technology proof on one thickened-edge concrete story. |
| 12–15 | Supplier transaction concept. Name the boundary. Do not pretend a live BMR connection. |
| 15–35 | Darcy enters his numbers on the live economic page. Do not type CalibraytAI assumptions for him. |
| 35–40 | Ask which of his numbers a pilot would have to prove. |
| 40–45 | Next step. If he wants a deeper product review, book a separate 2–3 hour working session. |

---

## Target story

One contractor project. Preferred subject: a thickened-edge concrete slab.

The story to tell:

PDF, upload, CalibraytAI interpretation and takeoff, contractor review, estimate, structured concrete requirement, BMR pricing and confirmation, order, delivery schedule, contractor approval and digital sign-off, a field change, an iPhone delivery-change request, BMR primary and backup notification, BMR acknowledgement, and an updated delivery schedule.

That is the target story. It is not a claim that every step is live.

---

## What the technology minutes may show

About 5–7 minutes. The question those minutes answer is what CalibraytAI does for a contractor and a supplier.

1. **Calculation.** The public thickened-edge concrete calculation is closed on the Website. Authority is `lib/calculation-engine/concrete-slab.ts` in the Website repository. Website SHA `5dcb4f2b9cc0a291a16375f06ce89f09a02262cf`. The formula is not copied into this repository. Platform workflow use of that formula is **BLOCKED — DEPENDENCY IDENTIFIED**.

2. **Contractor review.** The office mapper adds an estimate line only after confirmation. A 1 Oct 2026 live walk showed nothing added before confirmation. After an explicit confirm, line 135 held 9.45 m3. That walk proves the gate. It does not prove the office calculates the slab.

3. **Structured requirement.** FG-029 is **CLOSED / OPERATIONAL FOR UAT**. The office can hold a material requirement, a human supplier mapping, and a frozen HTML and PDF package. Delivery stage on that package is a human label. The bounded demo is synthetic project 14, `FG029-UAT-BMR-DEMO`. It is not a live BMR account. Say the DEMO / SYNTHETIC banner out loud if that package is opened.

Plan upload and sheet review exist. Do not say a PDF is interpreted into a takeoff by itself.

---

## Supplier transaction minutes

Draw this chain and stop at the live boundary:

Contractor → CalibraytAI → material requirement → BMR → price → order → delivery.

Live today: the contractor side can produce a reviewed quantity and a supplier-facing HTML/PDF package.

Not live, and not to be acted out as if it were:

- a BMR login
- a BMR price or inventory feed
- an electronic order
- a delivery booking
- a BMR acknowledgement
- primary and backup supplier notification

Say that the next stage is the connection into BMR’s own pricing and fulfilment system. BMR remains the authority for price and fulfilment.

---

## iPhone and field change

Field capture on the phone exists. FG-020 field evidence is **CLOSED / OPERATIONAL FOR UAT**. FG-021 Field Web is closed for UAT, with session-expiry recovery still deferred. FG-033 contract signing is **CLOSED / OPERATIONAL FOR UAT**. Real iPhone signing UAT is deferred.

Those surfaces are not a BMR delivery-change request. They do not notify a primary and a backup supplier contact. They do not record a BMR acknowledgement. They do not update a BMR delivery schedule.

If the phone is shown, show a field capture and say the supplier notification is the next stage. Do not play a notification or an acknowledgement that the software did not send.

---

## Economic model

Open `/supplier-program/economic-model` with empty fields.

Darcy supplies, as he has them:

- active PRO / eligible contractor accounts
- takeoff requests per month
- manual hours per takeoff
- fully loaded estimator cost per hour
- CalibraytAI takeoff share
- validation hours per takeoff
- average estimator hours per quote
- incremental contribution per additional quote, or leave it blank
- average material value
- quote-to-order conversion
- material gross margin
- base platform cost and active contractor cost, as annual amounts he enters

Each input is Known or Estimated. Estimated must stay visibly estimated.

Keep three results separate:

- takeoff labour value
- capacity value
- commercial value

If he has no contribution per extra quote, leave that field blank. Hours released and quote capacity may still show. No dollar capacity value is invented. Do not put BMR sample numbers in the form before he speaks.

Eligible contractor accounts are context. They do not calculate the takeoff volume.

---

## Questions for the assumption check

Ask which of his entries are from BMR’s own records and which are estimates.

Ask what a pilot would need to measure before an estimate could be treated as known. In particular: monthly takeoff volume, manual hours, validation hours, the share of takeoffs that would start in CalibraytAI, and whether an extra quote has a contribution he is willing to state.

Do not fill a blank with a CalibraytAI number.

---

## Known limitations

Say these in the meeting. Do not smooth them over.

- The platform does not run the thickened-edge formula. That calculation is the public Website tool.
- A PDF is not automatically turned into a takeoff.
- The supplier package is a structured document. It is not a live BMR integration.
- There is no supplier portal login for Darcy in this meeting. FG-030 is recorded and not authorized.
- There is no electronic order, no live price feed, and no inventory feed.
- Delivery stage on the package is a label. It is not a booked delivery.
- The phone can capture field information. It does not send a BMR delivery-change request or receive an acknowledgement.
- Contract signing is a contractor document ceremony. It is not BMR confirming a delivery.
- The economic page does not store Darcy’s numbers and does not contain BMR defaults.
- Supplier Pro, the sponsorship layer, and the ROI dashboard are not built.
- Controlled demo data is labeled. Synthetic project 14 is not BMR’s business.

---

## Backup

If the office, the phone, or the network fails, use screenshots or one recording of the same three surfaces:

1. The Website thickened-edge concrete result.
2. The office confirmation gate and the supplier package, including the DEMO / SYNTHETIC banner.
3. The economic page, empty, then one worked example that is clearly marked as an illustration and not BMR’s numbers.

That backup is not in the repository yet. Do not invent a recording. Capture it before the freeze, from the same path this record allows.

---

## 48-hour freeze

The freeze starts 48 hours before the meeting, once the meeting date is set.

During the freeze, no non-essential change to:

- the demo project
- the calculation used in the demo
- the supplier economic model
- the iPhone path that will be shown
- the platform routes that will be shown

After the freeze starts, only a critical defect repair that would break the meeting is permitted.

This record does not start the freeze. The date is not set.

---

## Success

The meeting works if Darcy can say what CalibraytAI does, has seen a credible contractor-to-supplier boundary, has seen the phone as a field-capture idea without a fake supplier notification, has entered his own numbers, has seen labour value, capacity value, and commercial value kept apart, has named which assumptions a pilot must prove, and there is enough interest for a longer technical or pilot discussion.

The meeting does not require the rest of the platform to be finished.

---

## What this record does not change

Supplier Pro stays **NOT STARTED**. The economic page stays the existing model. No second calculator is created. No BMR value is written into the product.
