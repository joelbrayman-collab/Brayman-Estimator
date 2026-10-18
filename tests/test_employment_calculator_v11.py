"""Employment vs Entrepreneurship 1.1 (Joel's decision 5, 14 Oct 2026).

Valid entries give exactly the original page's results; blank, non-numeric and
negative entries show a message instead of being read as zero. Runs both files
in Chromium side by side.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "calculation-engines" / "employment-vs-entrepreneurship"
ORIGINAL = ROOT / "website-source" / "public" / "employment-vs-entrepreneurship" / "index.html"
V11 = ROOT / "v1.1" / "index.html"
OUTPUTS = ["lBill", "lAnnual", "lRev", "lOwner", "lCost", "lPayroll", "lTotalCost", "lCostRev", "cur", "biz", "delta",
           "curHr", "bizHr", "hourDelta", "cash", "benefits", "curHours", "revenue", "allCosts", "bizHours", "beRate",
           "tBill", "tWeeks", "tUtil", "rateMsg", "sum1", "sum2"]

# A required test dependency (requirements-dev.txt). If it is missing the run fails
# here; it is not skipped (technical cleanup, 18 Oct 2026).
import playwright.sync_api as playwright  # noqa: E402


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _results(page, entries, model=None, trade=None, costs=None):
    return page.evaluate(
        """([entries, model, trade, costs, outputs]) => {
            for (const [id, v] of Object.entries(entries)) document.getElementById(id).value = v;
            if (costs) document.querySelectorAll('[data-cost]').forEach((el, i) => { if (costs[i] !== undefined) el.value = costs[i]; });
            if (model) model_set(model);
            if (trade) trade_set(trade);
            calc();
            return Object.fromEntries(outputs.map(id => [id, (document.getElementById(id) || {}).textContent || '']));
        }""".replace("model_set(model)", "model = model").replace("trade_set(trade)", "trade = trade"),
        [entries, model, trade, costs, OUTPUTS],
    )


def _open(browser, path):
    page = browser.new_page()
    page.goto(path.as_uri())
    return page


VALID_SETS = [
    ({}, None, None, None),
    ({"wage": "60", "site": "35", "util": "70", "rate": "120", "weeks": "44"}, None, None, None),
    ({"helper": "yes", "hw": "28", "hh": "30", "burden": "20"}, "Helper", "Electrical", None),
    ({"wage": "0", "tb": "0", "fb": "0", "ob": "0"}, None, "Plumbing", None),
    ({"weeks": "60", "util": "130"}, None, None, ["15000", "9000", "1000"]),
]


@pytest.mark.parametrize("entries, model, trade, costs", VALID_SETS)
def test_valid_entries_give_exactly_the_original_results(browser, entries, model, trade, costs):
    original, corrected = _open(browser, ORIGINAL), _open(browser, V11)
    expected = _results(original, entries, model, trade, costs)
    actual = _results(corrected, entries, model, trade, costs)
    assert actual == expected
    assert corrected.locator("#inputError").is_hidden()
    original.close(); corrected.close()


@pytest.mark.parametrize("field, value", [("wage", ""), ("site", "-5"), ("rate", ""), ("weeks", "-1")])
def test_a_blank_or_negative_number_is_refused_with_a_message(browser, field, value):
    page = _open(browser, V11)
    before = _results(page, {})
    after = _results(page, {field: value})
    assert after == before  # the last valid results stay; nothing is read as zero
    message = page.locator("#inputError")
    assert message.is_visible() and "number of 0 or more" in message.text_content()
    assert page.locator(f"#{field}").get_attribute("aria-invalid") == "true"
    fixed = _results(page, {field: "41"})
    assert message.is_hidden() and page.locator(f"#{field}").get_attribute("aria-invalid") is None
    assert fixed == _results(_open(browser, ORIGINAL), {field: "41"})
    page.close()


def test_a_text_annual_cost_is_refused(browser):
    page = _open(browser, V11)
    before = _results(page, {})
    after = _results(page, {}, costs=["abc"])
    assert after == before and page.locator("#inputError").is_visible()
    page.close()


def test_a_typed_letter_in_a_number_box_is_refused(browser):
    page = _open(browser, V11)
    page.locator("#wage").fill("")
    page.locator("#wage").press_sequentially("abc")
    page.evaluate("calc()")
    assert page.locator("#inputError").is_visible()
    page.close()


def test_the_original_file_is_unchanged_and_still_reads_bad_entries_as_zero(browser):
    import hashlib

    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == "41f449de2a148a4f26b89cf52d6e878052a97d61e341f8a3fac8b5586e5fa295"
    page = _open(browser, ORIGINAL)
    assert _results(page, {"wage": ""})["cash"] != _results(page, {"wage": "45"})["cash"]
    page.close()
