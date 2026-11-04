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

## CaliSIGN internal approval — the sixth signable class (Joel, 3 Nov 2026)

Joel's ruling: not a special "Ben signs" feature, but a governed signable class `INTERNAL_APPROVAL` on the existing
CaliSIGN engine. The Internal Project Financial Summary is its first document type. The Training environment is not
touched (on the training site the existing synthetic authority / consent applies, as for change orders).

Workflow, as built (`app/services/internal_approval.py`):
1. **Freeze REVn.** Review This Estimate → Internal approval → *Freeze the working summary as the next REV*: an
   insert-only `InternalSummaryRevision` (figures JSON + SHA-256 of the figures and of the rendered PDF) and the PDF
   itself in signing custody (`SigningFrozenArtifact`, family `INTERNAL_APPROVAL`, `source_record_id` = the REV).
   Refused when nothing changed since the latest frozen REV. One REV series per estimate: the prices sent to the
   client are REVs of the same series (`origin` `SENT_TO_CLIENT`; `quoted_revisions` now reads it).
2. **Send for internal approval.** A `SigningRequest` (family `INTERNAL_APPROVAL`, `client_id` NULL, participant
   `APPROVER`, consent `CONSENT-BRAYMAN-INTERNAL-APPROVAL-V1-001`), approved for signature at creation, then the
   existing `issue_customer_invitation`: one-time token (hash at rest), the normal CaliSIGN invitation email.
3. **Review and sign** on the existing `/sign/<credential>` ceremony with no Calibrayt account: the exact frozen PDF
   (`/document`), consent, typed signature, Sign & Accept.
4. **Evidence**: the same events (REQUEST_CREATED, APPROVED_FOR_SIGNATURE, SENT, VIEWED, CONSENT_ACCEPTED, SIGNED,
   EXECUTED, each with the artifact SHA), signer IP / user agent / consent time, the executed PDF with its signing
   record page ("Internal approval", "Approver email / IP / user-agent", pre-sign SHA-256).
5. **Filed** automatically when executed (`signing._after_executed` → `internal_approval.file_signed_copy`): the
   executed copy in the project's Documents, type Internal financial summary, record SIGNING_REQUEST; PEOPLE when the
   REV carries crew loaded rates, else FINANCIAL. The documents sources skip this family so it is never registered
   again at a lower sensitivity; the review page re-files a copy whose filing failed.
6. **Immutable.** REV rows are insert-only (model guard; trigger in the migration) and the frozen and executed
   artifacts are content-addressed: a later change to the working summary is REV(n+1), separate and unsigned; REV n
   keeps its PDF, figures and signature.

Countersignature: per-document-type governance rule (`internal_approval.GOVERNANCE`): `approver` (the request is
complete when the approver signs) or `approver+countersigner` (the office countersigns on Review This Estimate with
the existing `countersign_and_execute`). The Financial Summary: approver only.

Security: the link resolves only its own request (`resolve_customer_access`, signer roles CUSTOMER or APPROVER) and its
pages read only that request's frozen / executed artifact; office pages, Documents, employee and financial screens
redirect to sign-in. Used, expired and guessed tokens refuse (409 / 410 / 404) and guessing is rate-limited per address
exactly as the other classes (`SIGNING_TOKEN_FAIL_LIMIT`). Freeze and send require `can_view_project_economics`; a REV
with crew loaded rates is frozen / sent only by someone who also has `can_view_employee_cost`, otherwise the
crew-total variant is frozen. The ceremony page shows the document title, the company and the project name only.

Why `client_id` NULL-able (for this family only): an internal approval has no client party; putting the project's
client on the request would record a party that is not one, and the evidence, mail and documents code would treat
them as the signer's counterpart. The column is NULL-able and a new check
`ck_signing_requests_client_required` (`client_id IS NOT NULL OR document_family = 'INTERNAL_APPROVAL'`) keeps the old
guarantee for every other class.

