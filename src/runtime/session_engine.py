"""Minimal session planning helpers for imported programs."""

from src.contracts import SessionStatus, TrainingDay, TrainingProgram, WorkoutSession


def build_planned_session(
    program: TrainingProgram,
    day_id: str,
    *,
    session_id: str | None = None,
) -> WorkoutSession:
    """Create a planned workout session for a specific training day."""

    training_day = get_training_day(program, day_id)
    return WorkoutSession(
        session_id=session_id or f"{program.program_id}:{training_day.day_id}",
        program_id=program.program_id,
        day_id=training_day.day_id,
        status=SessionStatus.PLANNED,
    )


def build_planned_sessions(program: TrainingProgram) -> list[WorkoutSession]:
    """Create one planned session per day in the program."""

    sessions: list[WorkoutSession] = []
    for week in program.weeks:
        for day in week.days:
            sessions.append(build_planned_session(program, day.day_id))
    return sessions


def get_training_day(program: TrainingProgram, day_id: str) -> TrainingDay:
    """Look up a training day by day id."""

    for week in program.weeks:
        for day in week.days:
            if day.day_id == day_id:
                return day
    raise ValueError(f"Unknown training day: {day_id}")
