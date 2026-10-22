const LENGTH_TO_METRES = Object.freeze({
  mm: 0.001,
  cm: 0.01,
  m: 1,
  in: 0.0254,
  ft: 0.3048,
});

const CUBIC_METRE_FACTORS = Object.freeze({
  "m3": 1,
  "yd3": 1.307950619314392,
  "ft3": 35.31466672148859,
});

export function toMetres(value, unit) {
  const factor = LENGTH_TO_METRES[unit];
  if (!factor) throw new RangeError(`Unsupported length unit: ${unit}`);
  return value * factor;
}

export function fromCubicMetres(value, unit) {
  const factor = CUBIC_METRE_FACTORS[unit];
  if (!factor) throw new RangeError(`Unsupported volume unit: ${unit}`);
  return value * factor;
}

