# Useful Calculators

| Attribute | Value |
|-----------|-------|
| Status | Built on branch `v1/useful-calculators-2026-10-22` (22 Oct 2026); not deployed |
| Owner brief | Joel, 22 Oct 2026: "ONE APPROVED ICON. ONE CALCULATOR COLLECTION. NO DUPLICATE ENGINES." |
| Code | `app/routes/useful_calculators.py`, `app/services/useful_calculators.py`, `app/templates/useful_calculators/`, `app/static/useful-calculators/` |
| Tests | `tests/test_useful_calculators.py`, `tests/test_security_route_sweep.py`, `tools/release/evidence_useful_calculators.mjs` |

## What it is

A phone dashboard and a second iPhone Home Screen app, beside CalibraytAI Field. It lists every existing
calculator and opens each one in the right place. It calculates nothing itself: the calculator pages are the
existing views from `app/routes/calculators.py`, served again under `/useful-calculators/` with a phone layout
(the templates pick it with `{% extends calculator_layout | default("base.html") %}`; the office keeps `base.html`).

## Addresses

| What | Address |
|------|---------|
| Dashboard (canonical; the website's Useful Calculators icon links here) | `https://calibryatai.onrender.com/useful-calculators/` |
| Sign-in (stays inside the app) | `/useful-calculators/sign-in?next=/useful-calculators/...` |
| Job calculators (office only) | `/useful-calculators/projects` |
| Calculators | `/useful-calculators/{concrete,stairs,wall-form,wall-framing,footing,roofing,siding,drywall,flooring}` |
| Manifest | `/static/useful-calculators/manifest.webmanifest` |

Signed out, the dashboard shows the established public set, linking to the public website's existing pages:
Concrete (`https://calibraytai.com/useful-tools/concrete/`), Stairs (`/useful-tools/stairs/`) and Employment vs
Entrepreneurship (`/employment-vs-entrepreneurship/`), plus a sign-in for every other calculator. No platform
calculator page is public (Joel, 22 Oct 2026: keep what is established).

## Home Screen app

| | Useful Calculators | CalibraytAI Field (unchanged) |
|--|--|--|
| Manifest | `/static/useful-calculators/manifest.webmanifest` | `/static/manifest.webmanifest` |
| name / title | Useful Calculators | CalibraytAI |
| id | `/useful-calculators/` | `/` |
| start_url | `/useful-calculators/?source=home-screen` | `/` |
| scope | `/useful-calculators/` | `/` |
| Icon | approved artwork, `useful-calculators-icon-180.png` | `calibraytai-app-icon-180.png` |
| Service worker | none (nothing is claimed offline) | `/field-sw.js`, scope `/` |

Field's service worker controls the whole origin but only answers Field pages, Field assets and `/`; it passes
every `/useful-calculators/` request through to the network. On the iPhone each Home Screen app keeps its own
sign-in, so the app has its own in-scope sign-in that returns to the page asked for.

## Icon

The approved artwork (`CalibraytAI_Useful_Calculators_Transparent_Approved.png`, SHA-256 checked in the tests) is
kept byte for byte. `tools/useful_calculators/make_icons.py <approved.png>` makes every size by resize or pad
only: 192/512/32 keep the transparency; the 180 apple-touch-icon and the maskable 512 are opaque on the tile's own
edge blue `#0039b1` (iOS shows transparent Home Screen pixels as black). A new artwork is one run of the script.

## Who sees what

| Calculator | Signed out | Office | Field-only |
|--|--|--|--|
| Concrete, Stairs | website page | phone page | phone page |
| Footing, ICF wall, Wall framing, Roofing, Siding, Drywall, Flooring | sign in | phone page | phone page |
| Employment vs Entrepreneurship | website page | office page (new tab) | named, Office only |
| Supplier economic model | sign in | office page (new tab) | named, Office only |
| Job calculators: Add from calculation, ICF wall quantities, Footing concrete, Wall framing, Labour hours, Construction information, Deck takeoff, Construction drawings | none | choose the job, then the office page (new tab) | named, Office only |

The Field-only allow list (`app/services/access_domains.py`) gains only the quantity-only phone pages and the
app's sign-out. Every other page still sends a Field-only worker to Field Today.
