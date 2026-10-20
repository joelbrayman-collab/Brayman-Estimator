# FG-041 — Supplier Native Signing

| Attribute | Value |
|-----------|--------|
| Status | **IMPLEMENTED ON BRANCH `signing/supplier-native-signing` / NOT DEPLOYED / MIGRATION NOT APPLIED LIVE** |
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
