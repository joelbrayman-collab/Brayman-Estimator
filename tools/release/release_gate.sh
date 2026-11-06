#!/bin/bash
# CalibraytAI release gate. Runs on the office Mac. A release with a database change adds
# --migration-to <revision> --new-tables <t1,t2,...> (19 Oct 2026); without them a migration stops the gate.
# It pushes nothing and deploys nothing: it stops at READY_FOR_PUSH. Production needs Joel's
# separate authorization; then Claude pushes the tested commit itself to main and deploys it,
# and Joel runs postrelease_check.sh.
#
# Replaces the per-release copies in ~/Desktop/Brayman-Estimator/generated/ (cal1_release.sh,
# v1bd_release.sh, ...). The gates are the same ones those scripts ran; only the release values
# are now parameters instead of being edited into a new copy each time.
#
# Usage (from any folder; fetch this script from the candidate commit itself):
#   git -C ~/Desktop/Brayman-Estimator fetch -q origin <branch>
#   git -C ~/Desktop/Brayman-Estimator show <candidate>:tools/release/release_gate.sh > /tmp/release_gate.sh
#   bash /tmp/release_gate.sh --label cal2 --candidate <sha> --branch v1/completion \
#        --main-base <sha> --live-base <sha> --live-deploy <dep-id> [--browser-expected 49]
#        [--migration-to <revision> --new-tables <t1,t2,...> [--altered-tables <t1,...>] [--altered-checks <ck_1,...>]
#         [--filled-columns <table.column,...>] [--populated-tables <t1,...>]]
#
# Gates (stops at the first failure):
#   1 one run at a time; GitHub main = --main-base; --branch = --candidate; live instance (SSH) = --live-base
#   2 fresh clone at the candidate: fast-forward from main, descends from live, no migration or model change,
#     nothing outside app/ tests/ docs/ tools/ calculation-engines/ requirements*.txt changed;
#     Python from requirements.txt + requirements-dev.txt with requirements-lock.txt (production's exact
#     versions); complete native regression must exit 0 with NO skipped test (on the Mac the historical
#     folder and Python Playwright are present, so nothing may skip); the end-to-end contractor walk and the
#     Cal tests must have run and passed; release browser checks in Google Chrome
#   3 fresh hosted backup (SQLite online backup), copied to the Mac, checksum and integrity verified, rows counted
#   3a with --migration-to: the candidate's single Alembic head is that revision and it follows the live
#      revision; the migration is rehearsed on a copy of the fresh backup on this Mac (every existing table's
#      schema and rows identical, exactly the new tables added and empty, integrity ok); the copy is deleted
#   3b contract signing readiness (read-only)
#   4 READY_FOR_PUSH — stop.
# After authorization of a release with a migration: Claude pushes and deploys; Joel runs
# release_migrate.sh (applies the migration on the live instance after its own backup), then postrelease_check.sh.
# Since 3 Nov 2026 tools/release/release.sh runs this gate, waits for the push and deploy, the migration (after a typed
# confirmation) and the post-release checks in one Terminal window. Each run of this gate gets its own run ID
# (<label>-<YYYYMMDD-HHMMSS>, or --run-id from release.sh) and folder $GEN/runs/<run ID>/; its gate/ evidence is sealed
# (SHA-256 MANIFEST, read-only) when it ends. A second run with the same label never truncates or replaces the first.
set -u
usage() { sed -n '2,39p' "$0"; exit 2; }
RUN_ID_ARG=""; LABEL=""; SHA=""; BRANCH=""; MAIN_BASE=""; LIVE_BASE=""; LIVE_DEPLOY=""; BROWSER_EXPECTED=263; MIGRATION_TO=""; NEW_TABLES=""; ALTERED_TABLES=""; ALTERED_CHECKS=""; FILLED_COLUMNS=""; POPULATED_TABLES=""
while [ $# -gt 0 ]; do
  case "$1" in
    --label) LABEL=$2; shift 2;;
    --run-id) RUN_ID_ARG=$2; shift 2;;
    --candidate) SHA=$2; shift 2;;
    --branch) BRANCH=$2; shift 2;;
    --main-base) MAIN_BASE=$2; shift 2;;
    --live-base) LIVE_BASE=$2; shift 2;;
    --live-deploy) LIVE_DEPLOY=$2; shift 2;;
    --browser-expected) BROWSER_EXPECTED=$2; shift 2;;
    --migration-to) MIGRATION_TO=$2; shift 2;;
    --new-tables) NEW_TABLES=$2; shift 2;;
    --altered-tables) ALTERED_TABLES=$2; shift 2;;
    --altered-checks) ALTERED_CHECKS=$2; shift 2;;
    --filled-columns) FILLED_COLUMNS=$2; shift 2;;
    --populated-tables) POPULATED_TABLES=$2; shift 2;;
    *) usage;;
  esac
done
for v in LABEL SHA BRANCH MAIN_BASE LIVE_BASE LIVE_DEPLOY; do [ -n "${!v}" ] || usage; done
for v in SHA MAIN_BASE LIVE_BASE; do
  [[ "${!v}" =~ ^[0-9a-f]{40}$ ]] || { echo "$v must be a full 40-character commit SHA"; exit 2; }
