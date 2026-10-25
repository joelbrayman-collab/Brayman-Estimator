"""Site Plans (Joel, 23 Oct 2026): the plans viewer and the crew's Home Screen app.

Release 8 (Joel): the office keeps one plan button, "View project plan" (tests/test_project_plan_access.py);
Site Plans' own office "Plans" button was removed.

"I want this to go on almost every project screen in the office App and I also want it to load on the boys'
iPhones like the calculator App so they can instantly access all project plans while on a job site."

Synthetic data only (tests/site_plans_support.py)."""

from __future__ import annotations

import hashlib
import json
import re
import struct
import tempfile
from io import BytesIO
from pathlib import Path

import pytest
from flask import g
from pypdf import PdfReader

from app import create_app, db
from tests import site_plans_support as S

pytestmark = pytest.mark.no_office_auth

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
SP_STATIC = STATIC / "site-plans"
APPROVED = SP_STATIC / "CalibraytAI_Site_Plans_Approved.png"
APPROVED_SHA256 = "a9e0f5d3475a8f6944525e3209f287e6f2ee9e31230b4c3dd8f167c5663992ee"
NAVY = (26, 43, 63)  # #1a2b3f, the rounded tile's own dark navy (tools/site_plans/make_icons.py tile_colour)
# The derivatives, made by tools/site_plans/make_icons.py from the approved artwork (crop the transparent margin,
# pad to a square on transparency, resize; the iPhone and maskable icons on the navy). Recorded 23 Oct 2026.
ICONS = {
    "site-plans-icon-32.png": (32, "28308f546d749d5a1ac06b6b2e767b3d90bdd9da4ceb888de20045a7262f1053"),
    "site-plans-icon-180.png": (180, "230ee2e901bffdd7de9f43ae1ef962d823bb90d19472d759107c897698389905"),
    "site-plans-icon-192.png": (192, "e7c698c46a4b39279245531dba5014ed08d7eeb47549ca2b6949e1fc4dbdbca1"),
    "site-plans-icon-512.png": (512, "9b4fc11f2a036875a6710d35d3413b8a541a2b5bce608bcdd64003e950246e2a"),
    "site-plans-icon-maskable-512.png": (512, "e06c2218218e55aebc42de3abfdcf52fae92aa8371c2797dcba7421924ce05c9"),
}
MONEY = re.compile(r"\$\s?\d|\bprice|\bpricing|\bcost|margin|markup|labour rate|invoice|\bquote|\bwage", re.I)


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "test-site-plans", "WTF_CSRF_ENABLED": False,
                              "PLAN_UPLOAD_ROOT": tempfile.mkdtemp(prefix="site-plans-test-")})
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def facts(app):
    return S.seed()


def _signed_in(app, who, via="/site-plans/sign-in"):
    g.pop("_login_user", None)
    client = app.test_client()
    email, password = {"owner": S.OWNER, "kevin": S.KEVIN, "lee": S.LEE, "bea": S.BEA}[who][:2]
    r = client.post(via, data={"email": email, "password": password})
    assert r.status_code == 302, (who, r.status_code)
    return client


def _get(client, path, **kw):
    g.pop("_login_user", None)
    return client.get(path, **kw)


def _text(response):
    return response.get_data(as_text=True)


def _png_size(path: Path):
    head = path.read_bytes()[:24]
    assert head[:8] == b"\x89PNG\r\n\x1a\n", path.name
    return struct.unpack(">II", head[16:24])


# ------------------------------------------------------------------ the approved icon and its sizes


def test_the_approved_artwork_is_in_the_repository_unchanged():
    assert hashlib.sha256(APPROVED.read_bytes()).hexdigest() == APPROVED_SHA256
    assert _png_size(APPROVED) == (1312, 1199)
    assert [p.name for p in SP_STATIC.glob("CalibraytAI_*.png")] == [APPROVED.name]


def _pixels(path):
    from PIL import Image

    with Image.open(path) as im:
        return im.mode, im.size, im.tobytes()


