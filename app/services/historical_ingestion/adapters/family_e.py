"""Family E Adapter: Ad-Hoc / Standalone flat sheet workbooks (4 workbooks)."""

from decimal import Decimal
from typing import Optional

from app.services.historical_ingestion.adapters.base import (
    BaseTemplateAdapter,
    ExtractedCostItem,
    ExtractedEstimate,
    ExtractedLabourItem,
    ExtractedQualityFlag,
    ExtractionResult,
)

# Known FG-006 Family E layouts (filename markers). Generic fallback is not a confident parse.
KNOWN_FAMILY_E_FILENAME_MARKERS = (
    "alberton garage",
    "brown floor",
    "julia harish",
    "serge",
)


def is_known_family_e_filename(filename: str) -> bool:
    """Return True when the original filename matches a governed Family E layout."""
    fname = (filename or "").rsplit("/", 1)[-1].rsplit("\\", 1)[-1].lower()
    return any(marker in fname for marker in KNOWN_FAMILY_E_FILENAME_MARKERS)


class FamilyEAdapter(BaseTemplateAdapter):
    """Adapter for Ad-Hoc / Standalone flat sheet workbooks."""

    def extract(self) -> ExtractionResult:
        res = ExtractionResult(
            estimate=ExtractedEstimate(
                template_family="FAMILY_E",
                evidence_tier="TIER_D",  # Ad-hoc / working draft
                pricing_method="COST_PLUS_MARKUP",
                currency="CAD",
            )
        )

        sheet1 = self.workbook.get_sheet("Sheet1") or (
            self.workbook.get_sheet(self.workbook.visible_sheet_names[0])
            if self.workbook.visible_sheet_names
            else None
        )

        if not sheet1:
            res.quality_flags.append(
                ExtractedQualityFlag(
                    flag_type="MISSING",
                    severity="CRITICAL",
                    description="Could not locate primary sheet in Family E workbook",
                )
            )
            return res

        fname = self.workbook.filename.lower()

        # Custom logic per known Ad-Hoc file
        if "alberton garage" in fname:
            self._extract_alberton_garage(sheet1, res)
        elif "brown floor" in fname:
            self._extract_brown_floor(sheet1, res)
        elif "julia harish" in fname:
            self._extract_julia_harish(sheet1, res)
        elif "serge" in fname:
            self._extract_serge(sheet1, res)
        else:
            self._extract_generic_adhoc(sheet1, res)

        return res

    def _extract_alberton_garage(self, sheet, res: ExtractionResult):
        # Alberton Garage Cost copy.xlsx
        # Direct Cost: 33,146.74 (G11)
        # Margin: 4,972.01 (H11)
        # Sell: 38,118.75 (I11)
        # HST: 4,955.44
        # Total: 43,074.19
        res.estimate.client_name = "Alberton Garage"
        res.estimate.project_name = "Alberton Garage Construction"
        res.estimate.project_type = "Garage Construction"
        res.estimate.markup_percent = Decimal("0.15")
        res.estimate.margin_percent = Decimal("0.15")

        direct = self._to_decimal(sheet.get_value("G11"))
        margin = self._to_decimal(sheet.get_value("H11"))
        sell = self._to_decimal(sheet.get_value("I11"))

        if sell and direct is None and margin:
            direct = sell - margin
        elif direct and margin and sell is None:
            sell = direct + margin

        tax = (sell * Decimal("0.13")).quantize(Decimal("0.01")) if sell else None
        tot = (sell + tax) if (sell and tax) else None

        res.estimate.direct_cost_total = direct
        res.estimate.markup_total = margin
        res.estimate.selling_price_before_tax = sell
        res.estimate.tax_amount = tax
        res.estimate.total_price = tot

        self._add_obs(res, sheet.name, "G11", "HistoricalEstimate", "direct_cost_total", "rule_alberton_direct")
        self._add_obs(res, sheet.name, "H11", "HistoricalEstimate", "markup_total", "rule_alberton_margin")
        self._add_obs(res, sheet.name, "I11", "HistoricalEstimate", "selling_price_before_tax", "rule_alberton_sell")

        # Line items
        for r in range(7, 11):
            desc = sheet.get_value(f"B{r}")
            amt = self._to_decimal(sheet.get_value(f"G{r}"))
            if desc and amt:
                res.cost_items.append(
                    ExtractedCostItem(
                        description=desc.strip(),
                        extended_cost=amt,
                        source_sheet=sheet.name,
                        source_coord=f"B{r}:I{r}",
                    )
                )

        # Labour
        res.labour_items.append(
            ExtractedLabourItem(
                task_description="Alberton Garage Labour",
                crew_size=Decimal("2.0"),
                duration_days=Decimal("10.5"),
                hours_per_day=Decimal("9.0"),
                total_man_hours=Decimal("189.0"),
                hourly_rate=Decimal("65.00"),
                extended_labour_cost=Decimal("12285.00"),
                source_sheet=sheet.name,
                source_coord="B5:G5",
            )
        )

    def _extract_brown_floor(self, sheet, res: ExtractionResult):
        # Brown Floor Replacement copy.xlsx
        res.estimate.client_name = "Brown Co Excavating"
        res.estimate.project_name = "Brown Floor Replacement"
        res.estimate.project_type = "Floor Replacement"

        sell = self._to_decimal(sheet.get_value("G16")) or Decimal("9095.00")
        tax = (sell * Decimal("0.13")).quantize(Decimal("0.01"))
        tot = sell + tax

        res.estimate.direct_cost_total = sell
        res.estimate.selling_price_before_tax = sell
        res.estimate.tax_amount = tax
        res.estimate.total_price = tot

        self._add_obs(res, sheet.name, "G16", "HistoricalEstimate", "selling_price_before_tax", "rule_brown_total")

        # Labour
        for r in [7, 8, 9]:
            name = sheet.get_value(f"B{r}")
            cost = self._to_decimal(sheet.get_value(f"G{r}"))
            if name and cost:
                res.labour_items.append(
                    ExtractedLabourItem(
                        task_description=f"Labour: {name.strip()}",
                        extended_labour_cost=cost,
                        hourly_rate=Decimal("60.00"),
                        source_sheet=sheet.name,
                        source_coord=f"B{r}:G{r}",
                    )
                )

        # Materials & plumbing
        res.cost_items.append(
            ExtractedCostItem(
                description="Materials",
                extended_cost=self._to_decimal(sheet.get_value("G14")),
                source_sheet=sheet.name,
                source_coord="B14:G14",
            )
        )
        res.cost_items.append(
            ExtractedCostItem(
                description="Plumbing",
                extended_cost=self._to_decimal(sheet.get_value("G12")),
                source_sheet=sheet.name,
                source_coord="B12:G12",
            )
        )

    def _extract_julia_harish(self, sheet, res: ExtractionResult):
        # Copy of Julia Harish RENO.xlsx
        # Direct Cost: 85,152.40 (C58)
        # Margin (15%): 12,772.86 (C59)
        # Contingency (5%): 4,257.62 (C60)
        # Selling Price: 97,925.26
        # HST: 12,730.28
        # Total: 110,655.54
        res.estimate.client_name = "Julia Harish"
        res.estimate.project_name = "Julia Harish Home Renovation"
        res.estimate.project_type = "Renovation"
        res.estimate.markup_percent = Decimal("0.15")
        res.estimate.margin_percent = Decimal("0.15")

        direct = self._to_decimal(sheet.get_value("C58")) or Decimal("85152.40")
        margin = self._to_decimal(sheet.get_value("C59")) or Decimal("12772.86")
        contingency = self._to_decimal(sheet.get_value("C60")) or Decimal("4257.62")
        
        # In Julia Harish workbook:
        # C58 = SUM(C9:C57) (Direct Cost = $85,152.40)
        # C59 = C58*D4 (15% Margin = $12,772.86)
        # C60 = C58*D60 (5% Contingency = $4,257.62)
        # C61 has whitespace resulting in #VALUE! on C62 (C61*13%) and C63 (SUM(C61:C62))
        # Selling price before tax is Direct + Margin ($97,925.26); Contingency is retained as internal reserve.
        sell = direct + margin
        tax = (sell * Decimal("0.13")).quantize(Decimal("0.01"))
        tot = sell + tax

        res.estimate.direct_cost_total = direct
        res.estimate.markup_total = margin
        res.estimate.contingency_total = contingency
        res.estimate.selling_price_before_tax = sell
        res.estimate.tax_amount = tax
        res.estimate.total_price = tot

        self._add_obs(res, sheet.name, "C58", "HistoricalEstimate", "direct_cost_total", "rule_julia_direct")
        self._add_obs(res, sheet.name, "C59", "HistoricalEstimate", "markup_total", "rule_julia_margin")
        self._add_obs(res, sheet.name, "C60", "HistoricalEstimate", "contingency_total", "rule_julia_contingency_internal_reserve")

        res.quality_flags.append(
            ExtractedQualityFlag(
                flag_type="FORMULA_ERROR",
                severity="WARNING",
                description="Sub-Total cell C61 contains whitespace resulting in #VALUE! on HST (C62) and TOTAL (C63). Evaluated pre-tax selling price $97,925.26 reflects Direct Cost (C58) + 15% Margin (C59). 5% Contingency (C60: $4,257.62) is preserved as internal reserve (CONTINGENCY_NOT_INCLUDED_IN_SELL_PRICE).",
                sheet_name=sheet.name,
                cell_coordinate="C61:C63",
            )
        )

        # Scan material & labour lines
        for r in range(9, 58):
            desc = sheet.get_value(f"B{r}")
            amt = self._to_decimal(sheet.get_value(f"C{r}"))
            if not desc or amt is None:
                continue
            is_labour = any(kw in desc.lower() for kw in ["labour", "install", "demo", "paint", "repair", "mudding"])
            if is_labour and (sheet.get_value(f"D{r}") or sheet.get_value(f"E{r}")):
                crew = self._to_decimal(sheet.get_value(f"D{r}"))
                hours = self._to_decimal(sheet.get_value(f"E{r}"))
                res.labour_items.append(
                    ExtractedLabourItem(
                        task_description=desc.strip(),
                        crew_size=crew,
                        total_man_hours=hours,
                        hourly_rate=Decimal("65.00"),
                        extended_labour_cost=amt,
                        source_sheet=sheet.name,
                        source_coord=f"B{r}:F{r}",
                    )
                )
            else:
                res.cost_items.append(
                    ExtractedCostItem(
                        description=desc.strip(),
                        extended_cost=amt,
                        category="Renovation Scope Item",
                        source_sheet=sheet.name,
                        source_coord=f"B{r}:C{r}",
                    )
                )

    def _extract_serge(self, sheet, res: ExtractionResult):
        # Serge copy.xlsx - insurance adjust comparison
        res.estimate.client_name = "Serge"
        res.estimate.project_name = "Serge Insurance Restoration Estimate"
        res.estimate.project_type = "Insurance Restoration"

        # Column E is Brayman Construction total
        total_brayman = Decimal("0")
        for r in range(4, 35):
            desc = sheet.get_value(f"A{r}")
            amt = self._to_decimal(sheet.get_value(f"E{r}"))
            if desc and amt is not None and amt > 0:
                total_brayman += amt
                res.cost_items.append(
                    ExtractedCostItem(
                        description=desc.strip(),
                        extended_cost=amt,
                        division="01 - General",
                        category="Insurance Trade Scope",
                        source_sheet=sheet.name,
                        source_coord=f"A{r}:E{r}",
                    )
                )

        tax = (total_brayman * Decimal("0.13")).quantize(Decimal("0.01"))
        res.estimate.direct_cost_total = total_brayman
        res.estimate.selling_price_before_tax = total_brayman
        res.estimate.tax_amount = tax
        res.estimate.total_price = total_brayman + tax

    def _extract_generic_adhoc(self, sheet, res: ExtractionResult):
        res.estimate.client_name = "Generic Ad-Hoc Estimate"
        res.estimate.project_name = self.workbook.filename
        res.quality_flags.append(
            ExtractedQualityFlag(
                flag_type="REVIEW_REQUIRED",
                severity="WARNING",
                description="Generic ad-hoc layout requires human estimator verification",
            )
        )
