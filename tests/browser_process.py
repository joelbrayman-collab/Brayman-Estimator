"""Run a Node browser test and stop every process it started.

Python's subprocess timeout kills only the Node pid. Headless Chrome
puts itself in a new process group, and the office server stays attached
to the Node worker. Both survive that kill and are reparented to launchd.
The next browser test then starts beside the leftover Chrome.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time


def _process_table():
    output = subprocess.check_output(["ps", "-axo", "pid=,ppid=,pgid="], text=True)
    table = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        pid, parent, group = (int(part) for part in parts)
        table[pid] = (parent, group)
    return table


def _descendants(root_pid, table):
    children = {}
    for pid, (parent, _group) in table.items():
        children.setdefault(parent, []).append(pid)
    found = []
    stack = list(children.get(root_pid, []))
    while stack:
        pid = stack.pop()
        found.append(pid)
        stack.extend(children.get(pid, []))
    return found


def stop_process_tree(root_pid):
    """Kill the Node worker, Chrome's own process group, and the office server."""
    table = _process_table()
    descendants = _descendants(root_pid, table)
    groups = set()
    if root_pid in table:
        groups.add(table[root_pid][1])
    for pid in descendants:
        groups.add(table[pid][1])
    own_group = os.getpgrp()
    for group in groups:
        if group in (own_group, 0, 1):
            continue
        try:
            os.killpg(group, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    for pid in [root_pid, *descendants]:
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


HERMETIC_PRELOAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hermetic_playwright.mjs")
# --no-proxy-server: a system proxy would resolve names itself and bypass the resolver rule.
HERMETIC_CHROME_ARGS = ["--no-proxy-server", "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost"]


def _host_snapshot(root_pid):
    """What the machine was doing: the busiest processes, the load, and the test's own process tree."""
    def run(cmd):
        try:
            return subprocess.run(cmd, text=True, capture_output=True, check=False, timeout=20).stdout
        except Exception as error:  # a diagnostic must never hide the timeout
            return f"({cmd[0]} failed: {error})\n"
    top = "\n".join(run(["ps", "-Ao", "pid,ppid,etime,pcpu,pmem,stat,comm", "-r"]).splitlines()[:28])
    tree = [line for line in run(["ps", "-Ao", "pid,ppid,pgid,etime,pcpu,stat,command"]).splitlines()
            if line.split()[:1] and (str(root_pid) in line.split()[:3] or "chrome" in line.lower()
                                     or "playwright" in line.lower())][:40]
    return f"uptime: {run(['uptime']).strip()}\n--- busiest processes ---\n{top}\n--- the test's process tree and any Chrome ---\n" + "\n".join(line[:220] for line in tree)


def run_node_browser_test(args, *, cwd, timeout, env=None):
    """Run Node. On timeout, stop its whole process tree.

    Every browser the test launches is hermetic: hosts other than the local one fail to resolve at once, so a slow
    public network (Google Fonts and jsDelivr are linked from every page) cannot stall a walk (17 Nov 2026).

    A Node run also logs every Playwright call (DEBUG=pw:api). If the run times out, the busiest processes, the load and
    the last Playwright calls are written to the test's output and to a file, so a hung walk says what it was waiting on
    (three walks timed out on 17-18 Nov 2026 with nothing to show which step hung)."""
    is_node = os.path.basename(str(args[0])).startswith("node")
    if is_node:
        args = [args[0], "--import", HERMETIC_PRELOAD, *args[1:]]
        env = dict(os.environ if env is None else env)
        env["DEBUG"] = ",".join(filter(None, [env.get("DEBUG", ""), "pw:api"]))
    process = subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        snapshot = _host_snapshot(process.pid) if is_node else ""
        stop_process_tree(process.pid)
        stdout, stderr = process.communicate()
        if is_node:
            report = (f"BROWSER TEST TIMED OUT after {timeout}s: {' '.join(str(a) for a in args[-1:])}\n{snapshot}\n"
                      f"--- last 60 Playwright/Node stderr lines ---\n" + "\n".join((stderr or "").splitlines()[-60:])
                      + "\n--- last 15 stdout lines ---\n" + "\n".join((stdout or "").splitlines()[-15:]) + "\n")
            try:
                path = os.path.join(tempfile.gettempdir(), f"browser-timeout-{os.getpid()}-{int(time.time())}.txt")
                with open(path, "w", encoding="utf8") as handle:
                    handle.write(report)
                report += f"(also saved to {path})\n"
            except OSError:
                pass
            sys.stderr.write(report)
        raise subprocess.TimeoutExpired(
            process.args,
            timeout,
            output=stdout,
            stderr=stderr,
        ) from exc
    return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)


def process_is_running(pid):
    """True while ``pid`` is alive. A killed process that its parent has not yet
    collected (state Z, a zombie) has stopped running. Containers whose first
    process does not collect orphans leave such zombies indefinitely, and
    ``os.kill(pid, 0)`` still succeeds on them."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    state = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)],
        text=True,
        capture_output=True,
        check=False,
    ).stdout.strip()
    if not state:
        return False
    return not state.startswith("Z")


def wait_until_stopped(pid, *, timeout=5.0, interval=0.05):
    """Poll until ``pid`` is no longer running, for at most ``timeout`` seconds.
    SIGKILL is delivered asynchronously, so a check made the instant after the
    kill can still see the process. Returns True once stopped, False on timeout."""
    deadline = time.monotonic() + timeout
    while True:
        if not process_is_running(pid):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(interval)
