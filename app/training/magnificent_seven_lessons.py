"""Training for the Magnificent Seven everyday operations (Joel, 25 Oct 2026).

Two new modules, kept apart from contractor.py and field_crew.py so every existing lesson and acceptance-test key
stays exactly as it is (saved progress and UAT history are keyed by them; nothing here renames or moves one). They are
added when the Training Centre loads its content (app/training/content.py _load):

- Contractor module 16, "Every day: what needs my attention" — WHAT NEEDS MY ATTENTION? on Home, material requests
  into the existing supplier request, extra work into the existing change order, delivery problems, job updates and
  end-of-day reminders (owner and office), Suzanne's Receipts Inbox and QuickBooks Online (office), and the owner's
  QuickBooks connection and reminder settings (owner only).
- Field Crew module 9, "Field quick actions" — My Hours, Add Receipt, Need Materials, Extra Work, Confirm Delivery,
  Job Update and My Schedule on the iPhone, and the end-of-day reminder.

These lessons describe the release that ships them; they go live on the training site with that release, never
before. Every picture is a real screen captured by the release walk tools/release/evidence_magnificent_seven.mjs
(MAG7_SHOTS; app/static/training/shots/m7-*.png, synthetic data). Field lessons show no price, cost or wage.
"""

from __future__ import annotations

from typing import Tuple

from app.models.training import PATHWAY_CONTRACTOR, PATHWAY_FIELD_CREW, ROLE_FIELD, ROLE_OFFICE, ROLE_OWNER
from app.training.content import APP_FIELD, APP_OFFICE, APP_QUICKBOOKS, OFFICE_ROLES, Lesson, Module, Step, UatCase

O = APP_OFFICE
F = APP_FIELD
JOB = "Harbour Lane Pool Deck (training)"

