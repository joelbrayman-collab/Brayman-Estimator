import {Footer, Header} from "../site";

const workflow = [
  ["Contractor completes the front-end work", "CalibraytAI develops the project scope, material takeoff, quantities, selections and estimate once."],
  ["CalibraytAI submits the requirement", "The complete plan, takeoff and material requirement are automatically delivered into the supplier connection."],
  ["Supplier products and costs are matched", "The supplier’s catalogue, SKUs, contractor pricing and availability are automatically applied to the project."],
  ["Approval gate confirms the package", "The contractor and supplier confirm products, quantities, costing and availability from the same connected information."],
  ["Estimate approval releases the order", "CalibraytAI automatically converts the approved material package into a complete supplier order."],
  ["Approval gate coordinates delivery", "Picking, loading, delivery groups and scheduling are organized around the contractor’s construction sequence."],
] as const;

const supplierValue = [
  ["Receive the front-end work complete", "The contractor submits the project plan, takeoff, quantities, selections and estimate as one organized material requirement."],
  ["Eliminate repeated takeoffs", "Use the contractor-prepared requirement without recreating quantities from plans, notes and spreadsheets."],
  ["Automate product matching", "Connect project requirements to the supplier’s catalogue, products and SKUs through one consistent process."],
  ["Quote customers faster", "Apply contractor-specific pricing and availability directly to a clean, structured material list."],
  ["Receive cleaner orders", "Approved requirements arrive as organized supplier orders with clearer quantities, products and project information."],
  ["Coordinate better deliveries", "Schedule delivery groups around the contractor’s construction sequence and changing project needs."],
] as const;

const contractorValue = [
  ["Save hours on every estimate", "Build the material takeoff once and carry it through supplier pricing, project costing, ordering and delivery."],
  ["Use supplier-connected costing", "Bring contractor-specific product pricing and availability into the estimate without separate calls, emails or spreadsheets."],
  ["Reduce missed materials", "Keep scope, quantities, supplier products and estimate costing connected from the beginning."],
  ["Move directly into purchasing", "Turn the approved material requirement into a supplier order without rebuilding it in another system."],
  ["Control project cash flow", "Organize purchases and deliveries around the work sequence instead of receiving the entire material package at once."],
  ["Keep the project moving", "Coordinate supplier fulfillment and delivery timing with the schedule used to build the job."],
] as const;

export default function SupplierIntegration(){
  return <><Header active="supplier"/><main className="supplier-page">
    <section className="supplier-hero connection-hero"><div className="wrap"><div className="connection-hero-copy"><p className="kicker">THE CONTRACTOR–SUPPLIER CONNECTION</p><h1>Supplier Integration</h1><p>The contractor does the project work once. CalibraytAI carries it through the entire supplier process.</p><p className="supplier-hero-detail">CalibraytAI automatically transforms the contractor’s plans, takeoff and estimate into a complete supplier requirement. Products, costing, approval gates, ordering and scheduled deliveries remain connected—dramatically reducing the supplier’s takeoff and administrative workload.</p></div><div className="connection-hero-visual"><img src="/calibraytai-supplier-connection-hero-v1.png" alt="Project plans connected through CalibraytAI to supplier materials and delivery" /></div></div></section>

    <section className="section light"><div className="wrap"><p className="eyebrow">THE WORK IS COMPLETED ONCE</p><h2>The supplier receives the contractor’s front-end work—ready to process.</h2><p className="lede supplier-lede">The contractor completes the plans, scope, takeoff, quantities, selections and estimate inside CalibraytAI. The platform automatically submits that complete material requirement to the supplier, where products, costs and availability are matched without rebuilding the project.</p><div className="cards supplier-cards"><div className="card"><h3>Contractor work completed</h3><p>The project plan, takeoff and estimate become one complete supplier-ready material requirement.</p></div><div className="card"><h3>Automatic supplier submission</h3><p>CalibraytAI delivers the organized requirement directly into the supplier’s product and costing process.</p></div><div className="card"><h3>Approval gates move it forward</h3><p>Products, costing, ordering and delivery advance automatically as each project decision is approved.</p></div></div></div></section>

    <section className="section dark"><div className="wrap"><p className="eyebrow">AUTOMATED WITH APPROVAL GATES</p><h2>Contractor work → Supplier costing → Approval → Order → Delivery</h2><p className="lede supplier-lede">CalibraytAI automates the repetitive work between each approval gate. Both businesses stay connected while the material process moves from completed contractor requirements to scheduled supplier delivery.</p><div className="supplier-workflow">{workflow.map(([title,text],index)=><div className="supplier-step" key={title}><span>{index+1}</span><div><h3>{title}</h3><p>{text}</p></div></div>)}</div></div></section>

    <section className="section mist"><div className="wrap"><p className="eyebrow">VALUE FOR SUPPLIERS</p><h2>The supplier starts where the contractor’s work ends.</h2><p className="lede supplier-lede">CalibraytAI dramatically reduces supplier takeoff, estimating, costing and order-entry work. The supplier receives complete project information and concentrates on product availability, fulfillment and service.</p><div className="feature-list">{supplierValue.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section light"><div className="wrap"><p className="eyebrow">VALUE FOR CONTRACTORS</p><h2>Estimate faster and move directly toward delivery.</h2><p className="lede supplier-lede">CalibraytAI keeps the project scope, material takeoff, supplier costing, approved order and delivery schedule connected in one project workflow.</p><div className="feature-list">{contractorValue.map(([title,text])=><div className="feature" key={title}><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section dark"><div className="wrap"><p className="eyebrow">AUTOMATED SUPPLIER CONNECTION</p><h2>The supplier’s costing and fulfillment systems become part of the project.</h2><p className="lede supplier-lede">CalibraytAI connects the completed contractor requirement to supplier catalogues, SKUs, contractor-specific pricing and availability. Approval gates release the information into estimating, ordering and delivery at the right time.</p><div className="supplier-workflow"><div className="supplier-step"><span>1</span><div><h3>Automatic costing</h3><p>Supplier products, SKUs, pricing and availability are matched directly to the contractor’s takeoff and estimate.</p></div></div><div className="supplier-step"><span>2</span><div><h3>Automatic order submission</h3><p>Estimate approval converts the complete material requirement into a supplier order without duplicate entry.</p></div></div><div className="supplier-step"><span>3</span><div><h3>Automatic delivery coordination</h3><p>Approved delivery groups move into picking, loading and scheduling around the contractor’s project sequence.</p></div></div></div></div></section>

    <section className="section light"><div className="wrap"><p className="eyebrow">A STRONGER SUPPLIER RELATIONSHIP</p><h2>Both businesses save time on every project.</h2><p className="lede supplier-lede">Contractors bring complete requirements and purchasing demand to the supplier earlier. Suppliers respond faster, prepare more accurate material packages and coordinate fulfillment with greater visibility. The result is a closer working relationship built around cleaner information and more efficient service.</p></div></section>

    <section className="quote-band supplier-cta"><strong>One takeoff. One estimate. One supplier connection.</strong><p>From project requirements and supplier costing to approved orders and scheduled deliveries.</p><a className="btn primary" href="/plan">Start with PLAN</a></section>
  </main><Footer/></>
}
