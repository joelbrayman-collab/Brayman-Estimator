# CalibraytAI source of truth — what lives where (28 Oct 2026)

| Attribute | Value |
|---|---|
| Status | **Governing.** Written in the turnover corrective pass after the independent audit of 28 Oct 2026. |
| Read with | [turnover-2026-10-28.md](turnover-2026-10-28.md) (the turnover record and the audit's corrections) |
| Rule | `main` is the canonical **application** source. A few current assets are deliberately kept on their own branches (below). Those branches are deployment or publication sources: **never delete them**; each is also protected by a preservation tag. |

## 1. The application (office, Field, supplier portal, Training code)

- **Canonical source:** `main`. Every release candidate is built from `main` or from a branch that merges into it.
- **Live:** Render service `Calibryatai` (`srv-dar95mh42hec73df4rug`), branch `main`, auto-deploy **off**. Deployed only through the Mac release gate and Joel's explicit authorization. What is running is recorded in [../session-handoff.md](../session-handoff.md) §0.
- **Approval-gated work outside `main`:** FG-041 supplier native signing (§6). Nothing else.

## 2. Public website (calibraytai.com)

| Branch | What it is | Editable? | `main` depends on it? | Update how |
|---|---|---|---|---|
| `website/source` | **Authoritative editable source** of the public website (a separate Next.js / vinext "Sites" project with its own toolchain, unrelated history; 199 files, ~25 MB, mostly images). Tip `5f701cda` (22 Oct 2026: approved Useful Calculators icon). | **Yes — the only editable source.** | No (documented here). | Edit on this branch (or a branch from it), build with its own `npm run build`, commit the build output to a static-build branch. |
| `website/calibraytai-static-v1sync-2026-10-22` | **Generated static build** of `website/source` for calibraytai.com (V1 platform sync). Tip `b6deb1b5` (homepage Useful Calculators icon, from source `5f701cd`); `5af11f1` is the V1 sync build the deploy script defaults to. | No — generated output. | **Yes**: `tools/hosting/deploy_calibrayt_website.sh` fetches it and checks out a pinned commit (default `5af11f1`). | Rebuild from `website/source`, commit here, then run the deploy script with the new commit. |
| `website/calibrayt-static-2026-10-22` | **Generated static build**, website v31 for calibrayt.com (`18904f1b`). Historical derivative, kept as a rollback build. | No. | **Yes**: the deploy script fetches it so its commits can be pinned. | Not updated. |

Which build is on the server now is **not recorded** (the copy excludes `.git`). To confirm, read-only, in WHM Terminal:
`sha256sum "$(whmapi1 domainuserdata domain=calibraytai.com | awk '/documentroot:/{print $2; exit}')/index.html"` →
`5af11f1` = `458b5df805e28cc9…`, `b6deb1b5` = `8018f2324f17eaf3…`, `18904f1b` = `79917cc2867a0c8a…` (first 16 hex of the SHA-256 of `index.html`).

The editable website source is deliberately **not** imported into `main`: it is a different application with its own build system and history; its generated builds would duplicate it. It is kept, protected and named here instead.

## 3. Storybooks (calibraytai.com/storybook/)

| Location | What it is |
|---|---|
| `main`: `docs/storybook/supplier-editions/` | **Editable source** (generators `contractor.py`, `supplier_connection.py`, `bmr.py`, `kbc.py`, brand files with `SHA256SUMS`). Up to date to 23 Oct 2026 (`23de08c5`). |
| Branch `storybooks/site` | **Generated publication output** (four built books) plus its installer `install_storybooks.sh` (run as root in WHM Terminal). Tip `4540c609` (24 Oct 2026: all four at plain open addresses). The 24 Oct change is to the built pages' robots meta and the installer only. `docs/operations/url-register.md` names this branch. **Never delete.** |
| `main`: `docs/storybook/editions/2026-10-18-refined/` | Refined 18 Oct contractor storybook archive (HTML, PDF, editable source, Vercel package, MANIFEST, README). **Not published (Vercel 403).** Recovered into `main` on 28 Oct 2026. |

## 4. AiRIA publication packs (hosted on HostPapa; AiRIA source lives in Discovery-Search)

| Branch | What it is |
|---|---|
| `publish/airia-website-595754a` | Publication package: unchanged copy of Discovery-Search `595754a` `site/`. `tools/hosting/publish_airia_website.sh` (in `main`) pins a commit on it. **Never delete.** |
| `publish/airia-storybook-v15` | Publication package: AiRIA Storybook v15 (Discovery-Search `58c035a`) and its publish script. **Never delete.** |

The authoritative AiRIA source is the Discovery-Search repository; these branches are the exact packages that were published.

## 5. Training & Acceptance Centre

- **Real site:** https://training.calibraytai.com on the HostPapa VPS, service `calibrayt-training`, code `/opt/calibrayt/app`, own database. Installed and updated by `tools/hosting/install_training_centre.sh [commit]` (default `f3a01e1`, v1rel8), which fetches `v1/rel8-2026-10-23`, `main` and `v1/training-centre-2026-10-21`. Those two branches must therefore **not be deleted** while the installer names them. See [training-site.md](training-site.md).
- **Render preview** `calibraytai-training-preview` (`srv-dbce6bjbc2fs73c61akg`): free plan, data wiped on restart, branch `v1/training-centre-2026-10-21`, auto-deploy off, running `5f575c4` (23 Oct). `url-register.md` lists it as "to be suspended in Render". It is not the training site of record. Suspending it needs Joel's decision.
- The commit running on HostPapa is recorded in [../session-handoff.md](../session-handoff.md) §0 once read (read-only: `sudo -u calibrayt git -C /opt/calibrayt/app log -1 --format='%H %ad %s'`).

## 6. Approval-gated current work outside `main`

| Work | Where | Gate |
|---|---|---|
| FG-041 supplier native signing | Original: `signing/supplier-native-signing-on-prodesk` = `recovery/supplier-signing-preserved-2026-10-28` (`c2a3be14`). Reconciled onto current `main`: see the turnover record §"Corrective pass". | Joel's approval of consent wording `CONSENT-SUPPLIER-V1-001` and of its production migration, then the normal release gate. |

## 7. Preservation tags

Annotated tags `preserve/2026-10-28/*` mark the exact commits above (see the turnover record for names and SHAs). Tags and branches are both kept; neither is deleted.

## 8. Confidential documents

Approved masters (Families 01–08 and Family 05) stay outside Git, on the office Mac under `~/Documents/CalibAi/Approved Document Templates/Reusable Master Template Family V1/MASTER DOCX/` (see `docs/testing/test-environment.md`). Tests that need them run on the Mac release gate; anywhere else they report the master as missing, and that counts as **blocked**, not passed.
