"""Training for the four Guided Workflow Wizards (Joel, 24 Oct 2026).

Two new modules, kept apart from contractor.py and supplier.py so every existing lesson and acceptance-test key stays
exactly as it is (saved progress and UAT history are keyed by them; nothing here renames or moves one). They are
added when the Training Centre loads its content (app/training/content.py _load):

- Contractor module 15, "Guided Wizards" — Start a New Project, Guided Estimating and
  Manage a Project, Save & Exit / Resume, Continue manually, Ask the Tutor; for the contractor owner and office
  staff, with the owner's own lesson (closing a project, decisions only the owner or a System Administrator makes).
  For Ben's onboarding it follows module 13 (Guided Estimating); for Kevin's Contractor Review the estimating
  lesson is the same estimate as module 13, walked by the wizard.
- Supplier module 11, "The Supplier Pro Desk wizard" — a contractor request and a Quick Quote, step by step, for
  supplier owners, supplier administrators and PRO Desk staff.

Joel's decisions of 24 Oct 2026 are taught here: the optional Project Lead (Start a New Project step 6, Manage a
Project step 4; it gives no access), availability only from the supplier's own price file (otherwise "Availability
not confirmed"), and pickup or delivery "Arranged in the store's own system", never shown as done without a recorded
delivery.

These lessons describe the wizards in the release that ships them; they go live on the training site with that
release, never before. Every picture is a real screen captured by tools/training/capture_wizard_shots.mjs
(app/static/training/shots/w-*.png, from the synthetic wizard walk).
"""

from __future__ import annotations

from typing import Tuple

from app.models.training import PATHWAY_CONTRACTOR, PATHWAY_SUPPLIER, ROLE_OWNER
from app.training.content import ALL_SUPPLIER, APP_OFFICE, APP_SUPPLIER, OFFICE_ROLES, Lesson, Module, Step, UatCase

O = APP_OFFICE
SUP = APP_SUPPLIER
HOME = "Lakeview Wizard Home (training)"
CUSTOMER = "Jordan Avery (training)"
INITIALS = (" On the training site everyone shares one training company: add your initials to the project name "
            "(for example 'Lakeview Wizard Home (training) KF').")

