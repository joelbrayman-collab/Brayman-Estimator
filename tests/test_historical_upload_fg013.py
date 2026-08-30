"""Dedicated tests for FG-013 historical estimate upload UX."""

from __future__ import annotations

import hashlib
import io
import os
import zipfile
from pathlib import Path

import pytest

from app import create_app, db
from app.models.historical_estimates import (
    HistoricalEstimate,
    HistoricalSourceWorkbook,
    HistoricalUploadAttempt,
)
from app.models.labour_engine import LabourCalibrationCandidate
from app.models.organization import Organization
from app.models.pricing_engine import OrganizationPricingPolicy
from app.services.historical_ingestion.adapters.family_e import is_known_family_e_filename
from app.services.historical_ingestion.upload import process_one_workbook, process_upload_files
from app.services.historical_review import (
    get_historical_estimate_or_404,
    record_review_decision,
)

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _sheet_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{NS_MAIN}">'
        "<sheetData>"
        '<row r="1"><c r="A1" t="inlineStr"><is><t>sample</t></is></c></row>'
        "</sheetData>"
        "</worksheet>"
    )


def make_openxml_bytes(sheet_names, hidden=None, extra_members=None):
    """Build a minimal valid OpenXML workbook (no macros, no formula execution)."""
    hidden = set(hidden or [])
    extra_members = extra_members or {}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""",
        )
        zf.writestr(
            "_rels/.rels",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{NS_REL}">
<Relationship Id="rId1" Type="{NS_OFFICE_REL}/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        )
        sheet_tags = []
        rel_tags = []
        for idx, name in enumerate(sheet_names, 1):
            state_attr = ' state="hidden"' if name in hidden else ""
            rid = f"rId{idx}"
            sheet_tags.append(
                f'<sheet name="{name}" sheetId="{idx}" r:id="{rid}"{state_attr}/>'
            )
            rel_tags.append(
                f'<Relationship Id="{rid}" Type="{NS_OFFICE_REL}/worksheet" '
                f'Target="worksheets/sheet{idx}.xml"/>'
            )
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", _sheet_xml())
        zf.writestr(
            "xl/workbook.xml",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="{NS_MAIN}" xmlns:r="{NS_OFFICE_REL}">
<sheets>{''.join(sheet_tags)}</sheets>
</workbook>""",
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{NS_REL}">
{''.join(rel_tags)}
</Relationships>""",
        )
        for name, payload in extra_members.items():
            zf.writestr(name, payload)
    return buf.getvalue()


def family_a_bytes():
    return make_openxml_bytes(["House TES"])


def family_e_generic_bytes():
    return make_openxml_bytes(["Sheet1"])


def family_e_known_bytes():
    return make_openxml_bytes(["Sheet1"])


def low_confidence_bytes():
    return make_openxml_bytes(
        ["Alpha", "Beta", "Gamma", "HiddenSheet"],
        hidden=["HiddenSheet"],
    )


LEGACY_DIR = os.path.expanduser("~/Desktop/CalibAi Historical Estimates")


def _legacy_fingerprint():
    if not os.path.isdir(LEGACY_DIR):
        return None
    rows = []
    for name in sorted(os.listdir(LEGACY_DIR)):
        path = os.path.join(LEGACY_DIR, name)
        if not os.path.isfile(path):
            continue
        st = os.stat(path)
        with open(path, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        rows.append((name, st.st_mtime, st.st_size, digest))
    return rows


@pytest.fixture
def upload_root(tmp_path):
    return tmp_path / "historical_uploads"


@pytest.fixture
def app(upload_root):
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "HISTORICAL_UPLOAD_ROOT": str(upload_root),
            "HISTORICAL_UPLOAD_MAX_BYTES": 25 * 1024 * 1024,
        }
    )
    with app.app_context():
        db.create_all()
        db.session.add(
            Organization(
                id="ORG-001",
                legal_name="Brayman Construction Inc.",
                display_name="Brayman Construction",
                currency="CAD",
                tax_jurisdiction="Ontario (HST 13%)",
            )
        )
        db.session.add(
            Organization(
                id="ORG-002",
                legal_name="Second Builder Ltd.",
                display_name="Second Builder",
                currency="CAD",
                tax_jurisdiction="Ontario (HST 13%)",
            )
        )
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def legacy_lock():
    before = _legacy_fingerprint()
    yield before
    after = _legacy_fingerprint()
    assert before == after


def test_known_family_e_filename_markers():
    assert is_known_family_e_filename("Copy of Julia Harish RENO.xlsx")
    assert is_known_family_e_filename("Brown Floor Replacement copy.xlsx")
    assert not is_known_family_e_filename("random_contractor_quote.xlsx")


def test_multi_file_upload_one_request(client, app, legacy_lock):
    a = family_a_bytes()
    b = family_a_bytes()
    # Distinct bytes so both ingest: tweak second sheet extra member
    b = make_openxml_bytes(["House TES"], extra_members={"xl/custom.xml": b"<ok>1</ok>"})
    from werkzeug.datastructures import FileStorage, MultiDict

    payload = MultiDict()
    payload.add(
        "workbooks",
        FileStorage(stream=io.BytesIO(a), filename="job_one.xlsx"),
    )
    payload.add(
        "workbooks",
        FileStorage(stream=io.BytesIO(b), filename="job_two.xlsx"),
    )
    res = client.post(
        "/historical-estimates/upload",
        data=payload,
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    assert b"FILES RECEIVED" in res.data
    assert b"HISTORICAL EVIDENCE LOADED" in res.data
    assert b"COST MODEL COMPLETE" not in res.data
    with app.app_context():
        assert HistoricalSourceWorkbook.query.count() == 2
        assert HistoricalUploadAttempt.query.count() == 2
        assert HistoricalEstimate.query.count() == 2


def test_valid_xlsx_ingests(app, legacy_lock):
    result = process_one_workbook(
        data=family_a_bytes(),
        raw_filename="recognized_slab.xlsx",
        organization_id="ORG-001",
    )
    assert result.outcome == "INGESTED"
    sw = HistoricalSourceWorkbook.query.get(result.source_workbook_id)
    assert sw.template_family == "FAMILY_A"
    assert sw.ingestion_status == "INGESTED"


def test_valid_xlsm_ingests_without_macro_execution(app, legacy_lock):
    payload = family_a_bytes()
    result = process_one_workbook(
        data=payload,
        raw_filename="recognized_slab.xlsm",
        organization_id="ORG-001",
    )
    assert result.outcome == "INGESTED"
    sw = HistoricalSourceWorkbook.query.get(result.source_workbook_id)
    assert sw.extension == ".xlsm"


def test_one_failed_file_does_not_rollback_successes(app, legacy_lock):
    good_a = family_a_bytes()
    good_b = make_openxml_bytes(
        ["House TES"], extra_members={"xl/note.xml": b"<n>2</n>"}
    )
    class FakeFile:
        def __init__(self, name, data):
            self.filename = name
            self._data = data

        def read(self):
            return self._data

    summary = process_upload_files(
        [
            FakeFile("ok_one.xlsx", good_a),
            FakeFile("nope.csv", b"a,b,c\n1,2,3\n"),
            FakeFile("ok_two.xlsx", good_b),
        ],
        organization_id="ORG-001",
    )
    assert summary.files_received == 3
    assert summary.ingested_count == 2
    assert summary.unsupported_count == 1
    assert HistoricalSourceWorkbook.query.count() == 2
    assert HistoricalUploadAttempt.query.count() == 3


def test_duplicate_same_org_sha_idempotent(app, legacy_lock):
    data = family_a_bytes()
    first = process_one_workbook(
        data=data, raw_filename="slab.xlsx", organization_id="ORG-001"
    )
    second = process_one_workbook(
        data=data, raw_filename="slab_renamed.xlsx", organization_id="ORG-001"
    )
    assert first.outcome == "INGESTED"
    assert second.outcome == "DUPLICATE"
    assert first.source_workbook_id == second.source_workbook_id
    assert HistoricalSourceWorkbook.query.count() == 1
    assert HistoricalEstimate.query.count() == 1
    assert HistoricalUploadAttempt.query.filter_by(outcome="DUPLICATE").count() == 1


def test_same_bytes_different_org_are_separate(app, legacy_lock):
    data = family_a_bytes()
    r1 = process_one_workbook(
        data=data, raw_filename="slab.xlsx", organization_id="ORG-001"
    )
    r2 = process_one_workbook(
        data=data, raw_filename="slab.xlsx", organization_id="ORG-002"
    )
    assert r1.outcome == "INGESTED"
    assert r2.outcome == "INGESTED"
    assert r1.source_workbook_id != r2.source_workbook_id
    assert HistoricalSourceWorkbook.query.filter_by(organization_id="ORG-001").count() == 1
    assert HistoricalSourceWorkbook.query.filter_by(organization_id="ORG-002").count() == 1


def test_unsupported_extension_rejected(app, legacy_lock):
    result = process_one_workbook(
        data=b"not-excel",
        raw_filename="legacy.xls",
        organization_id="ORG-001",
    )
    assert result.outcome == "UNSUPPORTED"
    assert HistoricalSourceWorkbook.query.count() == 0
    attempt = HistoricalUploadAttempt.query.one()
    assert attempt.outcome == "UNSUPPORTED"


def test_malformed_openxml_fails_safely(app, legacy_lock):
    result = process_one_workbook(
        data=b"PK\x03\x04this-is-not-a-zip",
        raw_filename="broken.xlsx",
        organization_id="ORG-001",
    )
    assert result.outcome == "FAILED"
    assert HistoricalSourceWorkbook.query.count() == 0


def test_missing_workbook_xml_fails_safely(app, legacy_lock):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("hello.txt", "no workbook")
    result = process_one_workbook(
        data=buf.getvalue(),
        raw_filename="incomplete.xlsx",
        organization_id="ORG-001",
    )
    assert result.outcome == "FAILED"
    assert "workbook.xml" in result.message


def test_oversize_file_fails_according_to_config(app, legacy_lock):
    app.config["HISTORICAL_UPLOAD_MAX_BYTES"] = 64
    result = process_one_workbook(
        data=b"PK\x03\x04" + b"x" * 200,
        raw_filename="huge.xlsx",
        organization_id="ORG-001",
    )
    assert result.outcome == "FAILED"
    assert "maximum" in result.message.lower()


def test_zip_safety_limit_enforced(app, legacy_lock):
    app.config["HISTORICAL_UPLOAD_ZIP_MAX_UNCOMPRESSED"] = 80
    payload = family_a_bytes()
    result = process_one_workbook(
        data=payload,
        raw_filename="bomb.xlsx",
        organization_id="ORG-001",
    )
    assert result.outcome == "FAILED"
    assert "uncompressed" in result.message.lower()


def test_safe_filename_path_handling(app, upload_root, legacy_lock):
    data = family_a_bytes()
    result = process_one_workbook(
        data=data,
        raw_filename="../../secret.xlsx",
        organization_id="ORG-001",
    )
    assert result.outcome == "INGESTED"
    attempt = HistoricalUploadAttempt.query.get(result.attempt_id)
    assert attempt.original_filename == "secret.xlsx"
    assert ".." not in (attempt.stored_relative_path or "")
    stored = Path(attempt.stored_relative_path)
    assert stored.parts[0] == "ORG-001"
    abs_path = upload_root / attempt.stored_relative_path
    assert abs_path.is_file()
    assert abs_path.parent == upload_root / "ORG-001"


def test_productized_bytes_in_private_storage_not_git(app, upload_root, legacy_lock):
    result = process_one_workbook(
        data=family_a_bytes(),
        raw_filename="stored.xlsx",
        organization_id="ORG-001",
    )
    attempt = HistoricalUploadAttempt.query.get(result.attempt_id)
    abs_path = (upload_root / attempt.stored_relative_path).resolve()
    assert str(upload_root.resolve()) in str(abs_path)
    git_root = Path(__file__).resolve().parents[1]
    assert git_root not in abs_path.parents or "instance" in str(abs_path) or str(upload_root) in str(abs_path)
    # Must not live in the git-tracked tree under app/ or tests/
    assert "app/" not in str(abs_path)
    repo_files = {p.name for p in git_root.glob("*.xlsx")}
    assert abs_path.name not in repo_files


def test_duplicate_does_not_overwrite_stored_bytes(app, upload_root, legacy_lock):
    data = family_a_bytes()
    first = process_one_workbook(
        data=data, raw_filename="stored.xlsx", organization_id="ORG-001"
    )
    path = upload_root / HistoricalUploadAttempt.query.get(first.attempt_id).stored_relative_path
    before = path.read_bytes()
    mtime = path.stat().st_mtime
    second = process_one_workbook(
        data=data, raw_filename="stored-again.xlsx", organization_id="ORG-001"
    )
    assert second.outcome == "DUPLICATE"
    assert path.read_bytes() == before
    assert path.stat().st_mtime == mtime


def test_unknown_layout_quarantined(app, legacy_lock):
    result = process_one_workbook(
        data=family_e_generic_bytes(),
        raw_filename="random_contractor_quote.xlsx",
        organization_id="ORG-001",
    )
    assert result.outcome == "QUARANTINED"
    est = HistoricalEstimate.query.get(result.estimate_id)
    assert est.review_status == "REVIEW_REQUIRED"
    assert est.extraction_confidence == 0.0
    sw = HistoricalSourceWorkbook.query.get(result.source_workbook_id)
    assert sw.ingestion_status == "QUARANTINED"


def test_low_confidence_classifier_fallback_quarantined(app, legacy_lock):
    result = process_one_workbook(
        data=low_confidence_bytes(),
        raw_filename="mystery_pack.xlsx",
        organization_id="ORG-001",
    )
    assert result.outcome == "QUARANTINED"


def test_known_family_e_still_ingests(app, legacy_lock):
    result = process_one_workbook(
        data=family_e_known_bytes(),
        raw_filename="Copy of Julia Harish RENO.xlsx",
        organization_id="ORG-001",
    )
    assert result.outcome == "INGESTED"
    sw = HistoricalSourceWorkbook.query.get(result.source_workbook_id)
    assert sw.template_family == "FAMILY_E"
    assert sw.ingestion_status == "INGESTED"


def test_generic_family_e_does_not_masquerade_as_confident_parse(app, legacy_lock):
    result = process_one_workbook(
        data=family_e_generic_bytes(),
        raw_filename="adhoc_unknown.xlsx",
        organization_id="ORG-001",
    )
    assert result.outcome == "QUARANTINED"
    est = HistoricalEstimate.query.get(result.estimate_id)
    assert est.extraction_confidence < 1.0
    assert est.client_name != "Generic Ad-Hoc Estimate"


def test_durable_attempt_written(app, legacy_lock):
    process_one_workbook(
        data=family_a_bytes(), raw_filename="slab.xlsx", organization_id="ORG-001"
    )
    attempt = HistoricalUploadAttempt.query.one()
    assert attempt.organization_id == "ORG-001"
    assert attempt.sha256
    assert attempt.actor == "Joel Brayman"
    assert attempt.outcome == "INGESTED"
    assert attempt.archive_status == "ACTIVE"


def test_no_durable_upload_batch(app, legacy_lock):
    import app.models as models_mod

    assert not hasattr(models_mod, "UploadBatch")
    from sqlalchemy import inspect as sa_inspect

    names = sa_inspect(db.engine).get_table_names()
    assert "upload_batches" not in names
    assert "historical_upload_attempts" in names


def test_cross_org_access_fails_closed(app, legacy_lock):
    result = process_one_workbook(
        data=family_a_bytes(), raw_filename="slab.xlsx", organization_id="ORG-001"
    )
    with pytest.raises(Exception):
        get_historical_estimate_or_404(
            result.estimate_id, organization_id="ORG-002"
        )


def test_review_lifecycle_and_accepted_as_evidence_does_not_create_standards(
    app, client, legacy_lock
):
    result = process_one_workbook(
        data=family_a_bytes(), raw_filename="slab.xlsx", organization_id="ORG-001"
    )
    record_review_decision(
        estimate_id=result.estimate_id,
        review_status="ACCEPTED_AS_EVIDENCE",
        evidence_tier="TIER_A",
        reviewed_by="Joel Brayman",
        organization_id="ORG-001",
    )
    assert LabourCalibrationCandidate.query.count() == 0
    assert OrganizationPricingPolicy.query.count() == 0
    page = client.get(f"/historical-estimates/{result.estimate_id}")
    assert page.status_code == 200
    assert b"ACCEPTED AS EVIDENCE" in page.data
    assert b"Estimate associated with a completed project" in page.data
    assert b"Actual completed job" not in page.data


def test_upload_does_not_mutate_pricing_or_create_candidates(app, legacy_lock):
    process_one_workbook(
        data=family_a_bytes(), raw_filename="slab.xlsx", organization_id="ORG-001"
    )
    process_one_workbook(
        data=family_e_generic_bytes(),
        raw_filename="unknown.xlsx",
        organization_id="ORG-001",
    )
    assert LabourCalibrationCandidate.query.count() == 0
    assert OrganizationPricingPolicy.query.count() == 0


def test_index_has_multi_file_controls_and_no_cost_model_claim(client, legacy_lock):
    page = client.get("/historical-estimates/")
    assert page.status_code == 200
    assert b"UPLOAD PREVIOUS ESTIMATES" in page.data
    assert b'multiple' in page.data
    assert b"webkitdirectory" in page.data
    assert b"COST MODEL COMPLETE" not in page.data
    assert b"Compare Against Industry" not in page.data


def test_zip_path_traversal_member_rejected(app, legacy_lock):
    payload = make_openxml_bytes(
        ["House TES"], extra_members={"foo/../../escape.txt": b"nope"}
    )
    result = process_one_workbook(
        data=payload, raw_filename="traverse.xlsx", organization_id="ORG-001"
    )
    assert result.outcome == "FAILED"


def test_content_type_not_required(app, legacy_lock):
    class TypedFile:
        filename = "slab.xlsx"
        content_type = "application/octet-stream"

        def __init__(self, data):
            self._data = data

        def read(self):
            return self._data

    summary = process_upload_files(
        [TypedFile(family_a_bytes())], organization_id="ORG-001"
    )
    assert summary.ingested_count == 1
