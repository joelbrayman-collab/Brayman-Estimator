# CalibraytAI Useful Tools Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a mobile-first Useful Tools landing page, comprehensive concrete calculator, and verified Ontario V1 stair calculator to the CalibraytAI public website while preserving the existing website baseline.

**Architecture:** A pure browser-side JavaScript calculation core owns units, concrete geometry, stair geometry, validation, and profile evaluation. React client components provide the website presentation, while JSON conformance fixtures define the portable contract the separately governed contractor platform must later consume and reproduce. The website stores optional saved calculations locally and does not add a backend or mutate project data.

**Tech Stack:** Vinext/Next.js 16, React 19, TypeScript 5.9, browser ES modules, Node 22 test runner, existing CalibraytAI CSS tokens, Sites hosting.

**Spec:** `docs/superpowers/specs/2026-09-26-useful-tools-design.md`

## Global Constraints

- The public entry point is named **Useful Tools**.
- Replace only the existing home-hero calculator button wording and destination; do not modify the seven frozen Version 15 pages.
- Useful Tools contains Employment vs. Entrepreneurship, Concrete Calculator, and Stair Calculator.
- The contractor platform receives a separate implementation plan after its authoritative repository is opened and inspected.
- Calculations run entirely in the browser and never modify projects, estimates, prices, or orders.
- Support imperial and metric units; preserve full internal precision.
- Default concrete waste is 10% and remains editable.
- Ontario Residential — V1 is the only enabled stair profile.
- No Ontario threshold may be encoded until its authoritative source and manual verification record are committed and approved.
- Mobile support begins at 320px with no clipping, collision, or horizontal scrolling.
- Do not add a dependency unless an existing browser or platform capability cannot meet the requirement.

## Review Focus

- Mixed feet/inches and decimal metric inputs must normalize without double conversion or hidden rounding; Task 1 tests both paths.
- Extremely small and extremely large concrete dimensions must remain finite and produce a non-decreasing recommended order; Task 1 tests both boundaries.
- A stair layout exactly on, immediately inside, and immediately outside every Ontario threshold must produce the correct profile result; Task 6 generates boundary cases from the verified profile.
- Local storage being disabled, full, or corrupt must not prevent calculation or falsely report a successful save; Task 4 tests all three cases.
- Phone-width diagrams and result actions must not create horizontal scrolling or hide labels at 320px; Tasks 3, 7, and 8 include explicit responsive checks.

---

### Task 1: Shared units and concrete calculation core

**Files:**
- Create: `lib/useful-tools/units.mjs`
- Create: `lib/useful-tools/concrete.mjs`
- Create: `lib/useful-tools/contracts.d.ts`
- Create: `lib/useful-tools/conformance/concrete.json`
- Create: `tests/useful-tools-concrete.test.mjs`

**Interfaces:**
- Produces: `toMetres(value, unit)`, `fromCubicMetres(value, unit)`, `calculateConcreteSection(section)`, `calculateConcretePour(input)`, and portable concrete conformance fixtures.
- `calculateConcreteSection(section)` accepts one discriminated shape: `slab`, `footing`, `wall`, `round-column`, `post-hole`, `curb`, or `concrete-stairs`.
- `calculateConcretePour({sections,wastePercent,orderIncrementM3,bagYieldM3?,truckCapacityM3?})` returns `{baseM3,wasteM3,adjustedM3,recommendedOrderM3,bagCount?,truckCount?,sections}`.

- [ ] **Step 1: Write failing conversion and shape tests**

Add Node tests asserting:

- 12 inches, 1 foot, 0.3048 metres, and 304.8 millimetres normalize to the same length.
- A 20 ft × 24 ft × 4 in slab returns the same base volume as its metric equivalent.
- Footing, wall, round-column, post-hole, and curb fixtures match independently calculated cubic-metre values within `1e-9`.
- Solid concrete stairs use `width × treadRun × riserHeight × n(n+1)/2` for `n` risers.
- Quantity multiplies base volume before waste.
- 10% waste produces `adjustedM3 = baseM3 × 1.10`.
- Recommended order rounds upward to the supplied increment and never downward.
- Bag and truck counts use `Math.ceil(adjustedM3 / suppliedCapacity)`.
- Missing, zero, negative, `NaN`, and infinite dimensions return typed validation errors rather than numeric output.
- Very small and very large valid inputs remain finite.

- [ ] **Step 2: Run the focused test and verify failure**

Run: `node --test tests/useful-tools-concrete.test.mjs`  
Expected: FAIL because the shared modules do not exist.

