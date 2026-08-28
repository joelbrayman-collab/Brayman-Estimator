"""Historical Estimate Ingestion Engine (FG-006 / Phase B).

Coordinates OpenXML parsing, template classification, family adapters, source-cell
provenance, data quality flags, and idempotent organization-owned persistence.
"""

from datetime import datetime
import hashlib
import os
from typing import Any, Dict, List, Optional, Tuple

from app import db
from app.models.historical_estimates import (
    HistoricalCostLineItem,
    HistoricalDataQualityFlag,
    HistoricalEstimate,
    HistoricalLabourItem,
    HistoricalSourceObservation,
    HistoricalSourceWorkbook,
    HistoricalSubcontractItem,
)
from app.services.historical_ingestion.adapters.base import (
    BaseTemplateAdapter,
    ExtractionResult,
)
from app.services.historical_ingestion.adapters.family_a import FamilyAAdapter
from app.services.historical_ingestion.adapters.family_b import FamilyBAdapter
from app.services.historical_ingestion.adapters.family_c import FamilyCAdapter
from app.services.historical_ingestion.adapters.family_d import FamilyDAdapter
from app.services.historical_ingestion.adapters.family_e import FamilyEAdapter
from app.services.historical_ingestion.openxml_reader import (
    WorkbookData,
    read_openxml_workbook,
)
from app.services.historical_ingestion.template_classifier import (
    FAMILY_A,
    FAMILY_B,
    FAMILY_C,
    FAMILY_D,
    FAMILY_E,
    classify_template_family,
)
from app.services.organizations import get_current_organization_id

ADAPTER_REGISTRY = {
    FAMILY_A: FamilyAAdapter,
    FAMILY_B: FamilyBAdapter,
    FAMILY_C: FamilyCAdapter,
    FAMILY_D: FamilyDAdapter,
    FAMILY_E: FamilyEAdapter,
}


class HistoricalIngestionError(Exception):
    """Raised when historical ingestion encounters an unrecoverable failure."""
    pass


def get_adapter(family: str, wb: WorkbookData) -> BaseTemplateAdapter:
    """Instantiate the extraction adapter for a template family."""
    adapter_cls = ADAPTER_REGISTRY.get(family, FamilyEAdapter)
    return adapter_cls(wb)


