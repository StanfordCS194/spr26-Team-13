"""Event contracts emitted by sensing and consumed by runtime/display."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .common import ContractModel, DetectionSource


class RepEvent(ContractModel):
    timestamp: datetime
    exercise_id: str
    event_type: str
    rep_index: Optional[int] = Field(default=None, ge=1)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source: DetectionSource
    sensor_window_id: Optional[str] = None


class DisplayState(ContractModel):
    exercise_name: str
    set_progress: str
    rep_progress: Optional[str] = None
    target_summary: str
    rest_remaining_seconds: Optional[int] = Field(default=None, ge=0)
    next_action: Optional[str] = None
    warning_message: Optional[str] = None
