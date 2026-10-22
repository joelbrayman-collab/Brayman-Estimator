# Employment vs. Entrepreneurship Integration Design

## Objective

Integrate the approved `CalibraytAI_Business_Owner_App.html` calculator into the authoritative CalibraytAI ChatGPT Sites project and publish a clean direct link suitable for Josh and future users.

## Authority and Baseline

- Authoritative Site project: `appgprj_6a9095543b74819186183f9a522890e5`
- Current approved published baseline: Version 24
- Baseline source commit: `5d96f6f9049a003c23e73796f2e08e0d67998b7e`
- Live URL: `https://calibai.joel-brayman.chatgpt.site/`
- Calculator source: Library file `CalibraytAI_Business_Owner_App.html`, current version 2
- The obsolete Mac folder `/Users/joelbrayman/Documents/CalibAi/Website` is not an authorized website source and must not be merged or deployed.

## Product Intent

The calculator is a neutral decision tool for comparing employment with entrepreneurship. It must remain useful beyond Josh while retaining the researched trade defaults, editable assumptions, workload comparison, operating costs, break-even result, and objective summary already approved.

## Integration Approach

Preserve the self-contained calculator as the functional source rather than rebuilding its calculation engine in React. Install it as a clean, first-party Site route at:

`/employment-vs-entrepreneurship/`

The route will load directly into the working calculator. It will not place a marketing hero, intermediate landing page, or iframe in front of the tool.

Add one existing-style entry point on the Contractor Connection page only. Do not add the calculator to the shared header navigation and do not change the seven original Version 15 pages.

### Authorized Home Hero Amendment — 26 Sep 2026

Joel confirmed the previously agreed calculator entry point belongs in the top-right of the Home splash-page hero image. Add one compact calculator icon/button in that position linking to `/employment-vs-entrepreneurship/`. This is the sole authorized Home-page exception; the hero copy, artwork, existing Supplier and Contractor buttons, dimensions, and all other original-page content remain unchanged.

## Allowed Changes

- Add the calculator route and its required static assets.
- Add a concise return path from the calculator to the CalibraytAI website if the current calculator lacks one.
- Add one CTA on Contractor Connection using the existing button design language.
- Add route metadata needed for the calculator title and description.
- Add focused tests or verification scripts needed to prove the calculator and route work.

## Frozen Scope

The following pages must remain visually and textually unchanged:

- Home
- Plan
- Price
- Contract
- Build
- Monitor
- Learn

The approved logo assets, Supplier Connection page, shared header, shared footer, responsive breakpoints, typography, colours, spacing, and existing navigation remain unchanged except for no change at all to the shared navigation.

## Calculator Preservation

Preserve:

- Employment, Business, Market, Costs, and Results steps
- Masonry, Electrical, Plumbing, and Custom profiles
- Existing researched defaults and contextual labels
- Truck, fuel, insurance, maintenance, tools, payroll, administration, working-weeks, utilization, and productivity inputs
- Live calculation updates
- Employment economic value
- Entrepreneurship income
- Financial difference
- Effective hourly comparisons
- Break-even selling rate
- The neutral “what has to be true” and personal-decision framing

No recommendation will be added telling a user to remain employed or start a business.

### Employment stabilization ruling — 30 Sep 2026

- Quote Win Rate is not part of the governed financial model and is not displayed as an active assumption.
- Seasonality is represented by the user's actual working-weeks assumption and, where applicable, the editable Winter Protection / Heat operating cost. No separate season selector changes the calculation.
- Supported operating models are Solo Business Owner and Owner + Labourer / Helper. An unsupported crew/company model is not offered.
- Helper wage is an editable owner estimate. Its regional benchmark remains context only.
- Every displayed calculation-active input is protected by a deterministic participation regression test.

## Navigation and User Flow

1. A visitor may open the calculator directly using the clean URL.
2. A visitor may reach it from the Contractor Connection page through one existing-style CTA.
3. The calculator opens immediately at the Employment step with the approved defaults populated.
4. The visitor can move forward, backward, or revisit any step without losing current in-page values.
5. The visitor can return to the CalibraytAI website through a clearly labelled but visually restrained link.

## Responsive Behaviour

The tool must remain fully usable on desktop, tablet, and phone widths. There must be no clipped fields, distorted logo, overlapping text, unusable navigation, horizontal scrolling, or nested-scroll iframe behaviour.

## Verification

Before publication:

- Confirm the five calculator steps work in both directions.
- Confirm all trade and operating-model controls update the displayed assumptions.
- Verify representative calculations independently from the displayed results.
- Test empty, zero, decimal, high, and boundary inputs for stable output.
- Confirm the calculator route and Contractor Connection CTA resolve correctly.
- Confirm desktop, tablet, and mobile rendering.
- Build the Site successfully.
- Confirm the seven Version 15 pages have no source changes.
- Confirm Supplier Connection has no unintended source or presentation change.

After publication:

- Confirm the deployment succeeds.
- Confirm the live direct calculator URL.
- Confirm the live Contractor Connection entry point.
- Return the published version number, deployment result, and Josh-ready link.

## Publication

Publish through the existing ChatGPT Sites workflow, preserve the Site’s current access mode, and do not create or deploy a separate website.