C16 = Module(
    key="c16", pathway=PATHWAY_CONTRACTOR, number=16, title="Every day: what needs my attention",
    summary="Home starts with WHAT NEEDS MY ATTENTION?: real items from the jobs — time to approve, material requests, "
            "extra work, delivery problems, prices returned, receipts, job problems — each one click from the screen "
            "where it is done. What the crew sends from Field flows into the existing supplier requests, change "
            "orders and QuickBooks, entered once.",
    roles=OFFICE_ROLES,
    lessons=(
        Lesson(
            key="c16-attention", title="WHAT NEEDS MY ATTENTION? on Home",
            what="Read today's list and open each item straight on its working screen.",
            why="One place for the day's actions; nothing to search for, and nothing is approved for you.",
            steps=(
                Step(title="The list", app=O, where="Home", do="Read WHAT NEEDS MY ATTENTION? at the top",
                     expect="Each line says what, the job or person, the status and the date; Overdue or Today in "
                            "red or amber. GUIDED WIZARDS is still just below.",
                     if_wrong="Empty? Nothing needs you: 'Nothing needs your attention right now.'",
                     shot="m7-home-attention-desktop.png", endpoint="main.dashboard"),
                Step(title="On the iPhone", app=O, where="Home on your phone", do="Scroll to the top",
                     expect="The same list, one item under the other; nothing scrolls sideways.",
                     if_wrong="Turn the phone upright and reload.",
                     shot="m7-home-attention-phone.png", endpoint="main.dashboard"),
                Step(title="Open an item", app=O, where="Home → an item", do="Press the item (or its action)",
                     expect="The working screen itself: the request, the receipt, the delivery or the job update.",
                     if_wrong="More than four items? Press Show all.", shot="m7-material-review-desktop.png",
                     endpoint="operations.attention"),
                Step(title="Done means gone", app=O, where="Home", do="Come back after you deal with it",
                     expect="The item is no longer listed. The list is read from the records every time.",
                     if_wrong="Still there? It is not finished yet (for example the change order still waits for "
                              "the customer).", shot="m7-home-attention-desktop.png", endpoint="main.dashboard"),
            ),
            exercise=f"On the training site, open Home and open the first item of WHAT NEEDS MY ATTENTION? for {JOB}.",
        ),
        Lesson(
            key="c16-materials-deliveries", title="Material requests and deliveries from the site",
            what="Approve a crew's material request into a supplier request, and sort out a short delivery.",
            why="The crew asks once from the site; the request becomes the same supplier request, quote and purchase "
                "order you already use. Nothing is ordered until you order it.",
            steps=(
                Step(title="Check the request", app=O, where="Material request (from Home)",
                     do="Correct the quantity or unit, choose the catalogue item if it is missing, press Approve",
                     expect="Approved — the office is choosing the supplier.",
                     if_wrong="Not wanted? Type the reason and press Decline; the worker sees it.",
                     shot="m7-material-review-desktop.png", endpoint="operations.material_request"),
                Step(title="Send it to the supplier", app=O, where="The same page → Supplier and order",
                     do="Choose your supplier and press Send to the supplier for a price",
                     expect="Supplier request SRQ-… sent. The price comes back on the job's supplier requests, where "
                            "you approve the cost and place the order as always.",
                     if_wrong="'No Supplier Hub sign-in'? Add the store's user on Company → Suppliers.",
                     shot="m7-material-review-desktop.png", endpoint="supplier_office.project_requests"),
                Step(title="A short or damaged delivery", app=O, where="Home → Delivery short (or damaged)",
                     do="Read what the crew counted, then choose how it is resolved and Save",
                     expect="The rest is coming, a replacement, or accept and close the order with a note. The "
                            "order's own lines never change; it is only Delivered when nothing is outstanding.",
                     if_wrong="Cannot close? The supplier has not confirmed the order in CalibraytAI.",
                     shot="m7-delivery-exception-desktop.png", endpoint="operations.delivery"),
            ),
            exercise="Approve a training material request and send it to the training store.",
        ),
        Lesson(
            key="c16-extra-work-updates", title="Extra work, job updates and reminders",
            what="Turn extra work reported on site into a change order; read the day's job updates.",
            why="Extra work is written down with who asked and photos before it becomes a dispute; only an approved "
                "change order goes on the customer's bill.",
            steps=(
                Step(title="Review extra work", app=O, where="Home → Extra work reported",
                     do="Read it, look at the photos; ask the crew a question if needed",
                     expect="Who asked for it, the date, the photos. The crew answers in Field.",
                     if_wrong="Not extra? Press Part of the original work (nothing is charged).",
                     shot="m7-extra-work-review-desktop.png", endpoint="operations.extra_work_report"),
                Step(title="Prepare the change order", app=O, where="The same page",
                     do="Press Estimate it and prepare the change order, price it, save",
                     expect="The existing change order form with the extra work linked. The customer approves it "
                            "through the change order and its signing; the report then reads Approved by the customer.",
                     if_wrong="Nothing reaches the bill until the change order is approved.",
                     shot="m7-extra-work-review-desktop.png", endpoint="project_controls.create_change_order_route"),
                Step(title="Job updates", app=O, where="Home → Problem or delay reported (or the project page)",
                     do="Read the update; press Mark handled with what was done",
                     expect="'From CalibraytAI records (verified)' apart from what the crew reported. It is never sent "
                            "to the customer and creates no time or cost.",
                     if_wrong="Looking for older ones? The project page → From the field → Job updates.",
                     shot="m7-job-update-desktop.png", endpoint="operations.job_update"),
                Step(title="End-of-day reminders", app=O, where="Office → /operations/reminders",
                     do="Read the reminders made today and whether texts are switched on",
                     expect="One reminder a day per person, only when something is outstanding. 'Texts not switched "
                            "on' until texting is activated: the reminder is in the app.",
                     if_wrong="Nothing made? It is not reminder time yet, or nothing is outstanding.",
                     shot="m7-reminders-desktop.png", endpoint="operations.reminders"),
                Step(title="On the project", app=O, where="The project's page → From the field",
                     do="Scroll to From the field",
                     expect="The job's receipts, material requests, extra work, deliveries and job updates, with "
                            "their history.", if_wrong="Nothing yet? The crew has not sent anything for this job.",
                     shot="m7-hub-field-operations-desktop.png", endpoint="projects.view_project"),
            ),
            exercise=f"Open the extra work reported on {JOB} and prepare its change order (do not approve it).",
        ),
        Lesson(
            key="c16-receipts-quickbooks", title="Suzanne: receipts and QuickBooks Online",
            what="Review receipts from Field and send them to QuickBooks Online with the original image.",
            why="No box of receipts and no typing: the photo, the supplier, the amounts and the job are entered once. "
                "QuickBooks gets each receipt once, attached to the expense or bill already there when there is one.",
            steps=(
                Step(title="The Receipts Inbox", app=O, where="Accounting → Receipts Inbox",
                     do="Choose New", expect="Every receipt from Field: date, supplier, amount, job, who sent it, "
                     "the review and QuickBooks status.", if_wrong="Not listed? The crew's phone may still be "
                     "sending it; it arrives when the phone is back online.",
                     shot="m7-receipts-inbox-desktop.png", endpoint="accounting.receipts_inbox"),
                Step(title="Check and correct", app=O, where="A receipt",
                     do="Look at the original image; confirm the supplier, date, subtotal, tax, total and the job "
                        "(or Shop / Company Expense); link the purchase order if there is one; press Save review",
                     enter="Subtotal plus tax must equal the total",
                     expect="Reviewed.", if_wrong="Cannot read it? Press Mark Needs Attention with the reason.",
                     shot="m7-receipt-review-desktop.png", endpoint="accounting.receipt_detail"),
                Step(title="Approve for QuickBooks", app=O, where="The same receipt",
                     do="Press Approve for QuickBooks",
                     expect="'In QuickBooks: entered as a new expense …, with the receipt image', or 'attached to "
                            "the existing expense …' when QuickBooks already had it. Synced only when QuickBooks "
                            "confirms.", if_wrong="Several possible matches? Choose the right one, or Enter as a new "
                     "expense with the reason. Vendor not in QuickBooks? Type the QuickBooks vendor name.",
                     shot="m7-receipt-synced-desktop.png", endpoint="accounting.receipt_detail"),
                Step(title="Failed or not known", app=O, where="A receipt marked Sync Failed",
                     do="Read the reason, correct it, press Retry",
                     expect="Retry is safe: CalibraytAI sends the same request id and checks QuickBooks first, so "
                            "nothing is entered twice.", if_wrong="'Reconnect'? Ask the owner to reconnect QuickBooks.",
                     shot="m7-receipt-synced-desktop.png", endpoint="accounting.receipt_detail"),
                Step(title="In QuickBooks", app=APP_QUICKBOOKS, where="Expenses → the expense",
                     do="Open the expense CalibraytAI entered",
                     expect="The vendor, date, amounts, the job and the receipt image attached; the memo starts "
                            "'CalibraytAI receipt R-…'.", if_wrong="Not there? Check the receipt's QuickBooks history.",
                     shot="m7-qbo-reconciliation-desktop.png", endpoint="accounting.quickbooks_online_reconciliation"),
                Step(title="A job already in QuickBooks", app=O, where="Accounting → QuickBooks Online connection → "
                     "Projects in QuickBooks (or the item on Home)",
                     do="Read the job QuickBooks already has; if it is the same job, press This is the same customer / "
                        "project / job code",
                     expect="Matched once and used from then on (receipts too); nothing new is made in QuickBooks.",
                     if_wrong="Not the same job? Leave it and tell the owner; rename one of them so the names differ, "
                              "then Retry.",
                     shot="m7-qbo-projects-confirm-desktop.png", endpoint="accounting.quickbooks_projects"),
            ),
            exercise="Review and approve the training receipt from Kevin for the pool deck.",
            roles=(ROLE_OWNER, ROLE_OFFICE),
        ),
        Lesson(
            key="c16-owner-connection", title="For the owner: QuickBooks connection and reminder settings",
            what="See the QuickBooks Online connection and set the company's reminder time and working days.",
            why="Only the owner or a System Administrator connects QuickBooks or changes company settings.",
            steps=(
                Step(title="QuickBooks Online", app=O, where="Accounting → QuickBooks Online connection",
                     do="Read the connection and the accounts receipts go to",
                     expect="Connected (or what is still needed to switch it on), the expense and payment accounts, "
                            "the tax codes, and the transfer counts.",
                     if_wrong="Not switched on? That needs Joel's authorization and the Intuit app settings.",
                     shot="m7-qbo-connection-desktop.png", endpoint="accounting.quickbooks_online"),
                Step(title="Reminder settings", app=O, where="/operations/reminders",
                     do="Set the reminder time, the latest time and the working days, then Save settings",
                     expect="Reminders go out once a day between those times, on those days, in the company's time.",
                     if_wrong="Fields greyed out? Only the owner or a System Administrator changes them.",
                     shot="m7-reminders-desktop.png", endpoint="operations.reminders"),
                Step(title="Projects in QuickBooks", app=O, where="Accounting → QuickBooks Online connection → "
                     "Projects in QuickBooks",
                     do="Read each job's QuickBooks Online customer and project and its QuickBooks Time job code",
                     expect="A new or accepted job is made in QuickBooks once (the customer, the project under it, "
                            "the job code); renames follow; a closed job is made inactive, never deleted. Shop / "
                            "Company Work is one job code. CalibraytAI never changes accounting fields or makes a "
                            "transaction there.",
                     if_wrong="'Not switched on'? Project sync needs Joel's authorization (QBO_PROJECT_SYNC_ENABLED). "
                              "Failed? Read the reason and press Retry; retry never makes a second copy.",
                     shot="m7-qbo-projects-desktop.png", endpoint="accounting.quickbooks_projects"),
            ),
            exercise="As the training owner, open the QuickBooks Online page and the reminder settings (change nothing).",
            roles=(ROLE_OWNER,),
        ),
    ),
)

