export type MeasurementSystem = "metric" | "imperial";
export type ConcreteSlabVariant = "standard" | "thickened_edge";

export type CodedValue = {
  code: string;
  value: string;
  unit_code: string;
};

export type QuantityLine = {
  code: string;
  quantity: string;
  unit_code: "m3" | "yd3";
};

export type ConcreteSlabRun = {
  variant: ConcreteSlabVariant;
  measurement_system: MeasurementSystem;
  inputs: CodedValue[];
  assumptions: CodedValue[];
};

export type ConcreteSlabResult = {
  contract_version: "1";
  result_id: string;
  engine_id: "concrete_slab";
  engine_version: "1.0.0";
  variant: ConcreteSlabVariant;
  measurement_system: MeasurementSystem;
  inputs: CodedValue[];
  assumptions: CodedValue[];
  product_specification: null;
  components: QuantityLine[];
  quantities: QuantityLine[];
  produced_at?: string;
};

type Rational = { numerator: bigint; denominator: bigint };

const METRIC_UNITS = new Set(["m", "mm"]);
const IMPERIAL_UNITS = new Set(["ft", "in"]);
const REQUIRED_BASE_CODES = ["length", "width", "slab_thickness"];
const REQUIRED_EDGE_CODES = ["edge_width", "edge_depth_below_slab"];
const DECIMAL_PATTERN = /^\d+(?:\.\d+)?$/;

export class ConcreteSlabValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConcreteSlabValidationError";
  }
}

function gcd(a: bigint, b: bigint): bigint {
  let left = a < 0n ? -a : a;
  let right = b < 0n ? -b : b;
  while (right !== 0n) {
    const remainder = left % right;
    left = right;
    right = remainder;
  }
  return left || 1n;
}

function rational(numerator: bigint, denominator = 1n): Rational {
  if (denominator === 0n) throw new Error("Division by zero");
  const sign = denominator < 0n ? -1n : 1n;
  const divisor = gcd(numerator, denominator);
  return {
    numerator: (numerator / divisor) * sign,
    denominator: (denominator / divisor) * sign,
  };
}

function decimal(value: string, label: string): Rational {
  if (!DECIMAL_PATTERN.test(value)) {
    throw new ConcreteSlabValidationError(`${label} must be a decimal number.`);
  }
  const [whole, fraction = ""] = value.split(".");
  return rational(BigInt(`${whole}${fraction}`), 10n ** BigInt(fraction.length));
}

function add(a: Rational, b: Rational): Rational {
  return rational(
    a.numerator * b.denominator + b.numerator * a.denominator,
    a.denominator * b.denominator,
  );
}

function subtract(a: Rational, b: Rational): Rational {
  return rational(
    a.numerator * b.denominator - b.numerator * a.denominator,
    a.denominator * b.denominator,
  );
}

function multiply(a: Rational, b: Rational): Rational {
  return rational(a.numerator * b.numerator, a.denominator * b.denominator);
}

function divide(a: Rational, b: Rational): Rational {
  return rational(a.numerator * b.denominator, a.denominator * b.numerator);
}

function compare(a: Rational, b: Rational): number {
  const difference = a.numerator * b.denominator - b.numerator * a.denominator;
  return difference < 0n ? -1 : difference > 0n ? 1 : 0;
}

function roundHalfUpToMilli(value: Rational): bigint {
  const scaled = value.numerator * 1000n;
  const whole = scaled / value.denominator;
  const remainder = scaled % value.denominator;
  return remainder * 2n >= value.denominator ? whole + 1n : whole;
}

function formatMilli(value: bigint): string {
  const whole = value / 1000n;
  const fraction = (value % 1000n).toString().padStart(3, "0").replace(/0+$/, "");
  return fraction ? `${whole}.${fraction}` : whole.toString();
}

function normalizeDecimal(value: string): string {
  const parsed = decimal(value, "Value");
  const [whole, fraction = ""] = value.split(".");
  const trimmedFraction = fraction.replace(/0+$/, "");
  void parsed;
  return trimmedFraction ? `${BigInt(whole)}.${trimmedFraction}` : BigInt(whole).toString();
}

function toMetres(value: Rational, unitCode: string): Rational {
  if (unitCode === "m") return value;
  if (unitCode === "mm") return divide(value, rational(1000n));
  if (unitCode === "ft") return multiply(value, rational(3048n, 10000n));
  if (unitCode === "in") return multiply(value, rational(254n, 10000n));
  throw new ConcreteSlabValidationError(`Unsupported length unit: ${unitCode}.`);
}

