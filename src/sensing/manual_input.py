"""Manual logging fallback for when automatic rep/set detection is unavailable.

Exposes two pure helpers that produce the canonical runtime contracts with
`MANUAL` source values:

- `manual_rep_event`: emit a `RepEvent` for a tap-style manual rep log.
- `manual_completed_set`: emit a `CompletedSet` for an end-of-set manual form.

Both optionally accept a `WorkoutSession` so callers can enforce the
session-level `manual_override_enabled` flag at the logging boundary.
"""

from datetime import datetime
from typing import Optional

from src.contracts import (
    CompletedSet,
    CompletionSource,
    DetectionSource,
    RepEvent,
    WorkoutSession,
)


class ManualLoggingDisabledError(RuntimeError):
    """Raised when manual input is attempted on a session with overrides disabled."""


def _check_session(session: Optional[WorkoutSession]) -> None:
    if session is not None and not session.manual_override_enabled:
        raise ManualLoggingDisabledError(
            f"session {session.session_id} has manual_override_enabled=False"
        )


def manual_rep_event(
    exercise_id: str,
    *,
    rep_index: Optional[int] = None,
    timestamp: Optional[datetime] = None,
    session: Optional[WorkoutSession] = None,
) -> RepEvent:
    """Return a `RepEvent` representing a user-logged rep.

    `rep_index` is optional — some UIs will not know the count at tap time and
    leave the runtime to infer it. `timestamp` defaults to `datetime.now()`.
    """

    _check_session(session)
    return RepEvent(
        timestamp=timestamp or datetime.now(),
        exercise_id=exercise_id,
        event_type="rep_complete",
        rep_index=rep_index,
        source=DetectionSource.MANUAL,
    )


def manual_completed_set(
    exercise_id: str,
    set_number: int,
    actual_reps: int,
    *,
    started_at: Optional[datetime] = None,
    ended_at: Optional[datetime] = None,
    target_reps: Optional[int] = None,
    actual_load: Optional[float] = None,
    target_load: Optional[float] = None,
    actual_rpe: Optional[float] = None,
    target_rpe: Optional[float] = None,
    notes: Optional[str] = None,
    session: Optional[WorkoutSession] = None,
) -> CompletedSet:
    """Return a `CompletedSet` representing a set the user logged by hand.

    Missing `started_at` / `ended_at` default to `datetime.now()`; callers that
    know real timestamps should pass them. Load and RPE fields are forwarded
    as-is so the ingestion-side targets can be paired with the manual actuals.
    """

    _check_session(session)
    now = datetime.now()
    return CompletedSet(
        exercise_id=exercise_id,
        set_number=set_number,
        target_reps=target_reps,
        actual_reps=actual_reps,
        target_load=target_load,
        actual_load=actual_load,
        target_rpe=target_rpe,
        actual_rpe=actual_rpe,
        started_at=started_at or now,
        ended_at=ended_at or now,
        completion_source=CompletionSource.MANUAL,
        notes=notes,
    )
