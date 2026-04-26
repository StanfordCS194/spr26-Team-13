import sys
from datetime import datetime, timedelta

from src.contracts import (
    ProgramExercise,
    SessionStatus,
    SourceType,
    TrainingDay,
    TrainingProgram,
    TrainingWeek,
    WorkoutSession,
)
from src.sensing.manual_input import manual_completed_set, manual_rep_event


def _demo_manual_logging():
    program = TrainingProgram(
        program_id="prog-lower-a",
        user_id="demo-user",
        title="Lower A (demo)",
        source_type=SourceType.TEXT,
        weeks=[
            TrainingWeek(
                week_number=1,
                days=[
                    TrainingDay(
                        day_id="day-lower-a",
                        title="Lower A",
                        exercises=[
                            ProgramExercise(
                                exercise_id="back_squat",
                                display_name="Back Squat",
                                set_count=3,
                                rep_target="5",
                                load_target="185",
                            )
                        ],
                    )
                ],
            )
        ],
        parse_confidence=1.0,
        needs_user_confirmation=False,
    )

    session = WorkoutSession(
        session_id="sess-manual-demo-1",
        program_id=program.program_id,
        day_id=program.weeks[0].days[0].day_id,
        status=SessionStatus.IN_PROGRESS,
        started_at=datetime.now(),
    )

    tap = manual_rep_event("back_squat", rep_index=1, session=session)
    started = datetime.now()
    first_set = manual_completed_set(
        "back_squat",
        set_number=1,
        actual_reps=5,
        started_at=started,
        ended_at=started + timedelta(seconds=20),
        target_reps=5,
        actual_load=185.0,
        target_load=185.0,
        actual_rpe=7.5,
        session=session,
    )

    print(f"program:   {program.title} ({program.program_id})")
    print(f"session:   {session.session_id} status={session.status.value}")
    print(f"rep tap:   {tap.exercise_id} rep={tap.rep_index} source={tap.source.value}")
    print(
        "set log:   "
        f"{first_set.exercise_id} set#{first_set.set_number} "
        f"{first_set.actual_reps} reps @ {first_set.actual_load} lb "
        f"source={first_set.completion_source.value}"
    )


def main():
    if "--demo-manual" in sys.argv:
        _demo_manual_logging()
        return

    print("Team 13 scaffold is set up.")
    print("See docs/team-plan.md for ownership and shared folders.")
    print("See docs/api-contracts.md for shared schemas.")
    print("Run with --demo-manual to exercise the manual logging fallback.")


if __name__ == "__main__":
    main()
