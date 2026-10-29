"""Contractor training: 12 modules for the contractor owner and authorized office staff (Joel, 21 Oct 2026).

Ben's First Day (app/services/onboarding.py, Company → Getting started) is the backbone of the owner's
pathway: its sixteen steps are taught across the modules in the order the owner meets them. Office staff get
the office workflows; People & Access, crews, Getting started and closing/reopening a project are the owner's.
The owner also keeps the Field lessons, to know what the crew see. The crew themselves (role Field worker)
follow their own Field Crew pathway, app/training/field_crew.py (22 Oct 2026).

Every label below was checked against the real pages and pictured by tools/training/capture_contractor_shots.mjs
(the screenshots in app/static/training/shots, c<module>-<name>.png). The practice exercises follow ONE
connected job on the training site: Harbour Lane Pool Deck (training) for Morgan Ellis (training) at
14 Harbour Lane, Merrickville, with concrete from BMR Winchester (training): intake, estimate, supplier quote
and order, scheduling, Field, change order, invoice and closeout. Connected example: see app/training/content.py.
"""

from app.models.training import PATHWAY_CONTRACTOR as P
from app.models.training import ROLE_OFFICE, ROLE_OWNER
from app.training.content import (
    APP_CUSTOMER,
    APP_EMAIL,
    APP_FIELD,
    APP_OFFICE,
    APP_PHONE_CALENDAR,
    APP_QUICKBOOKS,
    APP_SUPPLIER,
    OFFICE_ROLES,
    Lesson,
    Module,
    Step,
    UatCase,
)

OWNER = (ROLE_OWNER,)
# Contractor owners and authorized office staff (Joel, 22 Oct 2026). The crew have their own Field Crew pathway
# (field_crew.py); the Field lessons kept here are the owner's view of what the crew see on their phones.
TEAM = OFFICE_ROLES
OWNER_FIELD = OWNER  # Field lessons kept for the owner, who should know what the crew see
OFFICE = OFFICE_ROLES
O = APP_OFFICE
F = APP_FIELD
INITIALS = (" On the training site everyone shares one training company: add your initials to anything you name "
            "(for example 'Site visit: Harbour Lane Pool Deck (training) BB') so you and the trainer can find it.")
JOB = "Harbour Lane Pool Deck (training)"
HUB = "Projects → Harbour Lane Pool Deck (training)"

# ====================================================================================== 1
M01 = Module(
    key="c01", pathway=P, number=1, title="Welcome, registration and first sign-in",
    summary="Register in the Training Centre, sign in to CalibraytAI (the office on a computer, Field on the phone), "
            "find your way around and look after your password.",
    roles=TEAM,
    lessons=(
        Lesson(
            key="c01-welcome", title="Welcome: register and use the Training Centre",
            what="Sign in to the Training Centre, choose the job you do, and learn how lessons, the Tutor and the "
                 "acceptance tests work.",
            why="Your lessons follow your job: the owner, the office and the crew each learn what they use. Your "
                "place is saved, so you can stop and carry on later on your computer or your iPhone.",
            steps=(
                Step(title="Open the Training Centre", app=O, where="The training site address from your invitation, then /training",
                     do="Press I work for a contractor",
                     expect="The page says Welcome to CalibraytAI training, with three buttons: I work for a contractor, "
                            "I work on a crew (Field) and I work for a building supplier.",
                     if_wrong="If the page is not found, check the address with the person who invited you: the Training "
                              "Centre is only on the training site, never on the real office.",
                     shot="c01-training-signin.png", endpoint="training.signin"),
                Step(title="Sign in", app=O, where="The Sign in page",
                     do="Type your email and password, then press Sign in",
                     enter="Your training email (for example ben@training.calibraytai.invalid) and the password from your invitation",
                     expect="The Training Centre opens with Welcome and your name.",
                     if_wrong="Check the email is typed exactly. If the password is refused, press Forgot Password? "
                              "(lesson 'Forgot your password').",
                     shot="c01-sign-in.png", endpoint="auth.login"),
                Step(title="Choose the job you do", app=O, where="Training Centre → Welcome, <your name>",
                     do="Tick your job (Contractor owner or Office staff), then press Start my training",
                     expect="Your modules appear, numbered, each with the lessons for your job and a count such as 0/3.",
                     if_wrong="Picked the wrong job? Press Change role (keeps my progress) at the bottom of the Training "
                              "Centre. Field worker opens the separate Field Crew training; Field-only crew are only "
                              "offered that.",
                     why="Office staff do not get the owner's set-up lessons; the crew have their own Field Crew "
                         "training with no office or money lessons.",
                     shot="c01-register.png", endpoint="training.home"),
                Step(title="Find your lessons and tests", app=O, where="Training Centre home",
                     do="Press the first lesson's name",
                     expect="The lesson opens with all its steps listed in order, an 'I did this step' button under each, "
                            "Save and exit, and the Ask the Tutor button in the header. The home page also has Acceptance tests.",
                     if_wrong="If a lesson is missing, check your role at the bottom of the page.",
                     shot="c01-training-home.png", endpoint="training.home"),
                Step(title="Save and come back later", app=O, where="Any lesson",
                     do="Press Save and exit, then on the Training Centre home press Continue where I left off",
                     expect="You are back in the same lesson at the first step you have not ticked; ticked steps stay green.",
                     if_wrong="Every tick is saved at once, so nothing is lost if you close the page; open the lesson again "
                              "from your training home.",
                     why="Lessons are short; do them between jobs.", endpoint="training.lesson"),
                Step(title="Ask the Tutor", app=O, where="Any lesson → Ask the Tutor (in the header)",
                     do="Tap Ask the Tutor in the header, type a question such as 'Where is the button?' and press Ask; tap Minimize to close it",
                     expect="The Tutor answers from this step (where to go, what to press) without moving your place.",
                     if_wrong="If you cannot see the Tutor, tap Ask the Tutor in the header to open it.",
                     endpoint="training.lesson"),
            ),
            exercise="Register on the training site with your own job, open your first lesson, tick Step 1 (it turns "
                     "green), press Save and exit, then come back with Continue where I left off. Tick each remaining "
                     "step, tick I did the practice exercise and finish the lesson.",
        ),
        Lesson(
            key="c01-sign-in", title="Sign in to the office and change your password",
            what="Sign in to CalibraytAI on your computer, open Home and change the password from your invitation to "
                 "one only you know.",
            why="Your own sign-in keeps your work under your name, and only you know your password.",
            roles=OFFICE,
            steps=(
                Step(title="Open the sign-in page", app=O, where="The training site address Joel sent you",
                     do="Type your email and password, then press Sign in",
                     enter="Your email and the password from your invitation",
                     expect="Home opens: Good morning (or afternoon), <your name>, with TODAY, WHAT NEEDS ATTENTION and "
                            "COMING DAYS.",
                     if_wrong="Check the email is typed exactly. Press Forgot Password? to get a new link by email. There "
                              "is no Create account button: only the owner adds people.",
                     shot="c01-sign-in.png", endpoint="auth.login"),
                Step(title="Find the key button", app=O, where="The top right of every office page",
                     do="Press the key button (Change password), beside your name",
                     expect="The Change password page opens.",
                     if_wrong="On a narrow window the header buttons may be squeezed; widen the window.",
                     shot="c01-key-button.png", endpoint="main.dashboard"),
                Step(title="Change your password", app=O, where="Change password",
                     do="Type the current password once and the new password twice, then press Change password",
                     enter="Current password; New password (at least 8 characters); New password again",
                     expect="You are signed out and the sign-in page says: Your password is changed. Sign in with your "
                            "email and the new password.",
                     if_wrong="'The current password is not correct': type the invitation password again. 'do not match': "
                              "type the new one carefully twice.",
                     shot="c01-change-password.png", endpoint="auth.change_password"),
                Step(title="Sign in with the new password", app=O, where="Sign in",
                     do="Type your email and the new password, then press Sign in",
                     expect="Home opens again under your name.",
                     if_wrong="Use Forgot Password? if the new password is refused.",
                     shot="c01-sign-in.png", endpoint="main.dashboard"),
                Step(title="Sign out when you leave", app=O, where="The top right, the last button (Sign out)",
                     do="Press Sign out",
                     expect="The sign-in page opens.",
                     if_wrong="If a page still shows your work, press the browser's back button: it asks you to sign in.",
                     why="On a shared computer, always sign out."),
            ),
            exercise="On the training site, sign in as yourself, change your password with the key button, sign in "
                     "again with the new password, then sign out.",
        ),
        Lesson(
            key="c01-find-your-way", title="Find your way around the office",
            what="Learn the menu on the left, Home, the Help panel on each page and where everything for one job lives.",
            why="Everything for a job is on its project page; the menu takes you to the company-wide lists.",
            roles=OFFICE,
            steps=(
                Step(title="Read Home", app=O, where="Home (the first item in the menu)",
                     do="Read TODAY, WHAT NEEDS ATTENTION and COMING DAYS",
                     expect="Each box says what is scheduled or 'Nothing is scheduled'. Below: Current projects, Estimates "
                            "outstanding, Proposals outstanding, Open change orders.",
                     if_wrong="If the menu is hidden on a small screen, press the three-line button at the top left.",
                     shot="c01-home.png", endpoint="main.dashboard"),
                Step(title="Learn the menu", app=O, where="The menu on the left",
                     do="Look at each group: Home, Calendar, Projects, Clients; CALCULATORS; COSTS & PRICING (What we pay, "
                        "Reusable work, How we price); PROPOSALS (Templates); COMPANY LIBRARY (Past jobs); COMPANY",
                     expect="Office staff see COMPANY → Getting started, Crews, Suppliers, Accounting, Work catalog. The "
                            "owner also sees People & Access.",
                     if_wrong="CALCULATORS is folded; press it to open the list.",
                     shot="c01-office-home.png", endpoint="main.dashboard"),
                Step(title="Open Help on a page", app=O, where="Any office page → the Help bar at the top",
                     do="Press Show on Help, read What, Do and Next; you can type a question or press Ask by speaking",
                     expect="Help explains this page. It never changes the job.",
                     if_wrong="Help needs a connection. If offline, it says so.", endpoint="main.dashboard"),
                Step(title="Open a project", app=O, where="Home → Current projects (or Projects in the menu)",
                     do=f"Press {JOB}",
                     expect="The project page (the hub) opens with tabs PROJECT, SETTINGS, MONEY, DOCUMENTS and PROJECT WORK.",
                     if_wrong="If the job is missing, look under Closed on the Projects page.",
                     shot="c06-project-tabs.png", endpoint="projects.view_project"),
            ),
            exercise=f"Sign in, open each group of the menu once, open Help on Home, then open {JOB} from Home → "
                     "Current projects and press each tab (PROJECT … PROJECT WORK).",
        ),
        Lesson(
            key="c01-forgot-password", title="Forgot your password",
            what="Get a new password by email from the sign-in page.",
            why="Nobody else can see or set your password, so if you forget it you choose a new one yourself.",
            steps=(
                Step(title="Ask for reset instructions", app=O, where="Sign in → Forgot Password?",
                     do="Type your email address and press Send Reset Instructions",
                     enter="Your training email",
                     expect="Check your email: if an account exists for that email address, password reset instructions "
                            "have been sent.",
                     if_wrong="The page looks the same for any address, so check the spelling. On the training site the "
                              "email goes to the trainer's mail folder; ask the trainer for the link.",
                     shot="c01-forgot-password.png", endpoint="auth.forgot_password"),
                Step(title="Open the link", app=APP_EMAIL, where="Your email → the message from CalibraytAI",
                     do="Press the link in the email (on the iPhone it opens in Safari)",
                     expect="Set New Password opens.",
                     if_wrong="A link works once. If it says it is no longer valid, ask for a new one.",
                     endpoint="auth.reset_password"),
                Step(title="Choose the new password", app=O, where="Set New Password",
                     do="Type it in New Password and Confirm New Password, then press Reset Password",
                     expect="Password Updated, with Return to Sign In.",
                     if_wrong="Show password lets you check what you typed.",
                     shot="c03-set-password.png", endpoint="auth.reset_password"),
            ),
            exercise="Sign out, press Forgot Password? and ask for reset instructions for your training email. Ask the "
                     "trainer for the link, choose a new password and sign in with it.",
        ),
    ),
)

