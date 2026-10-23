"""Site Plans lessons (Joel, 23 Oct 2026): "Open plans on site" for the crew, and the Plans button for the office.

Kept apart from field_crew.py and contractor.py, like app/training/useful_calculators_lesson.py, so branches merge
cleanly: this module defines one Field Crew lesson and its acceptance test, attached to Field Crew module 4
("Drawings and job information") after f04-drawings, and one extra step for the Contractor lesson c07-plans
("Upload the plan PDF") about the Plans button. Attached when the Training Centre loads its content
(app/training/content.py _load). field_crew.py and contractor.py are not edited.

Every label was checked against the real pages (app/routes/site_plans.py, app/templates/site_plans/*,
app/templates/partials/plans_button.html) and pictured by tools/release/evidence_site_plans.mjs (SITE_PLANS_SHOTS):
f04-sp-*.png at iPhone size (390 x 844) and c07-plans-button.png on the office desktop (1280 x 900). The open plan
is not pictured: the test browser cannot draw a PDF page, Safari on the iPhone does. The Share sheet,
the Home Screen and Airplane Mode are the iPhone's own screens and are described in words.
"""

from __future__ import annotations

from typing import Tuple

from app.models.training import PATHWAY_CONTRACTOR, PATHWAY_FIELD_CREW, ROLE_FIELD
from app.training.content import APP_FIELD, APP_OFFICE, Lesson, Module, Step, UatCase

ADDRESS = "/site-plans/"
APP_NAME = "Site Plans"
CREW = (ROLE_FIELD,)
JOB = "Harbour Lane Pool Deck (training)"
HELP = "If it still does not work, call the office (Ben or Olivia) and write a note under My notes and feedback."
SP = APP_FIELD  # Site Plans is a third Home Screen icon from the same CalibraytAI sign-in

LESSON = Lesson(
    key="f04-site-plans", title="Open plans on site",
    what="Put the Site Plans icon on your iPhone Home Screen, open your job's plans and keep them for when there is "
         "no signal.",
    why="Every plan and drawing of the jobs you are booked on, one tap from your Home Screen, even in a basement or "
        "a field with no signal. It sits beside the CalibraytAI (Field) and Useful Calculators icons.",
    steps=(
        Step(title="Open the address in Safari", app=SP,
             where="Safari (not Chrome) → the CalibraytAI address Ben gave you, ending in " + ADDRESS,
             do="Type the address and tap Go",
             enter="The CalibraytAI address followed by " + ADDRESS,
             expect="Site Plans opens with a dark blue bar at the top and Sign in.",
             if_wrong="Page not found? Check the address with Ben: it ends in " + ADDRESS + " " + HELP,
             shot="f04-sp-sign-in.png"),
        Step(title="Add to Home Screen", app=SP,
             where="Safari → the Share button (a square with an arrow up) → Add to Home Screen",
             do="Tap Share. Scroll down. Tap Add to Home Screen. Check the name says " + APP_NAME + ". Tap Add",
             expect="A new icon called " + APP_NAME + " (a rolled plan with an eye, on dark blue) is on your Home "
                    "Screen, beside the CalibraytAI icon for Field.",
             if_wrong="Add to Home Screen not in the list? Scroll the list down, or tap Edit Actions and add it. Do "
                      "not remove or rename the CalibraytAI icon: that one is Field."),
        Step(title="Open it and sign in", app=SP, where="iPhone Home Screen → the " + APP_NAME + " icon → Sign in",
             do="Tap the icon. Type your email and your password. Tap Sign in",
             enter="Your CalibraytAI email and password (the same as Field)",
             expect="Projects: the jobs you are booked on. Only your jobs are listed.",
             if_wrong="It opened Field instead? You added the icon from a Field page. Delete that new icon only and "
                      "start again from the address ending in " + ADDRESS + ". Password refused? Tap Forgot Password?",
             shot="f04-sp-projects.png"),
        Step(title="Open the job's plans", app=SP, where="Site Plans → Projects → " + JOB,
             do="Tap the job",
             expect="The job's plans and drawings, each with its date, pages and sheet numbers, and Save for offline.",
             if_wrong="Job not listed? You are not booked on it. Call the office. 'No plans for this project yet'? "
                      "Ask the office to upload the plan.",
             shot="f04-sp-project.png"),
        Step(title="Open a plan and zoom", app=SP, where="The job's plans → a plan",
             do="Tap the plan. Tap a sheet number at the top to jump to it. Pinch with two fingers to zoom in",
             expect="Every page of the plan, one under the other, with its sheet number and name. It stays sharp "
                    "when you zoom.",
             if_wrong="A page stays blank? Check your signal and open the plan again.",
             why="Safari draws each page itself, so a sheet stays sharp when you zoom in."),
        Step(title="Keep the plans for no signal", app=SP, where="The job's plans → Save for offline",
             do="With signal (at the shop, or on Wi-Fi), tap Save for offline and wait",
             expect="'Saved 2 of 2 plans on this phone.' Each plan says On this phone. A plan you open is kept too.",
             if_wrong="'Saved 1 of 2'? The signal dropped. Tap Save for offline again.",
             why="On site you may have no signal. Plans kept on the phone open without it until you sign out.",
             shot="f04-sp-saved.png"),
        Step(title="Open a plan without signal", app=SP, where="iPhone → Airplane Mode on → the " + APP_NAME + " icon",
             do="Turn on Airplane Mode. Open Site Plans, the job and the plan. Turn Airplane Mode off after",
             expect="The plan opens. A yellow line says 'No signal: this is the copy saved on this phone.'",
             if_wrong="'No signal. This page is not saved on this phone'? Turn the signal back on, open the plan "
                      "once (or tap Save for offline), then try again."),
        Step(title="Back and sign out", app=SP, where="The dark blue bar → ‹ Plans, ‹ Projects, Sign out",
             do="Tap ‹ Plans to go back. Sign out only when you hand the phone to someone else",
             expect="Sign out removes the plans kept on this phone and shows Sign in.",
             if_wrong="Signed out by itself? After 8 hours without use you sign in again; that removes the kept "
                      "plans too, so save them again."),
    ),
    exercise=f"On your iPhone, add Site Plans to the Home Screen from Safari, sign in, open {JOB}, tap Save for "
             "offline, then turn on Airplane Mode and open the deck plan. Zoom in on the stairs. Turn Airplane Mode "
             "off. Check the CalibraytAI (Field) icon still opens Field.",
    roles=CREW,
)