done
[[ "$LABEL" =~ ^[a-z0-9-]+$ ]] || { echo "--label: lower-case letters, digits and dashes only"; exit 2; }
if [ -n "$MIGRATION_TO$NEW_TABLES" ]; then
  [[ "$MIGRATION_TO" =~ ^[0-9a-z]{12}$ ]] && [[ "$NEW_TABLES" =~ ^[a-z_]+(,[a-z_]+)*$ ]] \
    || { echo "--migration-to <12-character revision> and --new-tables <t1,t2> go together"; exit 2; }
  # --new-tables none (27 Oct 2026): a migration that only adds columns to declared --altered-tables; the rehearsal
  # then requires that no table at all is added.
  if [ "$NEW_TABLES" = "none" ] && [ -z "$ALTERED_TABLES$ALTERED_CHECKS" ]; then
    echo "--new-tables none is only for a migration that changes declared --altered-tables (or --altered-checks)"; exit 2
  fi
fi
# --altered-tables <t1,...> (20 Oct 2026): existing tables whose schema the migration changes (e.g. a widened
# check constraint). Every one of their rows must still be identical; any other schema change still stops.
if [ -n "$ALTERED_TABLES" ]; then
  [ -n "$MIGRATION_TO" ] && [[ "$ALTERED_TABLES" =~ ^[a-z_]+(,[a-z_]+)*$ ]] \
    || { echo "--altered-tables <t1,t2> needs --migration-to and lower-case table names"; exit 2; }
fi
# --altered-checks <ck_1,...> (29 Oct 2026, supplier signing a4d5e6f7a8b9): the only check constraints the migration
# may change. The rehearsal and the live apply then allow a rebuilt table only if its columns, keys, foreign keys and
# every other check are identical (stricter than --altered-tables, which accepts any schema change of a table).
# --filled-columns <table.column,...> and --populated-tables <t1,...> (30 Oct 2026, estimate-to-project release):
# the data the migration is authorized to write, named here so Joel sees it in the command. A filled column that
# already existed may only go from empty to a value; every other column of every row is still compared exactly.
if [ -n "$FILLED_COLUMNS" ]; then
  [ -n "$MIGRATION_TO" ] && [[ "$FILLED_COLUMNS" =~ ^[a-z_]+\.[a-z_]+(,[a-z_]+\.[a-z_]+)*$ ]] \
    || { echo "--filled-columns <table.column,...> needs --migration-to"; exit 2; }
fi
if [ -n "$POPULATED_TABLES" ]; then
  [ -n "$MIGRATION_TO" ] && [[ "$POPULATED_TABLES" =~ ^[a-z_]+(,[a-z_]+)*$ ]] \
    || { echo "--populated-tables <t1,t2> needs --migration-to (and the tables in --new-tables)"; exit 2; }
fi
if [ -n "$ALTERED_CHECKS" ]; then
  [ -n "$MIGRATION_TO" ] && [[ "$ALTERED_CHECKS" =~ ^ck_[a-z0-9_]+(,ck_[a-z0-9_]+)*$ ]] \
    || { echo "--altered-checks <ck_1,ck_2> needs --migration-to and check constraint names (ck_...)"; exit 2; }
fi

REPO_URL=https://github.com/joelbrayman-collab/Brayman-Estimator.git
# Release working files and office backups live outside the iCloud Desktop (18 Oct 2026):
# ~/CalibraytAI-Office, made by tools/release/relocate_local_storage.py (copy only).
OFFICE_LOCAL="${CALIBRAYTAI_OFFICE_LOCAL:-$HOME/CalibraytAI-Office}"
GEN="$OFFICE_LOCAL/release-work"
HOST=srv-dar95mh42hec73df4rug@ssh.virginia.render.com
SSH_OPTS=(-o UpdateHostKeys=no)
BACKUPS="$OFFICE_LOCAL/office-backups"
if [ ! -d "$GEN" ] || [ ! -d "$BACKUPS" ]; then
  echo "STOP: $GEN or $BACKUPS does not exist. Run tools/release/relocate_local_storage.py first"
  echo "(it copies the Desktop backups and release files there and verifies them; nothing is deleted)."
  exit 1
fi

# One run at a time (two copies of a release script once ran side by side on 18 Oct).
LOCKDIR="$GEN/.release-gate.lock"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "STOP: another release gate is running (lock $LOCKDIR, started by: $(cat "$LOCKDIR/owner" 2>/dev/null))."
  echo "If no other run is open in any Terminal window, remove the lock folder and start again."
  exit 1
fi
echo "$LABEL pid $$ $(date)" > "$LOCKDIR/owner"
trap 'rm -rf "$LOCKDIR"' EXIT

