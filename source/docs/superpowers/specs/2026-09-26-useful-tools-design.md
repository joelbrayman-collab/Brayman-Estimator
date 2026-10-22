# CalibraytAI Useful Tools — Cross-Product Design

**Date:** 26 September 2026  
**Status:** Approved design; implementation planning not yet authorized  
**Products:** CalibraytAI public website and Brayman contractor platform

## 1. Purpose

Create a small, dependable collection of everyday construction tools that people will choose to use on site, in the truck, or at the office. The first release adds a comprehensive concrete calculator and an Ontario V1 stair calculator. The existing Employment vs. Entrepreneurship calculator also moves under the same public **Useful Tools** destination.

The website and contractor platform must return identical answers from the same inputs. The tools must be clean, fast, mobile-first, and understandable without training.

## 2. Approved product boundaries

### Public website

- Replace the home-hero button labelled **Employment vs. Entrepreneurship** with **Useful Tools**.
- The button opens a new Useful Tools landing page.
- The landing page contains three tools:
  1. Employment vs. Entrepreneurship
  2. Concrete Calculator
  3. Stair Calculator
- Preserve the seven original Version 15 pages and their shared visual presentation. The only existing-page change is the authorized home-hero button wording and destination.

### Contractor platform

- Add **Useful Tools** as a permanent daily-menu destination.
- Include the Concrete Calculator and Stair Calculator.
- Present them in the platform's established shared presentation system and tenant chrome.
- Do not add the Employment vs. Entrepreneurship tool to the contractor platform. It is a neutral public resource for people considering employment and entrepreneurship; contractors using the platform have already made that choice.
- V1 calculations are standalone. They do not silently change a project, quantity, estimate, cost, price, or order.
- Project and estimate attachment are separate future feature gates, not part of this release.

## 3. Shared architecture

Use one pure, versioned calculation core for formulas, rounding, measurement conversion, validation, waste calculations, and stair-profile evaluation. Both products bundle the core locally and wrap it in their own native presentation.

The platform must not embed the website in an iframe. Its bundled tools must continue calculating after the platform has been loaded and connectivity becomes weak or unavailable.

The shared core must expose deterministic inputs and outputs. A common conformance fixture set must run against both integrations and prove that equivalent inputs produce equivalent outputs.

Saved V1 calculations and unit preferences remain on the user's device. V1 introduces no server record, account synchronization, database migration, estimate mutation, or project mutation.

## 4. Shared interaction and visual design

- Follow the established CalibraytAI navy, white/light, and metallic-gold visual language.
- Follow the contractor platform's current presentation system inside the authenticated product.
- Design at phone width first, then adapt to tablet and desktop.
- Use large touch targets and input text of at least 16px on mobile.
- Avoid horizontal scrolling, dense tables, modal-dependent workflows, and hidden hover-only help.
- Show only fields relevant to the selected calculation type.
- Support imperial and metric units and remember the device preference.
- Preserve full calculation precision internally; apply explicit display and ordering rules at the output boundary.
- Use concise plain-language labels and a labelled visual confirming how each measurement is interpreted.
- Results update immediately after valid input changes.
- Validation must identify the specific missing, zero, negative, impossible, or conflicting measurement without discarding valid work.
- Provide Start New, Save on Device, Print, and Share actions where supported by the device.

## 5. Useful Tools landing page

The landing page uses the established page width, spacing, typography, card treatment, header, footer, and responsive behaviour. Each tool receives one restrained card with its name, a brief practical explanation, a familiar line icon, and one existing-style launch action.

The page must not resemble a dashboard or introduce a new design system. Concrete and Stair are presented as practical field tools. Employment vs. Entrepreneurship retains its neutral decision-support purpose.

## 6. Concrete Calculator V1

### Calculation types

- Slab or pad
- Rectangular footing
- Wall
- Round column
- Tube or post hole
- Curb
- Concrete stairs

Each type requests only the measurements required for its geometry. Every type supports a quantity multiplier. A calculation may contain several named sections, and the combined-pour result totals all sections.

### Inputs

- Calculation name, optional
- Shape-specific dimensions
- Quantity
- Imperial or metric unit system
- Waste allowance, editable and defaulted to 10%
- Bag size for bag-count calculations
- Truck capacity for truck-count guidance when the user elects to enter one

### Results

- Exact base volume
- Waste volume
- Adjusted volume
- Practical recommended order quantity
- Cubic yards and cubic metres
- Bag count for small pours when a bag size is selected
- Truck count when a truck capacity is entered
- Per-section breakdown and combined-pour total
- Labelled geometry image showing the dimensions used

### Calculation rules

- Calculate every shape from explicit geometric formulas in the shared core.
- Convert user inputs to one canonical internal unit before calculating.
- Apply the quantity multiplier before the waste allowance.
- Show the base and waste-adjusted quantities separately.
- Never reduce an order quantity through rounding.
- Make the ordering increment explicit in the result rather than hiding it in a formula.
- Treat bag yield and truck capacity as user- or supplier-confirmed inputs; do not imply universal supplier capacities.

