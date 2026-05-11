"""Live demo driver for the workout overlay display.

Simulates changing workout state, feeds it through the shared adapter, and
renders the result over a webcam frame or demo video for quick visual testing.
"""

import argparse
import json
import threading
from dataclasses import dataclass
from datetime import datetime
from math import ceil
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

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
from src.assistant.voice import VoiceInputUnavailableError, record_and_transcribe

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
        rep_start_seconds=12.0,
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
        rep_start_seconds=56.0,
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
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to save the rendered overlay video as an MP4.",
    )
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Render without opening a preview window. Useful with --output.",
    )
    parser.add_argument(
        "--display-state-url",
        help="Optional API URL to poll for live DisplayState JSON instead of scripted demo state.",
    )
    parser.add_argument(
        "--display-state-poll-seconds",
        type=float,
        default=0.5,
        help="Minimum interval between live DisplayState API polls.",
    )
    parser.add_argument(
        "--assistant-chat-url",
        help="Optional assistant chat API URL. Press the voice key to send spoken commands here.",
    )
    parser.add_argument(
        "--user-id",
        default="demo-user",
        help="User id to send with assistant voice commands.",
    )
    parser.add_argument(
        "--session-id",
        help="Optional active session id to send with assistant voice commands.",
    )
    parser.add_argument(
        "--voice-key",
        default="p",
        help="Keyboard key that starts a fixed-duration push-to-talk recording.",
    )
    parser.add_argument(
        "--voice-seconds",
        type=float,
        default=4.0,
        help="Seconds to record after pressing the voice key.",
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


def _build_empty_live_display_state(status_message: str | None = None) -> DisplayState:
    return DisplayState(
        exercise_name="Live Workout",
        set_progress="No workout started",
        rep_progress=None,
        target_summary="Say a command to build this workout",
        rest_remaining_seconds=None,
        rest_total_seconds=None,
        next_action=status_message or "Press P and speak",
        warning_message=None,
    )


def _display_state_url_from_chat_url(chat_url: str, session_id: str) -> str:
    parsed = urlparse(chat_url)
    query = dict(parse_qsl(parsed.query))
    query["session_id"] = session_id
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            "/api/display-state",
            "",
            urlencode(query),
            "",
        )
    )


class LiveDisplayStatePoller:
    """Polls an API endpoint for DisplayState without owning workout logic."""

    def __init__(self, url: str, poll_seconds: float) -> None:
        self.url = url
        self.poll_seconds = max(poll_seconds, 0.1)
        self.last_polled_at = 0.0
        self.last_state: DisplayState | None = None

    def get_state(self) -> DisplayState | None:
        now = perf_counter()
        if self.last_state is not None and now - self.last_polled_at < self.poll_seconds:
            return self.last_state

        self.last_polled_at = now
        try:
            with urlopen(self.url, timeout=1.5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, TimeoutError, json.JSONDecodeError):
            return self.last_state

        raw_state = payload.get("display_state", payload)
        self.last_state = DisplayState.model_validate(raw_state)
        return self.last_state


