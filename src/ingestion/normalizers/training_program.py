"""Normalize parsed ingestion data into canonical training program contracts."""

from __future__ import annotations

from difflib import get_close_matches
import re

from src.contracts import ProgramExercise, SourceType, TrainingBlock, TrainingDay, TrainingProgram, TrainingWeek
from src.ingestion.models import ParsedBlock, ParsedExercise, ParsedProgram
from src.shared.exercise_catalog import EXERCISE_CATALOG
from src.shared.validators import validate_program


def normalize_parsed_program(
    parsed_program: ParsedProgram,
    *,
    user_id: str,
    source_type: SourceType,
    program_id: str | None = None,
    title: str | None = None,
) -> TrainingProgram:
    """Convert a parsed program into the shared canonical contract."""

    alias_map = _build_alias_map()
    training_weeks: list[TrainingWeek] = []
    ambiguity_count = 0

    for parsed_week in parsed_program.weeks:
        training_days: list[TrainingDay] = []
        for day_index, parsed_day in enumerate(parsed_week.days, start=1):
            training_blocks = [
                _normalize_block(parsed_block, alias_map)
                for parsed_block in parsed_day.blocks
                if parsed_block.exercises
            ]
            if training_blocks:
                blocked_ids = {
                    id(exercise)
                    for parsed_block in parsed_day.blocks
                    for exercise in parsed_block.exercises
                }
                unblocked_exercises = [
                    _normalize_exercise(exercise, alias_map)
                    for exercise in parsed_day.exercises
                    if id(exercise) not in blocked_ids
                ]
                program_exercises = [
                    exercise
                    for block in training_blocks
                    for exercise in block.exercises
                ] + unblocked_exercises
                if unblocked_exercises:
                    training_blocks = [
                        TrainingBlock(
                            block_id="block_0",
                            title="Block 0",
                            execution_style="round_robin",
                            exercises=unblocked_exercises,
                            notes="Exercises parsed outside an explicit source block.",
                        ),
                        *training_blocks,
                    ]
                ambiguity_count += sum(
                    len(exercise.ambiguity_flags)
                    for block in training_blocks
                    for exercise in block.exercises
                )
            else:
                program_exercises = [_normalize_exercise(exercise, alias_map) for exercise in parsed_day.exercises]
                ambiguity_count += sum(len(exercise.ambiguity_flags) for exercise in program_exercises)

            training_days.append(
                TrainingDay(
                    day_id=_build_day_id(parsed_week.week_number, day_index, parsed_day.title),
                    title=parsed_day.title,
                    blocks=training_blocks,
                    exercises=program_exercises,
                    notes=parsed_day.notes,
                )
            )

        training_weeks.append(
            TrainingWeek(
                week_number=parsed_week.week_number,
                days=training_days,
            )
        )

    program = TrainingProgram(
        program_id=program_id or _slugify(title or parsed_program.title or "imported_program"),
        user_id=user_id,
        title=title or parsed_program.title or "Imported Program",
        source_type=source_type,
        weeks=training_weeks,
        parse_confidence=parsed_program.parse_confidence,
        needs_user_confirmation=(
            (ambiguity_count > 0)
            or bool(parsed_program.extraction_notes)
            or (parsed_program.parse_confidence or 0.0) < 0.9
        ),
    )
    return validate_program(program)


def _build_alias_map() -> dict[str, str]:
    alias_map: dict[str, str] = {}
    for exercise_id, details in EXERCISE_CATALOG.items():
        aliases = [details["display_name"], *details.get("aliases", [])]
        for alias in aliases:
            alias_map[_normalize_name(alias)] = exercise_id
    return alias_map


def _normalize_block(parsed_block: ParsedBlock, alias_map: dict[str, str]) -> TrainingBlock:
    return TrainingBlock(
        block_id=_slugify(parsed_block.title),
        title=parsed_block.title,
        execution_style=parsed_block.execution_style or "sequential",
        exercises=[_normalize_exercise(exercise, alias_map) for exercise in parsed_block.exercises],
        notes=parsed_block.notes,
    )


def _normalize_exercise(
    exercise: ParsedExercise,
    alias_map: dict[str, str],
) -> ProgramExercise:
    exercise_id, fuzzy_match_used = _resolve_exercise_id(exercise.raw_name, alias_map)
    ambiguity_flags = list(exercise.ambiguity_flags)

    if exercise_id is None:
        exercise_id = _slugify(exercise.raw_name)
        ambiguity_flags.append("unmapped_exercise_name")
        display_name = exercise.raw_name.strip()
    else:
        display_name = EXERCISE_CATALOG[exercise_id]["display_name"]
        if fuzzy_match_used:
            ambiguity_flags.append("fuzzy_name_match")

    return ProgramExercise(
        exercise_id=exercise_id,
        display_name=display_name,
        set_count=exercise.set_count or 1,
        rep_target=exercise.rep_target,
        load_target=exercise.load_target,
        rpe_target=exercise.rpe_target,
        rest_seconds=exercise.rest_seconds,
        notes=exercise.notes,
        ambiguity_flags=ambiguity_flags,
    )


def _resolve_exercise_id(raw_name: str, alias_map: dict[str, str]) -> tuple[str | None, bool]:
    normalized_name = _normalize_name(raw_name)
    direct_match = alias_map.get(normalized_name)
    if direct_match is not None:
        return direct_match, False

    close_matches = get_close_matches(normalized_name, list(alias_map.keys()), n=1, cutoff=0.84)
    if close_matches:
        return alias_map[close_matches[0]], True

    return None, False


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "imported_item"


def _build_day_id(week_number: int, day_index: int, title: str) -> str:
    day_slug = _slugify(title)
    return f"week-{week_number}-day-{day_index}-{day_slug}"
