"""A new proposal template starts from the company's current brand profile (defect 5, 21 Oct 2026).

Synthetic data only. The form used to pre-fill a fixed "Brayman Construction Co." whatever the
brand profile said.
"""

from __future__ import annotations

import re

from app import db
from app.services.brand_profile import save_brand_profile
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.test_brand_profile_fg017 import app, client  # noqa: F401


def _value(html, name):
    match = re.search(rf'name="{name}" value="([^"]*)"', html)
    assert match is not None, name
    return match.group(1)


def test_new_template_form_prefills_the_current_brand_profile(app, client):
    save_brand_profile(DEFAULT_ORGANIZATION_ID, legal_name="Brayman Construction Inc. (synthetic)",
                       customer_facing_name="Brayman Construction", address="1 Synthetic Road, Merrickville, ON",
                       phone="613-555-0100", email="office@brayman.example.invalid",
                       website="brayman.example.invalid", actor="test")
    db.session.commit()
    html = client.get("/proposal-templates/new").get_data(as_text=True)
    assert "Brayman Construction Co." not in html
    assert _value(html, "company_name") == "Brayman Construction"
    assert _value(html, "company_address") == "1 Synthetic Road, Merrickville, ON"
    assert _value(html, "company_phone") == "613-555-0100"
    assert _value(html, "company_email") == "office@brayman.example.invalid"
    assert _value(html, "company_website") == "brayman.example.invalid"

    # A later brand change is what the next new template starts from.
    save_brand_profile(DEFAULT_ORGANIZATION_ID, legal_name="Brayman Construction Inc. (synthetic)",
                       customer_facing_name="Brayman Builders (synthetic)", actor="test")
    db.session.commit()
    html = client.get("/proposal-templates/new").get_data(as_text=True)
    assert _value(html, "company_name") == "Brayman Builders (synthetic)"
