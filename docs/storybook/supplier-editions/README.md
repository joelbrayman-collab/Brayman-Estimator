# Supplier Storybook — master and supplier editions

| Attribute | Value |
|-----------|--------|
| Status | **Draft for Joel's review — not published, not approved by either supplier.** |
| Date | 2026-10-22 |
| Branch | `feature/supplier-storybook-editions` |
| Brief | "CalibraytAI — Two Supplier Storybook Editions" and "Supplier Storybook Brand Assets" (Joel, 22 Oct 2026) |
| Economics | [../../architecture/supplier-pro-storybook-economics-addendum-v1.md](../../architecture/supplier-pro-storybook-economics-addendum-v1.md) |

## Structure: one engine, one master, two editions

| File | Role |
|---|---|
| `src/deck.py` | Shared screen-storybook engine: page layout, navigation, phone reflow, print-to-PDF, the shared economics worksheet (`calc_pages`) and the shared sponsorship concept page (`sponsor_concept`). One implementation for every edition. |
| `src/supplier_connection.py` | **Governed supplier-neutral master** ("CalibraytAI — Supplier Connection"). |
| `src/make_kbc.py` → `src/kbc.py` | **KBC edition** (Kemptville Home Hardware Building Centre). `kbc.py` is generated from the master by `make_kbc.py`; every difference from the master is an explicit, asserted replacement or insertion in `make_kbc.py`. Do not edit `kbc.py` by hand. |
| `src/bmr.py` | **BMR Winchester edition.** Keeps the approved BMR narrative (Sell more / Spend less / Miss less, concrete through Tomlinson) from the approved BMR source, read-only, and uses the same engine, worksheet and concept page. |
| `src/contractor.py` | Contractor Storybook, screen edition (same engine; not part of this brief). |
| `src/verify_model.py` | Runs the app's Supplier Economics Calculator (`app/services/supplier_economic_model.py`, model v2) and the books' browser worksheet on the same inputs and requires identical results. |
| `src/qa.py`, `src/pdf.py`, `src/stage.py` | Page-by-page checks at laptop and phone size (overflow, text over the page footer, smallest text), landscape PDF export, artifact staging. |
| `brand/` | Supplier brand files actually used, with `SHA256SUMS`. See "Brand assets". |

The build scripts read photographs, CalibraytAI artwork and synthetic-company screens from the session working folder (paths at the top of each file). Those inputs are not committed here; the approved CalibraytAI artwork is inventoried in [../../branding/approved-asset-inventory.md](../../branding/approved-asset-inventory.md).

## Economics (both editions)

Both editions use the existing CalibraytAI Supplier Economics Calculator — the office page `/supplier-program/economic-model` — extended to model version 2 on this branch (won / unsuccessful split of takeoff labour value; missed-material opportunity; net including it). The books carry a browser copy of exactly those formulas (`deck.py`, `semModel`), so a supplier can type numbers without signing in. There is one copy, used by every edition; there are no supplier-specific calculators. `verify_model.py` result on 22 Oct 2026: **parity OK, 6 cases × 14 results, for the BMR, KBC and master books.** No URL to the office page is printed. Example inputs are labelled illustrative; capacity value is labelled time, not cash; measured results are said to come only from the store's own Dashboard and Material demand pages. The PDFs need no Adobe Acrobat and contain no form fields.

## Brand assets

| File | Source | Format | Notes |
|---|---|---|---|
| `brand/home-hardware-building-centre-lockup.svg`, `…-1200dpi.png` | Home Hardware Stores Limited Supplier Guide v3.1 (July 2025), page 4, `homehardware.sirv.com/supplier-guide/HHSL Supplier Guide Version 3.1.pdf` | Vector, exported unchanged (SVG crop of the page; PNG rendered at 1200 dpi with transparency) | The Home Hardware **Building Centre** banner, as instructed. |
| `brand/bmr-logo-site-342x90.png` | `www.bmr.ca/media/logo/websites/1/logo-bmr-342x90_1_CANADA.png` (logo served on bmr.ca) | PNG 342 × 90, transparent | Raster only; no vector file is public. |
| `brand/bmr-pro-elevation-360-banner-1260x340.jpg` | `www.bmr.ca/media/wysiwyg/Elevation_Desktop_1260x340ENs1_1.jpg` (bmr.ca/en/elevation-360-pro) | JPG 1260 × 340 | BMR's promotional graphic, shown whole and unchanged on the BMR "Supplier choice and rewards" page. |

**Not available publicly, so not used (text instead):** a standalone BMR PRO logo; a standalone Elevation 360 logo; any vector BMR logo; any KBC- or Kemptville-specific logo. lg2's BMR PRO case study contains store photographs only. No supplier logo was redrawn, recoloured or cropped out of other artwork. The supplied seven-panel BMR PRO mock-up's logos (BMR PRO, Home Hardware, RONA) were not reused.

