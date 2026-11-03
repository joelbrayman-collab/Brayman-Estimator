#!/bin/bash
# CalibraytAI release, one command in one Terminal window (3 Nov 2026). Runs on the office Mac.
#   1 runs the release gate (release_gate.sh, every gate unchanged) from the candidate commit itself, as a new run
#     <label>-<YYYYMMDD-HHMMSS> with its own sealed evidence folder;
#   2 at READY_FOR_PUSH prints a short block for Joel to send to Claude, then waits (GitHub main and the live
#     instance, every --poll-seconds, up to --wait-minutes) until Claude has pushed and deployed exactly that commit.
#     It never pushes or deploys anything itself: production still needs Joel's authorization to Claude;
#   3 a release with a migration then stops and asks Joel to type MIGRATE <label> <revision> in this window before
#     release_migrate.sh runs (with all of its own protections);
#   4 runs postrelease_check.sh and ends with RELEASED or STOPPED.
# Safe to run again after an interruption (Ctrl-C, closed window, timeout): the same command resumes the run of this
# label that reached READY_FOR_PUSH for this candidate and is not yet released. It does not run the gate again (so no
# second backup), does not migrate twice, and never touches another run's evidence. --new-run gates again as a new run.
#
# Usage (fetch this script from the candidate commit itself, then the one command):
#   curl -fsSL https://raw.githubusercontent.com/joelbrayman-collab/Brayman-Estimator/<candidate>/tools/release/release.sh -o /tmp/release.sh
#   bash /tmp/release.sh --label vd2 --candidate <sha> --branch <branch> --main-base <sha> --live-base <sha> \
#        --live-deploy <dep-id> [--browser-expected N] [--migration-to <revision> --new-tables <t1,...> ...]
#        [--wait-minutes 180] [--poll-seconds 30] [--new-run]
#   bash /tmp/release.sh --label vd2 --list        (every run of the label and its outcome)
# The gate, migration and post-release scripts it runs are taken from the candidate commit (git show), sealed in
# $GEN/tools/<commit>/, and this script must be byte-identical to the candidate's own copy.
set -u
usage() { sed -n '2,24p' "$0"; exit 2; }
LABEL=""; SHA=""; BRANCH=""; MAIN_BASE=""; LIVE_BASE=""; LIVE_DEPLOY=""; BROWSER_EXPECTED=""; MIGRATION_TO=""
NEW_TABLES=""; ALTERED_TABLES=""; ALTERED_CHECKS=""; FILLED_COLUMNS=""; POPULATED_TABLES=""
NEW_RUN=0; LIST=0; WAIT_MINUTES=180; POLL_SECONDS=30
while [ $# -gt 0 ]; do
  case "$1" in
    --label) LABEL=$2; shift 2;;
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
    --wait-minutes) WAIT_MINUTES=$2; shift 2;;
    --poll-seconds) POLL_SECONDS=$2; shift 2;;
    --new-run) NEW_RUN=1; shift;;
    --list) LIST=1; shift;;
    *) usage;;
  esac
done
[[ "$LABEL" =~ ^[a-z0-9-]+$ ]] || usage
REPO_URL=https://github.com/joelbrayman-collab/Brayman-Estimator.git
OFFICE_LOCAL="${CALIBRAYTAI_OFFICE_LOCAL:-$HOME/CalibraytAI-Office}"
GEN="$OFFICE_LOCAL/release-work"
HOST=srv-dar95mh42hec73df4rug@ssh.virginia.render.com
SSH_OPTS=(-o UpdateHostKeys=no)
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
if [ "$LIST" -eq 1 ]; then
  echo "Runs of $LABEL in $GEN/runs (oldest first): <run ID> <outcome> <commit that reached READY_FOR_PUSH>"
  rr_runs "$LABEL"
  exit 0
