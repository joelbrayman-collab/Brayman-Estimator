# CalibraytAI Contractor Storybook — refined review edition

18 October 2026. **Archived review edition; not a new platform release and not yet published.**

Joel authorized creation of this edition, a matching PDF, and preservation in the project repository. This is the completed 44-page / 14-chapter book, distinct from the original 16 October screenshot-library capture record.

## Retained deliverables

- [CalibraytAI_Contractor_Storybook_Refined_2026-10-18.html](CalibraytAI_Contractor_Storybook_Refined_2026-10-18.html.zip) — extract the ZIP to recover the original file.
- [CalibraytAI_Contractor_Storybook_Refined_2026-10-18.pdf](CalibraytAI_Contractor_Storybook_Refined_2026-10-18.pdf.zip) — extract the ZIP to recover the original file.
- [CalibraytAI_Storybook_Refined_Editable_Source_2026-10-18.zip](CalibraytAI_Storybook_Refined_Editable_Source_2026-10-18.zip)
- [CalibraytAI_Storybook_Refined_Vercel_2026-10-18.zip](CalibraytAI_Storybook_Refined_Vercel_2026-10-18.zip)

HTML and PDF use individual ZIP wrappers because the connector request limit prevents direct upload of the larger originals. Their contents are unchanged. `MANIFEST.json` records SHA-256 and byte counts for both stored archives and original deliverables. Both wrapped files were extracted and checked against the original hashes before upload.

## Editorial changes and protected assets

- All 44 pages and 14 chapters retained. Eleven pages received bounded editorial/screenshot overlays.
- Approved original logos and brand artwork preserved; front cover, inside front cover, inside back cover and back cover remain byte-identical page assets. All 33 unchanged page assets are byte-identical; each modified SVG embeds its original unchanged source page.
- Existing synthetic captures provide readable stair-diagram, estimate-total, schedule and estimated-versus-actual details. No generated substitute screens.
- Supplier pricing-form workflow distinguished from planned direct supplier integration; broad Canada-wide wording reconciled with the roadmap.
- Clickable contents, printed-folio counter, chapter navigation, page enlargement and original-screen detail views added. Original page-turn animation retained. Closing project-record explanation strengthened.
- Existing source capture provenance remains [../../README.md](../../README.md). This edition does not certify application capability or expand product approval.

## Verification actually performed

- `node verify-book.cjs`: **17 focused code/asset checks passed** (script retained in editable-source ZIP). Includes complete forward/backward traversal of the page model, phone single-page model, tablet spread retention, chapter links, printed counters, swipe classification, original-asset checks, zoom-state isolation and original animation/motion handling.
- Changed SVG pages parsed and rendered at 1275 × 1650; all 11 changed pages visually reviewed.
- PDF reopened: **44 pages render**; all rendered pages compared with source imagery, mean per-channel pixel difference below 3. Fourteen contents links and the contact link checked; chapter bookmarks retained.
- ZIP integrity and extracted original hashes verified.
- **New-edition real-browser verification NOT performed.** Earlier live edition received a desktop walkthrough, but that result is not claimed for this edition.
- No unrelated platform CI, migration, live database or production check was run for this archival-only change.

## Publication and recovery

Existing book URL: https://calibraytaiwebstorybookreadytopubli.vercel.app/

Existing Vercel project: `calibraytai_web_storybook_ready_to_publish` / `prj_dC5qstDwfnbZLcD1EdNeK9l97n63`. Existing account scope: `team_VBgdZDEQi72xBacwVcFjMvkQ` (`joelbrayman-9492`).

**NOT PUBLISHED:** Vercel rejected file access/upload with HTTP 403 for this scope. Do not infer a successful deployment from the prepared Vercel ZIP. Last observed live deployment `dpl_3mwzevynqKtdNmogcWrPm7VxJCB5` remains the rollback/reference baseline. No new project was created.

Extract the HTML ZIP to read the self-contained edition. Extract the Vercel package to restore the static deployment folder. Extract the editable-source package for original page layers, fonts, screenshot inputs, editorial manifest, authoring scripts and focused checks. Its rendering helper needs the installed `@resvg/resvg-js` require path adjusted for the receiving checkout.

## Authorized scope and next action

This commit changes documentation/archive paths only. Application code, authentication, records, databases, pricing policy, schemas, migrations, approved brand masters and active engineering work are outside scope. No platform milestone is advanced. No new development or deployment is approved by this record.

The owner's request is to retain these exact deliverables as the project record. Publication remains blocked on existing-project Vercel access and must distinguish browser checks from code checks. Future editorial changes should create a new dated edition, preserving this one.
