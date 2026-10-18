"""Joel's decision 6 (14 Oct 2026): the five trade calculator pages in a real browser.

Each page is filled in and submitted in Chromium against a running copy of the app,
at desktop width and at a 390 px phone width. Expected figures are worked by hand
in the comments; the page must show them. Standalone use needs no project.
"""

from __future__ import annotations

import threading

import pytest
from werkzeug.serving import make_server

from app import create_app, db
from app.services.organizations import ensure_default_organization
from tests.auth_fixtures import DEFAULT_OFFICE_EMAIL, DEFAULT_OFFICE_PASSWORD, ensure_office_user

# A required test dependency (requirements-dev.txt). If it is missing the run fails
# here; it is not skipped (technical cleanup, 18 Oct 2026).
import playwright.sync_api as playwright  # noqa: E402


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("trade") / "trade.db"
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
                      "SECRET_KEY": "trade-browser", "WTF_CSRF_ENABLED": False})
    with app.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_office_user()
        db.session.commit()
    httpd = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture(params=[(1280, 900), (390, 844)], ids=["desktop", "phone"])
def page(request, browser, server):
    width, height = request.param
    context = browser.new_context(viewport={"width": width, "height": height})
    pg = context.new_page()
    pg.goto(f"{server}/login")
    pg.fill("input[name=email]", DEFAULT_OFFICE_EMAIL)
    pg.fill("input[name=password]", DEFAULT_OFFICE_PASSWORD)
    pg.click("button[type=submit]")
    pg.wait_for_load_state()
    pg.base = server
    pg.width = width
    yield pg
    context.close()


def _fill(pg, values):
    for field, value in values.items():
        if field == "unit_system" or field == "sheet_size":
            pg.select_option(f"#{field}", value)
        else:
            pg.fill(f"#{field}", value)


def _calculate(pg, kind, values):
    pg.goto(f"{pg.base}/calculators/{kind}")
    assert pg.locator(f"[data-trade-form={kind}]").is_visible()
    _fill(pg, values)
    pg.click("button[value=calculate]")
    pg.wait_for_load_state()
    return pg.locator(f"[data-trade-result={kind}]")


def _no_sideways_scroll(pg):
    overflow = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 1, f"page scrolls sideways by {overflow}px at {pg.width}px"


CASES = {
    # 40 × 30 ft plane at 6/12: slope factor √(1 + 0.5²) = 1.1180340; 1200 × 1.1180340 = 1341.64 ft².
    # +10 % = 1475.80 ft² → 1475.80 / 33.3 = 44.3 → 45 bundles; 1475.80 / 400 = 3.69 → 4 rolls.
    "roofing": ({"plane_length_1": "40", "plane_width_1": "30", "plane_pitch_1": "6", "waste_percent": "10",
                 "bundle_coverage": "33.3", "underlayment_coverage": "400"},
                {"[data-roof-area]": "1341.64 ft²", "[data-bundles]": "45 shingle bundles", "[data-rolls]": "4 underlayment rolls"}),
    # Wall 100 × 9 = 900; gable ½ × 24 × 6 = 72; openings 3 × 5 × 4 = 60 → net 912 ft².
    # +10 % = 1003.2 ft² → 1003.2 / 100 = 10.03 → 11 pieces.
    "siding": ({"wall_length_1": "100", "wall_height_1": "9", "gable_base_1": "24", "gable_height_1": "6",
                "opening_width_1": "3", "opening_height_1": "5", "opening_count_1": "4", "waste_percent": "10",
                "piece_coverage": "100"},
               {"[data-net-area]": "912", "[data-pieces]": "11 pieces"}),
    # Wall 40 × 8 = 320; ceiling 12 × 10 = 120; door 3 × 7 = 21 → net 419 ft².
    # +10 % = 460.9 ft² → 460.9 / 32 = 14.4 → 15 sheets of 4 × 8.
    "drywall": ({"wall_length_1": "40", "wall_height_1": "8", "ceiling_length_1": "12", "ceiling_width_1": "10",
                 "opening_width_1": "3", "opening_height_1": "7", "waste_percent": "10", "sheet_size": "4x8"},
                {"[data-net-area]": "419", "[data-sheets]": "15 sheets of 4 × 8 ft"}),
    # 12 × 15 = 180 ft²; +8 % = 194.4 → 194.4 / 20 = 9.72 → 10 boxes; perimeter 2 × (12 + 15) = 54 ft.
    "flooring": ({"room_length_1": "12", "room_width_1": "15", "waste_percent": "8", "box_coverage": "20"},
                 {"[data-floor-area]": "180", "[data-boxes]": "10 boxes", "[data-perimeter]": "54"}),
    # Two footings 20 × 2 ft × 12 in = 40 ft³ each → 80 ft³ = 80 / 27 = 2.963 yd³; +5 % = 84 ft³ = 3.111 yd³.
    "footing": ({"footing_length_1": "20", "footing_width_1": "2", "footing_thickness_1": "12", "footing_count_1": "2",
                 "waste_percent": "5"},
                {"[data-volume]": "2.963 yd³", "[data-order-volume]": "3.111 yd³"}),
}


@pytest.mark.parametrize("kind", list(CASES))
def test_each_page_gives_the_hand_worked_figures(page, kind):
    values, expected = CASES[kind]
    result = _calculate(page, kind, values)
    assert result.is_visible()
    for selector, text in expected.items():
        assert text in result.locator(selector).first.text_content(), (kind, selector)
    assert "not on an estimate" in result.text_content()
    _no_sideways_scroll(page)


def test_metric_footing_and_the_unit_labels_switch(page):
    page.goto(f"{page.base}/calculators/footing")
    label = page.locator("label[for=footing_length_1]")
    assert "feet" in label.inner_text() and "metres" not in label.inner_text()
    page.select_option("#unit_system", "metric")
    assert "metres" in label.inner_text() and "feet" not in label.inner_text()
    assert "millimetres" in page.locator("label[for=footing_thickness_1]").inner_text()
    # 6 m × 0.6 m × 300 mm = 1.08 m³ = 1.08 / 0.764554858 = 1.413 yd³; no waste.
    _fill(page, {"footing_length_1": "6", "footing_width_1": "0.6", "footing_thickness_1": "300", "waste_percent": "0"})
    page.click("button[value=calculate]")
    page.wait_for_load_state()
    volume = page.locator("[data-volume]").text_content()
    assert "1.413 yd³" in volume and "1.080 m³" in volume
    assert page.locator("#unit_system").input_value() == "metric"


@pytest.mark.parametrize("kind, values, message", [
    ("flooring", {"room_length_1": "-12", "room_width_1": "15", "waste_percent": "0"}, "greater than zero"),
    ("drywall", {"wall_length_1": "abc", "wall_height_1": "8", "waste_percent": "0"}, "number"),
    ("roofing", {"plane_length_1": "40", "plane_width_1": "30", "plane_pitch_1": "6"}, "Waste"),
    ("footing", {"waste_percent": "0"}, "at least one footing"),
])
def test_bad_entries_show_a_message_not_a_result(page, kind, values, message):
    page.goto(f"{page.base}/calculators/{kind}")
    _fill(page, values)
    page.click("button[value=calculate]")
    page.wait_for_load_state()
    alert = page.locator("[role=alert]")
    assert alert.is_visible() and message.lower() in alert.text_content().lower()
    assert page.locator(f"[data-trade-result={kind}]").count() == 0
    _no_sideways_scroll(page)
