"""Family C Adapter: Extended Multi-Trade ICF workbooks (1 workbook - Michelle Steele)."""

from decimal import Decimal
from typing import Optional

from app.services.historical_ingestion.adapters.base import (
    BaseTemplateAdapter,
    ExtractedCostItem,
    ExtractedEstimate,
    ExtractedLabourItem,
    ExtractedQualityFlag,
    ExtractedSubcontractItem,
    ExtractionResult,
)


class FamilyCAdapter(BaseTemplateAdapter):
    """Adapter for Extended Multi-Trade ICF workbooks."""

    def extract(self) -> ExtractionResult:
        res = ExtractionResult(
            estimate=ExtractedEstimate(
                template_family="FAMILY_C",
                evidence_tier="TIER_C",
                pricing_method="COST_PLUS_MARKUP",
                currency="CAD",
            )
        )

        cd = self.workbook.get_sheet("COST DATA")
        fdn = self.workbook.get_sheet("Worksheet FOUNDATION")
        subfloor = self.workbook.get_sheet("Sub-floor Calcs")

        client_name = "Michelle Steele"
        project_type = "Full Height ICF Multi-Trade"
        project_address = "5328 Kilby Road, Manotick ON"
        ref_num = "BC(2025-ESTIMATE)STEELE-001"
        margin_pct = Decimal("0.125")
        hourly_rate = Decimal("62.50")

        if cd:
            c3 = cd.get_value("C3")
            c4 = cd.get_value("C4")
            c6 = cd.get_value("C6")
            c8 = cd.get_value("C8")
            c13 = cd.get_float("C13")
            c17 = cd.get_float("C17")

            ref_num = c4 or ref_num
            client_name = c6 or c3 or client_name
            project_address = c8 or project_address
            if c13 is not None:
                margin_pct = Decimal(str(c13)).quantize(Decimal("0.0001"))
            if c17 is not None:
                hourly_rate = Decimal(str(c17)).quantize(Decimal("0.01"))

            self._add_obs(res, "COST DATA", "C4", "HistoricalEstimate", "estimate_number", "rule_ext_icf_ref")
            self._add_obs(res, "COST DATA", "C6", "HistoricalEstimate", "client_name", "rule_ext_icf_client")

        res.estimate.client_name = client_name
        res.estimate.project_name = f"{client_name} - Full Height ICF"
        res.estimate.project_type = project_type
        res.estimate.project_address = project_address
        res.estimate.estimate_number = ref_num
        res.estimate.markup_percent = margin_pct
        res.estimate.margin_percent = margin_pct

        # 1. Extract Foundation line items & labour
        if fdn:
            current_stage = "Footings"
            for r in range(12, 140):
                hdr = fdn.get_value(f"B{r}") or fdn.get_value(f"A{r}")
                if hdr and hdr.strip().isupper() and len(hdr.strip()) > 3:
                    current_stage = hdr.strip()

                desc = fdn.get_value(f"B{r}")
                if not desc or desc.strip().upper() in ["CONCRETE", "ICF BLOCKS", "LABOUR", "STAGE TOTALS"]:
                    continue

                desc_clean = desc.strip()
                ext_cost = self._to_decimal(fdn.get_value(f"H{r}") or fdn.get_value(f"I{r}"))

                is_labour = any(kw in desc_clean.lower() for kw in ["labour", "preparation", "pour", "finish", "strip", "install block"])
                crew = self._to_decimal(fdn.get_value(f"C{r}") or fdn.get_value(f"D{r}"))
                days = self._to_decimal(fdn.get_value(f"E{r}") or fdn.get_value(f"D{r}"))
                hours = self._to_decimal(fdn.get_value(f"F{r}") or fdn.get_value(f"G{r}"))

                if is_labour and (crew or hours or ext_cost):
                    if hours is None and crew and days:
                        hours = crew * days * Decimal("8.0")

                    res.labour_items.append(
                        ExtractedLabourItem(
                            task_description=f"Foundation {current_stage}: {desc_clean}",
                            crew_size=crew,
                            duration_days=days,
                            hours_per_day=Decimal("8.0"),
                            total_man_hours=hours,
                            hourly_rate=hourly_rate,
                            extended_labour_cost=ext_cost,
                            formula_pattern="Crew * Days * 8 Hours",
                            source_sheet=fdn.name,
                            source_coord=f"B{r}:H{r}",
                        )
                    )
                elif ext_cost is not None or fdn.get_value(f"F{r}"):
                    qty = self._to_decimal(fdn.get_value(f"F{r}") or fdn.get_value(f"C{r}"))
                    unit = fdn.get_value(f"G{r}") or fdn.get_value(f"D{r}")
                    cost_item = ExtractedCostItem(
                        description=f"Foundation {current_stage}: {desc_clean}",
                        quantity=qty,
                        unit=unit,
                        extended_cost=ext_cost,
                        division="03 - Concrete",
                        category="Foundation Material",
                        source_sheet=fdn.name,
                        source_coord=f"B{r}:H{r}",
                    )
                    res.cost_items.append(cost_item)

        # 2. Extract Sub-floor items
        if subfloor:
            for r in range(8, 21):
                desc = subfloor.get_value(f"B{r}")
                if not desc:
                    continue
                ext_cost = self._to_decimal(subfloor.get_value(f"E{r}") or subfloor.get_value(f"F{r}"))
                qty = self._to_decimal(subfloor.get_value(f"D{r}") or subfloor.get_value(f"C{r}"))
                unit_cost = self._to_decimal(subfloor.get_value(f"C{r}"))
                res.cost_items.append(
                    ExtractedCostItem(
                        description=f"Sub-Floor: {desc.strip()}",
                        quantity=qty,
                        unit_cost=unit_cost,
                        extended_cost=ext_cost,
                        division="06 - Wood, Plastics, and Composites",
                        category="Framing / Sub-Floor Material",
                        source_sheet=subfloor.name,
                        source_coord=f"B{r}:F{r}",
                    )
                )

        # 3. Extract Contract / Estimate Totals from ICF Estimate / ICF Contract
        icf_est = self.workbook.get_sheet("ICF Estimate") or self.workbook.get_sheet("ICF Contract")
        if icf_est:
            tot_before_tax = self._to_decimal(icf_est.get_value("E22"))
            tax_amt = self._to_decimal(icf_est.get_value("E23"))
            tot_with_tax = self._to_decimal(icf_est.get_value("E24"))

            res.estimate.selling_price_before_tax = tot_before_tax
            res.estimate.tax_amount = tax_amt
            res.estimate.total_price = tot_with_tax
            if tot_before_tax and margin_pct:
                res.estimate.direct_cost_total = (tot_before_tax / (Decimal("1.0") + margin_pct)).quantize(Decimal("0.01"))
                res.estimate.markup_total = tot_before_tax - res.estimate.direct_cost_total

            self._add_obs(res, icf_est.name, "E22", "HistoricalEstimate", "selling_price_before_tax", "rule_ext_icf_sell_total")
            self._add_obs(res, icf_est.name, "E23", "HistoricalEstimate", "tax_amount", "rule_ext_icf_tax")
            self._add_obs(res, icf_est.name, "E24", "HistoricalEstimate", "total_price", "rule_ext_icf_grand_total")

        # 4. Check for template residue in trade estimate sheets
        joist_sheet = self.workbook.get_sheet("Estimate Floor Joists-Trusses")
        if joist_sheet:
            residue_client = joist_sheet.get_value("E8")
            if residue_client and "Jamie Jackson" in residue_client:
                res.quality_flags.append(
                    ExtractedQualityFlag(
                        flag_type="POSSIBLE_TEMPLATE_RESIDUE",
                        severity="WARNING",
                        sheet_name=joist_sheet.name,
                        cell_coordinate="E8",
                        description=f"Sheet {joist_sheet.name}!E8 contains residue client name '{residue_client}', differing from primary client '{client_name}'.",
                    )
                )

        return res
