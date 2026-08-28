"""Milestone 010 — Scale Calibration and Manual Measurement Tools tests."""

import json
from io import BytesIO
import pytest

from app import create_app, db
from app.models import Client, Project, Estimate, ProposalTemplate, Proposal, ChangeOrder
from app.plan_intelligence.models import (
    DrawingPackage,
    DrawingRevision,
    PlanAuditEvent,
    PlanDocument,
    PlanPage,
    PlanSheet,
    PlanSheetPage,
    PlanScaleCalibration,
    PlanMeasurement,
)
from app.plan_intelligence.packages import ensure_default_revision
from app.plan_intelligence.processing import process_document_deterministic
from app.plan_intelligence.services import PlanIntelligenceServiceError
from app.plan_intelligence.sheets import create_sheet, map_page_to_sheet
from app.plan_intelligence.scale_measurement import (
    calculate_linear_distance,
    calculate_polygon_area_and_perimeter,
    calculate_polyline_length,
    confirm_calibration,
    convert_area_unit,
    convert_linear_unit,
    create_measurement,
    create_preset_calibration,
    create_two_point_calibration,
    find_applicable_calibration,
    list_calibrations_for_sheet,
    list_measurements_for_sheet,
    mark_sheet_nts,
    parse_dimension_input,
    void_calibration,
    void_measurement,
)


