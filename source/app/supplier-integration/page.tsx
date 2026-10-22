import {Footer, Header, LINKS, StatusBadge} from "../site";

const workflow = [
  ["Contractor completes the front-end work", "The contractor builds the project scope, material takeoff and quantities once, inside CalibraytAI."],
  ["Contractor chooses the supplier and sends the request", "The contractor selects the supplier account and sends the material request. The supplier sees only what the contractor sends."],
  ["Supplier quotes in the Supplier Hub", "The supplier enters the product SKU, unit price and discount for each line on screen, or uploads the filled request. SKUs quoted before for the same product are filled in for checking; prices never are."],
  ["Contractor approves the quotation", "The quotation lands on the contractor’s project, where the contractor records it and approves it."],
  ["Purchase order and confirmation", "The contractor’s purchase order accepts the quotation. The supplier’s confirmation completes the agreement."],
  ["Delivery coordination", "Delivery dates, delivery changes and their answers, and the delivered order stay connected to the project and show on the contractor’s calendar."],
] as const;

const supplierValue = [
  ["Receive the front-end work complete", "The material request arrives organized by line, with quantities, units and project details already set out by the contractor."],
  ["Eliminate repeated takeoffs", "Price the contractor’s requirement instead of recreating quantities from plans, notes and spreadsheets."],
  ["Quote from one screen", "Enter SKUs, prices, discounts and how long the quotation is valid in the Supplier Hub, or upload the filled request."],
  ["Receive clear purchase orders", "Orders follow from the quotation the contractor approved, so products, quantities and prices match what was quoted."],
  ["Coordinate deliveries", "Confirm orders, answer delivery changes and mark orders delivered. Text alerts can tell staff when an order is placed or a delivery change is asked for."],
  ["See the demand", "The Supplier Hub dashboard and material demand page show which contractors sent requests, what was asked for by product, what was priced and what was ordered."],
] as const;

const contractorValue = [
  ["Save hours on every estimate", "Build the material takeoff once and carry it through supplier pricing, project costing, ordering and delivery."],
  ["Use supplier quotations in the estimate", "Bring the supplier’s quoted products and prices back into the project without separate calls, emails or spreadsheets."],
  ["Reduce missed materials", "Keep scope, quantities, supplier products and estimate costing connected from the beginning."],
  ["Move directly into purchasing", "Turn the approved quotation into a purchase order without rebuilding it in another system."],
  ["Control project cash flow", "Organize purchases and deliveries around the work sequence instead of receiving the entire material package at once."],
  ["Keep the project moving", "Agreed deliveries and delivery changes appear on the Company Calendar beside the work they support."],
] as const;

const hubToday = [
  ["Supplier Hub", "A separate sign-in for supplier staff, with requests, quotations, orders, deliveries and a dashboard for the supplier’s own account."],
  ["Contractor-authorized material requests", "Deck material requests and concrete requests the contractor chooses to send. Nothing else from the contractor’s company is visible."],
  ["Supplier quotations", "Prices, SKUs, discounts and valid-until dates entered by the supplier and returned to the contractor’s project."],
  ["Purchase orders and confirmations", "The contractor’s purchase order and the supplier’s confirmation, recorded on both sides."],
  ["Delivery coordination", "Delivery changes asked and answered, orders marked delivered, and text alerts for supplier staff."],
  ["Supplier catalogues and selling prices", "The supplier loads its own price file of products and selling prices for use at the PRO Desk."],
] as const;

const proDesk = [
  ["Quick Quote and detailed quotations", "Counter staff prepare a quotation for a walk-in customer, from a quick quote to a guided, line-by-line quotation."],
  ["Post-frame buildings first", "Guided questions and a material takeoff for post-frame (pole barn) buildings with steel roof and wall cladding. Stick-framed and steel-frame buildings are not offered yet."],
  ["Priced from the supplier’s own price file", "Lines are priced from the supplier’s loaded price file. A line without a price shows as needing one; nothing is guessed."],
  ["Quotation, drawing and order", "Issue the quotation as a PDF with a drawing, record the customer’s acceptance and prepare the order."],
] as const;

