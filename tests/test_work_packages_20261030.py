"""Governed work packages and Paulusse parity in the application (Joel, 30 Oct 2026).

Selected work is the governed work package. Excluding a package is non-destructive: every line stays, and only
the package's participation in Brayman's price changes. Shared general conditions count while any contractor work
is included. The accepted Paulusse REV2 figures are reproduced exactly by the application engine; they are
acceptance data and are never adjusted to make a test pass.
"""

from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, EstimateLineItem, EstimateSection, GuidedEstimateEvent, Project
from app.models.guided_estimating import (
    COMMERCIAL_EXCLUDED,
    COMMERCIAL_INCLUDED,
    PARTY_BY_OTHERS,
    PARTY_CLIENT,
    PARTY_NAMED,
    SHARED_WHILE_ANY_INCLUDED,
)
from app.services import estimate_labour_hours as labour
from app.services import guided_estimating as G
from app.services import selected_work as SW
from app.services import work_packages as WP
from app.services.estimate_builder import add_manual_line
from app.services.estimate_economics import economics, set_project_pricing
from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard, promote_direct_labour_cost_rate
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
from app.services.pricing_engine import create_pricing_policy
from tests.proposal_issue_support import approve_for_issue

JOEL = "Joel Brayman"
M = Decimal

# Paulusse REV3 (the acceptance reference since 30 Oct 2026; REV2 is superseded, its files untouched): each work
# package's material, equipment and other cost, and its labour activities (hours, crew), exactly as the REV3
# Estimate Builder carries them. Hardie touch-up is Ben's 3 people x 1.5 days = 36 hours.
PAULUSSE = (
    ("General conditions", "800.00", (("Set-up and protection", "8.00", 3), ("Receive and stage deliveries", "4.00", 3),
                                      ("Final clean-up, magnet sweep, walk-through", "8.00", 3))),
    ("Removal & substrate preparation", "700.00", (("Strip existing siding, load bin", "19.55", 3),
                                                   ("Remove aluminum corners and trim", "4.45", 3),
                                                   ("Inspect sheathing, re-nail", "6.00", 3))),
    ("Weather barrier & flashing", "1136.00", (("Typar house wrap", "10.00", 3), ("Z flashing", "8.00", 3))),
    ("HardiePanel siding & battens", "10721.28", (("HardiePanel vertical siding", "62.12", 3),
                                                  ("HardieTrim battens", "21.88", 3))),
    ("Exterior trim", "1896.75", (("Corner trim", "6.25", 3), ("Window trim", "18.08", 3), ("Door trim", "5.75", 3),
                                  ("Drip cap", "1.75", 3), ("Freeze boards", "4.17", 3))),
    ("Aluminum soffit & fascia", "1712.57", (("Vented soffit", "10.00", 3), ("J-channel", "5.25", 3),
                                             ("Fascia", "20.75", 3))),
    ("Estate Stone veneer & sills", "2312.72", (("Lath and scratch coat", "3.70", 2), ("Set stone and point", "21.30", 2),
                                                ("Set limestone sills", "4.00", 2), ("Angle iron", "3.00", 2))),
    ("Sealant & touch-up", "268.00", (("ColorMatch sealant", "12.00", 3), ("Hardie touch-up", "36.00", 3))),
)

