"""Deterministic assistant tools for workout actions."""

from __future__ import annotations

from typing import Any

from src.assistant.mock_db import EXERCISE_ALIASES, LOGGED_SETS, PERSONAL_RECORDS, WORKOUT_STATE


def normalize_exercise_name(exercise_name: str | None) -> str | None:
    """Normalize user-facing exercise names into mock database keys."""

    if exercise_name is None:
        return None

    normalized = " ".join(exercise_name.strip().lower().split())
    return EXERCISE_ALIASES.get(normalized, normalized)


def get_pr(exercise_name: str | None) -> dict[str, Any]:
    """Return a mocked personal record for an exercise."""

    normalized_name = normalize_exercise_name(exercise_name)
    if not normalized_name:
        return {
            "ok": False,
            "status": "missing_exercise",
            "message": "Which exercise PR do you want to check?",
        }

    record = PERSONAL_RECORDS.get(normalized_name)
    if record is None:
        return {
            "ok": False,
            "status": "not_found",
            "exercise_name": normalized_name,
            "message": f"I do not have a PR saved for {normalized_name}.",
        }

    return {
        "ok": True,
        "status": "found",
        **record,
    }


def log_set(exercise_name: str | None, reps: int | None, weight: float | None) -> dict[str, Any]:
    """Log a mocked workout set in memory."""

    normalized_name = normalize_exercise_name(exercise_name)
    if not normalized_name or reps is None or weight is None:
        return {
            "ok": False,
            "status": "missing_fields",
            "message": "To log a set, I need the exercise, reps, and weight.",
        }

    logged_set = {
        "exercise_name": normalized_name,
        "reps": reps,
        "weight": weight,
    }
    LOGGED_SETS.append(logged_set)
    return {
        "ok": True,
        "status": "logged",
        **logged_set,
    }


def start_workout() -> dict[str, Any]:
    """Start a mocked workout session."""

    WORKOUT_STATE.update(
        {
            "active": True,
            "resting": False,
            "rest_duration_seconds": None,
        }
    )
    return {"ok": True, "status": "started"}


def start_exercise(exercise_name: str | None) -> dict[str, Any]:
    """Set the current mocked exercise."""

    normalized_name = normalize_exercise_name(exercise_name)
    if not normalized_name:
        return {
            "ok": False,
            "status": "missing_exercise",
            "message": "Which exercise should I start?",
        }

    WORKOUT_STATE.update(
        {
            "active": True,
            "current_exercise": normalized_name,
            "resting": False,
            "rest_duration_seconds": None,
        }
    )
    return {
        "ok": True,
        "status": "exercise_started",
        "exercise_name": normalized_name,
    }


def start_rest(duration_seconds: int | None) -> dict[str, Any]:
    """Start a mocked rest timer."""

    duration = duration_seconds or 90
    WORKOUT_STATE.update(
        {
            "resting": True,
            "rest_duration_seconds": duration,
        }
    )
    return {
        "ok": True,
        "status": "rest_started",
        "duration_seconds": duration,
    }


def finish_workout() -> dict[str, Any]:
    """Finish the mocked workout session."""

    WORKOUT_STATE.update(
        {
            "active": False,
            "current_exercise": None,
            "resting": False,
            "rest_duration_seconds": None,
        }
    )
    return {"ok": True, "status": "finished"}
