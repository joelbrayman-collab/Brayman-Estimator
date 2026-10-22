export type LengthUnit = "mm" | "cm" | "m" | "in" | "ft";
export type Measurement = {value:number; unit:LengthUnit};
export type ConcreteSection =
  | {type:"slab"|"footing"; length:Measurement; width:Measurement; thickness:Measurement; quantity:number; name?:string}
  | {type:"wall"; length:Measurement; height:Measurement; thickness:Measurement; quantity:number; name?:string}
  | {type:"round-column"|"post-hole"; diameter:Measurement; height:Measurement; quantity:number; name?:string}
  | {type:"curb"; length:Measurement; width:Measurement; height:Measurement; quantity:number; name?:string}
  | {type:"concrete-stairs"; width:Measurement; treadRun:Measurement; riserHeight:Measurement; riserCount:number; quantity:number; name?:string};
export type ValidationIssue = {field:string; code:string; message:string};
export declare class UsefulToolsValidationError extends Error { issues:ValidationIssue[] }
export declare function toMetres(value:number,unit:LengthUnit):number;
export declare function fromCubicMetres(value:number,unit:"m3"|"yd3"|"ft3"):number;
export declare function calculateConcreteSection(section:ConcreteSection):ConcreteSection & {baseM3:number};
export declare function calculateConcretePour(input:{sections:ConcreteSection[];wastePercent:number;orderIncrementM3:number;bagYieldM3?:number;truckCapacityM3?:number}):{baseM3:number;wasteM3:number;adjustedM3:number;recommendedOrderM3:number;bagCount?:number;truckCount?:number;sections:Array<ConcreteSection & {baseM3:number}>};

export type StairInput={totalRise:Measurement;availableRun:Measurement;preferredRiserHeightM?:number};
export type StairCheck={id:string;field:string;measured:number;limit:number;unit:"mm";article:string;status:"pass"|"fail"};
export type StairResult={riserCount:number;treadCount:number;riserHeightM:number;treadRunM:number;totalRiseM:number;totalRunM:number;stringerLengthM:number;angleDegrees:number;checks:StairCheck[];overallStatus:"pass"|"fail"};
export declare function calculateStairCandidates(input:StairInput):Omit<StairResult,"checks"|"overallStatus">[];
export declare function evaluateStairProfile(layout:Omit<StairResult,"checks"|"overallStatus">,profile:unknown):Pick<StairResult,"checks"|"overallStatus">;
export declare function selectRecommendedStair(input:StairInput,profile:unknown):StairResult;
