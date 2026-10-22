"""Field Crew training: 8 modules for the crew on the iPhone (Joel, 22 Oct 2026).

The Training Centre serves three groups: contractor owners and office staff (contractor.py), the Field crew
(this file) and supplier owners and PRO Desk staff (supplier.py). Kevin and Liam on the training company are
Field-only: they register straight into this pathway and see nothing else.

Written for a worker with little or no technical experience, on a phone, on site: short sentences, the exact
button, what to type, what they should see, and what to do if it goes wrong. Every label was checked against the
real Field pages (app/routes/field.py, app/templates/field/*) and pictured at iPhone size (390 x 844) by
tools/training/capture_field_crew_shots.mjs (app/static/training/shots/f<module>-<name>.png). Where a module title
promises more than Field does, the lesson says so plainly and says what the office does instead:

- Drawings: Field opens the job's construction drawings and plan PDFs read-only. It cannot mark up, upload or
  change a drawing, and it does not show the customer's contract, the quote or the material list.
- Schedule changes: only the office changes dates. Field has no message or alert when a date moves; the new
  dates show the next time a Field page opens (it checks itself when the app comes back on screen).
- Progress updates: there is no percent-complete or status button. A progress update is a note and photos on
  Capture; the office reads them under Field Observations.
- Refresh: there is no refresh button. Tap Today (or This week) again, or close and reopen the app.
- Offline: Today, This week, This month, Company today, Projects and Capture open from the copy saved on the
  phone; a capture saved with no signal waits on the phone and sends when the connection is back while Field
  is open. Time and Extra work need a connection.

Field never shows money, and nor does this pathway: no prices, rates, quotes, totals or office pages.
"""

from app.models.training import PATHWAY_FIELD_CREW as P
from app.models.training import ROLE_FIELD
from app.training.content import APP_EMAIL, APP_FIELD, APP_TRAINING_PHONE, Lesson, Module, Step, UatCase

CREW = (ROLE_FIELD,)
F = APP_FIELD
JOB = "Harbour Lane Pool Deck (training)"
ADDRESS = "14 Harbour Lane, Merrickville, ON"
WORK = "Pool deck framing and decking (training)"
ACTIVITY = "Framing and decking (training)"
TEAM = "Pool deck crew (training)"
OFFICE_HELP = "If it still does not work, call the office (Ben or Olivia) and write a note under My notes and feedback."
TC_APP = APP_TRAINING_PHONE  # the Training Centre pages themselves, in Safari on the iPhone

