"""Construction drawings inside CalibraytAI, on a synthetic copy of Linda Bushel J1.

Generate from the stored construction model → preview → PDF and DXF →
Project Plans → attach the same revision to an estimate version, a proposal
and the BMR supplier request. Sets are write-once, outdated sets cannot be
attached, newer attachments supersede older ones, and another project or
organization cannot reach them.
"""

from __future__ import annotations

import io
from datetime import date

import pytest
from ezdxf import recover
from pypdf import PdfReader

from app import db
from app.models import Organization, Proposal
from app.models.construction_drawing import ConstructionDrawingAttachment, ConstructionDrawingSet
from app.models.estimate import EstimateVersion
from app.plan_intelligence.models import PlanDocument
from app.services import construction_drawings as drawings
from app.services.deck_takeoff.intake import read_response_pdf
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.project_construction_model import save_construction_model_revision
from app.services.proposals import create_proposal, create_proposal_template
from tests.fixtures.construction_model.linda_j1_takeoff_fixture import SOURCE_REFERENCE, model
from tests.test_deck_takeoff_workflow import _facts_form, _issue, _project, _setup, app, client  # noqa: F401

ACTOR = "Test office"


def _template(name="Drawing test template"):
    return create_proposal_template(
        name=name, company_name="Brayman Construction (synthetic)", company_address="Synthetic",
        company_phone="000", company_email="x@example.test", primary_color="#1f3a5f", accent_color="#c79a2b", logo_path=None,
        default_intro_text="Synthetic.", default_scope_intro="Synthetic.", default_clarifications="", default_exclusions="",
        default_schedule_text="", default_warranty_text="", default_acceptance_text="", default_payment_terms="Net 30",
        is_default=True, is_active=True, show_detailed_pricing=True, show_section_totals=True, show_allowances=True, show_tax=True,
    )


def _generate(client, project):
    response = client.post(f"/projects/{project.id}/drawings/generate", data={"actor_display_name": ACTOR})
    assert response.status_code == 302
    return ConstructionDrawingSet.query.filter_by(project_id=project.id).order_by(ConstructionDrawingSet.id.desc()).first()


def _pages(data: bytes) -> int:
    return len(PdfReader(io.BytesIO(data)).pages)


def test_generate_preview_download_and_write_once(app, client):
    project, _other, _account = _setup()
    client.post(f"/projects/{project.id}/deck-takeoff/product-facts", data=_facts_form())
    page = client.get(f"/projects/{project.id}/drawings")
    assert page.status_code == 200 and b"Generate drawings" in page.data
    record = _generate(client, project)
    assert record.drawing_revision == 1 and record.sheet_count == 7 and record.status == "PRELIMINARY"
    assert record.model_revision_number == 1 and record.product_facts_version == 1
    preview = client.get(f"/projects/{project.id}/drawings/{record.id}")
    assert preview.status_code == 200 and b"PRELIMINARY" in preview.data and b"A-1" in preview.data
    pdf = client.get(f"/projects/{project.id}/drawings/{record.id}.pdf")
    assert pdf.status_code == 200 and pdf.mimetype == "application/pdf" and _pages(pdf.data) == 7
    import hashlib

    assert hashlib.sha256(pdf.data).hexdigest() == record.pdf_sha256
    dxf = client.get(f"/projects/{project.id}/drawings/{record.id}.dxf")
    assert dxf.status_code == 200
    doc, auditor = recover.read(io.BytesIO(dxf.data))
    assert not auditor.has_errors and len(doc.modelspace().query("DIMENSION")) > 20
    assert hashlib.sha256(dxf.data).hexdigest() == record.dxf_sha256
    # Same inputs: the existing set is returned, nothing is regenerated.
    again = _generate(client, project)
    assert again.id == record.id and ConstructionDrawingSet.query.filter_by(project_id=project.id).count() == 1
    text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(record.pdf_bytes)).pages)
    assert project.name in text and "D1" in text and "R1" in text


def test_model_change_marks_the_set_outdated_and_it_cannot_be_attached(app, client):
    project, _other, _account = _setup()
    client.post(f"/projects/{project.id}/deck-takeoff/product-facts", data=_facts_form())
    first = _generate(client, project)
    pdf_before = first.pdf_bytes
    estimate = create_estimate(project_id=project.id, estimate_number="DRW-1", title="Deck")
    content = model()
    content["uncertainty"] = list(content.get("uncertainty") or []) + [{"code": "field_confirmation", "note": "Revision 2: gate swing confirmed on site (synthetic)."}]
    save_construction_model_revision(organization_id=DEFAULT_ORGANIZATION_ID, project_id=project.id, content=content,
                                     source_kind="source_document", source_reference=SOURCE_REFERENCE, actor_display_name=ACTOR)
    state = drawings.drawing_state(first)
    assert not state.current and "revision R2" in state.reasons[0]
    with pytest.raises(drawings.DrawingError, match="outdated"):
        drawings.attach(first, "estimate_version", estimate.current_version.id, ACTOR)
    second = _generate(client, project)
    assert second.id != first.id and second.drawing_revision == 2 and second.model_revision_number == 2
    db.session.refresh(first)
    assert first.pdf_bytes == pdf_before  # the earlier set is unchanged
    page = client.get(f"/projects/{project.id}/drawings")
    assert b"Outdated" in page.data and b"Current" in page.data


