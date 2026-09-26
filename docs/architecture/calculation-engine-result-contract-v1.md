# Calculation Engine Result Contract V1

| Attribute | Value |
|-----------|--------|
| Status | **ACCEPTED / PINNED** |
| Date | 2026-09-26 |
| Kind | Architecture contract. Not a calculator. Not an estimate mapper. |
| Website | Separate repository, separate deployment. No runtime call. |
| Platform | May later consume a result. Does not own the public calculator. |

**Subsequent status (2026-09-26 hosted validation):** This envelope remains **ACCEPTED / PINNED**. It was not rescored. Migration `j0e1f2a3b4c5` is applied on the hosted validation database. The Mac primary remains `h8c9d0e1f2a3`.

**Subsequent status (2026-09-26):** This envelope remains **ACCEPTED / PINNED**. Estimating can review a valid result and confirm a quantity onto an estimate (`app/services/calculation_estimate_mapping.py`). That step does not calculate, and it does not change this envelope. Migration `j0e1f2a3b4c5` is in the repository. The hosted validation database now has that revision. The Mac primary does not.

This record is the handshake between a public calculation engine and a future Platform estimate mapping step. It does not authorize either implementation.

## Purpose

A calculation engine turns measurements and assumptions into a versioned structured result.

```text
Measurements / assumptions
        ↓
Calculation engine
        ↓
Versioned structured result
```

On the Platform only, and only after a later authorization:

```text
Structured result
        ↓
Human-reviewed estimate mapping
        ↓
Company costs / labour / reusable work
        ↓
Estimate commercial settings
        ↓
Estimate
        ↓
Proposal
```

## Ownership

The engine owns inputs, assumptions, the deterministic calculation, the structured result, and the engine version.

The engine does not own company identity, Cost Item ids, Assembly ids, labour-rate ids, company margin, pricing policy, sell price, proposal price, estimate ids, or Platform workflow state.

The Website may render the result. The Platform may later consume it. Neither repository requires runtime access to the other.

Employment versus entrepreneur may use the same engineering principles. Its result is not this contract. FG-039 stays parked.

## Why two fields were added

The starting proposal was `engine_id`, `engine_version`, `variant`, `measurement_system`, `inputs`, `assumptions`, `components`, `quantities`, and `product_specification`.

Those fields stay. Two envelope fields are required for safe consumption:

| Field | Why it is required |
|-------|--------------------|
| `contract_version` | Tells the Platform which envelope this is. `engine_version` is the calculation version. They are not the same. |
| `result_id` | Distinguishes one run from another so a later audit row can point at a result without using an estimate id. |

`produced_at` is optional. It is the producer clock. It is not the time a contractor accepted a mapping. It is excluded from the calculation fingerprint.

Inside `inputs`, `assumptions`, `components`, and `quantities`, each entry needs a stable `code`, a decimal `value` or `quantity`, and a `unit_code`. A display label is not an identity and is not a unit.

## V1 shape

```text
contract_version          "1"
result_id                 string, unique to this run
engine_id                 string
engine_version            string
variant                   string or null
measurement_system        "metric" or "imperial"
inputs                    array of coded values
assumptions               array of coded values
product_specification     object or null
components                array of quantity lines
quantities                array of quantity lines
produced_at               optional timestamp string
```

A coded value:

```text
code        string
value       decimal string
unit_code   a V1 unit code
label       optional display text
```

A quantity line:

```text
code        string
quantity    decimal string, zero or greater
unit_code   a V1 unit code other than percent
label       optional display text
```

`components` are intermediate results worth keeping, including waste as a quantity. `quantities` are the final quantities a later mapper may carry forward. Do not collapse a useful component into the total.

`product_specification` carries the product or system that governed the calculation. It is null when the engine has no product system. For `icf_wall` it is required, because ICF systems do not share one geometry. The contract does not store manufacturer dimensions as universal constants. Any geometry number in the specification is a value recorded for the selected system.

## Unit codes

Every mapped quantity uses a `unit_code` from this list. A display word is not enough.