# ====================================================================================== 1
M01 = Module(
    key="f01", pathway=P, number=1, title="First sign-in and iPhone setup",
    summary="Sign in on your iPhone, start your Field Crew training, set your own password, and put Field on the "
            "Home Screen so it opens like an app.",
    roles=CREW,
    lessons=(
        Lesson(
            key="f01-start-training", title="Start your Field Crew training",
            what="Sign in to the training site on your iPhone and start your Field Crew training.",
            why="Your lessons are only about Field, the app the crew use. Every step you tick is saved, so you can "
                "stop at any time and carry on later.",
            steps=(
                Step(title="Open the training site", app=TC_APP,
                     where="Safari on your iPhone → the training site address from your invitation",
                     do="Tap I work on a crew (Field)",
                     expect="The page says Welcome to CalibraytAI training. It has three big buttons. The middle one "
                            "is I work on a crew (Field).",
                     if_wrong="Page not found? Check the address with Ben. The training site is not the real "
                              "CalibraytAI. " + OFFICE_HELP,
                     shot="f01-training-signin.png", endpoint="training.signin"),
                Step(title="Sign in", app=TC_APP, where="Training sign in",
                     do="Type your email and your password. Tap Sign in",
                     enter="Your training email, for example kevin@training.calibraytai.invalid, and your password",
                     expect="Your Field Crew training opens with Welcome and your name.",
                     if_wrong="Password refused? Check each letter. Tap the eye to see what you typed. Still refused: "
                              "tap Forgot Password? (lesson 'Your password').",
                     shot="f01-sign-in.png", endpoint="auth.login"),
                Step(title="Start your training", app=TC_APP, where="Field Crew training → Welcome",
                     do="Tap Start my Field Crew training",
                     expect="Your 8 Field Crew modules appear, numbered 1 to 8, with Continue where I left off at the "
                            "top.",
                     if_wrong="If you see office or supplier lessons, stop and tell Ben: you should only see Field "
                              "Crew lessons.",
                     shot="f01-register.png", endpoint="training.home"),
                Step(title="Open your first lesson", app=TC_APP, where="Field Crew training → home",
                     do="Tap Continue where I left off",
                     expect="This lesson opens. Each step has a big button: I did this step.",
                     if_wrong="Nothing happens? Scroll up to the top of the page and tap it again.",
                     shot="f01-training-home.png", endpoint="training.home"),
                Step(title="Tick a step when you have done it", app=TC_APP, where="Any lesson → the step",
                     do="Do the step. Then tap I did this step",
                     expect="The button turns green and says Done. The step number turns into a green tick. Your "
                            "place is saved at once.",
                     if_wrong="Tapped it by mistake? Tap Done again and the tick goes away.",
                     shot="f01-lesson.png", endpoint="training.lesson"),
                Step(title="Ask the Tutor, then make it small", app=TC_APP,
                     where="Any lesson → Training Tutor (under the steps)",
                     do="Tap a question button such as Where is it? Then tap Minimize. Tap Open the Tutor to bring it "
                        "back",
                     expect="The Tutor answers about the step you are on. Minimize makes it small; Open the Tutor "
                            "brings it back. It stays the way you left it on every page.",
                     if_wrong="No answer? Check you have a signal and tap the question again.",
                     shot="f01-tutor.png", endpoint="training.lesson"),
                Step(title="Save and exit", app=TC_APP, where="Any lesson → Save and exit (below the practice exercise)",
                     do="Tap Save and exit. Later, tap Continue where I left off",
                     expect="Next time you are back at the first step you have not ticked. Green ticks stay green.",
                     if_wrong="Closed Safari by mistake? Nothing is lost. Open the training site and tap Continue "
                              "where I left off.",
                     endpoint="training.move"),
            ),
            exercise="On your iPhone: sign in to the training site, start your Field Crew training, tick step 1 of "
                     "this lesson, tap Save and exit, then come back with Continue where I left off and tick the rest.",
        ),
        Lesson(
            key="f01-activate", title="Set your password from the email",
            what="Open the email the office sent you and choose your own password.",
            why="Only you know your password. Nobody in the office can see it.",
            steps=(
                Step(title="Open the email", app=APP_EMAIL,
                     where="Mail on your iPhone → the email from CalibraytAI",
                     do="Tap the link in the email",
                     expect="Safari opens Set New Password.",
                     if_wrong="No email? Look in Junk. Then ask Ben to tap Email a link to choose a password. Use the "
                              "newest email: an older link stops working.",
                     endpoint="auth.reset_password"),
                Step(title="Choose your password", app=F, where="Set New Password",
                     do="Type the same new password in New Password and in Confirm New Password. Tap Reset Password",
                     enter="A password only you know, at least 12 characters, for example three words you will "
                           "remember",
                     expect="Password Updated. Your password has been reset. Return to Sign In.",
                     if_wrong="'Reset link unavailable' means the link was old or already used. Ask Ben for a new one.",
                     shot="f01-set-password.png", endpoint="auth.reset_password"),
                Step(title="Sign in with it", app=F, where="Password Updated → Return to Sign In",
                     do="Type your email and the new password. Tap Sign in",
                     expect="You are signed in under your own name.",
                     if_wrong="Refused? Use Forgot Password? on the sign-in page.",
                     shot="f01-sign-in.png", endpoint="auth.login"),
            ),
            exercise="If Ben sends you a set-password email on the training site, open it on your iPhone, choose your "
                     "password and sign in. If not, read the steps so you know them for the real site.",
        ),
        Lesson(
            key="f01-open-field", title="Open Field and look around",
            what="Open CalibraytAI Field and learn the buttons at the top.",
            why="Field is your app for the job: your work, the job address, drawings, photos, notes and your hours. "
                "It never shows money and never opens office pages.",
            steps=(
                Step(title="Open Field", app=F, where="Field Crew training home → Open Field",
                     do="Tap Open Field",
                     expect="Field opens at Today: Today, This week, This month and Company today along the top; "
                            "Help; Print; the date; My Work — your first name.",
                     if_wrong="If an office page opens, stop and tell Ben: you should be Field only.",
                     shot="f01-field-today.png", endpoint="field.today"),
                Step(title="The buttons at the very top", app=F, where="Field → the black bar at the top",
                     do="Find Guide, Password and Sign out",
                     expect="Guide opens your day on Field step by step. Password changes your password. Sign out "
                            "signs you out.",
                     if_wrong="On the training site a dark bar above it says Training site, with ← Back to my "
                              "training. That is only on the training site.",
                     shot="f01-field-today.png", endpoint="field.today"),
                Step(title="Open Guide", app=F, where="Field → Guide",
                     do="Tap Guide. Scroll down through the stages",
                     expect="Field Workflow: your day in five stages, SIGN IN → TODAY → ON THE JOB → CAPTURE → TIME. "
                            "Each stage has buttons that open the right Field page.",
                     why="On the training site each stage also lists your lessons and tests for it.",
                     if_wrong="Tap Today at the top to go back to your work.",
                     shot="f01-guide.png", endpoint="field.workflow"),
                Step(title="Office pages stay closed", app=F, where="Field",
                     do="Notice there is no office menu",
                     expect="Field has no menu for projects, customers, people or accounts. If you open an office "
                            "address, Field takes you back to Today.",
                     if_wrong="If you can open an office page, tell Ben. Your account should be Field only."),
                Step(title="Back to your training", app=F, where="Field → Training site bar → ← Back to my training",
                     do="Tap ← Back to my training",
                     expect="Your Field Crew training home opens again.",
                     if_wrong="Not there? Type the training site address and /training in Safari.",
                     endpoint="training.home"),
            ),
            exercise="Open Field from your training home, find Guide, Password and Sign out, then go back to your "
                     "training with ← Back to my training.",
        ),
        Lesson(
            key="f01-home-screen", title="Put Field on your Home Screen",
            what="Add CalibraytAI to your iPhone Home Screen so it opens like an app.",
            why="One tap opens today's work. You do not need to type the address again.",
            steps=(
                Step(title="Open Field in Safari", app=F, where="Safari (not Chrome) → Field Today",
                     do="Sign in if asked and open Today",
                     expect="Field Today is on the screen.",
                     if_wrong="Use Safari. Other browsers may not offer Add to Home Screen.",
                     shot="f01-field-today.png", endpoint="field.today"),
                Step(title="Add to Home Screen", app=F,
                     where="Safari → the Share button (a square with an arrow up) → Add to Home Screen",
                     do="Tap Share. Scroll down. Tap Add to Home Screen. Tap Add",
                     expect="A CalibraytAI icon is on your Home Screen.",
                     if_wrong="Add to Home Screen not in the list? Scroll the list down, or tap Edit Actions and add "
                              "it."),
                Step(title="Open it from the icon", app=F, where="iPhone Home Screen → the CalibraytAI icon",
                     do="Tap the icon",
                     expect="Field opens at Today. Sign in only if it asks.",
                     if_wrong="Asks you to sign in every time? Check Safari is not in Private mode."),
            ),
            exercise="Put Field on your iPhone Home Screen from Safari, close Safari, and open Field from the new icon.",
        ),
        Lesson(
            key="f01-password", title="Your password: change it or reset it",
            what="Change your password on Field, and get a new one if you forget it.",
            why="Keep your password to yourself. If someone else knows it, change it.",
            steps=(
                Step(title="Open Password", app=F, where="Field → Password (top of the screen)",
                     do="Tap Password",
                     expect="Change password. You sign in as <your email>.",
                     if_wrong="Not there? Tap Today first, then look at the black bar at the top.",
                     shot="f01-password.png", endpoint="auth.change_password"),
                Step(title="Change it", app=F, where="Change password",
                     do="Type your current password once and the new one twice. Tap Change password",
                     enter="Current password; New password (at least 8 characters); New password again",
                     expect="You are signed out. The message says: Your password is changed. Sign in with your email "
                            "and the new password.",
                     if_wrong="Current password refused? Use Forgot Password? on the sign-in page instead. "
                              "Back to Field leaves without changing anything.",
                     endpoint="auth.change_password"),
                Step(title="Forgot it?", app=F, where="Sign in → Forgot Password?",
                     do="Type your email. Tap Send Reset Instructions",
                     enter="Your email",
                     expect="Check your email. Open the newest email from CalibraytAI and set a new password (lesson "
                            "'Set your password from the email').",
                     if_wrong="No email after a few minutes? Look in Junk, then ask Ben to send you a new link from "
                              "People & Access.",
                     shot="f01-forgot.png", endpoint="auth.forgot_password"),
            ),
            exercise="On the training site, open Password on Field and read the page. Tap Back to Field without "
                     "changing anything (or change it, if Ben says so, and sign in again).",
        ),
    ),
)

