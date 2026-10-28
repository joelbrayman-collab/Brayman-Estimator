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
| `app/static/branding/brayman-construction-logo-dark.png` | Brayman Construction logo for dark backgrounds (white lettering, gold mark): navy document headers such as the supplier pricing request | `904667b4d0ea0d50ca69b77d731a9c918f16a6464ae579a0b7f38037a3332c44` (recorded 28 Oct 2026) |

The dark Brayman logo is recovered byte-for-byte from commit `5ebbfdb1` (21 Jul 2026, Joel Brayman, branch `cursor/sidebar-navigation-refinement`, where it was the office sidebar mark); it had never reached `main`. Joel named it the approved dark logo on 28 Oct 2026 ("There are approved logos in repo that say 'dark' and they should be used") for the supplier pricing request. Preservation tag `preserve/2026-10-28/brayman-dark-logo-source`. 1692 × 736 px, transparent background; never recoloured, cropped or redrawn.

## Orphaned or duplicate assets (recorded, not deleted)

- `calibraytai-app-icon-32.png` has no reference in any template, script, manifest or service worker. It is kept (an approved derivative); adding it as the browser favicon or retiring it is Joel's decision.
- `approved-logo-v1-dark-reference.png` is an intentional duplicate of the sidebar logo (the reference the tests compare with).
- Historical record: [../current-state.md](../current-state.md) still lists `calibraytai-logo-office.png` (SHA `16d3b5b1…`) as the live office logo in its 27 Aug section. That file was removed on 15 Oct 2026 when `calibraytai-logo-v1-dark.png` replaced it; the old line is history, not the current state.

## Ask the Tutor identity (23 Oct 2026)

Joel's approved master (a circular badge: graduation cap, tassel and the two lines "Ask the Tutor", transparent outside the circle) recoloured to this platform's own tokens (`--gold #c79a2b`, `--gold-soft #e8d7a8`, `--black #141414`, `--sidebar #17191d` in `app/static/css/app.css`; font IBM Plex Sans is the app font, and the master's lettering is kept, recoloured, not re-set). Shape, proportions, layout and transparency are the master's. Made by `docs/branding/ask_the_tutor/make_ask_the_tutor_icons.py`. Used for: the Training Tutor panel header (`app/templates/training/_tutor.html`).

| File | SHA-256 |
|---|---|
| `app/static/branding/ask_the_tutor/ask-the-tutor-calibraytai-192.png` | `4a5e77d92a1a3498bd7fa0ba61340b3298f2299aac44bac988cfbd8ecbb1ded9` |
| `app/static/branding/ask_the_tutor/ask-the-tutor-calibraytai-48.png` | `6e217b8b328823d6666329e3dff526a0ec733e4f7705f80a1941c0290ae3b957` |
| `app/static/branding/ask_the_tutor/ask-the-tutor-calibraytai-512.png` | `acd8c03d21be6bc2eedc9f5e463e2fdbc5b9f82f63d79beaaa5bcd25a7568776` |
| `app/static/branding/ask_the_tutor/ask-the-tutor-calibraytai-96.png` | `fb898b27be4990521614a0cd9db94ade15237d22470b645a231c4d14893dde74` |
| `app/static/branding/ask_the_tutor/ask-the-tutor-calibraytai.png` | `08cc6c64e889bcd1b42374ec552e2d388ffa9c00a4febc19cd327688bba401f0` |
| `docs/branding/ask_the_tutor/ask-the-tutor-master.png` | `f0e3131f47324316af3fe89de2b46141069b2fab205dcabb80ea441613161582` |

## CaliSIGN — approved identity (28 Oct 2026)

Joel approved the CaliSIGN identity sheet on 28 Oct 2026 ("approved. record, save file and use for the next task"). CaliSIGN is a named CalibraytAI capability ("CaliSIGN by CalibraytAI"), not a separate brand. Record: [calisign/README.md](calisign/README.md). The wordmark in the app is live text (IBM Plex Sans 700, `Cali` navy or white, `SIGN` gold); the PNG identifiers are for email and PDFs only.

| File | Used for | SHA-256 |
|---|---|---|
| `app/static/branding/calisign/calisign-app-icon-128.png` | App icon 128 × 128 | `36bd7c3e0bbeb15b1ae70db3e66cf99b7065cbdd4ab47ebb6b9f8dfdbf6aeb9d` |
| `app/static/branding/calisign/calisign-app-icon-512.png` | App icon (navy tile), large | `3ff48c4a54d9dd779e21b8b0fce7ac8a4d4c2b62c24558075e2d822041bbb526` |
| `app/static/branding/calisign/calisign-icon-32.png` | Menu icon 32 × 32 | `e8b5a95ae40198dfd7f5c9527c458a48e2d3428b87c1d362cfe7cde46a9773ba` |
| `app/static/branding/calisign/calisign-icon-64.png` | Navigation icon 64 × 64 | `f415f00dbf626eaea856db5690ecb2e502f79ebfec76ea3ea7db9851e1306930` |
| `app/static/branding/calisign/calisign-identifier-dark@2x.png` | Primary identifier, dark backgrounds, where live text cannot be used (navy headers) | `017aa9736fe0a2e1c4be5ca3486715307883f0eaad9ce88ad20d632bd8975fe0` |
| `app/static/branding/calisign/calisign-identifier-light@2x.png` | Primary identifier, light backgrounds, where live text cannot be used (email, PDF) | `00df1feac4924f47df0b96a5b22879f54a8be3062e34bec9deea68a694acb1d4` |
| `app/static/branding/calisign/calisign-mark-dark.svg` | The CaliSIGN mark on dark backgrounds (office sidebar, navy headers) | `8f7cc5316454e18eb6595461aa3abbb5349d4315ebe945604ddd162e30455191` |
| `app/static/branding/calisign/calisign-mark.svg` | The CaliSIGN mark on light backgrounds (buttons, signing screens, email, documents) | `13271c260bf54c126d0e7f07c9fdb44e88f8b1e196958138feb309e7aae8e13a` |
| `docs/branding/calisign/calisign-approved-identity-sheet-2026-10-28.png` | The approved identity sheet (reference) | `0395c520f82d412cc9c3ecd73d6dfbe363a0e102640fecce17bea8910c94bc63` |