# ====================================================================================== 2
M02 = Module(
    key="c02", pathway=P, number=2, title="Company setup, users and permissions",
    summary="Ben's First Day steps 1 to 5: Getting started, the company's brand, the pricing and 13 % HST, the people "
            "who sign in, what each may do, and the crews.",
    roles=OWNER,
    lessons=(
        Lesson(
            key="c02-getting-started", title="Getting started: Ben's First Day checklist",
            what="Open Company → Getting started and learn the sixteen set-up steps you will follow through this course.",
            why="Getting started ticks each step by itself when the records show it is done, so you always know what "
                "is left. This course follows the same sixteen steps.",
            steps=(
                Step(title="Open Getting started", app=O, where="Company → Getting started",
                     do="Press Getting started in the menu",
                     expect="Set up CalibraytAI, step by step: a bar with how many of 16 are done, the next step to do, "
                            "and 16 numbered steps.",
                     if_wrong="If COMPANY is not in the menu, scroll the menu down.",
                     shot="c02-getting-started.png", endpoint="getting_started.index"),
                Step(title="Read a step", app=O, where="Getting started → any step",
                     do="Read its why and how; press Go there to open the page that does it",
                     expect="Done steps show a tick. Steps the platform cannot see (6 Set up their iPhones, 16 Run a "
                            "complete working day) have Mark done.",
                     if_wrong="A step ticks itself only from the records (a client and project exist, a proposal was "
                              "made). Do the work, then come back.",
                     shot="c02-getting-started-steps.png", endpoint="getting_started.index"),
                Step(title="Use Next", app=O, where="Getting started → the top",
                     do="Press the Next: link",
                     expect="The page for the next unfinished step opens (for example the brand profile).",
                     if_wrong="When all are done the page says All done.", shot="c02-getting-started.png", endpoint="getting_started.index"),
            ),
            exercise="Open Company → Getting started on the training site, count how many of the 16 steps are already "
                     "ticked, and write down the next step it suggests.",
        ),
        Lesson(
            key="c02-company-brand", title="Set up your company (brand profile)",
            what="Enter the company's names, phone, email, address, colours and logo.",
            why="Getting started step 2: your logo, colours and contact details go on every proposal the customer sees.",
            steps=(
                Step(title="Open the brand profile", app=O, where="The company name button at the top right",
                     do="Press your company's name (Brayman Construction (training))",
                     expect="Brand profile opens with Legal name, Customer-facing name, Phone, Email, Website, Primary color, "
                            "Accent color, Address and Logo.",
                     if_wrong="It is also Getting started → 2 Set up your company → Go there.",
                     shot="c02-brand-profile.png", endpoint="settings.brand_profile"),
                Step(title="Fill in the details", app=O, where="Brand profile",
                     do="Type each field; choose a logo file for Logo",
                     enter="Legal name and Customer-facing name: Brayman Construction (training); Phone 613-555-0100; "
                           "Primary color #1F4E8C; Accent color #C79A2B",
                     expect="The fields hold what you typed.",
                     if_wrong="Colours are typed as # and six characters.", endpoint="settings.brand_profile"),
                Step(title="Save", app=O, where="Brand profile → the bottom",
                     do="Press Save Brand Profile",
                     expect="A green message says Brand Profile saved; Getting started step 2 is ticked.",
                     if_wrong="Fields marked * are required: Legal name and Customer-facing name.",
                     shot="c02-brand-saved.png", endpoint="settings.brand_profile"),
            ),
            exercise="On the training site, open the brand profile, check the training company's phone and address, add "
                     "'(your initials)' to the Website box, press Save Brand Profile and confirm the green message.",
        ),
        Lesson(
            key="c02-pricing-hst", title="Financial and HST settings (How we price)",
            what="Make the company's pricing policy: gross margin or markup, and 13 % Ontario HST; approve it and use it "
                 "for the company.",
            why="Getting started step 3: every estimate is priced with this policy and every proposal and invoice "
                "carries this HST.",
            steps=(
                Step(title="Open How we price", app=O, where="COSTS & PRICING → How we price",
                     do="Read the policies; the one marked Company default is in use",
                     expect="A list such as 'Gross Margin Pricing 15% of the customer price is margin. Tax 13.00%. "
                            "Approved · Company default'.",
                     if_wrong="If there is no Company default, estimates cannot be priced: make one now.",
                     shot="c02-how-we-price.png", endpoint="pricing_engine.index"),
                Step(title="Start a new draft", app=O, where="How we price",
                     do="Press New pricing draft and fill in the form",
                     enter="Policy code HARBOUR-GM-20 (add your initials); Method Gross Margin Pricing; Target gross margin "
                           "0.20; Overhead and Profit treatment Included in margin economics; Contingency visibility Not "
                           "applied; Tax jurisdiction CA-ON; Tax % 13",
                     expect="The Create draft policy form holds your values.",
                     if_wrong="Margins are decimals: 0.20 means 20 %. Gross margin is a share of the customer price; "
                              "markup (Cost plus markup) is added to the cost.",
                     why="20 % gross margin: cost $12,452.50 becomes a price of $15,565.63 before HST.",
                     shot="c02-pricing-draft.png", endpoint="pricing_engine.create_policy"),
                Step(title="Create the draft", app=O, where="Create draft policy → the bottom",
                     do="Press Create draft",
                     expect="Draft pricing policy created, with the buttons Approve (human) and Withdraw.",
                     if_wrong="A code already in use is refused; add your initials.",
                     shot="c02-pricing-approve.png", endpoint="pricing_engine.policy_detail"),
                Step(title="Approve it", app=O, where="The new policy",
                     do="Press Approve (human)",
                     expect="The policy is Approved and the button Use for this company appears.",
                     if_wrong="Only a person approves a pricing policy; nothing is approved by itself.",
                     shot="c02-pricing-use.png", endpoint="pricing_engine.policy_detail"),
                Step(title="Use it for the company", app=O, where="The approved policy",
                     do="Press Use for this company",
                     expect="It says Company default and '20% of the customer price is margin', tax 13.00.",
                     if_wrong="Estimates priced earlier keep their old price; re-apply pricing on an estimate to use the "
                              "new policy.",
                     shot="c02-pricing-default.png", endpoint="pricing_engine.policy_detail"),
            ),
            exercise="Make the pricing policy HARBOUR-GM-20-<initials>: Gross Margin Pricing 0.20, CA-ON, 13 % HST. "
                     "Approve it and press Use for this company. The Harbour Lane estimate in module 9 is priced with it.",
        ),
        Lesson(
            key="c02-people", title="Invite your people (People & Access)",
            what="Add each person who will sign in; tick Field only for the crew.",
            why="Getting started step 5: everyone has their own sign-in. Field-only crew see Field and their own "
                "account, never office pages, costs or prices.",
            steps=(
                Step(title="Open People & Access", app=O, where="Company → People & Access",
                     do="Read the list",
                     expect="Each person with their email, Can sign in, and their role (Owner, Office).",
                     if_wrong="Only the owner (or a System Administrator) sees People & Access. Note: the list shows "
                              "crew as 'Office' even when they are Field only; open the person to check Field only.",
                     shot="c02-people-list.png", endpoint="people_access.index"),
                Step(title="Add a person", app=O, where="People & Access",
                     do="Press Add a person, type the name and email, tick Field only for crew",
                     enter="Name: Tyler Field (training crew) <initials>; Email: tyler.<initials>@training.calibraytai.invalid; "
                           "tick Field only",
                     expect="The form: Name, Email, and 'Field only: crew see Field pages and their own account, never "
                            "office pages, costs or prices'.",
                     if_wrong="Use an address the person reads; the link to choose a password goes there.",
                     shot="c02-people-add.png", endpoint="people_access.new"),
                Step(title="Send the invitation", app=O, where="Add a person → the bottom",
                     do="Press Add and email the link",
                     expect="A message says the person was added and a link to choose a password was emailed. Their page "
                            "shows Sign-in, Crews, Access, System Administrator and History.",
                     if_wrong="If the email is already used, open that person instead.",
                     shot="c02-people-added.png", endpoint="people_access.detail"),
            ),
            exercise="Add 'Tyler Field (training crew) <initials>' as Field only with a made-up training email, and "
                     "check that Getting started step 5 Invite the boys is ticked.",
        ),
        Lesson(
            key="c02-access", title="What each person may do (permissions)",
            what="Change a person to or from Field only, give access areas, appoint a System Administrator, and "
                 "deactivate a sign-in.",
            why="The owner decides who sees the office, money and company management; every change is kept in History.",
            steps=(
                Step(title="Open a person", app=O, where="Company → People & Access → Olivia Office (training)",
                     do="Press the person's name",
                     expect="Sign-in (Deactivate sign-in, Email a link to choose a password, Make Field only), Crews, "
                            "Access, System Administrator, History.",
                     if_wrong="Your own record has fewer buttons: you cannot deactivate yourself.",
                     shot="c02-people-detail.png", endpoint="people_access.detail"),
                Step(title="Give an access area", app=O, where="The person → Access",
                     do="Choose the area and press Give (Remove takes it away)",
                     expect="The area is listed under Access and in History.",
                     if_wrong="Field-only people cannot be given office areas; remove Field only first.",
                     shot="c02-people-access.png", endpoint="people_access.detail"),
                Step(title="Field only on or off", app=O, where="The person → Sign-in",
                     do="Press Make Field only (or Remove Field only)",
                     expect="The page says Field only: Field pages and their own account; no office pages, costs or prices.",
                     if_wrong="The person sees the change at their next page.",
                     shot="c02-people-added.png"),
                Step(title="When someone leaves", app=O, where="The person → Sign-in",
                     do="Press Deactivate sign-in",
                     expect="They cannot sign in; their work stays in the records; their calendar feed stops. Reactivate "
                            "sign-in brings them back.",
                     if_wrong="Do not delete their work or share their password; deactivating is enough.",
                     shot="c02-people-detail.png"),
            ),
            exercise="Open Olivia Office (training): read Access and History without changing anything. Then open your "
                     "Tyler record and check it says Field only.",
        ),
        Lesson(
            key="c02-crews", title="Crews",
            what="Make a crew and put people on it with dates.",
            why="You schedule a crew on a job and everyone on it sees the work on Field.",
            steps=(
                Step(title="Open Crews", app=O, where="Company → Crews",
                     do="Press Add crew",
                     expect="Add crew with Crew name.",
                     if_wrong="Crews is under COMPANY in the menu.",
                     shot="c02-crews.png", endpoint="organization_crew.index"),
                Step(title="Name the crew", app=O, where="Add crew",
                     do="Type the name and press Add crew",
                     enter="Pool deck crew (training) <initials>",
                     expect="Crew saved; the crew is in the list.",
                     if_wrong="Names must be unique; add your initials.",
                     shot="c02-crew-add.png", endpoint="organization_crew.new"),
                Step(title="Add people with dates", app=O, where="Crews → your crew → People on this crew",
                     do="Choose the Person, set From (and Last day if known), press Add dates on this crew",
                     enter="Kevin Field (training crew), From: yesterday; then Liam Field (training crew)",
                     expect="Both are listed on the crew with their dates.",
                     if_wrong="A person is on a crew only between From and Last day; check the dates cover the job.",
                     shot="c02-crew-member.png", endpoint="organization_crew.detail"),
            ),
            exercise="Make 'Pool deck crew (training) <initials>' with Kevin Field and Liam Field from yesterday. You "
                     "will schedule this crew on Harbour Lane in module 11.",
        ),
    ),
)

# ====================================================================================== 3
M03 = Module(
    key="c03", pathway=P, number=3, title="Connecting workers and setting up iPhones",
    summary="Ben's First Day step 6: each worker opens the invitation on their iPhone, chooses a password, puts Field "
            "on the Home Screen and sees My Work.",
    roles=OWNER_FIELD,
    lessons=(
        Lesson(
            key="c03-invite-worker", title="Send the link and check the phone is set up",
            what="Send (or resend) the set-password link, see that the worker has activated, and mark the phones step done.",
            why="The platform cannot see a phone, so the owner marks Set up their iPhones done once each worker is in.",
            roles=OWNER,
            steps=(
                Step(title="Send the link again if needed", app=O, where="Company → People & Access → the worker",
                     do="Press Email a link to choose a password",
                     expect="A message says the link was emailed. Each new link replaces the old one.",
                     if_wrong="Check the email address on the page; a wrong address never arrives.",
                     shot="c03-send-link.png", endpoint="people_access.detail"),
                Step(title="See that they are in", app=O, where="People & Access → the worker",
                     do="Open the worker after they have chosen a password",
                     expect="Sign-in says Can sign in; Field only is shown.",
                     if_wrong="If they never chose a password, send the link again and sit with them.",
                     shot="c03-activated.png", endpoint="people_access.detail"),
                Step(title="Mark the phones step done", app=O, where="Company → Getting started → 6 Set up their iPhones",
                     do="Press Mark done",
                     expect="Step 6 shows a tick with your name.",
                     if_wrong="Pressed it too early? Press Undo beside the step.",
                     shot="c03-mark-phones.png", endpoint="getting_started.index"),
            ),
            exercise="Open your Tyler record, press Email a link to choose a password, and (once a field trainee or the "
                     "trainer has set the password) mark Getting started → 6 Set up their iPhones done.",
        ),
        Lesson(
            key="c03-activate-phone", title="Activate your account on your iPhone",
            what="Open the invitation email on the iPhone, choose your password and sign in to Field.",
            why="Your own password; nobody else sees or sets it.",
            steps=(
                Step(title="Open the invitation", app=APP_EMAIL, where="Mail on your iPhone → the CalibraytAI invitation "
                     "('… invited you to CalibraytAI')",
                     do="Press the link (it opens in Safari)",
                     expect="Set New Password opens.",
                     if_wrong="No email? Look in junk mail, then ask the owner to press Email a link to choose a password. "
                              "Use the newest email: an older link no longer works.",
                     endpoint="auth.reset_password"),
                Step(title="Choose your password", app=F, where="Set New Password",
                     do="Type it in New Password and Confirm New Password, press Reset Password",
                     expect="Password Updated, with Return to Sign In.",
                     if_wrong="Press Show password to check what you typed.",
                     shot="c03-set-password.png", endpoint="auth.reset_password"),
                Step(title="Sign in", app=F, where="Password Updated → Return to Sign In",
                     do="Type your email and the new password, press Sign in",
                     expect="Field Today opens: My Work — <your name>.",
                     if_wrong="Check the email; use Forgot Password? if needed.",
                     shot="c03-password-set.png", endpoint="auth.login"),
            ),
            exercise="Field trainees: if you were invited by email, set your password from the link on your iPhone and "
                     "sign in. Owners: watch a field trainee do it, or use your Tyler record's link with the trainer.",
        ),
        Lesson(
            key="c03-home-screen", title="Put Field on the iPhone Home Screen",
            what="Add CalibraytAI to the Home Screen so it opens like an app.",
            why="One tap opens today's work; you do not type the address again.",
            steps=(
                Step(title="Open the site in Safari", app=F, where="Safari (not Chrome) on the iPhone → the training site address",
                     do="Sign in if asked",
                     expect="Field Today.",
                     if_wrong="Add to Home Screen is in Safari's Share menu; other browsers may not offer it.",
                     shot="c03-field-today.png", endpoint="field.today"),
                Step(title="Add to Home Screen", app=F, where="Safari → the Share button (square with an arrow) → Add to Home Screen",
                     do="Check the name says Calibrayt (training), then press Add",
                     expect="The Calibrayt icon is on the Home Screen.",
                     if_wrong="If Add to Home Screen is not in the list, scroll the Share list down or press Edit Actions."),
                Step(title="Open it from the icon", app=F, where="The iPhone Home Screen → the Calibrayt icon",
                     do="Tap the icon",
                     expect="Today opens. Sign in only if asked, while the phone has a connection.",
                     if_wrong="Do not delete the icon. If it asks you to sign in every time, check Safari is not in "
                              "Private mode."),
                Step(title="No signal on site", app=F, where="Field → Capture or Time",
                     do="Save your note or photo as normal",
                     expect="'Saved on this phone — will sync when connected' and 'Pending on this phone'. It sends by "
                            "itself when the connection is back, while the app is open.",
                     if_wrong="Do not sign out while anything is pending: open the app where there is signal and wait for "
                              "'Saved'."),
            ),
            exercise="Put the training site on your iPhone Home Screen from Safari, close Safari, and open Field from the "
                     "new icon.",
        ),
        Lesson(
            key="c03-field-first-look", title="A first look at Field",
            what="Learn the four Field views and what Field never shows.",
            why="Field shows the work, the job and the drawings, never money.",
            steps=(
                Step(title="Today", app=F, where="Field → Today",
                     do="Read My Work",
                     expect="What you are booked on today, or 'Nothing is scheduled for you today.'",
                     if_wrong="Work shows only after the office schedules your crew (module 11).",
                     shot="c03-field-today.png", endpoint="field.today"),
                Step(title="This week", app=F, where="Field → This week",
                     do="Read each day",
                     expect="Seven days, today marked Today.",
                     if_wrong="Use This month for later weeks.",
                     shot="c03-field-week.png", endpoint="field.week"),
                Step(title="Office pages stay closed", app=F, where="Field",
                     do="Notice there is no office menu",
                     expect="Projects, estimates, People & Access and Accounting are not available to Field-only crew; "
                            "an office address takes you back to Today.",
                     if_wrong="If you can open an office page, tell the owner: you should be Field only.",
                     shot="c03-field-today.png"),
            ),
            exercise="On your iPhone, open Today, This week, This month and Company today on the training site.",
        ),
    ),
)