# ====================================================================================== 2
M02 = Module(
    key="f02", pathway=P, number=2, title="Today's assigned work",
    summary="Read Today: the job you are booked on, its address and Directions, your crew and the day's delivery. "
            "Then confirm the job you are standing on.",
    roles=CREW,
    lessons=(
        Lesson(
            key="f02-my-work", title="Read My Work on Today",
            what="Find today's job, its address and how to get there.",
            why="Today shows only the work the office has booked for you or your crew today.",
            steps=(
                Step(title="Open Today", app=F, where="Field → Today",
                     do="Tap Today at the top",
                     expect=f"My Work — your first name. Under it: {JOB}, the address ({ADDRESS}), Directions, "
                            f"and a box with the work ({WORK}), your crew ({TEAM}) and Enter time.",
                     if_wrong="'Nothing is scheduled for you today.' means the office has not booked you or your crew "
                              "today. Look at This week, or call the office.",
                     shot="f02-today.png", endpoint="field.today"),
                Step(title="Get directions", app=F, where="Today → My Work → Directions",
                     do="Tap Directions (or tap the address)",
                     expect="Maps opens with the job address.",
                     if_wrong="Wrong place on the map? Call the office. Do not guess the address."),
                Step(title="Check the delivery", app=F, where="Today → My Work → the Delivery line",
                     do="Read the Delivery line, if there is one",
                     expect="Delivery: what is coming, from which store, for which job, the time window and its "
                            "status (for example Agreed).",
                     if_wrong="Questions about a delivery go to the office. The order is theirs, not yours.",
                     shot="c11-field-delivery.png", endpoint="field.today"),
                Step(title="Ask Help on any page", app=F, where="Any Field page → Help (under the top buttons)",
                     do="Tap Help",
                     expect="It says what this page is for, what to do and what comes next. You can type a question "
                            "under Ask about this screen.",
                     if_wrong="Tap Help again to close it.",
                     shot="f02-help.png", endpoint="field.today"),
            ),
            exercise=f"When the office has booked your crew on {JOB}, open Today on your iPhone, find the address and "
                     "tap Directions. Then open Help and read it.",
        ),
        Lesson(
            key="f02-confirm-job", title="Confirm the job you are on",
            what="Tell Field which job you are standing on.",
            why="Photos, notes, extra work and time all go to the job you confirm. Confirm the right one first.",
            steps=(
                Step(title="Choose Project", app=F, where="Today → Choose Project",
                     do="Tap Choose Project. Then tap the job's name",
                     enter=JOB,
                     expect="Projects lists only the jobs you are booked on. Select the job you are standing on.",
                     if_wrong="Your job is not listed? You are not booked on it. Call the office.",
                     shot="f02-projects.png", endpoint="field.projects"),
                Step(title="Confirm it", app=F, where="Confirm Project",
                     do="Tap Confirm for Today",
                     expect="You are back on Today. The job's name is under Today with Capture, Time, Extra work, "
                            "My time and Change project.",
                     why="Confirm and Capture or Confirm and Time do the same and go straight there.",
                     if_wrong="Picked the wrong job? Tap Change project and choose again. 'This Project is closed.' "
                              "means the office closed the job: call them.",
                     shot="f02-confirm.png", endpoint="field.project_confirm"),
                Step(title="Check it", app=F, where="Today → Today section",
                     do="Read the job name under Today",
                     expect=f"{JOB} with the buttons Capture, Time, Extra work, My time and Change project.",
                     if_wrong="Still says 'Confirm the project before capturing.'? Do step 1 again.",
                     shot="f02-today-confirmed.png", endpoint="field.today"),
            ),
            exercise=f"On your iPhone, choose {JOB} and tap Confirm for Today. Check its name shows under Today.",
        ),
        Lesson(
            key="f02-company-today", title="What the whole company has on today",
            what="See who in the company is working where today.",
            why="Handy when you need to find another crew. It is for reading only.",
            steps=(
                Step(title="Open Company today", app=F, where="Field → Company today",
                     do="Tap Company today at the top",
                     expect="What the company has scheduled today. This does not change dates.",
                     if_wrong="'Nothing is scheduled today.' means nothing is booked for anyone today.",
                     shot="f02-company-today.png", endpoint="field.company_today"),
                Step(title="Go back to your own work", app=F, where="Field → Today",
                     do="Tap Today",
                     expect="Your own work again.",
                     if_wrong="Your jobs are always on Today, not on Company today."),
            ),
            exercise="Open Company today on the training site and find which crew is on Harbour Lane, then go back to "
                     "Today.",
        ),
    ),
)

# ====================================================================================== 3
M03 = Module(
    key="f03", pathway=P, number=3, title="Weekly schedule and schedule changes",
    summary="See your week and month on Field, and what happens when the office moves your dates.",
    roles=CREW,
    lessons=(
        Lesson(
            key="f03-week", title="Your week",
            what="See the work booked for you this week.",
            why="Know where you are going tomorrow before you leave the site today.",
            steps=(
                Step(title="Open This week", app=F, where="Field → This week",
                     do="Tap This week at the top",
                     expect="Seven days. Today is marked. Each day shows its job, address, Directions, the work and "
                            "Enter time; a day with nothing shows —.",
                     if_wrong="'Nothing is scheduled for you this week.' means nothing is booked yet. Call the office.",
                     shot="f03-week.png", endpoint="field.week"),
                Step(title="Scroll down the days", app=F, where="This week",
                     do="Scroll down with your finger",
                     expect="Every day of the week, one under the other. No sideways scrolling.",
                     if_wrong="Page cut off on the side? Turn the phone upright and tap This week again."),
            ),
            exercise=f"Open This week and find which days you are on {JOB}.",
        ),
        Lesson(
            key="f03-month", title="Your month",
            what="See which days have work this month, and look at any day.",
            why="Plan ahead: holidays, appointments, a long job.",
            steps=(
                Step(title="Open This month", app=F, where="Field → This month",
                     do="Tap This month at the top",
                     expect="A calendar. A dot under a day means you have work that day. Today is marked.",
                     if_wrong="No dots? Nothing is booked for you this month yet.",
                     shot="f03-month.png", endpoint="field.month"),
                Step(title="Look at one day", app=F, where="This month → a day with a dot",
                     do="Tap the day",
                     expect="That day's work shows under the calendar.",
                     if_wrong="'No scheduled work for this day.' means that day is free."),
                Step(title="Other months", app=F, where="This month → Previous month / Next month",
                     do="Tap Next month, then Previous month",
                     expect="The calendar moves one month each tap.",
                     if_wrong="Tap This month at the top to come back to this month."),
            ),
            exercise="Open This month, tap a day with a dot and read its work. Then look at next month.",
        ),
        Lesson(
            key="f03-changes", title="When the office changes your dates",
            what="See your new dates after the office moves your work, and know who changes dates.",
            why="Weather and deliveries move jobs. Only the office changes dates, so check Field each morning and "
                "evening.",
            steps=(
                Step(title="Only the office moves dates", app=F, where="This week, This month, Company today",
                     do="Notice there is no button to change a date",
                     expect="Field pages say: This does not change dates. Dates are changed in the office.",
                     if_wrong="A date looks wrong? Call the office. Do not go to a job you are not booked on."),
                Step(title="See the new dates", app=F, where="Field → This week",
                     do="Tap This week again (or close and reopen Field)",
                     expect="The work shows on its new days.",
                     why="Field does not send a message when a date moves. It checks for the newest schedule each "
                         "time a page opens, and when you come back to the app after a few minutes.",
                     if_wrong="Still the old dates? Check you have a signal (lesson 'No signal'). An Offline bar means "
                              "you are looking at the copy saved on the phone.",
                     shot="f03-week-moved.png", endpoint="field.week"),
                Step(title="A warning on a day", app=F, where="This week or Today → a yellow line on the work",
                     do="Read it",
                     expect="For example: You are already scheduled elsewhere. Under it: This is information only. "
                            "You can keep working.",
                     if_wrong="Not sure where to go? Call the office before you drive."),
            ),
            exercise="Ask the trainer (or Ben) to move your Harbour Lane dates on the training site. Then tap This "
                     "week again and find the work on its new days.",
        ),
    ),
)