| Code | Meaning |
|------|---------|
| `m` `mm` `ft` `in` | Length |
| `m2` `ft2` | Area |
| `m3` `ft3` `yd3` | Volume |
| `ea` | Count |
| `percent` | Ratio. Allowed on inputs and assumptions. Not allowed on components or quantities. |

`measurement_system` records how the person entered the measurements. Each value still carries its own `unit_code`.

A trade unit that is not in this list is not valid Contract V1. Adding it is a contract revision. Wall framing, drywall, roofing, and flooring can use this list when their mappable results are length, area, volume, or count. A roofing square, for example, is expressed as `ft2` until a later contract revision names another unit.

Numeric values are decimal strings, not JSON floats.

## Determinism

The same `engine_id`, `engine_version`, `variant`, `measurement_system`, inputs, assumptions, and `product_specification` produce the same components and quantities.

The calculation fingerprint is SHA-256 over canonical JSON of the result with `result_id` and `produced_at` removed. Canonical JSON sorts object keys, uses the decimal strings as written after stripping trailing zeros, and uses no insignificant whitespace. `result_id` and `produced_at` do not change the fingerprint.

## Validation

A result is valid enough for the Platform to consider mapping when all of the following hold:

- `contract_version` is `"1"`.
- `result_id`, `engine_id`, and `engine_version` are non-empty strings.
- `variant` is present and is either a non-empty string or null.
- `measurement_system` is `metric` or `imperial`.
- `inputs` and `assumptions` are arrays of coded values with V1 unit codes.
- `components` is an array of quantity lines.
- `quantities` has at least one quantity line.
- Every quantity line has a `code`, a non-negative decimal `quantity`, and a V1 unit code other than `percent`.
- `product_specification` is an object or null.
- When `engine_id` is `icf_wall`, `product_specification` includes a non-empty `system_name` and a `nominal_core_thickness_in` of `6`, `8`, `10`, or `12`.
- When `engine_id` is `concrete_slab`, `variant` is `standard` or `thickened_edge`.
- The payload contains none of these keys at any depth: `organization_id`, `cost_item_id`, `assembly_id`, `labour_task_id`, `labour_rate_id`, `estimate_id`, `estimate_version_id`, `pricing_policy_id`, `policy_code`, `sell_price`, `unit_cost`, `markup_percent`, `margin`, `proposal_id`.

An unknown quantity `code` is still a valid result. It is not a reason to reject the contract.

## First proving engines

These engines are not implemented here. They are the minimum shapes this contract must carry.

| Engine | `engine_id` | Variants |
|--------|-------------|----------|
| Concrete slab | `concrete_slab` | `standard`, `thickened_edge` |
| ICF wall | `icf_wall` | none required |

Illustrative payloads, not formulas, live in `docs/architecture/fixtures/calculation-result-contract-v1/`.

Stairs, wall framing, drywall, roofing, and flooring may use this same envelope when their results are length, area, volume, or count in the V1 unit list. They are not implemented here, and they are not the first proving engines.

## Consumer metadata

An optional project or reference name is not part of Contract V1.

The engine result is the envelope in this record. Its fingerprint covers that envelope, excluding `result_id` and `produced_at`.

Consumer metadata sits outside that object. It may hold an optional project or reference label, a download title, a date the person created the copy when that date is distinct from `produced_at`, and other local display or save context. It must not change inputs, assumptions, specification, components, or quantities.

Consumer metadata does not include an account, an email address, a phone number, a contact form, a lead-capture field, a marketing identifier, or a company price.

```text
Engine result          Contract V1. Deterministic.
Consumer metadata      Optional label and local presentation. Outside the fingerprint.
```

## Save and download

Save on this device and download calculation are consumer actions. The engine does not perform them.

The Website may later print a calculation summary from the Contract V1 result plus optional consumer metadata. A visitor can open a public tool, calculate, see the full result, save it on the device, and download it without an account.

