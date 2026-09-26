# Contractor UX E2E audit — post UAT 1 cleanup

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-26 |
| Status | **AUDIT ONLY / NOT IMPLEMENTED** |
| Baseline | `ae37c0fa52b986ebc5a628f19bc8ccc3de2bb2bb` live as `dep-darrc4jncjis73eqcr5g` |
| UAT record | `220bbd49ab7aebd08c35fa41b638785d0428327a` |
| Tests at baseline | 1769 passed, exit 0 |
| V1 | Not rescored |
| FG-039 | PARKED / NOT PUBLISHED |
| Bypass | ACTIVE. Password authentication UNRESOLVED. |

This record does not authorize implementation. Wave 1 is not authorized.

## Diagnosis

The daily office (Home, Projects, Estimates, Proposals, Schedule) now reads as one product. The rest of the office still reads as specialist tools joined by the sidebar. A contractor who stays on the five daily pages can work. A contractor who opens Cost library or Project work meets calibration, mappings, organization language, and database indexes.

No finding blocks the five daily destinations. The next work is P1 before broader real-life UAT, not another reshuffle of Home.

## P0

None on the five daily destinations after the cleanup.

## P1

- Project detail is grouped, and it is still a long record: Project Hub eyebrow, equal heading buttons, and a visible LEARN · Future note.
- Labour rates, Pricing, and Previous estimates are one click from Cost library and speak in specialist language (mappings, calibration candidates, organization-owned, workbook upload).
- Clients can be created and cannot be opened or corrected. There is no client page. Rows are not links.
- Settings in the menu opens Brand profile only.
- Most indexes still use a data table with View/Edit/Open on the right. Projects and Estimates are the exception.
- Breadcrumbs exist on Project detail only. Other pages say Back to list or Back.

## P2

- Assemblies, Cost items, Materials, Change orders, and Proposal Templates indexes do not follow the Projects/Estimates row pattern.
- Proposal Templates sit under Cost library.
- Work types and Crews sit under Project work although they are company catalogs.
- Clients eyebrow says CRM.
- Cost library menu says Cost items; the page title still says Cost library.
- Materials menu label and the Material Catalogue page title differ.
- Estimate detail still has a View Version control and a versions table with View.
- Field office (`/field`) is a separate shell and is not in the office menu.

## P3

- Dark-sidebar CalibraytAI logo is not in the repository. Do not substitute another asset.
- Inline styles on Previous estimates and some plan screens.
- Schedule and some lists will scroll sideways on a narrow laptop.

## Waves (not authorized)

1. Shared language and patterns: drop CRM and Project Hub from contractor view, one status word, one index row, one return path. Do not reshuffle Home.
2. Remaining indexes: proposals, assemblies, cost items, materials, change orders, clients.
3. Specialist libraries: labour, pricing, previous estimates, work types. Show the contractor question first.
4. Project page: what to do next, then the rest on request. Keep the five groups.
5. Empty, error, and help copy, plus spacing. Logo only when the approved file arrives.

Joel should look at the live office before any wave is authorized.