def test_every_icon_has_its_size_and_recorded_checksum_and_the_script_makes_them_again(tmp_path):
    from tools.site_plans import make_icons

    for name, (size, digest) in ICONS.items():
        assert _png_size(SP_STATIC / name) == (size, size), name
        assert hashlib.sha256((SP_STATIC / name).read_bytes()).hexdigest() == digest, name
    written = make_icons.make(APPROVED, tmp_path)
    assert written[make_icons.APPROVED_NAME] == APPROVED_SHA256
    assert written["background"] == "#1a2b3f"
    for name in ICONS:
        # Same pixels, not same bytes: PNG compression output differs between machines (zlib builds), so
        # the regenerated files are compared decoded. The committed files' own checksums are pinned above.
        assert _pixels(tmp_path / name) == _pixels(SP_STATIC / name), name


def test_the_icons_are_the_artwork_resized_and_only_the_phone_icons_are_opaque():
    """Crop and pad only: the same picture as the approved artwork, squared. The manifest "any" icons keep their
    transparent corners; the iPhone 180 and the maskable icon are opaque on the tile's navy."""
    from PIL import Image

    from tools.site_plans import make_icons

    square = make_icons.squared(Image.open(APPROVED))
    assert square.size == (880, 880)
    for name in ("site-plans-icon-512.png", "site-plans-icon-192.png", "site-plans-icon-32.png"):
        small = Image.open(SP_STATIC / name)
        assert small.mode == "RGBA" and small.getpixel((0, 0))[3] == 0, name
        size = small.size[0]
        box = square.resize((size, size), Image.BOX)
        diff = sum(abs(x - y) for a, b in zip(box.getdata(), small.getdata()) for x, y in zip(a, b))
        assert diff / (size * size * 4) < (12 if size < 64 else 6), name  # 32 px: resampling differs more
    for name, inner in (("site-plans-icon-180.png", 180), ("site-plans-icon-maskable-512.png", 410)):
        icon = Image.open(SP_STATIC / name)
        assert icon.mode == "RGB", name  # no transparency: no black corners on the iPhone
        assert icon.getpixel((0, 0)) == NAVY, name
        flat = Image.new("RGBA", square.size, NAVY + (255,))
        flat.alpha_composite(square)
        art = flat.convert("RGB").resize((inner, inner), Image.BOX)
        off = (icon.size[0] - inner) // 2
        inside = icon.crop((off, off, off + inner, off + inner))
        diff = sum(abs(x - y) for a, b in zip(art.getdata(), inside.getdata()) for x, y in zip(a, b))
        assert diff / (inner * inner * 3) < 6, name
    assert Image.open(SP_STATIC / "site-plans-icon-maskable-512.png").getpixel((40, 256)) == NAVY  # outside safe zone


def test_the_cal_logo_and_the_calibraytai_brand_icons_are_unchanged():
    import subprocess

    changed = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", "app/static/branding"], cwd=ROOT,
                             capture_output=True, text=True).stdout.split()
    assert changed == []


# ------------------------------------------------------------------ the Home Screen app, beside Field and Useful Calculators


def test_manifest_scope_start_and_icons_are_its_own(app):
    client = app.test_client()
    r = client.get("/static/site-plans/manifest.webmanifest")
    assert r.status_code == 200 and r.mimetype == "application/manifest+json"
    sp = r.get_json()
    assert sp["name"] == sp["short_name"] == "Site Plans"
    assert sp["id"] == sp["scope"] == "/site-plans/"
    assert sp["start_url"] == "/site-plans/?source=home-screen"
    assert sp["display"] == "standalone"
    field = client.get("/static/manifest.webmanifest").get_json()
    uc = client.get("/static/useful-calculators/manifest.webmanifest").get_json()
    assert (field["name"], field["scope"], field["start_url"]) == ("CalibraytAI", "/", "/")
    assert (uc["name"], uc["scope"]) == ("Useful Calculators", "/useful-calculators/")
    sizes = {}
    for icon in sp["icons"]:
        served = client.get(icon["src"])
        assert served.status_code == 200 and served.mimetype == "image/png", icon["src"]
        name = icon["src"].rsplit("/", 1)[1]
        size, digest = ICONS[name]
        assert icon["sizes"] == f"{size}x{size}"
        assert hashlib.sha256(served.data).hexdigest() == digest, name
        sizes[icon["purpose"], icon["sizes"]] = name
    assert {("any", "192x192"), ("any", "512x512"), ("maskable", "512x512"), ("any", "180x180")} <= set(sizes)


