from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from src.contracts import (
    CompletedSet,
    CompletionSource,
    DetectionSource,
    RepEvent,
    WorkoutSession,
)
from src.sensing.manual_input import (
    ManualLoggingDisabledError,
    manual_completed_set,
    manual_rep_event,
)


def test_manual_rep_event_defaults_and_source():
    event = manual_rep_event("back_squat", rep_index=3)

    assert isinstance(event, RepEvent)
    assert event.exercise_id == "back_squat"
    assert event.rep_index == 3
    assert event.source is DetectionSource.MANUAL
    assert event.event_type == "rep_complete"


def test_manual_rep_event_accepts_explicit_timestamp():
    ts = datetime(2026, 4, 24, 12, 0, 0)
    event = manual_rep_event("bench_press", timestamp=ts)

    assert event.timestamp == ts
    assert event.rep_index is None


def test_manual_completed_set_golden_path():
    started = datetime(2026, 4, 24, 12, 0, 0)
    ended = started + timedelta(seconds=45)

    completed = manual_completed_set(
        "back_squat",
        set_number=1,
        actual_reps=5,
        started_at=started,
        ended_at=ended,
        target_reps=5,
        actual_load=185.0,
        target_load=185.0,
        actual_rpe=7.5,
        notes="felt strong",
    )

    assert isinstance(completed, CompletedSet)
    assert completed.completion_source is CompletionSource.MANUAL
    assert completed.actual_reps == 5
    assert completed.actual_load == 185.0
    assert completed.started_at == started
    assert completed.ended_at == ended
    assert completed.notes == "felt strong"


def test_manual_completed_set_defaults_timestamps_to_now():
    before = datetime.now()
    completed = manual_completed_set("deadlift", set_number=2, actual_reps=3)
    after = datetime.now()

    assert before <= completed.started_at <= after
    assert before <= completed.ended_at <= after


def test_manual_completed_set_rejects_invalid_reps():
    with pytest.raises(ValidationError):
        manual_completed_set("back_squat", set_number=1, actual_reps=-1)


def test_manual_rep_event_rejects_invalid_rep_index():
    with pytest.raises(ValidationError):
        manual_rep_event("back_squat", rep_index=0)


def test_manual_logging_blocked_when_override_disabled():
    session = WorkoutSession(
        session_id="s1",
        program_id="p1",
        day_id="day-1",
        manual_override_enabled=False,
    )

    with pytest.raises(ManualLoggingDisabledError):
        manual_rep_event("back_squat", session=session)

    with pytest.raises(ManualLoggingDisabledError):
        manual_completed_set(
            "back_squat", set_number=1, actual_reps=5, session=session
        )


def test_manual_logging_allowed_when_override_enabled():
    session = WorkoutSession(session_id="s1", program_id="p1", day_id="day-1")

    assert session.manual_override_enabled is True
    event = manual_rep_event("back_squat", rep_index=1, session=session)
    completed = manual_completed_set(
        "back_squat", set_number=1, actual_reps=5, session=session
    )

    assert event.source is DetectionSource.MANUAL
    assert completed.completion_source is CompletionSource.MANUAL
