# CaliSIGN — approved identity (28 Oct 2026)

**Status: APPROVED by Joel, 28 Oct 2026** ("approved. record, save file and use for the next task").
Reference: [calisign-approved-identity-sheet-2026-10-28.png](calisign-approved-identity-sheet-2026-10-28.png).
Checksums: [../approved-asset-inventory.md](../approved-asset-inventory.md) (enforced by `tests/test_branding_asset_integrity.py`).

## What CaliSIGN is

CaliSIGN is CalibraytAI's native electronic-signature capability for **Contractor ↔ Client** (contracts, change
orders, client agreements) and **Contractor ↔ Supplier** (purchase orders, supplier agreements). It is a named
CalibraytAI capability — "CaliSIGN by CalibraytAI" — not a separate company or product brand. CalibraytAI is not
renamed; Brayman Construction (or any contractor's Brand Profile) stays the sender the signer sees first.

## The identity

| Element | Rule |
|---|---|
| Mark | A page with a gold folded corner and a gold handwritten signature stroke crossing out of it. `calisign-mark.svg` (light: navy page, white fill) and `calisign-mark-dark.svg` (dark: white page). Never redrawn, recoloured or cropped. |
| Wordmark | Live text, IBM Plex Sans 700, letter-spacing −0.02em: `Cali` navy `#1F3A5F` (white on dark) + `SIGN` gold `#C79A2B`. |
| Byline | `BY CALIBRAYTAI`, IBM Plex Sans 600, letter-spacing 0.34em, same colour as `Cali`. |
| Icon tiles | The dark mark on a navy `#1F3A5F` tile: 512 / 128 (app icon), 64 (navigation), 32 (menu); button icon 24 = the light mark without a tile. |
| Colours | Navy `#1F3A5F` (the approved document navy: Supplier Pricing Request header), gold `#C79A2B` (`--gold` in app.css), white, and the app's existing neutrals (`--cream #f4f2ee`, `--workspace #f6f5f2`, `--muted #6b6f76`, `--border #e2ddd4`, `--sidebar #17191d`). No other colours. |
| Font | IBM Plex Sans (the app font). |
| Gold text | Gold is for the wordmark and the mark (a logotype). Ordinary small text stays dark (gold on white is 2.6:1); gold buttons carry black text (7.1:1). |
| Actions | Plain words, never the brand: **Send for E-Signature**, **Review and Sign**, **Sign & Accept**, **View Signing Status**, **Download Executed Copy**. |

## Files

| File | Use |
|---|---|
| `app/static/branding/calisign/calisign-mark.svg` | Mark, light backgrounds (inline or `<img>`) |
| `app/static/branding/calisign/calisign-mark-dark.svg` | Mark, dark backgrounds |
| `app/static/branding/calisign/calisign-identifier-light@2x.png` | Identifier as an image (email, PDF), light |
| `app/static/branding/calisign/calisign-identifier-dark@2x.png` | Identifier as an image, dark |
| `app/static/branding/calisign/calisign-app-icon-512.png`, `-128.png` | App icon tiles |
| `app/static/branding/calisign/calisign-icon-64.png`, `-32.png` | Navigation and menu icons |
| `app/templates/partials/calisign.html` | Jinja macros: `calisign_mark(size, dark)`, `calisign_identifier(size, dark, byline)` |

The approved sheet's placements: primary identifier light/dark; compact icons; the signing-ceremony identifier;
the email header (gold rule, the contractor's own logo on the right); the office actions; the desktop office
(CaliSIGN in the sidebar with the dark mark); mobile; the signing page (Review → Sign → Done).

## Source of the approval

The concept images Joel shared on 28 Oct 2026 set the direction (document + signature, gold SIGN, BY CALIBRAYTAI,
navy tiles); this identity reproduces that direction in the approved CalibraytAI colours and font. The concept
images themselves are not assets.

## In use (28 Oct 2026, native e-signature)

The signing page, office panel, Supplier Hub signature box and emails use these assets and tokens only. The typed
signature preview uses Dancing Script 600 (SIL Open Font License), served from
`app/static/fonts/dancing-script/` with its licence; it renders the signer's own typed name and is not a brand
asset. No other font, colour or mark was added.