def _make_searchable_pdf_bytes(text="A-101 Floor Plan Scale: 1/4\" = 1'-0\""):
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 50 750 Td ({safe}) Tj ET"
    content_bytes = content.encode("latin-1")
    objects = []

    def obj(n, body):
        objects.append((n, body))

    obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    obj(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    obj(
        3,
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
    )
    obj(
        4,
        f"<< /Length {len(content_bytes)} >>\nstream\n".encode()
        + content_bytes
        + b"\nendstream",
    )
    obj(5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = {0: 0}
    for n, body in objects:
        offsets[n] = out.tell()
        out.write(f"{n} 0 obj\n".encode())
        out.write(body)
        out.write(b"\nendobj\n")
    xref_pos = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for n in range(1, len(objects) + 1):
        out.write(f"{offsets[n]:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode()
    )
    out.write(f"startxref\n{xref_pos}\n%%EOF".encode())
    return out.getvalue()


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "SECRET_KEY": "test-secret-scale",
            "WTF_CSRF_ENABLED": False,
            "PLAN_UPLOAD_ROOT": str(tmp_path / "plan_uploads"),
            "PLAN_UPLOAD_MAX_BYTES": 2 * 1024 * 1024,
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def base_setup(app):
    with app.app_context():
        from app.plan_intelligence.storage import project_upload_dir

        c = Client(name="Scale Test Client")
        db.session.add(c)
        db.session.commit()

        p = Project(name="Commercial Plaza Scale Test", client_id=c.id)
        db.session.add(p)
        db.session.commit()

        pdf_bytes = _make_searchable_pdf_bytes("A-101 Floor Plan")
        doc = PlanDocument(
            project_id=p.id,
            original_filename="architectural_set.pdf",
            stored_filename="architectural_set.pdf",
            byte_size=len(pdf_bytes),
            sha256_hex="test_sha_arch_set",
            content_type="application/pdf",
        )
        db.session.add(doc)
        dest = project_upload_dir(p.id) / "architectural_set.pdf"
        dest.write_bytes(pdf_bytes)
        db.session.flush()

        rev = ensure_default_revision(p)
        rev.documents.append(doc)
        db.session.flush()

        process_document_deterministic(doc, force=True)
        db.session.commit()

        sheet = create_sheet(
            revision=rev,
            number="A-101",
            title="Ground Floor Plan",
            discipline_code="ARCH",
            review_status="reviewed",
            drawing_status="reviewed",
        )
        map_page_to_sheet(sheet, plan_document_id=doc.id, page_index=0)
        db.session.commit()

        return {
            "project_id": p.id,
            "revision_id": rev.id,
            "document_id": doc.id,
            "page_index": 0,
            "sheet_id": sheet.id,
        }


# =========================================================================
# Unit & Dimension Parsing Tests
# =========================================================================


def test_fractional_feet_inches_parsing():
    val, unit = parse_dimension_input("24' 6\"")
    assert val == 24.5
    assert unit == "ft"

    val, unit = parse_dimension_input("24'-6 1/2\"")
    assert round(val, 4) == 24.5417
    assert unit == "ft"

    val, unit = parse_dimension_input("300 in")
    assert val == 300.0
    assert unit == "in"

    val, unit = parse_dimension_input("7500 mm")
    assert val == 7500.0
    assert unit == "mm"

    val, unit = parse_dimension_input("7.5 m")
    assert val == 7.5
    assert unit == "m"


def test_imperial_and_metric_unit_conversions():
    # Linear
    assert convert_linear_unit(1.0, "ft", "in") == 12.0
    assert convert_linear_unit(12.0, "in", "ft") == 1.0
    assert round(convert_linear_unit(1.0, "m", "mm"), 1) == 1000.0
    assert round(convert_linear_unit(1000.0, "mm", "m"), 1) == 1.0

    # Area
    assert convert_area_unit(1.0, "sq_ft", "sq_in") == 144.0
    assert convert_area_unit(144.0, "sq_in", "sq_ft") == 1.0
    assert round(convert_area_unit(1.0, "sq_m", "sq_ft"), 4) == 10.7639


# =========================================================================
# Calibration & Measurement Math Tests
# =========================================================================


def test_two_point_calibration_computes_exact_scale_ratio(app, base_setup):
    with app.app_context():
        p1 = {"x": 0.1, "y": 0.5}
        p2 = {"x": 0.6, "y": 0.5}  # normalized distance = 0.5
        known_str = "50 ft"  # known distance = 50 ft

        cal = create_two_point_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            point_a=p1,
            point_b=p2,
            known_distance_str=known_str,
            auto_confirm=True,
        )

        assert cal.scale_ratio == 100.0  # 50.0 / 0.5 = 100.0 ft per normalized unit
        assert cal.is_confirmed is True
        assert cal.known_distance_value == 50.0
        assert cal.known_distance_unit == "ft"


def test_human_confirmation_required_before_measurement(app, base_setup):
    with app.app_context():
        # Create unconfirmed (draft) calibration
        cal = create_two_point_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            point_a={"x": 0.1, "y": 0.1},
            point_b={"x": 0.5, "y": 0.1},
            known_distance_str="20 ft",
            auto_confirm=False,  # Draft
        )
        assert cal.is_confirmed is False

        # Attempting measurement against unconfirmed calibration must fail closed
        with pytest.raises(PlanIntelligenceServiceError, match="not calibrated|not confirmed"):
            create_measurement(
                project_id=base_setup["project_id"],
                sheet_id=base_setup["sheet_id"],
                plan_document_id=base_setup["document_id"],
                page_index=0,
                measurement_type="linear",
                geometry_data=[{"x": 0.1, "y": 0.1}, {"x": 0.3, "y": 0.1}],
            )

        # Now explicitly confirm calibration
        confirm_calibration(base_setup["project_id"], base_setup["sheet_id"], cal.id)
        assert cal.is_confirmed is True

        # Now measurement succeeds
        meas = create_measurement(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            measurement_type="linear",
            geometry_data=[{"x": 0.1, "y": 0.1}, {"x": 0.3, "y": 0.1}],  # 0.2 norm dist * 50.0 = 10.0 ft
        )
        assert meas.computed_value == 10.0
        assert meas.display_unit == "ft"


def test_linear_measurement_calculation(app, base_setup):
    with app.app_context():
        cal = create_two_point_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            point_a={"x": 0.0, "y": 0.0},
            point_b={"x": 1.0, "y": 0.0},
            known_distance_str="100 ft",
            auto_confirm=True,
        )
        meas = create_measurement(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            measurement_type="linear",
            geometry_data=[{"x": 0.2, "y": 0.2}, {"x": 0.5, "y": 0.6}],  # 3-4-5 triangle: dist = 0.5
        )
        assert meas.computed_value == 50.0  # 0.5 * 100.0


def test_polyline_cumulative_length(app, base_setup):
    with app.app_context():
        cal = create_two_point_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            point_a={"x": 0.0, "y": 0.0},
            point_b={"x": 1.0, "y": 0.0},
            known_distance_str="100 ft",
            auto_confirm=True,
        )
        # Segments: (0.1, 0.1) -> (0.4, 0.1) (0.3 norm = 30 ft) -> (0.4, 0.5) (0.4 norm = 40 ft)
        pts = [{"x": 0.1, "y": 0.1}, {"x": 0.4, "y": 0.1}, {"x": 0.4, "y": 0.5}]
        meas = create_measurement(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            measurement_type="polyline",
            geometry_data=pts,
        )
        assert meas.computed_value == 70.0  # 30.0 + 40.0