# ====================================================================================== 4
M04 = Module(
    key="c04", pathway=P, number=4, title="QuickBooks and financial workflows",
    summary="Ben's First Day step 4: invoices from the accepted proposal and approved change orders, files for "
            "QuickBooks Online, bills from purchase orders, and the weekly check.",
    roles=OFFICE,
    lessons=(
        Lesson(
            key="c04-accounting-page", title="The Accounting page",
            what="Learn what CalibraytAI keeps, what QuickBooks keeps, and the Accounting page.",
            why="CalibraytAI keeps jobs, proposals, change orders and orders; QuickBooks Online keeps the books. They "
                "meet through files. CalibraytAI never asks for your QuickBooks password.",
            steps=(
                Step(title="Open Accounting", app=O, where="Company → Accounting",
                     do="Read the page",
                     expect="QuickBooks Online (Not connected. Use the export files below), Files for QuickBooks, Invoices, "
                            "Last check against QuickBooks, History; Check QuickBooks at the top right.",
                     if_wrong="Crew on Field never see Accounting.",
                     shot="c04-accounting.png", endpoint="accounting.index"),
                Step(title="Read Files for QuickBooks", app=O, where="Accounting → Files for QuickBooks",
                     do="Read each row: Customers, Suppliers (vendors), Invoices, Bills from purchase orders, Purchase orders "
                        "(list to enter by hand)",
                     expect="NEW (not yet in a file), ALREADY IN A FILE, and where to import it in QuickBooks.",
                     if_wrong="A record goes into a file once; the next file leaves it out.",
                     shot="c04-files.png", endpoint="accounting.index"),
            ),
            exercise="Open Company → Accounting on the training site and write down how many NEW customers and invoices "
                     "it shows.",
        ),
        Lesson(
            key="c04-quickbooks-setup", title="Once: customers and suppliers into QuickBooks",
            what="Download the Customers and Suppliers files and import them in QuickBooks Online; check HST ON and the "
                 "Construction services item.",
            why="Invoices import only when their customer already exists in QuickBooks.",
            steps=(
                Step(title="Download Customers", app=O, where="Accounting → Customers",
                     do="Press Download the file",
                     expect="A .csv file named like calibraytai-customers-<date>.csv downloads, with Morgan Ellis (training).",
                     if_wrong="'Nothing new' means every customer is already in a file; choose Include those again only "
                              "if an import failed, and say why.",
                     shot="c04-export-customers.png", endpoint="accounting.export"),
                Step(title="Import Customers in QuickBooks", app=APP_QUICKBOOKS,
                     where="QuickBooks Online → gear icon (Settings) → Import data → Customers",
                     do="Choose the file, check the columns match (they have the same names), press Import",
                     expect="Morgan Ellis (training) is in QuickBooks' customer list.",
                     if_wrong="Needs a QuickBooks Online account with admin rights. Practise on a QuickBooks sample or "
                              "sandbox company, never your real books, with training data."),
                Step(title="Suppliers the same way", app=O, where="Accounting → Suppliers (vendors)",
                     do="Press Download the file; in QuickBooks: Import data → Suppliers",
                     expect="BMR Winchester (training) is a supplier in QuickBooks.",
                     if_wrong="As for customers.", shot="c04-export-suppliers.png", endpoint="accounting.export"),
                Step(title="Check tax and the item", app=APP_QUICKBOOKS, where="QuickBooks → Taxes → Sales tax settings; Products and services",
                     do="Check the tax code HST ON (13 %) exists; make one Service called Construction services",
                     expect="Both exist. Every invoice line uses Construction services.",
                     if_wrong="HST ON is there by default for an Ontario company; if not, set up sales tax first."),
            ),
            exercise="Download the Customers file from the training site and open it: check Morgan Ellis (training) is in "
                     "it. If you have a QuickBooks sandbox, import it there (never into your real books).",
        ),
        Lesson(
            key="c04-invoices", title="Make invoices (deposit, progress, final, change order)",
            what="Make a deposit invoice from the accepted proposal and an invoice for an approved change order.",
            why="Invoices are made only from what the customer agreed: the accepted proposal and approved change orders.",
            steps=(
                Step(title="Open Make an invoice", app=O, where=f"{HUB} → MONEY → Related Change Orders",
                     do="Press Make an invoice",
                     expect="Make an invoice: From the accepted proposal, From an approved change order, Invoices on this "
                            "project.",
                     if_wrong="Without an accepted proposal there is nothing to invoice (module 10).",
                     shot="c04-hub-invoice.png", endpoint="projects.view_project"),
                Step(title="A deposit", app=O, where="Make an invoice → From the accepted proposal",
                     do="Kind: Deposit; Percent of the proposal before HST: 30; press Make the invoice",
                     enter="30",
                     expect="'Invoice INV-2026-… made: $5,276.75 with HST' (30 % of $15,565.63 plus 13 %).",
                     if_wrong="Give a percent or an amount, not both. You cannot invoice more than the proposal.",
                     shot="c04-make-invoice.png", endpoint="accounting.new_invoice"),
                Step(title="A change order", app=O, where="Make an invoice → From an approved change order",
                     do="Choose the change order and press Invoice the change order",
                     expect="'CO-… Extra steps to the lawn (training) · $850.00 before HST' becomes an invoice of $960.50 "
                            "with HST. A change order is invoiced once.",
                     if_wrong="Only Approved change orders are listed (module 11).",
                     shot="c04-invoice-change-order.png", endpoint="accounting.new_invoice"),
                Step(title="See the invoice", app=O, where="The invoice page",
                     do="Read it; Record a correction or Void this invoice are here if needed",
                     expect="The invoice number, amounts with HST, and History.",
                     if_wrong="Never make a second invoice to fix the first: void or correct it.",
                     shot="c04-invoice-made.png", endpoint="accounting.invoice"),
            ),
            exercise=f"After Morgan accepts in module 10: on {JOB} make a 30 % Deposit invoice and check it says $5,276.75 "
                     "with HST (if you used the 20 % policy). After module 11, invoice the approved change order.",
        ),
        Lesson(
            key="c04-invoice-export", title="Send invoices to QuickBooks",
            what="Download the Invoices file and import it in QuickBooks with the right settings.",
            why="Only invoices not already sent are in the file, so nothing is entered twice.",
            steps=(
                Step(title="Download Invoices", app=O, where="Accounting → Invoices",
                     do="Press Download the file",
                     expect="A .csv with InvoiceNo, Customer, InvoiceDate, DueDate … ItemTaxCode. Opening it again later "
                            "says Nothing new.",
                     if_wrong="Up to 100 invoices go in one file; download again for the rest.",
                     shot="c04-export-invoices.png", endpoint="accounting.export"),
                Step(title="Import in QuickBooks", app=APP_QUICKBOOKS, where="QuickBooks Online → gear icon → Import data → Invoices",
                     do="Choose the file. Date format dd/MM/yyyy; Amounts are Exclusive of tax; map InvoiceNo → Invoice "
                        "number and the Item columns",
                     expect="The invoices appear in QuickBooks with HST ON.",
                     if_wrong="If an import failed, in CalibraytAI choose Include those again and say why."),
                Step(title="Nothing new next time", app=O, where="Accounting → Invoices",
                     do="Open it again",
                     expect="Nothing new: every invoice has been in a file.",
                     if_wrong="That is correct; it prevents duplicates.",
                     shot="c04-nothing-new.png", endpoint="accounting.export"),
            ),
            exercise="Download the Invoices file with your Harbour Lane deposit invoice and check its InvoiceNo matches "
                     "the invoice page.",
        ),
        Lesson(
            key="c04-bills-and-check", title="Bills from purchase orders and Check QuickBooks",
            what="Use the draft bills from confirmed or delivered orders, and check every week that QuickBooks matches.",
            why="Supplier bills are checked against the supplier's own invoice; the weekly check finds anything missing "
                "or entered twice.",
            steps=(
                Step(title="Bills from purchase orders", app=O, where="Accounting → Bills from purchase orders",
                     do="Press Download the file; check each bill against BMR's own invoice before importing (QuickBooks: "
                        "Import data → Bills)",
                     expect="A draft bill for each confirmed or delivered order: the order amount before tax plus 13 % HST.",
                     if_wrong="Cancelled orders never appear. Purchase orders are a list to enter by hand: QuickBooks has "
                              "no purchase-order import.",
                     shot="c04-export-bills.png", endpoint="accounting.export"),
                Step(title="Export the Invoice List", app=APP_QUICKBOOKS, where="QuickBooks → Reports → Invoice List",
                     do="Set the dates, then Export → Export to CSV",
                     expect="A .csv of QuickBooks' invoices.",
                     if_wrong="Needs QuickBooks Online report access."),
                Step(title="Check QuickBooks", app=O, where="Accounting → Check QuickBooks",
                     do="Choose that file, press Check",
                     expect="Each invoice: match, amount differs, exported but not in QuickBooks, in QuickBooks but not in "
                            "CalibraytAI, or in QuickBooks more than once.",
                     if_wrong="Amount differs: fix it in QuickBooks, then Record a correction on the invoice here.",
                     shot="c04-check-quickbooks.png", endpoint="accounting.reconcile"),
            ),
            exercise="After the BMR concrete order is confirmed (module 8), download Bills from purchase orders and check "
                     "the BMR bill is $612.50 plus HST. Open Check QuickBooks and read what each result means.",
        ),
        Lesson(
            key="c04-hours-policy", title="Hours and banked time (Getting started step 15)",
            what="Enter your company's own hours policy: the normal work week, when extra hours start, whether they are "
                 "banked or paid as overtime, the bank rate, whether Shop / Company Work counts, and the week's first day.",
            why="Nothing is preset: CalibraytAI banks hours only under the rules you enter, and shows them to the crew "
                "on Field. Agree the numbers with your payroll person first (docs: Payroll with CalibraytAI).",
            roles=OWNER,
            steps=(
                Step(title="Open the hours policy", app=O, where="Company → Getting started → 15 Hours and banked time → "
                                                                 "Go there (or Accounting → Hours policy)",
                     do="Press Go there",
                     expect="Hours policy: 'No hours policy has been entered yet, so no hours are banked.' and an empty form.",
                     if_wrong="Only the owner or a System Administrator can open it.",
                     shot="c04-hours-policy-empty.png", endpoint="payroll_time.hours_policy"),
                Step(title="Fill in every value", app=O, where="Hours policy → Enter the policy",
                     do="Type the normal work week and when extra hours start; choose Banked or Paid as overtime; type the "
                        "banked hours for each extra hour; choose whether Shop / Company Work counts; choose the day the "
                        "week starts; choose the date it takes effect",
                     enter="For practice: 40, 40, Banked, 1, Yes, Monday, this Monday",
                     expect="Every box must be filled; a missing value is named in red.",
                     if_wrong="'cannot be before … the start of this week': earlier weeks keep the rules they were "
                              "worked under; choose this week or later."),
                Step(title="Save it", app=O, where="Hours policy",
                     do="Press Save hours policy",
                     expect="'Hours policy saved (version 1, in effect from …)'; In use now states the policy in one "
                            "line; Changes lists version 1 with your name. Getting started step 15 is ticked.",
                     if_wrong="To change it later, save again with a new effective date; the old version stays in "
                              "Changes with old → new.",
                     shot="c04-hours-policy-saved.png", endpoint="payroll_time.hours_policy"),
            ),
            exercise="On the training site enter 40, 40, Banked, 1, Yes, Monday, this Monday, and read the policy "
                     "line on Banked hours.",
        ),
        Lesson(
            key="c04-approve-to-quickbooks-time", title="Approve hours: they go to QuickBooks Time by themselves",
            what="Approve the crew's hours and see each approved entry go to QuickBooks Time for payroll.",
            why="The crew enter hours once. Approval sends them to QuickBooks Time; nobody types them again.",
            steps=(
                Step(title="Review and approve", app=O, where=f"{HUB} → Time → Review time (or Accounting → QuickBooks "
                                                              "Time transfers → Time review)",
                     do="Tick the Submitted rows and press Approve selected",
                     expect="'Approved N time entries.' and, when QuickBooks Time is switched on, 'Sent to QuickBooks "
                            "Time: N.' The QuickBooks Time column says In QuickBooks Time.",
                     if_wrong="'Not everything reached QuickBooks Time' — do the next lesson. Not switched on: the "
                              "column says Waiting to send and nothing is sent.",
                     shot="c04-time-review-qbt.png", endpoint="time_entry.review"),
                Step(title="Open QuickBooks Time transfers", app=O, where="Company → Accounting → Crew hours and payroll "
                                                                          "→ QuickBooks Time transfers",
                     do="Read the Connection box and the Transfers table",
                     expect="Each approved entry once: CT-T number, worker, date, hours, job, status (In QuickBooks "
                            "Time, Waiting to send, Needs a link, Failed — retry, Replaced by a correction).",
                     if_wrong="Crew never see this page.",
                     shot="c04-quickbooks-time.png", endpoint="payroll_time.quickbooks_time"),
                Step(title="Link people and jobs (owner, once)", app=O, where="QuickBooks Time transfers → People and "
                                                                               "job links",
                     do="Choose each person's QuickBooks Time person, each job's and each Shop / Company Work "
                        "category's job code; press Save on each row",
                     expect="'Link saved.' and 'Linked to … by <you>'.",
                     if_wrong="A QuickBooks Time person can be linked to one worker only.",
                     endpoint="payroll_time.quickbooks_time_links"),
                Step(title="Correct after approval", app=O, where="The time entry → Correct approved time",
                     do="Type the right hours and the reason; press Correct approved time",
                     expect="'Approved time corrected. The original entry is kept.' The same QuickBooks Time timesheet "
                            "is changed (the transfer shows (correction)) and banked hours get a difference row.",
                     if_wrong="If the week is approved and locked in QuickBooks Time, unapprove it there, then Retry.",
                     endpoint="time_entry.detail"),
            ),
            exercise="Approve Kevin's Harbour Lane hours on the training site and find the entry on QuickBooks Time "
                     "transfers.",
        ),
        Lesson(
            key="c04-failed-transfers", title="When hours did not reach QuickBooks Time",
            what="Fix a transfer that needs a link or failed, and retry it safely.",
            why="Every failure stays on the page with the reason. Retry checks QuickBooks Time first, so nothing is "
                "ever entered twice.",
            steps=(
                Step(title="Find it", app=O, where="Accounting → QuickBooks Time transfers",
                     do="Press the Failed — retry (or Needs a link) count at the top",
                     expect="Only those rows, each with What to do.",
                     if_wrong="No such count: everything went.", endpoint="payroll_time.quickbooks_time"),
                Step(title="Fix the cause", app=O, where="The row's What to do",
                     do="Needs a link: Add the link. Token refused: ask Joel for a new QuickBooks Time token. Slow down: "
                        "wait five minutes. Locked: unapprove the week in QuickBooks Time",
                     expect="The cause is fixed.",
                     if_wrong="Read the full reason on the time entry's QuickBooks Time panel."),
                Step(title="Retry", app=O, where="The row",
                     do="Press Retry (or Send waiting and retry failed for all)",
                     expect="'QuickBooks Time: 1 sent …' and the row says In QuickBooks Time.",
                     if_wrong="Held back as 'In a hand-entry file': it was already typed into QuickBooks; only if that "
                              "entry was deleted there, write why and press Send anyway."),
            ),
            exercise="Open QuickBooks Time transfers on the training site and say what you would do for Needs a link.",
        ),
        Lesson(
            key="c04-check-quickbooks-time", title="Reconcile payroll: Check QuickBooks Time",
            what="Once a week, compare QuickBooks Time with what CalibraytAI sent.",
            why="Someone may change or delete hours in QuickBooks Time; the check finds it before payroll.",
            steps=(
                Step(title="Run the check", app=O, where="QuickBooks Time transfers → Check QuickBooks Time",
                     do="Choose the pay week's From and To; press Check",
                     expect="Match; Different in QuickBooks Time; Sent but no longer there; In QuickBooks Time more than "
                            "once; Entered directly in QuickBooks Time; Approved here, not in QuickBooks Time yet.",
                     if_wrong="It only reads; nothing changes in either place.",
                     endpoint="payroll_time.quickbooks_time_check"),
                Step(title="Act on each line", app=O, where="The result",
                     do="Different: change it back there or correct it here. No longer there: Retry the transfer. More "
                        "than once: delete the extra in QuickBooks Time",
                     expect="The next check shows only matches.",
                     if_wrong="Entered directly in QuickBooks Time: make sure it is not the same hours twice."),
            ),
            exercise="Run Check QuickBooks Time for this week on the training site and read each heading.",
        ),
        Lesson(
            key="c04-banked-hours", title="Banked hours: balances, time off and adjustments",
            what="See everyone's banked hours, record time off taken, and make an agreed adjustment.",
            why="The ledger keeps every week earned, every day off and every adjustment, with who and why.",
            steps=(
                Step(title="Open Banked hours", app=O, where="Accounting → Crew hours and payroll → Banked hours",
                     do="Read the policy line and the balances",
                     expect="The hours policy in one line, each person and their banked hours.",
                     if_wrong="'Nothing is banked until the owner enters the company's hours policy': lesson Hours and "
                              "banked time.",
                     shot="c04-banked-hours.png", endpoint="payroll_time.banked_hours_index"),
                Step(title="Record time off", app=O, where="A person → Record time off taken",
                     do="Day off, Hours, What for; press Record time off",
                     expect="'Time off recorded.' The ledger shows Time off taken and the balance goes down.",
                     if_wrong="It cannot be more than the balance. You cannot change your own banked hours.",
                     endpoint="payroll_time.banked_hours_worker"),
                Step(title="Adjust", app=O, where="A person → Adjust",
                     do="Hours (2 adds, -2 removes) and Why; press Adjust",
                     expect="'Banked hours adjusted.' with the reason in the ledger.",
                     if_wrong="Use only for agreed corrections; wrong approved hours are fixed with Correct approved time."),
            ),
            exercise="On the training site record 2 hours of time off for Kevin and find it in his ledger.",
        ),
        Lesson(
            key="c04-shop-company-work", title="Shop / Company Work",
            what="Set up Shop / Company Work once, add a category, and approve shop hours.",
            why="Shop, yard, equipment and safety-meeting hours are paid and count for payroll, but are never charged "
                "to a customer's job or shown as one.",
            steps=(
                Step(title="Set it up (once)", app=O, where="Company → Getting started → 15 Hours and banked time → "
                                                           "Go there (Hours policy; or Accounting → Shop / Company Work)",
                     do="Press Set up Shop / Company Work",
                     expect="'Shop / Company Work is ready. Crew choose Shop / Company Work on My time; it is never "
                            "billed to a customer.' The Shop / Company Work page opens.",
                     if_wrong="Already set up: Hours policy links to Shop / Company Work instead. Time review no longer "
                              "has this button; once set up, Shop / Company Work is a choice in its Project filter.",
                     endpoint="payroll_time.hours_policy"),
                Step(title="Add a category", app=O, where="Accounting → Shop / Company Work",
                     do="Type a new category (for example Snow clearing at the yard) and press Add",
                     expect="'Category added.' Crew see it under Shop / Company Work on Field.",
                     if_wrong="Categories are kinds of company work, not customers.",
                     endpoint="payroll_time.company_work"),
                Step(title="Approve shop hours", app=O, where="Time review",
                     do="Tick the shop rows (Kind: Company time) and press Approve selected",
                     expect="Approved like other time; they go to QuickBooks Time under the category's job code and are "
                            "not on any customer's job.",
                     if_wrong="Shop / Company Work never appears in Projects, Clients, estimates, change orders or "
                              "invoices; its page is Accounting → Shop / Company Work."),
            ),
            exercise="Add the category 'Snow clearing at the yard (training)' and find it on Kevin's Shop / Company "
                     "Work list.",
        ),
    ),
)

