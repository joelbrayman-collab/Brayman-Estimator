# A Day in the Life with CalibraytAI — screenshot library

## Refined book edition recorded — 18 October 2026

The completed **44-page, 14-chapter** refined review edition, matching PDF, Vercel package and editable source are preserved in [editions/2026-10-18-refined/](editions/2026-10-18-refined/README.md), with original-file SHA-256 checksums and verification/publication status. This is a documentation archive; approved branding and earlier capture assets remain preserved. The revised edition is **not published** (Vercel 403); new-edition browser testing is not claimed.

The screenshot-library description below is the historical 16 October capture record, not the current book's completion status.

Advance Reading Edition for Ben and Kevin. Historical capture status on 16 October: **screenshot library only; awaiting Joel's visual approval.**

- Product code: `6a8c807` on branch `v1/completion` (the screens are V1 as live, plus the Eastern Ontario contract correction and the job-location address fallback, which are ready for release). Captured 2026-10-16.
- Office: a fresh office built by the real database migrations on a temporary database; **synthetic data only**. No production database was read or changed.
- Story job: **Harbour Lane Pool Deck**, 48 Harbour Lane, Merrickville, ON — client **Morgan Ellis** (fictional). Other clients in the list (Priya Nair, Dan and Claire Roy, Rideau Valley Rentals) are fictional. All emails end in `example.invalid`. Supplier: BMR Winchester (synthetic account). Signed-in office user: "Brayman Office".
- The pool-deck geometry comes from the synthetic J1 pool-deck model used by the takeoff tests (a deck layout only; no customer name, address or contact). It is the only model the pool-deck takeoff and drawing engines accept.
- Every step was done through the real screens (forms filled and buttons pressed in Chromium), except: the construction model was loaded with the product's own save function (the office enters such models from a source drawing), and the supplier, contract package and three extra clients were seeded.
- Viewports: desktop 1440 × 900, phone 390 × 844, both at 2× pixel density (PNG). Browser chrome is not included (headless capture). Icons and the IBM Plex Sans font are the same versions the live site loads (bootstrap-icons 1.11.3; IBM Plex Sans), served locally because the capture machine cannot reach the CDN.

Files: `assets/screenshots/<chapter>/` (PNG), `assets/documents/` (original PDFs) and `assets/documents/pages/` (page renders), `assets/catalogue.csv` (one row per image: screen or document, chapter, product SHA, capture date, viewport, fixture, approval status, note), `storybook-contact-sheet.pdf`.

## Subjects requested and where they are