C15 = Module(
    key="c15", pathway=PATHWAY_CONTRACTOR, number=15, title="Guided Wizards",
    summary="Home's GUIDED WIZARDS band offers three guided wizards — Start a New Project, Estimate a Project "
            "and Manage a Project — each with Continue manually beneath it. The wizard walks the real pages one "
            "task at a time and shows what each task still needs; nothing is entered twice and nothing is "
            "approved for you. Ben: after module 13. Kevin's Contractor Review: the estimating lesson.",
    roles=OFFICE_ROLES,
    lessons=(
        Lesson(
            key="c15-what-do-you-need", title="Home: Guided Wizards",
            what="Find the three guided wizards on Home, and the manual way beside each.",
            why="One press takes you to the work. The wizard is a guide over the same pages you already know.",
            steps=(
                Step(title="The three wizards", app=O, where="Home",
                     do="Read the dark-blue GUIDED WIZARDS band, under WHAT NEEDS MY ATTENTION?",
                     expect="Three gold buttons — Start a New Project, Estimate a Project and Manage a Project — each "
                            "with Continue manually beneath it; What are Wizards? explains them. Company Calendar is "
                            "beside the greeting at the top.",
                     if_wrong="Not on Home? Press Home at the top of the menu.",
                     shot="w-home-what-do-you-need-to-do-desktop.png", endpoint="main.dashboard"),
                Step(title="On the iPhone", app=O, where="Home on your phone",
                     do="Scroll to GUIDED WIZARDS",
                     expect="The same three wizards, one under the other; nothing scrolls sideways.",
                     if_wrong="Turn the phone upright and reload.",
                     shot="w-home-what-do-you-need-to-do-phone.png", endpoint="main.dashboard"),
                Step(title="Unfinished work", app=O, where="Home → Continue where you left off",
                     do="Look under the three wizards for Continue where you left off",
                     expect="One line for each wizard you left: Resume, what it is about, and the step you stopped on "
                            "(for example 'Step 2 of 7: What are we building?').",
                     if_wrong="Nothing listed? You have no wizard open. Start one.",
                     shot="w-home-what-do-you-need-to-do-desktop.png", endpoint="main.dashboard"),
            ),
            exercise="On the training site, open Home and find the three wizards, each with Continue manually beneath it.",
        ),
        Lesson(
            key="c15-new-project-wizard", title="Start a New Project, step by step",
            what="Set up a new home with the wizard in seven short tasks: customer, what is being built, where, "
                 "drawings, your role, who leads it, and a last look.",
            why="The project is made once, exactly as the New Project form makes it, and every later step reads "
                "the project's own records.",
            steps=(
                Step(title="Start the wizard", app=O, where="Home → Start a New Project",
                     do="Press Start a New Project",
                     expect="'Start a New Project · Step 1 of 7' with a thin progress bar, and one task: Who is the "
                            "customer? View all steps opens the list of the seven tasks.",
                     if_wrong="Opened the New Project form instead? That was Continue manually; go back to Home.",
                     shot="w-wizard1-customer-desktop.png", endpoint="wizards.start"),
                Step(title="Who is the customer?", app=O, where="Step 1",
                     do="Choose the customer and press Save & Continue",
                     enter=CUSTOMER,
                     expect="Nothing is chosen for you; Save & Continue with no customer says what is still needed.",
                     if_wrong="A new customer? Choose New customer and type the name (email, phone and address can "
                              "wait); Save & Continue saves the customer and goes straight on with that customer.",
                     shot="w-wizard1-customer-phone.png", endpoint="wizards.step"),
                Step(title="What are we building?", app=O, where="Step 2",
                     do="Type the project name, choose New Home Construction and press Save & Continue",
                     enter=f"{HOME} <initials>",
                     expect="Typing is saved by itself (Saved automatically). The commercial project type under More "
                            "details is filled in as New Build; you can change it.",
                     if_wrong="Refused? Name the project and choose what is being built.",
                     shot="w-wizard1-customer-desktop.png", endpoint="wizards.step"),
                Step(title="Where is the job? (creates the project)", app=O, where="Step 3",
                     do="Enter the job-site address (or tick Same as the customer's address) and press Save & Continue",
                     enter="Street, city or town, province, postal code",
                     expect="The project is created once and the wizard moves to the drawings. Going back shows the "
                            "project; nothing is created twice.",
                     if_wrong="An error about the commercial gate? Open 'Permit class and commercial decision gate'.",
                     shot="w-wizard1-location-desktop.png", endpoint="projects.create_project"),
                Step(title="Drawings", app=O, where="Step 4 (optional)",
                     do="Choose the plan PDF (or tick This job needs no drawings) and press Save & Continue",
                     expect="The drawing is uploaded to the project right here; no drawings yet is fine and is listed "
                            "on the last step as something to add later.",
                     if_wrong="Lost? Continue manually opens the plan page, which shows Return to the wizard.",
                     shot="w-wizard1-documents-desktop.png", endpoint="wizards.step"),
                Step(title="Your role", app=O, where="Step 5",
                     do="Choose General Contractor and press Save & Continue",
                     expect="The project's guided estimate starts. The construction stages (Internal, Subcontracted "
                            "or N/A) are decided in Guided Estimating, not here.",
                     if_wrong="Refused? Choose what work you are responsible for.",
                     shot="w-wizard1-role-desktop.png", endpoint="wizards.step"),
                Step(title="Who is leading it, and when?", app=O, where="Step 6 (optional)",
                     do="Choose the Project Lead from your company's people and press Save & Continue; add a site "
                        "visit or meeting if you have one",
                     enter="Project Lead: Ben (or the person who looks after the job)",
                     expect="'Project Lead: <name>'. The Project Lead is a name on the project only: it gives no "
                            "access and does not assign scheduled work or appointments. Unassigned is fine.",
                     if_wrong="Person not in the list? Only active people of your company are offered "
                              "(People & Access).",
                     shot="w-wizard1-lead-desktop.png", endpoint="wizards.step"),
                Step(title="Does this look right?", app=O, where="Step 7",
                     do="Read the summary, then press Finish and start estimating",
                     expect="Guided Estimating opens on the same project. Anything still missing (an email, the "
                            "drawings) is listed first, to add later.",
                     if_wrong="Not ready to estimate? Press Finish — estimate later.",
                     shot="w-wizard1-continue-desktop.png", endpoint="wizards.step"),
            ),
            exercise=f"Set up '{HOME} <initials>' for {CUSTOMER} with the wizard, as a New Home, General Contractor, "
                     "with yourself as Project Lead, then Finish and start estimating." + INITIALS,
        ),
        Lesson(
            key="c15-estimating-wizard", title="Guided Estimating with the wizard",
            what="Walk the estimate stage by stage to the proposal with the wizard.",
            why="The wizard shows, from the estimate itself, what is done and what is missing — the same Guided "
                "Estimating you learned in module 13, in order.",
            steps=(
                Step(title="Internal stages", app=O, where="Guided Estimating → Calculators for internal work",
                     do="Press Open <stage>, or the stage's calculator",
                     expect="'0 of 5 internal stages complete' until each stage is completed on its own page.",
                     if_wrong="Next refused? Complete each internal stage first.",
                     shot="w-wizard2-internal-desktop.png", endpoint="guided.stage"),
                Step(title="Subcontractor quotes", app=O, where="Steps 7 and 8",
                     do="Open each subcontracted stage, request and record the quote, select it and use its cost",
                     expect="Waiting for a quote never stops you: the step shows Waiting and you go on.",
                     if_wrong="A quote shows but the stage is not done? Press Use this cost on the line.",
                     shot="w-wizard2-internal-desktop.png", endpoint="guided.stage"),
                Step(title="Complete the internal cost estimate", app=O, where="Step 11",
                     do="Resolve every stage the step lists",
                     expect="'Internal cost estimate complete' with the direct cost. It is never a customer document.",
                     if_wrong="An allowance or no-cost decision is needed? See module 13.",
                     shot="w-wizard2-pricing-desktop.png", endpoint="guided.internal_cost"),
                Step(title="Approve the costing and price it", app=O, where="Step 12",
                     do="Press Approve the costing, then Apply the company pricing policy",
                     expect="Back on the same step: the selling price, the true gross margin and the customer total.",
                     if_wrong="No Approve button? A stage is still unresolved (step 11).",
                     shot="w-wizard2-pricing-phone.png", endpoint="guided.pricing"),
                Step(title="Ask the Tutor", app=O, where="Any wizard step → Help",
                     do="Open Help, type a question and press Ask",
                     expect="The answer appears on the step; you stay where you are.",
                     if_wrong="No answer? Read the step's own Help text above the question box.",
                     shot="w-wizard2-pricing-desktop.png", endpoint="help.ask_help"),
            ),
            exercise="Open Guided Estimating with the wizard on your training project and take it to the pricing step.",
        ),
        Lesson(
            key="c15-manage-project-wizard", title="Manage a Project with the wizard",
            what="Follow an accepted project from the schedule to closing.",
            why="Each step counts the real records (scheduled work, assignments, orders, deliveries, change orders, "
                "punch list) and says plainly when something is not switched on.",
            steps=(
                Step(title="Milestones and schedule", app=O, where="Manage a Project → step 3",
                     do="Press Schedule work for each work item",
                     expect="'1 of 5 work items scheduled', counting up as you schedule.",
                     if_wrong="'The work plan is not built'? Build it from the accepted estimate first.",
                     shot="w-wizard3-schedule-desktop.png", endpoint="schedule.new_item"),
                Step(title="Project Lead and people", app=O, where="Step 4",
                     do="Check the Project Lead (change it with Save Project Lead), then assign a person or crew to "
                        "each scheduled item",
                     expect="The Project Lead is listed first; it never counts as an assignment and gives no access. "
                            "The same Project Lead shows on the Project Hub and on the project's card in the "
                            "Company Calendar.",
                     if_wrong="'0 of N scheduled items assigned'? Open each item and assign a person or crew.",
                     shot="w-wizard3-people-desktop.png", endpoint="wizards.step"),
                Step(title="The Project Lead on the Project Hub", app=O, where="The project's page → Project",
                     do="Read Project Lead beside the client; press Change to choose someone else or Unassigned",
                     expect="The Project Lead's name (or Unassigned). The same name is on the project's card in "
                            "the Company Calendar.",
                     if_wrong="No Change link? Open the project from Projects.",
                     shot="w-hub-project-lead-desktop.png", endpoint="projects.view_project"),
                Step(title="People, texts and QuickBooks Time", app=O, where="Steps 4 and 9",
                     do="Assign a person or crew to each scheduled item",
                     expect="The steps also say whether schedule texts and QuickBooks Time are switched on.",
                     if_wrong="Not switched on? That is the real status; tell the crew yourself.",
                     shot="w-wizard3-schedule-phone.png", endpoint="schedule.company"),
                Step(title="Orders, deliveries and changes", app=O, where="Steps 5 to 10",
                     do="Open Supplier requests and orders from the step",
                     expect="'2 of 3 requests ordered' style counts; only the office places an order.",
                     if_wrong="Nothing to order? The step says no line is bought by you.",
                     shot="w-wizard3-schedule-desktop.png", endpoint="supplier_office.project_requests"),
            ),
            exercise="On the training site, open Manage a Project on an accepted training project and schedule one "
                     "work item.",
        ),
        Lesson(
            key="c15-save-resume-manual", title="Save & Exit, Resume and Continue manually",
            what="Stop part way, come back later, or do a step on its own page.",
            why="Your place and your typing are kept; the records are the same whichever way you work.",
            steps=(
                Step(title="Save & Exit", app=O, where="Any wizard step",
                     do="Press Save & Exit",
                     expect="Home, with the wizard under Continue where you left off.",
                     if_wrong="Closed the browser instead? Your typing was saved automatically; Resume it.",
                     shot="w-wizard1-customer-phone.png", endpoint="wizards.step"),
                Step(title="Resume", app=O, where="Home → Continue where you left off",
                     do="Press Resume <wizard>",
                     expect="The step you left, with what you typed.",
                     if_wrong="Not listed? Someone finished or stopped that wizard; start it again.",
                     shot="w-home-what-do-you-need-to-do-desktop.png", endpoint="wizards.resume"),
                Step(title="Continue manually and come back", app=O, where="Any wizard step",
                     do="Press Continue manually under the step, then Return to the wizard at the top of that page",
                     expect="The step's own page, then the same step again, showing the change you made.",
                     if_wrong="No Return to the wizard bar? Open the wizard from Home → Continue where you left off.",
                     shot="w-wizard3-schedule-desktop.png", endpoint="wizards.manual"),
            ),
            exercise="Start a wizard, Save & Exit, Resume it from Home, then use Continue manually and come back.",
        ),
        Lesson(
            key="c15-owner-decisions", title="For the owner: decisions the wizard leaves to you",
            what="See which steps only the owner (or a System Administrator) can finish.",
            why="The wizard never approves anything for anyone: the owner's decisions stay the owner's.",
            steps=(
                Step(title="Close the project", app=O, where="Manage a Project → Close the project",
                     do="Press Close the project when the work is done",
                     expect="The existing Close Project page. Office staff see 'Only the owner or a System "
                            "Administrator can close a project' instead of the button.",
                     if_wrong="Open punch list items? Close Project asks you to confirm them.",
                     shot="w-wizard3-close-desktop.png", endpoint="projects.close_project"),
                Step(title="No-cost decisions", app=O, where="Guided Estimating → a stage",
                     do="Open the stage from the wizard to record a no-cost decision",
                     expect="Only the owner or a System Administrator sees the form (module 13).",
                     if_wrong="Not the owner? Approve an allowance with its reason instead.",
                     shot="w-wizard2-internal-desktop.png", endpoint="guided.stage"),
            ),
            exercise="As the training owner, open the Close the project step of Manage a Project (do not close it).",
            roles=(ROLE_OWNER,),
        ),
    ),
)

