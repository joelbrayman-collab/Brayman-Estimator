"""Family B Adapter: Standard ICF Foundation workbooks (5 workbooks)."""

from decimal import Decimal
import re
from typing import Optional

from app.services.historical_ingestion.adapters.base import (
    BaseTemplateAdapter,
    ExtractedCostItem,
    ExtractedEstimate,
    ExtractedLabourItem,
    ExtractedQualityFlag,
    ExtractionResult,
)


class FamilyBAdapter(BaseTemplateAdapter):
    """Adapter for Standard ICF Foundation workbooks."""

    def extract(self) -> ExtractionResult:
        res = ExtractionResult(
            estimate=ExtractedEstimate(
                template_family="FAMILY_B",
                evidence_tier="TIER_C",
                pricing_method="COST_PLUS_MARKUP",
                currency="CAD",
            )
        )

        cd = self.workbook.get_sheet("COST DATA")
        calc_sheet = self.workbook.get_sheet("Worksheet FOUNDATION")

        if not calc_sheet:
            res.quality_flags.append(
                ExtractedQualityFlag(
                    flag_type="MISSING",
                    severity="CRITICAL",
                    description="Could not locate Worksheet FOUNDATION in Family B workbook",
                )
            )
            return res

        # 1. Project Identity & Global Config
        client_name = None
        project_type = "ICF Foundation"
        project_address = None
        margin_pct = Decimal("0.12")
        hourly_rate = Decimal("60.00")

        if cd:
            c2 = cd.get_value("C2")
            c3 = cd.get_value("C3")
            c4 = cd.get_value("C4")
            c6 = cd.get_value("C6")
            c10 = cd.get_float("C10")
            c14 = cd.get_float("C14") or cd.get_float("C12")

            client_name = c3 or c2 or c6
            project_address = c4

            if c10 is not None:
                margin_pct = Decimal(str(c10)).quantize(Decimal("0.0001"))
            if c14 is not None:
                hourly_rate = Decimal(str(c14)).quantize(Decimal("0.01"))

            self._add_obs(res, "COST DATA", "C3", "HistoricalEstimate", "client_name", "rule_icf_client")
            self._add_obs(res, "COST DATA", "C10", "HistoricalEstimate", "margin_percent", "rule_icf_margin")

        if not client_name or client_name in ["PROJECT:", "Name"]:
            proj_val = calc_sheet.get_value("C3") or calc_sheet.get_value("C4")
            if proj_val:
                client_name = proj_val

        res.estimate.client_name = client_name or "Unknown ICF Client"
        res.estimate.project_name = f"{client_name} - ICF Foundation" if client_name else "ICF Foundation Project"
        res.estimate.project_type = project_type
        res.estimate.project_address = project_address
        res.estimate.markup_percent = margin_pct
        res.estimate.margin_percent = margin_pct

        # 2. Extract Line Items & Labour across Stages
        sname = calc_sheet.name
        # Scan stages up to row 140
        current_stage = "Footings"
        for r in range(14, 140):
            header = calc_sheet.get_value(f"B{r}") or calc_sheet.get_value(f"A{r}")
            if header and header.strip().isupper() and len(header.strip()) > 3:
                current_stage = header.strip()

            desc = calc_sheet.get_value(f"B{r}")
            if not desc or desc.strip().upper() in ["CONCRETE", "ICF BLOCKS", "LABOUR", "STAGE TOTALS"]:
                continue

            desc_clean = desc.strip()
            ext_cost = self._to_decimal(calc_sheet.get_value(f"I{r}") or calc_sheet.get_value(f"H{r}"))

            is_labour = any(kw in desc_clean.lower() for kw in ["labour", "form", "pour", "finish", "strip", "install block"])
            crew = self._to_decimal(calc_sheet.get_value(f"C{r}") or calc_sheet.get_value(f"D{r}"))
            days = self._to_decimal(calc_sheet.get_value(f"E{r}"))
            hours = self._to_decimal(calc_sheet.get_value(f"G{r}") or calc_sheet.get_value(f"F{r}"))

            if is_labour and (crew or hours or ext_cost):
                if hours is None and crew and days:
                    hours = crew * days * Decimal("8.0")

                labour_item = ExtractedLabourItem(
                    task_description=f"{current_stage}: {desc_clean}",
                    crew_size=crew,
                    duration_days=days,
                    hours_per_day=Decimal("8.0"),
                    total_man_hours=hours,
                    hourly_rate=hourly_rate,
                    extended_labour_cost=ext_cost,
                    formula_pattern="Crew * Days * 8 Hours",
                    source_sheet=sname,
                    source_coord=f"B{r}:I{r}",
                )
                res.labour_items.append(labour_item)
                if ext_cost is not None:
                    self._add_obs(res, sname, f"I{r}", "HistoricalLabourItem", "extended_labour_cost", "rule_icf_labour_ext")
            elif ext_cost is not None or calc_sheet.get_value(f"C{r}"):
                qty = self._to_decimal(calc_sheet.get_value(f"C{r}") or calc_sheet.get_value(f"F{r}"))
                unit = calc_sheet.get_value(f"D{r}") or calc_sheet.get_value(f"G{r}")
                unit_cost = self._to_decimal(calc_sheet.get_value(f"E{r}"))

                cost_item = ExtractedCostItem(
                    description=f"{current_stage}: {desc_clean}",
                    quantity=qty,
                    unit=unit,
                    unit_cost=unit_cost,
                    extended_cost=ext_cost,
                    division="03 - Concrete",
                    category="ICF / Foundation Material",
                    source_sheet=sname,
                    source_coord=f"B{r}:I{r}",
                )
                res.cost_items.append(cost_item)
                if ext_cost is not None:
                    self._add_obs(res, sname, f"I{r}", "HistoricalCostLineItem", "extended_cost", "rule_icf_mat_ext")

        # 3. Detect Summary Rollup Totals
        # Standard ICF Foundation rollup is typically at rows 140–155
        direct_cost = None
        tax_amt = None
        total_price = None

        for r in range(140, 155):
            lbl_candidates = [
                calc_sheet.get_value(f"H{r}"),
                calc_sheet.get_value(f"G{r}"),
                calc_sheet.get_value(f"B{r}"),
            ]
            lbl = next((str(c).strip() for c in lbl_candidates if c), "").upper()
            val = self._to_decimal(calc_sheet.get_value(f"I{r}"))

            if "TOTAL" in lbl and "FOOTING" not in lbl and "WALL" not in lbl and "HST" not in lbl:
                if direct_cost is None and r < 148:
                    direct_cost = val
                    self._add_obs(res, sname, f"I{r}", "HistoricalEstimate", "direct_cost_total", "rule_icf_direct_cost")
                elif r >= 148:
                    total_price = val
                    self._add_obs(res, sname, f"I{r}", "HistoricalEstimate", "total_price", "rule_icf_total")
            elif "HST" in lbl:
                tax_amt = val
                self._add_obs(res, sname, f"I{r}", "HistoricalEstimate", "tax_amount", "rule_icf_tax")

        # In Family B, stage totals are marked up within each stage (I34, I64, etc.), so the rollup total is the pre-tax sell price.
        sell_price = direct_cost
        if sell_price is not None and tax_amt is not None and total_price is None:
            total_price = sell_price + tax_amt
        if sell_price is not None and margin_pct:
            markup_amt = (sell_price * margin_pct).quantize(Decimal("0.01"))
        else:
            markup_amt = None

        res.estimate.direct_cost_total = direct_cost
        res.estimate.markup_total = markup_amt
        res.estimate.selling_price_before_tax = sell_price
        res.estimate.tax_amount = tax_amt
        res.estimate.total_price = total_price

        # 4. Check presentation contract sheets
        contract_sheet = self.workbook.get_sheet("ICF Contract") or self.workbook.get_sheet("ICF Estimate")
        if contract_sheet and contract_sheet.is_visible:
            c_date = contract_sheet.get_value("E2") or contract_sheet.get_value("F2")
            if c_date:
                res.estimate.estimate_date = str(c_date).strip()

        if self.workbook.ref_error_count > 0:
            res.quality_flags.append(
                ExtractedQualityFlag(
                    flag_type="FORMULA_ERROR",
                    severity="INFO",
                    description=f"Workbook contains {self.workbook.ref_error_count} #REF! formula error cells in background/hidden layers.",
                )
            )

        return res