def test_pages_carry_site_plans_home_screen_tags_and_never_field_s(app, facts):
    anonymous = _text(_get(app.test_client(), "/site-plans/sign-in"))
    kevin = _signed_in(app, "kevin")
    pages = [anonymous, _text(_get(kevin, "/site-plans/")),
             _text(_get(kevin, f"/site-plans/projects/{facts['assigned_id']}"))]
    for html in pages:
        assert 'name="apple-mobile-web-app-title" content="Site Plans"' in html
        assert 'rel="apple-touch-icon" sizes="180x180" href="/static/site-plans/site-plans-icon-180.png"' in html
        assert 'rel="manifest" href="/static/site-plans/manifest.webmanifest"' in html
        assert "/static/manifest.webmanifest" not in html and "useful-calculators" not in html
        assert "field-sw.js" not in html


def test_its_service_worker_is_scoped_to_site_plans_and_never_keeps_office_pages(app):
    r = app.test_client().get("/site-plans/sw.js")
    assert r.status_code == 200 and "javascript" in r.mimetype
    assert r.headers["Service-Worker-Allowed"] == "/site-plans/" and "no-cache" in r.headers["Cache-Control"]
    body = _text(r)
    assert 'var CACHE = "calibrayt-site-plans-v1";' in body
    for office in ("/estimates", "/proposals", "/clients", '"/projects/', "/pricing", '"/field', "/login", "password"):
        assert office not in body, office
    assert "!response.redirected" in body and 'request.method !== "GET"' in body
    assert 'key.indexOf(PREFIX) === 0 && key !== CACHE' in body  # it never deletes Field's cache
    page_js = (SP_STATIC / "site-plans.js").read_text()
    assert 'register("/site-plans/sw.js", { scope: "/site-plans/" })' in page_js
    # Field keeps its own worker, cache and Home Screen tags.
    field = (STATIC / "field-sw.js").read_text()
    assert 'var CACHE = "calibrayt-field-shell-v3";' in field and "site-plans" not in field


def test_sign_in_and_sign_out_remove_the_plans_kept_on_the_phone(app):
    script = (STATIC / "js" / "sign-in-clears-field-cache.js").read_text()
    assert 'key.indexOf("calibrayt-site-plans") === 0' in script and 'indexOf("calibrayt-field-shell") === 0' in script
    for path in ("/site-plans/sign-in", "/login"):
        assert "js/sign-in-clears-field-cache.js" in _text(_get(app.test_client(), path)), path
    page_js = (SP_STATIC / "site-plans.js").read_text()
    assert "[data-sp-sign-out-form]" in page_js and "caches.delete(k)" in page_js


# ------------------------------------------------------------------ signed out


def test_signed_out_every_site_plans_page_goes_to_its_own_sign_in(app, facts):
    client = app.test_client()
    a, p = facts["assigned_id"], facts["plan_id"]
    for path in ("/site-plans/", "/site-plans/?source=home-screen", f"/site-plans/projects/{a}",
                 f"/site-plans/projects/{a}/plan/{p}", f"/site-plans/projects/{a}/plan/{p}.pdf",
                 f"/site-plans/projects/{a}/plan/{p}/page-1.pdf"):
        r = client.get(path)
        assert r.status_code == 302, path
        assert r.headers["Location"].startswith("/site-plans/sign-in?next="), (path, r.headers["Location"])
    page = client.get("/site-plans/sign-in")
    assert page.status_code == 200 and "data-sp-sign-in-form" in _text(page)
    assert "no-store" in page.headers["Cache-Control"]