# Accepted REV3 results: (hours, direct cost, selling price, HST, customer total).
BASELINE = (M("304"), M("42347.32"), M("49820.38"), M("6476.65"), M("56297.03"))  # CASE A, winter off
EXCLUDED_ALONE = {
    "Removal & substrate preparation": (M("274"), M("39397.32"), M("46349.79"), M("6025.47"), M("52375.26")),
    "Weather barrier & flashing": (M("286"), M("39861.32"), M("46895.67"), M("6096.44"), M("52992.11")),
    "HardiePanel siding & battens": (M("220"), M("25326.04"), M("29795.34"), M("3873.39"), M("33668.73")),
    "Exterior trim": (M("268"), M("37750.57"), M("44412.44"), M("5773.62"), M("50186.06")),
    "Aluminum soffit & fascia": (M("268"), M("37934.75"), M("44629.12"), M("5801.79"), M("50430.91")),
    "Estate Stone veneer & sills": (M("272"), M("37634.60"), M("44276.00"), M("5755.88"), M("50031.88")),
    "Sealant & touch-up": (M("256"), M("38479.32"), M("45269.79"), M("5885.07"), M("51154.86")),
}
WINTER_B = (M("364.80"), M("47467.32"), M("55843.91"), M("7259.71"), M("63103.62"))
WINTER_C_NO_STONE = (M("326.40"), M("42190.60"), M("49636.00"), M("6452.68"), M("56088.68"))
WINTER_D_30_50 = (M("395.23"), M("50056.30"), M("58889.76"), M("7655.67"), M("66545.43"))


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
                              "WTF_CSRF_ENABLED": False})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_org_001_direct_labour_cost_rate_standard()
        promote_direct_labour_cost_rate("75", approved_by=JOEL, reason="Brayman $75 (30 Oct 2026)", organization_id=ORG)
        create_pricing_policy(policy_code="ORG-001-TRUE-GM-15", method="TRUE_GROSS_MARGIN", actor=JOEL,
                              target_gross_margin=M("0.15"), tax_jurisdiction="CA-ON", tax_percent=M("13"),
                              overhead_treatment="UNSPECIFIED", profit_treatment="UNSPECIFIED",
                              contingency_visibility="UNSPECIFIED", provenance="docs/pricing-policy.md", is_default=True)
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


def build_paulusse():
    """Paulusse through selected work: eight packages, each with its cost line and labour hours."""
    client = Client(name="Lockwood Brothers (synthetic)", organization_id=ORG)
    db.session.add(client)
    db.session.commit()
    project = Project(name="Paulusse & Bonokoski (synthetic)", client_id=client.id, organization_id=ORG,
                      status="Estimating")
    db.session.add(project)
    db.session.commit()
    guided = SW.ensure_scope(ORG, project.id, actor=JOEL)
    for name, _cost, _labour in PAULUSSE:
        SW.add_work(guided, custom_name=name, actor=JOEL)
    packages = {p.display_name: p for p in WP.packages(guided)}
    version = G.editable_version(guided)
    for name, cost, labour_rows in PAULUSSE:
        section = G.section_for(packages[name], version, create=True)
        add_manual_line(section, line_type="Custom", description=f"{name}: materials, equipment and other",
                        quantity=1, unit="ls", unit_cost=M(cost))
        for n, (activity, hours, crew) in enumerate(labour_rows, 1):
            # an ordinary labour line (LAB-, hours x the version's labour rate), as the labour-hours page writes it
            line = add_manual_line(section, line_type="Custom", description=f"Labour — {activity}", quantity=M(hours),
                                   unit=labour.LABOUR_UNIT, unit_cost=M("75.00"),
                                   code=f"{labour.LABOUR_CODE_PREFIX}{packages[name].id}-{n}")
            line.crew_size = crew
    db.session.commit()
    WP.set_shared(packages["General conditions"], actor=JOEL, rule=SHARED_WHILE_ANY_INCLUDED)
    db.session.commit()
    approve_for_issue(version, actor=JOEL)
    db.session.commit()
    return guided, version, packages


def figures(version):
    e = economics(version)
    return (e["labour_hours"] if "labour_hours" in e else e["hours"], e["direct_cost"], e["selling_price"], e["tax"],
            e["customer_total"])


def test_selected_work_sections_are_linked_durably(app):
    guided, version, packages = build_paulusse()
    for package in packages.values():
        section = EstimateSection.query.filter_by(estimate_version_id=version.id, guided_stage_id=package.id).one()
        assert section.name == package.section_name
    # The link survives a section rename: no name matching.
    section = G.section_for(packages["Exterior trim"], version)
    section.name = "Trim (renamed by the estimator)"
    db.session.commit()
    assert G.section_for(packages["Exterior trim"], version).id == section.id


def test_paulusse_baseline_is_reproduced_exactly(app):
    _guided, version, _packages = build_paulusse()
    assert figures(version) == BASELINE
    assert economics(version)["applied"]


