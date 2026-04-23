"""Contracts for imported or generated training programs."""

from typing import List, Optional

from pydantic import Field

from .common import ContractModel, SourceType


class ProgramExercise(ContractModel):
    exercise_id: str
    display_name: str
    set_count: int = Field(ge=1)
    rep_target: Optional[str] = None
    load_target: Optional[str] = None
    rpe_target: Optional[float] = Field(default=None, ge=1.0, le=10.0)
    rest_seconds: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None
    ambiguity_flags: List[str] = Field(default_factory=list)


class TrainingDay(ContractModel):
    day_id: str
    title: str
    exercises: List[ProgramExercise] = Field(default_factory=list)
    notes: Optional[str] = None


class TrainingWeek(ContractModel):
    week_number: int = Field(ge=1)
    days: List[TrainingDay] = Field(default_factory=list)


class TrainingProgram(ContractModel):
    program_id: str
    user_id: str
    title: str
    source_type: SourceType
    weeks: List[TrainingWeek] = Field(default_factory=list)
    parse_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    needs_user_confirmation: bool = True