def test_polygon_area_shoelace_calculation_and_perimeter(app, base_setup):
    with app.app_context():
        cal = create_two_point_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            point_a={"x": 0.0, "y": 0.0},
            point_b={"x": 1.0, "y": 0.0},
            known_distance_str="100 ft",
            auto_confirm=True,
        )
        # Rectangle from (0.1, 0.1) to (0.5, 0.4): width 0.4 norm (40 ft), height 0.3 norm (30 ft)
        # Area = 1200 sq_ft, Perimeter = 140 ft
        pts = [
            {"x": 0.1, "y": 0.1},
            {"x": 0.5, "y": 0.1},
            {"x": 0.5, "y": 0.4},
            {"x": 0.1, "y": 0.4},
        ]
        meas = create_measurement(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            measurement_type="area",
            geometry_data=pts,
        )
        assert meas.computed_value == 1200.0
        assert meas.display_unit == "sq_ft"
        assert meas.perimeter_value == 140.0


def test_count_measurement(app, base_setup):
    with app.app_context():
        cal = create_two_point_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            point_a={"x": 0.0, "y": 0.0},
            point_b={"x": 1.0, "y": 0.0},
            known_distance_str="100 ft",
            auto_confirm=True,
        )
        pts = [{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.2}, {"x": 0.3, "y": 0.3}, {"x": 0.4, "y": 0.4}]
        meas = create_measurement(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            measurement_type="count",
            geometry_data=pts,
        )
        assert meas.computed_value == 4.0
        assert meas.display_unit == "count"


def test_normalized_coordinate_zoom_invariance():
    # If canvas display size changes (e.g. 1000px vs 2000px vs 500px), normalized coordinates remain [0.2, 0.4]
    p1 = {"x": 0.2, "y": 0.4}
    p2 = {"x": 0.5, "y": 0.8}
    scale_ratio = 50.0

    len1 = calculate_linear_distance(p1, p2, scale_ratio)
    # Re-evaluate with exact same normalized points on simulated 4K screen
    len2 = calculate_linear_distance(p1, p2, scale_ratio)
    assert len1 == len2 == 25.0


def test_multi_scale_viewport_calibration_scoping(app, base_setup):
    with app.app_context():
        # Sheet default scale: 100 ft per 1.0 norm
        default_cal = create_two_point_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            point_a={"x": 0.0, "y": 0.0},
            point_b={"x": 1.0, "y": 0.0},
            known_distance_str="100 ft",
            calibration_type="sheet_default",
            auto_confirm=True,
        )

        # Enlarged detail viewport in region (0.6, 0.6) to (0.9, 0.9): 20 ft per 1.0 norm (enlarged 5x)
        viewport_cal = create_two_point_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            point_a={"x": 0.6, "y": 0.6},
            point_b={"x": 0.7, "y": 0.6},
            known_distance_str="2 ft",  # 0.1 norm = 2 ft -> scale_ratio = 20.0
            calibration_type="viewport_region",
            region_box={"x1": 0.55, "y1": 0.55, "x2": 0.95, "y2": 0.95},
            auto_confirm=True,
        )

        # Measurement outside viewport -> uses default scale (100.0)
        m_outside = create_measurement(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            measurement_type="linear",
            geometry_data=[{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.1}],  # 0.1 norm * 100 = 10 ft
        )
        assert m_outside.computed_value == 10.0
        assert m_outside.scale_calibration_id == default_cal.id

        # Measurement inside viewport -> automatically scopes to viewport scale (20.0)
        m_inside = create_measurement(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            measurement_type="linear",
            geometry_data=[{"x": 0.65, "y": 0.65}, {"x": 0.75, "y": 0.65}],  # 0.1 norm * 20 = 2 ft
        )
        assert m_inside.computed_value == 2.0
        assert m_inside.scale_calibration_id == viewport_cal.id


