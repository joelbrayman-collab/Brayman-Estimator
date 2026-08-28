"""Family D Adapter: Comprehensive Build Package workbooks (1 workbook - Mike Pratt)."""

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


class FamilyDAdapter(BaseTemplateAdapter):
    """Adapter for Comprehensive Multi-Trade Build Package workbooks."""

    def extract(self) -> ExtractionResult:
        res = ExtractionResult(
            estimate=ExtractedEstimate(
                template_family="FAMILY_D",
                evidence_tier="TIER_B",  # Mike Pratt contracted full build
                pricing_method="TIERED_MARKUP",
                currency="CAD",
            )
        )

        sum_sheet = self.workbook.get_sheet("SUMMARY")
        cd_sheet = self.workbook.get_sheet("Cost Data") or self.workbook.get_sheet("COST DATA")
        fdn_sheet = self.workbook.get_sheet("Foundation")
        bc_sheet = self.workbook.get_sheet("BC Internal Work")
        sub_sheet = self.workbook.get_sheet("SUB-TRADES")

        client_name = "Mike Pratt"
        project_name = "Mike Pratt - Full ICF Custom Home Build"
        project_address = "2562 Church St"
        project_type = "Custom Residential ICF Build"
        margin_pct = Decimal("0.125")

        if cd_sheet:
            c3 = cd_sheet.get_value("C3")
            c4 = cd_sheet.get_value("C4")
            c10 = cd_sheet.get_float("C10")
            if c3:
                client_name = c3
            if c4:
                project_address = c4
            if c10:
                margin_pct = Decimal(str(c10)).quantize(Decimal("0.0001"))

        res.estimate.client_name = client_name
        res.estimate.project_name = project_name
        res.estimate.project_address = project_address
        res.estimate.project_type = project_type
        res.estimate.markup_percent = margin_pct
        res.estimate.margin_percent = margin_pct

        # 1. Extract Summary Master Rollup
        if sum_sheet:
            # Pilot anchors:
            # Direct Cost: 547,405.80
            # Tiered Markup: 73,419.11
            # Selling Price before tax: 620,824.91 (C37)
            # HST: 80,707.24
            # Total: 701,532.15
            sell_price = self._to_decimal(sum_sheet.get_value("C37"))
            if sell_price is None:
                for r in range(35, 45):
                    lbl = sum_sheet.get_value(f"A{r}")
                    if lbl and "TOTAL" in lbl.upper():
                        sell_price = self._to_decimal(sum_sheet.get_value(f"C{r}"))
                        break

            # Extract GC margin & contingency as distinct commercial layers
            gc_margin = self._to_decimal(sum_sheet.get_value("C35")) or Decimal("0")
            contingency = self._to_decimal(sum_sheet.get_value("C36")) or Decimal("0")

            if sell_price is not None:
                direct_cost = sell_price - gc_margin - contingency
                tax_amt = (sell_price * Decimal("0.13")).quantize(Decimal("0.01"))
                grand_total = sell_price + tax_amt

                res.estimate.direct_cost_total = direct_cost
                res.estimate.markup_total = gc_margin
                res.estimate.contingency_total = contingency
                res.estimate.selling_price_before_tax = sell_price
                res.estimate.tax_amount = tax_amt
                res.estimate.total_price = grand_total

                self._add_obs(res, "SUMMARY", "C37", "HistoricalEstimate", "selling_price_before_tax", "rule_build_sell_price")
                self._add_obs(res, "SUMMARY", "C35", "HistoricalEstimate", "markup_total", "rule_build_gc_margin")
                self._add_obs(res, "SUMMARY", "C36", "HistoricalEstimate", "contingency_total", "rule_build_contingency")

            # Extract division line items from SUMMARY
            for r in range(9, 35):
                cat = sum_sheet.get_value(f"A{r}")
                desc = sum_sheet.get_value(f"B{r}") or cat
                val = self._to_decimal(sum_sheet.get_value(f"C{r}"))
                if desc and val is not None and val > 0:
                    res.cost_items.append(
                        ExtractedCostItem(
                            description=f"{cat}: {desc}" if cat and cat != desc else desc,
                            division=cat or "01 - General Requirements",
                            category="Package / Division Total",
                            extended_cost=val,
                            source_sheet="SUMMARY",
                            source_coord=f"A{r}:C{r}",
                        )
                    )

        # 2. Extract Sub-trades quotes from SUB-TRADES sheet
        if sub_sheet:
            for r in range(4, 30):
                trade = sub_sheet.get_value(f"B{r}") or sub_sheet.get_value(f"A{r}")
                desc = sub_sheet.get_value(f"C{r}") or trade
                amt = self._to_decimal(sub_sheet.get_value(f"M{r}") or sub_sheet.get_value(f"K{r}") or sub_sheet.get_value(f"D{r}"))
                if trade and amt is not None and amt > 0:
                    res.subcontract_items.append(
                        ExtractedSubcontractItem(
                            trade_category=trade.strip(),
                            scope_description=desc.strip(),
                            direct_cost=amt,
                            source_sheet=sub_sheet.name,
                            source_coord=f"B{r}:M{r}",
                        )
                    )

        # 3. Extract Labour items from BC Internal Work
        if bc_sheet:
            for r in range(5, 40):
                task = bc_sheet.get_value(f"B{r}")
                if not task:
                    continue
                crew = self._to_decimal(bc_sheet.get_value(f"C{r}"))
                days = self._to_decimal(bc_sheet.get_value(f"D{r}"))
                hours = self._to_decimal(bc_sheet.get_value(f"F{r}"))
                cost = self._to_decimal(bc_sheet.get_value(f"H{r}"))
                if hours or cost:
                    res.labour_items.append(
                        ExtractedLabourItem(
                            task_description=task.strip(),
                            crew_size=crew,
                            duration_days=days,
                            hours_per_day=Decimal("8.0"),
                            total_man_hours=hours,
                            hourly_rate=Decimal("65.00"),
                            extended_labour_cost=cost,
                            formula_pattern="Crew * Days * 8 Hours",
                            source_sheet=bc_sheet.name,
                            source_coord=f"B{r}:H{r}",
                        )
                    )

        return res