S11 = Module(
    key="s11", pathway=PATHWAY_SUPPLIER, number=11, title="The Supplier Pro Desk wizard",
    summary="The Supplier Hub asks What do you need to do? The Supplier Pro Desk wizard takes a contractor's "
            "request, or a walk-in quotation from Quick Quote, through your prices, the quotation, the answer, "
            "the order and the delivery — on your own pages, with only what the contractor shared with you.",
    roles=ALL_SUPPLIER,
    lessons=(
        Lesson(
            key="s11-start-wizard", title="Start the wizard and choose the work",
            what="Open the wizard from Requests and choose a contractor request or a quotation.",
            why="One place shows what each request or quotation still needs.",
            steps=(
                Step(title="What do you need to do?", app=SUP, where="Supplier Hub → Requests",
                     do="Press Start Guided Wizard",
                     expect="Step 1, Open a request or start a quotation, with Quick Quote, New quotation and "
                            "Contractor requests.",
                     if_wrong="Not on Requests? Press your store's name at the top.",
                     shot="w-wizard4-open-desktop.png"),
                Step(title="Quick Quote", app=SUP, where="Step 1 → Quick Quote",
                     do="Press Quick Quote, fill the customer and building, press Price this building, then Return "
                        "to the wizard",
                     expect="The new quotation is listed in step 1; choose it and press Work on this.",
                     if_wrong="Not listed? Only your own open quotations and requests are shown.",
                     shot="w-wizard4-open-desktop.png"),
            ),
            exercise="On the supplier practice store, start the wizard and make a Quick Quote for a training customer.",
        ),
        Lesson(
            key="s11-quote-to-order", title="Prices, quotation, answer and order",
            what="Take the quotation to the order package with the wizard.",
            why="Each step reads the quotation itself: nothing is priced, issued or accepted for you.",
            steps=(
                Step(title="Availability", app=SUP, where="Step 5",
                     do="Read the Availability step",
                     expect="Only what your own price file says (for example 'In stock (supplier-reported)'); every "
                            "other product reads 'Availability not confirmed'. CalibraytAI never shows a quantity "
                            "on hand.",
                     if_wrong="Everything 'Availability not confirmed'? Your price file has no availability column; "
                              "check stock in your own system.",
                     shot="w-wizard4-availability-desktop.png"),
                Step(title="Your prices and terms", app=SUP, where="Step 6",
                     do="Open Price review and terms; price or leave out each line",
                     expect="'N line(s) priced from your price file' and the total. No points or rewards are "
                            "worked out in CalibraytAI.",
                     if_wrong="'No current price'? Load your price file or leave the line out with a reason.",
                     shot="w-wizard4-pricing-desktop.png"),
                Step(title="On the iPhone", app=SUP, where="Step 6 on your phone",
                     do="Open the same step on the phone",
                     expect="Compact, nothing scrolls sideways.",
                     if_wrong="Turn the phone upright and reload.",
                     shot="w-wizard4-pricing-phone.png"),
                Step(title="Issue, answer, order", app=SUP, where="Steps 8 to 10",
                     do="Issue the quotation, record the customer's answer, then press Make the order package",
                     expect="Each step turns Done when the quotation says so.",
                     if_wrong="Waiting? The customer has not answered yet; Save & Exit and come back.",
                     shot="w-wizard4-close-desktop.png"),
                Step(title="Pickup or delivery", app=SUP, where="Steps 11 and 12",
                     do="Record what the customer asked for (Pickup at the store or Delivery) and press Record",
                     expect="'Arranged in the store's own system' with the real status: the order package is ready; "
                            "the pickup or delivery is completed in your own system and is never shown as done here.",
                     if_wrong="Not recorded? Choose pickup or delivery on the step, or on the quotation's order "
                              "section.",
                     shot="w-wizard4-delivery-desktop.png"),
            ),
            exercise="Take your Quick Quote to the order package with the wizard.",
        ),
        Lesson(
            key="s11-contractor-request", title="A contractor's request with the wizard",
            what="Quote a contractor's request and follow their order to delivery.",
            why="You see only what the contractor shared, and only they place the order.",
            steps=(
                Step(title="Choose the request", app=SUP, where="Requests → a request → Start Guided Wizard",
                     do="Press Start Guided Wizard on the request page",
                     expect="The wizard on that request: the contractor, the project reference, the delivery town.",
                     if_wrong="Another store's request is never shown to you.",
                     shot="w-wizard4-open-desktop.png"),
                Step(title="Order and delivery", app=SUP, where="Steps 10 to 12",
                     do="When the contractor orders, press Confirm the order; mark it delivered when it is",
                     expect="'Only the contractor places the order' until they do; then Confirm. A contractor's "
                            "order is a delivery to the job site, arranged in the store's own system; it shows as "
                            "delivered only after it is marked delivered (with the date).",
                     if_wrong="Delivery change waiting? Answer it on the request page.",
                     shot="w-wizard4-close-desktop.png"),
            ),
            exercise="With a training contractor request, quote it and follow it with the wizard.",
        ),
    ),
)

