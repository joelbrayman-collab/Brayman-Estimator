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


def run_node_browser_test(args, *, cwd, timeout, env=None):
    """Run Node. On timeout, stop its whole process tree."""
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
        stop_process_tree(process.pid)
        stdout, stderr = process.communicate()
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
