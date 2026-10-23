# Site Plans

| Attribute | Value |
|-----------|-------|
| Status | Built on branch `v1/site-plans-2026-10-23` (stacked on `v1/calendar-print-2026-10-23`), 23 Oct 2026; not deployed. Ships with the calendar print change in the release after v1rel7 |
| Owner brief | Joel, 23 Oct 2026: "I want this to go on almost every project screen in the office App and I also want it to load on the boys' iPhones like the calculator App so they can instantly access all project plans while on a job site." |
| Database | No migration. Reads the existing Project Plans (`plan_documents`, Sheet Index) and Construction drawings (`construction_drawing_sets`) |
| Code | `app/routes/site_plans.py`, `app/services/site_plans.py`, `app/templates/site_plans/`, `app/static/site-plans/` |
| Tests | `tests/test_site_plans.py` (24), `tests/test_security_route_sweep.py`, `tools/release/evidence_site_plans.mjs` (7 browser checks, in the release gate: 183 → 190) |
| Training | Field Crew lesson `f04-site-plans` "Open plans on site" and test `uat-f04-site-plans` (Field Crew: 31 lessons, 21 tests) (`app/training/site_plans_lesson.py`) |

## Addresses

| What | Address |
|------|---------|
| Project list (the Home Screen app opens here) | `/site-plans/` (start page `/site-plans/?source=home-screen`) |
| Sign-in (stays inside the app) | `/site-plans/sign-in?next=/site-plans/...` |
| A project's plans and drawings | `/site-plans/projects/<project id>` |
| One plan, every page (viewer) | `/site-plans/projects/<id>/plan/<plan id>` or `/drawing/<drawing set id>` |
| The PDF, whole / one page | `.../<file id>.pdf` / `.../<file id>/page-<n>.pdf` |
| Service worker | `/site-plans/sw.js` (scope `/site-plans/` only) |
| Manifest | `/static/site-plans/manifest.webmanifest` |

Hosted: `https://calibryatai.onrender.com/site-plans/`.

## What each person sees

| | Signed out | Office member | Field-only crew |
|--|--|--|--|
| `/site-plans/` | Site Plans sign-in | the organization's active projects | only the jobs they are booked on |
| A project's plans | sign-in | any project of the organization; "Back to the project" and "Upload a plan PDF" links | their jobs only; another job goes back to the list ("not available to you") |
| Files | sign-in | the organization's files | their jobs' files; anything else is 404 |

The crew rule is Field's own, unchanged: `app/services/access_domains.field_visible_project_ids` (scheduled work they
are on, directly or through their crew, ending no more than two weeks ago), applied exactly as
`app/routes/field.py` `_visible_projects` / `_project_or_redirect` apply it. Another organization's project or file is
never found. No Site Plans page shows money, prices, costs, wages or customer contact details: project name and
number, file names, dates, page counts, sheet numbers and names only.

## One plan button in the office (release 8)

Joel's decision (23 Oct 2026): the office keeps one plan button, **View project plan** (Joel's plan-and-eye icon,
`app/services/project_plan_link.py`, in `templates/base.html`), and Field keeps its **View project plan** button
(`field.drawings`). Site Plans' own office "Plans" button (`partials/plans_button.html`, `site_plans.button_project_id`)
and its Contractor training step were removed before release. The office opens Site Plans at `/site-plans/`. Field's
**View project plan** and Site Plans use the same crew rule (`field_visible_project_ids`) and separate addresses
(`/field/projects/<id>/drawings` and `/site-plans/...`); `tests/test_site_plans.py` checks both.

## Where the plans come from (nothing new is stored)

- **Project Plans**: the PDFs the office uploads on the project's Plans page (Upload Plan PDF) and generated drawings
  saved there. Archived plans are left out. Sheet numbers and names come from the Sheet Index where the office made
  one; otherwise pages are "Page N". Plans are still added only there.
- **Construction drawings**: generated drawing sets with their own sheet index. A set already saved to Project Plans
  is listed once, as that plan; the newest set is marked Latest.

Only PDF is stored by Project Plans today, so only PDFs are listed.

## Viewing

- Computers and Android: the browser's own PDF viewer in the page (all pages, its own zoom), plus "Open the PDF on
  its own".
- iPhone and iPad: Safari shows only the first page of a PDF placed inside a page, so each page is served as its own
  one-page PDF (`page-<n>.pdf`, cut from the stored file with pypdf, the file itself unchanged) in an image, which
  Safari draws sharp at any zoom. Pinch with two fingers to zoom; sheet chips jump to a sheet. If a browser cannot
  draw a PDF in an image the page falls back to a frame. In the Home Screen app "Open the PDF on its own" is hidden
  (it would have no way back). No PDF library is added.
- Files are served inline with `Cache-Control: private, no-store` and `X-Content-Type-Options: nosniff`, without
  range requests, only after the same project check.

## Home Screen app

