"""One governed release command and immutable gate runs (3 Nov 2026).

On 3 Nov Joel ran release_gate.sh twice with the label vd1. The second run began by truncating
vd1-release-status.txt and vd1-release-state.txt and then stopped early, so postrelease_check.sh read a blank SHA
and stopped with "the release gate did not reach READY_FOR_PUSH for" and nothing after it. Now every gate run has its
own run ID and folder, its evidence is sealed (SHA-256 MANIFEST, read-only), a run that reached READY_FOR_PUSH is never
displaced, the post-release and migration steps bind to the run whose READY_FOR_PUSH is the commit on GitHub main,
blank values stop with the file and the reason, and tools/release/release.sh runs the whole release in one window.

These tests run the real scripts against stand-ins: `git` is the real git with the GitHub URL pointed at a local bare
repository, `ssh` answers with a local file. Nothing here reaches GitHub, Render or any network.
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import stat
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "tools" / "release"
TOOL = RELEASE / "release.sh"
GATE = RELEASE / "release_gate.sh"
POST = RELEASE / "postrelease_check.sh"
MIGRATE = RELEASE / "release_migrate.sh"
SCRIPTS = (TOOL, GATE, MIGRATE, POST)
REPO_URL = "https://github.com/joelbrayman-collab/Brayman-Estimator.git"
REAL_GIT = shutil.which("git")
A, B, C = "a" * 40, "b" * 40, "c" * 40


def _block(path: Path = TOOL) -> str:
    text = path.read_text()
    start, end = text.index("# >>> release-runs"), text.index("# <<< release-runs\n")
    return text[start:end + len("# <<< release-runs\n")]


def _code(path: Path) -> str:
    return "\n".join(line for line in path.read_text().splitlines() if not line.lstrip().startswith("#"))


def _env(tmp_path: Path, **extra) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "CALIBRAYTAI_OFFICE"))}
    env.update(HOME=str(tmp_path / "home"), CALIBRAYTAI_OFFICE_LOCAL=str(tmp_path / "office"),
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@example.com", GIT_CONFIG_NOSYSTEM="1", LC_ALL="C")
    env.update(extra)
    return env


def _gen(tmp_path: Path) -> Path:
    gen = tmp_path / "office" / "release-work"
    (tmp_path / "office" / "office-backups").mkdir(parents=True, exist_ok=True)
    (tmp_path / "home").mkdir(exist_ok=True)
    gen.mkdir(parents=True, exist_ok=True)
    return gen


def _sh(tmp_path: Path, body: str, **extra):
    """Run `body` with the shared release-runs functions loaded and GEN set (as every release script does)."""
    gen = _gen(tmp_path)
    script = f'set -u; GEN="{gen}"; REPO_URL={REPO_URL}\n' + _block() + body
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True, env=_env(tmp_path, **extra))


def _make_run(tmp_path: Path, label: str, run_id: str, *, ready: str = "", stopped: str = "", extra_state: str = ""):
    """A gate run folder as release_gate.sh leaves it: run.txt, gate/ evidence, an outcome marker, then the seal."""
    state = (f"RUN_ID={run_id}\nLABEL={label}\nSHA={ready or A}\nBRANCH=cand\nMAIN_BASE={C}\nLIVE_BASE={C}\n"
             f"LIVE_DEPLOY=dep-x\nREVISION=r1\nBACKUP=/b.db\nBACKUP_ROWS=TABLES=1 ROWS=1\nBACKUP_SEARCH_INDEX=TABLES=0 "
             f"ROWS=0\nCLONE=/nowhere\nMIGRATION_TO=\nNEW_TABLES=\nALTERED_TABLES=\nALTERED_CHECKS=\n"
             f"FILLED_COLUMNS=\nPOPULATED_TABLES=\n{extra_state}")
    body = f'''
rr_new_run {label} {run_id} >/dev/null || exit 1
E="$GEN/runs/{run_id}/gate"; mkdir "$E"
echo "STARTED label={label} run={run_id}" >> "$GEN/runs/{run_id}/status.txt"
echo "gate log of {run_id}" > "$E/gate.log"
'''
    if ready:
        body += f'''printf '%s' "{state}" > "$E/state.txt"
echo "READY_FOR_PUSH commit={ready} run={run_id}" >> "$GEN/runs/{run_id}/status.txt"
printf 'SHA=%s\\nRUN_ID=%s\\n' {ready} {run_id} > "$E/READY_FOR_PUSH"
'''
    elif stopped:
        body += f'echo "{stopped}" > "$E/STOPPED"; echo "STOPPED: {stopped}" >> "$GEN/runs/{run_id}/status.txt"\n'
    body += 'rr_seal "$E" >/dev/null\n'
    r = _sh(tmp_path, body)
    assert r.returncode == 0, r.stdout + r.stderr
    return _gen(tmp_path) / "runs" / run_id


def _snapshot(folder: Path) -> dict:
    return {p.relative_to(folder): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


# --- the shared functions -------------------------------------------------------------------------------------------

def test_the_shared_block_is_identical_in_every_release_script_and_parses():
    block = _block(TOOL)
    for script in SCRIPTS:
        assert _block(script) == block, script.name
        assert subprocess.run(["bash", "-n", str(script)], capture_output=True).returncode == 0, script.name
    # Bash 3.2 (the Mac's /bin/bash): none of the bash 4 features.
    for feature in ("declare -A", "mapfile", "readarray", ",,}", "^^}", "&>>", "|&"):
        for script in SCRIPTS:
            assert feature not in _code(script), (feature, script.name)


def test_run_ids_are_unique_even_within_one_second_and_a_run_folder_is_never_reused(tmp_path):
    r = _sh(tmp_path, "rr_new_run vd1; rr_new_run vd1; rr_new_run vd1\n")
    assert r.returncode == 0, r.stderr
    ids = r.stdout.split()
    assert len(ids) == len(set(ids)) == 3
    assert all(re.fullmatch(r"vd1-\d{8}-\d{6}(-\d+)?", i) for i in ids), ids
    runs = _gen(tmp_path) / "runs"
    first = runs / ids[0] / "run.txt"
    before = first.read_bytes()
    assert not first.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    again = _sh(tmp_path, f"rr_new_run vd1 {ids[0]}\n")
    assert again.returncode == 1 and "never reused or overwritten" in again.stderr
    assert first.read_bytes() == before
    wrong = _sh(tmp_path, "rr_new_run vd1 other-20261103-101010\n")
    assert wrong.returncode == 1 and "is not vd1-<YYYYMMDD-HHMMSS>" in wrong.stderr


def test_sealed_evidence_is_read_only_and_any_change_is_detected(tmp_path):
    run = _make_run(tmp_path, "vd1", "vd1-20261103-090000", ready=A)
    gate = run / "gate"
    for p in [gate, *gate.iterdir()]:
        assert not p.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH), p
    manifest = (gate / "MANIFEST.sha256").read_text()
    assert "./state.txt" in manifest and "./READY_FOR_PUSH" in manifest and "./gate.log" in manifest
    assert _sh(tmp_path, f'rr_verify "{gate}"\n').returncode == 0
    assert "already sealed" in _sh(tmp_path, f'rr_seal "{gate}"\n').stdout
    # A change (possible for root or after chmod) and an added file are both caught.
    gate.chmod(0o755)
    (gate / "state.txt").chmod(0o644)
    (gate / "state.txt").write_text((gate / "state.txt").read_text().replace(A, B))
    assert "differs from its MANIFEST" in _sh(tmp_path, f'rr_verify "{gate}"\n').stdout
    (gate / "state.txt").write_text((gate / "state.txt").read_text().replace(B, A))
    assert _sh(tmp_path, f'rr_verify "{gate}"\n').returncode == 0
    (gate / "extra.txt").write_text("x")
    assert "added to or removed" in _sh(tmp_path, f'rr_verify "{gate}"\n').stdout


def test_blank_values_are_detected_with_the_file_and_the_reason(tmp_path):
    state = tmp_path / "state.txt"
    missing = _sh(tmp_path, f'rr_require "{state}" SHA "release state"\n')
    assert missing.returncode == 1 and f"release state {state} does not exist" in missing.stdout
    state.write_text("")
    empty = _sh(tmp_path, f'rr_require "{state}" SHA "release state"\n')
    assert empty.returncode == 1 and f"release state {state} is EMPTY (0 bytes), so SHA cannot be read" in empty.stdout
    assert "did not reach READY_FOR_PUSH" in empty.stdout and "--list" in empty.stdout
    state.write_text("SHA=\nLIVE_BASE=x\n")
    blank = _sh(tmp_path, f'rr_require "{state}" SHA "release state"\n')
    assert blank.returncode == 1 and "has no value for SHA" in blank.stdout
    state.write_text(f"SHA={A}\n")
    ok = _sh(tmp_path, f'rr_require "{state}" SHA "release state"\n')
    assert ok.returncode == 0 and ok.stdout.strip() == A


def test_binding_takes_the_run_whose_ready_commit_is_on_main_never_a_later_or_failed_run(tmp_path):
    _make_run(tmp_path, "vd1", "vd1-20261103-090000", ready=A)
    _make_run(tmp_path, "vd1", "vd1-20261103-100000", stopped="live instance runs '', expected ...")
    _make_run(tmp_path, "vd1", "vd1-20261103-110000", ready=B)
    _make_run(tmp_path, "vd1-2", "vd1-2-20261103-120000", ready=A)  # another label that shares the prefix
    listing = _sh(tmp_path, "rr_runs vd1\n").stdout.splitlines()
    assert listing == ["vd1-20261103-090000 READY_FOR_PUSH " + A, "vd1-20261103-100000 STOPPED ",
                       "vd1-20261103-110000 READY_FOR_PUSH " + B]
    assert _sh(tmp_path, f"rr_bind vd1 {A}\n").stdout.strip() == "vd1-20261103-090000"
    assert _sh(tmp_path, f"rr_bind vd1 {B}\n").stdout.strip() == "vd1-20261103-110000"
    none = _sh(tmp_path, f"rr_bind vd1 {C}\n")
    assert none.returncode == 1 and f"no gate run of vd1 reached READY_FOR_PUSH for {C}" in none.stdout
    assert "vd1-20261103-100000 STOPPED" in none.stdout
    blank = _sh(tmp_path, "rr_bind vd1 ''\n")
    assert blank.returncode == 1 and "is blank" in blank.stdout
    # Two passed runs for the same commit: the newest, unless the older one already holds migration records.
    _make_run(tmp_path, "vd1", "vd1-20261103-130000", ready=A)
    assert _sh(tmp_path, f"rr_bind vd1 {A}\n").stdout.strip() == "vd1-20261103-130000"
    (_gen(tmp_path) / "runs" / "vd1-20261103-090000" / "migrate").mkdir()
    assert _sh(tmp_path, f"rr_bind vd1 {A}\n").stdout.strip() == "vd1-20261103-090000"
    # A run whose sealed evidence no longer matches its manifest is never bound.
    gate = _gen(tmp_path) / "runs" / "vd1-20261103-110000" / "gate"
    gate.chmod(0o755)
    (gate / "gate.log").chmod(0o644)
    (gate / "gate.log").write_text("edited")
    assert _sh(tmp_path, f"rr_bind vd1 {B}\n").returncode == 1


# --- the real release gate ------------------------------------------------------------------------------------------

def _stubs(tmp_path: Path, origin: Path) -> Path:
    """`git` = real git with the GitHub URL pointed at a local bare repository; `ssh` answers from ./live."""
    stubs = tmp_path / "stubs"
    stubs.mkdir(exist_ok=True)
    (stubs / "git").write_text(f'''#!/bin/bash
args=()
for a in "$@"; do if [ "$a" = "{REPO_URL}" ]; then args+=("{origin}"); else args+=("$a"); fi; done
exec {REAL_GIT} "${{args[@]}}"
''')
    (stubs / "ssh").write_text(f'''#!/bin/bash
case "${{@: -1}}" in
  *RENDER_GIT_COMMIT*) [ -f "{tmp_path}/live" ] && echo "SHA=$(cat "{tmp_path}/live")";;
  *) cat "{tmp_path}/ssh-answer" 2>/dev/null;;
esac
''')
    for f in stubs.iterdir():
        f.chmod(0o755)
    return stubs


def _git(cwd: Path, *args, env=None) -> str:
    return subprocess.run([REAL_GIT, *args], cwd=cwd, capture_output=True, text=True, check=True,
                          env=env).stdout.strip()


def _origin(tmp_path: Path, files: dict, env: dict):
    """A bare 'GitHub' with main at a base commit and branch cand at a candidate commit holding `files`."""
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    _git(tmp_path, "init", "-q", "--bare", str(origin), env=env)
    _git(tmp_path, "init", "-q", str(work), env=env)
    _git(work, "checkout", "-q", "-b", "main", env=env)
    (work / "README").write_text("base\n")
    _git(work, "add", "-A", env=env)
    _git(work, "commit", "-q", "-m", "base", env=env)
    base = _git(work, "rev-parse", "HEAD", env=env)
    _git(work, "push", "-q", str(origin), "main", env=env)
    _git(work, "checkout", "-q", "-b", "cand", env=env)
    for name, text in files.items():
        path = work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(0o755)
    _git(work, "add", "-A", env=env)
    _git(work, "commit", "-q", "-m", "candidate", env=env)
    candidate = _git(work, "rev-parse", "HEAD", env=env)
    _git(work, "push", "-q", str(origin), "cand", env=env)
    return origin, work, base, candidate


def test_a_second_gate_run_of_the_same_label_never_touches_the_first(tmp_path):
    gen = _gen(tmp_path)
    env = _env(tmp_path)
    origin, _work, base, candidate = _origin(tmp_path, {"x": "y"}, env)
    ready = _make_run(tmp_path, "vd1", "vd1-20261103-090000", ready=candidate)
    before = _snapshot(ready)
    env["PATH"] = f"{_stubs(tmp_path, origin)}:{env['PATH']}"
    args = ["bash", str(GATE), "--label", "vd1", "--candidate", candidate, "--branch", "cand",
            "--main-base", A, "--live-base", base, "--live-deploy", "dep-x"]  # main is not A: stops at gate 1
    first = subprocess.run(args, capture_output=True, text=True, env=env)
    second = subprocess.run(args, capture_output=True, text=True, env=env)
    for r in (first, second):
        assert r.returncode == 1 and f"STOP: GitHub main is {base}, expected {A}" in r.stdout, r.stdout + r.stderr
        assert "evidence sealed" in r.stdout
    runs = sorted(p.name for p in (gen / "runs").iterdir())
    assert len(runs) == 3 and runs[0] == "vd1-20261103-090000"
    assert _snapshot(ready) == before  # the READY_FOR_PUSH run is untouched, byte for byte
    assert _sh(tmp_path, f'rr_verify "{ready}/gate"\n').returncode == 0
    for name in runs[1:]:
        gate = gen / "runs" / name / "gate"
        assert (gate / "STOPPED").read_text().startswith("GitHub main is")
        assert "STARTED" in (gate / "gate.log").read_text() and (gate / "MANIFEST.sha256").exists()
        assert _sh(tmp_path, f'rr_verify "{gate}"\n').returncode == 0
    # Nothing is written to the old label-wide files, and the gate lock is released.
    assert not list(gen.glob("vd1-release-*.txt")) and not (gen / ".release-gate.lock").exists()
    assert _sh(tmp_path, f"rr_bind vd1 {candidate}\n").stdout.strip() == "vd1-20261103-090000"
    # An explicit run ID that already exists is refused before anything is written.
    reuse = subprocess.run(args + ["--run-id", "vd1-20261103-090000"], capture_output=True, text=True, env=env)
    assert reuse.returncode == 1 and "never reused or overwritten" in reuse.stdout + reuse.stderr
    assert _snapshot(ready) == before


def test_the_gate_code_never_truncates_and_writes_the_state_once():
    code = _code(GATE)
    assert ': > "$STATUS"' not in code and ': > "$STATE"' not in code
    assert not re.search(r"(^|[;&|]\s*):\s*>", code, re.M)  # no `: > file` anywhere
    assert '( set -o noclobber; cat > "$STATE" )' in code
    assert 'RUN_ID=$(rr_new_run "$LABEL" "$RUN_ID_ARG")' in code
    assert "trap finish_gate EXIT" in code and 'rr_seal "$EVID"' in code
    for key in ("RUN_ID=$RUN_ID", "MAIN_BASE=$MAIN_BASE", "BRANCH=$BRANCH"):
        assert key in code


def test_an_interrupted_gate_is_marked_interrupted_and_sealed(tmp_path):
    gen = _gen(tmp_path)
    env = _env(tmp_path)
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    (stubs / "git").write_text("#!/bin/bash\nsleep 30\n")
    (stubs / "git").chmod(0o755)
    env["PATH"] = f"{stubs}:{env['PATH']}"
    proc = subprocess.Popen(["bash", str(GATE), "--label", "vd1", "--candidate", A, "--branch", "cand",
                             "--main-base", A, "--live-base", A, "--live-deploy", "dep-x"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env,
                            start_new_session=True)
    deadline = time.time() + 20
    while time.time() < deadline and not list((gen / "runs").glob("vd1-*/status.txt")):
        time.sleep(0.2)
    time.sleep(0.5)
    os.killpg(proc.pid, signal.SIGINT)
    out, _ = proc.communicate(timeout=30)
    (run,) = list((gen / "runs").iterdir())
    assert (run / "gate" / "INTERRUPTED").exists() and not (run / "gate" / "READY_FOR_PUSH").exists()
    assert "INTERRUPTED" in (run / "status.txt").read_text()
    assert _sh(tmp_path, f'rr_verify "{run}/gate"\n').returncode == 0, out
    assert _sh(tmp_path, "rr_runs vd1\n").stdout.split()[1] == "INTERRUPTED"
    assert not (gen / ".release-gate.lock").exists()


# --- the real post-release check and migration step ------------------------------------------------------------------

def test_post_release_on_an_emptied_state_file_names_the_file_and_why(tmp_path):
    """The 3 Nov failure, in the pre-run-folder layout a release gated before 3 Nov still uses."""
    gen = _gen(tmp_path)
    (gen / "vd1-release-state.txt").write_text("")
    (gen / "vd1-release-status.txt").write_text("")
    for script in (POST, MIGRATE):
        r = subprocess.run(["bash", str(script), "--label", "vd1"], capture_output=True, text=True,
                           env=_env(tmp_path))
        assert r.returncode == 1, script.name
        assert f"release state {gen}/vd1-release-state.txt is EMPTY (0 bytes), so SHA cannot be read" in r.stdout
        assert "READY_FOR_PUSH for \n" not in r.stdout and not re.search(r"READY_FOR_PUSH for\s*$", r.stdout, re.M)


def _released_clone(tmp_path: Path, env: dict):
    origin, work, base, candidate = _origin(
        tmp_path, {"tools/release/hosted_postcheck.py": "print('x')\n",
                   "tools/release/migration_check.py": "print('x')\n"}, env)
    _git(work, "push", "-q", str(origin), "cand:main", env=env)  # Claude pushed the candidate to main
    clone = tmp_path / "clone"
    _git(tmp_path, "clone", "-q", str(origin), str(clone), env=env)
    _git(clone, "checkout", "-q", candidate, env=env)
    return origin, base, candidate, clone


def test_post_release_binds_to_the_run_whose_ready_commit_is_on_main(tmp_path):
    env = _env(tmp_path)
    origin, base, candidate, clone = _released_clone(tmp_path, env)
    # The same label gated again later: one run stopped early, one passed for another commit.
    _make_run(tmp_path, "vd1", "vd1-20261103-100000", stopped="early stop")
    other = _make_run(tmp_path, "vd1", "vd1-20261103-110000", ready=B)
    good = _gen(tmp_path) / "runs" / "vd1-20261103-090000"
    gen = _gen(tmp_path)
    r = _sh(tmp_path, f'''
rr_new_run vd1 vd1-20261103-090000 >/dev/null; E="$GEN/runs/vd1-20261103-090000/gate"; mkdir "$E"
printf 'RUN_ID=vd1-20261103-090000\\nLABEL=vd1\\nSHA={candidate}\\nMAIN_BASE={base}\\nLIVE_BASE={base}\\nLIVE_DEPLOY=dep-x\\nREVISION=r1\\nBACKUP=/b.db\\nBACKUP_ROWS=TABLES=1 ROWS=1\\nCLONE={clone}\\n' > "$E/state.txt"
echo "READY_FOR_PUSH commit={candidate} run=vd1-20261103-090000" >> "$GEN/runs/vd1-20261103-090000/status.txt"
printf 'SHA={candidate}\\n' > "$E/READY_FOR_PUSH"; rr_seal "$E" >/dev/null
''')
    assert r.returncode == 0, r.stderr
    other_before = _snapshot(other)
    env["PATH"] = f"{_stubs(tmp_path, origin)}:{env['PATH']}"
    (tmp_path / "live").write_text(candidate)
    (tmp_path / "ssh-answer").write_text("POSTCHECK=ok\nRUNNING_SHA=" + "0" * 40 + "\n")
    post = subprocess.run(["bash", str(POST), "--label", "vd1"], capture_output=True, text=True, env=env, timeout=120)
    assert post.returncode == 1, post.stdout + post.stderr
    assert "== Run vd1-20261103-090000" in post.stdout
    assert f"STOP: post-check did not run on {candidate}" in post.stdout
    status = (good / "status.txt").read_text()
    assert f"PUSHED main={candidate}" in status and "STOPPED (post-release): post-check did not run" in status
    assert list((good / "post").glob("vd1-post-*.log"))
    assert _snapshot(other) == other_before and not (other / "post").exists()
    assert not (good / "RELEASED").exists()
    # Asking for the other run explicitly: GitHub main is not its commit, so it stops in that run's own record.
    explicit = subprocess.run(["bash", str(POST), "--label", "vd1", "--run", "vd1-20261103-110000"],
                              capture_output=True, text=True, env=env, timeout=120)
    assert explicit.returncode == 1 and "STOP: the release clone /nowhere is not at " + B in explicit.stdout
    # A run that stopped cannot be named, and the migration step binds the same way.
    stopped = subprocess.run(["bash", str(POST), "--label", "vd1", "--run", "vd1-20261103-100000"],
                             capture_output=True, text=True, env=env)
    assert stopped.returncode == 1 and "did not reach READY_FOR_PUSH (its outcome: STOPPED)" in stopped.stdout
    mig = subprocess.run(["bash", str(MIGRATE), "--label", "vd1"], capture_output=True, text=True, env=env)
    assert mig.returncode == 1 and "== Run vd1-20261103-090000" in mig.stdout
    assert "this release has no migration" in mig.stdout
    assert gen.joinpath("runs", "vd1-20261103-090000", "migrate").is_dir()


def test_post_release_and_migration_keep_their_safeguards():
    post, migrate = _code(POST), _code(MIGRATE)
    assert 'rr_resolve "$LABEL" "$RUN_ARG" || exit 1' in post and 'rr_resolve "$LABEL" "$RUN_ARG" || exit 1' in migrate
    assert 'rr_seal "$RUN_DIR"' in post and 'echo "$SHA $(date' in post  # RELEASED seals the whole run
    for key in ("SHA", "LIVE_BASE", "REVISION", "BACKUP_ROWS", "CLONE"):
        assert f'$(rr_require "$GSTATE" {key} "release state")' in post
    assert 'for f in "$REPORTS/$LABEL"-migrate-*-migrate.txt; do' in migrate
    assert "--expect-sha $SHA" in migrate and "MIGRATION_REHEARSAL $REVISION -> $MIGRATION_TO" in migrate


# --- release.sh, the one command -------------------------------------------------------------------------------------

FAKE_GATE = r'''#!/bin/bash
# Stand-in for release_gate.sh: makes a sealed READY_FOR_PUSH run exactly as the real gate leaves one.
set -u
OFFICE_LOCAL="${CALIBRAYTAI_OFFICE_LOCAL}"; GEN="$OFFICE_LOCAL/release-work"
RUN_ID_ARG=""; LABEL=""; SHA=""; BRANCH=""; MAIN_BASE=""; LIVE_BASE=""; LIVE_DEPLOY=""; MIGRATION_TO=""; NEW_TABLES=""
while [ $# -gt 0 ]; do case "$1" in
  --run-id) RUN_ID_ARG=$2;; --label) LABEL=$2;; --candidate) SHA=$2;; --branch) BRANCH=$2;; --main-base) MAIN_BASE=$2;;
  --live-base) LIVE_BASE=$2;; --live-deploy) LIVE_DEPLOY=$2;; --migration-to) MIGRATION_TO=$2;; --new-tables) NEW_TABLES=$2;;
esac; shift 2; done
echo "gate $RUN_ID_ARG" >> "$OFFICE_LOCAL/calls"
@@BLOCK@@
RUN_ID=$(rr_new_run "$LABEL" "$RUN_ID_ARG") || exit 1
E="$GEN/runs/$RUN_ID/gate"; mkdir "$E"
if [ -f "$OFFICE_LOCAL/gate-fails" ]; then echo "browser checks failed" > "$E/STOPPED"; rr_seal "$E" >/dev/null; exit 1; fi
printf 'RUN_ID=%s\nLABEL=%s\nSHA=%s\nBRANCH=%s\nMAIN_BASE=%s\nLIVE_BASE=%s\nLIVE_DEPLOY=%s\nREVISION=r1\nBACKUP=/b.db\nBACKUP_ROWS=TABLES=1 ROWS=1\nCLONE=/c\nMIGRATION_TO=%s\nNEW_TABLES=%s\nALTERED_TABLES=\nALTERED_CHECKS=\nFILLED_COLUMNS=\nPOPULATED_TABLES=\n' \
  "$RUN_ID" "$LABEL" "$SHA" "$BRANCH" "$MAIN_BASE" "$LIVE_BASE" "$LIVE_DEPLOY" "$MIGRATION_TO" "$NEW_TABLES" > "$E/state.txt"
echo "READY_FOR_PUSH commit=$SHA run=$RUN_ID" >> "$GEN/runs/$RUN_ID/status.txt"
printf 'SHA=%s\nRUN_ID=%s\n' "$SHA" "$RUN_ID" > "$E/READY_FOR_PUSH"
rr_seal "$E" >/dev/null
'''
FAKE_MIGRATE = r'''#!/bin/bash
OFFICE_LOCAL="${CALIBRAYTAI_OFFICE_LOCAL}"; RUN=""
while [ $# -gt 0 ]; do case "$1" in --run) RUN=$2;; esac; shift 2; done
echo "migrate $RUN" >> "$OFFICE_LOCAL/calls"
mkdir -p "$OFFICE_LOCAL/release-work/runs/$RUN/migrate"
echo "MIGRATED r1 -> m2m2m2m2m2m2 on the live instance" >> "$OFFICE_LOCAL/release-work/runs/$RUN/status.txt"
'''
FAKE_POST = r'''#!/bin/bash
OFFICE_LOCAL="${CALIBRAYTAI_OFFICE_LOCAL}"; RUN=""
while [ $# -gt 0 ]; do case "$1" in --run) RUN=$2;; esac; shift 2; done
echo "post $RUN" >> "$OFFICE_LOCAL/calls"
if [ -f "$OFFICE_LOCAL/post-fails-once" ]; then rm "$OFFICE_LOCAL/post-fails-once"; echo "STOP: Cal styles are not served"; exit 1; fi
D="$OFFICE_LOCAL/release-work/runs/$RUN"; mkdir -p "$D/post"
echo "RELEASED now run=$RUN" >> "$D/status.txt"; echo done > "$D/RELEASED"
'''


class Release:
    """A candidate commit whose tools/release holds the real release.sh and stand-ins for the three scripts it runs."""

    def __init__(self, tmp_path: Path, release_text: str = None):
        self.tmp = tmp_path
        self.gen = _gen(tmp_path)
        self.env = _env(tmp_path)
        block = _block()
        files = {"tools/release/release.sh": TOOL.read_text() if release_text is None else release_text,
                 "tools/release/release_gate.sh": FAKE_GATE.replace("@@BLOCK@@\n", block),
                 "tools/release/release_migrate.sh": FAKE_MIGRATE,
                 "tools/release/postrelease_check.sh": FAKE_POST}
        self.origin, self.work, self.base, self.sha = _origin(tmp_path, files, self.env)
        self.env["PATH"] = f"{_stubs(tmp_path, self.origin)}:{self.env['PATH']}"
        (tmp_path / "live").write_text(self.base)

    def args(self, *extra):
        return ["bash", str(TOOL), "--label", "vd2", "--candidate", self.sha, "--branch", "cand",
                "--main-base", self.base, "--live-base", self.base, "--live-deploy", "dep-x",
                "--poll-seconds", "1", *extra]

    def run(self, *extra, stdin="", timeout=120):
        return subprocess.run(self.args(*extra), capture_output=True, text=True, env=self.env, input=stdin,
                              timeout=timeout)

    def push_and_deploy(self):
        """What Claude does after Joel's authorization (never the script)."""
        _git(self.work, "push", "-q", str(self.origin), "cand:main", env=self.env)
        (self.tmp / "live").write_text(self.sha)

    def calls(self):
        f = self.tmp / "office" / "calls"
        return f.read_text().splitlines() if f.exists() else []

    def runs(self):
        return sorted(p.name for p in (self.gen / "runs").iterdir()) if (self.gen / "runs").exists() else []


