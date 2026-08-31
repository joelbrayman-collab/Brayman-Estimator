"""FG-020 Media Compatibility increment: HEIC/HEIF → JPEG display renditions.

HEIC bytes used here are generated in-process with Pillow/pillow-heif (tiny
synthetic stills for decode/orientation). The existing FG-020 ftyp-only HEIC
stub (`HEIC` in test_build_field_observation_fg020) is reused only as an
undecodable conversion-failure fixture. No third-party photograph is stored
in the repository.
"""

from __future__ import annotations

import hashlib
import socket
from io import BytesIO

import pytest
from PIL import Image, ImageOps

from app import create_app, db
from app.models import Organization
from app.models.build import FieldCaptureDerivedCandidate, FieldCaptureOriginal
from app.services.build_rendition import (
    DISPLAY_FILENAME,
    JPEG_QUALITY,
    MAX_LONG_EDGE,
    absolute_rendition_path,
    convert_heic_original_to_jpeg,
    ensure_compatible_rendition,
)
from app.services.build_storage import absolute_stored_path
from app.services.organizations import ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.test_build_field_observation_fg020 import (
    GIF,
    HEIC,
    JPEG,
    MP3,
    PNG,
    _add_project,
    _multipart,
    _post_json,
)


def _real_heic_bytes(*, width=32, height=48, left_green=True) -> bytes:
    image = Image.new("RGB", (width, height), (200, 40, 40))
    if left_green:
        for y in range(height):
            for x in range(min(8, width)):
                image.putpixel((x, y), (0, 255, 0))
    buf = BytesIO()
    image.save(buf, format="HEIF")
    return buf.getvalue()


def _oriented_heic_bytes() -> bytes:
    image = Image.new("RGB", (40, 20), (10, 10, 200))
    for x in range(40):
        for y in range(4):
            image.putpixel((x, y), (0, 255, 0))
    exif = Image.Exif()
    exif[0x0112] = 6
    buf = BytesIO()
    image.save(buf, format="HEIF", exif=exif.tobytes())
    return buf.getvalue()


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg020-rendition",
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


def _upload_heic(client, filename="iphone.heic", data=None):
    project = _add_project(name="Rendition House")
    event_id = _post_json(
        client, f"/api/v1/projects/{project.id}/field-events", {}
    ).get_json()["id"]
    payload = data if data is not None else _real_heic_bytes()
    uploaded = _multipart(
        client,
        f"/api/v1/projects/{project.id}/field-events/{event_id}/originals",
        "image",
        payload,
        filename,
    )
    assert uploaded.status_code == 201, uploaded.get_data(as_text=True)[:800]
    return project, event_id, uploaded.get_json(), payload


def test_heic_original_preserved_and_jpeg_rendition_generated(client, app):
    project, event_id, body, source = _upload_heic(client)
    original = FieldCaptureOriginal.query.get(body["id"])
    source_path = absolute_stored_path(original.stored_relative_path)
    stored = source_path.read_bytes()
    assert stored == source
    assert hashlib.sha256(stored).hexdigest() == original.sha256_hex
    assert original.sha256_hex == hashlib.sha256(source).hexdigest()
    assert original.mime_type == "image/heic"
    rendition = absolute_rendition_path(original)
    assert rendition.is_file()
    jpeg = rendition.read_bytes()
    assert jpeg.startswith(b"\xff\xd8\xff")
    assert jpeg != stored
    decoded = Image.open(BytesIO(jpeg))
    assert decoded.format == "JPEG"
    assert decoded.mode == "RGB"
    assert FieldCaptureDerivedCandidate.query.count() == 0
    assert DISPLAY_FILENAME == rendition.name
    assert JPEG_QUALITY == 85
    assert MAX_LONG_EDGE == 2048


def test_rendition_does_not_replace_original_download(client, app):
    project, event_id, body, source = _upload_heic(client)
    original_id = body["id"]
    original_bytes = client.get(
        f"/projects/{project.id}/field-events/{event_id}/originals/{original_id}?download=1"
    )
    assert original_bytes.status_code == 200
    assert original_bytes.data == source
    display = client.get(
        f"/projects/{project.id}/field-events/{event_id}/originals/{original_id}/display"
    )
    assert display.status_code == 200
    assert display.mimetype == "image/jpeg"
    assert display.data.startswith(b"\xff\xd8\xff")
    assert display.data != source


def test_event_detail_uses_rendition_for_real_heic(client, app):
    project, event_id, body, _source = _upload_heic(client)
    original_id = body["id"]
    html = client.get(f"/projects/{project.id}/field-events/{event_id}").get_data(
        as_text=True
    )
    assert "Photo" in html
    assert (
        f'src="/projects/{project.id}/field-events/{event_id}/originals/{original_id}/display"'
        in html
    )
    assert ">Original<" in html
    assert "Compatible Rendition" not in html
    assert "build_renditions" not in html
    assert str(app.config["BUILD_RENDITION_ROOT"]) not in html
    hub = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "Field Observations" in hub
    assert "Related Change Orders" in hub
    assert "build_renditions" not in hub


