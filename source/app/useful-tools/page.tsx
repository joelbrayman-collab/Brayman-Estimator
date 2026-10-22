import {Box, Calculator, Ruler} from "lucide-react";
import {Footer, Header} from "../site";

const tools = [
  {title:"Employment vs. Entrepreneurship",text:"Compare income, costs, time commitments and the financial trade-offs between employment and running a business.",href:"/employment-vs-entrepreneurship/",Icon:Calculator},
  {title:"Concrete Calculator",text:"Calculate concrete for standard slabs and slabs with thickened perimeter edges.",href:"/useful-tools/concrete/",Icon:Box},
  {title:"Stair Calculator",text:"Lay out risers, treads, stair angle and stringer length with clear Ontario residential guidance.",href:"/useful-tools/stairs/",Icon:Ruler},
] as const;

export default function UsefulTools(){
  return <><Header/><main className="tools-page">
    <section className="tools-hero"><div className="wrap"><p className="kicker">USEFUL TOOLS</p><h1>Fast answers for practical decisions.</h1><p>Simple, reliable calculators for the questions that come up every day—in the office, in the truck and on site.</p></div></section>
    <section className="section light tools-directory"><div className="wrap"><div className="tools-list">{tools.map(({title,text,href,Icon})=><article className="tools-row" key={title}><span className="tools-icon"><Icon aria-hidden="true"/></span><div className="tools-row-copy"><h2>{title}</h2><p>{text}</p></div><a className="btn primary tools-open" href={href} aria-label={`Open ${title}`}>Open</a></article>)}</div></div></section>
  </main><Footer/></>;
}
