"""Dedicated FG-020 BUILD Field Observation foundation tests."""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from contextlib import contextmanager
from io import BytesIO

import pytest
from flask import g
from flask_login import login_user

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.build import (
    DERIVED_SOURCE_TEST_FIXTURE,
    DERIVED_STATUS_CONFIRMED,
    DERIVED_STATUS_PROPOSED,
    DERIVED_STATUS_REJECTED,
    FieldCaptureDerivedCandidate,
    FieldCaptureEvent,
    FieldCaptureOriginal,
)
from app.models.estimate import Estimate
from app.models.labour_engine import EstimateLabourSnapshot
from app.models.project import PermitProfile
from app.models.proposal import Proposal
from app.plan_intelligence.models import TakeoffPackage
from app.project_controls.models import ChangeOrder
from app.project_controls.services import create_change_order
from app.services.build import (
    create_event_with_text,
    propose_derived_candidate,
)
from app.services.build_storage import absolute_stored_path, stored_relative_path
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.proposals import create_proposal, create_proposal_template
from tests.auth_fixtures import (
    DEFAULT_OFFICE_DISPLAY_NAME,
    DEFAULT_OFFICE_EMAIL,
    DEFAULT_OFFICE_PASSWORD,
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
)


JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
GIF = b"GIF89a" + b"\x00" * 32
MP3 = b"ID3" + b"\x00" * 32
WAV = b"RIFF" + (36).to_bytes(4, "little") + b"WAVE" + b"fmt " + b"\x00" * 24
WEBM = b"\x1a\x45\xdf\xa3" + b"\x00" * 32
AAC = bytes([0xFF, 0xF1]) + b"\x00" * 32


def _iso_bmff(major: bytes, compatible: list[bytes]) -> bytes:
    payload = b"ftyp" + major + (0).to_bytes(4, "big") + b"".join(compatible)
    return (4 + len(payload)).to_bytes(4, "big") + payload + b"\x00" * 24


HEIC = _iso_bmff(b"mif1", [b"heic", b"mif1"])
HEIF = _iso_bmff(b"heif", [b"mif1"])
GENERIC_MP4 = _iso_bmff(b"mp42", [b"isom", b"mp42"])
M4A = _iso_bmff(b"M4A ", [b"isom", b"mp42"])
AVIF = _iso_bmff(b"avif", [b"avif", b"mif1"])


def _csrf_token(response):
    html = response.get_data(as_text=True)
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    if match is None:
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
    assert match is not None, html[:800]
    return match.group(1)


@contextmanager
def office_actor(app):
    user = ensure_office_user()
    prior_present = "_login_user" in g
    prior = getattr(g, "_login_user", None)
    with app.test_request_context():
        login_user(user)
        yield user
    if prior_present:
        g._login_user = prior
    elif hasattr(g, "_login_user"):
        del g._login_user


def _assert_json_error(response, status):
    assert response.status_code == status
    assert response.is_json
    payload = response.get_json()
    assert set(payload.keys()) == {"error"}
    assert payload["error"]
    return payload


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg020",
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


@pytest.fixture
def org_b(app):
    org = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


@pytest.fixture
def csrf_app():
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "csrf-test-fg020",
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def csrf_client(csrf_app):
    return csrf_app.test_client()


