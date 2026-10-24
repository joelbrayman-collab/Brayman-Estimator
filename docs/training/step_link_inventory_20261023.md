# Lesson step buttons and Workflow map Back button (23 Oct 2026)

Joel: never invent a calculator; use the existing calculators and forms. Wherever a step asks the trainee to fill in
information, one button in the step lands directly on the right page with the cursor in the field, and one click
takes them back to the same lesson step.

How it works
- `app/training/links.py` lists each (lesson, step) and the page it opens. A button shows only when the page exists
  for that trainee (their own Harbour Lane job, the request sent to their own store, and so on).
- The button adds `tc_back` (the lesson step) and `tc_focus` (the field) to the address. On the training site, every
  page then shows "Back to the lesson step" in the training bar and as a floating button, and puts the cursor in the
  field (`app/static/training/site-bar.js`). The way back is cleared when the trainee is back in the Training Centre.
- The pages open in the same tab. Ticks, lesson order, exercise IDs and "I did this step" are unchanged.
- Clicks before = the menu steps in the step's own "Go to" directions (not counting finding the lesson). Clicks after = 1.

## Steps with a button (60)

| Lesson | Step | Button and page it opens | Clicks before | Clicks after |
|---|---|---|---|---|
| c02-company-brand | 2. Fill in the details | Complete the brand profile [settings.brand_profile] | 1+ | 1 |
| c02-pricing-hst | 2. Start a new draft | Complete the pricing draft [pricing_engine.create_policy] | 1+ | 1 |
| c02-people | 2. Add a person | Complete the Add a person page [people_access.new] | 1+ | 1 |
| c02-crews | 2. Name the crew | Complete the Add crew page [organization_crew.new] | 1+ | 1 |
| c04-invoices | 3. A change order | Complete the invoice page [accounting.new_invoice] | 2+ | 1 |
| c04-bills-and-check | 3. Check QuickBooks | Open Check QuickBooks [accounting.reconcile] | 2+ | 1 |
| c05-appointments | 2. Fill in the site visit | Complete the appointment page [schedule.new_appointment] | 1+ | 1 |
| c05-appointments | 4. A personal appointment | Complete the appointment page [schedule.new_appointment] | 2+ | 1 |
| c06-clients | 2. A new client | Complete the New Client page [clients.create_client] | 2+ | 1 |
| c06-project-setup | 2. Job location | Complete the job location [projects.edit_project_location] | 2+ | 1 |
| c06-existing-jobs | 1. Start a project | Complete the New Project page [projects.create_project] | 2+ | 1 |
| c06-existing-jobs | 2. The required choices | Complete the New Project page [projects.create_project] | 2+ | 1 |
| c07-plans | 2. Choose the PDF | Complete the plan upload page [plan_intelligence.upload_plan] | 1+ | 1 |
| c07-concrete-calculator | 1. Open the calculator | Open the concrete calculator [calculators.concrete] | 2+ | 1 |
| c07-concrete-calculator | 2. Calculate | Open the concrete calculator [calculators.concrete] | 1+ | 1 |
| c07-deck-takeoff | 2. Product facts | Complete the product facts page [deck_takeoff.review] | 2+ | 1 |
| c08-suppliers | 2. Give a sign-in | Complete the Suppliers page [supplier_office.suppliers] | 3+ | 1 |
| c08-suppliers | 3. Add a supplier | Complete the Suppliers page [supplier_office.suppliers] | 2+ | 1 |
| c08-concrete-request | 2. Fill in the concrete | Open the concrete calculator [calculators.concrete]; Complete the concrete request [supplier_office.project_requests] | 2+ | 1 |
| c08-place-order | 1. Fill in the order | Complete the order page [supplier_office.project_requests] | 4+ | 1 |
| c09-new-estimate | 2. Save the estimate | Complete the New Estimate page [estimates.create_estimate_route] | 1+ | 1 |
| c09-new-estimate | 4. Add a section | Complete the estimate page [estimates.view_version] | 2+ | 1 |
| c09-new-estimate | 5. Add the lines | Complete the estimate page [estimates.view_version] | 2+ | 1 |
| c09-scope-delivery-costing | 2. Choose and approve | Complete the Scope Delivery Review [scope_delivery.review] | 1+ | 1 |
| c10-proposal-template | 2. Fill and save | Complete the template page [proposal_templates.create_template] | 1+ | 1 |
| c11-schedule-crew | 2. Add the work item | Complete the project work page [work_structure.project_work_plan] | 2+ | 1 |
| c11-schedule-crew | 3. Add an activity | Complete the project work page [work_structure.project_work_plan] | 2+ | 1 |
| c11-schedule-crew | 5. Set dates | Complete the Set dates page [schedule.new_item] | 2+ | 1 |
| c11-capture | 1. Open Capture | Open Capture [field.capture] | 3+ | 1 |
| c11-extra-work | 1. Open Extra work | Complete the Extra work page [field.extra_work] | 3+ | 1 |
| c11-field-time | 1. Enter time | Complete the time page [field.time_entry] | 3+ | 1 |
| c11-office-review | 4. Mark the concrete delivered | Open the concrete request [supplier_office.project_requests] | 4+ | 1 |
| c11-change-order | 2. New Change Order | Complete the New Change Order page [project_controls.create_change_order_route] | 3+ | 1 |
| c12-invoice-closeout | 2. Final invoice | Complete the invoice page [accounting.new_invoice] | 3+ | 1 |
| f05-send-time | 1. Open Time | Complete the time page [field.time_entry] | 2+ | 1 |
| f05-send-time | 3. Type your hours and a note | Complete the time page [field.time_entry] | 2+ | 1 |
| f05-extra-work | 2. Say what they asked for | Complete the Extra work page [field.extra_work] | 1+ | 1 |
| f06-capture | 2. Type a note | Open Capture [field.capture] | 2+ | 1 |
| f06-capture | 3. Add a photo | Open Capture [field.capture] | 2+ | 1 |
| s02-texts | 2. Your mobile | Complete the text settings [supplier_portal.account] | 2+ | 1 |
| s02-texts | 3. Also text someone who does not sign in | Complete the text settings [supplier_portal.account] | 2+ | 1 |
| s04-material-quote | 1. Enter SKU, Unit cost and Discount % | Complete this quote page [supplier_portal.request_detail] | 2+ | 1 |
| s04-material-quote | 2. The same form on your phone | Complete this quote page [supplier_portal.request_detail] | 1+ | 1 |
| s04-material-quote | 3. Fill the bottom of the form | Complete this quote page [supplier_portal.request_detail] | 2+ | 1 |
| s04-concrete-quote | 3. Fill Your quote | Complete this quote page [supplier_portal.request_detail] | 2+ | 1 |
| s05-confirm | 1. Confirm the order | Complete the order page [supplier_portal.request_detail] | 3+ | 1 |
| s05-confirm | 3. Or report a problem | Complete the order page [supplier_portal.request_detail] | 3+ | 1 |
| s06-ask-change | 1. Fill Change the delivery | Complete the delivery change [supplier_portal.request_detail] | 3+ | 1 |
| s06-delivered | 1. Open Mark delivered | Complete the delivery page [supplier_portal.request_detail] | 2+ | 1 |
| s07-sku-reuse | 3. Check each SKU on your phone | Complete this quote page [supplier_portal.request_detail] | 1+ | 1 |
| s08-what-exists | 1. Contractor requests: typed on each quote | Complete this quote page [supplier_portal.request_detail] | 2+ | 1 |
| s08-settings | 1. Fill Quote settings | Complete the Quote settings page [supplier_pro_desk.settings] | 4+ | 1 |
| s08-price-file | 2. Load it | Complete the price file page [supplier_pro_desk.prices] | 4+ | 1 |
| s08-standards-matches | 1. Add a standard building | Complete the standard building page [supplier_pro_desk.standards] | 4+ | 1 |
| s08-standards-matches | 3. Match a product to a line | Complete the quotation page [supplier_pro_desk.quote] | 4+ | 1 |
| s09-quick-quote | 3. 1 · Customer | Complete the Quick Quote page [supplier_pro_desk.quick] | 4+ | 1 |
| s09-quick-quote | 4. Size, doors, floor and the sketch | Complete the Quick Quote page [supplier_pro_desk.quick] | 2+ | 1 |
| s09-quick-quote | 6. Or a detailed quotation | Complete the Detailed quotation page [supplier_pro_desk.new_quote] | 4+ | 1 |
| s09-price-issue | 3. 5 · Pricing | Complete the quotation page [supplier_pro_desk.quote] | 2+ | 1 |
| s10-pro-desk-cycle | 1. Quick Quote | Complete the Quick Quote page [supplier_pro_desk.quick] | 4+ | 1 |

