"""password-reveal.js keeps the focus and the cursor of a field it moves (6 Nov 2026).

The script wraps each password field in a span (for the Show password button). Moving a focused field takes the focus
from it, so on a slow page someone who had started typing lost the keys typed next; the release walk's sign-in (fill:
focus, then type) lost the whole password the same way and was refused. These tests run the real script in Chromium
while the field is focused and typed in, exactly between the focus and the typing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "app" / "static" / "js" / "password-reveal.js").read_text()
PAGE = """<!doctype html><form><input id="email" name="email">
<input id="password" type="password" name="password" data-password-reveal>
<button type="submit">Sign in</button></form>"""


@pytest.fixture(scope="module")
def page():
    from playwright.sync_api import sync_playwright  # requirements-dev.txt; never skipped

    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page()
        yield pg
        browser.close()


def test_typing_continues_into_the_field_when_the_script_runs_between_focus_and_typing(page):
    for attempt in range(5):
        page.set_content(PAGE)
        page.focus("#password")
        page.evaluate(SCRIPT)  # the script arrives late, after the focus and before the typing
        page.keyboard.insert_text("Synthetic-secret-1")
        assert page.input_value("#password") == "Synthetic-secret-1", attempt
        assert page.evaluate("document.activeElement.id") == "password"
        assert page.evaluate("document.getElementById('password').parentElement.className") == "password-reveal"


def test_the_cursor_and_selection_are_kept(page):
    page.set_content(PAGE)
    page.fill("#password", "abcdef")
    page.evaluate("var f = document.getElementById('password'); f.focus(); f.setSelectionRange(2, 4);")
    page.evaluate(SCRIPT)
    assert page.evaluate("[document.activeElement.id, document.activeElement.selectionStart,"
                         " document.activeElement.selectionEnd]") == ["password", 2, 4]
    page.keyboard.insert_text("Z")
    assert page.input_value("#password") == "abZef"


def test_a_field_nobody_is_in_is_not_given_the_focus(page):
    page.set_content(PAGE)
    page.focus("#email")
    page.evaluate(SCRIPT)
    assert page.evaluate("document.activeElement.id") == "email"
    assert page.locator("[data-password-reveal-toggle]").count() == 1
