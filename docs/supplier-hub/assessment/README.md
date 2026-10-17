# Supplier Hub — building store dashboard: current state and completion plan

16 October 2026 · first pilot: BMR Winchester · status: **assessment for Joel's review — nothing implemented, nothing deployed**

Evidence base: the repository on branch `v1/completion` at `c1af230` (live product `dfe098b`). Screens are from a migration-built office with synthetic data (the Harbour Lane Pool Deck job and a synthetic "BMR Winchester" supplier account), in `screenshots/`.

---

## Headline

**There is no Supplier Hub today.** CalibraytAI has:
- no supplier sign-in;
- no supplier user or role;
- no supplier inbox, supplier dashboard, orders or acknowledgements.

The only sign-in is the office sign-in (`screenshots/09`).

Everything supplier-related that exists is used by the contractor. The supplier works outside the app, on paper or PDF:
1. Brayman downloads a supplier request PDF (Form 2).
2. Brayman sends it to the store by email or by hand.
3. The store fills in SKU, unit cost and discount and sends the PDF back.
4. Brayman uploads the PDF, or types the prices in.
5. CalibraytAI checks the response, calculates line and quote totals, records the prices as evidence, and Brayman approves each cost.

That half of the loop is **built, tested and live**. The store's side of the loop — the Hub — is **designed, not built**:
- FG-030 / ADR-047 cover supplier identity.
- The Supplier Pro architecture covers the PRO Hub, firewall, acknowledgement and ROI dashboard.

All of these are recorded as "not implementation-authorized".

The 2026-10 Darcy meeting record (`docs/architecture/darcy-bmr-meeting-readiness-2026-10.md`) says so explicitly: *"There is no supplier portal login for Darcy in this meeting."* The six-step demo in the brief therefore cannot be shown today. Steps 1, 3 and 6 need the Hub. Step 2 (concrete) and step 4 work only from the contractor side.

---

## 1. Current-state capability matrix

| | Capability | Status | Evidence |
|---|---|---|---|
| A | Supplier registration and login | **Designed, not built** | FG-030 / ADR-047: "not implementation-authorized". No supplier user model or route. The only login is `/login`. `app/__init__.py` requires a contractor membership on every page. |
| B | Contractor-selected supplier connections and permissions | **Partly built** | `Supplier`, `SupplierLocation` and `ContractorSupplierAccount` exist (`app/models/supplier_catalogue.py`). The contractor picks an active account on the request (`screenshots/01`). No screen creates an account; they are seeded. No supplier-side permissions. |
| C | Incoming material takeoffs | **Built and tested — as a PDF the contractor sends outside the app** | Deck Takeoff Form 2 request (`/projects/<id>/deck-takeoff/request`; `screenshots/02`), FG-029 Supplier Package HTML/PDF, and a drawings-plus-request bundle. No email to suppliers and no supplier inbox. |
| D | Supplier quotation workflow | **Built and tested — contractor side only** | Brayman uploads the store's filled PDF, or types its prices (`screenshots/03`). The store has no screen. |
| E | SKU matching and product pricing | **Built and tested (human-confirmed)** | `SupplierProduct`, `CanonicalMaterialSupplierMap` and `SupplierProductPriceEvidence` (CONTRACTOR_CONFIRMED_PRICE, validity window). Recording a quote creates the SKU and the map, and refuses a unit mismatch. Bulk catalogue onboarding is not built. |
| F | Contractor-specific discounts | **Partly built** | Discount % per quote line is built and tested; a blank is never treated as 0. Stored account-level discount schedules are **not built**. |
| G | Automated line and quote totals | **Built and tested** | Net unit = cost × (100 − discount)/100, rounded to the cent. Line total = qty × net. Recordable Quoted Total, plus provisional value and named exclusions (`screenshots/04`). A total typed into the PDF is ignored. |
| H | Returned supplier quotations | **Built and tested** | Reconciliation refuses: another project or organization, a tampered line identity, no valid-until date, and unread supplier notes. Statuses: quoted / not quoted / incomplete / price conflict / substitution review / invalid. |
| I | Quotation revisions and status | **Partly built** | Request IDs are fixed by the takeoff (a changed takeoff makes a new request). Responses are numbered RSP-… and go imported → recorded. There is no quote revision chain and no status visible to the supplier. |
| J | Order conversion tracking | **Not built** | No purchase-order or order-status record. Quote-to-order is only a typed input on the economic model. |
| K | PRO account engagement | **Not built (input only)** | "Active PRO accounts" is a typed what-if field. Sponsorship and entitlement are designed, not built. |
| L | Supplier dashboard reporting | **Designed, not built** | Supplier Pro "ROI & Opportunity Dashboard": "Future dashboard. Not implemented." |
| M | Internal quotation labour savings | **What-if calculator only** | `/supplier-program/economic-model` (`screenshots/07`) calculates from numbers typed in, marked Known or Estimated, and stores nothing. No time is measured. |
| N | Supplier privacy and contractor data ownership | **Partly built (between contractors only)** | Org and project isolation is tested on every supplier route. The contractor data firewall is designed but has nothing to protect yet, because suppliers have no access. |
| O | Electronic agreements for suppliers | **Not built** | Native Signing covers customer contracts and change orders. Nothing for suppliers. |

