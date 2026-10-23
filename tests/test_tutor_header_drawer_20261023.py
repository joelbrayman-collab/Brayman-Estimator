"""Training Tutor in the header (23 Oct 2026): lessons use the whole page; the Tutor opens as a drawer that scrolls on its own."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "app" / "templates" / "training" / "_tutor.html").read_text()
CSS = (ROOT / "app" / "static" / "training" / "training.css").read_text()
JS = (ROOT / "app" / "static" / "training" / "training.js").read_text()


def test_a_header_launcher_exists_and_starts_closed():
    assert "data-tutor-launch" in TEMPLATE and 'aria-expanded="false"' in TEMPLATE
    assert 'aria-controls="tutor"' in TEMPLATE and "ask-the-tutor-calibraytai-48.png" in TEMPLATE
    assert "is-open" not in TEMPLATE  # the drawer is closed until the trainee opens it


def test_the_existing_tutor_hooks_and_calls_are_unchanged():
    for hook in ("data-tutor-toggle", "data-tutor-button", "data-tutor-ask", "data-tutor-quick", 'name="csrf_token"',
                 "url_for('training.tutor_state')", "url_for('training.tutor_ask')", 'aria-label="Training Tutor"'):
        assert hook in TEMPLATE, hook


def test_the_drawer_scrolls_on_its_own_and_is_full_screen_on_a_phone():
    flat = CSS.replace(" ", "")
    assert ".tc-js.tc-tutor{position:fixed" in flat and "overflow-y:auto" in flat
    assert ".tc-js.tc-layout{grid-template-columns:minmax(0,1fr)" in flat  # lessons use the whole page
    assert "width:100vw" in flat and "(max-width:600px)" in flat
    assert "prefers-reduced-motion" in CSS


def test_keyboard_escape_and_focus_return():
    assert '"Escape"' in JS and "launch.focus()" in JS and "aria-expanded" in JS
    assert 'classList.add("tc-js")' in JS
