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
    "pushup": "push-ups",
    "pushups": "push-ups",
    "push up": "push-ups",
    "push ups": "push-ups",
    "push-up": "push-ups",
    "push-ups": "push-ups",
    "pullup": "pull-ups",
    "pullups": "pull-ups",
    "pull up": "pull-ups",
    "pull ups": "pull-ups",
    "pull-up": "pull-ups",
    "pull-ups": "pull-ups",
    "bodyweight squat": "bodyweight squat",
    "bodyweight squats": "bodyweight squat",
    "squat": "back squat",
    "back squat": "back squat",
    "barbell squat": "back squat",
}

LOGGED_SETS: list[dict[str, Any]] = []

EXERCISE_HISTORY: dict[str, dict[str, list[dict[str, Any]]]] = {
    "demo-user": {
        "bench press": [
            {"exercise_name": "bench press", "weight": 225, "reps": 4, "unit": "lb", "completed_at": "2026-05-01"},
            {"exercise_name": "bench press", "weight": 205, "reps": 6, "unit": "lb", "completed_at": "2026-04-24"},
        ],
        "back squat": [
            {"exercise_name": "back squat", "weight": 315, "reps": 2, "unit": "lb", "completed_at": "2026-05-02"},
            {"exercise_name": "back squat", "weight": 285, "reps": 5, "unit": "lb", "completed_at": "2026-04-25"},
        ],
    }
}

WORKOUT_SESSIONS: dict[str, dict[str, Any]] = {}


def reset_mock_state() -> None:
    """Reset mutable in-memory session data for tests and local demos."""

    LOGGED_SETS.clear()
    WORKOUT_SESSIONS.clear()
