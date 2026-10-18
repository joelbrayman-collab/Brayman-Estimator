# Signing Artifact Inventory — September synthetic UAT files

| Attribute | Value |
|-----------|--------|
| Status | Inventory verified 18 Oct 2026; restoration **prepared, not run** (needs Joel's separate authorization) |
| Data | [../../tools/release/september_signing_files.tsv](../../tools/release/september_signing_files.tsv) |
| Script | [../../tools/release/restore_september_signing_files.py](../../tools/release/restore_september_signing_files.py) |

## What is missing and why

The live database holds 14 frozen and 5 executed signing records created 14–15 Sep 2026 during synthetic UAT (consent `CONSENT-SYNTHETIC-UAT-001`). Their files were made on the office Mac. The hosted database was seeded from the Mac on 25 Sep 2026 (database file only), so the files never reached the live disk. Live check 18 Oct: `instance/signing_artifacts` does not exist; `SIGNING_ARTIFACT_ROOT` is not set.

This does not block new signing: the folder is created on the first write and the disk is mounted at `instance/`. Opening one of these 19 records' documents shows "This document is not available." once the security branch is released (before that, the error page). No real customer is affected.

## The 19 files (18 Oct 2026)

| Records | On the Mac (`~/Desktop/Brayman-Estimator/instance/signing_artifacts/ORG-001/`) |
|---|---|
| 8: frozen 1, 3, 9, 11, 13, 14; executed 2, 4 | Local; SHA-256 equals the database record |
| 11: frozen 2 (a contract DOCX), 4, 5, 6, 7, 8, 10, 12; executed 1, 3, 5 | Kept in iCloud only (not downloaded); not yet verified |

Every file name is its own SHA-256, as recorded in the database.

## Restoration plan (exact source and destination)

Source on the Mac: `~/Desktop/Brayman-Estimator/instance/signing_artifacts/<storage_key>`
Staging on the Mac: `~/CalibraytAI-Office/signing-restore/<storage_key>`
Destination on the live instance: `/opt/render/project/src/instance/signing_artifacts/<storage_key>`

1. **Stage (Mac only, no production change).** `/usr/bin/python3 tools/release/restore_september_signing_files.py stage` copies the 8 local files and verifies each against the database. The 11 iCloud files need `--download-from-icloud` (Joel's choice: reading them downloads them; the script sends each back to iCloud afterwards with `brctl evict`). Stage must report `verified=19 of 19`.
2. **Verify live (read-only).** `... verify-live` must report `records_match=True files_present=0`.
3. **Apply (production write, separate authorization).** `... apply --authorization "<Joel's words>"`. It refuses unless steps 1 and 2 hold. Per file: upload to `instance/signing_artifacts/.incoming-<time>/`, check the SHA-256 on the instance, link into place only if nothing is there (never overwrites), check again. No database row changes. It ends with verify-live: `files_present=19 files_matching=19`.
4. **Rollback.** Delete only the 19 files listed in the apply log. Nothing else was changed.

Alternative: leave the 19 synthetic records as they are; nothing else depends on them.
