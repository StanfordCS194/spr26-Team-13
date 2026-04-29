from datetime import datetime

from src.contracts import (
    BlockExecutionStyle,
    CompletedSet,
    CompletionSource,
    DetectionSource,
    ProgramExercise,
    RepEvent,
    SourceType,
    TrainingBlock,
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
                        blocks=[
                            TrainingBlock(
                                block_id="block-1",
                                title="Block 1",
                                execution_style=BlockExecutionStyle.ROUND_ROBIN,
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
        ],
    )

    assert program.weeks[0].days[0].blocks[0].title == "Block 1"
    assert program.weeks[0].days[0].exercises[0].exercise_id == "back_squat"
    assert program.weeks[0].days[0].ungrouped_exercises == []


def test_training_day_tracks_ungrouped_exercises():
    day = TrainingDay(
        day_id="day-1",
        title="Lower",
        blocks=[
            TrainingBlock(
                block_id="block-1",
                title="Block 1",
                execution_style=BlockExecutionStyle.ROUND_ROBIN,
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
        exercises=[
            ProgramExercise(
                exercise_id="back_squat",
                display_name="Back Squat",
                set_count=3,
                rep_target="5",
            ),
            ProgramExercise(
                exercise_id="bench_press",
                display_name="Bench Press",
                set_count=3,
                rep_target="5",
            ),
        ],
    )

    assert [exercise.exercise_id for exercise in day.ungrouped_exercises] == ["bench_press"]


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
