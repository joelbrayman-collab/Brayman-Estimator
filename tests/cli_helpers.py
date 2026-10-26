"""Run a Flask command against one specific test app.

Flask's command runner uses whatever app context is already active, and only builds the test's own app when none
is. Some older tests leave an app context open, so in a complete regression run a bare
``app.test_cli_runner().invoke(...)`` can run against another (empty, default-config) app. ``cli_runner(app)``
pushes the test's own app context for each command so the command always sees that site's database and settings.
"""
from __future__ import annotations


class _AppCliRunner:
    def __init__(self, app):
        self.app = app

    def invoke(self, *args, **kwargs):
        with self.app.app_context():
            return self.app.test_cli_runner().invoke(*args, **kwargs)


def cli_runner(app) -> _AppCliRunner:
    return _AppCliRunner(app)
