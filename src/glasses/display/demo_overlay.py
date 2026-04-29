"""Live demo driver for the workout overlay display.

Simulates changing workout state, feeds it through the shared adapter, and
renders the result over a webcam frame or demo video for quick visual testing.
"""

import argparse
from dataclasses import dataclass
from datetime import datetime
from math import ceil
from pathlib import Path
from time import perf_counter

import cv2

from src.contracts import (
    DisplayState,
    OverlayPanel,
    OverlayPlacement,
    OverlayState,
    OverlayTextLine,
)
from src.glasses.display.adapter import build_tracking_indicator, display_state_to_overlay
from src.glasses.display.renderer import OverlayRenderer

DEFAULT_CAMERA_WIDTH = 1280
DEFAULT_CAMERA_HEIGHT = 720
DEFAULT_CAMERA_FPS = 30
COUNTDOWN_SECONDS = 3.0
SET_COMPLETE_WARNING_SECONDS = 3.0


@dataclass(frozen=True)
class DemoExercise:
    name: str
    set_progress: str
    target_summary: str
    next_action: str
    rep_goal: int
    rep_label: str
    rep_start_seconds: float
    rep_end_seconds: float
    rest_seconds: int

    @property
    def countdown_start_seconds(self) -> float:
        return self.rep_start_seconds - COUNTDOWN_SECONDS

    @property
    def rest_end_seconds(self) -> float:
        return self.rep_end_seconds + self.rest_seconds


DEMO_EXERCISES = (
    DemoExercise(
        name="Curls",
        set_progress="Set 1 of 1",
        target_summary="30 lb x 9 each arm",
        next_action="Keep back straight and core engaged",
        rep_goal=9,
        rep_label="each arm",
        rep_start_seconds=14.0,
        rep_end_seconds=42.0,
        rest_seconds=9,
    ),
    DemoExercise(
        name="Bench Press",
        set_progress="Set 1 of 1",
        target_summary="Barbell x 10",
        next_action="Drive through the bar path",
        rep_goal=10,
        rep_label="reps",
        rep_start_seconds=58.0,
        rep_end_seconds=69.0,
        rest_seconds=16,
    ),
    DemoExercise(
        name="Back Squat",
        set_progress="Set 1 of 1",
        target_summary="Barbell x 10",
        next_action="Brace, descend under control",
        rep_goal=10,
        rep_label="reps",
        rep_start_seconds=88.0,
        rep_end_seconds=103.0,
        rest_seconds=0,
    ),
)


def _parse_args():
    parser = argparse.ArgumentParser(description="Run the AR glasses workout overlay demo.")
    parser.add_argument(
        "--video",
        type=Path,
        help="Path to a local demo video. Omit this to use the webcam.",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop the demo video when it reaches the end.",
    )
    parser.add_argument(
        "--playback-speed",
        type=float,
        default=1.0,
        help="Video playback multiplier. Use values like 4.0 for exported slow-motion clips.",
    )
    return parser.parse_args()


def _rep_count(exercise: DemoExercise, elapsed_seconds: float) -> int:
    if elapsed_seconds < exercise.rep_start_seconds:
        return 0
    if elapsed_seconds >= exercise.rep_end_seconds:
        return exercise.rep_goal

    seconds_per_rep = (
        exercise.rep_end_seconds - exercise.rep_start_seconds
    ) / exercise.rep_goal
    completed_reps = int((elapsed_seconds - exercise.rep_start_seconds) / seconds_per_rep)
    return min(max(completed_reps, 0), exercise.rep_goal)


def _format_rep_progress(exercise: DemoExercise, rep_count: int) -> str:
    return f"{rep_count} / {exercise.rep_goal} {exercise.rep_label}"


def _build_countdown_panel(seconds_remaining: int) -> OverlayPanel:
    return OverlayPanel(
        panel_id="exercise_countdown",
        title="Starting In",
        lines=[
            OverlayTextLine(label="Count", value=str(seconds_remaining), emphasis="warning"),
        ],
        placement=OverlayPlacement(anchor="top_center", margin_y=20, width=320),
        opacity=0.78,
        priority=2,
    )