fi
for v in SHA BRANCH MAIN_BASE LIVE_BASE LIVE_DEPLOY; do [ -n "${!v}" ] || usage; done
for v in SHA MAIN_BASE LIVE_BASE; do
  [[ "${!v}" =~ ^[0-9a-f]{40}$ ]] || { echo "$v must be a full 40-character commit SHA"; exit 2; }
done
[[ "$WAIT_MINUTES" =~ ^[0-9]+$ ]] && [[ "$POLL_SECONDS" =~ ^[0-9]+$ ]] && [ "$POLL_SECONDS" -ge 1 ] \
  || { echo "--wait-minutes and --poll-seconds take whole numbers (poll at least 1 second)"; exit 2; }
[ -d "$GEN" ] || { echo "STOP: $GEN does not exist. Run tools/release/relocate_local_storage.py first."; exit 1; }

# One release.sh per label at a time (the gate has its own lock as well).
LOCK="$GEN/.release-$LABEL.lock"
mkdir "$LOCK" 2>/dev/null || {
  echo "STOP: release.sh for $LABEL is already running in another window (lock $LOCK, $(cat "$LOCK/owner" 2>/dev/null))."
  echo "If no other window runs it, remove that lock folder and run the same command again."; exit 1; }
echo "pid $$ $(date)" > "$LOCK/owner"
RUN_ID=""
trap 'rm -rf "$LOCK"' EXIT
trap 'echo; echo "Interrupted. Nothing was pushed or deployed by this script. Run the same command again to resume${RUN_ID:+ run $RUN_ID}."; exit 130' INT TERM HUP
mkdir -p "$GEN/release-logs"
exec > >(tee -a "$GEN/release-logs/$LABEL-$(date +%Y%m%d-%H%M%S).log") 2>&1

summary() {  # summary RELEASED|STOPPED <what happened / what to do>
  echo
  echo "==================== $1 ===================="
  echo "label $LABEL   run ${RUN_ID:-(none)}   commit $SHA"
  echo "$2"
  if [ -n "$RUN_ID" ] && [ -f "$GEN/runs/$RUN_ID/status.txt" ]; then
    echo "evidence $GEN/runs/$RUN_ID"
    echo "last status lines:"; tail -3 "$GEN/runs/$RUN_ID/status.txt" | sed 's/^/  /'
  fi
  echo "=============================================="
  [ "$1" = RELEASED ] && exit 0
  exit 1
}

# The candidate's own release scripts, sealed once per commit (release checks use the exact approved commit).
TOOLS="$GEN/tools/$SHA"
if ! rr_verify "$TOOLS" >/dev/null 2>&1; then
  if [ -e "$TOOLS" ]; then chmod -R u+w "$TOOLS" && rm -rf "$TOOLS"; fi  # an incomplete copy from an interrupted fetch
  SRC="$GEN/.release-source.git"
  [ -d "$SRC" ] || git init -q --bare "$SRC" || summary STOPPED "could not create $SRC"
  git -C "$SRC" fetch -q "$REPO_URL" "+refs/heads/main:refs/release/main" || summary STOPPED "could not fetch GitHub main"
  git -C "$SRC" fetch -q "$REPO_URL" "+refs/heads/$BRANCH:refs/release/candidate" 2>/dev/null || true  # gone after release
  git -C "$SRC" cat-file -e "$SHA^{commit}" 2>/dev/null || summary STOPPED "$SHA is on neither GitHub main nor $BRANCH"
  mkdir -p "$GEN/tools"; PART="$TOOLS.partial-$$"; rm -rf "$PART"; mkdir "$PART" || summary STOPPED "could not create $PART"
  for f in release.sh release_gate.sh release_migrate.sh postrelease_check.sh; do
    git -C "$SRC" show "$SHA:tools/release/$f" > "$PART/$f" && [ -s "$PART/$f" ] || summary STOPPED "$SHA has no tools/release/$f"
  done
  echo "SHA=$SHA" > "$PART/COMMIT"
  mv "$PART" "$TOOLS" && rr_seal "$TOOLS" >/dev/null || summary STOPPED "could not seal the candidate's release scripts in $TOOLS"
