"""Workflow Maps (Joel, 21 Oct 2026): the one governed definition and the four places it is shown.

Definition: every destination is a real GET page with exactly the arguments the definition supplies, every
lesson and acceptance test exists and belongs to the right side, every lesson and test is on a stage, roles are
real, no stage is orphaned, steps CalibraytAI does not do have no link.
Pages, per role (contractor owner, office staff, field-only crew, supplier owner, PRO Desk staff, trainee,
training administrator): what each sees, that no forbidden link is shown, that every link shown answers,
organization isolation, supplier privacy, project context, training progress kept, and Cal's answers.
Synthetic data only.
"""

from __future__ import annotations

import json
import re
from html import escape

import pytest
from flask import g

from app import create_app, db
from app.models import Client, Project
from app.models.organization import Organization
from app.training import content as C
from app.training import environment
from app.workflow_map import definition as D

pytestmark = pytest.mark.no_office_auth
PW = {k: f"Synthetic-{k}-training-1" for k in ("ben", "olivia", "kevin", "liam", "darcy", "pat")}
HREF = re.compile(r'href="([^"#]*)(#[^"]*)?"')


# ------------------------------------------------------------------ the definition


@pytest.fixture(scope="module")
def plain_app():
    return create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t"})


def _rules(app):
    rules = {}
    for rule in app.url_map.iter_rules():
        if "GET" in (rule.methods or ()):
            rules.setdefault(rule.endpoint, []).append(rule)
    return rules


def test_every_destination_is_a_real_page_with_the_arguments_it_needs(plain_app):
    rules = _rules(plain_app)
    seen = 0
    for where, dest in D.all_destinations():
        seen += 1
        assert dest.endpoint in rules, f"{where}: {dest.endpoint} is not a GET page"
        args = {arg for arg, _ctx in dest.path}
        assert any(set(r.arguments) == args for r in rules[dest.endpoint]), f"{where}: {dest.endpoint} needs {args}"
        assert dest.requires in D.REQUIREMENTS, where
        assert all(ctx in D.CONTEXTS for _a, ctx in dest.path + dest.query), where
        if dest.path:
            assert dest.fallback and dest.fallback_label, f"{where}: no page to choose the {dest.needs}"
            assert any(not r.arguments for r in rules[dest.fallback]), f"{where}: fallback {dest.fallback}"
        assert dest.label.startswith("Open "), where
    assert seen > 120


def test_every_lesson_and_acceptance_test_exists_on_the_right_side_and_is_on_a_stage():
    lessons = {lesson.key: m for m in C.modules() for lesson in m.lessons}
    cases = {c.key: c for c in C.uat_cases()}
    for s in D.STAGES:
        side = C.PATHWAY_SUPPLIER if s.journey.startswith("supplier") else C.PATHWAY_CONTRACTOR
        keys = list(s.lessons) + [x.lesson for x in s.substeps if x.lesson]
        for key in keys:
            assert key in lessons, f"{s.id}: lesson {key}"
            assert lessons[key].pathway == side, f"{s.id}: {key} is on the other side"
        for key in s.uat:
            assert key in cases and cases[key].pathway == side, f"{s.id}: UAT {key}"
    mapped = {k for s in D.STAGES for k in s.lessons}
    assert set(lessons) - mapped == set(), "every lesson is on a stage"
    assert set(cases) - {k for s in D.STAGES for k in s.uat} == set(), "every acceptance test is on a stage"


def test_roles_availability_and_honest_steps():
    roles = set(D.ALL_ROLES)
    for s in D.STAGES:
        assert s.roles and set(s.roles) <= roles, s.id
        keys = [x.key for x in s.substeps]
        assert len(keys) == len(set(keys)), s.id
        for x in s.substeps:
            assert x.availability in D.AVAILABILITY_LABELS, (s.id, x.key)
            assert set(x.roles) <= roles
            if x.availability == D.AVAILABLE:
                assert x.dest is not None, f"{s.id}:{x.key} is available but goes nowhere"
            else:
                assert x.dest is None and x.note, f"{s.id}:{x.key}: no link and a reason for what is not in the app"
    labels = {x.label for s in D.STAGES for x in s.substeps if x.availability == D.NOT_YET}
    for honest in ("Direct point-of-sale (POS) integration", "Supplier-sponsored contractor access",
                   "Direct QuickBooks Online connection"):
        assert honest in labels
    draw = D.stage("sb-draw")
    assert "not engineered" in draw.description and any(x.availability == D.OUTSIDE for x in draw.substeps)


