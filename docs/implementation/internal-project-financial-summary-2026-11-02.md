# Internal Project Financial Summary, employee cost profiles and labour-at-rate pricing (2 Nov 2026)

Branch `feature/internal-financial-summary-2026-11-02` (from `8a83c4b3`, the viewport-density head; Production is
`ec80e6f1`). Not released. One migration: `u8b9c0d1e2f3` (from `t7a8b9c0d1e2`).

## Joel's decisions (2 Nov 2026), as built

1. **Employee cost profile, mandatory for every employee** (`app/services/labour_cost_profile.py`,
   `app/services/payroll_statutory.py`).
   - Inputs: hourly wage; paid hours a year (2,080); vacation weeks (2) and paid public holidays (9) → working hours
     (1,928); truck and fuel a month; tool allowance a year (taxable); company RRSP % of wages; health & dental
     premium a month (not taxable: no CPP, EI or WSIB); WSIB per $100 (company setting, default 3.55 = 2026 G3;
     per-employee override).
   - 2026 statutory constants in one module, versioned by year, with sources: CPP 5.95 % to YMPE $74,600 less $3,500;
     CPP2 4 % between $74,600 and YAMPE $85,000; EI employer 1.4 × 1.63 % to $68,900; Ontario EHT 0.
   - Pensionable / insurable earnings = wages + tool allowance. Annual cost = wages + CPP + CPP2 + EI + WSIB + RRSP +
     tools + 12 × (truck + fuel + premium). LLR = annual cost ÷ working hours. Half-up to the cent where calculated.
   - Verified cases reproduced exactly: Worker A ($36, truck $1,100, fuel $700, tools $1,000, RRSP 2 %) →
     $107,525.29, LLR $55.77; Worker B ($26) → $60,243.46, LLR $31.25 (CPP $3,009.51, EI $1,234.11, WSIB $1,919.84).
   - Model family extended, not replaced: `OrganizationPerson` (+ the existing append-only
     `OrganizationPersonWageEvent`, now written when a profile changes the wage) gains the append-only
     `OrganizationPersonCostProfile` (insert-only: model guard + triggers) and the append-only company
     `OrganizationLabourCostSetting` (WSIB). The newest row is current; the history is kept and shown.
   - UI: People & Access → **Employees & labour cost** (`/settings/people/employees`, owner / System Administrator
     only, the existing People wall). List with "Cost profile required"; add an employee with the profile; one
     employee's form with Calculate (breakdown per year / per paid hour / per working hour, the approved sheet's line
     labels) and Save; history; company WSIB form. People & Access shows the count needing a profile.
   - "Mandatory": an employee without a complete profile (none, or the wage changed outside the profile, e.g. the CLI)
     cannot be put on an estimate crew (`estimate_crew.set_crew` refuses). Sign-in and time entry are untouched;
     crews/time entries still link users; no user link on people was needed (the estimate crew links people).
