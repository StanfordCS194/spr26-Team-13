"""Service layer for document ingestion into training program contracts."""

from pathlib import Path
import re

from src.contracts import ProgramExercise, SourceType, TrainingProgram

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
    program = normalize_parsed_program(
        parsed_program,
        user_id=user_id,
        source_type=source_type,
        program_id=program_id,
        title=title,
    )
    return _drop_aggregate_exercise_rows(program)


def ingest_program_file(
    path: str | Path,
    user_id: str,
    *,
    program_id: str | None = None,
    title: str | None = None,
) -> TrainingProgram:
    """Extract text from a file and normalize it into a training program."""

    try:
        document = extract_document_text(path, include_structured_data=True)
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
    program = normalize_parsed_program(
        parsed_program,
        user_id=user_id,
        source_type=document.source_type,
        program_id=program_id,
        title=title,
    )
    return _drop_empty_navigation_days(_drop_aggregate_exercise_rows(program)), "local_fallback"


def _drop_empty_navigation_days(program: TrainingProgram) -> TrainingProgram:
    """Remove empty day shells produced by app screenshots.

    Some workout app screenshots include calendar/navigation rows such as
    "Week 1 - Day 1 / 0 lifts / 0 sets" before the selected day. The parser
    should not expose those empty shells as real training days when another day
    contains the actual workout.
    """

    for week in program.weeks:
        if len(week.days) <= 1:
            continue
        non_empty_days = [day for day in week.days if _day_has_work(day)]
        if not non_empty_days or len(non_empty_days) == len(week.days):
            continue
        week.days = non_empty_days

    return program


def _day_has_work(day) -> bool:
    return any(block.exercises for block in day.blocks) or bool(day.exercises)


def _drop_aggregate_exercise_rows(program: TrainingProgram) -> TrainingProgram:
    """Remove OCR/LLM rows that glue adjacent exercise rows together."""

    for week in program.weeks:
        for day in week.days:
            for block in day.blocks:
                block.exercises = _without_aggregate_exercises(block.exercises)
            day.exercises = _without_aggregate_exercises(day.exercises)
    return program


def _without_aggregate_exercises(exercises: list[ProgramExercise]) -> list[ProgramExercise]:
    if len(exercises) < 3:
        return exercises

    kept: list[ProgramExercise] = []
    for index, exercise in enumerate(exercises):
        siblings = exercises[:index] + exercises[index + 1 :]
        if _is_aggregate_exercise(exercise, siblings):
            continue
        kept.append(exercise)
    return kept


def _is_aggregate_exercise(candidate: ProgramExercise, siblings: list[ProgramExercise]) -> bool:
    candidate_name = _exercise_match_key(candidate)
    if not candidate_name or len(candidate_name.split()) < 4:
        return False
    if not _has_weak_or_missing_prescription(candidate):
        return False

    sibling_phrases = [
        phrase
        for sibling in siblings
        for phrase in _exercise_phrase_variants(sibling)
        if phrase and phrase != candidate_name
    ]
    return _can_segment_phrase(candidate_name, sibling_phrases, min_segments=2)


def _has_weak_or_missing_prescription(exercise: ProgramExercise) -> bool:
    return (
        exercise.set_count <= 1
        and not exercise.load_target
        and exercise.rpe_target is None
        and exercise.rest_seconds is None
    )


def _exercise_phrase_variants(exercise: ProgramExercise) -> set[str]:
    name = _exercise_match_key(exercise)
    phrases = {name} if name else set()
    reps = str(exercise.rep_target or "").strip()
    if reps and re.fullmatch(r"\d{1,3}", reps):
        phrases.add(_normalize_phrase(f"{reps} {name}"))
    return phrases


def _can_segment_phrase(value: str, phrases: list[str], *, min_segments: int) -> bool:
    phrase_set = set(phrases)

    def can_segment(remaining: str, segment_count: int) -> bool:
        if not remaining:
            return segment_count >= min_segments
        for phrase in phrase_set:
            if remaining == phrase:
                return segment_count + 1 >= min_segments
            prefix = f"{phrase} "
            if remaining.startswith(prefix) and can_segment(remaining[len(prefix) :], segment_count + 1):
                return True
        return False

    return can_segment(value, 0)


def _exercise_match_key(exercise: ProgramExercise) -> str:
    name = exercise.display_name or exercise.exercise_id
    return _normalize_phrase(name)


def _normalize_phrase(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return re.sub(r"\s+", " ", key)


def extract_program_file(path: str | Path):
    """Expose raw extracted document output for review or downstream LLM use."""

    try:
        return extract_document_text(path, include_structured_data=True)
    except ValueError as exc:
        raise UnsupportedProgramSourceError(str(exc)) from exc
