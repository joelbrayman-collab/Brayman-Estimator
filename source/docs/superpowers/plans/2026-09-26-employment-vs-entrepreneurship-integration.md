# Employment vs. Entrepreneurship Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the approved Employment vs. Entrepreneurship calculator as a clean CalibraytAI Site route, reachable from Contractor Connection, without changing the seven frozen Version 15 pages.

**Architecture:** Preserve the approved self-contained calculator as a first-party static route under `public/employment-vs-entrepreneurship/index.html`. Add one existing-style CTA to Contractor Connection and leave the shared header, shared footer, original pages, and Supplier Connection unchanged. Validate the calculator in a browser at desktop, tablet, and phone widths before publishing through the existing Sites workflow.

**Tech Stack:** Vinext/Next-style App Router site, static HTML/CSS/JavaScript calculator, existing CalibraytAI CSS, ChatGPT Sites hosting.

**Spec:** `docs/superpowers/specs/2026-09-26-employment-vs-entrepreneurship-integration-design.md`

## Global Constraints

- Site project remains `appgprj_6a9095543b74819186183f9a522890e5`.
- Version 24 at commit `5d96f6f9049a003c23e73796f2e08e0d67998b7e` is the visual baseline.
- Do not change Home, Plan, Price, Contract, Build, Monitor, or Learn.
- Do not change the shared header, shared footer, shared navigation, Supplier Connection, logo assets, or existing responsive breakpoints.
- Authorized amendment: add one responsive calculator icon/button at the top-right of the Home hero image without moving or rewriting existing hero content.
- Preserve the approved calculator’s neutral wording, trade profiles, defaults, inputs, calculations, navigation, and result framing.
- Preserve the Site’s current access mode.
- The obsolete Mac HTML website is not a source and must not be merged.

## Review Focus

- Zero and blank numeric inputs must not produce `NaN`, `Infinity`, or broken result text.
- Decimal and high-but-valid inputs must calculate and format consistently.
- Switching trade or business model must update only the intended defaults and dependent calculations.
- Back/forward step navigation must preserve the user’s current values during the session.
- Phone-width navigation and fields must remain usable without horizontal scrolling.

---

### Task 1: Install the approved calculator route

**Files:**
- Create: `public/employment-vs-entrepreneurship/index.html`
- Source: `/workspace/scratch/e2bdacfbe36a/calculator-source/CalibraytAI_Business_Owner_App.html`
- Test: `scripts/verify-calculator-route.mjs`

**Interfaces:**
- Consumes: The approved self-contained calculator HTML, version 2.
- Produces: A first-party static route at `/employment-vs-entrepreneurship/`.

- [ ] **Step 1: Write the failing route verification**

Create `scripts/verify-calculator-route.mjs` to assert that the installed file exists and contains the five step IDs (`today`, `business`, `market`, `costs`, `results`), the four trade profiles, the `calc()` function, and neutral result language.

- [ ] **Step 2: Run the verification and confirm it fails**

Run: `node scripts/verify-calculator-route.mjs`

Expected: failure because the route file does not exist.

- [ ] **Step 3: Install the approved HTML without altering its calculation logic**

Copy the approved source bytes into `public/employment-vs-entrepreneurship/index.html` using `apply_patch`. Add only a restrained return link if the source has no way back to the CalibraytAI website.

- [ ] **Step 4: Run the verification and confirm it passes**

Run: `node scripts/verify-calculator-route.mjs`

Expected: pass with all required calculator elements present.

- [ ] **Step 5: Commit**

Commit message: `feat: add employment entrepreneurship calculator`

### Task 2: Add the Contractor Connection entry point

**Files:**
- Modify: `app/contractor-connection/page.tsx`
- Test: `scripts/verify-calculator-route.mjs`

**Interfaces:**
- Consumes: `/employment-vs-entrepreneurship/` from Task 1 and the existing `.btn` component styles.
- Produces: One visible Contractor Connection CTA linking to the calculator.

