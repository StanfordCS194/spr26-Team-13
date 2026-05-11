"""Deterministic assistant tools for workout actions."""

from __future__ import annotations

from typing import Any

from src.assistant.backend import DEFAULT_USER_ID, get_backend, normalize_exercise_name
from src.assistant.mock_db import EXERCISE_ALIASES


def get_pr(user_id: str | None, exercise_name: str | None) -> dict[str, Any]:
    """Return a personal record for an exercise."""

    normalized_name = normalize_exercise_name(exercise_name)
    if not normalized_name:
        return {
            "ok": False,
            "status": "missing_exercise",
            "message": "Which exercise PR do you want to check?",
        }
    return get_backend().get_pr(user_id or DEFAULT_USER_ID, normalized_name)


def get_recent_exercise_history(
    user_id: str | None,
    exercise_name: str | None,
    *,
    limit: int = 5,
) -> dict[str, Any]:
    """Return recent set history for an exercise."""

    normalized_name = normalize_exercise_name(exercise_name)
    if not normalized_name:
        return {
            "ok": False,
            "status": "missing_exercise",
            "message": "Which exercise history do you want to check?",
        }
    return get_backend().get_recent_exercise_history(user_id or DEFAULT_USER_ID, normalized_name, limit=limit)


def log_set(
    user_id: str | None,
    session_id: str | None,
    exercise_name: str | None,
    reps: int | None,
    weight: float | None,
    *,
    unit: str | None = None,
    notes: str | None = None,
    target_rpe: float | None = None,
) -> dict[str, Any]:
    """Log a completed workout set."""

    normalized_name = normalize_exercise_name(exercise_name)
    if not normalized_name or reps is None:
        return {
            "ok": False,
            "status": "missing_fields",
            "message": "To log a set, I need the exercise and reps.",
        }
    return get_backend().log_set(
        user_id or DEFAULT_USER_ID,
        session_id,
        normalized_name,
        reps,
        weight,
        unit=unit,
        notes=notes,
        target_rpe=target_rpe,
    )


def start_workout(user_id: str | None, program_id: str | None = None) -> dict[str, Any]:
    """Start a workout session."""

    return get_backend().start_workout(user_id or DEFAULT_USER_ID, program_id=program_id)


def start_next_set(user_id: str | None, session_id: str | None) -> dict[str, Any]:
    """Advance to the next set in the active session."""

    if not session_id:
        return {
            "ok": False,
            "status": "missing_session",
            "message": "I need an active session before I can start the next set.",
        }
    return get_backend().start_next_set(user_id or DEFAULT_USER_ID, session_id)


def start_next_exercise(user_id: str | None, session_id: str | None) -> dict[str, Any]:
    """Advance to the next exercise in the active session."""

    if not session_id:
        return {
            "ok": False,
            "status": "missing_session",
            "message": "I need an active session before I can start the next exercise.",
        }
    return get_backend().start_next_exercise(user_id or DEFAULT_USER_ID, session_id)


def start_exercise(user_id: str | None, session_id: str | None, exercise_name: str | None) -> dict[str, Any]:
    """Set the current exercise."""

    normalized_name = normalize_exercise_name(exercise_name)
    if not normalized_name:
        return {
            "ok": False,
            "status": "missing_exercise",
            "message": "Which exercise should I start?",
        }
    return get_backend().start_exercise(user_id or DEFAULT_USER_ID, session_id, normalized_name)


def add_exercise(
    user_id: str | None,
    session_id: str | None,
    exercise_name: str | None,
    *,
    sets: int | None = None,
    reps: int | None = None,
    weight: float | None = None,
    unit: str | None = None,
    notes: str | None = None,
    target_rpe: float | None = None,
) -> dict[str, Any]:
    """Add an exercise to the current workout session."""

    normalized_name = normalize_exercise_name(exercise_name)
    if not normalized_name:
        return {
            "ok": False,
            "status": "missing_exercise",
            "message": "Which exercise should I add?",
        }
    return get_backend().add_exercise(
        user_id or DEFAULT_USER_ID,
        session_id,
        normalized_name,
        sets=sets,
        reps=reps,
        weight=weight,
        unit=unit,
        notes=notes,
        target_rpe=target_rpe,
    )


def start_rest(user_id: str | None, session_id: str | None, duration_seconds: int | None) -> dict[str, Any]:
    """Start a rest timer."""

    return get_backend().start_rest(user_id or DEFAULT_USER_ID, session_id, duration_seconds)


def finish_workout(user_id: str | None, session_id: str | None) -> dict[str, Any]:
    """Finish the workout session."""

    return get_backend().finish_workout(user_id or DEFAULT_USER_ID, session_id)


def get_active_exercise_name(user_id: str | None, session_id: str | None) -> str | None:
    """Return the active exercise for context-dependent commands."""

    return get_backend().get_active_exercise_name(user_id or DEFAULT_USER_ID, session_id)


def get_display_state(session_id: str | None) -> dict[str, Any] | None:
    """Return the current display state as JSON-ready data."""

    display_state = get_backend().get_display_state(session_id)
    return display_state.model_dump(mode="json") if display_state else None