## 7. Stair Calculator V1

### Standards scope

V1 includes one profile: **Ontario Residential — V1**. The profile must identify its source, applicable building-code edition, effective date, verification date, intended occupancy/use, and every encoded threshold.

No threshold may enter the production profile from memory, a generic calculator, a search-result snippet, or an unofficial summary. The implementation plan must identify the authoritative Ontario sources and a manual verification record before enabling the profile.

Future Canadian and U.S. profiles use the same versioned profile schema but are outside V1.

### Inputs

- Total rise
- Available run
- Stair width
- Tread thickness when it affects the cut or finished geometry
- Imperial or metric unit system
- Ontario Residential — V1 standards profile

### Results

- Recommended riser count
- Tread count
- Exact riser height
- Exact tread run
- Stair angle
- Stringer length
- Overall rise and run
- Plain-language profile result for each encoded limit
- Clear warnings for incomplete, impossible, or out-of-profile layouts

### Dynamic measurement image

Show a clean side-elevation stair profile that updates with the calculation. Navy represents the stair geometry. Gold dimension lines and arrowheads identify:

- Total rise
- Available run
- Individual riser height
- Individual tread run
- Stringer length
- Stair angle

The image must remain legible on a phone, use real labels rather than colour alone, and include an accessible text description. A compact summary below the image repeats the riser count, tread count, rise, and run.

### Standards language

The tool may state that a layout fits or does not fit the selected encoded profile. It must also state that permit documents and the authority having jurisdiction govern construction. It must never present a generic result as universal code compliance.

## 8. Offline behaviour

The contractor-platform tools must be bundled with the application rather than fetched from the public website. After the relevant platform assets have loaded once, loss of network connectivity must not prevent calculations, unit conversion, profile checks, or access to locally saved calculations.

If platform authentication expires while offline, the implementation must follow the platform's existing security rules. This feature does not create an authentication bypass.

The public website calculators run entirely in the browser but are not required to provide a formal offline installation experience in V1.

## 9. Accessibility and responsive behaviour

- Support keyboard and touch operation.
- Associate every input with a visible label and unit.
- Announce recalculated results without announcing every keystroke.
- Do not use colour as the sole pass, warning, or error signal.
- Maintain readable contrast across navy, light, and gold surfaces.
- Prevent clipping, collision, or horizontal scrolling at 320px and wider.
- Keep primary results visible without requiring a precision table.
- Provide accessible text alternatives for geometry images.

## 10. Error handling

- Preserve valid entries when another field fails validation.
- Distinguish missing values from impossible values.
- Reject negative dimensions and zero-sized geometry.
- Explain when available stair run cannot produce a valid layout under the selected profile.
- Prevent divide-by-zero, non-finite, overflow, and precision-display errors.
- Treat browser storage as optional: calculations must still work if saving is unavailable.
- Do not report a successful save, share, print, or offline action unless that action actually completes.

## 11. Verification and acceptance

### Shared core

- Independent formula tests for every supported concrete shape
- Boundary, zero, negative, fractional, large-value, and mixed-unit tests
- Imperial/metric round-trip conversion tests
- Waste, quantity, bag, truck, and rounding tests
- Stair geometry and trigonometry tests
- Ontario profile boundary tests at, immediately inside, and immediately outside every encoded threshold
- Common conformance fixtures proving website/platform parity

### Website

- Useful Tools route and all three tool routes
- Home-hero button wording and destination
- No unintended changes to the seven frozen baseline pages
- Desktop, tablet, and phone-width visual checks
- Keyboard, touch, print, and share checks
- No broken assets, clipping, collision, or horizontal scrolling

### Contractor platform

- Useful Tools daily-menu destination
- Platform-native presentation and tenant-brand separation
- Online and post-load offline calculation checks
- Device-local preference and saved-calculation checks
- Confirmation that no project or estimate record changes
- Phone, tablet, and desktop checks

## 12. Release sequence

This design becomes two coordinated implementation releases sharing one calculation contract:

1. **Website release:** shared core, Useful Tools landing page, Concrete Calculator, Ontario V1 Stair Calculator, and the authorized home-hero button change.
2. **Platform release:** consume the verified shared contract, add the platform Useful Tools section, provide local/offline assets and device-local saves, and prove parity with the website fixtures.

The website release may proceed from the existing Sites project. Platform implementation begins only from the authoritative Brayman contractor-platform repository and under its current governance, feature-gate, migration, and UAT rules.

## 13. Explicitly excluded from V1

- Canadian profiles outside Ontario
- U.S. jurisdiction profiles
- Automatic project or estimate updates
- Material ordering or purchase-order submission
- Supplier price or availability integration
- Cloud synchronization of saved calculations
- User-created standards profiles
- Structural engineering, load design, reinforcement design, or professional certification
- Changes to existing website pages beyond the approved home-hero Useful Tools access change
