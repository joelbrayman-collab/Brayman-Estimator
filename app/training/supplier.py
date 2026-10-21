"""Supplier training: 10 modules for supplier owners, administrators and PRO Desk staff (Joel, 21 Oct 2026).

Example: BMR Winchester (training), Darcy at the store and Pat at the PRO Desk, following the same
Harbour Lane Pool Deck job from the supplier's side. BMR sells concrete to the contractor; Tomlinson
Ready-Mix supplies it to BMR upstream (Tomlinson is not a party in CalibraytAI).

What CalibraytAI does today, taught as it is:
- There is no separate supplier administrator or PRO Desk permission. Every active supplier user of a store
  has the same access. The contractor's office adds and removes supplier users (Company → Suppliers).
- The Centre's roles only choose the lessons: PRO Desk staff get the basics and the PRO Desk lessons;
  supplier owners and administrators get everything.
- Concrete requests are separate from material requests.
- Prices on a contractor request are typed on each quote. The PRO Desk prices only from the store's own
  price file (a CSV); there is no screen to edit one product or price, and no link to the store's own system.

Screenshots: tools/training/capture_supplier_shots.mjs (real pages on the local training site).
"""

from app.models.training import PATHWAY_SUPPLIER as P
from app.training.content import (
    ALL_SUPPLIER,
    APP_CUSTOMER,
    APP_EMAIL,
    APP_OFFICE,
    APP_PRO_DESK,
    APP_SUPPLIER,
    SUPPLIER_DESK,
    Lesson,
    Module,
    Step,
    UatCase,
)

STORE = "Supplier Hub → your store's page (BMR Winchester (training))"
PRO_DESK = "Supplier Hub → your store's page → PRO Desk quotations"
REQUESTS_OFFICE = "Projects → Harbour Lane Pool Deck (training) → Purchasing → Supplier requests, concrete and orders"

