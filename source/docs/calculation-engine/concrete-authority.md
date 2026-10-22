# Concrete calculation authority

Status: **RECORDED — 2026-09-30**

## Governed live authority

`lib/calculation-engine/concrete-slab.ts` is the **GOVERNED LIVE AUTHORITY** for the public Concrete Calculator.

- Public route: `app/useful-tools/concrete/page.tsx`
- Public consumer: `components/useful-tools/ConcreteSlabCalculator.tsx`
- Engine: `concrete_slab`
- Engine version: `1.0.0`
- Public variants: `standard` and `thickened_edge`
- Result envelope: pinned Contract V1
- Governed fixtures: `docs/calculation-engine/fixtures/concrete-slab-1.0.0/`
- Engine regression: `tests/concrete-slab-engine.test.mjs`
- Consumer regression: `tests/concrete-slab-consumer.test.mjs`

The engine owns Metric and Imperial normalization, base-slab geometry, additional perimeter-edge geometry, user-entered waste, deterministic three-decimal rounding, component reconciliation and the Contract V1 result.

## Dormant broad implementation

`lib/useful-tools/concrete.mjs` and `components/useful-tools/ConcreteCalculator.tsx` are a **DORMANT SUPERSEDED PROTOTYPE** retained for historical compatibility. They predate the governed slab engine, are not imported by the public Concrete route, do not emit the governed Contract V1 result and must not be advertised as current public capability.

Their compatibility tests remain legitimate historical protection, but their shape coverage does not establish public product capability or governed conformance. They must not be promoted, merged into the governed engine or routed publicly without a separately authorized engine-design package.

## Test classification

| Classification | Files | Meaning |
| --- | --- | --- |
| Governed live engine | `tests/concrete-slab-engine.test.mjs` | Reproduces the approved `concrete_slab` 1.0.0 fixtures and validation rules. |
| Contract V1 / consumer | `tests/concrete-slab-consumer.test.mjs` | Protects the structured handoff and public calculator surface. |
| Route / authority | `tests/concrete-authority.test.mjs`, `tests/useful-tools-concrete-ui.test.mjs` | Protects the public route, truthful directory copy and authority boundary. |
| Dormant compatibility | `tests/useful-tools-concrete.test.mjs`, `lib/useful-tools/conformance/concrete.json` | Retains historical prototype behaviour without claiming it is public or governed. |

Contract V1 remains accepted and pinned. This stabilization does not change engine mathematics or the contract.