**Other relevant facts:**
- The project schedule (`screenshots/08`) has no supplier, delivery or notification fields.
- The deck takeoff is pool-deck lumber, hardware and railing. It says "No concrete".
- A concrete request exists only through the FG-029 Supplier Package. Its canonical material list includes "CAL-CONC — Concrete" (`screenshots/06`).

## 2. Verified screenshots

All screens are contractor-side, because no supplier screen exists:

| File | Shows |
|---|---|
| `01-deck-takeoff-supplier-request-panel` | Supplier account picker, issued request DTR-…, returned-PDF upload, response list |
| `02-form2-supplier-request.pdf` + page render | The Form 2 PDF a store fills in (SKU, unit cost, discount per line) |
| `03-contractor-hand-entry-of-supplier-prices` | Brayman typing the store's returned prices |
| `04-supplier-response-review-totals` | Reconciliation, Recordable Quoted Total, excluded lines with reasons |
| `05-supplier-response-lines-and-cost-approval` | Line table, recorded evidence, per-material cost approval |
| `06-fg029-supplier-package-mapping` | FG-029 Supplier Package mapping review (DEMO / SYNTHETIC labels) |
| `07-supplier-economic-model` | Economic model (empty inputs, nothing stored) |
| `08-schedule-change-no-supplier-link` | Schedule form: no supplier fields |
| `09-only-login-is-office-login` | The only sign-in page |

## 3. Pilot-critical gaps (for the Darcy demo)

| Demo step | Today | Gap to close |
|---|---|---|
| 1 Darcy signs into Supplier Hub | Not possible | **G1.** Supplier identity and sign-in (FG-030 minimum): supplier user, membership to BMR Winchester, separate supplier area, isolation. |
| 2 Ben prepares and sends a concrete material request | Ben can build a concrete requirement (FG-029) or a deck Form 2, then download a PDF | **G2.** "Send to supplier": a contractor-authorized share of one request to one supplier location, recorded as a transaction. |
| 3 Darcy receives it in his Hub | Not possible | **G3.** Supplier inbox listing only the requests shared with that store. |
| 4 Darcy prepares or returns the quotation | Only by returning the PDF for Brayman to upload or type | **G4.** Darcy enters SKU, unit cost and discount on screen, or uploads the filled PDF himself. It uses the **same** reconciliation and totals code. Brayman still records and approves. |
| 5 Ben changes the project schedule | Works (contractor side) | — |
| 6 The update reaches the supplier | Not possible | **G5.** When a scheduled item linked to a shared request changes date, the store sees a "schedule changed" notice with a first-class acknowledgement state (notified → acknowledged). Text or email can alert; it is not the acknowledgement. |

**Needed for a credible store dashboard:**
- **G6.** A manual "order placed / not placed" mark on an approved quote, made by Brayman or the store. Without it, conversion (J) cannot be shown.
- **G7.** Quote status and revision as the store sees it: received → in progress → returned → recorded → approved, plus "revised" when a request is re-issued.

## 4. Recommended dashboard layout (verified metrics only)

One page for the store owner or PRO desk. Every number comes from recorded events, never estimates.

