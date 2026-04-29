"""Service layer for document ingestion into training program contracts."""

from pathlib import Path

from src.contracts import SourceType, TrainingProgram

from .llm_normalizer import get_llm_provider, llm_normalization_available, normalize_document_with_llm
from .models import ParsedProgram
from .normalizers.training_program import normalize_parsed_program
from .parsers.document_extractors import extract_document_text
from .parsers.program_text import parse_program_text


class UnsupportedProgramSourceError(ValueError):
    """Raised when a program source file cannot be handled."""


def ingest_program_text(
    text: str,
    user_id: str,
    *,
    program_id: str | None = None,
    title: str | None = None,
    source_type: SourceType = SourceType.TEXT,
) -> TrainingProgram:
    """Parse free-form workout text into a canonical training program."""

    parsed_program = parse_program_text(
        text,
        fallback_title=title,
        prefer_multiline_grouping=(source_type == SourceType.IMAGE),
    )
    return normalize_parsed_program(
        parsed_program,
        user_id=user_id,
        source_type=source_type,
        program_id=program_id,
        title=title,
    )


def ingest_program_file(
    path: str | Path,
    user_id: str,
    *,
    program_id: str | None = None,
    title: str | None = None,
) -> TrainingProgram:
    """Extract text from a file and normalize it into a training program."""

    try:
        document = extract_document_text(path)
    except ValueError as exc:
        raise UnsupportedProgramSourceError(str(exc)) from exc

    fallback_title = title or Path(path).stem.replace("_", " ").replace("-", " ").title()
    program, _ = normalize_extracted_program(
        document,
        user_id=user_id,
        program_id=program_id,
        title=fallback_title,
    )
    return program


def normalize_extracted_program(
    document,
    *,
    user_id: str,
    program_id: str | None = None,
    title: str | None = None,
) -> tuple[TrainingProgram, str]:
    """Normalize an extracted document, preferring LLM normalization when configured."""

    fallback_title = title or "Imported Program"

    if llm_normalization_available():
        try:
            program = normalize_document_with_llm(
                document,
                user_id=user_id,
                program_id=program_id,
                title=fallback_title,
            )
            return program, get_llm_provider()
        except Exception:
            pass

    parsed_program: ParsedProgram = parse_program_text(
        document.text,
        fallback_title=title or "Imported Program",
        prefer_multiline_grouping=(document.source_type == SourceType.IMAGE) or bool(document.extraction_notes),
    )
    parsed_program.extraction_notes.extend(document.extraction_notes)
    return (
        normalize_parsed_program(
            parsed_program,
            user_id=user_id,
            source_type=document.source_type,
            program_id=program_id,
            title=title,
        ),
        "local_fallback",
    )


def extract_program_file(path: str | Path):
    """Expose raw extracted document output for review or downstream LLM use."""

    try:
        return extract_document_text(path)
    except ValueError as exc:
        raise UnsupportedProgramSourceError(str(exc)) from exc
