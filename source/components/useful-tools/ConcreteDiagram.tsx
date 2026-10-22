type DiagramProps={shape:string; measurement:string};

export function ConcreteDiagram({shape,measurement}:DiagramProps){
  const label=shape.replaceAll("-"," ");
  const description=`Concrete ${label} measurement diagram using ${measurement} dimensions.`;
  const round=shape==="round-column"||shape==="post-hole";
  const stairs=shape==="concrete-stairs";
  return <svg className="tool-calculator-diagram" viewBox="0 0 520 230" role="img" aria-label={description}>
    <defs><marker id="concrete-arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 10 5 0 10z"/></marker></defs>
    {stairs?<path className="tool-diagram-shape" d="M90 178v-28h56v-28h56V94h56V66h56V38h96v140z"/>:round?<><ellipse className="tool-diagram-shape" cx="260" cy="55" rx="92" ry="31"/><path className="tool-diagram-shape" d="M168 55v112c0 17 41 31 92 31s92-14 92-31V55"/><ellipse className="tool-diagram-line" cx="260" cy="167" rx="92" ry="31"/></>:<path className="tool-diagram-shape" d="M105 80 330 48l86 55-224 36zM105 80v70l87 44v-55M192 139v55l224-38v-53"/>}
    <line className="tool-diagram-measure" x1="96" y1="211" x2="412" y2="211" markerStart="url(#concrete-arrow)" markerEnd="url(#concrete-arrow)"/>
    <text x="254" y="226" textAnchor="middle">{measurement} measurements</text>
  </svg>;
}

