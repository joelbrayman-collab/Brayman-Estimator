# Release simplification and faster-gate review (3 Nov 2026)

| Attribute | Value |
|-----------|--------|
| Branch | `feature/faster-gate-2026-11-02` (cut from `5db36f30`; main merged at `8a83c4b3`, release vd1) |
| Status | Implemented; **not yet relied on**: a supervised dry run on the office Mac is required first (see Risks) |
| Scripts | `tools/release/release.sh` (new), `release_gate.sh`, `release_migrate.sh`, `postrelease_check.sh` |
| Tests | `tests/test_release_runs.py` (new), `tests/test_parallel_gate.py`, `tests/test_release_tools.py`, `tests/test_release_postcheck_seed.py` |

## Why

On 3 Nov 2026 Joel ran `release_gate.sh` twice with the label vd1. The second run began with
`: > "$STATUS"; : > "$STATE"`, truncating `vd1-release-status.txt` and `vd1-release-state.txt`, then stopped early.
`postrelease_check.sh` read a blank SHA and stopped with "the release gate did not reach READY_FOR_PUSH for" and
nothing after it. The release was recovered from the first run's log.

## 1. Merge

`git merge origin/main` (no rebase, no force-push): merge commit `1fb85bcb`, no conflicts. Main had added only a ledger
entry (`docs/implementation/task-first-rdims-ledger.md`) and a load wait in `tests/wall_framing_page_browser.mjs`.

## 2. Faster-gate review (commits `b85b5f7b`, `5d58d926`)

### Coverage equality

| Run | Test IDs |
|---|---|
| Serial `pytest --collect-only -q tests` | 4,013 (4,013 unique) |
| `-n 2 --dist loadfile`, worker gw0 (each worker wrote the IDs it collected, then ran none) | 4,013, identical after sorting |
| `-n 2 --dist loadfile`, worker gw1 | 4,013, identical after sorting |

xdist distributes only what every worker collected identically, so the parallel run covers exactly the serial set.

### Full parallel run 1 (Python 3.9.6, `-n 2 --dist loadfile`, 2-CPU container)

3,998 passed, 4 failed, 11 skipped in 3,657 s (61 min).

* The 4 failures were release-tool tests (`test_release_tools.py` x2, `test_release_postcheck_seed.py` x2). The run used
  the same worktree in which the release scripts were being rewritten, so they read half-edited scripts. The tests were
  updated with the new scripts; all release-tool tests pass. **A clean full run is still owed** (see Risks).
* The 11 skips are all `tests/test_historical_ingestion.py`: the real customer workbook folder exists only on the office
  Mac. The gate still stops on any skip, so on the Mac the count must be 0.

### Isolation findings and fixes

| Finding | Fix | Commit |
|---|---|---|
| Schema-cache fingerprint described table-level create listeners by `repr` only and ignored metadata-level listeners: a DDL listener added in a process was served the older copy without it | Every before/after_create listener (table or metadata) is fingerprinted by full DDL text and dialect, or a function's module, name and bytecode; run-time-deciding callables must be listed in `REVIEWED_CALLABLE_CREATE_LISTENERS` (today only `_create_fts`, whose condition, the SQLite build, is in the fingerprint). The new guard test fails on the old fingerprint | `487c599b` |
| Two browser scripts stopped the page server with an immediate SIGKILL, so its cleanup never ran: a `calibai-page-server-*` folder per run | SIGTERM, wait, SIGKILL only after 10 s; guard test over every browser script | `8451eb09` |
| Wall-framing second phone measurement read the unstyled page under load (scrollWidth 2508 at 390 px, 1 in 3 with two workers) | `waitForLoadState("load")` before it, as for the first measurement; 6 of 6 repeats passed | `8451eb09` |
| Passed tests' `tmp_path` folders: ~1.3 GB per full run, three runs kept | Gate passes `-o tmp_path_retention_policy=failed` (failed tests keep theirs) | `8451eb09` |
| Concrete-slab, stair, employment, ICF and wall-framing page tests: "office page did not start" on a loaded machine (fixed 20 s start limit) | 120 s overall limit while polling the server's `READY <port>` line every 50 ms; still fails at once if the server exits; on timeout stops the server and prints the limit, elapsed time and server output. Python wrappers' outer limit raised to 300 s so the script's explanation is what is reported. Guard test; both failure paths proved with temporary probes | this commit |