- [ ] **Step 3: Implement the units and concrete modules**

Use metres and cubic metres as canonical internal units. Keep geometry, conversion, validation, ordering increments, bag capacity, and truck capacity separate in the return structure. Add JSDoc to the `.mjs` exports and matching declarations to `contracts.d.ts`.

- [ ] **Step 4: Add portable conformance fixtures**

Write `concrete.json` with at least one imperial and one metric case for every shape plus quantity, waste, ordering increment, bag, and truck cases. Store canonical expected cubic-metre values without formatted strings.

- [ ] **Step 5: Run focused and build verification**

Run: `node --test tests/useful-tools-concrete.test.mjs && npm run build`  
Expected: all new tests PASS and the production build exits 0.

- [ ] **Step 6: Commit**

```bash
git add lib/useful-tools tests/useful-tools-concrete.test.mjs
git commit -m "feat: add useful tools concrete core"
```

### Task 2: Useful Tools landing page and public entry point

**Files:**
- Create: `app/useful-tools/page.tsx`
- Modify: `app/page.tsx`
- Modify: `app/globals.css`
- Create: `scripts/verify-useful-tools-routes.mjs`

**Interfaces:**
- Consumes: existing `Header`, `Footer`, `.hero-tool-link`, `.btn`, `.section`, `.wrap`, `.card`, and brand tokens.
- Produces: `/useful-tools/` and links to all three tool routes.

- [ ] **Step 1: Write the failing route contract**

The script must assert:

- Home contains exactly one `/useful-tools/` hero link labelled `Useful Tools`.
- Home no longer contains a direct `/employment-vs-entrepreneurship/` hero link.
- The landing page links exactly once to each of `/employment-vs-entrepreneurship/`, `/useful-tools/concrete/`, and `/useful-tools/stairs/`.
- The six lifecycle pages, `app/site.tsx`, and both connection pages contain no unintended `/useful-tools/` additions.
- The six non-Home lifecycle page sources remain byte-identical to commit `e1107f32593b6270297ed0ce932e7cb899cebc63`, and the Home diff is limited to the approved hero button wording, icon, accessible label, and destination.

- [ ] **Step 2: Run the route contract and verify failure**

Run: `node scripts/verify-useful-tools-routes.mjs`  
Expected: FAIL because the landing page and new hero destination do not exist.

- [ ] **Step 3: Build the landing page**

Use the existing header/footer, page width, typography, navy hero, light section, cards, and buttons. Each card contains one familiar Lucide icon, a concise practical description, and one launch link. Do not add a header navigation item.

- [ ] **Step 4: Change the home-hero access point**

Keep the existing button dimensions and top-right placement. Change its accessible label, visible text, icon, and destination to `Useful Tools` and `/useful-tools/`.

- [ ] **Step 5: Add scoped responsive styling**

Add only `.tools-*` selectors and any necessary updated `.hero-tool-link` child styling. Do not modify lifecycle, supplier, contractor, header, footer, or shared phase selectors.

- [ ] **Step 6: Verify and commit**

Run: `node scripts/verify-useful-tools-routes.mjs && npm run build`  
Expected: route contract PASS; build exits 0.

```bash
git add app/useful-tools/page.tsx app/page.tsx app/globals.css scripts/verify-useful-tools-routes.mjs
git commit -m "feat: add useful tools entry point"
```

### Task 3: Mobile-first concrete calculator interface

**Files:**
- Create: `app/useful-tools/concrete/page.tsx`
- Create: `components/useful-tools/ConcreteCalculator.tsx`
- Create: `components/useful-tools/ConcreteDiagram.tsx`
- Modify: `app/globals.css`
- Create: `tests/useful-tools-concrete-ui.test.mjs`

**Interfaces:**
- Consumes: `calculateConcretePour(input)` from Task 1.
- Produces: an interactive `/useful-tools/concrete/` page and accessible dimension diagram for all seven shapes.

- [ ] **Step 1: Write failing interface-source tests**

Assert the component exposes selectors for all seven shape identifiers; imperial/metric controls; quantity; 10% default waste; section add/remove; base, waste, adjusted, and recommended results; and an `aria-live="polite"` result region. Assert every diagram has a role and accessible label.

- [ ] **Step 2: Verify failure**

Run: `node --test tests/useful-tools-concrete-ui.test.mjs`  
Expected: FAIL because the route and components do not exist.

- [ ] **Step 3: Implement the calculator state and fields**