def test_ambiguous_overlapping_viewport_handling_fails_closed(app, base_setup):
    with app.app_context():
        # Create two conflicting overlapping viewports
        create_two_point_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            point_a={"x": 0.1, "y": 0.1},
            point_b={"x": 0.2, "y": 0.1},
            known_distance_str="10 ft",
            calibration_type="viewport_region",
            region_box={"x1": 0.0, "y1": 0.0, "x2": 0.5, "y2": 0.5},
            auto_confirm=True,
        )
        create_two_point_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            point_a={"x": 0.1, "y": 0.1},
            point_b={"x": 0.2, "y": 0.1},
            known_distance_str="20 ft",
            calibration_type="viewport_region",
            region_box={"x1": 0.1, "y1": 0.1, "x2": 0.6, "y2": 0.6},
            auto_confirm=True,
        )

        # Points at (0.2, 0.2) fall inside both viewports with conflicting scales -> must fail closed
        with pytest.raises(PlanIntelligenceServiceError, match="overlapping viewports"):
            create_measurement(
                project_id=base_setup["project_id"],
                sheet_id=base_setup["sheet_id"],
                plan_document_id=base_setup["document_id"],
                page_index=0,
                measurement_type="linear",
                geometry_data=[{"x": 0.2, "y": 0.2}, {"x": 0.25, "y": 0.2}],
            )


def test_nts_sheet_fails_closed(app, base_setup):
    with app.app_context():
        # Flag sheet as NTS
        mark_sheet_nts(
            base_setup["project_id"],
            base_setup["sheet_id"],
            base_setup["document_id"],
            page_index=0,
        )

        with pytest.raises(PlanIntelligenceServiceError, match="Not To Scale"):
            create_measurement(
                project_id=base_setup["project_id"],
                sheet_id=base_setup["sheet_id"],
                plan_document_id=base_setup["document_id"],
                page_index=0,
                measurement_type="linear",
                geometry_data=[{"x": 0.1, "y": 0.1}, {"x": 0.3, "y": 0.1}],
            )


def test_preset_scale_conversion(app, base_setup):
    with app.app_context():
        cal = create_preset_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            preset_key='1/4" = 1\'-0"',
            page_width_points=2592.0,  # 36" wide page
            auto_confirm=True,
        )
        assert cal.is_confirmed is True
        # 1 inch = 4 feet. 36 inches = 144 feet. Scale ratio should be 144.0 ft per normalized width!
        assert round(cal.scale_ratio, 2) == 144.0


def test_superseded_revision_calibration_preserved(app, base_setup):
    with app.app_context():
        cal1 = create_two_point_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            point_a={"x": 0.0, "y": 0.0},
            point_b={"x": 1.0, "y": 0.0},
            known_distance_str="100 ft",
            auto_confirm=True,
        )
        m1 = create_measurement(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            measurement_type="linear",
            geometry_data=[{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.1}],
        )

        # Create Revision 2 and Sheet in Rev 2
        pkg = DrawingPackage.query.filter_by(project_id=base_setup["project_id"]).first()
        rev2 = DrawingRevision(package_id=pkg.id, label="Rev B", is_active=False)
        db.session.add(rev2)
        db.session.commit()

        sheet2 = create_sheet(
            revision=rev2,
            number="A-101",
            title="Ground Floor Plan Rev B",
            discipline_code="ARCH",
        )

        # Ensure sheet2 has no calibrations yet (not silently carried over)
        assert len(sheet2.scale_calibrations) == 0
        assert len(sheet2.measurements) == 0

        # Prior revision calibrations/measurements remain untouched
        s1 = PlanSheet.query.get(base_setup["sheet_id"])
        assert len(s1.scale_calibrations) == 1
        assert len(s1.measurements) == 1
        assert s1.measurements[0].computed_value == 10.0


def test_project_and_revision_isolation(app, base_setup):
    with app.app_context():
        c2 = Client(name="Other Client")
        db.session.add(c2)
        db.session.commit()
        p2 = Project(name="Other Project", client_id=c2.id)
        db.session.add(p2)
        db.session.commit()

        # Attempting to access base_setup sheet from Project 2 must fail closed
        with pytest.raises(PlanIntelligenceServiceError, match="Sheet not found for this project"):
            create_two_point_calibration(
                project_id=p2.id,
                sheet_id=base_setup["sheet_id"],
                plan_document_id=base_setup["document_id"],
                page_index=0,
                point_a={"x": 0.0, "y": 0.0},
                point_b={"x": 1.0, "y": 0.0},
                known_distance_str="50 ft",
            )