# ====================================================================================== 5
M05 = Module(
    key="c05", pathway=P, number=5, title="My Calendar, Company Calendar and scheduling",
    summary="Ben's First Day steps 7 and 8: company and personal appointments, the calendar on your phone, and how "
            "the crew read their schedule on Field.",
    roles=TEAM,
    lessons=(
        Lesson(
            key="c05-calendars", title="My Calendar and Company Calendar",
            what="Read the calendar by day, week and month, and switch between My Calendar and Company Calendar.",
            why="My Calendar is your appointments and work; Company Calendar is everyone's company appointments and the "
                "job schedule.",
            roles=OFFICE,
            steps=(
                Step(title="Open the calendar", app=O, where="Calendar (menu), or Home → Company Calendar",
                     do="Press Calendar",
                     expect="My Calendar | Company Calendar in the top bar; the whole month; the buttons Today, Month, Week, "
                            "Day, Mon–Fri | Full week, Set dates, ? and + New Appointment; under them the selected day, All "
                            "projects, This period, Text notices, Outlook · Google · Apple Calendar and Print. A busy day "
                            "shows two entries and +N more; press it to see the whole day.",
                     if_wrong="Use ‹ and › to move months, or Go to a date.",
                     shot="c05-calendar.png", endpoint="schedule.company"),
                Step(title="My or Company", app=O, where="Calendar → My Calendar | Company Calendar (top bar)",
                     do="Press Company Calendar, then My Calendar",
                     expect="Company Calendar adds everyone's company appointments; nobody else's personal appointments ever show.",
                     if_wrong="Project filters the calendar to one job; choose All projects to clear it.",
                     shot="c05-my-company-switch.png", endpoint="schedule.company"),
                Step(title="Day and Week", app=O, where="Calendar → Day / Week",
                     do="Press Week, then Day",
                     expect="Week shows seven days with + to add; Day shows the hours.",
                     if_wrong="Today brings you back to today. Mon–Fri hides Saturday and Sunday (a Sat: or Sun: tag shows "
                              "anything booked then); Full week brings them back.", shot="c05-week.png", endpoint="schedule.company"),
                Step(title="Print", app=O, where="Calendar → Print (top right, under + New Appointment)",
                     do="Press Print, check From and To (they start on the dates on screen), press Print, then Print "
                        "on the printout",
                     expect="A printable list of every appointment, work item and delivery from the From date to the To "
                            "date, day by day, with your company name and the date printed. Up to 92 days at a time.",
                     if_wrong="The From date must be on or before the To date. Back to calendar returns to the calendar.",
                     endpoint="schedule.print_calendar"),
            ),
            exercise="Open the training company's Calendar, switch to Company Calendar and Week, and find tomorrow.",
        ),
        Lesson(
            key="c05-appointments", title="Company and personal appointments",
            what="Book the Harbour Lane site visit as a company appointment and a personal appointment for yourself.",
            why="Getting started step 7: company appointments are seen by everyone; personal ones only by you.",
            roles=OFFICE,
            steps=(
                Step(title="New appointment", app=O, where="Calendar → + New Appointment",
                     do="Choose Who can see it: Company — everyone in the company",
                     expect="The form: Who can see it, Title, Type, Date, All day, times, Location, For, Client (optional), "
                            "Project (optional), Notes, Also attending.",
                     if_wrong="Personal — only you hides it from everyone else.",
                     shot="c05-appointment-form.png", endpoint="schedule.new_appointment"),
                Step(title="Fill in the site visit", app=O, where="New appointment",
                     do="Type and choose each field",
                     enter="Title: Site visit: Harbour Lane Pool Deck (training) <initials>; Type: Site visit; Date: tomorrow; "
                           "10:00–11:00; Location: 14 Harbour Lane, Merrickville, ON; For: Ben Brayman (training); "
                           "Client: Morgan Ellis (training); Project: Harbour Lane Pool Deck (training)",
                     expect="The fields hold your values.",
                     if_wrong="End must be after start.", shot="c05-appointment-form.png", endpoint="schedule.new_appointment"),
                Step(title="Add it", app=O, where="New appointment → the bottom",
                     do="Press Add appointment",
                     expect="The day shows the site visit at 10 AM with its address.",
                     if_wrong="If it does not show, check the date and My/Company switch.",
                     shot="c05-appointment-company.png", endpoint="schedule.new_appointment"),
                Step(title="A personal appointment", app=O, where="Calendar → + New Appointment",
                     do="Choose Personal — only you, Title, date and time; press Add appointment",
                     enter="Truck service (training, personal) <initials>, tomorrow 15:00–16:00",
                     expect="You see both on your day; others see only the company one.",
                     if_wrong="Open an appointment to edit or cancel it.",
                     shot="c05-day.png", endpoint="schedule.company"),
            ),
            exercise="Book 'Site visit: Harbour Lane Pool Deck (training) <initials>' for tomorrow 10:00 with Morgan Ellis "
                     "and the Harbour Lane project, and a personal appointment. Ask a colleague whether they can see each.",
        ),
        Lesson(
            key="c05-phone-calendar", title="See it on your phone's calendar",
            what="Turn on your private calendar feed and subscribe to it in Apple, Google or Outlook.",
            why="Getting started step 8: your appointments show in the calendar you already use and update by themselves. "
                "It is read-only: you still make changes in CalibraytAI.",
            roles=OFFICE,
            steps=(
                Step(title="Open Calendar connection", app=O, where="Calendar → Outlook · Google · Apple Calendar",
                     do="Press Turn on my calendar feed",
                     expect="Your private address is shown once, with Copy and Open in Apple Calendar or Outlook.",
                     if_wrong="Lost the address? Press Make a new address: the old one stops at once.",
                     shot="c05-feed-off.png", endpoint="schedule.calendar_feed_settings"),
                Step(title="Copy the address", app=O, where="Calendar connection → Your private address",
                     do="Press Copy",
                     expect="The address (ending .ics) is copied. Keep it to yourself: anyone with it can read your appointments.",
                     if_wrong="It is shown only this once.",
                     shot="c05-feed-address.png", endpoint="schedule.calendar_feed_settings"),
                Step(title="iPhone", app=APP_PHONE_CALENDAR,
                     where="On the iPhone in Safari: Calendar connection → Open in Apple Calendar or Outlook",
                     do="Press Subscribe, then Add. (By hand: Settings → Apps → Calendar → Calendar Accounts → Add Account → "
                        "Other → Add Subscribed Calendar → paste → Next → Save)",
                     expect="A CalibraytAI calendar appears in Apple Calendar with the site visit.",
                     if_wrong="Before iOS 18: Settings → Calendar → Accounts → Add Account → Other. Needs only the iPhone, "
                              "no Apple password is given to CalibraytAI."),
                Step(title="Google or Outlook", app=APP_PHONE_CALENDAR,
                     where="Google: calendar.google.com → Other calendars → + → From URL. Outlook: Add calendar → Subscribe from web",
                     do="Paste the address and press Add calendar (Google) or Import (Outlook)",
                     expect="The calendar appears; Google and Outlook refresh it themselves, usually within hours.",
                     if_wrong="Google adds a calendar by address only on a computer; it then shows on the phone. Needs your "
                              "own Google or Microsoft account.",
                     shot="c05-feed-instructions.png", endpoint="schedule.calendar_feed_settings"),
            ),
            exercise="Turn on your calendar feed on the training site and subscribe to it in your phone's calendar. Check "
                     "your Harbour Lane site visit appears, then press Turn off when you finish training.",
        ),
        Lesson(
            key="c05-field-schedule", title="Your schedule on Field (This week, This month)",
            what="Read your work for the week and month, and what the company has on today.",
            why="The crew's job schedule is on Field, not in the phone calendar feed.",
            roles=OWNER_FIELD,
            steps=(
                Step(title="This week", app=F, where="Field → This week",
                     do="Read each day",
                     expect="Each day lists the work you or your crew are booked on, with the job address and Directions.",
                     if_wrong="'Nothing is scheduled for you this week' until the office schedules your crew.",
                     shot="c11-field-week.png", endpoint="field.week"),
                Step(title="This month", app=F, where="Field → This month",
                     do="Tap a day; use Previous month and Next month",
                     expect="The month with your booked days; the chosen day's work below.",
                     if_wrong="Dates move when the office changes the schedule.",
                     shot="c11-field-month.png", endpoint="field.month"),
                Step(title="Company today", app=F, where="Field → Company today",
                     do="Read it",
                     expect="What the company has scheduled today. It does not change dates.",
                     if_wrong="It is information only.",
                     shot="c11-field-company-today.png", endpoint="field.company_today"),
            ),
            exercise="On your iPhone, open This week and This month on the training site. After the office schedules the "
                     "Pool deck crew on Harbour Lane (module 11), look again and find the job.",
        ),
    ),
)

# ====================================================================================== 6
M06 = Module(
    key="c06", pathway=P, number=6, title="Customers, projects and existing jobs",
    summary="Ben's First Day step 10: the customer, the project and its hub, the job location, and bringing in the "
            "jobs you already have.",
    roles=OFFICE,
    lessons=(
        Lesson(
            key="c06-clients", title="Customers (Clients)",
            what="Find, add and update a customer.",
            why="The customer's email is where proposals go; their name goes on the contract and invoices.",
            steps=(
                Step(title="Open Clients", app=O, where="Clients (menu)",
                     do="Read the list",
                     expect="Each client with email and phone; New Client at the top.",
                     if_wrong="The client list is the company's; Field crew never see it.",
                     shot="c06-clients.png", endpoint="clients.list_clients"),
                Step(title="A new client", app=O, where="Clients → New Client",
                     do="Type Client name (required), Company, Email, Phone, Address, Notes; press Save Client",
                     expect="Client created.",
                     if_wrong="Check the email: the proposal link goes there.",
                     shot="c06-client-new.png", endpoint="clients.create_client"),
                Step(title="Update a client", app=O, where="Clients → Morgan Ellis (training)",
                     do="Change Notes, press Save Client",
                     enter="Notes: Pool deck around the existing in-ground pool. Prefers email. (training) <initials>",
                     expect="The client is saved.",
                     if_wrong="Cancel leaves without saving.",
                     shot="c06-client-edit.png", endpoint="clients.edit_client"),
            ),
            exercise="Open Morgan Ellis (training), check the email and phone (613-555-0142), add your note and press Save "
                     "Client. Do not make a second Morgan Ellis.",
        ),
        Lesson(
            key="c06-project-hub", title="The project page (the hub)",
            what="Open a project and learn its tabs.",
            why="Everything about one job is on its hub: the customer, location, drawings, estimate, proposal, contract, "
                "work, money and field notes.",
            steps=(
                Step(title="Open Projects", app=O, where="Projects (menu)",
                     do="Read Current and Closed; press the job",
                     expect="Harbour Lane Pool Deck (training) · Morgan Ellis (training) · 14 Harbour Lane, Merrickville, ON · "
                            "Estimating.",
                     if_wrong="A closed job is under Closed.",
                     shot="c06-projects.png", endpoint="projects.list_projects"),
                Step(title="The hub", app=O, where=HUB,
                     do="Read the top: Continue setup, Drawings, Scope of work, New Change Order, Print, Close Project",
                     expect="The project name and the tabs PROJECT, SETTINGS, MONEY, DOCUMENTS, PROJECT WORK.",
                     if_wrong="Close Project is only for the owner.",
                     shot="c06-project-hub.png", endpoint="projects.view_project"),
                Step(title="Move between tabs", app=O, where="The hub → tabs",
                     do="Press DOCUMENTS (drawings, estimates, proposals, contract), PROJECT WORK (work, schedule, purchasing, "
                        "time, change orders, field observations), MONEY (actual costs)",
                     expect="The page jumps to that part.",
                     if_wrong="Scroll back to the top for the tabs.",
                     shot="c06-project-tabs.png", endpoint="projects.view_project"),
            ),
            exercise=f"Open {JOB} and find, without searching: Related Estimates, Purchasing, Related Change Orders and "
                     "Field Observations.",
        ),
        Lesson(
            key="c06-project-setup", title="Finish the project's setup and location",
            what="Use Continue setup: confirm the job address and say whether drawings are needed.",
            why="The job location decides the contract package and the permit report; the drawings choice decides what "
                "setup still asks for.",
            steps=(
                Step(title="Continue setup", app=O, where=f"{HUB} → Continue setup",
                     do="Read What's ready and What's still needed",
                     expect="For example: The client is in this company; Review location.",
                     if_wrong="Project page takes you back to the hub.",
                     shot="c06-project-setup.png", endpoint="projects.project_setup"),
                Step(title="Job location", app=O, where="Continue setup → Review location",
                     do="Type the structured address and press Save location and preliminary profile",
                     enter="Street / civic address 14 Harbour Lane; Municipality Merrickville; Province / state Ontario; Country Canada",
                     expect="Setup says The job location is complete.",
                     if_wrong="Postal / ZIP is optional. A permit report is not municipal approval.",
                     shot="c06-location.png", endpoint="projects.edit_project_location"),
                Step(title="Drawings needed?", app=O, where=f"{HUB} → DOCUMENTS → Drawings",
                     do="Press Drawings are required (or Drawings are not required)",
                     expect="Setup moves on (Choose about drawings disappears).",
                     if_wrong="You can change it later on the hub.",
                     shot="c07-hub-drawings.png", endpoint="projects.project_setup"),
            ),
            exercise=f"On {JOB}: Continue setup, complete the location (14 Harbour Lane, Merrickville, Ontario, Canada) and "
                     "choose Drawings are required (Morgan has a deck plan; module 7).",
        ),
        Lesson(
            key="c06-existing-jobs", title="Bring in the jobs you already have",
            what="Add a project for work already under way, with its client.",
            why="Getting started step 10: schedule, Field and invoices work only on projects in CalibraytAI.",
            steps=(
                Step(title="Start a project", app=O, where="Projects → + Start New Project",
                     do="Type Project name, choose Client and Status",
                     enter="Project name: Ellis Front Steps (training, existing job) <initials>; Client: Morgan Ellis (training); Status: Active",
                     expect="New Project with Project Details, Structured project location, Permit context class and the "
                            "Commercial Decision Gate.",
                     if_wrong="Make the client first (Clients → New Client) if they are not in the list.",
                     shot="c06-project-new.png", endpoint="projects.create_project"),
                Step(title="The required choices", app=O, where="New Project → Commercial Decision Gate",
                     do="Choose Project Type, Pricing Posture, Execution Risk, Schedule Condition, Site Condition, Estimate "
                        "Stage and Delivery Model; press Save Project",
                     expect="Project created; the hub opens.",
                     if_wrong="Fields with * are required. An exceptional choice may need a Justification Reason.",
                     shot="c06-project-gate.png", endpoint="projects.create_project"),
            ),
            exercise="Practise on the form only: fill in 'Ellis Front Steps (training, existing job) <initials>' for "
                     "Morgan Ellis, then press Cancel (the course follows Harbour Lane only).",
        ),
    ),
)

