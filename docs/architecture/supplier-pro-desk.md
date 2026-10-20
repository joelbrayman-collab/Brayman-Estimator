# Supplier PRO Desk — five-minute walk-in quotation

| Attribute | Value |
|-----------|--------|
| Date | 20 October 2026 |
| Directive | Joel, 20 Oct 2026, "Complete current work → build Supplier PRO Desk workflow" (execution authorization) |
| Status | **In development** on branch `supplier/pro-desk-2026-10-20`. Not released. See the implementation register at the end. |
| Governs | [ADR-047 Amendment 1](../adr/ADR-047-supplier-identity-authentication-and-access-isolation.md#amendment-1--supplier-owned-quotation-workspace-20-oct-2026) |

## What it does

A supplier's store staff (BMR Winchester first; any supplier) take a walk-in customer's sketch and produce, at the counter:

1. a preliminary **sales** drawing (not for construction),
2. a material takeoff for the defined scope,
3. prices from the supplier's **own authorized price file**,
4. a supplier-branded **materials-only** quotation,
5. the customer's approval and an **order-ready package** for the supplier's own sales/POS system.

The customer is the supplier's customer. They never register with CalibraytAI and never become a contractor's client.

## Reuse map (nothing duplicated)

| Need | Existing engine reused | Extension added |
|---|---|---|
| Supplier staff sign-in, isolation | `supplier_portal` blueprint, `require_supplier_membership`, the global principal-class guard in `app/__init__.py` | New supplier-scoped routes under `/supplier/<id>/pro-desk/…`; same guard, same 404-outside-your-supplier rule |
| Store identity, brand | `suppliers`, `supplier_locations`, `supplier_brand_profiles` | Supplier quotation settings (tax, validity, terms, delivery) per supplier |
| Drawing | `app/services/drawings/` (`core`, `pdf`, `dxf`, drawing standard, title block) | `drawings/outbuilding.py` — a composer like `deck.py`; same primitives, renderers and status banner |
| Takeoff identities | `canonical_materials`, `deck_takeoff.catalogue.ensure_identity` (ADR-057 pattern) | `outbuilding/catalogue.py` identities; five categories added to the canonical catalogue |
| Quantities | Geometry only; the same "human confirms every input" rule as `calculation_quantity_reviews` | `outbuilding/takeoff.py` — rule-per-line, every rule shown with its basis |
| SKU identity, conversions | `supplier_products`, `canonical_material_supplier_maps.requirement_to_sales_factor` | Mapping screen for the supplier's own products |
| Prices | Supplier catalogue price evidence model (stored class, validity dates, source, actor) | A store **selling** price kept beside contractor-cost evidence, loaded only from the supplier's price file |
| Quotation PDF | ReportLab pipeline and helpers in `proposal_pdf.py` | `supplier_quote_pdf.py` — a materials-only document; never a construction proposal, never a contract |
| Approval link | The hashed lookup-key + secret pattern of `proposal_acceptance` | Supplier quote links; acceptance records the content hash and starts **no** contract |
| Email | `transactional_email.send_transactional_message` (allowlist, log) | One template, sent only with the customer's recorded consent |
| Audit | `supplier_request_events` pattern | `supplier_quote_events` |

## Rules that do not bend

- **Nothing is invented.** Every dimension and specification is entered and confirmed by staff. Prices come only from the supplier's imported file. A line without a confirmed input or a current price is shown as a gap; a quote with gaps cannot be issued.
- **Structure is not designed.** Trusses are counted, never designed ("design by truss manufacturer"). Posts, headers, footings and door framing are flagged for technical review. Drawings carry "PRELIMINARY SALES DRAWING — NOT FOR CONSTRUCTION".
- **No AI.** The sketch is a photo kept with the quote; staff read it. No automatic interpretation, no external service (tests enforce this).
- **Materials only.** No labour, installation, margin or contract. Acceptance never creates an Ontario construction contract.
- **Separation.** Supplier-owned customers and quotes carry a `supplier_id` and no `organization_id`. Contractors never see them; suppliers never see contractor records. A supplier sees only its own.
- **POS.** The order-ready package is a printable sheet and CSV for entry into the supplier's own system. There is no POS connection.

## Reference building system (first validated assembly)

**Post-frame with steel roof and wall cladding, gable roof.** Chosen because the directive's reference building (30 × 40 ft, 12 ft walls, one 10 × 10 overhead door, one man door) is the common farm storage form. The takeoff rules are listed in `app/services/outbuilding/takeoff.py` and on the quote's Materials step. Other systems are listed in intake as "not yet available" rather than approximated.

## Implementation register

| Item | State |
|---|---|
| Development branch | `supplier/pro-desk-2026-10-20` (from `f30fb19`) |
| Database migration | `pd1a2b3c4d5e` — new supplier-quote tables; canonical category list extended (no existing row changed) |
| Tests | `tests/test_supplier_pro_desk.py` (15), `tests/test_supplier_pro_desk_migration.py` (3), route sweep, migration check `--altered-tables` |
| Browser evidence | `tools/release/evidence_pro_desk.mjs` — desktop timed walk, phone walk (no sideways scrolling; pricing and order tables become cards), supplier and contractor isolation; release gate total 60 |
| Release gate flags | `--migration-to pd1a2b3c4d5e --new-tables <the eight supplier_* tables> --altered-tables canonical_materials --browser-expected 60` |
| Production | Not released |
| Operational now (development branch only) | Walk-in customer with consent, sketch upload, post-frame steel gable building, plan + elevations, takeoff, price-file import, product matches, pricing with blockers, issue (frozen), revision, approval link, order package + CSV, quotation email (allowlist) |
| Not built (planned only) | Stick-frame and shingle systems, foundation quantities, AI sketch reading, POS integration, supplier staff roles for who may import prices |
| BMR reference package | **Not yet provided** (sketch, BMR takeoff, BMR prices, BMR quote). All demo data is synthetic and labelled so. |
| Rollback | Code: redeploy the previous live commit. Database: restore the pre-migration backup (only with Joel). |

The register is kept current in `docs/session-handoff.md` and in the release record.
