"""Contracts for live workout execution and logged sets."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .common import CompletionSource, ContractModel, SessionStatus


class CompletedSet(ContractModel):
    exercise_id: str
    set_number: int = Field(ge=1)
    target_reps: Optional[int] = Field(default=None, ge=0)
    actual_reps: int = Field(ge=0)
    target_load: Optional[float] = Field(default=None, ge=0)
    actual_load: Optional[float] = Field(default=None, ge=0)
    target_rpe: Optional[float] = Field(default=None, ge=1.0, le=10.0)
    actual_rpe: Optional[float] = Field(default=None, ge=1.0, le=10.0)
    started_at: datetime
    ended_at: datetime
    completion_source: CompletionSource
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    notes: Optional[str] = None


class WorkoutSession(ContractModel):
    session_id: str
    program_id: str
    day_id: str
    status: SessionStatus = SessionStatus.PLANNED
    current_exercise_index: int = Field(default=0, ge=0)
    current_set_index: int = Field(default=0, ge=0)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    manual_override_enabled: bool = True
