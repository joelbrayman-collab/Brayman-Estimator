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