def test_save_to_project_plans_once(app, client):
    project, _other, _account = _setup()
    record = _generate(client, project)
    client.post(f"/projects/{project.id}/drawings/{record.id}/save-to-plans")
    db.session.refresh(record)
    plan = db.session.get(PlanDocument, record.plan_document_id)
    assert plan is not None and plan.project_id == project.id and plan.origin == "generated"
    assert plan.sha256_hex == record.pdf_sha256
    client.post(f"/projects/{project.id}/drawings/{record.id}/save-to-plans")
    assert PlanDocument.query.filter_by(project_id=project.id).count() == 1


def test_attach_to_estimate_version_and_supersede(app, client):
    project, _other, _account = _setup()
    client.post(f"/projects/{project.id}/deck-takeoff/product-facts", data=_facts_form())
    first = _generate(client, project)
    estimate = create_estimate(project_id=project.id, estimate_number="DRW-2", title="Deck")
    version = estimate.current_version
    base = client.get(f"/estimates/{estimate.id}/versions/{version.id}/print.pdf")
    base_pages = _pages(base.data)
    client.post(f"/projects/{project.id}/drawings/{first.id}/attach",
                data={"target_kind": "estimate_version", "estimate_version_id": version.id, "actor_display_name": ACTOR})
    with_drawings = client.get(f"/estimates/{estimate.id}/versions/{version.id}/print.pdf")
    assert _pages(with_drawings.data) == base_pages + first.sheet_count
    text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(with_drawings.data)).pages)
    assert "PRELIMINARY — NOT FOR CONSTRUCTION" in text and "D1" in text
    # New product facts → new drawing revision → attaching it supersedes D1 on this version.
    form = _facts_form()
    form["decking.gap_in"] = "0.25"
    client.post(f"/projects/{project.id}/deck-takeoff/product-facts", data=form)
    second = _generate(client, project)
    drawings.attach(second, "estimate_version", version.id, ACTOR)
    rows = ConstructionDrawingAttachment.query.filter_by(estimate_version_id=version.id).order_by(ConstructionDrawingAttachment.id).all()
    assert [r.drawing_set_id for r in rows] == [first.id, second.id]
    assert rows[0].superseded_at is not None and rows[1].superseded_at is None
    final = client.get(f"/estimates/{estimate.id}/versions/{version.id}/print.pdf")
    text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(final.data)).pages)
    assert "D2" in text and _pages(final.data) == base_pages + second.sheet_count
    # A locked version refuses a new attachment.
    version.is_locked = True
    db.session.commit()
    with pytest.raises(drawings.DrawingError, match="locked"):
        drawings.attach(second, "estimate_version", version.id, ACTOR)


def test_attach_to_draft_proposal_and_refuse_issued(app, client):
    project, _other, _account = _setup()
    record = _generate(client, project)
    estimate = create_estimate(project_id=project.id, estimate_number="DRW-3", title="Deck")
    proposal = create_proposal(estimate=estimate, version=estimate.current_version, template=_template(), title="Deck proposal",
                               valid_until=date(2026, 12, 31))
    base_pages = _pages(client.get(f"/proposals/{proposal.id}/pdf").data)
    client.post(f"/projects/{project.id}/drawings/{record.id}/attach",
                data={"target_kind": "proposal", "proposal_id": proposal.id, "actor_display_name": ACTOR})
    assert _pages(client.get(f"/proposals/{proposal.id}/pdf").data) == base_pages + record.sheet_count
    issued = create_proposal(estimate=estimate, version=estimate.current_version, template=_template("Second template"), title="Issued",
                             valid_until=date(2026, 12, 31))
    issued.status = "Issued"
    db.session.commit()
    with pytest.raises(drawings.DrawingError, match="Issued"):
        drawings.attach(record, "proposal", issued.id, ACTOR)


