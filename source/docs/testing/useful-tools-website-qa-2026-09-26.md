# Useful Tools website QA — 2026-09-26

Release candidate: Useful Tools directory, Concrete Calculator, and Ontario Residential — V1 Stair Calculator.

## Automated release gate

| Gate | Result |
| --- | --- |
| Route and Version 26 frozen-page source verification | PASS |
| Concrete and stair portable conformance fixtures | PASS — 9 concrete and 5 stair fixtures |
| Useful Tools focused test suite | PASS — 27/27 |
| Production build | PASS |
| Ontario stair evidence/profile mirror | PASS — 4 verified limits |

The conformance gate corrected the original slab fixture from `4.530702422016 m³` to the exact canonical result `4.53069545472 m³`; equivalent imperial and metric inputs now share that exact fixture value.

## Change boundary

- Home: only the previously approved Useful Tools hero link wording, icon, and destination differ from Version 26.
- Plan, Price, Contract, Build, Monitor, and Learn: exact source match to the Version 26 baseline.
- Supplier Connection and Contractor Connection: no Useful Tools link or content change.
- Shared header, footer, logo, connection-page hero assets, and existing calculator: unchanged.

## Responsive and interaction review

Automated source/build checks cover 16px calculator inputs, 44px touch controls, responsive one-column breakpoints, accessible live result regions, named validation states, device-local save failure handling, print/share actions, and unit-equivalent calculations.

Rendered checks required before publication:

- Useful Tools, Concrete, and Stairs at 320, 375, 390, 768, 1024, and 1440 px;
- no clipping, horizontal scrolling, text collision, or diagram distortion;
- keyboard order and visible focus;
- live result updates, unit switching, save/restore/remove, print, and share fallback;
- frozen-page visual comparison against Version 26.

The managed browser-review capability was unavailable in the execution environment. Therefore this record does not claim rendered desktop/mobile QA. Publication remains blocked pending Joel's private visual review or a later managed-browser pass.

## Stair visual-geometry remediation — 2026-09-30

The Stair calculation remains governed by `lib/useful-tools/stairs.mjs` and the Ontario Residential — V1 profile. The calculation module and profile were not changed. `StairDiagram` now consumes a deterministic geometry projection from `lib/useful-tools/stair-diagram-geometry.mjs`; treads, risers, stair path, stringer, dimensions, and stringer-label angle all derive from the same governed result.

The durable geometry regression pin is `tests/useful-tools-stair-diagram-geometry.test.mjs`, supported by a UI binding assertion in `tests/useful-tools-stairs-ui.test.mjs`. It protects:

- the 38 in × 44 in benchmark: 5 risers, 4 treads, 7.60 in rise, 11.00 in going, 58.14 in stringer, and 40.815° slope;
- rendered rise/run ratio and stringer rise/run alignment;
- tread and riser counts;
- a materially different 112 in × 168 in stair;
- identical physical geometry after Imperial/Metric conversion.

Verification results:

| Gate | Result |
| --- | --- |
| Stair calculation, UI, and geometry regression tests | PASS — 19/19 |
| Concrete/Stair conformance | PASS — 9 concrete and 5 stair fixtures |
| Ontario Residential — V1 evidence/profile | PASS — 4/4 verified limits |
| Useful Tools focused tests | PASS — 37/37 |
| Useful Tools route verification | PASS |
| Full `npm test` | 45/47 — two unchanged pre-existing failures: development-only `codex-preview` metadata and starter animation/scroll utility output |
| Production build | PASS |

Rendered QA passed at a 1363 px desktop viewport and a 375 px CSS mobile viewport inside a 390 px phone review frame. Both the 38 × 44 benchmark and the 112 × 168 comparison stair were inspected. Imperial, Metric, and the round trip preserved the same rendered dimensions and 40.815° benchmark slope. No horizontal scrolling, clipping, distortion, or unit-dependent geometry movement was observed.

## Employment vs. Entrepreneurship stabilization — 2026-09-30

The neutral employment-versus-entrepreneurship mathematics remain unchanged. The calculator now displays only assumptions supported by that model:

- Quote Win Rate was removed rather than double-discounting realized utilization and revenue.
- Seasonality and Slower-Season Approach were replaced with guidance to enter actual working weeks and any Winter Protection / Heat cost.
- Small Contracting Business was removed because the source contained no distinct governed crew economics.
- Helper Wage is identified as an owner estimate while its regional benchmark remains contextual.
- The Home route check follows the approved Home → Useful Tools path.

