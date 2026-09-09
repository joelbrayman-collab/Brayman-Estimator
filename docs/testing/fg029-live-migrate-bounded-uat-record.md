# FG-029 live migrate + bounded BMR demo office UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** Live-migrated. Bounded DEMO/SYNTHETIC office UAT **PASS**. Close/current-authority docs reconciled in the FG-029 post-UAT governance commit. |
| Date | 2026-09-09 |
| Gate | [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) |
| Product SHA | `ee578dcb5a688842ebedaff0682131826e6c7188` |
| Pin SHA at start | `489d69aa21697b7cde0ccdc207271f8ebd558a43` |
| Actor | Joel Brayman — FG029-UAT |
| Organization | ORG-001 / Brayman Construction Inc. |

This file records live-migration and UAT facts only. It does not implement FG-028 Slice 3 or FG-030.

## Migration

| Field | Value |
|-------|--------|
| Pre-migration live current | `a5b6c7d8e9f0` |
| Repository head | `b6c7d8e9f0a1` |
| Backup | `instance/brayman_estimator-backup-before-fg029-b6c7d8e9f0a1.db` (gitignored) |
| Backup size | 1,654,784 bytes |
| Backup SHA-256 | `cb6bb915e66535faa3eb1e03a03c8d07634397a2b4da0681ee5709e4edc1c2da` |
| Command | `./venv/bin/flask db upgrade b6c7d8e9f0a1` |
| Post-migration live current | `b6c7d8e9f0a1 (head)` |
| Post-migration repository head | `b6c7d8e9f0a1 (head)` |
| Graph heads | one |
| Added tables only | `suppliers`, `supplier_locations`, `contractor_supplier_accounts`, `supplier_products`, `canonical_material_supplier_maps`, `material_requirements`, `supplier_requirement_maps`, `supplier_product_price_evidence`, `supplier_product_availability_evidence`, `supplier_packages`, `supplier_package_lines` |
| Removed tables | none |

## UAT identities (DEMO / SYNTHETIC)

| Kind | Id | Identity |
|------|----|----------|
| Project | 14 | `FG029-UAT-BMR-DEMO` / `ORG-001` / created_at `2026-09-09T14:54:04.121040` |
| Client | 9 | FG029-UAT DEMO SYNTHETIC Client |
| Office user | 1 | Joel Brayman (ORG-001 membership) |
| Supplier | 1 | code `BMR-WINCHESTER-DEMO` / legal name `BMR Winchester — DEMO / SYNTHETIC` / `demo_synthetic=True` |
| Location | 1 | code `WINCHESTER` / `WINCHESTER — DEMO / SYNTHETIC` |
| Contractor account | 1 | ORG-001 ↔ Winchester DEMO |
| Canonical materials | 7 / 6 / 17 | `CAL-LUM-2X6-12`, `CAL-LUM-2X6-8` (no 2×6 stud seed exists), `CAL-SHT-OSB-7-16-4X8` |
| Requirements | 1 / 2 / 3 | sources `DEMO_SYNTHETIC` / `MANUAL` / `DEMO_SYNTHETIC`; status `REVIEWED`; **not FG-010** |
| SKUs | 1 / 2 / 3 | `DEMO-BMR-2X6-12`, `DEMO-BMR-2X6-8`, `DEMO-BMR-OSB-716` |
| Maps | 1 / 2 / 3 | demonstrated `MAPPED`, `REVIEW_REQUIRED` then human-resolved `MAPPED`, left `UNRESOLVED` |
| Prices | 1 / 2 / 3 | CAD `12.50` / `8.00` frozen; living after-issue `99.99` |
| Availability | 1 / 2 / 3 | `IN_STOCK` / `LIMITED` / `UNKNOWN` |
| Draft then issued package | 1 | `DRAFT` generated then `ISSUED` same id; issued_by `Joel Brayman — FG029-UAT`; issued_at `2026-09-09T14:54:04.226692` |
| Frozen lines | 1 / 2 / 3 | FRAMING / FRAMING / SHEATHING |
| HTML | HTTP 200 | Hub PRICE `/projects/14/supplier-package/1` |
| PDF | HTTP 200 | SHA-256 `1c698d824228d6f2689008b8a702a7d4c9880547b51f41dd939f11101d2c1be5` (3064 bytes) |
| Isolation | HTTP 404 | ORG-001 session cannot open project 4 (`ORG-FG014-UAT`) |

Local HTML/PDF copies (gitignored): `instance/fg029-uat-supplier-package.html`, `instance/fg029-uat-supplier-package.pdf`.

## Boundaries verified

- Supplier price INFORM ONLY. Frozen line 1 remains `12.5000` CAD after living price 3 `99.9900`.
- No `Apply Supplier Cost`. EstimateLineItem / EstimateCostingSnapshot / EstimatePricingSnapshot counts backup→live **7 / 2 / 6 unchanged**. UAT project has **0** estimates.
- TakeoffPackage / TakeoffPackageItem / TakeoffCandidate / FG-026 insertion/citation counts unchanged. No supplier columns on PLAN tables.
- Package status `ISSUED` / readiness `order-ready / review-ready`. HTML and PDF contain no `SUBMITTED`. No BMR HTTP/API, EDI, or PO. External order side effect: **NONE**.
- FG-029 contractor-office tenancy: ORG-001 session cannot open project 4 (`ORG-FG014-UAT`) — HTTP **404**. This is **contractor-office isolation only**. FG-030 supplier-user portal isolation is **NOT IMPLEMENTED**.
- FG-028 application logo **not** installed. HTML chrome still uses existing tenant `brayman-construction-logo.png`.
- FG-030 supplier login **not** implemented.
- ADR-008 remains **Proposed**.

## Tests

**NOT RERUN** this session (UAT revealed no product defect).

Historical FG-029 implementation evidence: dedicated **16 passed**; governed bundle **210 passed**; full suite **677 passed**.
