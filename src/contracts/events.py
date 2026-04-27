"""Event contracts emitted by sensing and consumed by runtime/display."""

from datetime import datetime
from typing import Literal, Optional

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


class OverlayPlacement(ContractModel):
    anchor: Literal[
        "top_left",
        "top_right",
        "bottom_left",
        "bottom_right",
        "top_center",
        "bottom_center",
        "center",
    ] = "top_left"
    margin_x: int = Field(default=20, ge=0)
    margin_y: int = Field(default=20, ge=0)
    width: int = Field(default=380, ge=8)


class OverlayTextLine(ContractModel):
    label: str
    value: str
    emphasis: Literal["normal", "muted", "strong", "warning", "success"] = "normal"


class OverlayPanel(ContractModel):
    panel_id: str
    title: Optional[str] = None
    lines: list[OverlayTextLine] = Field(default_factory=list)
    placement: OverlayPlacement = Field(default_factory=OverlayPlacement)
    visible: bool = True
    opacity: float = Field(default=0.6, ge=0.0, le=1.0)
    priority: int = Field(default=0)


class OverlayBadge(ContractModel):
    badge_id: str
    text: str
    placement: OverlayPlacement = Field(
        default_factory=lambda: OverlayPlacement(anchor="top_right", width=180)
    )
    tone: Literal["info", "success", "warning", "danger"] = "info"
    compact: bool = False
    visible: bool = True
    expires_at: Optional[datetime] = None


class OverlayProgressBar(ContractModel):
    bar_id: str
    label: str
    progress: float = Field(ge=0.0, le=1.0)
    placement: OverlayPlacement = Field(
        default_factory=lambda: OverlayPlacement(anchor="bottom_left", width=420)
    )
    visible: bool = True
    color: Literal["blue", "green", "amber", "red"] = "blue"


class OverlayNotification(ContractModel):
    notification_id: str
    message: str
    tone: Literal["info", "success", "warning", "danger"] = "info"
    text_align: Literal["left", "center"] = "left"
    placement: OverlayPlacement = Field(
        default_factory=lambda: OverlayPlacement(anchor="bottom_center", width=420)
    )
    visible: bool = True
    expires_at: Optional[datetime] = None


class OverlayState(ContractModel):
    panels: list[OverlayPanel] = Field(default_factory=list)
    badges: list[OverlayBadge] = Field(default_factory=list)
    progress_bars: list[OverlayProgressBar] = Field(default_factory=list)
    notifications: list[OverlayNotification] = Field(default_factory=list)