def test_sign_in_returns_to_the_page_asked_for_and_only_inside_the_app(app, facts):
    g.pop("_login_user", None)
    client = app.test_client()
    target = f"/site-plans/projects/{facts['assigned_id']}"
    r = client.post("/site-plans/sign-in", data={"email": S.KEVIN[0], "password": S.KEVIN[1], "next": target})
    assert r.status_code == 302 and r.headers["Location"] == target
    g.pop("_login_user", None)
    other = app.test_client()
    r = other.post("/site-plans/sign-in", data={"email": S.KEVIN[0], "password": S.KEVIN[1],
                                                "next": "https://evil.example/site-plans/"})
    assert r.headers["Location"] == "/site-plans/"
    g.pop("_login_user", None)
    wrong = app.test_client().post("/site-plans/sign-in", data={"email": S.KEVIN[0], "password": "nope"})
    assert wrong.status_code == 200 and "data-sp-sign-in-form" in _text(wrong)


def test_idle_sign_out_comes_back_to_the_site_plans_sign_in(app, facts):
    kevin = _signed_in(app, "kevin")
    html = _text(_get(kevin, "/site-plans/"))
    assert 'data-login-url="/site-plans/sign-in"' in html


# ------------------------------------------------------------------ who sees which projects


def test_field_only_crew_see_only_the_jobs_they_are_booked_on_the_same_as_field(app, facts):
    from app.services import site_plans as SP
    from app.services.access_domains import field_visible_project_ids
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
    from app.models.user import User

    kevin_user = db.session.get(User, facts["kevin_id"])
    assert [p.id for p in SP.visible_projects(kevin_user, ORG)] == [facts["assigned_id"]]
    assert facts["assigned_id"] in field_visible_project_ids(kevin_user, ORG)
    kevin = _signed_in(app, "kevin")
    page = _text(_get(kevin, "/site-plans/"))
    assert S.ASSIGNED in page and S.UNASSIGNED not in page and S.ORG_B_PROJECT not in page
    assert re.findall(r'data-sp-project="(\d+)"', page) == [str(facts["assigned_id"])]
    field = _text(_get(kevin, "/field/projects"))
    assert S.ASSIGNED in field and S.UNASSIGNED not in field  # the same rule as Field
    lee = _signed_in(app, "lee")
    empty = _text(_get(lee, "/site-plans/"))
    assert 'data-sp-projects="0"' in empty and "not booked on a job" in empty and S.ASSIGNED not in empty


def test_office_users_see_their_organization_s_active_projects_only(app, facts):
    owner = _signed_in(app, "owner")
    page = _text(_get(owner, "/site-plans/"))
    assert sorted(re.findall(r'data-sp-project="(\d+)"', page)) == sorted([str(facts["assigned_id"]),
                                                                         str(facts["unassigned_id"])])
    assert S.ORG_B_PROJECT not in page
    bea = _signed_in(app, "bea")
    rival = _text(_get(bea, "/site-plans/"))
    assert re.findall(r'data-sp-project="(\d+)"', rival) == [str(facts["org_b_project_id"])]
    assert S.ASSIGNED not in rival and S.UNASSIGNED not in rival