F09 = Module(
    key="f09", pathway=PATHWAY_FIELD_CREW, number=9, title="Field quick actions",
    summary="Field Today starts with seven big buttons: My Hours, Add Receipt, Need Materials, Extra Work, Confirm "
            "Delivery, Job Update and My Schedule. Each keeps the job you are on. Nothing shows money, and nothing "
            "you send is approved for the office.",
    roles=(ROLE_FIELD,),
    lessons=(
        Lesson(
            key="f09-quick-actions", title="The seven buttons", what="Find the quick actions on Field Today.",
            why="The day's paperwork is one press away, with the job already chosen.",
            steps=(
                Step(title="Field Today", app=F, where="Field → Today", do="Look at the top of the page",
                     expect="My Hours, Add Receipt, Need Materials, Extra Work, Confirm Delivery, Job Update, "
                            "My Schedule.", if_wrong="Not on Today? Press the logo.",
                     shot="m7-field-quick-actions-phone.png", endpoint="field.today"),
                Step(title="Which job", app=F, where="Any quick action", do="Press it",
                     expect="It opens on the job you are on. If you are on more than one, choose the job first.",
                     if_wrong="Job not listed? You are not booked on it; ask the office.",
                     shot="m7-field-quick-actions-phone.png", endpoint="field.choose_job"),
                Step(title="My Schedule on a Sunday", app=F, where="Field → This week",
                     do="Open the week; use Previous week and Next week to move",
                     expect="On a Sunday it opens on the coming Monday to Sunday (the button says Coming week), so "
                            "tomorrow's work and deliveries are there. Other days it opens on this week.",
                     if_wrong="Lost? Press This week (Coming week) to come back.",
                     shot="m7-field-week-phone.png", endpoint="field.week"),
            ),
            exercise="Open Field Today on the training site and find the seven buttons.",
        ),
        Lesson(
            key="f09-receipt", title="Add Receipt", what="Photograph a store receipt for the office.",
            why="No receipts in the truck: the office gets the photo the same day.",
            steps=(
                Step(title="Take the photo", app=F, where="Field Today → Add Receipt",
                     do="Choose the job (or Shop / Company Expense), press Take Photo of Receipt",
                     enter="Supplier and amount if you know them (optional)",
                     expect="The photo shows under the buttons.", if_wrong="Blurry? Remove it and take it again.",
                     shot="m7-receipt-capture-phone.png", endpoint="field.receipt"),
                Step(title="Save", app=F, where="Add Receipt", do="Press Save Receipt",
                     expect="'Receipt R-… saved. The office has it.' It shows under My receipts as Sent to the office.",
                     if_wrong="No signal? It stays on this phone and sends itself when you are back online.",
                     shot="m7-receipt-saved-phone.png", endpoint="field.receipt"),
            ),
            exercise="Add a training receipt for the pool deck.",
        ),
        Lesson(
            key="f09-materials-extra", title="Need Materials and Extra Work",
            what="Ask for material, and report extra work the customer asked for.",
            why="The office sees it right away; you see where it is.",
            steps=(
                Step(title="Need Materials", app=F, where="Field Today → Need Materials",
                     do="Pick the material (or type it), how many, the unit, when you need it; Send to the office",
                     expect="'Material request MR-… sent to the office.' My requests shows Approved, Sent to the "
                            "supplier, Ordered, Delivered as it moves.", if_wrong="Pressed twice? It is sent once.",
                     shot="m7-materials-form-phone.png", endpoint="field.materials"),
                Step(title="Extra Work", app=F, where="Field Today → Extra Work",
                     do="Describe it, who asked for it, the date, add photos; Record extra work",
                     expect="'Extra work recorded.' Nothing is charged until the customer approves a change order.",
                     if_wrong="A question from the office? Answer it under My extra work.",
                     shot="m7-extra-work-phone.png", endpoint="field.extra_work"),
                Step(title="Where it is", app=F, where="My requests", do="Open My requests",
                     expect="Each request and extra work with its status.", if_wrong="Not there? Check the job.",
                     shot="m7-my-requests-phone.png", endpoint="field.my_requests"),
            ),
            exercise="Ask for 10 training items and report one piece of extra work on the pool deck.",
        ),
        Lesson(
            key="f09-delivery-update", title="Confirm Delivery and Job Update",
            what="Say what arrived, and send the day's job update.",
            why="The office knows the same day what is short, damaged or needed tomorrow.",
            steps=(
                Step(title="Confirm Delivery", app=F, where="Field Today → Confirm Delivery → the order",
                     do="Choose Received, Short or Damaged; count each line; add a note and photos; Save",
                     expect="Received with empty boxes means everything due arrived. Short or Damaged goes to the "
                            "office.", if_wrong="Order not listed? It is not ordered yet, or already delivered.",
                     shot="m7-delivery-short-phone.png", endpoint="field.delivery_confirm"),
                Step(title="Job Update", app=F, where="Field Today → Job Update",
                     do="Check what CalibraytAI filled in, answer the three questions, Save Job Update",
                     expect="'Job update saved to the project.' Hours stay on My Hours; this creates no time.",
                     if_wrong="Saved twice? The second one replaces your answers.",
                     shot="m7-job-update-phone.png", endpoint="field.job_update"),
                Step(title="The end-of-day reminder", app=F, where="Field Today",
                     do="Read Before you finish today", expect="Only what is still to do; it disappears as you do it. "
                     "'Texts not switched on' means it is in Field only.",
                     if_wrong="Want a text too? Field → Texts → Also text me my end-of-day reminder.",
                     shot="m7-field-reminder-phone.png", endpoint="field.today"),
            ),
            exercise="Confirm the training delivery as Short (2 missing) and send today's job update.",
        ),
    ),
)