2. **Pricing: labour at $80/h with no margin; materials at cost + 15 % true gross margin.** Explicit, versioned
   company method `LABOUR_AT_RATE_MATERIAL_MARGIN` (`OrganizationPricingPolicy.method`; policies are versioned by
   supersede). Labour (LAB- lines) at the project labour rate = sell; materials = cost / (1 − margin); equipment,
   delivery, disposal, allowances and other direct costs at cost; subcontracts × (1 + subcontract markup), a visible
   company setting (How we price), default 0 %. Each bucket is rounded half-up once; line sell prices are spread per
   bucket by extended cost, last line takes the remainder.
   - Recorded on each version: `EstimateVersion.pricing_method`, captured at creation (a revision keeps its
     version's). A version under any other method, or with none recorded (every estimate before this release), is
     priced exactly as before (whole-estimate true gross margin) even after the company switches; approved / locked
     versions are never re-priced (existing `ensure_version_editable` and snapshot guards). Snapshot freezes
     `labour_rate` and `subcontract_markup_rate`.
   - Labour rate and margin stay adjustable per project (existing Project pricing); the company default margin form
     now also supersedes a labour-at-rate policy.
   - Seed/test data only: the synthetic Brayman org is set to $80 / 15 % in tests. **No data migration**: Joel sets
     Production through How we price (new pricing draft → method "Labour at rate (no margin), margin on materials",
     material margin 0.15 → approve → make default; labour rate $80 under Labour rates).
   - Change orders under this method: CO items carry no kind, so a CO is priced with the snapshot's margin on its whole
     subtotal (as before). Open item.
3. **Internal Project Financial Summary** (`app/services/internal_financial_summary.py`): faithful port of
   `ipfs.py` (landscape letter, flat ReportLab PDF, two-pass Page X of N, the two logos, "(continued)" pages,
   subcontract page only when there are subcontracts). For every estimate, from the working figures; once approved,
   from the figures frozen at approval.
   - Data mapping: packages = guided work packages in Brayman's price (`work_packages.packages_in` /
     `package_participates`), plus each section no package owns (manual estimates); revenue per package = the
     customer selling price of its lines (frozen snapshot via `estimate_economics.economics` when applied, else the
     same calculation on the working lines); line kind via `guided_estimating._line_kind` → `pricing_bucket`;
     materials: description, takeoff = line quantity + unit, order = the project's newest supplier request purchasing
     quantity (`approved_cost_estimate._takeoff_quantities`) when the cost item's canonical material is on it, else
     quantity incl. waste; unit price; supplier (`ContractorCostApproval.supplier_id` → supplier, else
     `CostItem.supplier`); labour: activity, item quantity / unit, rate = quantity per person-hour (base hours), hours
     incl. winter (line quantity), value at the rate (line cost), crew cost = hours × blended LLR; subcontracts: trade
     = package, company / scope / reference from the selected `SubcontractQuoteEvidence`, cost = line cost.
   - Real labour cost = hours × the estimate crew's LLRs (`EstimateCrewMember`, equal shares by default, last crew
     member takes the rounding remainder). No crew: tiles, P&L and labour page say "Crew not assigned — real labour
     cost not available" and show labour at the charge rate only; no cost or profit is shown.
   - "How we price it internally" shows the labour-at-rate build-up; for an earlier-method estimate it shows the whole
     margin on direct cost.
   - Approval (Gate 1, `record_approval`): the summary's figures and crew LLRs are stored in
     `estimate_approvals.summary_json["internal_financial_summary"]` (the Gate 1 fingerprint is unchanged: it is still
     the approval summary, which `verify()` recomputes). After the sign-off commits, the PDF is filed in the project's
     Documents as the new type `INTERNAL_FINANCIAL_SUMMARY` (FINANCIAL; raised to PEOPLE when it carries crew LLRs),
     record `ESTIMATE_VERSION`; idempotent; a filing failure is logged and never undoes an approval. The approval
     block then shows the approver and time.
   - Who sees it: the PDF, crew form and live P&L are for people administrators (owner / System Administrator) — the
     same people who may read wages, since LLRs are wage figures. Office staff get 403; field crew never pass the
     Field wall; suppliers and customers never pass the office wall; nothing is added to proposals.
   - Not one of the governed DOCX Approved Masters (families 01–08 untouched).
4. **Migration `u8b9c0d1e2f3`**: three new tables (`organization_person_cost_profiles`,
   `organization_labour_cost_settings` with insert-only triggers, `estimate_crew_members`) and six nullable columns
   (`organization_pricing_policies.subcontract_markup_rate`, `estimate_pricing_snapshots.labour_rate` /
   `.subcontract_markup_rate`, `estimate_versions.pricing_method` / `.package_pricing_json`). No row written. The
   downgrade refuses while anything new is held. Test: `tests/test_cost_profiles_migration.py`.

## Added scope (Joel, 16:06): change it on the fly

- Per package on a working version: **By others** = the existing `work_packages.exclude_work` (lines kept, out of
  revenue and cost); **client budget / fixed price** stored per version in `package_pricing_json` (audited, carried
  into revisions); **pass-through at cost** = a line of the new manual kind `passthrough` (`GE-PASSTHROUGH`), always
  at cost, never part of a budget (`app/services/package_scenario.py`).
- Engine `scenario_price`: a budgeted package sells for its budget, spread over its lines by extended cost (last line
  takes the remainder); its costs are unchanged; other packages keep the method. Budgets require the labour-at-rate
  method.
- Review This Estimate: **Live P&L** (people administrators): per package internal price, budget input, By others
  toggle, revenue, real cost (crew LLRs), profit and margin, and the whole job, recalculated in the page as the toggle,
  a budget or the crew changes; Save re-prices the working version; a pass-through form.