def test_another_job_and_another_organization_never_open(app, facts):
    a, u, b = facts["assigned_id"], facts["unassigned_id"], facts["org_b_project_id"]
    kevin = _signed_in(app, "kevin")
    for project in (u, b):
        r = _get(kevin, f"/site-plans/projects/{project}")
        assert r.status_code == 302 and r.headers["Location"] == "/site-plans/", project
    for path in (f"/site-plans/projects/{u}/plan/{facts['other_plan_id']}",
                 f"/site-plans/projects/{u}/plan/{facts['other_plan_id']}.pdf",
                 f"/site-plans/projects/{u}/plan/{facts['other_plan_id']}/page-1.pdf",
                 f"/site-plans/projects/{b}/plan/{facts['org_b_plan_id']}.pdf",
                 f"/site-plans/projects/{a}/plan/{facts['org_b_plan_id']}.pdf",   # B's file under A's job
                 f"/site-plans/projects/{a}/plan/{facts['other_plan_id']}.pdf",   # another job's file under his job
                 f"/site-plans/projects/{a}/drawing/{facts['drawing_set_id'] + 100}.pdf",  # no such drawing
                 f"/site-plans/projects/{a}/x/{facts['plan_id']}.pdf",
                 f"/site-plans/projects/{a}/plan/{facts['plan_id']}/page-9.pdf"):
        assert _get(kevin, path).status_code == 404, path
    owner = _signed_in(app, "owner")
    assert _get(owner, f"/site-plans/projects/{b}").headers["Location"] == "/site-plans/"
    for path in (f"/site-plans/projects/{b}/plan/{facts['org_b_plan_id']}.pdf",
                 f"/site-plans/projects/{a}/plan/{facts['org_b_plan_id']}.pdf"):
        assert _get(owner, path).status_code == 404, path
    bea = _signed_in(app, "bea")
    assert _get(bea, f"/site-plans/projects/{a}").headers["Location"] == "/site-plans/"
    assert _get(bea, f"/site-plans/projects/{a}/plan/{facts['plan_id']}.pdf").status_code == 404
    assert _get(bea, f"/site-plans/projects/{b}/plan/{facts['org_b_plan_id']}.pdf").status_code == 200


def test_field_only_crew_still_cannot_open_office_pages(app, facts):
    kevin = _signed_in(app, "kevin")
    for path in (f"/projects/{facts['assigned_id']}", f"/estimates/{facts['estimate_id']}",
                 f"/projects/{facts['assigned_id']}/plans", f"/projects/{facts['assigned_id']}/plans/upload"):
        r = _get(kevin, path)
        assert r.status_code == 302 and r.headers["Location"].endswith("/field/today"), path


# ------------------------------------------------------------------ the viewer


def test_the_project_lists_every_stored_plan_and_drawing_with_sheet_numbers(app, facts):
    kevin = _signed_in(app, "kevin")
    page = _text(_get(kevin, f"/site-plans/projects/{facts['assigned_id']}"))
    assert re.findall(r'data-sp-file="([a-z]+-\d+)"', page) == [f"plan-{facts['plan_id']}",
                                                                 f"drawing-{facts['drawing_set_id']}"]
    for number, title in S.SHEETS + S.DRAWING_SHEETS:
        assert f"{number} · {title}" in page
    assert S.PLAN_NAME in page and "Construction drawings" in page and "Revision D1" in page and "Latest" in page
    assert "Save for offline" in page and "Upload a plan PDF" not in page  # crew never upload


def test_an_archived_plan_is_left_out_and_a_drawing_saved_to_plans_is_listed_once(app, facts):
    from app.models.construction_drawing import ConstructionDrawingSet
    from app.plan_intelligence.models import PlanDocument
    from app.plan_intelligence.services import archive_plan_document, store_generated_plan_pdf
    from app.models import Project
    from app.services import site_plans as SP
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG

    project = db.session.get(Project, facts["assigned_id"])
    drawing_set = db.session.get(ConstructionDrawingSet, facts["drawing_set_id"])
    saved = store_generated_plan_pdf(project, drawing_set.pdf_bytes, "construction-drawings-D1.pdf")
    drawing_set.plan_document_id = saved.id
    db.session.commit()
    files = SP.plan_files(ORG, project)
    assert [f.key for f in files] == [f"plan-{saved.id}", f"plan-{facts['plan_id']}"]  # newest first, set once
    assert [s.label for s in files[0].sheets] == [f"{n} · {t}" for n, t in S.DRAWING_SHEETS]  # the set's index
    archive_plan_document(db.session.get(PlanDocument, facts["plan_id"]))
    assert [f.key for f in SP.plan_files(ORG, project)] == [f"plan-{saved.id}"]


