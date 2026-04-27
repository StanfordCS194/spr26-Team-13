"""Live demo driver for the workout overlay display.

Simulates changing workout state, feeds it through the shared adapter, and
renders the result over a webcam frame for quick visual testing.
"""

from datetime import datetime

import cv2

from src.contracts import DisplayState, OverlayState
from src.glasses.display.adapter import build_tracking_indicator, display_state_to_overlay
from src.glasses.display.renderer import OverlayRenderer

DEFAULT_CAMERA_WIDTH = 1280
DEFAULT_CAMERA_HEIGHT = 720
DEFAULT_CAMERA_FPS = 30
DEMO_ACTIVE_PHASE_SECONDS = 9.0
DEMO_REST_PHASE_SECONDS = 9.0
DEMO_REST_TOTAL_SECONDS = 90.0
LOCKOUT_WARNING_START = 5.5
LOCKOUT_WARNING_END = 8.5
SET_COMPLETE_WARNING_SECONDS = 3.0


class DemoOverlayController:
    """Simulates runtime-driven overlay updates without hard-wiring camera logic to UI."""

    def __init__(self) -> None:
        self.phase_started_at = datetime.now()

    def build_state(self, now: datetime | None = None) -> OverlayState:
        now = now or datetime.now()
        elapsed = (now - self.phase_started_at).total_seconds()
        total_cycle_seconds = DEMO_ACTIVE_PHASE_SECONDS + DEMO_REST_PHASE_SECONDS
        cycle = elapsed % total_cycle_seconds

        if cycle < DEMO_ACTIVE_PHASE_SECONDS:
            rep_count = min(int(cycle) + 1, 8)
            state = DisplayState(
                exercise_name="Bench Press",
                set_progress="Set 2 of 4",
                rep_progress=f"{rep_count} / 8 reps",
                target_summary="185 lb x 8 @ RPE 8",
                rest_remaining_seconds=None,
                next_action="Drive through the bar path",
                warning_message=(
                    "Lockout cleaner on the right arm"
                    if LOCKOUT_WARNING_START <= cycle < LOCKOUT_WARNING_END
                    else None
                ),
            )
        else:
            rest_phase_elapsed = cycle - DEMO_ACTIVE_PHASE_SECONDS
            rest_progress = min(max(rest_phase_elapsed / DEMO_REST_PHASE_SECONDS, 0.0), 1.0)
            rest_remaining = max(0.0, (1.0 - rest_progress) * DEMO_REST_TOTAL_SECONDS)
            state = DisplayState(
                exercise_name="Bench Press",
                set_progress="Set 2 of 4 complete",
                rep_progress="8 / 8 reps",
                target_summary="Next set: 185 lb x 8",
                rest_remaining_seconds=int(round(rest_remaining)),
                next_action="Breathe, reset, and prepare for set 3",
                warning_message=(
                    "Set complete"
                    if DEMO_ACTIVE_PHASE_SECONDS
                    <= cycle
                    < DEMO_ACTIVE_PHASE_SECONDS + SET_COMPLETE_WARNING_SECONDS
                    else None
                ),
            )

        overlay_state = display_state_to_overlay(state, now=now)
        if cycle >= DEMO_ACTIVE_PHASE_SECONDS and overlay_state.progress_bars:
            overlay_state.progress_bars[0].progress = rest_progress
        overlay_state.badges.append(build_tracking_indicator(elapsed))
        return overlay_state


def draw_overlay(frame, state: DisplayState):
    overlay_state = display_state_to_overlay(state)
    return OverlayRenderer().render(frame, overlay_state)


def main():
    controller = DemoOverlayController()
    renderer = OverlayRenderer()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, DEFAULT_CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DEFAULT_CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, DEFAULT_CAMERA_FPS)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        raise RuntimeError("Could not open video source")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        overlay_state = controller.build_state()
        frame = renderer.render(frame, overlay_state)
        cv2.imshow("AR Glasses Workout Overlay Demo", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