Existing CaliSIGN flows (contract, change order, subcontract, supplier order, supplier delivery change) are unchanged:
the only engine change is that the link signer is "the customer or the approver" (`LINK_SIGNER_ROLES`), plus class
labels in the mail, ceremony and executed record.

Consent: `CONSENT-BRAYMAN-INTERNAL-APPROVAL-V1-001`, recorded in `docs/governance/signing-consent-register.md` as in
use on Joel's authorization, not counsel-approved.

### Migration `u8b9c0d1e2f3` — cumulative schema (unreleased; one revision from `t7a8b9c0d1e2`)
- New tables: `organization_person_cost_profiles` (insert-only), `organization_labour_cost_settings` (insert-only),
  `estimate_crew_members`, `internal_summary_revisions` (insert-only).
- New nullable columns: `organization_pricing_policies.subcontract_markup_rate`, `.pricing_rules_json`;
  `estimate_pricing_snapshots.labour_rate`, `.subcontract_markup_rate`, `.pricing_rules_json`;
  `estimate_versions.pricing_method`, `.package_pricing_json`, `.pricing_rules_json`;
  `estimate_line_items.pricing_treatment`; `change_order_items.cost_kind`.
- Signing (tables rebuilt with `batch_alter_table`, rows copied unchanged): `ck_signing_frozen_artifacts_document_family`
  and `ck_signing_requests_document_family` add `INTERNAL_APPROVAL`; `ck_signing_participants_role` adds `APPROVER`;
  `signing_requests.client_id` NULL-able with the new `ck_signing_requests_client_required`.
- Downgrade refuses while any new table, new column, internal approval, APPROVER participant or NULL client holds a
  value; otherwise it restores every constraint and `client_id NOT NULL`.
- Release-gate migration arguments: `--new-tables estimate_crew_members,internal_summary_revisions,
  organization_labour_cost_settings,organization_person_cost_profiles --altered-tables change_order_items,
  estimate_line_items,estimate_pricing_snapshots,estimate_versions,organization_pricing_policies,signing_requests
  --altered-checks ck_signing_frozen_artifacts_document_family,ck_signing_participants_role`
  (rehearsed by `tests/test_cost_profiles_migration.py::test_the_release_rehearsal_proves_every_row_identical`).

### Tests and browser walk (3 Nov 2026)
- `tests/test_internal_approval_calisign.py` (5): the full lifecycle (REV1-REV9 earlier states, REV10 frozen, sent,
  captured email, link opened with no session, exact PDF bytes and SHA, consent, sign, executed, Documents, evidence;
  then REV11 separate and unsigned, REV10 unchanged and signed); the link reaches only its own document (office,
  Documents, employee, financial pages redirect; another project's link has other bytes; mixed credentials 404); used
  409 / expired 410 / guessing 429; permissions (economics to freeze/send, employee cost for crew rates, crew-total
  variant, no duplicate REV); the approver + countersigner rule.
- `tests/test_cost_profiles_migration.py` (+2): signing rows in every existing class (5 requests, 25 participants
  of every role, events, executed artifacts, access attempts) at `t7a8b9c0d1e2`, row SHA-256 identical after upgrade
  and after downgrade, constraints proven (other classes still need a client; unknown family refused; downgrade
  guarded); the release rehearsal with this release's arguments.
- Browser: `tools/release/evidence_internal_approval.mjs` (8 checks, laptop 1280×800 and phone 390×844), server
  `tests/internal_approval_page_server.py`; added to `release_gate.sh`. Gate count 324 → **332**
  (`--browser-expected 332`).

### Affected-file sweep (3 Nov 2026, Python 3.9.6 venv, Family 05 env, one file at a time)
197 files (every file of the earlier sweeps, every CaliSIGN / signing / documents / attention / proposal-acceptance test,
the new internal-approval and migration tests, the release-tool tests): **2,618 passed, 0 failed, 0 skipped** after one
fix. The one failure was `tests/test_approved_master_governance.py::test_every_office_pdf_renderer_is_classified...`:
the new `internal_financial_summary.py` renderer (from the 2 Nov commit; that file was not in the earlier sweeps) had to
be classified. It is added to the test's `NOT_GOVERNED` list (Joel: not an Approved Master) — an existing test
expectation changed deliberately. All existing CaliSIGN tests pass unchanged.

## Customer estimate approval for customer issue, and the f98ec33d review fixes (Joel, 3 Nov 2026)

### Which PDF is frozen
The customer-facing document is the proposal's **CONSTRUCTION ESTIMATE** (`app/services/proposal_pdf.generate_proposal_pdf`):
the renderer the client's proposal link serves (`/proposal/<credential>/pdf`) and the office downloads. The Contractor
Estimate Package (`contractor_estimate_package.py`) is not it: it is stamped "INTERNAL — CONTRACTOR COPY … Not for the
customer". The frozen bytes are `internal_approval.customer_estimate_pdf(proposal)`: `generate_proposal_pdf` at the
proposal's own validity date, without the office-copy stamp or appended drawings (exactly what the client link renders),
with a new opt-in `invariant=True` (no creation time / random document id), so the same content always renders the
same bytes and any change renders other bytes. Every other caller still gets the file it always did.
Known difference, reported to Joel: the client's link copy shows "Valid until" as the earlier of the proposal's date
and the link's expiry, which is only known at send; the client link still renders live (option: serve the approved
frozen bytes to the client when the proposal is authorized).

