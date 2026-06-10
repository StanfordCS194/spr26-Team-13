"""Pydantic models for assistant intent parsing."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AssistantActionName = Literal[
    "get_pr",
    "search_history",
    "query_history",
    "get_progression",
    "log_set",
    "build_workout",
    "start_workout",
    "start_exercise",
    "start_rest",
    "advance_set",
    "skip_exercise",
    "finish_exercise",
    "query_workout",
    "finish_workout",
    "unknown",
]


class AssistantAction(BaseModel):
    """Structured action produced by the assistant from natural language."""

    model_config = ConfigDict(extra="forbid")

    action: AssistantActionName = Field(
        description="The supported workout action inferred from the user message."
    )
    exercise_name: str | None = Field(
        default=None,
        description="Exercise name when the action targets a specific movement.",
    )
    program_name: str | None = Field(
        default=None,
        description="Saved workout or program name when the action targets a specific program.",
    )
    day_name: str | None = Field(
        default=None,
        description="Program day name when the action targets a specific day.",
    )
    day_number: int | None = Field(
        default=None,
        ge=1,
        description="Program day number when the user asks for day 1, day 2, etc.",
    )
    week_number: int | None = Field(
        default=None,
        ge=1,
        description="Program week number when the user asks for a specific week.",
    )
    weight: float | None = Field(
        default=None,
        ge=0,
        description="Weight used for a logged set, in pounds unless the user says otherwise.",
    )
    reps: int | None = Field(
        default=None,
        ge=0,
        description="Number of repetitions for a logged set or requested rep-specific record.",
    )
    duration_seconds: int | None = Field(
        default=None,
        ge=0,
        description="Duration for rest or timer actions in seconds.",
    )
    date_range: str | None = Field(
        default=None,
        description="Requested history range such as last_week, recent, or last_session.",
    )
    history_metric: Literal["max_weight", "max_reps", "max_volume", "last_time", "recent_sets"] | None = Field(
        default=None,
        description="Metric to compute for query_history requests.",
    )
    min_weight: float | None = Field(
        default=None,
        ge=0,
        description="Minimum load filter for history queries.",
    )
    max_weight: float | None = Field(
        default=None,
        ge=0,
        description="Maximum load filter for history queries.",
    )
    min_reps: int | None = Field(
        default=None,
        ge=0,
        description="Minimum reps filter for history queries.",
    )
    max_reps: int | None = Field(
        default=None,
        ge=0,
        description="Maximum reps filter for history queries.",
    )
    workout_query_type: Literal["current_exercise", "next_exercise", "last_set", "progress"] | None = Field(
        default=None,
        description="Live workout question type for query_workout requests.",
    )
    workout_goal: str | None = Field(
        default=None,
        description="Free-text goal or constraints when the user asks to build a new workout.",
    )
    start_immediately: bool = Field(
        default=False,
        description="Whether the user asked to immediately start the newly created workout.",
    )
    confirmed_off_current: bool = Field(
        default=False,
        description=(
            "Internal flag set after the user confirms logging an exercise that "
            "does not match the current workout step."
        ),
    )
