"""Display-state adapter for the workout overlay.

Converts the app-facing DisplayState contract into concrete OverlayState widgets
that the renderer can draw on screen.
"""

from datetime import datetime, timedelta

from src.contracts import (
    DisplayState,
    OverlayBadge,
    OverlayNotification,
    OverlayPanel,
    OverlayPlacement,
    OverlayProgressBar,
    OverlayState,
    OverlayTextLine,
)

WARNING_DISPLAY_SECONDS = 4.0
TRACKING_BADGE_SECONDS = 6.0
TRACKING_DOT_SIZE = 14
BOTTOM_NOTIFICATION_CLEARANCE = 92


def _build_status_panel(state: DisplayState) -> OverlayPanel:
    return OverlayPanel(
        panel_id="workout_status",
        title="Workout",
        lines=[
            OverlayTextLine(label="Exercise", value=state.exercise_name, emphasis="strong"),
            OverlayTextLine(label="Set", value=state.set_progress),
            OverlayTextLine(label="Target", value=state.target_summary),
            OverlayTextLine(label="Next", value=state.next_action or "--", emphasis="muted"),
        ],
        placement=OverlayPlacement(anchor="top_left", margin_x=20, margin_y=20, width=420),
    )


def _build_rep_counter_panel(state: DisplayState) -> OverlayPanel:
    return OverlayPanel(
        panel_id="rep_counter",
        title="Reps",
        lines=[
            OverlayTextLine(label="Count", value=state.rep_progress or "--", emphasis="strong"),
        ],
        placement=OverlayPlacement(anchor="bottom_right", margin_x=20, margin_y=20, width=300),
        opacity=0.72,
        priority=1,
    )


def _build_rest_widgets(state: DisplayState) -> tuple[list[OverlayBadge], list[OverlayProgressBar]]:
    if state.rest_remaining_seconds is None:
        return [], []

    rest_total_seconds = state.rest_total_seconds or 120
    rest_progress = max(0.0, min(1.0, 1.0 - (state.rest_remaining_seconds / rest_total_seconds)))
    return (
        [
            OverlayBadge(
                badge_id="rest",
                text=f"Rest {state.rest_remaining_seconds}s",
                tone="warning",
            )
        ],
        [
            OverlayProgressBar(
                bar_id="rest_progress",
                label="Rest Timer",
                progress=rest_progress,
                color="amber",
            )
        ],
    )


def _build_warning_notification(state: DisplayState, now: datetime) -> list[OverlayNotification]:
    if not state.warning_message:
        return []

    is_set_complete = state.warning_message.lower() == "set complete"
    margin_y = BOTTOM_NOTIFICATION_CLEARANCE if state.rest_remaining_seconds is not None else 20
    return [
        OverlayNotification(
            notification_id="warning",
            message=state.warning_message,
            tone="warning",
            text_align="center" if is_set_complete else "left",
            placement=OverlayPlacement(anchor="bottom_center", margin_y=margin_y, width=420),
            expires_at=now + timedelta(seconds=WARNING_DISPLAY_SECONDS),
        )
    ]


def build_tracking_indicator(elapsed: float) -> OverlayBadge:
    if elapsed < TRACKING_BADGE_SECONDS:
        return OverlayBadge(
            badge_id="tracking",
            text="Tracking Active",
            tone="success",
            placement=OverlayPlacement(anchor="top_right", margin_x=20, margin_y=20, width=180),
        )

    return OverlayBadge(
        badge_id="tracking",
        text="",
        tone="success",
        compact=True,
        placement=OverlayPlacement(
            anchor="top_right",
            margin_x=4,
            margin_y=4,
            width=TRACKING_DOT_SIZE,
        ),
    )


def display_state_to_overlay(state: DisplayState, now: datetime | None = None) -> OverlayState:
    now = now or datetime.now()
    badges, progress_bars = _build_rest_widgets(state)
    return OverlayState(
        panels=[_build_status_panel(state), _build_rep_counter_panel(state)],
        badges=badges,
        progress_bars=progress_bars,
        notifications=_build_warning_notification(state, now),
    )