def test_no_orphans_journeys_maps_loops_and_handoffs():
    in_journeys = [sid for j in D.JOURNEYS for sid in j.stage_ids]
    assert sorted(in_journeys) == sorted(s.id for s in D.STAGES) and len(in_journeys) == len(set(in_journeys))
    on_maps = [j for m in D.MAPS.values() for j in m.journeys]
    assert sorted(on_maps) == sorted(j.key for j in D.JOURNEYS)
    assert [s.label for s in D.CONTRACTOR_STAGES] == ["SET UP", "PLAN", "PRICE", "WIN", "BUILD", "CLOSE"]
    assert [D.stage(i).label for i in D.JOURNEYS_BY_KEY["supplier-a"].stage_ids] == [
        "RECEIVE", "QUOTE", "CONFIRM", "DELIVER", "COMPLETE"]
    assert [D.stage(i).label for i in D.JOURNEYS_BY_KEY["supplier-b"].stage_ids] == [
        "CUSTOMER", "SKETCH", "CONFIGURE", "DRAW", "PRICE", "QUOTE", "APPROVE", "ORDER"]
    assert [D.stage(i).label for i in D.JOURNEYS_BY_KEY["supplier-c"].stage_ids] == [
        "SET UP", "MANAGE", "MEASURE", "GROW"]
    for key, m in D.MAPS.items():
        ids = {s.id for s in D.map_stages(key)}
        for s in D.map_stages(key):
            assert [x.number for x in D.map_stages(key) if x.journey == s.journey].count(s.number) == 1
            for lp in s.loops:
                assert lp.target in ids, f"{s.id} loops off its map"
    numbers = [h.number for h in D.HANDOFFS]
    assert numbers == list(range(1, 9))
    for h in D.HANDOFFS:
        assert D.stage(h.contractor_stage).journey == "contractor"
        assert D.stage(h.supplier_stage).journey == "supplier-a"
        assert h.number in D.stage(h.contractor_stage).handoffs and h.number in D.stage(h.supplier_stage).handoffs
    concrete = " ".join(h.supplier for h in D.HANDOFFS) + D.stage("sa-deliver").description
    assert "Tomlinson" in concrete and "BMR Winchester sells" in concrete


def test_each_side_only_points_at_its_own_pages():
    from app.services.access_domains import field_only_endpoint_allowed

    for s in D.map_stages(D.MAP_SUPPLIER):
        for dest in [s.primary] + [x.dest for x in s.substeps]:
            if dest is not None:
                assert dest.requires == D.REQ_SUPPLIER and dest.endpoint.startswith(("supplier_portal.", "supplier_pro_desk.")), s.id
    for b in D.MAPS[D.MAP_SUPPLIER].branches:
        assert all(d.requires == D.REQ_SUPPLIER for d in b.dests)
    for s in D.map_stages(D.MAP_FIELD):
        for dest in [s.primary] + [x.dest for x in s.substeps]:
            if dest is not None:
                assert field_only_endpoint_allowed(dest.endpoint), f"{s.id}: {dest.endpoint} is behind the Field wall"
                assert dest.requires == D.REQ_CONTRACTOR
    for s in D.CONTRACTOR_STAGES:
        for dest in [s.primary] + [x.dest for x in s.substeps]:
            if dest is not None:
                assert not dest.endpoint.startswith(("supplier_portal.", "supplier_pro_desk.")), s.id


def test_the_export_is_versioned_plain_data():
    data = json.loads(json.dumps(D.export()))
    assert data["version"] == D.DEFINITION_VERSION
    assert len(data["stages"]) == len(D.STAGES) and len(data["handoffs"]) == 8


# ------------------------------------------------------------------ the pages, per role


def _app(enabled):
    return create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
                       "WTF_CSRF_ENABLED": False, "TRAINING_ENVIRONMENT": True}), enabled


