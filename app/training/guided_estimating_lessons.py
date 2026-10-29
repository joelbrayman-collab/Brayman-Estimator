"""Contractor training: Guided Estimating and the calculators' three choices (Joel, 23 Oct 2026).

Two modules for the contractor owner and office staff, kept apart from contractor.py so that file's lessons and
keys stay exactly as they are (saved progress is keyed by lesson and acceptance-test keys; nothing here renames
or moves one). They are added after module 12 when the Training Centre loads its content (app/training/content.py
_load, one call):

- Module 13, Guided Estimating — Ben's path New Project → What work are we doing? → Guided Estimating → Internal
  Cost Estimate → Pricing → Proposal, on one synthetic new home (selected-work estimating, Approach B, 28 Oct 2026:
  the scope is only the work chosen; no stage list and no N/A; reconciled 29 Oct 2026). It is the centrepiece of Kevin's Contractor Review: he can do
  the whole estimate on the training company without setting up a company or QuickBooks (the training site
  already has the company's labour rate, pricing policy and practice costs).
- Module 14, the calculators' three choices — Use Result Only, Add to Existing Project, Create New Project, and
  how a calculation reaches the estimate only through the estimate review.

Every label was checked against the real pages and pictured by tools/training/capture_guided_estimating_shots.mjs
(app/static/training/shots/c13-*.png and c14-*.png).
"""

from __future__ import annotations

from typing import Tuple

from app.models.training import PATHWAY_CONTRACTOR as P
from app.training.content import APP_OFFICE, APP_TRAINING_PHONE, OFFICE_ROLES, Lesson, Module, Step, UatCase

O = APP_OFFICE
HOME = "Lakeview New Home (training)"
CUSTOMER = "Jordan Avery (training)"
INITIALS = (" On the training site everyone shares one training company: add your initials to the project name "
            "(for example 'Lakeview New Home (training) KF').")
WORK = "Windows, Excavation, Footings, Electrical and HVAC"
SCOPE_TABLE = "Windows Internal; Excavation Subcontracted; Footings Internal; Electrical Subcontracted; HVAC Subcontracted"