def ingest_workbook_file(
    file_path: str,
    organization_id: Optional[str] = None,
    source_id: Optional[str] = None,
    ingestion_version: str = "v1",
    commit: bool = True,
) -> HistoricalSourceWorkbook:
    """Ingest a historical estimate workbook file deterministically and idempotently."""
    org_id = organization_id or get_current_organization_id()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Historical workbook file not found: {file_path}")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    sha256 = hashlib.sha256(file_bytes).hexdigest()
    byte_size = len(file_bytes)
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    mtime = datetime.utcfromtimestamp(os.path.getmtime(file_path))

    idempotency_key = f"{org_id}:{sha256}:{ingestion_version}"

    # 1. Idempotency Check: Return existing record if already ingested
    existing = HistoricalSourceWorkbook.query.filter_by(
        idempotency_key=idempotency_key,
        organization_id=org_id,
    ).first()
    if existing:
        return existing

    # 2. Parse OpenXML workbook safely (no macro execution)
    wb_data = read_openxml_workbook(file_path)

    # 3. Classify Template Family
    family_code, confidence, class_reason = classify_template_family(wb_data)

    # 4. Execute Family Adapter
    adapter = get_adapter(family_code, wb_data)
    extraction_result: ExtractionResult = adapter.extract()

    # 5. Determine source_id if not provided (e.g. autoincrement HIST-EST-xxxx)
    if not source_id:
        count = HistoricalSourceWorkbook.query.filter_by(organization_id=org_id).count() + 1
        source_id = f"HIST-EST-{count:04d}"

    # 6. Create HistoricalSourceWorkbook root
    sw = HistoricalSourceWorkbook(
        organization_id=org_id,
        source_id=source_id,
        original_filename=filename,
        extension=ext,
        sha256=sha256,
        byte_size=byte_size,
        filesystem_modified_at=mtime,
        template_family=family_code,
        ingestion_status="INGESTED",
        ingestion_version=ingestion_version,
        idempotency_key=idempotency_key,
        source_file_path=file_path,
        notes=class_reason,
    )
    db.session.add(sw)
    db.session.flush()

    # 7. Create HistoricalEstimate
    ee = extraction_result.estimate
    he = HistoricalEstimate(
        organization_id=org_id,
        source_workbook_id=sw.id,
        project_name=ee.project_name,
        client_name=ee.client_name,
        project_address=ee.project_address,
        project_type=ee.project_type,
        template_family=family_code,
        estimate_date=ee.estimate_date,
        estimate_number=ee.estimate_number,
        evidence_tier=ee.evidence_tier,
        pricing_method=ee.pricing_method,
        markup_percent=ee.markup_percent,
        margin_percent=ee.margin_percent,
        direct_cost_total=ee.direct_cost_total,
        markup_total=ee.markup_total,
        contingency_total=ee.contingency_total,
        selling_price_before_tax=ee.selling_price_before_tax,
        tax_amount=ee.tax_amount,
        total_price=ee.total_price,
        currency=ee.currency,
        extraction_confidence=confidence,
        review_status="EXTRACTED",
    )
    db.session.add(he)
    db.session.flush()

    # 8. Store Cell Observations & Map to Line Items
    obs_id_map: Dict[Tuple[str, str], int] = {}
    for obs in extraction_result.observations:
        hso = HistoricalSourceObservation(
            organization_id=org_id,
            source_workbook_id=sw.id,
            sheet_name=obs.sheet_name,
            cell_coordinate=obs.cell_coordinate,
            raw_formula=obs.raw_formula,
            raw_value=obs.raw_value,
            display_value=obs.display_value,
            normalized_entity_type=obs.normalized_entity_type,
            normalized_entity_id=he.id if obs.normalized_entity_type == "HistoricalEstimate" else None,
            normalized_field=obs.normalized_field,
            extraction_rule_id=obs.extraction_rule_id,
            confidence=obs.confidence,
        )
        db.session.add(hso)
        db.session.flush()
        obs_id_map[(obs.sheet_name, obs.cell_coordinate)] = hso.id

    # 9. Store Material / Cost Line Items
    for item in extraction_result.cost_items:
        prov_id = None
        if item.source_sheet and item.source_coord:
            prov_id = obs_id_map.get((item.source_sheet, item.source_coord.split(":")[-1]))

        cli = HistoricalCostLineItem(
            organization_id=org_id,
            historical_estimate_id=he.id,
            division=item.division,
            category=item.category,
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
            unit_cost=item.unit_cost,
            extended_cost=item.extended_cost,
            markup_percent=item.markup_percent,
            selling_price=item.selling_price,
            supplier_name=item.supplier_name,
            is_allowance=item.is_allowance,
            provenance_observation_id=prov_id,
        )
        db.session.add(cli)

    # 10. Store Labour Items
    for item in extraction_result.labour_items:
        prov_id = None
        if item.source_sheet and item.source_coord:
            prov_id = obs_id_map.get((item.source_sheet, item.source_coord.split(":")[-1]))

        li = HistoricalLabourItem(
            organization_id=org_id,
            historical_estimate_id=he.id,
            task_description=item.task_description,
            crew_size=item.crew_size,
            duration_days=item.duration_days,
            hours_per_day=item.hours_per_day,
            total_man_hours=item.total_man_hours,
            hourly_rate=item.hourly_rate,
            extended_labour_cost=item.extended_labour_cost,
            formula_pattern=item.formula_pattern,
            provenance_observation_id=prov_id,
        )
        db.session.add(li)

    # 11. Store Subcontract Items
    for item in extraction_result.subcontract_items:
        prov_id = None
        if item.source_sheet and item.source_coord:
            prov_id = obs_id_map.get((item.source_sheet, item.source_coord.split(":")[-1]))

        si = HistoricalSubcontractItem(
            organization_id=org_id,
            historical_estimate_id=he.id,
            trade_category=item.trade_category,
            scope_description=item.scope_description,
            subcontractor_name=item.subcontractor_name,
            direct_cost=item.direct_cost,
            markup_percent=item.markup_percent,
            selling_price=item.selling_price,
            installation_included=item.installation_included,
            quote_date=item.quote_date,
            provenance_observation_id=prov_id,
        )
        db.session.add(si)

    # 12. Store Data Quality Flags
    for flag in extraction_result.quality_flags:
        qf = HistoricalDataQualityFlag(
            organization_id=org_id,
            source_workbook_id=sw.id,
            historical_estimate_id=he.id,
            flag_type=flag.flag_type,
            severity=flag.severity,
            sheet_name=flag.sheet_name,
            cell_coordinate=flag.cell_coordinate,
            description=flag.description,
        )
        db.session.add(qf)

    if commit:
        db.session.commit()

    return sw