# ====================================================================================== 4
M04 = Module(
    key="f04", pathway=P, number=4, title="Drawings and job information",
    summary="Open the job's construction drawings and plans on your iPhone, and know what job information Field "
            "shows and what you ask the office for.",
    roles=CREW,
    lessons=(
        Lesson(
            key="f04-drawings", title="Open the job's drawings and plans",
            what="Open the drawings the office put on the job.",
            why="Build from the plan the office uploaded, not from an old printout.",
            steps=(
                Step(title="Choose the job", app=F, where="Today → Choose Project (or Change project) → the job",
                     do="Tap the job's name",
                     enter=JOB,
                     expect="Confirm Project with Confirm and Capture, Confirm and Time, Confirm for Today, and "
                            "Drawings and plans.",
                     if_wrong="Job not listed? You are not booked on it. Call the office.",
                     shot="f04-confirm.png", endpoint="field.project_confirm"),
                Step(title="Open Drawings and plans", app=F, where="Confirm Project → Drawings and plans",
                     do="Tap Drawings and plans",
                     expect="Drawings and plans, with the job name. Construction drawings (Revision, sheets) and "
                            "Plans (the PDF names) are listed.",
                     if_wrong="'No drawings or plans for this job yet. Ask the office.' Nothing has been uploaded yet.",
                     shot="f04-drawings.png", endpoint="field.drawings"),
                Step(title="Open a plan", app=F, where="Drawings and plans → a plan's name",
                     do="Tap the name",
                     expect="The PDF opens in a new tab. Pinch with two fingers to zoom in. Close the tab to come back.",
                     if_wrong="It will not open? Check your signal. Drawings open only with a connection."),
                Step(title="Back to the job", app=F, where="Drawings and plans → Back to the job",
                     do="Tap Back to the job",
                     expect="Confirm Project for the same job.",
                     if_wrong="Tap Today at the top to start again."),
            ),
            exercise=f"Open {JOB} → Drawings and plans on your iPhone and open the deck plan. Zoom in on the pool.",
        ),
        Lesson(
            key="f04-job-info", title="What Field shows about the job, and what it does not",
            what="Know which job information is on Field, and what to ask the office for.",
            why="Field shows what the crew needs to build. Office records stay in the office.",
            steps=(
                Step(title="What Field shows", app=F, where="Today, This week, Confirm Project",
                     do="Read the job card",
                     expect="The job name and number, the address with Directions, the work and the crew booked, "
                            "the day's delivery, the drawings and plans, and the photos and notes already sent "
                            "(Recent observations).",
                     if_wrong="Something missing that you need on site? Call the office.",
                     shot="f04-confirm.png", endpoint="field.project_confirm"),
                Step(title="What Field does not show", app=F, where="Field",
                     do="Know what to ask the office for",
                     expect="Field does not show the customer's phone number, the contract, the material list or "
                            "any money. You cannot draw on a plan or upload one from Field. The office does those.",
                     if_wrong="Need a measurement that is not on the plan? Call the office. Do not guess."),
            ),
            exercise=f"On {JOB}, find the address, the crew, the Recent observations and the plan on your iPhone. "
                     "Write down one thing you would have to ask the office for.",
        ),
    ),
)

