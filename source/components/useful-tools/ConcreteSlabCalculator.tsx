"use client";

import { FormEvent, useMemo, useState } from "react";

import {
  calculateConcreteSlab,
  ConcreteSlabValidationError,
  type ConcreteSlabResult,
  type ConcreteSlabVariant,
  type MeasurementSystem,
} from "@/lib/calculation-engine/concrete-slab";
import {
  calculationDownloadFilename,
  createCalculationDownload,
} from "@/lib/calculation-engine/consumer";

type FormValues = {
  length: string;
  width: string;
  slabThickness: string;
  edgeWidth: string;
  edgeDepth: string;
  wastePercent: string;
};

const defaults: Record<MeasurementSystem, FormValues> = {
  metric: {
    length: "10",
    width: "8",
    slabThickness: "100",
    edgeWidth: "600",
    edgeDepth: "300",
    wastePercent: "5",
  },
  imperial: {
    length: "40",
    width: "20",
    slabThickness: "6",
    edgeWidth: "2",
    edgeDepth: "12",
    wastePercent: "5",
  },
};

const inputLabels: Record<string, string> = {
  length: "Length",
  width: "Width",
  slab_thickness: "Slab thickness",
  edge_width: "Edge width",
  edge_depth_below_slab: "Depth below slab",
};

const componentLabels: Record<string, string> = {
  base_slab_concrete: "Base slab concrete",
  thickened_edge_concrete: "Additional thickened-edge concrete",
  waste: "Waste allowance",
};

const unitLabels: Record<string, string> = {
  m: "m",
  mm: "mm",
  ft: "ft",
  in: "in",
  m3: "m³",
  yd3: "yd³",
  percent: "%",
};

function Field({
  label,
  value,
  unit,
  onChange,
  hint,
}: {
  label: string;
  value: string;
  unit: string;
  onChange: (value: string) => void;
  hint?: string;
}) {
  return (
    <label className="tool-field">
      <span>{label}</span>
      <span className="tool-input-wrap">
        <input
          inputMode="decimal"
          min="0"
          step="any"
          required
          type="number"
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
        <strong>{unit}</strong>
      </span>
      {hint ? <small>{hint}</small> : null}
    </label>
  );
}

