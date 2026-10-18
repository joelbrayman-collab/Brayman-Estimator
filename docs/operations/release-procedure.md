# Release Procedure

| Attribute | Value |
|-----------|--------|
| Status | Current (technical cleanup, 18 Oct 2026) |
| Scripts | `tools/release/release_gate.sh`, `tools/release/postrelease_check.sh` |
| Replaces | the per-release copies in `~/Desktop/Brayman-Estimator/generated/` (`cal1_release.sh`, `v1bd_release.sh`, …), which remain there as history |

Production is changed only after Joel's explicit authorization of the exact commit. Tests passing never deploys anything. Auto-deploy stays off.

## Release without a database change

1. **Candidate.** The commit to release is pushed to its development branch. Claude names the full SHA, the branch, GitHub `main`, the live SHA and its deploy id.
2. **Gate (Joel, on the Mac).**
   ```bash
   git -C ~/Desktop/Brayman-Estimator fetch -q origin <branch>
   git -C ~/Desktop/Brayman-Estimator show <candidate>:tools/release/release_gate.sh > /tmp/release_gate.sh
   bash /tmp/release_gate.sh --label <name> --candidate <sha> --branch <branch> \
        --main-base <main sha> --live-base <live sha> --live-deploy <dep-id>
   ```
   It stops at the first failure, and on success at **READY_FOR_PUSH**. It checks: one run at a time; `main`, the branch and the live instance separately; a fresh clone at the exact commit, a fast-forward from `main`, descended from live, no migration or model change; production's exact Python packages; the complete native regression with exit 0 and **no skipped test**; the end-to-end contractor walk and the Cal tests ran and passed; the release browser checks in Google Chrome (desktop and phone); a fresh hosted backup, copied to the Mac and verified by SHA-256 and `PRAGMA integrity_check`, with tables and rows counted; contract signing readiness (read-only). It pushes nothing and deploys nothing.
3. **Authorization (Joel).** Separate, explicit, naming the commit.
4. **Push and deploy (Claude).** `git push origin <sha>:refs/heads/main` (the tested commit itself, fast-forward), then deploy that commit on Render.
5. **Post-release (Joel, on the Mac).** `bash /tmp/postrelease_check.sh --label <name>` (fetched the same way). Read-only: `main` is the commit, `git fsck`, the live instance reports it, the database re-read shows the same revision, integrity ok and the same tables and rows as the backup, and the signed-out public and Cal checks pass. Safe to run again.
6. **Record.** Session handoff entry with the SHA, deploy id, gate results, backup, post-check and rollback.

## Release with a database change

Not covered by the generic gate (it stops if `migrations/` or `app/models` changed). A migration release needs, in addition and with Joel's separate authorization of the migration: a rehearsal on a copy of the fresh backup on the Mac that proves exactly which tables and columns are added and that no existing row or value changes (see `generated/v1hub_hosted_migrate.py`, 17 Oct, for the pattern), and the same proof on the live database once after the deploy.

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
