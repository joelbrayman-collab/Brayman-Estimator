"""Tests must not depend on today's real date (22 Nov 2026).

Gate run ai9 failed on three tests that had passed on 18 Nov: proposal links set to expire on a fixed date (20 Nov) were
expired by 22 Nov, and a calendar feed that looks 60 days back from the real date lost an appointment fixed at 21 Sep.
A link expiry in a test is a day computed from today; a feed test pins the feed's own "today"."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_test_sets_a_link_expiry_to_a_fixed_calendar_date():
    offenders = []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        for number, line in enumerate(path.read_text(encoding="utf8").splitlines(), 1):
            if re.search(r"expires_at\s*=\s*datetime\(\s*20\d\d", line):
                offenders.append(f"{path.name}:{number}")
    assert not offenders, offenders


def test_the_calendar_feed_test_pins_the_feed_clock():
    text = (ROOT / "tests" / "test_calendar_sync.py").read_text(encoding="utf8")
    assert 'monkeypatch.setattr("app.services.appointments.local_today"' in text