function createResultId(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return `concrete-slab-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function indexValues(values: CodedValue[], kind: string): Map<string, CodedValue> {
  const indexed = new Map<string, CodedValue>();
  for (const item of values) {
    if (indexed.has(item.code)) {
      throw new ConcreteSlabValidationError(`Duplicate ${kind}: ${item.code}.`);
    }
    indexed.set(item.code, item);
  }
  return indexed;
}

export function calculateConcreteSlab(
  run: ConcreteSlabRun,
  options: { result_id?: string; produced_at?: string } = {},
): ConcreteSlabResult {
  if (run.variant !== "standard" && run.variant !== "thickened_edge") {
    throw new ConcreteSlabValidationError("Select a valid slab type.");
  }
  if (run.measurement_system !== "metric" && run.measurement_system !== "imperial") {
    throw new ConcreteSlabValidationError("Select Metric or Imperial measurements.");
  }

  const inputMap = indexValues(run.inputs, "input");
  const assumptionMap = indexValues(run.assumptions, "assumption");
  const expectedCodes = new Set([
    ...REQUIRED_BASE_CODES,
    ...(run.variant === "thickened_edge" ? REQUIRED_EDGE_CODES : []),
  ]);
  if (run.inputs.length !== expectedCodes.size) {
    throw new ConcreteSlabValidationError("The selected slab type has missing or unexpected measurements.");
  }
  for (const code of expectedCodes) {
    if (!inputMap.has(code)) {
      throw new ConcreteSlabValidationError(`Missing required measurement: ${code}.`);
    }
  }
  for (const code of inputMap.keys()) {
    if (!expectedCodes.has(code)) {
      throw new ConcreteSlabValidationError(`Unexpected measurement: ${code}.`);
    }
  }

  const allowedUnits = run.measurement_system === "metric" ? METRIC_UNITS : IMPERIAL_UNITS;
  const metres = new Map<string, Rational>();
  const normalizedInputs = run.inputs.map((item) => {
    if (!allowedUnits.has(item.unit_code)) {
      throw new ConcreteSlabValidationError(`${item.code} uses a unit outside the selected measurement system.`);
    }
    const parsed = decimal(item.value, item.code);
    if (compare(parsed, rational(0n)) <= 0) {
      throw new ConcreteSlabValidationError(`${item.code} must be greater than zero.`);
    }
    metres.set(item.code, toMetres(parsed, item.unit_code));
    return { ...item, value: normalizeDecimal(item.value) };
  });

  if (run.assumptions.length !== 1 || !assumptionMap.has("waste_percent")) {
    throw new ConcreteSlabValidationError("A waste percent is required.");
  }
  const wasteInput = assumptionMap.get("waste_percent")!;
  if (wasteInput.unit_code !== "percent") {
    throw new ConcreteSlabValidationError("Waste must use percent.");
  }
  const wastePercent = decimal(wasteInput.value, "waste_percent");
  if (compare(wastePercent, rational(0n)) < 0) {
    throw new ConcreteSlabValidationError("Waste percent cannot be negative.");
  }
  const normalizedAssumptions = [
    { ...wasteInput, value: normalizeDecimal(wasteInput.value) },
  ];

  const length = metres.get("length")!;
  const width = metres.get("width")!;
  const thickness = metres.get("slab_thickness")!;
  const baseM3 = multiply(multiply(length, width), thickness);
  let edgeM3 = rational(0n);

  if (run.variant === "thickened_edge") {
    const edgeWidth = metres.get("edge_width")!;
    const edgeDepth = metres.get("edge_depth_below_slab")!;
    if (
      compare(multiply(rational(2n), edgeWidth), length) >= 0 ||
      compare(multiply(rational(2n), edgeWidth), width) >= 0
    ) {
      throw new ConcreteSlabValidationError(
        "Edge width is too large for this slab; the perimeter bands would overlap.",
      );
    }
    const edgeArea = subtract(
      multiply(multiply(rational(2n), edgeWidth), add(length, width)),
      multiply(rational(4n), multiply(edgeWidth, edgeWidth)),
    );
    edgeM3 = multiply(edgeArea, edgeDepth);
  }

  const wasteM3 = divide(
    multiply(add(baseM3, edgeM3), wastePercent),
    rational(100n),
  );
  const outputUnit = run.measurement_system === "metric" ? "m3" : "yd3";
  const cubicYardM3 = rational(764554857984n, 1000000000000n);
  const inOutputUnit = (value: Rational) =>
    run.measurement_system === "metric" ? value : divide(value, cubicYardM3);

  const baseMilli = roundHalfUpToMilli(inOutputUnit(baseM3));
  const edgeMilli = roundHalfUpToMilli(inOutputUnit(edgeM3));
  const wasteMilli = roundHalfUpToMilli(inOutputUnit(wasteM3));
  const components: QuantityLine[] = [
    { code: "base_slab_concrete", quantity: formatMilli(baseMilli), unit_code: outputUnit },
  ];
  if (run.variant === "thickened_edge") {
    components.push({
      code: "thickened_edge_concrete",
      quantity: formatMilli(edgeMilli),
      unit_code: outputUnit,
    });
  }
  components.push({ code: "waste", quantity: formatMilli(wasteMilli), unit_code: outputUnit });

  const result: ConcreteSlabResult = {
    contract_version: "1",
    result_id: options.result_id ?? createResultId(),
    engine_id: "concrete_slab",
    engine_version: "1.0.0",
    variant: run.variant,
    measurement_system: run.measurement_system,
    inputs: normalizedInputs,
    assumptions: normalizedAssumptions,
    product_specification: null,
    components,
    quantities: [
      {
        code: "total_concrete",
        quantity: formatMilli(baseMilli + edgeMilli + wasteMilli),
        unit_code: outputUnit,
      },
    ],
  };
  if (options.produced_at) result.produced_at = options.produced_at;
  return result;
}