M13 = Module(
    key="c13", pathway=P, number=13, title="Guided Estimating: a new home from start to proposal",
    summary="New Project → What work are we doing? → Guided Estimating → Internal Cost Estimate → Pricing → Proposal. You say what is "
            "being built and who does each piece of work; CalibraytAI brings the right calculator or quote to each "
            "and builds one internal cost estimate. This is the centrepiece of the Contractor Review: no company "
            "or QuickBooks set-up is needed on the training site.",
    roles=OFFICE_ROLES,
    lessons=(
        Lesson(
            key="c13-start-new-estimate", title="Start New Estimate: the project, what you build and your role",
            what="Start a new home estimate from Home: the project, the customer, what is being built and your role.",
            why="You choose only the work you are doing and who does it; you never have to know which "
                "calculator or page comes next.",
            steps=(
                Step(title="Start New Estimate", app=O, where="Home → GUIDED WIZARDS",
                     do="Press Continue manually under Estimate a Project",
                     expect="Start New Estimate: Create a new project, Calculators, any unfinished estimates to resume "
                            "and your current projects.",
                     if_wrong="Not on Home? Press Home at the top of the menu.",
                     shot="c13-home-start.png", endpoint="main.dashboard"),
                Step(title="Create a new project", app=O, where="Start New Estimate",
                     do="Press Create a new project",
                     expect="New Project, with 'What is being built, and your role' and 'Start the guided estimate "
                            "when the project is saved' ticked.",
                     if_wrong="To estimate a job you already have, use 'Estimate an existing project' on the same page.",
                     shot="c13-start-page.png", endpoint="guided.start"),
                Step(title="The project, its type and your role", app=O, where="New Project",
                     do="Type the project name, choose the customer, choose Project type New Home Construction and "
                        "General Contractor, fill the Commercial Decision Gate and press Save Project",
                     enter=f"{HOME} <initials>; Client {CUSTOMER}; New Home Construction; General Contractor",
                     expect="The commercial project type is filled in as New Build for you; you can change it.",
                     if_wrong="'Project name and client are required': check both. Every Commercial Decision Gate "
                              "box needs a choice.",
                     shot="c13-new-project-type.png", endpoint="projects.create_project"),
                Step(title="What work are we doing?", app=O, where="Work included in this project",
                     do="Read the page",
                     expect="'What work are we doing?' with the work under Exterior, Structure, Foundation & site, "
                            "Interior, Mechanical & electrical and General, and nothing chosen yet. There is no list "
                            "of stages to decide.",
                     if_wrong="Opened the project page instead? Press Start the guided estimate on it.",
                     shot="c13-scope-empty.png", endpoint="guided.scope"),
            ),
            exercise=f"Start a new estimate for '{HOME} <initials>' for {CUSTOMER}: New Home Construction, General "
                     "Contractor." + INITIALS,
        ),
        Lesson(
            key="c13-scope", title="What work are we doing? Choose the work and who does it",
            what="Choose the five pieces of work this exercise prices, say who does each, then start estimating.",
            why="Only the work you choose is estimated: there is nothing to rule out and no N/A. Internal work brings "
                "your calculators and labour; subcontracted work brings the quote tools.",
            steps=(
                Step(title="Choose the work", app=O, where="What work are we doing?",
                     do=f"Tick {WORK} (Find work narrows the list), then press Add work",
                     expect="'5 work items · 0 of 5 complete', each with Who is doing this work? Internal or "
                            "Subcontracted. New work starts as Internal.",
                     if_wrong="Missed one? The same page keeps Add work below the list. Work that is not in the "
                              "list can be typed under Other work, named.",
                     shot="c13-scope-chosen.png", endpoint="guided.scope"),
                Step(title="Who is doing this work?", app=O, where="Work included in this project → each work item",
                     do="Press Subcontracted on Excavation, Electrical and HVAC; leave Windows and Footings Internal",
                     enter=SCOPE_TABLE,
                     expect="Each work item shows the choice you pressed.",
                     if_wrong="Pressed the wrong one? Press the other; only one is chosen.",
                     endpoint="guided.scope"),
                Step(title="Mixed work, or work to take out", app=O,
                     where="A work item → More: split materials and installation, or remove",
                     do="Open More on Windows to see the two choices. Leave them for this exercise",
                     expect="Decide materials and installation separately (for example your materials and a "
                            "subcontractor's installation), and Remove, which asks you to confirm.",
                     if_wrong="Work that already holds estimate lines cannot be removed until those are taken off.",
                     shot="c13-scope-parts.png", endpoint="guided.scope"),
                Step(title="Estimate this work", app=O, where="Work included in this project → the bottom",
                     do="Press Estimate this work",
                     expect=f"The Estimating workflow: 0 of 5 work items complete, 'Estimating: {WORK.replace(' and ', ', ')}', "
                            "each with who does it, its status and its next action.",
                     if_wrong="Changed your mind later? The Work page stays open; each change is kept in the history.",
                     shot="c13-workflow.png", endpoint="guided.workflow"),
            ),
            exercise=f"Choose {WORK} for your Lakeview estimate, with the responsibilities above, and press "
                     "Estimate this work.",
        ),
        Lesson(
            key="c13-internal-stage", title="Internal work: the calculator comes to you",
            what="Estimate Footings with the footing calculator, the estimate review and labour hours.",
            why="The work item opens the right calculator with the project and the work already chosen; the result goes to the estimate "
                "only after you confirm each quantity and its company cost.",
            steps=(
                Step(title="Open the work", app=O, where="Estimating workflow → Footings",
                     do="Press Footings",
                     expect="Your tools for this work: Footing calculator, Labour hours and Enter a cost line.",
                     if_wrong="Any work item can be opened in any order.",
                     shot="c13-stage-internal.png", endpoint="guided.stage"),
                Step(title="Calculate the footings", app=O, where="Footings → Footing calculator",
                     do="Press Footing calculator, enter the two footings and the waste, press Calculate",
                     enter="Footing 1: 120 ft × 2 ft × 10 in; Footing 2: 40 ft × 2 ft × 10 in; Waste 5",
                     expect="The quantities, then 'What would you like to do with this result?' with your project "
                            "and Footings already chosen.",
                     if_wrong="A red message means a box is empty or not a number.",
                     shot="c13-footing-calculator.png", endpoint="calculators.footing"),
                Step(title="Add it to Footings", app=O, where="The calculator → Add to Existing Project",
                     do="Press Add to project, then Review it for the estimate",
                     expect="'Saved on Lakeview New Home…'. Pressing it again says it is already there: never doubled.",
                     if_wrong="The button stays grey until there is a result and a project.",
                     shot="c13-footing-add.png", endpoint="calculators.footing"),
                Step(title="Send it to the estimate review", app=O, where="The calculation",
                     do="Check what was entered and calculated, then press Send to the estimate review",
                     expect="The estimate review with the Footings section already chosen. Nothing is on the estimate yet.",
                     if_wrong="'issued or locked': the estimate was issued; start a revision first.",
                     shot="c13-calc-send.png", endpoint="guided.calculation"),
                Step(title="Confirm the quantity", app=O, where="The estimate review → Add to this estimate",
                     do="Choose Ready-mix concrete 25 MPa (training) and press Add to estimate; then go back to "
                        "Footings",
                     expect="'Quantity added to the estimate.' Footings lists the concrete line at the company cost.",
                     if_wrong="'No company item uses this unit yet': the company has no cost in that unit.",
                     shot="c13-review-confirm.png", endpoint="estimates.calculation_review"),
                Step(title="Labour hours", app=O, where="Footings → Labour hours",
                     do="Type the hours for the concrete line and press Save labour hours",
                     enter="40",
                     expect="A labour line at the company's approved labour rate.",
                     if_wrong="No approved labour rate? The company sets it under How we price.",
                     shot="c13-stage-labour.png", endpoint="guided.stage"),
                Step(title="Confirm and complete", app=O, where="Footings → the bottom",
                     do="Press Confirm who supplies and builds these lines, then Complete & Next",
                     expect="'Footings is complete.' The next work item that is not complete opens.",
                     if_wrong="'Not complete yet' lists what is missing: work completes only with confirmed costs, "
                              "an approved allowance or a no-cost decision authorized by the owner.",
                     shot="c13-stage-complete.png", endpoint="guided.stage"),
            ),
            exercise="Estimate Footings on your Lakeview project with the footing calculator (the two "
                     "footings above, 5 % waste), the training concrete cost and 40 labour hours, and complete it.",
        ),
        Lesson(
            key="c13-subcontracted-stage", title="Subcontracted work: request, record, compare, use the cost",
            what="Estimate Electrical from two subcontractor quotes.",
            why="A quote is evidence: selecting it only suggests the cost. You apply it with Use this cost on the "
                "line (and can undo it), so nothing changes your estimate behind your back.",
            steps=(
                Step(title="Describe the work", app=O, where="Estimating workflow → Electrical",
                     do="Type what the electrician is to do and press Set up the subcontract",
                     enter="Wire the house to code, panel and fixtures (training)",
                     expect="The subcontract line on the estimate, with a Printable quote request sheet.",
                     if_wrong="Only subcontracted work has a subcontract.",
                     shot="c13-sub-setup.png", endpoint="guided.stage"),
                Step(title="Request the quote", app=O, where="Electrical",
                     do="Send the quote request sheet, then press I have sent the quote request",
                     expect="Electrical shows Waiting for Quote. Carry on with the other work while you wait.",
                     if_wrong="Quotes can also come by phone or email; record them the same way.",
                     shot="c13-sub-waiting.png", endpoint="guided.stage"),
                Step(title="Record the quotes", app=O, where="Electrical → Record a quote",
                     do="Fill in the subcontractor, reference, amount and date; press Record the quote (once for each)",
                     enter="Sparks Electric (training) EL-9 24500; Bright Wire (training) EL-10 26100",
                     expect="Quotes received lists both, with what they include and exclude.",
                     if_wrong="An amount must be a number, without the dollar sign.",
                     shot="c13-sub-quotes.png", endpoint="guided.stage"),
                Step(title="Select and use the cost", app=O, where="Electrical → Quotes received",
                     do="Press Select this quote on EL-9, then Use this cost on the line",
                     expect="Suggested cost from the selected quote, then the line at $24,500.00, applied by you.",
                     if_wrong="Undo puts the line back to its earlier cost.",
                     shot="c13-sub-use-cost.png", endpoint="guided.stage"),
                Step(title="Complete", app=O, where="Electrical → the bottom",
                     do="Press Complete & Next",
                     expect="'Electrical is complete.'",
                     if_wrong="A quote that is only selected (not used on the line) is not a confirmed cost.",
                     endpoint="guided.stage"),
            ),
            exercise="Estimate Electrical on your Lakeview project from the two quotes above, using EL-9.",
        ),
        Lesson(
            key="c13-missing-costs", title="Missing costs, allowances and coming back later",
            what="See work refused without a cost, approve an allowance, save and come back.",
            why="A missing cost stays visible until it is resolved; the proposal waits for it. An allowance is an "
                "explicit, approved decision with a reason. Deciding that included work has no cost at all is the "
                "owner's decision (or a System Administrator's).",
            steps=(
                Step(title="No cost, no completion", app=O, where="Estimating workflow → HVAC",
                     do="Press Complete & Next without any cost",
                     expect="'Not complete yet: No cost yet …'. HVAC stays as it was.",
                     if_wrong="That is the rule working: nothing completes on a click alone.",
                     shot="c13-missing.png", endpoint="guided.stage"),
                Step(title="Approve an allowance", app=O, where="HVAC → Allowance or no-cost decision",
                     do="Type the allowance amount and why an allowance is used, press Approve the allowance, then "
                        "Complete & Next",
                     enter="16000; Why an allowance: The HVAC quote is still to come",
                     expect="An allowance line on the estimate, approved in your name with the date and your reason "
                            "(kept in the history); HVAC completes as an Approved allowance.",
                     if_wrong="'Say why this work uses an allowance': the reason is required. Only a person who can "
                              "approve costing can approve an allowance. 'Authorize no cost' is shown only to the "
                              "owner and System Administrators: everyone else sees that it is the owner's decision.",
                     shot="c13-allowance.png", endpoint="guided.stage"),
                Step(title="Save & Exit, then Resume", app=O, where="Windows → Save & Exit",
                     do="Press Save & Exit; on the project page press Resume estimating",
                     expect="You are back on Windows, where you stopped.",
                     if_wrong="Start New Estimate (Home → Estimate a Project → Continue manually) also lists "
                              "unfinished estimates to resume.",
                     shot="c13-resume.png", endpoint="projects.view_project"),
            ),
            exercise="On your Lakeview project try to complete HVAC with no cost, then approve a $16,000 allowance and "
                     "complete it. Open Windows, Save & Exit and Resume.",
        ),
        Lesson(
            key="c13-internal-cost", title="The internal cost estimate",
            what="Read the internal cost estimate and download it.",
            why="It is the principal result of guided estimating: every work item's materials, labour, subcontracts, "
                "allowances and their sources in one place, for the office only.",
            steps=(
                Step(title="Open it", app=O, where="Estimating workflow → Internal cost estimate",
                     do="Press Internal cost estimate",
                     expect="INTERNAL — NOT FOR CUSTOMER DISTRIBUTION, the totals by kind of cost, each work item with "
                            "its lines and sources, and anything still missing.",
                     if_wrong="DRAFT means the costing is not approved yet; it updates as work is confirmed.",
                     shot="c13-internal-cost.png", endpoint="guided.internal_cost"),
                Step(title="Download or print", app=O, where="Internal cost estimate",
                     do="Press Download PDF (or Print)",
                     expect="The same document as a PDF, marked INTERNAL — NOT FOR CUSTOMER DISTRIBUTION on every page.",
                     if_wrong="Never send it to a customer: the customer gets the proposal.",
                     endpoint="guided.internal_cost_pdf"),
            ),
            exercise="Open the internal cost estimate of your Lakeview project, find the Electrical quote and the HVAC "
                     "allowance, and download the PDF.",
        ),
        Lesson(
            key="c13-pricing-proposal", title="Review Pricing & Prepare Proposal",
            what="Approve the costing, apply the company pricing and prepare the customer proposal.",
            why="The price comes from the company pricing policy and true gross margin, with HST; the customer sees the "
                "scope and price, never your costs.",
            steps=(
                Step(title="All the work resolved", app=O, where="Estimating workflow → Review Pricing & Prepare Proposal",
                     do="Read step 1",
                     expect="Either 'Every included stage is complete' (the page still says stage; it means every work "
                            "item), or the work still missing a cost.",
                     if_wrong="The proposal waits until every work item has a confirmed cost, an approved allowance or "
                              "an owner-authorized no-cost decision.",
                     shot="c13-pricing-blocked.png", endpoint="guided.pricing"),
                Step(title="Approve the costing", app=O, where="Review Pricing & Prepare Proposal → 2",
                     do="Press Approve the costing",
                     expect="'Costing approved', and you come back to this page.",
                     if_wrong="A refusal names the lines to fix (for example who supplies and builds is not confirmed).",
                     endpoint="guided.pricing"),
                Step(title="Apply the company pricing", app=O, where="Review Pricing & Prepare Proposal → 3",
                     do="Press Apply the company pricing policy",
                     expect="Direct cost, method, true gross margin, selling price before tax, HST and customer total.",
                     if_wrong="The training company's policy is the one marked Company default under How we price.",
                     shot="c13-pricing-priced.png", endpoint="guided.pricing"),
                Step(title="Prepare the proposal", app=O, where="Review Pricing & Prepare Proposal → 4",
                     do="Press Prepare the proposal and save it as a draft",
                     expect="The existing proposal page with the work items as sections and the selling price.",
                     if_wrong="Sending it to the customer is module 10.",
                     shot="c13-proposal.png", endpoint="proposals.create_proposal_route"),
            ),
            exercise="When all the work on your Lakeview estimate is resolved (use allowances for Windows and Excavation, "
                     "which this exercise does not price), approve the costing, apply the pricing and prepare the proposal.",
        ),
    ),
)

