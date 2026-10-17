# Planned: proposal acceptance, contract and supplier ordering flow

Approved in principle by Joel, 17 Oct 2026 (05:09–05:17). **Not authorized for implementation yet.** New feature work; needs its own authorization, migration approval, tests and release.

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

Open: whether Tomlinson is its own supplier account kept apart from BMR Winchester; the concrete request's field list.
