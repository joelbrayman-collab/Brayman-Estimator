"""Browser-test page servers clean up their temporary files when they stop (faster gate, 2 Nov 2026).

Each page server (tests/*_server.py, tests/identity_pair_site.py) is started by a Node browser test and stopped
with SIGTERM. Before this, every server left its SQLite database, work folder and test-app folders in the system
temporary folder. ``install()`` gives the server process one private temporary folder (every ``tempfile`` call in
the process lands inside it), removes it at exit, and turns SIGTERM into a normal exit so that cleanup runs.
A server killed with SIGKILL (a browser test that timed out) cannot clean up; the folder is then named
``calibai-page-server-*`` so it is easy to find.
"""

from __future__ import annotations

import atexit
import shutil
import signal
import sys
import tempfile


def _exit_on_signal(signum, frame):  # noqa: ARG001 - signal handler signature
    sys.exit(0)


def install() -> str:
    private = tempfile.mkdtemp(prefix="calibai-page-server-")
    tempfile.tempdir = private
    atexit.register(shutil.rmtree, private, True)
    signal.signal(signal.SIGTERM, _exit_on_signal)
    return private