# ====================================================================================== 5
# TIME ENTRY LESSONS (Joel, 22 Oct 2026): everything about Time, My time, returned time, Ben's approval and
# shop / company time is in this module only (f05-send-time, f05-my-time-review, f05-returned-time,
# f05-approved, f05-company-time, f05-banked-hours (22 Oct 2026, shots f05-banked-*.png from
# tools/release/evidence_time_payroll.mjs TRAINING_SHOTS); shots f05-time*.png, f05-my-time*.png, f05-today-returned.png and
# f05-company-time.png from the TIME ENTRY steps of tools/training/capture_field_crew_shots.mjs; UAT
# uat-f05-time*, uat-f05-my-time, uat-f05-returned, uat-f05-approved, uat-f05-company-time). Written against
# the final Field time screens recorded in docs/operations/field-time.md (merged 22 Oct 2026). When those
# screens change, re-check these labels and re-capture these pictures here, and nowhere else.
M05 = Module(
    key="f05", pathway=P, number=5, title="Recording field work",
    summary="Send your daily hours on the iPhone against the job and the work, check your week on My time, fix "
            "time Ben returns, see when Ben approves it, record shop and company time, and record extra "
            "work the customer asks for.",
    roles=CREW,
    lessons=(
        Lesson(
            key="f05-send-time", title="Send your hours",
            what="Send the hours you worked today on the job, against the work you did.",
            why="The office checks your hours against the job's work before they count. Send them every day.",
            steps=(
                Step(title="Open Time", app=F, where="Today → Enter time (on the job's card), or Time",
                     do="Tap Enter time on the job's card",
                     expect="Time, the job name, Date (today), Scheduled today with a button for your booked work, "
                            "Choose different work, Hours, Note and Send time.",
                     if_wrong="Asked to choose the job? Do lesson 'Confirm the job you are on' first. A date in "
                              "the future is refused: 'Time cannot be recorded for a future date.'",
                     shot="f05-time-scheduled.png", endpoint="field.time_entry"),
                Step(title="Pick the work", app=F, where="Time → Scheduled today",
                     do="Tap the button with your booked work. If a Work box opens, pick the work you did in it",
                     enter=f"{WORK}, then Work: {ACTIVITY}",
                     expect="The work is chosen. When the booked work item has only one work, it is filled in for "
                            "you.",
                     why="Did something else today? Tap Choose different work and pick the Work item and the "
                         "Work. Recent work shows what you used last on this job.",
                     if_wrong="'Choose the work you did.' (or '... on <work item>') means the Work box is empty: "
                              "pick one. Your work is not there? Call the office.",
                     shot="f05-time.png", endpoint="field.time_entry"),
                Step(title="Type your hours and a note", app=F, where="Time → Hours and Note",
                     do="Type the hours. Add a short note if it helps",
                     enter="Hours: 8. Note: Ledger and joists, north side (training)",
                     expect="Hours go in quarter hours: 7.5 is seven and a half hours. Up to 16 hours in one entry "
                            "and 24 in a day.",
                     if_wrong="'Enter the hours worked.' means Hours is empty. 'Hours for one day cannot be more "
                              "than 24.00.' means your day adds up to too much."),
                Step(title="Send it", app=F, where="Time → Send time",
                     do="Tap Send time",
                     expect="Time sent for approval. My time opens and lists it as Submitted.",
                     if_wrong="No signal? Time needs a connection. Write your hours down and send them when you "
                              "have a signal.",
                     shot="f05-time-sent.png", endpoint="field.my_time"),
            ),
            exercise=f"Send 8 hours on {JOB} for today against {ACTIVITY}, with a short note, and find it on My "
                     "time.",
        ),
        Lesson(
            key="f05-my-time-review", title="Check your week on My time",
            what="Look over the hours you sent this week, every day, on My time.",
            why="My time is your own record: what you sent, for which job and work, and where it is with Ben.",
            steps=(
                Step(title="Open My time", app=F, where="Today → My time",
                     do="Tap My time",
                     expect="My time. At the top: This week (from Mon …): your hours · Approved · Waiting · "
                            "Returned. Then your entries, newest first.",
                     if_wrong="'No time recorded yet.' means you have not sent any time.",
                     shot="f05-my-time-week.png", endpoint="field.my_time"),
                Step(title="Read each entry", app=F, where="My time → an entry",
                     do="Read the date and status, the job, the work item — work, and the hours",
                     expect="Submitted: 'Waiting for approval. Ask the office if something is wrong; they can "
                            "return it to you.' Returned: Ben sent it back. Approved: it counts. Replaced: the "
                            "office corrected it after approval. The kind of work shows too (Original work, "
                            "Extra work, Company time).",
                     if_wrong="An entry is missing? Send it now from Time. Two for the same work and day? Tell "
                              "Ben; do not send it again.",
                     shot="f05-time-sent.png", endpoint="field.my_time"),
                Step(title="Check it is right", app=F, where="My time → each entry",
                     do="Check the date, the job, the work and the hours",
                     expect="Every day you worked is there once, on the right job and work.",
                     if_wrong="Wrong but still Submitted? Call Ben; he can return it to you to fix."),
            ),
            exercise="After sending your Harbour Lane hours, open My time and read the week's hours at the top and "
                     "your entry's status.",
        ),
        Lesson(
            key="f05-returned-time", title="Time Ben sent back",
            what="See time Ben returned, and fix it and send it again.",
            why="Returned time is not lost. Fix what the reason says and send it again.",
            steps=(
                Step(title="See it on Today", app=F, where="Field → Today (red line at the top)",
                     do="Tap the red line: '1 time entry was returned to you. Fix and send again on My time.'",
                     expect="My time opens.",
                     if_wrong="No red line? Nothing was returned. My time also says how many entries were returned.",
                     shot="f05-today-returned.png", endpoint="field.today"),
                Step(title="Read the reason", app=F, where="My time → the Returned entry",
                     do="Read 'Returned: …' under the entry",
                     expect="Ben's reason, for example 'Returned: You left at 3:30. Please send 7.5 hours.', and "
                            "Fix and send again.",
                     if_wrong="Do not understand the reason? Call Ben before you send it again.",
                     shot="f05-time-returned.png", endpoint="field.my_time"),
                Step(title="Fix it and send it again", app=F, where="My time → Fix and send again",
                     do="Tap Fix and send again. Change what the reason says. Tap Send time",
                     enter="For example: Hours 7.5",
                     expect="Time opens with Returned: and the reason at the top and your entry filled in. After "
                            "Send time: 'Time sent again for approval.' My time shows it as Submitted again.",
                     if_wrong="No Fix and send again button? Only Returned time can be fixed. Approved time is done.",
                     shot="f05-time-fix.png", endpoint="field.time_entry"),
            ),
            exercise="When the trainer returns your Harbour Lane time on the training site, open it from the red line "
                     "on Today, fix it and send it again.",
        ),
        Lesson(
            key="f05-approved", title="When Ben approves your hours",
            what="See your hours approved, and know what happens if something is still wrong after that.",
            why="Approved hours are final and count for the job. Only the office can correct them, and the first "
                "entry is kept.",
            steps=(
                Step(title="Ben approves (the office's step)", app=F, where="Nothing to do on Field",
                     do="Wait for Ben. In the office he opens your entry and presses Approve, or Return with a "
                        "reason",
                     expect="You do nothing on Field for this step.",
                     if_wrong="Waiting a long time? Ask Ben. Field does not send a message when he approves."),
                Step(title="See it approved", app=F, where="Today → My time",
                     do="Tap My time",
                     expect="The entry says Approved, with no Fix and send again and no 'Waiting for approval'. The "
                            "week line counts it under Approved.",
                     if_wrong="Still Submitted? Ben has not looked yet. Returned? Do lesson 'Time Ben sent back'.",
                     shot="f05-time-approved.png", endpoint="field.my_time"),
                Step(title="Wrong after it was approved", app=F, where="My time",
                     do="Do not send the same hours again. Call Ben",
                     expect="Ben corrects it in the office. The old entry is kept and shows Replaced; the corrected "
                            "one is listed too.",
                     if_wrong="Sent it twice by mistake? Tell Ben which one is right."),
            ),
            exercise="When Ben approves your fixed Harbour Lane hours on the training site, open My time and find "
                     "Approved.",
        ),
        Lesson(
            key="f05-company-time", title="Shop / Company Work",
            what="Send paid hours that are not for a customer's job: the shop and yard, equipment upkeep, picking up "
                 "material, safety meetings, office work.",
            why="Shop / Company Work is paid like any other time but is never billed to a customer. Keep it off the "
                "customer's job.",
            steps=(
                Step(title="Open Shop / Company Work", app=F, where="Today → Shop / Company Work (or My time → Shop / "
                                                                    "Company Work)",
                     do="Tap Shop / Company Work",
                     expect="Time for 'Shop / Company Work', with 'Shop / Company Work: paid company time, not a "
                            "customer's job, never billed to a customer. Choose the kind of work below.'",
                     why="The office sets it up once (Set up Shop / Company Work). Until then the button is not there.",
                     if_wrong="No Shop / Company Work button? Ask Ben to set it up.",
                     shot="f05-company-time.png", endpoint="field.my_time"),
                Step(title="Pick the kind of work and send", app=F, where="Shop / Company Work → Work",
                     do="Pick the Work, type the hours, tap Send time",
                     enter="Work: Equipment and vehicle upkeep. Hours: 1.5",
                     expect="Time sent for approval. My time lists it with Company time.",
                     why="The kinds of work are: Shop and yard, Equipment and vehicle upkeep, Material pickup and "
                         "deliveries, Safety meetings and training, Office and estimating (and any the office adds). "
                         "There is no Extra work here, and it does not change the job you are on today.",
                     if_wrong="'Choose the work you did.' means Work is empty."),
            ),
            exercise="Once Ben has set it up on the training site, send 1.5 hours of Equipment and vehicle upkeep as "
                     "Shop / Company Work and find it on My time.",
        ),
        Lesson(
            key="f05-banked-hours", title="Your banked hours",
            what="See how many hours you have banked, this week's hours, and what was earned or taken.",
            why="Hours over the company's work week are banked under the company's own hours policy. You see your "
                "own balance on the phone; the office records time off.",
            steps=(
                Step(title="See your balance", app=F, where="Field → Today (or My time)",
                     do="Look at the Banked hours card at the top",
                     expect="Banked hours in large figures, this week (worked approved · regular · extra · banked) and "
                            "the company's hours policy in one line.",
                     why="Only approved hours count. Hours waiting for approval are not in it yet.",
                     if_wrong="No card? The office has not entered the hours policy yet.",
                     shot="f05-banked-hours.png", endpoint="field.today"),
                Step(title="See the history", app=F, where="Banked hours card → See banked hours",
                     do="Tap See banked hours",
                     expect="Each week earned (with that week's worked, regular and extra hours), time off taken and "
                            "adjustments, with the reason.",
                     if_wrong="Something looks wrong? Ask the office; they can correct approved time or adjust it.",
                     shot="f05-banked-history.png", endpoint="field.banked_hours"),
                Step(title="Time off", app=F, where="Ask the office",
                     do="Tell the office the day and the hours you want off",
                     expect="After the office records it, the history shows Time off taken and the balance goes down.",
                     if_wrong="You cannot record time off on the phone; the office does it."),
            ),
            exercise="After Ben approves your Harbour Lane hours on the training site, open Today and read your Banked "
                     "hours card and the policy line under it.",
        ),
        Lesson(
            key="f05-extra-work", title="Extra work the customer asks for",
            what="Record it when the customer asks for something that is not in the job.",
            why="If the customer asks you to add, remove, move or change something outside the work you were sent "
                "to do, record it as Extra work. The office then agrees it with the customer.",
            steps=(
                Step(title="Open Extra work", app=F, where="Today → Extra work",
                     do="Tap Extra work",
                     expect="Extra work, the job name, the rule about extra work, and the form.",
                     if_wrong="Asked to confirm the job? Confirm it first.",
                     shot="f05-extra-work.png", endpoint="field.extra_work"),
                Step(title="Say what they asked for", app=F, where="Extra work",
                     do="Type What did the customer ask for?. Leave New work item and type a New work item name",
                     enter="Morgan asked for two extra steps down to the lawn on the east side. (training). New work "
                           "item name: Extra steps to the lawn (training)",
                     expect="Your words are in the boxes.",
                     why="Never promise the customer anything about money on site. The office agrees that.",
                     if_wrong="It belongs to work already on the job? Choose it under Existing work item instead."),
                Step(title="Record it", app=F, where="Extra work → Record extra work",
                     do="Tap Record extra work",
                     expect="Extra work recorded. You are back on Today.",
                     if_wrong="'Describe the extra work.' means the first box was empty.",
                     shot="f05-extra-recorded.png", endpoint="field.today"),
                Step(title="Hours on extra work", app=F, where="Time → + Extra work",
                     do="When you send time for extra work, tap + Extra work on the Time page and describe it",
                     expect="The time is marked as extra work for the office.",
                     if_wrong="Not sure if it is extra? Ask the office before you start it."),
            ),
            exercise="Record Morgan's request for two extra steps to the lawn as Extra work on Harbour Lane.",
        ),
    ),
)