### Workflow (same INTERNAL_APPROVAL architecture; no separate estimate-signing mechanism)
`GOVERNANCE["CUSTOMER_ESTIMATE"]` = approver only (`SIGNERS_APPROVER_ONLY`), 7-day link. On the proposal page
(Approval for customer issue): Freeze → an insert-only `internal_summary_revisions` row (`document_type =
CUSTOMER_ESTIMATE`, origin FROZEN, `proposal_id`, `estimate_version_id`, `pdf_sha256`) and its PDF in signing custody →
Send → `send_for_internal_approval` (APPROVER participant, no client, normal one-time token and CaliSIGN email) → Ben
signs signed out on `/sign/` → executed → filed in the project's Documents (the executed copy, and the exact frozen PDF
as its own document; type Estimate, STANDARD: normal estimate access) → **authorized for customer issue**.
`customer_issue_status(proposal)` is authorized only when an executed approval exists for a REV of *this* proposal with
*this* estimate version and exactly the bytes the proposal renders now; otherwise "Approved REVn; current estimate
differs, not authorized" (stale), "REVn awaiting the approver …", or not frozen. Approval never carries forward.
Shown on the proposal page (panel and at the Send to client form), the estimate and estimate-version pages, the
guided pricing page, and as a flash when the proposal is sent. **No hard block** on sending without it (Joel has not
made that rule; it is an option for him). Ben's approval never reads or writes proposal status, `ProposalAcceptance` or
client links, and customer acceptance is never read by the status.

### REV series decision
One series per estimate shared by both document types (`_next_number` = max over all types + 1). Reason: Joel names a
revision of the job's price ("REV10 estimate"), and the price sent to the client was already a REV of the summary's
series; two series would let "REV10" mean two different states of the same job. When the client is sent a proposal
whose customer estimate is authorized as REVn, the summary's sent-to-client record takes the same REVn (one revision,
two documents), so the unique key is (`estimate_id`, `document_type`, `revision_number`). An unauthorized send takes
the next number as before.

### Permission chosen
`financial_access.can_issue_customer_estimate` = `has_office_scheduling_authority`: an active office member, never
field-only. That is exactly what governs estimate sign-off and Send to client today (the office wall plus the
field-only refusal); nothing is broadened or narrowed. The customer estimate carries no wage or internal-economics
figures. The Financial Summary keeps `can_view_project_economics` (+ `can_view_employee_cost` for a wage REV).