# >>> release-runs (3 Nov 2026). Byte-identical in release.sh, release_gate.sh, release_migrate.sh and
# postrelease_check.sh (tests/test_release_runs.py checks this), so each script still works when fetched on its own.
# Every gate run has its own run ID (<label>-<YYYYMMDD-HHMMSS>) and folder $GEN/runs/<run ID>/; nothing in one run's
# folder is ever truncated or rewritten by another run. A run's gate/ folder is sealed when the gate ends (a SHA-256
# MANIFEST of every file, then every file and the folder read-only); gate/READY_FOR_PUSH marks a run that passed.
# Plain bash 3.2 (the Mac's /bin/bash): no associative arrays, no mapfile.
rr_sha256() { if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$@"; else sha256sum "$@"; fi; }
rr_val() { grep "^$1=" "$2" 2>/dev/null | head -1 | cut -d= -f2-; }
# rr_require <file> <key> <what the file is>: prints the value, or explains exactly what is missing and returns 1.
rr_require() {
  local f=$1 k=$2 what=${3:-file} v
  if [ ! -e "$f" ]; then
    echo "$what $f does not exist, so $k cannot be read"; return 1
  fi
  if [ ! -s "$f" ]; then
    echo "$what $f is EMPTY (0 bytes), so $k cannot be read; it was truncated or never written (the gate run that made it did not reach READY_FOR_PUSH). Nothing was guessed. Run release.sh --label <label> --list to see every run and which one reached READY_FOR_PUSH"; return 1
  fi
  v=$(rr_val "$k" "$f")
  if [ -z "$v" ]; then
    echo "$what $f has no value for $k (line '$k=' missing or blank; $(grep -c . "$f") line(s) in the file)"; return 1
  fi
  printf '%s\n' "$v"
}
# rr_new_run <label> [<run ID>]: creates $GEN/runs/<run ID>/ atomically (mkdir, never -p on the run folder) and prints
# the run ID. Without a run ID, <label>-<timestamp> (with -2, -3, ... if that second is already taken). An existing
# run folder is never reused.
rr_new_run() {
  local label=$1 id=${2:-} base n=1
  mkdir -p "$GEN/runs" || return 1
  if [ -n "$id" ]; then
    case "$id" in "$label"-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]*) ;; *)
      echo "run ID $id is not $label-<YYYYMMDD-HHMMSS>" >&2; return 1;; esac
    mkdir "$GEN/runs/$id" 2>/dev/null || { echo "run $id already exists in $GEN/runs; its evidence is never reused or overwritten" >&2; return 1; }
  else
    base="$label-$(date +%Y%m%d-%H%M%S)"; id=$base
    until mkdir "$GEN/runs/$id" 2>/dev/null; do
      n=$((n + 1)); id="$base-$n"; [ "$n" -lt 100 ] || { echo "could not create a run folder in $GEN/runs" >&2; return 1; }
    done
  fi
  printf 'RUN_ID=%s\nLABEL=%s\nCREATED=%s\n' "$id" "$label" "$(date '+%Y-%m-%d %H:%M:%S %z')" > "$GEN/runs/$id/run.txt" \
    && chmod a-w "$GEN/runs/$id/run.txt" && echo "$id"
}
# rr_seal <folder>: SHA-256 MANIFEST of every file below it, then every file and folder in it read-only. Once only.
rr_seal() {
  local d=$1
  [ -d "$d" ] || { echo "cannot seal $d: no such folder"; return 1; }
  [ -e "$d/MANIFEST.sha256" ] && { echo "$d is already sealed"; return 1; }
  ( cd "$d" && find . -type f ! -path ./MANIFEST.sha256 | LC_ALL=C sort | while IFS= read -r f; do rr_sha256 "$f"; done \
      > MANIFEST.sha256 ) || return 1
  chmod -R a-w "$d"
}
# rr_verify <folder>: the folder is sealed, every file matches its MANIFEST line and no file was added or removed.
rr_verify() {
  local d=$1 listed present
  [ -s "$d/MANIFEST.sha256" ] || { echo "$d has no MANIFEST.sha256 (not sealed)"; return 1; }
  ( cd "$d" && rr_sha256 -c MANIFEST.sha256 >/dev/null 2>&1 ) || { echo "a file in $d differs from its MANIFEST.sha256 entry"; return 1; }
  listed=$(sed -E 's/^[0-9a-f]{64}  //' "$d/MANIFEST.sha256" | LC_ALL=C sort)
  present=$(cd "$d" && find . -type f ! -path ./MANIFEST.sha256 | LC_ALL=C sort)
  [ "$listed" = "$present" ] || { echo "files were added to or removed from sealed $d"; return 1; }
}
# rr_runs <label>: "<run ID> <outcome> <commit>" for every run of this label, oldest first. Outcome is RELEASED,
# READY_FOR_PUSH (passed, not yet released), STOPPED, INTERRUPTED or RUNNING (no end marker: running, or killed).
rr_runs() {
  local d id outcome
  for d in "$GEN/runs/$1"-[0-9]*; do
    [ -d "$d" ] && [ "$(rr_val LABEL "$d/run.txt")" = "$1" ] || continue
    id=${d##*/}
    if [ -f "$d/RELEASED" ]; then outcome=RELEASED
    elif [ -f "$d/gate/READY_FOR_PUSH" ]; then outcome=READY_FOR_PUSH
    elif [ -f "$d/gate/STOPPED" ]; then outcome=STOPPED
    elif [ -f "$d/gate/INTERRUPTED" ]; then outcome=INTERRUPTED
    else outcome=RUNNING; fi
    echo "$id $outcome $(rr_val SHA "$d/gate/READY_FOR_PUSH" || true)"
  done
}
# rr_bind <label> <commit>: the run whose READY_FOR_PUSH is exactly <commit> (the commit on GitHub main and live).
# Several such runs: the one that already holds migration or post-release records, else the newest. A run whose gate
# evidence fails its MANIFEST is never bound. Prints the run ID, or explains and returns 1.
rr_bind() {
  local label=$1 sha=$2 id outcome commit picked="" used="" all
  [ -n "$sha" ] || { echo "no commit to bind to (the commit read from GitHub main is blank)"; return 1; }
  all=$(rr_runs "$label")
  while read -r id outcome commit; do
    [ -n "$id" ] && [ "$commit" = "$sha" ] || continue
    case "$outcome" in RELEASED|READY_FOR_PUSH) ;; *) continue;; esac
    rr_verify "$GEN/runs/$id/gate" >/dev/null || continue
    picked=$id
    if [ -d "$GEN/runs/$id/migrate" ] || [ -d "$GEN/runs/$id/post" ]; then used=$id; fi
  done <<EOF
