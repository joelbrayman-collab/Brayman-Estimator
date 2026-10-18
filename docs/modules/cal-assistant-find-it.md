# Cal Assistant — Phase 1: Find It

Status: **IMPLEMENTED ON BRANCH / NOT DEPLOYED.** Production requires Joel's separate authorization. Phases 2 ("Understand it") and 3 ("Get it done") are **not authorized and not built**.

## What it does

- The approved Cal icon is the first button in the office header. Cal opens only when it is clicked. It is a small panel and not a modal. It closes with ✕, Esc (focus goes back to the icon) or a click outside, and the page underneath is never changed.
- The user types what they are looking for. `GET /cal/find?q=` returns links to records the signed-in user can already open, grouped by kind. Clicking a link opens the record.
- Ambiguous project names: Cal lists the matching projects and asks "Which one do you mean?". If a destination was named (for example "harbour lane estimate"), each choice says how many of those records it has and links straight to the record when there is exactly one.
- Nothing found: Cal says so plainly and suggests what to type. It never invents an answer.
- Signed-out visitors don't see Cal. The endpoint sends them to sign-in.

Destinations: Projects, Drawings and Project Plans (generated drawing sets and uploaded plans), Estimates, Proposals, Contracts, Supplier quotations (supplier requests and concrete requests), Purchase orders, the Delivery schedule, the Company Calendar (filtered to the project when one is named), menu tools such as the calculators, and the existing office Help topics (linked to the topic on its page).

## Existing services reused (no duplicate systems)

| Need | Existing authority used |
|---|---|
| Organization isolation | `get_current_organization_id()`; every query is filtered by organization |
| Signed-in / supplier separation | `protect_office_routes` before-request (unchanged) |
| Tools and their permissions | `app/navigation.py` `NAV_SECTIONS` filtered by `app.shell._nav_item_visible` (honours `requires_access_domain`, e.g. Company Management) |
| Help answers | `app/presentation/help_content.py` office topics, quoted word for word and linked to the existing `#help-<key>` anchors |
| Deliveries | `supplier_hub.upcoming_deliveries` |
| Record pages | the existing routes: project, estimate, proposal, contract review, drawing preview, plan viewer, supplier requests (`#share-<id>`, `#concrete`), deliveries, company schedule |
| Header | the existing `header-actions` and `header-icon-btn` styling |

## Rules held

- No external AI provider and no network calls: matching is deterministic word matching on the organization's own records.
- Read-only: a test records every SQL statement and asserts that Cal makes no INSERT/UPDATE/DELETE.
- No orders, approvals, messages or schedule changes. The panel only shows ordinary links.

## Files

`app/services/cal_find.py`, `app/routes/cal_assistant.py`, `app/presentation/cal_copy.py`, `app/templates/partials/cal_assistant.html`, `app/static/css/cal-assistant.css`, `app/static/js/cal_assistant.js`, `app/static/img/cal-assistant/` (derivatives recorded in `docs/branding/cal-assistant-approved-identity-2026-10-17.md`), and `tests/test_cal_find_it.py` (20 tests).

## Known limitations (Phase 1)

- Office header only. Cal is not yet in the Field app or the supplier portal.
- Word matching, not language understanding: there is no typo tolerance or synonyms beyond the listed destination words, and every typed project word must appear in the project's name, number, address, client or location.
- Only office-wide Help topics are linked. Project-page topics (permit report, job location, workflow documents, supplier estimate request) and Hub/Field topics are not.
- Delivery searches list upcoming deliveries (the panel example reads "Upcoming deliveries"); there is no date-range filter such as "this week".
- Results are capped at 8 per group.
- Without JavaScript, the form returns the raw JSON answer.
- The disabled "Search (coming soon)" header placeholder was removed (Joel, 17 Oct); Cal replaces it. The unused `partials/header.html` (included nowhere) was left untouched.