M14 = Module(
    key="c14", pathway=P, number=14, title="Calculators and your projects: three choices",
    summary="Every calculator still works on its own. After a result: Use Result Only, Add to Existing Project, or "
            "Create New Project. A calculation reaches an estimate only through the estimate review.",
    roles=OFFICE_ROLES,
    lessons=(
        Lesson(
            key="c14-use-result-only", title="Use Result Only",
            what="Use a calculator on its own.",
            why="Quick numbers on site or on the phone, with nothing saved anywhere.",
            steps=(
                Step(title="Calculate", app=O, where="CALCULATORS → Concrete calculator",
                     do="Enter the slab and press Calculate concrete",
                     enter="24 ft × 24 ft × 4 in, waste 5",
                     expect="The order and 'What would you like to do with this result?'.",
                     if_wrong="Use the actual dimensions for this pour.",
                     shot="c14-concrete-result.png", endpoint="calculators.concrete"),
                Step(title="Use result only", app=O, where="The result → Use Result Only",
                     do="Press Use result only",
                     expect="'Nothing was saved.' No project or estimate changed.",
                     if_wrong="That is all: the result stays on the screen.",
                     shot="c14-use-only.png", endpoint="calculators.concrete"),
            ),
            exercise="Calculate a 24 × 24 ft, 4 in slab with 5 % waste and use the result only.",
        ),
        Lesson(
            key="c14-add-to-existing", title="Add to Existing Project",
            what="Keep a result on a project and send it to its estimate review.",
            why="Everything you entered goes with it: you never type the calculation again.",
            steps=(
                Step(title="Select Project", app=O, where="The result → Add to Existing Project",
                     do="Choose the project and, if it has a guided estimate, the work; press Add to project",
                     enter="Lakeview New Home (training) <initials>; Footings",
                     expect="'Saved on …' and Review it for the estimate. Pressing it again never adds it twice.",
                     if_wrong="Only your company's current projects are listed.",
                     shot="c14-add-existing.png", endpoint="calculators.concrete"),
                Step(title="Send it to the estimate review", app=O, where="Review it for the estimate",
                     do="Press Send to the estimate review, choose the company cost and press Add to estimate",
                     expect="The quantity on the estimate only after your confirmation. An issued estimate is never "
                            "changed: start a revision first.",
                     if_wrong="Nothing is added until you press Add to estimate.",
                     shot="c14-send-review.png", endpoint="guided.calculation"),
            ),
            exercise="Add a concrete result to your Lakeview project's Footings and confirm it in the estimate review.",
        ),
        Lesson(
            key="c14-create-new-project", title="Create New Project from a calculator",
            what="Start a new project from a result, cancel once, then create it.",
            why="The project did not exist when you calculated; the calculation is kept and waits on the new project.",
            steps=(
                Step(title="New Project", app=O, where="The result → Create New Project",
                     do="Press New Project",
                     expect="New Project with 'Bringing your Concrete result: …' at the top.",
                     if_wrong="The button stays grey until there is a result.",
                     shot="c14-new-project.png", endpoint="projects.create_project"),
                Step(title="Cancel returns the result", app=O, where="New Project → the banner",
                     do="Press Cancel and go back to the calculator",
                     expect="The calculator with the same entries and the same result: 'Your result is back'.",
                     if_wrong="Nothing was saved; the project was not created.",
                     shot="c14-cancel-back.png", endpoint="calculators.concrete"),
                Step(title="Create the project", app=O, where="The result → New Project → New Project form",
                     do="Fill in the project, choose its type and role and press Save Project; on What work are we "
                        "doing? add Concrete slab and Footings, then press Estimate this work",
                     enter="Rivera Garage (training) <initials>; Garage / Outbuilding; Contractor performing selected portions",
                     expect="'Your Concrete result is saved on the project'; the workflow lists it under Calculations "
                            "waiting for a work item.",
                     if_wrong="Open the calculation and choose its work item, then Send to the estimate review.",
                     shot="c14-waiting.png", endpoint="guided.workflow"),
            ),
            exercise="From a concrete result create 'Rivera Garage (training) <initials>', cancelling once first, and send "
                     "the waiting calculation to the Concrete slab review.",
        ),
        Lesson(
            key="c14-phone", title="On the iPhone (Useful Calculators)",
            what="See the same three choices in the Useful Calculators app.",
            why="The office can add a site measurement to the job from the phone; crew members see the result only.",
            steps=(
                Step(title="Calculate on the phone", app=APP_TRAINING_PHONE, where="Useful Calculators → Footing calculator",
                     do="Calculate a footing",
                     expect="The result, then Use Result Only, Add to Existing Project and Create New Project.",
                     if_wrong="Signed in as Field crew? Crew see the result only; adding to a project is the office's.",
                     shot="c14-phone-options.png", endpoint="useful_calculators.footing"),
            ),
            exercise="On your iPhone open Useful Calculators, calculate a footing and add it to your Lakeview project.",
        ),
    ),
)

