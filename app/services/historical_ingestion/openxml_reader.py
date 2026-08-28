"""Pure-Python deterministic OpenXML reader for Excel workbooks (.xlsx and .xlsm).

Reads spreadsheet XML directly without executing macros or VBA code.
"""

from dataclasses import dataclass, field
import hashlib
import os
from typing import Any, Dict, List, Optional, Set, Tuple
import xml.etree.ElementTree as ET
import zipfile

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

NS_MAP = {
    "main": MAIN_NS,
    "rel": REL_NS,
}


@dataclass
class CellData:
    coordinate: str
    raw_value: Optional[str] = None
    raw_formula: Optional[str] = None
    display_value: Optional[str] = None
    data_type: Optional[str] = None

    @property
    def as_float(self) -> Optional[float]:
        val = self.display_value or self.raw_value
        if val is None:
            return None
        try:
            return float(str(val).replace(",", "").strip())
        except (ValueError, TypeError):
            return None


@dataclass
class SheetData:
    name: str
    state: str  # 'visible', 'hidden', 'veryHidden'
    sheet_id: str
    target_path: str
    cells: Dict[str, CellData] = field(default_factory=dict)

    @property
    def is_visible(self) -> bool:
        return self.state not in ("hidden", "veryHidden")

    def get_cell(self, coordinate: str) -> Optional[CellData]:
        return self.cells.get(coordinate.upper())

    def get_value(self, coordinate: str) -> Optional[str]:
        c = self.get_cell(coordinate)
        return c.display_value if c else None

    def get_float(self, coordinate: str) -> Optional[float]:
        c = self.get_cell(coordinate)
        return c.as_float if c else None


@dataclass
class WorkbookData:
    filename: str
    byte_size: int
    sha256: str
    sheets: Dict[str, SheetData] = field(default_factory=dict)
    visible_sheet_names: List[str] = field(default_factory=list)
    hidden_sheet_names: List[str] = field(default_factory=list)
    has_macros: bool = False
    ref_error_count: int = 0
    raw_sheet_count: int = 0

    def get_sheet(self, name: str) -> Optional[SheetData]:
        return self.sheets.get(name)


def read_openxml_workbook(file_path: str) -> WorkbookData:
    """Deterministically read an OpenXML .xlsx or .xlsm file without executing code."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Source workbook not found at: {file_path}")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    sha256 = hashlib.sha256(file_bytes).hexdigest()
    byte_size = len(file_bytes)
    filename = os.path.basename(file_path)
    has_macros = filename.lower().endswith(".xlsm")

    with zipfile.ZipFile(file_path, "r") as z:
        # 1. Read shared strings if present
        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            sst_xml = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in sst_xml.findall(".//main:si", NS_MAP):
                texts = [t.text or "" for t in si.findall(".//main:t", NS_MAP)]
                shared_strings.append("".join(texts))

        # 2. Map workbook relationships to find sheet XML target paths
        rid_target_map: Dict[str, str] = {}
        if "xl/_rels/workbook.xml.rels" in z.namelist():
            rels_xml = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
            for r in rels_xml.findall(".//rel:Relationship", NS_MAP):
                rid = r.attrib.get("Id")
                target = r.attrib.get("Target")
                if rid and target:
                    rid_target_map[rid] = target

        # 3. Read workbook.xml to identify all sheets and visibility
        if "xl/workbook.xml" not in z.namelist():
            raise ValueError(f"Invalid OpenXML workbook: missing xl/workbook.xml in {filename}")

        wb_xml = ET.fromstring(z.read("xl/workbook.xml"))
        sheets_dict: Dict[str, SheetData] = {}
        visible_names: List[str] = []
        hidden_names: List[str] = []

        for s in wb_xml.findall(".//main:sheet", NS_MAP):
            name = s.attrib.get("name", "")
            state = s.attrib.get("state", "visible")
            sheet_id = s.attrib.get("sheetId", "")
            r_id = s.attrib.get(f"{{{OFFICE_REL_NS}}}id") or s.attrib.get("id")

            target_rel = rid_target_map.get(r_id, f"worksheets/sheet{sheet_id}.xml")
            if not target_rel.startswith("xl/"):
                target_path = f"xl/{target_rel}"
            else:
                target_path = target_rel

            sheet_data = SheetData(
                name=name,
                state=state,
                sheet_id=sheet_id,
                target_path=target_path,
            )
            sheets_dict[name] = sheet_data

            if sheet_data.is_visible:
                visible_names.append(name)
            else:
                hidden_names.append(name)

        # 4. Parse cells for each sheet
        total_ref_errors = 0
        for name, sdata in sheets_dict.items():
            if sdata.target_path in z.namelist():
                sheet_xml = ET.fromstring(z.read(sdata.target_path))
                for c in sheet_xml.findall(".//main:c", NS_MAP):
                    coord = c.attrib.get("r", "").upper()
                    t = c.attrib.get("t")
                    f_elem = c.find("main:f", NS_MAP)
                    v_elem = c.find("main:v", NS_MAP)

                    formula = f_elem.text if f_elem is not None else None
                    val = v_elem.text if v_elem is not None else None

                    if t == "s" and val is not None:
                        try:
                            s_idx = int(val)
                            display_val = shared_strings[s_idx] if s_idx < len(shared_strings) else val
                        except ValueError:
                            display_val = val
                    elif t == "b" and val is not None:
                        display_val = "TRUE" if val == "1" else "FALSE"
                    elif t == "e":
                        display_val = val or "#ERROR!"
                        if val == "#REF!":
                            total_ref_errors += 1
                    else:
                        display_val = val

                    sdata.cells[coord] = CellData(
                        coordinate=coord,
                        raw_value=val,
                        raw_formula=formula,
                        display_value=display_val,
                        data_type=t or "n",
                    )

        return WorkbookData(
            filename=filename,
            byte_size=byte_size,
            sha256=sha256,
            sheets=sheets_dict,
            visible_sheet_names=visible_names,
            hidden_sheet_names=hidden_names,
            has_macros=has_macros,
            ref_error_count=total_ref_errors,
            raw_sheet_count=len(sheets_dict),
        )