def test_the_viewer_shows_every_page_with_its_sheet_number(app, facts):
    kevin = _signed_in(app, "kevin")
    base = f"/site-plans/projects/{facts['assigned_id']}/plan/{facts['plan_id']}"
    r = _get(kevin, base)
    page = _text(r)
    assert r.status_code == 200 and "no-store" in r.headers["Cache-Control"]
    assert f'data-sp-pages="{facts["plan_pages"]}"' in page
    assert re.findall(r'data-src="([^"]+page-\d+\.pdf)"', page) == [f"{base}/page-{n}.pdf" for n in (1, 2, 3)]
    assert "A-101 · Deck framing plan" in page and "A-201 · Sections and details" in page and "Page 3" in page
    assert f'data-src="{base}.pdf#view=FitH"' in page  # computers: the browser's own PDF viewer
    viewport = re.search(r'name="viewport" content="([^"]+)"', page).group(1)
    assert "user-scalable=no" not in viewport and "maximum-scale" not in viewport  # pinch zoom allowed
    drawing = _text(_get(kevin, f"/site-plans/projects/{facts['assigned_id']}/drawing/{facts['drawing_set_id']}"))
    assert "D-1 · Deck plan" in drawing and "D-2 · Framing sections" in drawing


def test_files_are_served_inline_privately_and_whole_or_one_page(app, facts):
    kevin = _signed_in(app, "kevin")
    base = f"/site-plans/projects/{facts['assigned_id']}/plan/{facts['plan_id']}"
    whole = _get(kevin, base + ".pdf")
    assert whole.status_code == 200 and whole.mimetype == "application/pdf"
    assert whole.headers["Cache-Control"] == "private, no-store"
    assert whole.headers["X-Content-Type-Options"] == "nosniff"
    assert whole.headers["Content-Disposition"].startswith("inline")
    assert "Accept-Ranges" not in whole.headers  # the phone always keeps the whole file
    assert len(PdfReader(BytesIO(whole.data)).pages) == 3
    one = _get(kevin, base + "/page-2.pdf")
    assert one.status_code == 200 and one.headers["Cache-Control"] == "private, no-store"
    reader = PdfReader(BytesIO(one.data))
    assert len(reader.pages) == 1 and "A-201" in reader.pages[0].extract_text()
    drawing = _get(kevin, f"/site-plans/projects/{facts['assigned_id']}/drawing/{facts['drawing_set_id']}.pdf")
    assert drawing.status_code == 200 and len(PdfReader(BytesIO(drawing.data)).pages) == 2


def test_no_money_prices_costs_wages_or_customer_contacts_on_any_site_plans_page(app, facts):
    a = facts["assigned_id"]
    pages = ["/site-plans/", f"/site-plans/projects/{a}", f"/site-plans/projects/{a}/plan/{facts['plan_id']}",
             f"/site-plans/projects/{a}/drawing/{facts['drawing_set_id']}"]
    for who in ("kevin", "owner"):
        client = _signed_in(app, who)
        for path in pages:
            html = _text(_get(client, path))
            text = re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S))
            assert not MONEY.findall(text), (who, path, MONEY.findall(text))
            for secret in (S.INTERNAL_COST, S.CUSTOMER[1], S.CUSTOMER[2], "41.25", S.ORG_B_PROJECT):
                assert secret not in html, (who, path, secret)
    assert not MONEY.findall(_text(_get(app.test_client(), "/site-plans/sign-in")))


# ------------------------------------------------------------------ one office plan button; Field and Site Plans agree


def test_the_office_has_one_plan_button_view_project_plan_and_no_site_plans_duplicate(app, facts):
    owner = _signed_in(app, "owner", via="/login")
    a = facts["assigned_id"]
    for path in (f"/projects/{a}", f"/estimates/{facts['estimate_id']}", f"/projects/{a}/plans",
                 f"/schedule/items/{facts['schedule_item_id']}"):
        r = _get(owner, path)
        assert r.status_code == 200, (path, r.status_code)
        html = _text(r)
        assert "data-plans-button" not in html and "header-plans-btn" not in html, path
        assert "site-plans-icon-32.png" not in html, path
    hub = _text(_get(owner, f"/projects/{a}"))
    assert hub.count("data-view-project-plan") == 1 and "View project plan" in hub
    # The office can still open the Site Plans viewer itself (its project list and project pages).
    viewer = _get(owner, f"/site-plans/projects/{a}")
    assert viewer.status_code == 200 and f'href="/projects/{a}"' in _text(viewer)


