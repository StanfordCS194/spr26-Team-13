"""Deterministic assistant tools for workout actions."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.assistant.mock_db import EXERCISE_ALIASES, LOGGED_SETS, PERSONAL_RECORDS, WORKOUT_STATE


_tracker_cache: dict[str, object] = {}


def _get_tracker():
    """Return a cached ExcelTracker instance, parsing the file only once per process."""
    from src.app.excel_tracker import ExcelTracker

    path = os.getenv("PROGRAM_XLSX_PATH") or str(Path("programs/Phase3.xlsx"))
    if not Path(path).exists():
        return None
    if path not in _tracker_cache:
        try:
            _tracker_cache[path] = ExcelTracker(path)
        except Exception:
            return None
    return _tracker_cache[path]


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


def read_program_workout(week: int | None, day: int | None) -> dict[str, Any]:
    """Return prescribed exercises from the Excel program for a given week/day."""
    from src.app.excel_tracker import format_workout_summary

    tracker = _get_tracker()
    if tracker is None:
        return {"ok": False, "status": "no_program_file", "message": "No program spreadsheet found."}

    w = week or 1
    d = day or 1
    exercises = tracker.get_workout(w, d)
    if not exercises:
        return {
            "ok": False,
            "status": "not_found",
            "message": f"No exercises found for week {w} day {d}.",
        }
    return {
        "ok": True,
        "status": "found",
        "week": w,
        "day": d,
        "day_label": exercises[0].day_label,
        "exercises": [
            {
                "name": ex.exercise_name,
                "sets": ex.working_sets,
                "reps": ex.prescribed_reps,
                "load": ex.prescribed_load,
                "rpe": ex.rpe,
                "rest": ex.rest,
            }
            for ex in exercises
        ],
        "message": format_workout_summary(exercises),
    }


def query_program_history(exercise_name: str | None) -> dict[str, Any]:
    """Look up past loads for an exercise across all weeks in the Excel program."""
    from src.app.excel_tracker import format_history_summary

    if not exercise_name:
        return {"ok": False, "status": "missing_exercise", "message": "Which exercise should I look up?"}

    tracker = _get_tracker()
    if tracker is None:
        return {"ok": False, "status": "no_program_file", "message": "No program spreadsheet found."}

    rows = tracker.query_history(exercise_name)
    if not rows:
        return {
            "ok": False,
            "status": "not_found",
            "message": f"I couldn't find {exercise_name} in your program.",
        }
    return {
        "ok": True,
        "status": "found",
        "exercise_name": exercise_name,
        "entries": [
            {"week": r.week, "day_label": r.day_label, "load": r.prescribed_load, "date": r.logged_date}
            for r in rows
        ],
        "message": format_history_summary(rows, exercise_name),
    }


def log_set_to_program(
    week: int | None,
    day: int | None,
    exercise_name: str | None,
    actual_load: float | str | None,
    comment: str | None = None,
) -> dict[str, Any]:
    """Write a completed set back into the Excel spreadsheet."""
    from datetime import date as date_type

    if not exercise_name or actual_load is None:
        return {"ok": False, "status": "missing_fields", "message": "Need exercise name and load to log."}

    tracker = _get_tracker()
    if tracker is None:
        return {"ok": False, "status": "no_program_file", "message": "No program spreadsheet found."}

    w = week or 1
    d = day or 1
    success = tracker.log_set(w, d, exercise_name, actual_load, comment=comment, log_date=date_type.today())
    if not success:
        return {
            "ok": False,
            "status": "not_found",
            "message": f"Couldn't find {exercise_name} in week {w} day {d}.",
        }
    return {
        "ok": True,
        "status": "logged",
        "exercise_name": exercise_name,
        "load": actual_load,
        "week": w,
        "day": d,
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