No problem found: xdist workers run `atexit` cleanup; every page server binds a free port; tests change environment
variables through `monkeypatch`; no shared file in `instance/`. `pytest-randomly` is not installed.

Not affected by the review, confirmed:

* **Password memo** cannot weaken a security test: the key is the exact (stored hash, password) pair, so every answer is
  the real one; reset tests still see a new hash and the old password refused; `hash_password` is untouched.
* **Python 3.9**: every run above used `/home/claude/venv39` (3.9.6, pytest 8.4.2, xdist 3.8.0).

### Verification on the final head (6 Nov 2026, after merging release 1 at `9985330f`)

| Check | Result |
|---|---|
| (a) full run, `-n 2 --dist loadfile`, Python 3.9.6 (head `47de1018`) | 4,124 passed, 0 failed, 11 skipped (all `test_historical_ingestion.py`, the Mac's real workbooks), 2,549 s; junit lists 4,124 passed; e2e walk and Cal tests passed; no `calibai-*` folder left |
| (b) full run, `--dist load` (head `545df492`) | 4,122 passed, 0 failed, 11 skipped (same file), 2,905 s |
| (c) 659-test subset (every 7th of 348 files), same head | serial 793 s, `-n 2` 482 s: 1.65x; full suite: 5,038 s of test time ran in 2,559 s wall at `-n 2` (1.97x) |
| (d) gate browser walks, 29 files, `--test-concurrency=1` | 337 of 337 passed, 2,244 s; `--browser-expected 337` for this branch |

Extrapolation for the Mac: wall time ~ T_serial / (0.8 x N) + ~1 min start, never below the longest test file
(`test_session_idle_timeout_browser.py`, ~3.6 min) because `--dist loadfile` keeps a file on one worker. With the Mac's
61-minute serial run and N = 8 cores: about 61 / 6.4 + 1 = ~10.5 min; N = 10: ~8.6 min.

Found and fixed during this verification: field.js lost a wake-up during a sync (receipt walk), password-reveal.js
dropped the focus of a field it wrapped (training sign-in walk), the internal-approval page server and the identity
walk left temporary files, and three calculator test files leaked a pushed app context into later tests of the same
xdist worker (the 44 `calibai-*` folders every full run left).

## 3. Release design

### Runs and evidence

* Each gate run gets a run ID `<label>-<YYYYMMDD-HHMMSS>` (`-2`, `-3` within one second), created atomically with
  `mkdir`, and its own folder `~/CalibraytAI-Office/release-work/runs/<run ID>/`:
  `run.txt` (read-only), `status.txt`, `gate/` (log, junit, full output, browser, preflight, rehearsal, signing
  readiness, `state.txt`, status copy, outcome marker), later `migrate/` and `post/`.
* Nothing is truncated. `state.txt` is written once (`noclobber`). An existing run ID is refused.
* When the gate ends, however it ends, `gate/` gets `READY_FOR_PUSH`, `STOPPED` or `INTERRUPTED`, then is **sealed**:
  `MANIFEST.sha256` of every file, then every file and the folder read-only. `RELEASED` seals the whole run folder.
* Shared functions (`rr_require`, `rr_new_run`, `rr_seal`, `rr_verify`, `rr_runs`, `rr_bind`, `rr_resolve`) are one
  block, byte-identical in all four scripts (tested), so each still works when fetched on its own.

### Binding and blank values

* `release_migrate.sh` and `postrelease_check.sh` take `--run <run ID>`, or bind to the run of the label whose
  READY_FOR_PUSH is the commit on GitHub main. Never a later or failed run; never a run whose evidence fails its
  manifest; with several, the one already holding migration or post-release records, else the newest.
* A label with no run folders (gated before 3 Nov) uses the old `<label>-release-*.txt` files, so earlier releases keep
  working.
* Blank or empty values stop naming the file and the reason, for example
  `release state …/vd1-release-state.txt is EMPTY (0 bytes), so SHA cannot be read; it was truncated or never written …`.

### `release.sh`, one command in one window

1. Takes the four scripts from the candidate commit (`git show`), seals them in `release-work/tools/<commit>/`, and
   refuses to run unless it is itself byte-identical to the candidate's copy.
2. Runs the gate as a new run (every gate check unchanged).
3. At READY_FOR_PUSH prints **SEND THIS TO CLAUDE** (run ID, commit, bases, database change, evidence folder and manifest
   hash, status file), then polls GitHub main and the live SHA (every 30 s, up to 180 min; `--poll-seconds`,
   `--wait-minutes`) until both are exactly the commit. It stops if either shows a third commit.
4. With a migration: Joel must type `MIGRATE <label> <revision>`; anything else stops with nothing migrated. Then
   `release_migrate.sh --run` with all of its protections (its own instance backup, `--expect-sha`, rehearsal record).
5. `postrelease_check.sh --run`, then a **RELEASED** or **STOPPED** summary with the reason and the evidence folder.

Re-running the same command after an interruption resumes the pending run: no second gate or backup, no second
migration. The command's declarations (branch, bases, deploy, migration flags) must match what that run was gated with,
otherwise it stops and points to `--new-run`. `--new-run` gates again; the earlier run is never displaced.
`--list` shows every run of a label and its outcome. It never pushes or deploys: Claude still does both after Joel's
authorization.

## 4. Joel's exact usage

```bash
curl -fsSL https://raw.githubusercontent.com/joelbrayman-collab/Brayman-Estimator/<candidate>/tools/release/release.sh -o /tmp/release.sh && bash /tmp/release.sh --label <label> --candidate <candidate sha> --branch <branch> --main-base <main sha> --live-base <live sha> --live-deploy <dep-id>
```

With a migration, add the gate's own flags, for example
`--migration-to <revision> --new-tables <t1,t2>` (and `--altered-tables`, `--altered-checks`, `--filled-columns`,
`--populated-tables` as declared). Every run of a label:

```bash
bash /tmp/release.sh --label <label> --list
```

## 5. Bash 3.2

Static audit of `release.sh`, `release_gate.sh`, `release_migrate.sh`, `postrelease_check.sh` and
`tools/setup_test_environment.sh` for 4.x-only constructs (associative arrays, namerefs, `declare -g/-l/-u`,
`${v,,}` / `${v^^}`, `${v@Q}`, mapfile/readarray, `|&`, `&>>`, negative indices, `[[ -v ]]`, `coproc`, `wait -n`,
`;&`, `{fd}>`, `printf %(…)T`, `printf -v` into arrays, fractional `read -t`, `$'\u'`, 4.x `shopt` options): none found.
The one array expansion (`"${GATE_ARGS[@]}"`) is never empty (bash < 4.4 treats an empty one as unbound under
`set -u`). `tests/test_release_runs.py` enforces both and proves the check catches each construct.

## 6. Tests added

* `tests/test_release_runs.py` (23): shared block identical and parsing; unique run IDs within one second and no reuse;
  sealed evidence read-only and tamper detection; blank, empty and missing state values; binding to the right run (not a
  later, failed or tampered one; not a same-prefix label); a second real gate run never touches the first; the gate
  never truncates; an interrupted gate is marked and sealed; post-release and migration on an emptied state file; real
  post-release binding against a local origin; `release.sh` end to end (gate, wait, push-and-deploy seen, post-release,
  RELEASED), resume after interruption, typed migration phrase and no second migration, never displacing a run,
  changed declaration refused, own-copy check; `--list`; bash 3.2 constructs.
* `tests/test_parallel_gate.py`: schema-cache listener guards (2), no immediate SIGKILL, page-server start limit.

## 7. Risks

* **A supervised dry run on the office Mac is required before Joel relies on `release.sh`.** Every test here ran on Linux
  with bash 5.2, GNU coreutils, a local git origin and an SSH stand-in. Not yet exercised: macOS `/bin/bash` 3.2 (only
  statically checked), real SSH to Render, BSD `find`/`sed`/`chmod` and `shasum -c` on the manifests, and the Terminal
  prompt for the migration phrase.
* The gate's own code changed (run folders, sealing, the gate now runs as a function piped to its log). Every check is
  kept and the existing safeguard tests pass, but the old `release_gate.sh` flow has more real-world history.
* Sealed run folders are read-only: deleting an old one needs `chmod -R u+w` first.
* `tools/release/evidence_common.mjs` still has a 30 s page-server start limit. It is byte-pinned as a proven helper
  (`tests/test_release_tools.py`), so it was left unchanged; it is used by the gate's browser walks, which run one at a
  time after pytest, not under pytest load.
