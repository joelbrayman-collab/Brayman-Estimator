"""The client's proposal page shows the proposal's real validity (defect 1, 21 Oct 2026). Synthetic data only.

The link's expiry is what the code enforces (after it the client cannot accept), so "Valid until"
on the client's page and PDF shows that date, or the proposal's own earlier validity date — never "—".
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from io import BytesIO

from pypdf import PdfReader

from app import db
from app.models.proposal_acceptance import ProposalClientLink
from app.services import proposal_acceptance as PA
from tests.test_proposal_client_acceptance import _credential, _sent, app, client  # noqa: F401


def _day_ahead(days=30):
    """A day that is always in the future when the test runs. A fixed date here became a time bomb: the links expired
    on 20 Nov 2026 and gate run ai9 (22 Nov) failed on it. Thirty days keeps the Ottawa and UTC dates the same."""
    return date.today() + timedelta(days=days)


def _words(day):
    return f"{day:%B} {day.day}, {day.year}"


def _valid_until_on_page(html):
    match = re.search(r'data-proposal-valid-until="([^"]*)">([^<]*)<', html)
    assert match is not None, html[:600]
    return match.group(1), match.group(2)


def test_client_page_shows_the_link_expiry_as_valid_until(app, client):
    _user, _project, proposal, sent = _sent("EST-VU-1")
    assert proposal.valid_until is None
    link = db.session.get(ProposalClientLink, sent.link.id)
    day = _day_ahead()
    link.expires_at = datetime.combine(day, time(18, 0))  # 1 p.m. in Ottawa (2 p.m. in summer) that day
    db.session.commit()
    stamp, text = _valid_until_on_page(client.get(sent.path).get_data(as_text=True))
    assert stamp == day.isoformat() and text == _words(day)

    pdf = client.get(sent.path + "/pdf")
    assert pdf.status_code == 200
    pdf_text = "".join(page.extract_text() for page in PdfReader(BytesIO(pdf.data)).pages)
    assert f"Valid until: {_words(day)}" in pdf_text


def test_expiry_late_in_the_evening_is_the_ottawa_date_not_the_utc_date(app, client):
    _user, _project, proposal, sent = _sent("EST-VU-2")
    link = db.session.get(ProposalClientLink, sent.link.id)
    day = _day_ahead()
    link.expires_at = datetime.combine(day + timedelta(days=1), time(2, 30))  # 9:30 or 10:30 p.m. the day before, in Ottawa
    db.session.commit()
    assert PA.client_valid_until(proposal, link) == day


def test_an_earlier_validity_date_stated_on_the_proposal_is_what_the_client_reads(app, client):
    _user, _project, proposal, sent = _sent("EST-VU-3")
    link = db.session.get(ProposalClientLink, sent.link.id)
    link.expires_at = datetime.combine(_day_ahead(), time(18, 0))
    proposal.valid_until = _day_ahead(10)  # earlier than the link
    db.session.commit()
    stamp, _text = _valid_until_on_page(client.get(sent.path).get_data(as_text=True))
    assert stamp == _day_ahead(10).isoformat()