MODULES = (
    # ------------------------------------------------------------------ 1
    Module(
        key="s01", pathway=P, number=1, title="Welcome, registration and supplier sign-in",
        summary="Sign in to the Supplier Hub, register for training, and get back in if you forget your password.",
        roles=ALL_SUPPLIER,
        lessons=(
            Lesson(
                key="s01-sign-in", title="Sign in to the Supplier Hub",
                what="Open the Training Centre, sign in with the supplier sign-in and open your store's page.",
                why="The Supplier Hub is where your contractors' requests, orders and deliveries arrive. Store staff "
                    "have their own sign-in, separate from the contractor's office.",
                steps=(
                    Step(title="Open the Training Centre", app=APP_SUPPLIER,
                         where="The training site address from your invitation (Welcome to CalibraytAI training)",
                         do="Press I work for a building supplier",
                         expect="The Supplier sign-in page opens.",
                         if_wrong="If the page says Not Found, check the address with the person who invited you: "
                                  "the Training Centre is only on the training site.",
                         endpoint="training.signin", shot="s1-training-signin.png"),
                    Step(title="Sign in", app=APP_SUPPLIER, where="Supplier sign-in",
                         do="Type your Email and Password, then press Sign in",
                         enter="Your email (Darcy: darcy@training.calibraytai.invalid) and the password from your invitation",
                         expect="You come back to the Training Centre. The first time, it asks which job you do.",
                         if_wrong="'The email or password is not correct, or this is not a supplier sign-in': check the "
                                  "email letter by letter. A contractor's office email cannot sign in here. If the "
                                  "password does not work, press Forgot your password? (next lesson).",
                         why="The eye button in the Password box shows what you typed.",
                         endpoint="supplier_portal.login", shot="s1-supplier-sign-in.png"),
                    Step(title="The same sign-in on your phone", app=APP_SUPPLIER,
                         where="The training site address on your phone's browser, then Supplier sign-in",
                         do="Sign in the same way; add the page to your home screen if you like",
                         expect="The same page, sized for the phone. Everything in the Supplier Hub works on a phone.",
                         if_wrong="If the page is too small, make sure you opened it in the phone's browser, not an "
                                  "email preview.",
                         endpoint="supplier_portal.login", shot="s1-supplier-sign-in-phone.png"),
                    Step(title="Open your store's page", app=APP_SUPPLIER,
                         where="Supplier Hub (the address ending /supplier/, or your store's name at the top left)",
                         do="Press your store's name at the top left",
                         expect="BMR Winchester (training) opens: the buttons PRO Desk quotations, Deliveries, Dashboard "
                                "and Material demand, then Needs attention and Requests. With one store you go straight here.",
                         if_wrong="'You are not linked to a supplier yet': the contractor's office has not given you a "
                                  "Supplier Hub sign-in for a store. Ask them (Company → Suppliers).",
                         endpoint="supplier_portal.home", shot="s3-inbox.png"),
                    Step(title="Sign out when you leave the counter", app=APP_SUPPLIER,
                         where="Top right of any Supplier Hub page", do="Press Sign out",
                         expect="The Supplier sign-in page opens. On a shared counter computer, always sign out.",
                         if_wrong="If you closed the browser instead, CalibraytAI signs you out after a period without use.",
                         endpoint="supplier_portal.logout"),
                ),
                exercise="Sign in to the training site as yourself, open BMR Winchester (training), sign out, and sign "
                         "in again on your phone.",
            ),
            Lesson(
                key="s01-register", title="Register for training and find your way",
                what="Choose the job you do, then learn the Training Centre's buttons.",
                why="Your role chooses your lessons and acceptance tests. It does not change what you may do in the "
                    "Supplier Hub: every active user of a store has the same access.",
                steps=(
                    Step(title="Choose the job you do", app=APP_SUPPLIER,
                         where="Training Centre → Welcome, <your name> (first visit only)",
                         do="Choose Supplier owner, Supplier administrator or PRO Desk staff, then press Start my training",
                         enter="Darcy: Supplier owner. Pat: PRO Desk staff",
                         expect="Your training home opens with 'Supplier training · <your role>'.",
                         if_wrong="If you chose the wrong job, open Change my role at the bottom of the training home "
                                  "and press Change role (keeps my progress).",
                         why="Owners and administrators get every lesson; PRO Desk staff get the basics and the PRO Desk "
                             "lessons.",
                         endpoint="training.home", shot="s1-register.png"),
                    Step(title="Read your training home", app=APP_SUPPLIER, where="Training Centre (your training home)",
                         do="Look at the progress line, then press Continue where I left off",
                         expect="The progress bar, 'N of M lessons done', Acceptance tests and your modules. Continue "
                                "where I left off opens the next lesson at the step you reached.",
                         if_wrong="If no modules show, you are not registered yet: go back to the training address.",
                         endpoint="training.home", shot="s1-training-home.png"),
                    Step(title="What PRO Desk staff see", app=APP_PRO_DESK, where="Training Centre (Pat's training home)",
                         do="Compare Pat's modules with Darcy's",
                         expect="Pat has the basics and the PRO Desk modules; the contractor-order modules are left out.",
                         if_wrong="If a PRO Desk person needs the contractor lessons too, change their role to Supplier "
                                  "administrator. Their Supplier Hub access does not change.",
                         endpoint="training.home", shot="s1-training-home-pro-desk.png"),
                    Step(title="Move through a lesson", app=APP_SUPPLIER, where="Any lesson",
                         do="Do each step and press I did this step under it (it turns green); press Save and exit to stop; "
                            "tick I did the practice exercise on the training site, then press Finish this lesson",
                         expect="Each ticked step shows a green check and is saved at once. Finish this lesson marks it "
                                "Done on your training home.",
                         if_wrong="Finish this lesson refuses until every step and the practice exercise are ticked. "
                                  "Use Save note for anything unclear.",
                         endpoint="training.lesson"),
                ),
                exercise="Register with your own job, open the first lesson, press Save and exit, then use Continue "
                         "where I left off to come back to the same step.",
            ),
            Lesson(
                key="s01-password", title="Forgot your password, or want a new one",
                what="Get a password link by email and choose a new password.",
                why="The Supplier Hub has no change-password page. Forgot your password? is how a supplier user sets "
                    "a new password, and how a new user chooses the first one.",
                steps=(
                    Step(title="Ask for a password link", app=APP_SUPPLIER,
                         where="Supplier sign-in → Forgot your password?",
                         do="Type your Email address, then press Send Reset Instructions",
                         enter="Your supplier email",
                         expect="A page says the instructions were sent. For safety it says the same even if the email "
                                "is not known.",
                         if_wrong="No email after a few minutes: check junk mail, then ask the contractor's office to "
                                  "check your email on Company → Suppliers.",
                         endpoint="auth.forgot_password", shot="s1-forgot-password.png"),
                    Step(title="Open the email", app=APP_EMAIL, where="Your inbox: 'Reset your CalibraytAI password'",
                         do="Press the link in the email",
                         expect="The Set New Password page opens.",
                         if_wrong="'Reset link unavailable': the link was used or is too old. Ask for a new one.",
                         endpoint="auth.reset_password"),
                    Step(title="Choose the new password", app=APP_SUPPLIER, where="Set New Password",
                         do="Type it in New Password and Confirm New Password, then press Reset Password",
                         enter="A password only you know",
                         expect="'Password Updated'. Sign in again on the supplier sign-in page with the new password.",
                         if_wrong="If it refuses the password, it says why (for example too short or not matching): "
                                  "type a longer one in both boxes.",
                         endpoint="auth.reset_password"),
                ),
                exercise="On the training site, ask for a password link for your training email and look at the page "
                         "that confirms it was sent.",
            ),
        ),
    ),
    # ------------------------------------------------------------------ 2
    Module(
        key="s02", pathway=P, number=2, title="Store setup, users and permissions",
        summary="Who can sign in for your store, who controls it, your store's branding and your text messages.",
        roles=ALL_SUPPLIER,
        lessons=(
            Lesson(
                key="s02-users", title="Who can sign in for your store",
                what="See how store people get, share and lose their Supplier Hub sign-in.",
                why="CalibraytAI has no supplier administrator screen. The contractor who works with your store adds "
                    "and removes your users, and every active user has the same access.",
                steps=(
                    Step(title="The contractor adds a store person", app=APP_OFFICE,
                         where="Company → Suppliers → BMR Winchester (training)",
                         do="The contractor types the person's Name and Email and presses Give Supplier Hub sign-in",
                         enter="For example: Pat at the PRO Desk (BMR Winchester, training), pat@training.calibraytai.invalid",
                         expect="'<name> can now sign in to the Supplier Hub. A link to choose a password was emailed to "
                                "<email>.' The person is listed with 'can sign in'.",
                         if_wrong="'This email belongs to an office user. A person cannot be both office and supplier.': "
                                  "the store person needs an email that is not used in the contractor's office.",
                         why="On the training site Darcy and Pat are already listed; you do not need to add anyone.",
                         endpoint="supplier_office.suppliers", shot="s2-office-suppliers.png"),
                    Step(title="The new person chooses a password", app=APP_EMAIL,
                         where="The new person's inbox: 'Reset your CalibraytAI password'",
                         do="Press the link and choose a password on Set New Password",
                         expect="They can sign in on the supplier sign-in page.",
                         if_wrong="If the link is too old, use Forgot your password? on the supplier sign-in page.",
                         endpoint="auth.reset_password"),
                    Step(title="Everyone at the store has the same access", app=APP_SUPPLIER, where=STORE,
                         do="Sign in as Darcy, then as Pat, and open the same request",
                         expect="Both see the same requests, orders, deliveries, Dashboard, Material demand and PRO Desk. "
                                "There is no separate administrator or PRO Desk permission.",
                         if_wrong="If one person sees nothing, their sign-in may have been removed: ask the contractor's "
                                  "office to check Company → Suppliers.",
                         endpoint="supplier_portal.inbox", shot="s3-inbox-requests.png"),
                    Step(title="Someone leaves the store", app=APP_OFFICE,
                         where="Company → Suppliers → BMR Winchester (training)",
                         do="Ask the contractor's office to press Remove sign-in next to the person",
                         expect="'Supplier sign-in removed.' The person shows as 'removed' and can no longer sign in. "
                                "Giving the sign-in again restores it.",
                         if_wrong="Only the contractor's office can do this. Phone them the same day someone leaves.",
                         endpoint="supplier_office.suppliers"),
                ),
                exercise="Sign in as Darcy and as Pat (each with their own training password) and check that both see "
                         "the same Harbour Lane requests.",
            ),
            Lesson(
                key="s02-branding", title="Your store's name, logo and colour",
                what="See where your store's branding is set and where it shows.",
                why="The Supplier Hub and your PRO Desk quotations show your store's name, logo and colour, so "
                    "customers and staff know whose page it is.",
                roles=SUPPLIER_DESK,
                steps=(
                    Step(title="Branding is saved by the contractor's office", app=APP_OFFICE,
                         where="Company → Suppliers → BMR Winchester (training) → Branding in the Supplier Hub",
                         do="Send the office your logo file; they fill Name shown, Main colour and Logo and press Save branding",
                         enter="For example Main colour #1F4E8C and the store's own PNG or JPEG logo (up to 2 MB)",
                         expect="'Branding saved. BMR Winchester (training)'s Supplier Hub area now shows it.'",
                         if_wrong="Use your store's own logo file. A colour must look like #1F4E8C.",
                         endpoint="supplier_office.suppliers", shot="s2-office-branding.png"),
                    Step(title="Where it shows", app=APP_SUPPLIER, where="The top bar of every Supplier Hub page",
                         do="Sign in and look at the top bar",
                         expect="Your name shown, logo and colour, with 'Supplier Hub' under it. PRO Desk quotation PDFs "
                                "use the same logo and colour.",
                         if_wrong="If it still shows the old name, sign out and in again.",
                         endpoint="supplier_portal.inbox"),
                ),
                exercise="Find your store's name in the top bar of the Supplier Hub on the training site.",
            ),
            Lesson(
                key="s02-texts", title="Text messages for orders and delivery changes",
                what="Add your mobile number for texts, and up to two more people at the store.",
                why="When a contractor places an order or asks to move a delivery, you get an email and, if you agree, "
                    "a text with a link to answer.",
                steps=(
                    Step(title="Open Text settings", app=APP_SUPPLIER, where="Top right of any Supplier Hub page",
                         do="Press your name",
                         expect="The Text settings page opens.",
                         if_wrong="If your name is not shown, you are signed out: sign in again.",
                         endpoint="supplier_portal.account", shot="s2-text-settings-phone.png"),
                    Step(title="Your mobile", app=APP_SUPPLIER, where="Text settings → Your mobile",
                         do="Type your Mobile number, tick Text me delivery updates, then press Save",
                         enter="613-555-0100 (training)",
                         expect="'Text settings saved.' and 'Texts on since <date>'. Email notices continue as well.",
                         if_wrong="If the number is refused, type it with the area code, like 613-555-0100. Untick the "
                                  "box any time to stop texts. The training site does not send real texts.",
                         endpoint="supplier_portal.account"),
                    Step(title="Also text someone who does not sign in", app=APP_SUPPLIER,
                         where="Text settings → Also text someone at BMR Winchester (training) (optional)",
                         do="Type Name and Mobile number, tick This person agreed to receive these texts., press Add number",
                         enter="For example the yard foreman (training), 613-555-0101",
                         expect="'Number added. They will get the same delivery texts as you.' Up to two numbers; "
                                "Remove takes one off.",
                         if_wrong="Ask the person first: the box confirming their agreement is required.",
                         endpoint="supplier_portal.account"),
                ),
                exercise="On the training site, save a training mobile number for yourself with texts on, then untick "
                         "texts and save again.",
            ),
        ),
    ),
    # ------------------------------------------------------------------ 3
    Module(
        key="s03", pathway=P, number=3, title="Supplier Hub dashboard",
        summary="Your store's page (Needs attention and Requests) and the Dashboard's measured figures.",
        roles=ALL_SUPPLIER,
        lessons=(
            Lesson(
                key="s03-store-page", title="Your store's page: Needs attention and Requests",
                what="Read the four Needs attention boxes and the Requests table, on the computer and the phone.",
                why="It is the first thing to check each morning: quotes to answer, orders to confirm, delivery "
                    "changes to answer and the next deliveries.",
                steps=(
                    Step(title="Needs attention", app=APP_SUPPLIER, where=STORE,
                         do="Read the four boxes under Needs attention",
                         expect="Quotes to answer, Orders to confirm, Delivery changes to answer, Deliveries in the next "
                                "14 days. Each lists the request or order numbers; press one to open it.",
                         if_wrong="'Nothing waiting for <store> right now.' means there is nothing to do.",
                         why="A new request is not emailed: it appears here. Orders and delivery changes are also emailed "
                             "(and texted, if you turned texts on).",
                         endpoint="supplier_portal.inbox", shot="s3-inbox.png"),
                    Step(title="The Requests table", app=APP_SUPPLIER, where=STORE + " → Requests",
                         do="Read each row",
                         expect="Request (SRQ-…), From (the contractor and who sent it), Type (Concrete, or Materials with "
                                "the number of lines), Needed by, Delivery town, Status (New, Opened, Quote returned, "
                                "Replaced by a newer request) and Order (PO-… and its state).",
                         if_wrong="If a request you expected is missing, the contractor may have withdrawn it. Ask them.",
                         endpoint="supplier_portal.inbox", shot="s3-inbox-requests.png"),
                    Step(title="The same page on your phone", app=APP_SUPPLIER, where=STORE + " (on the phone)",
                         do="Scroll down the page",
                         expect="Each request becomes a card with the same details; nothing scrolls sideways.",
                         if_wrong="Turn the phone upright and reload the page.",
                         endpoint="supplier_portal.inbox", shot="s3-inbox-phone.png"),
                    Step(title="The page buttons", app=APP_SUPPLIER, where=STORE + " (top right)",
                         do="Find PRO Desk quotations, Deliveries, Dashboard and Material demand",
                         expect="Each opens its page; Back to requests (or your store's name) brings you back here.",
                         if_wrong="On a phone the buttons are above Needs attention: scroll to the top.",
                         endpoint="supplier_portal.inbox"),
                ),
                exercise="Open BMR Winchester (training) and write down the Harbour Lane request numbers and their "
                         "Status, on the computer and on your phone.",
            ),
            Lesson(
                key="s03-dashboard", title="Read the Dashboard",
                what="Choose a period and read the measured figures for your store.",
                why="It shows how many quotes you answered, how many became orders and the order value, from the "
                    "records only. Nothing is estimated.",
                roles=SUPPLIER_DESK,
                steps=(
                    Step(title="Open the Dashboard", app=APP_SUPPLIER, where=STORE + " → Dashboard",
                         do="Press Dashboard",
                         expect="Dashboard: Needs attention again, then the figures for the chosen period, the All-time "
                                "record and Contractors who sent requests.",
                         if_wrong="If the figures are all 0, choose a longer period (next step).",
                         endpoint="supplier_portal.supplier_dashboard", shot="s3-dashboard.png"),
                    Step(title="Choose the period", app=APP_SUPPLIER, where="Dashboard → Period",
                         do="Choose This week, This month, Last 90 days, All time or Custom dates, then press Show",
                         enter="This month (Custom dates also asks From and To)",
                         expect="The heading shows the period and its dates (Eastern time); the tiles change.",
                         if_wrong="With Custom dates, both From and To are needed.",
                         endpoint="supplier_portal.supplier_dashboard", shot="s3-dashboard-figures.png"),
                    Step(title="What each tile means", app=APP_SUPPLIER, where="Dashboard → the tiles",
                         do="Read Quote requests received, Quotes returned, Quote-to-order conversion, Orders placed with "
                            "you, Average recorded order value, Measured quotation effort, Deliveries in the next 14 days",
                         expect="Conversion shows 'N of M' until there are enough returned quotes for a percentage. "
                                "Order values are purchase orders before tax, not invoiced sales. Effort is the minutes "
                                "your staff typed when returning quotes.",
                         if_wrong="Whether an order was invoiced or paid is in your own store system, not here.",
                         endpoint="supplier_portal.supplier_dashboard"),
                    Step(title="On your phone", app=APP_SUPPLIER, where="Dashboard (on the phone)",
                         do="Scroll through the tiles",
                         expect="The same figures, one under the other.",
                         if_wrong="Reload the page if a tile looks cut off.",
                         endpoint="supplier_portal.supplier_dashboard", shot="s3-dashboard-phone.png"),
                ),
                exercise="Open the Dashboard for This month and for All time, and say how many quotes BMR Winchester "
                         "(training) returned and how many orders were placed.",
            ),
        ),
    ),
    # ------------------------------------------------------------------ 4
    Module(
        key="s04", pathway=P, number=4, title="Receiving and returning quotations",
        summary="Open Ben's Harbour Lane material request, price it and return it; quote the concrete request.",
        roles=SUPPLIER_DESK,
        lessons=(
            Lesson(
                key="s04-open-request", title="Open a contractor's request",
                what="Find Ben's Harbour Lane material request and read what it asks for.",
                why="The contractor's estimate depends on your prices. You see only what the contractor chose to "
                    "send: no customer name, job name or site address until an order is placed.",
                steps=(
                    Step(title="How Ben sends it", app=APP_OFFICE, where=REQUESTS_OFFICE,
                         do="Ben sends the deck takeoff's request with Send to BMR Winchester (training) in CalibraytAI; "
                            "concrete is sent separately with Save concrete request",
                         expect="'Request SRQ-… sent to BMR Winchester (training). It is in their Supplier Hub inbox "
                                "now.' Ben sees 'Sent, not opened' until you open it.",
                         if_wrong="If BMR shows '(no sign-in yet)' in Ben's list, nobody at the store can sign in yet.",
                         why="This step is the contractor's side, so you know what happened before the request reached you.",
                         endpoint="supplier_office.project_requests", shot="s4-office-requests-sent.png"),
                    Step(title="Open the request", app=APP_SUPPLIER, where=STORE + " → Needs attention → Quotes to answer",
                         do="Press the request number",
                         enter="SRQ-2026-0001 (your number may differ)",
                         expect="'Material request', the number, 'From Brayman Construction (training) — Ben Brayman "
                                "(training)', the reference 'Brayman project 1', Delivery town and Needed by, then Items.",
                         if_wrong="Delivery town 'To be confirmed' means the contractor has not set the job's town yet; "
                                  "the full address comes with the order.",
                         endpoint="supplier_portal.request_detail", shot="s4-material-request.png"),
                    Step(title="Read the lines", app=APP_SUPPLIER, where="The request → Items",
                         do="Read each line's item, quantity and unit",
                         expect="Each line shows FINAL QUANTITY or a note such as ENGINEERING-DEPENDENT — NOT READY TO "
                                "ORDER. Price all the lines you can: only final lines can be ordered later.",
                         if_wrong="If a line is unclear, phone or email the contact shown at the top.",
                         why="Opening the request marks it Opened; Ben sees 'Opened by the supplier'.",
                         endpoint="supplier_portal.request_detail"),
                ),
                exercise="Open the Harbour Lane material request on the training site and count its lines and how many "
                         "are not ready to order.",
            ),
            Lesson(
                key="s04-material-quote", title="Price a material request and return the quote",
                what="Enter your SKU, unit cost and discount for each line, the validity date, and press Return quote.",
                why="CalibraytAI works out the line and quote totals with the contractor's quantities, so the "
                    "contractor gets exact, comparable prices.",
                steps=(
                    Step(title="Enter SKU, Unit cost and Discount %", app=APP_SUPPLIER, where="The request → Items",
                         do="For each line type the SKU, Unit cost and Discount % (0 if none)",
                         enter="Line 1: BMR-20400, 12.00, 5 (training prices)",
                         expect="The boxes keep what you typed. A blank is not zero: a line left blank is returned "
                                "without a price.",
                         if_wrong="Type numbers only (12.00, not $12). Leave a line blank if you do not stock it.",
                         endpoint="supplier_portal.request_detail", shot="s4-material-quote-form.png"),
                    Step(title="The same form on your phone", app=APP_SUPPLIER, where="The request (on the phone)",
                         do="Fill each line card's SKU, Unit cost and Discount %",
                         expect="Every box is on screen; nothing scrolls sideways.",
                         if_wrong="If the keyboard hides a box, scroll down a little.",
                         endpoint="supplier_portal.request_detail", shot="s4-material-quote-phone.png"),
                    Step(title="Fill the bottom of the form", app=APP_SUPPLIER, where="The request → under the lines",
                         do="Check Your name (contact); fill Quote date, Prices valid until, General notes and Minutes "
                            "this quote took (optional)",
                         enter="Prices valid until: 30 days from today. Minutes: 14",
                         expect="Prices valid until is required. General notes is for substitutions: the line number and "
                                "the replacement SKU.",
                         if_wrong="Instead of typing, you can upload the filled request PDF in Or upload the filled request PDF.",
                         why="Minutes are optional and appear on your Dashboard as measured quotation effort.",
                         endpoint="supplier_portal.request_detail", shot="s4-material-quote-send-phone.png"),
                    Step(title="Return the quote", app=APP_SUPPLIER, where="The request → bottom",
                         do="Press Return quote",
                         expect="'Quote returned to the contractor. They review it before any order is placed.' and "
                                "'Quote returned by Darcy … N of M lines priced. Quoted total … valid until …'.",
                         if_wrong="If an error shows at the top (for example the date), fix it and press Return quote "
                                  "again. Once returned, the quote cannot be edited: ask the contractor to withdraw the "
                                  "request and send it again.",
                         endpoint="supplier_portal.request_detail", shot="s4-quote-returned.png"),
                ),
                exercise="Price the Harbour Lane material request on the training site (any training prices, leave one "
                         "line blank), valid for 30 days, and return it.",
            ),
            Lesson(
                key="s04-concrete-quote", title="Quote the concrete request",
                what="Read Ben's concrete request and return BMR's concrete price.",
                why="Concrete is its own request, never mixed with materials. BMR sells the concrete to the contractor; "
                    "Tomlinson Ready-Mix supplies it to BMR and is not in CalibraytAI, so you get Tomlinson's price your "
                    "usual way and quote BMR's own price here.",
                steps=(
                    Step(title="How Ben sends concrete", app=APP_OFFICE, where=REQUESTS_OFFICE + " → Concrete",
                         do="Ben fills Volume (m³), Strength (MPa), Exposure class, Air, Slump (mm), Delivery date, "
                            "Delivery time window, Placement and Notes, chooses Send to, and presses Save concrete request",
                         expect="'Concrete request … sent to BMR Winchester (training) (SRQ-…).' It reaches you as its own "
                                "request, Type: Concrete.",
                         if_wrong="This is the contractor's side, shown so you know where the request comes from.",
                         endpoint="supplier_office.project_requests", shot="s4-office-concrete-request.png"),
                    Step(title="Open the concrete request", app=APP_SUPPLIER, where=STORE + " → Requests (Type: Concrete)",
                         do="Press the request number",
                         enter="SRQ-2026-0002 (your number may differ)",
                         expect="'Concrete request' with Volume, Strength, Exposure class, Air, Slump, Requested delivery, "
                                "Placement and the notes. Example: 6.50 m³, 32 MPa, C-2, 5–8% air, 100 mm, by pump.",
                         if_wrong="If anything is unclear (for example the pump access), phone the contact shown at the top.",
                         endpoint="supplier_portal.request_detail", shot="s4-concrete-request.png"),
                    Step(title="Fill Your quote", app=APP_SUPPLIER, where="The concrete request → Your quote",
                         do="Fill Your quote number, Price per m³, the charges that apply, Prices valid until and Notes",
                         enter="BMR-CQ-1042; Price per m³ 245.00; Pump charge 350.00; valid 3 weeks; Notes '32 MPa C-2, "
                               "5–8% air, from Tomlinson Ready-Mix (training)'",
                         expect="CalibraytAI calculates the total: volume × price per m³, plus the charges, before tax.",
                         if_wrong="Price per m³ and Prices valid until are required. Leave a charge blank if it does not apply.",
                         endpoint="supplier_portal.request_detail", shot="s4-concrete-quote-form.png"),
                    Step(title="Return the concrete quote", app=APP_SUPPLIER, where="The concrete request → bottom",
                         do="Press Return quote",
                         expect="'Quote BMR-CQ-1042: 6.50 m³ at $245.00 = $1592.50; total before tax $1942.50, valid until …'",
                         if_wrong="If the total is not what you expected, check the volume on the request and the charges "
                                  "you typed; ask the contractor to send a new request if the volume is wrong.",
                         endpoint="supplier_portal.request_detail", shot="s4-concrete-quote-returned.png"),
                    Step(title="The contractor approves it", app=APP_OFFICE, where=REQUESTS_OFFICE,
                         do="Ben presses Approve this quote, then places the order as a separate step",
                         expect="'Concrete quote approved. Placing the order is a separate step.' No order exists yet.",
                         if_wrong="Do not book the truck with Tomlinson until a purchase order arrives (module 5).",
                         endpoint="supplier_office.project_requests"),
                ),
                exercise="Quote the Harbour Lane concrete request on the training site: 245.00 per m³ and a 350.00 pump "
                         "charge, valid three weeks, and check the total.",
            ),
        ),
    ),
    # ------------------------------------------------------------------ 5
    Module(
        key="s05", pathway=P, number=5, title="Purchase orders and confirmations",
        summary="A purchase order arrives; read it, confirm it or report a problem.",
        roles=SUPPLIER_DESK,
        lessons=(
            Lesson(
                key="s05-new-order", title="A purchase order arrives",
                what="Find the new purchase order and read what was ordered, where and when.",
                why="The order is not agreed until you confirm it. It is also the first time you see the site address.",
                steps=(
                    Step(title="How Ben places it", app=APP_OFFICE, where=REQUESTS_OFFICE,
                         do="Ben fills Delivery date, Time window, Site contact and Notes for the supplier, then presses "
                            "Place order",
                         expect="'Purchase order PO-… sent to BMR Winchester (training). It is agreed when they confirm it.'",
                         if_wrong="Ben can only order after he records and approves your returned prices.",
                         endpoint="supplier_office.project_requests", shot="s5-office-place-order.png"),
                    Step(title="The email", app=APP_EMAIL, where="Your inbox: 'New purchase order PO-…'",
                         do="Press the link in the email",
                         expect="'Ben Brayman (training) placed purchase order PO-… ($… before tax) for delivery …. "
                                "Please confirm it in the Supplier Hub.' The link opens the order.",
                         if_wrong="If no email arrives (a test site may keep its emails instead of sending them), use Needs attention.",
                         endpoint="supplier_portal.request_detail"),
                    Step(title="Orders to confirm", app=APP_SUPPLIER, where=STORE + " → Needs attention → Orders to confirm",
                         do="Press the order number",
                         enter="PO-2026-0001 (your number may differ)",
                         expect="The request opens at Purchase order PO-…. In Requests, the Order column says 'to confirm'.",
                         if_wrong="If the box says None waiting, the order may already be confirmed by a colleague.",
                         endpoint="supplier_portal.inbox", shot="s5-orders-to-confirm.png"),
                    Step(title="Read the order", app=APP_SUPPLIER, where="The request → Purchase order PO-…",
                         do="Read Placed by, Total before tax, Deliver to, Requested delivery, Site contact, Notes and the lines",
                         expect="'Deliver to 14 Harbour Lane, Merrickville, ON · Requested delivery … 8:00–10:00 · Site "
                                "contact …'. Only the lines the contractor can order now are listed.",
                         if_wrong="Lines that were not final stay on your quote and are not ordered yet; that is expected.",
                         endpoint="supplier_portal.request_detail", shot="s5-order-to-confirm.png"),
                ),
                exercise="Open the Harbour Lane purchase order on the training site and note its total, delivery "
                         "address, requested date and window, and site contact.",
            ),
            Lesson(
                key="s05-confirm", title="Confirm the order or report a problem",
                what="Confirm the delivery you can make, or put the order on hold with a problem.",
                why="Confirm order completes the agreement with the contractor under your account terms.",
                steps=(
                    Step(title="Confirm the order", app=APP_SUPPLIER, where="The request → Purchase order → the form under the lines",
                         do="Check Delivery date you can make and Time window, type a Note to the contractor, press Confirm order",
                         enter="Note: 'Boards and railing from the Winchester yard (training)'",
                         expect="'Order PO-… confirmed.' and 'Confirmed by Darcy … · Delivery <date>, 8:00–10:00'.",
                         if_wrong="If you cannot make the requested date, put the date you can make before confirming; "
                                  "it becomes the agreed delivery.",
                         endpoint="supplier_portal.request_detail", shot="s5-confirm-form.png"),
                    Step(title="What a confirmed order looks like", app=APP_SUPPLIER, where="The request → Purchase order",
                         do="Read the line under the order",
                         expect="Confirmed, by whom and when, the delivery, a Mark delivered link and the Delivery panel.",
                         if_wrong="If it still shows the confirm form, the button was not pressed: press Confirm order.",
                         endpoint="supplier_portal.request_detail", shot="s5-order-confirmed.png"),
                    Step(title="Or report a problem", app=APP_SUPPLIER, where="The request → Purchase order → the form",
                         do="Type what is wrong in Note to the contractor, then press Report a problem",
                         enter="For example 'Line 8 rail fittings out of stock until next week (training)'",
                         expect="'Problem sent to the contractor. The order is on hold until they answer.' The order "
                                "shows 'problem reported'.",
                         if_wrong="'Describe the problem…': the note is required. The contractor answers by phone or "
                                  "with a new request; only they can cancel the order.",
                         endpoint="supplier_portal.request_detail"),
                    Step(title="What Ben sees", app=APP_OFFICE, where=REQUESTS_OFFICE,
                         do="Ben reads his purchase order line",
                         expect="'Confirmed by Darcy …; agreed delivery …. The order is agreed.' Ben also gets an email.",
                         if_wrong="If Ben still sees 'Waiting for the supplier to confirm', open the order again and check.",
                         endpoint="supplier_office.project_requests", shot="s5-office-order-agreed.png"),
                    Step(title="Confirm the concrete order", app=APP_SUPPLIER, where="The concrete request → Purchase order",
                         do="Book the truck with Tomlinson Ready-Mix your usual way, then press Confirm order with a note",
                         enter="Note: 'Booked with Tomlinson Ready-Mix (training)'",
                         expect="'Order PO-… confirmed.'",
                         if_wrong="If Tomlinson cannot make the date, confirm the date they can make, or confirm and then "
                                  "use Change the delivery (module 6).",
                         endpoint="supplier_portal.request_detail"),
                ),
                exercise="Confirm the Harbour Lane material order and the concrete order on the training site, each "
                         "with a note.",
            ),
        ),
    ),
    # ------------------------------------------------------------------ 6
    Module(
        key="s06", pathway=P, number=6, title="Deliveries and schedule changes",
        summary="The Deliveries list, moving a delivery from either side, and marking an order delivered.",
        roles=SUPPLIER_DESK,
        lessons=(
            Lesson(
                key="s06-deliveries", title="The Deliveries list",
                what="See every open order's delivery, soonest first.",
                why="It is the yard's list for the coming days, including changes waiting for an answer.",
                steps=(
                    Step(title="Open Deliveries", app=APP_SUPPLIER, where=STORE + " → Deliveries",
                         do="Press Deliveries",
                         expect="Delivery, Order, Contractor, Deliver to and Status (Agreed, Confirm the order, Answer "
                                "needed: …, Waiting for the contractor: …, Problem reported).",
                         if_wrong="'No open deliveries.' means there is no placed or confirmed order. Delivered and "
                                  "cancelled orders leave this list.",
                         endpoint="supplier_portal.supplier_deliveries", shot="s6-deliveries.png"),
                    Step(title="On your phone", app=APP_SUPPLIER, where="Deliveries (on the phone)",
                         do="Press an order number to open it",
                         expect="The order opens at its Delivery panel.",
                         if_wrong="Reload the page if a card looks cut off.",
                         endpoint="supplier_portal.supplier_deliveries", shot="s6-deliveries-phone.png"),
                    Step(title="Cancelled by the contractor", app=APP_SUPPLIER, where="Deliveries → Cancelled by the contractor",
                         do="Read any order listed there",
                         expect="'Do not deliver these orders.' with the reason the contractor gave. The order page says "
                                "'Cancelled by the contractor … Do not deliver this order.'",
                         if_wrong="Only the contractor can cancel an order. If you need to cancel, phone them.",
                         endpoint="supplier_portal.supplier_deliveries"),
                ),
                exercise="Open Deliveries on the training site on your phone and find the Harbour Lane orders and their status.",
            ),
            Lesson(
                key="s06-ask-change", title="Ask to move a delivery",
                what="Ask the contractor to move the concrete delivery because Tomlinson has no pump truck that morning.",
                why="The agreed delivery only changes when the other side accepts, so both sides always know the real date.",
                steps=(
                    Step(title="Fill Change the delivery", app=APP_SUPPLIER,
                         where="The concrete order → Delivery → Change the delivery",
                         do="Choose New date, type Time window, choose Reason, type a Note, press Send the change to the contractor",
                         enter="The next day; 10:00–12:00; Supplier availability; 'Tomlinson Ready-Mix has no pump truck "
                               "that morning (training)'",
                         expect="'Delivery change sent to the contractor. The current delivery stands until they accept.'",
                         if_wrong="New date and Reason are required.",
                         endpoint="supplier_portal.request_detail", shot="s6-request-change.png"),
                    Step(title="Waiting for the answer", app=APP_SUPPLIER, where="The concrete order → Delivery",
                         do="Read the panel",
                         expect="'Change requested by Darcy …', 'Waiting for the contractor to accept. The delivery above "
                                "stands until then.' and a Withdraw the change button.",
                         if_wrong="Press Withdraw the change if you asked by mistake.",
                         endpoint="supplier_portal.request_detail", shot="s6-change-sent.png"),
                    Step(title="The contractor answers", app=APP_EMAIL,
                         where="Your inbox: 'Delivery change accepted: PO-… is now …' (or 'declined')",
                         do="Open the link and read Delivery changes",
                         expect="Accepted: the Agreed delivery shows the new date. Declined: the old date stands and the "
                                "contractor's note is shown.",
                         if_wrong="If declined, phone the contractor or propose another date the same way.",
                         endpoint="supplier_portal.request_detail"),
                ),
                exercise="On the training site, ask to move the Harbour Lane concrete delivery by one day for supplier "
                         "availability, then look at the panel while it waits.",
            ),
            Lesson(
                key="s06-answer-change", title="Answer the contractor's change",
                what="Ben asks to move the material delivery for rain; accept it on your phone.",
                why="Until you answer, the agreed delivery stands and the contractor does not know if you can make the new date.",
                steps=(
                    Step(title="See the change waiting", app=APP_SUPPLIER,
                         where=STORE + " → Delivery changes waiting for your answer",
                         do="Press the order number",
                         expect="'PO-…: Ben Brayman (training) asks to move the delivery to <date> (Weather)'. You also "
                                "get an email 'Delivery change requested: PO-… → …'.",
                         if_wrong="If the box is missing, nothing is waiting.",
                         endpoint="supplier_portal.inbox", shot="s6-change-waiting-phone.png"),
                    Step(title="Read the change", app=APP_SUPPLIER, where="The order → Delivery",
                         do="Read the yellow box",
                         expect="'Change requested by Ben …: old date → new date. Reason: Weather.' with Accept <date>, "
                                "Decline and Propose another time instead.",
                         if_wrong="The delivery above stands until you answer.",
                         endpoint="supplier_portal.request_detail", shot="s6-answer-change-phone.png"),
                    Step(title="Accept", app=APP_SUPPLIER, where="The order → Delivery", do="Press Accept <date>",
                         expect="'Answer sent to the contractor.' and 'Agreed delivery: <new date>'.",
                         if_wrong="To refuse, type a note in Note (required to decline) and press Decline. To offer a "
                                  "different time, open Propose another time instead, fill Date, Time window and Reason, "
                                  "and press Propose this time.",
                         endpoint="supplier_portal.request_detail", shot="s6-change-accepted-phone.png"),
                ),
                exercise="Have the contractor side (or your trainer) ask to move the Harbour Lane material delivery, then "
                         "accept it on your phone.",
            ),
            Lesson(
                key="s06-delivered", title="Mark the order delivered",
                what="Record that the Harbour Lane boards were delivered, with a note.",
                why="It closes the order on both sides: it leaves the delivery lists and the contractor is told.",
                steps=(
                    Step(title="Open Mark delivered", app=APP_SUPPLIER, where="The confirmed order → Mark delivered",
                         do="Press Mark delivered, check Delivered on, type a Note (optional), press Mark delivered",
                         enter="Today's date; 'Unloaded at the side gate (training)'",
                         expect="'Order PO-… marked delivered. The contractor has been told.'",
                         if_wrong="'The delivery date cannot be in the future.' Only a confirmed order can be marked delivered.",
                         endpoint="supplier_portal.request_detail", shot="s6-mark-delivered-phone.png"),
                    Step(title="Check it is closed", app=APP_SUPPLIER, where="The order",
                         do="Read the order",
                         expect="'Delivered on <date> (recorded by Darcy …) · Unloaded at the side gate'. The delivery "
                                "can no longer be changed and the order leaves Deliveries.",
                         if_wrong="If the contractor already marked it delivered, you see their record instead.",
                         endpoint="supplier_portal.request_detail", shot="s6-delivered-phone.png"),
                ),
                exercise="Mark the Harbour Lane material order delivered on your phone (use today's date on the training "
                         "site), then check it left Deliveries.",
            ),
        ),
    ),
    # ------------------------------------------------------------------ 7
    Module(
        key="s07", pathway=P, number=7, title="Material demand and SKU reuse",
        summary="SKUs you quoted before are filled in on new requests; Material demand adds up what contractors ask for.",
        roles=SUPPLIER_DESK,
        lessons=(
            Lesson(
                key="s07-sku-reuse", title="Remembered SKUs on a new request",
                what="See your SKUs filled in on Ben's updated Harbour Lane request, check them and price it.",
                why="You do not retype SKUs for products you quoted before; prices and discounts are never filled in.",
                steps=(
                    Step(title="How a SKU is remembered", app=APP_OFFICE,
                         where="The returned quote → Record the ready prices (contractor side)",
                         do="Ben records the prices you returned",
                         expect="Recording links each of his products to your SKU. Only then is it remembered.",
                         if_wrong="If nothing is filled in on a new request, the contractor has not recorded an earlier "
                                  "quote of yours for those products yet: type the SKU as usual.",
                         endpoint="supplier_office.project_requests"),
                    Step(title="Open the updated request", app=APP_SUPPLIER, where=STORE + " → Quotes to answer",
                         do="Open the new request",
                         enter="Ben changed the pool gate and sent SRQ-2026-0003 (your number may differ)",
                         expect="'SKUs you quoted before for the same product are filled in for you.' Each filled SKU "
                                "says 'Your confirmed SKU — check it'. Prices and Discount % are empty.",
                         if_wrong="A product you have not quoted before arrives with an empty SKU box. 'On "
                                  "record: A, B' means two SKUs are on record: type the right one.",
                         endpoint="supplier_portal.request_detail", shot="s7-sku-remembered.png"),
                    Step(title="Check each SKU on your phone", app=APP_SUPPLIER, where="The request (on the phone)",
                         do="Read each filled SKU; type over any that is wrong; then enter today's prices",
                         expect="Your changes are kept when you press Return quote.",
                         if_wrong="A remembered SKU is only a suggestion: always check it against the item.",
                         endpoint="supplier_portal.request_detail", shot="s7-sku-remembered-phone.png"),
                ),
                exercise="Open the updated Harbour Lane request on the training site, check the remembered SKUs, enter "
                         "prices and return it.",
            ),
            Lesson(
                key="s07-demand", title="Read Material demand",
                what="See what contractors asked BMR to quote, by product, and what was ordered.",
                why="It shows recurring products, products without a confirmed SKU and possible gaps in what you stock.",
                steps=(
                    Step(title="Open Material demand", app=APP_SUPPLIER, where=STORE + " → Material demand",
                         do="Press Material demand and choose a Period, then Show",
                         expect="Requests sent to you, Contractors who asked, Products asked for more than once, Products "
                                "with no confirmed SKU of yours.",
                         if_wrong="'No requests were sent to <store> in this period.': choose a longer period.",
                         endpoint="supplier_portal.supplier_demand", shot="s7-demand.png"),
                    Step(title="Requested materials", app=APP_SUPPLIER, where="Material demand → Requested materials",
                         do="Read the table by category",
                         expect="Product, Unit, Requests, Contractors, Quantity requested, You priced, Ordered from you, "
                                "and the flags Recurring, No confirmed SKU and Possible gap.",
                         if_wrong="Requested is not purchased: a contractor may have bought it elsewhere.",
                         endpoint="supplier_portal.supplier_demand", shot="s7-demand-products.png"),
                    Step(title="Possible assortment gaps and concrete", app=APP_SUPPLIER,
                         where="Material demand → Possible assortment gaps, Concrete",
                         do="Read the lists",
                         expect="A gap is a product returned without a price in two or more requests and never priced. "
                                "Concrete is counted on its own, by mix.",
                         if_wrong="'How this is counted' at the bottom explains every figure. Contractors are counted, "
                                  "never named.",
                         endpoint="supplier_portal.supplier_demand"),
                ),
                exercise="Open Material demand for This month on the training site and find the product you left "
                         "without a price.",
            ),
        ),
    ),
    # ------------------------------------------------------------------ 8
    Module(
        key="s08", pathway=P, number=8, title="Supplier pricing and catalogue management",
        summary="Where your prices live: typed on each contractor quote, and the store's own price file, settings, "
                "standard buildings and product matches for the PRO Desk.",
        roles=ALL_SUPPLIER,
        lessons=(
            Lesson(
                key="s08-what-exists", title="What CalibraytAI keeps of your prices",
                what="Learn what is and is not available for prices and the product catalogue today.",
                why="So you know where a price comes from and what must be set up before the PRO Desk can price.",
                steps=(
                    Step(title="Contractor requests: typed on each quote", app=APP_SUPPLIER,
                         where="Any contractor request → Items",
                         do="Type today's price on each quote",
                         expect="Prices are never filled in on a contractor request; only remembered SKUs are (module 7).",
                         if_wrong="The PRO Desk price file is not used for contractor requests.",
                         endpoint="supplier_portal.request_detail"),
                    Step(title="PRO Desk: the store's own price file", app=APP_PRO_DESK, where=PRO_DESK,
                         do="Read the boxes at the top before the first quotation",
                         expect="'Before the first quotation' (tax and validity in Quote settings) and 'No price file "
                                "loaded'. Quotations can be prepared, but no line is priced until the price file is loaded.",
                         if_wrong="These are the prerequisites: Quote settings and a price file (next lessons).",
                         why="There is no screen to edit one product or price, and no link to your store's own system. "
                             "To change a price, load a new price file; the newest price in effect is used.",
                         endpoint="supplier_pro_desk.index", shot="s8-pro-desk-before-setup.png"),
                ),
                exercise="Open PRO Desk quotations on the training site and read what it says must be set up first.",
            ),
            Lesson(
                key="s08-settings", title="Quote settings",
                what="Set the tax, validity, delivery charge, contact line and terms printed on every quotation.",
                why="Without the tax and validity, no PRO Desk quotation can be issued.",
                steps=(
                    Step(title="Fill Quote settings", app=APP_PRO_DESK, where=PRO_DESK + " → Quote settings",
                         do="Fill Sales tax label, Sales tax rate (%), Quotation valid for (days), Default delivery charge "
                            "($), Contact line on quotations and Terms printed on quotations, then press Save settings",
                         enter="HST; 13; 30; 150; '613-555-0199 · prodesk@training.calibraytai.invalid · Winchester (training)'",
                         expect="'Quote settings saved.' and 'Last saved by <you>, <date>'.",
                         if_wrong="Type the rate as a number (13, not 13%).",
                         endpoint="supplier_pro_desk.settings", shot="s8-quote-settings.png"),
                ),
                exercise="Save the training Quote settings: HST 13 %, 30 days, $150 delivery.",
            ),
            Lesson(
                key="s08-price-file", title="Load the store's price file",
                what="Load a CSV of SKUs and prices, authorized by a named person at the store.",
                why="PRO Desk quotations use only these prices. CalibraytAI never types or estimates a price.",
                steps=(
                    Step(title="Prepare the CSV", app=APP_PRO_DESK, where="Your store's spreadsheet, saved as CSV (UTF-8)",
                         do="Use a header row with sku, description, unit, price and effective_from (optional: pack_qty, "
                            "discount_percent, discount_rule, effective_to, availability, store)",
                         enter="For example: BMR-T-POST, 'Laminated column 3-ply 2x6 (training)', EA, 62.00, 2026-10-18",
                         expect="Dates look like 2026-10-20. availability is IN_STOCK, LIMITED, SPECIAL_ORDER or UNKNOWN; "
                                "store is a store code, blank for every store.",
                         if_wrong="'The price file needs these columns: …' lists a missing column.",
                         endpoint="supplier_pro_desk.prices"),
                    Step(title="Load it", app=APP_PRO_DESK, where=PRO_DESK + " → Price file",
                         do="Choose the file in Price file (CSV), type Authorized by, then press Load prices",
                         enter="Authorized by: 'Darcy, store manager (training)'; on the training site tick These are "
                               "synthetic test prices",
                         expect="'8 prices loaded; 0 rows not loaded (listed below).'",
                         if_wrong="'Name the person at the supplier who authorized these prices.': Authorized by is required.",
                         endpoint="supplier_pro_desk.prices", shot="s8-price-file-load.png"),
                    Step(title="Check Loaded files", app=APP_PRO_DESK, where="Price file → Loaded files",
                         do="Read the newest row",
                         expect="When, File, Authorized by, Loaded by, Loaded and Not loaded. Rows not loaded are listed "
                                "with the reason, for example 'price is not a number'.",
                         if_wrong="Fix the rows in the spreadsheet and load the file again. A SKU's selling unit cannot "
                                  "change: 'unit X differs from this SKU's selling unit Y'.",
                         endpoint="supplier_pro_desk.prices", shot="s8-price-file-loaded.png"),
                ),
                exercise="Load the training price file (eight synthetic lines) and check that nothing was rejected.",
            ),
            Lesson(
                key="s08-standards-matches", title="Standard buildings and product matches",
                what="Set up a standard building for Quick Quote, and match your products to the material lines.",
                why="Both are done once; every later quotation reuses them.",
                steps=(
                    Step(title="Add a standard building", app=APP_PRO_DESK, where=PRO_DESK + " → Standard buildings",
                         do="Fill Name, Based on and the framing, panel and fastening answers, then press Save the standard",
                         enter="'Post-frame steel, 8 ft bays (training)'; posts 8 ft, trusses 8 ft, purlins and girts 2×4 "
                               "SPF at 24 in, 36 in panels, 12 in overhangs",
                         expect="'Standard building “…” saved for Quick Quote.' Posts, trusses and headers stay flagged "
                                "for technical review on every quotation.",
                         if_wrong="'Not saved:' lists what is missing. To change a standard, add the new one and press "
                                  "Retire this standard on the old.",
                         why="Every value is the store's own; CalibraytAI does not supply or check structural values.",
                         endpoint="supplier_pro_desk.standards", shot="s8-standard-building-form.png"),
                    Step(title="Check the saved standard", app=APP_PRO_DESK, where=PRO_DESK + " → Standard buildings",
                         do="Read the standard at the top of the page",
                         expect="Its values, who approved it and when, and the basis. Quick Quote now offers it.",
                         if_wrong="If Quick Quote says 'No standard buildings yet', the standard was not saved: add it again.",
                         endpoint="supplier_pro_desk.standards", shot="s8-standard-building.png"),
                    Step(title="Match a product to a line", app=APP_PRO_DESK,
                         where="A quotation → 5 · Pricing → a line marked Choose product → Match a product",
                         do="Choose the product, type the selling units per takeoff unit, press Match",
                         enter="Posts: BMR-T-POST, 1. Purlins: BMR-T-2416, 0.0625 (16 ft pieces against feet). Panels: "
                               "BMR-T-PANEL, 1",
                         expect="The line shows the SKU, the price and 'Priced'. The match is kept for later quotations.",
                         if_wrong="'… is already matched to this line with a conversion of …': a match cannot be changed "
                                  "with another conversion. If no product fits, use Leave out with a reason.",
                         endpoint="supplier_pro_desk.quote", shot="s8-match-product.png"),
                    Step(title="Setup is kept apart from quotation time", app=APP_PRO_DESK, where=PRO_DESK + " → Timing",
                         do="Read One-time store setup",
                         expect="Price files imported, Products matched to takeoff lines and Standard buildings approved; "
                                "none of it is counted in a quotation's time.",
                         if_wrong="If a count is 0, that setup has not been done yet.",
                         endpoint="supplier_pro_desk.timing"),
                ),
                exercise="Save the training standard building, then on your first Quick Quote match each line marked "
                         "Choose product to its training SKU.",
            ),
        ),
    ),
    # ------------------------------------------------------------------ 9
    Module(
        key="s09", pathway=P, number=9, title="PRO Desk walk-in customer quotations",
        summary="A walk-in customer's building: sketch, Quick Quote, price review, quotation, customer link, order sheet.",
        roles=ALL_SUPPLIER,
        lessons=(
            Lesson(
                key="s09-quick-quote", title="Start a Quick Quote with the customer's sketch",
                what="Enter the walk-in customer, the standard building, size, doors, floor and the sketch.",
                why="The PRO Desk serves your own customers. Contractors never see these quotations.",
                steps=(
                    Step(title="Open the PRO Desk", app=APP_PRO_DESK, where=STORE, do="Press PRO Desk quotations",
                         expect="The Walk-in quotations page opens.",
                         if_wrong="The button is at the top right of your store's page (above Needs attention on a phone).",
                         endpoint="supplier_portal.inbox", shot="s9-pro-desk-button.png"),
                    Step(title="The Walk-in quotations page", app=APP_PRO_DESK, where=PRO_DESK, do="Read the buttons and the list",
                         expect="Walk-in quotations: Quick Quote, Detailed quotation, Standard buildings, Timing, Price "
                                "file, Quote settings, Contractor requests, and the Quotations list.",
                         if_wrong="If 'Before the first quotation' shows, finish Quote settings first (module 8).",
                         endpoint="supplier_pro_desk.index", shot="s9-pro-desk.png"),
                    Step(title="1 · Customer", app=APP_PRO_DESK, where=PRO_DESK + " → Quick Quote",
                         do="Fill Name, Phone, Email and Town; ask the customer, then tick the consent boxes they agree to",
                         enter="Jordan Tremblay (training walk-in); 613-555-0177; jordan.tremblay@training.calibraytai.invalid; "
                               "Winchester; tick email consent and Training or demonstration quotation",
                         expect="The customer does not need an account; their details stay with your store.",
                         if_wrong="Without email consent the quotation cannot be emailed; you can still print it or give the link.",
                         endpoint="supplier_pro_desk.quick", shot="s9-quick-quote-customer.png"),
                    Step(title="Size, doors, floor and the sketch", app=APP_PRO_DESK,
                         where="Quick Quote → 2 · Standard building to 6 · Sketch (optional)",
                         do="Choose the standard; fill Width (endwall), Length (sidewall), Wall height (eave), Roof pitch; "
                            "add each door row; choose the floor; add the sketch photo; press Price this building",
                         enter="Post-frame steel, 8 ft bays (training); 30 × 40 ft, 12 ft walls, pitch 4; Overhead door 1 × "
                               "120 × 120 in Left endwall; Man door 1 × 36 × 80 in Front sidewall; No floor; the sketch photo",
                         expect="'Quotation Q2026-0001 for Jordan Tremblay (training walk-in): check the price review, "
                                "then issue.' The quotation page shows steps 1 to 8.",
                         if_wrong="'Not started yet: please fix' lists each missing answer.",
                         endpoint="supplier_pro_desk.quick", shot="s9-quick-quote-size.png"),
                    Step(title="The sketch is kept", app=APP_PRO_DESK, where="The quotation → 1 · Customer and sketch",
                         do="Check the sketch is shown",
                         expect="The photo is kept with the quotation. Nothing reads it automatically: you read it with "
                                "the customer. Keep the sketch adds another photo or PDF.",
                         if_wrong="If the photo was too large it was not kept: take a smaller photo and press Keep the sketch.",
                         endpoint="supplier_pro_desk.quote", shot="s9-sketch-kept.png"),
                    Step(title="Or a detailed quotation", app=APP_PRO_DESK, where=PRO_DESK + " → Detailed quotation",
                         do="Fill the customer, press Start the quotation, keep the sketch, then answer the building "
                            "questions and press Confirm the building",
                         expect="The same quotation steps, with every building answer typed by you.",
                         if_wrong="Use it when no standard building fits the customer's building.",
                         endpoint="supplier_pro_desk.new_quote"),
                ),
                exercise="Start a Quick Quote on the training site for Jordan Tremblay (training walk-in), 30 × 40 ft, "
                         "with the training sketch.",
            ),
            Lesson(
                key="s09-price-issue", title="Check the building, materials and prices, then issue",
                what="Review steps 2 to 6 and issue the quotation.",
                why="Issuing freezes the building, quantities, products and prices that the customer accepts.",
                steps=(
                    Step(title="2 · Building and 3 · Drawing", app=APP_PRO_DESK, where="The quotation → 2 · Building",
                         do="Read the standard used and the amber technical review items",
                         expect="'Quick Quote from the store standard …'. To change an answer, open the detailed building "
                                "form, change it and press Confirm the building. The preliminary sales drawing follows.",
                         if_wrong="The drawing is not for construction, not engineered and not a permit drawing.",
                         endpoint="supplier_pro_desk.quote", shot="s9-building-from-standard.png"),
                    Step(title="4 · Material list", app=APP_PRO_DESK, where="The quotation → 4 · Material list",
                         do="Read each line's status",
                         expect="Calculated, Technical review or Needs an answer, with how each quantity was worked out.",
                         if_wrong="A line that needs an answer is fixed in 2 · Building.",
                         endpoint="supplier_pro_desk.quote", shot="s9-materials.png"),
                    Step(title="5 · Pricing", app=APP_PRO_DESK, where="The quotation → 5 · Pricing",
                         do="Match any Choose product line (module 8); open Leave out on lines you do not sell and type the reason",
                         enter="Trusses: 'Truss quote to follow from the truss manufacturer'",
                         expect="Every line is Priced, Left out or By design.",
                         if_wrong="'No current price': the price file has no price in effect today for that SKU: load a "
                                  "new price file. Put back undoes Leave out.",
                         endpoint="supplier_pro_desk.quote", shot="s9-pricing.png"),
                    Step(title="6 · Quotation totals", app=APP_PRO_DESK, where="The quotation → 6 · Quotation",
                         do="Check Delivery charge ($), Quotation discount (%) and Note for the customer; press Update totals",
                         expect="Materials, Delivery, HST (13%) and Total. 'Before it can be issued' must be gone.",
                         if_wrong="Each item under 'Before it can be issued' says what is still open.",
                         endpoint="supplier_pro_desk.quote", shot="s9-quotation-totals.png"),
                    Step(title="Issue the quotation", app=APP_PRO_DESK, where="The quotation → 6 · Quotation",
                         do="Press Issue the quotation",
                         expect="'Quotation Q2026-0001 issued: $… including tax, valid until …'. Quotation PDF opens the "
                                "printable quotation with the drawing.",
                         if_wrong="To change an issued quotation that is not yet accepted, press Start a revision; the old "
                                  "one is kept and its approval link stops working.",
                         endpoint="supplier_pro_desk.quote", shot="s9-issued.png"),
                ),
                exercise="Finish the training quotation: leave the trusses out with a reason and issue it.",
            ),
            Lesson(
                key="s09-customer-link", title="Send the customer link and record the answer",
                what="Email the approval link; the customer accepts on their phone. Or record their answer at the counter.",
                why="The accepted quotation is kept exactly as issued, with who accepted it and how.",
                steps=(
                    Step(title="Create the approval link", app=APP_PRO_DESK, where="The quotation → 7 · Customer approval",
                         do="Leave Email it to <email> ticked and press Create approval link",
                         expect="'Quotation emailed to the customer.' and 'Approval link (shown once; copy it now)'. A "
                                "test site that keeps its mail says 'Quotation email recorded (local test mail).'",
                         if_wrong="'No email consent' means you give the link or the printed quotation instead.",
                         endpoint="supplier_pro_desk.quote", shot="s9-approval-link.png"),
                    Step(title="The customer opens the link", app=APP_CUSTOMER,
                         where="The email from BMR Winchester (training), on the customer's phone",
                         do="Open the link; press Open the quotation and drawing (PDF) to read it",
                         expect="'Material quotation Q2026-0001', the total including HST, materials only.",
                         if_wrong="'This quotation has expired' or 'Quotation unavailable': make a new link or a revision.",
                         endpoint="supplier_quote_link.view", shot="s9-customer-link-phone.png"),
                    Step(title="The customer accepts", app=APP_CUSTOMER, where="The link → Your answer",
                         do="Type Your full name, tick 'I accept material quotation …', press Accept",
                         enter="Jordan Tremblay (training walk-in)",
                         expect="'Thank you — accepted'.",
                         if_wrong="On some phones the sentence beside the tick box shows one letter per line (a reported "
                                  "display problem); it is the 'I accept material quotation …' box. Decline records a no.",
                         endpoint="supplier_quote_link.view", shot="s9-customer-accept-phone.png"),
                    Step(title="The customer's confirmation", app=APP_CUSTOMER, where="The link, after Accept",
                         do="Read the page",
                         expect="'Thank you — accepted', the name and date, and 'BMR Winchester (training) will prepare "
                                "your order and contact you about payment and delivery.'",
                         if_wrong="A declined quotation cannot be revised: if the customer declined by mistake, start a new quotation.",
                         endpoint="supplier_quote_link.view", shot="s9-customer-accepted-phone.png"),
                    Step(title="Accepted on the PRO Desk", app=APP_PRO_DESK, where="The quotation → 7 · Customer approval",
                         do="Reload the quotation",
                         expect="'Accepted by Jordan Tremblay (training walk-in) on … (approval link)' and the record number.",
                         if_wrong="At the counter instead: fill Customer's full name, How and Answer under 'Or record the "
                                  "customer's answer at the counter' and press Record the answer.",
                         endpoint="supplier_pro_desk.quote", shot="s9-accepted.png"),
                ),
                exercise="Send the training quotation's approval link, open it on your phone as the customer and accept it.",
            ),
            Lesson(
                key="s09-order", title="Prepare the order for your store system",
                what="Turn the accepted quotation into the order sheet the store enters in its own system.",
                why="CalibraytAI does not connect to your sales system, place the order or take payment.",
                steps=(
                    Step(title="Prepare the order", app=APP_PRO_DESK, where="The quotation → 8 · Order-ready package",
                         do="Press Prepare the order for entry",
                         expect="'Order for Q2026-0001': SKU, Description, Qty, Unit, Unit price, Discount, Extended and "
                                "the totals, with Order CSV and Back to the quotation.",
                         if_wrong="It is only offered once the customer has accepted.",
                         endpoint="supplier_pro_desk.order", shot="s9-order.png"),
                    Step(title="Enter it in the store system", app=APP_PRO_DESK, where="The order sheet",
                         do="Type the lines into your store's sales system, or press Order CSV for a file",
                         expect="Quantities and prices are the accepted ones.",
                         if_wrong="On the training site the sheet is marked synthetic: do not enter it as a real order.",
                         endpoint="supplier_pro_desk.order_csv"),
                    Step(title="See how long it took", app=APP_PRO_DESK, where=PRO_DESK + " → Timing",
                         do="Find the quotation",
                         expect="Each stage's time and 'Walk-in quotation, start to printable quotation', measured from "
                                "the buttons staff pressed.",
                         if_wrong="'Start time not recorded' is shown for a detailed quotation.",
                         endpoint="supplier_pro_desk.timing", shot="s9-timing.png"),
                ),
                exercise="Prepare the order for the accepted training quotation and download the Order CSV.",
            ),
        ),
    ),
    # ------------------------------------------------------------------ 10
    Module(
        key="s10", pathway=P, number=10, title="Complete supplier workflow and acceptance",
        summary="Run the whole Harbour Lane cycle and a walk-in without help, then record your acceptance tests.",
        roles=ALL_SUPPLIER,
        lessons=(
            Lesson(
                key="s10-contractor-cycle", title="The whole Harbour Lane cycle, start to finish",
                what="Request → quote → order → confirmation → delivery change → delivered, then read the history.",
                why="This is the daily work with a contractor; the history shows who did what and when.",
                roles=SUPPLIER_DESK,
                steps=(
                    Step(title="Quote", app=APP_SUPPLIER, where=STORE + " → Quotes to answer",
                         do="Open each Harbour Lane request and press Return quote (materials and concrete separately)",
                         expect="Both show Quote returned.",
                         if_wrong="See module 4.",
                         endpoint="supplier_portal.inbox", shot="s3-inbox.png"),
                    Step(title="Confirm", app=APP_SUPPLIER, where=STORE + " → Orders to confirm",
                         do="Open each order and press Confirm order",
                         expect="Each says 'Order PO-… confirmed.'",
                         if_wrong="See module 5.",
                         endpoint="supplier_portal.request_detail", shot="s5-order-confirmed.png"),
                    Step(title="Deliver", app=APP_SUPPLIER, where=STORE + " → Deliveries",
                         do="Answer or ask for any delivery change; mark the order delivered when it is",
                         expect="Agreed dates on both sides; delivered orders leave the list.",
                         if_wrong="See module 6.",
                         endpoint="supplier_portal.supplier_deliveries", shot="s6-deliveries.png"),
                    Step(title="Read the history", app=APP_SUPPLIER, where="The request → History",
                         do="Read the list at the bottom",
                         expect="Sent, Opened, Returned, Order confirmed, the delivery change and Order delivered, each "
                                "with the date, time and person.",
                         if_wrong="The history cannot be edited; it is the record both sides see.",
                         endpoint="supplier_portal.request_detail", shot="s10-request-history.png"),
                    Step(title="End of the day", app=APP_SUPPLIER, where=STORE + " → Needs attention",
                         do="Check every box",
                         expect="Nothing waiting, or only what you will do tomorrow.",
                         if_wrong="Anything left in Quotes to answer or Orders to confirm is waiting for you.",
                         endpoint="supplier_portal.inbox", shot="s10-inbox-end-of-day.png"),
                ),
                exercise="Without the lessons open, take one new Harbour Lane request from New to Delivered on the "
                         "training site.",
            ),
            Lesson(
                key="s10-pro-desk-cycle", title="A walk-in from sketch to order",
                what="Quote a walk-in customer on your own, from the sketch to the order sheet.",
                why="Shows you can serve a counter customer without help.",
                steps=(
                    Step(title="Quick Quote", app=APP_PRO_DESK, where=PRO_DESK + " → Quick Quote",
                         do="Enter the customer, building, doors, floor and sketch; press Price this building",
                         expect="The quotation opens at 5 · Pricing.", if_wrong="See module 9.",
                         endpoint="supplier_pro_desk.quick"),
                    Step(title="Issue and send", app=APP_PRO_DESK, where="The quotation → 6 · Quotation, 7 · Customer approval",
                         do="Press Issue the quotation, then Create approval link",
                         expect="The approval link is shown once.", if_wrong="See module 9.",
                         endpoint="supplier_pro_desk.quote"),
                    Step(title="Customer accepts, order sheet", app=APP_CUSTOMER, where="The link on the customer's phone",
                         do="Accept as the customer; then on the PRO Desk press Prepare the order for entry",
                         expect="'Thank you — accepted' and the order sheet.", if_wrong="See module 9.",
                         endpoint="supplier_quote_link.view"),
                ),
                exercise="Quote a second training walk-in (a 24 × 32 ft building, one man door) from Quick Quote to the "
                         "order sheet.",
            ),
            Lesson(
                key="s10-acceptance", title="Record your acceptance tests",
                what="Run each acceptance test and record Pass, Fail or Blocked.",
                why="Acceptance tests are separate from training: they confirm CalibraytAI works for your store.",
                steps=(
                    Step(title="Open your acceptance tests", app=APP_SUPPLIER,
                         where="Training Centre → your training home → Acceptance tests",
                         do="Press Acceptance tests",
                         expect="Your tests, each with its result so far.",
                         if_wrong="Only the tests for your role are listed.",
                         endpoint="training.uat", shot="s10-uat-list.png"),
                    Step(title="Run one test and record it", app=APP_SUPPLIER, where="Acceptance tests → a test",
                         do="Follow Start and Action on the training site, then choose Pass, Fail or Blocked and press "
                            "Save result",
                         expect="The result is saved as Attempt 1. A retest after a fix adds Attempt 2; earlier results are kept.",
                         if_wrong="Fail and Blocked need What went wrong (needed for Fail or Blocked).",
                         endpoint="training.uat_case", shot="s10-uat-case.png"),
                ),
                exercise="Run and record every acceptance test in your list.",
            ),
        ),
    ),
)


