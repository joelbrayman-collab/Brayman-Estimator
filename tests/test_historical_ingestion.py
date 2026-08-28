"""Comprehensive Test Suite for Historical Estimate Ingestion Engine Phase B (FG-006)."""

from decimal import Decimal
import hashlib
import os
import pytest

from app import create_app, db
from app.models.historical_estimates import (
    HistoricalCostLineItem,
    HistoricalDataQualityFlag,
    HistoricalEstimate,
    HistoricalEstimateReviewDecision,
    HistoricalLabourItem,
    HistoricalSourceObservation,
    HistoricalSourceWorkbook,
    HistoricalSubcontractItem,
)
from app.models.organization import Organization
from app.services.historical_ingestion import (
    FAMILY_A,
    FAMILY_B,
    FAMILY_C,
    FAMILY_D,
    FAMILY_E,
    classify_template_family,
    ingest_workbook_file,
    read_openxml_workbook,
)
from app.services.historical_review import (
    HistoricalReviewError,
    get_historical_estimate_or_404,
    list_historical_estimates,
    list_historical_workbooks,
    record_review_decision,
)


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        # Seed default organization
        org = Organization(
            id="ORG-001",
            legal_name="Brayman Construction Inc.",
            display_name="Brayman Construction",
            currency="CAD",
            tax_jurisdiction="Ontario (HST 13%)",
        )
        db.session.add(org)
        # Seed second organization for tenant isolation tests
        org2 = Organization(
            id="ORG-002",
            legal_name="Second Builder Ltd.",
            display_name="Second Builder",
            currency="CAD",
            tax_jurisdiction="Ontario (HST 13%)",
        )
        db.session.add(org2)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def source_dir():
    path = os.path.expanduser("~/Desktop/CalibAi Historical Estimates")
    if not os.path.exists(path):
        pytest.skip(f"Historical source directory not found at {path}")
    return path