## Fill-in style steps with no button (54) and why

| Lesson | Step | Page | Reason |
|---|---|---|---|
| c01-welcome | 2. Sign in | auth.login | You are already on the page (sign-in, password or Training Centre screen) |
| c01-welcome | 3. Choose the job you do | training.home | You are already on the page (sign-in, password or Training Centre screen) |
| c01-welcome | 6. Ask the Tutor | training.lesson | You are already on the page (sign-in, password or Training Centre screen) |
| c01-sign-in | 1. Open the sign-in page | auth.login | You are already on the page (sign-in, password or Training Centre screen) |
| c01-sign-in | 3. Change your password | auth.change_password | You are already on the page (sign-in, password or Training Centre screen) |
| c01-sign-in | 4. Sign in with the new password | main.dashboard | You are already on the page (sign-in, password or Training Centre screen) |
| c01-find-your-way | 2. Learn the menu | main.dashboard | Reading or navigation, not a form |
| c01-find-your-way | 3. Open Help on a page | main.dashboard | Reading or navigation, not a form |
| c01-forgot-password | 1. Ask for reset instructions | auth.forgot_password | You are already on the page (sign-in, password or Training Centre screen) |
| c01-forgot-password | 3. Choose the new password | auth.reset_password | You are already on the page (sign-in, password or Training Centre screen) |
| c02-pricing-hst | 1. Open How we price | pricing_engine.index | Choosing or reading only, not filling in values |
| c02-access | 2. Give an access area | people_access.detail | The page is made by an earlier step in the lesson, so its address differs for every trainee; no fixed page to link |
| c02-crews | 3. Add people with dates | organization_crew.detail | The page is made by an earlier step in the lesson, so its address differs for every trainee; no fixed page to link |
| c03-invite-worker | 1. Send the link again if needed | people_access.detail | The page is made by an earlier step in the lesson, so its address differs for every trainee; no fixed page to link |
| c03-activate-phone | 2. Choose your password | auth.reset_password | You are already on the page (sign-in, password or Training Centre screen) |
| c03-activate-phone | 3. Sign in | auth.login | You are already on the page (sign-in, password or Training Centre screen) |
| c04-accounting-page | 2. Read Files for QuickBooks | accounting.index | Choosing or reading only, not filling in values |
| c04-quickbooks-setup | 2. Import Customers in QuickBooks | (none) | Opens from a link emailed to the customer or person, so there is no fixed page to link |
| c04-invoice-export | 2. Import in QuickBooks | (none) | Happens in another program (QuickBooks) or on the phone with no matching page in the training site |
| c04-bills-and-check | 2. Export the Invoice List | (none) | Happens in another program (QuickBooks) or on the phone with no matching page in the training site |
| c05-appointments | 1. New appointment | schedule.new_appointment | Choosing or reading only, not filling in values |
| c07-field-drawings | 1. Choose the job | field.project_confirm | Choosing or reading only, not filling in values |
| c08-approve-quote | 1. BMR returns the quote | supplier_portal.request_detail | Choosing or reading only (no values to fill in), or the request does not exist until the contractor sends it |
| c09-pricing | 2. Check the totals | estimates.view_version | Choosing or reading only, not filling in values |
| c10-customer-acceptance | 2. Accept | proposal_link.view | Opens from a link emailed to the customer or person, so there is no fixed page to link |
| c11-schedule-crew | 6. Assign the crew | schedule.edit_item | The page is made by an earlier step in the lesson, so its address differs for every trainee; no fixed page to link |
| c11-field-today | 3. Choose the project | field.projects | Choosing or reading only, not filling in values |
| c11-office-review | 3. Approve or return | time_entry.detail | The page is made by an earlier step in the lesson, so its address differs for every trainee; no fixed page to link |
| c11-change-order | 3. Add the line | project_controls.view_change_order | The page is made by an earlier step in the lesson, so its address differs for every trainee; no fixed page to link |
| c11-change-order | 4. Approve | project_controls.view_change_order | The page is made by an earlier step in the lesson, so its address differs for every trainee; no fixed page to link |
| c12-final-acceptance | 2. Run it and record the result | training.uat_case | You are already on the page (sign-in, password or Training Centre screen) |
| f01-start-training | 2. Sign in | auth.login | You are already on the page (sign-in, password or Training Centre screen) |
| f01-activate | 2. Choose your password | auth.reset_password | You are already on the page (sign-in, password or Training Centre screen) |
| f01-activate | 3. Sign in with it | auth.login | You are already on the page (sign-in, password or Training Centre screen) |
| f01-password | 2. Change it | auth.change_password | You are already on the page (sign-in, password or Training Centre screen) |
| f01-password | 3. Forgot it? | auth.forgot_password | You are already on the page (sign-in, password or Training Centre screen) |
| f02-confirm-job | 1. Choose Project | field.projects | Choosing or reading only, not filling in values |
| f04-drawings | 1. Choose the job | field.project_confirm | Choosing or reading only, not filling in values |
| f05-company-time | 2. Pick the work and send | (none) | Happens in another program (QuickBooks) or on the phone with no matching page in the training site |
| f07-troubleshooting | 4. 'This Project is closed.' | (none) | Happens in another program (QuickBooks) or on the phone with no matching page in the training site |
| s01-sign-in | 2. Sign in | supplier_portal.login | You are already on the page (sign-in, password or Training Centre screen) |
| s01-register | 1. Choose the job you do | training.home | You are already on the page (sign-in, password or Training Centre screen) |
| s01-password | 1. Ask for a password link | auth.forgot_password | You are already on the page (sign-in, password or Training Centre screen) |
| s01-password | 3. Choose the new password | auth.reset_password | You are already on the page (sign-in, password or Training Centre screen) |
| s02-users | 2. The new person chooses a password | auth.reset_password | You are already on the page (sign-in, password or Training Centre screen) |
| s02-branding | 1. Branding is saved by the contractor's office | supplier_office.suppliers | Choosing or reading only, not filling in values |
| s03-dashboard | 2. Choose the period | supplier_portal.supplier_dashboard | Choosing or reading only (no values to fill in), or the request does not exist until the contractor sends it |
| s04-concrete-quote | 1. How Ben sends concrete | supplier_office.project_requests | Choosing or reading only, not filling in values |
| s07-demand | 1. Open Material demand | supplier_portal.supplier_demand | Choosing or reading only (no values to fill in), or the request does not exist until the contractor sends it |
| s08-what-exists | 2. PRO Desk: the store's own price file | supplier_pro_desk.index | Choosing or reading only, not filling in values |
| s08-price-file | 1. Prepare the CSV | supplier_pro_desk.prices | Choosing or reading only, not filling in values |
| s09-customer-link | 3. The customer accepts | supplier_quote_link.view | Opens from a link emailed to the customer or person, so there is no fixed page to link |
| s09-order | 2. Enter it in the store system | supplier_pro_desk.order_csv | The page is made by an earlier step in the lesson, so its address differs for every trainee; no fixed page to link |
| s10-acceptance | 2. Run one test and record it | training.uat_case | You are already on the page (sign-in, password or Training Centre screen) |