Use one client component. Keep values as user-entered strings until validation, convert only at the calculation boundary, and preserve valid section data when another field fails. Show only fields used by the selected shape. Support multiple named sections and combined-pour totals.

- [ ] **Step 4: Implement the dynamic geometry diagram**

Use code-native SVG with navy geometry and gold measurement lines. Labels and accessible text must update with the selected shape and current valid dimensions. Do not use a generated raster diagram.

- [ ] **Step 5: Implement result formatting**

Show base, waste, adjusted, and recommended order values in both cubic metres and cubic yards. Show bags only after a bag yield is selected and trucks only after capacity is entered. State that supplier capacities and final order quantities require confirmation.

- [ ] **Step 6: Add scoped mobile-first styles**

Use `.tool-calculator-*` selectors, 16px editable input text at phone widths, minimum 44px touch targets, stacked phone results, and no horizontal overflow at 320px.

- [ ] **Step 7: Verify and commit**

Run: `node --test tests/useful-tools-concrete.test.mjs tests/useful-tools-concrete-ui.test.mjs && npm run build`  
Expected: tests PASS; build exits 0.

```bash
git add app/useful-tools/concrete components/useful-tools app/globals.css tests/useful-tools-concrete-ui.test.mjs
git commit -m "feat: add concrete calculator interface"
```

### Task 4: Device-local saves, print, and share

**Files:**
- Create: `lib/useful-tools/local-saves.mjs`
- Create: `components/useful-tools/ToolActions.tsx`
- Create: `tests/useful-tools-local-saves.test.mjs`
- Modify: `components/useful-tools/ConcreteCalculator.tsx`

**Interfaces:**
- Produces: `loadSavedCalculations(storage,key)`, `saveCalculation(storage,key,record)`, `removeSavedCalculation(storage,key,id)`, and reusable `ToolActions`.
- Saved record schema: `{id,toolVersion,calculatorType,name,unitSystem,input,output,savedAt}`.

- [ ] **Step 1: Write failing storage tests**

Test round-trip save/load/remove, corrupt JSON recovery, unavailable storage, quota failure, and stable most-recent-first ordering. Assert failures return an explicit unsuccessful result and never throw into calculation rendering.

- [ ] **Step 2: Verify failure**

Run: `node --test tests/useful-tools-local-saves.test.mjs`  
Expected: FAIL because the storage module does not exist.

- [ ] **Step 3: Implement local storage and actions**

Use a versioned key beginning `calibraytai.useful-tools.v1`. Print calls `window.print()`. Share uses `navigator.share()` when available and otherwise copies a plain-text summary. Do not claim success unless the selected operation resolves.

- [ ] **Step 4: Integrate with Concrete Calculator**

Add Save, Print, Share, Start New, and a compact saved-calculation list. Loading a saved record must restore the unit system, sections, waste, and optional capacities without recalculating from formatted strings.

- [ ] **Step 5: Verify and commit**

Run: `node --test tests/useful-tools-local-saves.test.mjs tests/useful-tools-concrete.test.mjs && npm run build`  
Expected: tests PASS; build exits 0.

```bash
git add lib/useful-tools/local-saves.mjs components/useful-tools tests/useful-tools-local-saves.test.mjs
git commit -m "feat: add useful tools device actions"
```

### Task 5: Ontario Residential V1 evidence gate

**Files:**
- Create: `docs/reference/ontario-residential-stairs-v1.md`
- Create: `lib/useful-tools/profiles/ontario-residential-v1.json`
- Create: `scripts/verify-stair-profile-evidence.mjs`

**Interfaces:**
- Produces: a reviewed profile with `id`, `label`, `codeEdition`, `effectiveDate`, `verifiedAt`, `scope`, `sources`, and named numeric limits.
- Blocks: Task 6 must not begin until Joel approves the evidence record and profile values.

- [ ] **Step 1: Acquire authoritative sources**

Use the Government of Ontario 2024 Building Code page and the official 2024 Building Code Compendium currently in force. Record the exact Division B article/table references governing the selected residential stair scope. Record any amendments effective on the implementation date.

- [ ] **Step 2: Write the human-readable evidence record**

For each encoded limit, list the exact field name, value, unit, applicability, source document, article/table, effective date, and verification date. Explain exclusions such as winding stairs, exterior stairs, guards, landings, headroom, accessibility, and occupancies not covered by the selected profile.

- [ ] **Step 3: Encode the profile and write the evidence verifier**

