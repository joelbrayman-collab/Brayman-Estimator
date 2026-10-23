"""Field Crew lesson: Installing and Using Useful Calculators (Joel, 22 Oct 2026).

Kept apart from field_crew.py (which is being extended on another branch) so the two merge cleanly: this module
defines one Lesson and one acceptance test and attaches them to Field Crew module 1 ("First sign-in and iPhone
setup") when the Training Centre loads its content (app/training/content.py _load, one call). field_crew.py is
not edited.

Every label was checked against the real pages (app/routes/useful_calculators.py,
app/templates/useful_calculators/*) and pictured at iPhone size (390 x 844) by
tools/training/capture_useful_calculators_shots.mjs (app/static/training/shots/f01-uc-*.png). The Share sheet and
the Home Screen are the iPhone's own screens and cannot be pictured from the site, so those steps describe them in
words. Field-only workers see only the quantity calculators; the lesson says plainly what stays in the office.
"""

from __future__ import annotations

from typing import Tuple

from app.models.training import PATHWAY_FIELD_CREW, ROLE_FIELD
from app.training.content import APP_FIELD, Lesson, Module, Step, UatCase

ADDRESS = "/useful-calculators/"
APP_NAME = "Useful Calculators"
CREW = (ROLE_FIELD,)
HELP = "If it still does not work, call the office (Ben or Olivia) and write a note under My notes and feedback."
UC = APP_FIELD  # the Useful Calculators icon is a second Home Screen app from the same CalibraytAI sign-in

LESSON = Lesson(
    key="f01-useful-calculators", title="Installing and Using Useful Calculators",
    what="Put a second icon, Useful Calculators, on your iPhone Home Screen and use a calculator on site.",
    why="Concrete, footings, ICF walls, framing, stairs, roofing, siding, drywall and flooring in one place, one tap "
        "from your Home Screen. It sits beside the CalibraytAI Field icon; it does not replace it.",
    steps=(
        Step(title="Open the address in Safari", app=UC,
             where="Safari (not Chrome) → the CalibraytAI address Ben gave you, ending in " + ADDRESS,
             do="Type the address and tap Go",
             enter="The CalibraytAI address followed by " + ADDRESS,
             expect="The Useful Calculators page opens with a blue bar at the top and the calculators listed.",
             if_wrong="Page not found? Check the address with Ben: it ends in " + ADDRESS + " " + HELP,
             shot="f01-uc-safari.png"),
        Step(title="Add to Home Screen", app=UC,
             where="Safari → the Share button (a square with an arrow up) → Add to Home Screen",
             do="Tap Share. Scroll down. Tap Add to Home Screen. Check the name says " + APP_NAME + ". Tap Add",
             expect="A new icon called " + APP_NAME + " (a calculator, tape measure and lumber on blue) is on your "
                    "Home Screen, beside the CalibraytAI icon for Field.",
             if_wrong="Add to Home Screen not in the list? Scroll the list down, or tap Edit Actions and add it. Do "
                      "not remove or rename the CalibraytAI icon: that one is Field."),
        Step(title="Confirm the icon and open it", app=UC, where="iPhone Home Screen → the " + APP_NAME + " icon",
             do="Tap the " + APP_NAME + " icon",
             expect="Useful Calculators opens on its own, without the Safari address bar. You may need to sign in "
                    "once: tap Sign in.",
             if_wrong="It opened Field instead? You added the icon from a Field page. Delete that new icon only, then "
                      "repeat from the first step with the address ending in " + ADDRESS),
        Step(title="Sign in", app=UC, where="Useful Calculators → Sign in",
             do="Type your email and your password. Tap Sign in",
             enter="Your CalibraytAI email and password (the same as Field)",
             expect="You are back on Useful Calculators. The page says Signed in as and your name.",
             if_wrong="Password refused? Check each letter. Still refused: tap Forgot Password?",
             shot="f01-uc-sign-in.png"),
        Step(title="Open the dashboard", app=UC, where="Useful Calculators (the first page)",
             do="Look at the list. Calculators you can use are white cards; Office only cards are grey",
             expect="Concrete, Footing, ICF wall, Stair, Wall framing, Roofing, Siding, Drywall and Flooring are "
                    "white. Employment vs Entrepreneurship, Supplier economic model and Job calculators are grey and "
                    "say Office only.",
             if_wrong="Only the public calculators and a Sign in button? You are not signed in yet: tap Sign in.",
             why="The grey cards work with the company's own business numbers or job records, so they stay in "
                 "the office. Ask the office if you need a figure from them.",
             shot="f01-uc-dashboard.png"),
        Step(title="Use a calculator", app=UC, where="Useful Calculators → Footing calculator",
             do="Tap Footing calculator. Enter one footing. Type 0 for waste. Tap Calculate",
             enter="Length 20, Width 2, Thickness 8, Waste 0",
             expect="Under Quantities: Concrete 0.988 yd³ (26.67 ft³). These quantities are not saved and not added "
                    "to any job.",
             if_wrong="A red message instead? A box is empty or has letters in it. Fix it and tap Calculate again.",
             shot="f01-uc-calculator.png"),
        Step(title="Return to the dashboard", app=UC, where="The blue bar at the top → ‹ All calculators",
             do="Tap ‹ All calculators (or Back to all calculators at the bottom)",
             expect="The list of calculators again. Next time, open it from the icon: it starts on this list.",
             if_wrong="Nothing happens? Scroll up to the top of the page and tap it again.",
             shot="f01-uc-return.png"),
    ),
    exercise="On your iPhone, add Useful Calculators to the Home Screen from Safari, open it from the new icon, sign "
             "in, work out the concrete for one footing 20 ft long, 2 ft wide and 8 in thick with no waste, and go "
             "back to the list. Check the CalibraytAI (Field) icon still opens Field.",
    roles=CREW,
)

UAT = UatCase(
    key="uat-f01-useful-calculators", pathway=PATHWAY_FIELD_CREW, module_key="f01",
    title="Useful Calculators from its own Home Screen icon",
    start="Safari → the CalibraytAI address ending in " + ADDRESS + " → Share → Add to Home Screen",
    action="Add the Useful Calculators icon, open it, sign in, use the Footing calculator, then return to the list. "
           "Open the CalibraytAI (Field) icon too.",
    expected="Two icons. Useful Calculators opens on its list with the nine calculators you can use and the Office "
             "only cards grey; the footing gives the concrete; ‹ All calculators returns to the list. Field still "
             "opens at Today.",
    roles=CREW,
)


def attach(modules: Tuple[Module, ...], uat_cases: Tuple[UatCase, ...]):
    """Field Crew module 1 with this lesson added after its Home Screen lesson; the acceptance test added after
    module 1's. Everything else is returned unchanged. Idempotent."""
    out = []
    for module in modules:
        if module.key == "f01" and module.pathway == PATHWAY_FIELD_CREW and LESSON not in module.lessons:
            keys = [lesson.key for lesson in module.lessons]
            at = keys.index("f01-home-screen") + 1 if "f01-home-screen" in keys else len(keys)
            module = Module(module.key, module.pathway, module.number, module.title, module.summary, module.roles,
                            module.lessons[:at] + (LESSON,) + module.lessons[at:])
        out.append(module)
    cases = list(uat_cases)
    if UAT not in cases:
        f01 = [i for i, c in enumerate(cases) if c.module_key == "f01" and c.pathway == PATHWAY_FIELD_CREW]
        cases.insert(f01[-1] + 1 if f01 else len(cases), UAT)
    return tuple(out), tuple(cases)
