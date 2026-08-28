"""Family A Adapter: Slab-on-Grade / Thickened Edge Slab workbooks (9 workbooks)."""

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


class FamilyAAdapter(BaseTemplateAdapter):
    """Adapter for Slab-on-Grade / Thickened Edge Slab workbooks."""

    def extract(self) -> ExtractionResult:
        res = ExtractionResult(
            estimate=ExtractedEstimate(
                template_family="FAMILY_A",
                evidence_tier="TIER_C",
                pricing_method="COST_PLUS_MARKUP",
                currency="CAD",
            )
        )

        cd = self.workbook.get_sheet("COST DATA")
        calc_sheet = None
        for sname in ["House TES", "Worksheet GARAGE SLAB", "Worksheet Slab"]:
            s = self.workbook.get_sheet(sname)
            if s and s.is_visible:
                calc_sheet = s
                break

        if not calc_sheet:
            for sname in self.workbook.visible_sheet_names:
                if "SLAB" in sname.upper() or "TES" in sname.upper():
                    calc_sheet = self.workbook.get_sheet(sname)
                    break

        if not calc_sheet:
            res.quality_flags.append(
                ExtractedQualityFlag(
                    flag_type="MISSING",
                    severity="CRITICAL",
                    description="Could not locate primary slab calculation sheet in Family A workbook",
                )
            )
            return res

        # 1. Extract Project Identity & Global Config from COST DATA
        client_name = None
        project_type = None
        project_address = None
        margin_pct = Decimal("0.15")
        hourly_rate = Decimal("60.00")

        if cd:
            c2 = cd.get_value("C2")
            c3 = cd.get_value("C3")
            c4 = cd.get_value("C4")
            c5 = cd.get_value("C5")
            c10 = cd.get_float("C10")
            c14 = cd.get_float("C14") or cd.get_float("C12")

            # In some templates C2 is project type, C3 is client name; in others C2 is project name
            project_type = c2 or "Slab-on-Grade"
            client_name = c3 or c2
            project_address = c4

            if c10 is not None:
                margin_pct = Decimal(str(c10)).quantize(Decimal("0.0001"))
            if c14 is not None:
                hourly_rate = Decimal(str(c14)).quantize(Decimal("0.01"))

            self._add_obs(res, "COST DATA", "C3", "HistoricalEstimate", "client_name", "rule_cost_data_client")
            self._add_obs(res, "COST DATA", "C2", "HistoricalEstimate", "project_type", "rule_cost_data_proj_type")
            self._add_obs(res, "COST DATA", "C10", "HistoricalEstimate", "margin_percent", "rule_cost_data_margin")

        # Fallback identity from calculation sheet
        if not client_name or client_name in ["PROJECT:", "Name"]:
            proj_val = calc_sheet.get_value("C4") or calc_sheet.get_value("C3")
            if proj_val:
                client_name = proj_val

        res.estimate.client_name = client_name or "Unknown Client"
        res.estimate.project_name = f"{client_name} - {project_type}" if client_name else project_type
        res.estimate.project_type = project_type or "Slab-on-Grade"
        res.estimate.project_address = project_address
        res.estimate.markup_percent = margin_pct
        res.estimate.margin_percent = margin_pct

        # 2. Extract Line Items & Labour from Calculation Sheet
        sname = calc_sheet.name
        start_row = 14
        end_row = 50

        # Scan for line items
        for r in range(start_row, end_row + 1):
            desc = calc_sheet.get_value(f"B{r}")
            if not desc:
                continue

            desc_clean = desc.strip()
            # Check if this is a section header or summary line
            if desc_clean.upper() in ["CONCRETE", "ICF BLOCKS", "SLABS", "LABOUR", "COST DATA"]:
                continue

            # Check if this is a labour row
            c_val = calc_sheet.get_value(f"C{r}")
            d_val = calc_sheet.get_value(f"D{r}")
            f_val = calc_sheet.get_value(f"F{r}")
            h_val = calc_sheet.get_value(f"H{r}") or calc_sheet.get_value(f"I{r}")

            is_labour = any(kw in desc_clean.lower() for kw in ["labour", "form", "pour", "finish", "strip", "insulation labour"])

            if is_labour and (calc_sheet.get_float(f"C{r}") or calc_sheet.get_float(f"F{r}")):
                crew = self._to_decimal(calc_sheet.get_value(f"C{r}"))
                days = self._to_decimal(calc_sheet.get_value(f"D{r}"))
                hours = self._to_decimal(calc_sheet.get_value(f"F{r}"))
                ext_cost = self._to_decimal(h_val)

                if hours is None and crew and days:
                    hours = crew * days * Decimal("8.0")

                labour_item = ExtractedLabourItem(
                    task_description=desc_clean,
                    crew_size=crew,
                    duration_days=days,
                    hours_per_day=Decimal("8.0"),
                    total_man_hours=hours,
                    hourly_rate=hourly_rate,
                    extended_labour_cost=ext_cost,
                    formula_pattern="Crew * Days * 8 Hours",
                    source_sheet=sname,
                    source_coord=f"B{r}:H{r}",
                )
                res.labour_items.append(labour_item)
                self._add_obs(res, sname, f"H{r}", "HistoricalLabourItem", "extended_labour_cost", "rule_slab_labour_ext")
            else:
                ext_cost = self._to_decimal(h_val)
                qty = self._to_decimal(calc_sheet.get_value(f"C{r}") or calc_sheet.get_value(f"F{r}"))
                unit = calc_sheet.get_value(f"D{r}") or calc_sheet.get_value(f"G{r}")
                unit_cost = self._to_decimal(calc_sheet.get_value(f"E{r}"))

                if ext_cost is not None or qty is not None:
                    cost_item = ExtractedCostItem(
                        description=desc_clean,
                        quantity=qty,
                        unit=unit,
                        unit_cost=unit_cost,
                        extended_cost=ext_cost,
                        division="03 - Concrete",
                        category="Material / Equipment",
                        source_sheet=sname,
                        source_coord=f"B{r}:H{r}",
                    )
                    res.cost_items.append(cost_item)
                    if ext_cost is not None:
                        self._add_obs(res, sname, f"H{r}", "HistoricalCostLineItem", "extended_cost", "rule_slab_mat_ext")

        # 3. Detect Summary Totals
        # Look for Sub-Total, Margin, Selling Price, HST, Total
        direct_cost = None
        markup_amt = None
        sell_price = None
        tax_amt = None
        total_price = None

        for r in range(30, 60):
            lbl_candidates = [
                calc_sheet.get_value(f"G{r}"),
                calc_sheet.get_value(f"F{r}"),
                calc_sheet.get_value(f"B{r}"),
                calc_sheet.get_value(f"E{r}"),
            ]
            lbl = next((str(c).strip() for c in lbl_candidates if c), "").upper()
            val = self._to_decimal(calc_sheet.get_value(f"H{r}") or calc_sheet.get_value(f"I{r}"))
            if val is None:
                continue

            if "SUB-TOTAL" in lbl or "SUBTOTAL" in lbl or (lbl == "TOTAL" and direct_cost is None and r < 40):
                direct_cost = val
                self._add_obs(res, sname, f"H{r}", "HistoricalEstimate", "direct_cost_total", "rule_slab_direct_cost")
            elif "MARGIN" in lbl:
                markup_amt = val
                self._add_obs(res, sname, f"H{r}", "HistoricalEstimate", "markup_total", "rule_slab_markup")
            elif "TOTAL ICF" in lbl or "TOTAL BASEMENT" in lbl or "TOTAL PROJECT" in lbl or "SELL" in lbl:
                sell_price = val
                self._add_obs(res, sname, f"H{r}", "HistoricalEstimate", "selling_price_before_tax", "rule_slab_sell_price")
            elif "HST" in lbl:
                tax_amt = val
                self._add_obs(res, sname, f"H{r}", "HistoricalEstimate", "tax_amount", "rule_slab_tax")
            elif lbl == "TOTAL":
                if sell_price is None and tax_amt is None:
                    sell_price = val
                    self._add_obs(res, sname, f"H{r}", "HistoricalEstimate", "selling_price_before_tax", "rule_slab_sell_price")
                elif tax_amt is not None or sell_price is not None:
                    total_price = val
                    self._add_obs(res, sname, f"H{r}", "HistoricalEstimate", "total_price", "rule_slab_total")

        # Reconcile missing totals if derivable
        if direct_cost is not None and markup_amt is not None and sell_price is None:
            sell_price = direct_cost + markup_amt
        if sell_price is not None and tax_amt is not None and (total_price is None or total_price == sell_price):
            total_price = sell_price + tax_amt
        if direct_cost is None and sell_price is not None and markup_amt is not None:
            direct_cost = sell_price - markup_amt

        res.estimate.direct_cost_total = direct_cost
        res.estimate.markup_total = markup_amt
        res.estimate.selling_price_before_tax = sell_price
        res.estimate.tax_amount = tax_amt
        res.estimate.total_price = total_price

        # 4. Check presentation sheet residue / discrepancy
        pres_sheet = self.workbook.get_sheet("Esiimate") or self.workbook.get_sheet("Invoice SLABS")
        if pres_sheet and pres_sheet.is_visible:
            # check estimate date or header
            pres_date = pres_sheet.get_value("E2") or pres_sheet.get_value("F2")
            if pres_date:
                res.estimate.estimate_date = str(pres_date).strip()

            # check for residue in presentation sheet
            for coord in ["F2", "C3", "E8", "F5"]:
                txt = pres_sheet.get_value(coord)
                if txt and client_name and client_name.lower() not in txt.lower():
                    if any(known in txt for known in ["Gorman", "BROWN", "Township", "Kyle Guy"]):
                        res.quality_flags.append(
                            ExtractedQualityFlag(
                                flag_type="POSSIBLE_TEMPLATE_RESIDUE",
                                severity="WARNING",
                                sheet_name=pres_sheet.name,
                                cell_coordinate=coord,
                                description=f"Presentation sheet {pres_sheet.name}!{coord} contains '{txt}', potentially stale copy-paste residue differing from client '{client_name}'.",
                            )
                        )

        # Flag broken formula errors if any
        if self.workbook.ref_error_count > 0:
            res.quality_flags.append(
                ExtractedQualityFlag(
                    flag_type="FORMULA_ERROR",
                    severity="INFO",
                    description=f"Workbook contains {self.workbook.ref_error_count} #REF! formula error cells in background/hidden layers.",
                )
            )

        return res
