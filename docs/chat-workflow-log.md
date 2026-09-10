# Chat Workflow Log — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Continuity log (append-only) |
| Updated | 2026-09-10 |

## Purpose

Memorializes important ChatGPT / Cursor work. This is **not** a verbatim transcript. It is the authoritative decision and implementation summary for recovery without chat history.

**Do not overwrite past entries.** Append new entries at the top of the Entries section (newest first).

## Entry template (copy for each sprint)

```markdown
### YYYY-MM-DD — <short title>

| Field | Content |
|-------|---------|
| Date | |
| Branch | |
| Active ChatGPT development chat title | |
| Objective | |
| Business decision | |
| Architectural decision | |
| Prompt template used | |
| Approved Cursor prompt summary | |
| Files expected to change | |
| Files prohibited from changing | |
| Implementation result | |
| Tests | command(s) + exact result |
| Project-state-report update | |
| Milestone entry update | |
| Constitutional issue raised | |
| Unresolved issues | |
| Next approved step | |
| Next approved prompt | |
| Commit hash | (when available) |
```

---

## Entries

### 2026-09-10 — FG-031 documentation-only final governance close

| Field | Content |
|-------|---------|
| Date | 2026-09-10 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Documentation-only final governance close of FG-031 after architectural review, implementation review, live migration, Slice A office UAT, and Slice B bounded office UAT. No application code. No migration. No live DB mutation. No UAT rerun. No V1 rescore. |
| Business decision | FG-031 **CLOSED / OPERATIONAL FOR UAT**. Slice A and Slice B **OPERATIONAL FOR UAT**. Subcontract RFQ/package **MATURATION DURING UAT / NOT REQUIRED FOR CLOSURE / NOT IMPLEMENTED**. V1 remains **55% / 3 of 11**. Current scored package **V1-04 / NOT STARTED**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. Independent remaining blocker: Ontario/fail-closed contract story. |
| Architectural decision | ADR-048 remains **Accepted**. FG-027 remains final human Costing authority. FG-029 supplier price remains INFORM ONLY. FG-030 remains **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. ADR-008 remains **Proposed**. Close does **not** authorize RFQ/package, FG-030, or V1-04. |
| Prompt template used | Joel/ChatGPT FG-031 final governance close — documentation reconciliation only (10 Sep 2026) |
| Approved Cursor prompt summary | Verify baseline on `main` @ `8629f0459e51a94ee42cb475a536570cfbc21639`; reconcile FG-031 current vs original design; update minimum authoritative docs; commit `docs: close FG-031`; push main; return A–AB report; STOP. |
| Files expected to change | FG-031 gate; preflight; ADR-048; current-state; project-state-report; session-handoff; V1 register; platform-roadmap; docs indexes; estimating module; milestones; chat-workflow-log; UAT records only if a subsequent close note was required |
| Files prohibited from changing | Application code; templates; CSS; migrations; live database; UAT evidence body; FG-030; V1-04; ADR-008 acceptance |
| Implementation result | Documentation reconciled. FG-031 **CLOSED / OPERATIONAL FOR UAT**. Diff documentation-only. |
| Tests | **NOT RERUN.** HISTORICAL Slice B UAT focused **83 passed**, 454 warnings, 15.24s; full **728 passed**, 2173 warnings, 373.17s. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | FG-030 not implementation-authorized. V1-04 not begun. RFQ/package not implemented. BMR DEMO READY remains NO (Ontario/fail-closed contract story). |
| Next approved step | **STOP.** Return to ChatGPT Architect. Do **not** implement FG-030. Do **not** begin V1-04. Do **not** implement subcontract RFQ/package. |
| Next approved prompt | None from this documentation close. |
| Commit hash | This documentation close commit (`docs: close FG-031`). Product **`5e1082af68e0eb145d9da01c0fa26585f6b8b9d1`**. Slice B UAT close **`8629f0459e51a94ee42cb475a536570cfbc21639`**. |

### 2026-09-10 — FG-031 Slice B live migrate + bounded office UAT

| Field | Content |
|-------|---------|
| Date | 2026-09-10 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Governed live DB backup; live migrate `d8e9f0a1b2c3`; bounded synthetic office UAT of FG-031 Slice B. No FG-030. No V1-04. No subcontract RFQ/package. |
| Business decision | Slice B becomes LIVE-MIGRATED / OFFICE UAT PASS / OPERATIONAL FOR UAT only if required checks PASS. Overall FG-031 remains NOT CLOSED pending ChatGPT Architect confirmation. V1 remains **55% / 3 of 11**. BMR DEMO READY remains **NO**. |
| Architectural decision | ADR-048 remains Accepted. Quote is evidence, not cost or Pricing authority. FG-027 remains human costing authority. Selected quote freeze is identity plus copied facts. ADR-008 remains Proposed. FG-030 unchanged. |
| Prompt template used | Joel/ChatGPT FG-031 Slice B live migration + bounded office UAT (10 Sep 2026) |
| Approved Cursor prompt summary | Baseline verify; recoverable backup; apply `d8e9f0a1b2c3`; bounded DEMO office UAT; operational close if PASS; commit/push close docs. No FG-030. No V1-04. No product correction unless a verified Slice B defect blocked UAT. |
| Files expected to change | Current-authority governance docs; dedicated Slice B UAT record. Live DB mutation via Alembic + labeled synthetic UAT only. |
| Files prohibited from changing | Product code (none required); FG-030; V1-04; ADR-008 acceptance; LEARN; QuickBooks; contracts; Native Signing; Observation Delete; website; HostPapa; backup file (gitignored) |
| Implementation result | Backup SHA-256 `b1096083400b6bc840cdb113e157f5795fb3a7c52723ffb70515eb293617bef5`. Live current = head `d8e9f0a1b2c3`. Canonical UAT project **id 25**. Required UAT PASSed. No product defect. |
| Tests | Focused Slice B+A+FG-027+FG-029 **83 passed** (15.24s). Full suite **728 passed**, 2173 warnings, **373.17s**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | FG-031 overall NOT CLOSED (Architect confirmation). FG-030 not implementation-authorized. V1-04 not begun. RFQ/package not implemented. BMR DEMO READY remains NO (Ontario/fail-closed contract story). |
| Next approved step | **STOP.** Return to ChatGPT Architect. Do **not** implement FG-030. Do **not** begin V1-04. Do **not** implement a subcontract RFQ/package. |
| Next approved prompt | None from this UAT. |
| Commit hash | This documentation/UAT close commit. Start pin **`314ced5699688a329dbdd7ab2484ef552dd447db`**. Product **`5e1082af68e0eb145d9da01c0fa26585f6b8b9d1`**. |

### 2026-09-10 — FG-031 Slice B subcontract quote evidence product implementation

| Field | Content |
|-------|---------|
| Date | 2026-09-10 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Implement FG-031 Slice B: thin org-scoped Subcontractor, EstimateVersion-scoped SubcontractQuoteEvidence, human selection, selected-quote freeze into FG-027 costing snapshot, PRICE quote review. No live migrate. No live UAT. No FG-030. No V1-04. |
| Business decision | A quote is evidence. It does not set EstimateLineItem cost or apply Pricing. One SELECTED quote per line. Prior SELECTED is SUPERSEDED, not deleted. Selected quote freeze is identity plus copied facts. |
| Architectural decision | ADR-048 remains Accepted. Do not collapse Subcontractor into Supplier. No SOURCE_SUBCONTRACT_QUOTE. No selected-quote requirement before costing. Allowance remains compatible. Attachment is optional textual provenance_note. V1 remains **55% / 3 of 11**. |
| Prompt template used | Joel/ChatGPT FG-031 Slice B product implementation (9 Sep 2026) |
| Approved Cursor prompt summary | Slice B product implementation. One additive Alembic file `d8e9f0a1b2c3`. No live flask db upgrade. No live UAT. No FG-030. No V1-04. Commit/push if PASS. |
| Files expected to change | Subcontractor/quote models; migration `d8e9f0a1b2c3`; quote service; costing freeze columns; Scope Delivery Review UI; dedicated tests; minimum current-authority docs |
| Files prohibited from changing | Live DB; FG-030; V1-04; ADR-008 acceptance; LEARN; QuickBooks; contracts; Native Signing; Observation Delete; website; HostPapa |
| Implementation result | Slice B coded and tested. Migration file **not applied live**. Live current remains `c7d8e9f0a1b2`. Repository Alembic head `d8e9f0a1b2c3`. |
| Tests | Dedicated Slice B **21 passed**. Slice A **26**. FG-027 **20**. FG-029 **16**. Estimating clone/builder **22**. Pricing **33**. Output/proposals **68**. Material Catalogue **35**. Labour Engine **25**. FG-026 **20**. Project Hub **13**. Governed bundle **306 passed**. Full suite **728 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Live migrate not run. UAT not authorized. FG-030 not implementation-authorized. V1-04 not begun. RFQ/package not implemented. |
| Next approved step | **STOP.** Return to ChatGPT Architect. Do **not** live-migrate Slice B. Do **not** implement FG-030. Do **not** begin V1-04. |
| Next approved prompt | None from this implementation. |
| Commit hash | Product **`5e1082af68e0eb145d9da01c0fa26585f6b8b9d1`**. Start pin **`0d98b87112e8dda3537fe125d25f0737212bfe1c`**. Pin follows. |

### 2026-09-09 — FG-031 Slice A live migrate + bounded office UAT

| Field | Content |
|-------|---------|
| Date | 2026-09-09 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Governed live DB backup; live migrate `c7d8e9f0a1b2`; bounded synthetic office UAT of FG-031 Slice A. No Slice B. No FG-030. No V1-04. No product-code repair if UAT finds a defect. |
| Business decision | Slice A becomes LIVE-MIGRATED / OFFICE UAT PASS / OPERATIONAL FOR UAT only if required checks PASS. Overall FG-031 remains NOT CLOSED because Slice B is not implemented. V1 remains **55% / 3 of 11**. BMR DEMO READY remains **NO**. |
| Architectural decision | ADR-048 remains Accepted. CONFIRMED routing is costing authority; resolved PROPOSED still blocks. Supplier Package cited CONFIRMED CONTRACTOR_PURCHASED filter. ADR-008 remains Proposed. FG-030 unchanged. |
| Prompt template used | Joel/ChatGPT FG-031 Slice A live migration + bounded office UAT (9 Sep 2026) |
| Approved Cursor prompt summary | Live backup; migrate `c7d8e9f0a1b2`; bounded DEMO UAT; operational close if PASS; commit/push close docs. No Slice B. No product repair. |
| Files expected to change | Current-authority governance docs; dedicated UAT record. Live DB mutation via Alembic + labeled synthetic UAT only. |
| Files prohibited from changing | Product code; Slice B; FG-030; V1-04; ADR-008 acceptance; LEARN; QuickBooks; contracts; Native Signing; Observation Delete; website; HostPapa; backup file (gitignored) |
| Implementation result | Backup SHA-256 `f2dec3fd0010f67398a908c065a6f273a7c8b3ed7b37280d1113ed16f3b3987b`. Live current = head `c7d8e9f0a1b2`. Canonical UAT project **id 19**. Required UAT PASSed. No product defect. |
| Tests | **NOT RERUN** (no product defect). HISTORICAL dedicated FG-031 **26**; FG-027 **20**; FG-029 **16**; governed bundle **258**; full suite **707**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Slice B not authorized. FG-030 not implementation-authorized. V1-04 not begun. BMR DEMO READY remains NO (Ontario/fail-closed contract story). Interactive logged-in browser walkthrough of Scope Delivery Review was not available (expired sessions); authenticated product HTML PASS. |
| Next approved step | **STOP.** Return to ChatGPT Architect. Do **not** implement Slice B. Do **not** implement FG-030. Do **not** begin V1-04. |
| Next approved prompt | None from this UAT. |
| Commit hash | Close **`b50b0dcd1ea24f1a37ed32d04325ce09127fd203`**. Start pin **`bbe22f2a10ba9ba827e50c92688774a025b95d34`**. Pin follows. |

### 2026-09-09 — FG-031 Slice A human-confirmation costing gate repair

| Field | Content |
|-------|---------|
| Date | 2026-09-09 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Bounded repair: FG-027 Costing Approval requires CONFIRMED scope routing, not merely resolved dimensions. No live migrate. No Slice B. |
| Business decision | PROPOSED is suggested/resolved working routing, not approved routing. CONFIRMED is human-approved routing and is required before Costing Approval. |
| Architectural decision | Keep public block identity `SCOPE_DELIVERY_UNRESOLVED`. No new `SCOPE_DELIVERY_UNCONFIRMED` code. Allowance exception preserved. Clone remains PROPOSED (reconfirm before costing). Supplier Package still CONFIRMED + CONTRACTOR_PURCHASED. V1 remains **55% / 3 of 11**. |
| Prompt template used | Joel/ChatGPT FG-031 Slice A bounded human-confirmation gate repair (9 Sep 2026) |
| Approved Cursor prompt summary | One bounded repair: costing requires CONFIRMED routing. No live migrate. No Slice B. Commit/push if PASS. |
| Files expected to change | `app/services/estimate_costing.py`; test helper + FG-027/pricing/output/FG-029/FG-031 tests; minimum FG-031 docs |
| Files prohibited from changing | Live DB; Alembic revision; Slice B; FG-030; V1-04; website |
| Implementation result | Costing BLOCK if absent, UNRESOLVED, or status != CONFIRMED. No schema change. Live current remains `b6c7d8e9f0a1`. |
| Tests | Dedicated FG-031 **26 passed**. FG-027 **20**. FG-029 **16**. Clone/builder **22**. Governed bundle **258 passed**. Full suite **707 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Live migrate not run. UAT not authorized. Slice B not authorized. |
| Next approved step | **STOP.** Return to ChatGPT Architect. Do **not** live-migrate. Do **not** implement Slice B. Do **not** implement FG-030. Do **not** begin V1-04. |
| Next approved prompt | None from this repair. |
| Commit hash | Repair **`ec8dcf35f0da109b75422504e1a104c1623d186c`**. Pin follows. Parent pin **`c7662164a3f562f18cdd4b71079970348b1cd72c`**. |

### 2026-09-09 — FG-031 Slice A scope delivery routing product implementation

| Field | Content |
|-------|---------|
| Date | 2026-09-09 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Implement FG-031 Slice A routing core: EstimateScopeDelivery, additive Alembic file, Hub PRICE Scope Delivery Review, per-row confirm, Approve All, FG-027 unresolved BLOCK, Supplier Package CONTRACTOR_PURCHASED filter, clone copy, tests. No live migrate. No Slice B. |
| Business decision | Two stored dimensions; no HYBRID enum; 1:1 per EstimateLineItem; OWNER_SUPPLIED / OWNER_THIRD_PARTY schema-valid but hidden in first Slice A UI; human confirmation; Approve All explicit POST; uncited MANUAL/DEMO fail-closed for Supplier Package. |
| Architectural decision | [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **SLICE A IMPLEMENTED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / SLICE B NOT AUTHORIZED / NOT CLOSED**. Clone copies dimensions; cloned Draft is `PROPOSED` (resolved) or `DRAFT` (unresolved) with confirmation cleared. Costing BLOCK is absent/UNRESOLVED dimensions (Allowance exception), not unconfirmed. V1 remains **55% / 3 of 11**. FG-030 remains **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 remains **Proposed**. |
| Prompt template used | Joel/ChatGPT FG-031 Slice A product implementation (9 Sep 2026) |
| Approved Cursor prompt summary | Slice A product implementation. One additive Alembic **file**. No live flask db upgrade. No live UAT. No Slice B. Commit/push if PASS. |
| Files expected to change | EstimateScopeDelivery model; migration `c7d8e9f0a1b2`; routing service/routes/template; FG-027 BLOCK; Supplier Package filter; clone copy; tests; minimum current-authority docs |
| Files prohibited from changing | Live DB; Slice B Subcontractor/quote/RFQ/portal; FG-030; V1-04; ADR-008 acceptance; LEARN; QuickBooks; contracts; Native Signing; Observation Delete; website; HostPapa |
| Implementation result | Slice A coded and tested. Migration file not applied live. Live current remains `b6c7d8e9f0a1`. Repository Alembic head `c7d8e9f0a1b2`. |
| Tests | Dedicated FG-031 **23 passed**. FG-027 **20**. FG-026 **20**. FG-029 **16**. Estimating clone/builder **22**. Material Catalogue **35**. Labour Engine **25**. Pricing **33**. Output/proposals **28**. Project Hub **13**. Governed bundle **235 passed**. Full suite **704 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Live migrate not run. UAT not authorized. Slice B not authorized. FG-030 not implementation-authorized. V1-04 not begun. Owner/third-party remain reserved UI values. |
| Next approved step | **STOP.** Return to ChatGPT Architect. Do **not** live-migrate. Do **not** implement Slice B. Do **not** implement FG-030. Do **not** begin V1-04. |
| Next approved prompt | None from this implementation. |
| Commit hash | Product **`54120608df98432b9be80faf8c2a3a08cdb5679c`**. Pin follows. Parent pin **`9c3eeddb0ae8e4c0daaba119ee6eb590a25c6a18`**. |

### 2026-09-09 — ADR-048 / FG-031 scope delivery routing architecture recording

| Field | Content |
|-------|---------|
| Date | 2026-09-09 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Docs-only recording of ADR-048, FG-031, and architecture preflight from the completed scope-delivery reconciliation. No product implementation. |
| Business decision | Two stored routing dimensions (material procurement × labour delivery). No HYBRID enum. Human confirmation required. Approve All Scope Routing is authorized design for Slice A. Unresolved routing later BLOCKS FG-027 except Allowance. Supplier Package eligibility = CONTRACTOR_PURCHASED only. Customer estimate remains delivery-blind. |
| Architectural decision | [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted** (architecture only). [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Supporting V1 gate; **not** a 12th package. V1 remains **55% / 3 of 11**. FG-030 remains **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 remains **Proposed**. |
| Prompt template used | Joel/ChatGPT ADR-048 + FG-031 governance recording (9 Sep 2026) |
| Approved Cursor prompt summary | Docs/architecture only. Record ADR-048, FG-031, preflight, minimum current-authority. Commit/push if coherent. Do not implement FG-031, FG-030, or V1-04. No schema. No Alembic. |
| Files expected to change | Governance/current-authority docs only |
| Files prohibited from changing | `app/`; `migrations/`; tests; live DB; branding; website |
| Implementation result | Docs recorded. ADR-048 **Accepted**. FG-031 **NOT IMPLEMENTATION-AUTHORIZED**. **NOT IMPLEMENTED**. No product code. No migration. |
| Tests | **NOT RERUN** — ADR-048 / FG-031 architecture recording only. Last product-changing full suite **681 passed** (HISTORICAL; FG-028 Slice 3). |
| Project-state-report update | Yes |
| Milestone entry update | Yes (recorded architecture; not a coded milestone) |
| Constitutional issue raised | None |
| Unresolved issues | FG-031 implementation not authorized. Slice A UI may hide OWNER_SUPPLIED / OWNER_THIRD_PARTY (architecture values retained). FG-030 not implementation-authorized. V1-04 not begun. |
| Next approved step | **STOP.** Return to ChatGPT Architect. Do **not** implement FG-031. Do **not** implement FG-030. Do **not** begin V1-04. |
| Next approved prompt | None from this recording. |
| Commit hash | Architecture **`1c6c8c492b92f11cc80ad1b6e8689f0e42523bcd`**. Pin follows. |

### 2026-09-09 — FG-028 Slice 3 approved logo installation / close

| Field | Content |
|-------|---------|
| Date | 2026-09-09 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Install Joel-approved CalibraytAI runtime product logos, test, verify, close FG-028. |
| Business decision | Strict asset swap. V2 on Field header (light/cream). No V1 install (no governed dark PRODUCT placement). Tenant office/login/Brand Profile/Proposal/Change Order unchanged. No favicon derivation. No layout/typography change. |
| Architectural decision | FG-028 **SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT**. CALIBRAYTAI PRODUCT IDENTITY TRANSITION **COMPLETE**. V1 remains **55% / 3 of 11**. FG-030 **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. SCOPE DELIVERY / MAKE-BUY **QUEUED** only. |
| Prompt template used | Joel/ChatGPT FG-028 Slice 3 authorized prompt (9 Sep 2026) |
| Approved Cursor prompt summary | Locate `CalibraytAI_090926_Final.zip`; install required runtime PNG; replace governed PRODUCT placements only; V1 dark / V2 light; bounded tests; visual QA; close FG-028; commit/push if PASS. |
| Files expected to change | Runtime V2 PNG; Field header template; FG-028 tests; minimum FG-028 governance close docs |
| Files prohibited from changing | Schema/Alembic; live DB; tenant logos; website; FG-030; V1-04; scope-delivery; Supplier Integration; HostPapa |
| Implementation result | V2 PNG installed as exact ZIP bytes. Field header src swapped. Layout/CSS footprint preserved. V1 PNG not installed. Favicon unchanged. |
| Tests | Dedicated FG-028 **13 passed**. Field **20**. Combined Field/FG-025/Brand/Proposal/CO/auth **131 passed**. Focused Field/Hub/Permit/Brand/Labour **117 passed**. FG-029 **16 passed**. Full suite **681 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Field favicon remains tenant PNG (no supplied square favicon). FG-030 not implementation-authorized. V1-04 not begun. SCOPE DELIVERY / MAKE-BUY not implemented. |
| Next approved step | **STOP.** Return to ChatGPT Architect. Queued next architecture: SCOPE DELIVERY / MAKE-BUY / PROCUREMENT ROUTING. |
| Next approved prompt | None from this close. |
| Commit hash | Product **`502035fa70ced1d0ff042db3077cc66f50e68de4`**. Pin follows. |

### 2026-09-09 — FG-029 post-UAT governance reconciliation

| Field | Content |
|-------|---------|
| Date | 2026-09-09 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Reconcile interleaved already-authorized governance dirt into one coherent current-authority state after FG-029 live migrate + bounded UAT PASS. |
| Business decision | One governance commit containing FG-029 close/UAT authority, FG-028 asset-status, FG-030 architecture recording, and previously authorized copyable-output rule. Push `main`. Bounded SHA-pin if convention requires. No product code. No logo install. No FG-030 implementation. |
| Architectural decision | FG-029 **CLOSED / OPERATIONAL FOR UAT**. V1-03 **COMPLETE**. V1 **55% / 3 of 11**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. FG-028 Slice 3 **ASSET RECEIVED / JOEL APPROVED / FINAL / APPLICATION INSTALLATION / TEST / ACCEPTANCE PENDING / NOT CLOSED**. ADR-047 **Accepted** (architecture only). FG-030 **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. ADR-008 remains **Proposed**. SCOPE DELIVERY / MAKE-BUY routing **QUEUED** only. Website Version 15 published / live QA PASS (external). HostPapa **QUEUED POST-BETA**. |
| Prompt template used | Joel/ChatGPT FG-029 post-UAT governance reconciliation (9 Sep 2026) |
| Approved Cursor prompt summary | Docs/governance only. Preserve FG-028 / FG-030 / copyable-output. One coherent commit. Push main. Do not install logos. Do not implement FG-030. Do not begin V1-04. |
| Files expected to change | Governance/current-authority docs + `.cursor/rules/50-chat-copyable-output.mdc` (preserved) + UAT record |
| Files prohibited from changing | Product code; tests; models; templates; Alembic; live DB; logo assets; website source |
| Implementation result | Governance reconciled. Product tree unchanged. Live Alembic remains `b6c7d8e9f0a1`. |
| Tests | **NOT RERUN** — docs/governance reconciliation only. Historical FG-029 dedicated **16** / governed **210** / full **677**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | FG-028 Slice 3 application installation pending. FG-030 not implementation-authorized. V1-04 not begun. SCOPE DELIVERY / MAKE-BUY not implemented. |
| Next approved step | **STOP.** Return to ChatGPT Architect. |
| Next approved prompt | None from this reconciliation. FG-028 Slice 3 / FG-030 / V1-04 require separate authorization. |
| Commit hash | Close **`880697a246de7e901a81f89584168a9a9fb1dd67`**. Pin follows. |

### 2026-09-09 — FG-029 live migration + bounded BMR demo office UAT

| Field | Content |
|-------|---------|
| Date | 2026-09-09 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Authorized FG-029 live migrate + bounded DEMO Winchester office UAT. Preserve existing FG-028 / FG-030 / copyable-output dirt. |
| Business decision | Live-migrate `a5b6c7d8e9f0` → `b6c7d8e9f0a1`. Create labeled DEMO/SYNTHETIC UAT only. Close FG-029 if all criteria PASS. Do not install FG-028 logos. Do not implement FG-030. |
| Architectural decision | Additive schema only. Supplier price INFORM ONLY. Frozen issued package does not float. No EstimateLineItem / costing / Pricing mutation. No PLAN mutation. No BMR HTTP/EDI/PO. ADR-008 remains Proposed. |
| Prompt template used | Joel/ChatGPT FG-029 live-migrate / UAT prompt (9 Sep 2026) |
| Approved Cursor prompt summary | Resume live migration + bounded BMR demo office UAT. Preserve existing governance dirt. Do not run FG-028. Do not implement FG-030. |
| Files expected to change | Live DB (gitignored) + minimum FG-029 close/current-authority docs |
| Files prohibited from changing | Product code; FG-028 logo install; FG-030 implementation; discarding unrelated dirt |
| Implementation result | Migration **PASS**. UAT **PASS**. Project **id 14**. Package **id 1** ISSUED. V1-03 **COMPLETE**. Readiness **55%**. BMR DEMO READY **NO**. Close-doc Git commit **blocked** by interleaved FG-028/FG-030 dirt. |
| Tests | **NOT RERUN**. Historical FG-029 dedicated **16** / governed **210** / full **677**. |
| Project-state-report update | Yes (working tree; not committed) |
| Milestone entry update | Yes (working tree; not committed) |
| Constitutional issue raised | None |
| Unresolved issues | Close docs cannot be safely committed while FG-028/FG-030 dirt is interleaved in the same files. FG-028 Slice 3 installation pending. FG-030 not implementation-authorized. |
| Next approved step | **STOP.** Return to ChatGPT Architect. |
| Next approved prompt | None from this close. FG-028 Slice 3 / FG-030 / V1-04 require separate authorization. |
| Commit hash | **none** — UAT PASS / CLOSE DOC COMMIT BLOCKED BY INTERLEAVED GOVERNANCE DIRT |

### 2026-09-09 — FG-030 supplier identity / authentication / access isolation architecture

| Field | Content |
|-------|---------|
| Date | 2026-09-09 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Define and govern supplier named-user login, membership, sharing, isolation, workspace, and login routing. No implementation. |
| Business decision | No supplier sees another supplier's commercial data or work product. No supplier receives unrestricted contractor-office access. Contractor costing/margins never supplier-visible. Share unit = issued Supplier Package. Website may link to one application login. |
| Architectural decision | [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). One `User`; principal classes CONTRACTOR vs SUPPLIER; SupplierUserMembership separate from `UserMembership`; V1 dual-hat fails closed; not office RBAC; not a 12th V1 package. ADR-008 remains **Proposed**. |
| Prompt template used | Joel/ChatGPT define-and-govern brief (9 Sep 2026) |
| Approved Cursor prompt summary | Record FG-030 + ADR-047; no product code; no migration; do not live-migrate FG-029; do not install FG-028 Slice 3; do not rescore V1 |
| Files expected to change | Governance/current-authority docs only |
| Files prohibited from changing | `app/`; `migrations/`; tests; live DB; website source; logos |
| Implementation result | Docs recorded. FG-030 **NOT IMPLEMENTATION-AUTHORIZED**. **NOT IMPLEMENTED**. V1 remains **45% / 2 of 11**. |
| Tests | **NOT RERUN** (docs-only). Historical FG-029 dedicated **16** / governed **210** / full **677**. |
| Project-state-report update | Yes |
| Milestone entry update | No (not a completed coded milestone) |
| Constitutional issue raised | None |
| Unresolved issues | FG-030 implementation not authorized. FG-029 live-migrate / UAT not authorized from this recording. FG-028 Slice 3 installation pending. Website **EXTERNAL**. |
| Next approved step | **STOP.** Return to ChatGPT Architect. Next product action is FG-029 live migration + bounded BMR demo UAT after Joel’s explicit live-migrate authorization. Do **not** implement FG-030 from this recording. |
| Next approved prompt | FG-029 live migration + bounded BMR demo office UAT (execute only after Joel explicitly authorizes). |
| Commit hash | uncommitted docs at this recording |

### 2026-09-09 — FG-028 Slice 3 asset received (installation pending)

| Field | Content |
|-------|---------|
| Date | 2026-09-09 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Record Joel-approved CalibraytAI final logo package. No Slice 3 installation. No FG-029 live migrate from this prompt. |
| Business decision | Package `CalibraytAI_090926_Final.zip` is FINAL. V1 for dark/navy (white Calibrayt + gold Ai). V2 for light/white (navy Calibrayt + gold Ai). AI/EPS/JPG/PDF/PNG/PSD/SVG. Do not redesign/regenerate/recolour/retype/reconstruct or change emblem, proportions, or PLAN • PRICE • BUILD lockup. |
| Architectural decision | FG-028 Slice 3 = **ASSET RECEIVED / JOEL APPROVED / INSTALLATION PENDING / NOT CLOSED**. Do **not** install during FG-029 live migration / UAT. Installation is next after FG-029 reconciliation under a separate prompt. |
| Prompt template used | FG-028 Slice 3 asset status update (9 Sep 2026) |
| Approved Cursor prompt summary | Record asset received; do not install; do not live-migrate FG-029 from this prompt; return control after recording |
| Files expected to change | Governance/current-authority docs only |
| Files prohibited from changing | `app/`; `app/static/branding/`; migrations; tests; live DB; FG-029 product code; website |
| Implementation result | Docs recorded. Zip listed/hashed **outside Git**. **Not extracted into the app.** FG-028 **NOT CLOSED**. V1 remains **45% / 2 of 11**. |
| Tests | **NOT RERUN** (docs-only status; no product defect). Historical FG-028 dedicated **9** / focused **117** / full **661**. Historical FG-029 dedicated **16** / governed **210** / full **677**. |
| Project-state-report update | Yes |
| Milestone entry update | No (gate not closed; not a completed milestone) |
| Constitutional issue raised | None |
| Unresolved issues | Slice 3 installation pending. FG-029 live-migrate / UAT not authorized from this recording. Website **EXTERNAL / PENDING**. |
| Next approved step | **STOP.** Return to ChatGPT Architect. Next product action is FG-029 live migration + bounded BMR demo UAT after Joel’s explicit live-migrate authorization. Do **not** install Slice 3 during that UAT. |
| Next approved prompt | FG-029 live migration + bounded BMR demo office UAT (execute only after Joel explicitly authorizes). |
| Commit hash | uncommitted docs at this recording |

### 2026-09-09 — FG-029 V1-03 BMR / supplier workflow product implementation

| Field | Content |
|-------|---------|
| Date | 2026-09-09 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Resume and complete authorized FG-029 product implementation from interrupted WIP |
| Business decision | CanonicalMaterial → thin MaterialRequirement → human mapping → Supplier/SKU → inform-only evidence → frozen Supplier Package HTML+PDF. No live BMR. No live migrate. No UAT. |
| Architectural decision | [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. ADR-008 remains **Proposed**. Supplier price INFORM ONLY. |
| Prompt template used | Authorized FG-029 resume implementation package (9 Sep 2026) |
| Approved Cursor prompt summary | Resume FG-029; preserve interrupted working tree; one additive migration file `b6c7d8e9f0a1`; tests; commit/push; no live migrate; no live DEMO BMR seed |
| Files expected to change | models/services/routes/templates/tests/migration `b6c7d8e9f0a1`; FG-029 / V1 / current-authority docs |
| Files prohibited from changing | live DB; live DEMO seed; ADR-008 acceptance; FG-028 Slice 3; FG-024; LEARN; PO/API |
| Implementation result | FG-029 **IMPLEMENTED / TESTED / COMMITTED / PUSHED**. **NOT LIVE-MIGRATED.** **UAT NOT AUTHORIZED.** **NOT CLOSED.** V1 remains **45% / 2 of 11**. |
| Tests | A dedicated FG-029 **16 passed**. B Material Catalogue **35 passed**. C Estimating+FG-026+FG-027 **62 passed**. D output/PDF **41 passed**. E tenancy **56 passed**. F governed bundle **210 passed**. G full suite **677 passed**. Historical full **661** is the pre-FG-029 product-changing baseline. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Live migrate + UAT not authorized. Live DEMO BMR seed not populated. V1-03 not COMPLETE. FG-028 Slice 3 pending. |
| Next approved step | **STOP.** Return to ChatGPT Architect. Do **not** live-migrate. Do **not** populate live DEMO BMR data. Do **not** begin another V1 package. |
| Next approved prompt | None until Joel/ChatGPT authorize live-migrate/UAT or FG-028 Slice 3. |
| Commit hash | Product **`ee578dcb5a688842ebedaff0682131826e6c7188`**. Pin follows. |

### 2026-09-09 — FG-029 V1-03 BMR / supplier workflow architecture recording

| Field | Content |
|-------|---------|
| Date | 2026-09-09 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Docs-only ADR-046 + FG-029 + V1-03 preflight. No product implementation. |
| Business decision | Smallest honest BMR demo: CanonicalMaterial → thin MaterialRequirement → human DEMO Winchester mapping → inform-only evidence → frozen Supplier Package HTML+PDF. No live BMR. No lumber take-off. |
| Architectural decision | [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. ADR-008 remains **Proposed**. Supplier price INFORM ONLY. |
| Prompt template used | Authorized V1-03 ADR + FG governance recording (9 Sep 2026) |
| Approved Cursor prompt summary | ADR-046 + FG-029 + preflight docs only; commit/push; no schema; no V1 rescore |
| Files expected to change | ADR/FG/preflight + current-authority indexes |
| Files prohibited from changing | app/; migrations/; tests/; live DB; FG-028 product identity; logos |
| Implementation result | **RECORDED.** FG-029 **NOT IMPLEMENTATION-AUTHORIZED**. V1 remains **45% / 2 of 11**. |
| Tests | **PRODUCT TESTS NOT RERUN — V1-03 ADR / FG / PREFLIGHT ONLY.** |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Implementation authorization; Slice 3 logo; website; apply-to-estimate still needs ADR-008 if ever wanted |
| Next approved step | **STOP.** Return to ChatGPT Architect. Do not implement V1-03. |
| Next approved prompt | None until Joel/ChatGPT authorize FG-029 implementation, Slice 3, or website. |
| Commit hash | Architecture recording **`07039c8dabfeba7b6ef4714d2cee50abf648bc4f`**. Pin follows. |

### 2026-09-09 — FG-028 CalibAi → CalibraytAI product identity Slices 1–2

| Field | Content |
|-------|---------|
| Date | 2026-09-09 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBRAYTAI DEVELOPMENT 9 SEP 2026 |
| Objective | Record ADR-045 / FG-028 / product-identity.md and implement Slices 1–2 (visible product text + current-authority docs). Slice 3 logo held. No V1-03. |
| Business decision | Permanent product name **CalibraytAI**. Former name **CalibAi**. Historical CalibAi remains historical truth. Office chrome Brayman Construction Platform and ORG-001 Brand Profile preserved. |
| Architectural decision | [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. No schema migration. No live DB mutation. Technical identifiers preserved. |
| Prompt template used | Authorized governed product-identity transition Slices 1–2 (9 Sep 2026) |
| Approved Cursor prompt summary | ADR + FG-028 + product-identity.md; Slice 1 visible strings + tests; Slice 2 current authority; Slice 3 held; no V1-03; no migration |
| Files expected to change | Field/Hub/historical/permit/labour visible product strings; tests; current-authority docs; new ADR/FG/product-identity |
| Files prohibited from changing | Alembic; live DB; logos; website; V1 percentages; Brand Profile; office BCP; identifier tokens |
| Implementation result | Slices 1–2 **IMPLEMENTED**. FG-028 **NOT CLOSED** (Slice 3 pending). V1 remains **45% / 2 of 11**. |
| Tests | Dedicated FG-028 **9 passed**. Focused Field/Hub/Permit/Brand/Labour **117 passed**. Full suite **661 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None (product-identity linked; Articles 1–12 not amended) |
| Unresolved issues | Slice 3 Joel-approved lettering asset. Website **EXTERNAL / PENDING**. Field PNG remains Brayman Construction until Slice 3. |
| Next approved step | **STOP.** Do not begin V1-03. Do not install logo until Joel supplies asset. |
| Next approved prompt | None until Joel/ChatGPT authorize Slice 3, website, or V1-03. |
| Commit hash | `e06fa92c4543ae641ba5067b1d277af048d97139` |

### 2026-09-08 — V1-02 / FG-027 bounded office UAT continuation + close

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026 |
| Objective | Resume remaining FG-027 office UAT after the legacy override-provenance repair and close the gate only if remaining UAT PASS |
| Business decision | Joel authorized UAT continuation. Close FG-027 only on PASS. Do not begin V1-03. No new migration. |
| Architectural decision | Unchanged ADR-044. Pre-edit working `unit_cost` freeze for NULL library reference was office-verified. |
| Prompt template used | Authorized V1-02 / FG-027 bounded office UAT continuation after legacy override-provenance repair (8 Sep 2026) |
| Approved Cursor prompt summary | BOUNDED OFFICE UAT CONTINUATION AFTER LEGACY OVERRIDE-PROVENANCE REPAIR; NO NEW MIGRATION; NO FG-027 CLOSE UNLESS UAT PASS; NO V1-03 |
| Files expected to change | Live UAT DB (EstimateVersion 9 / line 7 / costing + pricing snapshots); FG-027 / V1 / current-authority docs if PASS |
| Files prohibited from changing | Alembic revisions; product redesign; V1-03; CalibAi rename; FG-024; FG-025; LEARN |
| Implementation result | Remaining office UAT **PASS**. FG-027 **CLOSED / OPERATIONAL FOR UAT**. V1-02 **COMPLETE**. Readiness **45%**. |
| Tests | Product tests **not** rerun under this prompt. Last verified dedicated FG-027 **20** / full **652**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | V1-03 not authorized; BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO** |
| Next approved step | **STOP.** Return to ChatGPT Architect for V1-03 authorization. |
| Next approved prompt | Not in this pass (STOP / V1-03 authorization). |
| Commit hash | Close SHA **`c348bcfb41daead674aaf75050fc0a6847a8c0c0`**. Pin follows. |

### 2026-09-08 — V1-02 / FG-027 bounded legacy override-provenance repair

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` |
| Active ChatGPT development chat title | BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026 |
| Objective | Bounded FG-027 product repair for legacy NULL `library_unit_cost_reference` override provenance |
| Business decision | Joel authorized repair without a new migration, without live DB write, and without UAT continuation or FG-027 close |
| Architectural decision | Pre-edit working `unit_cost` is the frozen library reference for CostItem/Assembly lines whose `library_unit_cost_reference` is NULL. Do not query today’s library. Do not overwrite a populated reference. |
| Prompt template used | Authorized V1-02 / FG-027 bounded legacy override-provenance defect repair (8 Sep 2026) |
| Approved Cursor prompt summary | BOUNDED LEGACY OVERRIDE-PROVENANCE DEFECT REPAIR; NO NEW MIGRATION; NO UAT CONTINUATION IN THIS PASS |
| Files expected to change | `app/services/estimate_costing.py`; `app/services/estimate_builder.py`; `tests/test_estimate_costing_fg027.py`; FG-027 / V1 / current-authority docs |
| Files prohibited from changing | Alembic revisions; live DB; FG-027 close; V1-03; CalibAi rename; FG-024; FG-025; LEARN |
| Implementation result | Defect **REPAIRED / TESTED / COMMITTED / PUSHED**. FG-027 remains **LIVE-MIGRATED / OFFICE UAT STOPPED / NOT PASS / NOT CLOSED**. V1 readiness remains **39%**. |
| Tests | A dedicated FG-027 **20 passed**. B estimating focused **29 passed**. C pricing focused **52 passed**. D FG-026 **20 passed**. E governed A–D bundle **121 passed**. F full suite **652 passed**. Historical dedicated **15** / full **647** remain the pre-repair baseline. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Office UAT continuation; live line 7 residue (working 250 / NULL reference); FG-027 close; remaining costing/pricing UAT |
| Next approved step | **STOP.** Return to ChatGPT Architect for UAT-continuation authorization. |
| Next approved prompt | Not in this pass. |
| Commit hash | Product **`72949f99da2b56ec06e95e16e29fa194a6730bbd`**. Docs **`020bb55cfb87222ed6dfb1b6fd6770f3b0e3b6be`**. |

### 2026-09-08 — V1-02 / FG-027 live migration and office UAT stop

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` @ `b944436136d0bafb198b27c401b79792d076ef16` (start) |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026** |
| Objective | Live-migrate additive `a5b6c7d8e9f0` and run bounded office UAT of costing approval on EstimateVersion 9 |
| Business decision | Joel authorized live migrate + bounded office UAT. Do not re-implement. Do not silently repair defects. Close only if all UAT criteria PASS. |
| Architectural decision | Unchanged ADR-044. UAT stopped because pre-FG-027 line 7 has NULL `library_unit_cost_reference`, so a working-cost change is not classified as MANUAL_OVERRIDE. |
| Prompt template used | Authorized V1-02 / FG-027 live migration + bounded office UAT package (8 Sep 2026) |
| Approved Cursor prompt summary | Backup live DB; upgrade `a5b6c7d8e9f0`; office UAT BLOCK → override → Approve All → Pricing → recost → stale → re-apply. Do not begin V1-03. |
| Files expected to change | Governance/current-authority docs only if UAT complete; this recording is live-migrate PASS / UAT STOP |
| Files prohibited from changing | Product code; silent defect repair; V1-03 / ADR-008 / FG-024 / another FG-025 slice / LEARN |
| Implementation result | Live upgrade **PASS**. Office UAT **STOPPED / NOT PASS**. Gate **NOT CLOSED**. V1-02 remains **PARTIAL** 0.40. Readiness **39%**. |
| Tests | Product tests **NOT RERUN**. Historical dedicated FG-027 **15** / full **647**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Override provenance on pre-FG-027 EstimateLineItem rows. Remaining costing/pricing UAT not run. |
| Next approved step | **STOP.** Return defect to ChatGPT Architect. Do **not** silently repair. Do **not** begin V1-03. |
| Next approved prompt | **None** — HOLD pending defect-repair authorization. |
| Commit hash | `3bf832b2fea5e1ade8c3e412dc7635a4a15c42b1` |

### 2026-09-08 — V1-02 / FG-027 costing-approval product implementation

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` @ `28fb5c0445fafabb2924d5d43bce46bf5fca3d0e` (start) |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026** |
| Objective | Implement FG-027 Automated Costing + Human Cost Approval V1 |
| Business decision | Joel authorized the FG-027 implementation package. Approve All = costing approval only. Live migrate and UAT not authorized. |
| Architectural decision | Estimating-owned `EstimateCostingSnapshot` + frozen line facts. Pricing consumes CURRENT frozen total and fails closed without it. Recost supersedes on the same Draft. Locked/Issued cannot recost. Labour snapshot remains out of basis. ADR-008 remains Proposed. |
| Prompt template used | Authorized V1-02 / FG-027 implementation package (8 Sep 2026) |
| Approved Cursor prompt summary | AUTOMATED COSTING + HUMAN COST APPROVAL V1. One additive migration file `a5b6c7d8e9f0`. Do not live migrate. Do not UAT. Do not begin V1-03. |
| Files expected to change | `app/models/estimate_costing.py`; `app/services/estimate_costing.py`; estimate builder/routes/templates; pricing consume; migration `a5b6c7d8e9f0`; tests; FG-027 / V1 / current-authority docs |
| Files prohibited from changing | Live DB; UAT data; V1-03 / ADR-008 / FG-024 / another FG-025 slice / LEARN / QuickBooks / contracts |
| Implementation result | FG-027 **IMPLEMENTED / TESTED / COMMITTED / PUSHED**. **NOT LIVE-MIGRATED.** **UAT NOT AUTHORIZED.** V1 readiness remains **39%** (V1-02 PARTIAL 0.40). |
| Tests | A dedicated FG-027 **15 passed**. B estimating focused **29 passed**. C pricing focused **52 passed**. D labour/material **60 passed**. E FG-026 **20 passed**. F governed bundle **176 passed**. G full suite **647 passed**. Historical full **632** is the pre-FG-027 baseline. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Live migrate + office UAT not authorized. V1-03 not started. |
| Next approved step | **STOP.** Return to ChatGPT Architect. Do **not** live-migrate. Do **not** UAT. Do **not** begin V1-03. |
| Next approved prompt | **None** — HOLD pending live-migrate / UAT authorization. |
| Commit hash | `c751d72b32f1ed415375719df2fd69936ace64d7` |

### 2026-09-08 — V1-02 / FG-027 costing-approval ADR, Feature Gate, and architecture preflight

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` @ `bacb5abf574b3dfe30bda4b6d6015026a3946607` (start) |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026** |
| Objective | Docs-only memorialization of V1-02 Automated Costing + Human Cost Approval architecture: one ADR, one Feature Gate, one preflight, minimum current-authority updates |
| Business decision | Approve All means costing approval only. Human costing approval is mandatory before governed Pricing. Labour snapshots remain out of default pricing basis. Supplier evidence is not required. Zero/missing CostItem/Assembly commercial cost BLOCKS. Manual Custom/Allowance WARN if a valid cost is entered. Recost = new immutable costing snapshot on the same Draft EstimateVersion. Pricing becomes STALE after recost. Locked/Issued cannot recost. |
| Architectural decision | [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. Estimating owns costing approval/snapshots. Pricing Engine consumes. Labour Engine retains EstimateLabourSnapshot. Do not use EstimatePricingSnapshot as the costing record. Relational snapshot header + line rows; JSON only for advisory warnings. Proposed later Alembic `a5b6c7d8e9f0` down_revision `f4a5b6c7d8e9` — not created. ADR-008 remains Proposed. |
| Prompt template used | Authorized V1-02 ADR + Feature Gate + architecture preflight prompt (governance / documentation only) |
| Approved Cursor prompt summary | Create next unused ADR and Feature Gate; write preflight; update minimum governance docs; no product code, schema, migration, live DB, or costing implementation |
| Files expected to change | `docs/adr/ADR-044-*.md`; `docs/feature-gates/FG-027-*.md`; `docs/architecture/fg-027-costing-approval-preflight.md`; ADR/FG READMEs; V1 register; current-state; session-handoff; project-state-report; platform-roadmap; chat-workflow-log; milestones; estimating/pricing-engine modules; architecture.md; docs/README.md; CAR-001 subsequent status; FG-026 subsequent note |
| Files prohibited from changing | `app/**`; `migrations/**`; tests; live DB; Feature Gate implementation |
| Implementation result | ADR-044 **Accepted**. FG-027 **RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. V1 readiness remains **39%** (V1-02 stays PARTIAL 0.40). No product code. |
| Tests | `git diff --check`. **PRODUCT TESTS NOT RERUN — V1-02 ADR / FEATURE GATE / PREFLIGHT ONLY.** Last product-changing full suite remains **632 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | FG-027 product implementation not authorized. Remaining V1 register §13 decisions except #2. |
| Next approved step | **STOP.** Return to ChatGPT Architect. Do **not** implement FG-027. |
| Next approved prompt | **None** — HOLD. Do not implement V1-02. |
| Commit hash | `076e12f022fa5248a34e7baf7d05ae51e9e0ac4b` |

### 2026-09-08 — FG-026 live migration and office UAT close

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026** |
| Objective | Execute authorized FG-026 live `flask db upgrade` to `f4a5b6c7d8e9` and bounded project-3 office UAT. Close the gate if acceptance passes. |
| Business decision | Joel authorized the previously HOLDed live-migrate + UAT prompt. V1-02 remains unauthorized. |
| Architectural decision | No product-code change. Additive live apply only. Estimating-owned insertion/citation remains. No automatic pricing/labour/supplier/MaterialRequirement. |
| Prompt template used | `docs/prompts/cursor-feature-template.md` (live migrate + bounded UAT). |
| Approved Cursor prompt summary | FG-026 LIVE MIGRATE + BOUNDED UAT (8 Sep 2026). V1-02 / Approve All Costing / V1-03 / FG-024 / another FG-025 slice not authorized. |
| Files expected to change | `docs/` current-authority pins, FG-026 close, V1 register scoring, milestones, chat-workflow-log. |
| Files prohibited from changing | Product code; tests; `migrations/`; V1-02 costing; supplier/BMR; FG-024; another FG-025 slice; LEARN; QuickBooks; contracts; Native Signing; Observation Delete; new Permit/Field. |
| Implementation result | Live upgrade `e3f4a5b6c7d8` → `f4a5b6c7d8e9` **PASS**. Office UAT **PASS** on port **5015**. Gate **CLOSED / OPERATIONAL FOR UAT**. V1-01 **COMPLETE**. Readiness **38.85 → 39%**. |
| Tests | PRODUCT TESTS NOT RERUN — live-migrate / UAT / governance close only. Historical implementation evidence remains dedicated **20** / full **632**. |
| Project-state-report update | Yes. |
| Milestone entry update | Yes. |
| Constitutional issue raised | None. |
| Unresolved issues | V1-02 costing not authorized. Hub PLAN leftover “mapping is not started” copy is remaining FG-025 surface / not this gate. |
| Next approved step | **STOP.** Return to ChatGPT Architect. Do **not** begin V1-02. |
| Next approved prompt | HOLD — do not begin V1-02. |
| Commit hash | `20d23b0103ee729e1d9770feeddfa7f8754e8804` |

### 2026-09-08 — FG-026 takeoff-to-estimate mapping V1 implementation

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026** |
| Objective | Implement FG-026 PLAN → PRICE Phase D takeoff-to-estimate mapping V1. |
| Business decision | Explicit human insert only. Package approval does not insert. No live migrate. UAT not run. |
| Architectural decision | Estimating-owned `TakeoffEstimateInsertion` + citations. Atomic line+provenance. Uncommitted builder helpers. UNIQUE grouping + client_insertion_key. No labour/pricing snapshot. No MaterialRequirement. |
| Prompt template used | `docs/prompts/cursor-feature-template.md` (implementation package). |
| Approved Cursor prompt summary | V1-01 / FG-026 PLAN → PRICE Phase D takeoff-to-estimate mapping V1 implementation package (8 Sep 2026). Live migrate/UAT not authorized. |
| Files expected to change | Estimating models/service, estimate_builder helpers, Plan Intelligence map routes/templates, one Alembic revision, dedicated tests, current-authority docs. |
| Files prohibited from changing | Live DB; V1-02 costing; supplier/BMR; FG-024; another FG-025 slice; LEARN; QuickBooks; contracts; Native Signing; Observation Delete; new Permit/Field. |
| Implementation result | Product implemented in Git. Migration file `f4a5b6c7d8e9` not applied live. Gate not closed. |
| Tests | Dedicated FG-026 **20 passed**. PLAN takeoff **18 passed**. Estimating/builder **22 passed**. Pricing/labour/material **93 passed**. Governed bundle **172 passed**. Full suite **632 passed**. Historical full **612** is the pre-FG-026 baseline. |
| Project-state-report update | Yes. |
| Milestone entry update | Yes. |
| Constitutional issue raised | None. |
| Unresolved issues | Live migrate. Bounded UAT on project 3 (no estimate today — not a defect). Human-created door Assembly still required for UAT. |
| Next approved step | **STOP.** Return to ChatGPT Architect for live-migrate / UAT authorization. |
| Next approved prompt | HOLD — live migrate / UAT not authorized. |
| Commit hash | `aa4c71800586e0b8e2a63931bcdc8bc44d87a489` |

### 2026-09-08 — CalibAi V1 completion register

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026** |
| Objective | Establish the authoritative CalibAi V1 definition and measurable V1 completion register. Docs/governance only. |
| Business decision | V1 means BMR DEMO READY **and** BRAYMAN REAL-LIFE UAT READY. Brayman Construction is the first real-life UAT organization. Initial readiness **30%**. **0 / 11** major packages COMPLETE. Neither readiness flag is YES. |
| Architectural decision | One canonical register at `docs/v1-completion-register.md`. Feature Gates remain implementation governance. LEARN V1 = evidence capture, not ML. QuickBooks V1 recommended as output/entry (not live API) pending Joel. FG-024 Slice D live monitoring recommended POST-V1; 06H versioning remains V1. FG-026 and FG-024 remain **NOT IMPLEMENTATION-AUTHORIZED**. |
| Prompt template used | `docs/prompts/cursor-documentation-template.md` (docs/governance only). |
| Approved Cursor prompt summary | V1 COMPLETION REGISTER — AUTHORITATIVE V1 DEFINITION + REPOSITORY GAP RECONCILIATION. No product implementation. |
| Files expected to change | `docs/` only (register + indexes + current-authority pins). |
| Files prohibited from changing | Product code; tests; `migrations/`; live DB; `app/`. |
| Implementation result | Register recorded. Cross-pins updated. No product code. No migration. No live DB writes. |
| Tests | `git diff --check`. PRODUCT TESTS NOT RERUN — V1 GOVERNANCE / GAP RECONCILIATION ONLY. |
| Project-state-report update | Yes — V1 register governing; readiness 30%. |
| Milestone entry update | Yes — V1 register recorded. |
| Constitutional issue raised | None. |
| Unresolved issues | Seven Joel decisions in register §13. FG-026/FG-024 not implemented. Remaining FG-025 surfaces unauthorized. |
| Next approved step | **STOP.** Do **not** implement FG-026. Do **not** implement FG-024. Do **not** start another FG-025 slice. Do **not** start LEARN. |
| Next approved prompt | None authorized. Return control to ChatGPT Architect. |
| Commit hash | (this V1 register docs commit) |

### 2026-09-08 — FG-026 takeoff-to-estimate mapping preflight

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026** |
| Objective | Record FG-026 Feature Gate and architecture preflight for PLAN → PRICE Phase D takeoff-to-estimate mapping V1. Docs/governance only. |
| Business decision | FG-026 **RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Recording is **not** implementation approval. Remaining FG-025 surfaces remain **NOT AUTHORIZED**. FG-023 remains **CLOSED**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. |
| Architectural decision | PLAN proposes; Estimating commits. Package approval does not insert. Map only to existing org Assembly or CostItem. Insert only into existing editable Draft EstimateVersion on the same Project. Four quantity layers stay distinct. One commercial line per package element grouping with many frozen citations. No new ADR. Later implementation would require an additive Estimating-owned insertion/citation migration. MaterialRequirement, labour-from-takeoff, automatic pricing, and PlanMeasurement are out of V1. |
| Prompt template used | `docs/prompts/cursor-documentation-template.md` (docs/governance only). |
| Approved Cursor prompt summary | FG-026 PLAN → PRICE Phase D takeoff-to-estimate mapping V1 Feature Gate + architecture preflight. No product implementation. |
| Files expected to change | `docs/` only (FG-026 gate, preflight, indexes, current-state, session-handoff, PSR, milestones, chat-workflow-log, roadmap, module pins). |
| Files prohibited from changing | Product code; tests; `migrations/`; live DB; `app/`. |
| Implementation result | Gate and preflight recorded. Current-authority pins updated. No product code. No migration. No live DB writes. |
| Tests | `git diff --check`. PRODUCT TESTS NOT RERUN — FEATURE GATE / ARCHITECTURE PREFLIGHT ONLY. Historical Slice 5 full suite **612** remains the last product-changing evidence. |
| Project-state-report update | Yes — FG-026 recorded / not implementation-authorized. |
| Milestone entry update | Yes — FG-026 preflight recorded. |
| Constitutional issue raised | None. Insertion-audit ownership stays with Estimating (ADR-006/007). |
| Unresolved issues | FG-026 not implemented. Implementation requires a separate prompt. Remaining FG-025 surfaces unauthorized. Observation Delete still QUEUED. SESSION-EXPIRY RECOVERY still DEFERRED. |
| Next approved step | **STOP.** Do **not** implement FG-026 from this recording. Do **not** start another FG-025 slice. Do **not** start FG-024. Do **not** start LEARN. |
| Next approved prompt | None authorized. Return control to ChatGPT Architect. |
| Commit hash | (this FG-026 docs commit) |

### 2026-09-08 — FG-025 Slice 5 Review Turnover

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026** |
| Objective | Complete Review Turnover with full repo review. Docs-only. Pin Slice 5 product SHA. Repair current-authority contradictions. Produce Fresh Chat Startup Prompt. |
| Business decision | Substantive development **STOP**. FG-025 Slice 5 remains **IMPLEMENTED / NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. FG-023 remains **CLOSED**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. |
| Architectural decision | No product, test, migration, or DB change. Pin product SHA **`5b497905086554214e85f69afd8101d88f89161c`**. Preserve historical Slice 1–4 stop-lines. This turnover commit is **not** the Slice 5 product SHA. |
| Prompt template used | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) Phase 2. |
| Approved Cursor prompt summary | Cursor chat refresh / complete turnover with full repo review. Docs only. No Slice 6. No FG-024. No LEARN. |
| Files expected to change | Current-authority docs: session-handoff, current-state, PSR, milestones, chat-workflow-log, FG-025, CAR-001, roadmap, feature-gates README. |
| Files prohibited from changing | Product code; tests; `migrations/`; live DB; CSS. |
| Implementation result | Slice 5 SHA pinned. Stale §3 ADR-021, §19 Slice 5 stop, §22 2026-09-07 prompt, durable-storage A–J, and roadmap “Do not start Slice 5” repaired. Completeness test **NO**. TURNOVER PASS. |
| Tests | Dedicated FG-025 reconfirmed this pass: `./venv/bin/python -m pytest -q tests/test_fg025_contractor_copy.py` → **19 passed**. Full suite **not** rerun this turnover; cite Slice 5 product SHA run **612 passed**. |
| Project-state-report update | Yes — turnover recorded; product SHA pinned. |
| Milestone entry update | Yes — turnover recorded. |
| Constitutional issue raised | None. |
| Unresolved issues | Remaining FG-025 surfaces unauthorized. Observation Delete still QUEUED. SESSION-EXPIRY RECOVERY still DEFERRED. |
| Next approved step | **STOP.** Start a fresh chat from the Fresh Chat Startup Prompt. Do **not** start another FG-025 slice. Do **not** start FG-024. Do **not** start LEARN. |
| Next approved prompt | None authorized. Fresh Chat Startup Prompt is resume-only. |
| Commit hash | (this Review Turnover docs commit) |

### 2026-09-08 — FG-025 Slice 5 contractor-facing Field Web language

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026** |
| Objective | Implement FG-025 Slice 5 only: contractor-facing language on existing Field Web. |
| Business decision | Slice 5 **AUTHORIZED AND IMPLEMENTED**. Field header **Sign out**. Today **Change project** / **Not sent yet**. Capture **Notes** with **Save original** preserved. Visible save status **Saved** / **Saving…** / **Could not send**. FG-025 overall **NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. FG-023 remains **CLOSED**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. |
| Architectural decision | Reuse Slice 1–4 `app/presentation/contractor_copy.py`. Do not create a competing copy system. Do not rename models, enums, routes, or schema. No Field workflow, media pipeline, Observation Delete, or session-revocation change. |
| Prompt template used | `docs/prompts/cursor-implementation-template.md` does **not** exist. Followed AGENTS.md and the bounded Slice 5 prompt. |
| Approved Cursor prompt summary | FG-025 Slice 5 only. Field Web copy. No schema/migration/DB. No Slice 6. No FG-024. No LEARN. No website. |
| Files expected to change | Field templates; `app/static/js/field.js` visible strings; `app/presentation/contractor_copy.py`; FG-025 tests; FG-021 copy assertion; current-authority docs. |
| Files prohibited from changing | `migrations/`; models/enums except read-only; office UI rewrite; customer PDF; MONITOR arithmetic; LEARN; website; CSS; FG-024. |
| Implementation result | Field Log out → Sign out. Switch Project → Change project. Short text → Notes. Visible ALL_CAPS save status mapped. Save original preserved. Live current `e3f4a5b6c7d8`. Live **39** / **39**. Project **13** five actuals unchanged. |
| Tests | Dedicated: `./venv/bin/python -m pytest -q tests/test_fg025_contractor_copy.py` → **19 passed**. Field-focused (FG-025 + both FG-020 + FG-021) **83 passed**. Governed (prompt list) **190 passed**. Full `./venv/bin/python -m pytest -q` → **612 passed**. |
| Project-state-report update | Yes — Slice 5 implemented / not closed; remaining surfaces not authorized. |
| Milestone entry update | Yes — Slice 5 recorded. |
| Constitutional issue raised | None. |
| Unresolved issues | Remaining FG-025 surfaces unauthorized (customer PDF, Historical Evidence, standalone Permit, Hub PRICE TRUE_GROSS_MARGIN, final sweep). Observation Delete still QUEUED. |
| Next approved step | **STOP.** Do **not** start another FG-025 slice. Do **not** start FG-024. Do **not** start LEARN. Do **not** restart website work. |
| Next approved prompt | None authorized. |
| Commit hash | `5b497905086554214e85f69afd8101d88f89161c` |

### 2026-09-08 — FG-025 Slice 4 post-close documentation reconciliation

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026** |
| Objective | Docs-only reconciliation of Slice 4 close-review documentation-hygiene findings. |
| Business decision | Slice 4 remains **PASS — MINOR DOCUMENTATION NOTE ONLY**. Product SHA stays **`56e16f03446f982d577d2a3f0d3375ef865e1dc9`**. This commit is **not** the Slice 4 product SHA. FG-025 overall **NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. |
| Architectural decision | No product, test, migration, or DB change. Pin Slice 4 product SHA. Expand current-authority remaining-surface inventory. Preserve historical Slice 1–4 stop-lines. Distinguish **REVIEW / DECISION REQUIRED** from unauthorized candidate surfaces. |
| Prompt template used | Bounded Joel/ChatGPT post-close documentation reconciliation prompt. |
| Approved Cursor prompt summary | Pin Slice 4 product SHA `56e16f0…`; reconcile current-state/PSR/handoff HEAD; complete remaining-surface inventory with REVIEW/DECISION vs unauthorized-candidate distinction. Docs only. Commit + push. No Slice 5. |
| Files expected to change | Current-authority docs only. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live DB; website. |
| Implementation result | Slice 4 product SHA pinned. Remaining-surface inventory expanded in current-state, PSR, session-handoff, and FG-025. CAR-001 Slice 4 subsequent-status now pins product SHA. Live current `e3f4a5b6c7d8`. Live **39** / **39**. |
| Tests | Not rerun (docs-only). Preserved Slice 4 evidence: dedicated **16**; Slice-4 focused **114**; governed **226**; full **609**. Independent close review reran dedicated **16** and Slice-4 focused **114**; governed and full **not** independently rerun. |
| Project-state-report update | Yes — Slice 4 product SHA pinned; docs-only reconciliation distinguished. |
| Milestone entry update | Yes — Slice 4 product SHA pinned; docs-reconciliation recorded. |
| Constitutional issue raised | None. |
| Unresolved issues | Remaining FG-025 surfaces unauthorized. Slice 5 not authorized. |
| Next approved step | **STOP.** Do **not** start Slice 5. Do **not** start FG-024. Do **not** start LEARN. Do **not** restart website work. |
| Next approved prompt | None authorized. |
| Commit hash | this docs-only reconciliation commit (not Slice 4 product SHA `56e16f03446f982d577d2a3f0d3375ef865e1dc9`) |

### 2026-09-08 — FG-025 Slice 4 contractor-facing office language

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026** |
| Objective | Implement FG-025 Slice 4 only: contractor-facing language on shared OFFICE shell, navigation, dashboard, authentication, and Settings / Brand Profile. |
| Business decision | Slice 4 **AUTHORIZED AND IMPLEMENTED**. Global nav **Labour rates** / **Pricing**. Dashboard **Office home**. Login **Sign in with your email and password.** Header **Sign out**. Settings **Brand profile**. FG-025 overall **NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. FG-023 remains **CLOSED**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. |
| Architectural decision | Reuse Slice 1–3 `app/presentation/contractor_copy.py`. Do not create a competing copy system. Do not rename routes, blueprints, enums, or schema. No auth/session/Settings behavior change. No Field Web / PDF / MONITOR / pricing / labour arithmetic change. |
| Prompt template used | `docs/prompts/cursor-implementation-template.md` does **not** exist. Followed AGENTS.md and the bounded Slice 4 prompt. |
| Approved Cursor prompt summary | FG-025 Slice 4 only. Shared office nav/dashboard/auth/Settings copy. No schema/migration/DB. No Slice 5. No FG-024. No LEARN. No website. |
| Files expected to change | `app/presentation/contractor_copy.py`; `app/navigation.py`; office templates for login, base, dashboard, brand profile; FG-025 tests; current-authority docs. |
| Files prohibited from changing | `migrations/`; models/enums except read-only; Field Web; customer PDF; MONITOR arithmetic; LEARN; website; FG-024. |
| Implementation result | Nav titles mapped to Slice 3 page names. Dashboard heading/lede and status labels. Login lede + Sign out. Brand profile heading/lede; MB helper. Routes/endpoints/auth/Settings values unchanged. Field Web still **Log out**. Live current `e3f4a5b6c7d8`. Live **39** / **39**. Project **13** five actuals unchanged. |
| Tests | Dedicated: `./venv/bin/python -m pytest -q tests/test_fg025_contractor_copy.py` → **16 passed**. Slice-4 focused (FG-025 + auth FG-018 + Brand Profile + organization foundation + change orders + proposals) **114 passed**. Governed (required FG-023/Hub/auth/FG-020/FG-021 plus Slice 4 affected files) **226 passed**. Full `./venv/bin/python -m pytest -q` → **609 passed**. |
| Project-state-report update | Yes — Slice 4 implemented / not closed; remaining surfaces not authorized. |
| Milestone entry update | Yes — Slice 4 recorded. |
| Constitutional issue raised | None. |
| Unresolved issues | Remaining FG-025 surfaces unauthorized (Field Web, customer PDF, Historical Evidence nav, standalone Permit screens). Header disabled **Settings (coming soon)** left frozen (FG-017). “Contract value” still flagged G. Slice 5 not authorized. |
| Next approved step | **STOP.** Do **not** start Slice 5. Do **not** start FG-024. Do **not** start LEARN. Do **not** restart website work. |
| Next approved prompt | None authorized. |
| Commit hash | `56e16f03446f982d577d2a3f0d3375ef865e1dc9` (`feat: continue FG-025 contractor-facing office language`) |

### 2026-09-08 — FG-025 Slice 3 post-close documentation reconciliation

| Field | Content |
|-------|---------|
| Date | 2026-09-08 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 8 SEP 2026** |
| Objective | Docs-only reconciliation of three Slice 3 close-review documentation-hygiene findings. |
| Business decision | Slice 3 remains **PASS — MINOR DOCUMENTATION NOTE ONLY**. Product SHA stays **`071f5f923515c6405298bf96b0af249a20f81358`**. This commit is **not** the Slice 3 product SHA. FG-025 overall **NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. |
| Architectural decision | No product, test, migration, or DB change. Preserve CAR-001 chronological subsequent-status. Restore FG-025 Slice 2 historical stop-line from parent `1aa54f51dcd2447ce6934dddbf5305c81016a824`. |
| Prompt template used | Bounded Joel/ChatGPT post-close documentation reconciliation prompt. |
| Approved Cursor prompt summary | Pin Slice 3 product SHA; reconcile current-state/handoff confirm-HEAD wording; restore CAR-001 Slice 2 subsequent-status and append Slice 3; restore FG-025 Slice 2 historical wording from parent if exact. Docs only. Commit + push. No Slice 4. |
| Files expected to change | Current-authority docs only. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live DB; website. |
| Implementation result | Placeholders pinned. CAR-001 Slice 2 paragraph restored and Slice 3 paragraph appended. FG-025 Slice 2 stop-line restored to **Do not start Slice 3 from this section.** Live current `e3f4a5b6c7d8`. Live **39** / **39**. |
| Tests | Not rerun (docs-only). Preserved Slice 3 evidence: dedicated **13**; PRICE-focused **167**; governed **303**; full **606**. Independent close review reran dedicated **13** and PRICE-focused **167**; governed and full **not** independently rerun. |
| Project-state-report update | Yes — Slice 3 product SHA pinned; docs-only reconciliation distinguished. |
| Milestone entry update | Yes — Slice 3 product SHA pinned; docs-reconciliation recorded. |
| Constitutional issue raised | None. |
| Unresolved issues | Remaining FG-025 surfaces unauthorized. Slice 1/Slice 2 chat-workflow-log and milestones commit placeholders left unchanged (historical; not this prompt). |
| Next approved step | **STOP.** Do **not** start Slice 4. Do **not** start FG-024. Do **not** start LEARN. Do **not** restart website work. |
| Next approved prompt | None authorized. |
| Commit hash | this docs-only reconciliation commit (not Slice 3 product SHA `071f5f923515c6405298bf96b0af249a20f81358`) |

### 2026-09-07 — FG-025 Slice 3 contractor-facing PRICE language

| Field | Content |
|-------|---------|
| Date | 2026-09-07 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 7 SEP 2026** |
| Objective | Implement FG-025 Slice 3 only: contractor-facing language on current office PRICE specialist screens. |
| Business decision | Slice 3 **AUTHORIZED AND IMPLEMENTED**. Office titles **Pricing** / **Labour rates**. Internal `TRUE_GROSS_MARGIN` unchanged; display **Gross Margin Pricing**. FG-025 overall **NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. FG-023 remains **CLOSED**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. |
| Architectural decision | Reuse Slice 1/2 `app/presentation/contractor_copy.py`. Do not create a competing copy system. Do not rename enums/schema. No pricing/labour/estimate arithmetic change. Hub otherwise frozen except PRICE specialist link labels. |
| Prompt template used | `docs/prompts/cursor-implementation-template.md` does **not** exist. Followed AGENTS.md and the bounded Slice 3 prompt. |
| Approved Cursor prompt summary | FG-025 Slice 3 PRICE specialist language only. No schema, migration, calculation change, enum rename, MONITOR, FG-024, LEARN, Field Web, customer PDF, auth/Settings, or navigation-wide sweep. Commit + push after PASS. |
| Files expected to change | `app/presentation/contractor_copy.py`; PRICE office templates; Hub PRICE link labels if needed; `tests/test_fg025_contractor_copy.py`; PRICE HTML assertions; current-authority docs. |
| Files prohibited from changing | `migrations/`; models/enums; MONITOR services; Field Web; PDFs; auth/Settings; `app/navigation.py`; FG-024; live DB. |
| Implementation result | Slice 3 implemented. Hub PRICE links: **Pricing** / **Labour rates**. Live current `e3f4a5b6c7d8`. Live **39** / **39**. Project **13** five actuals unchanged. |
| Tests | Dedicated **13 passed**. PRICE-focused **167 passed**. Governed **303 passed**. Full **606 passed**. Manual PRICE review **PASS**. `git diff --check` PASS. |
| Project-state-report update | Yes — FG-025 Slice 3 implemented / not closed. |
| Milestone entry update | Yes — Slice 3 recorded. |
| Constitutional issue raised | None. Global nav still Labour Engine / Pricing Engine (Slice 4). Hub PRICE table leftover `TRUE_GROSS_MARGIN` left frozen except link labels. |
| Unresolved issues | Remaining FG-025 surfaces unauthorized. “Contract value” still flagged. |
| Next approved step | **STOP.** Do **not** start Slice 4. Do **not** start FG-024. Do **not** start LEARN. |
| Next approved prompt | None authorized. |
| Commit hash | `071f5f923515c6405298bf96b0af249a20f81358` (`feat: continue FG-025 contractor-facing PRICE language`) |

### 2026-09-07 — FG-025 Slice 2 contractor-facing Project Hub language

| Field | Content |
|-------|---------|
| Date | 2026-09-07 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 7 SEP 2026** |
| Objective | Implement FG-025 Slice 2 only: contractor-facing language on the office Project Hub and its directly embedded PLAN/PRICE/CONTRACT/BUILD/MONITOR project-context copy. |
| Business decision | Slice 2 **AUTHORIZED AND IMPLEMENTED**. Chosen Hub heading **Pricing assumptions**. FG-025 overall **NOT CLOSED**. Remaining slices **NOT AUTHORIZED**. FG-023 remains **CLOSED**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. |
| Architectural decision | Reuse Slice 1 `app/presentation/contractor_copy.py`. Do not create a competing copy system. Do not rename enums/schema. MONITOR identities unchanged. |
| Prompt template used | `docs/prompts/cursor-implementation-template.md` does **not** exist. Followed AGENTS.md and the bounded Slice 2 prompt. |
| Approved Cursor prompt summary | FG-025 Slice 2 Project Hub language only. No schema, migration, MONITOR arithmetic, enum rename, FG-024, LEARN, Field Web, engines, PDF, nav, or product-wide copy sweep. Commit + push after PASS. |
| Files expected to change | `app/presentation/contractor_copy.py`; `app/templates/projects/detail.html`; `tests/test_fg025_contractor_copy.py`; Hub HTML assertions in `tests/test_project_hub.py` / `tests/test_monitor_v1_fg023.py`; current-authority docs. |
| Files prohibited from changing | `migrations/`; models/enums; `app/services/monitor.py`; Field Web; labour/pricing/nav/PDF; FG-024; live DB. |
| Implementation result | Slice 2 implemented. Extra Hub HTML assertion files: `tests/test_permit_foundation_fg015.py`, `tests/test_organization_foundation.py`. Internal keys preserved. Live current `e3f4a5b6c7d8`. Live **39** / **39**. Project **13** five actuals unchanged. |
| Tests | Dedicated **10 passed**. Focused **159 passed**. Full **603 passed**. Manual Hub review **PASS**. `git diff --check` PASS. |
| Project-state-report update | Yes — FG-025 Slice 2 implemented / not closed. |
| Milestone entry update | Yes — Slice 2 recorded. |
| Constitutional issue raised | None. Extra test files are Hub HTML copy regressions only. |
| Unresolved issues | Remaining FG-025 slices unauthorized. Hub leftovers: Update Context; TRUE_GROSS_MARGIN method name; proposal “immutable”; PASS finding caution; lifecycle ALL_CAPS; form `other_direct` values. “Contract value” still flagged. |
| Next approved step | **STOP.** Do **not** start Slice 3. Do **not** start FG-024. Do **not** start LEARN. |
| Next approved prompt | None authorized. |
| Commit hash | (this product commit) |

### 2026-09-07 — FG-025 Slice 1 Hub MONITOR contractor-facing display mapping

| Field | Content |
|-------|---------|
| Date | 2026-09-07 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 7 SEP 2026** |
| Objective | Implement FG-025 Slice 1 only: presentation-layer mapping for Project Hub `#hub-monitor` and office actuals forms/tables. |
| Business decision | Slice 1 **AUTHORIZED AND IMPLEMENTED**. FG-025 overall **NOT CLOSED**. Remaining slices **NOT AUTHORIZED**. FG-023 remains **CLOSED**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. |
| Architectural decision | Presentation mapping in `app/presentation/contractor_copy.py`. Do not rename enums/schema. MONITOR identities unchanged. Optional Jinja wiring via existing `app/shell.py` UI helper. |
| Prompt template used | `docs/prompts/cursor-implementation-template.md` does **not** exist. Followed AGENTS.md and the bounded Slice 1 prompt. |
| Approved Cursor prompt summary | FG-025 Slice 1 Hub MONITOR display mapping only. No schema, migration, MONITOR arithmetic, enum rename, FG-024, LEARN, or product-wide copy sweep. Commit + push after PASS. |
| Files expected to change | `app/presentation/contractor_copy.py`; `app/templates/projects/detail.html` (`#hub-monitor` / actuals); optional `app/shell.py`; `tests/test_fg025_contractor_copy.py`; HTML assertions in `tests/test_monitor_v1_fg023.py` / `tests/test_project_hub.py`; current-authority docs. |
| Files prohibited from changing | `migrations/`; models/enums; `app/services/monitor.py` keys/arithmetic; Field Web; labour/pricing/nav/PDF; FG-024; live DB. |
| Implementation result | Slice 1 implemented. Internal keys preserved. Live current `e3f4a5b6c7d8`. Live **39** / **39**. Project **13** five actuals unchanged. |
| Tests | Dedicated **10 passed**. Focused **159 passed**. Full **603 passed**. `git diff --check` PASS. |
| Project-state-report update | Yes — FG-025 Slice 1 implemented / not closed. |
| Milestone entry update | Yes — Slice 1 recorded. |
| Constitutional issue raised | None. Display vs domain keys distinguished. Extra product file: `app/shell.py` (existing UI context processor). |
| Unresolved issues | Remaining FG-025 slices unauthorized. “Superseded by” column header and empty superseded history copy left as leakage. “Contract value” still flagged. |
| Next approved step | **STOP.** Do **not** start Slice 2. Do **not** start FG-024. Do **not** start LEARN. |
| Next approved prompt | None authorized. |
| Commit hash | (this product commit) |

### 2026-09-07 — FG-025 contractor-facing UX implementation preflight

| Field | Content |
|-------|---------|
| Date | 2026-09-07 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 7 SEP 2026** |
| Objective | FG-025 implementation preflight: product-wide UI language inventory, terminology contract, slice strategy, file allow-list, test/UAT plan. Docs/reconnaissance only. |
| Business decision | FG-025 is **IMPLEMENTATION PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED / NOT CLOSED**. FG-023 remains **CLOSED**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. Glossary candidates **not pinned**. “Current contract value” wording **flagged**. Strategy **B** (controlled slices). Next: Joel/ChatGPT review, then separate Slice 1 prompt if approved. |
| Architectural decision | Presentation-layer mapping. Do not rename enums/schema. MONITOR identities unchanged. Customer documents are a separate audience (Slice F). No new ADR. No migration. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | FG-025 implementation preflight. Inventory UI language. Do not rewrite copy. Docs commit + push after PASS. |
| Files expected to change | FG-025 gate (preflight section); current-authority pins; current-state / session-handoff / project-state-report / chat-workflow-log / milestones. |
| Files prohibited from changing | `app/`; `tests/`; templates; CSS/JS; Alembic; live DB; FG-024 implementation. |
| Implementation result | Documentation preflight only. No `app/` / `tests/` / `migrations/` change. Live current `e3f4a5b6c7d8`. Live **39** / **39**. |
| Tests | Product pytest **not re-run** (docs-only). `git diff --check` on this docs pass. Historical close-time **35 / 149 / 593** remain the coded baseline. |
| Project-state-report update | Yes — FG-025 preflight complete / not implementation-authorized. |
| Milestone entry update | Yes — preflight recorded. |
| Constitutional issue raised | None. |
| Unresolved issues | Final contractor strings not pinned; “contract value” vs Current Authorized Pre-Tax Revenue **G**; specialist nav names **G**; FG-012 office Overhead/Profit residual out of terminology-only slice. |
| Next approved step | **STOP pending review.** Do **not** implement FG-025 from this preflight. Do **not** start FG-024. Do **not** start LEARN. |
| Next approved prompt | None authorized. Recommended Slice 1 Hub MONITOR display mapping after Joel/ChatGPT review. |
| Commit hash | (this docs commit) |

### 2026-09-07 — FG-023 MONITOR V1 CLOSED / OPERATIONAL FOR UAT

| Field | Content |
|-------|---------|
| Date | 2026-09-07 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 7 SEP 2026** |
| Objective | Close FG-023 after independently verifying Slice C PASS, Hub lifecycle, live Alembic/Field/UAT evidence, and close-time pytest. Docs/governance close. Bounded Hub-label exception only if MONITOR still claimed Future. |
| Business decision | FG-023 is **CLOSED / OPERATIONAL FOR UAT**. MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED**. Item 13 **CLOSED / OPERATIONAL FOR UAT**. Hub MONITOR lifecycle already operational; LEARN remains Future. No product-code change. No FG-025 copy rewrite. No FG-024 implementation. No further actuals. Next governed action: **STOP**. |
| Architectural decision | Display-copy remains FG-025. Commercial identities unchanged. No MONITOR snapshot table. No Field Event conversion. No new migration. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) (documentation / governance close). |
| Approved Cursor prompt summary | FG-023 MONITOR V1 close authorization. Verify Slice C PASS. Close tests. Reconcile current-authority docs. Do not start FG-024/FG-025/LEARN. |
| Files expected to change | FG-023 gate; current-authority indexes; current-state / session-handoff / project-state-report / chat-workflow-log / milestones; modules; bounded architecture pins. Product code only if Hub still labeled MONITOR Future. |
| Files prohibited from changing | `app/` (unless bounded Hub label); `tests/`; Alembic; live DB; FG-024/FG-025 implementation. |
| Implementation result | Documentation close. Hub already operational (`MONITOR` not `MONITOR · Future`). No `app/` / `tests/` / `migrations/` change. Live current `e3f4a5b6c7d8`. Live **39** / **39**. Project **13** five actuals rows unchanged. |
| Tests | Dedicated **35 passed**. Focused **149 passed**. Full **593 passed**. Historical Slice A focused **126** / pre-Slice-B **137** remain historical. `git diff --check` on this docs pass. |
| Project-state-report update | Yes — FG-023 CLOSED / OPERATIONAL FOR UAT. |
| Milestone entry update | Yes — close recorded. |
| Constitutional issue raised | None. |
| Unresolved issues | FG-025 **NOT IMPLEMENTATION-AUTHORIZED**; Observation Delete **QUEUED**; SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. FG-024 Slices A–D remain unauthorized. |
| Next approved step | **STOP.** Do **not** implement FG-025. Do **not** implement FG-024. Do **not** start LEARN. |
| Next approved prompt | None authorized from this close. |
| Commit hash | (this docs commit) |

### 2026-09-07 — FG-025 Contractor-Facing UX Language recorded (future; not implementation-authorized)

| Field | Content |
|-------|---------|
| Date | 2026-09-07 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 7 SEP 2026** |
| Objective | Record FG-025 as a FUTURE Feature Gate for a product-wide contractor-facing UX language / terminology sweep. Docs/governance only. Do not rewrite UI. Do not interrupt FG-023. |
| Business decision | FG-025 is **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Sequence: FG-023 **close** first, then FG-025 sweep, then broader external / U.S. commercialization. Internal model/state names may remain technical in code. User-facing UI must use contractor-facing terminology. FG-023 remains **OPEN** with Slice C **PASS**. Next governed action remains FG-023 close. |
| Architectural decision | Extends FG-011 Hub / ADR-019 lifecycle labels, FG-012 office vs customer copy, FG-013 TIER_A label, FG-017 visual brand (not terminology), FG-021 Field copy, and FG-023 commercial identities (display only after close). Does **not** duplicate FG-024 legal content. FG-025 is **not** a split of FG-024 slices. No new ADR. No migration. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) (documentation / governance). |
| Approved Cursor prompt summary | Record FG-025. Search existing UX/terminology authority first. Inventory surfaces and internal-term leakage. No product code. No UI rewrite. Do not interrupt FG-023. |
| Files expected to change | New FG-025 document; feature-gates README; FG-024 ID clarification; FG-023 next-action pin; docs README; platform-roadmap; platform-governance; current-state / session-handoff / project-state-report / chat-workflow-log / milestones; bounded architecture/module pins. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; live DB; FG-023 product meaning / close sequence; FG-021/FG-022 product meaning. |
| Implementation result | Documentation only. FG-025 recorded. No `app/` / `tests/` / `migrations/` change. Live current remains `e3f4a5b6c7d8`. Live **39** / **39**. |
| Tests | Product pytest **not re-run** (docs-only). Last governed product baseline remains dedicated FG-023 **35** / focused **149** / historical Slice A focused **126** / pre-Slice-B focused **137** / full **593**. `git diff --check` on this docs pass. |
| Project-state-report update | Yes — FG-025 recorded 2026-09-07; current milestone remains FG-023 close. |
| Milestone entry update | Yes — recorded, not a completed product milestone. |
| Constitutional issue raised | None. Display copy vs domain keys distinguished. |
| Unresolved issues | FG-023 **close authorization**; Observation Delete **QUEUED**; SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. FG-025 implementation unauthorized. FG-024 Slices A–D remain unauthorized. |
| Next approved step | FG-023 close authorization under a separate ChatGPT prompt. Do **not** close from this pass. Do **not** implement FG-025. Do **not** implement FG-024. |
| Next approved prompt | FG-023 CLOSE AUTHORIZATION (ChatGPT Architect; not this pass). |
| Commit hash | (this docs commit) |

### 2026-09-07 — FG-023 MONITOR V1 Slice C live migrate + office UAT

| Field | Content |
|-------|---------|
| Date | 2026-09-07 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 7 SEP 2026** |
| Objective | Execute FG-023 Slice C exactly as pinned: live `flask db upgrade e3f4a5b6c7d8`, post-migration verification, labeled `FG023-UAT-MONITOR`, office Hub UAT, four-class actuals, `0.00` supersession, docs after PASS. |
| Business decision | FG-023 remains **APPROVED / OPEN / NOT CLOSED**. Slice A + Slice B **IMPLEMENTED / LIVE-MIGRATED**. Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**. MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / NOT YET CLOSED**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. |
| Architectural decision | Apply existing committed revision only. Gitignored pre-migration copy. UAT writes only on synthetic project **id 13**. Fail-closed HTTP remains **AUTOMATED COVERAGE SUFFICIENT FOR V1**. No DELETE. No in-place rewrite. No new migration. No product-code change. |
| Prompt template used | Slice C execution prompt (live migrate + office UAT). |
| Approved Cursor prompt summary | FG-023 MONITOR V1 Slice C execution: live migrate existing `e3f4a5b6c7d8`; gitignored backup; create `FG023-UAT-MONITOR`; office UAT of `#hub-monitor`; actual-cost create + `0.00` supersession; docs commit + push after PASS. Do not close FG-023. Do not begin FG-024. |
| Files expected to change | Current-authority docs only after PASS. |
| Files prohibited from changing | `app/`; `tests/`; Alembic revisions; live DB/backup (gitignored); FG-024 implementation. |
| Implementation result | Upgrade **PASS**. current = heads = `e3f4a5b6c7d8`. Field **39 / 39**. Project **13** commercial vessel + five actuals rows. Office UAT port **5014** Hub baseline / four-class / supersession **PASS**. Independent arithmetic **PASS**. Zero actuals on projects 1, 2, 9, 11, 12. |
| Tests | Product pytest **not re-run**. Last governed product baseline remains dedicated FG-023 **35** / focused **149** / historical Slice A focused **126** / pre-Slice-B focused **137** / full **593**. `git diff --check` on this docs pass. |
| Project-state-report update | Yes — Slice C PASS; gate remains OPEN. |
| Milestone entry update | Yes — Slice C execution recorded; not a gate close. |
| Constitutional issue raised | None. |
| Unresolved issues | FG-023 **close authorization**; Observation Delete **QUEUED**; SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. FG-024 Slices A–D remain unauthorized. |
| Next approved step | FG-023 close authorization under a separate ChatGPT prompt. Do **not** close from this pass. Do **not** implement FG-024. |
| Next approved prompt | FG-023 CLOSE AUTHORIZATION (ChatGPT Architect; not this pass). |
| Commit hash | (this docs commit) |

### 2026-09-07 — FG-024 North American Contract Intelligence recorded (future; not implementation-authorized)

| Field | Content |
|-------|---------|
| Date | 2026-09-07 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 7 SEP 2026** (Cursor authorized prompt title; session-handoff still records ChatGPT originating title **BRAYMAN - CalibAi 5 Sep 2026**) |
| Objective | Record FG-024 as one linked FUTURE Feature Gate (Legal Content Library + Contract Update Engine + frozen generation snapshot + legal-change monitoring). Docs/governance only. Do not implement. Do not interrupt FG-023. |
| Business decision | FG-024 is **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. One gate, four internal slices, none authorized. Legal Content Gate preserved and still empty. Canada + United States commercial destinations; Ontario first expected Canadian package; no population. FG-023 remains the active implementation stream. |
| Architectural decision | Extend existing Legal Content Gate, ProjectLocation/ADR-037 identity, and issued-document immutability (Constitution Article 5 / ADR-002 / ADR-039 analogue). Do not duplicate Permit Rules Library. Fail closed if no approved jurisdiction package. AI cannot approve or activate legal content. No new ADR. No migration. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) (documentation / governance). |
| Approved Cursor prompt summary | Record FG-024. Search existing authority first. No product code. No migration. No legal-content population. Do not interrupt FG-023. |
| Files expected to change | New FG-024 document; feature-gates README; Legal Content Gate; project-document-package; platform-roadmap Item 15; docs README; Projects module; current-state / session-handoff / project-state-report / chat-workflow-log / milestones; bounded architecture pins. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; live DB; FG-023 product/state file; FG-021/FG-022 product meaning. |
| Implementation result | Documentation only. FG-024 recorded. No `app/` / `tests/` / `migrations/` change. Live current remains `d2e3f4a5b6c7`. Live **39** / **39**. |
| Tests | Product pytest not re-run (docs-only). Last governed product baseline remains dedicated FG-023 **35** / focused **149** / historical Slice A focused **126** / pre-Slice-B focused **137** / full **593**. `git diff --check` on this docs pass. |
| Project-state-report update | Yes — FG-024 recorded 2026-09-07; current milestone remains FG-023 Slice C. |
| Milestone entry update | Yes — recorded, not a completed product milestone. |
| Constitutional issue raised | None. Issued/signed contract immutability restated as FG-024 invariant (Article 5 analogue). |
| Unresolved issues | FG-023 Slice C **execution**; Observation Delete **QUEUED**; SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. FG-024 Slices A–D remain unauthorized. |
| Next approved step | FG-023 Slice C live `flask db upgrade e3f4a5b6c7d8` + office UAT under a separate execution authorization. Do **not** implement FG-024. |
| Next approved prompt | FG-023 SLICE C EXECUTION LIVE MIGRATION + POST-MIGRATION VERIFICATION + BOUNDED OFFICE UAT. |
| Commit hash | (this docs commit) |

### 2026-09-07 — FG-023 MONITOR V1 Slice C implementation preflight

| Field | Content |
|-------|---------|
| Date | 2026-09-07 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 7 SEP 2026** (Cursor authorized prompt title; session-handoff still records ChatGPT originating title **BRAYMAN - CalibAi 5 Sep 2026**) |
| Objective | Governed Slice C implementation preflight only: pin live `flask db upgrade e3f4a5b6c7d8`, post-migration verification, office-UAT project strategy, UAT/fail-closed/closure contracts. No migrate. No UAT. No product code. |
| Business decision | FG-023 remains **APPROVED / OPEN / NOT CLOSED**. Slice A + Slice B remain **IMPLEMENTED / NOT LIVE-MIGRATED**. Slice C **PREFLIGHT COMPLETE / NOT PERFORMED**. Hub `#hub-monitor` **in product code**. Office UAT **NOT STARTED**. MONITOR V1 **not operational**. |
| Architectural decision | Explicit upgrade target `e3f4a5b6c7d8`. Gitignored pre-migration copy. UAT strategy **C**: new labeled `FG023-UAT-MONITOR` project required at execution. Fail-closed HTTP cases **AUTOMATED COVERAGE SUFFICIENT FOR V1**. `0.00` proven as successor, not first create. No new ADR. No new migration. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) (documentation / reconnaissance). |
| Approved Cursor prompt summary | Slice C preflight. Design live migrate + office UAT. Do not run flask db upgrade. Do not perform office UAT. Do not create actuals. |
| Files expected to change | Existing preflight record; current-state; session-handoff; project-state-report; chat-workflow-log; milestones; feature-gates README; FG-023 next action; modules/monitor; platform-roadmap; bounded current-authority pins. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; live DB; FG-021/FG-022 product meaning; FG-023 commercial identities; Slice A/B historical preflight bodies. |
| Implementation result | Documentation only. Slice C section appended to [fg-023-monitor-v1-implementation-preflight.md](architecture/fg-023-monitor-v1-implementation-preflight.md). No `app/` / `tests/` / `migrations/` change. Live current remains `d2e3f4a5b6c7`. Live **39** / **39**. |
| Tests | Product pytest not re-run (docs-only). Last governed product baseline remains dedicated FG-023 **35** / focused **149** / historical Slice A focused **126** / pre-Slice-B focused **137** / full **593**. `git diff --check` on this docs pass. |
| Project-state-report update | Yes — Slice C preflight 2026-09-07. |
| Milestone entry update | Yes. |
| Constitutional issue raised | None. |
| Unresolved issues | Slice C **execution** authorization; Observation Delete **QUEUED**; SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. |
| Next approved step | FG-023 Slice C live `flask db upgrade e3f4a5b6c7d8` + office UAT under a separate execution authorization. Do not live-migrate from this preflight. Do not start office UAT from this preflight. |
| Next approved prompt | FG-023 SLICE C EXECUTION LIVE MIGRATION + POST-MIGRATION VERIFICATION + BOUNDED OFFICE UAT. |
| Commit hash | (this docs commit) |

### 2026-09-07 — FG-023 MONITOR V1 Slice B Hub MONITOR + office actuals writes

| Field | Content |
|-------|---------|
| Date | 2026-09-07 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 7 SEP 2026** (Cursor authorized prompt title; session-handoff still records ChatGPT originating title **BRAYMAN - CalibAi 5 Sep 2026**) |
| Objective | Implement FG-023 Slice B only: Project Hub `#hub-monitor` MONITOR V1 display + BUILD office actual-cost create/supersede POSTs, bounded tests, current-authority docs. No live migrate. No office UAT. |
| Business decision | FG-023 remains **APPROVED / OPEN / NOT CLOSED**. Slice A remains **IMPLEMENTED / NOT LIVE-MIGRATED**. Slice B **IMPLEMENTED / NOT LIVE-MIGRATED**. Hub `#hub-monitor` **in product code**. Office UAT **NOT STARTED**. MONITOR V1 **not operational** in live/UAT. |
| Architectural decision | Reuse Slice A `create_direct_cost_actual` / `supersede_direct_cost_actual` / `assemble_monitor_v1`. Hub GET `/projects/<id>` via `project_hub.py` `hub["monitor"]`. BUILD POSTs create/supersede. No second model/engine. Template does not recompute commercial identities. GM Hub display = percent via `as_money(gm * 100)` two decimals. No DELETE. No in-place amount edit. No new ADR. No new migration. |
| Prompt template used | FG-023 Slice B IMPLEMENTATION (product code + tests + docs). |
| Approved Cursor prompt summary | Slice B Hub MONITOR + office actuals writes. Do not live-migrate. Do not start office UAT. Do not close FG-023. |
| Files expected to change | `app/routes/build.py`; `app/services/project_hub.py`; `app/templates/projects/detail.html`; `tests/test_monitor_v1_fg023.py`; `tests/test_project_hub.py`; current-authority docs. CSS only if required (not required). |
| Files prohibited from changing | Slice A services/models; Alembic; live DB; Field Web; Observation Delete; LEARN; FG-021/FG-022 product meaning; FG-023 commercial identities. |
| Implementation result | Slice B product code landed. Live current remains `d2e3f4a5b6c7`. Live **39** / **39**. No live `project_direct_cost_actuals` table. Gate **OPEN**. |
| Tests | Dedicated `./venv/bin/python -m pytest -q tests/test_monitor_v1_fg023.py` — **35 passed**. Focused dedicated FG-023 + Hub + FG-018 + both FG-020 + FG-021 — **149 passed**. Full suite `./venv/bin/python -m pytest -q` — **593 passed**. Historical Slice A focused **126** and pre-Slice-B focused **137** remain historical. `git diff --check`. |
| Project-state-report update | Yes — FG-023 Slice B 2026-09-07. |
| Milestone entry update | Yes. |
| Constitutional issue raised | None. |
| Unresolved issues | Slice C live-migrate + office UAT; Observation Delete **QUEUED**; SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. |
| Next approved step | FG-023 Slice C live `flask db upgrade` + office UAT under a separate authorization. Do not live-migrate from this result. Do not start office UAT from this result. |
| Next approved prompt | FG-023 SLICE C LIVE MIGRATE + OFFICE UAT. |
| Commit hash | (this commit) |

### 2026-09-07 — FG-023 MONITOR V1 Slice B implementation preflight

| Field | Content |
|-------|---------|
| Date | 2026-09-07 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN — CALIBAI DEVELOPMENT 7 SEP 2026** (Cursor authorized prompt title; session-handoff still records ChatGPT originating title **BRAYMAN - CalibAi 5 Sep 2026**) |
| Objective | Governed Slice B implementation preflight only: Hub + office write reconnaissance, file allow-list, workflow pin, focused-bundle resolution. No product code. No live migrate. |
| Business decision | FG-023 remains **APPROVED / OPEN / NOT CLOSED**. Slice A remains **IMPLEMENTED / NOT LIVE-MIGRATED**. Slice B **PREFLIGHT COMPLETE**. Hub UI **NOT IMPLEMENTED**. Office UAT **NOT STARTED**. MONITOR V1 **not operational**. |
| Architectural decision | Reuse Slice A `create_direct_cost_actual` / `supersede_direct_cost_actual` / `assemble_monitor_v1`. Hub GET `/projects/<id>` + BUILD POST create/supersede. No second model/engine. GM Hub display = percent via `as_money(gm * 100)` two decimals. Focused **137** current / **126** historical. No new ADR. No new migration. |
| Prompt template used | FG-023 Slice B IMPLEMENTATION PREFLIGHT (documentation / reconnaissance). |
| Approved Cursor prompt summary | Slice B preflight. Recon + design + governed docs. Do not implement Slice B product code. Do not live-migrate. |
| Files expected to change | Existing preflight record; current-state; session-handoff; project-state-report; chat-workflow-log; milestones; feature-gates README; FG-023 next action; modules/monitor + build; platform-roadmap. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; live DB; FG-021/FG-022 product meaning; FG-023 commercial identities; Slice A historical inspect-gap table. |
| Implementation result | Documentation only. Slice B section appended to [fg-023-monitor-v1-implementation-preflight.md](architecture/fg-023-monitor-v1-implementation-preflight.md). No `app/` / `tests/` / `migrations/` change. Live current remains `d2e3f4a5b6c7`. Live **39** / **39**. |
| Tests | Product pytest not re-run (docs-only). Last governed product baseline remains dedicated FG-023 **23** / current focused **137** (start-of-day 7 Sep) / historical Slice A focused **126** / full **581**. `git diff --check` on this docs pass. |
| Project-state-report update | Yes — Slice B preflight 2026-09-07. |
| Milestone entry update | Yes. |
| Constitutional issue raised | None. |
| Unresolved issues | Slice B Hub UI **implementation** authorization; Slice C live-migrate + office UAT; Observation Delete **QUEUED**; SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. |
| Next approved step | FG-023 Slice B office write routes/forms + Project Hub `#hub-monitor` **implementation** under a separate product-code authorization. Do not live-migrate. Do not start office UAT from this preflight. |
| Next approved prompt | FG-023 SLICE B OFFICE WRITE ROUTES/FORMS + PROJECT HUB `#hub-monitor` IMPLEMENTATION. |
| Commit hash | (this docs commit) |

### 2026-09-07 — Review Turnover (FG-023 Slice A stop state)

| Field | Content |
|-------|---------|
| Date | 2026-09-07 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN - CalibAi 5 Sep 2026** |
| Objective | Full Review Turnover. Stop substantive development. Reconcile current-authority docs and produce a zero-memory fresh-chat prompt. No Slice B. No live migrate. |
| Business decision | **TURNOVER PASS** after delta-ledger reconciliation. FG-023 remains **APPROVED / OPEN / NOT CLOSED**. Slice A remains **IMPLEMENTED / NOT LIVE-MIGRATED**. MONITOR V1 **PARTIALLY IMPLEMENTED**. Hub UI **NOT IMPLEMENTED**. Office UAT **NOT STARTED**. |
| Architectural decision | No new ADR. Frozen FG-023 contract unchanged. Last product-changing SHA remains `2553cf09bdd6b8018112d7eb4b682f87aa103b01`. |
| Prompt template used | [governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) 22-point package |
| Approved Cursor prompt summary | Review Turnover. Full and complete. Create a fully briefed new chat. |
| Files expected to change | session-handoff; current-state; project-state-report; chat-workflow-log; milestones; feature-gates README; adr README; bounded current-authority pins. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; live DB; FG-021/FG-022 product meaning; FG-023 commercial identities; master template bytes. |
| Implementation result | Documentation only. Stale §9/§10/§14/§18/§22 repaired. Completeness test **NO**. Live current remains `d2e3f4a5b6c7`. Live **39** / **39**. No live actuals table. |
| Tests | Product pytest not re-run (docs-only). Last governed product-changing baseline remains dedicated FG-023 **23** / focused **126** / full **581**. `git diff --check` on this docs pass. |
| Project-state-report update | Yes — Review Turnover 2026-09-07. |
| Milestone entry update | Yes. |
| Constitutional issue raised | None. |
| Unresolved issues | Slice B Hub UI authorization; Slice C live-migrate + office UAT; GM display digits; Observation Delete **QUEUED**; SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. |
| Next approved step | FG-023 Slice B office write routes/forms + Project Hub `#hub-monitor` implementation preflight / authorization. Do not implement Slice B from this turnover. Do not live-migrate. |
| Next approved prompt | FG-023 SLICE B OFFICE WRITE ROUTES/FORMS + PROJECT HUB `#hub-monitor` IMPLEMENTATION PREFLIGHT / AUTHORIZATION. |
| Commit hash | `ea9c4b765bd58c5d12414784399e2c29822f1e6f` |

### 2026-09-06 — FG-023 Slice A model, services, tests

| Field | Content |
|-------|---------|
| Date | 2026-09-06 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN - CalibAi 5 Sep 2026** |
| Objective | Implement FG-023 Slice A only: `ProjectDirectCostActual`, additive Alembic revision, BUILD actuals service, MONITOR `assemble_monitor_v1`, dedicated tests, current-authority docs. No Hub UI. No live migrate. |
| Business decision | FG-023 remains **APPROVED / OPEN / NOT CLOSED**. Slice A **IMPLEMENTED / NOT LIVE-MIGRATED**. MONITOR V1 **PARTIALLY IMPLEMENTED**. Hub UI **NOT IMPLEMENTED**. Office UAT **NOT STARTED**. Item 13 **PARTIALLY IMPLEMENTED**. |
| Architectural decision | BUILD owns actuals. MONITOR owns live projection. No MONITOR snapshot table. No Field Event conversion. `incurred_on` accepts any parseable calendar date. Multiple Accepted Proposals → `AMBIGUOUS_COMMITMENT`. No new ADR. |
| Prompt template used | Approved Slice A implementation prompt (model + migration + services + tests). |
| Approved Cursor prompt summary | BRAYMAN — FG-023 MONITOR V1 IMPLEMENTATION SLICE A. MODEL + MIGRATION + SERVICES + TESTS. NO HUB UI. NO LIVE MIGRATE. |
| Files expected to change | `app/models/direct_cost_actual.py`; `app/models/__init__.py`; `app/services/direct_cost_actuals.py`; `app/services/monitor.py`; `migrations/versions/e3f4a5b6c7d8_add_project_direct_cost_actuals_fg023.py`; `tests/test_monitor_v1_fg023.py`; current-authority docs. |
| Files prohibited from changing | Hub routes/templates; Field Web; live DB; FG-021/FG-022 product meaning; LEARN; Observation Delete; QuickBooks; FG-023 commercial identities. |
| Implementation result | Slice A product code landed. Revision `e3f4a5b6c7d8` (`down_revision = d2e3f4a5b6c7`). Live current remains `d2e3f4a5b6c7`. Live **39** / **39**. No live actuals table. No Hub UI. |
| Tests | Dedicated `./venv/bin/python -m pytest -q tests/test_monitor_v1_fg023.py` — **23 passed**. Focused dedicated FG-023 + Hub + FG-018 + FG-020 + FG-021 — **126 passed**. Full suite `./venv/bin/python -m pytest -q` — **581 passed**. `git diff --check` clean. |
| Project-state-report update | Yes — FG-023 Slice A. |
| Milestone entry update | Yes. |
| Constitutional issue raised | None. |
| Unresolved issues | Hub UI / Slice B; live migrate / Slice C; office UAT; GM display digits; Observation Delete **QUEUED**; SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. |
| Next approved step | FG-023 Slice B office write routes/forms + Project Hub `#hub-monitor` implementation preflight / authorization. Do not live-migrate. Do not start office UAT. |
| Next approved prompt | FG-023 SLICE B OFFICE WRITE ROUTES/FORMS + PROJECT HUB `#hub-monitor` IMPLEMENTATION PREFLIGHT / AUTHORIZATION. |
| Commit hash | (this commit) |

### 2026-09-06 — FG-023 MONITOR V1 implementation preflight (docs + read-only inspect)

| Field | Content |
|-------|---------|
| Date | 2026-09-06 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN - CalibAi 5 Sep 2026** |
| Objective | Pin implementation-ready FG-023 mechanics. Do not implement MONITOR. Do not create a model or migration. |
| Business decision | Preflight **COMPLETE**. Readiness **B. READY WITH EXPLICIT NON-BLOCKING NOTES**. FG-023 remains **APPROVED / IMPLEMENTATION NOT STARTED / IMPLEMENTATION NOT YET AUTHORIZED**. Item 13 still **NOT AUTHORIZED FOR CODE**. |
| Architectural decision | Frozen FG-023 contract unchanged. BUILD `ProjectDirectCostActual` field/constraint/supersession pins recorded. MONITOR live projection service contract recorded. No new ADR. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — FG-023 MONITOR V1 IMPLEMENTATION READINESS / PREFLIGHT (docs + read-only). |
| Files expected to change | Canonical preflight artifact; current-authority pins; recon subsequent status. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; live DB; FG-021/FG-022 product meaning; substantive FG-023 contract identities. |
| Implementation result | Documentation only. Product code unchanged. Tests unchanged. Database unchanged. No migration. No ADR accepted. Live **39** / **39**. Live current = head `d2e3f4a5b6c7`. |
| Tests | Product pytest not re-run (docs-only). Last governed product-changing baseline remains dedicated **20** / focused **148** / full **558**. `git diff --check` on this docs pass. |
| Project-state-report update | Yes — FG-023 preflight. |
| Milestone entry update | Yes. |
| Constitutional issue raised | None. |
| Unresolved issues | Future-dated `incurred_on`; GM display digits; multiple Accepted Proposals → `AMBIGUOUS_COMMITMENT`. Observation Delete **QUEUED**. SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. |
| Next approved step | Separate FG-023 implementation authorization. Do not implement MONITOR from this preflight. |
| Next approved prompt | Separate implementation prompt (slices A/B; live migrate/UAT remains C). |
| Commit hash | (this commit) |

### 2026-09-06 — FG-023 MONITOR V1 Feature Gate approval (docs only)

| Field | Content |
|-------|---------|
| Date | 2026-09-06 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN - CalibAi 5 Sep 2026** |
| Objective | Record Joel/ChatGPT approval of FG-023 as written. Do not implement MONITOR. Do not create a migration. Do not accept a new ADR. |
| Business decision | FG-023 **APPROVED / IMPLEMENTATION NOT STARTED / IMPLEMENTATION NOT YET AUTHORIZED**. Correction semantics including `amount >= 0` / `0.00` superseding successor **accepted**. Office Direct Cost actuals remain in the same gate (BUILD `ProjectDirectCostActual`; not created). Item 13 **RECON COMPLETE / FEATURE GATE APPROVED / NOT IMPLEMENTED / NOT AUTHORIZED FOR CODE**. |
| Architectural decision | Frozen FG-023 contract unchanged. No new ADR. ADR-021 remains the commercial baseline. Dual ownership unchanged: MONITOR comparison projection; BUILD actuals; Projects Hub UX. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — RECORD FG-023 APPROVAL (docs only). |
| Files expected to change | FG-023 status/approval; feature-gate index; current-authority docs; recon subsequent status; roadmap Item 13. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; live DB; FG-021/FG-022 product meaning; substantive FG-023 contract identities. |
| Implementation result | Documentation only. Product code unchanged. Tests unchanged. Database unchanged. No migration. No ADR accepted. Live **39** / **39**. Live current = head `d2e3f4a5b6c7`. |
| Tests | Product pytest not re-run (docs-only). Last governed product-changing baseline remains dedicated **20** / focused **148** / full **558**. `git diff --check` on this docs pass. |
| Project-state-report update | Yes — FG-023 approval. |
| Milestone entry update | Yes. |
| Constitutional issue raised | None. |
| Unresolved issues | Separate FG-023 implementation authorization. Observation Delete **QUEUED**. SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. |
| Next approved step | IMPLEMENTATION READINESS / PREFLIGHT for approved FG-023. Do not implement MONITOR. |
| Next approved prompt | Implementation readiness / preflight (not implementation). |
| Commit hash | (this commit) |

### 2026-09-06 — FG-023 MONITOR V1 Feature Gate draft (docs only)

| Field | Content |
|-------|---------|
| Date | 2026-09-06 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN - CalibAi 5 Sep 2026** |
| Objective | Draft FG-023 from the MONITOR V1 recon. Do not implement MONITOR. Do not create a migration. Do not accept a new ADR. |
| Business decision | FG-023 **DRAFT FOR JOEL APPROVAL / NOT APPROVED / NOT AUTHORIZED FOR IMPLEMENTATION**. Office Direct Cost actuals **included** in the same gate (BUILD `ProjectDirectCostActual`; incremental; no MONITOR snapshot table). Field Events remain evidence only. Residual roadmap “Do not start Item 13” current-authority leftover repaired. |
| Architectural decision | No new ADR. ADR-021 remains the commercial baseline. Dual ownership: MONITOR comparison projection; BUILD actuals; Projects Hub UX. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — MONITOR V1 FEATURE GATE DRAFT (docs only). |
| Files expected to change | FG-023 gate; feature-gate index; current-authority docs; recon subsequent status; residual roadmap next/decisions sections. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; live DB; FG-021/FG-022 product meaning. |
| Implementation result | Documentation only. Product code unchanged. Tests unchanged. Database unchanged. No migration. No ADR accepted. Live **39** / **39**. Live current = head `d2e3f4a5b6c7`. |
| Tests | Product pytest not re-run (docs-only). Last governed product-changing baseline remains dedicated **20** / focused **148** / full **558**. `git diff --check` on this docs pass. |
| Project-state-report update | Yes — FG-023 draft. |
| Milestone entry update | Yes. |
| Constitutional issue raised | None. |
| Unresolved issues | Joel approval of FG-023. Observation Delete **QUEUED**. SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. |
| Next approved step | Joel review of FG-023. Do not implement MONITOR. |
| Next approved prompt | None until Joel approves FG-023 (then a separate implementation prompt). |
| Commit hash | (this commit) |

### 2026-09-06 — MONITOR V1 / Item 13 implementation reconnaissance (docs only)

| Field | Content |
|-------|---------|
| Date | 2026-09-06 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN - CalibAi 5 Sep 2026** |
| Objective | Freeze smallest lawful MONITOR V1 design. Do not implement MONITOR. Do not create/approve a Feature Gate. Do not accept a new ADR. |
| Business decision | Item 13 **RECON COMPLETE / NOT IMPLEMENTED / NOT FEATURE-GATED / NOT AUTHORIZED FOR CODE**. Feature-gate readiness **READY FOR FEATURE-GATE DRAFT**. Field Events **EVIDENCE ONLY**, not actual cost. Recommended V1: Hub comparison projection + BUILD office Direct Cost actuals. Forecast out of V1. |
| Architectural decision | No new ADR. ADR-021 remains the commercial baseline. MONITOR owns no V1 durable table. Actuals, if gated, are BUILD-owned `ProjectDirectCostActual` (design freeze only; not created). |
| Prompt template used | Bounded read-only implementation reconnaissance + docs-only current-authority cleanup. |
| Approved Cursor prompt summary | BRAYMAN — ROADMAP ITEM 13 / MONITOR V1 READ-ONLY IMPLEMENTATION RECONNAISSANCE. |
| Files expected to change | Recon artifact; current-authority docs; three CURRENT-looking stale pins (roadmap near-term subsection; Observation Delete capture header/priority; modules README live-head). |
| Files prohibited from changing | `app/`; `tests/`; Alembic; live DB; Feature Gate files (no new FG); ADR body except index cross-ref. |
| Implementation result | Documentation only. Product code unchanged. Tests unchanged. Database unchanged. No migration. No Feature Gate. No ADR accepted. Live **39** / **39**. Live current = head `d2e3f4a5b6c7`. |
| Tests | Product pytest not re-run (docs-only). Last governed product-changing baseline remains dedicated **20** / focused **148** / full **558**. `git diff --check` on this docs pass. |
| Project-state-report update | Yes — Item 13 recon complete. |
| Milestone entry update | Yes — recon recorded. |
| Constitutional issue raised | None. |
| Unresolved issues | Feature Gate still required before code. Joel freeze: include office actuals in V1 (recommended yes); incremental vs restated; no MONITOR snapshot table. Observation Delete **QUEUED**. SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**. |
| Next approved step | Draft MONITOR V1 Feature Gate from the recon. Do not implement MONITOR. |
| Next approved prompt | MONITOR V1 Feature Gate draft (docs only). |
| Commit hash | (this commit) |

### 2026-09-06 — FG-021 CLOSED with SESSION-EXPIRY deferred exception (docs only)

| Field | Content |
|-------|---------|
| Date | 2026-09-06 |
| Branch | `main` |
| Active ChatGPT development chat title | **BRAYMAN - CalibAi 5 Sep 2026** |
| Objective | Close FG-021 under Joel/ChatGPT-authorized OPTION 2 explicit deferred closure. Do not change product/tests/auth/DB. Do not convert SESSION-EXPIRY to PASS. Do not start Item 13 / MONITOR / Observation Delete / session revocation. |
| Business decision | **FG-021 CLOSED.** IMPLEMENTED / LIVE-MIGRATED / REAL-IPHONE UAT COMPLETE SUBJECT TO THE EXPLICIT SESSION-EXPIRY DEFERRED EXCEPTION. **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED.** NOT PASS. NOT FAIL. NOT N/A. NOT WAIVED. Recovery path implemented; current product has no naturally exercisable real-iPhone session-expiry trigger. Event **37** / Original **37** remain authenticated residue, **not** recovery evidence. **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** Observation Delete **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Server-side per-login session revocation / idle timeout remains **FUTURE AUTHENTICATION HARDENING / NOT FG-021**. Roadmap Item 12 **CLOSED**. |
| Architectural decision | None new. No ADR created/accepted. FG-018 signed-cookie architecture unchanged. |
| Prompt template used | Bounded FG-021 docs-only gate closure. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 OPTION 2 EXPLICIT DEFERRED CLOSURE. |
| Files expected to change | Current-authority docs only: FG-021 gate, Feature Gate index, current-state, session-handoff, project-state-report, roadmap, modules/build, chat-workflow-log, milestones, related current-authority indexes. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; live DB; ADR body except current-authority FG-021 cross-refs; FG-022. |
| Implementation result | Documentation/governance closure only. Product code unchanged. Tests unchanged. Database unchanged. No migration. No Event/Original created. Live **39** / **39**. Live current = head `d2e3f4a5b6c7`. |
| Tests | Product pytest not re-run (docs-only closure). Last governed product-changing baseline remains dedicated **20** / focused **148** / full **558**. `git diff --check` on this docs pass. |
| Project-state-report update | Yes — FG-021 **CLOSED**. |
| Milestone entry update | Yes — FG-021 closure recorded. |
| Constitutional issue raised | None. SESSION-EXPIRY remains explicitly not PASS. |
| Unresolved issues | SESSION-EXPIRY RECOVERY **DEFERRED / NOT YET EXERCISED**. Observation Delete **QUEUED**. Session revocation / idle timeout future auth hardening. Item 13 MONITOR **NOT AUTHORIZED**. |
| Next approved step | STOP. Do not start Item 13 / MONITOR. Do not implement Observation Delete. Do not implement session revocation. |
| Next approved prompt | None from this close. |
| Commit hash | (this commit) |

### 2026-09-06 — FG-021 older supported iPhone/Safari WAIVED AS NOT PRACTICAL (docs only)

| Field | Content |
|-------|---------|
| Date | 2026-09-06 |
| Branch | `main` @ `c858af55e29711ac421c552f4dc351b3fffb10ba` (start) |
| Active ChatGPT development chat title | BRAYMAN - CalibAi 5 Sep 2026 |
| Objective | Record Joel/ChatGPT older-device disposition. Do not close FG-021. Do not resume session-expiry UAT. |
| Business decision | **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** Not PASS. Not FAIL. Not exercised. Conservative: older coverage is distinct from the primary UAT device. Joel has no separate older physical iPhone. Approved FG-021 “where practical” applies. Primary UAT remains iPhone 14 / iOS 26.6.1 / Safari and is **not** the older-device PASS. No device matrix invented. SESSION-EXPIRY RECOVERY remains **OPEN / DEFERRED / NOT YET EXERCISED** (only substantive unresolved FG-021 UAT). Observation Delete **QUEUED** and does **not** block closure. Gate **NOT CLOSED**. |
| Architectural decision | None. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — FG-021 OLDER-IPHONE GOVERNANCE DISPOSITION. |
| Files expected to change | Current/UAT docs only. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; ADR; FG-022; architecture reconnaissance historical snapshots except current remaining-UAT language. |
| Implementation result | Docs-only disposition record. Product code unchanged. Tests unchanged. |
| Tests | Product pytest not re-run (docs-only). Last governed suite remains dedicated **20** / focused **148** / full **558**. `git diff --check` this pass. |
| Project-state-report update | Yes — PART B this-pass decision recorded. |
| Milestone entry update | No. |
| Constitutional issue raised | None. |
| Unresolved issues | Session-expiry **deferred**. Observation Delete **QUEUED**. FG-021 still OPEN. |
| Next approved step | STOP. Do not close FG-021. Do not resume session-expiry UAT. Do not implement Observation Delete. |
| Next approved prompt | None from this documentation pass. |
| Commit hash | this commit |

### 2026-09-06 — FG-021 landscape-tolerance real-iPhone UAT PASS (docs only)

| Field | Content |
|-------|---------|
| Date | 2026-09-06 |
| Branch | `main` @ `057ff15ce91ca8fd15ca815e9f7fd972e34c6f2c` (start) |
| Active ChatGPT development chat title | BRAYMAN - CalibAi 5 Sep 2026 |
| Objective | Record current-iPhone landscape / orientation / field-usability PASS after Joel disabled Portrait Orientation Lock. Do not modify product or tests. Do not close FG-021. |
| Business decision | **LANDSCAPE TOLERANCE PASS.** **ORIENTATION / PORTRAIT PASS.** **CURRENT-IPHONE FIELD-USABILITY PASS.** Implemented CSS `057ff15` is sufficient. Initial post-fix FAIL was confounded by iPhone Portrait Orientation Lock **ON** (not a CalibAi product defect). After lock **OFF**, Field adjusted correctly. No second CSS correction. Gate **NOT CLOSED**. SESSION-EXPIRY RECOVERY remains **OPEN / DEFERRED / NOT YET EXERCISED**. Older supported iPhone/Safari smoke pending separate disposition. Observation Delete **QUEUED / NOT AUTHORIZED**. |
| Architectural decision | None. Current landscape CSS remains sufficient. Do not add a short-wide media-query workaround. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — FG-021 LANDSCAPE-TOLERANCE FINAL REAL-IPHONE UAT GOVERNANCE. |
| Files expected to change | Current/UAT docs only. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; templates; JS; ADR; FG-022. |
| Implementation result | Docs-only UAT record. Product code unchanged. Tests unchanged. |
| Tests | Product pytest not re-run (docs-only). Last governed suite remains dedicated **20** / focused **148** / full **558**. `git diff --check` this pass. |
| Project-state-report update | Yes — PART B this-pass decision recorded. |
| Milestone entry update | No. |
| Constitutional issue raised | None. |
| Unresolved issues | Session-expiry **deferred**. Older iPhone smoke pending. Observation Delete **QUEUED**. FG-021 still OPEN. |
| Next approved step | STOP. Do not close FG-021. Do not start older-device or session-expiry UAT. Do not implement Observation Delete. |
| Next approved prompt | None from this documentation pass. |
| Commit hash | this commit |

### 2026-09-06 — FG-021 landscape-tolerance CSS correction (retest required)

| Field | Content |
|-------|---------|
| Date | 2026-09-06 |
| Branch | `main` @ `2df50177820c8421b091132d8ba1a70ddaaba38a` (start) |
| Active ChatGPT development chat title | BRAYMAN - CalibAi 5 Sep 2026 |
| Objective | Smallest CSS-only landscape-tolerance correction. Do not mark landscape PASS. Do not close FG-021. |
| Business decision | Operator landscape FAIL preserved. Portrait / one-handed / outdoor / general visibility **PASS**. Landscape **FIX IMPLEMENTED / REAL-IPHONE RETEST REQUIRED / NOT YET PASS**. |
| Architectural decision | `@media (orientation: landscape)` after `min-width: 720px`. Portrait defaults unchanged. No template/JS/API/schema change. |
| Prompt template used | [cursor-bugfix-template.md](prompts/cursor-bugfix-template.md) |
| Approved Cursor prompt summary | BRAYMAN — FG-021 LANDSCAPE-TOLERANCE BOUNDED CSS CORRECTION. |
| Files expected to change | `app/static/css/field.css`; `tests/test_field_web_fg021.py`; current/UAT docs. |
| Files prohibited from changing | `field.js`; capture/IndexedDB/CSRF/auth/API; Alembic; ADR; FG-022. |
| Implementation result | Landscape compact grid/row/sticky Save in `field.css`. New CSS contract test. Dedicated **20**. Focused **148**. Full **558**. |
| Tests | `./venv/bin/python -m pytest tests/test_field_web_fg021.py -q` — **20 passed**. Focused Hub+FG-018+FG-019+both FG-020+FG-021 — **148 passed**. `./venv/bin/python -m pytest -q` — **558 passed**. `git diff --check` clean. |
| Project-state-report update | Yes — PART B this-pass decision recorded. |
| Milestone entry update | No. |
| Constitutional issue raised | None. |
| Unresolved issues | Landscape real-iPhone retest. Session-expiry **deferred**. Older iPhone smoke pending. Observation Delete **QUEUED**. FG-021 still OPEN. |
| Next approved step | STOP. Real-iPhone landscape retest required before PASS. Do not close FG-021. Do not start older-device or session-expiry UAT. |
| Next approved prompt | None from this implementation pass. |
| Commit hash | this commit |

### 2026-09-06 — FG-021 CSRF recovery real-iPhone UAT PASS (docs only)

| Field | Content |
|-------|---------|
| Date | 2026-09-06 |
| Branch | `main` @ `4c52167f5d60372cb595a4984b9b7c93945b0782` (start) |
| Active ChatGPT development chat title | BRAYMAN - CalibAi 5 Sep 2026 |
| Objective | Inspect the authorized real-iPhone natural-expiry CSRF Save and record PASS if proven. Do not ask Joel to touch the iPhone. Do not create another Event/Original. Do not close FG-021. Do not mark session-expiry PASS. |
| Business decision | **CSRF RECOVERY REAL-IPHONE UAT PASS.** One Event **39** / one text Original **39** on Project **11**. Same Capture document dwelled **5856 s**. First Event POST **400** (expired CSRF) created no Event. `refreshCsrf` Capture GET **200**. Same UUID replayed Event **201** then Original **201**. Operator UI **SAVED**. Do not close FG-021. SESSION-EXPIRY RECOVERY remains **OPEN / DEFERRED / NOT YET EXERCISED**. |
| Architectural decision | None. Flask-WTF default `WTF_CSRF_TIME_LIMIT` **3600 s** (app does not override). CSRFProtect 400 is Werkzeug HTML; `field.js` `requestOnce` matches `/csrf/i` or `/token/i` then GETs `window.location.pathname`. ASCII hyphen in the text body vs operator em dash is not a product defect. Event **38** remains interrupted-pending residue (not this PASS). |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — FG-021 CSRF RECOVERY FINAL POST-SAVE EVIDENCE INSPECTION. |
| Files expected to change | Current/UAT records only. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; ADR; FG-022; master bytes; Legal Content Gate. |
| Implementation result | Detached HTTPS PID **88819** PPID **1** port **5443** continuous. T0 Capture GET **200** `06:02:58` EDT. Save `07:40:34` EDT. Sequence: Event POST **400** → Capture GET **200** (no static) → Event POST **201** → Original POST **201**. Event **39**, Project **11**, `ORG-001`, Joel Brayman `user_id` 1. Original **39** `kind=text` body `FG-021 CSRF recovery UAT - 6 Sep 2026`. `client_capture_uuid` `0012e6af-c627-4c40-9793-5e1e6611691f`; `client_original_uuid` `acba9f83-5ed2-40ae-a811-c805318594c0`. Live **39** / **39**. UUID counts 1/1. No orphan. No login/logout/401 during Save. Field Today GET after Save **not** performed. Hub HTML **200** **not** obtained (inspector unauthenticated **302**). Gate **NOT CLOSED**. |
| Tests | Docs: `git diff --check`; markdown links. Product pytest not run. Last product-changing suite remains 19 / 147 / 557. |
| Project-state-report update | Yes — PART B this-pass decision recorded. |
| Milestone entry update | No. |
| Constitutional issue raised | None. |
| Unresolved issues | Remaining FG-021 UAT: orientation / portrait / one-handed / outdoor; older iPhone smoke where practical; session-expiry **deferred**. Observation Delete **QUEUED**. FG-021 still OPEN. |
| Next approved step | STOP. Do not close FG-021. Do not start usability or session-expiry UAT in this pass. |
| Next approved prompt | None from this docs-only record. |
| Commit hash | this commit |

### 2026-09-05 — FG-021 background/foreground persistence real-iPhone UAT PASS (docs only)

| Field | Content |
|-------|---------|
| Date | 2026-09-05 |
| Branch | `main` @ `09bbbbb4321fd3ad1e87ddb6d97bc792dcf42d1a` (start) |
| Active ChatGPT development chat title | BRAYMAN - CalibAi 5 Sep 2026 |
| Objective | Record already-performed ordinary background/foreground text-capture UAT as PASS. Do not repeat the iPhone test. Do not create another Event/Original. Do not close FG-021. |
| Business decision | **BACKGROUND / FOREGROUND PERSISTENCE REAL-IPHONE UAT PASS.** One Event **36** / one text Original **36** on Project **11**. Unsaved Capture text survived ordinary Safari backgrounding (not force-close). Do not close FG-021. Do not start session-expiry or CSRF UAT in this pass. |
| Architectural decision | None. Unsaved Capture text is not IndexedDB until Save. This UAT is Safari keeping the Capture page in memory across ordinary backgrounding. ASCII hyphen in the text body vs operator em dash is not a product defect. |
| Prompt template used | Bounded FG-021 real-iPhone UAT docs-only record. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 BACKGROUND / FOREGROUND PERSISTENCE POST-SAVE SERVER EVIDENCE INSPECTION. |
| Files expected to change | Current/UAT records only. Current ChatGPT development chat title records updated to `BRAYMAN - CalibAi 5 Sep 2026`. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; ADR; FG-022; master bytes; Legal Content Gate. Historical chat-title entries left unchanged. |
| Implementation result | Event **36**, Project **11**, `ORG-001`, Joel Brayman `user_id` 1. Flask **556723**: Capture GET `07:17:25`; Event **201** + Original **201** at `07:19:10`; Today **200** `07:19:17`. Original **36** `kind=text` body `FG-021 background-foreground UAT - 5 Sep 2026`. `client_capture_uuid` `3394825c-bb74-409b-93c6-d976021ec39e`; `client_original_uuid` `f4ede486-1b7b-40de-be02-47e5af04c5ba`. Live **36** / **36**. Field Today **200**. Desktop Hub Event **36** **200**. One Event + one text Original; no 409; no orphan. Gate **NOT CLOSED**. |
| Tests | Docs: `git diff --check`; markdown links. Product pytest not run. Last product-changing suite remains 19 / 147 / 557. |
| Project-state-report update | Yes — PART B this-pass decision recorded. |
| Milestone entry update | No. |
| Constitutional issue raised | None. |
| Unresolved issues | Remaining FG-021 UAT: session-expiry; CSRF; older iPhone smoke; orientation/readability. Observation Delete **QUEUED**. FG-021 still OPEN. |
| Next approved step | STOP. Do not close FG-021. Do not start session-expiry recovery in this pass. |
| Next approved prompt | None from this docs-only record. |
| Commit hash | this commit |

### 2026-09-05 — FG-021 mixed-capture real-iPhone UAT PASS (docs only)

| Field | Content |
|-------|---------|
| Date | 2026-09-05 |
| Branch | `main` @ `25644d2e3910d1c06cf9d349dc8d0044a2ad98f7` (start) |
| Active ChatGPT development chat title | CalibAi Development — 4 Sep 2026 |
| Objective | Record already-performed mixed-capture UAT as PASS. Do not repeat the iPhone test. Do not create another Event/Original. |
| Business decision | **MIXED CAPTURE REAL-IPHONE UAT PASS.** One Event **35** with three Originals `{text, image, audio}` on Project **11**. Do not close FG-021. Do not repeat mixed capture. |
| Architectural decision | None. Short text remains Original `kind=text` (count-criteria conflict from the first mixed prompt is historical). ASCII hyphen in the text body vs operator em dash is not a product defect. |
| Prompt template used | Bounded FG-021 real-iPhone UAT docs-only record. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 MIXED CAPTURE DOCS-ONLY PASS RECORD / DO NOT REPEAT IPHONE TEST. |
| Files expected to change | Current/UAT records only. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; ADR; FG-022; master bytes; Legal Content Gate. |
| Implementation result | Event **35**, Project **11**, `ORG-001`, Joel Brayman `user_id` 1. Flask **556723** `06:52:40` Event **201** + three Original **201**. Original **33** text `FG-021 mixed capture UAT - 5 Sep 2026`. Original **34** `note.m4a` `audio/mp4` 190338 bytes SHA-256 `92d3896b7f88887dd33bd3dc443609a413e8581a8bb86d2b743de6258e5b6c5f`. Original **35** `image.jpg` JPEG JFIF 3076035 bytes SHA-256 `d3e947e6603e7d1dbd947634e0a603778de2e2688367266e3972f3d61f9c3bae`. Live **35** / **35**. Field Today **200**. Desktop Hub Event **35** **200**. Gate **NOT CLOSED**. |
| Tests | Docs: `git diff --check`; markdown links. Product pytest not run. Last product-changing suite remains 19 / 147 / 557. |
| Project-state-report update | Yes — PART B this-pass decision recorded. |
| Milestone entry update | No. |
| Constitutional issue raised | None. |
| Unresolved issues | Remaining FG-021 UAT: background/foreground; session-expiry; CSRF; older iPhone smoke; orientation/readability. Observation Delete **QUEUED**. FG-021 still OPEN. |
| Next approved step | STOP. Do not close FG-021. Do not repeat mixed capture. Do not start background/foreground in this pass. |
| Next approved prompt | None from this docs-only record. |
| Commit hash | this commit |

### 2026-09-05 — FG-021 genuine HEIC Files/Browse real-device UAT PASS

| Field | Content |
|-------|---------|
| Date | 2026-09-05 |
| Branch | `main` @ `32317deca6f25435c59a69dffef86103b6164811` (start) |
| Active ChatGPT development chat title | CalibAi Development — 4 Sep 2026 |
| Objective | Inspect server-side bytes after Joel independently confirmed Files source `IMG_5351.HEIC`, then Safari Choose Photo → Browse/Files → Save original. Classify genuine HEIC PASS / FAIL / NOT EXERCISED. Do not close FG-021. |
| Business decision | **HEIC REAL-DEVICE UAT PASS.** Genuine HEIC Original received and preserved. JPEG Compatible Rendition derived. Field Today and desktop Hub display the rendition. Do not close FG-021. Do not start mixed capture. |
| Architectural decision | None. Existing FG-020 Compatible Rendition path exercised. Original Source remains HEIC; display uses derived JPEG. Rendition is not a second Original. |
| Prompt template used | Bounded FG-021 real-iPhone UAT evidence inspection. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 GENUINE HEIC FILES-PATH UAT — FINAL SERVER-SIDE VERIFICATION. |
| Files expected to change | Current/UAT records only (PASS). Preserve historical library Choose Photo NOT EXERCISED. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; ADR; FG-022; master bytes; Legal Content Gate. |
| Implementation result | Event **34** / Original **32**, Project **11** (`FG-016 UAT — Unsupported Use (synthetic Ottawa garage)`), `ORG-001`, Joel Brayman `user_id` 1. Flask **556723** `06:36:56` Event **201** then Original **201**. Filename `IMG_5351.HEIC`; MIME `image/heic`; stored `ORG-001/11/34/32.heic`. Actual bytes ISO-BMFF HEIC (`ftyp` major `heic`; compatible `mif1` `MiHE` `MiPr` `miaf` `MiHB` `heic`), 1479610 bytes, SHA-256 `e042b2672cbb7170bcfeeefc74cb816dae72710c5bf937cf17a46b313851b319`. Rendition `ORG-001/11/34/32/display.jpg` JPEG JFIF 439618 bytes, SHA-256 `946ce4f6eaa4bab05616f664695ce81d9c1d7c3bffcf32ab231e45b060f9365c`. Original `/content` `image/heic` 1479610; `/display` `image/jpeg` 439618. Desktop Hub `/projects/11/field-events/34` **200**. Live **34** / **32**. One Event + one Original; no 409; rendition not counted as Original. iOS version To be verified. Gate **NOT CLOSED**. |
| Tests | Docs: `git diff --check`; markdown links. Product pytest not run. Last product-changing suite remains 19 / 147 / 557. |
| Project-state-report update | Yes — PART B this-pass decision recorded. |
| Milestone entry update | No. |
| Constitutional issue raised | None. |
| Unresolved issues | Mixed capture not tested. Background/foreground, session-expiry, CSRF recovery, older iPhone smoke, orientation/readability remaining. Observation Delete **QUEUED**. iOS/Safari version To be verified. FG-021 still OPEN. |
| Next approved step | STOP. Do not close FG-021. Do not start mixed capture. |
| Next approved prompt | None from this inspection pass. |
| Commit hash | this commit |

### 2026-09-05 — FG-021 HEIC library-photo UAT NOT EXERCISED

| Field | Content |
|-------|---------|
| Date | 2026-09-05 |
| Branch | `main` @ `236e6c19d18fad5d44ea5f2b4e9325792ecfd27e` (start) |
| Active ChatGPT development chat title | CalibAi Development — 4 Sep 2026 |
| Objective | Inspect server-side bytes after Joel’s High Efficiency native Camera → library → Field Web Choose Photo Save. Classify HEIC PASS / FAIL / NOT EXERCISED from actual Original bytes. Do not close FG-021. |
| Business decision | **HEIC UAT NOT EXERCISED.** Safari delivered JPEG. Do not classify HEIC PASS. HEIC remains OPEN. Do not start mixed capture. Do not repair. |
| Architectural decision | None. FG-020 Compatible Rendition path was not invoked (JPEG is browser-displayable). |
| Prompt template used | Bounded FG-021 real-iPhone UAT evidence inspection. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 HEIC REAL-IPHONE UAT — SERVER-SIDE EVIDENCE INSPECTION / CLASSIFICATION. |
| Files expected to change | Current/UAT records only (NOT EXERCISED, not PASS). |
| Files prohibited from changing | `app/`; `tests/`; Alembic; ADR-043; FG-022; master bytes; Legal Content Gate. |
| Implementation result | Event **33** / Original **31**, project **12** (`FG-018 UAT Actor Project`), `ORG-001`, Joel Brayman `user_id` 1. Flask **556723** `06:14:32` Event **201** then Original **201**. Filename `IMG_5350.jpeg`; stored `ORG-001/12/33/31.jpg`; MIME `image/jpeg`. **Actual bytes JPEG JFIF** (`FF D8 FF` + `JFIF`), 2691705 bytes, SHA-256 `2fbfe2217f22f727a0a76455b5fb07e8e65d0b403a7ff521c4c1f2b7c4ec66f0`. No HEIC/HEIF `ftyp`. No rendition dir. Field Today display GET **200** same JPEG length. Desktop Hub `/projects/12/field-events/33` **200**. Live **33** / **31**. One Event + one Original; no duplicate UUIDs. iOS version To be verified. Gate **NOT CLOSED**. |
| Tests | Docs: `git diff --check`; markdown links. Product pytest not run. Last product-changing suite remains 19 / 147 / 557. |
| Project-state-report update | Yes — PART B this-pass decision recorded. |
| Milestone entry update | No. |
| Constitutional issue raised | None. |
| Unresolved issues | HEIC/HEIF Original still **NOT EXERCISED** on real iPhone Safari. Mixed capture not tested. Observation Delete **QUEUED**. iOS/Safari version To be verified. FG-021 still OPEN. |
| Next approved step | STOP. Do not close FG-021. Do not start mixed capture. |
| Next approved prompt | None from this inspection pass. |
| Commit hash | this commit |

### 2026-09-05 — FG-021 real iPhone browser-close IndexedDB recovery UAT

| Field | Content |
|-------|---------|
| Date | 2026-09-05 |
| Branch | `main` @ `a38d9e4a26318cdcfe900e56da2e1d1566225fed` (start) |
| Active ChatGPT development chat title | CalibAi Development — 4 Sep 2026 |
| Objective | Observation-only real-iPhone UAT of ADR-043 PENDING CAPTURE → SAFARI CLOSE → REOPEN → INDEXEDDB RECOVERY → RETRY → exactly one Event + one Original → desktop continuity. JPEG (Event+Original). No product-code change. Do not close FG-021. |
| Business decision | Browser-close recovery **PASS**. Gate remains OPEN. HEIC / mixed capture / Observation Delete remain OPEN. Do not proceed to HEIC in this pass. |
| Architectural decision | None. Used existing Case A pending path (no Event POST until Capture reload) then `retryExisting` 201/201. Safari process-kill operator-attested. |
| Prompt template used | Bounded FG-021 real-iPhone UAT. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 REAL IPHONE UAT — BROWSER CLOSE → INDEXEDDB RECOVERY → IDEMPOTENT RETRY. |
| Files expected to change | Current/UAT records only. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; ADR-043; FG-022; master bytes; Legal Content Gate. |
| Implementation result | **REAL IPHONE BROWSER CLOSE → INDEXEDDB RECOVERY → RETRY PASS.** HTTPS `https://192.168.134.223:5443`. Take Photo JPEG. Flask **556723**: no Event POST after Capture GET `05:14:26` until Capture GET `05:19:01` then Event POST **201** and Original POST **201** at `05:19:02`. Today `05:18:10` still showed Events **27**/**28** only. Event **32** / Original **30**, project **11**, `ORG-001`, Joel Brayman `user_id` 1. `image/jpeg`, `image.jpg`, 2796786 bytes, JFIF, SHA-256 `4bbd4d2fa9b5a660a57bc2d60c32e094876023c91fa8705a6c6827e22c3e3155`. UUIDs `bdfd719f-d008-4ecf-957f-6168c6edefe5` / `586c19d4-e122-4bdf-be71-525ab2574e61`. One Event + one Original; no 409; no duplicate UUID rows. Live **32** / **30**. Desktop Hub `/projects/11/field-events/32` **200** (Photo + Original; Hub list links Event **32**). No separate text Original. Gate **NOT CLOSED**. |
| Tests | Docs: `git diff --check`; markdown links. Product pytest not run (docs-only UAT record). Last product-changing suite remains 19 / 147 / 557. |
| Project-state-report update | Yes — PART B brought forward to 2026-09-05. |
| Milestone entry update | No. |
| Constitutional issue raised | None. |
| Unresolved issues | HEIC real-device **NOT YET TESTED**. Mixed capture not tested. Observation Delete **QUEUED**. iOS/Safari version To be verified. Safari process-kill cannot be observed from Flask. FG-021 still OPEN. |
| Next approved step | STOP. Do not close FG-021. Do not proceed to HEIC in this pass. |
| Next approved prompt | None from this UAT pass. |
| Commit hash | this commit |

### 2026-09-04 — Govern CalibAi chat-title continuity convention

| Field | Content |
|-------|---------|
| Date | 2026-09-04 |
| Branch | `main` @ `46eab360d5f43c4f0c3397f8409dd7fee1fb2c79` (start) |
| Active ChatGPT development chat title | CalibAi Development — 4 Sep 2026 (working title until Joel confirms the exact UI title) |
| Objective | Record a permanent CalibAi continuity convention for originating ChatGPT chat-title traceability. Docs/governance only. |
| Business decision | Every CalibAi development response begins with the exact active ChatGPT chat title in bold and ends with `END — <title>` after any Cursor prompt. Turnovers must record ACTIVE CHAT TITLE and carry the rule forward. Standing next-prompt rule preserved. Traceability metadata only. |
| Architectural decision | None. Existing continuity and turnover documents hold the rule. No new policy file. No Feature Gate. No ADR. |
| Prompt template used | BRAYMAN — CALIBAI CONTINUITY CONVENTION GOVERNANCE UPDATE (documentation template). |
| Approved Cursor prompt summary | Record chat-title continuity in existing governance. Do not change product code, FG-021, or FG-022. |
| Files expected to change | Continuity protocol, turnover protocol, session-handoff, chat-workflow-log, AGENTS.md, development-workflow, platform-governance pointer, Cursor rules. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; FG-021; FG-022; master DOCX/PDF; Legal Content Gate registers. |
| Implementation result | Convention recorded. Two title systems distinguished (ChatGPT originating title vs Cursor `BRAYMAN — <Topic>`). |
| Tests | Docs: `git diff --check`; markdown links. Product pytest not run. |
| Project-state-report update | No — not a milestone. |
| Milestone entry update | No. |
| Constitutional issue raised | None. |
| Unresolved issues | Exact ChatGPT UI title not independently readable from Cursor; working title recorded until Joel confirms. FG-021 remaining UAT independently open. |
| Next approved step | STOP. Do not begin another feature from this pass. |
| Next approved prompt | None from this governance pass. |
| Commit hash | this commit |

### 2026-09-04 — Close FG-022 reusable approved document masters

| Field | Content |
|-------|---------|
| Date | 2026-09-04 |
| Branch | `main` @ `a09ba34e8f97c0a83af65490b9fd104f2996160f` (start) |
| Objective | Record Joel presentation-master approval and close FG-022. Docs only. |
| Business decision | Families 01–07 JOEL APPROVED as APPROVED REUSABLE MASTER FAMILY V1 for presentation use. Family 05 remains COMMERCIAL_DRAFT / NOT LEGALLY APPROVED / NOT FOR EXECUTION / NOT FOR SIGNATURE. Legal Content Gate empty. Neutralization-related pagination variances accepted. |
| Architectural decision | None new. Immutable source remains provenance. Reusable Master Template Family V1 is reusable presentation authority. Project / Estimate / Pricing records remain project-data authority. FG-012 / FG-017 / FG-021 unchanged. No migration. |
| Prompt template used | BRAYMAN — CALIBAI FG-022 FINAL JOEL APPROVAL / CLOSURE (documentation template). |
| Approved Cursor prompt summary | Advance register approval states; close FG-022; do not alter master bytes, source ZIP, product code, Legal Content Gate, or FG-021. |
| Files expected to change | Docs/register only. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; source ZIP/DOCX/PDF; derived master DOCX/PDF; FG-021 body; FG-012; FG-017. |
| Implementation result | FG-022 **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. Seven masters / seven PDFs hashes unchanged. |
| Tests | Docs: `git diff --check`; live hash MATCH vs register; source ZIP MATCH. Product pytest not run. Last product-changing suite remains 19 / 147 / 557. |
| Project-state-report update | Yes. |
| Milestone entry update | No — FG-022 has no M0xx. |
| Constitutional issue raised | None. |
| Unresolved issues | FG-017 raster vs recovered header unresolved. FG-021 remaining UAT independently open. Family 05 legal content not approved. |
| Next approved step | STOP. Do not begin another feature from this pass. |
| Next approved prompt | None from this closure pass. |
| Commit hash | this commit |

### 2026-09-04 — Implement FG-022 reusable document masters

| Field | Content |
|-------|---------|
| Date | 2026-09-04 |
| Branch | `main` @ `a855663675b71c3bf941652b2be983f32fa139c8` (start) |
| Objective | Extract project-neutral reusable visual masters from the governed Allen Jacques presentation family. |
| Business decision | Seven families EXTRACTED / SOURCE-VERIFIED / ZERO-RESIDUE VERIFIED / VISUALLY VERIFIED. Not JOEL APPROVED. Document 04 INTERNAL ENTRY REFERENCE. Document 05 COMMERCIAL_DRAFT / NOT FOR EXECUTION. Legal Content Gate empty. |
| Architectural decision | None new. DOCX visual masters in a separate durable directory. PDFs are verification only. FG-012 / FG-017 / FG-021 unchanged. No migration. |
| Prompt template used | BRAYMAN — CALIBAI FG-022 IMPLEMENTATION. |
| Approved Cursor prompt summary | Copy governed DOCX; neutralize Allen Jacques project content; preserve presentation; render Word PDFs; inspect every page; populate register; stop before Joel approval. |
| Files expected to change | Docs/register only. Derived binaries outside Git. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; source ZIP/DOCX/PDF; FG-021 body; FG-012; FG-017. |
| Implementation result | Seven DOCX + seven verification PDFs. Source ZIP SHA unchanged. Zero user-visible residue. Family 01 PDF 1 page (source was 2). |
| Tests | Docs: `git diff --check`; markdown links. Product pytest not run. Last product-changing suite remains 19 / 147 / 557. |
| Project-state-report update | Yes. |
| Milestone entry update | No. |
| Constitutional issue raised | None. |
| Unresolved issues | Joel presentation-master approval pending. FG-017 raster vs recovered header unresolved. FG-021 remaining UAT independently open. |
| Next approved step | STOP for Joel/ChatGPT review of the seven masters. |
| Next approved prompt | None from this implementation pass. |
| Commit hash | this commit |

### 2026-09-04 — Approve FG-022 reusable document template family

| Field | Content |
|-------|---------|
| Date | 2026-09-04 |
| Branch | `main` @ `aed1163cde86910f06a536c758b11d3b488d399b` (start) |
| Objective | Create and approve FG-022 for project-neutral extraction of the governed Allen Jacques presentation family. Docs/governance only. |
| Business decision | FG-022 is a parallel document-template track. Seven families 01–07. Document 04 INTERNAL ENTRY REFERENCE. Document 05 COMMERCIAL_DRAFT / NOT FOR EXECUTION. Legal Content Gate remains empty. Extraction not performed. Immutable source unchanged. |
| Architectural decision | No new ADR. Existing project-document, ADR-032 custody, ADR-040 Brand Profile, and Legal Content Gate boundaries are sufficient. DOCX visual masters. Derived store separate from immutable source. FG-012 / FG-017 / FG-021 unchanged. No migration. |
| Prompt template used | BRAYMAN — CALIBAI FG-022 GOVERNANCE. |
| Approved Cursor prompt summary | Create FG-022 if unused. Approve if consistent. Do not extract. Do not change product code, Legal Content Gate, FG-021, or source ZIP. |
| Files expected to change | Feature Gate, indexes, presentation/legal pins, current-state, session-handoff, roadmap, chat-workflow-log. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; source ZIP/DOCX/PDF; FG-021 body; FG-012; FG-017. |
| Implementation result | FG-022 created **APPROVED / IMPLEMENTATION NOT STARTED**. Empty V1 identity register. Extraction not performed. |
| Tests | Docs only: `git diff --check`; markdown links on changed files. Full pytest not run. Last product-changing suite remains 19 / 147 / 557. |
| Project-state-report update | Yes — PART B records FG-022 parallel track. |
| Milestone entry update | No. |
| Constitutional issue raised | None. Rule 1 satisfied without a new `app/` module: ownership stays on existing presentation / project-document pins. |
| Unresolved issues | Joel/ChatGPT must review FG-022 before authorizing extraction. FG-017 raster vs recovered header unresolved. FG-021 remaining UAT independently open. ChatGPT Library remains a logical collection path. |
| Next approved step | STOP for Joel/ChatGPT review of FG-022 before extraction. |
| Next approved prompt | None from this governance pass. |
| Commit hash | this commit |

### 2026-09-04 — Reconcile current CalibAi turnover state

| Field | Content |
|-------|---------|
| Date | 2026-09-04 |
| Branch | `main` @ `97f35fe757f0be99af9140693d2e12924659ec46` (start) |
| Objective | Bounded docs-only reconciliation of remaining CURRENT-STATE drift after presentation-source custody closure. |
| Business decision | FG-021 remains OPEN. Proven iPhone PASSes (text, screenshot PNG, Take Photo JPEG, voice Save, network retain/retry, desktop continuity) are current. HEIC / mixed / IndexedDB browser-close / Observation Delete remain OPEN. Presentation source custody CLOSED. Legal Content Gate empty. |
| Architectural decision | None new. ADR-043 remains Accepted. FG-012 / FG-017 / Native Signing / reusable extraction unchanged. |
| Prompt template used | BRAYMAN — CALIBAI POST-CUSTODY CURRENT-STATE DOCUMENTATION RECONCILIATION. |
| Approved Cursor prompt summary | Repair stale current-looking language only. Preserve historical snapshots. Do not implement. Do not close FG-021. Do not choose next UAT vs template extraction. |
| Files expected to change | Current-authority docs only. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; Feature Gate files except CURRENT FG-021 wording; approved presentation ZIP. |
| Implementation result | Stale CURRENT FG-021 PENDING / IMPLEMENTATION NOT STARTED / screenshot re-UAT pending / old test baselines repaired where they presented as today. Historical dated entries left. |
| Tests | Docs only: `git diff --check`; markdown links on changed files. Full pytest not run. Last product-changing suite remains 19 / 147 / 557. |
| Project-state-report update | Yes — PART B brought forward to 2026-09-04. |
| Milestone entry update | No (historical milestone rows left). |
| Constitutional issue raised | None. |
| Unresolved issues | Joel/ChatGPT still chooses remaining FG-021 UAT versus reusable-template extraction. ChatGPT Library remains a logical collection path. FG-017 raster vs recovered header unresolved. |
| Next approved step | STOP for Joel/ChatGPT review. |
| Next approved prompt | None from this reconciliation. |
| Commit hash | this commit |

### 2026-09-04 — Close approved document template custody gap

| Field | Content |
|-------|---------|
| Date | 2026-09-04 |
| Branch | `main` @ `acba785259fd705b56042b08b486be2319a22745` (start) |
| Objective | Close presentation-source custody so approved bytes no longer depend solely on Desktop. Docs + durable exact ZIP copy. No Git binaries. No product code. |
| Business decision | Exact recovered ZIP remains byte-level presentation authority. Documents 01–07 classifications unchanged. Document 04 INTERNAL ENTRY REFERENCE. Document 05 COMMERCIAL_DRAFT / NOT APPROVED. Legal Content Gate empty. Reusable extraction not performed. |
| Architectural decision | Git remains identity authority. Durable byte store: `/Users/joelbrayman/Documents/CalibAi/Approved Document Templates/Allen Jacques Presentation Baseline - 2026-09-03/`. ChatGPT Library logical collection recorded; Cursor does not write ChatGPT Library objects. Desktop ZIP left in place as provenance. Not `instance/`. FG-012 / FG-017 / FG-021 unchanged. |
| Prompt template used | BRAYMAN — CALIBAI APPROVED DOCUMENT TEMPLATE CUSTODY CLOSURE. |
| Approved Cursor prompt summary | Verify ZIP SHA and 17-member manifest; copy exact original ZIP to durable store; update custody docs; commit/push docs only. |
| Files expected to change | Docs/governance only. Durable ZIP outside Git. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; Feature Gates; ADRs; FG-021; Native Signing; Speakeasy documents. |
| Implementation result | SOURCE ZIP SHA MATCH. 17/17 members PASS. Families 01–07 PASS. Durable copy SHA match. Original ZIP unmodified. No extraction. |
| Tests | Docs/custody only: `git diff --check`; member SHA verification. Full pytest not run. |
| Project-state-report update | No (not a coded milestone). |
| Milestone entry update | No |
| Constitutional issue raised | None. Legal Content Gate not populated. |
| Unresolved issues | ChatGPT Library is a logical collection path, not a Cursor-writable filesystem. FG-017 raster vs recovered header still unresolved. Reusable template extraction not authorized. Broader FG-021/test-count doc drift remains for a separate reconciliation prompt. |
| Next approved step | STOP. Do not extract reusable templates. Do not continue FG-021 from this pass. |
| Next approved prompt | None from this custody closure. |
| Commit hash | (filled after commit) |

### 2026-09-03 — Commit recovered Allen Jacques approved document presentation baseline

| Field | Content |
|-------|---------|
| Date | 2026-09-03 |
| Branch | `main` @ `0547bd5` (parent) |
| Objective | Docs-only governance commit of the recovered presentation pin/manifest. No binaries. No product code. |
| Business decision | Joel/ChatGPT: Allen Jacques package is the first project using the approved presentation family. 01–07 APPROVED PRESENTATION REFERENCES (design only). Document 04 = INTERNAL ENTRY REFERENCE. Document 05 legal = COMMERCIAL_DRAFT / NOT APPROVED. |
| Architectural decision | ADR-032 leave-in-place Desktop ZIP; SHA identity in Git. Recovered presentation raster is reconstruction reference; FG-017 raster question unresolved. FG-012 renderers current but materially different. |
| Prompt template used | BRAYMAN — COMMIT RECOVERED APPROVED DOCUMENT PRESENTATION BASELINE. |
| Approved Cursor prompt summary | Verify ZIP SHA; classify 04 as INTERNAL ENTRY REFERENCE; preserve 05 COMMERCIAL_DRAFT; commit/push docs only; do not copy binaries. |
| Files expected to change | Docs/governance only. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; Desktop ZIP; FG-021 product. |
| Implementation result | Pin + manifest committed. Original ZIP unmodified. No DOCX/PDF in Git. |
| Tests | Not run (docs-only). |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None. Legal Content Gate not populated. |
| Unresolved issues | Brand Profile / FG-017 raster vs recovered 2048×819 letterhead. Reusable template extraction not authorized. Product renderer reconciliation with this baseline is future governance. |
| Next approved step | Separate estimate-generation chat may use recovered files as presentation authority; current workbook remains data authority. Do not generate that estimate from this commit. |
| Next approved prompt | None from this commit for product code. |
| Commit hash | (filled after commit) |

### 2026-09-03 — Govern recovered Allen Jacques document presentation baseline

| Field | Content |
|-------|---------|
| Date | 2026-09-03 |
| Branch | `main` @ `0547bd5` (parent) |
| Objective | Close artifact-custody gap: record recovered Desktop ZIP as approved **presentation** baseline. Docs/governance only. No binaries in Git. |
| Business decision | Joel: first project using the approved document presentation family. Presentation/design approved. Legal content of document 05 remains COMMERCIAL_DRAFT. |
| Architectural decision | ADR-032-class custody: leave-in-place Desktop bytes; SHA-256 identity in Git. Do not use `instance/` product stores. Do not commit DOCX/PDF. |
| Prompt template used | BRAYMAN — GOVERN RECOVERED APPROVED DOCUMENT PRESENTATION BASELINE. |
| Approved Cursor prompt summary | Verify ZIP SHA; forensic presentation extraction; classify 01–07; Legal Content Gate unchanged; no template extraction; no estimate generation. |
| Files expected to change | Docs only. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; Desktop ZIP; FG-021 product. |
| Implementation result | Pin + manifest written. Original ZIP unmodified. FG-017 logo vs recovered header image recorded as different SHA. FG-012 renderers recorded as material visual mismatch. |
| Tests | Not run (docs-only). |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None. Legal Content Gate not populated. |
| Unresolved issues | Whether later Brand Profile / Proposal PDF should use recovered 2048×819 letterhead vs FG-017 `948f96e0…`. Reusable template extraction not authorized. |
| Next approved step | Docs-only commit authorized in the subsequent COMMIT prompt. |
| Next approved prompt | BRAYMAN — COMMIT RECOVERED APPROVED DOCUMENT PRESENTATION BASELINE. |
| Commit hash | (see subsequent commit entry) |

### 2026-09-03 — FG-021 real iPhone network retain / retry PASS (text)

| Field | Content |
|-------|---------|
| Date | 2026-09-03 |
| Branch | `main` @ `f7bd8c1` |
| Objective | Observation-only real-iPhone UAT of ADR-043 NETWORK INTERRUPTION → LOCAL RETENTION → NEEDS RETRY → RESTORE → RETRY → one Event + one Original. Text only. No product-code change. |
| Business decision | Stop after PASS. Do not close FG-021. Do not start mixed capture, HEIC, Observation Delete, or a second capture. |
| Architectural decision | None. Case A: Wi-Fi off before Save; no Event POST until Retry. Safari fetch `Load failed` shown in Capture feedback; top status **NEEDS RETRY**. Stored body `FG021 Network Retry UAT` (iPhone casing; instructed ALL CAPS). |
| Prompt template used | FG-021 real iPhone network retain / retry UAT (observation only). |
| Approved Cursor prompt summary | BRAYMAN — FG-021 REAL IPHONE NETWORK RETAIN / RETRY UAT. |
| Files expected to change | UAT docs only. |
| Files prohibited from changing | `app/`; `tests/`; Alembic; CSRF; auth. |
| Implementation result | **REAL IPHONE NETWORK RETAIN / RETRY PASS.** HTTPS `https://192.168.134.223:5443`. Offline Save: no Flask Event POST. Today: **Needs Retry** / `1 capture needs retry.` Retry: Flask **855195** `14:02:16` Event POST **201** then Original POST **201**. Event **31** / Original **29**, project **11**, `ORG-001`, Joel Brayman `user_id` 1. `client_capture_uuid` `532871ae-db01-4263-8562-d64baf4aa00e`; `client_original_uuid` `022fe42b-8e8f-421b-a159-0c01eae15667`. One text Original; no duplicate Event for this capture. Live **31** / **29**. Desktop Hub `/projects/11/field-events/31` **200** after Mac login (`next` preserved). Joel confirmed Field observation **31** and the same text. Gate **NOT CLOSED**. |
| Tests | Not re-run (observation only). Last product suite remains dedicated FG-021 **19** / focused **147** / full **557**. |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None |
| Unresolved issues | HEIC real-device **NOT YET TESTED**. Mixed capture not tested. Observation Delete **QUEUED**. Offline feedback uses Safari `Load failed` (status still NEEDS RETRY). Mac HTTPS needs login + local CA trust. FG-021 still OPEN. |
| Next approved step | Joel/ChatGPT review. Do not close FG-021. |
| Next approved prompt | None from this UAT. |
| Commit hash | (this commit) |

### 2026-09-03 — FG-021 real iPhone voice Save PASS (audio/mp4)

| Field | Content |
|-------|---------|
| Date | 2026-09-03 |
| Branch | `main` @ `f7bd8c1` |
| Objective | Observation-only retest of voice Save after audio IndexedDB Uint8Array repair. No product-code change. |
| Business decision | Stop after PASS. Do not close FG-021. Do not start mixed capture, HEIC, retry, or Observation Delete. |
| Architectural decision | None. Actual iPhone MIME was `audio/mp4` / `note.m4a`. |
| Prompt template used | FG-021 post-audio-repair real iPhone voice retest only. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 POST-AUDIO-REPAIR REAL IPHONE VOICE RETEST ONLY. |
| Files expected to change | UAT docs only. |
| Files prohibited from changing | `app/`; `tests/`; Alembic. |
| Implementation result | **REAL IPHONE VOICE SAVE PASS.** Event **30** / Original **28**. `audio/mp4`, `note.m4a`, 179117 bytes, SHA `f248655624f1f84f9c80a61cb7623443d96afd40069fdca29406f76a6072c1f9`. Flask **420792** Event 201 then Original 201 at `07:44:50`. Event **29** empty leftover at `07:44:11`. Live **30** / **28**. Gate **NOT CLOSED**. |
| Tests | Not re-run (observation only). |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None |
| Unresolved issues | HEIC real-device, mixed capture, retry, Observation Delete, FG-021 still OPEN. |
| Next approved step | Joel/ChatGPT review. |
| Next approved prompt | None from this retest. |
| Commit hash | (this commit) |

### 2026-09-03 — FG-021 persist Field audio bytes in IndexedDB for Safari

| Field | Content |
|-------|---------|
| Date | 2026-09-03 |
| Branch | `main` @ `207bcf1` (parent) |
| Objective | Bounded audio IndexedDB persist repair: Blob → arrayBuffer → Uint8Array, reconstruct Blob only for multipart POST. |
| Business decision | Do not close FG-021. Voice Save re-UAT required. No conversion/transcription. |
| Architectural decision | Share `bytesFromBlob()` for image and audio. ADR-043 retain-until-ACK preserved. |
| Prompt template used | Bounded audio IndexedDB persist repair. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 BOUNDED AUDIO INDEXEDDB PERSIST REPAIR. |
| Files expected to change | `app/static/js/field.js`; `tests/test_field_web_fg021.py`; FG-021 UAT docs. |
| Files prohibited from changing | migrations; CSRF; auth; Observation Delete; HTTPS certs. |
| Implementation result | `bytesFromBlob` + `normalizeImageOriginals` now converts audio Blobs to `row.bytes` and deletes `row.blob`. `fileBlobForUpload` reconstructs audio from bytes. Dedicated **19**. Focused **147**. Full **557**. Alembic still `d2e3f4a5b6c7`. Live DB not mutated. Gate **NOT CLOSED**. |
| Tests | Dedicated 19 passed. Focused 147 passed. Full 557 passed. |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None |
| Unresolved issues | Voice Save re-UAT pending. HEIC, retry, Observation Delete still open. |
| Next approved step | Hard-refresh Capture; voice-only Save on `https://192.168.134.223:5443`. |
| Next approved prompt | None until voice Save UAT result. |
| Commit hash | (this commit) |

### 2026-09-03 — FG-021 HTTPS iPhone voice Record/playback PASS, Save FAIL

| Field | Content |
|-------|---------|
| Date | 2026-09-03 |
| Branch | `main` @ `207bcf1` |
| Objective | Record exact HTTPS voice Save error after Record/playback succeeded. No product-code repair. |
| Business decision | Stop. Do not auto-repair audio IndexedDB persist. Do not close FG-021. |
| Architectural decision | None implemented. Audio still stored as IndexedDB Blob; images use `Uint8Array` bytes. |
| Prompt template used | FG-021 local HTTPS / voice UAT. |
| Approved Cursor prompt summary | BRAYMAN — RESUME FG-021 DOC RECONCILIATION → LOCAL HTTPS → VOICE UAT (Save-error capture). |
| Files expected to change | current-state; session-handoff; chat-workflow-log; FG-021; platform-roadmap (UAT fact only). |
| Files prohibited from changing | `app/`; `tests/`; Alembic; CSRF; auth. |
| Implementation result | HTTPS origin `https://192.168.134.223:5443` (`.local` Yahoo-search). Trust ON. Login/Capture worked. Record + playback **PASS**. Save error exact product text: `Cannot safely keep this capture on this phone. Try photo or text later, or free storage.` No Event/Original POST on Flask **510616**. Live DB **28** / **27**. Gate **NOT CLOSED**. |
| Tests | Not re-run (observation/docs only). |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None |
| Unresolved issues | Voice Save blocked at IndexedDB persist of audio Blob. HEIC, retry, Observation Delete still open. |
| Next approved step | Joel/ChatGPT review. Do not auto-repair. |
| Next approved prompt | None from this observation. |
| Commit hash | (docs; uncommitted) |

### 2026-09-02 — FG-021 local HTTPS UAT setup started (voice enablement only)

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ `6e7a8ef` (`6e7a8efe8e618844dae1cfae36621d44d8bf5112` = `origin/main` at setup start) |
| Objective | Start local HTTPS for real iPhone Safari secure-context voice UAT. No product-code change. |
| Business decision | Do not close FG-021. Do not claim voice PASS or iPhone trust complete. Do not kill HTTP 5014. |
| Architectural decision | Flask `--cert`/`--key` with openssl local CA + leaf. Certs outside git. Chosen origin `https://Joels-MacBook-Air.local:5443`. IndexedDB is origin-scoped; HTTP and HTTPS are different origins; no HTTP voice pending to migrate. |
| Prompt template used | FG-021 local HTTPS real iPhone UAT setup — voice enablement only. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 LOCAL HTTPS REAL IPHONE UAT SETUP — VOICE ENABLEMENT ONLY. |
| Files expected to change | session-handoff; current-state; chat-workflow-log (in-progress note only). |
| Files prohibited from changing | `app/`; `tests/`; Alembic; CSRF; auth; Observation Delete; PWA; transcription; AI. |
| Implementation result | Local CA + leaf generated at `/Users/joelbrayman/Desktop/CalibAi-UAT-TLS/` (outside git). Leaf SAN `DNS:Joels-MacBook-Air.local`, `IP:192.168.134.223`. Public CA `CalibAi-UAT-Local-CA.cer`. HTTP **5014** Flask **562293** left running. HTTPS Flask listening on **5443**. `curl -k` login **200**. Voice **NOT** claimed PASS. Gate **NOT CLOSED**. |
| Tests | Not re-run (docs + environment only). Preflight: `lsof` 5443 listen; HTTP 5014 still listen. |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None |
| Unresolved issues | iPhone CA install / trust / login / voice UAT not started. HEIC, retry, Observation Delete still open. |
| Next approved step | Get `CalibAi-UAT-Local-CA.cer` onto the iPhone (AirDrop). Do not browse HTTPS yet. Do not start voice. |
| Next approved prompt | None from this setup pass. |
| Commit hash | (docs; this increment) |

### 2026-09-02 — FG-021 secure-context UAT investigation (HTTPS not implemented)

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ `1422279` (`1422279598af5a16e770844494e7f8954a761838` = `origin/main`) |
| Objective | Read-only / environment-only investigation of the smallest safe way to run existing FG-021 Field Web on a real iPhone Safari secure origin for microphone UAT. |
| Business decision | Do not start HTTPS. Do not install mkcert, certs, or iPhone profiles. Do not close FG-021. Next is Joel/ChatGPT review. |
| Architectural decision | None implemented. Existing pin confirmed: `getUserMedia` requires a secure context (HTTPS or localhost). HTTP LAN IP is not a secure context. IndexedDB is origin-scoped. |
| Prompt template used | Investigation / environment-only (no product-code change). |
| Approved Cursor prompt summary | BRAYMAN — FG-021 SECURE-CONTEXT INVESTIGATION — READ-ONLY / ENVIRONMENT-ONLY. |
| Files expected to change | current-state; session-handoff; chat-workflow-log; FG-021; platform-roadmap (investigation findings only). |
| Files prohibited from changing | `app/`; `tests/`; Alembic; CSRF; auth; Observation Delete; HTTPS/PWA; transcription; AI; database writes. |
| Implementation result | HTTPS **NOT IMPLEMENTED**. Product code / tests / DB / migration **unchanged**. Alembic current = head **`d2e3f4a5b6c7`**. `which mkcert` failed; `CAROOT` unset; `cryptography` not installed. OpenSSL LibreSSL **3.3.6** at `/usr/bin/openssl`. Flask 3.1.3 `flask run --cert` / `--key` supported; current UAT **562293** is HTTP-only `--host=0.0.0.0 --port=5014`. No existing trusted cert files. No nginx/caddy; stock `httpd` not running. Bonjour `Joels-MacBook-Air.local`. Smallest later local path: Flask `--cert`/`--key` + SAN-matching hostname + iOS CA profile + Certificate Trust Settings. No voice pending created on HTTP origin (Save never reached). Record can appear tappable when voice APIs missing (captured, not repaired). Gate **NOT CLOSED**. |
| Tests | Not re-run (docs/investigation only). Preflight: `git diff --check` clean; `flask db current` / `heads` = `d2e3f4a5b6c7`. |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None |
| Unresolved issues | Voice UAT still blocked until authorized local HTTPS. HEIC, retry, Observation Delete still open. iPhone IndexedDB contents To be verified from device. |
| Next approved step | Joel/ChatGPT review. Do not start HTTPS until a separate local-HTTPS UAT prompt is authorized. |
| Next approved prompt | None from this investigation. Do not start HTTPS. |
| Commit hash | (docs; uncommitted) |

### 2026-09-02 — FG-021 real iPhone voice UAT blocked at Record tap

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ `1422279` |
| Objective | Observation-only diagnose of Joel-reported iPhone Safari Record tap that does nothing. No product-code change. |
| Business decision | Stop at Record-tap failure. Do not repair HTTP microphone. Do not close FG-021. Preserve Take Photo JPEG PASS. Do not claim HEIC. |
| Architectural decision | None. Existing pin: `getUserMedia` requires a secure context (HTTPS or localhost). |
| Prompt template used | UAT observe / voice Record tap. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 REAL IPHONE VOICE UAT — OBSERVATION ONLY. |
| Files expected to change | current-state; session-handoff; chat-workflow-log; FG-021; platform-roadmap (UAT fact only). |
| Files prohibited from changing | Product code; Alembic; CSRF; auth; Observation Delete; HTTPS/PWA; transcription; AI. |
| Implementation result | Record tap produced no recording-state UX and no reported permission prompt. Flask **562293**: last Event/Original POST remains `14:43:26`/`14:43:27` Event **28** / Original **27**. Capture `GET` at `14:52:41` from `192.168.134.202` with **no** later POST. Live DB **28** Events / **27** Originals; Event **26** empty; no new Project 11 audio Original. Alembic current = head **`d2e3f4a5b6c7`**. Most likely: `enableVoice()` disables `#field-record` when media APIs missing on HTTP LAN. **VOICE UAT BLOCKED — SECURE CONTEXT INVESTIGATION REQUIRED.** Gate **NOT CLOSED**. |
| Tests | Not re-run (docs/observation only). Live SQLite read-only + Flask **562293** + `flask db current`. |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None |
| Unresolved issues | Voice blocked pending secure-context investigation. Retry, HEIC, Observation Delete still open. |
| Next approved step | Joel/ChatGPT authorize a bounded secure-context investigation. Do not retry voice on `http://LAN-IP:5014`. |
| Next approved prompt | None from this observation pass. |
| Commit hash | (docs; uncommitted) |

### 2026-09-02 — FG-021 real iPhone Take Photo JPEG PASS

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ `1422279` |
| Objective | One Take Photo UAT after screenshot PASS. No code. No voice. No delete. |
| Business decision | Record actual MIME from live Original. Do not claim HEIC. Stop after PASS. |
| Architectural decision | None. |
| Prompt template used | UAT continue / Take Photo. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 IPHONE UAT CONTINUE — TAKE PHOTO — REAL CAMERA PATH. |
| Files expected to change | session-handoff; chat-workflow-log; current-state/FG-021 status (UAT fact). |
| Files prohibited from changing | Product code; Alembic; CSRF; auth; Observation Delete. |
| Implementation result | Event **28** / Original **27**. `image/jpeg` 3568736 bytes `image.jpg`. Flask 201/201 at 14:43. Hub Event Detail displays JPEG. **REAL IPHONE TAKE PHOTO: PASS.** HEIC **not** exercised. Gate **NOT CLOSED**. |
| Tests | Not re-run. Live SQLite + Flask **562293** + authenticated Hub GET. |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None |
| Unresolved issues | Voice, retry, HEIC camera-if-produced, Observation Delete still open. Event **26** remains originals-empty (prior retry artifact). |
| Next approved step | Joel/ChatGPT review. Do not start voice until authorized. |
| Next approved prompt | None from this UAT pass. |
| Commit hash | (docs; uncommitted) |

### 2026-09-02 — FG-021 persist image Uint8Array in IndexedDB

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ parent `33bac00` |
| Objective | Bounded IndexedDB image-bytes repair: persist Uint8Array, reconstruct Blob only for POST. Do not close FG-021. |
| Business decision | File→Blob was insufficient on real iPhone Safari screenshots. Store raw bytes instead. |
| Architectural decision | ADR-043 persist-before-POST unchanged. No skip-IDB. No HEIC convert. Text path unchanged. Audio still Blob. |
| Prompt template used | Bounded client repair. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 BOUNDED INDEXEDDB IMAGE-BYTES REPAIR — ArrayBuffer/Uint8Array persistence. |
| Files expected to change | `app/static/js/field.js`; `tests/test_field_web_fg021.py`; status docs. |
| Files prohibited from changing | Alembic; CSRF; auth; Observation Delete; live schema. |
| Implementation result | `bytesFromImageFile` + `row.bytes` Uint8Array; `fileBlobForUpload` reconstructs Blob; FormData still uses filename. Gate **NOT CLOSED**. |
| Tests | Dedicated FG-021 **17 passed**. Focused **145 passed**. Full **555 passed**. Cursor Terminal. |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None |
| Unresolved issues | Small-screenshot iPhone re-UAT not yet run against this JS. |
| Next approved step | Close Capture tab, reopen, CHOOSE PHOTO one small screenshot, Save. |
| Next approved prompt | None until that UAT result. |
| Commit hash | (pending) |

### 2026-09-02 — FG-021 screenshot re-UAT FAIL after File→Blob repair

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ `33bac00` (`ada1b7c` repair parent) |
| Objective | Observe three screenshot Save attempts after File→Blob repair. Do not patch unless separately authorized. |
| Business decision | STOP. File→Blob did not get screenshots into the office. Do not skip IndexedDB. ChatGPT reviews ArrayBuffer/Uint8Array persist. |
| Architectural decision | None implemented. Candidate: persist image bytes as ArrayBuffer/Uint8Array in IndexedDB; reconstruct Blob only for multipart POST. |
| Prompt template used | UAT observe / no product code. |
| Approved Cursor prompt summary | Joel reported same storage error on three screenshots. Inspect Flask + live DB. Do not implement a second repair from this message. |
| Files expected to change | session-handoff; chat-workflow-log (UAT fact). |
| Files prohibited from changing | Product code; Alembic; CSRF; auth; Observation Delete. |
| Implementation result | Live **25/25**. Events **19–25** text-only. No image Originals. Same UI storage message. Text notes (`Test 6`/`Test 7`) POSTed; screenshots did not. Gate **NOT CLOSED**. |
| Tests | Not re-run. Read-only SQLite + Flask **562293**. |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None |
| Unresolved issues | Safari IndexedDB still rejects image Blob/File put. Safari console exception not captured. |
| Next approved step | Paste CASE to ChatGPT. Do not try more photos until a new repair is authorized. |
| Next approved prompt | Bounded IDB persist as ArrayBuffer/Uint8Array — **only if ChatGPT authorizes**. |
| Commit hash | (docs; uncommitted) |

### 2026-09-02 — FG-021 capture: iPhone swipe-left Delete UX (queued)

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` |
| Objective | Capture Joel’s iPhone Recent Observation Delete UX. Do not implement. Do not interrupt IndexedDB photo-put repair. |
| Business decision | Field: tap opens; swipe left reveals Delete; tap Delete then confirm; then governed deletion. Swipe is not delete. Accessible non-swipe equivalent required. Desktop: no swipe; conventional Delete. Native iPhone patterns where they fit the task. |
| Architectural decision | **None.** UX does not choose hard delete / tombstone / UAT cleanup. Retention recon still required. |
| Prompt template used | Requirement capture / UX clarification. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 UAT REQUIREMENT CLARIFICATION — IPHONE RECENT OBSERVATIONS — SWIPE LEFT TO DELETE. Capture only. Continue photo-put repair. Do not delete observations. FG-021 stays OPEN. |
| Files expected to change | Capture note; chat-workflow-log; session-handoff pointer. |
| Files prohibited from changing | Product deletion code; live observations; Alembic; CSRF; auth. |
| Implementation result | Recorded in [architecture/fg-021-recent-observation-delete-requirement-capture.md](architecture/fg-021-recent-observation-delete-requirement-capture.md). **No Delete UI. No rows deleted.** |
| Tests | Not applicable (docs capture). |
| Project-state-report update | No |
| Milestone entry update | No |
| Constitutional issue raised | None |
| Unresolved issues | Record-retention model still unchosen. Photo re-UAT still required first. |
| Next approved step | Small-JPEG iPhone re-UAT of the photo-put repair. Then Joel/ChatGPT review of deletion capture. |
| Next approved prompt | None for Delete. Photo re-UAT is the next physical action. |
| Commit hash | (pending) |

### 2026-09-02 — FG-021 IndexedDB photo-put repair (File→ArrayBuffer→Blob)

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ parent `4cb07bee1d6f004d0cb67110d17350893a646f13` |
| Objective | Bounded Safari HTTP LAN IndexedDB photo-put repair. Do not close FG-021. |
| Business decision | Persist image bytes as Blob (not library File) so small CHOOSE PHOTO can retain-until-ACK. |
| Architectural decision | ADR-043 unchanged: persist before POST. No skip-IDB. No HEIC client convert. Filename/MIME stay metadata. Audio not converted. Console persist-stage logging only. |
| Prompt template used | Bounded client repair. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 BOUNDED INDEXEDDB PHOTO-PUT REPAIR — File → ArrayBuffer → Blob. Tests + docs. Commit/push if tests pass. |
| Files expected to change | `app/static/js/field.js`; `tests/test_field_web_fg021.py`; current-state; session-handoff; chat-workflow-log; FG-021; roadmap. |
| Files prohibited from changing | Alembic; models; CSRF; auth; live DB rows; HEIC conversion; PWA. |
| Implementation result | `blobFromBinary` + `normalizeImageOriginals` before `persistCapture`. `putStore` classifies `idb_open` / `idb_put` / quota. Gate **NOT CLOSED**. |
| Tests | Dedicated FG-021 **17 passed**. Focused **145 passed**. Full **555 passed**. Cursor Terminal. |
| Project-state-report update | No — not a milestone close. |
| Milestone entry update | No |
| Constitutional issue raised | None |
| Unresolved issues | Small-JPEG iPhone re-UAT not yet run against this JS. |
| Next approved step | Hard-refresh Capture; CHOOSE PHOTO one small screenshot/JPEG; Save. |
| Next approved prompt | Observation Delete — **not authorized**. See capture note. |
| Commit hash | (pending) |

### 2026-09-02 — FG-021 small JPEG CHOOSE PHOTO Save FAIL BEFORE POST (CASE B)

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ HEAD `4cb07bee1d6f004d0cb67110d17350893a646f13` |
| Objective | One diagnostic iPhone CHOOSE PHOTO (small screenshot/JPEG) after desktop Event 18 PASS. Observe IndexedDB vs POST. Do not repair. Do not close FG-021. |
| Business decision | CASE B: same local IndexedDB storage message on a small library image. Stop iPhone actions. ChatGPT reviews bounded File→ArrayBuffer→Blob repair before any code change. |
| Architectural decision | None implemented. Candidate (not applied): normalize photo `File` → `ArrayBuffer` → `Blob` before IndexedDB put; preserve MIME/bytes; filename metadata separate; retain-until-ACK; no skip-IDB; no client HEIC conversion. |
| Prompt template used | UAT continue / one diagnostic (no product code). |
| Approved Cursor prompt summary | BRAYMAN — FG-021 IPHONE UAT CONTINUE — ONE DIAGNOSTIC IMAGE TEST — NO REPAIR YET. Desktop Event 18 first (already PASS). Then CHOOSE PHOTO one small screenshot/JPEG, Save, inspect live DB/Flask. CASE A vs CASE B. Do not implement File→Blob from this prompt. |
| Files expected to change | session-handoff; current-state; chat-workflow-log; FG-021 gate status; platform-roadmap (UAT fact only). |
| Files prohibited from changing | Product code; Alembic; live schema; CSRF; auth; Event 18 / Original 18 rows; UUID repair; Native Signing; Closeout. |
| Implementation result | Joel reported the same IndexedDB message as the prior photo attempt. Live SQLite still **18/18**. Event **18** / Original **18** unchanged (`FG021-IPHON-UAT-TEXT`). Flask **562293**: last iPhone POST remains `13:02:30` (Event 18); **no** field-events POST for this attempt. **SMALL JPEG INDEXEDDB / SAVE: FAIL BEFORE POST.** Product code unchanged. Gate **NOT CLOSED**. |
| Tests | Not re-run. Read-only SQLite + Flask log inspect. |
| Project-state-report update | No — not a milestone close. |
| Milestone entry update | No — gate not closed. |
| Constitutional issue raised | None |
| Unresolved issues | Photo IndexedDB put on Safari HTTP LAN. Exact Safari `DOMException` not logged. Chosen file name/MIME/size not captured. Preview yes/no not reported. |
| Next approved step | Paste CASE B report to ChatGPT. Do not start another iPhone action. Do not implement File→Blob until a separate approved Cursor prompt. |
| Next approved prompt | Bounded IndexedDB photo-put repair (File→ArrayBuffer→Blob) — **only if ChatGPT authorizes**. |
| Commit hash | (docs only; uncommitted) |

### 2026-09-02 — FG-021 desktop Event 18 continuity PASS; small-image diagnostic pending

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ HEAD `4cb07bee1d6f004d0cb67110d17350893a646f13` |
| Objective | Desktop continuity of Event 18 before one iPhone CHOOSE PHOTO diagnostic. Do not repair. Do not close FG-021. |
| Business decision | Ask Joel for one small library JPEG/screenshot only after desktop Event 18 is still the same record. Do not invent iPhone image results. |
| Architectural decision | None. Verification only. No File→Blob. No product-code change. |
| Prompt template used | UAT continue / one diagnostic (no product code). |
| Approved Cursor prompt summary | BRAYMAN — FG-021 IPHONE UAT CONTINUE — ONE DIAGNOSTIC IMAGE TEST — NO REPAIR YET. Verify Event 18 on desktop Hub + live SQLite. If PASS, one iPhone CHOOSE PHOTO (small screenshot/JPEG) then Save. Do not implement File→Blob. Do not close FG-021. |
| Files expected to change | session-handoff; current-state; chat-workflow-log (factual UAT-continue note only). |
| Files prohibited from changing | Product code; Alembic; live schema; CSRF; auth; Event 18 / Original 18 rows; UUID repair; Native Signing; Closeout. |
| Implementation result | Desktop continuity **PASS**. Hub Field Observations: one row → Event **18**, actor **Joel Brayman**, originals `text`, Current. Event Detail text exact `FG021-IPHON-UAT-TEXT`. SQLite **18/18**; Event **18** project **11** / `ORG-001` / `user_id` 1; no duplicate text row. Flask **562293** no POST after `13:02:30`. Image diagnostic **not run** — pending Joel. Gate **NOT CLOSED**. |
| Tests | Not re-run this pass. Browser MCP could not open a tab; Hub verified via authenticated GET of rendered `/projects/11` and `/projects/11/field-events/18` on port **5014**. |
| Project-state-report update | No — not a milestone close. |
| Milestone entry update | No — gate not closed. |
| Constitutional issue raised | None |
| Unresolved issues | Photo / IndexedDB quota still open. Small-image iPhone Save not attempted this pass. |
| Next approved step | Joel: CHOOSE PHOTO one small screenshot or known JPEG, then Save. Report preview yes/no and SAVING/SAVED/error text. Do **not** TAKE PHOTO. Do **not** attach full-size HEIC. |
| Next approved prompt | After a real small-image attempt: write the small-image diagnostic report (CASE A or CASE B). Do not implement File→Blob unless CASE B and separately approved. |
| Commit hash | (docs only; uncommitted) |

### 2026-09-02 — FG-021 iPhone Safari text-only UAT verified PASS

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` |
| Objective | Objectively verify Joel-reported iPhone Safari FG-021 text-only Save (`FG021-IPHON-UAT-TEXT`, no photo) against live SQLite and Flask logs. Do not close the gate. |
| Business decision | UUID repair + text path may be marked PASS only if live Event/Original rows and Flask 201/201 match. Photo / IndexedDB quota remains open. |
| Architectural decision | None. Verification only. |
| Prompt template used | UAT verification (no product code). |
| Approved Cursor prompt summary | BRAYMAN — verify iPhone Safari FG-021 text-only capture against live `instance/brayman_estimator.db` (prior 17/17) and Flask logs ~13:00–13:02 `192.168.134.202` POST field-events 201. Confirm Event/Original ids, client UUIDs, ORG-001, actor, occurred_at. FG-021 stays OPEN. One next action only: do not attach full-size HEIC. |
| Files expected to change | current-state; session-handoff; chat-workflow-log; FG-021 status notes. |
| Files prohibited from changing | Product code; Alembic; live schema; CSRF; auth; Native Signing; Closeout. |
| Implementation result | Verified. Live counts **18/18**. Event **18** / Original **18** on project **11** / `ORG-001`. Text exact `FG021-IPHON-UAT-TEXT`. `client_capture_uuid` `50984dd1-1478-4ce6-9799-94b453f91368`. `client_original_uuid` `2dddb194-fd1c-4ced-9b28-2a3a332fb5b8`. Actor **Joel Brayman**. Flask Cursor terminal **562293** `13:02:30` **201/201**. UUID repair + text path **PASS**. Photo path **still open**. Gate **NOT CLOSED**. |
| Tests | Not re-run this pass (verification of live UAT rows only). Prior suite remains **553** / dedicated FG-021 **15** / focused **143**. |
| Project-state-report update | No — not a milestone close. |
| Milestone entry update | No — gate not closed. |
| Constitutional issue raised | None |
| Unresolved issues | Photo / IndexedDB quota still open. Voice, HEIC, retry, and remaining real-device checklist items not verified. |
| Next approved step | One small screenshot or JPEG on the same iPhone Safari capture. Do **not** attach a full-size HEIC yet. Do **not** close FG-021. |
| Next approved prompt | Verify the small JPEG/screenshot photo probe if Joel reports SAVED, or separately governed Native Signing development. |
| Commit hash | (docs only; uncommitted) |

### 2026-09-02 — FG-021 bounded LAN iPhone Save Original UUID repair

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ starting HEAD `443c39f556e30028d1166986342b8ee87264a8e8` |
| Objective | Bounded FG-021 UAT defect repair: Save Original no-op on HTTP LAN iPhone because `newUuid()` only called `crypto.randomUUID()` (unavailable on insecure HTTP). Do not close the gate. Do not migrate. |
| Business decision | Field Web V1 must generate RFC 4122 UUID v4 on iPhone Safari over HTTP LAN without weakening server validation, CSRF, auth, or idempotency. |
| Architectural decision | `crypto.randomUUID()` when available; else `crypto.getRandomValues` 16 bytes with v4 version/variant bits; fail visibly if neither API. No `Math.random()`. Pre-POST UUID errors use existing Capture feedback. JS remains source of truth. |
| Prompt template used | [cursor-bugfix-template.md](prompts/cursor-bugfix-template.md) |
| Approved Cursor prompt summary | BRAYMAN — FG-021 BOUNDED REPAIR SAVE ORIGINAL NO-OP ON HTTP LAN IPHONE. Repair `field.js` `newUuid()` only plus smallest pytest coverage and docs. Do not close FG-021. Do not migrate. Do not weaken CSRF/auth. |
| Files expected to change | `app/static/js/field.js`; `tests/test_field_web_fg021.py`; current-state; session-handoff; chat-workflow-log; FG-021 status / UUID contract as needed. |
| Files prohibited from changing | CSRF; auth; IndexedDB architecture; Event/Original idempotency; API routes; schema; Alembic; HEIC; desktop BUILD; Project selection; Today; live DB; Native Signing. |
| Implementation result | FG-021 remains **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN**. Gate **NOT CLOSED**. Live current = head `d2e3f4a5b6c7`. No migration. No live DB mutation. |
| Tests | Dedicated FG-021 **15 passed**. Focused **143 passed**. Full suite **553 passed**, 1568 warnings, 245.54s. Baselines 13 / 141 / 551; +2 dedicated, no unexplained loss. |
| Project-state-report update | No — not a milestone close. |
| Milestone entry update | No — gate not closed. |
| Constitutional issue raised | None |
| Unresolved issues | Real iPhone Safari UAT still pending. Retry Save Original after hard refresh. Gate not closed. |
| Next approved step | Retry Save Original on the same iPhone Safari UAT URL. Do not close FG-021 until UAT. |
| Next approved prompt | iPhone UAT / FG-021 close prompt after successful retry, or separately governed Native Signing development. |
| Commit hash | (this commit) |

### 2026-09-02 — FG-021 live migration apply d2e3f4a5b6c7

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ starting HEAD `5c36f6fcdf3c54aab9d103cd5152685382618984` |
| Objective | Live-migrate FG-021 only: identify live SQLite, take one gitignored pre-migration copy, apply `flask db upgrade` `c1d2e3f4a5b6` → `d2e3f4a5b6c7`. Do not close the gate. Do not invent iPhone UAT. |
| Business decision | Live SQLite file is not a backup. One bounded pre-FG-021 copy is required before upgrade. Backup stays outside Git and is not used for recovery unless separately authorized. |
| Architectural decision | Additive revision `d2e3f4a5b6c7` applied live. No backfill. Existing office UUID-null rows remain lawful. Live current = head. |
| Prompt template used | [cursor-migration-template.md](prompts/cursor-migration-template.md) |
| Approved Cursor prompt summary | BRAYMAN — FG-021 LIVE MIGRATION SAFETY CLARIFICATION THEN EXECUTE AUTHORIZED LIVE-MIGRATION PROMPT. Apply `d2e3f4a5b6c7` only after backup verification/creation. |
| Files expected to change | Governed docs only after live upgrade. |
| Files prohibited from changing | Product code; test code; migration files; Alembic history; backup commit. |
| Implementation result | FG-021 **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING**. Gate **NOT CLOSED**. Live current = head `d2e3f4a5b6c7`. Pre-migration copy `instance/brayman_estimator-backup-before-fg021-d2e3f4a5b6c7.db` gitignored. |
| Tests | Dedicated FG-021 **13 passed**. Focused **141 passed**. Full suite **551 passed**, 1564 warnings, 216.74s. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Real iPhone Safari UAT pending. Gate not closed. |
| Next approved step | Real iPhone Safari UAT. Do not close FG-021 until UAT. |
| Next approved prompt | iPhone UAT / FG-021 close prompt, or separately governed Native Signing development. |
| Commit hash | (this commit) |

### 2026-09-02 — Implement FG-021 Field Web V1 Today + Capture

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ starting HEAD `eb4466c4d090aaf366d39ebe2e3ff8ec1a382993` |
| Objective | Implement FG-021 Field Web V1: Today + Project confirm + Capture; idempotent Event/Original API; display GET; additive revision `d2e3f4a5b6c7`. Do not live-upgrade. Do not close the gate. |
| Business decision | Field Web V1 is Flask/Jinja + focused JS. IndexedDB retain-until-ACK. No PWA. No transcription. Native Signing remains a separate track. |
| Architectural decision | Event UUID UNIQUE(org, uuid); Original UUID UNIQUE(event, uuid); first 201 / replay 200 / conflict 409; Field display GET; live current remains `c1d2e3f4a5b6`. |
| Prompt template used | FG-021 Field Web V1 implementation prompt. |
| Approved Cursor prompt summary | BRAYMAN — FG-021 FIELD WEB V1 IMPLEMENTATION. Create `d2e3f4a5b6c7`. Implement `/field` + idempotent API. Do not run live `flask db upgrade`. Do not close FG-021. |
| Files expected to change | `app/`, `tests/test_field_web_fg021.py`, `migrations/versions/d2e3f4a5b6c7_*.py`, governed docs. |
| Files prohibited from changing | Live database; Legal Content Gate; Native Signing product; PWA; transcription. |
| Implementation result | FG-021 **IMPLEMENTED / LIVE MIGRATION PENDING**. Gate **NOT CLOSED**. Revision created. Live upgrade **not** run. |
| Tests | Dedicated FG-021 **13 passed**. Focused **141 passed**. Full suite **551 passed**. Live `flask db current` `c1d2e3f4a5b6`. Heads `d2e3f4a5b6c7`. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Live upgrade pending. Real iPhone UAT pending. Gate not closed. |
| Next approved step | Explicit live-migration prompt, then real iPhone Safari UAT. Do not close FG-021 until UAT. |
| Next approved prompt | Live-migration + iPhone UAT close prompt, or separately governed Native Signing development. |
| Commit hash | (this commit) |

### 2026-09-02 — Accept ADR-043, approve FG-021, Field Web implementation recon

| Field | Content |
|-------|---------|
| Date | 2026-09-02 |
| Branch | `main` @ starting HEAD `d69cfb66aaad5ad178375ddb2eaddc55091f6a7c` (copy-icon tooling). Origin was `24959d2650021380bbe8b1ef9ba94d5857debd26` before the tooling push. Draft commit `6273fa4` already on origin. |
| Objective | Docs-only: push tooling commit separately; commit ADR-043/FG-021 drafts; Accept ADR-043; Approve FG-021; record implementation reconnaissance. Do not implement Field Web. |
| Business decision | Field Web V1 remains Today + Project confirmation + Capture (voice/photo/short text). Flask/Jinja + focused JS + Shared API. No PWA. Native Signing development may proceed separately; production blocked pending counsel. |
| Architectural decision | ADR-043 **Accepted**: online-first IndexedDB retain-until-ACK; `client_capture_uuid` UNIQUE(org, uuid); `client_original_uuid` UNIQUE(event, uuid); Event/Original first 201 replay 200 conflict 409. FG-021 **APPROVED / IMPLEMENTATION NOT STARTED**. Designed revision `d2e3f4a5b6c7` **not created**. Readiness: READY FOR BOUNDED IMPLEMENTATION after a separate prompt. |
| Prompt template used | Governed Item-12 authorization (Accept / Approve / recon only). |
| Approved Cursor prompt summary | BRAYMAN — ACCEPT ADR-043 / APPROVE FG-021 — FIELD WEB V1 IMPLEMENTATION RECONNAISSANCE ONLY. Docs only. Do not modify app/, tests/, or create a migration. |
| Files expected to change | Governance/docs only, including `docs/architecture/fg-021-field-web-v1-implementation-reconnaissance.md`. |
| Files prohibited from changing | `app/`, `tests/`, `migrations/`, database, Legal Content Gate. |
| Implementation result | Docs only. ADR-043 **Accepted**. FG-021 **APPROVED / IMPLEMENTATION NOT STARTED**. Implementation recon **COMPLETE**. Field Web product **not started**. |
| Tests | Full suite **538 passed** claimed from FG-020 close — **not rerun**. Alembic current = heads `c1d2e3f4a5b6` verified. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Separate FG-021 implementation prompt not issued. Native Signing production remains counsel-blocked. Login lede copy for Field `next` is non-blocking. |
| Next approved step | **STOP product implementation.** Wait for a separate FG-021 implementation prompt. |
| Next approved prompt | Separate FG-021 implementation prompt (not this pass), or separately governed Native Signing development. |
| Commit hash | (this commit) |

### 2026-09-01 — Draft ADR-043 Proposed + FG-021 (not approved)

| Field | Content |
|-------|---------|
| Date | 2026-09-01 |
| Branch | `main` @ starting HEAD `24959d2650021380bbe8b1ef9ba94d5857debd26` (Item 12 recon). Copy-icon Cursor rule committed separately first as `d69cfb66aaad5ad178375ddb2eaddc55091f6a7c` (not pushed). |
| Objective | Docs-only: draft ADR-043 (Proposed) and FG-021 (DRAFT / NOT APPROVED) for Field Web V1 Today + Capture. |
| Business decision | Field Web V1 = Today + Project confirmation + Capture (voice/photo/short text). Flask/Jinja + focused JS + Shared API. Not SPA, PWA, or native iOS. Native Signing development may proceed under separate governance; production blocked pending counsel. |
| Architectural decision | ADR-043 Proposed: online-first IndexedDB retain-until-ACK; `client_capture_uuid` / `client_original_uuid`; tenant-safe uniqueness; Event-then-Originals partial success; SAVING/SAVED/NEEDS RETRY are client UX states; CSRF remains mandatory. FG-021 drafted, not approved. No migration. No product code. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — ITEM 12 FIELD WEB V1 ADR-043 + FG-021 GOVERNANCE DRAFT. Docs only. Do not Accept ADR-043. Do not Approve FG-021. Do not implement Field Web. |
| Files expected to change | ADR-043; FG-021; governed indexes; current-state; session-handoff; roadmap; project-state-report; chat-workflow-log; milestones. Copy-icon rule committed separately beforehand. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live database; Native Signing implementation; Contract templates. |
| Implementation result | Docs only. ADR-043 **Proposed**. FG-021 **DRAFT / NOT APPROVED**. Field Web implementation **not started**. |
| Tests | Not run (documentation-only). Full suite **538 passed** remains the FG-020 close claim. Alembic current = heads `c1d2e3f4a5b6` verified this pass. |
| Project-state-report update | Yes |
| Milestone entry update | Yes — this pass appended |
| Constitutional issue raised | None. Legal Content Gate unchanged. |
| Unresolved issues | Joel Accept ADR-043 and Approve FG-021. Exact schema/column names deferred to implementation reconnaissance. Safari MediaRecorder MIME To be verified on device. |
| Next approved step | **STOP Field Web implementation.** Joel may Accept ADR-043 and Approve FG-021 (implementation still a later prompt) **or** authorize separately governed Native Signing development (production still blocked pending counsel). |
| Next approved prompt | None from this pass. |
| Commit hash | (uncommitted docs; copy-icon rule `d69cfb6`; Item 12 recon `24959d2`) |

### 2026-09-01 — Item 12 recon verification + Native Signing counsel pin

| Field | Content |
|-------|---------|
| Date | 2026-09-01 |
| Branch | `main` @ starting HEAD `42b9c792b7c4fd968ed46be0ff15975cf3880eb5` = `origin/main` |
| Objective | Docs-only completion pass: verify Item 12 Field Web recon pin, replace leftover counsel-as-general-hold language, record Joel Native Signing pin, finish session-handoff leftovers. |
| Business decision | Ontario counsel review is **not** a general development hold and does **not** block Item 12. Native Signing **development may proceed under separate governance**. **Production activation / real customer use is blocked** pending counsel approval of the signing process. |
| Architectural decision | Canonical Item 12 pin remains [architecture/field-web-today-and-capture.md](architecture/field-web-today-and-capture.md) (extended; no second architecture document). Proposed FG-021 / ADR-043 **not created**. Field Web implementation **not started**. Native Signing implementation **not started**. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — ITEM 12 FIELD WEB recon completion + Joel Native Signing counsel pin. Docs only. Do not create FG-021 or ADR-043. Do not implement Field Web or Native Signing. Do not change counsel-review QUESTIONS. Do not weaken Legal Content Gate. |
| Files expected to change | Governed docs + canonical pin only. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live database; FG-021; ADR-043; counsel-review questions. |
| Implementation result | Docs only. Pin verified/extended to cover all 41 report topics. Leftover counsel-hold and session-handoff language corrected. Prior 2026-09-01 Field Web recon log entry preserved. |
| Tests | Not run (documentation-only; no product code). Full suite **538 passed** remains the FG-020 close claim. Alembic current = heads `c1d2e3f4a5b6` verified this pass. |
| Project-state-report update | Yes |
| Milestone entry update | Yes — this pass appended |
| Constitutional issue raised | None. Legal Content Gate for Ontario Contract/Warranty templates unchanged. |
| Unresolved issues | Joel authorization for FG-021 + ADR-043 drafting, or a separate Native Signing development track. Counsel answers remain open. Safari MediaRecorder MIME To be verified on device at implementation. |
| Next approved step | **STOP Field Web implementation.** Joel may authorize FG-021 + ADR-043 drafting **or** separately governed Native Signing development (production still blocked pending counsel). |
| Next approved prompt | None from this pass. |
| Commit hash | (uncommitted docs; verify `git rev-parse HEAD`) |

### 2026-09-01 — Field Web / Today + Capture architecture reconnaissance

| Field | Content |
|-------|---------|
| Date | 2026-09-01 |
| Branch | `main` @ starting HEAD `42b9c792b7c4fd968ed46be0ff15975cf3880eb5` |
| Objective | Docs-only architecture reconnaissance for roadmap Item 12 Field Web / Today + Capture. |
| Business decision | Field Web is a first-class iPhone capture surface over the same BUILD records. Not a shrunken office app. Capture-first. Plan access deferred from V1. Derived review and Change Order signing visibility out of V1. |
| Architectural decision | Flask/Jinja Field route family + JS calling `/api/v1`. Ordinary mobile web (PWA deferred). Event-then-Originals. IndexedDB retry-until-ACK. Server-side Event/Original idempotency required (not in FG-020 schema). API display rendition GET missing. Proposed future FG-021 / ADR-043 **not created**. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — ROADMAP ITEM 12 FIELD WEB / TODAY + CAPTURE — ARCHITECTURE RECONNAISSANCE ONLY. Docs only. Do not implement Field Web. Do not create a Feature Gate or ADR. |
| Files expected to change | Architecture pin + indexes, current-state / session-handoff / roadmap / chat-workflow-log / milestones / project-state-report. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live database; Native Signing; Contract; FG-020 rewind. |
| Implementation result | Docs only. Pin `docs/architecture/field-web-today-and-capture.md`. No product/database/Alembic change. |
| Tests | Not run (documentation-only; no product code). |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None. Idempotency requires a future ADR before implementation. |
| Unresolved issues | Safari MediaRecorder MIME To be verified on device; FG-021 / ADR-043 not created; Native Signing waiting for counsel. |
| Next approved step | **STOP.** Do not implement Field Web. Do not create FG-021 without Joel authorization. |
| Next approved prompt | None from this pass. |
| Commit hash | (this commit; verify `git rev-parse HEAD`) |

### 2026-09-01 — FG-020 live migration / office UAT close

| Field | Content |
|-------|---------|
| Date | 2026-09-01 |
| Branch | `main` @ starting HEAD `473b04eff8766f917e46abf793cc699b179a4fb6` |
| Objective | Close FG-020 after live Alembic verify and office UAT of Field Observations + HEIC Compatible Renditions. |
| Business decision | BUILD Field Capture V1 is operational for UAT. Item 11 COMPLETE. Item 12 eligible for separate governance, not authorized. Native Signing remains waiting for counsel. |
| Architectural decision | None new. Overlay existing Change Order. Original Source + regenerable JPEG rendition remains the active-storage model. Closeout not started. |
| Prompt template used | Feature increment / live-migrate close (this chat). |
| Approved Cursor prompt summary | BRAYMAN — RESUME FG-020 LIVE MIGRATION / OFFICE UAT. BUILD Field Capture V1 + Media Compatibility. Do not implement Native Signing or Field Web. |
| Files expected to change | FG-020 close docs and indexes only. |
| Files prohibited from changing | Product code; tests; migrations; counsel spec; Native Signing Feature Gate. |
| Implementation result | Live current already `c1d2e3f4a5b6` (verified; upgrade not re-run). Office UAT port **5013**, project **12**. Dedicated **44** / focused **128** / full **538**. Gate **CLOSED / OPERATIONAL FOR UAT**. |
| Tests | Dedicated 44 passed; focused 128 passed; full suite 538 passed. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Cursor browser tab could not be created this session; usability taken from authenticated office HTML. Placeholder office user password was CLI-reset for this pass. Field Web not started. Native Signing waiting for counsel. |
| Next approved step | **STOP.** Give counsel the Native Signing spec. Do not start Field Web. |
| Next approved prompt | None from this pass. |
| Commit hash | (this commit; verify `git rev-parse HEAD`) |

### 2026-09-01 — Native Signed Change Order counsel-review specification

| Field | Content |
|-------|---------|
| Date | 2026-09-01 |
| Branch | `main` @ starting HEAD `4538e6f3e8a6bdbe4cb01e2555ebf5a13ce41a86` |
| Objective | Prepare a docs-only Ontario counsel-review specification of the proposed CalibAi Native electronic-signing **process** for Change Orders. |
| Business decision | Brayman internally approved ≠ customer signed. Native signing overlays the existing Change Order. No unsigned-work bypass. Counsel reviews the process; this draft is not legal approval. |
| Architectural decision | None new. Recon remains **COMPLETE**; recommendation **NATIVE V1**. Counsel spec **PREPARED**. Implementation **NOT AUTHORIZED**. No Feature Gate. No ADR created or accepted. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — NATIVE SIGNED CHANGE ORDERS — COUNSEL-REVIEW SPECIFICATION — GOVERNANCE ONLY. Docs only. Do not implement signing, mail, DocuSign, Adobe, or CO lifecycle. Do not create a Feature Gate or ADR. |
| Files expected to change | Counsel-facing spec under `docs/legal/` plus minimum governance indexes. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live database; FG-020 close; Field Web; Contract implementation. |
| Implementation result | Docs only. Counsel spec at `docs/legal/native-signing-process-counsel-review.md`. No product/database/Alembic change. |
| Tests | Not run (documentation-only; no product code). |
| Project-state-report update | Yes (decisions pending; next action) |
| Milestone entry update | Yes (counsel spec recorded) |
| Constitutional issue raised | None. Consent wording is not marked APPROVED. |
| Unresolved issues | Ontario counsel answers to the 15-question decision list; then a Feature Gate only if Joel authorizes after counsel. CO document snapshot still a prerequisite pin (not implemented). |
| Next approved step | Give counsel the spec. Do not implement Native Signing. Do not start Contract. FG-020 live migration remains a separate prompt. |
| Next approved prompt | None from this pass. |
| Commit hash | (this commit; verify `git rev-parse HEAD`) |

### 2026-08-31 — Contract / e-signature / signed Change Order reconnaissance (native signing delta)

| Field | Content |
|-------|---------|
| Date | 2026-08-31 |
| Branch | `main` @ `3a31ed052cc4813b98d94ec8c71ec9a1b2b57946` |
| Objective | Record authorized CONTRACT / E-SIGNATURE / SIGNED CHANGE ORDER architecture reconnaissance, including native signing as a required option to evaluate. |
| Business decision | A signing provider is not the commercial source of truth. CalibAi owns the frozen document, commercial record, signing request, signed artifact, and provenance. Native signing must be evaluated; a TSP is not assumed. |
| Architectural decision | Recommended **NATIVE V1 subject to Ontario counsel review of the signing process**. Signing Service + Native adapter; DocuSign/Adobe remain future adapters. Click-to-sign + typed name is the V1 authority; graphics are presentation. Change Order overlay, not a second entity. Same service later for Contract after Legal Content Gate. No implementation. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — COMMERCIAL EXECUTION RECONNAISSANCE DELTA — EVALUATE CALIBAI NATIVE E-SIGNATURE. Docs only. Compare native vs DocuSign vs Adobe. Do not implement. Do not select a provider as product yet. |
| Files expected to change | Architecture recon pin + indexes, CO document-family subsequent status, Legal Content Gate open decision, ADR-004 subsequent status, current-state / session-handoff / roadmap / chat-workflow-log / milestones / project-state-report. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live database; FG-020 close; Field Web; mail; signing UI. |
| Implementation result | Docs only. Pin `docs/architecture/contract-esignature-and-signed-change-order.md`. No product/database/Alembic change. |
| Tests | Not run (documentation-only; no product code). |
| Project-state-report update | Yes (decisions pending) |
| Milestone entry update | Yes (recon recorded) |
| Constitutional issue raised | None. Native signing is not claimed legally sufficient without counsel. |
| Unresolved issues | Ontario counsel process review; optional vendor-pricing research pass; CO document snapshot still a prerequisite pin (not implemented). |
| Next approved step | **STOP.** Do not implement signing. FG-020 live migration / office UAT remains a separate prompt if still pending. Do not start Field Web. |
| Next approved prompt | None from this pass. |
| Commit hash | (this commit; verify `git rev-parse HEAD`) |

### 2026-08-31 — FG-020 Media Compatibility increment (HEIC/HEIF → JPEG)

| Field | Content |
|-------|---------|
| Date | 2026-08-31 |
| Branch | `main` @ starting HEAD `77d496367f9e6f003eb69949adb3bd82c6cadfd7` |
| Objective | Implement automatic HEIC/HEIF → JPEG Compatible Renditions before live migration / office UAT. Preserve and commit the storage-lifecycle docs. |
| Business decision | Original Source remains canonical. Compatible Rendition is a regenerable working/cache JPEG for user-friendly desktop display. Contractor should not need to know HEIC vs JPEG. |
| Architectural decision | Local `Pillow` + `pillow-heif` only. JPEG quality 85, max long edge 2048 px, EXIF orientation applied. Path `instance/build_renditions/<org>/<project>/<event>/<original_id>/display.jpg`. No schema. Capture-first: rendition failure does not roll back Original. Image-only. Closeout not started. |
| Prompt template used | Feature increment (this chat). |
| Approved Cursor prompt summary | BRAYMAN — FG-020 MEDIA COMPATIBILITY INCREMENT — AUTOMATIC HEIC/HEIF → JPEG DESKTOP RENDITION. Bounded increment + tests + docs. Do not live-migrate. Do not rewind FG-020. |
| Files expected to change | Rendition service/routes/templates; requirements.txt; dedicated tests; preserved storage-lifecycle docs and indexes. |
| Files prohibited from changing | Live database; Alembic revisions; Field Web; Closeout product; audio conversion; FG-020 rewind. |
| Implementation result | Renditions implemented. Storage-lifecycle docs preserved and committed with this increment. FG-020 remains **IMPLEMENTED / LIVE MIGRATION PENDING**. |
| Tests | Dedicated `tests/test_build_media_compatibility_fg020.py` **11 passed**. Combined dedicated FG-020 **44 passed**. Focused Hub+FG-018+FG-019+FG-020 **128 passed**. Full suite `./venv/bin/python -m pytest -q` **538 passed** (pre-increment **527**). |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append-only) |
| Constitutional issue raised | None |
| Unresolved issues | Live migration `b0c1d2e3f4a5` → `c1d2e3f4a5b6` and office UAT still pending. Closeout Feature Gate not created. |
| Next approved step | **STOP.** Separate live-migration / office UAT prompt. Do not start Field Web. Do not implement Closeout. |
| Next approved prompt | Live-migrate `b0c1d2e3f4a5` → `c1d2e3f4a5b6`, then office UAT of Field Observations including HEIC photos as JPEG. |
| Commit hash | (this increment; verify `git rev-parse HEAD` after commit) |

### 2026-08-31 — BUILD media compatibility + project-close storage lifecycle (docs only)

| Field | Content |
|-------|---------|
| Date | 2026-08-31 |
| Branch | `main` @ `77d496367f9e6f003eb69949adb3bd82c6cadfd7` |
| Objective | Record Original Source vs Compatible Rendition vs Closed Project Archive. Do not implement BUILD. Do not implement Closeout. Do not start Field Web. |
| Business decision | Active projects may retain Original Source + regenerable Compatible Renditions. After separately governed Project Closeout: archive Original Source, verify, purge renditions first then duplicate active originals. Do not accumulate redundant copies indefinitely. |
| Architectural decision | Renditions are regenerable presentation/cache artifacts, not Original Source, not Derived Candidates, not permanent archive records. HEIC/HEIF → JPEG is the first concrete rendition requirement. Archive format deferred to a future Project Closeout gate. FG-020 must not block archive-and-purge. Landed FG-020 Original Source custody is unchanged. Compatible Renditions remain **not implemented**. |
| Prompt template used | Governance clarification (this chat). |
| Approved Cursor prompt summary | BRAYMAN — BUILD MEDIA COMPATIBILITY + PROJECT-CLOSE STORAGE LIFECYCLE — GOVERNANCE CLARIFICATION BEFORE FG-020 IMPLEMENTATION. Docs only. Do not implement BUILD. |
| Files expected to change | Architecture pin; ADR-042 subsequent status; FG-020 subsequent status; BUILD module; current-state / session-handoff / roadmap / project-state-report / chat-workflow-log / milestones. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live database; Field Web; Closeout product; FG-020 rewind to not started. |
| Implementation result | Docs only. Pin `docs/architecture/build-media-storage-lifecycle.md`. Product/database/Alembic unchanged. FG-020 remains **IMPLEMENTED / LIVE MIGRATION PENDING**. |
| Tests | Docs-only. Product tests not rerun. Governed baseline remains **527 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append-only) |
| Constitutional issue raised | Prompt text assumed FG-020 **IMPLEMENTATION NOT STARTED**. Repository already has FG-020 implemented at `77d4963`. Status was **not** rewound. |
| Unresolved issues | Whether Compatible Renditions land as a revised FG-020 increment before live-migration/UAT. Archive format. Closeout Feature Gate not created. |
| Next approved step | **STOP.** Joel/ChatGPT review. Then a revised FG-020 increment authorization if renditions are to land. Do not start Field Web. Do not implement Closeout. |
| Next approved prompt | Revised FG-020 increment authorization after review. |
| Commit hash | (docs uncommitted unless Joel requests commit) |

### 2026-08-31 — Implement FG-020 BUILD Field Capture V1 (live migration pending)

| Field | Content |
|-------|---------|
| Date | 2026-08-31 |
| Branch | `main` @ starting HEAD `440d7c7c50306499fb720e874f7d0352031090e8` |
| Objective | Implement approved FG-020 Field Observation foundation. Stop at IMPLEMENTED / LIVE MIGRATION PENDING. |
| Business decision | FG-020 **IMPLEMENTED / LIVE MIGRATION PENDING**. Not closed. Item 12 remains blocked. HEIC/HEIF originals preserved (custody ≠ rendering). WebP out. |
| Architectural decision | Additive revision `c1d2e3f4a5b6` (`down_revision` `b0c1d2e3f4a5`). Events / Originals / Derived Candidates. Private custody `instance/build_originals/`. Narrow FG-019 mutating lock for BUILD POSTs only. UAT CLI source `UAT_CLI`. No Field Web. No AI. No MONITOR. No CO automation. |
| Prompt template used | Feature Gate implementation (this chat). |
| Approved Cursor prompt summary | BRAYMAN — IMPLEMENT FG-020 BUILD FIELD CAPTURE V1 — PROJECT FIELD OBSERVATION FOUNDATION. Authorize bounded product implementation + one additive migration. Do not live-migrate. Do not mark closed. |
| Files expected to change | BUILD models/services/routes/CLI/templates; `api_v1.py`; Project Hub; migration `c1d2e3f4a5b6`; dedicated tests; Hub assertions; governed docs. |
| Files prohibited from changing | Live database; Field Web; AI/transcription; MONITOR; CO automation; extra schema. |
| Implementation result | FG-020 **IMPLEMENTED / LIVE MIGRATION PENDING**. Live current remains `b0c1d2e3f4a5`. Repository head `c1d2e3f4a5b6`. |
| Tests | Dedicated **33 passed**. Focused **370 passed**. Full suite **527 passed**. Pre-FG-020 baseline **494**. `git diff --check`. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append-only) |
| Constitutional issue raised | None. Live upgrade remains separately governed. |
| Unresolved issues | Live `flask db upgrade` pending. Office UAT pending. Residual ISO-BMFF audio-in-video `ftyp` risk accepted without a heavy parser. |
| Next approved step | Separate live-migration / office UAT prompt. Do not start Field Web. |
| Next approved prompt | Live-migration / office UAT only. |
| Commit hash | (this commit) |

### 2026-08-31 — Approve FG-020 and record BUILD implementation reconnaissance (docs only)

| Field | Content |
|-------|---------|
| Date | 2026-08-31 |
| Branch | `main` @ `a2a161203daac9f9f6f758fcb72680803ff56b20` (starting HEAD) |
| Objective | Approve FG-020. Record implementation reconnaissance. Do not implement BUILD. |
| Business decision | FG-020 **APPROVED / IMPLEMENTATION NOT STARTED**. Item 11 remains not started. Item 12 remains blocked. |
| Architectural decision | Exact Event/Original/Derived schemas; BUILD storage under `instance/build_originals/`; image JPEG/PNG/GIF 25 MB; audio mp4/m4a/aac/mpeg/wav/webm 25 MB; payload_json Text object; designed revision `c1d2e3f4a5b6`. Narrow FG-019 GET-only lock for BUILD POSTs only. Verdict **READY FOR BOUNDED IMPLEMENTATION**. |
| Prompt template used | Feature Gate approval + implementation reconnaissance (this chat). |
| Approved Cursor prompt summary | BRAYMAN — APPROVE FG-020 / BUILD FIELD CAPTURE V1 — IMPLEMENTATION RECONNAISSANCE ONLY. Approve FG-020. Recon. Do not implement BUILD. |
| Files expected to change | FG-020 status + recon; indexes; current-state / handoff / roadmap / chat-workflow-log / milestones. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live database; BUILD product code. |
| Implementation result | FG-020 **APPROVED / IMPLEMENTATION NOT STARTED**. Recon recorded. Product/database/Alembic unchanged. |
| Tests | Docs-only. Product tests not rerun. Governed baseline remains **494 passed**. `git diff --check`. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append-only) |
| Constitutional issue raised | None. Gate approval without implementation prompt is not code authorization. |
| Unresolved issues | Separate implementation prompt after recon review. HEIC/WebP omitted (not a V1 blocker). Residual audio-in-video ftyp risk accepted. |
| Next approved step | **STOP.** Joel/ChatGPT review recon. Then a **separate** implementation prompt. Do not start Field Web. |
| Next approved prompt | None until the implementation authorization prompt is issued. |
| Commit hash | (this commit) |

### 2026-08-31 — Accept ADR-042 and draft FG-020 (governance only)

| Field | Content |
|-------|---------|
| Date | 2026-08-31 |
| Branch | `main` @ `327e510e7d521d2689bf7d756953fda85cb68a0d` (starting HEAD) |
| Objective | Accept ADR-042. Draft FG-020 as **NOT APPROVED**. Do not implement BUILD. Do not start Field Web. |
| Business decision | Dual first-class BUILD surfaces and original-custody architecture are **Accepted**. Item 11 remains unauthorized until FG-020 is approved. Item 12 remains blocked. |
| Architectural decision | **ADR-042 Accepted.** **FG-020 DRAFT FOR JOEL REVIEW / NOT APPROVED.** Additive migration later (`down_revision` `b0c1d2e3f4a5`). File-custody MIME/size deferred to implementation reconnaissance. |
| Prompt template used | ADR accept + Feature Gate draft prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — ACCEPT ADR-042 AND DRAFT FG-020 BUILD FIELD CAPTURE V1 — GOVERNANCE ONLY. Accept ADR-042. Draft FG-020. Do not implement BUILD. |
| Files expected to change | ADR-042 status; FG-020 draft; indexes; current-state / handoff / roadmap / chat-workflow-log / milestones. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live database; FG-020 approval; BUILD code. |
| Implementation result | ADR-042 **Accepted**. FG-020 **DRAFT / NOT APPROVED**. Product/database/Alembic unchanged. |
| Tests | Docs-only. Product tests not rerun. Governed baseline remains **494 passed**. `git diff --check`. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append-only) |
| Constitutional issue raised | None. Draft Feature Gate is not approval (Article 8 / Feature Gate process). |
| Unresolved issues | Joel must approve or reject FG-020. MIME/size for BUILD audio/image remains for implementation reconnaissance. |
| Next approved step | **STOP.** Joel / ChatGPT review FG-020. Do not implement BUILD. |
| Next approved prompt | None until FG-020 is approved. Then a separate implementation prompt plus file-custody reconnaissance. |
| Commit hash | (this commit) |

### 2026-08-31 — Draft ADR-042 BUILD field evidence / iPhone-first capture (governance only)

| Field | Content |
|-------|---------|
| Date | 2026-08-31 |
| Branch | `main` @ `50b21ec838e34799a7fe129da8e52a7126a81394` (starting HEAD) |
| Objective | Docs-only Proposed ADR for BUILD field evidence, original custody, dual first-class surfaces (desktop review + iPhone-first capture), Item 11 vs Item 12, offline A/B/C. Do not accept the ADR. Do not create FG-020. Do not implement BUILD. |
| Business decision | Desktop and Field are both first-class over one BUILD SoR. Capture-first. Original audio/photo/text immutable. Derived requires human confirmation. Audio/image upload API belongs to Item 11. Field Web UI remains Item 12. |
| Architectural decision | **ADR-042 Proposed / FOR JOEL REVIEW.** Additive to ADR-023 (does not rewrite CAR-001-era voice/photo implementation prohibition). `user_id` + display-name snapshot on new BUILD tables only. Distinct `created_at` / `occurred_at`. Generic Derived Candidate. No CO FK in V1. |
| Prompt template used | ADR governance draft prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — BUILD FIELD EVIDENCE / IPHONE-FIRST / VOICE-FIRST / DESKTOP-FIRST REVIEW ARCHITECTURE ADR — GOVERNANCE DRAFT ONLY. Create next valid ADR as Proposed. Do not accept. Do not create FG-020. Do not implement BUILD. |
| Files expected to change | `docs/adr/ADR-042-*.md`; ADR index; CAR-001 subsequent status; BUILD module; current-state / handoff / roadmap / chat-workflow-log; minimum related indexes. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live database; FG-020; ADR-042 acceptance; ADR-008/010 status. |
| Implementation result | ADR-042 drafted **Proposed / FOR JOEL REVIEW**. FG-020 **not created**. Product/database/Alembic unchanged. |
| Tests | Docs-only. Product tests not rerun. Governed baseline remains **494 passed**. `git diff --check`. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append-only recorded governance draft) |
| Constitutional issue raised | None. Proposed is not Accepted (Article 8). |
| Unresolved issues | Joel must accept or reject ADR-042. FG-020 not authorized until acceptance. Field MIME/size limits deferred to FG-020 reconnaissance. |
| Next approved step | **STOP.** Joel / ChatGPT review ADR-042. Do not create FG-020. Do not start BUILD. |
| Next approved prompt | None until Joel accepts ADR-042. Then a separate docs-only FG-020 draft prompt. |
| Commit hash | (this commit) |

### 2026-08-31 — Approve and implement FG-019 Shared API Foundation V1

| Field | Content |
|-------|---------|
| Date | 2026-08-31 |
| Branch | `main` @ `97280f9f9fc62e5d1238c098eb0c246ab4071a8b` (starting HEAD) |
| Objective | Approve and implement GET-only `/api/v1` Shared API Foundation. Close FG-019 if tests and UAT pass. Complete item 10. Do not start BUILD. |
| Business decision | Cookie/session reuse of FG-018. `/me` includes email, excludes `is_active`. Project identity includes `client_name`. No tokens. No mutation. No migration. |
| Architectural decision | No new ADR. ADR-022 + ADR-041 sufficient. JSON 401 for unauthenticated `/api/`. 403 for 0/>1 memberships. 404 for missing/cross-org. Mutating methods 405 before CSRF. |
| Prompt template used | FG-019 approve-and-implement prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — APPROVE AND IMPLEMENT FG-019 SHARED API FOUNDATION V1. GET `/api/v1/me`, `/api/v1/projects`, `/api/v1/projects/<id>` only. No BUILD. No tokens. No migration. |
| Files expected to change | `app/__init__.py`; `app/routes/api_v1.py`; `app/services/shared_api.py`; `tests/test_shared_api_fg019.py`; governed docs. |
| Files prohibited from changing | `migrations/`; BUILD; Field Web; tokens; office HTML rewrite; ADR-008/010 status. |
| Implementation result | GET-only `/api/v1` implemented. Dedicated **34**. Focused **326**. Full suite **494**. API UAT port **5012**. FG-019 **CLOSED / OPERATIONAL FOR UAT**. Item 10 **COMPLETE**. |
| Tests | `./venv/bin/python -m pytest -q tests/test_shared_api_fg019.py` → **34 passed**. Focused 16-file set → **326 passed**. Full suite → **494 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append-only) |
| Constitutional issue raised | None |
| Unresolved issues | BUILD architecture / Feature Gate not authorized. Native/token auth deferred. |
| Next approved step | **STOP.** Do not start BUILD. |
| Next approved prompt | None. Fresh-chat prompt remains [session-handoff.md](session-handoff.md) §22. |
| Commit hash | (this commit) |

### 2026-08-31 — Draft FG-019 Shared API Foundation V1 (governance only)

| Field | Content |
|-------|---------|
| Date | 2026-08-31 |
| Branch | `main` @ `f872662781260f0571f54c4921116389cc70dd27` (starting HEAD) |
| Objective | Docs-only Feature Gate draft for the remaining Shared API slice of roadmap item 10. Do not implement `/api/`. Do not start BUILD. |
| Business decision | FG-019 exists as **DRAFT FOR JOEL REVIEW / NOT APPROVED**. Item 10 remains **PARTIALLY COMPLETE**. Shared API product code **NOT STARTED**. BUILD remains **BLOCKED**. A draft is **not** approval. |
| Architectural decision | Reuse FG-018 cookie/session. GET-only `/api/v1/me`, `/api/v1/projects`, `/api/v1/projects/<id>`. No migration. No tokens. No new ADR (ADR-022 + ADR-041 sufficient). Unauthenticated API → 401 JSON; 0/>1 membership → 403; cross-org → 404. |
| Prompt template used | Feature Gate draft prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — DRAFT FG-019 SHARED API FOUNDATION — GOVERNANCE ONLY. Docs only. Do not implement `/api/`. Do not create a migration. Do not start BUILD. |
| Files expected to change | `docs/feature-gates/FG-019-shared-api-foundation-v1.md`; Feature Gate / docs indexes; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log; milestones. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live database; ADR creation/acceptance; FG-018 close evidence. |
| Implementation result | Docs-only. No product code. No tests changed. No database mutation. No migration. FG-019 **DRAFT / NOT APPROVED**. No ADR created. |
| Tests | Not rerun (docs-only; governed baseline remains **460 passed**). |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append-only) |
| Constitutional issue raised | None |
| Unresolved issues | Whether Joel Approves FG-019. Native/token auth remains deferred. |
| Next approved step | **STOP.** Wait for Joel review. Do not implement Shared API from this prompt. |
| Next approved prompt | None. Fresh-chat prompt remains [session-handoff.md](session-handoff.md) §22. |
| Commit hash | (this commit) |

### 2026-08-31 — Post-FG-018 current-state documentation reconciliation

| Field | Content |
|-------|---------|
| Date | 2026-08-31 |
| Branch | `main` @ `2bc8f5620983441de6772c0ac94cd5d6718c0efe` (starting HEAD) |
| Objective | Bounded docs-only repair of current-state drift after FG-018 close. Record item 10 as PARTIALLY COMPLETE. Do not create FG-019 or start Shared API. |
| Business decision | Office authentication remains **CLOSED / OPERATIONAL FOR UAT**. Shared API remains **NOT STARTED / NOT AUTHORIZED**. BUILD remains **BLOCKED**. Next authorized action remains **STOP**. |
| Architectural decision | None. ADR-041 Decision unchanged. ADR-022 sequence unchanged. ADR-008 / ADR-010 remain Proposed. |
| Prompt template used | Post-FG-018 documentation reconciliation prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — POST-FG-018 DOCUMENTATION RECONCILIATION. Docs only. Do not create FG-019. Do not start Shared API reconnaissance. |
| Files expected to change | Governing CURRENT-state docs listed in the prompt (roadmap, ADR index, CAR-001 subsequent status, ADR-041 current status, current-state, session-handoff, project-state-report, Feature Gate index as needed, chat-workflow-log, milestones). |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; live database; Feature Gate creation; ADR creation/acceptance. |
| Implementation result | Docs-only. No product code. No tests changed. No database mutation. No migration. No FG-019. No ADR created or accepted. |
| Tests | Not rerun (docs-only; governance does not require product tests for this pass). |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append-only) |
| Constitutional issue raised | None |
| Unresolved issues | Whether Joel authorizes later Shared API architecture reconnaissance. |
| Next approved step | **STOP.** Do not start Shared API reconnaissance from this prompt. |
| Next approved prompt | None. Fresh-chat prompt remains [session-handoff.md](session-handoff.md) §22. |
| Commit hash | (this commit) |

### 2026-08-31 — FG-018 live migration / bootstrap / office UAT close

| Field | Content |
|-------|---------|
| Date | 2026-08-31 |
| Branch | `main` @ `0d7af3e93a9d6c4f27eb2136f915297620be59ed` (starting HEAD) |
| Objective | Authorized live `flask db upgrade` `a9b0c1d2e3f4` → `b0c1d2e3f4a5`; bootstrap first ORG-001 user; bounded office UAT; close FG-018 only if all criteria pass. |
| Business decision | Office authentication is **CLOSED / OPERATIONAL FOR UAT**. Not production-security certification. Shared API / BUILD / RBAC remain out of gate. |
| Architectural decision | Membership-derived org context; fail-closed 0/>1 memberships; no silent ORG-001 fallback; no `user_id` columns; historical actor strings untouched. |
| Prompt template used | FG-018 live-migrate / bootstrap / office UAT prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — LIVE-MIGRATE / BOOTSTRAP / OFFICE UAT FG-018 AUTHENTICATION. Do not invent email. Password via getpass or AUTH_BOOTSTRAP_PASSWORD. Close only if all criteria pass. |
| Files expected to change | Governed docs; local-only gitignored `.env`; live SQLite schema/users. No product-code change. |
| Files prohibited from changing | Shared API; BUILD; RBAC; migrations history; ADR-008/010 status; committed secrets. |
| Implementation result | Migration applied. Bootstrap succeeded (email normalized via strip().lower(); display name Joel Brayman; one active ORG-001 membership; duplicate failed closed). Office UAT **PASSED** on port **5011**. Dedicated **37 passed**. Focused **460 passed**. Full suite **460 passed**. |
| Tests | `./venv/bin/python -m pytest -q tests/test_auth_fg018.py` → **37 passed**; focused FG-018 list → **460 passed**; `./venv/bin/python -m pytest -q` → **460 passed** |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Shared API deferred. Browser tab could not be held for a visual walk; HTTP UAT covered the authorized routes. |
| Next approved step | **STOP.** Do not start shared API or BUILD. |
| Commit hash | verify `git rev-parse HEAD` after this commit |

### 2026-08-31 — Implement FG-018 organization authentication (pre-live-migration)

| Field | Content |
|-------|---------|
| Date | 2026-08-31 |
| Branch | `main` @ `b7b1bb59d3826ced14459e35d307628672344b5f` (starting HEAD) |
| Objective | Implement FG-018 exactly as governed by ADR-041 and the recorded reconnaissance. Stop at IMPLEMENTED / LIVE MIGRATION PENDING. |
| Business decision | Office authentication is product-implemented. Live migration/bootstrap/UAT remain separately authorized. Shared API deferred. BUILD remains blocked until live close. |
| Architectural decision | User + UserMembership; pbkdf2:sha256; Flask-Login; CSRFProtect; membership fail-closed (0 or >1 active memberships); no RBAC; no org-switcher; no user_id columns; historical actor strings untouched. |
| Prompt template used | FG-018 implementation prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — IMPLEMENT FG-018 ORGANIZATION AUTHENTICATION, ACTOR IDENTITY, AND MEMBERSHIP V1. Single additive migration `b0c1d2e3f4a5`. Do not live-migrate. |
| Files expected to change | Auth models/services/routes/CLI; `create_app`; organizations/shell; bounded actor helpers; tests; docs; one Alembic revision; Flask-WTF dependency. |
| Files prohibited from changing | Live operating database; shared API; BUILD/Field; RBAC; ADR-008/010 status. |
| Implementation result | Implemented. Dedicated tests **37 passed**. Full suite **460 passed**. Live Alembic current **`a9b0c1d2e3f4`**. Repository head **`b0c1d2e3f4a5`**. Live upgrade **not run**. |
| Commit hash | verify `git rev-parse HEAD` after this commit |

### 2026-08-30 — Accept ADR-041 / Approve FG-018 / implementation reconnaissance

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `4d02b402e85a538d48ce74c410f7927b1b2464a8` (starting HEAD) |
| Objective | Accept ADR-041, approve FG-018 as IMPLEMENTATION NOT STARTED, record FG-018 implementation reconnaissance. |
| Business decision | Office authentication is approved architecture. Product implementation is **not** started. Shared API deferred. BUILD remains blocked. |
| Architectural decision | ADR-041 **Accepted**. FG-018 **Approved**. Recon pins `users` / `user_memberships`, pbkdf2:sha256, Flask-WTF CSRFProtect, Flask CLI bootstrap, membership fail-closed, no user_id campaign, revision `b0c1d2e3f4a5` not created. |
| Prompt template used | Docs-only governance prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — ACCEPT ADR-041 / APPROVE FG-018 — IMPLEMENTATION RECONNAISSANCE ONLY. Do not implement. |
| Files expected to change | Governed docs only. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; database. |
| Implementation result | ADR accepted; FG-018 approved not implemented; reconnaissance recorded on FG-018. No product code. |
| Tests | Not rerun. Governed baseline remains **423 passed**. `git diff --check`. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Separate implementation prompt still required. Multi-membership selection remains fail-closed. Login throttling deferred. |
| Next approved step | **STOP product implementation.** Joel/ChatGPT review reconnaissance then a separate implementation prompt. |
| Next approved prompt | None for implementation until separately authorized. |
| Commit hash | Live `HEAD`: verify `git rev-parse HEAD`. |

### 2026-08-30 — Draft ADR-041 and FG-018 (Item 10 office authentication)

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `b68dc6e014fc7854075c3d866eff831bf592eb95` (starting HEAD) |
| Objective | Docs-only draft of ADR-041 (Proposed) and FG-018 (DRAFT / NOT APPROVED) for office authentication, actor identity, and membership. |
| Business decision | Item 10 governance has begun. Product implementation is **not** authorized. Shared API deferred. BUILD remains blocked. No credentials in Git. |
| Architectural decision | One durable User; UserMembership; email/password; Flask-Login/session; no RBAC; historical actor strings preserved; CSRF and SECRET_KEY fail-closed required in later implementation. ADR remains **Proposed**. |
| Prompt template used | Docs-only governance prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — ROADMAP ITEM 10 — DRAFT AUTHENTICATION ADR + FG-018 GOVERNANCE ONLY. Do not accept ADR. Do not approve FG-018. Do not implement. |
| Files expected to change | Governed docs only. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; database. |
| Implementation result | ADR-041 Proposed and FG-018 Draft created. Indexes and current-state updated. No product code. |
| Tests | Not rerun. Governed baseline remains **423 passed**. `git diff --check`. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append; do not rewrite FG-017 close) |
| Constitutional issue raised | None |
| Unresolved issues | ADR-041 not accepted. FG-018 not approved. Multi-membership selection if a User has more than one active membership. Exact table names, CSRF library, bootstrap CLI, SECRET_KEY env, optional user_id paths deferred to implementation reconnaissance. |
| Next approved step | **STOP product implementation.** Joel/ChatGPT review ADR-041 and FG-018. |
| Next approved prompt | None for implementation. After acceptance/approval: separate implementation reconnaissance. |
| Commit hash | Live `HEAD`: verify `git rev-parse HEAD`. |

### 2026-08-30 — Post-FG-017 roadmap documentation reconciliation

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `620dec1a9612e87a1ede20cfa6aa46c6d72a8dd5` (starting HEAD) |
| Objective | Docs-only repair of stale CURRENT/FUTURE/NEXT roadmap and turnover language after FG-017 close. |
| Business decision | STOP remains the next authorized action. Numbered sequence item 10 (Authentication) remains first unfinished direction item and is **NOT AUTHORIZED**. No FG-018. |
| Architectural decision | None. ADR-040 remains Accepted. No ADR created or accepted. |
| Prompt template used | Docs-only reconciliation prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — POST-FG-017 ROADMAP DOCUMENTATION RECONCILIATION. Repair identified drift. Preserve sequence ≠ authorization. Do not start Authentication. |
| Files expected to change | Governed docs only. |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; database; Feature Gate creation; ADR create/accept. |
| Implementation result | Stale near-term Alembic/`b4c5d6e7f8a9`, Permit Pass 2 NOT IMPLEMENTED, FG-015/016/017-as-future, missing ADR-040 in handoff list, and “this commit” SHA wording repaired. Gate-at-close vs live-head distinction recorded. |
| Tests | Not rerun. Governed baseline remains **423 passed**. `git diff --check`. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append docs reconciliation; do not rewrite FG-017 close) |
| Constitutional issue raised | None |
| Unresolved issues | Individual Feature Gate files still record **gate-at-close** Alembic heads (historical; left in place). |
| Next approved step | **STOP.** Do not start Authentication. Do not create FG-018. |
| Next approved prompt | None authorized. Expected next *substantive* step only after Joel/ChatGPT review: separately authorized Authentication architecture and Feature-Gate reconnaissance. |
| Commit hash | Content `dd30d752190e56ed687e270950df9bf9a06d7a26`. SHA-pin `07cb46c501d968542dff567943044dc1db870f01`. Live `HEAD`: verify `git rev-parse HEAD`. |

### 2026-08-30 — FG-017 live migration + office UAT close

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `00ca492e28118d75757e9a9c82384978b5decd92` (starting HEAD) |
| Objective | Apply FG-017 live migrate; ensure Brand Profiles; backfill snapshots; bounded office UAT; close only if all criteria pass. |
| Business decision | CURRENT-on-save restore after UAT phone tests. Freeze at Issued; Accepted-without-Issued freezes at Accepted. Isolation fail-closed. Office UAT only — not broader production validation. |
| Architectural decision | Apply existing `a9b0c1d2e3f4` only. Do not create another migration. Do not change product code unless a defect is found (none found). |
| Prompt template used | Live-migrate + UAT prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — LIVE-MIGRATE AND UAT FG-017 ORGANIZATION BRAND PROFILE. Apply f8a9b0c1d2e3 → a9b0c1d2e3f4. Ensure + backfill. Office UAT. Tests. Docs. Close only if all evidence passes. |
| Files expected to change | Governed docs only (plus live DB UAT residue and logo custody under `instance/`). |
| Files prohibited from changing | Product code unless a defect is discovered; Alembic revisions; Change Order PDF; Permit branding. |
| Implementation result | Migration applied. Current=head=`a9b0c1d2e3f4`. One graph head. Ensure created 2 CURRENT profiles. Backfill 0. Office UAT port **5010**. FG-017 **CLOSED / OPERATIONAL FOR UAT**. |
| Tests | Dedicated FG-017 **22 passed**. Focused regressions **97 passed**. Full suite **423 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append close; do not rewrite implementation entry) |
| Constitutional issue raised | None |
| Unresolved issues | None for FG-017 closure. Issued→Draft lock still not decided. Internal breakdown branding later. Change Order / Permit branding remain unauthorized. |
| Next approved step | **STOP.** Do not start the next Feature Gate. Do not begin Change Order documents, Phase D, supplier integration, or external AI / runtime web. |
| Next approved prompt | None authorized. |
| Commit hash | (this close commit) |

### 2026-08-30 — Implement FG-017 Organization Brand Profile V1 (pre-live-migration)

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `7075a802ef98a4d4de5f66afd403d9c659a3c36d` (starting HEAD) |
| Objective | Implement FG-017 exactly as reconnaissance: schema, logo custody, CURRENT-on-save, Proposal freeze/snapshot, Settings UI, tests. Do not live-migrate. |
| Business decision | CURRENT-on-save. Freeze at first Issued; Accepted-without-Issued freezes at Accepted. Sticky snapshot. Settings nav, not a new module. |
| Architectural decision | Additive `a9b0c1d2e3f4`. Brand Profile owned by Organization subsystem. Proposal owns `proposal_brand_snapshots`. No `branding_config` JSON. Template identity columns retained. |
| Prompt template used | [prompts/cursor-implementation-template.md](prompts/cursor-implementation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — IMPLEMENT FG-017 ORGANIZATION BRAND PROFILE V1. Authorizes product code, tests, and migration file. Does **not** authorize live `flask db upgrade`. |
| Files expected to change | Models/services/routes/templates for Brand Profile; Proposal freeze/render; navigation; tests; revision `a9b0c1d2e3f4`; governed docs |
| Files prohibited from changing | Change Order PDF/email; Permit HTML/PDF; app chrome except Settings nav; live DB |
| Implementation result | **IMPLEMENTED / LIVE MIGRATION PENDING.** Live current remains `f8a9b0c1d2e3`. Not CLOSED. |
| Tests | Focused 119 passed. `./venv/bin/python -m pytest -q` → **423 passed**. Dedicated FG-017 **22**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None new. Issued brand freeze remains separate from ADR-002. |
| Unresolved issues | Live migrate + ensure/backfill + office UAT not authorized. Issued→Draft status lock not decided. Internal breakdown branding later. |
| Next approved step | **STOP.** Separate live-migrate prompt. |
| Next approved prompt | Fresh-chat prompt in `docs/session-handoff.md` §22. |
| Commit hash | (this implementation commit) |

### 2026-08-30 — Accept ADR-040 / Approve FG-017 / FG-017 implementation reconnaissance

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `ee6a695eab8a3dcd4c02b663671990d124ec313d` (starting HEAD) |
| Objective | Accept ADR-040; approve FG-017; produce exact implementation plan. Docs only. |
| Business decision | CURRENT-on-save (no Draft Brand Profile). Freeze at first Issued; Accepted-without-Issued freezes at Accepted. Settings nav, not a new module. Internal breakdown out of FG-017. |
| Architectural decision | ADR-040 **Accepted**. FG-017 **APPROVED / IMPLEMENTATION NOT STARTED**. Designed revision `a9b0c1d2e3f4` not created. No `branding_config` JSON. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — ACCEPT ADR-040 / APPROVE FG-017 — IMPLEMENTATION RECONNAISSANCE ONLY. |
| Files expected to change | Governance docs / FG-017 reconnaissance only |
| Files prohibited from changing | `app/` · `tests/` · `migrations/` · live DB · logos |
| Implementation result | Approval recorded. Exact plan on FG-017. **IMPLEMENTATION NOT STARTED.** |
| Tests | Not rerun (docs-only). `git diff --check`. Live DB read-only: 0 Issued / 0 Accepted proposals. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append; do not rewrite the prior draft record) |
| Constitutional issue raised | Issued brand freeze is separate from ADR-002 Accepted commercial lock. |
| Unresolved issues | Implementation prompt not issued. Issued→Draft sticky-snapshot vs status lock not separately gated. |
| Next approved step | **STOP.** Wait for FG-017 implementation authorization. |
| Next approved prompt | Fresh-chat prompt in `docs/session-handoff.md` §22. Does **not** start implementation. |
| Commit hash | (this docs commit) |

### 2026-08-30 — Organization Brand Profile ADR + Feature Gate governance draft

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `e03f9f88ebf65ded120448a1aba8f16347b18056` (starting HEAD) |
| Objective | Docs-only draft of Organization Brand Profile ADR and first Feature Gate from the accepted architecture reconnaissance. |
| Business decision | Brand Profile is the proposed single source for contractor identity on generated org/customer documents. Proposal is the first consumer. App-shell chrome stays out. Issued/Accepted documents must snapshot branding. CO and Permit are accounted for, not implemented. |
| Architectural decision | [ADR-040](adr/ADR-040-organization-brand-profile.md) **Proposed / for Joel review** (not Accepted). [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **DRAFT FOR JOEL REVIEW / NOT APPROVED**. No implementation. No migration. Do not implement `branding_config` JSON. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — ORGANIZATION BRAND PROFILE — ADR + FEATURE GATE GOVERNANCE DRAFT. Docs only. Do not implement product code. |
| Files expected to change | ADR-040; FG-017; indexes and status docs only |
| Files prohibited from changing | `app/` · `tests/` · `migrations/` · live DB · logos/assets · customer documents |
| Implementation result | Drafts written. Capability remains **NOT IMPLEMENTED**. Gate remains **NOT APPROVED**. |
| Tests | Not rerun (docs-only; no unexplained discrepancy vs governed 401). `git diff --check`. |
| Project-state-report update | Yes (draft exists; not implementation) |
| Milestone entry update | Yes (append architecture-record; do not rewrite historical entries) |
| Constitutional issue raised | Issued-document brand snapshot extends Article 5 / ADR-002 spirit to document identity (proposed, not accepted). |
| Unresolved issues | Joel must Accept/revise ADR-040 and Approve/revise FG-017. Internal breakdown branding still open. Legal identifiers still out. |
| Next approved step | **STOP.** Wait for Joel / ChatGPT review. Do not implement Brand Profile. |
| Next approved prompt | Fresh-chat prompt in `docs/session-handoff.md` §22. Does **not** start implementation. |
| Commit hash | (this docs commit, if committed) |

### 2026-08-30 — Post-FG-016 full documentation / governance turnover

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a` |
| Objective | Reconcile all approved CalibAi decisions into the repository; eliminate stale current-state language; rebuild the session turnover package; prepare one fresh-chat resume prompt. Docs only. |
| Business decision | Repository is the durable system of record. All active chat context may roll over. No next product gate authorized. Organization Brand Profile reconnaissance remains a **candidate only** (not authorized; not started). |
| Architectural decision | No Feature Gate. No ADR. No migration. No database mutation. No product code. Historical append-only entries retain dated historical state. |
| Prompt template used | Documentation / Review Turnover (this chat). |
| Approved Cursor prompt summary | BRAYMAN — FULL PROJECT DOCUMENTATION RECONCILIATION AND ALL-CHAT TURNOVER PACKAGE. Docs only. Do not implement. Do not start the next product task. |
| Files expected to change | Governed docs / indexes / handoff / log only |
| Files prohibited from changing | `app/` · `tests/` · `migrations/` · live DB · runtime config · seed data |
| Implementation result | Turnover reconciled. FG-016 remains **CLOSED / OPERATIONAL FOR UAT**. HEAD pin `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a`. Live current=head `f8a9b0c1d2e3`. Fresh-chat prompt in `docs/session-handoff.md` §22. |
| Tests | Not rerun (docs-only; no unexplained discrepancy vs governed 401). |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append turnover record; do not rewrite historical entries) |
| Constitutional issue raised | None |
| Unresolved issues | No next product work authorized. Candidate Organization Brand Profile reconnaissance unstarted. |
| Next approved step | **STOP.** New chats must run repository preflight first. Wait for Joel to authorize the next architecture/product task. |
| Next approved prompt | Fresh-chat prompt in `docs/session-handoff.md` §22. Does **not** start Organization Branding. |
| Commit hash | (this turnover commit) |

### 2026-08-30 — FG-016 live migration + Mike Pratt office UAT close

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ starting `1294db4f51bae5be68541c77b8721c7ab4d58496` |
| Objective | Apply FG-016 migration to development/UAT; bounded live Pratt Permit Intelligence UAT; HTML/PDF verify; close FG-016 if evidence passes. |
| Business decision | Advisory only. PASS never means AHJ approval. Pratt is labeled UAT/reference. Do not repair product/rule/source defects under this prompt. |
| Architectural decision | Apply existing `f8a9b0c1d2e3` only. Do not create another migration. Do not change product code unless a defect is found (none found). |
| Prompt template used | Live-migrate + UAT prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — FG-016 LIVE MIGRATION + MIKE PRATT OFFICE UAT. Apply e7f8a9b0c1d2 → f8a9b0c1d2e3. Pratt UAT from signed plans. HTML/PDF. Tests. Docs. Close only if all evidence passes. |
| Files expected to change | Governed docs only (plus live DB UAT residue). |
| Files prohibited from changing | Product code unless a defect is discovered; Alembic revisions; approved rule seed. |
| Implementation result | Migration applied. Current=head=`f8a9b0c1d2e3`. Pratt project 9 port 5009. Analyses v1–v3. 10 findings. HTML/PDF consistent. Unsupported coverage projects 10–11. No product-code change. FG-016 **CLOSED / OPERATIONAL FOR UAT**. |
| Tests | Dedicated FG-016 **37 passed**. Relevant regressions **357 passed**. Full suite **401 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append close; do not rewrite implementation entry) |
| Constitutional issue raised | None |
| Unresolved issues | None for FG-016 closure. National expansion / Phase D / branding / Change Order documents / supplier / external AI remain unauthorized. |
| Next approved step | **STOP.** Do not begin national permit expansion, Phase D, Organization Branding, Change Order documents, supplier integration, or external AI / runtime web. |
| Next approved prompt | None authorized. |
| Commit hash | `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a` |

### 2026-08-30 — FG-016 Ontario / Ottawa Permit Intelligence POC implementation

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ starting `4310c574b0c5dd2f047b402acfab77c7a32a57ab` |
| Objective | Implement FG-016 bounded Ontario / Ottawa coach-house Permit Intelligence POC. |
| Business decision | Advisory only. PASS never means AHJ approval. Pratt is UAT reference, not live-seeded. Dual-compliance numeric checks VERIFY unless conservative ceiling exceeded. |
| Architectural decision | Reuse FG-015 resolver. Platform `permit_rules` (no org CRUD). Project facts vs legal conclusions. Deterministic evaluation. Immutable `permit_analyses`. HTML report + existing ReportLab PDF. One additive migration `f8a9b0c1d2e3` **not** live-applied. No new ADR. |
| Prompt template used | Implementation prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — IMPLEMENT FG-016 ONTARIO / OTTAWA PERMIT INTELLIGENCE POC. Authoritative-source research; APPROVED seed; one additive migration; facts; snapshots; HTML report; PDF if existing stack; dedicated/regression/full-suite tests. Do not live-migrate. Do not enable runtime web or external AI. |
| Files expected to change | `app/` permit models/services/routes/templates; `migrations/versions/f8a9b0c1d2e3_*`; `tests/test_permit_intelligence_fg016.py`; governed docs |
| Files prohibited from changing | Live development/UAT DB; Estimate/Proposal/Contract economics; Plan Intelligence write paths; Brand Profile |
| Implementation result | Implemented. Graph head `f8a9b0c1d2e3`. Live current remains `e7f8a9b0c1d2`. 10 APPROVED rules. Neutral CalibAi PDF of the same snapshot. |
| Tests | Dedicated FG-016 **37 passed**. Full suite **401 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Live migration pending. Live office Pratt UAT pending. FG-016 not CLOSED. |
| Next approved step | **FG-016 live migration + office Pratt UAT**. This pass **STOPS**. |
| Next approved prompt | FG-016 live migration + office Pratt UAT (not this chat). |
| Commit hash | `a709829d32d94ab2baf36f142ad0095254ba3d3a` |

### 2026-08-30 — FG-016 Ontario / Ottawa Permit Intelligence POC Feature Gate governance

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `8c70ede72e37b5b0fe0910b70c34fca5d9c733ad` |
| Objective | Create and approve FG-016 Ontario / Ottawa Permit Intelligence POC. Docs only. Do not implement. |
| Business decision | Bounded Ontario / City of Ottawa / coach-house POC. Advisory only. PASS never means AHJ approval. Pratt is UAT reference, not a seeded conclusion. |
| Architectural decision | [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED**. Reuse FG-015 resolver. Smallest Permit Rules Library V1. Rule vs project fact. Deterministic evaluation. No new ADR (ADR-037/038/039). One later additive migration. No runtime scrape. No external AI. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | BRAYMAN — ONTARIO / OTTAWA PERMIT INTELLIGENCE POC FEATURE GATE GOVERNANCE. Documentation only. Do not implement. Do not create a migration. Do not populate the Permit Rules Library. Do not create the Mike Pratt project. Do not enable external AI or runtime web scraping. |
| Files expected to change | FG-016 + permit-rules architecture + indexes + module/status/handoff/log/roadmap |
| Files prohibited from changing | `app/` · `tests/` · `migrations/` · live DB |
| Implementation result | FG-016 created and approved. No product-code change. |
| Tests | Not rerun (docs only; no behaviour change). Prior full suite **364 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Implementation not started. Library empty. Pratt project not in product data. |
| Next approved step | **FG-016 implementation** under a later Cursor prompt. This pass **STOPS**. |
| Next approved prompt | FG-016 implementation (not this chat). |
| Commit hash | (this docs-approval commit) |

### 2026-08-30 — FG-015 live migration + office UAT close

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ starting HEAD `f5606a106aaeeb19928d5e1b020c60ba4ef6fcec` |
| Objective | Apply existing FG-015 revision `e7f8a9b0c1d2` to the development/UAT database; bounded office UAT; rerun tests; close FG-015 if all evidence passes. |
| Business decision | Foundation remains advisory PRELIMINARY / FOUNDATION ONLY. No zoning conclusions. No PASS. No Pratt project. No Permit Rules Library. |
| Architectural decision | Live current = head `e7f8a9b0c1d2`. Existing `Project.address` preserved. No forced backfill. Snapshot immutability and recheck confirmed live. |
| Prompt template used | Cursor live-migrate / office UAT prompt (this chat). |
| Approved Cursor prompt summary | BRAYMAN — FG-015 LIVE MIGRATION + OFFICE UAT. Apply only `e7f8a9b0c1d2`. Do not implement Gate 2. Do not populate Permit Rules. Do not enable live web lookup, geocoding, or external AI. Stop on product defect; do not repair. |
| Files expected to change | Governed docs only (after successful UAT). |
| Files prohibited from changing | Product code; new migrations; Permit Rules; Pratt seed |
| Implementation result | Live upgrade `d6e7f8a9b0c1` → `e7f8a9b0c1d2`. Office UAT **PASSED** on port **5008**. FG-015 **CLOSED / OPERATIONAL FOR UAT**. Product-code changes: none. |
| Tests | Dedicated FG-015 **19 passed**. Relevant regressions **338 passed**. Full suite **364 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Permit Rules Library not populated. Pass 2 / Gate 2 / Pratt POC not started. |
| Next approved step | Later **Ontario / Ottawa Permit Rules + Mike Pratt POC** Feature Gate (**not created**). Do not populate rules. Do not start Gate 2. |
| Next approved prompt | Gate 2 Feature Gate governance (not this chat). |
| Commit hash | (this docs-close commit) |

### 2026-08-30 — FG-015 Permit Foundation V1 implementation

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ starting HEAD `5f75da617d837add01bacf8f74b40d647f30a067` |
| Objective | Implement FG-015 Permit Foundation V1: ProjectLocation, jurisdiction resolver, preliminary Permit Profile, Project Hub foundation state. One additive Alembic revision. Do not live-migrate. |
| Business decision | Foundation only. Advisory PRELIMINARY / FOUNDATION ONLY. No zoning conclusions. No PASS. Preserve `Project.address`. No Pratt project. |
| Architectural decision | Projects owns `ProjectLocation` and `PermitProfile`. Platform-shared jurisdiction definitions. Permit context class distinct from commercial `PROJECT_TYPES`. Versioned immutable snapshots. Recheck/stale on location or permit-context change. |
| Prompt template used | Cursor implementation prompt (this chat). |
| Approved Cursor prompt summary | IMPLEMENT FG-015 PERMIT FOUNDATION V1. One additive migration. Do not apply to live development/UAT DB. Do not populate Permit Rules. Do not enable live web lookup or external AI. |
| Files expected to change | Models, services, routes, templates, tests, one Alembic revision, governed docs |
| Files prohibited from changing | Live DB; Plan Intelligence analysis; Estimating lines; Permit Rules Library; branding/CO/BUILD |
| Implementation result | Product implemented. Throwaway upgrade/downgrade verified. Live current left at `d6e7f8a9b0c1`. Graph head `e7f8a9b0c1d2`. Not CLOSED. |
| Tests | Dedicated FG-015 **19 passed**. Relevant regressions **338 passed**. Full suite **364 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Live migration pending. Office Hub UAT pending live schema. Ontario / Ottawa + Mike Pratt gate not created. |
| Next approved step | **FG-015 live migration** under a later Cursor prompt. Do not populate the Permit Rules Library. |
| Next approved prompt | FG-015 live-migrate (not this chat). |
| Commit hash | `e6462a9ee8688b6599ab1a7b0e91232e8d53db3a` |

### 2026-08-30 — FG-015 Permit Foundation V1 Feature Gate governance

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `5474c47189f67645cc6a636cdfa054cf3c6660f9` |
| Objective | Create and approve FG-015 Permit Foundation V1. Docs only. Do not implement. |
| Business decision | Foundation infrastructure only. CalibAi remains advisory. No zoning conclusions. No PASS. Ontario civic address supported; existing free-text address preserved; no ambiguous backfill. |
| Architectural decision | [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **APPROVED FOR IMPLEMENTATION** / **NOT STARTED**. Bounded ProjectLocation 1:1 parented to `projects` (ADR-037). Permit context class separate from commercial `PROJECT_TYPES` (no auto-map). Versioned preliminary profile snapshot (ADR-039). No new ADR. No rules library. No live lookup. No Pratt project. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | PERMIT FOUNDATION V1 FEATURE GATE GOVERNANCE. Documentation only. Do not implement. Do not create a migration. Do not modify product code. Do not populate the Permit Rules Library. Do not perform live web lookup. Do not enable external AI. |
| Files expected to change | FG-015 + indexes + architecture/module/status/handoff/log/milestones/roadmap |
| Files prohibited from changing | `app/` · `tests/` · `migrations/` · live DB |
| Implementation result | FG-015 created and approved. No product-code change. |
| Tests | Not rerun. No product-code change. Preserved full suite **345 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (architecture / Feature Gate record) |
| Constitutional issue raised | None |
| Unresolved issues | Ontario / Ottawa + Mike Pratt gate not created. Finding enums deferred to Gate 2. |
| Next approved step | **FG-015 implementation** under a later Cursor prompt. This pass **STOPS**. |
| Next approved prompt | FG-015 implementation (not this chat). |
| Commit hash | (this Feature Gate docs commit) |

### 2026-08-30 — Permit Intelligence architecture governance / ADR decision pass

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `3d91dda43a513bb0c72c57a3c5da70ee326a026b` |
| Objective | Memorialize accepted Permit Intelligence architecture. Docs / ADRs only. Do not implement. Do not create a Feature Gate. |
| Business decision | CalibAi is advisory preflight. AHJ remains final. **PASS** means no issue identified against governed checks performed — never permit/zoning/AHJ approved. Ontario-first; first municipal case City of Ottawa / North Gower; Mike Pratt Coach House at 2562 Church Street is a future UAT reference only. |
| Architectural decision | **Accepted:** [ADR-037](adr/ADR-037-project-location-and-jurisdiction-resolution.md) project location + one jurisdiction resolver; [ADR-038](adr/ADR-038-permit-intelligence-authority-and-rules-library.md) Permit Intelligence engine, Permit Rules Library (separate from Legal Content Gate), two-pass model, Plan Intelligence read-through, no auto estimate insert, no contract generation, BUILD post-issuance boundary; [ADR-039](adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) report snapshot/immutability, recheck/stale, finding/workflow policy (no product enums), core project document (not a Change Order). Brand Profile is not a prerequisite for analysis. Recommended future gates **Permit Foundation V1** then **Ontario / Ottawa Permit Rules + Mike Pratt POC** recorded only — **not created**. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | PERMIT INTELLIGENCE ARCHITECTURE GOVERNANCE / ADR DECISION PASS. Documentation only. Do not implement. Do not create a Feature Gate. Do not create a migration. Do not modify product code. Do not enable live web lookup or external AI. |
| Files expected to change | ADRs 037–039 + architecture/governance/status/handoff/log/milestones/roadmap indexes |
| Files prohibited from changing | `app/` · `tests/` · `migrations/` · Feature Gate files (none created) · live DB |
| Implementation result | Three ADRs **Accepted**. Architecture docs created/reconciled. No product-code change. No Feature Gate. |
| Tests | Not rerun. No product-code change. Preserved full suite **345 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (architecture record) |
| Constitutional issue raised | None |
| Unresolved issues | Finding-severity product enums deferred. Permit Foundation V1 Feature Gate not created. Branding / Change Order document gates remain later. |
| Next approved step | **STOP.** Architecture governed. Do not implement Permit Intelligence. Do not create a Permit Feature Gate. |
| Next approved prompt | None. Later Joel/ChatGPT may authorize Permit Foundation V1 as a Feature Gate (not this pass). |
| Commit hash | (this architecture-governance docs commit) |

### 2026-08-30 — Organization Brand Profile + Change Order document family pin

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `dc1bfc07fccec103bfebc0a9f22a789d93cce26c` |
| Objective | Pin future Organization Brand Profile and Change Order document-family requirements. Docs only. |
| Business decision | Branding is configured once per organization, not per module. Change Order remains the existing business record and becomes a repeating transaction-document family. Issued documents must preserve branding actually used. |
| Architectural decision | **FUTURE / NOT IMPLEMENTED.** No Feature Gate. No ADR. No schema. Do not create a second Change Order entity. Do not reorder the roadmap. FG-014 remains closed. Next governed action remains Permit Intelligence reconnaissance. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | FUTURE ORGANIZATION BRANDING + CHANGE ORDER DOCUMENT REQUIREMENTS PIN. Architecture pin only. Do not implement. Do not interrupt FG-014. |
| Files expected to change | Architecture pins + indexes + status/handoff/log/milestones/roadmap |
| Files prohibited from changing | `app/` · `tests/` · `migrations/` · FG-014 product status |
| Implementation result | Two canonical pins recorded. No product-code change. |
| Tests | Not rerun. No product-code change. Preserved full suite **345 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (architecture record) |
| Constitutional issue raised | None |
| Unresolved issues | Later: whether branding is a small platform prerequisite Feature Gate; how CO snapshot → email → acceptance evidence is gated. |
| Next approved step | **Permit Intelligence Engine architecture reconnaissance** (not implementation). |
| Next approved prompt | Architecture reconnaissance only. Do not implement Permit Intelligence, branding, or Change Order documents. |
| Commit hash | (this pin docs commit) |

### 2026-08-30 — FG-014 office re-UAT and closure

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `1a2e34cf9e8062a8c2a5e086e174d845f3f27417` |
| Objective | Short office browser re-UAT of the repaired Material Catalogue link/unlink workflow. Close FG-014 if all checks pass. Docs only. |
| Business decision | Gate closes only after office re-UAT of valid link/unlink, empty-select, non-Material fail-closed flashes, cross-org fail-closed, and catalogue page regression. |
| Architectural decision | No product-code change. Permit Intelligence remains FUTURE. No schema, ADR, or Feature Gate for permits. |
| Prompt template used | [cursor-bugfix-template.md](prompts/cursor-bugfix-template.md) (UAT/closure) |
| Approved Cursor prompt summary | FG-014 FINAL OFFICE RE-UAT / CLOSURE. Start repaired app on a fresh port. Do not use 5005. If new defect, STOP. If pass, close FG-014 as CLOSED / OPERATIONAL FOR UAT. Docs-only commit/push. Then STOP. |
| Files expected to change | FG-014 + status/handoff/log/milestones/roadmap |
| Files prohibited from changing | `app/` · `tests/` · `migrations/` unless a new defect (then stop) |
| Implementation result | All re-UAT checks passed on port **5007**. No new defect. FG-014 **CLOSED / OPERATIONAL FOR UAT**. |
| Tests | Not rerun. Preserved: dedicated **35 passed**; relevant regressions **29 passed**; full suite **345 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | None for FG-014. Permit Intelligence reconnaissance not started. |
| Next approved step | **Permit Intelligence Engine architecture reconnaissance** (not implementation). |
| Next approved prompt | Architecture reconnaissance only. Do not implement Permit Intelligence. |
| Commit hash | (this closure docs commit) |

### 2026-08-30 — FG-014 catalogue-link flash repair

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `3e671f20a561b4c70bc837486f59f93a150f7fee` (repair start; permit pin `5931696` committed first) |
| Objective | Repair only the FG-014 catalogue-link flash/message defect. Do not broaden Material Catalogue architecture. |
| Business decision | Improper catalogue link must fail closed **and** tell the caller the service reason. Empty select may still say `Select a Material cost item to link.` |
| Architectural decision | `MaterialCatalogueError` subclasses `ValueError`. Catch it before `(TypeError, ValueError)` in `link_cost_item`. Unlink already used the correct order. No schema, identity, CostItem ownership, supplier, Phase D, or Permit Intelligence change. |
| Prompt template used | [cursor-bugfix-template.md](prompts/cursor-bugfix-template.md) |
| Approved Cursor prompt summary | FG-014 CATALOGUE-LINK FLASH REPAIR. Reproduce, smallest root cause, repair flash only, add regression test, run dedicated/regression/full suite, reconcile FG-014 docs, commit and push. Permit pin remains FUTURE. Then STOP. |
| Files expected to change | `app/routes/material_catalogue.py` · `tests/test_material_catalogue_fg014.py` · FG-014 / status docs |
| Files prohibited from changing | migrations · canonical identity model · CostItem ownership · supplier/Phase D/Permit Intelligence · ADR-008 |
| Implementation result | Exception order repaired. Dedicated **35 passed**. Full suite **345 passed**. Live POST on 5006 flashed the Labour service reason. FG-014 not closed (office re-UAT remaining). |
| Tests | `./venv/bin/python -m pytest -q tests/test_material_catalogue_fg014.py` → **35 passed**. Assemblies/estimates/estimate_builder **29 passed**. Full suite **345 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes — architecture record (non-milestone) |
| Constitutional issue raised | None |
| Unresolved issues | Short office re-UAT of catalogue-link error flashes before FG-014 close. |
| Next approved step | **FG-014 office re-UAT of catalogue-link flashes, then close**. |
| Next approved prompt | Office re-UAT / gate-close prompt. Do not implement Permit Intelligence. |
| Commit hash | (this repair commit) |

### 2026-08-30 — FUTURE pin: Project Permit & Approvals Report

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `3e671f20a561b4c70bc837486f59f93a150f7fee` |
| Objective | Architecture requirement pin only. Record a governed advisory PROJECT PERMIT & APPROVALS REPORT as FUTURE / NOT IMPLEMENTED. Do not interrupt FG-014 live-migration/UAT. |
| Business decision | CalibAi must eventually generate an early-lifecycle permit/zoning/servicing preflight from address/jurisdiction + site/property + project type + plans/site plan + current governing municipal/provincial/state requirements, so issues can affect feasibility, scope, pricing, and contracting. The report is advisory. It does not replace the AHJ, building official, planner, surveyor, engineer, septic authority, conservation authority, attorney, or other regulated professionals. FINAL AUTHORITY remains the governing AHJ. |
| Architectural decision | Additional governed project document (not estimate outputs 1–4). Retain with project documents; tie to project, address/jurisdiction, plan version, site-plan version, governing-rule source/version/effective date, generation date, evidence/provenance. Later plan or by-law changes must not silently rewrite an earlier report. Freshness: CURRENT RULE LOOKUP → CITED / VERSIONED PERMIT ANALYSIS → PROJECT REPORT SNAPSHOT → IMMUTABLE HISTORY. Re-check when plans, site plan, scope, address/jurisdiction, or governing requirements change. Status vocabulary (PASS / VERIFY / POTENTIAL NON-CONFORMANCE / ADDITIONAL APPROVAL LIKELY / MISSING INFORMATION / NOT APPLICABLE) is conceptual only — not product enums. Mike Pratt Coach House at 2562 Church Street, North Gower, Ontario is a future architecture/UAT reference; preliminary ChatGPT research is not an authoritative permit determination. Separate repository-first reconnaissance required before implementation. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | ARCHITECTURE REQUIREMENT PIN ONLY. Record Permit & Approvals Report as FUTURE / NOT IMPLEMENTED. Do not authorize Permit Intelligence, legal-library, live regulatory AI, web lookup, automatic approval conclusions, municipal submissions, schema, migration, ADR, or a Feature Gate. Continue FG-014 unchanged. |
| Files expected to change | `docs/` architecture pin + indexes + status/handoff/log/milestones + UAT reference + legal-content distinction. |
| Files prohibited from changing | `app/` · `tests/` · `migrations/` · FG-014 Feature Gate status · any ADR · new Feature Gate |
| Implementation result | Canonical pin created. FG-014 status unchanged (**LIVE-MIGRATED / UAT DEFECT — CLOSURE BLOCKED**). Next coded work remains catalogue-link flash repair + re-UAT. |
| Tests | Docs-only; `git diff --check`. Full suite not re-run this pass. Last recorded full suite **338 passed** (FG-014 live-migrate/UAT). |
| Project-state-report update | Yes — future pin noted; next approved remains FG-014 defect repair. |
| Milestone entry update | Yes — architecture record (non-milestone). |
| Constitutional issue raised | None. Pin does not invent municipal law. |
| Unresolved issues | FG-014 catalogue-link flash defect unrepaired. Permit capability requires later reconnaissance before any Feature Gate. |
| Next approved step | **FG-014 catalogue-link flash repair + re-UAT**. |
| Next approved prompt | FG-014 UAT defect repair (`link_cost_item` exception order). Do not implement Permit Intelligence. |
| Commit hash | (pending docs commit) |

### 2026-08-30 — FG-014 live migration applied; office UAT closure blocked

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `a100caa2c1f5e1c29e79449c8ce5a144ff945f23` (start) |
| Objective | Apply `d6e7f8a9b0c1` to the live development/UAT DB. Bounded office Material Catalogue UAT. Docs only unless a product defect is found. |
| Business decision | Live migrate authorized. Do not repair product defects under this prompt. Do not close FG-014 if UAT finds a product-code defect. |
| Architectural decision | Canonical identity remains platform-shared. CostItem remains org costing. ADR-008 remains Proposed. Supplier onboarding pin unchanged (FUTURE). |
| Prompt template used | Bounded FG-014 live migration + office UAT |
| Approved Cursor prompt summary | Apply only `c5d6e7f8a9b0` → `d6e7f8a9b0c1`. Browser UAT `/material-catalogue/`. Do not modify product code unless a defect is found — if so, STOP and do not repair. |
| Files expected to change | Governed docs only (on success). Product code prohibited unless defect (then stop). |
| Files prohibited from changing | Product repair; new migrations; ADR-008 status; supplier schema |
| Implementation result | Migration **applied**. Live current = head = `d6e7f8a9b0c1`. Seed 27 rows. Catalogue list/search/filter/detail, Material link/unlink, org isolation GET 404, assembly read-through, Cost Library canonical column: **passed**. **UAT DEFECT:** catalogue `POST .../link` for non-Material and cross-org IDs flashes `Select a Material cost item to link.` instead of the service reason. Data remain unlinked. Closure **blocked**. Product code **not** changed. |
| Tests | Dedicated FG-014 **28 passed**. Relevant regressions **278 passed**. Full suite **338 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | FG-014 **not closed**. Catalogue link exception-order flash defect. Seed has no DISCONTINUED rows (filter empty; service tests cover new-link block). |
| Next approved step | **Bounded product-defect repair** for `app/routes/material_catalogue.py` `link_cost_item` exception order, then re-UAT the fail-closed flashes. Do **not** re-run `flask db upgrade`. Do not start supplier onboarding. |
| Next approved prompt | FG-014 UAT defect repair (catalogue link flash). Do not accept ADR-008. Do not start Phase D or supplier ingest. |
| Commit hash | (this commit) |

### 2026-08-30 — FG-014 Material Catalogue V1 implemented

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `273803b75b6bcbe6ae56fbf3274cd4a2dafcec36` (start) |
| Objective | Implement FG-014 identity V1. One additive migration. Do not live-migrate. |
| Business decision | Platform-owned lumber/sheet seed. Optional Material CostItem link. Read-only canonical UX. |
| Architectural decision | `canonical_materials` is platform-shared. CostItem remains org costing. ADR-008 remains Proposed. No supplier schema. |
| Prompt template used | Bounded FG-014 product implementation |
| Approved Cursor prompt summary | IMPLEMENT FG-014. One additive Alembic revision. Do not apply to live development/UAT DB. |
| Files expected to change | models, services, routes, templates, migration, tests, governed docs |
| Files prohibited from changing | TakeoffPackageItem; Assembly schema FK; ADR-008 status; live DB |
| Implementation result | Identity + seed (27 rows) + CostItem FK + `/material-catalogue/`. Graph head `d6e7f8a9b0c1`. Live current `c5d6e7f8a9b0`. |
| Tests | Dedicated FG-014 **28 passed**. Full suite **338 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | Live migrate and office UAT not done. ADR-008 remains Proposed. |
| Next approved step | **FG-014 live-migrate + office UAT** when Joel authorizes. |
| Next approved prompt | Bounded live-migrate + UAT. Do not start supplier ingest. |
| Commit hash | `976cc4a4942ae346b9843a77126f89969bba2b6e` |

### 2026-08-30 — FG-014 Material Catalogue V1 Feature Gate + future supplier-onboarding pin

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `130b3fd35114014f0635d9a70e7cb3096647d480` (start) |
| Objective | Documentation-only Feature Gate for Material Catalogue V1. Pin future bulk supplier onboarding. Do not implement either. |
| Business decision | Joel: approve FG-014 identity-only lumber/sheets. Suppliers must later onboard by governed bulk ingest (not one-product-at-a-time); INITIAL mapping vs ONGOING sync. That pin is FUTURE ONLY and does not expand V1. |
| Architectural decision | FG-014 **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED**. Owner: Material Catalogue (identity); Estimating (CostItem). Seed in the same additive Alembic revision as the table (implementation prompt). Ordinary org users must not mutate platform identity. ADR-008 remains Proposed. No Supplier Feature Gate. |
| Prompt template used | Bounded Material Catalogue V1 Feature Gate governance + future supplier-onboarding pin |
| Approved Cursor prompt summary | FEATURE GATE GOVERNANCE / DOCUMENTATION ONLY. Create FG-014. Do not implement. Do not migrate. Do not accept ADR-008. Record bulk supplier onboarding as FUTURE / NOT IMPLEMENTED without expanding V1. |
| Files expected to change | Feature Gate, indexes, architecture/module/status docs |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; product code; ADR-008 status |
| Implementation result | FG-014 approved, not started. Bulk supplier onboarding pinned in supplier architecture. No product code. |
| Tests | Not rerun (docs-only). Last recorded full suite **310 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | Implementation not started. ADR-008 remains Proposed. Supplier Feature Gate not authorized. |
| Next approved step | **FG-014 implementation prompt** when Joel authorizes. Do not implement after this docs commit. |
| Next approved prompt | Bounded FG-014 implementation (identity + seed + CostItem FK + office UX). Do not start supplier ingest. |
| Commit hash | (this commit) |

### 2026-08-30 — Material Catalogue ADR-034 / ADR-035 / ADR-036 accepted

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `b53d9e7150e43b173bad3c26eee8e829529773e5` (start) |
| Objective | Accept three Material Catalogue ADRs. Do not create a Feature Gate. Do not accept ADR-008. |
| Business decision | Joel: CalibAi-seeded identity; UOM vs pack; living evidence classes; promotions as effective-dated facts; identity V1 before Phase D. |
| Architectural decision | ADR-034 / ADR-035 / ADR-036 **Accepted**. ADR-008 remains **Proposed**. MaterialRequirement and Phase D not authorized. |
| Prompt template used | Bounded Material Catalogue ADR governance |
| Approved Cursor prompt summary | DOCUMENTATION / ADR GOVERNANCE ONLY. Create exactly three ADRs. Do not implement. Do not create a Feature Gate. Do not accept ADR-008. |
| Files expected to change | Three ADRs; indexes; architecture cross-refs; status docs |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; Feature Gates; ADR-008 status |
| Implementation result | ADR-034, ADR-035, ADR-036 Accepted. No Feature Gate. |
| Tests | Not rerun (docs-only). Last recorded full suite **310 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | Feature Gate not opened. ADR-008 remains Proposed. |
| Next approved step | **Material Catalogue Feature Gate** (docs) when Joel authorizes. Do not implement until that gate is approved. |
| Next approved prompt | Material Catalogue V1 Feature Gate (identity-only lumber/sheets). Do not accept ADR-008. |
| Commit hash | (this commit) |

### 2026-08-30 — Material Catalogue architecture governance

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `450cd39dea24c3e41d32defa39e9e74c00ae7c6d` (start) |
| Objective | Document Material Catalogue architecture: CalibAi-seeded identity; CostItem not identity; living supplier evidence distinct from identity; first FG identity-only. No ADR, Feature Gate, or product code. |
| Business decision | Joel: CalibAi-seeded vocabulary; identity-only first gate; Material Catalogue before Phase D; rolled-up commercial Assembly vs exploded fulfillment; Material Cost Standard deferred; ADR-008 deferred; living catalogue (price increases + promotions) with immutable snapshots. |
| Architectural decision | Canonical material ≠ CostItem ≠ supplier SKU. Material Catalogue UX capability ≠ canonical table. Living evidence is effective-dated, not `CURRENT_PRICE` only. |
| Prompt template used | Bounded Material Catalogue architecture governance (documentation) |
| Approved Cursor prompt summary | DOCUMENTATION / ARCHITECTURE GOVERNANCE ONLY. Create material-catalogue-architecture.md. Reconcile supplier docs. No FG, ADR, migration, or product code. Add living material intelligence (Joel decision). |
| Files expected to change | Architecture, module, and status docs |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; product code; Feature Gates; new ADRs |
| Implementation result | Architecture document created; supplier ownership wording reconciled; living intelligence recorded. |
| Tests | Not rerun (docs-only; no product-code change). Last recorded full suite **310 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | ADRs not yet written. Feature Gate not opened. ADR-008 remains Proposed. |
| Next approved step | **Material Catalogue ADRs** when Joel authorizes. Do not implement. Do not open a Feature Gate yet. |
| Next approved prompt | Material Catalogue ADRs (docs). Do not accept ADR-008 unless that prompt authorizes it. |
| Commit hash | (this commit) |

### 2026-08-30 — FG-013 migration reconciliation + UAT closure

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `0c36adb6d98ec2c1af88fa98cf61c00aa14f0eb3` (start) |
| Objective | Verify live DB already at `c5d6e7f8a9b0`; complete bounded FG-013 UAT; close gate. Do not re-run `flask db upgrade`. |
| Business decision | Preserve interrupted-session migration provenance. Folder/OS-drag native pickers not faked as browser PASS. |
| Architectural decision | FG-013 **CLOSED / OPERATIONAL FOR UAT**. Migration **VERIFIED APPLIED** before this pass. No product-code change. |
| Prompt template used | Bounded FG-013 migration-state reconciliation + UAT closure |
| Approved Cursor prompt summary | Independently verify DB; do not upgrade if current=head; UAT + tests; docs; close only if evidence supports. |
| Files expected to change | FG-013 and governed status docs |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; product code; Alembic revisions; Desktop corpus |
| Implementation result | UAT multi-file/mixed/duplicate/review/storage/quarantine/known-family/TIER_A/mutation/org passed. Folder/OS-drag not live-browser verified. Tests 27/11/25/33/310. |
| Tests | `./venv/bin/python -m pytest -q tests/test_historical_upload_fg013.py` → 27 passed. historical 11; labour 25; pricing 33; full suite **310 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | Native folder picker and OS drag/drop not live-browser verified. |
| Next approved step | **Material Catalogue architecture** (docs) when Joel authorizes. Do not `flask db upgrade`. Do not start supplier POC. |
| Next approved prompt | Material Catalogue architecture documentation. |
| Commit hash | (this commit) |

### 2026-08-30 — ADR-033 supplier channel / Winchester launch-partner architecture

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` |
| Objective | Add supplier-channel architecture: Darcy / BMR Winchester as launch/reference partner, not exclusive; dual contractor-procurement vs CalibAi-channel relationships; Darcy originated-value participation categories without terms. |
| Business decision | BMR, BMR Winchester, and Darcy are **not exclusive**. Winchester = design/launch partner, first reference deployment, supplier-channel BD partner. Reward Darcy for value created / business originated; do not surrender CalibAi’s broader supplier market. Channel expansion to other BMR dealers, BMR corporate, other suppliers, and potentially nationals (e.g. Home Depot class) must not assume one integration model. |
| Architectural decision | **ADR-033 Accepted** (docs only). Relationship **A** (contractor ↔ supplier procurement) distinct from **B** (CalibAi ↔ supplier channel). Do not collapse into PreferredSupplier. Anticipate national/enterprise capabilities; do not overbuild Winchester POC. Reference evidence families recorded for later measurement. No channel economics or analytics in a future POC. No Feature Gate. No product code. |
| Prompt template used | Bounded architecture documentation (Joel commercial clarification) |
| Approved Cursor prompt summary | ADD TO SUPPLIER CHANNEL ARCHITECTURE — DARCY / BMR WINCHESTER LAUNCH-PARTNER MODEL. Docs only. No exclusivity. No percentages. Do not implement supplier POC. |
| Files expected to change | Supplier channel architecture; ADR-033; indexes; catalogue/module/roadmap/vision/CAR-001; current-state; session-handoff; chat-workflow-log; milestones; project-state-report |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; product code; Alembic revisions; FG-013 product implementation |
| Implementation result | Architecture recorded. ADR-033 **Accepted**. Winchester/supplier integration **not implemented**. Darcy terms **unset**. |
| Tests | Docs-only pass. No product-code tests required. `git diff --check`. |
| Project-state-report update | Yes (architecture status only) |
| Milestone entry update | Architecture record appended (not a coded milestone) |
| Constitutional issue raised | None |
| Unresolved issues | Darcy commercial terms. Supplier Feature Gate not opened. Heterogeneous adapter designs deferred to later gates. |
| Next approved step | Do **not** start supplier integration. Next **product** action remains FG-013 live-migrate + UAT when separately authorized. |
| Next approved prompt | None for supplier/Winchester POC. FG-013 live-migrate only if Joel authorizes that prompt. |
| Commit hash | (this commit, if/when committed) |

### 2026-08-30 — FG-013 historical upload implementation

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `f52f06c4adbd04055485e49124da59222a8f7768` (start) |
| Objective | Implement FG-013 office UPLOAD PREVIOUS ESTIMATES, ADR-032 custody, one additive migration. |
| Business decision | Multi-file/folder UX; per-file outcomes; quarantine unknown layouts; TIER_A wording; no auto standards. |
| Architectural decision | `HistoricalUploadAttempt` only (no UploadBatch). Storage `instance/historical_uploads/<org>/<sha256>.<ext>`. Revision `c5d6e7f8a9b0`. Live migrate not applied. |
| Prompt template used | Bounded FG-013 implementation |
| Approved Cursor prompt summary | IMPLEMENT FG-013 — CONTRACTOR CALIBRATION ONBOARDING / HISTORICAL ESTIMATE UPLOAD UX. One additive Alembic revision authorized. Do not live-migrate unless established workflow requires a separate prompt — do not apply live. |
| Files expected to change | Models, routes, templates, ingestion/upload services, migration, tests, governed docs |
| Files prohibited from changing | Legacy Desktop corpus; labour/pricing standards writes; Phase D; auth |
| Implementation result | Implemented. Dedicated tests 27 passed. Full suite 310 passed. Live DB current remains `b4c5d6e7f8a9`. |
| Tests | `./venv/bin/python -m pytest -q tests/test_historical_upload_fg013.py` → 27 passed. `./venv/bin/python -m pytest -q` → 310 passed. Temp-DB upgrade/downgrade of `c5d6e7f8a9b0` verified. Live `flask db upgrade` **not** run. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture/implementation record appended |
| Constitutional issue raised | None |
| Unresolved issues | Live migrate + browser UAT pending. Folder-select not exercised in a live browser this pass. |
| Next approved step | Separate live-migrate + UAT smoke prompt. |
| Next approved prompt | Live-migrate `c5d6e7f8a9b0` only when Joel authorizes. |
| Commit hash | (this commit) |

### 2026-08-30 — FG-013 final governance + ADR-032 accepted

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `fc9fed32a7e2f18730a5778c1d09ab5597fe9b74` (start) |
| Objective | Complete FG-013 governance: storage/custody ADR, remaining gate answers, mark APPROVED FOR IMPLEMENTATION. Docs only. |
| Business decision | Productized historical uploads use app-managed private durable storage. Office upload before auth. Self-serve onboarding requires auth. Unknown layouts quarantine. TIER_A = estimate associated with a completed project, not ORG-ACTUAL. No auto standards. |
| Architectural decision | ADR-032 **Accepted**. Two custody regimes. Durable per-file upload attempts. **No** durable UploadBatch. SCHEMA YES additive; MIGRATION YES one bounded revision — **not created this pass**. |
| Prompt template used | Bounded FG-013 complete governance (documentation) |
| Approved Cursor prompt summary | COMPLETE FG-013 GOVERNANCE — HISTORICAL UPLOAD STORAGE / CUSTODY ADR + FINAL GATE APPROVAL. Do not implement. Do not create the migration. |
| Files expected to change | FG-013; ADR-032; ADR/feature-gate indexes; historical-ingestion and organization/calibration architecture; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log; milestones; docs indexes |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; product code; Alembic revisions |
| Implementation result | FG-013 **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED**. ADR-032 **Accepted**. Locked multi-file/folder UX preserved. No product code. No migration. |
| Tests | Docs-only pass. Last recorded full suite remains **283 passed**. Not re-run (no product code). `git diff --check`. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | FG-013 **implementation** not started. Migration not created. |
| Next approved step | **STOP PRODUCT CODE.** Wait for a separate FG-013 **implementation** prompt that explicitly authorizes the additive migration. |
| Next approved prompt | None unless Joel issues FG-013 implementation. |
| Commit hash | (this commit) |

### 2026-08-30 — FG-013 multi-file / folder upload UX locked

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `d41c4d92ee009cdc6679b140ecd44789362077f6` (start) |
| Objective | Memorialize Joel’s FG-013 UX rule: one user action may load many historical workbooks (multi-select, multi drop, folder where the client supports it). No durable UploadBatch for UX. Docs only. |
| Business decision | Users must not upload historical estimates one at a time. ~20–25 is guidance, not a quota. One failed/unsupported/duplicate/quarantined file must not block the rest. |
| Architectural decision | NO durable UploadBatch = database architecture only. Does not mean single-file upload. Per-file ingest remains the transaction unit. Combined results summary is request-scoped. Implementation not authorized. |
| Prompt template used | Bounded FG-013 governance clarification (documentation) |
| Approved Cursor prompt summary | ADD TO FG-013 GOVERNANCE — MULTI-FILE / FOLDER UPLOAD CLARIFICATION. Do not implement uploads. Do not create UploadBatch. |
| Files expected to change | FG-013 draft; feature-gates index; current-state; session-handoff; chat-workflow-log; roadmap as needed |
| Files prohibited from changing | `app/**`, `tests/**`, `migrations/**`, database |
| Implementation result | Created FG-013 as DRAFT FOR JOEL REVIEW with locked multi-file/folder section. Implementation not started. |
| Tests | Docs-only. Last recorded full suite **283 passed**. |
| Project-state-report update | Minimal (draft gate; not a coded milestone) |
| Milestone entry update | No (not a completed milestone) |
| Constitutional issue raised | None |
| Unresolved issues | FG-013 remainder (schema, storage ADR, quarantine, auth) not approved. Implementation not authorized. |
| Next approved step | **STOP DEVELOPMENT.** Do not implement FG-013. Joel reviews the draft gate. |
| Next approved prompt | None unless Joel authorizes remaining FG-013 answers or a later implementation prompt. |
| Commit hash | (this documentation commit) |

### 2026-08-30 — ADR-021 MONITOR baseline / Project Gross Margin acceptance

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `0b403d6aa51381d3763cf3dc9d5d96e096d5ab93` (start) |
| Objective | Accept ADR-021: MONITOR composed commercial baseline and Project Gross Margin. Governance / documentation only. |
| Business decision | Authoritative project metric is PROJECT GROSS MARGIN, not net profit. Frozen composed baseline: locked EstimateVersion + EstimatePricingSnapshot when present + Accepted Proposal + approved CO deltas as separate layers. Draft estimates/proposals must not be the committed baseline. |
| Architectural decision | MONITOR is a Project-centered comparison/read layer. Actuals owned by BUILD / later domains. Industry benchmarks not profitability truth. QuickBooks not mandatory. Phase D independent. No schema. No Feature Gate. MONITOR not implemented. |
| Prompt template used | Bounded ADR-021 governance pass (documentation) |
| Approved Cursor prompt summary | ADR-021 MONITOR BASELINE / PROJECT GROSS MARGIN GOVERNANCE PASS. Docs only. Do not implement MONITOR, BUILD actuals, profitability, benchmarking, or historical-upload onboarding. |
| Files expected to change | ADR-021 and supporting governed docs |
| Files prohibited from changing | `app/**`, `tests/**`, `migrations/**`, database, runtime configuration |
| Implementation result | ADR-021 set to Accepted. Module note `docs/modules/monitor.md` (not implemented). Supporting docs reconciled. |
| Tests | Docs-only; `git diff --check`. Product suite not re-run. Last recorded full suite **283 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (architecture record; no new M0xx) |
| Constitutional issue raised | None |
| Unresolved issues | CO estimated-cost delta not stored; no governed credits; labour-snapshot vs actual labour GM comparability; next product gate not authorized. ADR-010 Proposed. Phase D unauthorized. |
| Next approved step | **STOP DEVELOPMENT.** Do not implement MONITOR. Do not create a Feature Gate. |
| Next approved prompt | None. Joel chooses whether the next product gate is office historical-upload onboarding or authentication/BUILD. |
| Commit hash | (this documentation commit) |

### 2026-08-30 — FG-012 Estimate-Output Consistency implementation

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `17c2951cf586e15321756349ccd05d9133b719f3` (start) |
| Objective | Implement approved FG-012 Internal Detailed Cost Breakdown + Customer Estimate Consistency only. |
| Business decision | Estimating owns the internal breakdown. Existing Proposal remains the customer-facing estimate. Named-method totals copy frozen EstimatePricingSnapshot. Labour snapshots display-only, not in selling-price basis. No TBD/PLACEHOLDER schema. |
| Architectural decision | No new estimate entity, document module, or ADR. Preserve TRUE_GROSS_MARGIN / COST_PLUS_MARKUP / COST_PLUS_MARKUP_STACK / legacy no-snapshot. SCHEMA NO. MIGRATION NO. |
| Prompt template used | Bounded FG-012 implementation prompt (Feature Gate implementation) |
| Approved Cursor prompt summary | IMPLEMENT FG-012 INTERNAL DETAILED COST BREAKDOWN + CUSTOMER ESTIMATE CONSISTENCY. SCHEMA CHANGE NO. MIGRATION NO. No Phase D. No external AI. |
| Files expected to change | Estimating routes/templates/CSS; `app/services/estimate_output.py`; `app/services/proposals.py`; `app/services/proposal_pdf.py`; dedicated tests; governed docs |
| Files prohibited from changing | `migrations/**`, models/schemas, Phase D, auth, Dashboard counts |
| Implementation result | Internal breakdown route; named-method proposal totals; customer PDF OH/Profit leak closed; Estimate Totals method presentation; dedicated 19 tests; full suite 283. |
| Tests | Dedicated `tests/test_estimate_output_consistency.py` **19 passed**; listed regressions **183 passed**; full suite `./venv/bin/python -m pytest -q` **283 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (architecture record; no new M0xx) |
| Constitutional issue raised | None |
| Unresolved issues | Office proposal create/detail still lists Overhead/Profit amounts (zero for named methods). Live UAT estimates have no Allowance/labour snapshot rows (covered by tests). Phase D unauthorized. ADR-010 Proposed. Office auth not implemented. TBD/PLACEHOLDER durable state deferred. |
| Next approved step | **STOP DEVELOPMENT.** Do not begin another Feature Gate. |
| Next approved prompt | None. Phase D remains unauthorized. |
| Commit hash | (this implementation commit) |

### 2026-08-30 — FG-012 Estimate-Output Consistency governance approval

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `2733e2f3b68b7320f08f093875e272532cd78885` (start) |
| Objective | Memorialize Joel-approved FG-012 Internal Detailed Cost Breakdown + Customer Estimate Consistency. Documentation only. Do not implement. |
| Business decision | Estimating owns the internal breakdown. Existing Proposal remains the customer-facing estimate. Outputs 1 and 2 only. Direct Cost = Σ `extended_cost`. Labour snapshots not in selling-price basis. No TBD/PLACEHOLDER schema. Estimate Totals presentation and customer-PDF Overhead/Profit leak in FG-012 implementation scope. |
| Architectural decision | No new estimate entity, document module, or ADR. Consume FG-009 snapshots read-only. Preserve TRUE_GROSS_MARGIN / COST_PLUS_MARKUP / COST_PLUS_MARKUP_STACK / legacy no-snapshot. Source-contract principle for later outputs 3–4 only. Schema NO. Migration NO. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | FG-012 GOVERNANCE APPROVAL. Docs only. APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED. Do not implement FG-012. |
| Files expected to change | Governed docs listed in the prompt |
| Files prohibited from changing | `app/**`, `migrations/**`, tests, configuration |
| Implementation result | FG-012 created. Indexes and current-state/handoff/roadmap/module/package docs updated. No product code. |
| Tests / validation | `git diff --check`. Product tests not re-run (docs-only). Prior full suite **264 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | No (no new M0xx) |
| Constitutional issue raised | None |
| Unresolved issues | Implementation not started. Phase D unauthorized. ADR-010 Proposed. Office auth not implemented. TBD/PLACEHOLDER durable state deferred. |
| Next approved step | Separate bounded FG-012 **implementation** Cursor prompt. Do not implement in this pass. |
| Next approved prompt | FG-012 implementation (not this commit) |
| Commit hash | (this docs commit) |

### 2026-08-30 — FG-011 Project Hub UX implementation

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `225731a2208e16fea8558a048e8c34f0f4879549` (start) |
| Objective | Implement approved FG-011 Project Hub UX by evolving `/projects/<id>` only. |
| Business decision | Projects owns the hub UX. Hub reads and links stored facts. No new module, Job entity, schema, or ADR. |
| Architectural decision | PLAN / PRICE / CONTRACT from stored records; BUILD = existing Change Orders; field BUILD / MONITOR / LEARN / QuickBooks / four-output / Ontario contract / real AI labeled Future. Conservative pricing/labour presence only. Phase D unauthorized. Dashboard counts out of scope. |
| Prompt template used | Bounded FG-011 implementation prompt (Feature Gate implementation) |
| Approved Cursor prompt summary | IMPLEMENT FG-011 PROJECT HUB UX. Evolve existing project detail. SCHEMA CHANGE NO. MIGRATION NO. No Phase D. No external AI. |
| Files expected to change | `app/routes/projects.py`, `app/templates/projects/detail.html`, optional CSS/helper, dedicated tests, governed docs |
| Files prohibited from changing | `migrations/**`, models/schemas, take-off/pricing/labour write paths, Dashboard counts, auth |
| Implementation result | Project Hub on `/projects/<id>` with read-only `app/services/project_hub.py`. Dedicated tests added. Browser smoke on labeled FG-009/FG-010 UAT projects. |
| Tests / validation | Dedicated Project Hub **13 passed**. Full suite **264 passed**. `git diff --check` clean. Alembic current/head unchanged `b4c5d6e7f8a9`. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record only (no new M0xx) |
| Constitutional issue raised | None |
| Unresolved issues | Phase D unauthorized. ADR-010 Proposed. Office auth not implemented. Dashboard org-unscoped counts remain out of scope. FG-010 UAT project still has no commercial context recorded. |
| Next approved step | **STOP.** Do not start Phase D or another Feature Gate. |
| Next approved prompt | None. Next product work requires a new Feature Gate. |
| Commit hash | (this implementation commit) |

### 2026-08-30 — FG-011 Project Hub UX governance approval

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `49c490852fa5b129da7bd32fc7e446539140f30b` (start) |
| Objective | Memorialize Joel-approved FG-011 Project Hub UX. Documentation only. Do not implement. |
| Business decision | Evolve existing `/projects/<id>`. Projects owns the hub UX. No new module, Job entity, schema, or ADR. No M0xx. |
| Architectural decision | ADR-019 remains the hub-entity decision. Hub reads/links only. Conservative pricing/labour presentation. Phase D and external AI remain unauthorized. Dashboard org-unscoped counts out of scope. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | FG-011 GOVERNANCE APPROVAL. Docs only. APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED. |
| Files expected to change | Governed docs listed in the prompt |
| Files prohibited from changing | `app/**`, `migrations/**`, tests, configuration |
| Implementation result | FG-011 created. Indexes and current-state/handoff/roadmap updated. No product code. |
| Tests / validation | `git diff --check`. Product tests not re-run (docs-only). Prior full suite **251 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | No (no new M0xx) |
| Constitutional issue raised | None |
| Unresolved issues | Implementation not started. Phase D unauthorized. ADR-010 Proposed. Office auth not implemented. |
| Next approved step | Separate bounded FG-011 **implementation** Cursor prompt. Do not implement in this pass. |
| Next approved prompt | FG-011 implementation (not this commit) |
| Commit hash | (this docs commit) |

### 2026-08-30 — 29 Aug day-end reconciliation / Review Turnover

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` (start `316cc9f11c141d806737bb7caebdb7c37c5bda9b`) |
| Objective | Full 29 Aug repository / database / documentation / storage / Review Turnover audit. No product features. No Phase D. No external AI. |
| Business decision | Close FG-008 / FG-009 / FG-010 as **CLOSED / OPERATIONAL FOR UAT**. Leave synthetic UAT residue labeled. Next candidate (Project Hub UX) **NOT AUTHORIZED**. |
| Architectural decision | ADR-010 remains **Proposed**. Live Alembic current/head remains `b4c5d6e7f8a9`. No migrations created or altered. |
| Prompt template used | Review Turnover Protocol 22-point package + 29 Aug day-end reconciliation prompt |
| Approved Cursor prompt summary | READ → VERIFY → RECONCILE → TEST → DOCUMENT → COMMIT → PUSH → VERIFY → TURN OVER → STOP. Docs only. |
| Files expected to change | Governed docs only |
| Files prohibited from changing | `app/**` product code; `migrations/**`; tests; historical/commercial source files |
| Implementation result | Pre-flight matched start pins. All listed 29 Aug SHAs are ancestors of `main`. Origin parity. No untracked files. Linear Alembic chain to `b4c5d6e7f8a9`. Live DB snapshot recorded. Stale current-state Alembic/test/next-action language corrected. Complete 22-point `session-handoff.md` including Fresh Chat Startup Prompt. |
| Tests | take-off **18**; Plan Intelligence **56**; Pricing **33**; Labour **25**; Historical **11**; full **251**. `git diff --check` clean. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Historical 0.13 labour-rate cluster; material-as-labour labels; crew/duration inconsistencies; ORG-001 optional layers unspecified; labour-snapshot cost not in estimate basis by default; Estimate Totals header leftover percents (UI debt); take-off cancel not implemented; ARCH-only eligibility; actor-string identity; ADR-010 Proposed; Phase D not started; office auth not implemented; synthetic UAT residue left labeled. |
| Next approved step | **STOP DEVELOPMENT.** Fresh session uses `docs/session-handoff.md` §22. |
| Next approved prompt | None. Next candidate Project Hub UX requires a new Feature Gate. |
| Commit hash | (this docs reconciliation commit) |

### 2026-08-30 — FG-010 / M012 live migration and synthetic UAT smoke

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` |
| Objective | Apply `b4c5d6e7f8a9` to live development/UAT and perform bounded synthetic browser/UAT smoke. No external AI. No Phase D. No new milestone. |
| Business decision | Live migration authorized. Synthetic UAT only. Leave labeled FG-010 UAT residue. |
| Architectural decision | COUNT remains dimensionless. Dimensional measurement remains scale-governed. ADR-010 remains Proposed. |
| Prompt template used | FG-010 LIVE DEVELOPMENT/UAT MIGRATION + SYNTHETIC SMOKE VERIFICATION |
| Approved Cursor prompt summary | PRE-FLIGHT → TEST GATE → SNAPSHOT → UPGRADE → SCHEMA/INTEGRITY → SYNTHETIC UAT → BROWSER SMOKE → REGRESSION → DOCS RECONCILE → COMMIT/PUSH → STOP. |
| Files expected to change | Governed docs only after live migrate. |
| Files prohibited from changing | Product code; committed migration; historical/commercial records; Labour/Pricing logic. |
| Implementation result | Live current/head `b4c5d6e7f8a9`. Synthetic searchable run produced 4 mock candidates; 3 accepted + 1 duplicate; approved package total 3; immutable; rerun distinct; COUNT without scale succeeded; linear/polyline/area fail-closed; Estimate/Labour/Pricing deltas **ZERO**; external calls **ZERO**. Browser smoke: take-off index, run submit (run 3), candidate review, approved package UI. |
| Tests | Pre and post: take-off **18**; Plan Intelligence **56**; Pricing **33**; Labour **25**; Historical **11**; full **251**. `git diff --check` clean. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Cancel-run operation missing (accepted). ARCH-only eligibility. Actor-string reviewer identity until auth. Real provider undecided. Phase D mapping future. Synthetic FG-009 and FG-010 residue left labeled. |
| Next approved step | **STOP DEVELOPMENT.** Day-End Reconciliation / Review Turnover audit. |
| Next approved prompt | Single clean-turnover prompt for complete end-of-day audit and tomorrow-start package. |
| Commit hash | (this docs reconciliation commit; implementation `9665295ace673a46a8c645ed0598e5e91d41931c`) |

### 2026-08-29 — FG-010 / M012 implementation commit and push

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Final audit, commit, and push the reviewed FG-010 foundation. No live migrate. No external AI. No Phase D. |
| Business decision | PASS — approved for commit. Live database migration remains unauthorized. |
| Architectural decision | One implementation commit. Graph head `b4c5d6e7f8a9`. Live current remains `a3b4c5d6e7f8`. ADR-010 remains Proposed. |
| Prompt template used | FG-010 FINAL AUDIT + IMPLEMENTATION COMMIT / PUSH AUTHORIZATION |
| Approved Cursor prompt summary | VERIFY → AUDIT → TEST → STAGE → COMMIT → PUSH → STOP. Do not flask db upgrade. |
| Files expected to change | Reviewed FG-010 product + docs + migration `b4c5d6e7f8a9`. |
| Files prohibited from changing | Labour/Pricing commercial logic; historical workbooks; Accepted proposals; live DB schema. |
| Implementation result | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED** / **NOT YET LIVE-MIGRATED**. External provider calls: **ZERO**. Estimate/labour/pricing writes: **ZERO**. |
| Tests | Dedicated take-off **18**; Plan Intelligence combined **56**; Pricing **33**; Labour **25**; Historical **11**; full suite **251**. `git diff --check` clean. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Live DB still `a3b4c5d6e7f8`. Browser/live UAT not yet performed. No cancel-run operation (accepted for synchronous POC). |
| Next approved step | Separate live-migrate + UAT smoke authorization. |
| Next approved prompt | Apply `b4c5d6e7f8a9` to live development/UAT and bounded synthetic browser/UAT smoke. |
| Commit hash | (this commit) |

### 2026-08-29 — FG-010 / M012 foundation implementation (uncommitted)

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Implement FG-010 provider-neutral AI take-off foundation. No live migrate. No commit. No external AI. No Phase D. |
| Business decision | Interior-door COUNT POC via deterministic mock. Package approval is PLAN evidence only. COUNT does not require scale. |
| Architectural decision | First-class `TakeoffExtractionRun` / `TakeoffCandidate` / `TakeoffPackage` / `TakeoffPackageItem`. ADR-027 coordinates only. PlanAuditEvent extended. Org-scoped rows. Mock extractor `calibai-mock`. |
| Prompt template used | FG-010 BOUNDED IMPLEMENTATION AUTHORIZATION |
| Approved Cursor prompt summary | PRESERVE → VERIFY → IMPLEMENT FOUNDATION → TEST → REPORT → STOP. NO COMMIT. NO PUSH. NO LIVE MIGRATION. NO EXTERNAL AI. NO PHASE D. |
| Files expected to change | Plan Intelligence models/services/routes/templates; one additive migration; dedicated tests; governed docs. |
| Files prohibited from changing | Labour Engine / Pricing Engine commercial logic; EstimateVersion writes; historical workbooks; Accepted proposals. |
| Implementation result | **IMPLEMENTED / VERIFIED** / **NOT YET LIVE-MIGRATED**. External provider calls: **ZERO**. Estimate/labour/pricing writes: **ZERO**. |
| Tests | Dedicated take-off **18 passed**; Plan Intelligence combined **56 passed**; Pricing **33**; Labour **25**; Historical **11**; full suite **251**. `git diff --check` clean. Temp migration `a3b4c5d6e7f8` → `b4c5d6e7f8a9` → `a3b4c5d6e7f8`. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None. ADR-006: package approval does not insert estimate lines. |
| Unresolved issues | Uncommitted working tree. Live DB still `a3b4c5d6e7f8`. |
| Next approved step | Joel/ChatGPT governance review. |
| Next approved prompt | Separate commit/push authorization if review PASSes. Do not live-migrate in that prompt unless explicitly authorized. |
| Commit hash | **None** (this pass forbids commit) |

### 2026-08-29 — FG-010 governance approval (documentation commit)

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Approve FG-010 for implementation; Accept ADR-005/006/007/009/011/031; keep ADR-010 Proposed; record COUNT-without-scale and provider-not-authorized conditions; docs-only commit/push. |
| Business decision | M012 POC remains searchable PDF, `INTERIOR_DOOR_OPENING` COUNT. Package approval is not EstimateVersion insertion. |
| Architectural decision | COUNT is dimensionless (narrow authorized M010 count/scale correction in a later implementation prompt). Real external AI provider **not authorized**. Dimensional measurements remain fail-closed. |
| Prompt template used | FG-010 GOVERNANCE APPROVAL + DOCUMENTATION COMMIT |
| Approved Cursor prompt summary | APPROVE → RECONCILE → REGRESS → COMMIT → PUSH → STOP. NO PRODUCT CODE. NO MIGRATION. NO PROVIDER INTEGRATION. |
| Files expected to change | Governed docs only. |
| Files prohibited from changing | `app/`; `migrations/`; `tests/`; historical workbooks; Labour Engine / Pricing Engine product logic. |
| Implementation result | FG-010 **APPROVED FOR IMPLEMENTATION** / **NOT IMPLEMENTED**. Product code **NONE**. |
| Tests | Plan Intelligence combined **51**; Pricing **33**; Labour **25**; Historical **11**; full suite **228**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None. ADR-006 clarification: human take-off approval does not authorize estimate insert in M012. |
| Next approved prompt | Separate bounded FG-010 implementation prompt. Do not implement in this pass. |

### 2026-08-29 — FG-010 / M012 AI Take-off architecture and Feature Gate preparation

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Architecture / ADR reconciliation / Feature Gate preparation for AI Take-off / Quantity Extraction Foundation. No product implementation. |
| Business decision | Next coded candidate after FG-009 closure is M012 interior-door **count** from searchable architectural PDFs, with mandatory human review. Mapping into Estimating is **out of this gate**. |
| Architectural decision | Plan Intelligence owns take-off. First-class extraction run, candidate, and immutable package (ADR-031 **Proposed**). Reuse ADR-027 coordinates. Do not overload `PlanMeasurement`. COUNT V1 must not require scale. New take-off rows carry `organization_id`. |
| Prompt template used | AI TAKE-OFF / QUANTITY EXTRACTION FOUNDATION — ARCHITECTURE / ADR RECONCILIATION / FEATURE GATE PREPARATION |
| Approved Cursor prompt summary | READ → AUDIT → RECONCILE → ARCHITECT → PREPARE → STOP. NO PRODUCT IMPLEMENTATION. NO COMMIT. NO PUSH. |
| Files expected to change | Governed docs only. |
| Files prohibited from changing | `app/`; `migrations/`; historical workbooks; Labour Engine / Pricing Engine product logic; Accepted proposals. |
| Implementation result | Docs package prepared. FG-010 **PREPARED FOR GOVERNANCE APPROVAL**. Product code **NONE**. Migration **NONE**. |
| Tests | Plan Intelligence combined **51**; Pricing **33**; Labour **25**; Historical **11**; full suite **228**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append architecture-prepared record) |
| Constitutional issue raised | None blocking. Recommend Accept ADR-005/006/007/009/011 with FG-010; do not bulk-accept ADR-010. |
| Next approved prompt | None. Governance review of FG-010 + ADR-031. Do not implement AI take-off. |

### 2026-08-29 — FG-009 live development/UAT migration and UAT smoke

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Final preflight; apply committed FG-009 migration `a3b4c5d6e7f8`; verify seed/schema; bounded Pricing Engine UAT smoke; regression; docs reconciliation. STOP. |
| Business decision | Live migrate authorized for development/UAT only. ORG-001 15% TRUE_GM and 13% HST remain org-scoped. Optional layers remain `UNSPECIFIED`. No second organization created. Synthetic UAT labels only. |
| Architectural decision | No new product code. No new migration. No AI take-off. Labour-snapshot Direct Labour Cost remains excluded from estimate basis by default. |
| Prompt template used | Live development/UAT migration + Pricing Engine smoke verification (this session). |
| Approved Cursor prompt summary | PRESERVE → VERIFY → MIGRATE → SMOKE → REGRESSION → RECONCILE → STOP. `flask db upgrade` explicitly authorized. Do not start AI take-off. |
| Files expected to change | Governed docs only (plus live SQLite schema/seed/UAT rows). |
| Files prohibited from changing | Product code; committed migration file; historical workbooks; Labour Engine production logic; Accepted proposals; customer-facing proposal templates. |
| Implementation result | Migration `f2c3d4e5f6a7` → `a3b4c5d6e7f8` succeeded. UAT smoke passed. Docs reconciled. |
| Tests | Pricing **33**; Labour **25**; Historical **11**; full suite **228**. `git diff --check` clean. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Synthetic FG-009 UAT residue remains (Draft estimates / WITHDRAWN markup policy / COs). ORG-001 optional layers remain `UNSPECIFIED`. |
| Next approved step | FG-009 closure review, then prepare the next Feature Gate for AI Take-off / Quantity Extraction Foundation. |
| Next approved prompt | None in this pass. Do not start AI take-off. |
| Commit hash | Docs-only reconcile (record after push) |

### 2026-08-29 — FG-009 implementation commit and push

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Commit and push the reviewed FG-009 foundation. Do not apply live migration. |
| Business decision | Governance PASS — approved for commit. ADR-025 **Accepted**. ADR-030 **Accepted**. Live migrate not authorized by this prompt. |
| Architectural decision | One implementation commit. Graph head `a3b4c5d6e7f8`. Live current remains `f2c3d4e5f6a7`. |
| Prompt template used | Commit + push authorization (this session). |
| Approved Cursor prompt summary | PRESERVE → AUDIT → TEST → COMMIT → PUSH → VERIFY → STOP. Do not flask db upgrade. Do not start AI take-off. |
| Files expected to change | Reviewed FG-009 product + docs + migration `a3b4c5d6e7f8`. |
| Files prohibited from changing | Historical workbooks; Labour Engine production logic; live DB. |
| Implementation result | Committed and pushed. Live DB not migrated. |
| Tests | Pricing **33**; Labour **25**; Historical **11**; full suite **228**. `git diff --check` clean. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Live migrate not authorized. ORG-001 optional layers remain `UNSPECIFIED`. |
| Next approved step | Separate live-migrate + UAT-smoke authorization. |
| Next approved prompt | Apply `a3b4c5d6e7f8` to live development/UAT only when separately authorized. |
| Commit hash | Recorded after push (`git log -1`) |

### 2026-08-29 — FG-009 final pre-commit implementation review

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Preserve the uncommitted FG-009 tree; reconstruct from code; review against FG-009 / ADR-025 / ADR-030; resolve only remaining genuine FG-009 blockers; re-test; report. No commit, push, or live migrate. |
| Business decision | No new commercial values. ORG-001 15% TRUE_GM and 13% HST remain org-scoped. Optional layers remain `UNSPECIFIED`. |
| Architectural decision | Review found **no remaining FG-009 blockers**. Prior bounded correction already applies inherited CO methods via `price_change_order_from_snapshot` and seeds optional layers as `UNSPECIFIED`. `CALIBAI_BASELINE` is a resolution-source constant only; live fail-closed path is `PROVISIONAL_LEGACY_STACK`. Unlinked COs without snapshot remain legacy. ADR-025 and ADR-030 remain **Accepted**. |
| Prompt template used | Final pre-commit implementation review authorization (this session). |
| Approved Cursor prompt summary | PRESERVE → RECONSTRUCT → CORRECT ONLY FG-009 BLOCKERS → TEST → REPORT → STOP. Do not reimplement. Do not reset/stash. Do not commit/push. Do not apply live migration. |
| Files expected to change | Docs only if needed to record this review. Product code only if a genuine blocker remained. |
| Files prohibited from changing | Historical workbooks; FG-006 facts; Labour Engine production/calibration; Accepted proposals; live DB; new Alembic revision; AI take-off / BUILD / MONITOR / LEARN. |
| Implementation result | **No product-code change this pass.** Existing dirty FG-009 tree preserved. Review complete. Not committed. Live DB not migrated. |
| Tests | `tests/test_pricing_engine.py` **33 passed**; `tests/test_labour_engine.py` **25 passed**; `tests/test_historical_ingestion.py` **11 passed**; full suite **228 passed**. `git diff --check` clean. |
| Project-state-report update | Counts already current; this review confirms them. |
| Milestone entry update | No new milestone. |
| Constitutional issue raised | None |
| Unresolved issues | Commit/push/live-migrate not authorized. ORG-001 overhead/profit/contingency remain `UNSPECIFIED`. Labour-snapshot cost not in estimate basis by default. |
| Next approved step | Joel / ChatGPT governance review of this stopping report. **Do not commit. Do not push. Do not migrate live DB.** |
| Next approved prompt | None until review. Then commit (if approved), then a separate live-migrate prompt. |
| Commit hash | **None** (this pass) |

### 2026-08-29 — FG-009 pre-commit bounded correction (CO method + ORG-001 seed)

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Correct two governance issues in the uncommitted FG-009 tree before commit: (1) FG-009-aware Change Orders must apply inherited pricing METHOD; (2) ORG-001 optional layers must seed as `UNSPECIFIED`, not `NOT_APPLIED`. |
| Business decision | `NOT_APPLIED` is an org-approved commercial decision. Ungoverned overhead/profit/contingency remain `UNSPECIFIED`. TRUE_GM 15% and HST 13% unchanged. FG-009-aware COs apply method identity; legacy COs without snapshot unchanged. |
| Architectural decision | Reuse Pricing Engine `compute_named_method_pre_tax` / `legacy_stack_pre_tax` / `apply_tax_after_pre_tax` from Project Controls via `price_change_order_from_snapshot`. Do not invent a second engine. Copy snapshotted CO lines as direct/extended cost. Correct uncommitted migration `a3b4c5d6e7f8` in place; no new revision. ADR-025 and ADR-030 remain **Accepted**. |
| Prompt template used | Bounded pre-commit correction authorization (this session). |
| Approved Cursor prompt summary | PRE-COMMIT BOUNDED CORRECTION PASS only. Do not reimplement FG-009. Do not reset/stash/discard. Do not commit/push. Do not apply live migration. |
| Files expected to change | Pricing Engine models/services; Project Controls recalculate/copy-lines; uncommitted migration seed; tests; FG-009/module/handoff docs. |
| Files prohibited from changing | Historical workbooks; FG-006 facts; Labour Engine production/calibration; Accepted proposals; live DB; new Alembic revision. |
| Implementation result | **Complete in working tree.** Not committed. Live DB not migrated. Existing FG-009 implementation preserved. |
| Tests | `tests/test_pricing_engine.py` **33 passed**; `tests/test_labour_engine.py` **25 passed**; `tests/test_historical_ingestion.py` **11 passed**; full suite **228 passed**. `git diff --check` clean. Alembic `f2c3d4e5f6a7` → `a3b4c5d6e7f8` → downgrade in dedicated test. |
| Project-state-report update | Yes |
| Milestone entry update | Append-only correction record |
| Constitutional issue raised | None |
| Unresolved issues | Commit/push/live-migrate not authorized. ORG-001 overhead/profit/contingency remain `UNSPECIFIED`. Labour-snapshot cost not included in estimate basis by default. |
| Next approved step | Joel / ChatGPT governance review of the bounded-correction stopping report. **Do not commit. Do not push. Do not migrate live DB.** |
| Next approved prompt | None until review. Then commit (if approved), then a separate live-migrate prompt. |
| Commit hash | **None** (this pass) |

### 2026-08-29 — FG-009 Organization-Calibrated Pricing Engine implementation

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Implement FG-009 only: versioned org pricing policies, named methods, resolution, immutable estimate snapshots, ORG-001 seed, legacy compatibility, Change Order inheritance, tenant isolation, dedicated tests. |
| Business decision | CalibAi owns methods; orgs own rates. ORG-001 15% true GM and 13% HST are org-scoped, not platform defaults. New estimates are not auto-converted. Contingency/overhead for ORG-001 remain `NOT_APPLIED` (not invented). |
| Architectural decision | Route estimate recalc through snapshot if present else legacy stack. Do not delete legacy logic. Labour snapshot Direct Labour Cost is consume-only and not added to the estimate basis by default. Pricing Posture / Execution Risk snapshot-only. |
| Prompt template used | Bounded FG-009 implementation authorization (this session). |
| Approved Cursor prompt summary | Implement FG-009 Organization-Calibrated Pricing Engine foundation only. One additive migration. Do not commit/push. Do not migrate live DB. Do not expand into four-output, QuickBooks, contracts, Labour Engine expansion, historical evidence repair, ML, or BUILD/MONITOR/LEARN. |
| Files expected to change | Pricing Engine models/services/routes/templates; estimate builder routing; CO inheritance; migration `a3b4c5d6e7f8`; `tests/test_pricing_engine.py`; FG-009/docs status. |
| Files prohibited from changing | Historical workbooks; FG-006 facts; accepted proposal immutability rules; Labour Engine production/calibration logic (except read-only consume); live DB. |
| Implementation result | **Complete in working tree.** Not committed. Live DB not migrated. |
| Tests | `tests/test_pricing_engine.py` **26 passed**; `tests/test_labour_engine.py` **25 passed**; `tests/test_historical_ingestion.py` **11 passed**; full suite **221 passed**. `git diff --check` clean. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record (implementation; not a numbered milestone) |
| Constitutional issue raised | None |
| Unresolved issues | Commit/push/live-migrate not authorized. ORG-001 contingency treatment remains `NOT_APPLIED`. Labour-snapshot cost not included in estimate basis by default. |
| Next approved step | Joel / ChatGPT governance review. **Do not commit. Do not push. Do not migrate live DB.** |
| Next approved prompt | None until review. Then commit (if approved), then a separate live-migrate prompt. |
| Commit hash | **None** (this pass) |

### 2026-08-29 — FG-009 governance approval / documentation commit

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Finalize FG-009 architecture approval, accept ADR-025 and ADR-030, adopt contingency source vs pricing-treatment clarification, commit and push docs only. No product implementation. |
| Business decision | Joel/ChatGPT: FG-009 architecture approved (subject to contingency clarification); Feature Gate **APPROVED FOR IMPLEMENTATION**; ADR-025 **AMEND AND ACCEPT**; ADR-030 **ACCEPT**. Implementation **not authorized**. |
| Architectural decision | Contingency **source/purpose** distinct from **visibility** (`INTERNAL_RESERVE` / `CUSTOMER_PRICED` / `NOT_APPLIED`) and from **pricing treatment** (`INCLUDED_IN_MARGIN_BASIS` / `ADDED_AFTER_BASE_PRICING`). Overhead not equated with GM. TRUE_GROSS_MARGIN must not hide COST_PLUS_MARKUP_STACK. FG-009-aware COs inherit estimate snapshot; historical COs not rewritten. |
| Prompt template used | `docs/prompts/cursor-documentation-template.md` (authorized governance-finalization prompt, this session). |
| Approved Cursor prompt summary | Docs/governance only: accept ADRs, approve FG-009, contingency clarification, tests, commit, push. No product code, no migration, no pricing calculation change. |
| Files expected to change | `docs/**` FG-009 / ADR-025 / ADR-030 / indexes / handoff. |
| Files prohibited from changing | Product code, migrations, tests (except running them). |
| Implementation result | **Docs/governance only.** Live estimate formula unchanged. |
| Tests | `tests/test_labour_engine.py`; `tests/test_historical_ingestion.py`; full suite; `git diff --check` — exact counts in stopping report. |
| Project-state-report update | Yes — FG-009 approved for implementation; not a coded milestone |
| Milestone entry update | Architecture record updated (not a product milestone) |
| Constitutional issue raised | None |
| Unresolved issues | Selling-price code still the legacy stack until a separate implementation prompt. |
| Next approved step | Issue a separately authorized bounded FG-009 **implementation** prompt. |
| Next approved prompt | FG-009 implementation (not this pass). |
| Commit hash | (this commit) |

### 2026-08-29 — Organization-Calibrated Pricing Engine architecture / ADR-025 / FG-009 preparation

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | READ → AUDIT → RECONCILE → ARCHITECT → PREPARE → STOP. No product implementation. Prepare FG-009 Organization-Calibrated Pricing Engine; resolve ADR-025 recommendation; correct stale FG-008 docs. |
| Business decision | CalibAi owns methodology; each org owns commercial intelligence. ORG-001 15% **true gross margin** (`Direct / 0.85`) is not 15% markup and is not a CalibAi universal default. Historical “15% margin” labels are evidence, not auto-policy. |
| Architectural decision | **AMEND AND ACCEPT** ADR-025 recommended: named methods `TRUE_GROSS_MARGIN`, `COST_PLUS_MARKUP`, `COST_PLUS_MARKUP_STACK` (preserve live stack as explicit method; do not globally replace; do not map 15% GM onto 15% markup). ADR-030 Proposed for org policy records + estimate pricing snapshots + CO inheritance. File statuses remain **Proposed**. FG-009 **PREPARED FOR GOVERNANCE APPROVAL**. |
| Prompt template used | `docs/prompts/cursor-documentation-template.md` (authorized architecture / Feature Gate prompt, this session). |
| Approved Cursor prompt summary | Audit pricing code; reconcile vs `pricing-policy.md`; define org-calibrated engine; prepare next FG; amend ADR-025; no product code; no migration; no commit; no push. |
| Files expected to change | `docs/architecture/organization-calibrated-pricing-engine-architecture.md`, `docs/feature-gates/FG-009-*`, `docs/adr/ADR-025-*`, `docs/adr/ADR-030-*`, `docs/modules/pricing-engine.md`, indexes, current-state, session-handoff, roadmap, chat-workflow-log, milestones architecture record. |
| Files prohibited from changing | Product code, migrations, tests (except running them), historical workbooks, selling-price implementation. |
| Implementation result | **Docs/architecture only.** Live estimate formula unchanged. |
| Tests | `tests/test_labour_engine.py`; `tests/test_historical_ingestion.py`; full suite; `git diff --check` — exact counts in stopping report. |
| Project-state-report update | Yes — FG-009 prepared; not a coded milestone |
| Milestone entry update | Architecture record only (not a product milestone) |
| Constitutional issue raised | None new. Article 5 (immutability) and org-owned commercial intelligence constrain implementation. |
| Unresolved issues | FG-009 / ADR-025 / ADR-030 not accepted by Joel. Live CO math still inconsistent with estimates (architecture records the defect; code unchanged). |
| Next approved step | Joel / ChatGPT governance review. **Do not implement. Do not commit unless requested.** |
| Next approved prompt | None for implementation. |
| Commit hash | **None** (this pass) |

### 2026-08-29 — FG-008 post-UAT integrity stabilization

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Close two FG-008 live-UAT integrity issues: accidental ACCEPTED mapping; labour audit for nonexistent ORG-999. Not a new milestone. |
| Business decision | Preserve historical evidence and append-only audit. Revoke (do not silently rewrite) the accidental accept. Do not create Organization ORG-999. |
| Architectural decision | Added `REVOKED` mapping status (String(20), no migration). Rule suggestions join `LabourTask.status == ACTIVE`. `record_labour_audit` refuses unknown orgs. Unknown-org resolution returns fail-closed without persisting audit. Existing ORG-999 audit row preserved; ORG-001 reconciliation event recorded. DRAFT synthetic production standard withdrawn via existing `WITHDRAWN` approval status. |
| Prompt template used | Authorized post-UAT integrity stabilization prompt (this session). |
| Approved Cursor prompt summary | Inspect mapping/audit architecture; add REVOKED if narrowest; exclude archived tasks from rule suggestion; prevent unknown-org audit persist; reconcile live UAT mapping 1; tests; docs; commit/push if clean; STOP. |
| Files expected to change | `app/models/labour_engine.py`, `app/services/labour_engine.py`, `app/routes/labour_engine.py`, `app/templates/labour_engine/*`, `tests/test_labour_engine.py`, `docs/*` |
| Files prohibited from changing | Historical workbooks/facts, pricing-policy, estimate selling-price, ADR-025, Plan Intelligence, Accepted Proposals, migrations |
| Implementation result | Mapping 1 `REVOKED`. HistoricalLabourItem 1 unchanged. Archived-task rule-suggestion blocked. Unknown-org resolution does not persist audit. ORG-999 audit id 16 preserved; reconciliation event 23 under ORG-001. PRS 1 `WITHDRAWN`. |
| Tests | `tests/test_labour_engine.py` → **25 passed**; `tests/test_historical_ingestion.py` → **11 passed**; full suite → **195 passed**, 293 warnings |
| Project-state-report update | Yes — test counts; not a new milestone |
| Milestone entry update | Architecture record only (not a product milestone) |
| Constitutional issue raised | None |
| Unresolved issues | SQLite did not enforce FK on the preserved ORG-999 audit row; documented as historical UAT anomaly. Mapping 4 created then REJECTED during live verification probe. |
| Next approved step | **STOP.** |
| Next approved prompt | None |
| Commit hash | (this commit) |

### 2026-08-29 — FG-008 live development/UAT migration and UAT smoke

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Apply committed FG-008 migration `f2c3d4e5f6a7` to live development/UAT; verify schema/seed/historical integrity; bounded Labour Engine smoke; regression tests; docs-only reconciliation. |
| Business decision | Live migrate authorized. No new schema, no product code, no historical evidence repair, no Pricing Engine. |
| Architectural decision | `flask db upgrade` `e1b2c3d4e5f6` → `f2c3d4e5f6a7`. ORG-001 $65 CAD/man-hour seed confirmed org-specific. Historical counts unchanged (20 workbooks, 20 estimates, 120 labour items). Foundation operational for UAT only. |
| Prompt template used | Authorized live-migration + smoke verification prompt (this session). |
| Approved Cursor prompt summary | Final preflight; apply `f2c3d4e5f6a7`; verify tables/seed/history; UI/service smoke; 22/11/192 tests; docs-only if live-migrated state must be recorded; commit/push docs-only; STOP. |
| Files expected to change | `docs/*` migration-state reconciliation only. No product code. No new migration. |
| Files prohibited from changing | `app/**`, `migrations/**`, `tests/**`, historical evidence, `docs/pricing-policy.md` |
| Implementation result | Upgrade succeeded. Seven FG-008 tables present. Live current/head `f2c3d4e5f6a7`. UAT smoke performed. Leftover synthetic UAT records identified (archived task `UAT-FG008-001`; mapping 1 ACCEPTED to that UAT task; DRAFT 999.000001 production standard; WITHDRAWN candidate). |
| Tests | `./venv/bin/python -m pytest -q tests/test_labour_engine.py` → **22 passed**; `./venv/bin/python -m pytest -q tests/test_historical_ingestion.py` → **11 passed**; `./venv/bin/python -m pytest -q` → **192 passed**, 119 warnings (pre- and post-upgrade). |
| Project-state-report update | Yes — live current/head `f2c3d4e5f6a7` |
| Milestone entry update | Yes — append live-migration record |
| Constitutional issue raised | None |
| Unresolved issues | No live estimate versions for snapshot UAT (0 estimates); snapshot path covered by automated tests. Accidental ACCEPTED mapping of historical item 1 to UAT task during smoke (source row unchanged). One `LabourAuditEvent` with `organization_id=ORG-999` from a nonexistent-org resolution probe (no Organization row created). |
| Next approved step | **STOP.** Do not start the next milestone. |
| Next approved prompt | None |
| Commit hash | Product code `0569f25e7ff496ab637d52437d48cf815522afa1`; docs-only reconciliation this session |

### 2026-08-29 — FG-008 Labour Engine Phase B commit and push

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Final audit, commit, and push of the reviewed FG-008 Labour Engine Phase B implementation. **Do not upgrade the live database.** |
| Business decision | FG-008 implementation stopping report **PASS — ACCEPTED FOR COMMIT**. Labour Engine stops at direct labour cost. ADR-025 remains **Proposed**. |
| Architectural decision | Unchanged from implementation: org-owned LabourTask; human mapping; versioned production vs direct labour cost rates; no silent multipliers; historical rows immutable; calibration candidate lifecycle; tenant fail-closed. |
| Prompt template used | Bounded FG-008 commit/push authorization (this session) |
| Approved Cursor prompt summary | Audit uncommitted FG-008; re-run 22/11/192 tests; commit one implementation+docs commit; push `origin/main`; leave live Alembic at `e1b2c3d4e5f6`. |
| Files expected to change | FG-008 product files, wiring, migration `f2c3d4e5f6a7`, dedicated tests, governed docs |
| Files prohibited from changing | Historical workbooks; HistoricalLabourItem facts; Plan Intelligence; proposals; pricing-policy values; estimate selling-price formula; ADR-025 status; live DB |
| Implementation result | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED.** Live DB **not** migrated. |
| Tests | `tests/test_labour_engine.py` → **22 passed**; `tests/test_historical_ingestion.py` → **11 passed**; full suite → **192 passed**; `git diff --check` clean |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Live Alembic upgrade `f2c3d4e5f6a7` not applied (expected). ORG-001 canonical task catalog remains empty by design. |
| Next approved step | Separate authorization to apply `f2c3d4e5f6a7` to live development/UAT DB and smoke-verify. |
| Next approved prompt | **None.** Do not start another milestone. |
| Commit hash | *(this FG-008 implementation commit)* |

### 2026-08-29 — FG-008 Labour Engine Phase B implementation (not committed)

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Implement FG-008 Labour Engine Phase B foundation only. Return a stopping report. **Do not commit or push.** |
| Business decision | FG-008 **APPROVED FOR IMPLEMENTATION** (ADR-029 **Accepted**). CalibAi owns methodology; each organization owns labour intelligence. Labour Engine stops at direct labour cost. |
| Architectural decision | Org-owned LabourTask; human mapping (no auto-accept); versioned ProductionRateStandard separate from DirectLabourCostRateStandard; Calibration Candidate state machine; explainable resolution; immutable EstimateLabourSnapshot; ORG-001 $65 seeded as org policy only; no silent multipliers. |
| Prompt template used | Bounded FG-008 implementation authorization (this session) |
| Approved Cursor prompt summary | Implement FG-008 only from `820f54afc179279d2435ad3a426b3037548bb45e`. Additive models/migration/services/office UI/tests. No pricing-engine, ADR-025, AI take-off, BUILD/MONITOR, payroll, QuickBooks, contracts, cross-org learning. Do not commit or push. |
| Files expected to change | Labour Engine models/services/routes/templates; one Alembic revision; dedicated tests; governed docs after tests pass |
| Files prohibited from changing | Historical workbooks; HistoricalLabourItem facts; Plan Intelligence; Accepted proposals; M011 versioning; pricing-policy values; estimate selling-price formula; ADR-025 status |
| Implementation result | Implemented in working tree. Stopping report issued. **Not committed.** |
| Tests | `./venv/bin/python -m pytest -q tests/test_labour_engine.py` → **22 passed**, 55 warnings; `./venv/bin/python -m pytest -q tests/test_historical_ingestion.py` → **11 passed**; `./venv/bin/python -m pytest -q` → **192 passed**, 119 warnings |
| Project-state-report update | Yes |
| Milestone entry update | Yes (FG-008 implementation pending commit) |
| Constitutional issue raised | None |
| Unresolved issues | Commit/push not authorized; live Alembic upgrade not applied; ORG-001 canonical task catalog remains empty by design |
| Next approved step | Governance review of stopping report. Commit/push only if separately authorized. |
| Next approved prompt | **None.** |
| Commit hash | *(uncommitted — prompt forbade commit)* |

### 2026-08-29 — FG-008 architecture approved; ADR-029 Accepted; documentation commit

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Record Joel/ChatGPT approval of FG-008 architecture and ADR-029. Commit documentation only. **No product implementation.** |
| Business decision | FG-008 architecture **APPROVED FOR IMPLEMENTATION**. ADR-029 **Accepted**. Implementation **has not started** and requires a separate execution prompt. |
| Architectural decision | Unchanged from the reviewed stopping report: canonical LabourTask; human mapping; versioned production vs direct labour cost rates; no silent multipliers; historical rows immutable evidence; calibration candidate lifecycle; tenant fail-closed; Labour Engine stops at direct labour cost. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | Finalize FG-008 / ADR-029 governance status; confirm docs consistency; test; **one** docs commit; push `origin/main`. No app/, migrations/, or implementation tests. |
| Files expected to change | `docs/` only |
| Files prohibited from changing | Application code, models, migrations, routes, templates, services, tests, historical workbooks, pricing-policy rate/formula values |
| Implementation result | Governance statuses updated. Labour Engine **not implemented**. |
| Tests | See this session’s stopping report (full suite + historical ingestion). |
| Project-state-report update | Yes |
| Milestone entry update | Yes (FG-008 architecture record status) |
| Constitutional issue raised | None |
| Unresolved issues | Implementation prompt not issued; historical rate-quality defects remain unrepaired by design. |
| Next approved step | Bounded FG-008 implementation prompt (not issued in this pass). |
| Next approved prompt | **None.** |
| Commit hash | *(this approval commit)* |

### 2026-08-29 — FG-008 Labour Engine Phase B architecture / Feature Gate preparation

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Prepare FG-008 Labour Engine Phase B / Organization Labour Calibration Foundation: architecture, Feature Gate, ADR-029, stale-doc corrections. **No product implementation.** |
| Business decision | CalibAi owns methodology; each organization owns labour intelligence. ORG-001 $65/hr and 15% true gross margin are Brayman policy, not platform defaults. Historical labour remains evidence. No hidden hour multipliers. Crew catalog and burden modeling deferred. |
| Architectural decision | Canonical org-owned Labour Tasks with human-reviewed mappings; versioned Production Rate Standard separate from Direct Labour Cost Rate Standard; Calibration Candidate state machine; explainable resolution; estimate labour snapshots; actuals architecture defined but persistence deferred; ADR-029 **Proposed**; org architecture §18 automatic condition multiplier **not authorized** for labour. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | Joel authorized FG-008 **preparation only** (analysis, architecture, Feature Gate, ADR, stale SHA/ADR-028/M009 doc cleanup). Explicitly **not** product code, migration, schema, routes, UI, live engine, pricing change, historical source mutation, commit, or push. |
| Files expected to change | Docs/governance under `docs/` only |
| Files prohibited from changing | Application code, models, migrations, routes, templates, services, tests, historical workbooks, `pricing-policy.md` rate/formula values |
| Implementation result | Documentation prepared. FG-008 **not approved**. Labour Engine **not implemented**. |
| Tests | Before edits: `./venv/bin/python -m pytest -q` → **170 passed**, 64 warnings (27.26s); `./venv/bin/python -m pytest -q tests/test_historical_ingestion.py` → **11 passed** (10.15s). After docs: same commands → **170 passed**, 64 warnings (29.54s); **11 passed** (12.79s). |
| Project-state-report update | Yes |
| Milestone entry update | Yes (architecture record FG-008; CAR-001 M009 subsequent-status correction) |
| Constitutional issue raised | None. Articles 5–6, 9, 11 respected (no schema; no invented policy; historical records not rewritten). |
| Unresolved issues | Joel approval of FG-008/ADR-029; ORG-001 canonical task seed; actuals persistence timing; historical rate-quality defects remain as evidence (not repaired). |
| Next approved step | **None for implementation.** Review FG-008. |
| Next approved prompt | **None.** |
| Commit hash | *(uncommitted documentation pass — Joel has not directed commit)* |

### 2026-08-28 — Post-FG-006 Governance & Turnover State Reconciliation

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Comprehensive documentation-only state reconciliation post-FG-006. Audit repository docs, remove stale references to uncommitted states / obsolete test baselines / old Alembic heads, align current-state, session-handoff, project-state-report, roadmap, milestones, feature gates, and ADRs with authoritative commit `690d755d9901e04eb783198f4b89071fbeaf472a`. |
| Business decision | Documentation is the governing system of record. All operational and roadmap documents must truthfully reflect the completion of M011 and FG-006 and the protected/blocked status of future calibration modules. |
| Architectural decision | Reconciled all documentation across `docs/` to canonical truth: HEAD/origin `690d755d9901e04eb783198f4b89071fbeaf472a`, Alembic head `e1b2c3d4e5f6`, 170 tests passing (11 dedicated historical ingestion tests), 20/20 source workbooks SHA-256 verified, ORG-001 private evidence, commercial evidence anchors (Mike Pratt, Julia Harish, Allen Jacques), and explicit next candidate status (Labour Engine Phase B — NOT STARTED; REQUIRES SEPARATE GOVERNANCE AUTHORIZATION). Zero code, migration, or schema changes. |
| Prompt template used | Approved custom Cursor prompt (Post-FG-006 Governance & Turnover Reconciliation) |
| Approved Cursor prompt summary | Documentation-only state reconciliation: verify repo state (HEAD `690d755`, Alembic `e1b2c3d4e5f6`, 170 tests); audit and correct stale references across docs/; update current-state, session-handoff, project-state-report, roadmap, milestones, FG-006/FG-007, ADR-028, architecture docs; validate docs-only diff; run pytest baseline; output comprehensive stopping report. |
| Files expected to change | `docs/current-state.md`, `docs/session-handoff.md`, `docs/project-state-report.md`, `docs/milestones.md`, `docs/platform-roadmap.md`, `docs/feature-gates/README.md`, `docs/feature-gates/FG-006-historical-estimate-ingestion-phase-b.md`, `docs/feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md`, `docs/adr/ADR-028-organization-foundation-and-project-commercial-context.md`, `docs/architecture/historical-estimate-ingestion-architecture.md`, `docs/architecture/historical-estimates-source-manifest.md`, `docs/architecture/organization-and-calibration-architecture.md`, `docs/README.md`, `docs/chat-workflow-log.md` |
| Files prohibited from changing | `app/*`, `migrations/*`, `tests/*`, dependencies, database records, historical source workbooks |
| Implementation result | Documentation fully reconciled and aligned across the entire repository. Working tree contains only documentation changes. |
| Tests | `./venv/bin/python -m pytest -q` → **170 passed**, 64 legacy warnings |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | None. Repository in clean turnover state. |
| Next approved step | Ready for final turnover commit and handoff. |
| Next approved prompt | None approved (turnover state). Next candidate: Labour Engine Phase B architecture / Feature Gate preparation (NOT STARTED). |
| Commit hash | Reconciled against `690d755d9901e04eb783198f4b89071fbeaf472a` |

### 2026-08-28 — FG-006 Implementation: Historical Estimate Ingestion Engine Phase B

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Implement deterministic, organization-aware ingestion of historical estimate workbooks into CalibAi's governed evidence model (FG-006 Phase B). Ingest the 20 Brayman source workbooks into ORG-001 private intelligence. |
| Business decision | Historical workbooks contain private commercial evidence for future calibration. Ingestion must extract facts deterministically with source-cell provenance without executing macros, altering source files, or converting historical data into approved pricing/labour rates automatically. |
| Architectural decision | (1) Implemented pure Python OpenXML reader (`app/services/historical_ingestion/openxml_reader.py`) reading spreadsheet XML directly without executing macros or VBA; (2) Implemented deterministic template classifier (`template_classifier.py`) categorizing all 20 workbooks into Families A–E (9 Slab, 5 ICF, 1 Multi-trade, 1 Build, 4 Ad-hoc); (3) Implemented versioned family adapters (`family_a.py` through `family_e.py`); (4) Created canonical normalized models (`HistoricalSourceWorkbook`, `HistoricalEstimate`, `HistoricalSourceObservation`, `HistoricalCostLineItem`, `HistoricalLabourItem`, `HistoricalSubcontractItem`, `HistoricalDataQualityFlag`, `HistoricalEstimateReviewDecision`); (5) Enforced organization isolation on all tables (`ORG-001`); (6) Created additive Alembic migration `e1b2c3d4e5f6`; (7) Implemented evidence review service and UI routes/templates (`/historical-estimates/`); (8) Verified 20/20 SHA-256 source file integrity before and after ingestion; (9) Implemented 10 dedicated tests in `tests/test_historical_ingestion.py`. |
| Prompt template used | Approved custom Cursor prompt (FG-006 Historical Estimate Ingestion Engine Phase B) |
| Approved Cursor prompt summary | Implement deterministic OpenXML reader, template classifier, family adapters, canonical models, additive migration, human review UI, isolation tests, pilot regression anchors, and controlled UAT ingestion of 20 Brayman workbooks into ORG-001. Stop and report. Do not commit. Do not push. |
| Files expected to change | `app/models/historical_estimates.py`, `app/models/__init__.py`, `app/services/historical_ingestion/*`, `app/services/historical_review.py`, `app/routes/historical_estimates.py`, `app/templates/historical_estimates/*`, `app/navigation.py`, `migrations/versions/e1b2c3d4e5f6_add_historical_estimate_ingestion_fg006.py`, `tests/test_historical_ingestion.py`, `docs/*` |
| Files prohibited from changing | Protected Plan Intelligence geometry, accepted proposals, current pricing policy, source historical workbooks (`~/Desktop/CalibAi Historical Estimates`), Labour Engine Phase B (blocked), Pricing Engine (blocked) |
| Implementation result | Completed FG-006 implementation and controlled ingestion. 20 source workbooks ingested into ORG-001 (661 cost items, 120 labour items, 7 subcontract items, 664 source observations, 19 quality flags). 10/10 dedicated tests pass; 169/169 full suite tests pass. 20/20 source SHA-256 hashes verified exact. |
| Tests | `./venv/bin/python -m pytest -q tests/test_historical_ingestion.py` → **11 passed**; `./venv/bin/python -m pytest -q` → **170 passed** |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | None |
| Next approved step | Governance review and commit authorization for FG-006. |
| Next approved prompt | FG-006 Commit Authorization |
| Commit hash | `690d755d9901e04eb783198f4b89071fbeaf472a` |

### 2026-08-28 — M011 Final Implementation Reconciliation: Legacy Commercial Context Correction

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Correct M011 legacy commercial context backfill semantics to prevent fabricating historical commercial decisions. Ensure pre-M011 records explicitly reflect `Legacy / Unknown` across all 7 parameters, reject `Legacy / Unknown` for new projects, display human-readable legacy notices in UI, preserve old estimate version pinning to legacy-unknown context, and verify with dedicated tests and migration validation. |
| Business decision | Pre-M011 commercial decisions were not recorded historically. Assigning arbitrary default values (e.g. Specialty, Fair Market, Self-Perform) would contaminate future CalibAi calibration/analytics. Explicit `Legacy / Unknown` semantics guarantees CalibAi will never falsely infer historical pricing posture, risk, or delivery model from pre-M011 projects. |
| Architectural decision | (1) Updated Alembic migration `d0a1b2c3d4e5` to backfill `project_commercial_contexts` with `Legacy / Unknown` for all 7 decision fields and explicit change summary/provenance; (2) Added `is_legacy_unknown` property on `ProjectCommercialContext`; (3) Enforced that `Legacy / Unknown` is rejected in `validate_commercial_context_data` on new project creation or ordinary editing; (4) Updated project detail and context edit UI templates to render a clean "Legacy project — commercial context not recorded" notice; (5) Preserved immutable reference of historical `EstimateVersion` records to the legacy-unknown v1 context even if the project is subsequently updated to v2; (6) Added dedicated tests in `tests/test_organization_foundation.py`. |
| Prompt template used | Approved custom Cursor prompt (Bounded M011 Correction) |
| Approved Cursor prompt summary | Correct legacy commercial context backfill semantics: update migration d0a1b2c3d4e5 to use explicit `Legacy / Unknown`; enforce option validation rejecting legacy-unknown on new projects; update project templates for legacy notice; add tests proving legacy unknown creation, option rejection, and estimate version pinning; re-run migration validation and pytest suite; update docs; output stopping report. Do not commit. Do not push. |
| Files expected to change | `migrations/versions/d0a1b2c3d4e5_add_organization_foundation_m011.py`, `app/models/project.py`, `app/services/commercial_context.py`, `app/templates/projects/detail.html`, `app/templates/projects/edit_context.html`, `tests/test_organization_foundation.py`, `docs/current-state.md`, `docs/session-handoff.md`, `docs/chat-workflow-log.md` |
| Files prohibited from changing | Protected Plan Intelligence geometry, accepted proposals, pricing formulas, historical workbooks |
| Implementation result | Completed legacy commercial context correction. 19/19 dedicated M011 tests pass; 159/159 full suite tests pass. Upgrade/downgrade migration cycle verified. |
| Tests | `./venv/bin/python -m pytest tests/test_organization_foundation.py -v` → **19 passed**; `./venv/bin/python -m pytest -q` → **159 passed** |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None. Protects future learning/calibration from contaminated historical assumptions. |
| Unresolved issues | None for M011. Ready for governance audit and commit. |
| Next approved step | Submit stopping report for Joel / ChatGPT review prior to governance commit. |
| Next approved prompt | Pending governance commit. |
| Commit hash | Pending governance audit (do not commit / do not push) |

### 2026-08-28 — Milestone 011 Implementation: Organization Foundation & Project Commercial Context (FG-007 / ADR-028)

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Bounded product implementation of M011 authorized by FG-007 / ADR-028. Minimum organization-aware foundation, Brayman ORG-001 seed/backfill, direct ownership, tenant query scoping, versioned Project Commercial Context, immutable EstimateVersion references, policy-driven justification, and test suite. |
| Business decision | Establishes the canonical Organization entity (`ORG-001` Brayman Construction Inc.), backfills existing single-tenant data, and requires explicit 7-parameter commercial decision assumptions at project creation. Pricing calculations and multipliers remain completely unaffected in M011. |
| Architectural decision | Implemented per ADR-028: (1) `Organization` model in `app/models/organization.py`, (2) Direct `organization_id` FK on `Client`, `Project`, `CostItem`, `Assembly`, `ProposalTemplate`, (3) Composite uniqueness constraints (`organization_id` + `code`/`name`), (4) Single-tenant context helper `get_current_organization_id()` defaulting to `ORG-001`, (5) Tenant-safe fail-closed query isolation on all root and child entities, (6) Versioned `ProjectCommercialContext` with atomic V1 creation and immutable historical versions, (7) Policy-driven justification engine (`ORGANIZATION_REASON_POLICIES`), (8) Mandatory 7-parameter commercial decision gate in Project form and context update UI, (9) Immutable `EstimateVersion.commercial_context_id` capture, (10) Controlled additive Alembic migration `d0a1b2c3d4e5` with deterministic legacy backfill. |
| Prompt template used | `docs/prompts/cursor-feature-template.md` (Bounded Product Implementation) |
| Approved Cursor prompt summary | Execute M011 implementation: verify repo pins; read governing docs; implement Organization model; add direct ownership FKs; implement context helper and query isolation; implement ProjectCommercialContext model, controlled option sets, policy-driven justification; update Project creation/editing routes/templates; capture EstimateVersion context; create additive Alembic migration `d0a1b2c3d4e5` with ORG-001 seed and deterministic backfill; author `tests/test_organization_foundation.py`; verify full test suite; update governed docs; output stopping report. Do not commit. Do not push. |
| Files expected to change | `app/models/organization.py` (created), `app/models/project.py`, `app/models/client.py`, `app/models/cost_item.py`, `app/models/assembly.py`, `app/models/proposal.py`, `app/models/estimate.py`, `app/models/__init__.py`, `app/services/organizations.py` (created), `app/services/commercial_context.py` (created), `app/services/proposals.py`, `app/services/estimates.py`, `app/routes/projects.py`, `app/routes/clients.py`, `app/routes/cost_library.py`, `app/routes/assemblies.py`, `app/routes/proposal_templates.py`, `app/routes/estimates.py`, `app/routes/proposals.py`, `app/project_controls/repository.py`, `app/project_controls/routes.py`, `app/plan_intelligence/routes.py`, `app/templates/projects/form.html`, `app/templates/projects/detail.html`, `app/templates/projects/edit_context.html` (created), `migrations/versions/d0a1b2c3d4e5_add_organization_foundation_m011.py` (created), `tests/test_organization_foundation.py` (created), docs/ |
| Files prohibited from changing | Protected Plan Intelligence coordinate system/geometry, accepted proposal immutability, existing pricing formulas/gross margins, source historical workbooks |
| Implementation result | Completed full M011 implementation. All models, routes, services, templates, migrations, and test suites delivered cleanly. |
| Tests | `./venv/bin/python -m pytest -q` → **157 passed**, 61 warnings in 11.45s |
| Project-state-report update | Yes |
| Milestone entry update | Yes (M011 added to milestones) |
| Constitutional issue raised | Guaranteed customer commercial data isolation, historical assumption immutability, and policy-driven justification flexibility without modifying core pricing math. |
| Unresolved issues | None for M011. Ready for governance audit. |
| Next approved step | Submit implementation stopping report for Joel / ChatGPT review prior to governance commit. |
| Next approved prompt | FG-006 Historical Ingestion Phase B or Labour Engine Phase B prompt (after commit). |
| Commit hash | Pending governance audit (do not commit / do not push per instructions) |

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Prepare the first implementation Feature Gate (FG-007) and ADR-028 for the minimum organization-aware foundation and Project Creation Commercial Decision Gate required before Phase B Ingestion (FG-006), Labour Engine, and Calibrated Pricing Engine. |
| Business decision | Authorizes conceptual scope for `Organization` entity (`ORG-001` Brayman Construction seed/backfill), direct vs inherited ownership graph, versioned `ProjectCommercialContext` with 7 mandatory commercial decision parameters, decision provenance, and frozen estimate version context references. |
| Architectural decision | Defined ADR-028 and Feature Gate FG-007: (1) Minimal `Organization` entity, (2) Direct FK on root models (`Client`, `Project`, `CostItem`, `Assembly`, `ProposalTemplate`), (3) Inherited ownership through `Project` for child models (`Estimate`, `Proposal`, `ChangeOrder`, `PlanDocument`), (4) Dedicated versioned `ProjectCommercialContext` entity with policy-driven justification requirements, (5) Immutable `commercial_context_id` FK on `EstimateVersion`, (6) Service-level organization query scoping (`get_current_organization_id()`), (7) Controlled additive migration and backfill plan to `ORG-001` with minimal interruption objective. |
| Prompt template used | `docs/prompts/cursor-documentation-template.md` (Feature Gate Preparation) |
| Approved Cursor prompt summary | Execute 25-point Feature Gate Preparation: verify repo state; read governed state; specify M011 scope, Organization entity V1, ownership graph, tenant isolation V1, Brayman backfill strategy, Project Commercial Context V1, option sets, provenance model, estimate frozen context reference, pricing posture and execution risk invariants, estimate stage semantics, app impact audit, migration risks & mitigations, security baseline, test plan, UAT plan, ADR-028, and FG-007; update docs; confirm Phase B ingestion (FG-006), Labour Engine, and Pricing Engine remain blocked; run validation; output stopping report. |
| Files expected to change | `docs/feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md` (created), `docs/adr/ADR-028-organization-foundation-and-project-commercial-context.md` (created), `docs/feature-gates/README.md` (updated), `docs/adr/README.md` (updated), `docs/chat-workflow-log.md` (updated), `docs/current-state.md` (updated), `docs/session-handoff.md` (updated) |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, dependencies, database schema, UI, source workbooks in `~/Desktop/CalibAi Historical Estimates` |
| Implementation result | Prepared comprehensive Feature Gate FG-007, authored ADR-028, updated indexes and governance tracking documents. 0 lines of product code modified. 0 migrations created. |
| Tests | `git diff --check` (clean), `git status --short` (clean docs only) |
| Project-state-report update | Not required (Feature Gate preparation stage) |
| Milestone entry update | Not required |
| Constitutional issue raised | Guaranteed complete historical provenance for all estimate pricing assumptions and isolated customer commercial data. Prevented Brayman-specific rates from becoming CalibAi core platform defaults. |
| Unresolved issues | None for Feature Gate preparation. M011 implementation is NOT authorized and awaits explicit Joel / ChatGPT approval. Phase B Ingestion (FG-006), Labour Engine, and Calibrated Pricing Engine remain BLOCKED. |
| Next approved step | Submit FG-007 and ADR-028 for Joel Brayman / ChatGPT governance review and implementation authorization. |
| Next approved prompt | M011 Implementation Prompt (if approved). |
| Commit hash | Working tree uncommitted (pending governance review per instructions) |

### 2026-08-28 — CalibAi / Brayman Estimator: Organization & Calibration Architecture — Phase A

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Establish organization-aware commercial architecture required before CalibAi can implement organization-specific pricing, labour calibration, historical ingestion, or commercial learning. |
| Business decision | Governing Principle: CalibAi owns the engine and methodology; each customer organization owns its commercial intelligence; Brayman Construction is the first development/UAT organization (Org 001), not the universal CalibAi pricing model. |
| Architectural decision | Defined 3-tier commercial architecture (CalibAi Core vs Baseline Library vs Organization Calibration Model); specified canonical `Organization` entity; built Data Ownership Matrix; established 7-tier Evidence Hierarchy (`ORG-APPROVED`, `CURRENT`, `ORG-ACTUAL`, `ORG-HISTORICAL`, `BASELINE`, `PROVISIONAL`, `MANUAL`) with ORG-APPROVED as active operating standard and ORG-ACTUAL as empirical calibration evidence proposing review candidates; defined 7-phase Calibration Lifecycle and version immutability; specified 7-level Rate Resolution Cascade; defined 7-parameter Project Commercial Decision Gate with provenance and reason requirements; separated Direct Cost Economics from Commercial Pricing Strategy; defined multi-tenant isolation; prohibited cross-organization benchmarking; generalized analytical learning to technology-neutral methods; audited existing application models and routes (zero impact in Phase A; additive migration path for Phase B). |
| Prompt template used | `docs/prompts/cursor-architecture-template.md` (Architecture & Governance Specification) |
| Approved Cursor prompt summary | Execute 28-point Organization & Calibration Architecture Phase A: verify repo state; read governed state; specify CalibAi Core vs Baseline vs Org Model, canonical Organization, Data Ownership Matrix, Evidence Hierarchy, Calibration Lifecycle & Versioning, Rate Resolution Cascade, Commercial Decision Gate, Provenance, Reason Requirements, Pricing Posture, Execution Risk, Historical Learning, Tenant Isolation, Benchmarking Prohibition, Ingestion/Labour/Pricing Reconciliations, Branding, Integrations, UAT Org 001, Read-Only Impact Audit; generate `docs/architecture/organization-and-calibration-architecture.md`; update docs; enforce Phase B blocking condition; run test suite (140 passed); output stopping report. |
| Files expected to change | `docs/architecture/organization-and-calibration-architecture.md` (created), `docs/README.md` (updated), `docs/chat-workflow-log.md` (updated), `docs/current-state.md` (updated), `docs/session-handoff.md` (updated) |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, dependencies, source workbooks in `~/Desktop/CalibAi Historical Estimates` |
| Implementation result | Completed comprehensive 25-section architecture specification (`docs/architecture/organization-and-calibration-architecture.md`), updated README, current-state, session-handoff, and chat-workflow-log. 0 lines of app/migration/test code modified. |
| Tests | `git diff --check` (clean), `./venv/bin/python -m pytest -q` (140 passed) |
| Project-state-report update | Not required (Phase A is architectural specification stage) |
| Milestone entry update | Not required |
| Constitutional issue raised | Confirmed customer commercial data ownership, multi-tenant isolation, and strict prohibition on cross-organization benchmarking without legal governance. Decoupled physical direct cost economics from commercial pricing strategy. |
| Unresolved issues | None for Phase A. Phase B Ingestion (FG-006), Labour Engine (Phase B), and Calibrated Pricing Engine remain BLOCKED pending review and approval of this Phase A architecture. |
| Next approved step | Submit Phase A Organization & Calibration Architecture package for Joel / ChatGPT governance review. |
| Next approved prompt | FG-006 Historical Ingestion Engine (Phase B) Feature Gate prompt. |
| Commit hash | Working tree uncommitted (pending governance review per instructions) |

### 2026-08-28 — Historical Estimate Ingestion — Phase A (Source Audit & Ingestion Architecture)

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Perform read-only source data audit, profiling, and ingestion architecture design across 20 historical Brayman estimating workbooks located outside Git repository |
| Business decision | Historical estimates are commercial evidence of past pricing and estimating patterns, not automatic pricing truth or proof of profitability. Raw customer workbooks remain external and immutable. |
| Architectural decision | Categorized 20 workbooks into 5 template families (Family A: 9, Family B: 5, Family C: 1, Family D: 1, Family E: 4). Discovered historical workbooks use Cost-Plus Markup (10-15%) rather than true Gross Margin. Defined organization-neutral cell-level provenance model, 8-tier data quality / contradiction model, 6-tier historical evidence hierarchy, and canonical normalized schema design with Organization ownership. |
| Prompt template used | `docs/prompts/cursor-architecture-template.md` (Read-only audit & architecture) |
| Approved Cursor prompt summary | Read-only inspect `~/Desktop/CalibAi Historical Estimates`; calculate SHA-256 hashes; profile structure & content; detect pricing methods; design cell-level provenance, contradiction model, evidence hierarchy, and normalized schema; run pilot extraction on 5 workbooks; produce manifest and architecture specification; verify source files unchanged; do not commit. |
| Files expected to change | `docs/architecture/historical-estimates-source-manifest.md` (created), `docs/architecture/historical-estimate-ingestion-architecture.md` (created), `docs/chat-workflow-log.md` (updated), `docs/current-state.md` (updated), `docs/session-handoff.md` (updated) |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, dependencies, source workbooks in `~/Desktop/CalibAi Historical Estimates` |
| Implementation result | Completed full 20-workbook forensic audit, generated source provenance manifest, created comprehensive ingestion architecture specification, conducted 5-workbook pilot extraction, verified 100% source byte immutability. No code, migrations, or UI modified. |
| Tests | Python verification scripts for OpenXML zip parsing, SHA-256 integrity, cell extraction; `./venv/bin/python -m pytest -q` (140 passed) |
| Project-state-report update | Not required (Phase A is research / architecture stage) |
| Milestone entry update | Not required |
| Constitutional issue raised | Identified pricing methodology gap between historical cost-plus markup and governing 15% true gross margin policy (`pricing-policy.md` / `ADR-025`). Confirmed CalibAi Core vs Customer Organization separation. |
| Unresolved issues | None for Phase A. Phase B is explicitly blocked pending review and approval of CalibAi Organization & Calibration Architecture — Phase A. |
| Next approved step | Execute Organization & Calibration Architecture Phase A before any Phase B implementation. |
| Next approved prompt | Organization & Calibration Architecture — Phase A prompt. |
| Commit hash | `3461d2eb791d6382eab71e43d15f6b54b62a9192` (`3461d2e`) |

### 2026-08-28 — Implement Milestone 010 (Scale Calibration & Manual Measurement Tools)

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Implement M010 Scale Calibration and Manual Measurement Tools strictly per FG-005: durable scale calibration and measurement models, additive migration, service layer, human confirmation workflow, normalized document coordinates, interactive PDF.js viewer, and focused test suite. |
| Business decision | Estimators can calibrate physical scale on reviewed drawing sheets using 2-point reference dimensions or standard architectural/metric presets, define multi-scale viewports, and take manual linear, polyline, polygon area (Shoelace) / perimeter, and count measurements with coordinate stability. |
| Architectural decision | Additive models `PlanScaleCalibration` and `PlanMeasurement` under `PlanSheet` (scoped to `DrawingRevision`). ADR-026 and ADR-027 marked Accepted. Normalized document coordinate system (`[0.0, 1.0]`) rendered via Mozilla PDF.js in Flask templates with interactive SVG/Canvas overlay. Human confirmation required; uncalibrated/NTS fails closed. Additive migration `c9e0f1a2b3d4`. |
| Prompt template used | Approved custom Cursor implementation prompt (FG-005 Approved) |
| Approved Cursor prompt summary | Anti-drift preflight; mark ADR-026/027 Accepted; verify Alembic head `b8d9f0a1c2e3`; implement models, migration `c9e0f1a2b3d4`, services (`scale_measurement.py`), routes, viewer template (`sheet_measure.html`), controller (`sheet-measurement.js`); 19 focused tests in `tests/test_scale_measurement.py`; full test suite; documentation update; commit and push. |
| Files expected to change | `app/plan_intelligence/models.py`, `app/plan_intelligence/routes.py`, `app/plan_intelligence/scale_measurement.py`, `app/templates/plan_intelligence/**`, `app/static/js/**`, `migrations/versions/c9e0f1a2b3d4_add_scale_measurement_m010.py`, `tests/test_scale_measurement.py`, documentation. |
| Files prohibited from changing | Estimating commercial calculations, Proposals, Change Orders, CRM, Auth, Contracts, QuickBooks. |
| Implementation result | Full M010 implementation completed and verified. 19 focused tests pass. Full test suite (140 tests) pass. |
| Tests | `pytest tests/test_scale_measurement.py -v` (19 passed), `pytest -q` (140 passed) |
| Project-state-report update | Yes |
| Milestone entry update | Yes — Milestone 010 |
| Constitutional issue raised | None. Human authority strictly enforced (no auto-confirmation of scale). |
| Unresolved issues | None for M010. Automated quantity take-off deferred to M011+. |
| Next approved step | Feature Gate and architecture for M011 — AI Take-off / Quantity Extraction Foundation. |
| Next approved prompt | M011 Feature Gate prompt |
| Commit hash | `6b969fe` — *feat: implement M010 scale calibration* |

### 2026-08-28 — Prepare and Approve M010 Scale Calibration Feature Gate (FG-005)

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Prepare the formal Feature Gate FG-005 and architecture records for M010 — Scale Calibration / Measurement Tools. No product code, schema changes, or migrations. |
| Business decision | Estimators can calibrate physical scale on reviewed drawing sheets using 2-point reference dimensions or standard ratios, define multi-scale viewports, and take manual linear, polyline, area, and count measurements with coordinate stability. |
| Architectural decision | Additive models `PlanScaleCalibration` and `PlanMeasurement` under `PlanSheet` (scoped to `DrawingRevision`). Normalized document coordinate system (`0.0 to 1.0` / 72 DPI PDF points) rendered via Mozilla PDF.js in Flask templates with interactive SVG/Canvas overlay. Human authority required for confirmation; uncalibrated/NTS fails closed. Proposed ADR-026 (Scale Ownership & Multi-Scale Provenance) and ADR-027 (PDF Rendering & Normalized Coordinate System). |
| Prompt template used | Approved custom Cursor prompt (documentation/governance) |
| Approved Cursor prompt summary | Anti-drift preflight; existing-before-new search; create `docs/feature-gates/FG-005-m010-scale-calibration.md`, `docs/adr/ADR-026-scale-ownership-and-calibration-provenance.md`, `docs/adr/ADR-027-pdf-rendering-and-normalized-coordinate-system.md`; update indexes, roadmap, milestones, state, handoff, and log; validate; commit; push. |
| Files expected to change | Documentation and governance files only |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, models/schemas |
| Implementation result | FG-005 prepared and approved; ADR-026 and ADR-027 proposed; governance indexes and state reports updated. M010 code not begun. |
| Tests | `git diff --check`, `pytest -q` (121 passed) |
| Project-state-report update | Yes |
| Milestone entry update | Yes (`milestones.md` FG-005 added) |
| Constitutional issue raised | None |
| Unresolved issues | None for FG-005 |
| Next approved step | Dedicated M010 implementation Cursor prompt citing FG-005 |
| Next approved prompt | M010 implementation prompt |
| Commit hash | `f8da43c` |

### 2026-08-28 — Review Turnover Reconciliation Repair

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Repair Review Turnover package and governance documents: reconcile accepted ADR list (ADR-002, 017, 018, 019, 020, 022, 023, 024), classify PRICE as PARTIAL (pricing policy calculation migration Proposed in ADR-025), correct LEARN reference to ADR-024, align baseline pins (`5dc4b09` implementation, `39ae8fe` turnover adoption), and remove stale pre-implementation notes. |
| Business decision | Maintain rigorous anti-drift discipline so that repository documents remain 100% authoritative and internally consistent. |
| Architectural decision | No product code or schema changes. ADR statuses, lifecycle classifications, and baseline pins reconciled to exact repository truth. |
| Prompt template used | Approved custom Cursor prompt (documentation/governance repair) |
| Approved Cursor prompt summary | Preflight; audit 22-point turnover package; repair ADR list, lifecycle states, LEARN boundary, and baseline pins across `session-handoff.md`, `review-turnover-protocol.md`, `current-state.md`, `project-state-report.md`, `platform-roadmap.md`, and `milestones.md`; validate; commit; push. |
| Files expected to change | Documentation and governance files only |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, models/schemas |
| Implementation result | All four known defects and remaining documentation inconsistencies reconciled. Completeness test passed. |
| Tests | `git diff --check`, `pytest -q` (121 passed) |
| Project-state-report update | Yes (Part B fully updated) |
| Milestone entry update | Yes (`milestones.md` FG-004 and M009 updated) |
| Constitutional issue raised | None |
| Unresolved issues | None |
| Next approved step | Prepare Feature Gate for M010 Scale Calibration / Measurement Tools |
| Next approved prompt | M010 Feature Gate |
| Commit hash | `ed3e51f` |

### 2026-08-28 — Adopt Review Turnover Protocol

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Adopt the comprehensive repository-backed Review Turnover Protocol triggered by the exact phrase `Review Turnover` for safe chat rollover and anti-drift reconciliation. |
| Business decision | Enable deterministic, repository-backed session turnover so any long/stale conversation can be discarded and a fresh session started from repository evidence alone. |
| Architectural decision | Review Turnover Protocol (`docs/governance/review-turnover-protocol.md`) adopted as governing. Chat is expendable upon `TURNOVER PASS`. `docs/session-handoff.md` integrated with 22-point standard turnover package. |
| Prompt template used | Approved custom Cursor prompt (governance-only) |
| Approved Cursor prompt summary | Anti-drift preflight; existing-before-new search; create `docs/governance/review-turnover-protocol.md`; integrate governance docs (`AGENTS.md`, `README.md`, `continuity-and-anti-drift.md`, `platform-governance.md`, `development-workflow.md`, `session-handoff.md`, `current-state.md`); validate; commit; push. |
| Files expected to change | Governance and documentation files only |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, models/schemas |
| Implementation result | Protocol adopted. All governance references updated. 22-point turnover package and startup prompt integrated in session handoff. |
| Tests | `git diff --check`, `pytest -q` (121 passed) |
| Project-state-report update | Yes |
| Milestone entry update | Not required (governance update, not a new coded milestone) |
| Constitutional issue raised | None |
| Unresolved issues | None |
| Next approved step | Prepare Feature Gate for M010 Scale Calibration / Measurement Tools |
| Next approved prompt | M010 Feature Gate |
| Commit hash | `39ae8fe` |

### 2026-08-28 — Implement M009 Sheet Classification / Human Metadata Review

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Implement authorized M009 scope per FG-004: Sheet models, page mappings, suggestions, human review workflow (accept/edit/reject/void), uniqueness validation, migration, and office review UI. |
| Business decision | Estimators can classify PDF pages into logical drawing Sheets, review suggestions with human authority, manage non-1:1 page mappings, and validate/finalize revision sheet indices before downstream scale/take-off. |
| Architectural decision | Additive schema `plan_sheets`, `plan_sheet_pages`, `plan_sheet_suggestions`, and `sheet_id` on audit events. Suggestions never silently set SoR. Uniqueness scoped to `DrawingRevision`. Page ≠ Sheet preserved; source documents and pages immutable. |
| Prompt template used | Approved custom Cursor implementation prompt for M009 (FG-004 approved) |
| Approved Cursor prompt summary | Anti-drift preflight; verify Alembic head; implement authorized models, migration `b8d9f0a1c2e3`, service layer, office UI, tests, and documentation; run test suite; commit and push. |
| Files expected to change | `app/plan_intelligence/*`, `migrations/versions/*`, `tests/test_sheet_intelligence.py`, `app/templates/plan_intelligence/*`, governance/module docs |
| Files prohibited from changing | Estimating, proposals, change orders, CRM, pricing calculation, auth, field/mobile |
| Implementation result | M009 fully implemented. Migration `b8d9f0a1c2e3` applied cleanly. All 15 focused tests and 121 total suite tests pass. |
| Tests | `pytest tests/test_sheet_intelligence.py -q` (15 passed); `pytest -q` (121 passed) |
| Project-state-report update | Yes |
| Milestone entry update | Milestone 009 appended |
| Constitutional issue raised | None |
| Unresolved issues | None for M009 |
| Next approved step | Prepare Feature Gate for M010 Scale Calibration / Measurement Tools |
| Next approved prompt | M010 Feature Gate |
| Commit hash | `5dc4b09` |

### 2026-08-28 — Approve M009 Sheet Feature Gate (FG-004)

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Governance only: accept ADR-017/018 if consistent; create/approve FG-004 for M009. No product code. |
| Business decision | M009 = Sheet classification / human metadata review. FG-004 approved. Implementation awaits a dedicated Cursor prompt. |
| Architectural decision | ADR-017/018 **Accepted** without redesign. Page ≠ Sheet, human SoR, Plan Intelligence ownership, Project hub. ADR-014 document remains Proposed. |
| Prompt template used | Approved custom Cursor prompt (documentation-only) |
| Approved Cursor prompt summary | Preflight; existing-before-new; accept 017/018 or STOP; write FG-004; integrate docs; validate; commit; push; stop. Do not begin M009 code. |
| Files expected to change | Feature Gate, ADRs 017/018 status, indexes, state/handoff/log/roadmap/module docs |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, models/schemas |
| Implementation result | FG-004 created and approved. ADR-017/018 Accepted. M009 code not begun. |
| Tests | Docs-only: `git diff --check`; link check. No pytest invented. |
| Project-state-report update | Yes |
| Milestone entry update | FG-004 architecture/authorization record appended; M008 not rewritten |
| Constitutional issue raised | None |
| Unresolved issues | ADR-014 formal status; SQLite uniqueness mechanism (either allowed); M009 implementation prompt |
| Next approved step | Dedicated **M009 implementation Cursor prompt** citing FG-004 |
| Next approved prompt | M009 implementation (not this Gate) |
| Commit hash | This adoption commit (see stopping report SHA) |

### 2026-08-28 — CAR-001 CalibAi architecture & product vision adoption

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Documentation/governance only: adopt CAR-001 approved CalibAi vision and architecture. No product code. Do not begin M009. |
| Business decision | CalibAi vision (PLAN→PRICE→CONTRACT→BUILD→MONITOR→LEARN); office+field complementary; V1 direction; sequence recorded as roadmap only. Repository not renamed. |
| Architectural decision | ADR-019/020/022/023/024 **Accepted** (direction). ADR-021 and ADR-025 **Proposed**. Project remains hub. BUILD ≠ Change Orders. API-before-native. Field evidence original vs derived. LEARN cannot mutate pricing/cost library. M009 remains coded Sheets; CAR-001 is not M009. |
| Prompt template used | Approved custom Cursor prompt (documentation-only; equivalent constraints to cursor-documentation-template) |
| Approved Cursor prompt summary | Preflight; existing-before-new; create CAR-001 record; update vision; ADRs; V1/sequence/pricing record; minimum drift fixes; validate; commit; push; stop. |
| Files expected to change | Docs, ADRs, modules, roadmap, state/handoff/log only |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, models/schemas, product rename |
| Implementation result | CAR-001 recorded. Vision updated. ADRs 019–025 created. M009 code not begun. |
| Tests | Docs-only: `git diff --check`; link check; no pytest invented |
| Project-state-report update | Yes |
| Milestone entry update | CAR-001 architecture record appended; M008/M009 numbers not rewritten |
| Constitutional issue raised | None. Constitution not amended. |
| Unresolved issues | ADR-021, ADR-025, ADR-017/018; M009 Feature Gate |
| Next approved step | Stop. Next coded work is Feature-Gated **M009** when Joel authorizes it. |
| Next approved prompt | None |
| Commit hash | This adoption commit (see stopping report SHA) |

### 2026-08-28 — Adopt CalibAi Continuity & Anti-Drift Protocol

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Governance-only: formally adopt the approved CalibAi Continuity & Anti-Drift Protocol before any product/architecture reconciliation |
| Business decision | Joel approved adoption of the protocol; AI memory is never authoritative project state; repository remains the system of record |
| Architectural decision | None. Protocol supplements Constitution Article 1 and existing context-drift stop; Constitution not amended. Product/repository not renamed. |
| Prompt template used | Approved custom Cursor prompt (documentation-only constraints equivalent to [cursor-documentation-template.md](prompts/cursor-documentation-template.md)) |
| Approved Cursor prompt summary | Reconstruct state; existing-before-new search; create `docs/governance/continuity-and-anti-drift.md`; minimum governance integration; validate; commit; push if permitted; stop. No product code, schema, migrations, or M009. |
| Files expected to change | New protocol doc; minimum references in AGENTS.md, docs/README.md, platform-governance, development-workflow, current-state, project-state-report, chat-workflow-log, aiRIA-lessons-adopted, session-handoff |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, models/schemas, product features; Constitution; product/repository rename |
| Implementation result | Protocol created as APPROVED/GOVERNING. Existing drift rules preserved. Constitution not amended. M009 not begun. |
| Tests | Docs-only: `git diff --check`; link resolution; confirm no application/schema/migration changes. No pytest invented. Exact results in stopping report. |
| Project-state-report update | Yes — protocol adoption recorded |
| Milestone entry update | No — not a product milestone |
| Constitutional issue raised | None. Protocol supplements Article 1; Constitution left unchanged. |
| Unresolved issues | Product/architecture reconciliation not started (separate authorization required) |
| Next approved step | Stop. Do not begin M009. Next: Joel-authorized CalibAi product/architecture reconciliation (separate prompt). |
| Next approved prompt | None |
| Commit hash | This adoption commit (see stopping report SHA) |

### 2026-08-26 — Governance closure after commit 0fdf0d4

| Field | Content |
|-------|---------|
| Date | 2026-08-26 |
| Branch | `main` (tip at or after `ee100ac` = `origin/main`; confirm with `git rev-parse`) |
| Objective | Documentation-only state correction: clear stale transient journal facts after August reconciliation was committed and pushed |
| Business decision | No new product requirements; correct current pins only |
| Architectural decision | Unchanged |
| Approved Cursor prompt summary | Docs-only closure; commit/push allowed if validation passes and only governed docs change |
| Files expected to change | State/journal docs (`current-state`, `session-handoff`, `project-state-report`, `platform-roadmap`, `chat-workflow-log`) |
| Files prohibited from changing | app/, migrations/, tests/, dependencies; architecture/pricing/legal/UAT substance |
| Implementation result | Transient pins cleared; August reconciliation recorded as `0fdf0d4`; state closure tip `ee100ac` (plus any pin-alignment follow-up on `main`) |
| Next approved step | ADR-017/018; Feature Gate before coded Sheets (**not started**) |
| Commit hash | `ee100ac` (initial closure); confirm tip with `git rev-parse` |

### 2026-08-25 — Subsequent commit/push of August governance reconciliation

| Field | Content |
|-------|---------|
| Date | 2026-08-25 |
| Branch | `main` |
| Objective | Record actual outcome after Joel-directed commit-and-push (separate from the original no-commit reconciliation prompt) |
| Historical note | The original August 25 reconciliation prompt instructed **documentation only** and **no commit/push at that stage**. Commit/push occurred **subsequently**, not under that original prompt. |
| Outcome | Local checkpoint `ed36838` pushed; governance reconciliation committed as `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* (18 documentation files); `HEAD` = `origin/main` = `0fdf0d4`; working tree clean after that push |
| Files prohibited from changing | app/, migrations/, tests/ (unchanged) |
| Commit hash | `0fdf0d4` |

### 2026-08-25 — Governance reconciliation (authoritative record, document package, pricing, legal gate)

| Field | Content |
|-------|---------|
| Date | 2026-08-25 |
| Branch | At work time: `main` @ local `ed36838`; `origin/main` then `ee9b4b2` |
| Objective | Documentation-only governance reconciliation; preserve post-M008 state sync; record August 25 product/governance requirements |
| Business decision | One authoritative estimate record; four core outputs; pricing reference rule ($65/hr, 15% gross margin); no silent placeholders; 3415 Roger Stevens UAT reference case |
| Architectural decision | QuickBooks pipeline boundary (no API); Legal Content Gate for Ontario contract/warranty; context drift mandatory stop; PRESERVE → SEARCH → VERIFY → EXECUTE |
| Prompt template used | August 25, 2026 governance reconciliation prompt (documentation-only) |
| Approved Cursor prompt summary | Docs only; preserve six pre-existing state-sync modifications; no app/migrations/tests/deps; **original prompt forbade commit/push at that stage** |
| Files expected to change | `docs/` governance and state files only |
| Files prohibited from changing | app/, migrations/, tests/, dependencies |
| Implementation result | Extended state docs; new pricing policy, document package, QuickBooks architecture, legal template governance, UAT reference case (working tree dirty until subsequent commit) |
| Tests | Not run (documentation-only by design) |
| Project-state-report update | Yes |
| Milestone entry update | No new coded milestone |
| Subsequent outcome | Commit/push was **not** authorized by this prompt; occurred later under a separate Joel-directed commit-and-push → `0fdf0d4` (see entry above) |
| Next approved step | Joel review; then separate commit authorization; ADR-017/018; Feature Gate before coded Sheets |
| Commit hash | None under this prompt (forbade commit); subsequent `0fdf0d4` |

### 2026-07-25 — Repository state sync after M005–M008 merge to main

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `ee9b4b2` (then tip of `origin/main`) |
| Objective | Synchronize state/roadmap/milestone docs with merged Git reality |
| Business decision | Record M005–M008 as merged; do not start coded Sheets |
| Architectural decision | Unchanged — Sheet Intelligence remains architecture/readiness only |
| Files expected to change | `docs/current-state.md`, `project-state-report.md`, `session-handoff.md`, `platform-roadmap.md`, `milestones.md`, `chat-workflow-log.md` |
| Files prohibited from changing | app/, migrations/, tests/ |
| Implementation result | Docs updated to reflect M005–M008 merged on `origin/main`; preserved in local commit `ed36838` |
| Next approved step | Joel ADR-017/018 review; Feature Gate before sheet implementation |
| Commit hash | `ed36838` (local checkpoint; subsequently pushed with `0fdf0d4`) |

### 2026-07-25 — Milestone 008 Sheet Intelligence architecture

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `milestone-008-sheet-intelligence` |
| Objective | Architecture for Sheets from indexed Pages; register docs in indexes/state; **no code** |
| Business decision | Design Sheet Intelligence before any sheet tables/UI |
| Architectural decision | ADR-017 suggestion accept/reject/edit; ADR-018 uniqueness/supersession; first coded sheets require a later Feature Gate; scale/AI POC later |
| Files expected to change | docs only (ADR-017/018, sheet-intelligence.md, M008 readiness, indexes, roadmap, state) |
| Files prohibited from changing | app/, migrations/, tests/ |
| Implementation result | Architecture + readiness docs integrated; Sheets remain unimplemented |
| Tests | Docs validation only (`git diff --check`, link check) |
| Project-state-report update | Yes |
| Milestone entry update | Yes — M008 |
| Next approved step | Merged to `main` via PR #6 |
| Commit hash | `8c74e31` (merged in `ee9b4b2`) |

### 2026-07-25 — Milestone 007 Document Indexing

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `milestone-007-document-indexing` |
| Objective | Implement Document Indexing: pages, deterministic/embedded-text extraction, provenance, archive, audit, relational search |
| Business decision | First coded DI phase after FG-003 CONDITIONAL PASS conditions |
| Architectural decision | Page ≠ Sheet; immutable raw payloads; archive-over-delete; relational search (ADR-016 Stage 1); ADR-015 provenance |
| Files expected to change | `app/plan_intelligence/**`, models, templates, migration `a7c8e9f0b1d2`, `tests/test_plan_indexing.py`, M007 docs/ADRs |
| Files prohibited from changing | Estimating commercial writes; Sheet entity implementation; OCR/CAD/AI take-off |
| Implementation result | Indexing models/services/UI/migration/tests; Estimating untouched |
| Tests | Plan indexing + upload tests; full suite **106 passed** |
| Next approved step | Merged to `main` via PR #5 |
| Commit hash | `cbefe7a` (merged in `eb00123`) |

### 2026-07-25 — Milestone 006 Document Intelligence refinement (CONDITIONAL PASS)

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `milestone-005-plan-intelligence-phase-a` |
| Objective | Expand M006 to full prompt: CONDITIONAL PASS, Page/Sheet edge cases, processing provenance, staged search, revised M007–M010 |
| Business decision | Do not authorize DI code on FG-003 alone; require explicit conditions |
| Architectural decision | FG-003 **CONDITIONAL PASS**; ADR-015 provenance; ADR-016 staged search; M007=indexing/extraction; sheet review / scale / AI POC = later Feature-Gated milestones |
| Prompt template used | Milestone 006 Document Intelligence Architecture and Feature Gate (expanded) |
| Files expected to change | docs only |
| Files prohibited from changing | app/, migrations/, tests/, dependency files |
| Implementation result | Docs refined; no code |
| Tests | Docs validation only (status, diff --check, link check) |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Joel acceptance of conditions + ADR-013–016 |
| Next approved step | M007 Feature Gate when conditions satisfied |
| Next approved prompt | None |
| Commit hash | **None** (prompt forbids commits/pushes) |

### 2026-07-25 — Milestone 006 Document Intelligence architecture

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `milestone-005-plan-intelligence-phase-a` @ `098647c` |
| Objective | Document Intelligence architecture + FG-003; no code |
| Business decision | Insert DI layer between Phase A upload and take-off |
| Architectural decision | FG-003 **PASS**; ADR-013 (DI inside Plan Intelligence); ADR-014 (sheet ≠ page); M005 supports additive DI |
| Prompt template used | Milestone 006 architecture & Feature Gate prompt |
| Approved Cursor prompt summary | Docs only; evaluate M005 compatibility; FG-003; ADRs only if required; no commits |
| Files expected to change | docs only (FG, ADR, architecture, roadmap, milestones, state) |
| Files prohibited from changing | app/, migrations/, tests/ |
| Implementation result | FG-003 PASS; document-intelligence.md; M006 readiness report; ADR-013/014; governance updates |
| Tests | Not run (docs-only milestone by design) |
| Project-state-report update | Yes |
| Milestone entry update | Yes — M006 |
| Constitutional issue raised | None |
| Unresolved issues | Joel acceptance of ADR-013/014; M007 implementation authorization |
| Next approved step | Joel review/commit docs; Feature Gate M007 when ready |
| Next approved prompt | None |
| Commit hash | Pending |

### 2026-07-25 — Milestone 005 FG-002 + Phase A PDF upload

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `c59ec01` (uncommitted M004+M005) |
| Objective | ADR-012; FG-002 pass; Phase A PDF upload/storage only |
| Business decision | Authorize Phase A foundation; defer revision UI |
| Architectural decision | ADR-012 Proposed (drawing set/revision ownership); flat `plan_documents` interim |
| Prompt template used | Milestone 005 implementation prompt |
| Approved Cursor prompt summary | FG-002 + Phase A; no OCR/CAD/AI/estimate insert; no commits |
| Files expected to change | plan_intelligence package; templates; migration; tests; governance docs |
| Files prohibited from changing | Estimating redesign; Proposals immutability; unrelated modules |
| Implementation result | FG-002 Approved; ADR-012 docs; Phase A routes/services/storage/migration/tests |
| Tests | `pytest tests/test_plan_upload.py` — 8 passed; full suite `./venv/bin/python -m pytest -q` → **97 passed**, 68 warnings |
| Project-state-report update | Yes |
| Milestone entry update | Yes — M005 |
| Constitutional issue raised | None |
| Unresolved issues | Commit pending; ADR-012 acceptance; Phase B gate |
| Next approved step | Joel review/commit; Feature Gate Phase B when ready |
| Next approved prompt | None |
| Commit hash | Pending |

### 2026-07-25 — Milestone 004 Plan Intelligence architecture

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `c59ec01` |
| Objective | Architecture/docs for Plan Intelligence pipeline, model, review, traceability, estimate mapping, ADRs, POC — no code |
| Business decision | Plan Intelligence is the next strategic differentiator (plans → take-off → estimate → proposal) |
| Architectural decision | PDF-first; human approval mandatory; citations first-class; confidence thresholds via ADR-011; feed estimate builder without redesign |
| Prompt template used | Documentation / architecture |
| Approved Cursor prompt summary | Docs only; no app/migrations/tests/deps/commits |
| Files expected to change | `docs/modules/plan-intelligence.md`, `docs/architecture/**`, ADRs, roadmap/milestones/state |
| Files prohibited from changing | `app/**`, `migrations/**`, `tests/**`, `requirements.txt` |
| Implementation result | Architecture expanded; module rewritten; readiness report; ADR-011 added; ADR-005/006 updated |
| Tests | Not re-run (docs-only). Last verified: 89 passed, 53 warnings |
| Project-state-report update | Yes |
| Milestone entry update | Yes — Milestone 004 |
| Constitutional issue raised | Reinforced no silent AI commercial insert |
| Unresolved issues | ADR acceptance; Phase A Feature Gate; numeric confidence values |
| Next approved step | Joel review; commit M004 docs when directed |
| Next approved prompt | None until Phase A Feature Gate |
| Commit hash | Pending |

### 2026-07-25 — Milestone 003 Accepted Proposal Immutability

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` |
| Objective | Block all mutations when proposal.status == Accepted; preserve view/preview/PDF |
| Business decision | Accepted proposals never reopen/silently rewrite; void/supersede/revision deferred |
| Architectural decision | Central `ensure_proposal_mutable`; recalculate guarded except create-time snapshot flag |
| Prompt template used | Feature (Milestone 003 prompt) |
| Approved Cursor prompt summary | Service guard + UI + tests; no migration; no acceptance workflow; no commit |
| Files expected to change | `app/services/proposals.py`, routes/templates proposals, tests, minimal docs |
| Files prohibited from changing | migrations, estimate builder, unrelated modules |
| Implementation result | Guard implemented; UI read-only for Accepted; tests added |
| Tests | `./venv/bin/python -m pytest -q` → **89 passed**, 53 warnings; focused immutability file 11 passed |
| Project-state-report update | Milestone 003 recorded; full state refresh at commit |
| Milestone entry update | Yes — Milestone 003 |
| Constitutional issue raised | Closed for Accepted silent rewrite (Article 5 / Rule 3) |
| Unresolved issues | Void/supersede workflow not built |
| Next approved step | Joel review; commit when directed |
| Next approved prompt | None until Joel Feature-Gates next milestone |
| Commit hash | Pending |

### 2026-07-25 — Strategic architecture: Plan Intelligence + Supplier pillars

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `71e2754` (+ uncommitted M002 docs) |
| Objective | Update strategic roadmap pillars; create Plan Intelligence and Supplier architecture docs; Phases A–G; narrow POC; ADR-005–010 — documentation only |
| Business decision | Long-term differentiator is plan→take-off→estimate→supplier pricing→proposal/PO with human review and citations; PDF-first |
| Architectural decision | ADR-005–010 Proposed; Plan Intelligence and Supplier Catalogue as Future modules; no claim of existing integrations |
| Prompt template used | Documentation / architecture |
| Approved Cursor prompt summary | Docs only; no app/migrations/deps/commits; distinguish current vs future |
| Files expected to change | `docs/platform-roadmap.md`, `docs/platform-vision.md`, `docs/architecture/**`, `docs/adr/ADR-005`–`010`, module stubs, indexes, milestones/state |
| Files prohibited from changing | `app/**`, `migrations/**`, tests, requirements |
| Implementation result | Architecture docs + ADRs + roadmap pillars created; no application code changed |
| Tests | Full suite not re-run; last verified 78 passed, 43 warnings |
| Project-state-report update | Yes |
| Milestone entry update | Milestone 002 deliverables extended |
| Constitutional issue raised | Reinforced no silent AI commercial overwrite (Articles 5–6) |
| Unresolved issues | Joel ADR acceptance; M003 vs Phase A sequencing |
| Next approved step | Joel review; commit docs when directed |
| Next approved prompt | None for implementation |
| Commit hash | Pending |

### 2026-07-25 — Milestone 002 Product Architecture Review (Proposals FG + ADRs)

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `71e2754` (start) |
| Objective | Feature Gate FG-001 for Proposals; draft ADR-001–004; recommend next implementation milestone — documentation only |
| Business decision | Treat existing Proposal Builder as complete foundation; prioritize Accepted immutability before acceptance workflow / project creation |
| Architectural decision | ADRs Proposed: snapshot ownership (001); Accepted immutability (002); defer CRM FKs (003); acceptance workflow after immutability (004) |
| Prompt template used | Documentation / architecture review (aligned with cursor-documentation-template / cursor-review-template) |
| Approved Cursor prompt summary | Create FG + ADRs; update module/roadmap/milestones/state docs; no app/schema/migration/UI changes; no commit |
| Files expected to change | `docs/feature-gates/**`, `docs/adr/ADR-001`–`004`, proposals module, indexes, milestones, roadmap, state/handoff/log |
| Files prohibited from changing | `app/**`, `migrations/**`, tests, models, routes, templates, services |
| Implementation result | FG-001 + ADR-001–004 created; cross-links updated; no application code changed |
| Tests | Full suite **not re-run**. Last verified remains **78 passed**, 43 warnings |
| Project-state-report update | Yes |
| Milestone entry update | Yes — Milestone 002 recorded (pending doc commit) |
| Constitutional issue raised | Accepted proposals currently editable — Article 5 / Rule 3 gap (address in Milestone 003) |
| Unresolved issues | Joel approval of ADRs; Milestone 003 prompt not yet written |
| Next approved step | Joel review; commit M002 docs when directed |
| Next approved prompt | **None** — Milestone 003 prompt pending Joel ADR acceptance |
| Commit hash | Pending |

### 2026-07-25 — Record governance baseline milestone (post-commit)

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `29d1ba9` |
| Objective | Update governance records to mark Milestone 001 Completed and refresh project state before push — documentation only |
| Business decision | Memorialise commit `29d1ba9` as completed Governance Baseline before remote publish |
| Architectural decision | None (record-keeping only; no policy change) |
| Prompt template used | Documentation / milestone-record update |
| Approved Cursor prompt summary | Update milestones, project-state-report, current-state, session-handoff, chat-workflow-log, platform-roadmap only; do not commit or push |
| Files expected to change | Listed governance docs only |
| Files prohibited from changing | `app/**`, `migrations/**`, tests, models, routes, templates, services, repositories |
| Implementation result | Milestone 001 marked Completed; roadmap governance sprint moved to Completed; next milestone set to Product Architecture Review |
| Tests | Full suite **not re-run** (docs-only). Last verified remains **78 passed**, 43 warnings |
| Project-state-report update | Yes |
| Milestone entry update | Yes — Milestone 001 → Completed @ `29d1ba9` |
| Constitutional issue raised | None |
| Unresolved issues | Not yet pushed to `origin/main`; live Alembic current still To be verified |
| Next approved step | Push `29d1ba9`; then Product Architecture Review and Feature-Gate one product milestone |
| Next approved prompt | **Not yet created** — pending Product Architecture Review |
| Commit hash | Record update itself uncommitted; baseline commit referenced: `29d1ba9` |

### 2026-07-25 — Governance Baseline Completion (Constitution, milestones, prompts, state report)

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` (base `7b8d5ca`; committed as `29d1ba9`) |
| Objective | Complete governance foundation: Platform Constitution, Milestone History, Prompt Library, Project State Report, and cross-references — documentation only |
| Business decision | Further reduce chat-history dependence; make Joel → ChatGPT → Cursor cycles recoverable and repeatable |
| Architectural decision | Constitution is highest-order law; milestones append-only; project-state-report is milestone-level state; prompts are templates not scope licenses |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | Create constitution, milestones, prompts/*, project-state-report; update listed cross-ref docs and Cursor rules; no application/migration/test changes |
| Files expected to change | Governance/documentation paths only |
| Files prohibited from changing | `app/**`, `migrations/**`, models, routes, templates, services, repositories, tests, business logic |
| Implementation result | Governance baseline delivered and committed: **39** files, docs/rules/AGENTS/README only; **no** app/migration/test changes |
| Tests / validation | `./venv/bin/python -m pytest -q` → **78 passed**, 43 warnings; `git diff --check` clean; **171** internal links checked, **0** broken |
| Project-state-report update | Yes |
| Milestone entry update | Yes — later marked Completed at `29d1ba9` |
| Constitutional issue raised | None (established Constitution v1.0) |
| Unresolved issues | Live alembic `current` To be verified; push to origin pending |
| Next approved step | Record milestone completion in docs; then `git push origin main` when Joel directs |
| Next approved prompt | **Not yet created** — pending Product Architecture Review |
| Commit hash | `29d1ba9` — *Complete Estimator governance baseline and prompt library* |

### 2026-07-25 — Platform Governance Foundation

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `7b8d5ca` (start) |
| Objective | Establish documentation/governance foundation only; no application behaviour change |
| Business decision | Adopt AiRIA-derived operating discipline for The Estimator (docs as system of record; Feature Gate; handoffs) |
| Architectural decision | Document current Flask modular architecture as-is; distinguish Current / Intended / Future; encode Rules 1–12 |
| Prompt template used | N/A (predated prompt library) |
| Approved Cursor prompt summary | Create `docs/**`, `.cursor/rules/**`, `AGENTS.md`; inspect repo; do not touch models/migrations/routes/business logic except README links if needed |
| Files expected to change | `docs/**`, `.cursor/rules/**`, `AGENTS.md`, root `README.md` (pointer) |
| Files prohibited from changing | Application code under `app/` (except none intended), `migrations/versions/**`, schemas, tests behaviour |
| Implementation result | Governance document tree created; module docs grounded in code; Cursor rules added; later included in `29d1ba9` |
| Tests | `./venv/bin/python -m pytest -q` → **78 passed**, 43 warnings (2026-07-25) |
| Project-state-report update | Added in follow-on baseline completion task |
| Milestone entry update | Recorded as Milestone 001 |
| Constitutional issue raised | N/A at time of sprint |
| Unresolved issues | Live alembic `current` vs heads needs Flask-Migrate verification; authz depth unverified |
| Next approved step | Completed via baseline commit `29d1ba9` |
| Next approved prompt | Superseded by Product Architecture Review (not yet created) |
| Commit hash | `29d1ba9` (governance baseline commit includes this work) |