- [ ] **Step 1: Extend the failing verification**

Assert that `app/contractor-connection/page.tsx` contains exactly one link to `/employment-vs-entrepreneurship/` and that none of `app/page.tsx`, the six lifecycle pages, `app/site.tsx`, or `app/supplier-integration/page.tsx` contains that link.

- [ ] **Step 2: Run the verification and confirm it fails**

Run: `node scripts/verify-calculator-route.mjs`

Expected: failure because Contractor Connection does not yet link to the calculator.

- [ ] **Step 3: Add one existing-style CTA**

Add a concise CTA using the existing `btn primary` styling on Contractor Connection. Do not add new global CSS or change the shared navigation.

- [ ] **Step 4: Run the verification and confirm it passes**

Run: `node scripts/verify-calculator-route.mjs`

Expected: pass, with exactly one authorized site entry point.

- [ ] **Step 5: Commit**

Commit message: `feat: link contractor connection to calculator`

### Task 3: Functional and responsive QA

**Files:**
- Modify only if a calculator defect is demonstrated: `public/employment-vs-entrepreneurship/index.html`
- QA evidence: local browser inspection and command output; do not add screenshots to the repository.

**Interfaces:**
- Consumes: The calculator route and Contractor Connection CTA.
- Produces: Verified desktop, tablet, and mobile behaviour with independently checked representative calculations.

- [ ] **Step 1: Configure and build the existing Site**

Run the current Sites execution-profile configuration if required, then run the project build. Expected: successful build with the calculator static route included.

- [ ] **Step 2: Start the managed preview**

Open the calculator and Contractor Connection through the managed preview only.

- [ ] **Step 3: Verify navigation and controls**

Exercise all five steps in both directions, all four trade choices, Solo/Helper/Crew choices, seasonality controls, and representative editable cost inputs. Confirm entered values persist while revisiting steps.

- [ ] **Step 4: Verify calculations**

Check the approved default scenario against an independent calculation. Test zero, blank, decimal, and high inputs. Confirm no displayed `NaN`, `Infinity`, or negative-breakage state.

- [ ] **Step 5: Verify responsive behaviour**

Inspect desktop, tablet, and phone widths. Confirm no clipping, overlap, distorted logo, unusable control, horizontal scrolling, or nested scrolling.

- [ ] **Step 6: Verify frozen-source scope**

Diff against Version 24. Confirm no changes to `app/page.tsx`, `app/plan/page.tsx`, `app/price/page.tsx`, `app/contract/page.tsx`, `app/build/page.tsx`, `app/monitor/page.tsx`, `app/learn/page.tsx`, `app/site.tsx`, `app/supplier-integration/page.tsx`, or approved image assets.

- [ ] **Step 7: Commit any demonstrated calculator-only corrections**

If QA exposes a calculator defect, make the smallest correction, rerun the complete verification, and commit it separately. Otherwise, do not create a QA-only commit.

### Task 4: Publish and verify the live link

**Files:**
- Package artifact outside the repository.

**Interfaces:**
- Consumes: Fully verified committed source.
- Produces: A published Sites version and Josh-ready live calculator URL.

- [ ] **Step 1: Run final verification**

Run the route verification, project build, `git diff` scope check, and `git status`. Expected: tests and build pass; only planned commits exist; worktree is clean.

- [ ] **Step 2: Push and package the exact source**

Use the existing Sites workflow with a fresh source credential, the opened Site source record, the build command, and a new archive path.

- [ ] **Step 3: Save the archive-backed version**

Save the pushed commit and its matching archive to the existing Site project. Preserve the current access mode.

- [ ] **Step 4: Deploy the saved version**

Deploy the exact saved version and poll its deployment status to `succeeded`.

- [ ] **Step 5: Return the result**

Return the new version number, deployment status, unchanged-page confirmation, and direct Josh-ready URL:

`https://calibai.joel-brayman.chatgpt.site/employment-vs-entrepreneurship/`
