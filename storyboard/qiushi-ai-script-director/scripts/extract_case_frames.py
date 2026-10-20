#!/usr/bin/env python3
"""Extract embedded screenshot images from a Qiushi shot-analysis workbook.

Use:
  python3 extract_case_frames.py <workbook.xls|workbook.xlsx> <output-dir> [--limit 6]

The script reads the workbook only. For legacy .xls files it writes a converted
copy to a temporary directory and leaves the original untouched.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DRAW = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
MAIN = "http://schemas.openxmlformats.org/drawingml/2006/main"


def rel_targets(archive: zipfile.ZipFile, path: str) -> dict[str, str]:
    """Return relationship id -> normalised package path for one .rels file."""
    try:
        root = ET.fromstring(archive.read(path))
    except KeyError:
        return {}
    base = Path(path).parent.parent
    targets = {}
    for node in root.findall(f"{{{PKG}}}Relationship"):
        target = node.attrib.get("Target", "")
        if target.startswith("/"):
            resolved = target.lstrip("/")
        else:
            resolved = os.path.normpath(str(base / target)).replace("\\", "/")
        targets[node.attrib["Id"]] = resolved
    return targets


def cell_ref(anchor: ET.Element) -> str:
    marker = anchor.find(f"{{{DRAW}}}from")
    if marker is None:
        return "unknown"
    row = marker.findtext(f"{{{DRAW}}}row")
    col = marker.findtext(f"{{{DRAW}}}col")
    try:
        number = int(col) + 1
        letters = ""
        while number:
            number, digit = divmod(number - 1, 26)
            letters = chr(65 + digit) + letters
        return f"{letters}{int(row) + 1}"
    except (TypeError, ValueError):
        return "unknown"


def drawing_images(archive: zipfile.ZipFile, drawing_path: str) -> list[tuple[str, str]]:
    rel_path = str(Path(drawing_path).parent / "_rels" / f"{Path(drawing_path).name}.rels")
    targets = rel_targets(archive, rel_path)
    root = ET.fromstring(archive.read(drawing_path))
    images = []
    for anchor in list(root):
        blip = anchor.find(f".//{{{MAIN}}}blip")
        if blip is None:
            continue
        relation_id = blip.attrib.get(f"{{{REL}}}embed")
        target = targets.get(relation_id)
        if target and target.startswith("xl/media/"):
            images.append((cell_ref(anchor), target))
    return images


def extract_xlsx(workbook: Path, output_dir: Path, limit: int) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    seen = set()
    with zipfile.ZipFile(workbook) as archive:
        book_rels = rel_targets(archive, "xl/_rels/workbook.xml.rels")
        book = ET.fromstring(archive.read("xl/workbook.xml"))
        sheets = []
        for sheet in book.findall(f".//{{{SS}}}sheet"):
            rel_id = sheet.attrib.get(f"{{{REL}}}id")
            sheets.append((sheet.attrib.get("name", "Sheet"), book_rels.get(rel_id)))

        for sheet_name, sheet_path in sheets:
            if not sheet_path or len(manifest) >= limit:
                continue
            sheet_rels = rel_targets(
                archive,
                str(Path(sheet_path).parent / "_rels" / f"{Path(sheet_path).name}.rels"),
            )
            sheet_root = ET.fromstring(archive.read(sheet_path))
            drawing = sheet_root.find(f"{{{SS}}}drawing")
            if drawing is None:
                continue
            drawing_path = sheet_rels.get(drawing.attrib.get(f"{{{REL}}}id"))
            if not drawing_path:
                continue
            for cell, media_path in drawing_images(archive, drawing_path):
                if len(manifest) >= limit:
                    break
                key = (sheet_name, cell, media_path)
                if key in seen:
                    continue
                seen.add(key)
                suffix = Path(media_path).suffix or ".png"
                target = output_dir / f"{len(manifest) + 1:02d}_{sheet_name}_{cell}{suffix}"
                target.write_bytes(archive.read(media_path))
                manifest.append({"file": str(target), "sheet": sheet_name, "cell": cell})
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def convert_legacy_xls(source: Path, temp_dir: Path) -> Path:
    candidates = [
        os.environ.get("SOFFICE_BIN"),
        shutil.which("soffice"),
    ]
    soffice = next((Path(item) for item in candidates if item and Path(item).is_file()), None)
    if soffice is None:
        raise RuntimeError("无法转换 .xls：请设置 SOFFICE_BIN 指向 LibreOffice 的 soffice 可执行文件。")
    subprocess.run(
        [str(soffice), "--headless", "--convert-to", "xlsx", "--outdir", str(temp_dir), str(source)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    converted = temp_dir / f"{source.stem}.xlsx"
    if not converted.exists():
        raise RuntimeError(".xls 转换未生成 .xlsx 文件。")
    return converted


def main() -> int:
    parser = argparse.ArgumentParser(description="提取秋拾拉片表格中的镜头截图")
    parser.add_argument("workbook", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--limit", type=int, default=6)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit 必须大于 0")
    source = args.workbook.expanduser().resolve()
    if not source.is_file():
        parser.error(f"找不到文件：{source}")
    with tempfile.TemporaryDirectory(prefix="qiushi-case-frames-") as temp:
        workbook = source
        if source.suffix.lower() == ".xls":
            workbook = convert_legacy_xls(source, Path(temp))
        if workbook.suffix.lower() != ".xlsx":
            parser.error("只支持 .xls 或 .xlsx 拉片表格")
        frames = extract_xlsx(workbook, args.output_dir.expanduser().resolve(), args.limit)
    if not frames:
        print("未从表格中找到嵌入的镜头截图。", file=sys.stderr)
        return 2
    print(json.dumps(frames, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