class AssistantVoiceClient:
    """Records push-to-talk commands and sends transcripts to the assistant API."""

    def __init__(
        self,
        *,
        chat_url: str,
        user_id: str,
        session_id: str | None,
        record_seconds: float,
    ) -> None:
        self.chat_url = chat_url
        self.user_id = user_id
        self.session_id = session_id
        self.record_seconds = record_seconds
        self._lock = threading.Lock()
        self._busy = False
        self._latest_display_state: DisplayState | None = None
        self._status_message = "Press voice key to talk"

    @property
    def status_message(self) -> str:
        with self._lock:
            return self._status_message

    @property
    def active_session_id(self) -> str | None:
        with self._lock:
            return self.session_id

    def consume_display_state(self) -> DisplayState | None:
        with self._lock:
            state = self._latest_display_state
            self._latest_display_state = None
            return state

    def trigger(self) -> bool:
        with self._lock:
            if self._busy:
                return False
            self._busy = True
            self._status_message = f"Recording for {self.record_seconds:g}s..."

        thread = threading.Thread(target=self._record_and_send, daemon=True)
        thread.start()
        return True

    def _record_and_send(self) -> None:
        try:
            print(f"[voice] Recording for {self.record_seconds:g}s...")
            transcript = record_and_transcribe(duration_seconds=self.record_seconds)
            if not transcript:
                self._set_status("No speech detected")
                print("[voice] No speech detected.")
                return

            self._set_status(f"Heard: {transcript}")
            print(f"[voice] Heard: {transcript}")
            response = self._post_message(transcript)
            display_state = response.get("display_state")
            if display_state:
                with self._lock:
                    self._latest_display_state = DisplayState.model_validate(display_state)

            tool_result = response.get("tool_result")
            if isinstance(tool_result, dict) and tool_result.get("session_id"):
                with self._lock:
                    self.session_id = str(tool_result["session_id"])

            print(f"[assistant] {response.get('response', '')}")
            self._set_status(str(response.get("response") or "Assistant command sent"))
        except (VoiceInputUnavailableError, ValueError) as exc:
            self._set_status(str(exc))
            print(f"[voice] {exc}")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            message = f"Assistant API returned HTTP {exc.code}"
            if body:
                message = f"{message}: {body[:240]}"
            self._set_status(message)
            print(f"[voice] {message}")
        except Exception as exc:
            self._set_status("Voice command failed")
            print(f"[voice] Command failed: {exc}")
        finally:
            with self._lock:
                self._busy = False

    def _post_message(self, transcript: str) -> dict:
        payload = {
            "user_id": self.user_id,
            "message": transcript,
        }
        with self._lock:
            if self.session_id:
                payload["session_id"] = self.session_id

        body = json.dumps(payload).encode("utf-8")
        request = Request(
            self.chat_url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    def _set_status(self, message: str) -> None:
        with self._lock:
            self._status_message = message


def main():
    args = _parse_args()
    if args.playback_speed <= 0:
        raise ValueError("--playback-speed must be greater than 0")
    if args.output and args.loop:
        raise ValueError("--output cannot be used with --loop because export would never finish")

    controller = DemoOverlayController()
    renderer = OverlayRenderer()
    live_state_poller = (
        LiveDisplayStatePoller(args.display_state_url, args.display_state_poll_seconds)
        if args.display_state_url
        else None
    )
    auto_live_state_poller: LiveDisplayStatePoller | None = None
    auto_live_state_session_id: str | None = None
    voice_client = (
        AssistantVoiceClient(
            chat_url=args.assistant_chat_url,
            user_id=args.user_id,
            session_id=args.session_id,
            record_seconds=args.voice_seconds,
        )
        if args.assistant_chat_url
        else None
    )
    voice_key = ord(args.voice_key[:1]) if args.voice_key else None
    voice_display_state: DisplayState | None = None
    live_mode_enabled = bool(live_state_poller or voice_client)
    using_video = args.video is not None
    video_path = args.video.expanduser() if args.video else None
    output_path = args.output.expanduser() if args.output else None
    preview_enabled = not args.no_preview

    if using_video and not video_path.exists():
        raise FileNotFoundError(f"Demo video not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path) if using_video else 0)
    source_fps = cap.get(cv2.CAP_PROP_FPS) or DEFAULT_CAMERA_FPS
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

    writer = None
    try:
        while True:
            realtime_playback = using_video and preview_enabled
            if realtime_playback:
                target_video_seconds = (
                    perf_counter() - video_started_at
                ) * args.playback_speed
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

            latest_voice_state = voice_client.consume_display_state() if voice_client else None
            if latest_voice_state is not None:
                voice_display_state = latest_voice_state

            if live_state_poller is None and voice_client is not None:
                voice_session_id = voice_client.active_session_id
                if voice_session_id and voice_session_id != auto_live_state_session_id:
                    auto_live_state_session_id = voice_session_id
                    auto_live_state_poller = LiveDisplayStatePoller(
                        _display_state_url_from_chat_url(args.assistant_chat_url, voice_session_id),
                        args.display_state_poll_seconds,
                    )

            active_poller = live_state_poller or auto_live_state_poller
            live_display_state = active_poller.get_state() if active_poller else voice_display_state
            if live_display_state is not None:
                overlay_state = display_state_to_overlay(live_display_state)
                overlay_state.badges.append(build_tracking_indicator(perf_counter()))
            elif live_mode_enabled:
                live_display_state = _build_empty_live_display_state(
                    voice_client.status_message if voice_client else None
                )
                overlay_state = display_state_to_overlay(live_display_state)
                overlay_state.badges.append(build_tracking_indicator(perf_counter()))
            else:
                overlay_state = controller.build_state(elapsed_seconds=elapsed_seconds)
            frame = renderer.render(frame, overlay_state)

            if output_path and writer is None:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                frame_height, frame_width = frame.shape[:2]
                output_fps = source_fps * args.playback_speed
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(
                    str(output_path),
                    fourcc,
                    output_fps,
                    (frame_width, frame_height),
                )
                if not writer.isOpened():
                    raise RuntimeError(f"Could not open output video: {output_path}")

            if writer:
                writer.write(frame)

            if preview_enabled:
                cv2.imshow("AR Glasses Workout Overlay Demo", frame)

            if realtime_playback:
                frame_video_seconds = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                frame_wall_seconds = frame_video_seconds / args.playback_speed
                remaining_seconds = frame_wall_seconds - (perf_counter() - video_started_at)
                frame_delay_ms = max(1, int(round(remaining_seconds * 1000)))

            if preview_enabled:
                key = cv2.waitKey(frame_delay_ms) & 0xFF
                if key == ord("q"):
                    break
                if voice_client and voice_key is not None and key == voice_key:
                    if not voice_client.trigger():
                        print("[voice] Already handling a command.")
    finally:
        cap.release()
        if writer:
            writer.release()
        if preview_enabled:
            cv2.destroyAllWindows()

    if output_path:
        print(f"Wrote overlay video to {output_path}")


if __name__ == "__main__":
    main()