@pytest.fixture(params=[False, True], ids=["office-site", "training-site"])
def site(request):
    application, enabled = _app(request.param)
    with application.app_context():
        db.create_all()
        people = environment.build(application, PW)
        application.config["TRAINING_ENVIRONMENT"] = enabled
        facts = dict(people["_facts"])
        own = Project.query.filter_by(organization_id=facts["organization_id"]).first()
        other = Organization(id="ORG-WF-2", legal_name="Other Builder Ltd. (synthetic)", display_name="Other Builder",
                             primary_address="1 Elsewhere Rd", default_region="Ontario", currency="CAD",
                             tax_jurisdiction="Ontario (HST 13%)", is_active=True)
        db.session.add(other)
        db.session.flush()
        cl = Client(organization_id=other.id, name="Foreign Customer (synthetic)")
        db.session.add(cl)
        db.session.flush()
        foreign = Project(organization_id=other.id, name="Foreign Garage (synthetic)", client_id=cl.id, status="Active")
        db.session.add(foreign)
        from app.services.supplier_catalogue import create_supplier

        rival = create_supplier(code="RIVAL-WF", legal_name="Rival Lumber (synthetic)", demo_synthetic=True)
        db.session.commit()
        facts.update(own=own.id, own_name=own.name, foreign=foreign.id, rival=rival.id, training=enabled)
        yield application, facts
        db.session.remove()
        db.drop_all()


def _email(key):
    return next(e for k, _n, e, *_ in environment.OFFICE_PEOPLE + environment.SUPPLIER_PEOPLE if k == key)


def _client(app, key):
    g.pop("_login_user", None)
    client = app.test_client()
    url = "/supplier/login" if key in ("darcy", "pat") else "/login"
    assert client.post(url, data={"email": _email(key), "password": PW[key]}).status_code == 302
    return client


def _get(client, path, **kw):
    g.pop("_login_user", None)
    return client.get(path, **kw)


def _map_html(html):
    start = html.index('<section class="wf"')
    return html[start:html.index('<p class="wf-hint">', start)]


def _links(html):
    return sorted({m.group(1) for m in HREF.finditer(_map_html(html)) if m.group(1)})


def _every_link_answers(client, links):
    for href in links:
        r = _get(client, href)
        assert r.status_code in (200, 302), f"{href}: {r.status_code}"
        if r.status_code == 302:
            assert "/login" not in r.headers["Location"], f"{href} sent the person to sign in"


def test_contractor_owner_sees_the_whole_map_and_every_link_answers(site):
    app, f = site
    ben = _client(app, "ben")
    r = _get(ben, "/workflow")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    for label in ("SET UP", "PLAN", "PRICE", "WIN", "BUILD", "CLOSE", "One transaction, two sides", "Workflow Guide"):
        assert label in html
    links = _links(html)
    assert "/settings/people" in links  # owner: People & Access
    assert not any(h.startswith("/supplier/") for h in links), "no Supplier Hub page from the contractor side"
    assert ("/training/" in " ".join(links)) is f["training"], "lesson links only on the training site"
    _every_link_answers(ben, links)
    # The menu entry
    assert 'href="/workflow"' in _get(ben, "/").get_data(as_text=True)


def test_office_staff_see_the_reason_not_the_owner_pages(site):
    app, f = site
    olivia = _client(app, "olivia")
    html = _get(olivia, "/workflow?stage=c-close").get_data(as_text=True)
    links = _links(html)
    assert "/settings/people" not in links and "/company-attention" not in links
    assert escape(D.REQUIREMENT_REASONS[D.REQ_PEOPLE_ADMIN]) in html
    assert escape(D.REQUIREMENT_REASONS[D.REQ_COMPANY_MANAGEMENT]) in html
    _every_link_answers(olivia, links)


