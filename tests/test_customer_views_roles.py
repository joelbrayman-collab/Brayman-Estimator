"""Customer views found in the roles and isolation walk (tools/release/evidence_roles.mjs, 20 Oct 2026).

1. Security: the notes the platform writes on an estimate line to record where a cost or quantity came from
   ("Approved contractor cost #7; quantity confirmed by ...", and the calculator hand-offs' provenance) were
   copied onto the proposal and shown to the customer on the proposal link and its PDF. They are office
   provenance and must never reach the customer; a note a person typed is kept.
(The PRO Desk quotation link's missing CSRF token, from the same walk: tests/test_pro_desk_customer_csrf.py.)

Synthetic data only.
"""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO

from pypdf import PdfReader

from app import db
from app.models import CostItem
from app.models.estimate import EstimateSection
from app.models.proposal import ProposalLineItem, customer_line_note
from app.services import proposal_acceptance as PA
from app.services.estimate_builder import add_cost_item_line
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.proposal_issue_support import approve_for_issue
from tests.test_proposal_client_acceptance import CLIENT, _version, app, client  # noqa: F401

APPROVED_COST_NOTE = "Approved contractor cost #7; quantity confirmed by Ben Synthetic."
TYPED_NOTE = "Includes two coats of stain on the railing."


def _provenance_notes():
    """The provenance notes as the hand-offs themselves write them (so a format change is caught here)."""
    from app.services import deck_framing_handoff, estimating_handoff, foundation_handoff

    line = {"scope": "deck", "element": "joist", "quantity": "12", "unit": "ea", "canonical_material_code": "LUM-2X8-12",
            "quantity_meaning": "member_count", "provenance": {"member_ids": ["J1", "J2"], "source_element_id": "E1",
                                                               "rule": "joist-spacing-16"}}
    notes = [estimating_handoff.requirement_note(line, 5),
             estimating_handoff.requirement_note({**line, "conversion": {"rule": "stock-12", "factor": "1"},
                                                  "construction_quantity": "144", "construction_unit": "ft"}, 5),
             foundation_handoff.requirement_note(line, 5),
             deck_framing_handoff.requirement_note(line)]
    return notes


def test_platform_provenance_notes_are_not_customer_wording():
    for note in [APPROVED_COST_NOTE, *_provenance_notes()]:
        assert customer_line_note(note) is None, note
    assert customer_line_note(TYPED_NOTE) == TYPED_NOTE
    assert customer_line_note("Rule of thumb; quantity as discussed on site") == "Rule of thumb; quantity as discussed on site"
    assert customer_line_note("  ") is None and customer_line_note(None) is None


def _version_with_notes(number):
    project, version = _version(number)
    item = CostItem(organization_id=DEFAULT_ORGANIZATION_ID, code=f"INT-{number}", name="Internal crew allowance",
                    category="Labour", unit="ls", unit_cost=Decimal("800.00"), default_markup_percent=Decimal("25"))
    db.session.add(item)
    section = EstimateSection(estimate_version_id=version.id, name="Deck", sort_order=1, subtotal=Decimal("0"))
    db.session.add(section)
    db.session.commit()
    for note, description in ((APPROVED_COST_NOTE, "Deck framing"), (_provenance_notes()[0], "Joists"),
                              (TYPED_NOTE, "Railing")):
        line = add_cost_item_line(section, cost_item_id=item.id, quantity=1, notes=note,
                                  organization_id=DEFAULT_ORGANIZATION_ID)
        line.description = description
    db.session.commit()
    approve_for_issue(version)
    return project, version


def _pdf_text(data: bytes) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)


def test_the_customer_never_sees_the_platform_provenance_notes(app, client):  # noqa: F811
    from tests.auth_fixtures import ensure_office_user

    user = ensure_office_user(); db.session.commit()
    _project, version = _version_with_notes("EST-NOTES-1")
    proposal = PA.sign_off_estimate(version, user=user)
    stored = [line.notes for section in proposal.sections for line in section.line_items]
    assert APPROVED_COST_NOTE not in stored and TYPED_NOTE in stored  # not copied onto the proposal
    sent = PA.send_proposal_to_client(proposal, user=user, client_name=CLIENT[0], client_email=CLIENT[1])
    public = app.test_client()
    page = public.get(sent.path).get_data(as_text=True)
    pdf = _pdf_text(public.get(sent.path + "/pdf").data)
    for shown in (page, pdf):
        assert "Approved contractor cost" not in shown
        assert "canonical LUM-2X8-12" not in shown and "joist-spacing-16" not in shown
        assert TYPED_NOTE in shown  # what a person wrote for the customer still shows


def test_a_proposal_made_before_the_fix_hides_the_note_on_its_link_and_pdf(app, client):  # noqa: F811
    from tests.auth_fixtures import ensure_office_user

    user = ensure_office_user(); db.session.commit()
    _project, version = _version_with_notes("EST-NOTES-2")
    proposal = PA.sign_off_estimate(version, user=user)
    # As an earlier proposal was stored: the provenance note copied onto its line.
    line = ProposalLineItem.query.filter_by(description="Deck framing").filter(
        ProposalLineItem.proposal_section_id.in_([s.id for s in proposal.sections])).one()
    line.notes = APPROVED_COST_NOTE
    db.session.commit()
    sent = PA.send_proposal_to_client(proposal, user=user, client_name=CLIENT[0], client_email=CLIENT[1])
    public = app.test_client()
    assert "Approved contractor cost" not in public.get(sent.path).get_data(as_text=True)
    assert "Approved contractor cost" not in _pdf_text(public.get(sent.path + "/pdf").data)
    # The fingerprint the customer accepts does not include notes, so it is unchanged by hiding one.
    assert PA.proposal_content_sha256(proposal) == PA.proposal_content_sha256(db.session.get(PA.Proposal, proposal.id))
