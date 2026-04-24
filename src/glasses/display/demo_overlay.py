# src/glasses/demo_overlay.py

import cv2
from src.contracts import DisplayState


def draw_overlay(frame, state: DisplayState):
    # translucent black background
    overlay = frame.copy()
    cv2.rectangle(overlay, (20, 20), (420, 190), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.55, frame, 0.45, 0)

    lines = [
        f"Exercise: {state.exercise_name}",
        f"Set: {state.set_progress}",
        f"Reps: {state.rep_progress or '--'}",
        f"Target: {state.target_summary}",
        f"Next: {state.next_action or '--'}",
    ]

    y = 55
    for line in lines:
        cv2.putText(
            frame,
            line,
            (40, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        y += 30

    return frame


def main():
    state = DisplayState(
        exercise_name="Bench Press",
        set_progress="Set 2 of 4",
        rep_progress="6 / 8 reps",
        target_summary="185 lb x 8 @ RPE 8",
        rest_remaining_seconds=None,
        next_action="Finish set, then rest 2:00",
    )

    # Use 0 for webcam, or replace with a video path like "demo/workout.mp4"
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Could not open video source")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = draw_overlay(frame, state)
        cv2.imshow("AR Glasses Workout Overlay Demo", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()