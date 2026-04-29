"""Docling-backed document extraction helpers for supported program sources."""

from __future__ import annotations

from pathlib import Path
import tempfile

from docling.document_converter import DocumentConverter
from PIL import Image
from pillow_heif import register_heif_opener

from src.contracts import SourceType
from src.ingestion.models import ExtractedDocument

register_heif_opener()
Image.MAX_IMAGE_PIXELS = None


TEXT_SUFFIXES = {".txt", ".md"}
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
MAX_DOCLING_IMAGE_PIXELS = 12_000_000
MAX_DOCLING_IMAGE_LONG_EDGE = 2400


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
        prepared.save(temp_path, format="JPEG", quality=88, optimize=True)
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
