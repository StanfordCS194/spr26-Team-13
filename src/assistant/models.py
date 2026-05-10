"""Pydantic models for assistant intent parsing."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AssistantActionName = Literal[
    "get_pr",
    "log_set",
    "start_workout",
    "start_exercise",
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
    duration_seconds: int | None = Field(
        default=None,
        ge=0,
        description="Duration for rest or timer actions in seconds.",
    )
