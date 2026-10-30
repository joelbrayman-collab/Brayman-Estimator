"""The work page exposes the governed work-package decisions (Joel, 30 Oct 2026).

Excluding work from Brayman's price keeps every line and records who does it instead; including it again restores
it. Delivery method and the shared general-conditions rule are set on the same page. Synthetic data only.
"""

from decimal import Decimal

from app import db
from app.models import EstimateLineItem
from app.services import guided_estimating as G
from app.services import work_packages as WP
from app.services.estimate_builder import add_manual_line
from tests.test_selected_work import _add, _project, _row, _scope, env  # noqa: F401  (the fixture)


def _post(d, project, **data):
    return d.post(f"/projects/{project.id}/guided/scope", data=data)


def _setup(d, name):
    project = _project(d, name)
    _add(d, project, "work_siding", custom="Exterior trim")
    guided = _scope(project)
    version = G.editable_version(guided)
    for row in WP.packages(guided):
        add_manual_line(G.section_for(row, version, create=True), line_type="Custom",
                        description=f"{row.display_name} materials (synthetic)", quantity=1, unit="ls",
                        unit_cost=Decimal("1000"))
    db.session.commit()
    return project, version


def test_work_page_excludes_and_includes_without_deleting(env):
    _app, d, _ben = env
    project, version = _setup(d, "Work package page (synthetic)")
    page = d.get(f"/projects/{project.id}/guided/scope")
    assert 'data-exclude-work="work_siding"' in page and "In Brayman's scope" in page
    siding = _row(project, "Siding")
    lines = EstimateLineItem.query.count()
    _post(d, project, action="exclude", row_id=siding.id, party="NAMED", party_name="Lockwood",
          reason="Owner's siding crew (synthetic)")
    siding = _row(project, "Siding")
    assert not siding.is_included and WP.responsible_label(siding) == "Lockwood"
    assert EstimateLineItem.query.count() == lines
    page = d.get(f"/projects/{project.id}/guided/scope")
    assert "Excluded from Brayman Construction scope; by Lockwood" in page
    assert 'data-include-work="work_siding"' in page
    _post(d, project, action="responsible_party", row_id=siding.id, party="CLIENT")
    assert WP.responsible_label(_row(project, "Siding")) == "Owner / Client"
    _post(d, project, action="include", row_id=siding.id)
    assert _row(project, "Siding").is_included and EstimateLineItem.query.count() == lines


def test_named_party_needs_a_name_and_the_page_says_so(env):
    _app, d, _ben = env
    project, _version = _setup(d, "Work package named (synthetic)")
    siding = _row(project, "Siding")
    _post(d, project, action="exclude", row_id=siding.id, party="NAMED", party_name="")
    assert "Name the party responsible for the excluded work." in d.flashes()
    assert _row(project, "Siding").is_included


def test_delivery_method_and_shared_rule_from_the_page(env):
    _app, d, _ben = env
    project, _version = _setup(d, "Work package delivery (synthetic)")
    trim = _row(project, "Exterior trim")
    _post(d, project, action="delivery_method", row_id=trim.id, delivery_method="MATERIAL_ONLY")
    assert WP.delivery_label(_row(project, "Exterior trim")) == "Material only"
    _post(d, project, action="shared", row_id=trim.id, shared_rule="WHILE_ANY_INCLUDED")
    assert _row(project, "Exterior trim").is_shared
    page = d.get(f"/projects/{project.id}/guided/scope")
    assert 'data-shared="' in page and 'data-unset-shared="' in page
    _post(d, project, action="shared", row_id=trim.id, shared_rule="")
    assert not _row(project, "Exterior trim").is_shared


def test_decisions_are_refused_once_the_version_is_locked(env):
    _app, d, _ben = env
    project, version = _setup(d, "Work package locked (synthetic)")
    version.is_locked = True
    db.session.commit()
    page = d.get(f"/projects/{project.id}/guided/scope")
    assert 'disabled data-exclude-work="work_siding"' in page
    siding = _row(project, "Siding")
    _post(d, project, action="exclude", row_id=siding.id, party="BY_OTHERS")
    assert any("new version" in message for message in d.flashes())
    assert _row(project, "Siding").is_included
