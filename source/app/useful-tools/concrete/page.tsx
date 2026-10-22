import ConcreteSlabCalculator from "../../../components/useful-tools/ConcreteSlabCalculator";
import { Footer, Header } from "../../site";

export default function ConcreteSlabPage() {
  return (
    <>
      <Header active="tools" />
      <main>
        <section className="calculator-hero">
          <div className="wrap">
            <div>
              <a className="tool-back" href="/useful-tools">← Useful Tools</a>
              <p className="kicker">CONCRETE SLAB CALCULATOR</p>
              <h1>Know the volume<br /><span>before the pour.</span></h1>
              <p>Calculate concrete for a standard rectangular slab or a slab with a thickened perimeter edge. Use Metric or Imperial measurements.</p>
            </div>
            <div className="calculator-hero-note">
              <strong>Two clear calculations</strong>
              <span>Base slab volume</span>
              <span>Additional edge volume</span>
              <small>Each corner is counted once.</small>
            </div>
          </div>
        </section>
        <section className="calculator-workspace">
          <ConcreteSlabCalculator />
        </section>
      </main>
      <Footer />
    </>
  );
}
