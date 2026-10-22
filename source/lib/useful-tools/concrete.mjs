import {toMetres} from "./units.mjs";

// DORMANT BROAD CONCRETE PROTOTYPE
// Retained for historical compatibility tests only. Public slab calculations
// are governed by lib/calculation-engine/concrete-slab.ts.

export class UsefulToolsValidationError extends Error {
  constructor(issues) {
    super(issues.map(issue => issue.message).join(" "));
    this.name = "UsefulToolsValidationError";
    this.issues = issues;
  }
}

function positiveNumber(value, field) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    throw new UsefulToolsValidationError([{field, code:"positive-number-required", message:`${field} must be greater than zero.`}]);
  }
  return value;
}

function measurement(value, field) {
  if (!value || typeof value !== "object") {
    throw new UsefulToolsValidationError([{field, code:"measurement-required", message:`${field} is required.`}]);
  }
  return toMetres(positiveNumber(value.value, field), value.unit);
}

function quantity(value) {
  return positiveNumber(value ?? 1, "quantity");
}

export function calculateConcreteSection(section) {
  if (!section || typeof section !== "object") {
    throw new UsefulToolsValidationError([{field:"section",code:"section-required",message:"A concrete section is required."}]);
  }

  let volume;
  switch (section.type) {
    case "slab":
    case "footing":
      volume = measurement(section.length,"length") * measurement(section.width,"width") * measurement(section.thickness,"thickness");
      break;
    case "wall":
      volume = measurement(section.length,"length") * measurement(section.height,"height") * measurement(section.thickness,"thickness");
      break;
    case "round-column":
    case "post-hole": {
      const radius = measurement(section.diameter,"diameter") / 2;
      volume = Math.PI * radius * radius * measurement(section.height,"height");
      break;
    }
    case "curb":
      volume = measurement(section.length,"length") * measurement(section.width,"width") * measurement(section.height,"height");
      break;
    case "concrete-stairs": {
      const count = positiveNumber(section.riserCount,"riserCount");
      if (!Number.isInteger(count)) {
        throw new UsefulToolsValidationError([{field:"riserCount",code:"whole-number-required",message:"riserCount must be a whole number."}]);
      }
      volume = measurement(section.width,"width") * measurement(section.treadRun,"treadRun") * measurement(section.riserHeight,"riserHeight") * count * (count + 1) / 2;
      break;
    }
    default:
      throw new UsefulToolsValidationError([{field:"type",code:"unsupported-shape",message:`Unsupported concrete shape: ${section.type ?? "missing"}.`}]);
  }

  const baseM3 = volume * quantity(section.quantity);
  if (!Number.isFinite(baseM3)) {
    throw new UsefulToolsValidationError([{field:"section",code:"volume-overflow",message:"The section volume is too large to calculate."}]);
  }
  return {...section, baseM3};
}

const ceilRatio = (value, increment) => Math.ceil(value / increment - 1e-12);

export function calculateConcretePour(input) {
  if (!input?.sections?.length) {
    throw new UsefulToolsValidationError([{field:"sections",code:"section-required",message:"Add at least one concrete section."}]);
  }
  const sections = input.sections.map(calculateConcreteSection);
  const baseM3 = sections.reduce((total, section) => total + section.baseM3, 0);
  const wastePercent = input.wastePercent ?? 10;
  if (typeof wastePercent !== "number" || !Number.isFinite(wastePercent) || wastePercent < 0) {
    throw new UsefulToolsValidationError([{field:"wastePercent",code:"non-negative-number-required",message:"Waste allowance must be zero or greater."}]);
  }
  const orderIncrementM3 = positiveNumber(input.orderIncrementM3,"orderIncrementM3");
  const wasteM3 = baseM3 * wastePercent / 100;
  const adjustedM3 = baseM3 + wasteM3;
  const recommendedOrderM3 = ceilRatio(adjustedM3, orderIncrementM3) * orderIncrementM3;
  const result = {baseM3,wasteM3,adjustedM3,recommendedOrderM3,sections};
  if (input.bagYieldM3 !== undefined) result.bagCount = ceilRatio(adjustedM3, positiveNumber(input.bagYieldM3,"bagYieldM3"));
  if (input.truckCapacityM3 !== undefined) result.truckCount = ceilRatio(adjustedM3, positiveNumber(input.truckCapacityM3,"truckCapacityM3"));
  return result;
}
