# Concrete slab engine 1.0.0

| Attribute | Value |
|-----------|--------|
| Status | **SPECIFIED / NOT IMPLEMENTED** |
| Date | 2026-09-26 |
| `engine_id` | `concrete_slab` |
| `engine_version` | `1.0.0` |
| `contract_version` | `"1"` |
| Variants | `standard`, `thickened_edge` |
| `product_specification` | `null` |
| Fixtures | [fixtures/concrete-slab-1.0.0](fixtures/concrete-slab-1.0.0) |

This engine calculates concrete volume. It does not choose a mix, a price, reinforcement, forming, or an engineering design.

Programme names STANDARD and THICKENED_EDGE are the variants `standard` and `thickened_edge` in the payload.

## What the variants mean

`standard` is a rectangular slab of one thickness over the whole plan.

`thickened_edge` is that same slab, plus concrete below the slab along a perimeter band inside the plan. The band does not replace the slab thickness. The base volume already includes the slab thickness over the band. The edge volume is only the additional concrete.

## Inputs

Stored values are the numbers the person entered, with the unit they entered. Calculation converts them. Labels are omitted so a display word does not change the fingerprint.

| Code | Required | `standard` | `thickened_edge` | Metric units | Imperial units |
|------|----------|------------|------------------|--------------|----------------|
| `length` | Yes | Yes | Yes | `m` or `mm` | `ft` or `in` |
| `width` | Yes | Yes | Yes | `m` or `mm` | `ft` or `in` |
| `slab_thickness` | Yes | Yes | Yes | `m` or `mm` | `ft` or `in` |
| `edge_width` | Edge only | Absent | Yes | `m` or `mm` | `ft` or `in` |
| `edge_depth_below_slab` | Edge only | Absent | Yes | `m` or `mm` | `ft` or `in` |

`edge_width` is the horizontal width of the thickened band, measured in from the outer face of the rectangle. `edge_depth_below_slab` is the extra depth under the bottom of the slab. It is not the full depth from the top of the slab.

One run uses one measurement system. Metric inputs do not mix with imperial inputs.

## Assumptions

| Code | Required | Unit | Rule |
|------|----------|------|------|
| `waste_percent` | Yes | `percent` | Zero or greater. The person enters it. The engine has no hidden percent. |

Waste is applied to the sum of base and additional edge concrete. It is not applied twice.

## Conversion

Exact factors:

| From | To metres |
|------|-----------|
| `m` | value |
| `mm` | value / 1000 |
| `ft` | value × 0.3048 |
| `in` | value × 0.0254 |

One cubic yard is `0.764554857984` cubic metres (`27 × 0.3048³`).

Internal multiplication uses these exact decimals. It does not use binary floating point.

## Formulas

After conversion, `L`, `W`, and `T` are length, width, and slab thickness in metres.

```text
base_m3 = L × W × T
```

For `standard`:

```text
edge_m3 = 0
```

For `thickened_edge`, `E` is edge width in metres and `D` is depth below the slab in metres:

```text
edge_area_m2 = 2 × E × (L + W) − 4 × E × E
edge_m3 = edge_area_m2 × D
```

`edge_area_m2` is the area of a rectangular frame. Each corner is inside the frame once. The rejected alternative `2 × (L + W) × E × D` counts each corner twice. The double-counted corner volume is `4 × E × E × D`.

```text
waste_m3 = (base_m3 + edge_m3) × waste_percent / 100
```

Output unit:

| `measurement_system` | Quantity unit |
|----------------------|---------------|
| `metric` | `m3` |
| `imperial` | `yd3` |

Imperial cubic yards are `exact_m3 / 0.764554857984` before rounding.

## Rounding

Round `base`, `edge` when the variant includes it, and `waste` separately:

- mode: half up
- scale: 3 decimal places in the output unit
- source: the exact cubic-metre figure, converted to the output unit first when the output is `yd3`

`total_concrete` is the sum of those already rounded components. It is not a second rounding of the exact total.

Written decimal strings drop trailing zeros. `8.000` is written `"8"`. `14.750` is written `"14.75"`. The fingerprint uses that written string.

## Components and quantities

Array order is fixed.

`standard` components:

| Order | Code | Meaning |
|-------|------|---------|
| 1 | `base_slab_concrete` | Slab volume over the whole plan |
| 2 | `waste` | Waste volume, including zero |

`thickened_edge` components:

