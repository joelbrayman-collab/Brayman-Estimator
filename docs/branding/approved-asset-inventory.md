# Approved Branding Asset Inventory

| Attribute | Value |
|-----------|--------|
| Status | Current inventory (technical cleanup, 18 Oct 2026) |
| Enforced by | `tests/test_branding_asset_integrity.py` |
| Rule | Approved images are never regenerated, recoloured, cropped or redesigned. A replacement must be approved by Joel and recorded here before the file changes. |

Checksums are SHA-256 of the file in the repository. "Source verified" means the bytes were compared on 18 Oct 2026 with the approved source on the office Mac.

## Cal — approved assistant identity

| File | SHA-256 | Source verified 18 Oct 2026 |
|---|---|---|
| `app/static/branding/Cal_Assistant_Approved_Identity_2026-10-17.png` (frozen master, 1281 × 1227) | `d8857f1bfef06c709390e8eaedfe437aea49983236c79843ee7845d561617e87` | Matches `~/Downloads/Cal_Assistant_Approved_Identity_2026-10-17.png` |
| `app/static/img/cal-assistant/cal-64.png` (derivative, 64 × 61) | `0b10a30a284877f117fd933f8126cf68155d89591f90117b6db4b2043f92ef3d` | Matches the record in [cal-assistant-approved-identity-2026-10-17.md](cal-assistant-approved-identity-2026-10-17.md); served bytes checked live by the post-release check |
| `app/static/img/cal-assistant/cal-128.png` (derivative, 128 × 123) | `b524454d8d3defe55d7b24728fe41ed45c5ab3121d7a5f1a63ef8e94505ad4bf` | Matches the same record |

## CalibraytAI logos

Source authority: `CalibraytAI_090926_Final.zip` (SHA-256 `2328333b67a3cece1e0e251276d96bbcf83b9589f6dfe55440be11819e6b8cde`). On 18 Oct 2026 the package is at `~/Desktop/CalibAi Historical Estimates/CalibraytAI_090926_Final.zip` (and the FP70 copy of that folder), not loose on the Desktop as [../governance/product-identity.md](../governance/product-identity.md) says.

| File | Used for | SHA-256 | Source verified 18 Oct 2026 |
|---|---|---|---|
| `app/static/branding/calibraytai-logo-v1-dark.png` | Office sidebar | `86a4d964cb31aa4e4fbd6360d29f77ce82dc5b8d9d5df7319b3f962f427661de` | Equals zip member `V1 LOGO/CalibraytAI.png` |
| `docs/branding/calibraytai-opening-v1/storyboard/approved-logo-v1-dark-reference.png` | Reference copy | `86a4d964cb31aa4e4fbd6360d29f77ce82dc5b8d9d5df7319b3f962f427661de` | Same bytes as above |
| `app/static/branding/calibraytai-logo-v2.png` | Field, supplier portal, signing ceremony, walkthrough, decision-tool pages, business-owner PDF | `b719bdd2fe7814d49d1a4065c4d6b1915f8e3cd6696f711c08e8d49b3fa53aea` | Equals zip member `V2 LOGO/CalibraytAI.png` |

## Installable-app icons (15 Oct 2026, from the approved gold symbol on #000510)

No checksum was recorded when these were made; the values below are first recorded on 18 Oct 2026 from the files that are live.

| File | Used by | SHA-256 |
|---|---|---|
| `app/static/branding/calibraytai-app-icon-180.png` | `apple-touch-icon`, manifest, Field service worker | `4fe82fe5a6f1cce3aecd2cef8ce2c151a291ceaf1928bd562f31dbe7db153417` |
| `app/static/branding/calibraytai-app-icon-192.png` | manifest | `6a97220ea2a8bd4f9d6d8733b0dbb5deb24ba437c94d02d49f76d51729becbb8` |
| `app/static/branding/calibraytai-app-icon-512.png` | manifest | `d98dd1f6d279c13a850de726e5c3043b2a56a9424a596629c2075e039b68794e` |
| `app/static/branding/calibraytai-app-icon-maskable-512.png` | manifest | `2bedbfa356e82d89013d863e69e6ce7e37c19316802c302c177e89ea8b54fbb1` |
| `app/static/branding/calibraytai-app-icon-32.png` | **Not referenced by any page** (storybook list only) — see below | `a1a78d21023044294fb1d21566a7d921ab5acfa7b090dbb94afaf48a04477c4a` |

## Organization brand

| File | Used for | SHA-256 |
|---|---|---|
| `app/static/branding/brayman-construction-logo.png` | Brayman Construction brand profile: proposals, drawings, supplier estimates, project-controls PDFs, sign-in and page headers | `948f96e08827f18d77b47538f65c8b98b45caaf9c981adccba0189976948efe9` (first recorded 18 Oct 2026) |

## Orphaned or duplicate assets (recorded, not deleted)

- `calibraytai-app-icon-32.png` has no reference in any template, script, manifest or service worker. It is kept (an approved derivative); adding it as the browser favicon or retiring it is Joel's decision.
- `approved-logo-v1-dark-reference.png` is an intentional duplicate of the sidebar logo (the reference the tests compare with).
- Historical record: [../current-state.md](../current-state.md) still lists `calibraytai-logo-office.png` (SHA `16d3b5b1…`) as the live office logo in its 27 Aug section. That file was removed on 15 Oct 2026 when `calibraytai-logo-v1-dark.png` replaced it; the old line is history, not the current state.