$all
EOF
  [ -n "$used" ] && picked=$used
  if [ -z "$picked" ]; then
    echo "no gate run of $label reached READY_FOR_PUSH for $sha (with its sealed evidence intact). Runs of $label: $(echo "$all" | grep . | tr '\n' ';' || true)"
    [ -n "$all" ] || echo "(none in $GEN/runs)"
    return 1
  fi
  echo "$picked"
}
# rr_resolve <label> <run ID or empty>: which run release_migrate.sh / postrelease_check.sh act on. With a run ID, that
# run (it must be of this label, have reached READY_FOR_PUSH and have intact sealed evidence). Without one, the run
# bound to the commit on GitHub main (rr_bind). A label with no run folders at all is a release gated before 3 Nov 2026:
# its $GEN/<label>-release-status.txt and -state.txt are used, as before. Sets RUN_ID, RUN_DIR, STATUS, GSTATE (the
# gate's sealed state) and STATE (where the migration adds its records); prints STOP: ... and returns 1 otherwise.
rr_resolve() {
  local label=$1 run=$2 main="" tries outcome
  RUN_ID=""
  if [ -n "$run" ]; then
    outcome=$(rr_runs "$label" | awk -v r="$run" '$1 == r {print $2}')
    [ -n "$outcome" ] || { echo "STOP: run $run is not a run of $label in $GEN/runs"; return 1; }
    case "$outcome" in RELEASED|READY_FOR_PUSH) ;; *) echo "STOP: run $run did not reach READY_FOR_PUSH (its outcome: $outcome)"; return 1;; esac
    rr_verify "$GEN/runs/$run/gate" >/dev/null || { echo "STOP: $(rr_verify "$GEN/runs/$run/gate")"; return 1; }
    RUN_ID=$run
  elif [ -n "$(rr_runs "$label")" ]; then
    for tries in 1 2 3; do
      main=$(git ls-remote "$REPO_URL" refs/heads/main | cut -f1)
      [ -n "$main" ] && break
      [ "$tries" -lt 3 ] && sleep 5
    done
    [ -n "$main" ] || { echo "STOP: GitHub main could not be read (git ls-remote returned nothing, 3 tries), so no run can be bound; check the network and run the same command again"; return 1; }
    RUN_ID=$(rr_bind "$label" "$main") || { echo "STOP: $RUN_ID"; return 1; }
  fi
  if [ -n "$RUN_ID" ]; then
    RUN_DIR="$GEN/runs/$RUN_ID"; STATUS="$RUN_DIR/status.txt"; GSTATE="$RUN_DIR/gate/state.txt"; STATE="$RUN_DIR/after-state.txt"
    echo "== Run $RUN_ID (READY_FOR_PUSH $(rr_val SHA "$RUN_DIR/gate/READY_FOR_PUSH")); evidence $RUN_DIR"
  else
    RUN_DIR=""; STATUS="$GEN/$label-release-status.txt"; GSTATE="$GEN/$label-release-state.txt"; STATE=$GSTATE
    echo "== No run folders for $label in $GEN/runs: using the pre-3 Nov 2026 files $GSTATE and $STATUS"
  fi
}
# <<< release-runs