# ====================================================================================== 7
M07 = Module(
    key="c07", pathway=P, number=7, title="Drawings, calculators and material takeoffs",
    summary="Upload the customer's plan, work out quantities with the calculators, read the Deck Takeoff, and see the "
            "drawings on Field.",
    roles=TEAM,
    lessons=(
        Lesson(
            key="c07-plans", title="Upload the plan PDF",
            what="Put the customer's deck plan on the project.",
            why="The office and the crew work from the same drawing; Field shows it on the phone.",
            roles=OFFICE,
            steps=(
                Step(title="Open Drawings", app=O, where=f"{HUB} → DOCUMENTS → Drawings → All drawings",
                     do="Press Upload PDF",
                     expect="Drawings: Current drawings, Build Drawings; Upload PDF.",
                     if_wrong="Drawings is also at the top of the hub.",
                     shot="c07-drawings.png", endpoint="plan_intelligence.list_plans"),
                Step(title="Choose the PDF", app=O, where="Upload Plan PDF",
                     do="Choose the file in Plan PDF, type Notes, press Upload",
                     enter="Notes: Deck plan from Morgan Ellis (training)",
                     expect="The plan page opens with its name, Pages, Sheet Index and Download. A scanned PDF says no "
                            "embedded text was detected.",
                     if_wrong="Only PDF files. Searchable PDFs are better for take-off.",
                     shot="c07-upload.png", endpoint="plan_intelligence.upload_plan"),
                Step(title="See it listed", app=O, where="Drawings → Current drawings",
                     do="Find the file",
                     expect="The plan is listed; crew on the job see it on Field → Drawings and plans.",
                     if_wrong="Archive document removes a wrong upload from current drawings.",
                     shot="c07-plan-listed.png", endpoint="plan_intelligence.list_plans"),
            ),
            exercise=f"Upload a PDF plan (ask the trainer for the training deck plan) to {JOB} with the note 'Deck plan "
                     "from Morgan Ellis (training) <initials>'.",
        ),
        Lesson(
            key="c07-concrete-calculator", title="Calculators: concrete for the equipment pad",
            what="Work out the concrete for a slab with the Concrete calculator.",
            why="The quantity you order from BMR comes from a calculation, not a guess.",
            roles=OFFICE,
            steps=(
                Step(title="Open the calculator", app=O, where="CALCULATORS → Concrete calculator",
                     do="Choose Standard slab and Measured in Feet and inches",
                     expect="Length, Width, Slab thickness, Waste allowance, Order in (m³ or yd³) and Calculate concrete.",
                     if_wrong="CALCULATORS is folded in the menu; press it to open.",
                     shot="c07-concrete-calculator.png", endpoint="calculators.concrete"),
                Step(title="Calculate", app=O, where="Concrete calculator",
                     do="Type the sizes and press Calculate concrete",
                     enter="Length 12 ft, Width 10 ft, Slab thickness 6 in, Waste allowance 5",
                     expect="Order 2.00 m³ (total with waste 1.784 m³, 2.333 yd³, rounded up to the next 0.25 m³); "
                            "Base slab concrete 2.222 yd³, Waste allowance 0.111 yd³, Total concrete 2.333 yd³. "
                            "'This result is not on an estimate.'",
                     if_wrong="A blank or invalid measurement is refused; type numbers only.",
                     shot="c07-concrete-result.png", endpoint="calculators.concrete"),
            ),
            exercise="Calculate the Harbour Lane equipment pad: 12 ft × 10 ft × 6 in, 5 % waste. Write down the total "
                     "(2.333 yd³). You will ask BMR for 2.5 m³ (rounded up for a full load) in module 8.",
        ),
        Lesson(
            key="c07-deck-takeoff", title="Deck Takeoff and Construction Drawings",
            what="Read the Pool Deck Material Takeoff and the product facts it needs.",
            why="Brayman calculates the deck material; the supplier prices it. A missing fact stays visible; nothing here "
                "creates an estimate line by itself.",
            roles=OFFICE,
            steps=(
                Step(title="Open Deck Takeoff", app=O, where=f"{HUB} → DOCUMENTS → Deck Takeoff",
                     do="Read the top",
                     expect="Pool Deck Material Takeoff. Until the project's construction information is stored it says "
                            "PROJECT FACTS MISSING and lists them.",
                     if_wrong="Enter construction information (top of the hub) stores the deck's facts.",
                     shot="c07-deck-takeoff.png", endpoint="deck_takeoff.review"),
                Step(title="Product facts", app=O, where="Deck Takeoff → the product facts form",
                     do="Fill in the manufacturer's facts you have, Where these facts came from, Entered by; press Save "
                        "product facts",
                     expect="Saved as a new version; nothing has a default and a blank stays missing.",
                     if_wrong="Take facts from the manufacturer's sheet, never guess.",
                     shot="c07-deck-product-facts.png", endpoint="deck_takeoff.review"),
                Step(title="Construction Drawings", app=O, where=f"{HUB} → DOCUMENTS → Construction Drawings",
                     do="Open it",
                     expect="Construction Drawings for the job (empty until drawings are generated), with Back to project.",
                     if_wrong="CalibraytAI does not draw the crew set for you; upload your own plan.",
                     shot="c07-construction-drawings.png", endpoint="construction_drawings.index"),
            ),
            exercise=f"Open Deck Takeoff on {JOB} and write down which project facts it says are missing. Do not invent "
                     "product facts.",
        ),
        Lesson(
            key="c07-field-drawings", title="Your job's drawings on Field",
            what="Open the job's drawings and plans on your iPhone.",
            why="Build from the current plan the office uploaded.",
            roles=OWNER_FIELD,
            steps=(
                Step(title="Choose the job", app=F, where="Field → Today → Choose Project",
                     do="Tap Harbour Lane Pool Deck (training)",
                     expect="Confirm Project with Confirm and Capture, Confirm and Time, Confirm for Today, Drawings and plans.",
                     if_wrong="Only jobs you are scheduled on are listed.",
                     shot="c11-field-confirm.png", endpoint="field.project_confirm"),
                Step(title="Open Drawings and plans", app=F, where="Confirm Project → Drawings and plans",
                     do="Tap the plan's name",
                     expect="Drawings and plans: Construction drawings and Plans; the PDF opens in a new tab.",
                     if_wrong="Nothing listed? Ask the office to upload it.",
                     shot="c07-field-drawings.png", endpoint="field.drawings"),
            ),
            exercise="Once you are scheduled on Harbour Lane (module 11), open its Drawings and plans on your iPhone and "
                     "open the deck plan.",
        ),
    ),
)

# ====================================================================================== 8
M08 = Module(
    key="c08", pathway=P, number=8, title="Suppliers, quotations and purchasing",
    summary="Ben's First Day steps 9 and 13: your suppliers and their sign-ins, a concrete request to BMR Winchester, "
            "BMR's quote, the purchase order and deliveries.",
    roles=OFFICE,
    lessons=(
        Lesson(
            key="c08-suppliers", title="Your suppliers",
            what="See your supplier accounts and give the store's people a Supplier Hub sign-in.",
            why="Getting started step 9: requests and orders go to the store's own Supplier Hub; they never see your "
                "customer's prices or details.",
            steps=(
                Step(title="Open Suppliers", app=O, where="Company → Suppliers",
                     do="Read Supplier accounts",
                     expect="BMR Winchester (training) — Winchester store (training) · active, with the people who can sign in.",
                     if_wrong="If a supplier is missing, add it under Add a supplier.",
                     shot="c08-suppliers.png", endpoint="supplier_office.suppliers"),
                Step(title="Give a sign-in", app=O, where="Suppliers → the supplier → Name, Email",
                     do="Type the store person's name and email, press Give Supplier Hub sign-in",
                     expect="They are listed with Remove sign-in and sign in at the Supplier Hub address shown on the page (…/supplier/login).",
                     if_wrong="Use the store person's own work email.",
                     shot="c08-supplier-signins.png", endpoint="supplier_office.suppliers"),
                Step(title="Add a supplier", app=O, where="Suppliers → Add a supplier",
                     do="Type Supplier name and Store or location, press Add supplier",
                     expect="'… added'. If the supplier is already on CalibraytAI, that company is used (no duplicate).",
                     if_wrong="Do not add BMR again on the training site.",
                     shot="c08-add-supplier.png", endpoint="supplier_office.suppliers"),
            ),
            exercise="Open Company → Suppliers and check BMR Winchester (training) is active and that Darcy and Pat can "
                     "sign in. Do not add another BMR.",
        ),
        Lesson(
            key="c08-concrete-request", title="Ask BMR for a concrete quote",
            what="Send a concrete request from the project to BMR Winchester.",
            why="The quote comes back in CalibraytAI with the job, so the price you approve is the price you order.",
            steps=(
                Step(title="Open supplier requests", app=O, where=f"{HUB} → PROJECT WORK → Purchasing",
                     do="Press Supplier requests, concrete and orders",
                     expect="Supplier requests — Harbour Lane Pool Deck (training): Deliveries, Material and concrete requests, Concrete.",
                     if_wrong="Deck material requests start on Deck takeoff.",
                     shot="c08-hub-purchasing.png", endpoint="supplier_office.project_requests"),
                Step(title="Fill in the concrete", app=O, where="Supplier requests → Concrete",
                     do="Fill the form and choose Send to",
                     enter="Volume (m³) 2.5; Strength (MPa) 32; Exposure class C-2; Delivery date: the first day of the "
                           "job; Delivery time window 7:00–9:00; Placement Chute; Delivery town Merrickville; Notes: "
                           "Equipment pad beside the pool deck (training) <initials>; Send to BMR Winchester (training)",
                     expect="The form holds your values.",
                     if_wrong="'Save only, send later' keeps it unsent; press Send later.",
                     shot="c08-concrete-request.png", endpoint="supplier_office.project_requests"),
                Step(title="Send it", app=O, where="Concrete → the bottom",
                     do="Press Save concrete request",
                     expect="'Concrete request CON-… sent to BMR Winchester (training) (SRQ-…)'; it is listed under Material "
                            "and concrete requests.",
                     if_wrong="Withdraw this request if it was a mistake.",
                     shot="c08-request-sent.png", endpoint="supplier_office.project_requests"),
                Step(title="What BMR sees", app=APP_SUPPLIER, where="Supplier Hub (Darcy at BMR) → Needs attention",
                     do="Nothing to press: Darcy sees your request under QUOTES TO ANSWER",
                     expect="The request number, Brayman Construction (training), Concrete, the date and Merrickville. Never "
                            "the customer's name or your prices.",
                     if_wrong="The supplier pathway teaches Darcy's side.",
                     shot="c08-supplier-inbox.png", endpoint="supplier_portal.inbox"),
            ),
            exercise=f"From {JOB}, send BMR Winchester (training) a request for 2.5 m³ of 32 MPa C-2 concrete by chute to "
                     "Merrickville, 7:00–9:00, with your initials in the notes. Write down the SRQ number.",
        ),
        Lesson(
            key="c08-approve-quote", title="BMR's quote and approving it",
            what="Read BMR's returned quote and approve it.",
            why="Approving the quote accepts BMR's price for this job; placing the order is a separate step.",
            steps=(
                Step(title="BMR returns the quote", app=APP_SUPPLIER, where="Supplier Hub → the request → Your quote",
                     do="Darcy types the quote number, Price per m³ 215.00, Short-load charge 75.00, Prices valid until, then "
                        "presses Return quote",
                     expect="CalibraytAI works out the total: 2.5 m³ × $215.00 + $75.00 = $612.50 before tax.",
                     if_wrong="On the training site, ask the trainer or a supplier trainee to return it as Darcy.",
                     shot="c08-supplier-quote.png", endpoint="supplier_portal.request_detail"),
                Step(title="Read the quote", app=O, where=f"{HUB} → Supplier requests, concrete and orders",
                     do="Read the request",
                     expect="The quote: $612.50 before tax, valid until its date, with Approve this quote.",
                     if_wrong="Not returned yet? It says it is waiting for the supplier.",
                     shot="c08-quote-returned.png", endpoint="supplier_office.project_requests"),
                Step(title="Approve it", app=O, where="Supplier requests → the request",
                     do="Press Approve this quote",
                     expect="'Concrete quote approved. Placing the order is a separate step.' The order form appears.",
                     if_wrong="Use the approved $612.50 on the estimate (module 9).",
                     shot="c08-quote-approved.png", endpoint="supplier_office.project_requests"),
            ),
            exercise="When BMR's quote for your Harbour Lane request is returned ($215.00 per m³ and $75.00 short-load), "
                     "check it says $612.50 before tax and press Approve this quote. Do not place the order yet.",
        ),
        Lesson(
            key="c08-place-order", title="Place the order and follow the delivery",
            what="Once the customer has accepted, place the purchase order linked to the schedule; BMR confirms it.",
            why="Getting started step 13: the order is linked to the job and its schedule, so moving the work proposes "
                "a new delivery to BMR.",
            steps=(
                Step(title="Fill in the order", app=O, where=f"{HUB} → Supplier requests, concrete and orders → the approved quote",
                     do="Fill Delivery date, Time window, Follows the project schedule item, Site contact, Notes for the supplier",
                     enter="Delivery date: the first day of the job; 7:00–9:00; Follows: the Harbour Lane framing work; "
                           "Site contact: Kevin Field (training crew) 613-555-0101",
                     expect="The form holds your values.",
                     if_wrong="Place orders only after Morgan has accepted (module 10) and the work is scheduled (module 11).",
                     shot="c08-place-order.png", endpoint="supplier_office.project_requests"),
                Step(title="Sign and send it", app=O, where="The order form → Adopt your signature",
                     do="In Adopt your signature tick I agree to sign electronically and type your full name, then "
                        "press Sign & Send for E-Signature (CaliSIGN)",
                     enter="Your full name",
                     expect="'Purchase order PO-… signed and sent to BMR Winchester (training). It is agreed when they "
                            "sign and confirm it.' The order shows Awaiting Signature.",
                     if_wrong="Without the tick and your name nothing is signed or sent. A mistake? Cancel this order "
                              "(with a reason the supplier sees).",
                     shot="c08-order-sent.png", endpoint="supplier_office.project_requests"),
                Step(title="BMR confirms", app=APP_SUPPLIER, where="Supplier Hub → the request → Purchase order",
                     do="Darcy checks the date, ticks I agree to sign electronically, types his full name and "
                        "presses Sign & Confirm Order (or Report a problem)",
                     expect="Your page says Confirmed by Darcy and Executed, with both signatures and the agreed delivery "
                            "date and window. Both sides can download the signed purchase order.",
                     if_wrong="A problem shows the supplier's note; answer it or change the delivery.",
                     shot="c08-supplier-order.png", endpoint="supplier_portal.request_detail"),
                Step(title="Deliveries", app=O, where="Supplier requests → All deliveries, every project (or /deliveries)",
                     do="Read the list",
                     expect="Every order's delivery date, window and status; Text me updates sends changes by text.",
                     if_wrong="Change the delivery on the request page; BMR answers it in the Supplier Hub.",
                     shot="c08-deliveries.png", endpoint="supplier_office.deliveries"),
            ),
            exercise="After Morgan accepts (module 10) and the crew is scheduled (module 11): place the Harbour Lane "
                     "concrete order for the first day of the job, linked to the framing work, and check it shows as "
                     "Confirmed once BMR confirms.",
        ),
    ),
)