def test_field_view_project_plan_and_site_plans_use_the_same_crew_rule(app, facts):
    from app.models.user import User
    from app.services import site_plans as SP
    from app.services.access_domains import field_visible_project_ids
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG

    a, u = facts["assigned_id"], facts["unassigned_id"]
    kevin_user = db.session.get(User, facts["kevin_id"])
    ids = field_visible_project_ids(kevin_user, ORG)
    assert SP.visible_project_ids(kevin_user, ORG) == ids
    assert SP.project_for(kevin_user, ORG, a) is not None and SP.project_for(kevin_user, ORG, u) is None
    kevin = _signed_in(app, "kevin")
    job = _text(_get(kevin, f"/field/projects/{a}"))
    assert f'href="/field/projects/{a}/drawings" data-view-project-plan' in job
    assert _get(kevin, f"/field/projects/{a}/drawings").status_code == 200
    assert _get(kevin, f"/site-plans/projects/{a}").status_code == 200
    # Not booked on it: neither Field's plan page nor Site Plans opens it.
    r = _get(kevin, f"/field/projects/{u}/drawings")
    assert r.status_code == 302 and r.headers["Location"].endswith("/field/projects")
    r = _get(kevin, f"/site-plans/projects/{u}")
    assert r.status_code == 302 and r.headers["Location"] == "/site-plans/"  # back to their list, as in Field


def test_site_plans_routes_do_not_collide_with_field_or_the_office(app):
    rules = {}
    for rule in app.url_map.iter_rules():
        key = (rule.rule, tuple(sorted(rule.methods - {"HEAD", "OPTIONS"})))
        rules.setdefault(key, set()).add(rule.endpoint)
    assert all(len(endpoints) == 1 for endpoints in rules.values()), [k for k, v in rules.items() if len(v) > 1]
    site = [r.rule for r in app.url_map.iter_rules() if r.endpoint.startswith("site_plans.")]
    assert site and all(rule.startswith("/site-plans/") for rule in site)
    assert not [r.rule for r in app.url_map.iter_rules()
                if r.rule.startswith("/site-plans/") and not r.endpoint.startswith("site_plans.")]


# ------------------------------------------------------------------ training


def test_the_field_crew_lesson_and_test_and_the_contractor_note(app):
    from app.training import content as C

    field = [lesson for m in C.modules_for(C.PATHWAY_FIELD_CREW, "FIELD") for lesson in m.lessons]
    keys = [lesson.key for lesson in field]
    assert len(keys) == 35  # 35: Field module 9 (Magnificent Seven, 25 Oct 2026)
    assert keys.index("f04-site-plans") == keys.index("f04-drawings") + 1
    lesson = field[keys.index("f04-site-plans")]
    assert lesson.title == "Open plans on site"
    words = " ".join(s.title + " " + s.do + " " + s.expect for s in lesson.steps)
    for needed in ("Add to Home Screen", "Site Plans", "Save for offline", "Airplane Mode", "Sign out", "zoom"):
        assert needed in words, needed
    cases = C.uat_for(C.PATHWAY_FIELD_CREW, "FIELD")
    assert len(cases) == 26 and "uat-f04-site-plans" in [c.key for c in cases]
    contractor = {l.key: l for m in C.modules_for(C.PATHWAY_CONTRACTOR, "OWNER") for l in m.lessons}
    assert all(step.title != "The Plans button" for step in contractor["c07-plans"].steps)  # release 8: removed
    for step in lesson.steps:
        if step.shot:
            assert _png_size(STATIC / "training" / "shots" / step.shot) == (390, 844), step.shot
    assert not (STATIC / "training" / "shots" / "c07-plans-button.png").exists()
