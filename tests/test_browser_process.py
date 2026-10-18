"""A browser-test timeout must not leave a detached child running."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest

from tests.browser_process import process_is_running, run_node_browser_test, wait_until_stopped

DETACHED_CHILD = textwrap.dedent(
    """
    import os
    import time
    pid = os.fork()
    if pid == 0:
        os.setsid()
        time.sleep(30)
        raise SystemExit(0)
    print(pid, flush=True)
    time.sleep(30)
    """
)


def test_a_timeout_kills_a_detached_child():
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        run_node_browser_test(
            [sys.executable, "-c", DETACHED_CHILD],
            cwd=os.getcwd(),
            timeout=1,
        )
    child_pid = int(caught.value.output.strip())
    assert wait_until_stopped(child_pid, timeout=5), f"detached child {child_pid} is still running"
    assert not process_is_running(child_pid)


def test_a_live_process_is_reported_running_until_it_is_killed():
    """The running check must not pass vacuously: a live child reads as running,
    and as stopped only after it is killed."""
    sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        assert process_is_running(sleeper.pid)
        assert not wait_until_stopped(sleeper.pid, timeout=0.3)
    finally:
        sleeper.kill()
    assert wait_until_stopped(sleeper.pid, timeout=5)
    sleeper.wait(timeout=5)
    with pytest.raises(ProcessLookupError):
        os.kill(sleeper.pid, 0)