@pytest.mark.parametrize("name", list(EXCLUDED_ALONE))
def test_excluding_each_package_matches_rev2_and_keeps_everything(app, name):
    _guided, version, packages = build_paulusse()
    package = packages[name]
    lines_before = [(line.id, line.quantity, line.unit_cost, line.extended_cost)
                    for line in WP.package_lines(package, version)]
    WP.exclude_work(package, actor=JOEL)
    assert package.commercial_status == COMMERCIAL_EXCLUDED and package.responsible_party == PARTY_BY_OTHERS
    assert figures(version) == EXCLUDED_ALONE[name]
    lines_after = [(line.id, line.quantity, line.unit_cost, line.extended_cost)
                   for line in WP.package_lines(package, version)]
    assert lines_after == lines_before  # construction intelligence untouched
    assert all(line.sell_price == M("0.00") for line in WP.package_lines(package, version))
    WP.include_work(package, actor=JOEL)
    assert figures(version) == BASELINE


def test_customer_scope_names_the_excluded_work_and_the_responsible_party(app):
    _guided, version, packages = build_paulusse()
    removal = packages["Removal & substrate preparation"]
    WP.exclude_work(removal, actor=JOEL)
    scope = WP.customer_scope(version)
    assert [e["name"] for e in scope["excluded"]] == ["Removal & substrate preparation"]
    assert scope["excluded"][0]["text"] == "Excluded from Brayman Construction scope / By Others"
    assert "Removal & substrate preparation" not in [e["name"] for e in scope["included"]]
    assert sum(e["sell_price"] for e in scope["included"]) == M("46349.79")
    WP.set_responsible_party(removal, actor=JOEL, party=PARTY_NAMED, party_name="Lockwood")
    assert WP.customer_scope(version)["excluded"][0]["text"] == "Excluded from Brayman Construction scope; by Lockwood"
    WP.set_responsible_party(removal, actor=JOEL, party=PARTY_CLIENT)
    assert WP.responsible_label(removal) == "Owner / Client"
    events = [e.event for e in GuidedEstimateEvent.query.filter_by(stage_id=removal.id)]
    assert "WORK_EXCLUDED" in events and events.count("RESPONSIBLE_PARTY") == 2


def test_rate_and_margin_work_with_an_exclusion(app):
    _guided, version, packages = build_paulusse()
    WP.exclude_work(packages["Removal & substrate preparation"], actor=JOEL)
    set_project_pricing(version, actor=JOEL, labour_rate="80", reason="Union crew (synthetic)")
    db.session.commit()
    assert figures(version)[-1] == M("54196.55")
    set_project_pricing(version, actor=JOEL, margin_percent="20", reason="Tight schedule (synthetic)")
    db.session.commit()
    assert figures(version)[-1] == M("57583.84")


def test_general_conditions_drop_out_only_when_no_contractor_work_remains(app):
    _guided, version, packages = build_paulusse()
    productive = [p for name, p in packages.items() if name != "General conditions"]
    for package in productive[:-1]:
        WP.exclude_work(package, actor=JOEL)
    assert WP.package_participates(packages["General conditions"])
    WP.exclude_work(productive[-1], actor=JOEL)
    assert not WP.package_participates(packages["General conditions"])
    hours, direct, selling, tax, total = figures(version)
    assert (direct, selling, total) == (M("0.00"), M("0.00"), M("0.00"))
    for package in productive:
        WP.include_work(package, actor=JOEL)
    assert figures(version) == BASELINE


def test_exclusion_needs_a_person_and_an_editable_version(app):
    _guided, version, packages = build_paulusse()
    with pytest.raises(WP.WorkPackageError, match="person"):
        WP.exclude_work(packages["Exterior trim"], actor="system")
    with pytest.raises(WP.WorkPackageError, match="Name the party"):
        WP.exclude_work(packages["Exterior trim"], actor=JOEL, party=PARTY_NAMED)
    version.is_locked = True
    db.session.commit()
    with pytest.raises(WP.WorkPackageError, match="new version"):
        WP.exclude_work(packages["Exterior trim"], actor=JOEL)