MODULES: Tuple[Module, ...] = (C15, S11)


def _c(key, title, start, action, expected):
    return UatCase(key=key, pathway=PATHWAY_CONTRACTOR, module_key="c15", title=title, start=start, action=action,
                   expected=expected, roles=OFFICE_ROLES)


def _s(key, title, start, action, expected):
    return UatCase(key=key, pathway=PATHWAY_SUPPLIER, module_key="s11", title=title, start=start, action=action,
                   expected=expected, roles=ALL_SUPPLIER)


UAT_CASES: Tuple[UatCase, ...] = (
    _c("uat-c15-home", "Guided Wizards on Home", "Home",
       "Find the three wizards; press Continue manually under Start a New Project.",
       "Three wizards, each with Continue manually beneath it; Continue manually opens the New Project "
       "form; Company Calendar is at the top beside the greeting."),
    _c("uat-c15-required", "Required answers hold Save & Continue", "Home → Start a New Project",
       "Press Save & Continue with no customer chosen; then choose one and press Save & Continue.",
       "The first press says what is still needed and stays; the second moves to step 2."),
    _c("uat-c15-created-once", "The project is created once", "Start a New Project → step 3",
       "Press Save & Continue on Where is the job?, then go Back to step 3.",
       "One project in Projects; step 3 shows the project and does not create it again."),
    _c("uat-c15-save-resume", "Save & Exit and Resume", "Any wizard step",
       "Type something, press Save & Exit, then Resume from Home.",
       "Home lists the wizard under Continue where you left off; Resume opens the same step with what you typed."),
    _c("uat-c15-manual", "Continue manually and come back", "Any wizard step",
       "Press Continue manually, change something on that page, press Return to the wizard.",
       "The same step shows your change."),
    _c("uat-c15-estimating", "Guided Estimating prices like the manual path", "Guided Estimating → step 12",
       "Approve the costing and apply the company pricing from the wizard.",
       "Back on step 12 with the same selling price and true gross margin as Review Pricing & Prepare Proposal."),
    _c("uat-c15-manage", "Manage a Project shows the real status", "Manage a Project on an accepted project",
       "Open Milestones and schedule, schedule one work item, open it again; open Progress, costs and outstanding work.",
       "The count goes up by one; QuickBooks Time and schedule texts show whether they are switched on; the Project "
       "Lead is shown on the people step and never counts as an assignment."),
    _s("uat-s11-quick", "Quick Quote to the order package", "Requests → Start Guided Wizard",
       "Make a Quick Quote, choose it in step 1, price it, issue it, record the answer and make the order package.",
       "Each step turns Done from the quotation itself; availability shows only from your price file (otherwise "
       "'Availability not confirmed'); pickup or delivery reads 'Arranged in the store's own system' and is never "
       "shown as done."),
    _s("uat-s11-privacy", "Only your own requests and quotations", "Wizard step 1",
       "Look at the requests and quotations offered.",
       "Only your store's own; nothing of another store's and none of the contractor's costs."),
)


def attach(modules, uat_cases):
    """c15 after the last contractor module and s11 after the last supplier module, their tests likewise.
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