The Platform may later offer save to project, add to estimate, and download calculation. Those are Platform workflow actions. They are not part of this contract, and they are not implemented here.

## Provenance split

The calculation result keeps the envelope, inputs, assumptions, product specification, components, quantities, and optional `produced_at`.

A future Platform mapping and audit record keeps, at acceptance:

- `result_id` and the calculation fingerprint
- `engine_id`, `engine_version`, and `variant`
- a frozen copy of the inputs, assumptions, product specification, and the original quantity and unit
- the mapping the contractor confirmed: target kind and target id
- the time of acceptance and the person who confirmed it

Target kind is one of: Cost Item, Reusable work / Assembly, labour input, or another existing estimate line type (`Custom`, `Allowance`). Labour input is not an estimate line type today. A later mapper must not pretend a labour snapshot is a Cost Item.

Company ids, prices, and the confirming user belong only on the Platform record.

## Human review

A calculated quantity does not become an estimate line by itself.

```text
Run calculation
        ↓
Review result
        ↓
Review proposed mappings
        ↓
Confirm
        ↓
Add to estimate
```

The mapper may suggest. The contractor confirms. This matches the existing takeoff pattern of a suggested quantity and a confirmed quantity (`TakeoffEstimateInsertion` in `app/models/takeoff_estimate_insertion.py`). That workflow is not implemented for this contract.

## Unmapped quantities

When a result contains a quantity and the company has no mapping for that code:

- keep the quantity
- do not guess a Cost Item, Assembly, or labour task
- do not create a company cost record
- show it for a person to resolve

## Recalculation

Changing inputs, or running a newer engine version, produces a new result with a new `result_id`.

An estimate quantity that already came from an older result stays as it was. A locked estimate version (`EstimateVersion.is_locked`) is not rewritten. A pricing snapshot and a labour snapshot already freeze commercial and labour facts the same way.

```text
Original calculation     the result that was accepted
Recalculated result      a new result_id
Updated estimate mapping a new human confirmation
```

The new result does not replace the old acceptance.

## Website boundary

The Website owns the calculator page, the public engine, the structured result, and public rendering.

The Platform does not call the Website. The Website does not call the Platform. There is no shared database, no Platform sign-in from the Website, and no company data in a public calculator.

This record does not create a submodule, a cross-repository import, an API, or a package dependency.

## Shared code later

A pure package could be useful after `concrete_slab` and `icf_wall` have both produced real results that validate against this contract. Until then it is not worth the dependency.

If it is reconsidered, it may contain only calculation logic and these contract types. It must not contain Flask, database models, company pricing, authentication, or either user interface. Creating it requires a separate decision.

## Platform impact

Inspected and left unchanged:

- `EstimateVersion` and `EstimateLineItem` (`app/models/estimate.py`). Line types are Cost Item, Assembly, Custom, and Allowance. A line stores quantity, unit, cost, waste, markup, and sell price.
- Cost Items and Assemblies. They are company inputs. They are mapping targets, not calculation outputs.
- `EstimateLabourSnapshot` (`app/models/labour_engine.py`). Labour quantity, rate, and cost are snapshotted apart from estimate lines.
- `EstimatePricingSnapshot`. Customer price is snapshotted apart from quantities.
- `TakeoffEstimateInsertion`. The closest current pattern: human-confirmed quantity, target Cost Item or Assembly, actor, and a frozen citation. It does not accept this contract.

A future mapper belongs in Estimating, beside takeoff-to-estimate mapping, not in Costs & pricing and not in the pricing engine. The review screen belongs on the estimate. Persistence would be new organization-scoped rows: a frozen result, suggested mappings, and an acceptance event. That needs a later approved migration. This record creates no schema.

Later tests, when authorized, must prove confirmation, an unmapped quantity left unresolved, no silent cost-item creation, no rewrite of an accepted quantity, and no company id inside the result.

## Prohibited coupling

- No runtime dependency between Website and Platform.
- No company id, price, or estimate id inside a calculation result.
- No silent estimate line.
- No calculator formula and no mapper in this record.