def test_lines_are_never_deleted_by_exclusion(app):
    _guided, version, packages = build_paulusse()
    count = EstimateLineItem.query.count()
    for package in packages.values():
        WP.exclude_work(package, actor=JOEL)
    assert EstimateLineItem.query.count() == count
    assert all(p.commercial_status == COMMERCIAL_EXCLUDED for p in packages.values())
    for package in packages.values():
        WP.include_work(package, actor=JOEL)
    assert all(p.commercial_status == COMMERCIAL_INCLUDED for p in packages.values())
    assert figures(version) == BASELINE


# ---------------------------------------------------------------------------------------------- Gate 1 (S4)
def _sign_off(version):
    from app.services.proposal_acceptance import sign_off_estimate
    from app.services.proposals import create_proposal_template

    create_proposal_template(name="Paulusse template (synthetic)", is_active=True, is_default=True,
                             default_intro_text="Intro", default_payment_terms="As stated")

    class _Joel:
        id = None
        display_name = JOEL
        email = "joel@example.invalid"

    return sign_off_estimate(version, user=_Joel())


def test_gate_1_freezes_what_was_approved_with_a_fingerprint(app):
    from app.services import estimate_approval as A

    _guided, version, packages = build_paulusse()
    WP.exclude_work(packages["Removal & substrate preparation"], actor=JOEL)
    for name, package in packages.items():
        if name != "Removal & substrate preparation":
            assert G.complete_stage(package.guided_estimate, package, actor=JOEL)[0], name
    # Excluded work needs no cost confirmation: its exclusion is the recorded decision.
    assert not G.guided_issue_blockers(version)
    _sign_off(version)
    record = A.approval_for(version)
    summary = record.summary
    assert record.approved_by_name == JOEL and len(record.fingerprint) == 64
    assert summary["customer_total"] == "52375.26" and summary["labour_hours"] == "274.00"
    assert [x["name"] for x in summary["excluded"]] == ["Removal & substrate preparation"]
    assert summary["excluded"][0]["text"] == "Excluded from Brayman Construction scope / By Others"
    assert A.verify(version)["matches"] is True
    with pytest.raises(A.EstimateApprovalError, match="cannot be unlocked"):
        from app.services.estimates import unlock_version

        unlock_version(version)
    with pytest.raises(WP.WorkPackageError, match="new version"):
        WP.include_work(packages["Removal & substrate preparation"], actor=JOEL)
    with pytest.raises(A.EstimateApprovalError, match="why"):
        A.create_successor_version(version, actor=JOEL, reason="")
    successor = A.create_successor_version(version, actor=JOEL, reason="Owner wants the removal back (synthetic)")
    assert successor.id != version.id and A.approval_for(successor) is None
    assert A.verify(version)["matches"] is True  # the approved version is untouched


# ---------------------------------------------------------------------------------------------- customer outputs (S5)
def test_proposal_lists_included_and_excluded_work_and_prices_only_included(app):
    from pypdf import PdfReader
    from io import BytesIO

    from app.services.proposal_pdf import generate_proposal_pdf

    _guided, version, packages = build_paulusse()
    removal = packages["Removal & substrate preparation"]
    WP.exclude_work(removal, actor=JOEL, party=PARTY_NAMED, party_name="Lockwood")
    for name, package in packages.items():
        if package is not removal:
            G.complete_stage(package.guided_estimate, package, actor=JOEL)
    proposal = _sign_off(version)
    assert "Removal & substrate preparation" not in [s.name for s in proposal.sections]
    assert len(proposal.sections) == 7
    assert proposal.total == M("52375.26")
    scope = proposal.scope_snapshot
    assert [x["name"] for x in scope["excluded"]] == ["Removal & substrate preparation"]
    assert scope["excluded"][0]["text"] == "Excluded from Brayman Construction scope; by Lockwood"
    assert len(scope["included"]) == 7
    text = " ".join(page.extract_text() or "" for page in PdfReader(BytesIO(generate_proposal_pdf(proposal).getvalue())).pages)
    text = " ".join(text.split())
    assert "Included in Brayman Construction scope" in text and "Excluded / By Others" in text
    assert "Removal & substrate preparation: Excluded from Brayman Construction scope; by Lockwood" in text