The durable participation regression is `tests/employment-calculator.test.mjs`. It verifies every employment input, owner-capacity input, conditional helper input, and annual operating-cost input against its intended output relationship.

## Concrete authority stabilization — 2026-09-30

The public Concrete route continues to use `components/useful-tools/ConcreteSlabCalculator.tsx` and the governed `lib/calculation-engine/concrete-slab.ts` engine. Its only public modes are Standard Slab and Thickened Edge. The Useful Tools directory now describes only those live modes.

The earlier broad implementation in `components/useful-tools/ConcreteCalculator.tsx` and `lib/useful-tools/concrete.mjs` is retained as a dormant superseded prototype. Its historical compatibility tests are explicitly labelled and do not establish live public capability or Contract V1 conformance. The authority boundary is pinned by `tests/concrete-authority.test.mjs` and recorded in `docs/calculation-engine/concrete-authority.md`.

Verification results:

| Gate | Result |
| --- | --- |
| Concrete authority, governed engine/consumer, dormant-compatibility, and UI tests | PASS — 21/21 |
| Focused Useful Tools suite | PASS — 51/51 |
| Governed `concrete_slab` fixture reproduction and fingerprints | PASS — 7/7 |
| Useful Tools, calculator route, and calculator mathematics verification | PASS |
| Full `npm test` | 54/56 — the same two unrelated baseline failures: development-preview metadata and catalog animation/scrolling utilities |
| Production build | PASS |

Desktop functional QA passed at 1363 px against the unchanged Version 29 calculator component. Standard Metric produced 8 m³ net plus 0.4 m³ waste for 8.4 m³ total. Thickened Edge Metric produced 8 m³ base plus 6.048 m³ edge plus 0.702 m³ waste for 14.75 m³ total. Thickened Edge Imperial produced 14.815 yd³ base plus 8.296 yd³ edge plus 1.156 yd³ waste for 24.267 yd³ total. Zero length was rejected with `length must be greater than zero.` The desktop document width remained within the viewport with no horizontal overflow.

The public calculator UI and responsive CSS were not modified in this package. The existing 390 px mobile implementation, touch sizing, one-column breakpoint, save/download controls, and Contract V1 result rendering remain byte-for-byte unchanged; the focused render test remained green. The only user-visible change is the shorter, accurate Concrete description on the compact Useful Tools directory, which removes the previous capability overstatement and reduces rather than increases mobile wrapping risk.

## Website test-baseline stabilization — 2026-09-30

The two remaining full-suite failures were obsolete initial-import expectations rather than production Website defects:

- `rendered-html.test.mjs` continued to require a development-only `codex-preview` meta tag after commit `1cf07e2` deliberately removed it from the production layout. The test now protects the live CalibraytAI title, description, favicon, HTML response, and absence of the obsolete preview marker.
- `ui-components.test.mjs` continued to require animation and scrolling utilities from an unimported starter catalog stylesheet. No current Website route or component uses those utilities. The test now protects the Website's actual built responsive CSS for smooth scrolling, Useful Tools rows, calculator layouts, Stair diagrams, and the active 640 px, 520 px, and 860 px breakpoints. It also prevents the unused catalog animation bundle from being added accidentally.

This stabilization changes tests and this QA record only. Production source, calculator logic, Contract V1, Website copy, layout, CSS, and assets remain unchanged. Employment, governed Concrete, and Stair remain closed; the Stair geometry pin remains active.

Verification results:

| Gate | Result |
| --- | --- |
| Corrected baseline and companion UI tests | PASS — 5/5 |
| Employment regression | PASS — 5/5 |
| Concrete authority, engine, consumer, UI, and compatibility regression | PASS — 21/21 |
| Stair calculation, UI, geometry, profile, and visual-pin regression | PASS — 19/19 |
| Useful Tools directory, local-save, metadata, and component regression | PASS — 11/11 |
| Concrete/Stair conformance | PASS — 9 compatibility concrete and 5 governed stair fixtures |
| Ontario Residential — V1 evidence/profile | PASS — 4/4 verified limits |
| Useful Tools and calculator route/mathematics verification | PASS |
| Full `npm test` | PASS — 56/56 |
| Production build | PASS |
| Production artifact comparison | PASS — output identical after normalization of build-generated prerender secret and UUID values |

Repeated clean builds proved that the only byte differences in generated output are Vinext's per-build prerender secret and UUID values. After normalizing those generated values, the complete production artifacts match. No deployed Website version was created by this package.