def test_undecodable_heic_keeps_original_without_rendition(client, app):
    project, event_id, body, source = _upload_heic(
        client, data=HEIC, filename="stub.heic"
    )
    original = FieldCaptureOriginal.query.get(body["id"])
    assert original.sha256_hex == hashlib.sha256(source).hexdigest()
    assert absolute_stored_path(original.stored_relative_path).read_bytes() == source
    rendition = absolute_rendition_path(original)
    assert not rendition.exists()
    html = client.get(f"/projects/{project.id}/field-events/{event_id}").get_data(
        as_text=True
    )
    assert "This photo is saved" in html
    assert (
        f'src="/projects/{project.id}/field-events/{event_id}/originals/{body["id"]}"'
        not in html
    )
    display = client.get(
        f"/projects/{project.id}/field-events/{event_id}/originals/{body['id']}/display"
    )
    assert display.status_code == 404


def test_jpeg_png_gif_do_not_create_rendition(client, app):
    project = _add_project(name="Native Photos")
    event_id = _post_json(
        client, f"/api/v1/projects/{project.id}/field-events", {}
    ).get_json()["id"]
    for data, name in ((JPEG, "a.jpg"), (PNG, "a.png"), (GIF, "a.gif")):
        uploaded = _multipart(
            client,
            f"/api/v1/projects/{project.id}/field-events/{event_id}/originals",
            "image",
            data,
            name,
        ).get_json()
        original = FieldCaptureOriginal.query.get(uploaded["id"])
        assert not absolute_rendition_path(original).exists()
        display = client.get(
            f"/projects/{project.id}/field-events/{event_id}/originals/{original.id}/display"
        )
        assert display.status_code == 404


def test_audio_does_not_create_rendition(client, app):
    project = _add_project(name="Voice Note")
    event_id = _post_json(
        client, f"/api/v1/projects/{project.id}/field-events", {}
    ).get_json()["id"]
    uploaded = _multipart(
        client,
        f"/api/v1/projects/{project.id}/field-events/{event_id}/originals",
        "audio",
        MP3,
        "note.mp3",
    ).get_json()
    original = FieldCaptureOriginal.query.get(uploaded["id"])
    html = client.get(f"/projects/{project.id}/field-events/{event_id}").get_data(
        as_text=True
    )
    assert "<audio" in html
    assert "transcript" not in html.lower()
    assert "waveform" not in html.lower()
    display = client.get(
        f"/projects/{project.id}/field-events/{event_id}/originals/{original.id}/display"
    )
    assert display.status_code == 404


def test_existing_rendition_reused_and_regenerated_after_delete(client, app):
    _project, _event_id, body, source = _upload_heic(client)
    original = FieldCaptureOriginal.query.get(body["id"])
    first = absolute_rendition_path(original)
    first_bytes = first.read_bytes()
    first_mtime = first.stat().st_mtime
    reused = ensure_compatible_rendition(original)
    assert reused == first
    assert first.read_bytes() == first_bytes
    assert first.stat().st_mtime == first_mtime
    first.unlink()
    assert not first.exists()
    assert absolute_stored_path(original.stored_relative_path).read_bytes() == source
    regenerated = ensure_compatible_rendition(original)
    assert regenerated.is_file()
    assert regenerated.read_bytes().startswith(b"\xff\xd8\xff")
    assert absolute_stored_path(original.stored_relative_path).read_bytes() == source


def test_orientation_applied_to_jpeg_rendition():
    heic = _oriented_heic_bytes()
    jpeg = convert_heic_original_to_jpeg(heic)
    opened = Image.open(BytesIO(heic))
    expected = ImageOps.exif_transpose(opened) or opened
    decoded = Image.open(BytesIO(jpeg))
    assert decoded.size == expected.size
    # EXIF orientation 6 on a 40x20 source yields a 20x40 upright display.
    assert decoded.size == (20, 40)


def test_conversion_is_local_only():
    heic = _real_heic_bytes()

    class _NoNetSocket(socket.socket):
        def connect(self, *args, **kwargs):
            raise AssertionError("network conversion is not allowed")

        def connect_ex(self, *args, **kwargs):
            raise AssertionError("network conversion is not allowed")

    original_socket = socket.socket
    socket.socket = _NoNetSocket
    try:
        jpeg = convert_heic_original_to_jpeg(heic)
    finally:
        socket.socket = original_socket
    assert jpeg.startswith(b"\xff\xd8\xff")


@pytest.mark.no_office_auth
def test_unauthenticated_rendition_denied(app):
    authed = app.test_client()
    with app.app_context():
        ensure_office_user()
        login_office_user(authed)
        project, event_id, body, _source = _upload_heic(authed)
        project_id = int(project.id)
        original_id = int(body["id"])
    anon = app.test_client()
    response = anon.get(
        f"/projects/{project_id}/field-events/{event_id}/originals/{original_id}/display",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")


def test_cross_org_rendition_denied(client, app, org_b):
    project, event_id, body, _source = _upload_heic(client)
    original_id = body["id"]
    foreign = _add_project(
        name="Apex Job", organization_id=org_b.id, client_name="Apex"
    )
    denied = client.get(
        f"/projects/{foreign.id}/field-events/{event_id}/originals/{original_id}/display"
    )
    assert denied.status_code == 404
    home_ok = client.get(
        f"/projects/{project.id}/field-events/{event_id}/originals/{original_id}/display"
    )
    assert home_ok.status_code == 200