def test_contractor_estimate_package_is_landscape_and_matches_the_engine(app):
    from io import BytesIO

    from pypdf import PdfReader

    from app.services.contractor_estimate_package import build_contractor_estimate_package, package_rows

    _guided, version, packages = build_paulusse()
    WP.exclude_work(packages["Estate Stone veneer & sills"], actor=JOEL, party=PARTY_CLIENT)
    rows = {r["name"]: r for r in package_rows(version)}
    assert rows["Estate Stone veneer & sills"]["status"] == "Excluded · Owner / Client"
    assert sum(r["sell"] for r in rows.values() if r["participates"]) == M("44276.00")
    assert sum(r["hours"] for r in rows.values() if r["participates"]) == M("272")
    reader = PdfReader(BytesIO(build_contractor_estimate_package(version, generated_by=JOEL)))
    assert len(reader.pages) >= 3
    for page in reader.pages:
        box = page.mediabox
        assert float(box.width) > float(box.height)  # every page landscape
        assert round(float(box.width)) == 1008 and round(float(box.height)) == 612  # legal
    text = " ".join(" ".join(page.extract_text().split()) for page in reader.pages)
    assert "INTERNAL — CONTRACTOR COPY" in text and "$50,031.88" in text and "$44,276.00" in text
    assert "Excluded from Brayman Construction scope; by the Owner / Client" in text
    assert "/AcroForm" not in str(reader.trailer["/Root"])  # plain PDF: no form fields, opens in any viewer


# ---------------------------------------------------------------------------------------------- labour lineage (S6)
def test_work_plan_is_seeded_per_included_package_with_line_lineage(app):
    from app.models import ProjectWorkActivity, ProjectWorkElement
    from app.services.work_structure import seed_project_work_structure

    guided, version, packages = build_paulusse()
    WP.exclude_work(packages["Exterior trim"], actor=JOEL)
    for name, package in packages.items():
        if name != "Exterior trim":
            G.complete_stage(guided, package, actor=JOEL)
    proposal = _sign_off(version)
    proposal.status = "Issued"  # the customer commitment the work plan is built from (synthetic)
    db.session.commit()
    seed_project_work_structure(project_id=guided.project_id, estimate_version_id=version.id, seeded_by=JOEL,
                                organization_id=guided.organization_id)
    elements = ProjectWorkElement.query.filter_by(project_id=guided.project_id).order_by(ProjectWorkElement.sort_order).all()
    assert [e.display_name for e in elements] == [n for n, _c, _l in PAULUSSE if n != "Exterior trim"]
    assert all(e.guided_stage_id == packages[e.display_name].id for e in elements)
    assert sum(Decimal(e.estimated_hours) for e in elements) == M("268")
    for element in elements:
        for activity in ProjectWorkActivity.query.filter_by(project_work_element_id=element.id):
            line = db.session.get(EstimateLineItem, activity.source_estimate_line_item_id)
            assert line is not None and WP.package_of_section(line.section).id == element.guided_stage_id
            assert Decimal(activity.estimated_hours) == Decimal(line.quantity)


# ---------------------------------------------------------------------------------------------- review findings
def test_a_change_on_the_successor_never_changes_the_approved_version(app):
    from app.services import estimate_approval as A

    guided, version, packages = build_paulusse()
    WP.exclude_work(packages["Removal & substrate preparation"], actor=JOEL)
    for name, package in packages.items():
        if name != "Removal & substrate preparation":
            G.complete_stage(guided, package, actor=JOEL)
    _sign_off(version)
    approved_figures = figures(version)
    successor = A.create_successor_version(version, actor=JOEL, reason="Owner adds trim (synthetic)")
    WP.exclude_work(packages["Exterior trim"], actor=JOEL)
    db.session.refresh(version)
    assert figures(version) == approved_figures == EXCLUDED_ALONE["Removal & substrate preparation"]
    assert A.verify(version)["matches"] is True
    assert [x["name"] for x in WP.customer_scope(version)["excluded"]] == ["Removal & substrate preparation"]
    assert {x["name"] for x in WP.customer_scope(successor)["excluded"]} == {"Removal & substrate preparation",
                                                                              "Exterior trim"}
    assert not WP.package_participates(packages["Exterior trim"], successor)
    assert WP.package_participates(packages["Exterior trim"], version)