- Summary PDF: budgeted revenue labelled with the budget's label (default "client budget"), pass-through revenue lines
  "(billed at cost)", and an **Excluded / by others** block with the price we had quoted (the package's sell price on
  the newest earlier priced version, else its price by the method).
- Acceptance (synthetic Paulusse REV9 mirror, `tests/test_package_scenario.py`): revenue $40,693.52, cost $28,192.12,
  profit $12,501.40; materials $14,944.60, labour $10,897.52, equipment $2,350.00; aluminum internal price
  $11,703.06 vs $10,300.00 budget, $1,950.93 profit. The siding's "as quoted" $30,393.52 is entered as that package's
  client budget labelled "Nov 1 quote" (the reference quote was not built by the method from these lines).

## Lifecycle decision (Joel, 16:10) — how it is implemented

Working → Sent → Agreed, with the smallest change that keeps the guarantees:

- **Working**: the current Draft version; every scenario control, the crew and the live P&L are available.
- **Sent**: Gate 1 still locks a version when Ben approves it (that is what is sent). Every time a proposal goes to the
  client, the version's frozen summary is filed in Documents as **REVn sent to client** (REV1, REV2, … in order first
  sent; `quoted_revisions`, record `PROPOSAL`). To answer a counter-offer Ben starts the next revision (existing
  `start_revision` / `create_successor_version`), which carries the scope, budgets and settings; the sent version is
  never changed.
- **Agreed**: Ben's sign-off (Gate 1) plus the client's acceptance (existing); after acceptance, changes go through
  change orders (existing guard).
- Why not leave the sent version editable: the client link, the proposal's content hash and acceptance all assume the
  quoted version is immutable; making it editable would let what the client accepts differ from what was quoted. Keeping
  lock-on-approval and putting live work on the successor gives "the working version stays live" with no parallel
  system. **No existing test that asserts lock-on-approval was changed.**

## Existing test expectations changed (deliberately)

- `tests/test_person_identity_fg038.py::test_no_people_ui_routes`: the FG-038 slice guard said no route creates a
  Person; Joel's decision needs Ben to enter every employee, so `create_person` is now allowed only in
  `app/routes/people_access.py` (asserted to sit behind the owner / System Administrator wall); no route reads the wage
  through `get_person_hourly_wage`.
- `tests/test_security_route_sweep.py`: the frozen People & Access endpoint list gains the four Employees endpoints, and
  two Employees URLs are added to the signed-out-redirect check.
- Graph-head assertions in 44 test files moved from `t7a8b9c0d1e2` to `u8b9c0d1e2f3` (the same mechanical move every
  migration release makes); `tests/test_documents_migration.py::test_graph_head_is_the_documents_revision` now
  asserts the new head follows the documents revision.
- No pricing figure expectation changed.

## Tests (2 Nov 2026, Python 3.9.6 venv, one file at a time, Family 05 master env set)

- New, written first: `test_labour_cost_profile.py` (9), `test_pricing_labour_material_margin.py` (11),
  `test_internal_financial_summary.py` (11), `test_package_scenario.py` (4), `test_cost_profiles_migration.py` (3).
- Affected sweep: 150 files (everything touching pricing, economics, approval, proposals, guided tasks / estimating,
  people, documents, labour, migrations, plus the 44 head-assertion files): 2,115 passed, 4 failed. The 4: two FG-038
  guards and the security route sweep (above: one fixed by wording a template comment, two changed deliberately), and
  `test_guided_estimating_browser.py`, which failed because this new worktree had no `node_modules` and the sweep's
  long `TMPDIR` made Chrome's socket path too long; with the dependency present and the normal temp dir it passes.
  Reruns: all 4 pass; `test_python39_compat.py` 3 passed.
- Rendered PDFs (pdftoppm) checked against the reference layout: the app's port of `sample.json` reproduces the
  reference totals ($56,193.52 / $41,522.92 / $14,670.60); the Paulusse REV9 mirror renders $40,693.52 / $28,192.12 /
  $12,501.40 with the Excluded / by others block.

## Joel's rulings on the open questions (2 Nov 2026), as built