# ====================================================================================== 6
M06 = Module(
    key="f06", pathway=P, number=6, title="Photos, notes and progress updates",
    summary="Send photos, notes and voice notes from the site with Capture. A progress update is a note with "
            "photos; the office reads them on the job.",
    roles=CREW,
    lessons=(
        Lesson(
            key="f06-capture", title="Send a photo and a note",
            what="Save a note and a photo to the job.",
            why="Photos and notes are the job's record of what happened on site. The office sees them on the job "
                "under Field Observations.",
            steps=(
                Step(title="Open Capture", app=F, where="Today → Capture (or Confirm and Capture)",
                     do="Tap Capture",
                     expect="Capture, the job name, Notes, Record, Take Photo, Choose Photo and Save original.",
                     if_wrong="Asked to confirm the job? Confirm it first.",
                     shot="f06-capture.png", endpoint="field.capture"),
                Step(title="Type a note", app=F, where="Capture → Notes",
                     do="Tap Notes and type what happened",
                     enter="Ledger and joists in on the north side. Pool coping protected with plywood. (training)",
                     expect="Your words in the Notes box.",
                     if_wrong="Keyboard covers the buttons? Tap Done on the keyboard or scroll down."),
                Step(title="Add a photo", app=F, where="Capture → Take Photo (camera) or Choose Photo (photo library)",
                     do="Tap Take Photo and take it, or tap Choose Photo and pick one",
                     expect="The photo is listed under the buttons, with Remove photo.",
                     if_wrong="Camera does not open? When the iPhone asks, tap Allow. Or: Settings → Safari → Camera "
                              "→ Allow.",
                     shot="f06-capture.png", endpoint="field.capture"),
                Step(title="Save it", app=F, where="Capture → Save original",
                     do="Tap Save original",
                     expect="Saved.",
                     if_wrong="'Add a photo, recording, or note before saving.' means it was empty. No signal: see "
                              "lesson 'No signal on site'.",
                     shot="f06-capture-saved.png", endpoint="field.capture"),
            ),
            exercise="On Harbour Lane, capture a note and a photo of the framing (any photo will do on the training "
                     "site) and wait for Saved.",
        ),
        Lesson(
            key="f06-voice-note", title="A voice note instead of typing",
            what="Record a short voice note when your hands are full.",
            why="Quicker than typing with gloves on.",
            steps=(
                Step(title="Record", app=F, where="Capture → Record",
                     do="Tap Record and speak. Tap Stop when you finish",
                     expect="A player appears so you can listen. Discard recording deletes it.",
                     if_wrong="'Microphone permission was denied.' Tap Allow next time, or Settings → Safari → "
                              "Microphone → Allow. Photo and text still work.",
                     shot="f06-capture.png", endpoint="field.capture"),
                Step(title="Save it", app=F, where="Capture → Save original",
                     do="Tap Save original",
                     expect="Saved. On the job it shows Audio attached.",
                     if_wrong="'Voice capture is not available on this phone.' Type a note instead."),
            ),
            exercise="Record a ten-second voice note on Harbour Lane, listen to it, and save it.",
        ),
        Lesson(
            key="f06-progress", title="Progress updates for the office",
            what="Send a progress update: a note and photos at each stage of the work.",
            why="The office cannot see the site. Your notes and photos tell them how far the job is.",
            steps=(
                Step(title="At each stage, capture it", app=F, where="Today → Capture",
                     do="Take a photo and write one line: what is done, what is next, anything in the way",
                     enter="Framing done on the north side. Decking starts tomorrow. Need more joist hangers. "
                           "(training)",
                     expect="Saved.",
                     why="Field has no percent-complete or status button. A note with photos is the progress update.",
                     if_wrong="Something urgent, like a safety problem or a missing delivery? Call the office as well. "
                              "A note is not a phone call.",
                     shot="f06-capture.png", endpoint="field.capture"),
                Step(title="See what was sent", app=F, where="Today → Recent observations",
                     do="Scroll down on Today",
                     expect="Recent observations: who sent it, when, the note and the photo. Your crew's are there "
                            "too.",
                     if_wrong="Your note is not there? Check Pending on this phone (lesson 'No signal on site').",
                     shot="f06-recent.png", endpoint="field.today"),
            ),
            exercise="Send a progress update on Harbour Lane: one photo and one line saying what is done and what is "
                     "next. Find it under Recent observations.",
        ),
    ),
)