# ====================================================================================== 9
M09 = Module(
    key="c09", pathway=P, number=9, title="Estimates, costing and pricing",
    summary="Ben's First Day step 11: what you pay, the estimate and its lines, who supplies and builds each line, "
            "costing approval and the company's pricing.",
    roles=OFFICE,
    lessons=(
        Lesson(
            key="c09-cost-library", title="What we pay and Reusable work",
            what="See the company's cost items and reusable groups of work.",
            why="Lines you price often come from here; one-off lines are typed on the estimate.",
            steps=(
                Step(title="What we pay", app=O, where="COSTS & PRICING → What we pay",
                     do="Read the list",
                     expect="The company's cost items with their units and costs.",
                     if_wrong="Prices from a supplier's quote stay on that job; they are not a standing price list.",
                     shot="c09-what-we-pay.png", endpoint="cost_library.list_cost_items"),
                Step(title="Reusable work", app=O, where="COSTS & PRICING → Reusable work",
                     do="Read the list",
                     expect="Groups of lines you add to an estimate in one go (Add Assembly).",
                     if_wrong="Empty on a new company.",
                     shot="c09-reusable-work.png", endpoint="assemblies.list_assemblies"),
            ),
            exercise="Open What we pay and Reusable work on the training site and note whether anything there fits a pool "
                     "deck. (The Harbour Lane estimate uses typed lines.)",
        ),
        Lesson(
            key="c09-new-estimate", title="The estimate and its lines",
            what="Make the Harbour Lane estimate with a section and three lines.",
            why="The estimate is your cost; the customer sees the price only on the proposal.",
            steps=(
                Step(title="New estimate", app=O, where=f"{HUB} → DOCUMENTS → Related Estimates",
                     do="Press New estimate",
                     expect="New Estimate: Estimate number (suggested), Title, Project, Estimate status.",
                     if_wrong="Leave the suggested number.",
                     shot="c09-hub-estimates.png", endpoint="projects.view_project"),
                Step(title="Save the estimate", app=O, where="New Estimate",
                     do="Type the Title, press Save Estimate",
                     enter="Pool deck and equipment pad (training) <initials>",
                     expect="Estimate created with Version 1; press View Version.",
                     if_wrong="The project must be chosen.",
                     shot="c09-estimate-new.png", endpoint="estimates.create_estimate_route"),
                Step(title="Open the version", app=O, where="The estimate → v1 — Initial Estimate",
                     do="Press View Version",
                     expect="The version page: Estimate Totals, Costing review, Pricing, Add Section.",
                     if_wrong="Create New Version keeps the old one for history.",
                     shot="c09-estimate.png", endpoint="estimates.view_estimate"),
                Step(title="Add a section", app=O, where="The version → Add Section",
                     do="Type Section name, press Add Section",
                     enter="Pool deck",
                     expect="Section added.",
                     if_wrong="Sections group lines on the proposal.",
                     shot="c09-section.png", endpoint="estimates.view_version"),
                Step(title="Add the lines", app=O, where="The section → Add Custom / Allowance",
                     do="Type Description, Quantity, Unit, Unit cost; press Add Line (once per line)",
                     enter="Pool deck framing, pressure-treated, supplied and installed (training) 1 ls 6800; Composite "
                           "decking, supplied and installed (training) 420 sq ft 12.00; Concrete for the equipment pad, "
                           "2.5 m³ delivered by BMR (training) 1 ls 612.50",
                     expect="SUBTOTAL $12452.50.",
                     if_wrong="Edit or Delete a line beside it. Unit cost is your cost, not the customer's price.",
                     shot="c09-line.png", endpoint="estimates.view_version"),
            ),
            exercise=f"On {JOB} make the estimate 'Pool deck and equipment pad (training) <initials>' with a Pool deck "
                     "section and the three lines above (the concrete line is BMR's approved $612.50). Check SUBTOTAL "
                     "$12452.50.",
        ),
        Lesson(
            key="c09-scope-delivery-costing", title="Who supplies and builds each line, and costing approval",
            what="Confirm each line on Scope Delivery Review, then approve all costing.",
            why="Costing cannot be approved until you say who provides the material and who does the work for every line.",
            steps=(
                Step(title="Open Scope Delivery Review", app=O, where="The estimate version",
                     do="Press Open Scope Delivery Review",
                     expect="One row per line with who provides the material and who does the work.",
                     if_wrong="It is also on the hub under DOCUMENTS.",
                     shot="c09-lines.png", endpoint="estimates.view_version"),
                Step(title="Choose and approve", app=O, where="Scope Delivery Review",
                     do="For each line choose the material (we purchase) and the labour (our crew), then press Approve All "
                        "Scope Routing",
                     expect="'Approved scope routing for 3 …'.",
                     if_wrong="An unconfirmed line blocks approval: fix it or take it off. Do not approve over a block.",
                     shot="c09-scope-delivery.png", endpoint="scope_delivery.review"),
                Step(title="Approve all costing", app=O, where="The estimate version → Costing review",
                     do="Press Approve all costing",
                     expect="Costing approved. It approves your cost, not the customer's price or the supplier's price.",
                     if_wrong="If it is refused, go back to Scope Delivery Review.",
                     shot="c09-approve-costing.png", endpoint="estimates.view_version"),
            ),
            exercise="Confirm the three Harbour Lane lines as contractor-purchased material and our own crew, approve the "
                     "scope routing, then press Approve all costing.",
        ),
        Lesson(
            key="c09-pricing", title="Apply the company's pricing",
            what="Price the estimate with the company pricing policy and HST.",
            why="The customer price comes from the policy you approved in module 2, the same on every job.",
            steps=(
                Step(title="Apply org pricing policy", app=O, where="The estimate version → Pricing",
                     do="Leave 'Use resolved org / context policy' and press Apply org pricing policy",
                     expect="Pricing: Gross Margin Pricing, Target gross margin 0.200000, Pre-tax selling price $15565.63, "
                            "Tax $2023.53 (13.00%), Customer total $17589.16.",
                     if_wrong="The button stays off until costing is approved. An override needs a reason.",
                     shot="c09-apply-pricing.png", endpoint="estimates.view_version"),
                Step(title="Check the totals", app=O, where="The estimate version → Pricing",
                     do="Read DIRECT COST BASIS, PRE-TAX SELLING PRICE, TAX and CUSTOMER TOTAL",
                     expect="Direct cost $12452.50; Customer total $17589.16.",
                     if_wrong="Different numbers mean a different policy is the company default (check How we price).",
                     shot="c09-priced.png", endpoint="estimates.view_version"),
            ),
            exercise="Apply the company pricing to your Harbour Lane estimate and check the customer total: $17,589.16 "
                     "with the 20 % margin policy and 13 % HST.",
        ),
    ),
)

# ====================================================================================== 10
M10 = Module(
    key="c10", pathway=P, number=10, title="Proposals, customer acceptance and contracts",
    summary="Ben's First Day step 12: a proposal template, sign off the estimate, send Morgan her link, her "
            "acceptance on her phone, and the contract for review.",
    roles=OFFICE,
    lessons=(
        Lesson(
            key="c10-proposal-template", title="A proposal template (once)",
            what="Make the company's default proposal template.",
            why="Sign off asks for an active template: it holds the introduction, payment terms and what the customer sees.",
            steps=(
                Step(title="Open Templates", app=O, where="PROPOSALS → Templates",
                     do="Press New Template",
                     expect="New Proposal Template.",
                     if_wrong="An active default template may already exist; then you can skip this lesson.",
                     shot="c10-templates.png", endpoint="proposal_templates.list_templates"),
                Step(title="Fill and save", app=O, where="New Proposal Template",
                     do="Type Name, Default intro text, Default payment terms; tick Default template and Active; press Save Template",
                     enter="Name: Pool decks (training) <initials>; Payment terms: 30% deposit on acceptance; balance on completion.",
                     expect="Proposal template created.",
                     if_wrong="Name is required.",
                     shot="c10-template-new.png", endpoint="proposal_templates.create_template"),
            ),
            exercise="Make the template 'Pool decks (training) <initials>' with the 30 % deposit payment terms, Active.",
        ),
        Lesson(
            key="c10-send-proposal", title="Sign off and send the proposal",
            what="Sign off the priced estimate and send Morgan the proposal link.",
            why="Signing off locks the estimate so the price the customer accepts cannot change underneath them.",
            steps=(
                Step(title="Sign off", app=O, where="The priced estimate version",
                     do="Press Sign off estimate",
                     expect="'Estimate signed off and locked. Its proposal is ready: review it, then send it to the client.'",
                     if_wrong="'Create an active proposal template' first: see the previous lesson.",
                     shot="c10-sign-off.png", endpoint="estimates.view_version"),
                Step(title="Review the proposal", app=O, where="The proposal",
                     do="Press Preview or Download PDF and read it",
                     expect="The customer document titled CONSTRUCTION ESTIMATE with the Grand Total $17,589.16.",
                     if_wrong="Edit Proposal before sending if the words need changing.",
                     shot="c10-proposal.png", endpoint="proposals.view_proposal"),
                Step(title="Send it", app=O, where="The proposal → Client acceptance",
                     do="Check Client name and Client email, press Send proposal to client",
                     expect="'Proposal sent to …'. Morgan gets an email with her link.",
                     if_wrong="Fix the email on the client first if it is wrong.",
                     shot="c10-send.png", endpoint="proposals.view_proposal"),
            ),
            exercise="Sign off your Harbour Lane estimate and send the proposal to Morgan Ellis (training). The email goes "
                     "to the training mail folder: ask the trainer for the link for the next lesson.",
        ),
        Lesson(
            key="c10-customer-acceptance", title="Morgan accepts on her phone",
            what="See what the customer sees and how they accept.",
            why="Acceptance is recorded from the customer's own link, with their name and the time.",
            steps=(
                Step(title="The customer's link", app=APP_CUSTOMER, where="Morgan's email → the proposal link",
                     do="Open it",
                     expect="CONSTRUCTION ESTIMATE with your logo, introduction, pricing and payment terms. No unit costs or markup.",
                     if_wrong="An expired link: send the proposal again.",
                     shot="c10-customer-link.png", endpoint="proposal_link.view"),
                Step(title="Accept", app=APP_CUSTOMER, where="The link → Accept this proposal",
                     do="Tick 'I accept proposal PROP-… for $17,589.16, including its terms', type the full name, press Accept Proposal",
                     enter="Morgan Ellis (training)",
                     expect="Proposal accepted.",
                     if_wrong="Decline this proposal is below if the customer says no.",
                     shot="c10-customer-accept.png", endpoint="proposal_link.view"),
                Step(title="See it in the office", app=O, where="The proposal",
                     do="Open it",
                     expect="Accepted, with Review and send the contract.",
                     if_wrong="Acceptance is recorded from the customer's link only.",
                     shot="c10-accepted.png", endpoint="proposals.view_proposal"),
            ),
            exercise="Open the Harbour Lane proposal link (from the trainer) on your phone, accept it as Morgan Ellis "
                     "(training), and check the office proposal now says Accepted.",
        ),
        Lesson(
            key="c10-contract", title="The contract",
            what="Generate the construction contract for review.",
            why="The proposal is the price, not the contract. The contract uses the active Brayman V1 Ontario package.",
            steps=(
                Step(title="Review contract", app=O, where=f"{HUB} → DOCUMENTS → Production contract → Review contract",
                     do="Press Review contract",
                     expect="Production contract package available; Generate for review.",
                     if_wrong="It stays blocked without an accepted proposal or a resolved location (module 6).",
                     shot="c10-contract-review.png", endpoint="projects.review_contract"),
                Step(title="Generate", app=O, where="Review contract → Generate for review",
                     do="Press Generate contract",
                     expect="'This contract is generated for review. It is not signed.' Contract status Generated — not "
                            "signed, with Open contract.",
                     if_wrong="Generating does not send anything. Read it before Send for E-Signature (CaliSIGN).",
                     shot="c10-contract-generated.png", endpoint="projects.review_contract"),
            ),
            exercise="Generate the Harbour Lane contract for review and open it: check Morgan Ellis (training), the "
                     "project and the contract amount. Do not send it for signature on the training site unless the "
                     "trainer asks.",
        ),
    ),
)

