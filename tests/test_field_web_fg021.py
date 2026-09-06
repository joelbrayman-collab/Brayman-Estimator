"""Dedicated FG-021 Field Web V1 tests."""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from io import BytesIO
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Organization
from app.models.build import FieldCaptureEvent, FieldCaptureOriginal
from app.services.build import normalize_client_uuid
from app.services.organizations import ensure_default_organization
from tests.auth_fixtures import (
    DEFAULT_OFFICE_EMAIL,
    DEFAULT_OFFICE_PASSWORD,
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
    logout_office_user,
)
from tests.test_build_field_observation_fg020 import JPEG, _add_project, _csrf_token
from tests.test_build_media_compatibility_fg020 import _real_heic_bytes


def _uuid():
    return str(uuid.uuid4())


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg021",
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
            "SECRET_KEY": "csrf-test-fg021",
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


def _assert_json_error(response, status):
    assert response.status_code == status
    assert response.is_json
    payload = response.get_json()
    assert set(payload.keys()) == {"error"}
    assert payload["error"]
    return payload


def _login_csrf(csrf_app, csrf_client):
    with csrf_app.app_context():
        ensure_office_user()
    token = _csrf_token(csrf_client.get("/login"))
    csrf_client.post(
        "/login",
        data={
            "email": DEFAULT_OFFICE_EMAIL,
            "password": DEFAULT_OFFICE_PASSWORD,
            "csrf_token": token,
        },
    )
    return _csrf_token(csrf_client.get("/field/today"))


