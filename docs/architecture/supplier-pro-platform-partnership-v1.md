# Supplier Pro Platform Partnership — V1 architecture

| Attribute | Value |
|-----------|--------|
| Status | **RECORDED / NOT STARTED / NOT IMPLEMENTATION-AUTHORIZED** |
| Date | 2026-10-01 |
| Product | CalibraytAI |
| Effect on the contractor platform | None. This layer is additive. |
| First pilot context | BMR Winchester. The architecture stays supplier-neutral. BMR is not hard-coded. |
| Related | [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md) · [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) · [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) · [ADR-047](../adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) · [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) · [FG-030](../feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) · [PLATFORM_BUILD_OUT_REGISTER.md](PLATFORM_BUILD_OUT_REGISTER.md) |

This record does not change the current CalibraytAI contractor-platform architecture. It adds a supplier-commercial relationship around that platform. It does not add tables, routes, users, permissions, dashboards, transactions, or APIs.

FG-029 remains the closed contractor-office supplier-package workflow. FG-030 remains recorded and not implementation-authorized. Neither gate is this partnership.

---

## Relationship chain

```text
SUPPLIER / BANNER
→ DEALER / OWNERSHIP GROUP
→ STORE
→ SPONSORED CONTRACTOR
→ CONTRACTOR CALIBRAYTAI ORGANIZATION
→ PROJECT
```

The supplier relationship does not own the contractor organization.

The contractor retains control of:

- customers
- projects
- estimates
- proposals
- contracts
- margins
- labour rates
- profitability
- internal notes
- historical projects
- competitor supplier relationships
- other commercially sensitive information

---

## Fundamental principle

**Sponsorship must not equal data ownership or account control.**

CalibraytAI operates the platform.

The contractor owns and controls its CalibraytAI business account and its private data.

Supplier sponsorship provides entitlement and access.

Ending sponsorship does not terminate the contractor account and does not transfer ownership of that account.

The contractor must be able to move from supplier-sponsored, to another sponsor, to direct CalibraytAI, without losing its business data.

---

## V1 capability queue

These are architecture and roadmap requirements. This record does not implement them.

1. Supplier identity / hierarchy
2. Sponsorship / entitlement
3. Supplier permissions and privacy boundary
4. Material Opportunity / attribution
5. Contractor-authorized supplier transaction
6. Supplier ROI & Opportunity Dashboard
7. Dealer / multi-store reporting
8. External supplier POS / ERP / order integrations

The sequence is also the build-out register row. None of these items is closed.

---

## Supplier visibility

The default is aggregated and anonymized.

A supplier must not drill from an aggregate metric into an individual contractor’s private project unless that contractor deliberately shared that transaction.

Supplier visibility may occur in either of two ways:

- aggregated program reporting
- contractor-authorized transaction sharing

---

## Contractor-authorized transaction

Future workflow. Not implemented.

```text
REQUEST PRICING
→ SUPPLIER QUOTE
→ ACCEPT / MODIFY
→ PLACE ORDER
→ VERIFY PURCHASE
```

The contractor deliberately starts the move from private platform data to supplier-facing transactional data.

---

## Material Opportunity

Preferred attribution chain:

```text
CalibraytAI Project
→ Material Requirement
→ Supplier Opportunity
→ Quote
→ Order
```

Classifications:

| Class | Meaning |
|-------|---------|
| POTENTIAL | Demand or activity exists. It is not a claimed supplier sale. |
| ATTRIBUTED | The contractor deliberately connected that requirement to a supplier opportunity. |
| VERIFIED | A supplier-confirmed transaction matches that opportunity. |

Do not overstate causation. A supplier sales increase is not automatically attributed to CalibraytAI.

---

## Supplier ROI & Opportunity Dashboard

Future dashboard. Not implemented.

It may measure:

- sponsored contractors
- active contractors
- projects
- calculations and takeoffs
- material demand
- supplier opportunity
- pricing requests
- quotes
- orders
- captured material value
- capture rate
- uncaptured opportunity

Dashboard visibility must respect dealer and store ownership boundaries.

The dashboard is not a second economics calculator. When it is built, it must use the same definitions as the existing supplier/OEM economics calculator, including the operational addendum in [supplier-pro-operational-roi-addendum-v1.md](supplier-pro-operational-roi-addendum-v1.md). That addendum is not implemented.

---

## Dealer and store hierarchy

```text
Supplier / Banner
→ Independent Dealer / Ownership Group
→ Store
→ Sponsored Contractor
→ Contractor Project
```