# ====================================================================================== 11
M11 = Module(
    key="c11", pathway=P, number=11, title="Field work, deliveries and change orders",
    summary="Ben's First Day step 14: schedule the crew; Kevin's day on Field (the job, the delivery, photos and notes, "
            "extra work, time); the office turns the extra work into a change order and approves the time.",
    roles=TEAM,
    lessons=(
        Lesson(
            key="c11-schedule-crew", title="Schedule the crew on the job",
            what="Add the work item, set its dates on the calendar and assign the crew.",
            why="The crew see only what is scheduled for them; scheduling is what puts the job on their phones.",
            roles=OFFICE,
            steps=(
                Step(title="Open project work", app=O, where=f"{HUB} → PROJECT WORK",
                     do="Press Open project work",
                     expect="Project work: Extra work, Add a project work item, Add change order work item.",
                     if_wrong="Project Hub takes you back.",
                     shot="c11-hub-project-work.png", endpoint="work_structure.project_work_plan"),
                Step(title="Add the work item", app=O, where="Project work → Add a project work item",
                     do="Type Name, choose Original work, press Add work item",
                     enter="Pool deck framing and decking (training) <initials>; Original work — part of the accepted proposal",
                     expect="Work item added.",
                     why="Work added after the proposal is accepted is either the proposal's own work (original) or "
                         "extra work the customer asked for. CalibraytAI asks; it never decides for you.",
                     if_wrong="Names must be different on one project. Not choosing original or extra work is refused.",
                     shot="c11-work-item.png", endpoint="work_structure.project_work_plan"),
                Step(title="Add an activity", app=O, where="The work item → Activity name",
                     do="Type it, choose Original work, press Add activity",
                     enter="Framing and decking (training); Original work — part of the accepted proposal",
                     expect="The activity is listed; the crew send time against it.",
                     if_wrong="Without an activity, time cannot be sent.",
                     shot="c11-activity.png", endpoint="work_structure.project_work_plan"),
                Step(title="Check it is original work", app=O, where="The work item → the activity's row",
                     do="Read the activity's row",
                     expect="The activity shows Original work.",
                     why="Once the crew records time against it, original or extra can no longer be changed.",
                     if_wrong="Chose Extra work by mistake? Before any time is recorded, Record as original work on "
                              "the row fixes it. Real extra work (the customer asked for more) becomes a change order.",
                     shot="c11-record-original.png", endpoint="work_structure.project_work_plan"),
                Step(title="Set dates", app=O, where="Calendar → Set dates",
                     do="Choose the Project and the work item, Start and End, press Set dates",
                     enter="Harbour Lane Pool Deck (training); start today, end in two days",
                     expect="Schedule saved; the work shows in This period.",
                     if_wrong="End cannot be before start.",
                     shot="c11-set-dates.png", endpoint="schedule.new_item"),
                Step(title="Assign the crew", app=O, where="Calendar → Project dates in this period → the project → Edit dates → Assigned",
                     do="Choose Crew, press Assign",
                     enter="Pool deck crew (training) <initials>",
                     expect="Assignment saved; the crew is listed under Assigned. Kevin and Liam see it on Field.",
                     if_wrong="Unassigned is valid but nobody sees it on Field.",
                     shot="c11-assign-crew.png", endpoint="schedule.edit_item"),
            ),
            exercise=f"On {JOB}: add 'Pool deck framing and decking (training) <initials>' with the activity 'Framing and "
                     "decking (training)', both as original work, set it for today to two days from now, and assign "
                     "your Pool deck crew. Then place the BMR concrete order (module 8, last lesson).",
        ),
        Lesson(
            key="c11-field-today", title="Your job on Field Today",
            what="Find today's job, its address and the delivery, and confirm the project.",
            why="Confirming the project makes sure photos, notes and time go to the right job.",
            roles=OWNER_FIELD,
            steps=(
                Step(title="Read My Work", app=F, where="Field → Today",
                     do="Read the card",
                     expect="Harbour Lane Pool Deck (training), 14 Harbour Lane Merrickville, ON, Directions, the work and "
                            "your crew, Enter time. No prices.",
                     if_wrong="Not there? The office has not scheduled your crew today.",
                     shot="c11-field-today.png", endpoint="field.today"),
                Step(title="Today's delivery", app=F, where="Field → Today → My Work",
                     do="Read the Delivery line",
                     expect="Delivery: Concrete · BMR Winchester (training) · Harbour Lane Pool Deck (training) · 7:00–9:00 · Agreed.",
                     if_wrong="Questions about the delivery go to the office; the order is theirs.",
                     shot="c11-field-delivery.png", endpoint="field.today"),
                Step(title="Choose the project", app=F, where="Field → Today → Choose Project",
                     do="Tap Harbour Lane Pool Deck (training)",
                     expect="Projects lists only your scheduled jobs.",
                     if_wrong="Choose a different Project if you picked the wrong one.",
                     shot="c11-field-projects.png", endpoint="field.projects"),
                Step(title="Confirm it", app=F, where="Confirm Project",
                     do="Tap Confirm for Today (or Confirm and Capture / Confirm and Time)",
                     expect="Today shows the job with Capture, Time, Extra work, My time and Change project.",
                     if_wrong="Change project switches jobs.",
                     shot="c11-field-confirm.png", endpoint="field.project_confirm"),
            ),
            exercise="When you are scheduled on Harbour Lane, open Today on your iPhone, read the concrete delivery line, "
                     "and confirm Harbour Lane Pool Deck (training) for today.",
        ),
        Lesson(
            key="c11-capture", title="Photos and notes (Capture)",
            what="Save a note and a photo from the site.",
            why="A field note is evidence of what happened; the office sees it under Field Observations.",
            roles=OWNER_FIELD,
            steps=(
                Step(title="Open Capture", app=F, where="Field → Today → Capture (or Confirm and Capture)",
                     do="Type in Notes; tap Take Photo (camera) or Choose Photo (library); Record for a voice note",
                     enter="Ledger and joists in on the north side. Pool coping protected with plywood. (training)",
                     expect="The photo is listed under the buttons.",
                     if_wrong="Allow Safari to use the camera and microphone when the iPhone asks.",
                     shot="c11-capture.png", endpoint="field.capture"),
                Step(title="Save", app=F, where="Capture",
                     do="Tap Save original",
                     expect="Saved. With no signal: 'Saved on this phone — will sync when connected'.",
                     if_wrong="'Add a photo, recording, or note before saving.' Do not sign out while Pending on this phone.",
                     shot="c11-capture-saved.png", endpoint="field.capture"),
            ),
            exercise="On Harbour Lane, capture a note and a photo of the framing (any photo will do on the training site) "
                     "and wait for Saved.",
        ),
        Lesson(
            key="c11-extra-work", title="Extra work the customer asks for",
            what="Record extra work on Field when the customer asks for something outside the job.",
            why="If the customer asks you to add, remove, move or change something outside the work you were sent to do, "
                "use Extra work, so the office can price it as a change order before it is invoiced.",
            roles=OWNER_FIELD,
            steps=(
                Step(title="Open Extra work", app=F, where="Field → Today → Extra work",
                     do="Type What did the customer ask for?, choose New work item and type its name",
                     enter="Morgan asked for two extra steps down to the lawn on the east side. (training); New work item "
                           "name: Extra steps to the lawn (training)",
                     expect="The form shows the rule about extra work.",
                     if_wrong="Do not promise a price on site; the office prices it.",
                     shot="c11-extra-work.png", endpoint="field.extra_work"),
                Step(title="Record it", app=F, where="Extra work",
                     do="Tap Record extra work",
                     expect="Extra work recorded; you are back on Today.",
                     if_wrong="'Describe the extra work' means the box was empty.",
                     shot="c11-extra-work-recorded.png", endpoint="field.today"),
            ),
            exercise="Record Morgan's request for two extra steps to the lawn as extra work on Harbour Lane.",
        ),
        Lesson(
            key="c11-field-time", title="Send your time",
            what="Send your hours for the work you did today.",
            why="The office approves time against the job's work; nothing is paid from a guess.",
            roles=OWNER_FIELD,
            steps=(
                Step(title="Enter time", app=F, where="Field → Today → Enter time (or Time)",
                     do="Tap the scheduled work button, or Choose different work and pick Work item and Work; type Hours and Note",
                     enter="Pool deck framing and decking (training) — Framing and decking (training); Hours 8; Note: "
                           "Ledger and joists, north side (training)",
                     expect="Date, the work, Hours, Note and Send time.",
                     if_wrong="+ Extra work is for time on extra work the customer asked for.",
                     shot="c11-time.png", endpoint="field.time_entry"),
                Step(title="Send it", app=F, where="Time",
                     do="Tap Send time",
                     expect="Time sent for approval; My time lists it as submitted.",
                     if_wrong="If the office returns it, My time shows Fix and send again.",
                     shot="c11-time-sent.png", endpoint="field.my_time"),
            ),
            exercise="Send 8 hours on Harbour Lane framing for today with a short note, and find it in My time.",
        ),
        Lesson(
            key="c11-office-review", title="The office: field notes, time and the delivery",
            what="See the crew's notes, approve their time and mark the concrete delivered.",
            why="The office checks what Field sent before it counts.",
            roles=OFFICE,
            steps=(
                Step(title="Field Observations", app=O, where=f"{HUB} → PROJECT WORK → Field Observations",
                     do="Open the newest observation",
                     expect="Kevin's note and photo with the time it was taken.",
                     if_wrong="Add text observation adds an office note.",
                     shot="c11-field-observations.png", endpoint="projects.view_project"),
                Step(title="Time review", app=O, where=f"{HUB} → Time → Review time",
                     do="Open Kevin's entry",
                     expect="Time review lists Kevin Field (training crew), 8.00 hours.",
                     if_wrong="Filter by worker, project and status.",
                     shot="c11-time-review.png", endpoint="time_entry.review"),
                Step(title="Approve or return", app=O, where="The time entry",
                     do="Press Approve (or type a Return reason and press Return)",
                     expect="Approved; it shows in History.",
                     if_wrong="Correct approved time is there if a mistake is found later.",
                     shot="c11-time-approve.png", endpoint="time_entry.detail"),
                Step(title="Mark the concrete delivered", app=O, where=f"{HUB} → Supplier requests, concrete and orders → Mark delivered",
                     do="Open Mark delivered, check Delivered on, type a Note, press Mark delivered",
                     enter="Poured at the equipment pad (training)",
                     expect="'Order PO-… marked delivered.'",
                     if_wrong="Delivered on cannot be in the future.",
                     shot="c11-mark-delivered.png", endpoint="supplier_office.project_requests"),
            ),
            exercise="On Harbour Lane: read the crew's field note, approve the 8 hours, and mark the BMR concrete delivered.",
        ),
        Lesson(
            key="c11-change-order", title="Turn extra work into a change order",
            what="Make, price and approve the change order for the extra steps.",
            why="Extra work becomes billable only as an approved change order; the customer agrees to it in writing.",
            roles=OFFICE,
            steps=(
                Step(title="See the extra work", app=O, where=f"{HUB} → Open project work",
                     do="Find the extra work the crew recorded",
                     expect="Extra steps to the lawn (training) is listed as a work item.",
                     if_wrong="Nothing there? Ask the crew to use Extra work on Field.",
                     shot="c11-extra-work-office.png", endpoint="work_structure.project_work_plan"),
                Step(title="New Change Order", app=O, where=f"{HUB} → New Change Order",
                     do="Type Title, Requested by, Requested date, Description and Reason; press Create Change Order",
                     enter="Title: Extra steps to the lawn (training) <initials>; Requested by: Morgan Ellis (training)",
                     expect="Change order created. Tax % is filled from the project's proposal.",
                     if_wrong="Status starts as Draft; leave it until the line is in.",
                     shot="c11-change-order-form.png", endpoint="project_controls.create_change_order_route"),
                Step(title="Add the line", app=O, where="The change order → Items → Add Line Item",
                     do="Type Description, Quantity, Unit, Unit price; press Add Item",
                     enter="Two extra steps to the lawn, composite, supplied and installed (training); 1; ls; 850",
                     expect="The line is listed; the change order total is $850.00 before HST.",
                     if_wrong="Edit beside a line to change it.",
                     shot="c11-change-order-item.png", endpoint="project_controls.view_change_order"),
                Step(title="Approve", app=O, where="The change order → Update status",
                     do="Choose Approved, press Save Status (once Morgan has agreed in writing)",
                     expect="Status set to \"Approved\". Office Approved is not a customer signature; Send for E-Signature "
                            "(CaliSIGN) asks Morgan to sign.",
                     if_wrong="Rejected or Cancelled if she says no.",
                     shot="c11-change-order-approve.png", endpoint="project_controls.view_change_order"),
            ),
            exercise="Make the Harbour Lane change order 'Extra steps to the lawn (training) <initials>' for $850.00, set "
                     "it to Approved, then invoice it (module 4: Invoice the change order, $960.50 with HST).",
        ),
    ),
)

