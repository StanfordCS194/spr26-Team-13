from pathlib import Path

from src.ingestion import extract_program_file, ingest_program_text

from src.contracts import SourceType
from src.runtime.session_engine import build_planned_sessions


def test_ingest_text_fixture_into_training_program():
    fixture_path = Path("tests/fixtures/programs/sample_strength_program.txt")
    program = ingest_program_text(fixture_path.read_text(encoding="utf-8"), user_id="user-1")

    assert program.title == "Intro Strength Block"
    assert program.source_type == SourceType.TEXT
    assert len(program.weeks) == 1
    assert len(program.weeks[0].days) == 2
    assert program.weeks[0].days[0].exercises[0].exercise_id == "back_squat"
    assert program.weeks[0].days[0].exercises[1].exercise_id == "romanian_deadlift"


def test_extract_program_file_returns_plain_text_for_txt_fixture():
    extracted = extract_program_file("tests/fixtures/programs/sample_strength_program.txt")

    assert extracted.source_type == SourceType.TEXT
    assert "Back Squat - 3x5 @ 185 lb" in extracted.text
    assert extracted.structured_markdown is None


def test_build_planned_sessions_from_imported_program():
    program = ingest_program_text(
        """
        Day 1: Lower
        Back Squat - 3x5 @ 185 lb
        Day 2: Upper
        Bench Press - 3x5 @ 135 lb
        """,
        user_id="user-3",
    )

    sessions = build_planned_sessions(program)

    assert len(sessions) == 2
    assert sessions[0].day_id == program.weeks[0].days[0].day_id
    assert sessions[1].day_id == program.weeks[0].days[1].day_id
