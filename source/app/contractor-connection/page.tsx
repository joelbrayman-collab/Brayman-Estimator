import {Footer, Header, LINKS, StatusBadge} from "../site";

const workflow = [
  ["Understand the project", "Plans, specifications, scope, selections, assumptions and project questions become one clear project record."],
  ["Build the takeoff", "Drawing uploads, material takeoffs and construction calculators turn the plans into the quantities and labour for the work being priced."],
  ["Connect real project costs", "Supplier pricing, subcontract quotations, labour, equipment and allowances flow into the estimate."],
  ["Complete the estimate", "Direct costs, labour hours, overhead, margin and customer pricing are calculated and reconciled together."],
  ["Approval moves the project forward", "Approval gates create the customer proposal, contract, warranty, purchasing requirements and office-ready records."],
  ["Build, monitor and learn", "Field progress, actual costs, schedule and margin stay connected—and every completed project improves the next estimate."],
] as const;

const contractorValue = [
  ["Save estimating hours", "Carry project information forward instead of rebuilding scope, quantities and costs in separate spreadsheets and documents."],
  ["Price with confidence", "Connect materials, labour, subcontractors, allowances, overhead and margin in one complete estimate."],
  ["Protect project margin", "See the relationship between estimated cost, customer price and actual performance throughout the job."],
  ["Move from estimate to contract", "Turn approved scope and pricing into the customer proposal, construction contract and warranty package."],
  ["Connect office and field", "Give the team one project record for commitments, changes, progress, actual costs and project decisions."],
  ["Build company intelligence", "Turn completed-project results into practical knowledge for future estimates, schedules and risk decisions."],
] as const;

const teamValue = [
  ["Estimator", "Plans, takeoffs, supplier costs, labour and pricing stay together while the project is developed."],
  ["Office", "Approved project information moves into proposals, contracts, purchasing and accounting-ready records."],
  ["Field", "Scope, selections, commitments, materials, schedule and changes remain visible while the work is built."],
  ["Customer", "Clear scope, pricing, allowances, exclusions, contracts and changes come from the same approved project."],
  ["Suppliers", "Contractor-authorized material requests move into supplier quotations, purchase orders and delivery coordination."],
  ["Management", "Estimated, actual and forecast cost, schedule and margin remain connected from start to finish."],
] as const;

const platformToday = [
  ["Drawings and material takeoffs", "Upload the plan PDFs to the project, review the permit report, and build material takeoffs for supported work such as decks and ICF foundation walls."],
  ["Construction calculators", "Concrete, footings, stairs, ICF wall forms, wall framing, roofing, siding, drywall and flooring calculators, built into the platform."],
  ["Estimating, labour and material costing", "Estimate versions with material, labour and subcontract lines. Scope review confirms who supplies and who installs before costing is approved, and your pricing policy sets the customer price."],
  ["Supplier selection and quotations", "Choose the supplier, send the material request through the Supplier Hub, then record and approve the quotation that comes back."],
  ["Customer proposals and contracts", "Create the customer proposal from the estimate, share it by private link, record acceptance and generate the construction contract from the accepted work."],
  ["Change orders and approvals", "Record extra work and change orders against the project so scope, price and approvals stay with the job."],
  ["Company Calendar and My Calendar", "The whole company’s work, crews, appointments and deliveries in one calendar, and each person’s own day, week and month."],
  ["Project scheduling and crew assignments", "Schedule each piece of work, assign a crew or a person, and move a project’s dates together when the job shifts."],
  ["Personal and company appointments", "Site visits, client meetings, supplier meetings and estimate consultations. Personal appointments are seen only by the person who made them."],
  ["Field schedules and time entry", "Crews open today’s, this week’s and this month’s work on the phone, capture notes, photos and voice, and enter their time for the office to approve."],
  ["Project labour and cost performance", "Compare the committed estimate with the actual direct costs entered for the project while the job is underway."],
  ["Purchasing, deliveries and closeout", "Place purchase orders from approved quotations, follow confirmations and deliveries, answer delivery changes, and close the job with a punch list and final walkthrough. A QuickBooks-ready entry sheet is produced for the office."],
  ["Cal Assistant", "Ask Cal to find a project, estimate, proposal, order, delivery or appointment, or how to do something. Cal only reads what you can already open; it never changes a record."],
] as const;

const calendarPoints = [
  ["Company Calendar", "Every scheduled job, crew assignment, company appointment and supplier delivery, in Day, Week or Month view. Filter to one project when you need to."],
  ["My Calendar", "Your own work and appointments, including personal ones that no one else in the company can see."],
  ["Project scheduling and crew assignments", "Put each piece of work on the calendar, assign the crew, and move a project’s dates together when the job shifts."],
  ["Appointments and site visits", "Site visits, client meetings, supplier meetings and estimate consultations, linked to the client or project. Changes and cancellations are kept in the appointment’s history."],
  ["Delivery coordination", "Deliveries agreed with the supplier, and delivery changes still waiting for an answer, show on the calendar beside the work they support."],
  ["Field schedule visibility", "Crews see Today, This week and This month on the phone, with the job address and directions."],
  ["Your own calendar app", "Subscribe from Apple Calendar, Google Calendar or Outlook to your private CalibraytAI address. It is a one-way feed: you make and change appointments in CalibraytAI, and they appear in your calendar app when that app refreshes. Any single appointment can also be downloaded as a calendar file."],
] as const;

