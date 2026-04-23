from datetime import datetime

from src.contracts import (
    CompletedSet,
    CompletionSource,
    DetectionSource,
    ProgramExercise,
    RepEvent,
    SourceType,
    TrainingDay,
    TrainingProgram,
    TrainingWeek,
    WorkoutSession,
)


def test_program_contract_smoke():
    program = TrainingProgram(
        program_id="p1",
        user_id="u1",
        title="Strength Block",
        source_type=SourceType.TEXT,
        weeks=[
            TrainingWeek(
                week_number=1,
                days=[
                    TrainingDay(
                        day_id="day-1",
                        title="Lower",
                        exercises=[
                            ProgramExercise(
                                exercise_id="back_squat",
                                display_name="Back Squat",
                                set_count=3,
                                rep_target="5",
                            )
                        ],
                    )
                ],
            )
        ],
    )

    assert program.weeks[0].days[0].exercises[0].exercise_id == "back_squat"


def test_session_and_event_contract_smoke():
    session = WorkoutSession(session_id="s1", program_id="p1", day_id="day-1")
    event = RepEvent(
        timestamp=datetime.now(),
        exercise_id="back_squat",
        event_type="rep_complete",
        rep_index=1,
        source=DetectionSource.IMU,
    )
    completed = CompletedSet(
        exercise_id="back_squat",
        set_number=1,
        actual_reps=5,
        started_at=datetime.now(),
        ended_at=datetime.now(),
        completion_source=CompletionSource.MANUAL,
    )

    assert session.current_exercise_index == 0
    assert event.rep_index == 1
    assert completed.set_number == 1
