import {Footer, Header} from "../site";

const workflow = [
  ["Understand the project", "Plans, specifications, scope, selections, assumptions and project questions become one clear project record."],
  ["Build the takeoff", "CalibraytAI develops material quantities and labour requirements directly from the work being priced."],
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
  ["Suppliers", "Complete material requirements move directly into product costing, ordering and delivery coordination."],
  ["Management", "Estimated, actual and forecast cost, schedule and margin remain connected from start to finish."],
] as const;

export default function ContractorConnection(){
  return <><Header active="contractor"/><main className="supplier-page">
    <section className="supplier-hero connection-hero"><div className="wrap"><div className="connection-hero-copy"><p className="kicker">THE COMPLETE CONTRACTOR CONNECTION</p><h1>Contractor Connection</h1><p>Build the project once. CalibraytAI carries it from the first plan through final results.</p><p className="supplier-hero-detail">CalibraytAI connects plans, takeoffs, supplier and subcontractor costing, labour, estimates, approvals, contracts, purchasing, field execution and project performance through one authoritative project record.</p></div><div className="connection-hero-visual"><img src="/calibraytai-contractor-connection-hero-v1.png" alt="Residential plans connected through CalibraytAI to a completed home" /></div></div></section>

    <section className="section light"><div className="wrap"><p className="eyebrow">ONE PROJECT RECORD</p><h2>Every part of the contractor’s work stays connected.</h2><p className="lede supplier-lede">The contractor develops the project once. CalibraytAI carries the same scope, quantities, costs and decisions forward through estimating, contracting, purchasing, construction and performance review.</p><div className="cards supplier-cards"><div className="card"><h3>Less administrative work</h3><p>Project information moves forward automatically instead of being copied into disconnected spreadsheets, documents and systems.</p></div><div className="card"><h3>Faster project decisions</h3><p>Current scope, costs, supplier information, approvals and commitments remain visible in one place.</p></div><div className="card"><h3>Stronger project control</h3><p>The contractor sees how each decision affects cost, schedule, purchasing and margin before and during construction.</p></div></div></div></section>

    <section className="section dark"><div className="wrap"><p className="eyebrow">THE CONNECTED CONTRACTOR WORKFLOW</p><h2>PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN</h2><p className="lede supplier-lede">Approval gates move one complete project record through every stage of the construction lifecycle.</p><div className="supplier-workflow">{workflow.map(([title,text],index)=><div className="supplier-step" key={title}><span>{index+1}</span><div><h3>{title}</h3><p>{text}</p></div></div>)}</div></div></section>

    <section className="section mist"><div className="wrap"><p className="eyebrow">VALUE FOR CONTRACTORS</p><h2>Estimate faster. Build with control. Learn from every job.</h2><p className="lede supplier-lede">CalibraytAI reduces repeated office work while giving the contractor a clearer view of project cost, commitments, progress and margin.</p><div className="feature-list">{contractorValue.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section light"><div className="wrap"><p className="eyebrow">ONE CONNECTION FOR THE WHOLE TEAM</p><h2>Office, field, suppliers and customers work from the same project.</h2><p className="lede supplier-lede">Each participant receives the information needed for the work while the contractor maintains one connected commercial and construction record.</p><div className="feature-list">{teamValue.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section dark"><div className="wrap"><p className="eyebrow">AUTOMATED PROJECT CONNECTION</p><h2>Approval turns project intelligence into action.</h2><p className="lede supplier-lede">CalibraytAI automates the repetitive work between approval gates. The estimate produces the documents, supplier requirements and project records that move the job forward.</p><div className="supplier-workflow"><div className="supplier-step"><span>1</span><div><h3>Complete estimating package</h3><p>Internal costs, customer pricing, supplier requirements and accounting-ready information come from one estimate.</p></div></div><div className="supplier-step"><span>2</span><div><h3>Approval-driven handoff</h3><p>Approved scope and pricing move into contracts, warranty documents, purchasing and construction preparation.</p></div></div><div className="supplier-step"><span>3</span><div><h3>Continuous project control</h3><p>Actual labour, materials, cost, schedule and margin remain connected to the original estimate while the project is built.</p></div></div></div></div></section>

    <section className="section light"><div className="wrap"><p className="eyebrow">CONSTRUCTION INTELLIGENCE</p><h2>Every completed project makes the contractor stronger.</h2><p className="lede supplier-lede">CalibraytAI preserves the contractor’s real labour, material, cost, schedule, change and margin results. That experience becomes company-specific intelligence applied to the next project.</p></div></section>

    <section className="quote-band supplier-cta"><strong>One project. One connected contractor system.</strong><p>From plans and pricing through construction performance and company learning.</p><a className="btn primary" href="/employment-vs-entrepreneurship/">Compare Employment &amp; Entrepreneurship</a></section>
  </main><Footer/></>
}