### Review findings (f98ec33d), each with its regression test (fails on f98ec33d, passes now)
- B1: `signing_office_bp.before_request` refuses (403) any `/signing-requests/<id>/…` route on an INTERNAL_APPROVAL
  unless `internal_approval.may_manage` (the document type's freeze/send rule), before any route code runs; other
  families untouched; `_redirect_for_request` sends internal approvals to their page. Tests:
  `test_internal_approval_review_fixes.py::test_b1_*` (DB snapshot of signing, mail and document tables unchanged
  after every refused route).
- B2: new sensitivities ECONOMICS and EMPLOYEE_COST (`ck_documents_sensitivity` widened in `u8b9c0d1e2f3`).
  `documents.access.office_scope` grants ECONOMICS with `can_view_project_economics` and EMPLOYEE_COST with that and
  `can_view_employee_cost`; FINANCIAL no longer reaches the summary. All list / search / attention / preview /
  download paths filter through `scope_filter`. A type change never lowers them; a person link keeps them (scope
  then also requires people administrator). Tests: `test_b2_*`.
- S1: `ingest.file_document(sensitivity=…)` sets the final level before flush, indexing and the first commit (the
  CREATED event records it); the post-step `correct_field` calls are gone. Test: `test_s1_*`.
- S2: `version_pricing_method` honours any recorded method; re-pricing a version whose method differs from the
  company's uses `recorded_method_policy` (the policy it was priced with, else the newest approved/superseded policy of
  that method that existed when the version was created). Unrecorded versions unchanged. A policy chosen for the
  estimate itself (an estimate pricing override or its commercial context) still governs a recorded version, as
  before: ruling 5 is about company default changes (the sweep's one failure,
  `test_pricing_engine.py::test_change_order_override_requires_human_reason_and_preserves_method`, root-caused to
  this and fixed in `version_pricing_method`). Test: `test_s2_*` (4 methods) and that existing test.
- M1: one rule `internal_financial_summary.carries_wages` for the REV's `employee_detail` and for filing. Test: `test_m1_*`.
- M2: migration docstring now says ten new nullable columns (and four new tables). Test: `test_m2_*`.

### Migration `u8b9c0d1e2f3` — additions in this pass
`internal_summary_revisions.document_type` (NOT NULL; new table), unique (`estimate_id`, `document_type`,
`revision_number`), checks `ck_internal_summary_revisions_document_type` and
`ck_internal_summary_revisions_customer_estimate` (a customer estimate REV is FROZEN with no employee detail);
`documents` rebuilt for `ck_documents_sensitivity` (+ECONOMICS, EMPLOYEE_COST). Downgrade also refuses while a document
holds a new sensitivity. Release-gate arguments now: `--altered-checks ck_documents_sensitivity,
ck_signing_frozen_artifacts_document_family,ck_signing_participants_role` (new tables and altered tables unchanged).
Proofs: `test_documents_survive_the_sensitivity_widening_and_its_downgrade_byte_for_byte`, the signing proof, and the
rehearsal (`MIGRATION_REHEARSAL=ok`, three ALTERED_CHECK lines, every row identical).

### Browser
`tools/release/evidence_internal_approval.mjs` 8 → 12 checks (freeze and send on the proposal page at 1280×800; Ben
reviews the exact bytes signed out on a laptop and nothing else opens; signs on a 390 px phone; authorized on the
proposal, send form, estimate and pricing pages, filed in Documents). Gate count 332 → **336**.

### Affected-file sweep (3 Nov 2026, second pass, Python 3.9.6 venv, Family 05 env, one file at a time)
231 files: every file of the 197-file sweep plus the new customer-estimate and review-fix tests, every proposal,
estimate, estimate-output, pricing, signing / CaliSIGN, documents, attention, access and security test, and every test
that touches the changed surfaces. First run: 2,933 passed, 1 failed (the S2 explicit-override case above, fixed);
the pricing files and every test touching estimate overrides / commercial context / economics were then re-run green.
No skips.

