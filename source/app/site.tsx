const phases = ["plan","price","contract","build","monitor","learn"] as const;

export function Header({active="home"}:{active?:string}) {
  return <header className="top-band"><div className="band-inner"><a className="brand" href="/"><img src="/calibraytai-logo-v1.png" alt="CalibraytAI approved logo"/></a><nav className="nav"><a className={active==="home"?"active":""} href="/">HOME</a>{phases.map(p=><a key={p} className={active===p?"active":""} href={"/"+p}>{p.toUpperCase()}</a>)}</nav></div></header>
}

export const LINKS = {
  contractor: "https://calibryatai.onrender.com/login",
  supplier: "https://calibryatai.onrender.com/supplier/login",
  training: "https://training.calibraytai.com/training/signin",
} as const;

/* Useful Calculators icon (approved artwork; 600 px web copy of public/useful-calculators-icon-original.png). Change href here for the final landing page. */
export const USEFUL_CALCULATORS = {
  icon: "/useful-calculators-icon.png",
  href: "/useful-tools/",
  alt: "Useful Calculators — open the CalibraytAI Useful Calculators",
} as const;

export function FooterLinks(){return <nav className="footer-links" aria-label="Site and sign-in links"><a href="/contractor-connection/">Contractor Connection</a><a href="/supplier-integration/">Supplier Connection</a><a href="/useful-tools/">Useful Tools</a><a href={LINKS.contractor}>Contractor sign-in</a><a href={LINKS.supplier}>Supplier Hub sign-in</a><a href={LINKS.training}>Training Centre</a></nav>}

export function Footer(){return <footer className="footer"><div className="wrap"><span>CalibraytAI</span><span>PLAN • PRICE • BUILD</span><span><a href="/">Home</a></span></div><div className="wrap"><FooterLinks/></div></footer>}

export type Status = "released" | "next" | "concept";
const statusLabel: Record<Status,string> = {released:"In the platform today", next:"Rolling out in the next release", concept:"In development"};
export function StatusBadge({status}:{status:Status}){return <span className={`status-badge status-${status}`}>{statusLabel[status]}</span>}

export type PhaseData={name:string;title:string;description:string;image:string;eyebrow:string;features:{title:string;text:string}[]};

export function PhasePage({data}:{data:PhaseData}){
  const active=data.name.toLowerCase();
  return <><Header active={active}/><section className={`page-hero page-hero-${active}`}><div className="wrap"><div className="phase-copy"><span className="phase-label">{data.name}</span><h1>{data.title}</h1><p>{data.description}</p><div className="phase-nav">{phases.map(p=><a key={p} className={active===p?"active":""} href={"/"+p}>{p.toUpperCase()}</a>)}</div></div><div className={`phase-visual phase-visual-${active}`}><img src={data.image} alt="CalibraytAI approved visual"/></div></div></section><section className="section light"><div className="wrap"><p className="eyebrow">{data.eyebrow}</p><h2>{data.name} becomes part of one authoritative project record.</h2><div className="feature-list">{data.features.map(f=><div className="feature" key={f.title}><h3>{f.title}</h3><p>{f.text}</p></div>)}</div></div></section><section className="quote-band"><strong>Construction intelligence. Calibrated.</strong></section><Footer/></>
}