- **Header:** store name, period selector (this month, last 30 days, quarter) and a "Data shown: requests shared with this store only" note.
- **Row 1 — work waiting:**
  - requests received, not yet returned;
  - schedule changes not yet acknowledged.
- **Row 2 — quote flow (counts and dollar value):**
  - requests received → quotes returned → quote lines recorded by the contractor → costs approved by the contractor → orders marked (G6).
- **Row 3 — speed and quality:**
  - median time from received to returned;
  - share of lines returned complete;
  - lines refused, by reason (price conflict, unit mismatch, missing validity).
- **Row 4 — PRO accounts:**
  - connected contractor accounts and the active ones (sent at least one request in the period);
  - list of contractors who **shared** requests, with request counts only.
- **Panel — quotation time:**
  - Darcy's minutes per quote: typed once per quote, marked "self-reported";
  - lines per request.
  - The labour-saving value stays in the economic model, marked Estimated. The dashboard shows only what was measured.

**Not on the dashboard:**
- contractor margins, labour rates or internal costs;
- other suppliers' prices;
- projects not shared with the store;
- any "sales caused by CalibraytAI" claim.

The Supplier Pro architecture records these as firewall rules.

## 5. SKU and pricing integration approach

1. **Now (built):** SKU and price are captured per quote line and recorded as contractor-confirmed price evidence with a validity window. The SKU map is confirmed by a person.
2. **Pilot step (no BMR system access needed):** a **store price file**. Darcy uploads BMR's PRO price list for one contractor account as CSV: SKU, description, unit, list price, contractor price or discount %, valid from/to.
   - It is stored as supplier price evidence for that account only.
   - Requests can then be **pre-filled**: Darcy reviews and returns instead of typing, which is the quotation-time saving.
   - Totals stay calculated by CalibraytAI.
3. **Authorized connection later:** a read-only, BMR-authorized connection to BMR's product and account-pricing system for SKUs, account prices, discounts and stock.
   - It needs BMR's written authorization, their API or export specification, credentials held by BMR, and a per-account consent from the contractor.
   - Nothing like this exists, and this assessment does not claim it.
4. **Rules throughout:**
   - A price never changes an approved estimate by itself.
   - Brayman still approves costs.
   - Units must match.
   - Every price carries its source and dates.

## 6. Data privacy and permission rules

From the recorded Supplier Pro firewall, made specific for the pilot:

1. **Ownership.** The contractor owns its data. A store sees only what the contractor deliberately sends: one request, to one store location, at a time.
2. **What a shared request contains:** items, quantities, units, needed-by date, delivery town, the contractor's company and contact, and the project reference.
3. **What it never contains:** the customer's name, the full site address before an order, labour rates, internal costs, margins, other suppliers' prices, estimates, or unrelated projects.
4. **Access scope:**
   - A supplier user sees only requests shared with their store.
   - Store staff do not see other stores.
   - Dashboard totals are per store.
5. **Revocation.** The contractor can withdraw a share. The store keeps what it already returned; nothing new is shown.
6. **Audit.** Each share, view, return and acknowledgement is recorded with who and when.
7. **Identity.**
   - Supplier users sign in separately from the office and cannot open office pages.
   - Office users cannot act as a supplier.
   - Tests prove isolation both ways, plus between two stores and between two contractors.
8. **Pilot data.**
   - BMR Winchester's and Brayman's real business data is used only with both owners' agreement.
   - Demonstrations use labelled synthetic data.

## 7. Pilot acceptance criteria (BMR Winchester)

1. Darcy signs in at the supplier sign-in and lands in the Supplier Hub. He cannot open any office page (403 or 404, tested).
2. Ben builds a concrete material request on a Brayman project and selects **Send to BMR Winchester**. It appears in Darcy's inbox within one refresh, showing only the shared fields.
3. Darcy enters SKU, unit cost and discount, or uploads the filled Form 2. CalibraytAI shows line totals and the quote total, then returns it.
4. Ben sees the returned quote with the same reconciliation, exclusions and approval steps as today. Costs reach the estimate only after Ben approves.
5. Ben moves the delivery date. Darcy sees "schedule changed". Darcy selects Acknowledge, and Ben sees "acknowledged by Darcy" with the time.
6. Ben or Darcy marks the order placed. The store dashboard counts the request, the quote, the approval and the order, with nothing estimated.
7. A second store and a second contractor cannot see any of it (tests).
8. All existing contractor tests and the end-to-end walk still pass. Nothing in the contractor workflow changes unless Ben chooses Send.

