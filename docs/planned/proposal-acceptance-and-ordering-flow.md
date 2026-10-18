# Planned: proposal acceptance, contract and supplier ordering flow

Approved by Joel, 17 Oct 2026 (05:09–05:17). **Built 17 Oct 2026 on `v1/completion` after Joel's instruction to build all of it (05:52).** Current status (18 Oct 2026): **live** — released with both migrations in `098c554` on 17 Oct, then Supplier Hub B–D in `fb754ed` the same day; production now runs `0e2c917` at revision `y2b3c4d5e6f7`. ("Not deployed" was true when this was written.) Migrations `x1a2b3c4d5e6` (client flow) and `y2b3c4d5e6f7` (Supplier Hub).

## Client side
1. Ben signs off the estimate; the sign-off locks it. The proposal is built from that locked estimate (numbers carried automatically, as today).
2. The proposal is issued to the client **only through CalibraytAI**, as a link. No other route for the client copy, so no one works from an unauthorized proposal.
3. The client ticks **Accept Proposal**. The acceptance is recorded with name, time and the exact proposal version. If the client accepts by phone or email, the office records the acceptance and how it was given.
4. Acceptance marks the proposal and the estimate version Accepted automatically (Joel: yes).
5. The contract is generated automatically and waits for **one Send click** from the office (Joel: one click).
6. The client e-signs once, on the contract (existing Native Signing engine).

## Supplier side
1. A quote is an offer only; the supplier does not sign.
2. Ben approves costs, then **Place order** creates a purchase order referencing the supplier's quote number; it goes to the supplier's inbox.
3. The supplier clicks **Confirm order** (expected delivery, or flags a problem).
4. The agreement is the purchase order plus the confirmation, each recorded with who and when, under the store's existing account terms. No e-signature.
5. Concrete (Tomlinson, via Darcy) is a separate request, kept outside all other requests; the same order/confirm steps apply.

Joel, 05:54: Tomlinson is through Darcy at BMR but is not merged with his other requests. Built as its own supplier account; Darcy has one sign-in reaching both, in separate areas. Concrete fields: volume (m³), strength (MPa), exposure class, air, slump, delivery date and window, placement (pump, chute, wheelbarrow or buggy), delivery town, notes.

## Decisions that supersede earlier records
- ADR-047 §12 "no submitted purchase order": superseded by Joel's 17 Oct decision. CalibraytAI records a purchase order and the supplier's confirmation; there is still no live BMR system connection.
- ADR-047 §11 one login entry: the office `/login` still routes a supplier to the Supplier Hub, and suppliers also have their own sign-in page `/supplier/login` (Joel: "a separate sign in on the supplier side").
- Shared-request field list (assessment §6) approved by Joel 04:50 and enforced in `supplier_hub._base_shared`.
