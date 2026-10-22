# Shared architecture notes

| Attribute | Value |
|-----------|--------|
| Status | **RECORDED** |
| Date | 2026-09-26 |
| Contract | V1 remains as pinned. This note does not extend it. |

These items are for the Platform and the Website together. The Website specification works inside the current contract.

## Deficiencies

**Numeric precision is not in the envelope.** Contract V1 requires decimal strings and says the same inputs produce the same components and quantities. It does not say how many decimal places, or which rounding mode, make those strings. Two implementations can both validate and still differ. `concrete_slab` `1.0.0` defines its own rounding so its fixtures are portable. That rule is an engine rule. It is not a new contract field.

**The envelope does not require reconciliation.** A payload can pass validation when `total_concrete` is not the sum of the concrete components. `concrete_slab` `1.0.0` reconciles its own result. The contract still accepts a non-reconciling payload from some other producer.

## Cautions that are not contract defects

**The pinned thickened-edge example is illustrative.** The contract says those fixtures are not formulas. For inputs length `10` m, width `8` m, slab thickness `0.1` m, edge width `0.6` m, and depth below the slab `0.3` m, engine `1.0.0` produces additional edge concrete of `6.048` m³, not the illustrative `"1"`. The illustrative file stays in the mirror. Engine fixtures are separate, with `engine_version` `1.0.0`.

**Variant words.** Programme language STANDARD and THICKENED_EDGE maps to payload strings `standard` and `thickened_edge`. Uppercase tokens do not validate. The contract already states the strings. No change is required.

**Mixed units.** The contract allows each value to carry its own unit code. Engine `1.0.0` refuses a mix of metric and imperial input units inside one run. That is an engine validation rule, not a contract amendment.

## Speakeasy footprint

The 40 ft × 80 ft × 6 in fixtures are a generic base-slab example. They are not the Speakeasy slab.

The current Speakeasy footprint is 158 ft × 50 ft, plus an 8 ft front veranda. Edge width, depth below the slab, and the veranda treatment are not authoritatively recorded. No Speakeasy result is specified. That missing geometry is not a Contract V1 deficiency, and it is not a reason to invent an edge.