| # | Subject | Files |
|---|---|---|
| 01 | Home dashboard — desktop | 01-home-dashboard-desktop-1440.png<br>01-home-dashboard-full-desktop-1440.png |
| 02 | Home dashboard — mobile | 02-home-dashboard-full-mobile-390.png<br>02-home-dashboard-mobile-390.png |
| 03 | Installed PWA icon / launch | 03-app-icons.png |
| 04 | Mobile navigation | 04-mobile-navigation-calculators-mobile-390.png<br>04-mobile-navigation-mobile-390.png |
| 05 | Clients list | 05-clients-list-desktop-1440.png<br>05-clients-list-mobile-390.png |
| 06 | New Client | 06-new-client-desktop-1440.png |
| 07 | Start New Project | 07-start-new-project-desktop-1440.png |
| 08 | Project overview | 08-project-overview-desktop-1440.png<br>08-project-overview-full-desktop-1440.png<br>08-project-overview-mobile-390.png<br>08-projects-list-desktop-1440.png |
| 09 | Construction information | 09-construction-information-desktop-1440.png |
| 10 | Project Plans | 10-project-plans-desktop-1440.png |
| 11 | Concrete calculator | 11-concrete-desktop-1440.png<br>11-concrete-mobile-390.png |
| 12 | Stair calculator and diagram | 12-stairs-and-diagram-desktop-1440.png<br>12-stairs-and-diagram-mobile-390.png |
| 13 | ICF calculator | 13-icf-wall-desktop-1440.png<br>13-icf-wall-mobile-390.png |
| 14 | Wall framing calculator | 14-wall-framing-desktop-1440.png<br>14-wall-framing-mobile-390.png |
| 15 | Roofing calculator | 15-roofing-desktop-1440.png<br>15-roofing-mobile-390.png |
| 16 | Material takeoff | 16-material-takeoff-desktop-1440.png |
| 17 | Purchasing quantities | 17-purchasing-quantities-desktop-1440.png |
| 18 | Construction drawing | 18-construction-drawings.pdf<br>18-construction-drawings-desktop-1440.png<br>18-construction-drawings-page-1.png<br>18-construction-drawings-page-2.png<br>18-construction-drawings-page-3.png<br>18-construction-drawings-page-4.png<br>18-construction-drawings-page-5.png<br>18-construction-drawings-page-6.png<br>18-construction-drawings-page-7.png |
| 19 | BMR supplier request PDF | 19-bmr-supplier-request.pdf<br>19-supplier-request-issued-desktop-1440.png<br>19-bmr-supplier-request-page-1.png<br>19-bmr-supplier-request-page-2.png<br>19-bmr-supplier-request-page-3.png |
| 20 | Supplier price-entry screen | 20-supplier-price-entry-desktop-1440.png |
| 21 | Supplier price review | 21-supplier-price-review-desktop-1440.png<br>21-approved-costs-to-estimate-desktop-1440.png |
| 22 | Cost approval | 22-cost-approval-approved-desktop-1440.png<br>22-cost-approval-before-desktop-1440.png<br>22-costing-review-before-approval-desktop-1440.png<br>22-scope-delivery-review-desktop-1440.png |
| 23 | Labour hours and pricing | 23-labour-hours-desktop-1440.png |
| 24 | Estimate totals | 24-estimate-totals-desktop-1440.png<br>24-estimate-totals-mobile-390.png |
| 25 | Estimate detail | 25-estimate-detail-desktop-1440.png<br>25-estimate-detail-full-desktop-1440.png |
| 26 | Customer estimate PDF | 26-customer-estimate.pdf<br>26-customer-estimate-page-1.png |
| 27 | Customer proposal PDF | 27-customer-proposal.pdf<br>27-proposal-issued-desktop-1440.png<br>27-customer-proposal-page-1.png<br>27-customer-proposal-page-2.png<br>27-customer-proposal-page-3.png<br>27-customer-proposal-page-4.png |
| 28 | Contract review and signing | 28-generated-contract.pdf<br>28-contract-executed-desktop-1440.png<br>28-contract-review-desktop-1440.png<br>28-contract-sent-for-signature-desktop-1440.png<br>28-signer-consent-and-sign-mobile-390.png<br>28-signer-signed-mobile-390.png<br>28-generated-contract-page-1.png<br>28-generated-contract-page-2.png<br>28-generated-contract-page-3.png |
| 29 | Executed contract PDF | 29-executed-contract.pdf<br>29-executed-contract-page-1.png<br>29-executed-contract-page-2.png<br>29-executed-contract-page-3.png<br>29-executed-contract-page-4.png |
| 30 | Company Calendar | 30-company-calendar-desktop-1440.png |
| 31 | Project schedule / work plan | 31-project-work-plan-desktop-1440.png |
| 32 | Time and actual costs | 32-estimated-versus-actual-desktop-1440.png<br>32-time-entry-desktop-1440.png |
| 33 | Change order | 33-change-order-desktop-1440.png |
| 34 | Project closeout | 34-project-closed-desktop-1440.png<br>34-project-closeout-desktop-1440.png<br>34-projects-closed-list-desktop-1440.png<br>34-punch-list-desktop-1440.png |
| 35 | Calculator overview / montage | 35-calculator-montage.png<br>35a-footing-desktop-1440.png<br>35a-footing-mobile-390.png<br>35b-siding-desktop-1440.png<br>35b-siding-mobile-390.png<br>35c-drywall-desktop-1440.png<br>35c-drywall-mobile-390.png<br>35d-flooring-desktop-1440.png<br>35d-flooring-mobile-390.png<br>35e-employment-vs-entrepreneurship-desktop-1440.png<br>35e-employment-vs-entrepreneurship-mobile-390.png |
| — | Supplementary: footings, siding, drywall, flooring, Employment vs Entrepreneurship | 35a–35e in `ch08-calculators` |

## Missing or partial images (not fabricated)

1. **03 Installed app on a phone (home-screen icon, launch screen).** Needs a real iPhone or Android phone. Supplied instead: `03-app-icons.png`, the actual approved app icon files at true size. To capture: install from the live site (Safari → Share → Add to Home Screen) and take two phone screenshots.
2. **18 Construction drawing — in-page preview.** The drawing page embeds the PDF; a headless browser cannot render that viewer, so the screenshot shows an empty frame below the sheet list. Use the original drawing pages instead: `documents/pages/18-construction-drawings-page-1…7.png` (A-1 to G-1).
3. **31 and 32 were captured after closeout** (the hub section crops say "This Project is closed" in the punch list and walkthrough panels). If the chapter should show the job mid-way, these two need a recapture before closeout.
4. **Home greeting reads "Good morning, Brayman."** because the synthetic office user is "Brayman Office". If the Storybook should greet a person (for example Joel or Ben), the job must be re-run under that name — about 20 minutes.
5. **Supplier price review shows 17 lines outside the recordable total** ("Quantity not verified"). That is real behaviour: those takeoff lines need engineering or field verification before a final purchasing quantity. The office entered the verified quantities on the estimate.