The verifier must reject missing sources, missing article references, missing dates, non-positive limits, duplicate field names, and a profile whose values do not exactly match the evidence record.

- [ ] **Step 4: Run the evidence verifier**

Run: `node scripts/verify-stair-profile-evidence.mjs`  
Expected: PASS and print the profile id, code edition, effective date, and verified limit count.

- [ ] **Step 5: Stop for Joel's approval of the evidence record**

Provide `docs/reference/ontario-residential-stairs-v1.md` and the profile JSON for review. Do not implement profile evaluation until Joel explicitly approves them.

- [ ] **Step 6: Commit the approved evidence gate**

```bash
git add docs/reference/ontario-residential-stairs-v1.md lib/useful-tools/profiles/ontario-residential-v1.json scripts/verify-stair-profile-evidence.mjs
git commit -m "docs: verify Ontario stair profile"
```

### Task 6: Stair geometry and profile evaluation core

**Files:**
- Create: `lib/useful-tools/stairs.mjs`
- Modify: `lib/useful-tools/contracts.d.ts`
- Create: `lib/useful-tools/conformance/stairs.json`
- Create: `tests/useful-tools-stairs.test.mjs`

**Interfaces:**
- Consumes: approved `ontario-residential-v1.json` and unit conversion functions.
- Produces: `calculateStairCandidates(input)`, `selectRecommendedStair(input,profile)`, and `evaluateStairProfile(layout,profile)`.
- Stair result: `{riserCount,treadCount,riserHeightM,treadRunM,totalRiseM,totalRunM,stringerLengthM,angleDegrees,checks,overallStatus}`.

- [ ] **Step 1: Write failing geometry tests**

Assert `treadCount = riserCount - 1`; `riserHeight = totalRise / riserCount`; `treadRun = availableRun / treadCount`; stringer length follows Pythagoras; angle follows `atan(totalRise / totalRun)`; and equivalent imperial/metric input returns the same canonical result.

- [ ] **Step 2: Write generated profile-boundary tests**

For every approved minimum and maximum in the JSON profile, generate exact-boundary, one-display-increment-inside, and one-display-increment-outside cases. Assert check id, measured value, limit, status, and overall status.

- [ ] **Step 3: Verify failure**

Run: `node --test tests/useful-tools-stairs.test.mjs`  
Expected: FAIL because the stair module does not exist.

- [ ] **Step 4: Implement candidate generation and recommendation**

Generate integer riser-count candidates around `totalRise / preferredRiserHeight`. Reject non-finite and geometrically impossible candidates. Select the valid candidate closest to the profile's preferred rise/run relationship; if none fits, return the nearest geometry with explicit failed checks rather than inventing a compliant layout.

- [ ] **Step 5: Add portable conformance fixtures**

Include valid, exact-boundary, out-of-profile, insufficient-run, metric-equivalent, and large-input cases with canonical outputs and named profile checks.

- [ ] **Step 6: Verify and commit**

Run: `node scripts/verify-stair-profile-evidence.mjs && node --test tests/useful-tools-stairs.test.mjs && npm run build`  
Expected: evidence and tests PASS; build exits 0.

```bash
git add lib/useful-tools tests/useful-tools-stairs.test.mjs
git commit -m "feat: add verified Ontario stair core"
```

### Task 7: Stair calculator and dynamic measurement diagram

**Files:**
- Create: `app/useful-tools/stairs/page.tsx`
- Create: `components/useful-tools/StairCalculator.tsx`
- Create: `components/useful-tools/StairDiagram.tsx`
- Modify: `components/useful-tools/ToolActions.tsx`
- Modify: `app/globals.css`
- Create: `tests/useful-tools-stairs-ui.test.mjs`

**Interfaces:**
- Consumes: `selectRecommendedStair(input,profile)`, the approved Ontario profile, and local save/actions interfaces.
- Produces: interactive `/useful-tools/stairs/` with a dynamically scaled side-elevation diagram.

- [ ] **Step 1: Write failing interface-source tests**

Assert visible inputs for total rise, available run, width, tread thickness, unit system, and the named Ontario profile; outputs for risers, treads, exact rise/run, angle, stringer length, profile checks, and disclaimer; plus an accessible live result region.

- [ ] **Step 2: Verify failure**

Run: `node --test tests/useful-tools-stairs-ui.test.mjs`  
Expected: FAIL because the route and components do not exist.

- [ ] **Step 3: Implement the calculator screen**