def test_project_context_and_organization_isolation(site):
    app, f = site
    ben = _client(app, "ben")
    html = _get(ben, f"/workflow?project_id={f['own']}").get_data(as_text=True)
    assert f'/projects/{f["own"]}/supplier-requests' in html and f["own_name"] in html
    assert 'data-wf-current="c-price"' in html, "an Estimating project is in PRICE"
    _every_link_answers(ben, [h for h in _links(html) if f"/{f['own']}" in h])
    foreign = _get(ben, f"/workflow?project_id={f['foreign']}&stage=c-build").get_data(as_text=True)
    assert "Foreign Garage" not in foreign
    assert f"/projects/{f['foreign']}" not in foreign and f"project_id={f['foreign']}" not in foreign
    assert 'data-wf-current="c-build"' in foreign
    assert "Choose the project in Projects" in foreign  # no project: the list to choose one, no dead end
    hub = _get(ben, f"/projects/{f['own']}").get_data(as_text=True)
    assert f"/workflow?project_id={f['own']}" in hub


def test_field_only_crew_get_the_field_workflow_and_nothing_from_the_office(site):
    app, f = site
    kevin = _client(app, "kevin")
    r = _get(kevin, "/workflow")
    assert r.status_code == 302 and r.headers["Location"].endswith("/field/workflow")
    html = _get(kevin, "/field/workflow").get_data(as_text=True)
    for label in ("SIGN IN", "TODAY", "ON THE JOB", "CAPTURE", "TIME"):
        assert label in html
    assert "PRICE" not in _map_html(html) and "One transaction" not in html
    links = _links(html)
    for href in links:
        assert href.startswith(("/field", "/account/password", "/training")), href
    _every_link_answers(kevin, links)
    for href in links:  # the wall would turn an office page into a redirect to Today
        r = _get(kevin, href)
        if r.status_code == 302:
            assert "/training" in href or r.headers["Location"].startswith(("/field", "/training")), href
    assert 'href="/field/workflow"' in _get(kevin, "/field/today").get_data(as_text=True)


def test_supplier_owner_and_pro_desk_see_three_journeys_and_only_their_store(site):
    app, f = site
    sid = f["supplier_id"]
    for key in ("darcy", "pat"):
        c = _client(app, key)
        r = _get(c, f"/supplier/{sid}/workflow")
        assert r.status_code == 200
        html = r.get_data(as_text=True)
        for label in ("Serving contractors", "Walk-in PRO Desk customers", "Store setup and management",
                      "RECEIVE", "SKETCH", "MEASURE", "One transaction, two sides"):
            assert label in html
        links = _links(html)
        for href in links:
            assert href.startswith((f"/supplier/{sid}/", "/supplier/account", "/supplier/", "/training")), href
        assert not any(h.startswith(("/projects", "/settings", "/accounting", "/estimates")) for h in links)
        # Never a contractor record: the job, the customer, the company's people
        for private in (environment.JOB, environment.CUSTOMER, "Olivia Office", "Kevin Field"):
            assert private not in html
        pos = re.search(r'data-wf-substep="sb-order:pos".*?</li>', html, re.S).group(0)
        assert "<a " not in pos and "Not in CalibraytAI yet" in pos
        _every_link_answers(c, links)
        assert _get(c, f"/supplier/{f['rival']}/workflow").status_code == 404, "another store's map is not found"
        assert _get(c, "/workflow").status_code == 302
        assert f'href="/supplier/{sid}/workflow"' in _get(c, f"/supplier/{sid}/").get_data(as_text=True)
    # A contractor cannot open the Supplier Hub map
    assert _get(_client(app, "olivia"), f"/supplier/{sid}/workflow").status_code == 403


def test_signed_out_people_are_sent_to_sign_in(site):
    app, f = site
    c = app.test_client()
    assert "/login" in c.get("/workflow").headers["Location"]
    assert "/login" in c.get("/field/workflow").headers["Location"]
    assert "/supplier/login" in c.get(f"/supplier/{f['supplier_id']}/workflow").headers["Location"]


def test_back_next_and_the_stage_parameter(site):
    app, f = site
    html = _get(_client(app, "ben"), "/workflow?stage=c-win").get_data(as_text=True)
    assert 'data-wf-current="c-win"' in html
    assert 'data-wf-control-back data-wf-goto="c-price"' in html and 'data-wf-control-next data-wf-goto="c-build"' in html
    assert html.count('data-wf-page="') == 6 and html.count('" hidden>') >= 5
    first = _get(_client(app, "ben"), "/workflow?stage=nonsense").get_data(as_text=True)
    assert 'data-wf-current="c-setup"' in first and 'data-wf-control-back aria-disabled="true"' in first