def test_no_scope_change_or_revision_after_the_customer_accepts(app):
    from app.services import estimate_approval as A

    guided, version, packages = build_paulusse()
    for package in packages.values():
        G.complete_stage(guided, package, actor=JOEL)
    proposal = _sign_off(version)
    proposal.status = "Accepted"
    db.session.commit()
    with pytest.raises(A.EstimateApprovalError, match="change order"):
        A.create_successor_version(version, actor=JOEL, reason="After acceptance (synthetic)")
    with pytest.raises(WP.WorkPackageError, match="change order"):
        WP.exclude_work(packages["Exterior trim"], actor=JOEL)


def test_excluding_work_never_approves_an_unreviewed_cost(app):
    from app.services.estimate_costing import current_costing_snapshot, working_matches_costing_snapshot

    _guided, version, packages = build_paulusse()
    line = WP.package_lines(packages["Exterior trim"], version)[0]
    from app.services.estimate_builder import update_line_item as edit

    edit(line, unit_cost=M("2500.00"))
    db.session.commit()
    before = current_costing_snapshot(version)
    assert not working_matches_costing_snapshot(version, before)
    WP.exclude_work(packages["Sealant & touch-up"], actor=JOEL)
    assert current_costing_snapshot(version).id == before.id  # nobody approved the edited cost on their behalf


def test_work_removed_and_added_again_starts_included(app):
    guided, version, packages = build_paulusse()
    trim = packages["Exterior trim"]
    WP.exclude_work(trim, actor=JOEL, party=PARTY_NAMED, party_name="Lockwood")
    assert not trim.is_included
    trim.responsibility = "NA"  # removed (synthetic shortcut: its lines would otherwise block removal)
    db.session.commit()
    SW.add_work(guided, custom_name="Exterior trim", actor=JOEL)
    assert trim.is_included and trim.responsible_party is None


# ---------------------------------------------------------------------------------------------- winter job (REV3)
def _winter(version, **kw):
    from app.services import winter_job as W

    return W.set_winter_settings(version, actor=JOEL, **kw)


def _propane(version):
    return next((line.extended_cost for section in version.sections for line in section.line_items
                 if line.code == "WINTER-PROPANE"), M("0.00"))


def test_paulusse_rev3_winter_cases_and_the_full_state_sequence(app):
    """REV3 acceptance: A off, B on 20% $35, C stone excluded, back, D 30% $50, off again. No stale values."""
    _guided, version, packages = build_paulusse()
    assert (version.winter_job, version.winter_time_increase_percent, version.propane_per_crew_day) == (
        False, M("20.00"), M("35.00"))  # the approved defaults
    assert figures(version) == BASELINE and _propane(version) == M("0.00")  # CASE A
    _winter(version, winter_job=True)
    assert figures(version) == WINTER_B and _propane(version) == M("560.00")  # CASE B
    WP.exclude_work(packages["Estate Stone veneer & sills"], actor=JOEL)
    assert figures(version) == WINTER_C_NO_STONE and _propane(version) == M("476.00")  # CASE C
    WP.include_work(packages["Estate Stone veneer & sills"], actor=JOEL)
    assert figures(version) == WINTER_B and _propane(version) == M("560.00")  # restored
    _winter(version, increase_percent="30", propane_per_crew_day="50")
    assert figures(version) == WINTER_D_30_50 and _propane(version) == M("866.73")  # CASE D
    _winter(version, increase_percent="20", propane_per_crew_day="35", winter_job=False)
    assert figures(version) == BASELINE and _propane(version) == M("0.00")  # off again, nothing stale
    assert all(line.base_quantity is None for s in version.sections for line in s.line_items)