Use the approved mobile-first structure. Keep the profile visible but not editable in V1. Show specific validation near the relevant input. Distinguish geometry results from profile checks and never replace a failed check with generic success copy.

- [ ] **Step 4: Implement the dynamic SVG measurement image**

Scale the step path to its own view box and current riser/tread count. Add gold arrowed dimension lines and real labels for total rise, available run, riser height, tread run, stringer length, and angle. Provide a generated accessible description containing the same values.

- [ ] **Step 5: Integrate device actions**

Save and restore canonical inputs plus the approved profile id/version. Print/share summaries must include the profile name, profile effective date, geometry, check results, and authority-having-jurisdiction notice.

- [ ] **Step 6: Verify and commit**

Run: `node --test tests/useful-tools-stairs.test.mjs tests/useful-tools-stairs-ui.test.mjs tests/useful-tools-local-saves.test.mjs && npm run build`  
Expected: tests PASS; build exits 0.

```bash
git add app/useful-tools/stairs components/useful-tools app/globals.css tests/useful-tools-stairs-ui.test.mjs
git commit -m "feat: add Ontario stair calculator"
```

### Task 8: Baseline protection, responsive QA, preview, and publication

**Files:**
- Modify: `scripts/verify-useful-tools-routes.mjs`
- Create: `scripts/verify-useful-tools-conformance.mjs`
- Create: `docs/testing/useful-tools-website-qa-2026-09-26.md`
- Modify only if defects are found: Useful Tools files created by Tasks 1–7

**Interfaces:**
- Consumes: all calculation fixtures, routes, components, and the Version 26 live baseline.
- Produces: a private review record and, only after Joel approves the rendered result, a published Sites version.

- [ ] **Step 1: Add one-command conformance verification**

Run every fixture through the exported core and assert exact canonical outputs, finite numbers, stable formatting boundaries, and matching profile ids/versions.

- [ ] **Step 2: Run the full automated gate**

Run: `node scripts/verify-useful-tools-routes.mjs && node scripts/verify-useful-tools-conformance.mjs && node --test tests/useful-tools-*.test.mjs && npm run build`  
Expected: all Useful Tools checks PASS and build exits 0. Record any unrelated pre-existing starter-test failures separately; do not weaken them to make this feature pass.

- [ ] **Step 3: Perform responsive and accessibility QA**

Check Useful Tools, Concrete, and Stairs at 320px, 375px, 390px, 768px, 1024px, and 1440px. Verify touch targets, 16px inputs, no horizontal scroll, diagrams, error text, keyboard order, live results, print, share fallback, local save failure, and unit switching.

- [ ] **Step 4: Compare frozen pages to Version 26**

Visually compare Home, Plan, Price, Contract, Build, Monitor, Learn, Supplier Connection, and Contractor Connection. The only approved Home difference is the hero button wording, icon, and destination. No other original-page difference may remain.

- [ ] **Step 5: Record the QA evidence and commit**

```bash
git add scripts/verify-useful-tools-routes.mjs scripts/verify-useful-tools-conformance.mjs docs/testing/useful-tools-website-qa-2026-09-26.md
git commit -m "test: certify useful tools website release"
```

- [ ] **Step 6: Produce a private visual review**

Provide Joel with phone and desktop screenshots for the landing page, Concrete Calculator, and Stair Calculator plus a private preview or controlled preview surface. Stop for explicit visual approval.

- [ ] **Step 7: Publish the approved website release**

After Joel's approval, follow the Sites hosting workflow, preserve the current audience, save a new version from the exact pushed commit, deploy it, and wait for terminal `succeeded` status.

- [ ] **Step 8: Verify the live site**

Open the live home, Useful Tools, Concrete, Stairs, Employment vs. Entrepreneurship, and all frozen pages on desktop and mobile. Re-run calculator smoke cases and confirm no broken assets, missing routes, unexpected wrapping, horizontal scrolling, or baseline drift.

## Contractor-platform follow-on plan

Do not translate this website plan into guessed platform files. Open `/Users/joelbrayman/Desktop/Brayman-Estimator`, read its current governance and turnover records, confirm its live/source parity and active feature gate, inspect the shared presentation system, menu architecture, frontend asset pipeline, service-worker/offline behaviour, and test conventions, then write a separate exact-path implementation plan.

That platform plan must consume the committed conformance fixtures and profile version from this release, reproduce all canonical outputs, add Useful Tools to the approved daily menu, bundle the tools locally, preserve tenant branding, and prove no estimate or project mutation. It requires its own governance approval, implementation commits, UAT, and release record.