MODULES: Tuple[Module, ...] = (C16, F09)


def _c(key, title, start, action, expected, roles=OFFICE_ROLES):
    return UatCase(key=key, pathway=PATHWAY_CONTRACTOR, module_key="c16", title=title, start=start, action=action,
                   expected=expected, roles=roles)


def _f(key, title, start, action, expected):
    return UatCase(key=key, pathway=PATHWAY_FIELD_CREW, module_key="f09", title=title, start=start, action=action,
                   expected=expected, roles=(ROLE_FIELD,))


UAT_CASES: Tuple[UatCase, ...] = (
    _c("uat-c16-attention", "One click to the action", "Home → WHAT NEEDS MY ATTENTION?",
       "Open the first item, deal with it, come back to Home.",
       "The item opens its working screen (not another list) and is gone once it is done."),
    _c("uat-c16-materials", "Material request to the supplier", "Home → a Material request",
       "Change the quantity, approve it, send it to the training store.",
       "Supplier request sent; the worker's My requests says Asked the supplier for a price; nothing is ordered."),
    _c("uat-c16-extra-work", "Extra work to a change order", "Home → Extra work reported",
       "Ask the crew a question; after the answer, prepare the change order.",
       "The change order form opens with the extra work linked; nothing is billed until it is approved."),
    _c("uat-c16-delivery", "Short delivery resolved", "Home → Delivery short",
       "Choose The rest is coming and save.",
       "The item leaves Home; the order stays open until the rest is received."),
    _c("uat-c16-receipt", "Receipt to QuickBooks once", "Accounting → Receipts Inbox → a New receipt",
       "Save the review, approve it; then try to approve it again.",
       "Confirmed by QuickBooks with the image attached; it cannot be approved again; Reconciliation lists it once.",
       roles=(ROLE_OWNER, ROLE_OFFICE)),
    _c("uat-c16-receipt-existing", "Receipt already in QuickBooks", "A receipt matching an expense entered by hand",
       "Approve it.", "'attached to the existing expense …'; no second expense in QuickBooks.",
       roles=(ROLE_OWNER, ROLE_OFFICE)),
    _c("uat-c16-project-sync", "A new job into QuickBooks once", "Projects → New project (training company)",
       "Create the job; open Projects in QuickBooks; press Check all projects now twice.",
       "One customer and one project in QuickBooks Online and one job code in QuickBooks Time; the second check "
       "makes nothing new. A job QuickBooks already had waits for This is the same project.",
       roles=(ROLE_OWNER, ROLE_OFFICE)),
    _f("uat-f09-sunday-week", "My Week on a Sunday", "Field → This week, on a Sunday",
       "Open the week; press Next week, then Coming week.",
       "It opens on the coming Monday to Sunday with tomorrow's work; Coming week brings you back."),
    _f("uat-f09-receipt-offline", "Receipt without a signal", "Field Today → Add Receipt",
       "Turn on Airplane Mode, take and save a receipt, then turn Airplane Mode off.",
       "'Saved on this phone' first, then 'Receipt R-… saved'; one receipt under My receipts."),
    _f("uat-f09-materials", "Need Materials status", "Field Today → Need Materials",
       "Send a request; open My requests after the office approves it.",
       "Sent to the office, then Approved / Sent to the supplier. No money is shown."),
    _f("uat-f09-delivery", "Short delivery", "Field Today → Confirm Delivery",
       "Choose Short, enter the counts, add a note and a photo, save.",
       "Recorded; the office has it. No money is shown on the order."),
    _f("uat-f09-job-update", "Job update", "Field Today → Job Update",
       "Answer the three questions and save.",
       "Saved to the job; My Hours is unchanged; the reminder no longer lists the job update."),
)


def attach(modules, uat_cases):
    """c16 after the last contractor module and f09 after the last Field Crew module, their tests likewise.
    Everything else is returned unchanged. Idempotent."""
    out = list(modules)
    keys = {m.key for m in out}
    for module in MODULES:
        if module.key in keys:
            continue
        last = max((i for i, m in enumerate(out) if m.pathway == module.pathway), default=len(out) - 1)
        out.insert(last + 1, module)
    cases = list(uat_cases)
    present = {c.key for c in cases}
    for case in UAT_CASES:
        if case.key in present:
            continue
        last = max((i for i, c in enumerate(cases) if c.pathway == case.pathway), default=len(cases) - 1)
        cases.insert(last + 1, case)
    return tuple(out), tuple(cases)
