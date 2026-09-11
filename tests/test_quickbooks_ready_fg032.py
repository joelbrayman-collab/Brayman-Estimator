"""FG-032 QuickBooks-ready Slices A+B and Slice C."""

from __future__ import annotations

import os
import threading
from decimal import Decimal
from io import BytesIO

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from pypdf import PdfReader

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.estimate_costing import EstimateCostingSnapshotLine
from app.models.estimate_quickbooks import (
    ENTRY_STATE_ENTERED,
    ENTRY_STATE_NOT_ENTERED,
    QB_EVENT_CORRECTED,
    QB_EVENT_ENTERED,
    QB_EVENT_REVERSED,
    QB_STATUS_ISSUED,
    QB_STATUS_REVIEWED,
    QB_STATUS_SUPERSEDED,
    EstimateQuickBooksEntryEvent,
    EstimateQuickBooksEntryOccupancy,
    EstimateQuickBooksPackage,
)
from app.models.estimate_scope_delivery import (
    LABOUR_INTERNAL,
    LABOUR_SUBCONTRACT,
    MATERIAL_CONTRACTOR_PURCHASED,
    MATERIAL_OWNER_SUPPLIED,
)
from app.models.pricing_engine import EstimatePricingSnapshot
from app.models.user import User, UserMembership
from app.services.auth import hash_password
from app.services.estimate_builder import add_cost_item_line, add_manual_line, create_section
from app.services.estimate_costing import (
    PRICING_STATUS_CURRENT,
    PRICING_STATUS_STALE_REQUIRES_REAPPLY,
    approve_all_costing,
    current_costing_snapshot,
    pricing_consume_status,
)
from app.services import estimate_quickbooks as qb_service
from app.services.estimate_quickbooks import (
    BLOCK_COST_CLASS_SUM_MISMATCH,
    BLOCK_CROSS_ORG,
    BLOCK_CURRENCY_NOT_CAD,
    BLOCK_DUPLICATE_ACTIVE_ENTERED,
    BLOCK_DUPLICATE_ACTIVE_ISSUED,
    BLOCK_ENTRY_AI_ACTOR,
    BLOCK_ENTRY_ACTOR_REQUIRED,
    BLOCK_ENTRY_IMMUTABLE,
    BLOCK_ENTRY_NOT_ACTIVE,
    BLOCK_ENTRY_NOT_ISSUED,
    BLOCK_ENTRY_REASON_REQUIRED,
    BLOCK_MISSING_CLIENT_IDENTITY,
    BLOCK_MISSING_PROJECT_IDENTITY,
    BLOCK_NOT_REVIEWED,
    BLOCK_PRICING_NOT_CURRENT,
    BLOCK_PROPOSAL_NOT_ELIGIBLE,
    BLOCK_PROPOSAL_PRICING_MISMATCH,
    BLOCK_SALES_LINE_SUM_MISMATCH,
    BLOCK_SOURCE_IDENTITY_CHANGED,
    BLOCK_UNRESOLVED_ROUTING,
    WARN_ALLOWANCE,
    WARN_CLIENT_NAME_MISMATCH,
    WARN_HYBRID_UNSPLIT,
    WARN_MISSING_PRODUCT_SERVICE,
    WARN_OWNER_ROUTING,
    WARN_PROPOSAL_ISSUED_NOT_ACCEPTED,
    EstimateQuickBooksError,
    assemble_quickbooks_preview,
    confirm_entered,
    correct_entry,
    cost_class_artifact_text,
    derived_entry_state,
    issue_package,
    issued_pdf_bytes,
    list_entry_events,
    regenerate_draft,
    reverse_entry,
    sales_artifact_text,
    save_reviewed_package,
)
from app.services.estimate_scope_delivery import confirm_scope_delivery, save_scope_delivery
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.pricing_engine import (
    apply_resolved_pricing_to_version,
    as_money,
    create_pricing_policy,
)
from app.services.proposals import (
    create_proposal,
    create_proposal_template,
    update_proposal,
    update_proposal_status,
)
from tests.auth_fixtures import (
    DEFAULT_OFFICE_EMAIL,
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
)
from tests.scope_delivery_support import ensure_confirmed_scope_routing


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg032",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _true_gm_policy():
    policy = create_pricing_policy(
        policy_code="ORG-001-TRUE-GM-15-QB",
        method="TRUE_GROSS_MARGIN",
        actor="Joel Brayman",
        target_gross_margin=Decimal("0.15"),
        tax_jurisdiction="CA-ON",
        tax_percent=Decimal("13"),
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        contingency_visibility="UNSPECIFIED",
        provenance="docs/pricing-policy.md",
        is_default=True,
    )
    db.session.commit()
    return policy


def _cost_item():
    from app.models.cost_item import CostItem

    item = CostItem(
        code="MAT-FG032",
        name="FG-032 Material",
        category="Material",
        unit="ea",
        unit_cost=Decimal("50.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    )
    db.session.add(item)
    db.session.commit()
    return item


def _project(*, name="FG-032 Project", address="10 Main St", project_number="P-032"):
    client_row = Client(name=f"{name} Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
        address=address,
        project_number=project_number,
    )
    db.session.add(project)
    db.session.commit()
    return project


def _template():
    return create_proposal_template(
        name="FG-032 Template",
        company_name="Brayman Construction Co.",
        default_intro_text="Thank you for the opportunity.",
        default_payment_terms="Net 30",
        is_default=True,
        is_active=True,
        show_tax=True,
    )


def _seed(
    *,
    proposal_status="Accepted",
    hybrid=False,
    allowance=False,
    owner_routing=False,
    address="10 Main St",
    estimate_number="EST-FG032-0001",
):
    _true_gm_policy()
    project = _project(address=address, name=estimate_number)
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=estimate_number,
        title="FG-032 Estimate",
    )
    version = estimate.current_version
    section = create_section(version, name="Direct")
    cost_item = _cost_item()
    line = add_cost_item_line(section, cost_item_id=cost_item.id, quantity=2)
    allowance_line = None
    if allowance:
        allowance_line = add_manual_line(
            section,
            line_type="Allowance",
            description="Contingency Allowance",
            quantity=1,
            unit="ls",
            unit_cost=Decimal("100.00"),
        )
    if hybrid:
        save_scope_delivery(
            line,
            material_procurement=MATERIAL_CONTRACTOR_PURCHASED,
            labour_delivery=LABOUR_SUBCONTRACT,
            actor="Joel Brayman",
            commit=False,
        )
        confirm_scope_delivery(line, actor="Joel Brayman", commit=False)
        if allowance_line is None:
            db.session.commit()
        else:
            ensure_confirmed_scope_routing(version, actor="Joel Brayman")
            db.session.commit()
    elif owner_routing:
        save_scope_delivery(
            line,
            material_procurement=MATERIAL_OWNER_SUPPLIED,
            labour_delivery=LABOUR_INTERNAL,
            actor="Joel Brayman",
            commit=False,
        )
        confirm_scope_delivery(line, actor="Joel Brayman", commit=False)
        db.session.commit()
    else:
        ensure_confirmed_scope_routing(version, actor="Joel Brayman")
        db.session.commit()
    costing = approve_all_costing(version, actor="Joel Brayman")
    pricing = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    template = _template()
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=template,
        status=proposal_status,
    )
    db.session.commit()
    return {
        "project": project,
        "estimate": estimate,
        "version": version,
        "line": line,
        "allowance_line": allowance_line,
        "costing": costing,
        "pricing": pricing,
        "proposal": proposal,
        "cost_item": cost_item,
    }


