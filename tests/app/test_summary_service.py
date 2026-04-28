from datetime import datetime

from src.app.summary import format_workout_summary, generate_workout_summary
from src.contracts import CompletedSet, CompletionSource
from src.ingestion import ingest_program_text
from src.runtime.session_engine import build_planned_session, get_training_day


def test_generate_workout_summary_from_completed_sets():
    program = ingest_program_text(
        """
        Program: Demo Program
        Day 1: Lower
        Back Squat - 3x5 @ 185 lb
        Bench Press - 3x5 @ 135 lb
        """,
        user_id="user-1",
    )
    training_day = program.weeks[0].days[0]
    session = build_planned_session(program, training_day.day_id)
    completed_sets = [
        CompletedSet(
            exercise_id="back_squat",
            set_number=1,
            actual_reps=5,
            actual_load=185.0,
            started_at=datetime(2026, 1, 1, 9, 0, 0),
            ended_at=datetime(2026, 1, 1, 9, 2, 0),
            completion_source=CompletionSource.MANUAL,
        ),
        CompletedSet(
            exercise_id="bench_press",
            set_number=1,
            actual_reps=5,
            actual_load=135.0,
            started_at=datetime(2026, 1, 1, 9, 5, 0),
            ended_at=datetime(2026, 1, 1, 9, 7, 0),
            completion_source=CompletionSource.MANUAL,
        ),
    ]

    summary = generate_workout_summary(session, training_day, completed_sets)

    assert summary.session_id == session.session_id
    assert summary.total_volume == 1600.0
    assert "Back Squat" in summary.estimated_one_rep_max
    assert "Bench Press" in format_workout_summary(summary)


def test_get_training_day_matches_planned_session():
    program = ingest_program_text(
        """
        Day 1: Lower
        Back Squat - 3x5 @ 185 lb
        """,
        user_id="user-2",
    )
    session = build_planned_session(program, program.weeks[0].days[0].day_id)
    training_day = get_training_day(program, session.day_id)

    assert training_day.title == "Lower"