# ------------------------------------------------------------------ the Training Centre


def test_training_map_lessons_progress_and_role_pathways(site):
    app, f = site
    if not f["training"]:
        assert _get(_client(app, "ben"), "/training/workflow").status_code == 404
        return
    ben = _client(app, "ben")
    ben.post("/training/register", data={"role": "OWNER"})
    lesson = "c08-concrete-request"
    _get(ben, f"/training/lessons/{lesson}")
    g.pop("_login_user", None)
    ben.post(f"/training/lessons/{lesson}/check", data={"step": 0, "done": "1"})
    html = _get(ben, "/training/workflow?stage=c-price").get_data(as_text=True)
    steps = len(C.find_lesson(lesson)[1].steps)
    row = re.search(rf'data-wf-lesson="{lesson}".*?</li>', html, re.S).group(0)
    assert f"1 of {steps} steps" in row and f"/training/lessons/{lesson}" in row
    assert "/training/uat/uat-c08-quote" in html
    page = _get(ben, f"/training/lessons/{lesson}").get_data(as_text=True)
    assert '/training/workflow?stage=c-price' in page and "<span data-ticked>1</span> of" in page
    assert "/training/workflow?stage=c-price" in _get(ben, "/training/uat/uat-c08-quote").get_data(as_text=True)
    _every_link_answers(ben, _links(html))
    # Training administrator (the owner) keeps the dashboard
    assert _get(ben, "/training/admin").status_code == 200
    # A field trainee gets the Field workflow, with Field lessons only
    kevin = _client(app, "kevin")
    kevin.post("/training/register", data={"role": "FIELD"})
    k = _get(kevin, "/training/workflow").get_data(as_text=True)
    assert "ON THE JOB" in k and "c-price" not in k and "/training/lessons/c09" not in k
    _every_link_answers(kevin, _links(k))
    # A PRO Desk trainee: the supplier map, without the lessons that are not theirs
    pat = _client(app, "pat")
    pat.post("/training/register", data={"role": "PRO_DESK"})
    p = _get(pat, "/training/workflow?stage=sb-quote").get_data(as_text=True)
    assert "Walk-in PRO Desk customers" in p and "/training/lessons/s09-price-issue" in p
    assert "/training/lessons/s04-material-quote" not in p and "/training/lessons/c" not in p
    _every_link_answers(pat, _links(p))


def test_office_map_on_the_training_site_links_to_training(site):
    app, f = site
    ben = _client(app, "ben")
    html = _get(ben, "/workflow?stage=c-price").get_data(as_text=True)
    if f["training"]:
        assert "/training/workflow?stage=c-price" in html and "/training/lessons/c09-new-estimate" in html
    else:
        assert "/training" not in _map_html(html)


# ------------------------------------------------------------------ Cal


def test_cal_says_where_you_are_and_what_comes_next(site):
    app, f = site
    ben = _client(app, "ben")
    data = _get(ben, "/cal/find", query_string={"q": "What's next?", "here": f"/projects/{f['own']}/supplier-requests"}).get_json()
    titles = [i["title"] for grp in data["groups"] for i in grp["items"]]
    assert titles[0].startswith("You are in PRICE") and titles[1].startswith("Next: WIN")
    assert all(f"project_id={f['own']}" in i["url"] for i in data["groups"][0]["items"])
    data = _get(ben, "/cal/find", query_string={"q": "where am i", "here": f"/projects/{f['foreign']}"}).get_json()
    assert "Foreign" not in json.dumps(data) and f"project_id={f['foreign']}" not in json.dumps(data)
    data = _get(ben, "/cal/find", query_string={"q": "workflow", "here": "/estimates/"}).get_json()
    assert data["groups"][0]["items"][0]["title"].startswith("You are in PRICE")
    data = _get(ben, "/cal/find", query_string={"q": "which stage is close"}).get_json()
    assert any(i["title"].startswith("CLOSE") for grp in data["groups"] for i in grp["items"])
