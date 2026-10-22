import {createStairDiagramGeometry} from "../../lib/useful-tools/stair-diagram-geometry.mjs";

type Result={riserCount:number;treadCount:number;riserHeightM:number;treadRunM:number;totalRiseM:number;totalRunM:number;stringerLengthM:number;angleDegrees:number};

export function StairDiagram({result,formatLength,treadThicknessLabel}: {result:Result;formatLength:(metres:number)=>string;treadThicknessLabel:string}){
  const geometry=createStairDiagramGeometry(result);
  const {left,top,right,bottom,treadWidth,riserHeight}=geometry;
  const tread=geometry.treads[geometry.sampleTread];
  const riser=geometry.risers[geometry.sampleRiser];
  const runDimensionY=426;
  const riseDimensionX=Math.min(706,right+72);
  const treadDimensionY=Math.max(42,tread.y-Math.max(22,Math.min(34,riserHeight*.48)));
  const riserDimensionX=Math.min(riseDimensionX-54,riser.x+Math.max(28,Math.min(46,treadWidth*.34)));
  const stringerMid={x:(geometry.stringer.start.x+geometry.stringer.end.x)/2,y:(geometry.stringer.start.y+geometry.stringer.end.y)/2};
  const stringerPoints=geometry.stringerPolygon.map(point=>`${point.x},${point.y}`).join(" ");
  const label=`Detailed stair construction drawing. ${result.riserCount} risers and ${result.treadCount} treads. Total rise ${formatLength(result.totalRiseM)}. Available run ${formatLength(result.totalRunM)}. Riser height ${formatLength(result.riserHeightM)}. Tread run ${formatLength(result.treadRunM)}. Tread thickness ${treadThicknessLabel}. Stringer ${formatLength(result.stringerLengthM)}. Angle ${result.angleDegrees.toFixed(1)} degrees.`;
  return <svg className="tool-calculator-diagram stair-diagram" viewBox="0 0 760 480" role="img" aria-label={label} data-stair-angle={geometry.angleDegrees.toFixed(6)}>
    <defs>
      <marker id="stair-arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse"><path d="M0,0 L8,4 L0,8 z"/></marker>
      <linearGradient id="stair-wood" x1="0" x2="1"><stop offset="0" stopColor="#d8c79b"/><stop offset="1" stopColor="#bda875"/></linearGradient>
    </defs>

    <rect className="stair-upper-landing" x="44" y={top-14} width={Math.max(68,left-44)} height="14"/>
    <line className="stair-floor-line" x1="36" y1={top} x2={left+18} y2={top}/>
    <text className="stair-detail-label" x="46" y={top-27}>Finished floor</text>
    <text className="stair-detail-label" x="46" y={top+28}>Upper landing</text>
    <line className="stair-floor-line" x1={left-20} y1={bottom+14} x2={right+60} y2={bottom+14}/>
    <text className="stair-detail-label" x={right+18} y={bottom+36}>Finished landing</text>

    <polygon className="stair-stringer-body" points={stringerPoints}/>
    <path className="stair-step-outline" d={geometry.stairPath}/>
    {geometry.treads.map(item=><rect key={`t-${item.index}`} className="stair-tread-board" x={item.x1-3} y={item.y-5} width={item.x2-item.x1+8} height="7" rx="1"/>)}
    {geometry.risers.map(item=><rect key={`r-${item.index}`} className="stair-riser-face" x={item.x-3} y={item.y1} width="7" height={item.y2-item.y1}/>)}

    <g className="stair-measures">
      <g className="stair-dimension overall-rise">
        <line x1={riseDimensionX} y1={top} x2={riseDimensionX} y2={bottom} markerStart="url(#stair-arrow)" markerEnd="url(#stair-arrow)"/>
        <line x1={right+10} y1={top} x2={riseDimensionX-10} y2={top} className="stair-extension"/>
        <line x1={right+10} y1={bottom} x2={riseDimensionX-10} y2={bottom} className="stair-extension"/>
        <text x={riseDimensionX+24} y={(top+bottom)/2} transform={`rotate(-90 ${riseDimensionX+24} ${(top+bottom)/2})`}>Total rise · {formatLength(result.totalRiseM)}</text>
      </g>
      <g className="stair-dimension overall-run">
        <line x1={left} y1={runDimensionY} x2={right} y2={runDimensionY} markerStart="url(#stair-arrow)" markerEnd="url(#stair-arrow)"/>
        <line x1={left} y1={bottom+22} x2={left} y2={runDimensionY-10} className="stair-extension"/>
        <line x1={right} y1={bottom+22} x2={right} y2={runDimensionY-10} className="stair-extension"/>
        <text x={(left+right)/2} y="456" textAnchor="middle">Total run · {formatLength(result.totalRunM)}</text>
      </g>
      <g className="stair-dimension typical-tread">
        <line x1={tread.x1} y1={treadDimensionY} x2={tread.x2} y2={treadDimensionY} markerStart="url(#stair-arrow)" markerEnd="url(#stair-arrow)"/>
        <line x1={tread.x1} y1={treadDimensionY+7} x2={tread.x1} y2={tread.y-8} className="stair-extension"/>
        <line x1={tread.x2} y1={treadDimensionY+7} x2={tread.x2} y2={tread.y-8} className="stair-extension"/>
        <text x={(tread.x1+tread.x2)/2} y={treadDimensionY-28} textAnchor="middle">Typical tread</text>
        <text x={(tread.x1+tread.x2)/2} y={treadDimensionY-10} textAnchor="middle">{formatLength(result.treadRunM)}</text>
      </g>
      <g className="stair-dimension typical-riser">
        <line x1={riserDimensionX} y1={riser.y1} x2={riserDimensionX} y2={riser.y2} markerStart="url(#stair-arrow)" markerEnd="url(#stair-arrow)"/>
        <line x1={riser.x+7} y1={riser.y1} x2={riserDimensionX-8} y2={riser.y1} className="stair-extension"/>
        <line x1={riser.x+7} y1={riser.y2} x2={riserDimensionX-8} y2={riser.y2} className="stair-extension"/>
        <text x={riserDimensionX+12} y={(riser.y1+riser.y2)/2-5}>Typical riser</text>
        <text x={riserDimensionX+12} y={(riser.y1+riser.y2)/2+15}>{formatLength(result.riserHeightM)}</text>
      </g>
      <g className="stair-dimension tread-thickness">
        <line x1={right-36} y1={bottom-14} x2={right-36} y2={bottom-7} markerStart="url(#stair-arrow)" markerEnd="url(#stair-arrow)"/>
        <text x={right-24} y={bottom-5}>Tread thickness · {treadThicknessLabel}</text>
      </g>
      <text className="stair-stringer-label" x={stringerMid.x} y={stringerMid.y+23} textAnchor="middle" transform={`rotate(${geometry.stringer.angleDegrees} ${stringerMid.x} ${stringerMid.y+23})`}>Stringer · {formatLength(result.stringerLengthM)}</text>
      <text className="stair-angle-label" x={left+8} y={bottom+42}>Angle · {result.angleDegrees.toFixed(1)}°</text>
      <text className="stair-count" x="620" y="48">{result.riserCount} risers</text>
      <text className="stair-count" x="620" y="70">{result.treadCount} treads</text>
    </g>
  </svg>;
}
