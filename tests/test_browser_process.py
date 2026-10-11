"""A browser-test timeout must not leave a detached child running."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest

from tests.browser_process import run_node_browser_test

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
    with pytest.raises(ProcessLookupError):
        os.kill(child_pid, 0)
