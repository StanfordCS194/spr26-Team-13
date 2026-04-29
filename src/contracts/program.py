"""Contracts for imported or generated training programs."""

from typing import List, Optional

from pydantic import Field, model_validator

from .common import BlockExecutionStyle, ContractModel, SourceType


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


class TrainingBlock(ContractModel):
    block_id: str
    title: str
    execution_style: BlockExecutionStyle = BlockExecutionStyle.SEQUENTIAL
    exercises: List[ProgramExercise] = Field(default_factory=list)
    notes: Optional[str] = None


class TrainingDay(ContractModel):
    day_id: str
    title: str
    blocks: List[TrainingBlock] = Field(default_factory=list)
    exercises: List[ProgramExercise] = Field(default_factory=list)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _sync_flat_exercises(self) -> "TrainingDay":
        """Keep a flat exercise list available for older consumers."""

        if self.blocks and not self.exercises:
            self.exercises = [exercise for block in self.blocks for exercise in block.exercises]
        return self

    @property
    def ungrouped_exercises(self) -> List[ProgramExercise]:
        """Return exercises not already represented inside a named block."""

        if not self.blocks:
            return list(self.exercises)

        blocked_keys = [self._exercise_key(exercise) for block in self.blocks for exercise in block.exercises]
        remaining_keys = list(blocked_keys)
        ungrouped: List[ProgramExercise] = []

        for exercise in self.exercises:
            exercise_key = self._exercise_key(exercise)
            if exercise_key in remaining_keys:
                remaining_keys.remove(exercise_key)
                continue
            ungrouped.append(exercise)

        return ungrouped

    @staticmethod
    def _exercise_key(exercise: ProgramExercise) -> tuple:
        return (
            exercise.exercise_id,
            exercise.display_name,
            exercise.set_count,
            exercise.rep_target,
            exercise.load_target,
            exercise.rpe_target,
            exercise.rest_seconds,
            exercise.notes,
            tuple(exercise.ambiguity_flags),
        )


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
