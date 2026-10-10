const VIEWBOX={width:760,height:480};
const FRAME={left:112,top:78,width:500,height:270};

function finitePositive(value,name){
  if(!Number.isFinite(value)||value<=0) throw new RangeError(`${name} must be greater than zero.`);
  return value;
}

export function createStairDiagramGeometry(result){
  const totalRise=finitePositive(result?.totalRiseM,"Total rise");
  const totalRun=finitePositive(result?.totalRunM,"Total run");
  const riserCount=finitePositive(result?.riserCount,"Riser count");
  const treadCount=finitePositive(result?.treadCount,"Tread count");
  const scale=Math.min(FRAME.width/totalRun,FRAME.height/totalRise);
  const width=totalRun*scale;
  const height=totalRise*scale;
  const left=FRAME.left+(FRAME.width-width)/2;
  const top=FRAME.top+(FRAME.height-height)/2;
  const right=left+width;
  const bottom=top+height;
  const treadWidth=width/treadCount;
  const riserHeight=height/riserCount;
  const angleDegrees=Math.atan2(height,width)*180/Math.PI;
  const treads=Array.from({length:treadCount},(_,index)=>({
    index,
    x1:left+index*treadWidth,
    x2:left+(index+1)*treadWidth,
    y:top+(index+1)*riserHeight,
  }));
  const risers=Array.from({length:riserCount},(_,index)=>({
    index,
    x:left+Math.min(index,treadCount)*treadWidth,
    y1:top+index*riserHeight,
    y2:top+(index+1)*riserHeight,
  }));
  const stairPath=risers.reduce((path,riser,index)=>{
    const tread=index<treadCount?` H ${left+(index+1)*treadWidth}`:"";
    return `${path} V ${riser.y2}${tread}`;
  },`M ${left} ${top}`);
  const stringerOffset=Math.max(22,Math.min(34,riserHeight*.72));
  const stringerThickness=20;
  const stringer={
    start:{x:left,y:top+stringerOffset},
    end:{x:right,y:bottom+stringerOffset},
    angleDegrees,
    thickness:stringerThickness,
  };
  const length=Math.hypot(width,height);
  const normal={x:-height/length,y:width/length};
  const half=stringerThickness/2;
  const stringerPolygon=[
    {x:stringer.start.x+normal.x*half,y:stringer.start.y+normal.y*half},
    {x:stringer.end.x+normal.x*half,y:stringer.end.y+normal.y*half},
    {x:stringer.end.x-normal.x*half,y:stringer.end.y-normal.y*half},
    {x:stringer.start.x-normal.x*half,y:stringer.start.y-normal.y*half},
  ];
  const sampleTread=Math.max(0,Math.min(treadCount-1,Math.floor((treadCount-1)/2)));
  const sampleRiser=Math.max(0,Math.min(riserCount-1,sampleTread+1));
  return {
    viewBox:VIEWBOX,
    frame:FRAME,
    left,top,right,bottom,width,height,treadWidth,riserHeight,angleDegrees,
    stairPath,treads,risers,stringer,stringerPolygon,sampleTread,sampleRiser,
  };
}