def test_source_manifest_hashes_20_of_20_exact(source_dir):
    """Verify that all 20 historical source workbooks match their governed SHA-256 hashes."""
    expected_manifest = {
        "Alberton Garage Cost copy.xlsx": "1b302fc6cea78c56d50653744ab42a274181d7deb893d261c90a36ff8be8d88a",
        "Allen Jacques - TES copy.xlsm": "e20bf7aa7288d4f126636599bb558918220ed3dfdb036db26966dfa95ecfd38a",
        "Bob Milne copy.xlsm": "56f336e6ef732c04b6f638e4cc72c0621dfa133fba7f2c0aa14261cc2a758914",
        "Bradley Construction SLAB V2 copy.xlsm": "b3c8cb3bec4f002af54aa0d2a427e18029d1dd71956a76c3622f56ecb046ecf9",
        "Brian Alberton SLAB copy.xlsm": "8dfcf951dfc921d3268a450b5175b5caeb9963f4f5286077fd3ea538635ff596",
        "Brown Floor Replacement copy.xlsx": "2b70d312d795031e2bff5c60044adb2d8ba73825d613ef6fd07f199941200f50",
        "Chris Graham ICF Ottawa copy.xlsm": "76c24f50f198fd170f1313259c16b7278429052606bffd16665e4e342e4d3117",
        "Copy of Julia Harish RENO.xlsx": "04f25af45d12b8cbd43d1a6a6f6c677db3d024afe89d96804138270329fa4ebd",
        "GATE Pads KINGSTON copy.xlsm": "784206aac0ab759924045d666e7acde068c73820c6b389bcca20ad6f249f5616",
        "Gerry Cardinal copy.xlsm": "7a9316b26dff55f8bffb6af8a63d9666ecc5f82f1fd7f12d289f3db353e97cb9",
        "Jacob Brown copy.xlsm": "7b14e38d5ab5186696350719c8443a12363ff7ccf106752a6ff06c3cf3ee8cbb",
        "Lamb Thickened Edge Slab - House copy.xlsm": "bfbf1f200b48d1eed650660ed95fa080294dc82079bce91a3a1716962c497d4e",
        "Michelle Steele Manotick ICF V2 copy.xlsm": "0c474de61add228430331ed233e2b3a977f7e9ec5bf18aea19a853bc036b93e3",
        "Mike Pratt FULL ICF 2 V2 copy 2.xlsm": "48a40944465a89df67155def285a6fcadc1ba978fdff0c2b69c8a9ee111e7e07",
        "NG Slab Repair copy.xlsm": "6b6ab69a597ea9fcbf4b79d34b896bfdf15ddeaf441c3b66c61013fbb64688cf",
        "Patrick Pearce SLABS copy.xlsm": "126416ba38e3f379daed2866f3c12941b60235c40d00620d7e51266686297504",
        "Richard Gorman 2 copy.xlsm": "dede4c1050ae79a32a3da44fdfb572e17f5f01512a76a5264c0fee0a4cc3a2ee",
        "Ryan Dunwoodie SLAB-ON-GRADE V3 copy.xlsm": "461ad5f4e6c5e4f7a42f5fb587b51cf7411646b4ed9a1c83108be62384c26910",
        "Sasha - ICF  copy.xlsm": "697a98710a675d0d9d0de15d834d4af6dd2a48391b037b1b4a69cd4e1f535e8f",
        "Serge  copy.xlsx": "48d28ae88711e60e76bc42ed3246aca88ac387c0432ce136dbb0f63fc6dbf955",
    }

    files = sorted(os.listdir(source_dir))
    actual_workbooks = [f for f in files if f.endswith(".xlsx") or f.endswith(".xlsm")]
    assert len(actual_workbooks) == 20

    for fname in actual_workbooks:
        fpath = os.path.join(source_dir, fname)
        with open(fpath, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        assert fname in expected_manifest, f"Unexpected workbook: {fname}"
        assert h == expected_manifest[fname], f"Hash mismatch on {fname}: expected {expected_manifest[fname]}, got {h}"


def test_template_classifier_counts(source_dir):
    """Verify that the template classifier categorizes all 20 workbooks into exact family counts."""
    counts = {FAMILY_A: 0, FAMILY_B: 0, FAMILY_C: 0, FAMILY_D: 0, FAMILY_E: 0}
    files = sorted(os.listdir(source_dir))
    workbooks = [f for f in files if f.endswith(".xlsx") or f.endswith(".xlsm")]

    for fname in workbooks:
        wb = read_openxml_workbook(os.path.join(source_dir, fname))
        fam, conf, _ = classify_template_family(wb)
        assert conf > 0.0
        counts[fam] += 1

    assert counts[FAMILY_A] == 9, f"Expected 9 Family A, got {counts[FAMILY_A]}"
    assert counts[FAMILY_B] == 5, f"Expected 5 Family B, got {counts[FAMILY_B]}"
    assert counts[FAMILY_C] == 1, f"Expected 1 Family C, got {counts[FAMILY_C]}"
    assert counts[FAMILY_D] == 1, f"Expected 1 Family D, got {counts[FAMILY_D]}"
    assert counts[FAMILY_E] == 4, f"Expected 4 Family E, got {counts[FAMILY_E]}"


def test_allen_jacques_family_a_regression_anchor(app, source_dir):
    """Verify deterministic extraction of Allen Jacques pilot anchor."""
    fpath = os.path.join(source_dir, "Allen Jacques - TES copy.xlsm")
    sw = ingest_workbook_file(fpath, organization_id="ORG-001", source_id="HIST-EST-TEST-01")

    assert sw.template_family == FAMILY_A
    assert len(sw.estimates) == 1
    est = sw.estimates[0]

    assert est.client_name == "Allen Jacques"
    assert est.pricing_method == "COST_PLUS_MARKUP"
    assert est.margin_percent == Decimal("0.1500")

    # Pilot values
    assert est.direct_cost_total == Decimal("30976.00")
    assert est.markup_total == Decimal("4646.40")
    assert est.selling_price_before_tax == Decimal("35622.40")
    assert est.tax_amount == Decimal("4630.91")
    assert est.total_price == Decimal("40253.31")

    # Labour items and materials extracted
    assert len(est.labour_items) >= 2
    assert len(est.cost_items) >= 5
    assert len(sw.observations) >= 5


def test_mike_pratt_family_d_regression_anchor(app, source_dir):
    """Verify deterministic extraction of Mike Pratt comprehensive build pilot anchor.
    
    Commercial Structure:
    - SUMMARY!C10:C34 (Direct Scope Line Items) = $534,436.10
    - SUMMARY!C35 (GC Work 12.5% on subs) = $60,492.01 -> markup_total
    - SUMMARY!C36 (Change Order / Contingency 5% with note 'Balance split at close') = $25,896.80 -> contingency_total
    - SUMMARY!C37 (Selling Price Before Tax) = $620,824.91 (C10:C34 + C35 + C36)
    - HST 13% = $80,707.24
    - Grand Total = $701,532.15
    """
    fpath = os.path.join(source_dir, "Mike Pratt FULL ICF 2 V2 copy 2.xlsm")
    sw = ingest_workbook_file(fpath, organization_id="ORG-001", source_id="HIST-EST-TEST-02")

    assert sw.template_family == FAMILY_D
    assert len(sw.estimates) == 1
    est = sw.estimates[0]

    assert est.client_name == "Mike Pratt"
    assert est.pricing_method == "TIERED_MARKUP"
    assert est.evidence_tier == "TIER_B"

    # Exact deterministic commercial values asserting contingency is separate from markup
    assert est.direct_cost_total == Decimal("534436.10")
    assert est.markup_total == Decimal("60492.01")
    assert est.contingency_total == Decimal("25896.80")
    assert est.selling_price_before_tax == Decimal("620824.91")
    assert est.tax_amount == Decimal("80707.24")
    assert est.total_price == Decimal("701532.15")

    # Verify underlying cost items, subcontracts, and source observations
    assert len(est.cost_items) >= 15
    assert len(est.subcontract_items) >= 5
    assert len(sw.observations) >= 3

    # Verify explicit cell provenance observations:
    # C35 maps to markup_total (GC Work)
    # C36 maps to contingency_total (Change Order / Contingency) - NOT markup_total
    # C37 maps to selling_price_before_tax (SUM(C10:C36))
    obs_coords = {obs.cell_coordinate: obs for obs in sw.observations if obs.sheet_name == "SUMMARY"}
    assert "C35" in obs_coords
    assert obs_coords["C35"].normalized_field == "markup_total"
    assert obs_coords["C35"].raw_formula == "SUM(C9:C32)*B35"
    assert obs_coords["C35"].extraction_rule_id == "rule_build_gc_margin"

    assert "C36" in obs_coords
    assert obs_coords["C36"].normalized_field == "contingency_total"
    assert obs_coords["C36"].raw_formula == "SUM(C10:C33)*B36"
    assert obs_coords["C36"].extraction_rule_id == "rule_build_contingency"
    assert obs_coords["C36"].normalized_field != "markup_total", "C36 MUST NOT be mapped to markup_total"

    assert "C37" in obs_coords
    assert obs_coords["C37"].normalized_field == "selling_price_before_tax"
    assert obs_coords["C37"].raw_formula == "SUM(C10:C36)"
    assert obs_coords["C37"].extraction_rule_id == "rule_build_sell_price"


def test_julia_harish_family_e_contingency_rollup(app, source_dir):
    """Verify Julia Harish extraction where contingency is retained as an internal reserve."""
    fpath = os.path.join(source_dir, "Copy of Julia Harish RENO.xlsx")
    sw = ingest_workbook_file(fpath, organization_id="ORG-001", source_id="HIST-EST-JH-01")

    assert sw.template_family == FAMILY_E
    assert len(sw.estimates) == 1
    est = sw.estimates[0]

    assert est.client_name == "Julia Harish"
    assert est.direct_cost_total == Decimal("85152.40")
    assert est.markup_total == Decimal("12772.86")
    assert est.contingency_total == Decimal("4257.62")
    
    # Selling price before tax reflects Direct (C58) + Margin (C59) = $97,925.26
    # Contingency (C60: $4,257.62) is preserved as an internal reserve and does not participate in selling price
    assert est.selling_price_before_tax == Decimal("97925.26")
    assert est.tax_amount == Decimal("12730.28")
    assert est.total_price == Decimal("110655.54")

    # Verify provenance and formula lineage
    obs_coords = {obs.cell_coordinate: obs for obs in sw.observations if obs.sheet_name == "Sheet1"}
    assert "C58" in obs_coords
    assert obs_coords["C58"].normalized_field == "direct_cost_total"
    assert obs_coords["C58"].raw_formula == "SUM(C9:C57)"

    assert "C59" in obs_coords
    assert obs_coords["C59"].normalized_field == "markup_total"
    assert obs_coords["C59"].raw_formula == "C58*D4"

    assert "C60" in obs_coords
    assert obs_coords["C60"].normalized_field == "contingency_total"
    assert obs_coords["C60"].raw_formula == "C58*D60"
    assert obs_coords["C60"].extraction_rule_id == "rule_julia_contingency_internal_reserve"

    # Quality flag for C61:C63 formula error
    flags = [qf for qf in sw.quality_flags if qf.flag_type == "FORMULA_ERROR"]
    assert len(flags) >= 1
    assert "CONTINGENCY_NOT_INCLUDED_IN_SELL_PRICE" in flags[0].description


def test_idempotent_reingestion(app, source_dir):
    """Verify that re-ingesting the exact same file does not create duplicate database records."""
    fpath = os.path.join(source_dir, "Bob Milne copy.xlsm")
    sw1 = ingest_workbook_file(fpath, organization_id="ORG-001", source_id="HIST-EST-BM-1")
    count_sw_1 = HistoricalSourceWorkbook.query.count()
    count_est_1 = HistoricalEstimate.query.count()

    sw2 = ingest_workbook_file(fpath, organization_id="ORG-001", source_id="HIST-EST-BM-1")
    count_sw_2 = HistoricalSourceWorkbook.query.count()
    count_est_2 = HistoricalEstimate.query.count()

    assert sw1.id == sw2.id
    assert count_sw_1 == count_sw_2
    assert count_est_1 == count_est_2


def test_cross_tenant_isolation(app, source_dir):
    """Verify that historical records belonging to ORG-001 cannot be accessed or listed by ORG-002."""
    fpath = os.path.join(source_dir, "Gerry Cardinal copy.xlsm")
    sw = ingest_workbook_file(fpath, organization_id="ORG-001")
    est = sw.estimates[0]

    # Query for ORG-001
    list_org1 = list_historical_estimates("ORG-001")
    assert any(e.id == est.id for e in list_org1)

    # Query for ORG-002: must be empty
    list_org2 = list_historical_estimates("ORG-002")
    assert not any(e.id == est.id for e in list_org2)

    # get_or_404 for ORG-002 must fail closed
    with pytest.raises(HistoricalReviewError):
        get_historical_estimate_or_404(est.id, organization_id="ORG-002")


def test_review_decision_workflow(app, source_dir):
    """Verify that estimators can record review decisions with status and tier updates."""
    fpath = os.path.join(source_dir, "Brian Alberton SLAB copy.xlsm")
    sw = ingest_workbook_file(fpath, organization_id="ORG-001")
    est = sw.estimates[0]

    assert est.review_status == "EXTRACTED"
    assert est.evidence_tier == "TIER_C"

    dec = record_review_decision(
        estimate_id=est.id,
        review_status="ACCEPTED_AS_EVIDENCE",
        evidence_tier="TIER_B",
        reviewed_by="Joel Brayman",
        review_notes="Verified against completed job slab contract.",
        organization_id="ORG-001",
    )

    assert dec.id is not None
    assert dec.review_status == "ACCEPTED_AS_EVIDENCE"
    assert dec.evidence_tier == "TIER_B"
    assert dec.reviewed_by == "Joel Brayman"

    # Reload estimate
    updated_est = get_historical_estimate_or_404(est.id, organization_id="ORG-001")
    assert updated_est.review_status == "ACCEPTED_AS_EVIDENCE"
    assert updated_est.evidence_tier == "TIER_B"


def test_ui_historical_routes(client, source_dir):
    """Verify historical evidence UI endpoints return 200 and display data correctly."""
    fpath = os.path.join(source_dir, "Alberton Garage Cost copy.xlsx")
    sw = ingest_workbook_file(fpath, organization_id="ORG-001")
    est = sw.estimates[0]

    # List page
    res_list = client.get("/historical-estimates/")
    assert res_list.status_code == 200
    assert b"Historical Source Workbooks & Estimates" in res_list.data
    assert b"Alberton Garage" in res_list.data

    # Detail page
    res_detail = client.get(f"/historical-estimates/{est.id}")
    assert res_detail.status_code == 200
    assert b"Alberton Garage" in res_detail.data
    assert b"Source-Cell Provenance Observations" in res_detail.data

    # Review POST
    res_post = client.post(
        f"/historical-estimates/{est.id}/review",
        data={
            "review_status": "REVIEWED",
            "evidence_tier": "TIER_D",
            "reviewed_by": "Joel Brayman",
            "review_notes": "Ad-hoc garage cost sheet verified.",
        },
        follow_redirects=True,
    )
    assert res_post.status_code == 200
    assert b"Historical evidence review decision saved successfully." in res_post.data


def test_no_macro_execution_pure_xml(source_dir):
    """Verify that reading .xlsm workbooks with openxml_reader does not execute macros or code."""
    fpath = os.path.join(source_dir, "Allen Jacques - TES copy.xlsm")
    wb = read_openxml_workbook(fpath)
    assert wb.has_macros is True
    assert wb.sha256 is not None
    assert len(wb.visible_sheet_names) == 3
    assert len(wb.hidden_sheet_names) == 11
    assert wb.ref_error_count > 0


def test_full_source_collection_ingestion_and_counts(app, source_dir):
    """Verify that all 20 historical workbooks can be ingested cleanly into ORG-001."""
    files = sorted(os.listdir(source_dir))
    workbooks = [f for f in files if f.endswith(".xlsx") or f.endswith(".xlsm")]
    assert len(workbooks) == 20

    for idx, fname in enumerate(workbooks, 1):
        fpath = os.path.join(source_dir, fname)
        sw = ingest_workbook_file(
            fpath,
            organization_id="ORG-001",
            source_id=f"HIST-EST-{idx:04d}",
            commit=True,
        )
        assert sw.id is not None
        assert sw.organization_id == "ORG-001"

    # Verify database counts
    assert HistoricalSourceWorkbook.query.filter_by(organization_id="ORG-001").count() == 20
    assert HistoricalEstimate.query.filter_by(organization_id="ORG-001").count() == 20
    assert HistoricalCostLineItem.query.filter_by(organization_id="ORG-001").count() > 50
    assert HistoricalLabourItem.query.filter_by(organization_id="ORG-001").count() > 20
    assert HistoricalSourceObservation.query.filter_by(organization_id="ORG-001").count() > 40
    assert HistoricalDataQualityFlag.query.filter_by(organization_id="ORG-001").count() > 0
