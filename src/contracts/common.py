"""Shared enums and base helpers for cross-team contracts."""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    """Base model for all shared contracts."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SourceType(str, Enum):
    IMAGE = "image"
    PDF = "pdf"
    SPREADSHEET = "spreadsheet"
    TEXT = "text"
    GENERATED = "generated"


class BlockExecutionStyle(str, Enum):
    SEQUENTIAL = "sequential"
    ROUND_ROBIN = "round_robin"
    SUPERSET = "superset"
    CIRCUIT = "circuit"


class SessionStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class DetectionSource(str, Enum):
    MANUAL = "manual"
    IMU = "imu"
    CAMERA = "camera"
    HYBRID = "hybrid"


class CompletionSource(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    CONFIRMED_AUTO = "confirmed_auto"


class CueModality(str, Enum):
    AUDIO = "audio"
    DISPLAY = "display"


class TriggerType(str, Enum):
    EXERCISE_START = "exercise_start"
    DURING_REP = "during_rep"
    SET_COMPLETE = "set_complete"
    REST_START = "rest_start"
    REST_END = "rest_end"