const screens = [
  ["/app-screens/calendar-company-week-desktop.png", "Company Calendar, Week view: scheduled work for each crew across the top, appointments by the hour", "Company Calendar · Week", "wide"],
  ["/app-screens/calendar-my-day-phone.png", "My Calendar on a phone, Day view, showing a site visit at 8 AM", "My Calendar · Day, on the phone", "phone"],
  ["/app-screens/calendar-company-month-desktop.png", "Company Calendar, Month view: framing, foundation and slab work spread over the month with appointments and a colour legend", "Company Calendar · Month", "wide"],
  ["/app-screens/field-week-phone.png", "Field This week on a crew member’s phone, showing the project, address, Directions button and the crew’s assigned work", "Field · This week", "phone"],
  ["/app-screens/calendar-appointment-desktop.png", "Appointment form: company or personal, title, type, date, start and end time, location and who it is for", "An appointment", "wide"],
  ["/app-screens/field-month-phone.png", "Field This month on a phone, with the days that have work marked", "Field · This month", "phone"],
  ["/app-screens/calendar-connection-desktop.png", "Calendar connection page explaining the private one-way calendar feed for Outlook, Google Calendar or Apple Calendar", "Calendar connection for Outlook, Google and Apple Calendar", "wide"],
] as const;

const nextRelease = [
  ["Field time and labour cost", "My Time for every crew member, office approval, labour cost from approved hours compared with the estimate, shop time, and an hours file for QuickBooks."],
  ["Workflow Guide in the platform", "The interactive Contractor, Supplier and Field Workflow Maps, opened from inside the platform."],
  ["Field Crew Training", "A third Training Centre pathway for the crew: Field, time entry, My Time and corrections."],
] as const;

