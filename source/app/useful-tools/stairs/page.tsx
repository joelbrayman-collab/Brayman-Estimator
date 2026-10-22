import {Footer,Header} from "../../site";
import {StairCalculator} from "../../../components/useful-tools/StairCalculator";

export default function StairCalculatorPage(){return <><Header/><main>
  <section className="tool-calculator-hero"><div className="wrap"><p className="eyebrow">USEFUL TOOLS</p><h1>Stair Calculator</h1><p>Lay out a straight residential stair and review its rise and run against the Ontario Residential — V1 profile.</p></div></section>
  <StairCalculator/>
</main><Footer/></>}
