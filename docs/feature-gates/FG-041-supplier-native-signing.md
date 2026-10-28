# FG-041 — Supplier Native Signing

| Attribute | Value |
|-----------|--------|
| Status | **RECONCILED ONTO CURRENT MAIN ON BRANCH `reconcile/fg041-supplier-signing-on-main-2026-10-28` (28 Oct 2026) / NOT MERGED / NOT DEPLOYED / MIGRATION NOT APPLIED LIVE / CONSENT `CONSENT-SUPPLIER-V1-001` NOT APPROVED** |
| Directive | Joel, 20 Oct 2026: "Connect native signing...!" — supplier-side signing "is just as important as the contractor - client side" and "is just a connection of the engine we already built". |
| Engine | [FG-033](FG-033-native-signing-document-approval-signature-and-executed-artifact.md) Native Signing (frozen artifact, request, participants, events, executed PDF). No new provider. |
| Migration | `a4d5e6f7a8b9` (revises `q4c7l2n8t3a6` since the 28 Oct 2026 reconciliation onto main; originally `z3c4d5e6f7a8`, then `pd1a2b3c4d5e`). Authorized for the development branch by Joel 20 Oct 2026; production apply needs his separate authorization at release. |

## Owner decisions (Joel, 20 Oct 2026)

| Question | Answer |
|----------|--------|
| What is signed | Purchase orders, store confirmations and delivery changes: the purchase order is signed by the contractor and countersigned by the store when it confirms; every agreed delivery change is signed by both sides. |
| How the store signs | In the Supplier Hub while signed in: tick the consent box, type their name, Sign and confirm. No emailed link. |
| How the contractor signs | On Place order: tick the consent box and type their name. |
| Database change | Yes, on the development branch (rehearsed on synthetic databases only). |

## What it does

- **Place order** (office) requires the consent tick and a typed name. The purchase order is rendered once to PDF
  (`app/services/supplier_signing_pdf.py`), frozen with its SHA-256 in signing custody, and a signing request
  (family `SUPPLIER_ORDER`) opens with two participants: `CONTRACTOR` (signed now) and `SUPPLIER` (waiting).
- **Sign and confirm order** (Supplier Hub) requires the tick and a typed name. The store signs, and the executed PDF
  (the frozen order plus a signing-record page naming both signers, their sign-ins, times, IP, device, the pre-sign
  SHA-256 and the consent version) is retained. Both sides download the same signed copy.
- **Report a problem** needs no signature and voids the open request.
- **Delivery change**: the side that asks signs when it asks (family `SUPPLIER_DELIVERY_CHANGE`); the other side
  signs when it accepts, which completes the signed change. Declining needs no signature and voids it; proposing
  another time voids it and opens a new one signed by the proposing side; withdrawing voids it.
- A change proposed automatically when the project schedule moves, and an order placed before this release, are still
  frozen and recorded; the signing record says that side was "not signed by typed name" and names who placed or
  requested it. Nothing is presented as a signature that was not typed.
- Consent: real suppliers pin `CONSENT-SUPPLIER-V1-001` (production wording in `app/services/supplier_signing.py`,
  created once, never edited); synthetic (demo) suppliers pin the existing synthetic consent and their records carry the
  synthetic banner.
- Privacy: the store's documents show the contractor's project reference, never the internal project name (the Supplier
  Hub rule). Downloads fail closed: a store opens only documents whose order is its own; the office only documents of
  its own organization's project. Supplier documents have no client signing link (no token, no `/sign` access).

## Not changed

Client contract and change-order signing; the `/sign` ceremony; notification wording (except the flash messages and
button labels on the affected forms); purchase order, confirmation and delivery-change business rules.

## Release notes (for the release gate)

- Migration `a4d5e6f7a8b9` rebuilds three signing tables to widen three check constraints; no table, column or row is
  added or changed. `tools/release/migration_check.py` now accepts `--altered-checks` naming exactly those constraints and
  proves every row, column, key and foreign key is unchanged:
  `--from q4c7l2n8t3a6 --to a4d5e6f7a8b9 --new-tables "" --altered-checks ck_signing_frozen_artifacts_document_family,ck_signing_requests_document_family,ck_signing_participants_role`.
- The release gate script must pass those arguments for this release (not yet wired; release-time task).
- Joel to approve the production consent wording `CONSENT-SUPPLIER-V1-001` before release.
- Signing custody: the 18 Oct finding (`SIGNING_ARTIFACT_ROOT` not set) applies here too; new supplier documents are
  written beside the live database's instance folder like other signing files.

## Tests

`tests/test_supplier_native_signing.py` (10) and `tests/test_supplier_signing_migration.py` (4); existing supplier
tests sign where the screens now require it; migration head pins moved to `a4d5e6f7a8b9`.


## Reconciliation onto current main (28 Oct 2026)

Turnover corrective pass, after the independent audit. Source: `signing/supplier-native-signing-on-prodesk`
(`e424e14f`, `b0a747c9`, `c2a3be14`; preserved at `recovery/supplier-signing-preserved-2026-10-28`), cherry-picked
with `-x` onto `main` `66c93062`.

- **Migration:** `a4d5e6f7a8b9` now revises `q4c7l2n8t3a6` (the live head). One chain, one head. Release-gate flags:
  `--migration-to a4d5e6f7a8b9 --new-tables none --altered-checks
  ck_signing_frozen_artifacts_document_family,ck_signing_requests_document_family,ck_signing_participants_role`.
- **Conflicts resolved against newer main:** the Supplier Pro Desk wizard import stays at the end of
  `supplier_portal.py` after the signed-document route; delivery history keeps main's local-time formatting and gains
  the signed-change link; the store's order page keeps main's cancelled-order notice with FG-041's signing wording;
  the office request page keeps main's cancelled/delivered statuses and adds the signing line;
  `migration_check.py` keeps main's added-column checks (`--altered-tables`) and FG-041's `--altered-checks`; every
  head pin in the test suite moves from `q4c7l2n8t3a6` to `a4d5e6f7a8b9`.
- **Joined with main's later order lifecycle (cancel / delivered, 21 Oct 2026):** cancelling an order voids its
  signing request if the store has not signed yet (an executed order keeps its record); withdrawing open delivery
  changes on cancel or delivery voids their signing requests — they are never signed. Covered in
  `tests/test_supplier_po_cancel_delivered.py`.
- **Tests written after 20 Oct** that place, confirm or change orders now send the consent tick and typed name, as
  every on-screen order, confirmation and change requires.
- **Gate:** the consent wording `CONSENT-SUPPLIER-V1-001` is recorded in `app/services/supplier_signing.py` as a
  production consent version created on first use. It is **not approved**. This branch is not merged into `main`,
  because the next Live release from `main` would put that wording in front of real suppliers. Merge, migration
  and release wait for Joel's approval of the wording and of the migration.

## CaliSIGN presentation (28 Oct 2026)

Branch `feature/calisign-native-esignature-2026-10-28`, stacked on this reconcile branch: the supplier signing above
is unchanged in behaviour; it gains CaliSIGN wording (Sign & Send for E-Signature, Sign & Confirm Order, Sign &
Accept), the adopt-signature preview, status chips and a CaliSIGN email to the store. Consent
`CONSENT-SUPPLIER-V1-001` is still **not approved**; the migration is still **not applied live**.
See `docs/operations/calisign-native-esignature.md`.
