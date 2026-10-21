"""The client's proposal page shows the proposal's real validity (defect 1, 21 Oct 2026). Synthetic data only.

The link's expiry is what the code enforces (after it the client cannot accept), so "Valid until"
on the client's page and PDF shows that date, or the proposal's own earlier validity date — never "—".
"""

from __future__ import annotations

import re
from datetime import date, datetime
from io import BytesIO

from pypdf import PdfReader

from app import db
from app.models.proposal_acceptance import ProposalClientLink
from app.services import proposal_acceptance as PA
from tests.test_proposal_client_acceptance import _credential, _sent, app, client  # noqa: F401


def _valid_until_on_page(html):
    match = re.search(r'data-proposal-valid-until="([^"]*)">([^<]*)<', html)
    assert match is not None, html[:600]
    return match.group(1), match.group(2)


def test_client_page_shows_the_link_expiry_as_valid_until(app, client):
    _user, _project, proposal, sent = _sent("EST-VU-1")
    assert proposal.valid_until is None
    link = db.session.get(ProposalClientLink, sent.link.id)
    link.expires_at = datetime(2026, 11, 20, 18, 0)  # 1 p.m. in Ottawa on Nov 20
    db.session.commit()
    stamp, text = _valid_until_on_page(client.get(sent.path).get_data(as_text=True))
    assert stamp == "2026-11-20" and text == "November 20, 2026"

    pdf = client.get(sent.path + "/pdf")
    assert pdf.status_code == 200
    pdf_text = "".join(page.extract_text() for page in PdfReader(BytesIO(pdf.data)).pages)
    assert "Valid until: November 20, 2026" in pdf_text


def test_expiry_late_in_the_evening_is_the_ottawa_date_not_the_utc_date(app, client):
    _user, _project, proposal, sent = _sent("EST-VU-2")
    link = db.session.get(ProposalClientLink, sent.link.id)
    link.expires_at = datetime(2026, 11, 21, 2, 30)  # 9:30 p.m. Nov 20 in Ottawa
    db.session.commit()
    assert PA.client_valid_until(proposal, link) == date(2026, 11, 20)


def test_an_earlier_validity_date_stated_on_the_proposal_is_what_the_client_reads(app, client):
    _user, _project, proposal, sent = _sent("EST-VU-3")
    link = db.session.get(ProposalClientLink, sent.link.id)
    link.expires_at = datetime(2026, 11, 20, 18, 0)
    proposal.valid_until = date(2026, 11, 5)
    db.session.commit()
    stamp, _text = _valid_until_on_page(client.get(sent.path).get_data(as_text=True))
    assert stamp == "2026-11-05"
