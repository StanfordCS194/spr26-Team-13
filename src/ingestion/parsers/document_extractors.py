"""Docling-backed document extraction helpers for supported program sources."""

from __future__ import annotations

import csv
import io
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from docling.document_converter import DocumentConverter
from PIL import Image
from pillow_heif import register_heif_opener

from src.contracts import SourceType
from src.ingestion.models import ExtractedDocument

register_heif_opener()
Image.MAX_IMAGE_PIXELS = None


TEXT_SUFFIXES = {".txt", ".md"}
CSV_SUFFIXES = {".csv"}
XLSX_SUFFIXES = {".xlsx"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".heic", ".heif"}
DOCLING_SUFFIXES = {
    ".pdf",
    ".docx",
    ".pptx",
    ".html",
    ".csv",
    ".xlsx",
    ".md",
    *IMAGE_SUFFIXES,
}

_CONVERTER: DocumentConverter | None = None
MAX_DOCLING_IMAGE_PIXELS = 6_000_000
MAX_DOCLING_IMAGE_LONG_EDGE = 1800


def extract_document_text(
    path: str | Path,
    *,
    include_structured_data: bool = False,
) -> ExtractedDocument:
    """Extract program text from a supported file path."""

    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix in TEXT_SUFFIXES:
        return ExtractedDocument(
            text=file_path.read_text(encoding="utf-8"),
            source_type=SourceType.TEXT,
        )

    if suffix in CSV_SUFFIXES:
        return _extract_csv_text(file_path)

    if suffix in XLSX_SUFFIXES:
        return _extract_xlsx_text(file_path)

    if suffix in DOCLING_SUFFIXES:
        return _extract_with_docling(file_path, include_structured_data=include_structured_data)

    raise ValueError(f"Unsupported program source: {file_path.suffix or '<no extension>'}")


def _extract_with_docling(path: Path, *, include_structured_data: bool) -> ExtractedDocument:
    converter = _get_converter()
    source_path, cleanup_path = _prepare_docling_source(path)
    try:
        result = converter.convert(source_path)
    finally:
        if cleanup_path is not None:
            cleanup_path.unlink(missing_ok=True)

    document = result.document
    markdown = document.export_to_markdown()
    structured_data = document.export_to_dict() if include_structured_data else None
    extraction_notes = ["docling_used"]
    if path.suffix.lower() in IMAGE_SUFFIXES:
        extraction_notes.append("docling_image_parse")
    if result.errors:
        extraction_notes.append("docling_reported_errors")

    return ExtractedDocument(
        text=markdown,
        source_type=_infer_source_type(path),
        extraction_notes=extraction_notes,
        structured_markdown=markdown,
        structured_data=structured_data,
    )


def _get_converter() -> DocumentConverter:
    global _CONVERTER
    if _CONVERTER is None:
        _CONVERTER = DocumentConverter()
    return _CONVERTER


def _extract_csv_text(path: Path) -> ExtractedDocument:
    """Read CSVs directly instead of sending plain tabular text through Docling."""

    raw_text = path.read_text(encoding="utf-8-sig")
    sample = raw_text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample)
    except csv.Error:
        dialect = csv.excel

    rows = list(csv.reader(io.StringIO(raw_text), dialect))
    text = "\n".join("\t".join(cell.strip() for cell in row if cell.strip()) for row in rows)
    text = "\n".join(line for line in text.splitlines() if line.strip())

    return ExtractedDocument(
        text=text or raw_text,
        source_type=SourceType.SPREADSHEET,
        extraction_notes=["csv_direct_parse"],
        structured_markdown=text or raw_text,
    )


