#!/usr/bin/env python3
"""Validate the raw XLSX dataset using only Python stdlib.

This avoids requiring pandas/openpyxl during Phase 0 infrastructure checks.
"""
from __future__ import annotations

import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "data" / "raw" / "Car_sales.xlsx"
NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
EXPECTED_COLUMNS = [
    "Manufacturer",
    "Model",
    "Sales_in_thousands",
    "__year_resale_value",
    "Vehicle_type",
    "Price_in_thousands",
    "Engine_size",
    "Horsepower",
    "Wheelbase",
    "Width",
    "Length",
    "Curb_weight",
    "Fuel_capacity",
    "Fuel_efficiency",
    "Latest_Launch",
    "Power_perf_factor",
]


def col_to_idx(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        return 0
    value = 0
    for char in match.group(1):
        value = value * 26 + ord(char) - 64
    return value - 1


def read_rows(path: Path) -> list[list[object]]:
    with zipfile.ZipFile(path) as zf:
        shared = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall("a:si", NS):
                shared.append("".join(t.text or "" for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")))

        root = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
        rows = []
        for row in root.findall(".//a:sheetData/a:row", NS):
            row_data = {}
            max_idx = -1
            for cell in row.findall("a:c", NS):
                idx = col_to_idx(cell.attrib.get("r", "A1"))
                typ = cell.attrib.get("t")
                value_node = cell.find("a:v", NS)
                value = None
                if typ == "s" and value_node is not None:
                    value = shared[int(value_node.text)]
                elif value_node is not None:
                    text = value_node.text
                    try:
                        value = float(text)
                        if value.is_integer():
                            value = int(value)
                    except Exception:
                        value = text
                row_data[idx] = value
                max_idx = max(max_idx, idx)
            if max_idx >= 0:
                rows.append([row_data.get(i) for i in range(max_idx + 1)])
        width = max(len(row) for row in rows)
        return [row + [None] * (width - len(row)) for row in rows]


def main() -> int:
    if not XLSX.exists():
        print(f"ERROR: missing dataset: {XLSX}")
        return 1
    rows = read_rows(XLSX)
    header = [str(value) for value in rows[0]]
    data_rows = rows[1:]

    if header != EXPECTED_COLUMNS:
        print("ERROR: unexpected columns")
        print(header)
        return 1
    if len(data_rows) != 157:
        print(f"ERROR: expected 157 data rows, got {len(data_rows)}")
        return 1

    print("Dataset validation OK")
    print(f"Rows: {len(data_rows)}")
    print(f"Columns: {len(header)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