def _pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def test_accepted_proposal_eligibility_and_exact_reconciliation(app):
    seeded = _seed(proposal_status="Accepted")
    preview = assemble_quickbooks_preview(
        project=seeded["project"],
        version=seeded["version"],
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert preview["eligible"] is True
    assert WARN_PROPOSAL_ISSUED_NOT_ACCEPTED not in preview["warning_codes"]
    assert WARN_MISSING_PRODUCT_SERVICE in preview["warning_codes"]
    assert preview["pricing_consume_status"] == PRICING_STATUS_CURRENT
    header = preview["header"]
    pricing = seeded["pricing"]
    proposal = seeded["proposal"]
    assert header["pre_tax"] == as_money(pricing.pre_tax_selling_price)
    assert header["tax_amount"] == as_money(pricing.tax_amount)
    assert header["customer_total"] == as_money(pricing.customer_total)
    assert as_money(proposal.subtotal) == header["pre_tax"]
    assert as_money(proposal.tax_amount) == header["tax_amount"]
    assert as_money(proposal.total) == header["customer_total"]
    sales_sum = as_money(sum((row["amount"] for row in preview["sales_lines"]), Decimal("0")))
    cost_sum = as_money(
        sum((row["extended_cost"] for row in preview["cost_class_lines"]), Decimal("0"))
    )
    assert sales_sum == header["pre_tax"]
    assert cost_sum == header["approved_direct_cost_total"]
    assert header["project_number"] == seeded["project"].project_number
    assert preview["sales_lines"][0]["unit_price"] == proposal.sections[0].line_items[0].unit_price


def test_issued_proposal_eligibility_warns_and_reconciles_current_values(app):
    seeded = _seed(proposal_status="Issued")
    preview = assemble_quickbooks_preview(
        project=seeded["project"],
        version=seeded["version"],
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert preview["eligible"] is True
    assert WARN_PROPOSAL_ISSUED_NOT_ACCEPTED in preview["warning_codes"]
    assert as_money(seeded["proposal"].total) == preview["header"]["customer_total"]


def test_draft_proposal_is_blocked(app):
    seeded = _seed(proposal_status="Draft")
    preview = assemble_quickbooks_preview(
        project=seeded["project"],
        version=seeded["version"],
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert preview["eligible"] is False
    assert BLOCK_PROPOSAL_NOT_ELIGIBLE in preview["block_codes"]


def test_derived_pricing_consume_status_stale_blocks(app):
    seeded = _seed()
    assert pricing_consume_status(seeded["version"]) == PRICING_STATUS_CURRENT
    add_cost_item_line(
        seeded["version"].sections[0],
        cost_item_id=seeded["cost_item"].id,
        quantity=1,
    )
    ensure_confirmed_scope_routing(seeded["version"], actor="Joel Brayman")
    approve_all_costing(seeded["version"], actor="Joel Brayman")
    db.session.commit()
    assert pricing_consume_status(seeded["version"]) == PRICING_STATUS_STALE_REQUIRES_REAPPLY
    preview = assemble_quickbooks_preview(
        project=seeded["project"],
        version=seeded["version"],
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert preview["eligible"] is False
    assert BLOCK_PRICING_NOT_CURRENT in preview["block_codes"]


def test_proposal_pricing_mismatch_of_one_cent_blocks(app):
    seeded = _seed(proposal_status="Issued")
    proposal = seeded["proposal"]
    proposal.subtotal = as_money(proposal.subtotal) + Decimal("0.01")
    db.session.commit()
    preview = assemble_quickbooks_preview(
        project=seeded["project"],
        version=seeded["version"],
        proposal=proposal,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert preview["eligible"] is False
    assert BLOCK_PROPOSAL_PRICING_MISMATCH in preview["block_codes"]


def test_cad_only_enforcement(app):
    seeded = _seed()
    org = db.session.get(Organization, DEFAULT_ORGANIZATION_ID)
    org.currency = "USD"
    db.session.commit()
    preview = assemble_quickbooks_preview(
        project=seeded["project"],
        version=seeded["version"],
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert preview["eligible"] is False
    assert BLOCK_CURRENCY_NOT_CAD in preview["block_codes"]


def test_missing_identity_blocks(app):
    seeded = _seed()
    project = seeded["project"]
    project.name = ""
    seeded["proposal"].client_name = ""
    project.client.name = ""
    db.session.commit()
    preview = assemble_quickbooks_preview(
        project=project,
        version=seeded["version"],
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert preview["eligible"] is False
    assert BLOCK_MISSING_PROJECT_IDENTITY in preview["block_codes"]
    assert BLOCK_MISSING_CLIENT_IDENTITY in preview["block_codes"]


def test_unresolved_non_allowance_routing_blocks(app):
    seeded = _seed()
    costing_line = current_costing_snapshot(seeded["version"]).lines[0]
    db.session.execute(
        sa.update(EstimateCostingSnapshotLine)
        .where(EstimateCostingSnapshotLine.id == costing_line.id)
        .values(material_procurement="UNRESOLVED")
    )
    db.session.commit()
    db.session.expire_all()
    preview = assemble_quickbooks_preview(
        project=seeded["project"],
        version=seeded["version"],
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert preview["eligible"] is False
    assert BLOCK_UNRESOLVED_ROUTING in preview["block_codes"]


def test_allowance_exception_and_warning(app):
    seeded = _seed(allowance=True)
    preview = assemble_quickbooks_preview(
        project=seeded["project"],
        version=seeded["version"],
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert preview["eligible"] is True
    assert WARN_ALLOWANCE in preview["warning_codes"]
    allowance_rows = [row for row in preview["cost_class_lines"] if row["is_allowance"]]
    assert len(allowance_rows) == 1
    assert allowance_rows[0]["planned_class"] == "ALLOWANCE"


def test_hybrid_amount_included_once_no_invented_split(app):
    seeded = _seed(hybrid=True)
    preview = assemble_quickbooks_preview(
        project=seeded["project"],
        version=seeded["version"],
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert preview["eligible"] is True
    assert WARN_HYBRID_UNSPLIT in preview["warning_codes"]
    hybrid_rows = [row for row in preview["cost_class_lines"] if row["is_hybrid"]]
    assert len(hybrid_rows) == 1
    assert hybrid_rows[0]["planned_class"] == "HYBRID"
    assert hybrid_rows[0]["extended_cost"] == as_money(seeded["line"].extended_cost)
    assert len(preview["cost_class_lines"]) == 1


def test_owner_routing_warns(app):
    seeded = _seed(owner_routing=True)
    preview = assemble_quickbooks_preview(
        project=seeded["project"],
        version=seeded["version"],
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert preview["eligible"] is True
    assert WARN_OWNER_ROUTING in preview["warning_codes"]


def test_client_name_mismatch_warns(app):
    seeded = _seed()
    seeded["proposal"].client_name = "Different Client"
    db.session.commit()
    preview = assemble_quickbooks_preview(
        project=seeded["project"],
        version=seeded["version"],
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert preview["eligible"] is True
    assert WARN_CLIENT_NAME_MISMATCH in preview["warning_codes"]


def test_artifact_a_privacy_and_artifact_b_privacy(app):
    seeded = _seed(hybrid=True)
    package = save_reviewed_package(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    issue_package(package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    sales_text = sales_artifact_text(package).lower()
    assert "internal entry reference" in sales_text
    assert "quickbooks estimate / entry sheet" in sales_text
    for forbidden in (
        "contractor_purchased",
        "subcontract",
        "extended_cost",
        "margin",
        "supplier",
        "quote",
        "planned cost",
        "hybrid",
    ):
        assert forbidden not in sales_text
    cost_text = cost_class_artifact_text(package).lower()
    assert "planned cost-classification" in cost_text
    assert "customer total" not in cost_text
    assert str(package.customer_total) not in cost_text
    sales_pdf = _pdf_text(issued_pdf_bytes(package, "sales"))
    cost_pdf = _pdf_text(issued_pdf_bytes(package, "cost_class"))
    assert "INTERNAL ENTRY REFERENCE" in sales_pdf
    assert "QUICKBOOKS ESTIMATE / ENTRY SHEET" in sales_pdf
    assert "Not posted to QuickBooks" in sales_pdf
    assert "Not an import file" in sales_pdf
    assert "CONTRACTOR_PURCHASED" not in sales_pdf
    assert "HYBRID" not in sales_pdf
    assert "INTERNAL / PLANNED COST-CLASSIFICATION" in cost_pdf
    assert "QUICKBOOKS ESTIMATE / ENTRY SHEET" not in cost_pdf
    assert "Customer total" not in cost_pdf
    assert "Entered in QuickBooks" not in sales_pdf
    assert "Entered in QuickBooks" not in cost_pdf


def test_proposal_and_supplier_html_unchanged(client, app):
    seeded = _seed()
    proposal = seeded["proposal"]
    preview = client.get(f"/proposals/{proposal.id}/preview")
    assert preview.status_code == 200
    html = preview.get_data(as_text=True)
    assert "INTERNAL ENTRY REFERENCE" not in html
    assert "PLANNED COST-CLASSIFICATION" not in html
    assert "QuickBooks-ready" not in html
    assert "Entered in QuickBooks" not in html
    supplier = client.get(f"/projects/{seeded['project'].id}/supplier-package")
    assert supplier.status_code == 200
    supplier_html = supplier.get_data(as_text=True)
    assert "INTERNAL ENTRY REFERENCE" not in supplier_html
    assert "PLANNED COST-CLASSIFICATION" not in supplier_html
    assert "Entered in QuickBooks" not in supplier_html


def test_review_before_issue_and_issue_revalidation(app):
    seeded = _seed()
    draft = regenerate_draft(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    with pytest.raises(EstimateQuickBooksError) as exc:
        issue_package(draft, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    assert BLOCK_NOT_REVIEWED in exc.value.block_codes
    reviewed = save_reviewed_package(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert reviewed.status == QB_STATUS_REVIEWED
    add_cost_item_line(
        seeded["version"].sections[0],
        cost_item_id=seeded["cost_item"].id,
        quantity=1,
    )
    ensure_confirmed_scope_routing(seeded["version"], actor="Joel Brayman")
    approve_all_costing(seeded["version"], actor="Joel Brayman")
    db.session.commit()
    with pytest.raises(EstimateQuickBooksError) as exc:
        issue_package(reviewed, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    assert BLOCK_SOURCE_IDENTITY_CHANGED in exc.value.block_codes or BLOCK_PRICING_NOT_CURRENT in (
        assemble_quickbooks_preview(
            project=seeded["project"],
            version=seeded["version"],
            organization_id=DEFAULT_ORGANIZATION_ID,
        )["block_codes"]
    )


def test_issued_immutability_non_float_and_sha256(app):
    seeded = _seed(proposal_status="Issued")
    package = save_reviewed_package(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    issue_package(package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    frozen_total = package.customer_total
    frozen_message = package.customer_message
    frozen_sales_sha = package.sales_pdf_sha256
    frozen_cost_sha = package.cost_class_pdf_sha256
    assert frozen_sales_sha and len(frozen_sales_sha) == 64
    assert frozen_cost_sha and len(frozen_cost_sha) == 64
    original_costing_total = seeded["costing"].approved_direct_cost_total
    original_pricing_pre_tax = seeded["pricing"].pre_tax_selling_price
    update_proposal(seeded["proposal"], intro_text="Edited after QuickBooks issue")
    seeded["proposal"].subtotal = as_money(seeded["proposal"].subtotal) + Decimal("5.00")
    seeded["proposal"].total = as_money(seeded["proposal"].total) + Decimal("5.00")
    db.session.commit()
    db.session.refresh(package)
    assert package.customer_total == frozen_total
    assert package.customer_message == frozen_message
    assert package.sales_pdf_sha256 == frozen_sales_sha
    assert package.cost_class_pdf_sha256 == frozen_cost_sha
    pdf = _pdf_text(issued_pdf_bytes(package, "sales"))
    assert "Edited after QuickBooks issue" not in pdf
    assert "Thank you for the opportunity." in pdf
    with pytest.raises(EstimateQuickBooksError):
        package.customer_total = Decimal("1.00")
        db.session.commit()
    db.session.rollback()
    db.session.refresh(seeded["costing"])
    db.session.refresh(seeded["pricing"])
    assert seeded["costing"].approved_direct_cost_total == original_costing_total
    assert seeded["pricing"].pre_tax_selling_price == original_pricing_pre_tax


def test_duplicate_active_issue_refused_then_supersession(app):
    seeded = _seed()
    first = save_reviewed_package(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    issue_package(first, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    second = regenerate_draft(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    second = save_reviewed_package(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    with pytest.raises(EstimateQuickBooksError) as exc:
        issue_package(second, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    assert BLOCK_DUPLICATE_ACTIVE_ISSUED in exc.value.block_codes
    issue_package(
        second,
        actor="Joel Brayman",
        supersede_package_id=first.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.refresh(first)
    assert first.status == QB_STATUS_SUPERSEDED
    assert first.superseded_by_id == second.id
    assert second.status == QB_STATUS_ISSUED
    assert first.sales_pdf_sha256
    assert issued_pdf_bytes(first, "sales")


def test_separate_private_downloads_do_not_record_entry(client, app):
    seeded = _seed()
    package = save_reviewed_package(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    issue_package(package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    sales = client.get(
        f"/projects/{seeded['project'].id}/quickbooks-packages/{package.id}/sales.pdf"
    )
    cost = client.get(
        f"/projects/{seeded['project'].id}/quickbooks-packages/{package.id}/cost-class.pdf"
    )
    assert sales.status_code == 200
    assert cost.status_code == 200
    assert sales.mimetype == "application/pdf"
    assert cost.mimetype == "application/pdf"
    assert sales.headers["Content-Disposition"].startswith("attachment")
    assert "sales-entry.pdf" in sales.headers["Content-Disposition"]
    assert "cost-class.pdf" in cost.headers["Content-Disposition"]
    assert sales.data != cost.data
    db.session.refresh(package)
    assert package.status == QB_STATUS_ISSUED
    tables = {
        row[0]
        for row in db.session.execute(
            sa.text("SELECT name FROM sqlite_master WHERE type='table'")
        )
    }
    assert "estimate_quickbooks_entry_events" in tables
    assert (
        EstimateQuickBooksEntryEvent.query.filter_by(
            estimate_quickbooks_package_id=package.id
        ).count()
        == 0
    )
    page = client.get(f"/projects/{seeded['project'].id}/quickbooks-entry")
    assert page.status_code == 200
    text = page.get_data(as_text=True)
    assert "Downloading does not mean entered" in text
    assert "Entered in QuickBooks" in text
    assert "CalibraytAI did not post to QuickBooks" in text
    assert "did not verify QuickBooks" in text
    assert (
        EstimateQuickBooksEntryEvent.query.filter_by(
            estimate_quickbooks_package_id=package.id
        ).count()
        == 0
    )
    hub = client.get(f"/projects/{seeded['project'].id}")
    assert "QuickBooks-ready entry" in hub.get_data(as_text=True)


def test_tenant_isolation_and_transaction_rollback(client, app):
    seeded = _seed()
    org_b = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org_b)
    db.session.commit()
    other_client = Client(name="Apex Client", organization_id="ORG-002")
    db.session.add(other_client)
    db.session.flush()
    other_project = Project(
        name="Apex Project",
        client_id=other_client.id,
        organization_id="ORG-002",
        status="Estimating",
    )
    db.session.add(other_project)
    db.session.commit()
    assert client.get(f"/projects/{other_project.id}/quickbooks-entry").status_code == 404
    package = save_reviewed_package(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    issue_package(package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    assert (
        client.get(
            f"/projects/{other_project.id}/quickbooks-packages/{package.id}/sales.pdf"
        ).status_code
        == 404
    )
    user_b = create_user(
        email="apex@example.com",
        password="apex-password",
        display_name="Apex User",
    )
    create_membership(user_b, "ORG-002")
    db.session.commit()
    client.post("/logout")
    login_office_user(client, email="apex@example.com", password="apex-password")
    assert client.get(f"/projects/{seeded['project'].id}/quickbooks-entry").status_code == 404
    with pytest.raises(EstimateQuickBooksError):
        issue_package(package, actor="Joel Brayman", organization_id="ORG-002")
    db.session.rollback()
    db.session.refresh(package)
    assert package.status == QB_STATUS_ISSUED
    assert EstimateQuickBooksPackage.query.filter_by(organization_id="ORG-002").count() == 0


def test_no_source_record_mutation(app):
    seeded = _seed()
    costing_id = seeded["costing"].id
    pricing_id = seeded["pricing"].id
    proposal_id = seeded["proposal"].id
    line_unit_cost = seeded["line"].unit_cost
    proposal_total = seeded["proposal"].total
    package = save_reviewed_package(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    issue_package(package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.refresh(seeded["line"])
    db.session.refresh(seeded["proposal"])
    assert current_costing_snapshot(seeded["version"]).id == costing_id
    assert seeded["pricing"].id == pricing_id
    assert seeded["proposal"].id == proposal_id
    assert seeded["line"].unit_cost == line_unit_cost
    assert seeded["proposal"].total == proposal_total
    assert seeded["proposal"].status == "Accepted"


def test_ai_actor_rejected(app):
    seeded = _seed()
    with pytest.raises(EstimateQuickBooksError, match="AI cannot"):
        save_reviewed_package(
            project=seeded["project"],
            version=seeded["version"],
            actor="AI",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )


def test_routes_review_issue_and_csrf_fields(client, app):
    seeded = _seed()
    project_id = seeded["project"].id
    page = client.get(f"/projects/{project_id}/quickbooks-entry")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "INTERNAL ENTRY REFERENCE" in html
    assert "PLANNED COST-CLASSIFICATION" in html
    assert "csrf_token" in html
    review = client.post(
        f"/projects/{project_id}/quickbooks-entry/review",
        data={"actor_display_name": "Joel Brayman", "version_id": seeded["version"].id},
        follow_redirects=True,
    )
    assert review.status_code == 200
    package = EstimateQuickBooksPackage.query.filter_by(project_id=project_id).one()
    issued = client.post(
        f"/projects/{project_id}/quickbooks-entry/issue",
        data={
            "actor_display_name": "Joel Brayman",
            "version_id": seeded["version"].id,
            "package_id": package.id,
        },
        follow_redirects=True,
    )
    assert issued.status_code == 200
    db.session.refresh(package)
    assert package.status == QB_STATUS_ISSUED


def test_alembic_fg032_upgrade_and_downgrade(tmp_path):
    db_path = tmp_path / "fg032_migration.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
        command.upgrade(alembic_cfg, "d8e9f0a1b2c3")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "estimate_quickbooks_packages" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["d8e9f0a1b2c3"]
        command.upgrade(alembic_cfg, "e9f0a1b2c3d4")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "estimate_quickbooks_packages" in tables
            assert "estimate_quickbooks_sales_lines" in tables
            assert "estimate_quickbooks_cost_class_lines" in tables
            assert "estimate_quickbooks_entry_events" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["e9f0a1b2c3d4"]
        command.downgrade(alembic_cfg, "d8e9f0a1b2c3")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "estimate_quickbooks_packages" not in tables
            assert "estimate_quickbooks_sales_lines" not in tables
            assert "estimate_quickbooks_cost_class_lines" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["d8e9f0a1b2c3"]


def _issued_package(seeded, actor="Joel Brayman"):
    package = save_reviewed_package(
        project=seeded["project"],
        version=seeded["version"],
        actor=actor,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    issue_package(package, actor=actor, organization_id=DEFAULT_ORGANIZATION_ID)
    return package


def _package_fingerprint(package):
    return {
        "status": package.status,
        "customer_total": package.customer_total,
        "pre_tax": package.pre_tax,
        "tax_amount": package.tax_amount,
        "client_name": package.client_name,
        "customer_message": package.customer_message,
        "sales_pdf_sha256": package.sales_pdf_sha256,
        "cost_class_pdf_sha256": package.cost_class_pdf_sha256,
        "sales_storage_key": package.sales_storage_key,
        "cost_class_storage_key": package.cost_class_storage_key,
        "sales_amounts": [line.amount for line in package.sales_lines],
        "cost_amounts": [line.extended_cost for line in package.cost_class_lines],
        "sales_descriptions": [line.description for line in package.sales_lines],
        "cost_classes": [line.planned_class for line in package.cost_class_lines],
    }


def test_alembic_fg032_slice_c_upgrade_and_downgrade(tmp_path):
    from alembic.script import ScriptDirectory

    db_path = tmp_path / "fg032_slice_c_migration.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script.get_heads() == ["f1a2b3c4d5e6"]
        command.upgrade(alembic_cfg, "e9f0a1b2c3d4")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "estimate_quickbooks_packages" in tables
            assert "estimate_quickbooks_entry_events" not in tables
            assert "estimate_quickbooks_entry_occupancies" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["e9f0a1b2c3d4"]
        command.upgrade(alembic_cfg, "f0a1b2c3d4e5")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "estimate_quickbooks_entry_events" in tables
            assert "estimate_quickbooks_entry_occupancies" not in tables
            columns = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(estimate_quickbooks_entry_events)"))
            }
            assert {
                "id",
                "organization_id",
                "project_id",
                "estimate_quickbooks_package_id",
                "kind",
                "actor_user_id",
                "actor_display_name",
                "occurred_at",
                "note",
                "created_at",
            } <= columns
            sql = conn.execute(
                sa.text(
                    "SELECT sql FROM sqlite_master WHERE type='table' "
                    "AND name='estimate_quickbooks_entry_events'"
                )
            ).fetchone()[0]
            assert "ck_estimate_quickbooks_entry_events_kind" in sql
            assert "ENTERED" in sql and "REVERSED" in sql and "CORRECTED" in sql
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f0a1b2c3d4e5"]
        command.upgrade(alembic_cfg, "f1a2b3c4d5e6")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "estimate_quickbooks_entry_occupancies" in tables
            occupancy_columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(estimate_quickbooks_entry_occupancies)")
                )
            }
            assert {
                "estimate_quickbooks_package_id",
                "organization_id",
                "entered_event_id",
                "created_at",
            } <= occupancy_columns
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f1a2b3c4d5e6"]
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(sa.text("PRAGMA foreign_keys=OFF"))
                conn.execute(
                    sa.text(
                        "INSERT INTO estimate_quickbooks_entry_events ("
                        "organization_id, project_id, estimate_quickbooks_package_id, "
                        "kind, actor_display_name, occurred_at, created_at"
                        ") VALUES ('ORG-001', 1, 1, 'POSTED', 'Joel', "
                        "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                    )
                )
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(sa.text("PRAGMA foreign_keys=OFF"))
                conn.execute(
                    sa.text(
                        "INSERT INTO estimate_quickbooks_entry_occupancies ("
                        "estimate_quickbooks_package_id, organization_id, "
                        "entered_event_id, created_at"
                        ") VALUES (1, 'ORG-001', 1, CURRENT_TIMESTAMP)"
                    )
                )
                conn.execute(
                    sa.text(
                        "INSERT INTO estimate_quickbooks_entry_occupancies ("
                        "estimate_quickbooks_package_id, organization_id, "
                        "entered_event_id, created_at"
                        ") VALUES (1, 'ORG-001', 2, CURRENT_TIMESTAMP)"
                    )
                )
        command.downgrade(alembic_cfg, "f0a1b2c3d4e5")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "estimate_quickbooks_entry_occupancies" not in tables
            assert "estimate_quickbooks_entry_events" in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f0a1b2c3d4e5"]
        command.downgrade(alembic_cfg, "e9f0a1b2c3d4")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "estimate_quickbooks_entry_events" not in tables
            assert "estimate_quickbooks_packages" in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["e9f0a1b2c3d4"]


def test_entered_succeeds_on_issued_and_refuses_unissued(app):
    seeded = _seed()
    draft = regenerate_draft(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert derived_entry_state(draft) == ENTRY_STATE_NOT_ENTERED
    with pytest.raises(EstimateQuickBooksError) as exc:
        confirm_entered(
            draft,
            actor="Joel Brayman",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    assert BLOCK_ENTRY_NOT_ISSUED in exc.value.block_codes
    db.session.rollback()
    reviewed = save_reviewed_package(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    with pytest.raises(EstimateQuickBooksError) as exc:
        confirm_entered(
            reviewed,
            actor="Joel Brayman",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    assert BLOCK_ENTRY_NOT_ISSUED in exc.value.block_codes
    db.session.rollback()
    assert EstimateQuickBooksEntryEvent.query.count() == 0
    issue_package(reviewed, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    event = confirm_entered(
        reviewed,
        actor="Joel Brayman",
        actor_user_id=None,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert event.kind == QB_EVENT_ENTERED
    assert derived_entry_state(reviewed) == ENTRY_STATE_ENTERED
    assert list_entry_events(reviewed) == [event]
    occupancy = EstimateQuickBooksEntryOccupancy.query.filter_by(
        estimate_quickbooks_package_id=reviewed.id
    ).one()
    assert occupancy.entered_event_id == event.id
    assert occupancy.organization_id == DEFAULT_ORGANIZATION_ID


def test_duplicate_active_entered_blocks(app):
    seeded = _seed()
    package = _issued_package(seeded)
    confirm_entered(package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    with pytest.raises(EstimateQuickBooksError) as exc:
        confirm_entered(package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    assert BLOCK_DUPLICATE_ACTIVE_ENTERED in exc.value.block_codes
    db.session.rollback()
    assert EstimateQuickBooksEntryEvent.query.count() == 1
    assert EstimateQuickBooksEntryOccupancy.query.count() == 1


def test_concurrent_entered_exactly_one_succeeds(tmp_path):
    from sqlalchemy.pool import NullPool

    db_path = tmp_path / "fg032_concurrent_entered.db"
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False, "timeout": 15},
                "poolclass": NullPool,
            },
            "SECRET_KEY": "test-secret-fg032-concurrent",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        db.session.execute(sa.text("PRAGMA journal_mode=WAL"))
        db.session.execute(sa.text("PRAGMA busy_timeout=15000"))
        db.session.commit()
        ensure_default_organization()
        seeded = _seed()
        package = _issued_package(seeded)
        package_id = package.id
        assert derived_entry_state(package) == ENTRY_STATE_NOT_ENTERED
        assert EstimateQuickBooksEntryEvent.query.count() == 0
        assert EstimateQuickBooksEntryOccupancy.query.count() == 0
        db.session.commit()
        db.session.remove()

    barrier = threading.Barrier(2, timeout=15)
    observed_not_entered = []
    outcomes = []
    original_sync = qb_service._synchronize_entered_claim_for_tests

    def sync():
        observed_not_entered.append(ENTRY_STATE_NOT_ENTERED)
        barrier.wait()

    qb_service._synchronize_entered_claim_for_tests = sync
    try:

        def worker(actor):
            with application.app_context():
                pkg = db.session.get(EstimateQuickBooksPackage, package_id)
                try:
                    event = confirm_entered(
                        pkg,
                        actor=actor,
                        organization_id=DEFAULT_ORGANIZATION_ID,
                    )
                    outcomes.append(("ok", event.id, actor))
                except EstimateQuickBooksError as exc:
                    db.session.rollback()
                    outcomes.append(("block", list(exc.block_codes), actor))
                except Exception as exc:
                    db.session.rollback()
                    outcomes.append(("error", type(exc).__name__, str(exc)))

        threads = [
            threading.Thread(target=worker, args=("Joel Brayman",)),
            threading.Thread(target=worker, args=("Office Clerk",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
            assert not thread.is_alive()
    finally:
        qb_service._synchronize_entered_claim_for_tests = original_sync

    assert observed_not_entered == [ENTRY_STATE_NOT_ENTERED, ENTRY_STATE_NOT_ENTERED]
    successes = [row for row in outcomes if row[0] == "ok"]
    failures = [row for row in outcomes if row[0] == "block"]
    errors = [row for row in outcomes if row[0] == "error"]
    assert errors == []
    assert len(successes) == 1
    assert len(failures) == 1
    assert BLOCK_DUPLICATE_ACTIVE_ENTERED in failures[0][1]

    with application.app_context():
        package = db.session.get(EstimateQuickBooksPackage, package_id)
        events = list_entry_events(package)
        occupancies = EstimateQuickBooksEntryOccupancy.query.filter_by(
            estimate_quickbooks_package_id=package_id
        ).all()
        assert derived_entry_state(package) == ENTRY_STATE_ENTERED
        assert [event.kind for event in events] == [QB_EVENT_ENTERED]
        assert len(events) == 1
        assert len(occupancies) == 1
        assert occupancies[0].entered_event_id == events[0].id
        assert occupancies[0].organization_id == DEFAULT_ORGANIZATION_ID
        assert EstimateQuickBooksEntryEvent.query.count() == 1
        assert EstimateQuickBooksEntryOccupancy.query.count() == 1
        assert (
            EstimateQuickBooksEntryEvent.query.filter(
                EstimateQuickBooksEntryEvent.organization_id != DEFAULT_ORGANIZATION_ID
            ).count()
            == 0
        )
        assert (
            EstimateQuickBooksEntryOccupancy.query.filter(
                EstimateQuickBooksEntryOccupancy.organization_id
                != DEFAULT_ORGANIZATION_ID
            ).count()
            == 0
        )


def test_entry_human_actor_required_and_ai_refused(app):
    seeded = _seed()
    package = _issued_package(seeded)
    with pytest.raises(EstimateQuickBooksError) as exc:
        confirm_entered(package, actor="  ", organization_id=DEFAULT_ORGANIZATION_ID)
    assert BLOCK_ENTRY_ACTOR_REQUIRED in exc.value.block_codes
    db.session.rollback()
    with pytest.raises(EstimateQuickBooksError) as exc:
        confirm_entered(package, actor="AI", organization_id=DEFAULT_ORGANIZATION_ID)
    assert BLOCK_ENTRY_AI_ACTOR in exc.value.block_codes
    db.session.rollback()
    with pytest.raises(EstimateQuickBooksError) as exc:
        confirm_entered(package, actor="CALIBAI-AI", organization_id=DEFAULT_ORGANIZATION_ID)
    assert BLOCK_ENTRY_AI_ACTOR in exc.value.block_codes
    db.session.rollback()
    assert EstimateQuickBooksEntryEvent.query.count() == 0


def test_entry_organization_isolation_blocks_and_rolls_back(app):
    seeded = _seed()
    package = _issued_package(seeded)
    with pytest.raises(EstimateQuickBooksError) as exc:
        confirm_entered(package, actor="Joel Brayman", organization_id="ORG-002")
    assert BLOCK_CROSS_ORG in exc.value.block_codes
    db.session.rollback()
    assert derived_entry_state(package) == ENTRY_STATE_NOT_ENTERED
    assert EstimateQuickBooksEntryEvent.query.count() == 0
    assert EstimateQuickBooksEntryOccupancy.query.count() == 0


def test_reversed_and_corrected_state_machine(app):
    seeded = _seed()
    package = _issued_package(seeded)
    entered = confirm_entered(
        package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID
    )
    with pytest.raises(EstimateQuickBooksError) as exc:
        reverse_entry(
            package,
            actor="Joel Brayman",
            reason="   ",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    assert BLOCK_ENTRY_REASON_REQUIRED in exc.value.block_codes
    db.session.rollback()
    reversed_event = reverse_entry(
        package,
        actor="Joel Brayman",
        reason="Typed the wrong customer",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert reversed_event.kind == QB_EVENT_REVERSED
    events = list_entry_events(package)
    assert events[0].id == entered.id
    assert events[0].kind == QB_EVENT_ENTERED
    assert derived_entry_state(package) == ENTRY_STATE_NOT_ENTERED
    assert EstimateQuickBooksEntryOccupancy.query.count() == 0
    with pytest.raises(EstimateQuickBooksError) as exc:
        reverse_entry(
            package,
            actor="Joel Brayman",
            reason="Again",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    assert BLOCK_ENTRY_NOT_ACTIVE in exc.value.block_codes
    db.session.rollback()
    later = confirm_entered(
        package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID
    )
    assert later.kind == QB_EVENT_ENTERED
    assert derived_entry_state(package) == ENTRY_STATE_ENTERED
    later_occupancy = EstimateQuickBooksEntryOccupancy.query.filter_by(
        estimate_quickbooks_package_id=package.id
    ).one()
    assert later_occupancy.entered_event_id == later.id
    corrected = correct_entry(
        package,
        actor="Joel Brayman",
        note="Corrected QuickBooks estimate number",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert corrected.kind == QB_EVENT_CORRECTED
    assert derived_entry_state(package) == ENTRY_STATE_ENTERED
    assert EstimateQuickBooksEntryOccupancy.query.filter_by(
        estimate_quickbooks_package_id=package.id
    ).one().entered_event_id == later.id
    kinds = [event.kind for event in list_entry_events(package)]
    assert kinds == [
        QB_EVENT_ENTERED,
        QB_EVENT_REVERSED,
        QB_EVENT_ENTERED,
        QB_EVENT_CORRECTED,
    ]


def test_corrected_requires_active_entry_and_note(app):
    seeded = _seed()
    package = _issued_package(seeded)
    with pytest.raises(EstimateQuickBooksError) as exc:
        correct_entry(
            package,
            actor="Joel Brayman",
            note="Fix",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    assert BLOCK_ENTRY_NOT_ACTIVE in exc.value.block_codes
    db.session.rollback()
    confirm_entered(package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    with pytest.raises(EstimateQuickBooksError) as exc:
        correct_entry(
            package,
            actor="Joel Brayman",
            note=" ",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    assert BLOCK_ENTRY_REASON_REQUIRED in exc.value.block_codes
    db.session.rollback()
    assert derived_entry_state(package) == ENTRY_STATE_ENTERED
    assert EstimateQuickBooksEntryEvent.query.filter_by(kind=QB_EVENT_CORRECTED).count() == 0


def test_entry_events_are_append_only_immutable(app):
    seeded = _seed()
    package = _issued_package(seeded)
    event = confirm_entered(
        package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID
    )
    original_id = event.id
    original_occurred = event.occurred_at
    event.kind = QB_EVENT_REVERSED
    with pytest.raises(EstimateQuickBooksError) as exc:
        db.session.commit()
    assert BLOCK_ENTRY_IMMUTABLE in exc.value.block_codes
    db.session.rollback()
    event = db.session.get(EstimateQuickBooksEntryEvent, original_id)
    event.actor_display_name = "Someone Else"
    event.occurred_at = original_occurred
    with pytest.raises(EstimateQuickBooksError) as exc:
        db.session.commit()
    assert BLOCK_ENTRY_IMMUTABLE in exc.value.block_codes
    db.session.rollback()
    second = regenerate_draft(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    event = db.session.get(EstimateQuickBooksEntryEvent, original_id)
    event.estimate_quickbooks_package_id = second.id
    with pytest.raises(EstimateQuickBooksError) as exc:
        db.session.commit()
    assert BLOCK_ENTRY_IMMUTABLE in exc.value.block_codes
    db.session.rollback()
    event = db.session.get(EstimateQuickBooksEntryEvent, original_id)
    db.session.delete(event)
    with pytest.raises(EstimateQuickBooksError) as exc:
        db.session.commit()
    assert BLOCK_ENTRY_IMMUTABLE in exc.value.block_codes
    db.session.rollback()
    retained = db.session.get(EstimateQuickBooksEntryEvent, original_id)
    assert retained.kind == QB_EVENT_ENTERED
    assert retained.actor_display_name == "Joel Brayman"
    assert retained.estimate_quickbooks_package_id == package.id


def test_supersession_retains_history_successor_does_not_inherit(app):
    seeded = _seed()
    first = _issued_package(seeded)
    confirm_entered(first, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    second = regenerate_draft(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    second = save_reviewed_package(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    issue_package(
        second,
        actor="Joel Brayman",
        supersede_package_id=first.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.refresh(first)
    assert first.status == QB_STATUS_SUPERSEDED
    assert derived_entry_state(first) == ENTRY_STATE_ENTERED
    assert [event.kind for event in list_entry_events(first)] == [QB_EVENT_ENTERED]
    assert derived_entry_state(second) == ENTRY_STATE_NOT_ENTERED
    assert list_entry_events(second) == []
    with pytest.raises(EstimateQuickBooksError) as exc:
        confirm_entered(first, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    assert BLOCK_ENTRY_NOT_ISSUED in exc.value.block_codes
    db.session.rollback()
    successor_event = confirm_entered(
        second, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID
    )
    assert successor_event.estimate_quickbooks_package_id == second.id
    assert derived_entry_state(first) == ENTRY_STATE_ENTERED
    assert derived_entry_state(second) == ENTRY_STATE_ENTERED


def test_preview_issue_and_download_create_no_entry_events(client, app):
    seeded = _seed()
    project_id = seeded["project"].id
    preview = client.get(f"/projects/{project_id}/quickbooks-entry")
    assert preview.status_code == 200
    assert EstimateQuickBooksEntryEvent.query.count() == 0
    package = save_reviewed_package(
        project=seeded["project"],
        version=seeded["version"],
        actor="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    issue_package(package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    assert EstimateQuickBooksEntryEvent.query.count() == 0
    assert client.get(
        f"/projects/{project_id}/quickbooks-packages/{package.id}/sales.pdf"
    ).status_code == 200
    assert client.get(
        f"/projects/{project_id}/quickbooks-packages/{package.id}/cost-class.pdf"
    ).status_code == 200
    assert EstimateQuickBooksEntryEvent.query.count() == 0
    assert derived_entry_state(package) == ENTRY_STATE_NOT_ENTERED


def test_entry_does_not_mutate_package_source_or_pdfs(app):
    from app.models.estimate_scope_delivery import EstimateScopeDelivery
    from app.models.supplier_catalogue import SupplierPackage
    from app.plan_intelligence.models import TakeoffPackage

    seeded = _seed()
    package = _issued_package(seeded)
    fingerprint = _package_fingerprint(package)
    sales_bytes = issued_pdf_bytes(package, "sales")
    cost_bytes = issued_pdf_bytes(package, "cost_class")
    line_unit_cost = seeded["line"].unit_cost
    costing_id = seeded["costing"].id
    costing_total = seeded["costing"].approved_direct_cost_total
    pricing_id = seeded["pricing"].id
    pricing_total = seeded["pricing"].customer_total
    proposal_id = seeded["proposal"].id
    proposal_total = seeded["proposal"].total
    proposal_status = seeded["proposal"].status
    scope_count = EstimateScopeDelivery.query.count()
    supplier_count = SupplierPackage.query.count()
    takeoff_count = TakeoffPackage.query.count()
    confirm_entered(package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    reverse_entry(
        package,
        actor="Joel Brayman",
        reason="Office correction",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    confirm_entered(package, actor="Joel Brayman", organization_id=DEFAULT_ORGANIZATION_ID)
    correct_entry(
        package,
        actor="Joel Brayman",
        note="Noted typed invoice number",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.refresh(package)
    db.session.refresh(seeded["line"])
    db.session.refresh(seeded["costing"])
    db.session.refresh(seeded["pricing"])
    db.session.refresh(seeded["proposal"])
    assert _package_fingerprint(package) == fingerprint
    assert issued_pdf_bytes(package, "sales") == sales_bytes
    assert issued_pdf_bytes(package, "cost_class") == cost_bytes
    sales_pdf = _pdf_text(sales_bytes)
    cost_pdf = _pdf_text(cost_bytes)
    assert "Entered in QuickBooks" not in sales_pdf
    assert "Entered in QuickBooks" not in cost_pdf
    assert "REVERSED" not in sales_pdf
    assert "CORRECTED" not in cost_pdf
    assert seeded["line"].unit_cost == line_unit_cost
    assert seeded["costing"].id == costing_id
    assert seeded["costing"].approved_direct_cost_total == costing_total
    assert seeded["pricing"].id == pricing_id
    assert seeded["pricing"].customer_total == pricing_total
    assert seeded["proposal"].id == proposal_id
    assert seeded["proposal"].total == proposal_total
    assert seeded["proposal"].status == proposal_status
    assert EstimateScopeDelivery.query.count() == scope_count
    assert SupplierPackage.query.count() == supplier_count
    assert TakeoffPackage.query.count() == takeoff_count


def test_entry_routes_csrf_and_no_api_claim(client, app):
    seeded = _seed()
    project_id = seeded["project"].id
    package = _issued_package(seeded)
    page = client.get(f"/projects/{project_id}/quickbooks-entry")
    html = page.get_data(as_text=True)
    assert "csrf_token" in html
    assert "Entered in QuickBooks" in html
    assert "CalibraytAI did not post to QuickBooks" in html
    assert "did not verify QuickBooks" in html
    assert "Downloading does not mean entered" in html
    assert "does not change the estimate or Proposal" in html
    assert "recorded state" in html
    assert "Event history is retained" in html
    assert "OAuth" not in html
    assert "posted automatically" not in html.lower()
    entered = client.post(
        f"/projects/{project_id}/quickbooks-packages/{package.id}/entered",
        data={"actor_display_name": "Joel Brayman", "version_id": seeded["version"].id},
        follow_redirects=True,
    )
    assert entered.status_code == 200
    assert derived_entry_state(package) == ENTRY_STATE_ENTERED
    html = entered.get_data(as_text=True)
    assert "csrf_token" in html
    assert "Joel Brayman" in html
    assert "ENTERED" in html
    reversed_page = client.post(
        f"/projects/{project_id}/quickbooks-packages/{package.id}/reverse-entry",
        data={
            "actor_display_name": "Joel Brayman",
            "version_id": seeded["version"].id,
            "reason": "Wrong customer in QuickBooks",
        },
        follow_redirects=True,
    )
    assert reversed_page.status_code == 200
    assert derived_entry_state(package) == ENTRY_STATE_NOT_ENTERED
    client.post(
        f"/projects/{project_id}/quickbooks-packages/{package.id}/entered",
        data={"actor_display_name": "Joel Brayman", "version_id": seeded["version"].id},
        follow_redirects=True,
    )
    corrected = client.post(
        f"/projects/{project_id}/quickbooks-packages/{package.id}/correct-entry",
        data={
            "actor_display_name": "Joel Brayman",
            "version_id": seeded["version"].id,
            "note": "Corrected class mapping note",
        },
        follow_redirects=True,
    )
    assert corrected.status_code == 200
    assert derived_entry_state(package) == ENTRY_STATE_ENTERED
    kinds = [event.kind for event in list_entry_events(package)]
    assert kinds == [
        QB_EVENT_ENTERED,
        QB_EVENT_REVERSED,
        QB_EVENT_ENTERED,
        QB_EVENT_CORRECTED,
    ]


def test_entry_cross_org_http_404_no_residue(client, app):
    seeded = _seed()
    package = _issued_package(seeded)
    org_b = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org_b)
    db.session.commit()
    other_client = Client(name="Apex Client", organization_id="ORG-002")
    db.session.add(other_client)
    db.session.flush()
    other_project = Project(
        name="Apex Project",
        client_id=other_client.id,
        organization_id="ORG-002",
        status="Estimating",
    )
    db.session.add(other_project)
    db.session.commit()
    assert (
        client.post(
            f"/projects/{other_project.id}/quickbooks-packages/{package.id}/entered",
            data={"actor_display_name": "Joel Brayman"},
        ).status_code
        == 404
    )
    user_b = create_user(
        email="apex-entry@example.com",
        password="apex-password",
        display_name="Apex User",
    )
    create_membership(user_b, "ORG-002")
    db.session.commit()
    client.post("/logout")
    login_office_user(client, email="apex-entry@example.com", password="apex-password")
    assert (
        client.post(
            f"/projects/{seeded['project'].id}/quickbooks-packages/{package.id}/entered",
            data={"actor_display_name": "Apex User"},
        ).status_code
        == 404
    )
    db.session.rollback()
    assert EstimateQuickBooksEntryEvent.query.count() == 0
    assert derived_entry_state(package, organization_id=DEFAULT_ORGANIZATION_ID) == (
        ENTRY_STATE_NOT_ENTERED
    )
