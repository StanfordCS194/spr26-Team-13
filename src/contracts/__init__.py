"""Canonical shared contracts used across subsystems."""

from .coaching import CoachingCue
from .common import CompletionSource, CueModality, DetectionSource, SessionStatus, SourceType, TriggerType
from .device import DeviceCapabilities, EquipmentItem
from .events import (
    DisplayState,
    OverlayBadge,
    OverlayNotification,
    OverlayPanel,
    OverlayPlacement,
    OverlayProgressBar,
    OverlayState,
    OverlayTextLine,
    RepEvent,
)
from .logging import ExportRecord, WorkoutSummary
from .program import ProgramExercise, TrainingDay, TrainingProgram, TrainingWeek
from .session import CompletedSet, WorkoutSession

__all__ = [
    "CoachingCue",
    "CompletedSet",
    "CompletionSource",
    "CueModality",
    "DetectionSource",
    "DeviceCapabilities",
    "DisplayState",
    "OverlayBadge",
    "OverlayNotification",
    "OverlayPanel",
    "OverlayPlacement",
    "OverlayProgressBar",
    "OverlayState",
    "OverlayTextLine",
    "EquipmentItem",
    "ExportRecord",
    "ProgramExercise",
    "RepEvent",
    "SessionStatus",
    "SourceType",
    "TrainingDay",
    "TrainingProgram",
    "TrainingWeek",
    "TriggerType",
    "WorkoutSession",
    "WorkoutSummary",
]