## 8. Bounded implementation sequence

Each step: owner approval → tests → native Mac regression → release, as now. Every step needs an approved database migration.

| Step | Scope | Unblocks |
|---|---|---|
| **S0 Decisions** | Authorize FG-030 minimum; approve the shared-request field list (§6); approve the concrete request path (FG-029 package, not deck Form 2) | — |
| **S1 Supplier sign-in** | Supplier user + membership to a store location, supplier sign-in, empty Hub page, two-way isolation tests | Demo step 1 |
| **S2 Send to supplier + inbox** | Contractor-authorized share of one request (FG-029 package or Form 2) to one store; supplier inbox; audit events | Steps 2–3 |
| **S3 Supplier returns quote in Hub** | On-screen entry or PDF upload by the store; reuses `deck_takeoff/intake` reconciliation and totals; status received → returned; revision when re-issued | Step 4 |
| **S4 Schedule change + acknowledgement** | Link a shared request to a schedule item; date change creates a notice; acknowledge state visible to Ben | Steps 5–6 |
| **S5 Store dashboard + order mark** | §4 dashboard from recorded events; manual "order placed" | Dashboard, conversion |
| **S6 Store price file (future)** | CSV PRO price list per account; pre-filled quotes | Quotation time saving |
| **S7 Authorized BMR connection (future)** | Only with BMR authorization and specification | Live SKU and account prices |

S1–S4 is the smallest set that makes the six-step Darcy demo real. S5 makes it a business dashboard.

## 9. Exact next development prompt (for after this assessment is reviewed and S0 is decided)

```text
BRAYMAN — CALIBRAYTAI — SUPPLIER HUB S1: SUPPLIER SIGN-IN AND EMPTY HUB

MODE: AUTHORIZED IMPLEMENTATION (S1 ONLY). MIGRATION APPROVED: one additive migration for supplier
users and supplier-store memberships. NO DEPLOY without owner authorization.

Build the FG-030 minimum, following ADR-047, reusing the existing User and password/recovery code:
1. A supplier principal: a User may hold a supplier membership to one SupplierLocation (BMR Winchester).
   A user is either office or supplier for V1; one user cannot be both.
2. Supplier sign-in at /supplier/login (same password rules, rate limits, CSRF, recovery);
   lands on /supplier (an empty "Supplier Hub" page showing the store name and "No requests yet").
3. Isolation: supplier users get 403/404 on every office route; office users get 404 on /supplier/*;
   supplier users of another store see nothing. Tests for all three, plus the existing office tests.
4. CLI to create a supplier user for a store (no self-registration in the pilot).
5. No sharing, inbox, quotes, schedule notices or dashboard yet (S2–S5).
6. Synthetic data only. Do not change contractor screens or the deck takeoff/Form 2 flow.
Report: files, migration (up/down tested on a copy), focused and full regression, screenshots of
/supplier/login and /supplier at 1440 and 390, and the release script for owner authorization.
```

## 10. S0 decisions (Joel, 17 Oct 2026, 04:50)

1. **Supplier sign-in — APPROVED.** A separate supplier-side sign-in (FG-030 minimum) is authorized for build and test on synthetic data. No deploy without separate authorization.
2. **Shared-request field list (§6) — APPROVED as written.**
3. **Concrete path — NOT the FG-029 Supplier Package and not Form 2.** Concrete is a separate request that lives outside all other requests. It is a separate business that Darcy runs through Tomlinson. Open: whether it is its own supplier account, kept apart from BMR Winchester; and the concrete request's field list.
4. **Estimate Accepted on proposal acceptance — YES in principle.** Joel asked whether e-signing marks it accepted. Customers e-sign contracts and change orders, not proposals. Proposed rule awaiting confirmation: when the office marks the proposal Accepted, the estimate version becomes Accepted automatically.