export default function ConcreteSlabCalculator() {
  const [measurementSystem, setMeasurementSystem] = useState<MeasurementSystem>("metric");
  const [variant, setVariant] = useState<ConcreteSlabVariant>("standard");
  const [projectReference, setProjectReference] = useState("");
  const [values, setValues] = useState<FormValues>(defaults.metric);
  const [result, setResult] = useState<ConcreteSlabResult | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const units = useMemo(
    () =>
      measurementSystem === "metric"
        ? { plan: "m", thickness: "mm", edgeWidth: "mm", edgeDepth: "mm" }
        : { plan: "ft", thickness: "in", edgeWidth: "ft", edgeDepth: "in" },
    [measurementSystem],
  );

  function updateValue(key: keyof FormValues, value: string) {
    setValues((current) => ({ ...current, [key]: value }));
    setNotice("");
  }

  function changeSystem(next: MeasurementSystem) {
    setMeasurementSystem(next);
    setValues(defaults[next]);
    setResult(null);
    setError("");
    setNotice("");
  }

  function calculate(event: FormEvent) {
    event.preventDefault();
    setNotice("");
    try {
      const inputs = [
        { code: "length", value: values.length, unit_code: units.plan },
        { code: "width", value: values.width, unit_code: units.plan },
        { code: "slab_thickness", value: values.slabThickness, unit_code: units.thickness },
      ];
      if (variant === "thickened_edge") {
        inputs.push(
          { code: "edge_width", value: values.edgeWidth, unit_code: units.edgeWidth },
          {
            code: "edge_depth_below_slab",
            value: values.edgeDepth,
            unit_code: units.edgeDepth,
          },
        );
      }
      setResult(
        calculateConcreteSlab(
          {
            variant,
            measurement_system: measurementSystem,
            inputs,
            assumptions: [
              { code: "waste_percent", value: values.wastePercent, unit_code: "percent" },
            ],
          },
          { produced_at: new Date().toISOString() },
        ),
      );
      setError("");
    } catch (caught) {
      setResult(null);
      setError(
        caught instanceof ConcreteSlabValidationError
          ? caught.message
          : "Please check the measurements and try again.",
      );
    }
  }

  function saveOnDevice() {
    if (!result) return;
    const savedAt = new Date().toISOString();
    const record = createCalculationDownload(result, projectReference, savedAt);
    const existing = JSON.parse(localStorage.getItem("calibraytai.concrete-slab.saved") || "[]");
    localStorage.setItem(
      "calibraytai.concrete-slab.saved",
      JSON.stringify([record, ...existing].slice(0, 25)),
    );
    setNotice("Calculation saved on this device.");
  }

  function downloadCalculation() {
    if (!result) return;
    const record = createCalculationDownload(result, projectReference, new Date().toISOString());
    const blob = new Blob([JSON.stringify(record, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = calculationDownloadFilename(projectReference);
    anchor.click();
    URL.revokeObjectURL(url);
    setNotice("Calculation downloaded.");
  }

  const total = result?.quantities[0];

  return (
    <div className="calculator-shell">
      <form className="calculator-panel" onSubmit={calculate}>
        <div className="tool-section-heading">
          <p className="eyebrow">PROJECT DETAILS</p>
          <h2>Enter the slab measurements</h2>
          <p>Use the actual dimensions for this pour. Nothing is priced or added automatically.</p>
        </div>

        <label className="tool-field tool-field-wide">
          <span>Project / Reference Name <em>Optional</em></span>
          <input
            type="text"
            value={projectReference}
            placeholder="e.g. Garage slab"
            onChange={(event) => setProjectReference(event.target.value)}
          />
        </label>

        <fieldset className="tool-choice-group">
          <legend>Measurements</legend>
          <div className="tool-segmented">
            {(["metric", "imperial"] as const).map((system) => (
              <button
                key={system}
                className={measurementSystem === system ? "selected" : ""}
                type="button"
                aria-pressed={measurementSystem === system}
                onClick={() => changeSystem(system)}
              >
                {system === "metric" ? "Metric" : "Imperial"}
              </button>
            ))}
          </div>
        </fieldset>

        <fieldset className="tool-choice-group">
          <legend>Slab type</legend>
          <div className="tool-variant-grid">
            <button
              className={variant === "standard" ? "selected" : ""}
              type="button"
              aria-pressed={variant === "standard"}
              onClick={() => {
                setVariant("standard");
                setResult(null);
              }}
            >
              <strong>Standard Slab</strong>
              <span>One thickness across the full slab.</span>
            </button>
            <button
              className={variant === "thickened_edge" ? "selected" : ""}
              type="button"
              aria-pressed={variant === "thickened_edge"}
              onClick={() => {
                setVariant("thickened_edge");
                setResult(null);
              }}
            >
              <strong>Thickened Edge</strong>
              <span>Adds concrete below the slab around its perimeter.</span>
            </button>
          </div>
        </fieldset>

        <div className="tool-fields-grid">
          <Field label="Length" value={values.length} unit={units.plan} onChange={(value) => updateValue("length", value)} />
          <Field label="Width" value={values.width} unit={units.plan} onChange={(value) => updateValue("width", value)} />
          <Field label="Slab thickness" value={values.slabThickness} unit={units.thickness} onChange={(value) => updateValue("slabThickness", value)} />
          <Field label="Waste" value={values.wastePercent} unit="%" onChange={(value) => updateValue("wastePercent", value)} hint="Your allowance — no hidden waste factor" />
          {variant === "thickened_edge" ? (
            <>
              <Field label="Edge width" value={values.edgeWidth} unit={units.edgeWidth} onChange={(value) => updateValue("edgeWidth", value)} hint="Measured inward from the slab edge" />
              <Field label="Depth below slab" value={values.edgeDepth} unit={units.edgeDepth} onChange={(value) => updateValue("edgeDepth", value)} hint="Extra depth below the slab, not total depth" />
            </>
          ) : null}
        </div>

        {error ? <p className="tool-error" role="alert">{error}</p> : null}
        <button className="tool-calculate" type="submit">Calculate Concrete</button>
      </form>

      <section className={`calculation-summary ${result ? "has-result" : ""}`} aria-live="polite">
        <div className="summary-heading">
          <div>
            <p className="eyebrow">CALIBRAYTAI</p>
            <h2>Calculation Summary</h2>
          </div>
          <span>CONCRETE SLAB 1.0.0</span>
        </div>
        {!result ? (
          <div className="summary-empty">
            <span>01</span>
            <h3>Your concrete quantity will appear here.</h3>
            <p>Enter the slab dimensions and select Calculate Concrete.</p>
          </div>
        ) : (
          <>
            {projectReference.trim() ? <p className="summary-reference">{projectReference.trim()}</p> : null}
            <div className="summary-total">
              <span>Total concrete</span>
              <strong>{total?.quantity} <small>{total ? unitLabels[total.unit_code] : ""}</small></strong>
            </div>
            <dl className="summary-meta">
              <div><dt>Slab type</dt><dd>{result.variant === "standard" ? "Standard slab" : "Thickened edge"}</dd></div>
              <div><dt>Measurements</dt><dd>{result.measurement_system === "metric" ? "Metric" : "Imperial"}</dd></div>
            </dl>
            <div className="summary-block">
              <h3>Measurements</h3>
              {result.inputs.map((input) => (
                <div className="summary-line" key={input.code}>
                  <span>{inputLabels[input.code]}</span>
                  <strong>{input.value} {unitLabels[input.unit_code]}</strong>
                </div>
              ))}
              <div className="summary-line">
                <span>Waste allowance</span>
                <strong>{result.assumptions[0].value}%</strong>
              </div>
            </div>
            <div className="summary-block">
              <h3>Quantity breakdown</h3>
              {result.components.map((component) => (
                <div className="summary-line" key={component.code}>
                  <span>{componentLabels[component.code]}</span>
                  <strong>{component.quantity} {unitLabels[component.unit_code]}</strong>
                </div>
              ))}
            </div>
            <p className="summary-disclaimer">
              This is a quantity calculation—not a price, engineering design, or proposal.
            </p>
          </>
        )}
        <div className="summary-actions">
          <button type="button" disabled={!result} onClick={saveOnDevice}>Save on This Device</button>
          <button type="button" disabled={!result} onClick={downloadCalculation}>Download Calculation</button>
        </div>
        {notice ? <p className="tool-notice" role="status">{notice}</p> : null}
      </section>
    </div>
  );
}