**Permissions still required:** BMR Group (BMR, BMR PRO, Elevation 360); Home Hardware Stores Limited (Home Hardware Building Centre — the guide routes questions to an HHSL Merchandise Manager); KBC (use of its name in a proposal). Each book's inside front cover carries Joel's small-print notice that the logos are for illustration and discussion only and imply no endorsement.

## BMR Winchester edition — page-by-page changes (vs. the 21 Oct screen edition, 50 → 52 pages)

| Page | Change |
|---|---|
| 1 Cover | Official BMR logo (bmr.ca file) beside "Prepared for BMR Winchester". |
| 2 Inside front cover | Small-print notice: BMR, BMR PRO and Elevation 360 marks are illustrative, for discussion, no endorsement. |
| 4 Contents | Economics entries renamed; "Sponsorship in the app (concept)" added; Notes removed from the list (still in the menu) so the page fits. |
| 5–6 Economics | Replaced the old worksheets with the shared Supplier Economics Calculator worksheets (model v2): takeoff labour value, won / unsuccessful split, quote capacity, capacity value; material gross profit, missed-item gross profit, BMR PRO sponsorship and program cost, net program value, net with missed items. |
| 12, 32 Chapter 01 and 07 text | Body set one size smaller so the footnotes and the long concrete text no longer run into the page footer. Wording unchanged. |
| 27 Chapter 05 screen | "Work out the desk's time savings" button now opens economics page 1. |
| 43 BMR PRO-sponsored experience | Authorization sentence moved into the lead line; layout fits. |
| 44 **New:** Sponsorship in the app (concept) | Selected panels from the seven-panel concept — contractor dashboard recognition, supplier choice in the estimate, account settings ("your data always under your control", portability) and phone — as a labelled illustration, not a V1 screen. Projects, materials and calendar panels left out. |
| 46 Supplier choice and rewards | BMR's own Elevation 360 graphic added, unchanged and captioned; projected-points note moved under the illustration. |
| 47 **New:** Today, next and future | The capability ladder, moved off page 46 so both pages read cleanly. |
| 51 Notes and credits | Branding note states which BMR files were used and which were unavailable. |
| 52 Back cover | Official BMR logo and "Prepared for BMR Winchester · a proposal for discussion". |

Retained and checked in the text: BMR PRO sponsorship concept (proposed); contractor independence, supplier choice and portability; contractor-authorized sharing; Elevation 360 projected rewards (one point per eligible dollar, as BMR publishes; confirmed points only through an authorized connection); BMR Winchester as Ben's concrete supplier; Tomlinson as BMR's upstream concrete source; BMR's Tomlinson cost never shown to the contractor; Supplier Hub order and delivery-change screens; operational savings, material sales and missed-opportunity economics.

## KBC edition — what is specific to KBC

- **Identity.** "Kemptville Home Hardware Building Centre" (Hardlines, 15 Jan 2025: joined Home Hardware under new ownership, opened Christmas Eve 2024; 49,000 sq ft, 14,000 sq ft warehouse). Formerly Kemptville Building Centre (BMR from April 2021, RONA before) per bmr.ca — not mentioned in the book. Common ownership with Renfrew per the GOHBA member directory ("Kemptville + Renfrew Home Hardware Building Centres").
- **Branding.** Home Hardware Building Centre lock-up on the cover, sponsorship concept and back cover; small-print notice inside the front cover.
- **Narrative.** KBC's Pro Account contractors and the KBC Pro Desk throughout; no concrete (Chapter 01, 06, 07 and the demonstration rewritten without it; Chapter 07 photograph replaced); screens recaptured from a synthetic company in which the store is "KBC (synthetic) — Kemptville" with no concrete orders.
- **New pages.** "Prepared for KBC, Kemptville" (store context and what to confirm); "A Kemptville week" (clearly labelled illustrative, not KBC data); "KBC-sponsored access" (KBC-specific); "Sponsorship in the app (concept)"; "One connection, more than one store" (common ownership, no store counts, accounts or economics assumed).
- **Programs.** Home Hardware's contractor offers are national PRO programs; the Scotia Home Hardware PRO Visa Business Card earns Scene+ points (1 point per $1 at Home Hardware, per Milesopedia; Rewards Canada notes Pro Contractor accounts did not earn Scene+ points directly in 2023). KBC's own participation is **not confirmed**, so the book names the card only as an example "to be confirmed with KBC".
- **Not carried over:** BMR PRO, Elevation 360, BMR pricing, the BMR–Tomlinson relationship (checked: none of these words appear in the KBC book).

## Verification (22 Oct 2026)

- `qa.py` at 1440 × 820 and 390 × 760: BMR 52 pages, KBC 52, master 48 — no page errors, no overflow, no text over a page footer, no sideways scrolling on the phone.
- `verify_model.py`: parity OK on all three.
- Text scans: KBC has no BMR, Elevation, Tomlinson, Winchester, Darcy, Brayman, Linda, Bushel, concrete, RONA or Lennar; master has no supplier names; BMR has no Home Hardware, KBC, RONA, Linda, Bushel or Lennar.
- `tests/test_supplier_economic_model.py`: 21 passed (6 new).