MODULES = (M13, M14)


def _u(key, module, title, start, action, expected):
    return UatCase(key=key, pathway=P, module_key=module, title=title, start=start, action=action, expected=expected,
                   roles=OFFICE_ROLES)


UAT_CASES = (
    _u("uat-c13-scope", "c13", "New home: only the work you choose, nothing chosen for you",
       "Home → Estimate a Project → Continue manually (Start New Estimate)",
       "Create a new project as New Home Construction and General Contractor; on What work are we doing? add Windows, "
       "Excavation, Footings, Electrical and HVAC, make Excavation, Electrical and HVAC Subcontracted, and press "
       "Estimate this work.",
       "Nothing is chosen for you and no stage list or N/A appears; the workflow lists exactly the five work items "
       "with the responsibilities you chose (0 of 5 complete)."),
    _u("uat-c13-internal", "c13", "Internal work through its calculator and the estimate review",
       "Estimating workflow → Footings",
       "Open the Footing calculator from Footings, add the result to Footings, send it to the review, confirm the "
       "concrete, add labour hours, confirm routing and Complete & Next.",
       "Nothing reaches the estimate before you confirm; Footings completes with the concrete at the company cost and "
       "the labour at the company rate."),
    _u("uat-c13-subcontract", "c13", "Subcontracted work: the quote suggests, you apply",
       "Estimating workflow → Electrical",
       "Record two quotes, try Complete & Next, select one, press Use this cost on the line, then Complete & Next.",
       "Complete is refused until the selected quote's cost is used on the line; then Electrical completes at that cost."),
    _u("uat-c13-missing-cost", "c13", "Missing costs hold the proposal", "Review Pricing & Prepare Proposal",
       "With one work item left without a cost, open Review Pricing & Prepare Proposal; then approve an allowance for it "
       "(with the reason).",
       "The page names the work item and offers no proposal until the allowance is approved."),
    _u("uat-c13-internal-cost", "c13", "Internal cost estimate, office only", "Estimating workflow → Internal cost estimate",
       "Open the internal cost estimate and download the PDF.",
       "Both are marked INTERNAL — NOT FOR CUSTOMER DISTRIBUTION and show each work item's costs and sources."),
    _u("uat-c13-proposal", "c13", "Pricing and proposal from the guided estimate",
       "Review Pricing & Prepare Proposal",
       "Approve the costing, apply the company pricing and prepare the proposal.",
       "The pricing shows the true gross margin and HST; the proposal shows the work and selling price and none of "
       "your costs."),
    _u("uat-c14-use-only", "c14", "Use Result Only changes nothing", "CALCULATORS → Concrete calculator",
       "Calculate a slab and press Use result only.", "The result stays; no project or estimate changes."),
    _u("uat-c14-existing", "c14", "Add to Existing Project, once", "A calculator result → Add to Existing Project",
       "Add a result to a project and its work, press Add to project again, then send it to the estimate review and confirm.",
       "The second press says it is already there; the estimate gets one line, only after you confirm it."),
    _u("uat-c14-new-project", "c14", "Create New Project keeps the result; Cancel returns it",
       "A calculator result → Create New Project",
       "Press New Project, Cancel, then New Project again and save the project.",
       "Cancel shows the same result again; the new project receives the calculation without retyping it."),
)


def attach(modules: Tuple[Module, ...], uat_cases: Tuple[UatCase, ...]):
    """The two modules after the contractor modules and their acceptance tests after the contractor tests.
    Everything else is returned unchanged. Idempotent."""
    keys = {m.key for m in modules}
    out = list(modules)
    last_contractor = max((i for i, m in enumerate(out) if m.pathway == P), default=len(out) - 1)
    for offset, module in enumerate(m for m in MODULES if m.key not in keys):
        out.insert(last_contractor + 1 + offset, module)
    cases = list(uat_cases)
    present = {c.key for c in cases}
    last_case = max((i for i, c in enumerate(cases) if c.pathway == P), default=len(cases) - 1)
    for offset, case in enumerate(c for c in UAT_CASES if c.key not in present):
        cases.insert(last_case + 1 + offset, case)
    return tuple(out), tuple(cases)
