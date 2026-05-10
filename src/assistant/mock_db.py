"""In-memory workout data for assistant MVP development.

This module intentionally keeps data as simple dictionaries so it can be
replaced by Supabase queries later without changing the assistant service API.
"""

from __future__ import annotations

from typing import Any


PERSONAL_RECORDS: dict[str, dict[str, Any]] = {
    "bench press": {
        "exercise_name": "bench press",
        "display_name": "Bench Press",
        "weight": 225,
        "reps": 4,
    },
    "back squat": {
        "exercise_name": "back squat",
        "display_name": "Back Squat",
        "weight": 315,
        "reps": 2,
    },
}

EXERCISE_ALIASES: dict[str, str] = {
    "bench": "bench press",
    "bench press": "bench press",
    "barbell bench": "bench press",
    "squat": "back squat",
    "back squat": "back squat",
    "barbell squat": "back squat",
}

LOGGED_SETS: list[dict[str, Any]] = []

WORKOUT_STATE: dict[str, Any] = {
    "active": False,
    "current_exercise": None,
    "resting": False,
    "rest_duration_seconds": None,
}