export default function ContractorConnection(){
  return <><Header active="contractor"/><main className="supplier-page">
    <section className="supplier-hero connection-hero"><div className="wrap"><div className="connection-hero-copy"><p className="kicker">THE COMPLETE CONTRACTOR CONNECTION</p><h1>Contractor Connection</h1><p>Build the project once. CalibraytAI carries it from the first plan through final results.</p><p className="supplier-hero-detail">CalibraytAI connects plans, takeoffs, supplier and subcontractor costing, labour, estimates, approvals, contracts, purchasing, field execution and project performance through one authoritative project record.</p></div><div className="connection-hero-visual"><img src="/calibraytai-contractor-connection-hero-v1.png" alt="Residential plans connected through CalibraytAI to a completed home" /></div></div></section>

    <section className="section light"><div className="wrap"><p className="eyebrow">ONE PROJECT RECORD</p><h2>Every part of the contractor’s work stays connected.</h2><p className="lede supplier-lede">The contractor develops the project once. CalibraytAI carries the same scope, quantities, costs and decisions forward through estimating, contracting, purchasing, construction and performance review.</p><div className="cards supplier-cards"><div className="card"><h3>Less administrative work</h3><p>Project information moves forward automatically instead of being copied into disconnected spreadsheets, documents and systems.</p></div><div className="card"><h3>Faster project decisions</h3><p>Current scope, costs, supplier information, approvals and commitments remain visible in one place.</p></div><div className="card"><h3>Stronger project control</h3><p>The contractor sees how each decision affects cost, schedule, purchasing and margin before and during construction.</p></div></div></div></section>

    <section className="section dark"><div className="wrap"><p className="eyebrow">THE CONNECTED CONTRACTOR WORKFLOW</p><h2>PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN</h2><p className="lede supplier-lede">Approval gates move one complete project record through every stage of the construction lifecycle.</p><div className="supplier-workflow">{workflow.map(([title,text],index)=><div className="supplier-step" key={title}><span>{index+1}</span><div><h3>{title}</h3><p>{text}</p></div></div>)}</div></div></section>

    <section className="section mist" id="platform-today"><div className="wrap"><p className="eyebrow">IN THE PLATFORM TODAY</p><h2>What a contractor runs in CalibraytAI now.</h2><p className="lede supplier-lede">These are working parts of the contractor platform today, from the first drawing to the closed job.</p><div className="status-row"><StatusBadge status="released"/></div><div className="feature-list">{platformToday.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section light calendar-section" id="calendar"><div className="wrap"><p className="eyebrow">COMPANY CALENDAR AND MY CALENDAR</p><h2>One connected place to organize jobs, people, appointments and deliveries.</h2><p className="lede supplier-lede">The office sees the whole company. Each person sees their own day. The crew sees their work on the phone. Scheduled work, crew assignments, appointments and supplier deliveries all come from the same project records, so nobody keeps a second calendar to stay in step.</p><div className="status-row"><StatusBadge status="released"/></div><div className="feature-list">{calendarPoints.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div><p className="fine-print">The calendar feed is one-way and read-only. Nothing typed in Outlook, Google or Apple Calendar comes back into CalibraytAI, and CalibraytAI never asks for your Google, Microsoft or Apple password. Apple Calendar can refresh as often as every 5 minutes; Google and Outlook choose their own refresh time, usually within a few hours. The crew’s job schedule stays in Field rather than in the feed.</p><div className="screens">{screens.map(([src,alt,caption,kind])=><figure className={`shot shot-${kind}`} key={src}><img src={src} alt={alt} loading="lazy"/><figcaption>{caption}</figcaption></figure>)}</div><p className="fine-print">Actual CalibraytAI screens with sample data. The company, people, clients and addresses are made up.</p></div></section>

    <section className="section mist"><div className="wrap"><p className="eyebrow">VALUE FOR CONTRACTORS</p><h2>Estimate faster. Build with control. Learn from every job.</h2><p className="lede supplier-lede">CalibraytAI reduces repeated office work while giving the contractor a clearer view of project cost, commitments, progress and margin.</p><div className="feature-list">{contractorValue.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section light"><div className="wrap"><p className="eyebrow">ONE CONNECTION FOR THE WHOLE TEAM</p><h2>Office, field, suppliers and customers work from the same project.</h2><p className="lede supplier-lede">Each participant receives the information needed for the work while the contractor maintains one connected commercial and construction record.</p><div className="feature-list">{teamValue.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section dark"><div className="wrap"><p className="eyebrow">AUTOMATED PROJECT CONNECTION</p><h2>Approval turns project intelligence into action.</h2><p className="lede supplier-lede">CalibraytAI automates the repetitive work between approval gates. The estimate produces the documents, supplier requirements and project records that move the job forward.</p><div className="supplier-workflow"><div className="supplier-step"><span>1</span><div><h3>Complete estimating package</h3><p>Internal costs, customer pricing, supplier requirements and accounting-ready information come from one estimate.</p></div></div><div className="supplier-step"><span>2</span><div><h3>Approval-driven handoff</h3><p>Approved scope and pricing move into contracts, warranty documents, purchasing and construction preparation.</p></div></div><div className="supplier-step"><span>3</span><div><h3>Continuous project control</h3><p>Actual labour, materials, cost, schedule and margin remain connected to the original estimate while the project is built.</p></div></div></div></div></section>

    <section className="section light"><div className="wrap"><p className="eyebrow">CONSTRUCTION INTELLIGENCE</p><h2>Every completed project makes the contractor stronger.</h2><p className="lede supplier-lede">CalibraytAI preserves the contractor’s real labour, material, cost, schedule, change and margin results. That experience becomes company-specific intelligence applied to the next project.</p></div></section>

    <section className="section mist" id="training"><div className="wrap"><p className="eyebrow">TRAINING AND GETTING STARTED</p><h2>Learn it the way the work is done.</h2><p className="lede supplier-lede">Getting Started in the platform walks a new company through its first setup. The CalibraytAI Training Centre teaches each role step by step, using made-up training records rather than real jobs.</p><div className="cards supplier-cards"><div className="card"><StatusBadge status="released"/><h3>Contractor Training</h3><p>The contractor pathway in the Training Centre, from the first project through estimate, proposal, purchasing, schedule and closeout.</p></div><div className="card"><StatusBadge status="released"/><h3>Workflow Maps</h3><p>Interactive Contractor and Supplier Workflow Maps in the Training Centre show every stage in order and what comes next.</p></div><div className="card"><StatusBadge status="released"/><h3>Getting Started</h3><p>Onboarding guidance inside the platform, with Help on each main screen that says what the screen is for and what to do next.</p></div></div><div className="signin-band"><a className="btn primary" href={LINKS.training}>Open the Training Centre</a><a className="btn outline" href={LINKS.contractor}>Contractor sign-in</a></div></div></section>

    <section className="section light" id="next-release"><div className="wrap"><p className="eyebrow">ROLLING OUT NEXT</p><h2>Coming in the next release.</h2><p className="lede supplier-lede">These are built and in final release checks. They are not yet part of the live contractor platform.</p><div className="status-row"><StatusBadge status="next"/></div><div className="feature-list">{nextRelease.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div><p className="fine-print">Not offered today: two-way sync with Outlook, Google or Apple Calendar, and a direct QuickBooks connection. CalibraytAI produces QuickBooks-ready sheets for the office to enter; it does not send anything to QuickBooks.</p></div></section>

    <section className="quote-band supplier-cta"><strong>One project. One connected contractor system.</strong><p>From plans and pricing through construction performance and company learning.</p><div className="actions cta-actions"><a className="btn primary" href={LINKS.contractor}>Contractor sign-in</a><a className="btn primary" href="/employment-vs-entrepreneurship/">Compare Employment &amp; Entrepreneurship</a></div></section>
  </main><Footer/></>
}
