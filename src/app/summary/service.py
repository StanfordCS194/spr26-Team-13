"""Summary generation for completed workout sessions."""

from __future__ import annotations

from src.contracts import CompletedSet, TrainingDay, WorkoutSession, WorkoutSummary


def generate_workout_summary(
    session: WorkoutSession,
    training_day: TrainingDay,
    completed_sets: list[CompletedSet],
) -> WorkoutSummary:
    """Generate a contract summary from manual or imported completed sets."""

    exercise_names = list_completed_exercise_names(training_day, completed_sets)
    total_volume = sum(
        completed_set.actual_reps * completed_set.actual_load
        for completed_set in completed_sets
        if completed_set.actual_load is not None
    )
    estimated_one_rep_max = _estimate_one_rep_max(training_day, completed_sets)
    highlights = [
        f"Completed exercises: {', '.join(exercise_names)}" if exercise_names else "No exercises completed.",
        f"Logged {len(completed_sets)} sets.",
    ]

    if total_volume:
        highlights.append(f"Total logged volume: {round(total_volume, 2)}")

    return WorkoutSummary(
        session_id=session.session_id,
        total_volume=total_volume or None,
        estimated_one_rep_max=estimated_one_rep_max,
        highlights=highlights,
    )


def list_completed_exercise_names(training_day: TrainingDay, completed_sets: list[CompletedSet]) -> list[str]:
    """Return display names for the unique exercises completed in a session."""

    exercise_lookup = {exercise.exercise_id: exercise.display_name for exercise in training_day.exercises}
    ordered_names: list[str] = []
    seen: set[str] = set()

    for completed_set in completed_sets:
        display_name = exercise_lookup.get(completed_set.exercise_id, completed_set.exercise_id.replace("_", " ").title())
        if display_name not in seen:
            seen.add(display_name)
            ordered_names.append(display_name)

    return ordered_names


def format_workout_summary(summary: WorkoutSummary) -> str:
    """Render a concise summary string for demo output."""

    return "\n".join(summary.highlights)


def _estimate_one_rep_max(
    training_day: TrainingDay,
    completed_sets: list[CompletedSet],
) -> dict[str, float]:
    exercise_lookup = {exercise.exercise_id: exercise.display_name for exercise in training_day.exercises}
    estimates: dict[str, float] = {}

    for completed_set in completed_sets:
        if completed_set.actual_load is None or completed_set.actual_reps <= 0:
            continue
        estimate = completed_set.actual_load * (1 + completed_set.actual_reps / 30)
        display_name = exercise_lookup.get(completed_set.exercise_id, completed_set.exercise_id)
        estimates[display_name] = max(estimates.get(display_name, 0.0), round(estimate, 2))

    return estimates