def test_winter_lineage_and_the_approved_version_keeps_its_winter_values(app):
    from app.services import estimate_approval as A
    from app.services import winter_job as W

    guided, version, packages = build_paulusse()
    _winter(version, winter_job=True)
    touch_up = next(l for l in WP.package_lines(packages["Sealant & touch-up"], version) if l.description.startswith("Labour — Hardie"))
    assert (touch_up.base_quantity, touch_up.quantity, touch_up.extended_cost) == (M("36.0000"), M("43.2000"),
                                                                                   M("3240.00"))
    assert W.summary(version)["crew_days"] == "16.0000"
    for package in packages.values():
        G.complete_stage(guided, package, actor=JOEL)
    proposal = _sign_off(version)
    assert proposal.total == M("63103.62")
    frozen = A.approval_for(version).summary["winter"]
    assert frozen == {"winter_job": True, "winter_time_increase_percent": "20.00", "propane_per_crew_day": "35.00",
                      "hours_per_crew_day": "8.00", "base_labour_hours": "304.00", "adjusted_labour_hours": "364.80",
                      "crew_days": "16.0000", "winter_heat_cost": "560.00"}
    with pytest.raises(W.WinterJobError, match="new version"):
        _winter(version, winter_job=False)
    successor = A.create_successor_version(version, actor=JOEL, reason="Spring start (synthetic)")
    _winter(successor, winter_job=False)
    assert figures(successor) == BASELINE
    assert figures(version) == WINTER_B and A.verify(version)["matches"] is True  # history unchanged


def test_customer_documents_show_the_rev3_total(app):
    from io import BytesIO

    from pypdf import PdfReader

    from app.services.proposal_pdf import generate_proposal_pdf

    guided, version, packages = build_paulusse()
    for package in packages.values():
        G.complete_stage(guided, package, actor=JOEL)
    proposal = _sign_off(version)
    text = " ".join(page.extract_text() or "" for page in PdfReader(BytesIO(generate_proposal_pdf(proposal).getvalue())).pages)
    assert "$56,297.03" in text  # REV3 winter off, through the governed proposal pipeline


def test_winter_hours_drive_the_schedule(app):
    from app.models import ProjectWorkElement
    from app.services import governed_schedule as GS
    from app.services.work_structure import seed_project_work_structure

    guided, version, packages = build_paulusse()
    _winter(version, winter_job=True)
    for package in packages.values():
        G.complete_stage(guided, package, actor=JOEL)
    proposal = _sign_off(version)
    proposal.status = "Accepted"
    db.session.commit()
    seed_project_work_structure(project_id=guided.project_id, estimate_version_id=version.id, seeded_by=JOEL,
                                organization_id=guided.organization_id)
    siding = ProjectWorkElement.query.filter_by(project_id=guided.project_id,
                                                display_name="HardiePanel siding & battens").one()
    assert Decimal(siding.estimated_hours) == M("100.80")  # 84 h x 1.2
    assert GS.element_crew_days(siding) == M("4.2")  # 100.8 h / (3 x 8)
    from datetime import date

    guided.project.anticipated_start = date(2027, 5, 3)
    db.session.commit()
    plan = {row["element"].display_name: row for row in GS.preliminary_schedule(guided.project)}
    assert plan["HardiePanel siding & battens"]["duration_days"] == 5  # 4.2 crew days -> 5 working days


def test_project_pricing_form_sets_the_winter_job(app):
    from tests.auth_fixtures import ensure_office_user, login_office_user

    _guided, version, _packages = build_paulusse()
    ensure_office_user()
    http = app.test_client()
    login_office_user(http)
    url = f"/estimates/{version.estimate_id}/versions/{version.id}"
    page = http.get(url).get_data(as_text=True)
    assert "data-winter-toggle" in page and 'value="20"' in page and 'value="35.00"' in page  # defaults visible when off
    http.post(url + "/project-pricing", data={"labour_rate": "75.00", "margin_percent": "15.00", "winter_form": "1",
                                              "winter_job": "1", "winter_time_increase_percent": "20",
                                              "propane_per_crew_day": "35.00"})
    db.session.expire_all()
    version = db.session.get(type(version), version.id)
    assert version.winter_job and figures(version) == WINTER_B
    assert "data-winter-figures" in http.get(url).get_data(as_text=True)