# ====================================================================================== 12
M12 = Module(
    key="c12", pathway=P, number=12, title="Running a complete working day and final acceptance",
    summary="Ben's First Day step 16: the morning in the office, the crew's day on Field, the final invoice, Getting "
            "started 16 of 16, closing the job, and your acceptance tests.",
    roles=TEAM,
    lessons=(
        Lesson(
            key="c12-morning", title="The morning in the office",
            what="Start the day from Home: today's work, what needs attention, deliveries and time.",
            why="Home is where the day starts: read today, then open a job.",
            roles=OFFICE,
            steps=(
                Step(title="Read Home", app=O, where="Home",
                     do="Read TODAY and COMING DAYS",
                     expect="Harbour Lane Pool Deck (training) with the crew; the coming days.",
                     if_wrong="Open Company Calendar for the month.",
                     shot="c12-home-morning.png", endpoint="main.dashboard"),
                Step(title="On the phone", app=O, where="Home on your iPhone (Safari)",
                     do="Open the office address on the phone",
                     expect="The same Home, fitted to the phone.",
                     if_wrong="Office people sign in to the office on the phone; crew get Field.",
                     shot="c12-home-phone.png", endpoint="main.dashboard"),
                Step(title="Deliveries and time", app=O, where="/deliveries; the hub → Review time",
                     do="Check today's deliveries and any time waiting for review",
                     expect="Today's BMR delivery and Kevin's time.",
                     if_wrong="Change a delivery on its request page.",
                     shot="c08-deliveries-office.png", endpoint="supplier_office.deliveries"),
            ),
            exercise="Start a training day from Home: find Harbour Lane under TODAY, check the BMR delivery and the time "
                     "waiting for review.",
        ),
        Lesson(
            key="c12-field-day", title="A working day on Field",
            what="Do a whole day on Field: Today, confirm, capture, extra work if asked, time.",
            why="Everything the office needs from the site comes from these few taps.",
            roles=OWNER_FIELD,
            steps=(
                Step(title="Morning", app=F, where="The Calibrayt icon → Today",
                     do="Read My Work and the delivery; tap Directions if needed",
                     expect="Today's job, address, crew and delivery.",
                     if_wrong="Nothing scheduled? Call the office.",
                     shot="c12-field-day.png", endpoint="field.today"),
                Step(title="During the day", app=F, where="Today → Capture",
                     do="Save notes and photos as the work goes",
                     expect="Saved after each one.",
                     if_wrong="No signal: it waits on the phone and sends later.",
                     shot="c11-capture.png", endpoint="field.capture"),
                Step(title="End of the day", app=F, where="Today → Enter time",
                     do="Send your hours, then check My time",
                     expect="Time sent for approval.",
                     if_wrong="Returned time shows Fix and send again.",
                     shot="c11-my-time.png", endpoint="field.my_time"),
            ),
            exercise="On a training day on Harbour Lane: confirm the project, save one note with a photo, and send your "
                     "hours, all from the Home Screen icon.",
        ),
        Lesson(
            key="c12-invoice-closeout", title="The final invoice and the books",
            what="Make the final invoice and send the invoices to QuickBooks.",
            why="The final invoice is what is left of the accepted proposal; the change order was invoiced on its own.",
            roles=OFFICE,
            steps=(
                Step(title="Check the money tab", app=O, where=f"{HUB} → MONEY",
                     do="Read Estimated versus actual and any actual direct costs",
                     expect="The committed estimate against actual costs entered in the office. It is not a profit figure.",
                     if_wrong="Field notes are not actual costs.",
                     shot="c12-hub-money.png", endpoint="projects.view_project"),
                Step(title="Final invoice", app=O, where=f"{HUB} → Make an invoice",
                     do="Kind: Final, leave Percent and amount empty, press Make the invoice",
                     expect="'Invoice INV-… made: $12,312.41 with HST' (the rest of $15,565.63 after the 30 % deposit, plus HST).",
                     if_wrong="You cannot invoice more than the proposal.",
                     shot="c12-final-invoice.png", endpoint="accounting.new_invoice"),
                Step(title="Export", app=O, where="Company → Accounting → Invoices",
                     do="Press Download the file and import it in QuickBooks (module 4)",
                     expect="Only the new invoices are in the file.",
                     if_wrong="Include those again only with a reason.",
                     shot="c04-invoices.png", endpoint="accounting.invoices"),
            ),
            exercise="Make the Harbour Lane final invoice ($12,312.41 with HST) and download the Invoices file with it.",
        ),
        Lesson(
            key="c12-getting-started-done", title="Getting started: 16 of 16",
            what="Mark the working day done and see the whole checklist complete.",
            why="Getting started step 16: after one full day run through CalibraytAI, the set-up is complete.",
            roles=OWNER,
            steps=(
                Step(title="Mark the working day done", app=O, where="Company → Getting started → 16 Run a complete working day",
                     do="Press Mark done",
                     expect="16 of 16 steps done; All done. CalibraytAI is set up for Brayman Construction.",
                     if_wrong="An unticked step shows what is still missing; Go there opens it.",
                     shot="c12-getting-started-done.png", endpoint="getting_started.index"),
            ),
            exercise="After your Harbour Lane day, mark step 16 done and check how many of the 16 steps the training "
                     "company shows done.",
        ),
        Lesson(
            key="c12-close-project", title="Close (and reopen) the project",
            what="Close the finished job; reopen it if more work comes.",
            why="Closing takes the job out of current work. Its history stays. Only the owner closes and reopens.",
            roles=OWNER,
            steps=(
                Step(title="Close Project", app=O, where=f"{HUB} → Close Project (top of the page)",
                     do="Press Close Project",
                     expect="Close this Project? Closing removes this Project from current operating work. Historical "
                            "Project information remains available.",
                     if_wrong="Open Punch List items must be confirmed before closing; they stay open.",
                     shot="c12-close-confirm.png", endpoint="projects.close_project"),
                Step(title="Confirm", app=O, where="Close this Project?",
                     do="Press Close Project",
                     expect="This Project is closed. It is listed under Projects → Closed; Reopen Project is shown.",
                     if_wrong="Cancel leaves it open.",
                     shot="c12-closed.png", endpoint="projects.view_project"),
                Step(title="Reopen", app=O, where=f"{HUB} → Reopen Project",
                     do="Press Reopen Project, then Reopen Project to confirm",
                     expect="This Project is current.",
                     if_wrong="Office staff are not offered Close or Reopen.",
                     shot="c12-reopen-confirm.png", endpoint="projects.reopen_project"),
            ),
            exercise="When the trainer says Harbour Lane is finished, close it, find it under Projects → Closed, then "
                     "reopen it so the next trainee can use it.",
        ),
        Lesson(
            key="c12-final-acceptance", title="Final acceptance tests",
            what="Run the acceptance tests for your job and record Pass, Fail or Blocked.",
            why="Acceptance shows CalibraytAI does each job correctly before you rely on it. Tests are separate from "
                "training and never count as lessons.",
            steps=(
                Step(title="Open Acceptance tests", app=O, where="Training Centre → Acceptance tests",
                     do="Open the first test",
                     expect="Where to start, what to do and the expected result.",
                     if_wrong="Your tests follow your job; change role on the Training Centre home if needed.",
                     endpoint="training.uat"),
                Step(title="Run it and record the result", app=O, where="The test",
                     do="Do it on the training site, then choose Pass, Fail (say what went wrong) or Blocked, and save",
                     expect="Result saved; the next test you have not done opens (the list, after the last). A retest "
                            "after a fix (Retest beside the result) is a new attempt; the earlier ones stay.",
                     if_wrong="Fail needs a description: what you pressed and the words on the screen.",
                     endpoint="training.uat_case"),
            ),
            exercise="Run every acceptance test for your job on the training site and record each result.",
        ),
    ),
)

MODULES = (M01, M02, M03, M04, M05, M06, M07, M08, M09, M10, M11, M12)


def _u(key, module, title, start, action, expected, roles):
    return UatCase(key=key, pathway=P, module_key=module, title=title, start=start, action=action, expected=expected,
                   roles=roles)


UAT_CASES = (
    _u("uat-c01-sign-in", "c01", "Sign in and change the password", "The training site's sign-in page",
       "Sign in with your training email and password, then change the password (office: the key button at the top "
       "right; Field: the Password button at the top).",
       "You are signed in under your own name and the new password works the next time you sign in.", TEAM),
    _u("uat-c01-register", "c01", "Register for your job", "Training site → /training",
       "Sign in, choose your job and press Start my training.",
       "Only your job's lessons are listed; office staff do not get the owner's lessons.",
       TEAM),
    _u("uat-c02-people", "c02", "Add a Field-only person", "Company → People & Access",
       "Add a person with Field only ticked; press Add and email the link.",
       "The person is added, a set-password email is sent, and their page says Field only; Getting started step 5 is ticked.",
       OWNER),
    _u("uat-c02-pricing", "c02", "Company pricing with 13 % HST", "COSTS & PRICING → How we price",
       "Create a Gross Margin 0.20 draft with CA-ON 13 %, Approve (human), Use for this company.",
       "The policy shows Company default, '20% of the customer price is margin' and Tax 13.00%.", OWNER),
    _u("uat-c02-office-no-people", "c02", "Office staff cannot manage people", "Signed in as office staff, Home",
       "Look for People & Access in the menu, then type /settings/people.",
       "People & Access is not in the menu and the page is refused.", (ROLE_OFFICE,)),
    _u("uat-c03-activate", "c03", "Activate a worker's phone", "The invitation email on the worker's iPhone",
       "Open the link, choose a password, sign in, add the site to the Home Screen and open it from the icon.",
       "Field Today opens from the icon under the worker's name; the owner sees Can sign in on their record.",
       OWNER_FIELD),
    _u("uat-c03-phones-step", "c03", "Mark the phones step", "Company → Getting started → 6 Set up their iPhones",
       "Press Mark done.", "Step 6 shows done with your name; Undo beside it takes the mark away.", OWNER),
    _u("uat-c04-deposit", "c04", "Deposit invoice from the accepted proposal",
       "Harbour Lane Pool Deck (training) → Make an invoice",
       "Kind Deposit, 30 percent, Make the invoice.",
       "An invoice INV-… is made for 30 % of the proposal before HST plus 13 % ($5,276.75 with the 20 % policy).",
       OFFICE),
    _u("uat-c04-export", "c04", "Invoices file has no duplicates", "Company → Accounting → Invoices",
       "Download the file, then open Invoices again.",
       "The file lists the new invoice with HST ON; the second time the page says Nothing new.", OFFICE),
    _u("uat-c04-hours-policy", "c04", "Enter the company's hours policy", "Company → Getting started → 15 Hours and "
       "banked time → Go there",
       "Check every box is empty; fill in 40, 40, Banked, 1, Yes, Monday, this Monday; press Save hours policy.",
       "'Hours policy saved (version 1 …)'; the policy line reads 'Normal work week: 40.00 hours (Monday to Sunday). "
       "Hours after 40.00 in a week are banked …'; step 15 is ticked; Changes lists version 1 with your name.", OWNER),
    _u("uat-c04-qbt-approve", "c04", "Approved hours reach QuickBooks Time once", "Time review, with Kevin's hours "
       "Submitted (QuickBooks Time test connection)",
       "Tick Kevin's rows, press Approve selected; open QuickBooks Time transfers; press Send waiting and retry failed.",
       "'Sent to QuickBooks Time: N.'; each entry is In QuickBooks Time once; pressing Send again sends nothing more.",
       TEAM),
    _u("uat-c04-qbt-failed", "c04", "A failed transfer is shown and retried", "Accounting → QuickBooks Time transfers "
       "with a row Needs a link",
       "Add the missing link (owner), then press Retry on the row.",
       "The row showed what to do; after Retry it is In QuickBooks Time, and Check QuickBooks Time shows it once.", TEAM),
    _u("uat-c04-banked", "c04", "Banked hours, time off and correction", "Accounting → Banked hours → Kevin",
       "Record 2 hours of time off with a reason; then correct one of his approved entries down by 1 hour.",
       "The ledger shows Time off taken -2.00 and a difference row from the correction; Kevin sees the same balance on "
       "Field. You cannot adjust your own hours.", TEAM),
    _u("uat-c04-shop", "c04", "Shop / Company Work is never a customer job", "Hours policy (Company → Getting started → Hours and banked time) → Set up Shop / Company Work",
       "Approve a shop entry; look for Shop / Company Work in Projects, Clients, Cal (search 'shop') and New estimate.",
       "It is in none of them; its page is Accounting → Shop / Company Work with the hours by category.", TEAM),
    _u("uat-c04-check", "c04", "Check QuickBooks", "Company → Accounting → Check QuickBooks",
       "Upload a QuickBooks Invoice List CSV (sandbox) and press Check.",
       "Each invoice is shown as match, amount differs, exported but not in QuickBooks, in QuickBooks but not in "
       "CalibraytAI, or in QuickBooks more than once.", OFFICE),
    _u("uat-c05-appointments", "c05", "Company and personal appointments", "Calendar → + New Appointment",
       "Add a Company site visit and a Personal appointment for tomorrow.",
       "You see both; a colleague sees the company appointment on Company Calendar and never the personal one.", OFFICE),
    _u("uat-c05-feed", "c05", "Calendar on the phone", "Calendar → Outlook · Google · Apple Calendar",
       "Turn on my calendar feed and subscribe in Apple, Google or Outlook.",
       "The site visit appears in the phone's calendar; after Make a new address the old address stops.", OFFICE),
    _u("uat-c05-field-week", "c05", "The week on Field", "Field → This week",
       "Open This week and This month after the crew is scheduled.",
       "The scheduled Harbour Lane work shows on its days with the address; no prices or costs anywhere.", OWNER_FIELD),
    _u("uat-c06-project", "c06", "Customer and project ready", "Clients → Morgan Ellis (training)",
       "Check the client, open Harbour Lane Pool Deck (training) → Continue setup, complete the location.",
       "Setup says the client is in this company and the job location is complete; Getting started step 10 is ticked.",
       OFFICE),
    _u("uat-c06-hub", "c06", "Everything on the hub", "Projects → Harbour Lane Pool Deck (training)",
       "Press each tab PROJECT, SETTINGS, MONEY, DOCUMENTS, PROJECT WORK.",
       "Each tab jumps to its part: estimates, proposals and contract under DOCUMENTS; work, purchasing, time, change "
       "orders and Field Observations under PROJECT WORK.", OFFICE),
    _u("uat-c07-plan", "c07", "Plan uploaded and on Field", "Harbour Lane → Drawings → Upload PDF",
       "Upload a PDF plan; then a scheduled crew member opens Field → Choose Project → Harbour Lane → Drawings and plans.",
       "The plan is listed in Current drawings and opens on the crew member's phone.", TEAM),
    _u("uat-c07-calculator", "c07", "Concrete calculator", "CALCULATORS → Concrete calculator",
       "Standard slab, Feet and inches, 12 × 10 ft, 6 in, 5 % waste, Calculate concrete.",
       "Total concrete 2.333 yd3 (base 2.222, waste 0.111); nothing is added to an estimate.", OFFICE),
    _u("uat-c08-quote", "c08", "Concrete request and quote", "Harbour Lane → Supplier requests, concrete and orders",
       "Send 2.5 m³ 32 MPa to BMR Winchester (training); BMR returns $215.00/m³ + $75.00 short-load; Approve this quote.",
       "The quote shows $612.50 before tax and 'Concrete quote approved. Placing the order is a separate step.' BMR "
       "never sees Morgan's name or the customer price.", OFFICE),
    _u("uat-c08-order", "c08", "Purchase order confirmed", "The approved quote → order form",
       "Sign & Send for E-Signature for the first job day linked to the schedule; BMR presses Sign & Confirm Order.",
       "PO-… signed and sent, then Confirmed and Executed (both signatures) with the agreed date; it is on Deliveries; "
       "Getting started step 13 is ticked.",
       OFFICE),
    _u("uat-c09-estimate", "c09", "Estimate costed and priced", "Harbour Lane → New estimate",
       "Add the three lines, confirm Scope Delivery Review, Approve all costing, Apply org pricing policy.",
       "SUBTOTAL $12452.50; Customer total $17589.16 with the 20 % policy and 13 % HST; Getting started step 11 is ticked.",
       OFFICE),
    _u("uat-c09-block", "c09", "Costing waits for scope delivery", "A new estimate version with one line",
       "Press Approve all costing before confirming Scope Delivery Review.",
       "Costing is not approved and you are sent to confirm who provides the material and who does the work.", OFFICE),
    _u("uat-c10-accept", "c10", "Customer accepts on the phone", "The priced estimate version → Sign off estimate",
       "Send proposal to client; open the emailed link on a phone; tick, type Morgan Ellis (training), Accept Proposal.",
       "The customer page says Proposal accepted and shows no unit costs or markup; the office proposal says Accepted.",
       OFFICE),
    _u("uat-c10-contract", "c10", "Contract for review", "Harbour Lane → Review contract",
       "Press Generate contract.",
       "Contract status Generated — not signed, Brayman V1 Interim Contract, Ontario, the customer, project and amount; "
       "no signing link is sent.", OFFICE),
    _u("uat-c11-field", "c11", "Kevin's day on Field", "Field → Today on the crew member's iPhone",
       "Confirm Harbour Lane, Capture a note and photo, Record extra work, Enter time 8 hours, Send time.",
       "Saved, Extra work recorded and Time sent for approval; no prices anywhere on Field.", OWNER_FIELD),
    _u("uat-c11-delivery-field", "c11", "The delivery on Field", "Field → Today on a day with a BMR delivery",
       "Read My Work.", "A Delivery line shows Concrete · BMR Winchester (training), the window and its status.",
       OWNER_FIELD),
    _u("uat-c11-schedule", "c11", "Crew scheduled", "Calendar → Set dates",
       "Set dates for the Harbour Lane work item and assign the Pool deck crew.",
       "Assignment saved; the crew's members see the job on Field Today; Getting started step 14 is ticked.", OFFICE),
    _u("uat-c11-change-order", "c11", "Extra work to an approved change order", "Harbour Lane → New Change Order",
       "Create 'Extra steps to the lawn', add a $850 line, set Approved, then Make an invoice → Invoice the change order.",
       "Status Approved; the invoice is $960.50 with HST and the change order cannot be invoiced twice.", OFFICE),
    _u("uat-c12-day", "c12", "A complete working day", "Home in the morning",
       "Run the day: Home, the crew's Field day, approve time, mark the delivery, final invoice, export.",
       "Every step completes without an error; the final invoice is $12,312.41 with HST; the Invoices file has only "
       "new invoices.", OFFICE),
    _u("uat-c12-field-day", "c12", "A working day on Field", "The Calibrayt icon on the iPhone",
       "Open Today, confirm the job, capture, send time, check My time.",
       "Everything sends (Saved; Time sent for approval) and My time lists the day.", OWNER_FIELD),
    _u("uat-c12-close", "c12", "Close and reopen", "Harbour Lane → Close Project",
       "Close the project, find it under Projects → Closed, reopen it; then sign in as office staff and look for Close Project.",
       "This Project is closed, then This Project is current; office staff are not offered Close Project.", OWNER),
    _u("uat-c12-getting-started", "c12", "Getting started complete", "Company → Getting started",
       "Mark 16 Run a complete working day done.", "16 of 16 and All done.", OWNER),
)
