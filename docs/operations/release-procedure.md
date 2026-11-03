# Release Procedure

| Attribute | Value |
|-----------|--------|
| Status | Current (technical cleanup, 18 Oct 2026; one governed command `release.sh` and immutable gate runs, 3 Nov 2026) |
| Scripts | `tools/release/release.sh` (one command), which runs `release_gate.sh`, `release_migrate.sh` and `postrelease_check.sh` |
| Replaces | the per-release copies in `~/Desktop/Brayman-Estimator/generated/` (`cal1_release.sh`, `v1bd_release.sh`, …), which remain there as history |

Production is changed only after Joel's explicit authorization of the exact commit. Tests passing never deploys anything. Auto-deploy stays off.

## One command (3 Nov 2026)

Joel runs one command in one Terminal window. It fetches nothing but the candidate's own scripts, pushes nothing and
deploys nothing; Claude still pushes and deploys after Joel's authorization.

```bash
curl -fsSL https://raw.githubusercontent.com/joelbrayman-collab/Brayman-Estimator/<candidate>/tools/release/release.sh -o /tmp/release.sh && bash /tmp/release.sh --label <name> --candidate <sha> --branch <branch> --main-base <main sha> --live-base <live sha> --live-deploy <dep-id>
```

Add the same `--migration-to … --new-tables …` (and `--altered-*`, `--filled-columns`, `--populated-tables`) as the gate
for a release with a migration. What it does:

1. Runs the gate (every check below, unchanged) as a new run `<label>-<YYYYMMDD-HHMMSS>` in
   `~/CalibraytAI-Office/release-work/runs/<run ID>/`. The gate's evidence is sealed when it ends (SHA-256
   `MANIFEST.sha256`, read-only). A later run of the same label is a new folder and never truncates or replaces it.
2. At READY_FOR_PUSH prints a block headed **SEND THIS TO CLAUDE** (run ID, commit, bases, database change, evidence
   folder, status file) and waits, checking GitHub `main` and the live instance every 30 s for up to 180 min
   (`--poll-seconds`, `--wait-minutes`), until both are exactly the commit. Joel sends the block with his authorization.
3. With a migration: asks Joel to type `MIGRATE <label> <revision>` in the same window; anything else stops with nothing
   migrated. Then `release_migrate.sh --run <run ID>` (its own backup on the instance and every check, unchanged).
4. Runs `postrelease_check.sh --run <run ID>` and ends with **RELEASED** or **STOPPED** and the reason.

Interrupted (Ctrl-C, window closed, timeout)? Run the same command again: it resumes the run that reached READY_FOR_PUSH
for that candidate, without a second gate run or backup, and does not migrate twice. `--new-run` gates again as a new
run (the earlier one stays). `bash /tmp/release.sh --label <name> --list` lists every run and its outcome. The three
scripts still work on their own; `release_migrate.sh` and `postrelease_check.sh` take `--run <run ID>` or bind to the
run whose READY_FOR_PUSH is the commit on GitHub `main`. Details: `docs/implementation/release-simplification-2026-11-03.md`.

## Release without a database change (the steps release.sh runs)

1. **Candidate.** The commit to release is pushed to its development branch. Claude names the full SHA, the branch, GitHub `main`, the live SHA and its deploy id.
2. **Gate (Joel, on the Mac).** The script is fetched from GitHub at the exact candidate commit, so it does not depend on the Desktop copy of the repository (parts of the Desktop are kept in iCloud only).
   ```bash
   curl -fsSL https://raw.githubusercontent.com/joelbrayman-collab/Brayman-Estimator/<candidate>/tools/release/release_gate.sh -o /tmp/release_gate.sh
   bash /tmp/release_gate.sh --label <name> --candidate <sha> --branch <branch> \
        --main-base <main sha> --live-base <live sha> --live-deploy <dep-id>
   ```
   One-time prerequisite for releases from the security branch on: `/usr/bin/python3 relocate_local_storage.py` (fetched the same way from `tools/release/`). Release working files then go to `~/CalibraytAI-Office/release-work` and the Mac backup copies to `~/CalibraytAI-Office/office-backups`, outside the iCloud Desktop. The gate stops with that instruction if the folders are missing. (The cleanup-branch gate `3e36b9d` still uses the Desktop folders, as every release before it did.)
   It stops at the first failure, and on success at **READY_FOR_PUSH**. It checks: one run at a time; `main`, the branch and the live instance separately; a fresh clone at the exact commit, a fast-forward from `main`, descended from live, no migration or model change; production's exact Python packages; the complete native regression with exit 0 and **no skipped test**; the end-to-end contractor walk and the Cal tests ran and passed; the release browser checks in Google Chrome (desktop and phone); a fresh hosted backup, copied to the Mac and verified by SHA-256 and `PRAGMA integrity_check`, with tables and rows counted; contract signing readiness (read-only). It pushes nothing and deploys nothing.