1. **Visibility.** Two separate checks in `app/services/financial_access.py`: `can_view_employee_cost` (compensation
   components and loaded labour rates; Owner / System Administrator) and `can_view_project_economics` (project cost,
   price and profit; today also Owner / System Administrator). Employees pages and the crew form check employee cost;
   the summary PDF, live P&L, scenario, pass-through and allowance routes check project economics. A viewer with
   project economics but not employee cost (the future PM "project performance" grant, not built) gets the summary
   without crew names or loaded rates ("Labour (crew)" totals only) and the live P&L without the crew form. No access
   was broadened.
2. **Equipment / delivery / other / allowances.** Configurable company rules (`OrganizationPricingPolicy.
   pricing_rules_json`, edited on How we price → Company pricing rules): equipment, delivery and other direct cost
   markups (Brayman 0 %). Allowances: **full configurability chosen** — `estimate_line_items.pricing_treatment` is
   `PASS_THROUGH` (at cost, no markup) or `PRICED` (the material margin), set per allowance on Review This Estimate
   (`package_scenario.set_allowance_treatment`, audited). Existing allowances (NULL) default conservatively to
   pass-through, which is what this branch already did.
3. **Subcontractors.** A company value (`subcontract_markup_rate` on the policy, also in the rules form), Brayman 0 %;
   `DEFAULT_RULES` are only the starting values. Test: a configured 10 % gives $5,200 → $5,720 and is frozen on the
   snapshot.
4. **Change orders.** The blanket margin on the whole change-order subtotal is removed for labour-at-rate estimates.
   `change_order_items.cost_kind` (labour, material, subcontract, equipment, delivery, other, passthrough; blank =
   unclassified) and `pricing_engine.change_order_line_prices` price each item with the same
   `labour_material_margin_price` engine and the rules frozen on the estimate's pricing snapshot: labour = hours ×
   the frozen labour selling rate (no margin), materials at the material margin, subcontract / equipment / delivery /
   other at their rules, pass-throughs at cost, unclassified items at the company's generic change-order rule (blank:
   the material margin). Lines copied from the estimate keep their cost type. Estimates under the earlier method keep
   pricing change orders as before (that is the same engine for that method). The accepted version is never touched;
   the change order holds only the incremental items.
5. **Legacy.** Each version now also captures the company rules at creation (`estimate_versions.pricing_rules_json`)
   besides its labour rate, margin and method; the snapshot freezes them (`estimate_pricing_snapshots.
   pricing_rules_json`). Test: changing the company labour rate, margin and rules leaves a priced estimate and an
   unpriced draft at the same figures (the draft also when it is priced afterwards); only new estimates change. No
   reprice control.
6. **Fixed price.** Per package only (as built).
7. **Cost vs selling rate.** Loaded cost lives only in the cost profiles; the selling rate only on the estimate
   (version labour rate / snapshot). Tests: a profile change moves labour cost and profit but not the selling rate or
   price; a selling-rate change (project or company) leaves every cost-profile row unchanged; the approval's frozen
   summary keeps `settings.labour_rate` (selling), each crew member's `loaded_rate` and the pricing rules, so later
   profile, rate or rule changes do not change the approved report.

Schema added for the rulings (folded into `u8b9c0d1e2f3`, all nullable, downgrade guard extended):
`organization_pricing_policies.pricing_rules_json`, `estimate_versions.pricing_rules_json`,
`estimate_pricing_snapshots.pricing_rules_json`, `estimate_line_items.pricing_treatment`,
`change_order_items.cost_kind`.

Tests added: `tests/test_pricing_rulings_20261102.py` (11). Changed (own new tests from this branch):
`test_pricing_labour_material_margin.py` bucket names (`at_cost` → `equipment` / `delivery`),
`test_cost_profiles_migration.py` (the five new columns).

Sweep after the rulings (commit 53b7a72b; Python 3.9.6 venv, one file at a time, Family 05 master env set): all 167
affected files (the earlier 150 plus every change-order / project-controls test file and
`test_pricing_rulings_20261102.py`): **2,312 passed, 0 failed, 0 skipped**. The run was interrupted once by a container
restart after 70 files and resumed file by file from its log.

## Open items (superseded by the rulings above where marked)

- Ruled (2, 3, 4, 6, 1, 5): see above.
- No browser walk was added to the release gate for these screens (gate count stays 324).