fi
cmp -s "$0" "$TOOLS/release.sh" || summary STOPPED "this copy of release.sh ($0) is not the candidate's own. Fetch it from the candidate:
  curl -fsSL https://raw.githubusercontent.com/joelbrayman-collab/Brayman-Estimator/$SHA/tools/release/release.sh -o /tmp/release.sh"

# Resume or gate: the newest run of this label that reached READY_FOR_PUSH for this candidate and is not released.
PENDING=""; DONE=""
while read -r id outcome commit; do
  [ -n "$id" ] && [ "$commit" = "$SHA" ] || continue
  rr_verify "$GEN/runs/$id/gate" >/dev/null || { echo "  (run $id is not used: $(rr_verify "$GEN/runs/$id/gate"))"; continue; }
  [ "$outcome" = READY_FOR_PUSH ] && PENDING=$id
  [ "$outcome" = RELEASED ] && DONE=$id
done <<EOF
$(rr_runs "$LABEL")
EOF
if [ "$NEW_RUN" -eq 0 ] && [ -n "$DONE" ] && [ -z "$PENDING" ]; then
  RUN_ID=$DONE; summary RELEASED "already released as run $DONE (sealed). Nothing to do."
fi
if [ "$NEW_RUN" -eq 0 ] && [ -n "$PENDING" ]; then
  RUN_ID=$PENDING; GSTATE="$GEN/runs/$RUN_ID/gate/state.txt"
  echo "== Resuming run $RUN_ID: its gate reached READY_FOR_PUSH for $SHA (the gate and its backup are not repeated)"
  # The command must declare what that run's gate tested; anything else needs a new gate run.
  for pair in BRANCH:BRANCH MAIN_BASE:MAIN_BASE LIVE_BASE:LIVE_BASE LIVE_DEPLOY:LIVE_DEPLOY MIGRATION_TO:MIGRATION_TO \
              NEW_TABLES:NEW_TABLES ALTERED_TABLES:ALTERED_TABLES ALTERED_CHECKS:ALTERED_CHECKS \
              FILLED_COLUMNS:FILLED_COLUMNS POPULATED_TABLES:POPULATED_TABLES; do
    var=${pair%%:*}; key=${pair#*:}
    [ "$(rr_val "$key" "$GSTATE")" = "${!var}" ] || summary STOPPED "run $RUN_ID was gated with $key='$(rr_val "$key" "$GSTATE")' but this command says '${!var}'. Use the run's own command, or add --new-run to gate this command as a new run."
  done
else
  [ "$NEW_RUN" -eq 1 ] && [ -n "$PENDING" ] && echo "== --new-run: run $PENDING stays as it is (never displaced); gating again as a new run"
  # A new run ID; -2, -3, ... when that second is already taken (this window holds the label's lock).
  RUN_ID="$LABEL-$(date +%Y%m%d-%H%M%S)"; BASE_ID=$RUN_ID; N=1
  while [ -e "$GEN/runs/$RUN_ID" ]; do N=$((N + 1)); RUN_ID="$BASE_ID-$N"; done
  echo "== 1. Release gate, run $RUN_ID (from $SHA's own tools/release/release_gate.sh)"
  GATE_ARGS=(--run-id "$RUN_ID" --label "$LABEL" --candidate "$SHA" --branch "$BRANCH" --main-base "$MAIN_BASE"
             --live-base "$LIVE_BASE" --live-deploy "$LIVE_DEPLOY")
  [ -n "$BROWSER_EXPECTED" ] && GATE_ARGS+=(--browser-expected "$BROWSER_EXPECTED")
  [ -n "$MIGRATION_TO" ] && GATE_ARGS+=(--migration-to "$MIGRATION_TO")
  [ -n "$NEW_TABLES" ] && GATE_ARGS+=(--new-tables "$NEW_TABLES")
  [ -n "$ALTERED_TABLES" ] && GATE_ARGS+=(--altered-tables "$ALTERED_TABLES")
  [ -n "$ALTERED_CHECKS" ] && GATE_ARGS+=(--altered-checks "$ALTERED_CHECKS")
  [ -n "$FILLED_COLUMNS" ] && GATE_ARGS+=(--filled-columns "$FILLED_COLUMNS")
  [ -n "$POPULATED_TABLES" ] && GATE_ARGS+=(--populated-tables "$POPULATED_TABLES")
  bash "$TOOLS/release_gate.sh" "${GATE_ARGS[@]}"
  GATE_EXIT=$?
  if [ ! -d "$GEN/runs/$RUN_ID" ]; then RUN_ID=""; summary STOPPED "the gate did not start a run (exit $GATE_EXIT; see above)"; fi
  [ "$GATE_EXIT" -eq 0 ] && [ -f "$GEN/runs/$RUN_ID/gate/READY_FOR_PUSH" ] \
    || summary STOPPED "the gate did not reach READY_FOR_PUSH: $(cat "$GEN/runs/$RUN_ID/gate/STOPPED" "$GEN/runs/$RUN_ID/gate/INTERRUPTED" 2>/dev/null | head -1). Nothing was pushed or deployed. Fix the cause, then run the command again (a new run)."
  GSTATE="$GEN/runs/$RUN_ID/gate/state.txt"
fi
RUN_DIR="$GEN/runs/$RUN_ID"; STATUS="$RUN_DIR/status.txt"
CHECK=$(rr_verify "$RUN_DIR/gate") || summary STOPPED "$CHECK"
for key in SHA REVISION LIVE_BASE MAIN_BASE; do
  CHECK=$(rr_require "$GSTATE" "$key" "release state") || summary STOPPED "$CHECK"
done
[ "$(rr_val SHA "$GSTATE")" = "$SHA" ] && [ "$(rr_val SHA "$RUN_DIR/gate/READY_FOR_PUSH")" = "$SHA" ] \
  || summary STOPPED "run $RUN_ID's evidence is not for $SHA"
REVISION=$(rr_val REVISION "$GSTATE")

# 2. Joel sends the block to Claude; this window waits for exactly this commit on GitHub main and on the live instance.
if [ -n "$MIGRATION_TO" ]; then DBLINE="migration $REVISION -> $MIGRATION_TO (new tables: $NEW_TABLES${ALTERED_TABLES:+; altered: $ALTERED_TABLES}${ALTERED_CHECKS:+; checks: $ALTERED_CHECKS}${FILLED_COLUMNS:+; filled: $FILLED_COLUMNS}${POPULATED_TABLES:+; populated: $POPULATED_TABLES}), rehearsed"
else DBLINE="no migration (revision $REVISION unchanged)"; fi
echo
echo "==================== SEND THIS TO CLAUDE ===================="
echo "CalibraytAI release $LABEL: gate READY_FOR_PUSH"
echo "run       $RUN_ID"
echo "commit    $SHA"
echo "base      main $MAIN_BASE; live $LIVE_BASE ($LIVE_DEPLOY)"
echo "database  $DBLINE"
echo "evidence  $RUN_DIR/gate (sealed, MANIFEST sha256 $(rr_sha256 "$RUN_DIR/gate/MANIFEST.sha256" | cut -c1-12))"
echo "status    $STATUS"
echo "=============================================================="
echo "Production needs your authorization: if you authorize it, send the block above to Claude with your own words."
echo "This window waits until Claude has pushed and deployed exactly $SHA (checks every $POLL_SECONDS s, up to"
echo "$WAIT_MINUTES min). Leave it open. If it is interrupted, the same command resumes run $RUN_ID."
DEADLINE=$(( $(date +%s) + WAIT_MINUTES * 60 )); LAST=""
while :; do
  MAIN=$(git ls-remote "$REPO_URL" refs/heads/main 2>/dev/null | cut -f1)
  LIVE=$(ssh "${SSH_OPTS[@]}" -n -o ConnectTimeout=20 "$HOST" 'echo SHA=$RENDER_GIT_COMMIT' 2>/dev/null | tr -d '\r' | grep '^SHA=' | cut -d= -f2)
  NOW="${MAIN:-none} ${LIVE:-none}"
  [ "$NOW" = "$LAST" ] || echo "  $(date +%H:%M:%S) GitHub main ${MAIN:-(no answer)}; live ${LIVE:-(no answer)}"
  LAST=$NOW
  [ "$MAIN" = "$SHA" ] && [ "$LIVE" = "$SHA" ] && break
  [ -z "$MAIN" ] || [ "$MAIN" = "$SHA" ] || [ "$MAIN" = "$MAIN_BASE" ] \
    || summary STOPPED "GitHub main is $MAIN: neither the approved $SHA nor the base $MAIN_BASE. Nothing was migrated or checked; tell Claude."
  [ -z "$LIVE" ] || [ "$LIVE" = "$SHA" ] || [ "$LIVE" = "$LIVE_BASE" ] \
    || summary STOPPED "the live instance runs $LIVE: neither the approved $SHA nor the base $LIVE_BASE. Nothing was migrated or checked; tell Claude."
  [ "$(date +%s)" -lt "$DEADLINE" ] \
    || summary STOPPED "still waiting after $WAIT_MINUTES min (main ${MAIN:-no answer}, live ${LIVE:-no answer}). Run $RUN_ID is kept: run the same command again to keep waiting."
  sleep "$POLL_SECONDS"
done
grep -q "^PUSHED_AND_LIVE commit=$SHA" "$STATUS" || echo "PUSHED_AND_LIVE commit=$SHA seen by release.sh $(date) (GitHub main and the live instance)" >> "$STATUS"
echo "== 2. $SHA is on GitHub main and live"

# 3. The migration, only after Joel types the confirmation phrase in this window.
if [ -n "$MIGRATION_TO" ]; then
  if grep -q "^MIGRATED .*-> $MIGRATION_TO\|^MIGRATED already at $MIGRATION_TO" "$STATUS"; then
    echo "== 3. Migration to $MIGRATION_TO already recorded for run $RUN_ID: not run again (no second backup)"
  else
    PHRASE="MIGRATE $LABEL $MIGRATION_TO"
    echo "== 3. Database migration $REVISION -> $MIGRATION_TO on the live instance"
    echo "release_migrate.sh takes its own backup on the instance, applies the migration, proves every existing table's"
    echo "rows unchanged and copies the backup to this Mac. Only if you authorized this migration, type exactly:"
    echo "  $PHRASE"
    printf '> '
    TYPED=""; read -r TYPED || TYPED=""
    [ "$TYPED" = "$PHRASE" ] || summary STOPPED "the confirmation phrase was not typed (got '$TYPED'); nothing was migrated. Run the same command again to resume run $RUN_ID."
    echo "MIGRATION_CONFIRMED by typed phrase in release.sh $(date)" >> "$STATUS"
    bash "$TOOLS/release_migrate.sh" --label "$LABEL" --run "$RUN_ID" \
      || summary STOPPED "release_migrate.sh stopped (see above and $STATUS). The app keeps running; database recovery only with Joel."
  fi
fi

# 4. Post-release checks on the same run.
echo "== 4. Post-release checks for run $RUN_ID"
bash "$TOOLS/postrelease_check.sh" --label "$LABEL" --run "$RUN_ID" \
  || summary STOPPED "postrelease_check.sh stopped (see above). It is safe to run the same command again."
[ -f "$RUN_DIR/RELEASED" ] || summary STOPPED "postrelease_check.sh ended without recording RELEASED for run $RUN_ID"
summary RELEASED "$SHA is live and every post-release check passed. Claude now checks the release signed in."