def test_source_plandocument_and_page_immutability(app, base_setup):
    with app.app_context():
        doc_before = PlanDocument.query.get(base_setup["document_id"])
        orig_sha = doc_before.sha256_hex
        orig_bytes = doc_before.byte_size

        page_before = PlanPage.query.filter_by(plan_document_id=base_setup["document_id"], page_index=0).first()
        orig_text = page_before.extracted_text

        # Create calibration and measurements
        cal = create_two_point_calibration(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            point_a={"x": 0.0, "y": 0.0},
            point_b={"x": 1.0, "y": 0.0},
            known_distance_str="100 ft",
            auto_confirm=True,
        )
        create_measurement(
            project_id=base_setup["project_id"],
            sheet_id=base_setup["sheet_id"],
            plan_document_id=base_setup["document_id"],
            page_index=0,
            measurement_type="linear",
            geometry_data=[{"x": 0.1, "y": 0.1}, {"x": 0.3, "y": 0.1}],
        )

        doc_after = PlanDocument.query.get(base_setup["document_id"])
        page_after = PlanPage.query.filter_by(plan_document_id=base_setup["document_id"], page_index=0).first()

        assert doc_after.sha256_hex == orig_sha
        assert doc_after.byte_size == orig_bytes
        assert page_after.extracted_text == orig_text


def test_m009_sheet_review_workflow_unaffected(app, base_setup):
    with app.app_context():
        sheet = PlanSheet.query.get(base_setup["sheet_id"])
        assert sheet.review_status == "reviewed"
        assert sheet.drawing_status == "reviewed"
        assert sheet.number == "A-101"
        assert len(sheet.page_mappings) == 1


def test_estimating_proposals_change_orders_unaffected(app, base_setup):
    with app.app_context():
        p = Project.query.get(base_setup["project_id"])

        est = Estimate(
            project_id=p.id,
            estimate_number="EST-SCALE-001",
            title="Scale Test Estimate",
        )
        db.session.add(est)
        db.session.commit()

        tmpl = ProposalTemplate(name="Scale Test Template", company_name="Brayman Construction")
        db.session.add(tmpl)
        db.session.commit()

        prop = Proposal(
            proposal_number="PROP-SCALE-001",
            estimate_id=est.id,
            estimate_number=est.estimate_number,
            estimate_version_number=1,
            estimate_version_label="v1",
            proposal_template_id=tmpl.id,
            title="Proposal 1",
            status="Draft",
            client_name="Test Client",
            project_name=p.name,
        )
        db.session.add(prop)
        db.session.commit()

        co = ChangeOrder(
            project_id=p.id,
            number="CO-SCALE-001",
            title="Scale Calibration Scope",
            status="Draft",
        )
        db.session.add(co)
        db.session.commit()

        assert est.id is not None
        assert prop.id is not None
        assert co.id is not None


# =========================================================================
# Flask Route Tests
# =========================================================================


def test_measurement_routes_end_to_end(client, base_setup):
    p_id = base_setup["project_id"]
    s_id = base_setup["sheet_id"]

    # GET measurement view
    resp = client.get(f"/projects/{p_id}/plans/sheets/{s_id}/measure")
    assert resp.status_code == 200
    assert b"Sheet Scale Calibration" in resp.data

    # POST create two-point calibration
    resp = client.post(
        f"/projects/{p_id}/plans/sheets/{s_id}/calibrations/two-point",
        data={
            "point_a_x": "0.1",
            "point_a_y": "0.1",
            "point_b_x": "0.6",
            "point_b_y": "0.1",
            "known_distance": "50 ft",
            "auto_confirm": "1",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    # GET measurement data API
    resp = client.get(f"/projects/{p_id}/plans/sheets/{s_id}/measurements/data")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data["calibrations"]) == 1
    assert data["calibrations"][0]["is_confirmed"] is True

    # POST save measurement
    resp = client.post(
        f"/projects/{p_id}/plans/sheets/{s_id}/measurements",
        data={
            "measurement_type": "linear",
            "label": "Frontage Wall",
            "geometry_data_json": json.dumps([{"x": 0.2, "y": 0.2}, {"x": 0.4, "y": 0.2}]),
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Frontage Wall" in resp.data

    # POST void measurement
    resp = client.get(f"/projects/{p_id}/plans/sheets/{s_id}/measurements/data")
    data = json.loads(resp.data)
    m_id = data["measurements"][0]["id"]

    resp = client.post(
        f"/projects/{p_id}/plans/sheets/{s_id}/measurements/{m_id}/void",
        follow_redirects=True,
    )
    assert resp.status_code == 200