# This run's own folder (3 Nov 2026). Before, every run of a label wrote $GEN/<label>-release-status.txt and
# -state.txt and began by truncating them, so a second gate run of the same label (vd1, 3 Nov) blanked the first
# run's READY_FOR_PUSH record. Now nothing outside this run's new folder is written, and nothing is truncated.
RUN_ID=$(rr_new_run "$LABEL" "$RUN_ID_ARG") || { echo "STOP: could not create this run's folder (see above)"; exit 1; }
RUN_DIR="$GEN/runs/$RUN_ID"; EVID="$RUN_DIR/gate"
mkdir "$EVID" || { echo "STOP: could not create $EVID"; exit 1; }
DEST=$HOME/Developer/Brayman-Estimator-$RUN_ID
TS=${RUN_ID#"$LABEL"-}; OUT="$EVID/$LABEL"; LOG="$EVID/gate.log"; STATUS="$RUN_DIR/status.txt"
STATE="$EVID/state.txt"
# At the end of the run, however it ends (passed, stopped, Ctrl-C, closed window): the outcome marker, then the seal.
finish_gate() {
  if [ ! -f "$EVID/READY_FOR_PUSH" ] && [ ! -f "$EVID/STOPPED" ]; then
    echo "INTERRUPTED $(date) before READY_FOR_PUSH" > "$EVID/INTERRUPTED"
    echo "INTERRUPTED $(date): the gate did not finish; this run cannot be released. Start a new run." >> "$STATUS"
  fi
  rr_seal "$EVID" >/dev/null && echo "== Run $RUN_ID: evidence sealed in $EVID (MANIFEST.sha256, read-only)" \
    || echo "WARNING: could not seal $EVID"
  rm -rf "$LOCKDIR"
}
trap finish_gate EXIT
trap 'exit 130' INT TERM HUP

status() { echo "$1" >> "$STATUS"; echo "  [status] $1"; }
stop() { echo "$1" > "$EVID/STOPPED"; status "STOPPED: $1"; echo "STOP: $1"; exit 1; }
val() { grep "^$1=" "$2" | head -1 | cut -d= -f2-; }
REMOTE_PY='cd /opt/render/project/src && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=$(command -v python3); fi; $PY -'

# The gate itself. It runs as one function piped into the log, so the log is complete before the run is sealed.
gate_main() {
status "STARTED $(date) label=$LABEL run=$RUN_ID log=$LOG"

echo "== 1. GitHub main, the candidate branch and the live instance, each checked separately"
MAIN=$(git ls-remote "$REPO_URL" refs/heads/main | cut -f1)
[ "$MAIN" = "$MAIN_BASE" ] || stop "GitHub main is $MAIN, expected $MAIN_BASE"
BR=$(git ls-remote "$REPO_URL" "refs/heads/$BRANCH" | cut -f1)
[ "$BR" = "$SHA" ] || stop "$BRANCH is $BR, expected the candidate $SHA"
# The live SHA over SSH (27 Oct 2026): up to three attempts, 10 s apart, and SSH's own error is kept in the log.
# A single dropped SSH connection read as an empty SHA and stopped the pcux1 gate while the instance was on the
# expected commit. The comparison itself is unchanged: anything but exactly --live-base still stops.
LIVE=""
for attempt in 1 2 3; do
  LIVE=$(ssh "${SSH_OPTS[@]}" -n "$HOST" 'echo SHA=$RENDER_GIT_COMMIT' 2>"$OUT-live-ssh.txt" | tr -d '\r' | grep '^SHA=' | cut -d= -f2)
  [ -n "$LIVE" ] && break
  echo "live SHA attempt $attempt returned nothing; SSH said: $(tr '\n' ' ' < "$OUT-live-ssh.txt" | cut -c1-300)"
  [ "$attempt" -lt 3 ] && sleep 10
done
[ "$LIVE" = "$LIVE_BASE" ] || stop "live instance runs '$LIVE', expected $LIVE_BASE"
status "BASELINE github_main=$MAIN live=$LIVE $BRANCH=$BR to_release=$SHA"

echo "== 2. Clean clone at the candidate; checks; complete native regression; browser checks in Chrome"
[ -e "$DEST" ] && stop "$DEST exists"
mkdir -p "$HOME/Developer"
git clone -q "$REPO_URL" "$DEST" || stop "clone failed"
cd "$DEST"
git fetch -q origin "$BRANCH" || stop "fetch of $BRANCH failed"
git -c advice.detachedHead=false checkout -q "$SHA" || stop "checkout failed (is $SHA pushed to $BRANCH?)"
[ "$(git rev-parse HEAD)" = "$SHA" ] || stop "clone is not $SHA"
git merge-base --is-ancestor "$MAIN_BASE" "$SHA" || stop "$SHA is not a fast-forward from main $MAIN_BASE"
git merge-base --is-ancestor "$LIVE_BASE" "$SHA" || stop "$SHA does not descend from live $LIVE_BASE"
if [ -z "$MIGRATION_TO" ]; then
  [ -z "$(git diff --name-only "$LIVE_BASE" "$SHA" -- migrations app/models app/plan_intelligence/models.py)" ] \
    || stop "migrations or models changed: this release needs --migration-to and --new-tables"
  DBCHANGE="no migration or model change"
else
  ADDED=$(git diff --name-only --diff-filter=A "$LIVE_BASE" "$SHA" -- migrations/versions)
  OTHER=$(git diff --name-only --diff-filter=MDR "$LIVE_BASE" "$SHA" -- migrations)
  [ -z "$OTHER" ] || stop "an existing migration file was changed or removed: $OTHER"
  [ "$(echo "$ADDED" | grep -c .)" = "1" ] && grep -q "^revision = \"$MIGRATION_TO\"" $ADDED \
    || stop "the candidate must add exactly one migration, revision $MIGRATION_TO (added: $ADDED)"
  DBCHANGE="one new migration $MIGRATION_TO ($ADDED), rehearsed below"
fi
ALLOWED='^(app/|tests/|docs/|tools/|calculation-engines/|requirements(-dev|-lock)?\.txt$)'
[ -n "$MIGRATION_TO" ] && ALLOWED='^(app/|tests/|docs/|tools/|calculation-engines/|migrations/versions/|requirements(-dev|-lock)?\.txt$)'
OUTSIDE=$(git diff --name-only "$MAIN_BASE" "$SHA" | grep -vE "$ALLOWED")
[ -z "$OUTSIDE" ] || stop "unexpected files changed: $OUTSIDE"
status "FAST_FORWARD main $MAIN_BASE -> $SHA ($(git rev-list --count "$MAIN_BASE..$SHA") commits); descends from live; $DBCHANGE"
HELPERS=$(cd tools/release && shasum -a 256 hosted_preflight.py hosted_postcheck.py signing_readiness.py migration_check.py evidence_*.mjs | awk '{printf "%s=%s ", $2, substr($1,1,12)}')
status "HELPERS from $SHA: $HELPERS"
/usr/bin/python3 -m venv venv || stop "venv failed"
./venv/bin/python -m pip install -q --upgrade pip
./venv/bin/python -m pip install -q -r requirements.txt -r requirements-dev.txt -c requirements-lock.txt \
  || stop "package install failed"
./venv/bin/python -m playwright install chromium >/dev/null 2>&1 || stop "Playwright Chromium install failed"
for pkg in calculation-engines/concrete-slab-1.0.0 calculation-engines/stair-ontario-residential-v1; do
  ( cd "$pkg" && npm ci --no-audit --no-fund >/dev/null 2>&1 ) || stop "npm ci failed in $pkg"
done
bash tools/setup_test_environment.sh --check || stop "test environment check failed"
# tmp_path folders of passed tests are removed (3 Nov 2026: a full run kept ~1.3 GB, and pytest keeps three runs);
# a failed test keeps its folder for diagnosis. Which tests run and what they assert is unchanged.
PYTEST="./venv/bin/python -u -X faulthandler -m pytest -p no:cacheprovider -o faulthandler_timeout=180 -o tmp_path_retention_policy=failed"
# Faster gate (2 Nov 2026): the same complete suite, spread over one pytest-xdist worker per CPU core. --dist loadfile
# keeps each test file on one worker, in file order, exactly as a serial run sees it. The junit XML still lists every
# test case (the no-skip, end-to-end and Cal checks below read it unchanged, and the count check compares it with the
# summary line). PYTEST_WORKERS=4 sets the worker count; PYTEST_WORKERS=0 runs serially in one process.
XDIST="-n ${PYTEST_WORKERS:-auto} --dist loadfile"
START=$(date +%s)
$PYTEST -q -rfEs $XDIST --junitxml="$OUT-junit.xml" tests 2>&1 | tee "$OUT-full.txt" | tail -15
FULL=${PIPESTATUS[0]}
status "MAC_FULL=$(grep -E '(passed|failed)' "$OUT-full.txt" | tail -1) exit=$FULL duration=$(( $(date +%s) - START ))s"
[ "$FULL" -eq 0 ] || stop "complete Mac regression did not pass; nothing pushed"
/usr/bin/python3 - "$OUT-junit.xml" "$OUT-full.txt" <<'PYEOF' || stop "a test was skipped, the junit XML does not list every test that passed, or the end-to-end contractor walk or the Cal tests did not run and pass"
import re, sys, xml.etree.ElementTree as E
cases = list(E.parse(sys.argv[1]).iter("testcase"))
summary = re.findall(r"(\d+) passed", open(sys.argv[2], errors="replace").read())
listed = sum(1 for c in cases if not any(x.tag in ("skipped", "failure", "error") for x in c))
if not summary or int(summary[-1]) != listed:
    print("JUNIT_COUNT %d passed test cases in the XML, summary says %s" % (listed, summary[-1] if summary else "nothing"))
    sys.exit(1)
skipped = [c.get("classname") + "::" + c.get("name") for c in cases if any(x.tag == "skipped" for x in c)]
for s in skipped:
    print("SKIPPED " + s)
def clean(name):
    picked = [c for c in cases if c.get("classname") == name]
    return picked and not any(x.tag in ("skipped", "failure", "error") for c in picked for x in c)
sys.exit(0 if not skipped and clean("tests.test_contractor_workflow_e2e") and clean("tests.test_cal_find_it") else 1)
PYEOF
status "NO_SKIPS; E2E_CONTRACTOR_WALK=passed in Google Chrome; CAL_TESTS=passed"
( cd tools/release && EVIDENCE_REPO="$DEST" node --test --test-reporter=tap --test-force-exit --test-concurrency=1 \
    evidence_employment_v11.mjs evidence_trade_pages.mjs evidence_cal_find_it.mjs evidence_calendar.mjs evidence_pro_desk.mjs evidence_supplier_hub.mjs evidence_roles.mjs evidence_first_day.mjs evidence_training.mjs evidence_workflow_map.mjs evidence_training_signin.mjs evidence_field_crew.mjs evidence_field_time.mjs evidence_useful_calculators.mjs evidence_time_payroll.mjs evidence_sms_notifications.mjs evidence_site_plans.mjs evidence_guided_estimating.mjs evidence_wizards.mjs evidence_magnificent_seven.mjs evidence_identity.mjs evidence_project_creation.mjs evidence_selected_work.mjs evidence_calisign.mjs evidence_compact_new_project.mjs evidence_documents.mjs evidence_guided_tasks.mjs evidence_density.mjs evidence_internal_approval.mjs ) > "$OUT-browser.txt" 2>&1
BR_EXIT=$?
grep -E '(tests|pass|fail) [0-9]+$|^not ok' "$OUT-browser.txt"
[ "$BR_EXIT" -eq 0 ] && grep -qE "^(# |ℹ )pass $BROWSER_EXPECTED\$" "$OUT-browser.txt" && grep -qE '^(# |ℹ )fail 0$' "$OUT-browser.txt" \
  || stop "browser checks failed (expected $BROWSER_EXPECTED passed, 0 failed)"
status "BROWSER_CHECKS=$BROWSER_EXPECTED passed in Google Chrome (desktop and phone)"

echo "== 3. Fresh hosted backup"
ssh "${SSH_OPTS[@]}" "$HOST" "export BACKUP_PREFIX=pre-$LABEL; $REMOTE_PY" < tools/release/hosted_preflight.py | tee "$OUT-preflight.txt"
grep -q '^PREFLIGHT=ok' "$OUT-preflight.txt" || stop "hosted preflight failed"
[ "$(val RUNNING_SHA "$OUT-preflight.txt")" = "$LIVE_BASE" ] || stop "live instance is not $LIVE_BASE"
[ "$(val LIVE_INTEGRITY "$OUT-preflight.txt")" = "ok" ] || stop "live integrity is not ok"
[ "$(val BACKUP_INTEGRITY "$OUT-preflight.txt")" = "ok" ] || stop "backup integrity is not ok"
REVISION=$(val LIVE_REVISION "$OUT-preflight.txt")
[ -n "$REVISION" ] && [ "$(val BACKUP_REVISION "$OUT-preflight.txt")" = "$REVISION" ] || stop "backup revision differs from live"
grep -q "^revision = \"$REVISION\"" migrations/versions/*.py || stop "live revision $REVISION is not a migration in the candidate"
if [ -n "$MIGRATION_TO" ]; then
  HEADINFO=$(./venv/bin/python - "$MIGRATION_TO" <<'PYEOF'
import sys
from alembic.config import Config
from alembic.script import ScriptDirectory
cfg = Config(); cfg.set_main_option("script_location", "migrations")
s = ScriptDirectory.from_config(cfg)
print("HEADS=" + ",".join(s.get_heads()) + " DOWN=" + str(s.get_revision(sys.argv[1]).down_revision))
PYEOF
)
  [ "$HEADINFO" = "HEADS=$MIGRATION_TO DOWN=$REVISION" ] || stop "migration graph: $HEADINFO (expected head $MIGRATION_TO following live $REVISION)"
fi
BPATH=$(val BACKUP_PATH "$OUT-preflight.txt"); BSHA=$(val BACKUP_SHA256 "$OUT-preflight.txt")
mkdir -p "$BACKUPS"
LOCALB="$BACKUPS/$(basename "$BPATH")"
for i in 1 2 3 4 5; do
  scp "${SSH_OPTS[@]}" -q "$HOST:$BPATH" "$BACKUPS/" && [ "$(shasum -a 256 "$LOCALB" | awk '{print $1}')" = "$BSHA" ] && break
  echo "  backup copy attempt $i did not complete; retrying in $((i * 10)) s"; rm -f "$LOCALB"; sleep $((i * 10))
done
[ -f "$LOCALB" ] || stop "could not copy the backup to the Mac"
[ "$(shasum -a 256 "$LOCALB" | awk '{print $1}')" = "$BSHA" ] || stop "Mac backup checksum differs"
[ "$(/usr/bin/sqlite3 "$LOCALB" 'PRAGMA integrity_check;')" = "ok" ] || stop "Mac backup integrity is not ok"
# Row totals (review fix C1, 1 Nov 2026): every table except sqlite_* and the search index (document_search and its
# FTS5 shadow tables, derived data the app rewrites); the index is recorded on its own line. postrelease_check.sh
# counts the live database with the same helper, so both sides count the same tables.
BCOUNT=$(/usr/bin/python3 tools/release/migration_check.py count-rows --db "$LOCALB") || stop "could not count the backup's rows"
BROWS=$(echo "$BCOUNT" | grep '^TABLES=')
BSEARCH=$(echo "$BCOUNT" | grep '^SEARCH_INDEX=' | cut -d= -f2-)
[ -n "$BROWS" ] && [ -n "$BSEARCH" ] || stop "could not count the backup's rows ($BCOUNT)"
status "BACKUP=$BPATH sha256=$BSHA $BROWS (search index $BSEARCH, not in the totals) revision=$REVISION integrity=ok; Mac copy $LOCALB matches"

if [ -n "$MIGRATION_TO" ]; then
  echo "== 3a. Migration rehearsal on a copy of the fresh production backup (this Mac only)"
  REHEARSAL="$GEN/$RUN_ID-rehearsal.db"  # outside the run folder: never sealed into the evidence
  cp "$LOCALB" "$REHEARSAL" || stop "could not copy the backup for the rehearsal"
  ./venv/bin/python tools/release/migration_check.py rehearse --db "$REHEARSAL" --from "$REVISION" \
    --to "$MIGRATION_TO" --new-tables "$NEW_TABLES" ${ALTERED_TABLES:+--altered-tables "$ALTERED_TABLES"} \
    ${ALTERED_CHECKS:+--altered-checks "$ALTERED_CHECKS"} ${FILLED_COLUMNS:+--filled-columns "$FILLED_COLUMNS"} \
    ${POPULATED_TABLES:+--populated-tables "$POPULATED_TABLES"} > "$OUT-rehearsal.txt" 2>&1
  REH=$?
  rm -f "$REHEARSAL"  # production data: no extra copy is kept
  cat "$OUT-rehearsal.txt" | grep -E '^[A-Z_]+='
  [ "$REH" -eq 0 ] && grep -q '^MIGRATION_REHEARSAL=ok' "$OUT-rehearsal.txt" || stop "migration rehearsal failed (see $OUT-rehearsal.txt)"
  status "MIGRATION_REHEARSAL $REVISION -> $MIGRATION_TO on a copy of $(basename "$LOCALB"): $(val EXISTING_TABLES_UNCHANGED "$OUT-rehearsal.txt"); new: $(val NEW_TABLES "$OUT-rehearsal.txt"); integrity $(val INTEGRITY_AFTER "$OUT-rehearsal.txt"); $(val UPGRADE_SECONDS "$OUT-rehearsal.txt") s; copy deleted"
fi

echo "== 3b. Contract signing readiness on the live database (read-only)"
ssh "${SSH_OPTS[@]}" "$HOST" "$REMOTE_PY" < tools/release/signing_readiness.py | tee "$OUT-signing-readiness.txt"
grep -q '^READINESS=ok' "$OUT-signing-readiness.txt" || stop "no ACTIVE PRODUCTION contract package on the live database"
status "SIGNING_READINESS $(grep '^ACTIVE_PRODUCTION_PACKAGES=' "$OUT-signing-readiness.txt"); $(grep '^SIGNING_ARTIFACTS=' "$OUT-signing-readiness.txt")"

# The state is written once (noclobber: an existing file is never replaced) and sealed with the rest of gate/.
( set -o noclobber; cat > "$STATE" ) <<EOF || stop "could not write $STATE (it already exists; evidence is never overwritten)"
RUN_ID=$RUN_ID
LABEL=$LABEL
SHA=$SHA
BRANCH=$BRANCH
MAIN_BASE=$MAIN_BASE
LIVE_BASE=$LIVE_BASE
LIVE_DEPLOY=$LIVE_DEPLOY
REVISION=$REVISION
BACKUP=$LOCALB
BACKUP_ROWS=$BROWS
BACKUP_SEARCH_INDEX=$BSEARCH
CLONE=$DEST
MIGRATION_TO=$MIGRATION_TO
NEW_TABLES=$NEW_TABLES
ALTERED_TABLES=$ALTERED_TABLES
ALTERED_CHECKS=$ALTERED_CHECKS
FILLED_COLUMNS=$FILLED_COLUMNS
POPULATED_TABLES=$POPULATED_TABLES
EOF
for key in RUN_ID SHA LIVE_BASE LIVE_DEPLOY REVISION BACKUP BACKUP_ROWS BACKUP_SEARCH_INDEX CLONE; do
  CHECKED=$(rr_require "$STATE" "$key" "release state") || stop "$CHECKED"
done
echo "== 4. READY_FOR_PUSH — stop here"
if [ -n "$MIGRATION_TO" ]; then
  status "ROLLBACK_TARGET=code: redeploy $LIVE_BASE ($LIVE_DEPLOY, same settings) — it runs unchanged with the added tables present; database: only with Joel's approval, restore the pre-migration backup release_migrate.sh takes on the instance (or $LOCALB)"
  status "AFTER_AUTHORIZATION Claude pushes $SHA and deploys it; Joel runs release_migrate.sh --run $RUN_ID (migration $REVISION -> $MIGRATION_TO), then postrelease_check.sh --run $RUN_ID (release.sh --label $LABEL does both)"
else
  status "ROLLBACK_TARGET=redeploy $LIVE_BASE ($LIVE_DEPLOY, same settings); no database change to undo; restore only with Joel's approval from $LOCALB"
fi
status "READY_FOR_PUSH commit=$SHA run=$RUN_ID (nothing pushed, nothing deployed; production needs Joel's authorization)"
cp "$STATUS" "$EVID/status-at-ready.txt" || stop "could not keep a copy of the status file in $EVID"
printf 'SHA=%s\nRUN_ID=%s\nAT=%s\n' "$SHA" "$RUN_ID" "$(date '+%Y-%m-%d %H:%M:%S %z')" > "$EVID/READY_FOR_PUSH"
echo "== DONE. All gates passed. Send Claude the status file: $STATUS"
}

gate_main 2>&1 | tee "$LOG"
GATE_EXIT=${PIPESTATUS[0]}
[ "$GATE_EXIT" -eq 0 ] && [ -f "$EVID/READY_FOR_PUSH" ] || exit 1
exit 0