def _uat(key, module, title, start, action, expected, roles=SUPPLIER_DESK):
    return UatCase(key=key, pathway=P, module_key=module, title=title, start=start, action=action, expected=expected,
                   roles=roles)


UAT_CASES = (
    UatCase(key="uat-s01-sign-in", pathway=P, module_key="s01", title="Supplier sign-in",
            start="The training site's supplier sign-in page", action="Sign in with your training email and password.",
            expected="Your store's Supplier Hub opens; no contractor office pages are shown.", roles=ALL_SUPPLIER),
    _uat("uat-s01-wrong-password", "s01", "A wrong password is refused",
         "Supplier sign-in", "Type your email and a wrong password, press Sign in.",
         "'The email or password is not correct, or this is not a supplier sign-in.' You stay on the sign-in page.",
         ALL_SUPPLIER),
    _uat("uat-s01-password-link", "s01", "Forgot your password gives a working link",
         "Supplier sign-in → Forgot your password?",
         "Send Reset Instructions for your training email; open the email; set a new password; sign in with it.",
         "'Password Updated', and the new password signs you in to the Supplier Hub.", ALL_SUPPLIER),

    _uat("uat-s02-same-access", "s02", "Every store user has the same access",
         "Supplier sign-in, as Darcy and then as Pat",
         "Open BMR Winchester (training) and the same Harbour Lane request as each person.",
         "Both see the same requests, orders and PRO Desk quotations; neither sees an administrator setting.",
         ALL_SUPPLIER),
    _uat("uat-s02-removed", "s02", "A removed user cannot sign in",
         "Contractor office: Company → Suppliers → BMR Winchester (training)",
         "Ask Ben to give a training test person a sign-in, sign in as them, then ask Ben to press Remove sign-in; sign in again.",
         "After removal the sign-in is refused and the person shows as 'removed' on the contractor's page.",
         SUPPLIER_DESK),
    _uat("uat-s02-texts", "s02", "Text settings are saved",
         "Supplier Hub → your name (Text settings)",
         "Enter a training mobile number, tick Text me delivery updates, press Save.",
         "'Text settings saved.' and 'Texts on since <today>'.", ALL_SUPPLIER),

    _uat("uat-s03-needs-attention", "s03", "Needs attention counts what is waiting",
         "Supplier Hub → BMR Winchester (training)",
         "Ask Ben to send a new Harbour Lane request; reload the page.",
         "Quotes to answer goes up by one and lists the new SRQ number; the Requests table shows it as New.",
         ALL_SUPPLIER),
    _uat("uat-s03-period", "s03", "The Dashboard period changes the figures",
         "Supplier Hub → Dashboard",
         "Choose All time and press Show; then Custom dates 2020-01-01 to 2020-01-31 and press Show.",
         "All time shows the training quotes and orders; the 2020 period shows 0 and 'No quotes returned in this period.'"),
    _uat("uat-s03-phone", "s03", "The store page works on a phone",
         "Supplier Hub on a phone", "Open the store page, Deliveries and the Dashboard.",
         "Every page fits the screen with no sideways scrolling.", ALL_SUPPLIER),

    _uat("uat-s04-material-quote", "s04", "Return a material quote",
         "Supplier Hub → Quotes to answer → the Harbour Lane material request",
         "Enter SKU, unit cost and 5 % discount on every line but one, Prices valid until in 30 days, press Return quote.",
         "'Quote returned to the contractor.' and 'N−1 of N lines priced' with a quoted total; Ben sees 'Quote returned'."),
    _uat("uat-s04-concrete-quote", "s04", "Return a concrete quote with the correct total",
         "Supplier Hub → the Harbour Lane concrete request (6.50 m³)",
         "Price per m³ 245.00, Pump charge 350.00, valid in 3 weeks, press Return quote.",
         "'6.50 m³ at $245.00 = $1592.50; total before tax $1942.50'."),
    _uat("uat-s04-privacy", "s04", "A request shows no customer or address",
         "Supplier Hub → any Harbour Lane request before an order",
         "Read the whole page.",
         "Only the contractor, its contact, 'Brayman project <n>', the delivery town and the lines; no customer name, "
         "job name or street address."),

    _uat("uat-s05-confirm", "s05", "Confirm a purchase order",
         "Supplier Hub → Orders to confirm → the Harbour Lane material order",
         "Check the date and window, type a note, press Confirm order.",
         "'Order PO-… confirmed.'; Ben's page says 'The order is agreed.' with the same delivery."),
    _uat("uat-s05-problem-note", "s05", "Report a problem needs a note",
         "Supplier Hub → a placed order (ask Ben for a new one)",
         "Press Report a problem with the note empty; then type a note and press it again.",
         "First: 'Describe the problem…'. Then: 'Problem sent to the contractor. The order is on hold until they answer.'"),
    _uat("uat-s05-address", "s05", "The site address arrives with the order",
         "Supplier Hub → the Harbour Lane material order",
         "Read Deliver to.", "'14 Harbour Lane, Merrickville, ON' and the site contact are shown on the order."),

    _uat("uat-s06-supplier-change", "s06", "Ask to move a delivery",
         "Supplier Hub → the confirmed concrete order → Delivery → Change the delivery",
         "New date +1 day, 10:00–12:00, Supplier availability, note, press Send the change to the contractor.",
         "'The current delivery stands until they accept'; Ben sees the change and can accept; then the agreed date is the new one."),
    _uat("uat-s06-answer-change", "s06", "Answer a contractor's change",
         "Supplier Hub → Delivery changes waiting for your answer",
         "Open the order and press Accept <date>.",
         "'Answer sent to the contractor.' and 'Agreed delivery: <new date>'; Ben's page shows the same date."),
    _uat("uat-s06-delivered", "s06", "Mark an order delivered",
         "Supplier Hub → a confirmed order → Mark delivered",
         "Keep today's date, type a note, press Mark delivered.",
         "'Order PO-… marked delivered.'; it leaves Deliveries; Ben's page says Delivered, recorded by you."),

    _uat("uat-s07-sku-prefill", "s07", "Remembered SKUs are filled in, prices are not",
         "Supplier Hub → a new request for products you quoted before (after Ben recorded your earlier quote)",
         "Open the request.",
         "Each remembered SKU is filled in with 'Your confirmed SKU — check it'; every Unit cost and Discount % is empty."),
    _uat("uat-s07-demand", "s07", "Material demand counts the requests",
         "Supplier Hub → Material demand → This month",
         "Read the tiles and the Requested materials table.",
         "Requests sent to you matches the training requests; the line you left unpriced shows 'You priced' less than "
         "its requests."),

    _uat("uat-s08-settings", "s08", "Quote settings remove the blocker",
         "PRO Desk quotations (no settings yet)",
         "Open Quote settings, enter HST, 13, 30 days, press Save settings, go back to PRO Desk quotations.",
         "'Quote settings saved.' and 'Before the first quotation' is gone.", ALL_SUPPLIER),
    _uat("uat-s08-price-file", "s08", "Load a price file",
         "PRO Desk quotations → Price file",
         "Load the training CSV with Authorized by filled.",
         "'8 prices loaded; 0 rows not loaded' and a new row in Loaded files.", ALL_SUPPLIER),
    _uat("uat-s08-bad-row", "s08", "A bad price row is listed, never guessed",
         "PRO Desk quotations → Price file",
         "Load a CSV where one row's price is 'abc'.",
         "That row is not loaded and is listed with 'price is not a number'; the other rows load.", ALL_SUPPLIER),

    _uat("uat-s09-quick-quote", "s09", "Quick Quote prices a building",
         "PRO Desk quotations → Quick Quote",
         "Enter the training walk-in (30 × 40 ft, 12 ft, pitch 4, two doors, no floor, the sketch), press Price this building.",
         "The quotation opens at 5 · Pricing with the sketch kept and the lines priced from the price file.",
         ALL_SUPPLIER),
    _uat("uat-s09-issue", "s09", "Issue a quotation",
         "The training quotation → 6 · Quotation",
         "Leave the trusses out with a reason and press Issue the quotation.",
         "'Quotation Q… issued: $… including tax, valid until …' and the Quotation PDF opens.", ALL_SUPPLIER),
    _uat("uat-s09-customer-link", "s09", "The customer accepts on a phone",
         "The issued quotation → 7 · Customer approval",
         "Press Create approval link, open the link on a phone, type the name, tick the box, press Accept.",
         "'Thank you — accepted'; the PRO Desk shows 'Accepted by … (approval link)'.", ALL_SUPPLIER),
    _uat("uat-s09-order", "s09", "Prepare the order sheet",
         "The accepted quotation → 8 · Order-ready package",
         "Press Prepare the order for entry, then Order CSV.",
         "The order sheet lists the accepted SKUs, quantities and prices; the CSV downloads with the same total.",
         ALL_SUPPLIER),

    _uat("uat-s10-full-cycle", "s10", "Complete contractor cycle",
         "Supplier Hub → a new Harbour Lane request from Ben",
         "Quote it, confirm the order, accept a delivery change and mark it delivered.",
         "The request's History lists Sent, Opened, Returned, Order confirmed, the change accepted and Order delivered, "
         "each with your name."),
    _uat("uat-s10-other-store", "s10", "Another store's pages are not found",
         "Supplier Hub, signed in as yourself",
         "Change the store number in the address (for example /supplier/999/) and open it.",
         "'Not Found': you can open only your own store's pages.", ALL_SUPPLIER),
    _uat("uat-s10-walk-in", "s10", "Walk-in from sketch to order without help",
         "PRO Desk quotations", "Quote a new training walk-in from Quick Quote to the order sheet.",
         "Issued, accepted through the customer link, and the order sheet prepared.", ALL_SUPPLIER),
)