| | Site Plans | Useful Calculators | CalibraytAI Field (unchanged) |
|--|--|--|--|
| Manifest | `/static/site-plans/manifest.webmanifest` | `/static/useful-calculators/manifest.webmanifest` | `/static/manifest.webmanifest` |
| name / title | Site Plans | Useful Calculators | CalibraytAI |
| id / scope | `/site-plans/` | `/useful-calculators/` | `/` |
| start_url | `/site-plans/?source=home-screen` | `/useful-calculators/?source=home-screen` | `/` |
| Icon | `site-plans-icon-180.png` | `useful-calculators-icon-180.png` | `calibraytai-app-icon-180.png` |
| Service worker | `/site-plans/sw.js`, scope `/site-plans/` | none | `/field-sw.js`, scope `/` |

On the iPhone each Home Screen app keeps its own sign-in, so Site Plans has its own in-scope sign-in (the office
check, `app/services/auth.authenticate`) that returns to the page asked for. Crew stay signed in for 8 hours without
use, as on Field; the idle sign-out returns to the Site Plans sign-in.

### Adding it to an iPhone

Safari (not Chrome) → `https://calibryatai.onrender.com/site-plans/` → Share → Add to Home Screen → keep the name
Site Plans → Add. Open the new icon and sign in with the CalibraytAI email and password.

## Offline (no signal)

What is actually achieved:

- The Site Plans service worker keeps, network first, only Site Plans pages, plan files and the app's own static
  files, in one cache `calibrayt-site-plans-v1` on that phone. With signal the phone always gets the current plan;
  without signal it shows the copy it has, with the yellow line "No signal: this is the copy saved on this phone."
- **Last opened plans**: opening a plan keeps that plan, all its pages, and the project list and project page as they
  are seen.
- **Save for offline** (per project): keeps every plan and drawing of that project (pages on an iPhone, whole files on
  other devices) and says "Saved N of N plans on this phone"; each plan then shows "On this phone".
- A page that was never kept shows "No signal. This page is not saved on this phone."
- **Removed**: "Sign out" deletes the cache before signing out; every sign-in page (Site Plans, office `/login`)
  deletes it too, so the next person never sees an earlier person's plans, even after an idle sign-out
  (`app/static/js/sign-in-clears-field-cache.js`, the Field pattern, now also for `calibrayt-site-plans*`).
- Limits: a crew member taken off a job keeps that job's saved copy on his phone until he signs out or the 8-hour
  sign-in ends and he signs in again; the server refuses the files at once. If Field's own service worker is
  updated it clears every other cache on the phone (its existing activate step), so saved plans would need saving
  again; Field's worker was deliberately not changed. Redirects, sign-in pages and office pages are never kept.

## Icon

Approved artwork `CalibraytAI_Site_Plans_Approved.png` (1312 x 1199, transparent; SHA-256
`a9e0f5d3475a8f6944525e3209f287e6f2ee9e31230b4c3dd8f167c5663992ee`), kept byte for byte.
`tools/site_plans/make_icons.py <approved.png>` makes every size the way the Useful Calculators set was made, by crop,
pad and resize only: the transparent margin is cropped to the artwork's visible extent (alpha ≥ 8, x 214–1094,
y 193–1051, keeping the soft shadow), padded to an 880 x 880 square on transparency, then resized. 192/512/32 keep the
transparency; the 180 apple-touch-icon and the maskable 512 (artwork at 80 %) are opaque on the tile's own dark navy
`#1a2b3f`, the mean of the tile body sampled just inside its lighter rim. The Cal logo and the CalibraytAI brand icons
are not touched.

| File | Size | SHA-256 |
|------|------|---------|
| `site-plans-icon-32.png` | 32 x 32, transparent | `28308f546d749d5a1ac06b6b2e767b3d90bdd9da4ceb888de20045a7262f1053` |
| `site-plans-icon-180.png` | 180 x 180, opaque | `230ee2e901bffdd7de9f43ae1ef962d823bb90d19472d759107c897698389905` |
| `site-plans-icon-192.png` | 192 x 192, transparent | `e7c698c46a4b39279245531dba5014ed08d7eeb47549ca2b6949e1fc4dbdbca1` |
| `site-plans-icon-512.png` | 512 x 512, transparent | `9b4fc11f2a036875a6710d35d3413b8a541a2b5bce608bcdd64003e950246e2a` |
| `site-plans-icon-maskable-512.png` | 512 x 512, opaque | `e06c2218218e55aebc42de3abfdcf52fae92aa8371c2797dcba7421924ce05c9` |

## Checks

- `TZ=UTC venv/bin/python -m pytest tests/test_site_plans.py tests/test_security_route_sweep.py`
- `cd tools/release && EVIDENCE_REPO=$PWD/../.. EVIDENCE_EXECUTABLE=<chromium> node --test evidence_site_plans.mjs`
  (`SITE_PLANS_SHOTS=<dir>` also saves the pictures). The walk simulates "no signal" by cutting the connection in a
  local relay, so the service worker's own requests fail as on a phone. The test browser cannot draw PDF pages, so
  the plan itself appears blank in its pictures; Safari draws it.