def test_release_runs_the_gate_waits_for_claude_then_checks_and_reports_released(tmp_path):
    rel = Release(tmp_path)
    proc = subprocess.Popen(rel.args(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=rel.env)
    seen = []
    for line in proc.stdout:
        seen.append(line)
        if line.startswith("This window waits"):
            break
    block = "".join(seen)
    assert "SEND THIS TO CLAUDE" in block and f"commit    {rel.sha}" in block
    (run_id,) = rel.runs()
    assert f"run       {run_id}" in block and "database  no migration" in block
    assert "Production needs your authorization" in block
    time.sleep(2)
    assert proc.poll() is None  # still waiting: nothing happens until main and live are the commit
    rel.push_and_deploy()
    rest, _ = proc.communicate(timeout=60)
    assert proc.returncode == 0, block + rest
    assert "==================== RELEASED ====================" in rest
    assert rel.calls() == [f"gate {run_id}", f"post {run_id}"]
    status = (rel.gen / "runs" / run_id / "status.txt").read_text()
    assert f"PUSHED_AND_LIVE commit={rel.sha}" in status
    # The candidate's scripts were used from a sealed copy of that exact commit.
    assert _sh(tmp_path, f'rr_verify "{rel.gen}/tools/{rel.sha}"\n').returncode == 0
    again = rel.run()
    assert again.returncode == 0 and f"already released as run {run_id}" in again.stdout
    assert rel.calls() == [f"gate {run_id}", f"post {run_id}"]


def test_release_resumes_the_same_run_after_an_interruption_without_a_second_gate_or_backup(tmp_path):
    rel = Release(tmp_path)
    first = rel.run("--wait-minutes", "0")
    assert first.returncode == 1 and "still waiting after 0 min" in first.stdout
    (run_id,) = rel.runs()
    assert f"Run {run_id} is kept: run the same command again" in first.stdout
    rel.push_and_deploy()
    resumed = rel.run()
    assert resumed.returncode == 0, resumed.stdout
    assert f"== Resuming run {run_id}" in resumed.stdout and "not repeated" in resumed.stdout
    assert rel.runs() == [run_id]
    assert rel.calls() == [f"gate {run_id}", f"post {run_id}"]  # one gate run, so one backup


def test_release_with_a_migration_waits_for_the_typed_phrase_and_never_migrates_twice(tmp_path):
    rel = Release(tmp_path)
    mig = ("--migration-to", "m2m2m2m2m2m2", "--new-tables", "t_new")
    rel.push_and_deploy()  # already pushed and deployed when the gate passes: no waiting
    wrong = rel.run(*mig, stdin="yes\n")
    (run_id,) = rel.runs()
    assert wrong.returncode == 1 and "the confirmation phrase was not typed (got 'yes'); nothing was migrated" in wrong.stdout
    assert "MIGRATE vd2 m2m2m2m2m2m2" in wrong.stdout and "database  migration r1 -> m2m2m2m2m2m2" in wrong.stdout
    assert rel.calls() == [f"gate {run_id}"]
    no_input = rel.run(*mig)  # nobody typed anything (end of input)
    assert no_input.returncode == 1 and "nothing was migrated" in no_input.stdout
    (tmp_path / "office" / "post-fails-once").write_text("x")
    typed = rel.run(*mig, stdin="MIGRATE vd2 m2m2m2m2m2m2\n")
    assert typed.returncode == 1 and "postrelease_check.sh stopped" in typed.stdout
    assert rel.calls() == [f"gate {run_id}", f"migrate {run_id}", f"post {run_id}"]
    status = (rel.gen / "runs" / run_id / "status.txt").read_text()
    assert "MIGRATION_CONFIRMED by typed phrase" in status
    done = rel.run(*mig)  # resumes: the migration is recorded, so it is not run (or backed up) again
    assert done.returncode == 0, done.stdout
    assert "already recorded for run" in done.stdout and "no second backup" in done.stdout
    assert rel.calls() == [f"gate {run_id}", f"migrate {run_id}", f"post {run_id}", f"post {run_id}"]
    assert rel.runs() == [run_id]


def test_release_never_displaces_a_passed_run_and_refuses_a_changed_declaration(tmp_path):
    rel = Release(tmp_path)
    first = rel.run("--wait-minutes", "0")
    (run_id,) = rel.runs()
    before = _snapshot(rel.gen / "runs" / run_id / "gate")
    changed = rel.run("--wait-minutes", "0", "--migration-to", "m2m2m2m2m2m2", "--new-tables", "t_new")
    assert changed.returncode == 1 and "was gated with MIGRATION_TO=''" in changed.stdout and "--new-run" in changed.stdout
    assert rel.calls() == [f"gate {run_id}"]
    fresh = rel.run("--wait-minutes", "0", "--new-run")
    assert f"run {run_id} stays as it is (never displaced)" in fresh.stdout
    runs = rel.runs()
    assert len(runs) == 2 and runs[0] == run_id
    assert _snapshot(rel.gen / "runs" / run_id / "gate") == before
    # A failing gate ends STOPPED with the gate's own reason and leaves the passed runs alone.
    (tmp_path / "office" / "gate-fails").write_text("x")
    failed = rel.run("--new-run")
    assert failed.returncode == 1 and "the gate did not reach READY_FOR_PUSH: browser checks failed" in failed.stdout
    assert "==================== STOPPED ====================" in failed.stdout
    assert _snapshot(rel.gen / "runs" / run_id / "gate") == before
    assert first.returncode == 1


def test_release_sh_must_be_the_candidates_own_copy_and_never_pushes_or_deploys(tmp_path):
    rel = Release(tmp_path, release_text=TOOL.read_text() + "# a different copy\n")
    r = rel.run()
    assert r.returncode == 1 and "is not the candidate's own" in r.stdout and rel.calls() == []
    code = _code(TOOL)
    assert not re.search(r"\bgit\s+(-C\s+\S+\s+)?push\b", code)
    assert "trigger_deploy" not in code and "api.render.com" not in code and "render deploys" not in code
    usage = subprocess.run(["bash", str(TOOL)], capture_output=True, text=True)
    assert usage.returncode == 2
    bad = subprocess.run(["bash", str(TOOL), "--label", "x", "--candidate", "abc", "--branch", "b", "--main-base", A,
                          "--live-base", A, "--live-deploy", "d"], capture_output=True, text=True)
    assert bad.returncode == 2 and "full 40-character commit SHA" in bad.stdout


def test_release_list_shows_every_run_and_its_outcome(tmp_path):
    _make_run(tmp_path, "vd1", "vd1-20261103-090000", ready=A)
    _make_run(tmp_path, "vd1", "vd1-20261103-100000", stopped="x")
    r = subprocess.run(["bash", str(TOOL), "--label", "vd1", "--list"], capture_output=True, text=True,
                       env=_env(tmp_path))
    assert r.returncode == 0
    assert f"vd1-20261103-090000 READY_FOR_PUSH {A}" in r.stdout and "vd1-20261103-100000 STOPPED" in r.stdout


@pytest.mark.parametrize("script", [GATE, POST, MIGRATE, TOOL], ids=lambda p: p.name)
def test_every_release_script_keeps_its_files_outside_the_icloud_desktop(script):
    code = _code(script)
    assert '"$OFFICE_LOCAL/release-work"' in code
    assert "/Desktop" not in code and "Desktop/" not in code
