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


def test_ingest_program_text_preserves_blocks():
    program = ingest_program_text(
        """
        Day 1: Lower
        Block 1
        Back Squat - 3x5 @ 185 lb
        Bench Press - 3x5 @ 135 lb
        """,
        user_id="user-4",
    )

    day = program.weeks[0].days[0]

    assert len(day.blocks) == 1
    assert day.blocks[0].title == "Block 1"
    assert day.blocks[0].execution_style.value == "round_robin"
    assert [exercise.exercise_id for exercise in day.blocks[0].exercises] == ["back_squat", "bench_press"]
    assert [exercise.exercise_id for exercise in day.exercises] == ["back_squat", "bench_press"]


def test_ingest_program_text_treats_team_prep_as_named_block():
    program = ingest_program_text(
        """
        Day 1: Lower
        Team Prep
        Back Squat - 3x5 @ 185 lb
        Bench Press - 3x5 @ 135 lb
        Block 1
        Romanian Deadlift - 3x8 @ 225 lb
        """,
        user_id="user-5",
    )

    day = program.weeks[0].days[0]

    assert [block.title for block in day.blocks] == ["Team Prep", "Block 1"]
    assert [exercise.exercise_id for exercise in day.blocks[0].exercises] == ["back_squat", "bench_press"]
    assert [exercise.exercise_id for exercise in day.blocks[1].exercises] == ["romanian_deadlift"]


def test_ingest_program_text_forward_attaches_title_before_block_header():
    program = ingest_program_text(
        """
        Day 1: Lower
        Team Prep
        Calf Stretch - 2x20s
        Clean Pull + Hang Clean
        Block 1
        2+2
        """,
        user_id="user-6",
    )

    day = program.weeks[0].days[0]

    assert [block.title for block in day.blocks] == ["Team Prep", "Block 1"]
    assert [exercise.display_name for exercise in day.blocks[0].exercises] == ["Calf Stretch"]
    assert day.blocks[1].exercises[0].display_name == "Clean Pull + Hang Clean"
