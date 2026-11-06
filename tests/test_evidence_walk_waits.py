"""Release browser walks wait for the state they mean (6 Nov 2026 root causes of two gate-run failures).

1. evidence_training.mjs signIn clicked "I work for a contractor" inside ``Promise.all([waitForLoadState(), click])``.
   waitForLoadState() resolved at once, on the Training Centre page that was already loaded, so the walk typed into
   the sign-in form while that page's own scripts were still running. password-reveal.js moves the password field into
   a wrapper, which drops its focus; Playwright's fill is "focus the field, then type into whatever is focused", so the
   password was lost and the site answered "Invalid email or password" on /login.
2. evidence_magnificent_seven.mjs waited for ``data-state=needs_retry`` after the second interruption, but that state
   was still showing from the first one, so the wait returned at once and the next "online" could arrive while the
   retry was still sending (the phone runs one retry at a time and ignored it).

These checks read the walks; they run no browser.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WALKS = sorted([*(ROOT / "tools" / "release").glob("evidence_*.mjs"), *(ROOT / "tests").glob("*.mjs"),
                *(ROOT / "tests" / "e2e").glob("*.mjs"), *(ROOT / "tools" / "training").glob("*.mjs")])
SIGN_IN_FILL = re.compile(r"""fill\(\s*["'`][^"'`]*(name=email|name=password|#email|#password)""")


def test_no_walk_types_into_a_sign_in_form_reached_by_a_click_it_did_not_wait_for():
    """A click that opens a page, wrapped with waitForLoadState() (which answers for the page already shown), must not
    be followed by typing a sign-in: wait for the new page's URL with waitUntil "load" instead."""
    assert len(WALKS) >= 30
    found = []
    for walk in WALKS:
        lines = walk.read_text().splitlines()
        for number, line in enumerate(lines):
            if "waitForLoadState()," in line and ".click(" in line:
                following = "\n".join(lines[number + 1:number + 4])
                if SIGN_IN_FILL.search(following):
                    found.append(f"{walk.relative_to(ROOT)}:{number + 1}")
    # tests/e2e/contractor_workflow.mjs:89 defines submit(), which is followed by a goto (that waits) and then a fill.
    assert found == ["tests/e2e/contractor_workflow.mjs:89"], found


def test_training_sign_in_waits_for_the_sign_in_page_and_checks_the_password_was_typed():
    text = (ROOT / "tools" / "release" / "evidence_training.mjs").read_text()
    body = text[text.index("async function signIn("):text.index("async function register(")]
    assert 'waitForURL(signInPage, { waitUntil: "load" })' in body
    assert "waitForLoadState()" not in body
    assert body.index("waitForURL(signInPage") < body.index('fill("input[name=email]"')
    assert 'inputValue("input[name=password]"), person.password' in body
    assert "comes back to the Training Centre (${refused})" in body  # a refusal is reported with the site's message


def test_receipt_walk_waits_for_each_retry_it_starts_to_end():
    text = (ROOT / "tools" / "release" / "evidence_magnificent_seven.mjs").read_text()
    start = text.index('step("Add Receipt on the iPhone')
    body = text[start:text.index('await go(pg, "/field/receipt");', start)]
    onlines = [m.start() for m in re.finditer(r'dispatchEvent\(new Event\("online"\)\)', body)]
    assert len(onlines) == 2
    for position, end in zip(onlines, ("needs_retry", "saved")):
        after = body[position:position + 200]
        # The next wait after an "online" is for the retry it started to reach its end, not for a state already shown.
        assert re.match(r'[^\n]*\n(\s*await registerLost;\n)?\s*await retryEnded\(pg, "%s"\);' % end, after), after
    assert 'waitForEvent("requestfailed"' in body and "await trackFeedback(pg);" in body
    helper = text[text.index("async function retryEnded("):text.index("function step(")]
    assert 'seen.indexOf("saving")' in helper and "seen.indexOf(want, started) > started" in helper
