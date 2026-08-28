"""Base adapter interface and data transfer objects for historical estimate extraction."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.services.historical_ingestion.openxml_reader import SheetData, WorkbookData


@dataclass
class ExtractedObservation:
    sheet_name: str
    cell_coordinate: str
    raw_formula: Optional[str]
    raw_value: Optional[str]
    display_value: Optional[str]
    normalized_entity_type: str
    normalized_field: str
    extraction_rule_id: str
    confidence: float = 1.0


@dataclass
class ExtractedCostItem:
    description: str
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_cost: Optional[Decimal] = None
    extended_cost: Optional[Decimal] = None
    division: Optional[str] = None
    category: Optional[str] = None
    markup_percent: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    supplier_name: Optional[str] = None
    is_allowance: bool = False
    source_sheet: Optional[str] = None
    source_coord: Optional[str] = None


@dataclass
class ExtractedLabourItem:
    task_description: str
    crew_size: Optional[Decimal] = None
    duration_days: Optional[Decimal] = None
    hours_per_day: Decimal = Decimal("8.0")
    total_man_hours: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    extended_labour_cost: Optional[Decimal] = None
    formula_pattern: Optional[str] = None
    source_sheet: Optional[str] = None
    source_coord: Optional[str] = None


@dataclass
class ExtractedSubcontractItem:
    trade_category: str
    scope_description: str
    subcontractor_name: Optional[str] = None
    direct_cost: Optional[Decimal] = None
    markup_percent: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    installation_included: Optional[bool] = None
    quote_date: Optional[str] = None
    source_sheet: Optional[str] = None
    source_coord: Optional[str] = None


@dataclass
class ExtractedQualityFlag:
    flag_type: str
    severity: str
    description: str
    sheet_name: Optional[str] = None
    cell_coordinate: Optional[str] = None


@dataclass
class ExtractedEstimate:
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    project_address: Optional[str] = None
    project_type: Optional[str] = None
    template_family: str = "UNKNOWN"
    estimate_date: Optional[str] = None
    estimate_number: Optional[str] = None
    evidence_tier: str = "TIER_C"
    pricing_method: str = "COST_PLUS_MARKUP"
    markup_percent: Optional[Decimal] = None
    margin_percent: Optional[Decimal] = None
    direct_cost_total: Optional[Decimal] = None
    markup_total: Optional[Decimal] = None
    contingency_total: Optional[Decimal] = None
    selling_price_before_tax: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    currency: str = "CAD"
    extraction_confidence: float = 1.0


@dataclass
class ExtractionResult:
    estimate: ExtractedEstimate
    cost_items: List[ExtractedCostItem] = field(default_factory=list)
    labour_items: List[ExtractedLabourItem] = field(default_factory=list)
    subcontract_items: List[ExtractedSubcontractItem] = field(default_factory=list)
    observations: List[ExtractedObservation] = field(default_factory=list)
    quality_flags: List[ExtractedQualityFlag] = field(default_factory=list)


class BaseTemplateAdapter:
    """Base template extraction adapter."""

    def __init__(self, workbook: WorkbookData):
        self.workbook = workbook

    def extract(self) -> ExtractionResult:
        raise NotImplementedError("Subclasses must implement extract()")

    def _to_decimal(self, val: Any) -> Optional[Decimal]:
        if val is None:
            return None
        try:
            s = str(val).replace("$", "").replace(",", "").strip()
            if not s or s.startswith("#"):
                return None
            return Decimal(s).quantize(Decimal("0.01"))
        except Exception:
            return None

    def _add_obs(
        self,
        res: ExtractionResult,
        sheet_name: str,
        coord: str,
        entity_type: str,
        field_name: str,
        rule_id: str,
        confidence: float = 1.0,
    ) -> None:
        sheet = self.workbook.get_sheet(sheet_name)
        if not sheet:
            return
        cell = sheet.get_cell(coord)
        res.observations.append(
            ExtractedObservation(
                sheet_name=sheet_name,
                cell_coordinate=coord,
                raw_formula=cell.raw_formula if cell else None,
                raw_value=cell.raw_value if cell else None,
                display_value=cell.display_value if cell else None,
                normalized_entity_type=entity_type,
                normalized_field=field_name,
                extraction_rule_id=rule_id,
                confidence=confidence,
            )
        )