export default function SupplierIntegration(){
  return <><Header active="supplier"/><main className="supplier-page">
    <section className="supplier-hero connection-hero"><div className="wrap"><div className="connection-hero-copy"><p className="kicker">THE CONTRACTOR–SUPPLIER CONNECTION</p><h1>Supplier Connection</h1><p>The contractor does the project work once. CalibraytAI carries it to the supplier the contractor chooses.</p><p className="supplier-hero-detail">The contractor’s takeoff becomes a clear material request. In the Supplier Hub the supplier quotes it, receives the purchase order, confirms it and coordinates delivery, all connected to the same project and without rebuilding the takeoff.</p></div><div className="connection-hero-visual"><img src="/calibraytai-supplier-connection-hero-v1.png" alt="Project plans connected through CalibraytAI to supplier materials and delivery" /></div></div></section>

    <section className="section light"><div className="wrap"><p className="eyebrow">THE WORK IS COMPLETED ONCE</p><h2>The supplier receives the contractor’s front-end work—ready to price.</h2><p className="lede supplier-lede">The contractor completes the scope, takeoff and quantities inside CalibraytAI and sends the material request to the supplier they choose. The supplier prices that request in the Supplier Hub instead of rebuilding the project.</p><div className="cards supplier-cards"><div className="card"><h3>Contractor work completed</h3><p>The takeoff and quantities become one organized material request.</p></div><div className="card"><h3>Sent by the contractor’s choice</h3><p>The contractor decides which supplier receives which request. The supplier sees only what is sent.</p></div><div className="card"><h3>Approval gates move it forward</h3><p>Quotation, purchase order, confirmation and delivery each move forward when the right person approves them.</p></div></div></div></section>

    <section className="section dark"><div className="wrap"><p className="eyebrow">CONNECTED THROUGH APPROVAL GATES</p><h2>Contractor work → Supplier quotation → Approval → Order → Delivery</h2><p className="lede supplier-lede">CalibraytAI removes the repeated work between each approval gate. Both businesses stay connected while the material process moves from the contractor’s request to the supplier’s delivery.</p><div className="supplier-workflow">{workflow.map(([title,text],index)=><div className="supplier-step" key={title}><span>{index+1}</span><div><h3>{title}</h3><p>{text}</p></div></div>)}</div></div></section>

    <section className="section mist"><div className="wrap"><p className="eyebrow">VALUE FOR SUPPLIERS</p><h2>The supplier starts where the contractor’s work ends.</h2><p className="lede supplier-lede">The supplier spends less time on takeoffs and order entry, and more on products, availability, fulfillment and service.</p><div className="feature-list">{supplierValue.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section light"><div className="wrap"><p className="eyebrow">VALUE FOR CONTRACTORS</p><h2>Estimate faster and move directly toward delivery.</h2><p className="lede supplier-lede">CalibraytAI keeps the project scope, material takeoff, supplier quotation, approved order and delivery schedule connected in one project workflow.</p><div className="feature-list">{contractorValue.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section mist" id="supplier-hub"><div className="wrap"><p className="eyebrow">THE SUPPLIER HUB TODAY</p><h2>What suppliers use in CalibraytAI now.</h2><p className="lede supplier-lede">Supplier staff sign in to their own Supplier Hub. Each supplier sees its own account and the requests contractors have sent it, never another supplier’s work.</p><div className="status-row"><StatusBadge status="released"/></div><div className="feature-list">{hubToday.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section light" id="pro-desk"><div className="wrap"><p className="eyebrow">SUPPLIER PRO DESK</p><h2>Walk-in quotations at the supplier’s counter.</h2><p className="lede supplier-lede">The PRO Desk is for the supplier’s own walk-in customers. Those quotations belong to the supplier: contractors never see them, and nothing at the PRO Desk shows a contractor’s records.</p><div className="status-row"><StatusBadge status="released"/></div><div className="feature-list">{proDesk.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section dark" id="privacy"><div className="wrap"><p className="eyebrow">INDEPENDENCE AND PRIVACY</p><h2>The contractor’s business stays the contractor’s.</h2><p className="lede supplier-lede">CalibraytAI connects contractors and suppliers without either one giving up control of its own commercial information.</p><div className="supplier-workflow"><div className="supplier-step"><span>1</span><div><h3>Contractor independence</h3><p>The contractor chooses which supplier receives each request and can work with more than one supplier.</p></div></div><div className="supplier-step"><span>2</span><div><h3>Commercial privacy</h3><p>Suppliers never see the contractor’s internal costs, margins, labour rates or other suppliers’ quotations.</p></div></div><div className="supplier-step"><span>3</span><div><h3>Account portability</h3><p>The contractor’s CalibraytAI company, projects and records belong to the contractor, whichever suppliers they buy from.</p></div></div></div></div></section>

    <section className="section mist" id="sponsored-access"><div className="wrap"><p className="eyebrow">SUPPLIER-SPONSORED CONTRACTOR ACCESS</p><h2>A concept we are developing with the industry.</h2><p className="lede supplier-lede">We are exploring a model in which a supplier could sponsor CalibraytAI PRO accounts for the contractors it serves. It is a concept in development, not an offer: no supplier program or partnership has been agreed. Any program would keep the contractor’s account independent and portable, keep the contractor free to buy from any supplier, and keep the contractor’s commercial information private.</p><div className="status-row"><StatusBadge status="concept"/></div></div></section>

    <section className="section light" id="supplier-training"><div className="wrap"><p className="eyebrow">SUPPLIER TRAINING</p><h2>Learn the Supplier Hub step by step.</h2><p className="lede supplier-lede">Supplier Training in the CalibraytAI Training Centre walks supplier staff through requests, quotations, orders and deliveries, with an interactive Supplier Workflow Map, using made-up training records.</p><div className="status-row"><StatusBadge status="released"/></div><div className="signin-band"><a className="btn primary" href={LINKS.training}>Open the Training Centre</a><a className="btn outline" href={LINKS.supplier}>Supplier Hub sign-in</a></div></div></section>

    <section className="section mist"><div className="wrap"><p className="eyebrow">A STRONGER SUPPLIER RELATIONSHIP</p><h2>Both businesses save time on every project.</h2><p className="lede supplier-lede">Contractors bring complete requirements and purchasing demand to the supplier earlier. Suppliers respond faster, prepare more accurate material packages and coordinate fulfillment with greater visibility. The result is a closer working relationship built around cleaner information and more efficient service.</p></div></section>

    <section className="quote-band supplier-cta"><strong>One takeoff. One estimate. One supplier connection.</strong><p>From the contractor’s material request and the supplier’s quotation to approved orders and coordinated deliveries.</p><div className="actions cta-actions"><a className="btn primary" href={LINKS.supplier}>Supplier Hub sign-in</a><a className="btn primary" href="/plan">Start with PLAN</a></div></section>
  </main><Footer/></>
}
