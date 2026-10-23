"""Useful Calculators (Joel, 22 Oct 2026): one approved icon, one calculator collection, no duplicate engines.

The phone dashboard and Home Screen app at /useful-calculators/, beside (never instead of) CalibraytAI Field.
Synthetic office user and Field-only worker only."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path

import pytest
from flask import g

from app import create_app, db

pytestmark = pytest.mark.no_office_auth

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
UC_STATIC = STATIC / "useful-calculators"
APPROVED = UC_STATIC / "CalibraytAI_Useful_Calculators_Transparent_Approved.png"
APPROVED_SHA256 = "1e709058559deaf17922723907b5302d50ed0aadbaf0824c260970f554e8fd9b"
EDGE_BLUE = (0, 57, 177)  # #0039b1, the tile's own edge blue (tools/useful_calculators/make_icons.py)
ICON_SIZES = {"useful-calculators-icon-180.png": 180, "useful-calculators-icon-192.png": 192,
              "useful-calculators-icon-512.png": 512, "useful-calculators-icon-maskable-512.png": 512,
              "useful-calculators-icon-32.png": 32}
MONEY = re.compile(r"\$\s?\d|\bprice|\bpricing|\bcost|margin|markup|labour rate|invoice|\bquote", re.I)
OFFICE_PW = "Synthetic-office-uc-1"
CREW_PW = "Synthetic-crew-uc-1"


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "test-useful-calculators", "WTF_CSRF_ENABLED": False})
    from app.services.organizations import ensure_default_organization

    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


def _people():
    """An owner (office) and a Field-only crew member, both synthetic."""
    from app.models.user import UserMembership
    from app.services.access_domains import set_field_only
    from app.services.instance_authority import set_instance_owner
    from app.services.organizations import DEFAULT_ORGANIZATION_ID
    from tests.auth_fixtures import ensure_office_user

    owner = ensure_office_user(email="owner.uc@example.invalid", password=OFFICE_PW, display_name="Olive Owner")
    set_instance_owner(DEFAULT_ORGANIZATION_ID, UserMembership.query.filter_by(user_id=owner.id).one().id, owner.id)
    crew = ensure_office_user(email="crew.uc@example.invalid", password=CREW_PW, display_name="Casey Crew")
    set_field_only(UserMembership.query.filter_by(user_id=crew.id).one(), True, owner)
    db.session.commit()


def _signed_in(app, email, password):
    g.pop("_login_user", None)
    client = app.test_client()
    r = client.post("/useful-calculators/sign-in", data={"email": email, "password": password})
    assert r.status_code == 302 and r.headers["Location"].endswith("/useful-calculators/")
    return client


def _get(client, path, **kw):
    g.pop("_login_user", None)
    return client.get(path, **kw)


def _post(client, path, **kw):
    g.pop("_login_user", None)
    return client.post(path, **kw)


def _synthetic_job():
    from app.models import Client, Project
    from app.services.estimates import create_estimate
    from app.services.organizations import DEFAULT_ORGANIZATION_ID

    client = Client(name="Synthetic Customer UC", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client)
    db.session.flush()
    project = Project(name="Synthetic Garage UC", client_id=client.id, organization_id=DEFAULT_ORGANIZATION_ID,
                      status="Estimating")
    db.session.add(project)
    db.session.commit()
    estimate = create_estimate(project_id=project.id, estimate_number="EST-UC-1", title="Synthetic estimate",
                               organization_id=DEFAULT_ORGANIZATION_ID)
    return project, estimate


def _png_size(path: Path):
    head = path.read_bytes()[:24]
    assert head[:8] == b"\x89PNG\r\n\x1a\n", path.name
    return struct.unpack(">II", head[16:24])


# ------------------------------------------------------------------ one approved icon


def test_the_approved_artwork_is_in_the_repository_unchanged():
    assert hashlib.sha256(APPROVED.read_bytes()).hexdigest() == APPROVED_SHA256
    assert _png_size(APPROVED) == (1254, 1254)
    # Only the approved artwork is kept: the earlier (white-cornered) version was replaced (Joel, 22 Oct 2026).
    assert [p.name for p in UC_STATIC.glob("CalibraytAI_*.png")] == [APPROVED.name]


def test_every_home_screen_size_is_the_approved_artwork_resized_by_the_script(tmp_path):
    """The script reproduces the committed sizes exactly from the approved PNG: a later swap is one step."""
    from tools.useful_calculators import make_icons

    for name, size in ICON_SIZES.items():
        assert _png_size(UC_STATIC / name) == (size, size), name
    written = make_icons.make(APPROVED, tmp_path)
    assert written[make_icons.APPROVED_NAME] == APPROVED_SHA256
    assert written["background"] == "#0039b1"
    for name in ICON_SIZES:
        assert (tmp_path / name).read_bytes() == (UC_STATIC / name).read_bytes(), name
    assert (tmp_path / make_icons.APPROVED_NAME).read_bytes() == APPROVED.read_bytes()


def test_the_icons_keep_the_artwork_and_only_the_phone_icons_are_made_opaque():
    """Resize only: the artwork's own pixels match at the same relative places. The manifest "any" icons keep
    their transparent corners; the iPhone icon and the maskable icon are opaque on the tile's edge blue, because
    iOS shows transparent Home Screen pixels as black."""
    from PIL import Image

    original = Image.open(APPROVED).convert("RGBA")
    for name in ("useful-calculators-icon-512.png", "useful-calculators-icon-192.png"):
        small = Image.open(UC_STATIC / name)
        assert small.mode == "RGBA", name
        size = small.size[0]
        assert small.getpixel((0, 0))[3] == 0, name  # transparent corner kept
        # The same picture: an independent box average of the original differs only by resampling.
        box = original.resize((size, size), Image.BOX)
        diff = sum(abs(x - y) for a, b in zip(box.getdata(), small.getdata()) for x, y in zip(a, b))
        assert diff / (size * size * 4) < 6, name
    for name, inner in (("useful-calculators-icon-180.png", 180), ("useful-calculators-icon-maskable-512.png", 410)):
        icon = Image.open(UC_STATIC / name)
        assert icon.mode == "RGB", name  # opaque: no black corners on the iPhone
        assert icon.getpixel((0, 0)) == EDGE_BLUE, name
        size = icon.size[0]
        # Inside, the artwork composited on the blue, compared with an independent box average of it.
        flat = Image.new("RGBA", original.size, EDGE_BLUE + (255,))
        flat.alpha_composite(original)
        art = flat.convert("RGB").resize((inner, inner), Image.BOX)
        off = (size - inner) // 2
        inside = icon.crop((off, off, off + inner, off + inner))
        diff = sum(abs(x - y) for a, b in zip(art.getdata(), inside.getdata()) for x, y in zip(a, b))
        assert diff / (inner * inner * 3) < 6, name
    maskable = Image.open(UC_STATIC / "useful-calculators-icon-maskable-512.png")
    assert maskable.getpixel((40, 256)) == EDGE_BLUE  # outside the 80 % safe zone: background only


# ------------------------------------------------------------------ Home Screen app, beside Field


def test_manifest_is_its_own_app_distinct_from_field(app):
    client = app.test_client()
    r = client.get("/static/useful-calculators/manifest.webmanifest")
    assert r.status_code == 200 and r.mimetype == "application/manifest+json"
    uc = r.get_json()
    field = client.get("/static/manifest.webmanifest").get_json()
    assert uc["name"] == uc["short_name"] == "Useful Calculators"
    assert uc["scope"] == "/useful-calculators/" and uc["id"] == "/useful-calculators/"
    assert uc["start_url"].startswith("/useful-calculators/")
    assert uc["display"] == "standalone"
    # Field's manifest is untouched: its own name, id, start and scope.
    assert (field["name"], field["id"], field["start_url"], field["scope"]) == ("CalibraytAI", "/", "/", "/")
    assert {uc["id"], uc["start_url"], uc["scope"]}.isdisjoint({field["id"], field["start_url"]})
    for icon in uc["icons"]:
        assert client.get(icon["src"]).status_code == 200, icon["src"]
        assert icon["src"].startswith("/static/useful-calculators/useful-calculators-icon-")
    assert any(i["purpose"] == "maskable" for i in uc["icons"])
    assert {i["sizes"] for i in uc["icons"]} >= {"180x180", "192x192", "512x512"}


def test_home_screen_start_page_opens_the_dashboard(app):
    start = json.loads((UC_STATIC / "manifest.webmanifest").read_text())["start_url"]
    r = app.test_client().get(start)
    assert r.status_code == 200 and 'data-uc-dashboard="signed_out"' in r.get_data(as_text=True)


def test_dashboard_carries_the_useful_calculators_tags_and_never_field_s(app):
    _people()
    pages = [app.test_client().get("/useful-calculators/").get_data(as_text=True),
             app.test_client().get("/useful-calculators/sign-in").get_data(as_text=True),
             _get(_signed_in(app, "crew.uc@example.invalid", CREW_PW), "/useful-calculators/concrete").get_data(as_text=True)]
    for html in pages:
        assert 'name="apple-mobile-web-app-title" content="Useful Calculators"' in html
        assert 'rel="apple-touch-icon" sizes="180x180" href="/static/useful-calculators/useful-calculators-icon-180.png"' in html
        assert 'rel="manifest" href="/static/useful-calculators/manifest.webmanifest"' in html
        assert "/static/manifest.webmanifest" not in html and "calibraytai-app-icon-180" not in html
        assert "serviceWorker" not in html and "field-sw.js" not in html  # no offline claim, no Field worker


def test_field_keeps_its_own_manifest_service_worker_and_cache(app):
    partial = (ROOT / "app/templates/partials/home_screen.html").read_text()
    assert 'content="CalibraytAI"' in partial and "manifest.webmanifest" in partial and "useful" not in partial
    worker = (STATIC / "field-sw.js").read_text()
    assert "useful" not in worker.lower()
    assert 'var CACHE = "calibrayt-field-shell-v3";' in worker
    html = app.test_client().get("/login").get_data(as_text=True)
    assert 'content="CalibraytAI"' in html and "useful-calculators" not in html


# ------------------------------------------------------------------ one collection: every calculator


def test_the_collection_names_every_existing_calculator(app):
    from app.navigation import NAV_SECTIONS
    from app.routes.useful_calculators import PHONE_CALCULATOR_ENDPOINTS
    from app.services import useful_calculators as UC
    from app.services.access_domains import FIELD_ONLY_ALLOWED_ENDPOINTS

    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    menu = next(s for s in NAV_SECTIONS if s["title"] == "Calculators")
    office = {c.office_endpoint for c in UC.CALCULATORS}
    assert {link["endpoint"] for link in menu["links"]} <= office
    # "Link to a project" (release 8) and the Guided Estimating result actions (23 Oct 2026: the stages of a project,
    # and Create New Project's carry) are save actions, not calculators: they stay office only.
    actions = {"calculators.link_project", "calculators.project_stages", "calculators.carry_result"}
    assert actions <= endpoints and actions.isdisjoint(FIELD_ONLY_ALLOWED_ENDPOINTS)
    assert {e for e in endpoints if e.startswith("calculators.") and e not in actions} <= office
    for calc in UC.CALCULATORS:
        assert calc.office_endpoint in endpoints, calc.key
        if calc.audience == UC.AUDIENCE_CREW:
            assert calc.phone_endpoint in PHONE_CALCULATOR_ENDPOINTS and calc.phone_endpoint in endpoints
            assert calc.phone_endpoint in FIELD_ONLY_ALLOWED_ENDPOINTS
        else:
            assert not calc.phone_endpoint
    for tool in UC.PROJECT_TOOLS:
        assert tool.endpoint in endpoints, tool.key
    # The office business and job calculators never reach the Field-only allow list.
    office_only = {c.office_endpoint for c in UC.CALCULATORS if c.audience == UC.AUDIENCE_OFFICE}
    assert office_only.isdisjoint(FIELD_ONLY_ALLOWED_ENDPOINTS)
    assert {t.endpoint for t in UC.PROJECT_TOOLS}.isdisjoint(FIELD_ONLY_ALLOWED_ENDPOINTS)
    assert "useful_calculators.projects" not in FIELD_ONLY_ALLOWED_ENDPOINTS


def test_no_engine_is_copied_the_phone_pages_are_the_office_views(app):
    from app.routes import calculators
    from app.routes.useful_calculators import PHONE_CALCULATOR_ENDPOINTS

    for endpoint in PHONE_CALCULATOR_ENDPOINTS:
        view = app.view_functions[endpoint]
        assert view is app.view_functions["calculators." + endpoint.split(".", 1)[1]], endpoint
        assert view.__module__ == calculators.__name__


TRADE_POSTS = {
    "roofing": {"unit_system": "imperial", "plane_length": ["20", "20"], "plane_width": ["10", "10"],
                "plane_pitch": ["6", "6"], "waste_percent": "10", "bundle_coverage": "33.3",
                "underlayment_coverage": "400", "ridge_length": "20", "ridge_cap_coverage": "20"},
    "footing": {"unit_system": "metric", "footing_length": ["6", "3"], "footing_width": ["0.6", "0.5"],
                "footing_thickness": ["250", "200"], "footing_count": ["", "2"], "waste_percent": "5"},
    "drywall": {"unit_system": "imperial", "wall_length": ["12", "10", "12", "10"], "wall_height": ["8"] * 4,
                "ceiling_length": ["12"], "ceiling_width": ["10"], "opening_width": ["3"], "opening_height": ["7"],
                "opening_count": ["1"], "waste_percent": "10", "sheet_size": "4x8"},
    "flooring": {"unit_system": "imperial", "room_length": ["12", "8"], "room_width": ["10", "6"],
                 "waste_percent": "8", "box_coverage": "20"},
    "siding": {"unit_system": "imperial", "wall_length": ["30", "20"], "wall_height": ["9", "9"],
               "gable_base": ["20"], "gable_height": ["6"], "opening_width": ["3"], "opening_height": ["5"],
               "opening_count": ["4"], "waste_percent": "10", "piece_coverage": "16"},
    "wall-framing": {"length_ft": "12", "height_ft": "8", "spacing_in": "16", "stud_size": "2x6",
                     "top_plate_count": "2", "bottom_plate_count": "1"},
}


def _cells(html):
    """The result panel's text (data-trade-result / data-wall-framing-result), tags removed.

    Release 8: the calculators redesign (calculators.css) puts the result in <div class="cc-result">; the
    office page follows it with "Link to a project" (office only), so the panel ends there or at </section>."""
    m = re.search(r'<div class="cc-result" data-[a-z-]*result[^>]*>(.*?)(?=<div class="cc-link"|</section>)', html, re.S)
    if not m:
        return []
    return [line for line in (re.sub(r"\s+", " ", t).strip() for t in re.split(r"<[^>]+>", m.group(1))) if line]


def test_phone_pages_give_the_existing_verified_results(app):
    _people()
    office = _signed_in(app, "owner.uc@example.invalid", OFFICE_PW)
    crew = _signed_in(app, "crew.uc@example.invalid", CREW_PW)
    for slug, data in TRADE_POSTS.items():
        reference = _post(office, f"/calculators/{slug}", data=data)
        assert reference.status_code == 200, slug
        expected = _cells(reference.get_data(as_text=True))
        assert expected, slug
        for who in (office, crew):
            page = _post(who, f"/useful-calculators/{slug}", data=data)
            assert page.status_code == 200, slug
            html = page.get_data(as_text=True)
            assert _cells(html) == expected, slug
            assert "data-uc-back" in html and "shell-sidebar" not in html


def test_concrete_and_stair_engines_load_the_same_scripts(app):
    _people()
    office = _signed_in(app, "owner.uc@example.invalid", OFFICE_PW)
    for slug, script in (("concrete", "js/concrete-calculator-page.js"), ("stairs", "js/stair-calculator.js")):
        html = _get(office, f"/useful-calculators/{slug}").get_data(as_text=True)
        assert f"/static/{script}" in html
        assert ("data-concrete-calculator" if slug == "concrete" else "data-stair-calculator") in html
        assert 'name="measurement_system"' in html or slug == "stairs"  # metric/imperial where it already exists
        # Guided Estimating (23 Oct 2026): an office person on the phone app gets the result's three choices too
        # (Use Result Only / Add to Existing Project / Create New Project); the crew never do (checked below).
        assert "data-link-project" in html and "Create New Project" in html
    crew = _signed_in(app, "crew.uc@example.invalid", CREW_PW)
    for slug in ("concrete", "stairs"):
        html = _get(crew, f"/useful-calculators/{slug}").get_data(as_text=True)
        assert "data-link-project" not in html and "data-result-options" not in html  # the crew: the result alone
    # The office pages keep the office shell.
    assert "shell-sidebar" in _get(office, "/calculators/concrete").get_data(as_text=True)


# ------------------------------------------------------------------ who sees what


def test_signed_out_dashboard_shows_the_public_calculators_and_a_sign_in(app):
    html = app.test_client().get("/useful-calculators/").get_data(as_text=True)
    assert 'data-uc-dashboard="signed_out"' in html
    public = dict(re.findall(r'href="([^"]+)"[^>]*data-uc-calc="([^"]+)" data-uc-state="public"', html))
    # The established public set (Joel, 22 Oct 2026): the website's existing pages, nothing on the platform.
    assert public == {"https://calibraytai.com/useful-tools/concrete/": "concrete",
                      "https://calibraytai.com/useful-tools/stairs/": "stairs",
                      "https://calibraytai.com/employment-vs-entrepreneurship/": "employment"}
    assert len(re.findall(r'data-uc-state="sign_in"', html)) == 8
    assert "Please log in to access the office application" not in html
    assert "/useful-calculators/projects" not in html and "Job calculators" not in html


def test_sign_in_round_trip_returns_to_the_calculator(app):
    _people()
    client = app.test_client()
    r = client.get("/useful-calculators/wall-framing")
    assert r.status_code == 302 and r.headers["Location"].startswith("/useful-calculators/sign-in?next=")
    page = client.get(r.headers["Location"]).get_data(as_text=True)
    assert "Sign in to use this calculator" in page and "office application" not in page
    bad = client.post("/useful-calculators/sign-in", data={"email": "owner.uc@example.invalid", "password": "wrong",
                                                          "next": "/useful-calculators/wall-framing"})
    assert bad.status_code == 200 and "Sign in" in bad.get_data(as_text=True)
    good = client.post("/useful-calculators/sign-in", data={"email": "owner.uc@example.invalid", "password": OFFICE_PW,
                                                           "next": "/useful-calculators/wall-framing"})
    assert good.status_code == 302 and good.headers["Location"] == "/useful-calculators/wall-framing"
    assert _get(client, "/useful-calculators/wall-framing").status_code == 200
    # Signed in, the sign-in page goes back; sign out returns to the public dashboard.
    assert _get(client, "/useful-calculators/sign-in").headers["Location"] == "/useful-calculators/"
    assert _post(client, "/useful-calculators/sign-out").headers["Location"] == "/useful-calculators/"
    assert 'data-uc-dashboard="signed_out"' in _get(client, "/useful-calculators/").get_data(as_text=True)


def test_no_platform_calculator_is_public(app):
    """Wall framing, roofing, ICF and the rest still need a sign-in (Joel, 22 Oct 2026: keep what is established)."""
    client = app.test_client()
    for slug in ("wall-framing", "roofing", "wall-form", "concrete", "stairs", "footing", "siding", "drywall", "flooring"):
        for method in ("GET",) if slug in ("concrete", "stairs") else ("GET", "POST"):  # those two are GET only
            r = client.open(f"/useful-calculators/{slug}", method=method)
            assert r.status_code == 302 and r.headers["Location"].startswith("/useful-calculators/sign-in"), (slug, method)
            r = client.open(f"/calculators/{slug}", method=method)
            assert r.status_code == 302 and r.headers["Location"].startswith("/login"), (slug, method)


@pytest.mark.parametrize("target", ["//evil.example/x", "https://evil.example/", "/projects", "/field/today",
                                    "\\\\evil", ""])
def test_sign_in_returns_only_inside_the_app(app, target):
    _people()
    r = app.test_client().post("/useful-calculators/sign-in", data={
        "email": "owner.uc@example.invalid", "password": OFFICE_PW, "next": target})
    assert r.headers["Location"] == "/useful-calculators/"


def test_office_user_reaches_every_calculator_and_the_job_calculators(app):
    _people()
    project, estimate = _synthetic_job()
    office = _signed_in(app, "owner.uc@example.invalid", OFFICE_PW)
    html = _get(office, "/useful-calculators/").get_data(as_text=True)
    assert 'data-uc-dashboard="office"' in html and 'data-uc-state="restricted"' not in html
    from app.services import useful_calculators as UC

    for calc in UC.CALCULATORS:
        assert f'data-uc-calc="{calc.key}"' in html
    links = re.findall(r'href="([^"]+)"[^>]*data-uc-calc="([^"]+)" data-uc-state="(open|office|choose-job)"', html)
    assert len(links) == len(UC.CALCULATORS) + 1
    for href, key, _state in links:
        assert _get(office, href).status_code == 200, (key, href)
    jobs = _get(office, "/useful-calculators/projects").get_data(as_text=True)
    assert "Synthetic Garage UC" in jobs and "EST-UC-1" in jobs
    tools = re.findall(r'href="([^"]+)" target="_blank" rel="noopener" data-uc-tool="([^"]+)"', jobs)
    assert {k for _h, k in tools} == {t.key for t in UC.PROJECT_TOOLS}
    for href, key in tools:
        assert _get(office, href).status_code == 200, (key, href)
    assert f"/estimates/{estimate.id}/versions/" in jobs and f"/projects/{project.id}/deck-takeoff" in jobs


def test_field_only_worker_gets_the_crew_calculators_and_nothing_confidential(app):
    _people()
    _synthetic_job()
    crew = _signed_in(app, "crew.uc@example.invalid", CREW_PW)
    html = _get(crew, "/useful-calculators/").get_data(as_text=True)
    assert 'data-uc-dashboard="field_only"' in html
    from app.services import useful_calculators as UC

    for calc in UC.CALCULATORS:
        state = "open" if calc.audience == UC.AUDIENCE_CREW else "restricted"
        assert f'data-uc-calc="{calc.key}" data-uc-state="{state}"' in html, calc.key
        if calc.audience == UC.AUDIENCE_CREW:
            assert _get(crew, url_for_path(app, calc.phone_endpoint)).status_code == 200, calc.key
    assert 'data-uc-calc="jobs" data-uc-state="restricted"' in html
    assert "Synthetic Garage UC" not in html and "Synthetic Customer UC" not in html and "EST-UC-1" not in html
    assert not MONEY.findall(re.sub(r"<[^>]+>", " ", html))
    assert "/useful-calculators/projects" not in html and "/calculators/employment" not in html
    assert "/supplier-program/" not in html
    # Office pages, the office copies of the calculators and the job calculators stay refused.
    for path in ("/useful-calculators/projects", "/calculators/concrete", "/calculators/employment-vs-entrepreneurship",
                 "/supplier-program/economic-model", "/cost-library/", "/pricing-engine/", "/labour-engine/",
                 "/projects/", "/clients/", "/estimates/1/versions/1/calculations", "/projects/1/deck-takeoff"):
        r = _get(crew, path)
        assert r.status_code == 302 and r.headers["Location"].endswith("/field/today"), (path, r.status_code)
    assert _post(crew, "/useful-calculators/footing", data=TRADE_POSTS["footing"]).status_code == 200
    page = _post(crew, "/useful-calculators/footing", data=TRADE_POSTS["footing"]).get_data(as_text=True)
    assert not MONEY.findall(re.sub(r"<[^>]+>", " ", page))


def url_for_path(app, endpoint):
    with app.test_request_context():
        from flask import url_for

        return url_for(endpoint)


def test_idle_sign_out_on_a_phone_page_returns_to_its_own_sign_in(app):
    _people()
    app.config["SESSION_IDLE_TIMEOUT_SECONDS"] = 60
    crew = _signed_in(app, "crew.uc@example.invalid", CREW_PW)
    with crew.session_transaction() as s:
        s["last_activity_at"] = 1.0
    r = _get(crew, "/useful-calculators/drywall")
    assert r.status_code == 302 and r.headers["Location"].startswith("/useful-calculators/sign-in?next=")
    crew2 = _signed_in(app, "crew.uc@example.invalid", CREW_PW)
    html = _get(crew2, "/useful-calculators/drywall").get_data(as_text=True)
    assert 'data-login-url="/useful-calculators/sign-in"' in html


# ------------------------------------------------------------------ training and Getting Started


def test_field_crew_lesson_and_getting_started_teach_the_second_icon(app):
    from app.services.onboarding import STEP_BY_KEY
    from app.training import content as C

    found = C.find_lesson("f01-useful-calculators")
    assert found is not None and found[0].key == "f01"
    _module, lesson = found
    text = " ".join(f"{s.where} {s.do} {s.expect}" for s in lesson.steps)
    for words in ("Safari", "Share", "Add to Home Screen", "Useful Calculators", "/useful-calculators/"):
        assert words in text, words
    shots = Path(app.static_folder) / "training" / "shots"
    for step in lesson.steps:
        if step.shot:
            assert _png_size(shots / step.shot) == (390, 844), step.shot
    assert sum(1 for s in lesson.steps if s.shot) >= 4
    how = STEP_BY_KEY["phones"].how
    assert "Useful Calculators" in how and "/useful-calculators/" in how and "Add to Home Screen" in how