def _extract_xlsx_text(path: Path) -> ExtractedDocument:
    """Read workbook cell text directly for the LLM/local parser fast path."""

    try:
        with zipfile.ZipFile(path) as workbook:
            shared_strings = _read_xlsx_shared_strings(workbook)
            lines: list[str] = []
            for sheet_name in sorted(name for name in workbook.namelist() if name.startswith("xl/worksheets/sheet")):
                sheet_text = _read_xlsx_sheet_text(workbook, sheet_name, shared_strings)
                if sheet_text:
                    lines.append(sheet_text)
    except (OSError, KeyError, ET.ParseError, zipfile.BadZipFile) as exc:
        raise ValueError(f"Unsupported or unreadable spreadsheet: {path.name}") from exc

    text = "\n\n".join(lines).strip()
    if not text:
        raise ValueError(f"No readable cells found in spreadsheet: {path.name}")

    return ExtractedDocument(
        text=text,
        source_type=SourceType.SPREADSHEET,
        extraction_notes=["xlsx_direct_parse"],
        structured_markdown=text,
    )


def _read_xlsx_shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []

    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    namespace = _xml_namespace(root.tag)
    strings: list[str] = []
    for item in root.findall(f".//{namespace}si"):
        strings.append("".join(text_node.text or "" for text_node in item.findall(f".//{namespace}t")))
    return strings


def _read_xlsx_sheet_text(workbook: zipfile.ZipFile, sheet_name: str, shared_strings: list[str]) -> str:
    root = ET.fromstring(workbook.read(sheet_name))
    namespace = _xml_namespace(root.tag)
    rows: list[str] = []
    for row in root.findall(f".//{namespace}row"):
        values = [
            value
            for cell in row.findall(f"{namespace}c")
            if (value := _read_xlsx_cell_value(cell, namespace, shared_strings))
        ]
        if values:
            rows.append("\t".join(values))
    return "\n".join(rows)


def _read_xlsx_cell_value(cell: ET.Element, namespace: str, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return " ".join(text_node.text or "" for text_node in cell.findall(f".//{namespace}t")).strip()

    value_node = cell.find(f"{namespace}v")
    if value_node is None or value_node.text is None:
        return ""

    raw_value = value_node.text.strip()
    if cell_type == "s":
        try:
            return shared_strings[int(raw_value)].strip()
        except (IndexError, ValueError):
            return raw_value
    return raw_value


def _xml_namespace(tag: str) -> str:
    if tag.startswith("{"):
        return tag[: tag.index("}") + 1]
    return ""


def _prepare_docling_source(path: Path) -> tuple[Path, Path | None]:
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        return path, None

    with Image.open(path) as image:
        prepared = image.convert("RGB")
        pixel_count = prepared.width * prepared.height
        long_edge = max(prepared.width, prepared.height)
        if pixel_count > MAX_DOCLING_IMAGE_PIXELS or long_edge > MAX_DOCLING_IMAGE_LONG_EDGE:
            pixel_scale = (MAX_DOCLING_IMAGE_PIXELS / pixel_count) ** 0.5 if pixel_count > MAX_DOCLING_IMAGE_PIXELS else 1.0
            edge_scale = MAX_DOCLING_IMAGE_LONG_EDGE / long_edge if long_edge > MAX_DOCLING_IMAGE_LONG_EDGE else 1.0
            scale = min(pixel_scale, edge_scale)
            resized_dimensions = (
                max(1, int(prepared.width * scale)),
                max(1, int(prepared.height * scale)),
            )
            prepared = prepared.resize(resized_dimensions, Image.Resampling.LANCZOS)

        resized_pixel_count = prepared.width * prepared.height
        if (
            path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
            and resized_pixel_count == pixel_count
            and long_edge <= MAX_DOCLING_IMAGE_LONG_EDGE
        ):
            return path, None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg", dir="/tmp") as handle:
            temp_path = Path(handle.name)
        prepared.save(temp_path, format="JPEG", quality=82)
    return temp_path, temp_path


def _infer_source_type(path: Path) -> SourceType:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return SourceType.PDF
    if suffix in {".csv", ".xlsx"}:
        return SourceType.SPREADSHEET
    if suffix in IMAGE_SUFFIXES:
        return SourceType.IMAGE
    return SourceType.TEXT