UAT = UatCase(
    key="uat-f04-site-plans", pathway=PATHWAY_FIELD_CREW, module_key="f04",
    title="Site Plans from its own Home Screen icon, also without signal",
    start="Safari → the CalibraytAI address ending in " + ADDRESS + " → Share → Add to Home Screen",
    action=f"Add the Site Plans icon, open it, sign in, open {JOB}, tap Save for offline, then turn on Airplane Mode "
           "and open the plan.",
    expected="Only the jobs you are booked on are listed. The plan opens with every page and its sheet numbers, and "
             "zooms with two fingers. In Airplane Mode the saved plan still opens with 'No signal: this is the copy "
             "saved on this phone.' Field still opens at Today.",
    roles=CREW,
)

OFFICE_STEP = Step(
    title="The Plans button", app=APP_OFFICE, where=f"{'Projects → ' + JOB} → Plans (beside the page title)",
    do="Press Plans on the project page, or on its estimate, proposal or drawings pages",
    expect="Site Plans opens on this project: every plan and drawing, with sheet numbers. Press a plan to see all its "
           "pages; Back to the project returns. The crew see the same plans on their iPhones (Site Plans icon) for "
           "the jobs they are booked on.",
    if_wrong="No Plans button? The page is not about one project (the Projects list, the dashboard). Open the "
             "project first.",
    shot="c07-plans-button.png", endpoint="site_plans.project",
)


def attach(modules: Tuple[Module, ...], uat_cases: Tuple[UatCase, ...]):
    """Field Crew module 4 with the lesson after f04-drawings, the acceptance test after f04's; the Contractor lesson
    c07-plans with the Plans button as its last step. Everything else unchanged. Idempotent."""
    out = []
    for module in modules:
        if module.key == "f04" and module.pathway == PATHWAY_FIELD_CREW and LESSON not in module.lessons:
            keys = [lesson.key for lesson in module.lessons]
            at = keys.index("f04-drawings") + 1 if "f04-drawings" in keys else len(keys)
            module = Module(module.key, module.pathway, module.number, module.title, module.summary, module.roles,
                            module.lessons[:at] + (LESSON,) + module.lessons[at:])
        if module.pathway == PATHWAY_CONTRACTOR and any(l.key == "c07-plans" for l in module.lessons):
            lessons = []
            for lesson in module.lessons:
                if lesson.key == "c07-plans" and OFFICE_STEP not in lesson.steps:
                    lesson = Lesson(lesson.key, lesson.title, lesson.what, lesson.why, lesson.steps + (OFFICE_STEP,),
                                    lesson.exercise, lesson.roles)
                lessons.append(lesson)
            module = Module(module.key, module.pathway, module.number, module.title, module.summary, module.roles,
                            tuple(lessons))
        out.append(module)
    cases = list(uat_cases)
    if UAT not in cases:
        f04 = [i for i, c in enumerate(cases) if c.module_key == "f04" and c.pathway == PATHWAY_FIELD_CREW]
        cases.insert(f04[-1] + 1 if f04 else len(cases), UAT)
    return tuple(out), tuple(cases)
