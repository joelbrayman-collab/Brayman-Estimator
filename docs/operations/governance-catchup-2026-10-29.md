# Governance catch-up — Practice / Production / Training (29 Oct 2026)

| Attribute | Value |
|---|---|
| Status | **Governing record** of the 29 Oct 2026 catch-up (Joel's brief "GOVERNANCE CATCH-UP — PRACTICE / PRODUCTION / TRAINING"). |
| Rule enforced | Completed and accepted major work does not accumulate on branches; Git is the source of truth; accepted work is promoted to the live environments; the Training Centre is reconciled whenever the user journey changes. |
| Release label | `catchup1` (branch `release/governance-catchup-2026-10-29`) |

## 1. Baseline (verified 29 Oct 2026, not assumed)

| Item | Value | Evidence |
|---|---|---|
| `origin/main` | `02dd09ed` (docs-only release record on top of `471eec43`) | `git fetch`; `git log origin/main` |
| Production (Render `Calibryatai`, `srv-dar95mh42hec73df4rug`) | `471eec4345d8a87defff564bd112a19b77862669`, deploy `dep-dbhl0dafngtc73buj8q0`, live; auto-deploy off | Render deploy list |
| Production database revision | `a4d5e6f7a8b9` | CaliSIGN release record (post-release check RELEASED) |
| "Practice" | CalibraytAI has **no separate Practice service**. The practice environment is the Training & Acceptance Centre's own application and database (https://training.calibraytai.com, HostPapa, `calibrayt-training`, synthetic records only). The Render `calibraytai-training-preview` (`5f575c4`, free, data wiped on restart) is retired/"to be suspended" and is not an environment of record. | `source-of-truth.md` §5; turnover record "Training / Practice"; Render service list |
| Training Centre running code | **Not CaliSIGN, not Project Creation UX, not selected work.** Its public static files are byte-identical (git blob SHA) to the commits of 26 Oct 2026 up to `5c6f3d7` (v1rel13, Production before 27 Oct): `wizards.css` `8e689552…`, `v1-refinement.css` `29d4364f…`, `training.js` `fe7519c0…`, `calendar-months.js` `499e0086…`; `/static/js/calisign.js`, `/static/css/calisign.css` and the dark Brayman logo answer 404. The exact commit still needs the read-only WHM read (source-of-truth §5). | Signed-out fetch of the public static files from the built-in browser, 29 Oct 2026 15:2x EDT |
| Open PRs | #15 Compact Open a New Project (`e9e23999`) | GitHub REST |
| Branches ahead of `main` with unique patches | `feature/compact-new-project-workflow-2026-10-28` (PR #15); `feature/supplier-pricing-request-master-2026-10-28`; `security/closure-2026-10-18` and `calendar/release-2026-10-18` (one patch each: the 18 Oct local-storage release tools, already in `main` in later form — superseded). Every other branch ahead of `main` is a publication/deployment branch governed by `source-of-truth.md` or patch-equivalent to `main`. | `git cherry` against `origin/main` |

## 2. Turnover verification

The 28 Oct turnover closed "substantially correct — no current work stranded — release/operations verification
deferred". Re-checked against Git:

| Deferred item | 29 Oct status |
|---|---|
| Mac release gate on the exact `main` commit | **Done** by the CaliSIGN release (`calisign1`: 3,623 passed, 298 browser checks). |
| HostPapa Training running commit | **Still not read with WHM** — but now fingerprinted (§1): Training runs the 26 Oct code. It was not updated after the 27 Oct Project Creation release or the 29 Oct CaliSIGN release. **Gap: the Training Centre lagged Production by two releases.** Corrected by this catch-up (§7). |
| Preservation tags `preserve/2026-10-28/*` | **Still not created** (no tags on GitHub). Included in Joel's Mac command for this release. |

No accepted work was found missing from `main` other than the items in §3.

## 3. Major-work inventory

| Workstream | Git state (before) | Accepted? | Practice (Training site) | Production | Training impact | Class → action |
|---|---|---|---|---|---|---|
| CaliSIGN native e-signature + FG-041 supplier signing (PRs #13, #16) | `main` | Yes (released 29 Oct) | **Not present** | Live `471eec4` | Lessons said Place order / Confirm order / Send for Signature; no signature steps | A — promote to Training; lessons and screenshots reconciled |
| Selected-work estimating (Approach B, PR #8) | `main` | Yes (released with CaliSIGN) | **Not present** | Live | Module 13 taught the 14-stage Internal / Subcontracted / N/A scope; Tutor and Workflow Map too | A — promote to Training; module 13/14 lessons, Tutor, Workflow Map and 33 screenshots reconciled |
| Project Creation UX (7 tasks, structured address, migration `q4c7l2n8t3a6`) | `main` | Yes (live 27 Oct) | **Not present** | Live | Superseded for the wizard by Compact (below) | A — promote to Training (migration runs there) |
| Compact Open a New Project (PR #15) | branch, held out of calisign1 | Yes (reported complete 28 Oct; held only for release sequencing) | No | No | Lessons and screenshots already in the PR | **A — the hold expired when CaliSIGN went live**; reconciled onto current `main`, release `catchup1` |
| Supplier Pricing Request form generator + template library (Hardie v1) | branch | Yes (Joel approved the form; used for BMR and Timber Mart, 29 Oct) | n/a (tooling, no page) | n/a | None (no page yet) | A — merged into `main` as tooling; where it appears in the app is still Joel's decision; template box ratios await Joel's confirmation |
| Calendar month fit, banked hours, Linda Bushel/Family 08 governance, ops tools | `main` | Yes | Not present (Training at 26 Oct code) | Live | None beyond screenshots | A — promote to Training with the release |
| Supplier Unit Pricing & Conversion | **not started** (the brief was not supplied in this session) | No | — | — | — | C — not deployed |
| FG-041 originals, storybook/website/AiRIA publication branches | branches (governed) | — | — | — | — | Not application work; kept (source-of-truth) |
| 18 Oct calendar layout proof / WIP, `security/closure` local-storage commit | branches | Superseded | — | — | — | D — not deployed |

## 4. PR #15 — Compact Open a New Project

- `origin/main` (17 commits ahead of the PR's base, incl. CaliSIGN) merged into the PR branch with no conflict
  (`ef95cfa5`). No migration, no model change.
- The PR's browser walk was not in the release gate; it is added (`538d3a21`): 3 widths + no server error = 4 checks,
  so the gate expects **302** browser checks (298 on `main` + 4).
- Cloud checks on the merged tree (Chromium standing in for Chrome): the five affected browser suites — compact new
  project, project creation, wizards, selected work, CaliSIGN — **55 passed, 0 failed** (the same four suites on
  `main`: 51).

## 5. CaliSIGN

Not reopened. Production is the 29 Oct release. Training gets it with `catchup1`. Deliberate difference kept:
the training site's demo (synthetic) suppliers and its change orders pin `CONSENT-SYNTHETIC-UAT-001`; Production
uses the three production consents ([../governance/signing-consent-register.md](../governance/signing-consent-register.md)).

## 6. Supplier Unit Pricing

Development status only: **not started** — the implementation brief has not been provided in this session. The
architecture is recorded as Joel stated it: Calibrayt accepts construction requirements in takeoff/estimating
units and supplier pricing in supplier/POS sell units, and owns the governed conversion between them. It will be
built on its own branch from current `main` and not deployed until accepted.

## 7. Training Centre reconciliation (in `catchup1`)

- **Module 13 (Guided Estimating, the centre of Kevin's Contractor Review)** rewritten for selected work: Start New
  Estimate → New Project → **What work are we doing?** (Windows, Excavation, Footings, Electrical, HVAC; Internal or
  Subcontracted) → Estimate this work → Footings (calculator, review, labour) → Electrical (quotes) → HVAC
  (allowance) → internal cost → pricing → proposal. Lesson and acceptance-test **keys unchanged**, so every
  trainee's saved progress and every recorded result (Kevin's included, with its notes and release label) stays
  attached to the same lesson or test; only today's wording changed.
- Module 14 (calculators' three choices), the Tutor answers and the Workflow Map's PRICE stage: no N/A, "work
  item" instead of "stage".
- CaliSIGN: contractor module 8 (place the order: Adopt your signature, Sign & Send for E-Signature; the store's
  Sign & Confirm Order), module 10 and 11 (Send for E-Signature), supplier modules 5 and 6 (Sign & Confirm Order,
  Sign & Send the Change, Sign & Accept, Sign & Propose This Time; declining needs no signature) and their tests.
- Screenshots re-taken on the release tree by the training capture walks — contractor (16 walks), supplier (12),
  guided estimating (10), Field crew (11) — all passed with no server or page error. The capture walks were updated
  for selected work and CaliSIGN; the Field crew walk's counts follow the Magnificent Seven module (9 modules,
  26 tests) and its "no price on Field" check no longer flags the sentence "the office … prices it on a change order".
- Kevin's historical review results and comments are data on the Training site and are not touched.

## 8. Kevin's contractor feedback (for Joel's walk-through)

Kevin (three sessions; "tough going"; often does not see the next step; some terminology unclear; some workflows
do not match how he thinks). He used the Training Centre, which ran the **26 Oct code** (§1).

**Already corrected in the current product (live, or in `catchup1`):**
- Estimating no longer starts with fourteen generic stages to classify (Internal / Subcontracted / N/A). He now picks
  the work he is doing — "What work are we doing?" — and nothing else appears (selected work, live 29 Oct).
- Starting a project is one compact five-step dialog (Project, Customer, Details, Plans, Review) with a **Project
  Created** page that offers the next step (Start Guided Estimating / Open Project) (`catchup1`).
- The estimating workflow names the next action on every work item ("Start: Windows", "Next: Set up the subcontract
  and request the quote") and the count only covers chosen work.
- Signing reads the same everywhere (CaliSIGN): Send for E-Signature, Sign & Send, Sign & Confirm, with a signature
  preview.

**Training mismatch (stale instructions or pictures; corrected by `catchup1`):**
- Module 13 taught the stage/N/A model and its pictures showed it; the Tutor and Workflow Map said the same.
- Supplier-order, delivery-change and change-order steps named buttons that no longer exist after CaliSIGN.
- The Training site itself was two releases behind Production, so instructions written for Production would not
  have matched what he saw.

**Still present after synchronization (genuine UX issues to walk through with Kevin):**
1. **"Stage" and "work item" are mixed.** The pricing page says "Every included stage is complete"; the Guided
   Estimating wizard counts "internal stages" and "subcontracted stages"; the Workflow Map elsewhere still speaks of
   stages. Same thing, two names.
2. **Office/finance vocabulary on contractor screens:** Commercial Decision Gate, Pricing Posture, Execution Risk,
   Schedule Condition, Delivery Model, Permit context class (the full New Project form, which the "Create a new
   project" path from Start New Estimate still uses — the compact dialog pre-fills them); Scope Delivery Review,
   "Confirm who supplies and builds these lines", Costing review, Internal cost estimate.
3. **Two different ways to create a project.** Home → Start a New Project opens the compact dialog; Home → Estimate a
   Project → Continue manually → Create a new project opens the long form with the Commercial Decision Gate. A
   contractor following "estimate a new job" lands on the long form.
4. **Many places to go next.** After a work item is complete, "Complete & Next" opens the next unfinished item, but
   the estimate, the internal cost estimate, Review Pricing & Prepare Proposal and the proposal are separate pages
   with their own buttons; the proposal still needs a separate sign-off and send (module 10).
These are recorded, not changed: each is a product decision for Joel after the walk-through.

## 9. Environments after `catchup1` (filled in at release)

See the session handoff's current resume point for the final SHAs and checks.