## Findings while capturing (product, for Joel)

- **Corrected (ready for release):** contracts only resolved for Ottawa addresses — a Merrickville job could not get a contract. Now any Ontario municipality gets the Ontario contract (register §15.5b).
- **Corrected (ready for release):** the contract refused when the free-text "Project address" was blank even though the job location was complete. It now uses the job location.
- **Not changed — your decision:** a contract needs the estimate *version* status to be Issued or Accepted. Issuing or accepting the proposal does not change it, so the office must also set it on Edit Estimate (Version status → Issued). The Storybook job did that step. Recommendation: accepting a proposal marks its estimate version Accepted.

## Approved brand asset inventory (used as-is, not recreated)

| File | Size | SHA-256 (first 16) | Use |
|---|---|---|---|
| `app/static/branding/brayman-construction-logo.png` | 2083×833 | `948f96e08827f18d` | Brayman Construction logo (documents) |
| `app/static/branding/calibraytai-app-icon-180.png` | 180×180 | `4fe82fe5a6f1cce3` | Apple touch icon |
| `app/static/branding/calibraytai-app-icon-192.png` | 192×192 | `6a97220ea2a8bd4f` | App icon |
| `app/static/branding/calibraytai-app-icon-32.png` | 32×32 | `a1a78d2102304429` | Favicon size |
| `app/static/branding/calibraytai-app-icon-512.png` | 512×512 | `d98dd1f6d279c13a` | App icon |
| `app/static/branding/calibraytai-app-icon-maskable-512.png` | 512×512 | `2bedbfa356e82d89` | App icon (Android maskable) |
| `app/static/branding/calibraytai-logo-v1-dark.png` | 2500×1251 | `86a4d964cb31aa4e` | Sidebar logo (identical to the approved V1 dark reference) |
| `app/static/branding/calibraytai-logo-v2.png` | 2501×1251 | `b719bdd2fe7814d4` | Earlier logo file still in the repository; not used by the V1 screens |
| `docs/branding/calibraytai-opening-v1/storyboard/approved-logo-v1-dark-reference.png` | 2500×1251 | `86a4d964cb31aa4e` | Approved V1 reference |
| `app/static/branding/Cal_Assistant_Approved_Identity_2026-10-17.png` | 1281×1227 | `d8857f1bfef06c70` | **CAL — APPROVED ASSISTANT IDENTITY.** Approved 17 Oct 2026; frozen master, stored unchanged. Full SHA-256 `d8857f1bfef06c709390e8eaedfe437aea49983236c79843ee7845d561617e87`. Design record: [cal-assistant-approved-identity-2026-10-17.md](../branding/cal-assistant-approved-identity-2026-10-17.md). Not yet used by any screen. |

## Recommended placement by chapter

| Chapter | Images | Notes |
|---|---|---|
| 1. Morning at the office | 01, 02, 30, 04, 03 | Open on the phone Home screen (02), then desktop Home (01) and the Company Calendar (30); the menu (04) and the app icon (03) as small insets. |
| 2. A new customer calls | 06, 05, 07 | New Client form, the Clients list, then Start New Project for Harbour Lane. |
| 3. Understanding the job | 08, 09, 18, 10 | Project hub, construction information, the drawing set (use the PDF page renders), Project Plans. |
| 4. Takeoff and the supplier | 16, 17, 19, 20, 21, 22 | Takeoff first screen, the purchase-quantity table, the BMR Form 2 PDF pages, hand entry of the returned prices, review, cost approval. |
| 5. Building the estimate | 21 (approved costs), 22 (scope delivery), 23, 24, 25, 26 | Approved costs onto the estimate, who does the work, labour hours, totals, the estimate detail and the customer estimate PDF. |
| 6. Proposal and contract | 27, 28, 29 | Proposal issued and its PDF; the Contract page, the phone signing screens, executed status and the signed PDF's signing record. |
| 7. On the job | 31, 32, 33 | Work plan and schedule, time entry and estimated versus actual, the change order for the second gate. |
| 8. The calculators | 35 montage, 11–15, 35a–35e | Montage as the chapter opener; one or two calculators full page (stairs with its diagram is the strongest image). |
| 9. Closing the job | 34 | Punch list, close-project check, the closed hub and the Closed projects list. |

## Capture verification

- 91 screen images and 6 document page renders catalogued; 6 original PDFs (drawings, BMR request, customer estimate, proposal, generated contract, executed contract).
- Every image is a real application screen or an original PDF page, except two clearly labelled compositions made only from those: `35-calculator-montage.png` and `03-app-icons.png`.
- No real customer data. No production database or production site was used. No product code was changed for the capture.
- Application warnings and status messages were left on screen (for example "Engineering required" on takeoff lines and "PRELIMINARY — NOT FOR CONSTRUCTION" on the drawings).
