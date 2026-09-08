"""FG-026 PLAN → PRICE Phase D takeoff-to-estimate mapping tests."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import inspect as sa_inspect

from app import create_app, db
from app.models import (
    Assembly,
    AssemblyItem,
    CostItem,
    Estimate,
    EstimateLineItem,
    TakeoffEstimateInsertion,
    TakeoffEstimateInsertionCitation,
)
from app.models.estimate import EstimateVersion
from app.models.labour_engine import EstimateLabourSnapshot
from app.models.pricing_engine import EstimatePricingSnapshot
from app.plan_intelligence.takeoff import approve_package, create_draft_package
from app.services.estimate_builder import add_cost_item_line, create_section
from app.services.estimates import create_estimate, lock_version, set_version_status
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.takeoff_estimate_mapping import (
    TakeoffEstimateMappingError,
    insert_takeoff_estimate_mapping,
    preview_takeoff_estimate_mapping,
)
from tests.test_takeoff import _review_fixture, _seed_eligible_plan, _start_run


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "SECRET_KEY": "test-secret-fg026",
            "WTF_CSRF_ENABLED": False,
            "PLAN_UPLOAD_ROOT": str(tmp_path / "plan_uploads"),
            "PLAN_UPLOAD_MAX_BYTES": 2 * 1024 * 1024,
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


def _approved_package(name="FG026 Takeoff Project"):
    seed = _seed_eligible_plan(name=name)
    run = _review_fixture(_start_run(seed))
    pkg = create_draft_package(
        organization_id=seed["organization_id"],
        run_id=run.id,
        created_by="office-reviewer",
    )
    approved = approve_package(
        organization_id=seed["organization_id"],
        package_id=pkg.id,
        approved_by="office-reviewer",
    )
    return seed, approved


def _door_assembly(*, code="UAT-DOOR-ASM"):
    cost = CostItem(
        organization_id=DEFAULT_ORGANIZATION_ID,
        code=f"{code}-MAT",
        name="Interior door leaf",
        category="Material",
        unit="ea",
        unit_cost=Decimal("250.00"),
        default_markup_percent=Decimal("10.00"),
        is_active=True,
    )
    db.session.add(cost)
    db.session.flush()
    assembly = Assembly(
        organization_id=DEFAULT_ORGANIZATION_ID,
        code=code,
        name="UAT Interior Door Assembly",
        category="Doors",
        unit="ea",
        default_markup_percent=Decimal("10.00"),
        is_active=True,
    )
    db.session.add(assembly)
    db.session.flush()
    db.session.add(
        AssemblyItem(
            assembly_id=assembly.id,
            cost_item_id=cost.id,
            quantity=Decimal("1"),
            waste_percent=Decimal("0"),
            sort_order=0,
        )
    )
    db.session.commit()
    return assembly, cost


def _cost_item(*, code="UAT-DOOR-CI"):
    item = CostItem(
        organization_id=DEFAULT_ORGANIZATION_ID,
        code=code,
        name="UAT Interior Door Cost Item",
        category="Material",
        unit="ea",
        unit_cost=Decimal("180.00"),
        default_markup_percent=Decimal("15.00"),
        is_active=True,
    )
    db.session.add(item)
    db.session.commit()
    return item


def _draft_with_section(project_id, *, number="EST-2026-2601", title="FG026 Draft"):
    estimate = create_estimate(
        project_id=project_id,
        estimate_number=number,
        title=title,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    section = create_section(estimate.current_version, name="Doors")
    return estimate, estimate.current_version, section


def _insert_kwargs(package, version, section, *, target_kind, target_id, key=None, qty="3", unit="ea"):
    return dict(
        organization_id=DEFAULT_ORGANIZATION_ID,
        package_id=package.id,
        estimate_version_id=version.id,
        estimate_section_id=section.id,
        target_kind=target_kind,
        target_id=target_id,
        confirmed_quantity=qty,
        confirmed_unit=unit,
        client_insertion_key=key or str(uuid.uuid4()),
        actor_display_name="office-reviewer",
    )


def test_approved_package_maps_to_existing_assembly(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    assert len(package.items) == 3

    insertion = insert_takeoff_estimate_mapping(
        **_insert_kwargs(
            package,
            version,
            section,
            target_kind="assembly",
            target_id=assembly.id,
        )
    )
    assert insertion.estimate_line_item_id is not None
    line = EstimateLineItem.query.get(insertion.estimate_line_item_id)
    assert line.line_type == "Assembly"
    assert line.assembly_id == assembly.id
    assert line.quantity == Decimal("3")
    assert line.unit == "ea"
    assert line.waste_percent == Decimal("0")
    citations = TakeoffEstimateInsertionCitation.query.filter_by(
        insertion_id=insertion.id
    ).all()
    assert len(citations) == 3
    assert {c.takeoff_package_item_id for c in citations} == {
        item.id for item in package.items
    }


def test_existing_cost_item_mapping(app):
    seed, package = _approved_package()
    cost_item = _cost_item()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    insertion = insert_takeoff_estimate_mapping(
        **_insert_kwargs(
            package,
            version,
            section,
            target_kind="cost_item",
            target_id=cost_item.id,
        )
    )
    line = EstimateLineItem.query.get(insertion.estimate_line_item_id)
    assert line.line_type == "Cost Item"
    assert line.cost_item_id == cost_item.id
    assert line.unit == "ea"
    assert TakeoffEstimateInsertionCitation.query.filter_by(
        insertion_id=insertion.id
    ).count() == 3


def test_non_approved_package_rejected(app):
    seed = _seed_eligible_plan()
    run = _review_fixture(_start_run(seed))
    draft = create_draft_package(
        organization_id=seed["organization_id"],
        run_id=run.id,
        created_by="office-reviewer",
    )
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    with pytest.raises(TakeoffEstimateMappingError, match="approved"):
        insert_takeoff_estimate_mapping(
            **_insert_kwargs(
                draft,
                version,
                section,
                target_kind="assembly",
                target_id=assembly.id,
            )
        )
    assert EstimateLineItem.query.count() == 0
    assert TakeoffEstimateInsertion.query.count() == 0


def test_same_project_enforced(app):
    _seed_a, package = _approved_package(name="Project A")
    seed_b = _seed_eligible_plan(name="Project B")
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(
        seed_b["project_id"], number="EST-2026-2699"
    )
    with pytest.raises(TakeoffEstimateMappingError, match="same project"):
        insert_takeoff_estimate_mapping(
            **_insert_kwargs(
                package,
                version,
                section,
                target_kind="assembly",
                target_id=assembly.id,
            )
        )
    assert EstimateLineItem.query.count() == 0


def test_editable_draft_required_and_locked_rejected(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    lock_version(version)
    with pytest.raises(TakeoffEstimateMappingError, match="locked"):
        insert_takeoff_estimate_mapping(
            **_insert_kwargs(
                package,
                version,
                section,
                target_kind="assembly",
                target_id=assembly.id,
            )
        )
    version.is_locked = False
    version.status = "In Review"
    db.session.commit()
    with pytest.raises(TakeoffEstimateMappingError, match="editable Draft"):
        insert_takeoff_estimate_mapping(
            **_insert_kwargs(
                package,
                version,
                section,
                target_kind="assembly",
                target_id=assembly.id,
            )
        )


def test_issued_version_rejected(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    set_version_status(version, "Issued")
    with pytest.raises(TakeoffEstimateMappingError, match="locked"):
        insert_takeoff_estimate_mapping(
            **_insert_kwargs(
                package,
                version,
                section,
                target_kind="assembly",
                target_id=assembly.id,
            )
        )
    assert TakeoffEstimateInsertion.query.count() == 0


def test_existing_section_required(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    with pytest.raises(TakeoffEstimateMappingError, match="section"):
        insert_takeoff_estimate_mapping(
            organization_id=DEFAULT_ORGANIZATION_ID,
            package_id=package.id,
            estimate_version_id=version.id,
            estimate_section_id=section.id + 999,
            target_kind="assembly",
            target_id=assembly.id,
            confirmed_quantity="3",
            confirmed_unit="ea",
            client_insertion_key=str(uuid.uuid4()),
            actor_display_name="office-reviewer",
        )


def test_human_quantity_and_unit_confirmation_required(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    with pytest.raises(TakeoffEstimateMappingError, match="quantity must be confirmed"):
        insert_takeoff_estimate_mapping(
            **_insert_kwargs(
                package,
                version,
                section,
                target_kind="assembly",
                target_id=assembly.id,
                qty="",
            )
        )
    with pytest.raises(TakeoffEstimateMappingError, match="unit must be confirmed"):
        insert_takeoff_estimate_mapping(
            **_insert_kwargs(
                package,
                version,
                section,
                target_kind="assembly",
                target_id=assembly.id,
                unit="",
            )
        )
    assert EstimateLineItem.query.count() == 0


def test_n_source_items_one_line_n_citations_and_frozen_provenance(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    original_geoms = {item.id: dict(item.geometry_data) for item in package.items}
    insertion = insert_takeoff_estimate_mapping(
        **_insert_kwargs(
            package,
            version,
            section,
            target_kind="assembly",
            target_id=assembly.id,
        )
    )
    assert EstimateLineItem.query.count() == 1
    assert TakeoffEstimateInsertion.query.count() == 1
    citations = TakeoffEstimateInsertionCitation.query.filter_by(
        insertion_id=insertion.id
    ).all()
    assert len(citations) == 3
    for citation in citations:
        assert citation.geometry_data == original_geoms[citation.takeoff_package_item_id]
        assert citation.takeoff_run_id is not None
        assert citation.plan_document_id is not None
        assert citation.page_index is not None
        assert citation.review_status in {"accepted", "adjusted"}
    assert insertion.element_type == "INTERIOR_DOOR_OPENING"
    assert insertion.suggested_unit == "count"
    assert insertion.confirmed_unit == "ea"
    assert insertion.suggested_quantity == Decimal("3.0000")
    assert insertion.confirmed_quantity == Decimal("3")
    assert insertion.actor_display_name == "office-reviewer"
    assert insertion.provenance["source_takeoff_package_id"] == package.id
    assert insertion.provenance["destination_estimate_line_item_id"] == insertion.estimate_line_item_id


def test_package_unchanged_after_insert(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    before = {
        "status": package.status,
        "approved_total": package.approved_total,
        "approved_unit": package.approved_unit,
        "item_ids": [item.id for item in package.items],
        "qtys": [item.reviewed_quantity for item in package.items],
    }
    insert_takeoff_estimate_mapping(
        **_insert_kwargs(
            package,
            version,
            section,
            target_kind="assembly",
            target_id=assembly.id,
        )
    )
    db.session.refresh(package)
    assert package.status == before["status"] == "approved"
    assert package.approved_total == before["approved_total"]
    assert package.approved_unit == before["approved_unit"]
    assert [item.id for item in package.items] == before["item_ids"]
    assert [item.reviewed_quantity for item in package.items] == before["qtys"]


def test_later_package_rerun_does_not_mutate_insertion(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    insertion = insert_takeoff_estimate_mapping(
        **_insert_kwargs(
            package,
            version,
            section,
            target_kind="assembly",
            target_id=assembly.id,
        )
    )
    frozen = [
        (c.takeoff_package_item_id, c.reviewed_quantity, dict(c.geometry_data))
        for c in TakeoffEstimateInsertionCitation.query.filter_by(
            insertion_id=insertion.id
        ).order_by(TakeoffEstimateInsertionCitation.id)
        .all()
    ]
    run2 = _review_fixture(_start_run(seed))
    pkg2 = create_draft_package(
        organization_id=seed["organization_id"],
        run_id=run2.id,
        created_by="office-reviewer",
    )
    later = approve_package(
        organization_id=seed["organization_id"],
        package_id=pkg2.id,
        approved_by="office-reviewer",
    )
    db.session.refresh(package)
    assert package.status == "superseded"
    assert later.id != package.id
    db.session.refresh(insertion)
    still = [
        (c.takeoff_package_item_id, c.reviewed_quantity, dict(c.geometry_data))
        for c in TakeoffEstimateInsertionCitation.query.filter_by(
            insertion_id=insertion.id
        ).order_by(TakeoffEstimateInsertionCitation.id)
        .all()
    ]
    assert still == frozen
    assert insertion.takeoff_package_id == package.id
    with pytest.raises(TakeoffEstimateMappingError, match="approved"):
        insert_takeoff_estimate_mapping(
            **_insert_kwargs(
                package,
                version,
                section,
                target_kind="assembly",
                target_id=assembly.id,
                key=str(uuid.uuid4()),
            )
        )


def test_duplicate_grouping_prevention(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    insert_takeoff_estimate_mapping(
        **_insert_kwargs(
            package,
            version,
            section,
            target_kind="assembly",
            target_id=assembly.id,
        )
    )
    with pytest.raises(TakeoffEstimateMappingError, match="already mapped"):
        insert_takeoff_estimate_mapping(
            **_insert_kwargs(
                package,
                version,
                section,
                target_kind="assembly",
                target_id=assembly.id,
                key=str(uuid.uuid4()),
            )
        )
    assert EstimateLineItem.query.count() == 1
    assert TakeoffEstimateInsertion.query.count() == 1


def test_client_insertion_idempotency(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    key = str(uuid.uuid4())
    first = insert_takeoff_estimate_mapping(
        **_insert_kwargs(
            package,
            version,
            section,
            target_kind="assembly",
            target_id=assembly.id,
            key=key,
        )
    )
    second = insert_takeoff_estimate_mapping(
        **_insert_kwargs(
            package,
            version,
            section,
            target_kind="assembly",
            target_id=assembly.id,
            key=key,
        )
    )
    assert second.id == first.id
    assert EstimateLineItem.query.count() == 1
    assert TakeoffEstimateInsertion.query.count() == 1


def test_transaction_rollback_no_orphan_line_on_provenance_failure(app, monkeypatch):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    original_add = db.session.add

    def exploding_add(obj):
        if isinstance(obj, TakeoffEstimateInsertion):
            raise RuntimeError("synthetic provenance failure")
        return original_add(obj)

    monkeypatch.setattr(db.session, "add", exploding_add)
    with pytest.raises(RuntimeError, match="synthetic provenance failure"):
        insert_takeoff_estimate_mapping(
            **_insert_kwargs(
                package,
                version,
                section,
                target_kind="assembly",
                target_id=assembly.id,
            )
        )
    db.session.rollback()
    assert EstimateLineItem.query.count() == 0
    assert TakeoffEstimateInsertion.query.count() == 0
    assert TakeoffEstimateInsertionCitation.query.count() == 0
    db.session.refresh(package)
    assert package.status == "approved"


def test_no_labour_or_pricing_snapshot_or_material_requirement(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    insert_takeoff_estimate_mapping(
        **_insert_kwargs(
            package,
            version,
            section,
            target_kind="assembly",
            target_id=assembly.id,
        )
    )
    assert EstimateLabourSnapshot.query.count() == 0
    assert EstimatePricingSnapshot.query.count() == 0
    tables = set(sa_inspect(db.engine).get_table_names())
    assert "material_requirements" not in tables
    insertion = TakeoffEstimateInsertion.query.one()
    assert insertion.provenance.get("supplier") is None
    assert insertion.provenance.get("sku") is None
    line = EstimateLineItem.query.get(insertion.estimate_line_item_id)
    assert line.cost_item_id is None


def test_no_automatic_estimate_or_version_creation(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    with pytest.raises(TakeoffEstimateMappingError, match="Estimate version not found"):
        insert_takeoff_estimate_mapping(
            organization_id=DEFAULT_ORGANIZATION_ID,
            package_id=package.id,
            estimate_version_id=999999,
            estimate_section_id=1,
            target_kind="assembly",
            target_id=assembly.id,
            confirmed_quantity="3",
            confirmed_unit="ea",
            client_insertion_key=str(uuid.uuid4()),
            actor_display_name="office-reviewer",
        )
    assert Estimate.query.count() == 0
    assert EstimateVersion.query.count() == 0


def test_preview_does_not_write(app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    preview = preview_takeoff_estimate_mapping(
        organization_id=DEFAULT_ORGANIZATION_ID,
        package_id=package.id,
        estimate_version_id=version.id,
        estimate_section_id=section.id,
        target_kind="assembly",
        target_id=assembly.id,
        confirmed_quantity="3",
        confirmed_unit="ea",
    )
    assert preview["confirmed_unit"] == "ea"
    assert preview["unit_differs"] is True
    assert EstimateLineItem.query.count() == 0
    assert TakeoffEstimateInsertion.query.count() == 0


def test_http_map_workflow_and_non_approved_rejected(client, app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    listing = client.get(
        f"/projects/{seed['project_id']}/plans/takeoff/packages/{package.id}"
    )
    assert listing.status_code == 200
    assert b"Map to estimate" in listing.data
    mapped = client.get(
        f"/projects/{seed['project_id']}/plans/takeoff/packages/{package.id}/map"
    )
    assert mapped.status_code == 200
    assert b"Map to estimate" in mapped.data
    assert b"Insert into estimate" not in mapped.data
    preview = client.post(
        f"/projects/{seed['project_id']}/plans/takeoff/packages/{package.id}/map",
        data={
            "intent": "preview",
            "target_kind": "assembly",
            "target_assembly_id": str(assembly.id),
            "estimate_version_id": str(version.id),
            "estimate_section_id": str(section.id),
            "confirmed_quantity": "3",
            "confirmed_unit": "ea",
            "client_insertion_key": str(uuid.uuid4()),
            "actor": "office-reviewer",
        },
        follow_redirects=True,
    )
    assert preview.status_code == 200
    assert b"Proposed commercial line" in preview.data
    assert b"Insert into estimate" in preview.data
    assert EstimateLineItem.query.count() == 0

    seed_draft = _seed_eligible_plan(name="Draft only")
    run = _review_fixture(_start_run(seed_draft))
    draft = create_draft_package(
        organization_id=seed_draft["organization_id"],
        run_id=run.id,
        created_by="office-reviewer",
    )
    blocked = client.get(
        f"/projects/{seed_draft['project_id']}/plans/takeoff/packages/{draft.id}/map",
        follow_redirects=True,
    )
    assert blocked.status_code == 200
    assert b"Only an approved take-off package" in blocked.data


def test_http_insert_creates_line_and_empty_destination_copy(client, app):
    seed, package = _approved_package()
    assembly, _cost = _door_assembly()
    _estimate, version, section = _draft_with_section(seed["project_id"])
    key = str(uuid.uuid4())
    inserted = client.post(
        f"/projects/{seed['project_id']}/plans/takeoff/packages/{package.id}/map",
        data={
            "intent": "insert",
            "target_kind": "assembly",
            "target_assembly_id": str(assembly.id),
            "estimate_version_id": str(version.id),
            "estimate_section_id": str(section.id),
            "confirmed_quantity": "3",
            "confirmed_unit": "ea",
            "client_insertion_key": key,
            "actor": "office-reviewer",
        },
        follow_redirects=True,
    )
    assert inserted.status_code == 200
    assert b"Inserted estimate line" in inserted.data
    assert EstimateLineItem.query.count() == 1
    retry = client.post(
        f"/projects/{seed['project_id']}/plans/takeoff/packages/{package.id}/map",
        data={
            "intent": "insert",
            "target_kind": "assembly",
            "target_assembly_id": str(assembly.id),
            "estimate_version_id": str(version.id),
            "estimate_section_id": str(section.id),
            "confirmed_quantity": "3",
            "confirmed_unit": "ea",
            "client_insertion_key": key,
            "actor": "office-reviewer",
        },
        follow_redirects=True,
    )
    assert retry.status_code == 200
    assert EstimateLineItem.query.count() == 1

    seed_empty, empty_pkg = _approved_package(name="No estimate project")
    empty_page = client.get(
        f"/projects/{seed_empty['project_id']}/plans/takeoff/packages/{empty_pkg.id}/map"
    )
    assert empty_page.status_code == 200
    assert b"No editable Draft on this project" in empty_page.data
    assert b"Open Estimates" in empty_page.data
    assert Estimate.query.filter_by(project_id=seed_empty["project_id"]).count() == 0


def test_existing_builder_commit_behavior_preserved(app):
    seed, _package = _approved_package()
    _assembly, cost = _door_assembly()
    _estimate, version, section = _draft_with_section(
        seed["project_id"], number="EST-2026-2610"
    )
    line = add_cost_item_line(section, cost_item_id=cost.id, quantity=2)
    assert line.id is not None
    assert EstimateLineItem.query.get(line.id) is not None
    assert line.unit == cost.unit
    assert TakeoffEstimateInsertion.query.count() == 0