# ====================================================================================== 7
M07 = Module(
    key="f07", pathway=P, number=7, title="Offline use, refresh and troubleshooting",
    summary="Work with no signal, get the newest schedule, and fix the common problems yourself.",
    roles=CREW,
    lessons=(
        Lesson(
            key="f07-offline", title="No signal on site",
            what="Keep working when the phone has no signal.",
            why="Many sites have no signal. Field keeps your photos and notes on the phone until it can send them.",
            steps=(
                Step(title="The Offline bar", app=F, where="Any Field page with no signal",
                     do="Read the bar at the top",
                     expect="Offline — showing the copy saved on <day and time>. The schedule may be out of date. It "
                            "refreshes when you are back online.",
                     if_wrong="Today, This week, This month, Company today, Projects and Capture open with no "
                              "signal if you opened them before. Time, Extra work and drawings need a signal.",
                     shot="f07-offline-banner.png", endpoint="field.today"),
                Step(title="Capture with no signal", app=F, where="Capture → Save original",
                     do="Save your note or photo as normal",
                     expect="Saved on this phone — will sync when connected. Pending on this phone lists it as "
                            "Unsent.",
                     if_wrong="Keep Field open where you get a signal. It sends by itself.",
                     shot="f07-offline-saved.png", endpoint="field.capture"),
                Step(title="Back in signal", app=F, where="Field, open",
                     do="Open Field where you have a signal and wait a moment",
                     expect="Saved. Pending on this phone goes away.",
                     if_wrong="'Sync needs attention — your work is still on this phone'? Keep Field open and try "
                              "again in signal. Do not sign out.",
                     shot="f07-synced.png", endpoint="field.capture"),
                Step(title="Do not sign out with work waiting", app=F, where="Field → Sign out",
                     do="If anything is pending, do not sign out",
                     expect="If you tap Sign out, Field warns: Work on this phone has not reached the office. Signing "
                            "out removes it from this phone. Sign out?",
                     if_wrong="Tap Cancel. Get a signal, wait for Saved, then sign out."),
            ),
            exercise="On the training site, put your iPhone in Airplane mode, save a note on Capture, read the "
                     "message, then turn Airplane mode off with Field open and wait for Saved.",
        ),
        Lesson(
            key="f07-refresh", title="Get the newest schedule",
            what="Make sure you see the newest schedule.",
            why="The office may have changed your day. There is no refresh button on Field.",
            steps=(
                Step(title="Tap the page again", app=F, where="Field → Today (or This week)",
                     do="Tap Today (or This week) at the top",
                     expect="The page opens again with the newest schedule.",
                     if_wrong="An Offline bar? You have no signal; see 'No signal on site'.",
                     shot="f02-today.png", endpoint="field.today"),
                Step(title="Or close and reopen", app=F, where="The CalibraytAI icon on the Home Screen",
                     do="Swipe the app away and tap the icon again",
                     expect="Field opens at Today with the newest schedule.",
                     why="Field also checks by itself when you come back to it after a couple of minutes.",
                     if_wrong="Still old? Call the office to check what they changed."),
            ),
            exercise="Open This week, ask the trainer to move a date, then tap This week again and see the change.",
        ),
        Lesson(
            key="f07-troubleshooting", title="When something goes wrong",
            what="Fix the common problems yourself, and know when to call the office.",
            why="Most problems take one tap to fix.",
            steps=(
                Step(title="Cannot sign in", app=F, where="Sign in",
                     do="Check the email. Tap the eye to see the password. Then try Forgot Password?",
                     expect="You can sign in, or a reset email arrives.",
                     if_wrong="No email? Ask Ben for a new link from People & Access.",
                     shot="f01-sign-in.png", endpoint="auth.login"),
                Step(title="Nothing on Today", app=F, where="Today",
                     do="Look at This week. Then call the office",
                     expect="'Nothing is scheduled for you today.' means you are not booked today.",
                     if_wrong="Booked but not shown? The office may have booked a different crew."),
                Step(title="An office page sent me back to Today", app=F, where="Field",
                     do="Nothing to fix",
                     expect="That is right. Field-only crew cannot open office pages.",
                     if_wrong="Need something from the office? Call them."),
                Step(title="'This Project is closed.'", app=F, where="Projects or Confirm Project",
                     do="Choose a different project, or call the office",
                     expect="Closed jobs are not worked on from Field.",
                     if_wrong="Still working there? The office reopens it."),
                Step(title="Something else", app=TC_APP, where="The lesson → My notes and feedback",
                     do="Write what you pressed and what the screen said. Tap Save note. Then call the office",
                     expect="Your note is saved. Ben sees it on the administrator dashboard.",
                     if_wrong="Use Guide on Field to see your day step by step.",
                     endpoint="training.add_feedback"),
            ),
            exercise="Sign out and sign in again; open an office address such as /projects/ and see Field take you "
                     "back to Today; write one note under My notes and feedback.",
        ),
    ),
)

# ====================================================================================== 8
M08 = Module(
    key="f08", pathway=P, number=8, title="Complete working-day exercise and Field UAT",
    summary="Do a whole working day on Field, then run the Field acceptance tests: Pass, Fail or Blocked, with "
            "notes, and retest after a fix.",
    roles=CREW,
    lessons=(
        Lesson(
            key="f08-working-day", title="A whole working day on Field",
            what="Do a full day on Field, start to finish.",
            why="Everything the office needs from the site comes from these few taps.",
            steps=(
                Step(title="Morning", app=F, where="The CalibraytAI icon → Today",
                     do="Read My Work, the address and the delivery. Tap Directions if you need them",
                     expect="Today's job, address, crew and any delivery.",
                     if_wrong="Nothing booked? Call the office.",
                     shot="f02-today.png", endpoint="field.today"),
                Step(title="On site", app=F, where="Today → Choose Project → Confirm for Today",
                     do="Confirm the job. Open Drawings and plans if you need them",
                     expect="The job's name under Today with Capture, Time and Extra work.",
                     if_wrong="Wrong job? Change project.",
                     shot="f02-today-confirmed.png", endpoint="field.project_confirm"),
                Step(title="During the day", app=F, where="Today → Capture; Today → Extra work",
                     do="Send notes and photos as the work goes. Record anything extra the customer asks for",
                     expect="Saved after each one; Extra work recorded.",
                     if_wrong="No signal? It waits on the phone and sends later.",
                     shot="f06-capture-saved.png", endpoint="field.capture"),
                Step(title="End of the day", app=F, where="Today → Enter time → Send time; then My time",
                     do="Send your hours. Check My time",
                     expect="Time sent for approval; My time lists today as Submitted.",
                     if_wrong="Returned later? Fix and send again.",
                     shot="f05-time-sent.png", endpoint="field.my_time"),
                Step(title="Tomorrow", app=F, where="This week",
                     do="Check where you are tomorrow",
                     expect="Tomorrow's job on This week.",
                     if_wrong="Not sure? Call the office before you leave.",
                     shot="f03-week.png", endpoint="field.week"),
            ),
            exercise="Do a training day on Harbour Lane, all from the Home Screen icon: confirm the job, send one "
                     "note with a photo, record one extra work request, send your hours and check My time.",
        ),
        Lesson(
            key="f08-field-uat", title="Field acceptance tests",
            what="Run the Field acceptance tests and record Pass, Fail or Blocked.",
            why="The tests show Field works the way your crew need before the real jobs. They are kept apart from "
                "your lessons.",
            steps=(
                Step(title="Open Acceptance tests", app=TC_APP, where="Field Crew training → Acceptance tests",
                     do="Tap Acceptance tests, then Continue testing",
                     expect="The test opens: Start here, Do this, Expected result.",
                     if_wrong="Lost? Tap My training at the top, then Acceptance tests.",
                     shot="f08-uat-list.png", endpoint="training.uat"),
                Step(title="Do the test on Field", app=F, where="Where the test says to start",
                     do="Do exactly what Do this says, on Field",
                     expect="You can compare what you saw with Expected result.",
                     if_wrong="Could not get that far (no signal, page will not open)? That is Blocked."),
                Step(title="Record the result", app=TC_APP, where="The test → Result",
                     do="Tap Pass, Fail or Blocked. For Fail or Blocked, write what went wrong. Tap Save result",
                     enter="What went wrong: what you tapped and the words on the screen",
                     expect="Result saved. The next test you have not done opens. After the last one, Acceptance "
                            "tests opens with every result.",
                     if_wrong="'Say what went wrong' means Fail or Blocked needs the box filled in.",
                     shot="f08-uat-case.png", endpoint="training.uat_case"),
                Step(title="Retest after a fix", app=TC_APP, where="Acceptance tests → Retest (beside a Fail or Blocked)",
                     do="When Ben says it is fixed, tap Retest, do the test again and record the new result",
                     expect="A new attempt is added. Your earlier results stay under Earlier results.",
                     if_wrong="Still failing? Record Fail again with what you saw. Continue testing never reopens a "
                              "test you already did; use Retest."),
            ),
            exercise="Run every Field acceptance test on the training site and record each result.",
        ),
    ),
)

