# Findings register: Internal Project Financial Summary + CaliSIGN Internal Approval release

Branch `feature/internal-financial-summary-2026-11-02`. Every finding from the independent reviews and the related-endpoint
sweep, with its closure evidence. A finding is closed only when its fix is committed, a test that fails without the fix
passes with it, and the independent reviewer has confirmed the closure (or, for the last two, the full regression covers it).

| ID | Source | Severity | Finding | Fixed in | Proving test | Status |
|---|---|---|---|---|---|---|
| B1 | Review 1 (f98ec33d) | Blocker | Generic `/signing-requests/<id>/*` routes let any office member read, void, resend or countersign internal approvals (IDOR) | 8e77af09 | `tests/test_internal_approval_review_fixes.py::test_b1_*` | Closed (review 2) |
| B2 | Review 1 | Blocker | Filed Financial Summaries readable by every office member in Documents | 8e77af09 | `test_b2_*` | Closed (review 2) |
| S1 | Review 1 | Should-fix | Wage-bearing copy briefly filed at the weaker sensitivity, could stay there | 8e77af09 | `test_s1_*` | Closed (review 2) |
| S2 | Review 1 | Should-fix | Recorded pricing method honoured only for the new method (rule 5) | 8e77af09 | `test_s2_*` | Closed (review 2) |
| M1 | Review 1 | Minor | `employee_detail` inconsistent on sent-to-client REVs | 8e77af09 | `test_m1_*` | Closed (review 2) |
| M2 | Review 1 | Minor | Migration docstring column count | 8e77af09 | `test_m2_*` | Closed (review 2) |
| SF1 | Review 2 (8e77af09) | Should-fix | Client could receive bytes different from those Ben approved (validity date) | 4203c7f9 | `tests/test_customer_estimate_rereview_fixes.py::test_sf1_*` | Closed (review 3) |
| SF2 | Review 2 | Should-fix | Signed customer-estimate copy that failed to file never retried | 4203c7f9 | `test_sf2_*` | Closed (review 3) |
| m1 | Review 2 | Minor | Concurrent freezes could share a REV number | 4203c7f9 | `test_m1_*` | Closed (review 3) |
| m2 | Review 2 | Minor | Proposal PDF re-rendered on every page view | 4203c7f9 | `test_m2_*` | Closed (review 3) |
| m3 | Review 2 | Minor | Needs Attention showed internal approvals to every office user | 4203c7f9 | `test_m3_*` | Closed (review 3) |
| m-i | Review 3 (4203c7f9) | Minor (defect) | A REV could be frozen with a validity date no link can carry, and read "authorized" | 1540b939 | `test_mi_*` | Closed (full regression at 1540b939) |
| m-iii | Review 3 | Minor (hardening) | Pairing not enforced by the database | 1540b939 | `test_miii_*`, migration proof | Closed (full regression at 1540b939) |
| F1 | Endpoint sweep (1540b939) | Minor (latent) | Guided countersign route did not require employee cost for a crew-rates REV | this commit | `tests/test_internal_approval_calisign.py::test_the_guided_countersign_route_refuses_a_crew_rates_rev_without_employee_cost` (fails without the fix) | Closed |
| R1 | Full regression (1540b939) | Defect | New approval panel printed a raw UTC clock time (`customer_issue_approval.html:17`) | this commit | `tests/test_office_local_time.py::test_no_template_prints_a_raw_utc_clock_time` | Closed |

## Decisions for Joel (not defects; behaviour documented, nothing blocked)
- **m-ii:** when the estimate is authorized, sending sets the link length so the client reads the approved validity date; the office message states the requested and applied lengths. Alternative: keep the typed length and show "not authorized".
- **Send block:** sending an estimate that Ben has not approved is shown, not blocked.
- **F2:** with a future project-performance (PM) permission, a one-person crew's loaded rate could be derived from labour cost ÷ hours. A rule is needed before that permission is built (minimum crew size, or a company-average rate).
- **P1 (pre-existing model):** any office member can change company pricing rules, margins and policies.
- **P2 (pre-existing):** estimate cost, margin and selling price (not wages, loaded rates or real profit) are visible to every office member on the estimate breakdown, contractor package and guided internal cost pages.

## Environment notes
- The 11 `tests/test_historical_ingestion.py` tests need the real customer workbooks that exist only on Joel's Mac; they skip in the cloud container and run (and must pass, with zero skips) in the Mac release gate.
