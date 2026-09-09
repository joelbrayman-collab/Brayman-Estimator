# Feature Gate FG-028: CalibAi to CalibraytAI Product Identity Transition

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-028` |
| Feature Name | CalibAi to CalibraytAI Product Identity Transition |
| Target Milestone | **None.** FG-028 is the governing identifier. Do **not** assign a new M0xx number. Do **not** score V1 package completion from this gate. |
| Module | Platform product identity. No new module. Does **not** take ownership of Organization Brand Profile, Estimating, Permit Intelligence records, or Field capture records. |
| Date | 2026-09-09 |
| Status | **SLICES 1–2 IMPLEMENTED / TESTED / COMMITTED / PUSHED. SLICE 3 ASSET INSTALLATION PENDING. NOT CLOSED.** Live current = heads **`a5b6c7d8e9f0`**. [ADR-045](../adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. |
| Architecture | [ADR-045](../adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted** · [product-identity.md](../governance/product-identity.md) · [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) · [ADR-040](../adr/ADR-040-organization-brand-profile.md) · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |
| Related ADRs | **[ADR-045](../adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) Accepted**. Do **not** accept ADR-008 or ADR-010 from this gate. |
| Prerequisites | FG-027 **CLOSED / OPERATIONAL FOR UAT**. Product-identity reconnaissance complete (2026-09-08). |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **NOT CLOSED.** Slices 1–2 **IMPLEMENTED / TESTED / COMMITTED / PUSHED**. Slice 3 **PENDING**. |
| Slice 1 — visible product text + tests | **IMPLEMENTED** |
| Slice 2 — current authority + future-facing docs | **IMPLEMENTED** |
| Slice 3 — Joel-approved lettering asset | **HELD / JOEL ASSET PENDING** |
| Website | **EXTERNAL / PENDING SEPARATE JOEL-CHATGPT PASS** |
| Schema / Alembic | **None.** Live current = heads **`a5b6c7d8e9f0`**. |
| Live DB mutation | **None.** |

```text
FG-028:
SLICES 1–2 IMPLEMENTED / TESTED / COMMITTED / PUSHED
SLICE 3 ASSET INSTALLATION PENDING
NOT CLOSED
ADR-045 ACCEPTED
LIVE CURRENT = HEADS a5b6c7d8e9f0
NO SCHEMA MIGRATION
NO LIVE DB MUTATION
V1 REMAINS 45% / 2 OF 11
DO NOT BEGIN V1-03 FROM THIS GATE
```

Do **not** mark CLOSED while required logo/product-asset acceptance remains open.

## Tests (Slices 1–2)

| Suite | Result |
|-------|--------|
| Dedicated `tests/test_product_identity_fg028.py` | **9 passed** |
| Focused Field / Hub / Permit / Brand Profile / Labour | **117 passed** |
| Full `./venv/bin/python -m pytest -q` | **661 passed** |

Pre-rename governed full-suite baseline was **652 passed**. Delta is the 9 dedicated FG-028 tests.

## Remaining CalibAi search (not zero)

Do **not** require zero `CalibAi` hits. Remaining matches are classified:

| Class | Examples |
|-------|----------|
| PRESERVE_HISTORICAL | chat-workflow-log / milestones / closed FG and ADR bodies; CAR-001 original text; Alembic comments; live `permit_findings.advisory_language`; labour/pricing seed “not a CalibAi default” |
| TECHNICAL_IDENTIFIER_PRESERVE | `calibai-field-v1` keys; `calibai-mock`; `CALIBAI-AI`; `CALIBAI_BASELINE` token; tempfile prefixes; ADR-019 / CAR-001 filenames |
| EXTERNAL_PATH_PRESERVE | `~/Desktop/CalibAi Historical Estimates`; Documents `CalibAi/Approved Document Templates` |
| ASSET_PENDING | Field still uses `brayman-construction-logo.png` (Slice 3) |

No unexplained current user-facing CalibAi remains in Slice 1 templates/generators.

---

## Purpose

Transition **current** product identity from CalibAi to **CalibraytAI** without a blind global replace, without rewriting history, and without substituting product name for tenant or office chrome.

---

## Feature Gate answers

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | Current user-facing and governing product name is still CalibAi after Joel selected CalibraytAI. Identity must be recorded and applied without destroying historical CalibAi truth or tenant branding. |
| 2 | Who is the user? | Office estimators (Hub/historical copy, Permit reports), Field users (title/alt), and AI/human developers reading current governance. |
| 3 | Which module owns it? | No new module. Platform identity. Permit Intelligence keeps permit snapshots. Field keeps capture identifiers. Brand Profile stays Organizations. |
| 4 | What data does it own? | None. No new tables. |
| 5 | What data does it reference? | Live advisory constant (not frozen finding rows); Field templates; office `product_name` (must remain Brayman Construction Platform). |
| 6 | What may it change? | Authorized current visible product strings; current-authority / future-facing docs; tests that asserted the former visible name. |
| 7 | What must it not change? | Office chrome BCP; ORG-001 / Brand Profile; Field IndexedDB keys; `calibai-mock`; `CALIBAI-AI`; `CALIBAI_BASELINE` token; frozen DB rows; Alembic history; ADR-019/CAR-001 filenames; V1 45% / 2 of 11; V1-03; logos; website. |
| 8 | What are the acceptance criteria? | Current authorized surfaces say CalibraytAI; alias recorded; history preserved; identifiers preserved; tests PASS; no migration; remaining CalibAi hits classified; Slice 3 still open. |
| 9 | What tests are required? | Dedicated FG-028 tests plus Field, Hub, Permit, Brand Profile, Labour focused suites and full pytest. |
| 10 | What documentation must be updated? | product-identity.md; ADR-045; this gate; vision; constitution link; V1 register **product** field only; AGENTS; Cursor rules; continuity; current-state; session-handoff; roadmap; indexes; future-facing FG-024 / supplier-channel / Native Signing product name. |
| 11 | Does it require an ADR? | **Yes — ADR-045.** |
| 12 | Does it require a database migration? | **No.** |

---

## Slice 3 (held)

Joel-approved CalibraytAI lettering asset is **not** in this implementation. Same emblem, colours, layout; lettering only. Field may continue using `branding/brayman-construction-logo.png` until Slice 3.

Temporary known identity/asset conflation: Field **text** CalibraytAI + Brayman Construction **PNG**.

---

## Non-goals

V1-03 · ADR-008 · supplier/BMR/Winchester implementation · FG-024 implementation · another FG-025 slice · LEARN · QuickBooks · contracts · Native Signing · Observation Delete · schema migration · live DB mutation · marketing website · repository rename