MODULES = (M01, M02, M03, M04, M05, M06, M07, M08)


def _u(key, module, title, start, action, expected):
    return UatCase(key=key, pathway=P, module_key=module, title=title, start=start, action=action, expected=expected,
                   roles=CREW)


UAT_CASES = (
    _u("uat-f01-sign-in", "f01", "Sign in on the iPhone and start Field Crew training",
       "Your iPhone, Safari, the training site → I work on a crew (Field)",
       "Sign in with your training email and password, then tap Start my Field Crew training.",
       "Your Field Crew training opens with 8 modules. No contractor office or supplier lessons are listed."),
    _u("uat-f01-field-only", "f01", "Office pages stay closed",
       "Field → Today on your iPhone",
       "Type the office addresses /projects/ and /settings/people after the training site address.",
       "Each one takes you back to Field Today. No office page, customer or money is shown."),
    _u("uat-f01-home-screen", "f01", "Field from the Home Screen icon",
       "Safari → Field Today → Share → Add to Home Screen",
       "Add the icon, close Safari and open Field from the icon.",
       "Field opens at Today under your name."),
    _u("uat-f02-today", "f02", "Today shows your booked job",
       "Field → Today on a day your crew is booked on Harbour Lane",
       "Read My Work. Tap Directions.",
       f"{JOB}, {ADDRESS}, the work and your crew are shown; Directions opens the map. No money anywhere."),
    _u("uat-f02-confirm", "f02", "Confirm the job",
       "Field → Today → Choose Project",
       f"Choose {JOB} and tap Confirm for Today.",
       "Today shows the job with Capture, Time, Extra work, My time and Change project."),
    _u("uat-f03-week-month", "f03", "Week and month",
       "Field → This week, then This month",
       "Find your Harbour Lane days on This week, then tap one of those days on This month.",
       "The same days show the work on both pages, with the address. No sideways scrolling on the iPhone."),
    _u("uat-f03-change", "f03", "A date change shows on Field",
       "Field → This week, after the office moves your Harbour Lane dates",
       "Tap This week again.",
       "The work shows on the new days. Field has no button to change a date."),
    _u("uat-f04-drawings", "f04", "Drawings and plans open",
       f"Field → Choose Project → {JOB} → Drawings and plans",
       "Tap the plan's name.",
       "The plan PDF opens on the iPhone. Back to the job returns to the job."),
    _u("uat-f05-time", "f05", "Send time",
       "Field → Today → Enter time",
       "Tap the Scheduled today button for your work (pick the Work if the box opens), type 8 hours and a note, "
       "tap Send time.",
       "Time sent for approval; My time lists the day as Submitted and the week line counts it under Waiting."),
    _u("uat-f05-my-time", "f05", "Review hours on My time",
       "Field → Today → My time, after sending today's hours",
       "Read the newest entry.",
       "The week line shows this week's hours by Approved, Waiting and Returned; the entry shows today's date, "
       "Submitted, the job, the work item and the work, the hours and 'Waiting for approval'."),
    _u("uat-f05-returned", "f05", "Fix returned time",
       "Field → Today, after the office returns your time with a reason",
       "Tap the red returned-time line, then Fix and send again, change the hours, tap Send time.",
       "Today's line opens My time with 'Returned: <reason>'; Time opens with the entry filled in; after sending: "
       "'Time sent again for approval.' and My time shows it as Submitted."),
    _u("uat-f05-approved", "f05", "Ben approves the hours (Ben's step, then the crew's check)",
       "Office: Ben opens the time waiting for review and presses Approve. Then Field → My time on the iPhone",
       "After Ben approves your fixed entry, open My time.",
       "The entry says Approved and has no Fix and send again button. A failing result here goes on Ben's "
       "administrator dashboard."),
    _u("uat-f05-company-time", "f05", "Shop / Company Work",
       "Office first: Ben presses Set up Shop / Company Work (Time review, once). Then Field → Today",
       "Tap Shop / Company Work, pick Equipment and vehicle upkeep, type 1.5, tap Send time.",
       "Time sent for approval; My time lists it as Company time; it is not on the customer's job and Today's "
       "job is unchanged."),
    _u("uat-f05-banked-hours", "f05", "See your banked hours",
       "Office first: the owner has entered the hours policy and Ben has approved your hours. Then Field → Today",
       "Read the Banked hours card, then tap See banked hours.",
       "The card shows your balance, this week's worked, regular, extra and banked hours, and the company's policy; "
       "the history lists each week earned. No pay, rate or money anywhere; no sideways scrolling."),
    _u("uat-f05-extra-work", "f05", "Record extra work",
       "Field → Today → Extra work",
       "Describe the customer's request, name a new work item, tap Record extra work.",
       "Extra work recorded; you are back on Today."),
    _u("uat-f06-capture", "f06", "Photo and note saved",
       "Field → Today → Capture",
       "Type a note, add a photo, tap Save original.",
       "Saved; the note and photo are under Recent observations on Today."),
    _u("uat-f07-offline", "f07", "Capture with no signal",
       "Field → Capture, iPhone in Airplane mode",
       "Save a note. Turn Airplane mode off with Field open.",
       "First 'Saved on this phone — will sync when connected', then Saved; nothing is lost."),
    _u("uat-f08-day", "f08", "A whole working day",
       "The CalibraytAI icon on the iPhone",
       "Today, confirm the job, Capture, Extra work, Enter time, My time.",
       "Every step completes; Saved, Extra work recorded and Time sent for approval; no money shown anywhere."),
)