## Re-review of 8e77af09 (3–4 Nov 2026): fixes, each with a test that fails on 8e77af09
Tests: `tests/test_customer_estimate_rereview_fixes.py` (8).
- SF1 (the customer receives exactly what Ben approved). The REV now freezes the validity date the client will read
  (`issue_validity_date`: a live link's `client_valid_until`, else the proposal's date, else today + the default 30-day
  link) and renders at it. When the estimate is authorized, Send to client sets the link's expiry so the client reads
  that date (`issue_link_expiry`: the requested expiry when it already gives the date, else the end of the approved
  date on the company calendar; the offer never outlives the link: `client_valid_until` is unchanged), the office is
  told, and the client link serves the approved frozen bytes (`approved_client_copy`, re-rendered and SHA-checked).
  When the approved date cannot be kept (past, more than 90 days away, or after the proposal's own date) nothing is
  blocked: the status is `validity_differs` — "Not authorized for customer issue: the validity date differs (the
  customer sees …; REVn was approved with …); freeze a new REV" — and the link renders as before. Tests:
  `test_sf1_the_client_receives_exactly_the_approved_bytes` (validity date after a 14-day link; no validity date),
  `test_sf1_when_the_approved_date_cannot_be_kept_…`.
- SF2: `file_missing_signed_copies` (idempotent) runs on the proposal page, the estimate pages and the pricing page
  for customer-estimate REVs as well as summary REVs. Test: `test_sf2_…` (filing fails once at signing; later views
  file the signed copy and the exact PDF exactly once, Estimate / STANDARD).
- m1: `internal_summary_revisions.paired_revision_id` (FK to the authorized customer estimate REV) and the partial unique
  index `uq_internal_summary_revisions_series` on (estimate_id, revision_number) WHERE paired_revision_id IS NULL;
  check `ck_internal_summary_revisions_pairing` (only a summary sent-to-client row may pair). Numbers are allocated
  in a savepoint with retry on IntegrityError (`_allocate`). Tests: `test_m1_two_documents_can_never_share_a_number_…`
  (DB refusal and a simulated race), `test_m1_the_intended_pairing_shares_the_authorized_number`.
- m2: `customer_estimate_sha` caches the hash per key of every renderer input (proposal row, sections, lines, brand,
  project reference line, validity date, renderer sources, ReportLab version); a key that cannot be built re-renders;
  the send and the client link always re-render (`fresh=True`). Test: `test_m2_…` (no re-render for identical inputs;
  a line or brand change re-renders and is not authorized).
- m3: Needs Attention lists an INTERNAL_APPROVAL only for a viewer who `may_manage` it. Test: `test_m3_…`.
- Schema (still `u8b9c0d1e2f3`, new table only): `paired_revision_id`, the partial unique index and the pairing check.
  Migration proofs re-run green; release-gate arguments unchanged.
- Browser: `evidence_internal_approval.mjs` 12 → 13 checks (sent with a 14-day link, the client's PDF is the approved
  bytes). Gate count 336 → **337**.
- Sweep (4 Nov 2026, Python 3.9.6, Family 05 env, one file at a time, three runners): 232 files, 2,940 passed, 2 failed:
  `test_concrete_calculator_access.py::test_contractor_page_calculate_matches_the_original_fixtures` and
  `test_stair_calculator_access.py::test_recovered_stair_engine_diagram_and_page_tests`. Root cause, reproduced: on this
  2-CPU container, three parallel pytest runners plus a browser walk delay the calculator packages' own office
  server past its fixed 20-second start limit ("office page did not start",
  `calculation-engines/*/tests/office-page-browser.mjs`); not a defect in this change. Both files pass when run
  without that extra load (11 passed), also with the two run side by side and with one browser walk alongside.