def _add_project(*, name, organization_id=DEFAULT_ORGANIZATION_ID, client_name="Field Client"):
    row = Client(name=client_name, organization_id=organization_id)
    db.session.add(row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=row.id,
        organization_id=organization_id,
        status="Active",
        project_number=f"P-{name[:12]}",
        address="must-not-leak-address",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _post_json(client, url, payload):
    return client.post(url, json=payload)


def _multipart(client, url, kind, data, filename, content_type="application/octet-stream"):
    return client.post(
        url,
        data={"kind": kind, "file": (BytesIO(data), filename)},
    )


def test_office_text_event_create_and_hub_list(client, app):
    project = _add_project(name="Office House")
    response = client.post(
        f"/projects/{project.id}/field-events/new",
        data={"text": "Noted wet insulation at north wall."},
        follow_redirects=False,
    )
    assert response.status_code == 302
    event = FieldCaptureEvent.query.filter_by(project_id=project.id).one()
    original = FieldCaptureOriginal.query.filter_by(field_event_id=event.id).one()
    assert original.kind == "text"
    assert original.text_body == "Noted wet insulation at north wall."
    assert original.stored_relative_path is None
    assert original.sha256_hex is None
    assert event.user_id is not None
    assert event.actor_display_name == DEFAULT_OFFICE_DISPLAY_NAME
    assert event.occurred_at == event.created_at
    hub = client.get(f"/projects/{project.id}")
    html = hub.get_data(as_text=True)
    assert hub.status_code == 200
    assert "Field Observations" in html
    assert "Related Change Orders" in html
    assert "Noted wet insulation" not in html or "text" in html
    assert "Office Test User" in html
    assert "Current" in html
    assert "Add text observation" in html
    assert "Field BUILD" not in html
    detail = client.get(f"/projects/{project.id}/field-events/{event.id}")
    assert detail.status_code == 200
    detail_html = detail.get_data(as_text=True)
    assert "Noted wet insulation at north wall." in detail_html
    assert "Record correction" in detail_html
    assert "stored_relative_path" not in detail_html
    assert "build_originals" not in detail_html


def test_api_text_event_create_original_only(client, app):
    project = _add_project(name="API House")
    response = _post_json(
        client,
        f"/api/v1/projects/{project.id}/field-events",
        {"text": "Original-only note", "organization_id": "ORG-HACK", "user_id": 999},
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["organization_id"] == DEFAULT_ORGANIZATION_ID
    assert payload["user_id"] != 999
    assert payload["actor_display_name"] == DEFAULT_OFFICE_DISPLAY_NAME
    assert payload["originals"][0]["kind"] == "text"
    assert payload["derived"] == []
    assert "stored_relative_path" not in payload["originals"][0]
    assert FieldCaptureDerivedCandidate.query.count() == 0


def test_original_only_event_without_text(client, app):
    project = _add_project(name="Binary First")
    created = _post_json(client, f"/api/v1/projects/{project.id}/field-events", {})
    assert created.status_code == 201
    event_id = created.get_json()["id"]
    assert created.get_json()["originals"] == []
    uploaded = _multipart(
        client,
        f"/api/v1/projects/{project.id}/field-events/{event_id}/originals",
        "image",
        JPEG,
        "site.jpg",
    )
    assert uploaded.status_code == 201
    body = uploaded.get_json()
    assert body["kind"] == "image"
    assert body["mime_type"] == "image/jpeg"
    assert body["sha256_hex"] == hashlib.sha256(JPEG).hexdigest()
    assert body["byte_size"] == len(JPEG)
    assert "stored_relative_path" not in body
    listed = client.get(f"/api/v1/projects/{project.id}/field-events/{event_id}/originals")
    assert listed.status_code == 200
    assert listed.get_json()[0]["id"] == body["id"]


def test_organization_project_scope_and_provenance(client, app, org_b):
    home = _add_project(name="Home Job")
    foreign = _add_project(name="Foreign Job", organization_id=org_b.id, client_name="Apex")
    created = _post_json(
        client,
        f"/api/v1/projects/{home.id}/field-events",
        {"text": "Scoped note"},
    )
    event_id = created.get_json()["id"]
    assert client.get(f"/api/v1/projects/{foreign.id}/field-events").status_code == 404
    assert client.get(f"/api/v1/projects/{foreign.id}").status_code == 404
    assert client.get(
        f"/api/v1/projects/{foreign.id}/field-events/{event_id}"
    ).status_code == 404
    event = FieldCaptureEvent.query.get(event_id)
    assert event.organization_id == DEFAULT_ORGANIZATION_ID
    assert event.project_id == home.id
    user = ensure_office_user()
    assert event.user_id == user.id


def test_occurred_at_supplied_normalized_and_invalid(client, app):
    project = _add_project(name="Time Job")
    supplied = _post_json(
        client,
        f"/api/v1/projects/{project.id}/field-events",
        {
            "text": "Timed note",
            "occurred_at": "2026-01-15T18:30:00-05:00",
        },
    )
    assert supplied.status_code == 201
    payload = supplied.get_json()
    assert payload["occurred_at"] == "2026-01-15T23:30:00Z"
    assert payload["created_at"] != payload["occurred_at"]
    naive = _post_json(
        client,
        f"/api/v1/projects/{project.id}/field-events",
        {"text": "Naive", "occurred_at": "2026-02-01T12:00:00"},
    )
    assert naive.status_code == 201
    assert naive.get_json()["occurred_at"] == "2026-02-01T12:00:00Z"
    bad = _post_json(
        client,
        f"/api/v1/projects/{project.id}/field-events",
        {"text": "Bad", "occurred_at": "not-a-datetime"},
    )
    _assert_json_error(bad, 400)


def test_supersession_second_successor_and_wrong_project(client, app):
    first = _add_project(name="Job A")
    second = _add_project(name="Job B")
    prior = _post_json(
        client,
        f"/api/v1/projects/{first.id}/field-events",
        {"text": "Original wording"},
    ).get_json()
    correction = _post_json(
        client,
        f"/api/v1/projects/{first.id}/field-events",
        {"text": "Corrected wording", "supersedes_id": prior["id"]},
    )
    assert correction.status_code == 201
    body = correction.get_json()
    assert body["supersedes_id"] == prior["id"]
    refreshed = client.get(
        f"/api/v1/projects/{first.id}/field-events/{prior['id']}"
    ).get_json()
    assert refreshed["superseded_by_id"] == body["id"]
    assert FieldCaptureEvent.query.get(prior["id"]).id == prior["id"]
    conflict = _post_json(
        client,
        f"/api/v1/projects/{first.id}/field-events",
        {"text": "Second correction", "supersedes_id": prior["id"]},
    )
    _assert_json_error(conflict, 409)
    wrong = _post_json(
        client,
        f"/api/v1/projects/{second.id}/field-events",
        {"text": "Cross project", "supersedes_id": prior["id"]},
    )
    _assert_json_error(wrong, 404)


def test_original_immutability_and_shape(client, app):
    project = _add_project(name="Immutable")
    created = _post_json(
        client,
        f"/api/v1/projects/{project.id}/field-events",
        {"text": "Do not edit"},
    ).get_json()
    event_id = created["id"]
    original_id = created["originals"][0]["id"]
    assert client.put(
        f"/api/v1/projects/{project.id}/field-events/{event_id}/originals/{original_id}",
        json={"text": "mutated"},
    ).status_code == 405
    assert client.patch(
        f"/api/v1/projects/{project.id}/field-events/{event_id}",
        json={"text": "mutated"},
    ).status_code == 405
    row = FieldCaptureOriginal.query.get(original_id)
    assert row.text_body == "Do not edit"
    assert row.kind == "text"
    binary = _multipart(
        client,
        f"/api/v1/projects/{project.id}/field-events/{event_id}/originals",
        "image",
        JPEG,
        "keep.jpg",
    ).get_json()
    image_row = FieldCaptureOriginal.query.get(binary["id"])
    assert image_row.text_body is None
    assert image_row.stored_relative_path
    assert image_row.sha256_hex
    assert image_row.mime_type == "image/jpeg"


@pytest.mark.parametrize(
    "kind,data,filename,mime",
    [
        ("image", JPEG, "a.jpg", "image/jpeg"),
        ("image", PNG, "a.png", "image/png"),
        ("image", GIF, "a.gif", "image/gif"),
        ("image", HEIC, "a.heic", "image/heic"),
        ("image", HEIF, "a.heif", "image/heif"),
        ("audio", M4A, "a.m4a", "audio/mp4"),
        ("audio", AAC, "a.aac", "audio/aac"),
        ("audio", MP3, "a.mp3", "audio/mpeg"),
        ("audio", WAV, "a.wav", "audio/wav"),
        ("audio", WEBM, "a.webm", "audio/webm"),
    ],
)
def test_kind_validation_and_sha(client, app, kind, data, filename, mime):
    project = _add_project(name=f"Media {filename}")
    event_id = _post_json(client, f"/api/v1/projects/{project.id}/field-events", {}).get_json()["id"]
    response = _multipart(
        client,
        f"/api/v1/projects/{project.id}/field-events/{event_id}/originals",
        kind,
        data,
        filename,
    )
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    assert body["mime_type"] == mime
    assert body["sha256_hex"] == hashlib.sha256(data).hexdigest()
    content = client.get(
        f"/api/v1/projects/{project.id}/field-events/{event_id}/originals/{body['id']}/content"
    )
    assert content.status_code == 200
    assert content.data == data
    assert content.mimetype == mime


def test_invalid_heic_and_generic_iso_bmff_rejected(client, app):
    project = _add_project(name="Bad HEIC")
    event_id = _post_json(client, f"/api/v1/projects/{project.id}/field-events", {}).get_json()["id"]
    url = f"/api/v1/projects/{project.id}/field-events/{event_id}/originals"
    _assert_json_error(_multipart(client, url, "image", GENERIC_MP4, "clip.heic"), 400)
    _assert_json_error(_multipart(client, url, "image", JPEG, "photo.heic"), 400)
    _assert_json_error(_multipart(client, url, "image", AVIF, "photo.heic"), 400)
    _assert_json_error(_multipart(client, url, "image", b"not-heic", "photo.heic"), 400)


def test_mime_mismatch_empty_size_and_webp_out(client, app):
    project = _add_project(name="Rejects")
    event_id = _post_json(client, f"/api/v1/projects/{project.id}/field-events", {}).get_json()["id"]
    url = f"/api/v1/projects/{project.id}/field-events/{event_id}/originals"
    _assert_json_error(_multipart(client, url, "image", JPEG, "photo.png"), 400)
    _assert_json_error(_multipart(client, url, "image", b"", "photo.jpg"), 400)
    _assert_json_error(_multipart(client, url, "image", b"RIFF....WEBP", "photo.webp"), 400)
    _assert_json_error(_multipart(client, url, "audio", GENERIC_MP4, "clip.mp3"), 400)
    app.config["BUILD_ORIGINAL_MAX_BYTES"] = 20
    _assert_json_error(_multipart(client, url, "image", JPEG, "photo.jpg"), 400)


def test_path_traversal_denied_and_duplicate_bytes_allowed(client, app):
    with pytest.raises(Exception):
        stored_relative_path("../ORG-001", 1, 1, 1, ".jpg")
    with pytest.raises(Exception):
        absolute_stored_path("ORG-001/1/1/../1.jpg")
    with pytest.raises(Exception):
        absolute_stored_path("/etc/passwd")
    project = _add_project(name="Dupes")
    event_id = _post_json(client, f"/api/v1/projects/{project.id}/field-events", {}).get_json()["id"]
    url = f"/api/v1/projects/{project.id}/field-events/{event_id}/originals"
    first = _multipart(client, url, "image", JPEG, "one.jpg").get_json()
    second = _multipart(client, url, "image", JPEG, "two.jpg").get_json()
    assert first["id"] != second["id"]
    assert first["sha256_hex"] == second["sha256_hex"]
    assert FieldCaptureOriginal.query.count() == 2


def test_authorized_download_and_no_path_leak(client, app, org_b):
    project = _add_project(name="Download")
    event_id = _post_json(client, f"/api/v1/projects/{project.id}/field-events", {}).get_json()["id"]
    uploaded = _multipart(
        client,
        f"/api/v1/projects/{project.id}/field-events/{event_id}/originals",
        "image",
        PNG,
        "wall.png",
    ).get_json()
    office = client.get(
        f"/projects/{project.id}/field-events/{event_id}/originals/{uploaded['id']}"
    )
    assert office.status_code == 200
    assert office.data == PNG
    assert "build_originals" not in office.headers.get("Content-Disposition", "")
    html = client.get(f"/projects/{project.id}/field-events/{event_id}").get_data(as_text=True)
    assert "<img" in html
    assert "stored_relative_path" not in html
    download = client.get(
        f"/projects/{project.id}/field-events/{event_id}/originals/{uploaded['id']}?download=1"
    )
    assert download.status_code == 200
    foreign = _add_project(name="Other Org", organization_id=org_b.id, client_name="Apex")
    assert client.get(
        f"/projects/{foreign.id}/field-events/{event_id}/originals/{uploaded['id']}"
    ).status_code == 404
    assert client.get(
        f"/api/v1/projects/{foreign.id}/field-events/{event_id}/originals/{uploaded['id']}/content"
    ).status_code == 404


@pytest.mark.no_office_auth
def test_unauthenticated_denial(app):
    with office_actor(app):
        project = _add_project(name="Locked")
        event = create_event_with_text(project, "secret")
        project_id = project.id
        event_id = event.id
    anon = app.test_client()
    office = anon.get(
        f"/projects/{project_id}/field-events/{event_id}",
        follow_redirects=False,
    )
    assert office.status_code == 302
    assert "/login" in office.headers["Location"]
    api = anon.get(f"/api/v1/projects/{project_id}/field-events", follow_redirects=False)
    _assert_json_error(api, 401)
    post = anon.post(
        f"/api/v1/projects/{project_id}/field-events",
        json={"text": "nope"},
        follow_redirects=False,
    )
    _assert_json_error(post, 401)


@pytest.mark.no_office_auth
def test_api_403_zero_and_multiple_memberships(app, client):
    project = _add_project(name="Membership")
    create_user(
        email="nomember@example.com",
        password="no-member-password",
        display_name="No Member",
    )
    db.session.commit()
    login_office_user(client, email="nomember@example.com", password="no-member-password")
    _assert_json_error(client.get("/api/v1/projects"), 403)
    user = create_user(
        email="multi@example.com",
        password="multi-password",
        display_name="Multi Member",
    )
    create_membership(user, DEFAULT_ORGANIZATION_ID)
    org = Organization(
        id="ORG-003",
        legal_name="Second Org Ltd.",
        display_name="Second Org",
        primary_address="1 King St",
        default_region="Ottawa",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.flush()
    create_membership(user, "ORG-003")
    db.session.commit()
    client.post("/logout")
    login_office_user(client, email="multi@example.com", password="multi-password")
    _assert_json_error(client.get("/api/v1/me"), 403)
    _assert_json_error(
        client.post(
            f"/api/v1/projects/{project.id}/field-events",
            json={"text": "blocked"},
        ),
        403,
    )


def test_heic_desktop_metadata_not_broken_image(client, app):
    project = _add_project(name="HEIC Desk")
    event_id = _post_json(client, f"/api/v1/projects/{project.id}/field-events", {}).get_json()["id"]
    uploaded = _multipart(
        client,
        f"/api/v1/projects/{project.id}/field-events/{event_id}/originals",
        "image",
        HEIC,
        "iphone.heic",
    ).get_json()
    html = client.get(f"/projects/{project.id}/field-events/{event_id}").get_data(as_text=True)
    assert "image/heic" in html
    assert "iphone.heic" in html
    assert "This photo is saved" in html
    assert "iphone.heic" in html
    assert f'src="/projects/{project.id}/field-events/{event_id}/originals/{uploaded["id"]}"' not in html
    assert ">Original<" in html
    bytes_response = client.get(
        f"/projects/{project.id}/field-events/{event_id}/originals/{uploaded['id']}"
    )
    assert bytes_response.data == HEIC


def test_audio_desktop_rendering(client, app):
    project = _add_project(name="Audio Desk")
    event_id = _post_json(client, f"/api/v1/projects/{project.id}/field-events", {}).get_json()["id"]
    uploaded = _multipart(
        client,
        f"/api/v1/projects/{project.id}/field-events/{event_id}/originals",
        "audio",
        MP3,
        "note.mp3",
    ).get_json()
    html = client.get(f"/projects/{project.id}/field-events/{event_id}").get_data(as_text=True)
    assert "<audio" in html
    assert f"/projects/{project.id}/field-events/{event_id}/originals/{uploaded['id']}" in html
    assert ">Original<" in html
    assert "transcript" not in html.lower()
    assert "waveform" not in html.lower()


def test_derived_propose_confirm_reject_terminal(client, app):
    project = _add_project(name="Derived")
    with office_actor(app):
        event = create_event_with_text(project, "Saw extra labour")
        ok = propose_derived_candidate(
            event,
            kind="labour_note",
            payload={"hours": 4, "note": "extra"},
            source=DERIVED_SOURCE_TEST_FIXTURE,
        )
        event_id = event.id
        candidate_id = ok.id
        project_id = project.id
    assert ok.status == DERIVED_STATUS_PROPOSED
    listed_resp = client.get(
        f"/api/v1/projects/{project_id}/field-events/{event_id}/derived"
    )
    assert listed_resp.status_code == 200, listed_resp.get_json()
    listed = listed_resp.get_json()
    assert listed[0]["payload"] == {"hours": 4, "note": "extra"}
    confirmed = client.post(
        f"/api/v1/projects/{project_id}/field-events/{event_id}/derived/{candidate_id}/confirm",
        json={},
    )
    assert confirmed.status_code == 200
    body = confirmed.get_json()
    assert body["status"] == DERIVED_STATUS_CONFIRMED
    assert body["decided_by_display_name"] == DEFAULT_OFFICE_DISPLAY_NAME
    assert body["decided_by_user_id"] is not None
    _assert_json_error(
        client.post(
            f"/api/v1/projects/{project.id}/field-events/{event.id}/derived/{ok.id}/confirm",
            json={},
        ),
        409,
    )
    _assert_json_error(
        client.post(
            f"/api/v1/projects/{project.id}/field-events/{event.id}/derived/{ok.id}/reject",
            json={},
        ),
        409,
    )
    other = None
    with office_actor(app):
        with pytest.raises(Exception):
            propose_derived_candidate(
                event, kind="bad", payload=[1, 2], source=DERIVED_SOURCE_TEST_FIXTURE
            )
        with pytest.raises(Exception):
            propose_derived_candidate(
                event,
                kind="bad",
                payload="not-json-object",
                source=DERIVED_SOURCE_TEST_FIXTURE,
            )
        other = propose_derived_candidate(
            event,
            kind="material_note",
            payload={"item": "plywood"},
            source=DERIVED_SOURCE_TEST_FIXTURE,
        )
    rejected = client.post(
        f"/api/v1/projects/{project.id}/field-events/{event.id}/derived/{other.id}/reject",
        json={},
    )
    assert rejected.get_json()["status"] == DERIVED_STATUS_REJECTED
    _assert_json_error(
        client.post(
            f"/api/v1/projects/{project.id}/field-events/{event.id}/derived/{other.id}/reject",
            json={},
        ),
        409,
    )


def test_payload_json_object_validation_via_cli(app, client):
    project = _add_project(name="CLI Job")
    with office_actor(app):
        event = create_event_with_text(project, "CLI original")
        event_id = event.id
        project_id = project.id
    runner = app.test_cli_runner()
    ok = runner.invoke(
        args=[
            "build",
            "propose-derived-candidate",
            "--email",
            DEFAULT_OFFICE_EMAIL,
            "--project-id",
            str(project.id),
            "--event-id",
            str(event.id),
            "--kind",
            "uat_note",
            "--payload",
            '{"observed":"yes"}',
        ]
    )
    assert ok.exit_code == 0, ok.output
    candidate = FieldCaptureDerivedCandidate.query.filter_by(kind="uat_note").one()
    assert candidate.source == "UAT_CLI"
    assert json.loads(candidate.payload_json) == {"observed": "yes"}
    bad = runner.invoke(
        args=[
            "build",
            "propose-derived-candidate",
            "--email",
            DEFAULT_OFFICE_EMAIL,
            "--project-id",
            str(project.id),
            "--event-id",
            str(event.id),
            "--kind",
            "uat_note",
            "--payload",
            "[1,2]",
        ]
    )
    assert bad.exit_code != 0
    html = client.get(f"/projects/{project.id}/field-events/{event.id}").get_data(as_text=True)
    assert "uat_note" in html
    assert "Confirm" in html
    assert "Reject" in html
    assert "Generate AI" not in html


def test_confirm_does_not_mutate_commercial_or_monitor(client, app):
    project = _add_project(name="No Side Effects")
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-FG020-0001",
        title="Stay Put",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    template = create_proposal_template(name="FG020 Template")
    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        title="Stay Proposal",
    )
    change_order = create_change_order(project=project, title="Stay CO")
    with office_actor(app):
        event = create_event_with_text(project, "No commercial write")
        candidate = propose_derived_candidate(
            event,
            kind="change_hint",
            payload={"should_not_create_co": True},
            source=DERIVED_SOURCE_TEST_FIXTURE,
        )
    snapshot = {
        "estimates": Estimate.query.count(),
        "estimate_title": estimate.title,
        "proposals": Proposal.query.count(),
        "proposal_title": proposal.title,
        "change_orders": ChangeOrder.query.count(),
        "co_title": change_order.title,
        "co_total": change_order.total,
        "permits": PermitProfile.query.count(),
        "takeoff": TakeoffPackage.query.count(),
        "labour": EstimateLabourSnapshot.query.count(),
    }
    office = client.post(
        f"/projects/{project.id}/field-events/{event.id}/derived/{candidate.id}/confirm",
        follow_redirects=False,
    )
    assert office.status_code == 302
    db.session.refresh(estimate)
    db.session.refresh(proposal)
    db.session.refresh(change_order)
    assert Estimate.query.count() == snapshot["estimates"]
    assert estimate.title == snapshot["estimate_title"]
    assert Proposal.query.count() == snapshot["proposals"]
    assert proposal.title == snapshot["proposal_title"]
    assert ChangeOrder.query.count() == snapshot["change_orders"]
    assert change_order.title == snapshot["co_title"]
    assert change_order.total == snapshot["co_total"]
    assert PermitProfile.query.count() == snapshot["permits"]
    assert TakeoffPackage.query.count() == snapshot["takeoff"]
    assert EstimateLabourSnapshot.query.count() == snapshot["labour"]
    assert "labour_actual_observations" not in db.metadata.tables
    assert "monitor_snapshots" not in db.metadata.tables
    source = inspect.getsource(inspect.getmodule(propose_derived_candidate))
    assert "create_change_order" not in source
    assert "create_estimate(" not in source
    assert "transcrib" not in source.lower()
    assert "ffmpeg" not in source.lower()


def test_fg019_me_and_projects_remain_get_only(client, app):
    _assert_json_error(client.post("/api/v1/me", json={}), 405)
    _assert_json_error(client.post("/api/v1/projects", json={}), 405)
    _assert_json_error(client.post("/api/v1/projects/1", json={}), 405)
    _assert_json_error(client.put("/api/v1/projects/1/field-events", json={}), 405)


def test_api_csrf_required(csrf_app, csrf_client):
    with csrf_app.app_context():
        ensure_office_user()
        project = _add_project(name="CSRF Job")
        project_id = project.id
    token = _csrf_token(csrf_client.get("/login"))
    login = csrf_client.post(
        "/login",
        data={
            "email": DEFAULT_OFFICE_EMAIL,
            "password": DEFAULT_OFFICE_PASSWORD,
            "csrf_token": token,
        },
    )
    assert login.status_code == 302
    missing = csrf_client.post(
        f"/api/v1/projects/{project_id}/field-events",
        json={"text": "needs csrf"},
    )
    assert missing.status_code == 400
    office_token = _csrf_token(csrf_client.get(f"/projects/{project_id}"))
    ok = csrf_client.post(
        f"/api/v1/projects/{project_id}/field-events",
        json={"text": "csrf ok", "organization_id": "ORG-HACK"},
        headers={"X-CSRFToken": office_token},
    )
    assert ok.status_code == 201
    assert ok.get_json()["organization_id"] == DEFAULT_ORGANIZATION_ID
    me_post = csrf_client.post("/api/v1/me", headers={"X-CSRFToken": office_token})
    _assert_json_error(me_post, 405)


def test_office_supersession_display(client, app):
    project = _add_project(name="Correct")
    created = client.post(
        f"/projects/{project.id}/field-events/new",
        data={"text": "First wording", "occurred_at": "2026-03-01T09:15"},
        follow_redirects=False,
    )
    assert created.status_code == 302
    prior = FieldCaptureEvent.query.filter_by(project_id=project.id).one()
    correction = client.post(
        f"/projects/{project.id}/field-events/{prior.id}/supersede",
        data={"text": "Revised wording"},
        follow_redirects=False,
    )
    assert correction.status_code == 302
    successor = FieldCaptureEvent.query.filter_by(supersedes_id=prior.id).one()
    prior_html = client.get(
        f"/projects/{project.id}/field-events/{prior.id}"
    ).get_data(as_text=True)
    new_html = client.get(
        f"/projects/{project.id}/field-events/{successor.id}"
    ).get_data(as_text=True)
    assert "Superseded" in prior_html
    assert f"observation {successor.id}" in prior_html
    assert "Correction of" in new_html
    assert f"observation {prior.id}" in new_html
    assert "First wording" in prior_html
    assert "Revised wording" in new_html
    hub = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "Superseded" in hub
    assert "Current" in hub


def test_no_field_web_or_ai_surfaces(client, app):
    project = _add_project(name="Boundary")
    html = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "Today" not in html or "not operational" in html
    assert "microphone" not in html.lower()
    assert "camera" not in html.lower()
    assert "iPhone Capture" not in html
    assert client.get("/today").status_code == 404
    field = client.get("/field", follow_redirects=False)
    assert field.status_code == 302
    assert field.headers["Location"].endswith("/field/today")
    assert client.get("/api/v1/today").status_code == 404
    assert client.get("/api/v1/field").status_code == 404
    from app.routes import build as build_routes
    from app.services import build as build_service

    combined = inspect.getsource(build_routes) + inspect.getsource(build_service)
    assert "transcrib" not in combined.lower()
    assert "whisper" not in combined.lower()
    assert "ffmpeg" not in combined.lower()


def test_migration_revision_and_models_exist():
    from migrations.versions.c1d2e3f4a5b6_add_build_field_capture_fg020 import (
        down_revision,
        revision,
    )

    assert revision == "c1d2e3f4a5b6"
    assert down_revision == "b0c1d2e3f4a5"
    assert FieldCaptureEvent.__tablename__ == "field_capture_events"
    assert FieldCaptureOriginal.__tablename__ == "field_capture_originals"
    assert FieldCaptureDerivedCandidate.__tablename__ == "field_capture_derived_candidates"