A dealer that controls more than one store may see consolidated results, each store, comparisons, and the drill-down its permission allows.

One dealer must not see another dealer’s private commercial information.

Corporate and banner reporting stays dependent on permission and agreement.

---

## Multiple suppliers

A contractor may have more than one supplier relationship.

Examples:

- Lumber with Supplier A
- Concrete with Supplier B
- Roofing with Supplier C

Sponsorship by one supplier does not mean exclusivity.

This record does not implement a multi-supplier screen. It does not make the contractor organization supplier-owned.

[ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) remains the neutrality decision. BMR Winchester is the first pilot context, not the architecture.

---

## What implementation must reuse

A later implementation uses the existing platform. It does not create a second contractor account model. It does not add unrestricted supplier access to contractor membership.

Reuse:

- organization isolation
- user and membership foundation
- project, client, and location
- calculation engines
- Contract V1
- the mapper
- Cost Library
- estimates
- proposals
- change orders
- the existing Supplier Connection direction in [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md)

Contractor purchasing and the CalibraytAI channel relationship stay distinct, as ADR-033 already requires.

---

## Privacy classification

| Class | Meaning |
|-------|---------|
| PRIVATE CONTRACTOR DATA | The contractor’s business records. This is the default. It stays private. |
| AGGREGATED PROGRAM DATA | Program reporting that does not identify a contractor’s private project. |
| CONTRACTOR-AUTHORIZED TRANSACTION DATA | Data the contractor deliberately sent into a supplier transaction. |
| SUPPLIER-VERIFIED TRANSACTION DATA | A result the supplier confirms against an authorized transaction. |

Private contractor data remains private unless the contractor authorizes a transaction.

---

## Measurement before external integration

Meaningful supplier ROI can exist before a POS, ERP, or order integration.

CalibraytAI can measure adoption, activity, projects, calculations, takeoffs, material demand, potential opportunity, and opportunities the contractor deliberately submitted.

External supplier integration is a later capability. It is item 8 in the queue.

---

## EXISTING SUPPLIER / OEM ECONOMIC MODEL — OPERATIONAL ROI EXTENSION

Status: **RECORDED / NOT IMPLEMENTED** (2026-10-01). This section extends the existing model. It does not create a second supplier ROI model.

### Existing component

| Question | Record |
|----------|--------|
| Exact location | [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md), updated 2026-08-30, with [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md), accepted 2026-08-30. |
| Type | Architecture specification. Not code, not HTML, not a spreadsheet, and not a prototype. |
| Live data entry | Not present. A page that accepts operating numbers and renders results immediately was not found. |
| Deployed | No. The specification is not a product surface. |
| Audience | CalibraytAI architecture. Darcy / BMR Winchester is the launch and reference context, not an exclusive partner. |
| Darcy participation | Categories only. No percentages, fees, or contract terms. That participation is Darcy’s originated-value reward. It is not BMR’s own program ROI. |

A 1 Oct 2026 search of this repository, `Documents/CalibAi/Website`, and the live Website used Darcy, BMR Winchester, supplier economics, partnership, ROI, program, sponsorship, licence, active contractor, material gross profit, material opportunity, supplier value, assumptions, economic model, takeoff economics, estimating capacity, takeoff labour, supplier connection, supplier integration, Winchester, and OEM economics. Calculator was a secondary term only.

The live pages `https://calibai.joel-brayman.chatgpt.site/supplier-integration` and `https://calibai.joel-brayman.chatgpt.site/contractor-connection`, and the local file `Documents/CalibAi/Website/for-suppliers.html`, describe the contractor-to-supplier workflow. They do not accept operating numbers or calculate a result. Useful tools remain Employment, Concrete, and Stair.

### Existing purpose

The channel specification keeps CalibraytAI supplier-neutral, names BMR Winchester as a possible design and launch partner, and separates contractor purchasing from the CalibraytAI channel relationship. It lists later measurement families and says not to invent metric formulas, targets, or dashboards in that pass.

### Existing inputs, outputs, and formulas

The specification has no numeric inputs and no calculated outputs.

Later measurement families, still without formulas, are:

- supplier take-off and estimating hours avoided
- supplier review time
- quote preparation time
- contractor material spend captured
- project and material pipeline
- contractor adoption

Darcy participation categories, still without amounts, are originated-account referral, recurring participation on originated supplier accounts, BMR-channel participation, milestone or success fees, and strategic channel-partner economics. This extension does not set those terms and does not amend ADR-033.

### New operational inputs