| Order | Code | Meaning |
|-------|------|---------|
| 1 | `base_slab_concrete` | Slab volume over the whole plan, including the thickness over the edge band |
| 2 | `thickened_edge_concrete` | Additional concrete below the slab only |
| 3 | `waste` | Waste on base plus additional edge |

`standard` does not emit `thickened_edge_concrete`. A zero edge line would look like an edge had been calculated.

Quantities:

| Order | Code | Meaning |
|-------|------|---------|
| 1 | `total_concrete` | Sum of the rounded components |

`percent` is not used on components or quantities. Waste percent stays in `assumptions`. Waste volume is `m3` or `yd3`.

## Validation before a result exists

The engine rejects the run and emits no Contract V1 payload when any of these fail:

- `length`, `width`, and `slab_thickness` are present, decimal, and greater than zero.
- `waste_percent` is present, decimal, and zero or greater.
- Units belong to the selected measurement system.
- `standard` does not include `edge_width` or `edge_depth_below_slab`.
- `thickened_edge` includes both edge inputs, each greater than zero.
- After conversion, `2 × E < L` and `2 × E < W`. Otherwise the bands overlap across the slab and the frame formula would count the overlap twice.

Concrete strength, fibre, reinforcement, and price are not inputs. They do not change this volume.

## Worked audit

Inputs: length `10` m, width `8` m, thickness `0.1` m, edge width `0.6` m, depth below slab `0.3` m, waste `5` percent.

| Step | Exact | Rounded `m3` |
|------|-------|--------------|
| Base `10 × 8 × 0.1` | 8 | 8 |
| Frame area `2 × 0.6 × 18 − 4 × 0.36` | 20.16 m² | |
| Additional edge `20.16 × 0.3` | 6.048 | 6.048 |
| Double-count avoided `6.48 − 6.048` | 0.432 | |
| Waste `14.048 × 0.05` | 0.7024 | 0.702 |
| Total of rounded components | | 14.75 |

The pinned illustrative fixture uses the same inputs and a `thickened_edge_concrete` quantity of `"1"`. That fixture is not this result. Fixture: `audit-10x8-thickened-edge-metric.json`. Fingerprint `2be4aad59fa8efdc98db4d62732551a6306d33ec98b0ec03ec22505287c0f92a`.

## Metric and imperial equivalents

The same physical slab is stored once in imperial entry units and once in exact metric conversions.

Imperial: 40 ft × 20 ft × 6 in. Metric: 12.192 m × 6.096 m × 0.1524 m.

Standard, waste 0:

| System | Base and total |
|--------|----------------|
| Metric | `11.327` m³ |
| Imperial | `14.815` yd³ |

Thickened edge, band 2 ft wide and 12 in below the slab (metric 0.6096 m by 0.3048 m), waste 5 percent:

| System | Base | Additional edge | Waste | Total |
|--------|------|-----------------|-------|-------|
| Metric | 11.327 m³ | 6.343 m³ | 0.883 m³ | 18.553 m³ |
| Imperial | 14.815 yd³ | 8.296 yd³ | 1.156 yd³ | 24.267 yd³ |

`24.267` yd³ converts back to `18.553` m³ at 3 decimal places. `14.815` yd³ converts back to `11.327` m³ at 3 decimal places. The pair is equivalent at the engine's written scale. The fingerprints differ because the input units and the output units differ. Both are valid Contract V1 results.

## Generic base slab, 40 ft × 80 ft × 6 in

This is a generic base-slab example. It is not the Speakeasy slab.

Plan 80 ft by 40 ft, thickness 6 in. Metric equivalent: 24.384 m by 12.192 m by 0.1524 m. Variant `standard`. Waste `0`.

| System | Base and total |
|--------|----------------|
| Imperial | `59.259` yd³ |
| Metric | `45.307` m³ |

`59.259` yd³ converts back to `45.307` m³ at 3 decimal places.

Fixtures:

- `generic-40x80-base-imperial.json`
- `generic-40x80-base-metric.json`

## Speakeasy footprint

The current Speakeasy project footprint is 158 ft × 50 ft, plus an 8 ft front veranda.

Edge width, depth below the slab, and the veranda treatment are not authoritatively recorded. This specification does not invent them and does not emit a Speakeasy result.

## Determinism

The same `engine_id`, `engine_version`, variant, measurement system, inputs, assumptions, and null product specification produce the same components and quantities.

`result_id` and `produced_at` are per run. They are outside the fingerprint. Example fixtures use fixed `result_id` values so the files stay portable. A live run uses a new id.
