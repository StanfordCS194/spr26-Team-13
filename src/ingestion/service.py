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
            repaired = _repair_missing_prescriptions_from_local_parse(
                program,
                document,
                user_id=user_id,
                program_id=program_id,
                title=fallback_title,
            )
            return repaired, get_llm_provider()
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


def _repair_missing_prescriptions_from_local_parse(
    program: TrainingProgram,
    document,
    *,
    user_id: str,
    program_id: str | None,
    title: str,
) -> TrainingProgram:
    """Use the deterministic parser to fill fields the LLM left blank.

    LLM normalization preserves messy document structure better, but it can
    occasionally omit obvious reps/load/rest that the regex parser sees in the
    source text. This keeps the LLM layout and only backfills missing fields.
    """

    try:
      parsed_program = parse_program_text(
          document.text,
          fallback_title=title,
          prefer_multiline_grouping=(document.source_type == SourceType.IMAGE) or bool(document.extraction_notes),
      )
      local_program = normalize_parsed_program(
          parsed_program,
          user_id=user_id,
          source_type=document.source_type,
          program_id=program_id,
          title=title,
      )
    except Exception:
        return program

    local_exercises = _flatten_program_exercises(local_program)
    if not local_exercises:
        return program

    local_by_name: dict[str, list[ProgramExercise]] = {}
    for exercise in local_exercises:
        local_by_name.setdefault(_exercise_match_key(exercise), []).append(exercise)

    target_exercises = _flatten_program_exercises(program)
    for index, target in enumerate(target_exercises):
        if not _has_missing_prescription(target):
            continue

        local = _pop_matching_local_exercise(target, local_by_name)
        if local is None and index < len(local_exercises) and _compatible_names(target, local_exercises[index]):
            local = local_exercises[index]
        if local is None:
            continue

        _copy_missing_prescription_fields(target, local)

    return program


def _flatten_program_exercises(program: TrainingProgram) -> list[ProgramExercise]:
    exercises: list[ProgramExercise] = []
    seen: set[int] = set()
    for week in program.weeks:
        for day in week.days:
            for block in day.blocks:
                for exercise in block.exercises:
                    if id(exercise) not in seen:
                        exercises.append(exercise)
                        seen.add(id(exercise))
            for exercise in day.exercises:
                if id(exercise) not in seen:
                    exercises.append(exercise)
                    seen.add(id(exercise))
    return exercises


def _has_missing_prescription(exercise: ProgramExercise) -> bool:
    return (
        not exercise.rep_target
        or not exercise.load_target
        or exercise.rest_seconds is None
    )


def _pop_matching_local_exercise(
    target: ProgramExercise,
    local_by_name: dict[str, list[ProgramExercise]],
) -> ProgramExercise | None:
    key = _exercise_match_key(target)
    matches = local_by_name.get(key)
    if matches:
        return matches.pop(0)

    for candidate_key, candidates in local_by_name.items():
        if candidates and _compatible_name_keys(key, candidate_key):
            return candidates.pop(0)
    return None


def _copy_missing_prescription_fields(target: ProgramExercise, local: ProgramExercise) -> None:
    if target.set_count <= 1 and local.set_count > 1:
        target.set_count = local.set_count
    if not target.rep_target and local.rep_target:
        target.rep_target = local.rep_target
        _remove_ambiguity_flag(target, "missing_rep_target")
    if not target.load_target and local.load_target:
        target.load_target = local.load_target
        _remove_ambiguity_flag(target, "missing_intensity_target")
    if target.rpe_target is None and local.rpe_target is not None:
        target.rpe_target = local.rpe_target
        _remove_ambiguity_flag(target, "missing_intensity_target")
    if target.rest_seconds is None and local.rest_seconds is not None:
        target.rest_seconds = local.rest_seconds


def _remove_ambiguity_flag(exercise: ProgramExercise, flag: str) -> None:
    exercise.ambiguity_flags = [existing for existing in exercise.ambiguity_flags if existing != flag]


def _compatible_names(target: ProgramExercise, local: ProgramExercise) -> bool:
    return _compatible_name_keys(_exercise_match_key(target), _exercise_match_key(local))


def _compatible_name_keys(left: str, right: str) -> bool:
    if left == right:
        return True
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return False
    overlap = len(left_tokens & right_tokens)
    return overlap >= min(len(left_tokens), len(right_tokens), 2)


def _exercise_match_key(exercise: ProgramExercise) -> str:
    name = exercise.display_name or exercise.exercise_id
    key = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    return re.sub(r"\s+", " ", key)


def extract_program_file(path: str | Path):
    """Expose raw extracted document output for review or downstream LLM use."""

    try:
        return extract_document_text(path)
    except ValueError as exc:
        raise UnsupportedProgramSourceError(str(exc)) from exc