Add these only where the existing model does not already have the concept:

- takeoff requests per month
- average manual hours per takeoff
- fully loaded estimator cost per hour
- CalibraytAI takeoff share
- average supplier validation hours per CalibraytAI takeoff
- average estimator hours per quote
- incremental contribution per additional quote

Eligible contractors, expected adopting contractors, and takeoff volume stay separate. Do not hard-code hours, rates, margins, or BMR figures. The illustration of a manual hour and a validation hour is not a stored default.

### Takeoff labour value

Annual takeoff volume = takeoff requests per month × 12.

CalibraytAI-originated takeoff volume = annual takeoff volume × CalibraytAI takeoff share.

The remainder stays manual. The model does not claim labour savings on that remainder.

Current manual takeoff labour cost for the originated volume = originated volume × average manual hours per takeoff × fully loaded estimator cost per hour.

CalibraytAI validation labour cost = originated volume × average validation hours per takeoff × the same hourly cost.

Direct takeoff labour value = that manual labour cost − the validation labour cost.

### Capacity value

Hours released = originated volume × (manual hours per takeoff − validation hours per takeoff).

Hours released are capacity. They are not automatically cash.

Additional quote capacity = hours released ÷ average estimator hours per quote, when the supplier supplies that hours-per-quote figure.

Capacity value = additional quote capacity × incremental contribution per quote, only when the supplier supplies a valid contribution. If that contribution is absent, show hours released and additional quote capacity with no dollar value. Do not invent the contribution.

Takeoff labour value and capacity value stay separate. The same released hours are not both labour savings and capacity value. The combined view adds the two results. It does not add the hours a second time.

### Commercial value and program cost

Keep the existing commercial chain: material demand, supplier opportunity, supplier quote, supplier order, captured material sales, material gross profit. Material gross profit stays supplier-provided. Do not create a second material-opportunity concept. Do not hard-code BMR values.

Program cost keeps the existing supplier program-cost terminology. Possible names already in view are a base supplier platform licence plus an active contractor component, or a supplier platform fee plus an active contractor fee. This section does not choose between them and does not set a price.

### Combined view and break-even

Operational value = takeoff labour value + capacity value, including a capacity dollar amount only when the supplier supplied it.

Net supplier value = operational value + commercial value − program cost.

ROI multiple = (operational value + commercial value) ÷ program cost.

Where a category is unknown, omit it. Do not manufacture it. Do not present an estimate as an actual supplier result.

Remaining value to break even = program cost − takeoff labour value.

Where a valid capacity value exists, remaining economic value to break even = program cost − takeoff labour value − capacity value.

If that remainder is zero or below, the result is break-even achieved.

Additional material sales required = that positive remainder ÷ the supplier-provided material gross-margin percent. If the remainder is not positive, additional sales required are 0. If the supplier did not supply the margin, do not calculate sales. Sales revenue is not gross profit.

### Known, estimated, and later evidence

Every material economic input is known or estimated. An estimated input must not look like verified supplier data. An input may later move from estimated, to known or configured, to verified. The original assumption is kept when a measured value arrives.

Commercial attribution may separately move from potential, to attributed, to verified. That path is not the same as whether an input is estimated or known.

Before a pilot, the supplier enters assumptions: what CalibraytAI could be worth. During a pilot, operating evidence accumulates: what is happening. After a pilot, measured values replace assumptions without erasing them: what CalibraytAI delivered. Expansion may then use the measured pilot economics for a broader supplier scenario.

The pre-partnership surface can keep using typed assumptions. This section does not add a persistent ROI store. Persistent potential, attributed, and verified measurement belongs to the future Supplier Pro measurement architecture.

### Darcy / BMR live meeting

The immediate use is a live discussion with Darcy. He should be able to supply active PRO contractors, takeoff requests, manual hours, fully loaded estimator cost, expected CalibraytAI takeoff share, validation hours, adoption, average material value, quote-to-order conversion, material gross margin, and the existing program-cost inputs. The displayed results use those entries. Illustrative values are never actual BMR data.

### Dashboard compatibility

The future Supplier ROI & Opportunity Dashboard uses the same definitions for active contractors, projects, takeoffs and calculations, takeoff hours, validation hours, hours released, material demand, supplier opportunity, pricing requests, quotes, orders, captured material value, verified value, and potential value. The dashboard is not built here.

The formula record for this extension is also [supplier-pro-operational-roi-addendum-v1.md](supplier-pro-operational-roi-addendum-v1.md). That file is the same extension, not a second model.
