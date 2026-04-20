"""Contracts for workout summaries and external logging/export."""

from datetime import date
from typing import List, Optional

from pydantic import Field

from .common import ContractModel


class ExportRecord(ContractModel):
    workout_date: date
    exercise_name: str
    set_number: int = Field(ge=1)
    reps: int = Field(ge=0)
    load: Optional[float] = Field(default=None, ge=0)
    rpe: Optional[float] = Field(default=None, ge=1.0, le=10.0)
    volume: Optional[float] = Field(default=None, ge=0)
    session_id: str
    notes: Optional[str] = None
    image_refs: List[str] = Field(default_factory=list)


class WorkoutSummary(ContractModel):
    session_id: str
    total_volume: Optional[float] = Field(default=None, ge=0)
    estimated_one_rep_max: dict[str, float] = Field(default_factory=dict)
    highlights: List[str] = Field(default_factory=list)