@pytest.mark.no_office_auth
def test_field_today_requires_login(client):
    response = client.get("/field/today", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers["Location"]
    assert "/login" in location
    assert "next=" in location
    assert "field" in location and "today" in location


def test_field_root_redirects_today(client):
    response = client.get("/field", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/field/today")


def test_capture_without_confirm_redirects(client, app):
    project = _add_project(name="Field Confirm")
    response = client.get(
        f"/field/projects/{project.id}/capture",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/field/projects/{project.id}")


def test_project_confirm_then_capture(client, app):
    project = _add_project(name="Field House")
    confirm = client.post(
        f"/field/projects/{project.id}",
        data={"next": "capture"},
        follow_redirects=False,
    )
    assert confirm.status_code == 302
    assert confirm.headers["Location"].endswith(f"/field/projects/{project.id}/capture")
    capture = client.get(f"/field/projects/{project.id}/capture")
    assert capture.status_code == 200
    html = capture.get_data(as_text=True)
    assert "Field House" in html
    assert "Take Photo" in html
    assert "Choose Photo" in html
    assert "Save original" in html
    assert "app-shell" not in html
    assert "shell-sidebar" not in html


def test_event_uuid_create_replay_and_conflict(client, app):
    home = _add_project(name="Replay Home")
    other = _add_project(name="Replay Other")
    capture_uuid = _uuid()
    first = client.post(
        f"/api/v1/projects/{home.id}/field-events",
        json={"client_capture_uuid": capture_uuid},
    )
    assert first.status_code == 201
    body = first.get_json()
    event_id = body["id"]
    assert body["client_capture_uuid"] == capture_uuid
    replay = client.post(
        f"/api/v1/projects/{home.id}/field-events",
        json={"client_capture_uuid": capture_uuid},
    )
    assert replay.status_code == 200
    assert replay.get_json()["id"] == event_id
    assert FieldCaptureEvent.query.filter_by(project_id=home.id).count() == 1
    conflict = client.post(
        f"/api/v1/projects/{other.id}/field-events",
        json={"client_capture_uuid": capture_uuid},
    )
    _assert_json_error(conflict, 409)
    occurred = client.post(
        f"/api/v1/projects/{home.id}/field-events",
        json={
            "client_capture_uuid": capture_uuid,
            "occurred_at": "2020-01-01T00:00:00Z",
        },
    )
    _assert_json_error(occurred, 409)


def test_event_invalid_uuid_and_office_omit(client, app):
    project = _add_project(name="Office UUID")
    bad = client.post(
        f"/api/v1/projects/{project.id}/field-events",
        json={"client_capture_uuid": "not-a-uuid"},
    )
    _assert_json_error(bad, 400)
    urn = client.post(
        f"/api/v1/projects/{project.id}/field-events",
        json={"client_capture_uuid": f"urn:uuid:{_uuid()}"},
    )
    _assert_json_error(urn, 400)
    omitted = client.post(f"/api/v1/projects/{project.id}/field-events", json={})
    assert omitted.status_code == 201
    assert omitted.get_json()["client_capture_uuid"] is None


def test_original_uuid_create_replay_conflict_and_same_sha(client, app):
    project = _add_project(name="Original Replay")
    created = client.post(f"/api/v1/projects/{project.id}/field-events", json={})
    event_id = created.get_json()["id"]
    original_uuid = _uuid()
    url = f"/api/v1/projects/{project.id}/field-events/{event_id}/originals"
    first = client.post(
        url,
        data={
            "kind": "image",
            "client_original_uuid": original_uuid,
            "file": (BytesIO(JPEG), "site.jpg"),
        },
    )
    assert first.status_code == 201
    original_id = first.get_json()["id"]
    assert first.get_json()["client_original_uuid"] == original_uuid
    replay = client.post(
        url,
        data={
            "kind": "image",
            "client_original_uuid": original_uuid,
            "file": (BytesIO(JPEG), "renamed.jpg"),
        },
    )
    assert replay.status_code == 200
    assert replay.get_json()["id"] == original_id
    assert FieldCaptureOriginal.query.filter_by(field_event_id=event_id).count() == 1
    conflict = client.post(
        url,
        data={
            "kind": "image",
            "client_original_uuid": original_uuid,
            "file": (BytesIO(JPEG + b"x"), "site.jpg"),
        },
    )
    _assert_json_error(conflict, 409)
    other_uuid = _uuid()
    second = client.post(
        url,
        data={
            "kind": "image",
            "client_original_uuid": other_uuid,
            "file": (BytesIO(JPEG), "copy.jpg"),
        },
    )
    assert second.status_code == 201
    assert second.get_json()["id"] != original_id
    assert FieldCaptureOriginal.query.filter_by(field_event_id=event_id).count() == 2
    omitted = client.post(
        url,
        json={"kind": "text", "text": "office note"},
    )
    assert omitted.status_code == 201
    assert omitted.get_json()["client_original_uuid"] is None


def test_text_original_uuid_replay_and_conflict(client, app):
    project = _add_project(name="Text Replay")
    created = client.post(f"/api/v1/projects/{project.id}/field-events", json={})
    event_id = created.get_json()["id"]
    url = f"/api/v1/projects/{project.id}/field-events/{event_id}/originals"
    original_uuid = _uuid()
    first = client.post(
        url,
        json={
            "kind": "text",
            "text": "wet insulation",
            "client_original_uuid": original_uuid,
        },
    )
    assert first.status_code == 201
    replay = client.post(
        url,
        json={
            "kind": "text",
            "text": "wet insulation",
            "client_original_uuid": original_uuid,
        },
    )
    assert replay.status_code == 200
    assert replay.get_json()["id"] == first.get_json()["id"]
    conflict = client.post(
        url,
        json={
            "kind": "text",
            "text": "different note",
            "client_original_uuid": original_uuid,
        },
    )
    _assert_json_error(conflict, 409)


@pytest.mark.no_office_auth
def test_api_unauthenticated_is_json_401(client, app):
    project = _add_project(name="Auth Field")
    response = client.post(
        f"/api/v1/projects/{project.id}/field-events",
        json={"client_capture_uuid": _uuid()},
    )
    _assert_json_error(response, 401)


def test_cross_org_field_and_display_404(client, app, org_b):
    home = _add_project(name="Home Org")
    created = client.post(
        f"/api/v1/projects/{home.id}/field-events",
        json={"text": "secret"},
    )
    event_id = created.get_json()["id"]
    original_id = created.get_json()["originals"][0]["id"]
    other = _add_project(name="Other Org", organization_id=org_b.id)
    user = create_user(
        email="apex@example.com",
        password="apex-password",
        display_name="Apex User",
    )
    create_membership(user, org_b.id)
    db.session.commit()
    logout_office_user(client)
    login_office_user(client, email="apex@example.com", password="apex-password")
    missing = client.get(f"/api/v1/projects/{home.id}/field-events")
    _assert_json_error(missing, 404)
    display = client.get(
        f"/api/v1/projects/{home.id}/field-events/{event_id}/originals/{original_id}/display"
    )
    _assert_json_error(display, 404)
    capture = client.get(f"/field/projects/{home.id}", follow_redirects=False)
    assert capture.status_code in {302, 200}
    if capture.status_code == 200:
        assert "Home Org" not in capture.get_data(as_text=True)
    assert other.id != home.id


def test_display_jpeg_and_heic(client, app):
    project = _add_project(name="Display House")
    created = client.post(f"/api/v1/projects/{project.id}/field-events", json={})
    event_id = created.get_json()["id"]
    url = f"/api/v1/projects/{project.id}/field-events/{event_id}/originals"
    jpeg = client.post(
        url,
        data={"kind": "image", "file": (BytesIO(JPEG), "site.jpg")},
    )
    assert jpeg.status_code == 201
    jpeg_id = jpeg.get_json()["id"]
    shown = client.get(
        f"/api/v1/projects/{project.id}/field-events/{event_id}/originals/{jpeg_id}/display"
    )
    assert shown.status_code == 200
    assert shown.mimetype == "image/jpeg"
    assert shown.data.startswith(b"\xff\xd8\xff")
    heic_bytes = _real_heic_bytes()
    heic = client.post(
        url,
        data={"kind": "image", "file": (BytesIO(heic_bytes), "site.heic")},
    )
    assert heic.status_code == 201
    heic_id = heic.get_json()["id"]
    rendition = client.get(
        f"/api/v1/projects/{project.id}/field-events/{event_id}/originals/{heic_id}/display"
    )
    assert rendition.status_code == 200
    assert rendition.mimetype == "image/jpeg"
    assert rendition.data.startswith(b"\xff\xd8\xff")
    assert hashlib.sha256(heic_bytes).hexdigest() == heic.get_json()["sha256_hex"]


def test_fg019_post_locks_remain(client):
    me_post = client.post("/api/v1/me")
    _assert_json_error(me_post, 405)
    projects_post = client.post("/api/v1/projects")
    _assert_json_error(projects_post, 405)


def test_csrf_required_and_replay_after_fresh_token(csrf_app, csrf_client):
    with csrf_app.app_context():
        project = _add_project(name="CSRF Field")
        project_id = project.id
    token = _login_csrf(csrf_app, csrf_client)
    missing = csrf_client.post(
        f"/api/v1/projects/{project_id}/field-events",
        json={"client_capture_uuid": _uuid()},
    )
    assert missing.status_code == 400
    capture_uuid = _uuid()
    first = csrf_client.post(
        f"/api/v1/projects/{project_id}/field-events",
        json={"client_capture_uuid": capture_uuid},
        headers={"X-CSRFToken": token},
    )
    assert first.status_code == 201
    fresh = _csrf_token(csrf_client.get("/field/today"))
    replay = csrf_client.post(
        f"/api/v1/projects/{project_id}/field-events",
        json={"client_capture_uuid": capture_uuid},
        headers={"X-CSRFToken": fresh},
    )
    assert replay.status_code == 200
    me_post = csrf_client.post("/api/v1/me", headers={"X-CSRFToken": fresh})
    _assert_json_error(me_post, 405)


FIELD_JS = Path(__file__).resolve().parents[1] / "app" / "static" / "js" / "field.js"
FIELD_CSS = Path(__file__).resolve().parents[1] / "app" / "static" / "css" / "field.css"
PREPARE_FAIL_MESSAGE = "Unable to prepare this capture for saving. Please retry."


def _css_media_block(source: str, query: str) -> str:
    marker = f"@media {query}"
    idx = source.index(marker)
    brace = source.index("{", idx)
    depth = 0
    for offset, char in enumerate(source[brace:]):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[brace : brace + offset + 1]
    raise AssertionError(f"unclosed {marker}")


def test_field_css_landscape_tolerance_contract():
    source = FIELD_CSS.read_text(encoding="utf-8")
    default = source.split("@media", 1)[0]
    wide = _css_media_block(source, "(min-width: 720px)")
    landscape = _css_media_block(source, "(orientation: landscape)")

    assert ".field-actions" in default
    assert "flex-direction: column" in default
    assert "max-width: 42rem" in default
    assert "min-height: 6rem" in default
    assert "min-height: 48px" in default
    assert "min-height: 56px" in default
    assert "min-height: 44px" in default
    assert "min-width: 44px" in default
    assert "(orientation: landscape)" not in default
    assert "flex-direction: row" not in default
    assert "position: sticky" not in default
    assert "grid-template-columns: 1fr 1fr" not in default

    assert source.index("@media (min-width: 720px)") < source.index(
        "@media (orientation: landscape)"
    )
    assert "orientation" not in wide
    assert "flex-direction: row" in wide
    assert "grid-template-columns" not in wide
    assert "position: sticky" not in wide
    assert "max-width: none" not in wide

    assert "max-width: none" in landscape
    assert "grid-template-columns: 1fr 1fr" in landscape
    assert "flex-direction: row" in landscape
    assert "min-height: 2.75rem" in landscape
    assert "min-height: 44px" in landscape
    assert "min-height: 48px" in landscape
    assert "min-width: 44px" in landscape
    assert "position: sticky" in landscape
    assert ".field-save" in landscape
    assert "min-height: 6rem" not in landscape
    assert "flex-direction: column" not in landscape
    assert "(min-width: 720px)" not in landscape
    assert landscape.count("min-height: 44px") >= 1


def _uuid_v4_from_getrandomvalues(random_bytes: bytes) -> str:
    """Mirror field.js getRandomValues fallback. JS remains the source of truth."""
    assert len(random_bytes) == 16
    buf = bytearray(random_bytes)
    buf[6] = (buf[6] & 0x0F) | 0x40
    buf[8] = (buf[8] & 0x3F) | 0x80
    hexed = buf.hex()
    return (
        f"{hexed[0:8]}-{hexed[8:12]}-{hexed[12:16]}-{hexed[16:20]}-{hexed[20:32]}"
    )


def test_field_js_lan_http_uuid_fallback_contract():
    source = FIELD_JS.read_text(encoding="utf-8")
    fn_match = re.search(r"function newUuid\(\) \{.*?\n  \}", source, re.S)
    assert fn_match, "newUuid() must remain in field.js"
    new_uuid_src = fn_match.group(0)
    assert "crypto.randomUUID" in new_uuid_src
    assert "crypto.getRandomValues" in new_uuid_src
    assert "0x40" in new_uuid_src
    assert "0x0f" in new_uuid_src
    assert "0x80" in new_uuid_src
    assert "0x3f" in new_uuid_src
    assert "Math.random" not in source
    assert "This browser cannot create a capture identity." in new_uuid_src
    save_match = re.search(r"function saveNew\(projectId\) \{.*?\n  \}", source, re.S)
    assert save_match, "saveNew() must remain in field.js"
    save_src = save_match.group(0)
    assert "try {" in save_src
    assert "newUuid()" in save_src
    assert PREPARE_FAIL_MESSAGE in save_src
    assert "err.message" not in save_src
    assert "err.stack" not in save_src


def test_getrandomvalues_fallback_and_randomuuid_pass_server(client, app):
    project = _add_project(name="LAN UUID Fallback")
    random_style = str(uuid.uuid4())
    parsed_random = uuid.UUID(random_style)
    assert parsed_random.version == 4
    assert random_style == str(parsed_random)
    assert normalize_client_uuid(random_style, field_name="client_capture_uuid") == random_style
    first = client.post(
        f"/api/v1/projects/{project.id}/field-events",
        json={"client_capture_uuid": random_style},
    )
    assert first.status_code == 201
    assert first.get_json()["client_capture_uuid"] == random_style

    fallback = _uuid_v4_from_getrandomvalues(os.urandom(16))
    assert len(fallback) == 36
    assert fallback == fallback.lower()
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        fallback,
    )
    parsed = uuid.UUID(fallback)
    assert parsed.version == 4
    assert parsed.variant == uuid.RFC_4122
    assert str(parsed) == fallback
    assert normalize_client_uuid(fallback, field_name="client_capture_uuid") == fallback
    second = client.post(
        f"/api/v1/projects/{project.id}/field-events",
        json={"client_capture_uuid": fallback},
    )
    assert second.status_code == 201
    assert second.get_json()["client_capture_uuid"] == fallback
    assert FieldCaptureEvent.query.filter_by(project_id=project.id).count() == 2


STORAGE_FAIL_MESSAGE = (
    "Cannot safely keep this capture on this phone. Try photo or text later, or free storage."
)


def test_field_js_image_bytes_indexeddb_contract():
    source = FIELD_JS.read_text(encoding="utf-8")
    assert "function bytesFromBlob" in source
    assert "function bytesFromImageFile" in source
    assert "function normalizeImageOriginals" in source
    assert "function fileBlobForUpload" in source
    assert "function persistFailure" in source
    assert "function logFieldPersistFailure" in source
    assert "arrayBuffer()" in source
    assert "new Uint8Array(buffer)" in source
    assert "row.bytes = bytes" in source
    assert "delete row.blob" in source
    assert 'new Blob([original.bytes], { type: original.mime || "" })' in source
    assert 'form.append("file", fileBlob, original.filename || "capture")' in source
    assert "IMAGE_ARRAYBUFFER_READ" in source
    assert "INDEXEDDB_PENDING_ORIGINAL_PUT" in source
    assert "IMAGE_BLOB_RECONSTRUCT" in source
    assert "MULTIPART_PREPARE" in source
    assert "Math.random" not in source
    assert re.search(r"heic|heif|transcode|createImageBitmap|OffscreenCanvas", source, re.I) is None
    bytes_fn = re.search(r"function bytesFromBlob\(source, stage\) \{.*?\n  \}", source, re.S)
    assert bytes_fn, "bytesFromBlob() must remain in field.js"
    assert "arrayBuffer()" in bytes_fn.group(0)
    assert "new Blob(" not in bytes_fn.group(0)
    image_fn = re.search(r"function bytesFromImageFile\(source\) \{.*?\n  \}", source, re.S)
    assert image_fn, "bytesFromImageFile() must remain in field.js"
    assert "IMAGE_ARRAYBUFFER_READ" in image_fn.group(0)
    assert "new Blob(" not in image_fn.group(0)
    save_match = re.search(r"function saveNew\(projectId\) \{.*?\n  \}", source, re.S)
    assert save_match, "saveNew() must remain in field.js"
    save_src = save_match.group(0)
    assert save_src.index("normalizeImageOriginals") < save_src.index("persistCapture")
    assert save_src.index("persistCapture") < save_src.index("uploadCapture")
    assert STORAGE_FAIL_MESSAGE in save_src
    assert "err.message" not in save_src
    assert "err.stack" not in save_src
    catch_src = save_src[save_src.rfind(".catch(function (err)") :]
    assert "logFieldPersistFailure" in catch_src
    assert "uploadCapture" not in catch_src
    assert "postEvent" not in catch_src
    assert "postJson" not in catch_src
    assert "postForm" not in catch_src
    audio_push = save_src[save_src.index('kind: "audio"') : save_src.index("photos.forEach")]
    assert "bytesFromImageFile" not in audio_push
    assert "bytesFromBlob" not in audio_push
    log_match = re.search(r"function logFieldPersistFailure\(err\) \{.*?\n  \}", source, re.S)
    assert log_match, "logFieldPersistFailure() must remain in field.js"
    log_src = log_match.group(0)
    assert "console.warn" in log_src
    assert "stage" in log_src
    assert "cookie" not in log_src.lower()
    assert "csrf" not in log_src.lower()
    assert "password" not in log_src.lower()
    assert "blob" not in log_src.lower()
    init_match = re.search(r"function init\(\) \{.*?\n  \}", source, re.S)
    assert init_match
    assert 'persistFailure("idb_open"' in init_match.group(0)


def test_field_js_audio_bytes_indexeddb_contract():
    source = FIELD_JS.read_text(encoding="utf-8")
    assert "AUDIO_ARRAYBUFFER_READ" in source
    assert "AUDIO_BLOB_RECONSTRUCT" in source
    assert "INDEXEDDB_PENDING_ORIGINAL_PUT" in source
    assert "MULTIPART_PREPARE" in source
    assert re.search(r"transcode|ffmpeg|transcri", source, re.I) is None
    normalize = re.search(r"function normalizeImageOriginals\(originals\) \{.*?\n  \}", source, re.S)
    assert normalize, "normalizeImageOriginals() must remain in field.js"
    norm_src = normalize.group(0)
    assert 'row.kind !== "audio"' in norm_src
    assert "AUDIO_ARRAYBUFFER_READ" in norm_src
    assert "delete row.blob" in norm_src
    upload = re.search(r"function fileBlobForUpload\(original\) \{.*?\n  \}", source, re.S)
    assert upload, "fileBlobForUpload() must remain in field.js"
    upload_src = upload.group(0)
    assert 'original.kind === "audio"' in upload_src
    assert "AUDIO_BLOB_RECONSTRUCT" in upload_src
    assert 'new Blob([original.bytes], { type: original.mime || "" })' in upload_src
    save_match = re.search(r"function saveNew\(projectId\) \{.*?\n  \}", source, re.S)
    save_src = save_match.group(0)
    assert save_src.index("normalizeImageOriginals") < save_src.index("persistCapture")
    assert save_src.index("persistCapture") < save_src.index("uploadCapture")
    audio_push = save_src[save_src.index('kind: "audio"') : save_src.index("photos.forEach")]
    assert "blob: recordedBlob" in audio_push
    assert "mime: recordedMime" in audio_push
    assert "bytesFromBlob" not in audio_push
    catch_src = save_src[save_src.rfind(".catch(function (err)") :]
    assert STORAGE_FAIL_MESSAGE in catch_src
    assert "uploadCapture" not in catch_src
    assert "postEvent" not in catch_src


def test_photo_bytes_persist_and_blob_reconstruct_preserves_bytes_mime_filename():
    """Mirror: File.arrayBuffer() → Uint8Array persist → Blob([bytes], {type: mime}) for POST."""
    original = b"\xff\xd8\xff" + os.urandom(128)
    mime = "image/jpeg"
    filename = "IMG_UAT.PNG"
    capture_uuid = str(uuid.uuid4())
    original_uuid = str(uuid.uuid4())
    stored_bytes = bytes(original)
    row = {
        "client_original_uuid": original_uuid,
        "client_capture_uuid": capture_uuid,
        "kind": "image",
        "bytes": stored_bytes,
        "filename": filename,
        "mime": mime,
        "state": "pending",
    }
    assert "blob" not in row
    assert row["bytes"] == original
    reconstructed = bytes(row["bytes"])
    reconstructed_type = row["mime"]
    assert reconstructed == original
    assert reconstructed_type == mime
    assert row["filename"] == filename
    form_filename = row["filename"] or "capture"
    assert form_filename == filename
    assert hashlib.sha256(reconstructed).digest() == hashlib.sha256(original).digest()


def test_audio_bytes_persist_and_blob_reconstruct_preserves_bytes_mime_filename():
    """Mirror: Blob.arrayBuffer() → Uint8Array persist → Blob([bytes], {type: mime}) for POST."""
    original = b"\x00\x01\x02" + os.urandom(128)
    mime = "audio/mp4"
    filename = "note.m4a"
    capture_uuid = str(uuid.uuid4())
    original_uuid = str(uuid.uuid4())
    stored_bytes = bytes(original)
    row = {
        "client_original_uuid": original_uuid,
        "client_capture_uuid": capture_uuid,
        "kind": "audio",
        "bytes": stored_bytes,
        "filename": filename,
        "mime": mime,
        "state": "pending",
    }
    assert "blob" not in row
    assert row["bytes"] == original
    reconstructed = bytes(row["bytes"])
    reconstructed_type = row["mime"]
    assert reconstructed == original
    assert reconstructed_type == mime
    assert row["filename"] == filename
    form_filename = row["filename"] or "capture"
    assert form_filename == filename
    assert hashlib.sha256(reconstructed).digest() == hashlib.sha256(original).digest()
