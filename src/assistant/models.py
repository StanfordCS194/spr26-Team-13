"""Pydantic models for assistant intent parsing."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AssistantActionName = Literal[
    "get_pr",
    "get_recent_exercise_history",
    "log_set",
    "start_workout",
    "start_next_set",
    "start_next_exercise",
    "start_exercise",
    "add_exercise",
    "start_rest",
    "finish_workout",
    "unknown",
]


class AssistantAction(BaseModel):
    """Structured action produced by the assistant from natural language."""

    model_config = ConfigDict(extra="forbid")

    action: AssistantActionName = Field(
        description="The supported workout action inferred from the user message."
    )
    user_id: str | None = Field(
        default=None,
        description="User id supplied by the API layer or caller.",
    )
    session_id: str | None = Field(
        default=None,
        description="Workout session id supplied by the API layer or caller.",
    )
    program_id: str | None = Field(
        default=None,
        description="Optional program id when starting a workout from a program.",
    )
    exercise_name: str | None = Field(
        default=None,
        description="Exercise name when the action targets a specific movement.",
    )
    weight: float | None = Field(
        default=None,
        ge=0,
        description="Weight used for a logged set, in pounds unless the user says otherwise.",
    )
    reps: int | None = Field(
        default=None,
        ge=0,
        description="Number of repetitions for a logged set.",
    )
    sets: int | None = Field(
        default=None,
        ge=0,
        description="Number of planned sets when adding an exercise.",
    )
    duration_seconds: int | None = Field(
        default=None,
        ge=0,
        description="Duration for rest or timer actions in seconds.",
    )
    notes: str | None = Field(
        default=None,
        description="Optional user-supplied notes for a set or exercise.",
    )
    target_rpe: float | None = Field(
        default=None,
        ge=1.0,
        le=10.0,
        description="Optional target RPE for planned work.",
    )
    unit: str | None = Field(
        default=None,
        description="Weight unit such as lb or kg.",
    )