def test_bmr_request_package_keeps_the_form_and_needs_the_same_takeoff(app, client):
    project, _other, account = _setup()
    request_pdf, fields, _keys = _issue(client, project, account)
    request_id = fields["request_id"]["/V"]
    record = _generate(client, project)
    response = client.post(f"/projects/{project.id}/drawings/{record.id}/attach",
                           data={"target_kind": "supplier_request", "supplier_request_id": request_id, "actor_display_name": ACTOR})
    assert response.status_code == 302
    package = client.get(f"/projects/{project.id}/deck-takeoff/requests/{request_id}/package.pdf")
    assert package.status_code == 200
    assert _pages(package.data) == _pages(request_pdf) + record.sheet_count
    # The supplier form still reads back after the drawing pages are added.
    values = read_response_pdf(package.data)
    assert values["request_id"] == request_id
    # Form 2 survives: three supplier boxes per line, and a priced package imports through the server.
    assert values["response_form"] == "2"
    fields = PdfReader(io.BytesIO(package.data)).get_fields()
    keys = {f["/V"]: k[-2:] for k, f in fields.items() if k.startswith("line_key_")}
    n = next(v for k, v in keys.items() if k.startswith("decking.boards."))
    from tests.test_deck_takeoff_supplier_documents import _fill

    priced = _fill(package.data, {f"sku_{n}": "SYN-1", f"unit_cost_{n}": "10", f"discount_{n}": "0", "valid_until": "2026-11-30"})
    imported = client.post(f"/projects/{project.id}/deck-takeoff/responses", data={"response_pdf": (io.BytesIO(priced), "r.pdf")},
                           content_type="multipart/form-data")
    assert imported.status_code == 302 and "/deck-takeoff/responses/" in imported.headers["Location"]
    # The stored request itself is unchanged.
    stored = client.get(f"/projects/{project.id}/deck-takeoff/requests/{request_id}.pdf")
    assert stored.data == request_pdf
    # Drawings from a different takeoff cannot go with this request.
    form = _facts_form()
    form["decking.gap_in"] = "0.25"
    client.post(f"/projects/{project.id}/deck-takeoff/product-facts", data=form)
    other = _generate(client, project)
    with pytest.raises(drawings.DrawingError, match="takeoff"):
        drawings.attach(other, "supplier_request", request_id, ACTOR)


def test_projects_and_organizations_are_isolated(app, client):
    project, other, _account = _setup()
    record = _generate(client, project)
    other_estimate = create_estimate(project_id=other.id, estimate_number="DRW-4", title="Other")
    with pytest.raises(drawings.DrawingError, match="not on this project"):
        drawings.attach(record, "estimate_version", other_estimate.current_version.id, ACTOR)
    assert client.get(f"/projects/{other.id}/drawings/{record.id}.pdf").status_code == 404
    org = Organization(id="ORG-002", legal_name="Other Contracting Ltd.", display_name="Other Contracting", primary_address="1 Main St",
                       default_region="Ontario", currency="CAD", tax_jurisdiction="Ontario (HST 13%)", is_active=True)
    db.session.add(org)
    db.session.commit()
    stranger = _project("Other org deck", organization_id="ORG-002")
    assert client.get(f"/projects/{stranger.id}/drawings").status_code == 404


def test_a_project_without_a_model_cannot_generate(app, client):
    bare = _project("No construction model")
    response = client.post(f"/projects/{bare.id}/drawings/generate", data={"actor_display_name": ACTOR}, follow_redirects=True)
    assert b"no stored construction model revision" in response.data
    assert ConstructionDrawingSet.query.count() == 0


def test_generation_needs_a_person(app, client):
    project, _other, _account = _setup()
    with pytest.raises(drawings.DrawingError, match="person"):
        drawings.generate_drawing_set(organization_id=DEFAULT_ORGANIZATION_ID, project_id=project.id, actor=" ")


def test_estimate_and_proposal_still_print_before_the_drawing_tables_exist(app, client):
    """Between a deploy and migration v2c3d4e5f6a7 the documents are served without drawings."""
    from app.models.construction_drawing import ConstructionDrawingAttachment, ConstructionDrawingSet

    project, _other, _account = _setup()
    estimate = create_estimate(project_id=project.id, estimate_number="DRW-GAP", title="Deck")
    proposal = create_proposal(estimate=estimate, version=estimate.current_version, template=_template("Gap template"), title="Gap",
                               valid_until=date(2026, 12, 31))
    ConstructionDrawingAttachment.__table__.drop(db.engine)
    ConstructionDrawingSet.__table__.drop(db.engine)
    assert drawings.current_attachment("estimate_version", estimate.current_version.id) is None
    assert client.get(f"/estimates/{estimate.id}/versions/{estimate.current_version.id}/print.pdf").status_code == 200
    assert client.get(f"/proposals/{proposal.id}/pdf").status_code == 200
    ConstructionDrawingSet.__table__.create(db.engine)
    ConstructionDrawingAttachment.__table__.create(db.engine)
