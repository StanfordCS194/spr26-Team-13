"""Canonical shared contracts used across subsystems."""

from .coaching import CoachingCue
from .common import (
    BlockExecutionStyle,
    CompletionSource,
    CueModality,
    DetectionSource,
    SessionStatus,
    SourceType,
    TriggerType,
)
from .device import DeviceCapabilities, EquipmentItem
from .events import DisplayState, RepEvent
from .logging import ExportRecord, WorkoutSummary
from .program import ProgramExercise, TrainingBlock, TrainingDay, TrainingProgram, TrainingWeek
from .session import CompletedSet, WorkoutSession

__all__ = [
    "BlockExecutionStyle",
    "CoachingCue",
    "CompletedSet",
    "CompletionSource",
    "CueModality",
    "DetectionSource",
    "DeviceCapabilities",
    "DisplayState",
    "EquipmentItem",
    "ExportRecord",
    "ProgramExercise",
    "RepEvent",
    "SessionStatus",
    "SourceType",
    "TrainingBlock",
    "TrainingDay",
    "TrainingProgram",
    "TrainingWeek",
    "TriggerType",
    "WorkoutSession",
    "WorkoutSummary",
]