3. **Authorization (Joel).** Separate, explicit, naming the commit.
4. **Push and deploy (Claude).** `git push origin <sha>:refs/heads/main` (the tested commit itself, fast-forward), then deploy that commit on Render.
5. **Post-release (Joel, on the Mac).** `curl -fsSL https://raw.githubusercontent.com/joelbrayman-collab/Brayman-Estimator/<sha>/tools/release/postrelease_check.sh -o /tmp/postrelease_check.sh && bash /tmp/postrelease_check.sh --label <name>`. Read-only: `main` is the commit, `git fsck`, the live instance reports it, the database re-read shows the same revision, integrity ok and the same tables and rows as the backup, and the signed-out public and Cal checks pass. Safe to run again.
6. **Record.** Session handoff entry with the SHA, deploy id, gate results, backup, post-check and rollback.

## Release with a database change

Not covered by the generic gate (it stops if `migrations/` or `app/models` changed). A migration release needs, in addition and with Joel's separate authorization of the migration: a rehearsal on a copy of the fresh backup on the Mac that proves exactly which tables and columns are added and that no existing row or value changes (see `generated/v1hub_hosted_migrate.py`, 17 Oct, for the pattern), and the same proof on the live database once after the deploy.

Since 29 Oct 2026 the gate carries this itself when it is given `--migration-to <revision>` with the declared change: `--new-tables`, `--altered-tables`, `--altered-checks`, and (30 Oct 2026) `--filled-columns table.column,...` and `--populated-tables`. The candidate must add exactly one migration file. The rehearsal on the fresh backup compares every row of every table: a declared filled column may only go from empty to a value (a value already held must not change), a declared populated table may receive rows (counted in the log), and everything else must be identical. `release_migrate.sh` applies the same check to the live database after the deploy, with the same declarations from the gate's STATE.

## Rollback

Redeploy the previous live commit with the same settings (its deploy id is recorded by the gate). A database restore from the pre-release backup happens only with Joel's approval.

## Corrections made on 18 Oct 2026 (technical cleanup)

| Problem found | Correction |
|---|---|
| A new script copy per release with the SHA edited in; superseded copies kept beside them (`drawings_release.v1-stopped-…`, `v1addr_release.sh` and `v1addr2_release.sh`, …) | One parameterized gate and post-check in the repository; helpers versioned with the code (byte-identical to the proven ones; `tests/test_release_tools.py`) |
| The regression installed a 13 Oct Mac lock plus unpinned `requirements.txt`, so it did not test production's versions (for example pypdf 6.14.2 against production 6.21.1, reportlab 5.0.0 against 5.0.1) | `requirements-lock.txt` = Render's installed set for `0e2c917`, used as constraints |
| Python Playwright absent on the Mac; two test files skipped and the gate accepted it | `requirements-dev.txt`; any skip now stops the gate |
| Two copies of a release script ran at the same time (18 Oct) | Lock folder; a second run stops with a message |
| Backup copy retried three times at a fixed 10 s, checksum checked once after | Up to five attempts with growing waits; checksum verified on each attempt |
| `client_global_hostkeys_prove_confirm: server gave bad signature` noise on every SSH call | `-o UpdateHostKeys=no` (host keys in `known_hosts` are still verified) |