class DemoOverlayController:
    """Simulates runtime-driven overlay updates without hard-wiring camera logic to UI."""

    def __init__(self) -> None:
        self.phase_started_at = datetime.now()

    def _build_display_state(
        self,
        exercise: DemoExercise,
        elapsed_seconds: float,
    ) -> tuple[DisplayState, float | None]:
        rep_count = _rep_count(exercise, elapsed_seconds)
        rest_remaining_seconds = None
        rest_progress = None
        warning_message = None
        set_progress = exercise.set_progress
        next_action = exercise.next_action

        if exercise.rep_end_seconds <= elapsed_seconds < exercise.rest_end_seconds:
            rest_elapsed = elapsed_seconds - exercise.rep_end_seconds
            rest_remaining_seconds = max(0, ceil(exercise.rest_seconds - rest_elapsed))
            rest_progress = min(max(rest_elapsed / exercise.rest_seconds, 0.0), 1.0)
            set_progress = f"{exercise.set_progress} complete"
            next_action = "Recover and prepare for the next set"
            if elapsed_seconds < exercise.rep_end_seconds + SET_COMPLETE_WARNING_SECONDS:
                warning_message = "Set complete"

        return (
            DisplayState(
                exercise_name=exercise.name,
                set_progress=set_progress,
                rep_progress=_format_rep_progress(exercise, rep_count),
                target_summary=exercise.target_summary,
                rest_remaining_seconds=rest_remaining_seconds,
                next_action=next_action,
                warning_message=warning_message,
            ),
            rest_progress,
        )

    def _build_workout_complete_state(self, elapsed_seconds: float) -> OverlayState:
        return OverlayState(
            panels=[
                OverlayPanel(
                    panel_id="workout_complete",
                    title="Workout Complete",
                    lines=[
                        OverlayTextLine(
                            label="Summary",
                            value="Curls, bench press, and back squat complete",
                            emphasis="success",
                        ),
                    ],
                    placement=OverlayPlacement(anchor="center", width=560),
                    opacity=0.82,
                    priority=0,
                )
            ],
        )

    def build_state(
        self,
        now: datetime | None = None,
        elapsed_seconds: float | None = None,
    ) -> OverlayState:
        now = now or datetime.now()
        elapsed = (
            elapsed_seconds
            if elapsed_seconds is not None
            else (now - self.phase_started_at).total_seconds()
        )

        for exercise in DEMO_EXERCISES:
            if elapsed < exercise.countdown_start_seconds:
                state, rest_progress = self._build_display_state(exercise, elapsed)
                overlay_state = display_state_to_overlay(state, now=now)
                break

            if elapsed < exercise.rest_end_seconds:
                state, rest_progress = self._build_display_state(exercise, elapsed)
                overlay_state = display_state_to_overlay(state, now=now)

                if exercise.countdown_start_seconds <= elapsed < exercise.rep_start_seconds:
                    countdown_remaining = ceil(exercise.rep_start_seconds - elapsed)
                    overlay_state.panels.append(_build_countdown_panel(countdown_remaining))
                break
        else:
            overlay_state = self._build_workout_complete_state(elapsed)
            rest_progress = None

        if rest_progress is not None and overlay_state.progress_bars:
            overlay_state.progress_bars[0].progress = rest_progress
        overlay_state.badges.append(build_tracking_indicator(elapsed))
        return overlay_state


def draw_overlay(frame, state: DisplayState):
    overlay_state = display_state_to_overlay(state)
    return OverlayRenderer().render(frame, overlay_state)


def main():
    args = _parse_args()
    if args.playback_speed <= 0:
        raise ValueError("--playback-speed must be greater than 0")

    controller = DemoOverlayController()
    renderer = OverlayRenderer()
    using_video = args.video is not None
    video_path = args.video.expanduser() if args.video else None

    if using_video and not video_path.exists():
        raise FileNotFoundError(f"Demo video not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path) if using_video else 0)
    if using_video:
        video_started_at = perf_counter()
        frame_delay_ms = 1
    else:
        frame_delay_ms = 1
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, DEFAULT_CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DEFAULT_CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, DEFAULT_CAMERA_FPS)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        raise RuntimeError("Could not open video source")

    while True:
        if using_video:
            target_video_seconds = (perf_counter() - video_started_at) * args.playback_speed
            current_video_seconds = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            if current_video_seconds < target_video_seconds - 0.05:
                cap.set(cv2.CAP_PROP_POS_MSEC, target_video_seconds * 1000.0)

        ret, frame = cap.read()
        if not ret:
            if using_video and args.loop:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                video_started_at = perf_counter()
                continue
            break

        elapsed_seconds = None
        if using_video:
            elapsed_seconds = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

        overlay_state = controller.build_state(elapsed_seconds=elapsed_seconds)
        frame = renderer.render(frame, overlay_state)
        cv2.imshow("AR Glasses Workout Overlay Demo", frame)

        if using_video:
            frame_video_seconds = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            frame_wall_seconds = frame_video_seconds / args.playback_speed
            remaining_seconds = frame_wall_seconds - (perf_counter() - video_started_at)
            frame_delay_ms = max(1, int(round(remaining_seconds * 1000)))

        if cv2.waitKey(frame_delay_ms) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
