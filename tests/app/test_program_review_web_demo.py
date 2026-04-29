from io import BytesIO

from src.app.program_review import create_app
from src.contracts import (
    BlockExecutionStyle,
    ProgramExercise,
    SourceType,
    TrainingBlock,
    TrainingDay,
    TrainingProgram,
    TrainingWeek,
)
from src.ingestion.models import ExtractedDocument


def test_program_review_demo_process_flow(monkeypatch):
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr(
        "src.app.program_review.web_demo.extract_program_file",
        lambda _path: ExtractedDocument(
            text="Day 1\nBack Squat - 3x5 @ 185 lb",
            source_type=SourceType.IMAGE,
            structured_markdown="Day 1\nBack Squat - 3x5 @ 185 lb",
            structured_data={"doc": "structured"},
        ),
    )
    monkeypatch.setattr(
        "src.app.program_review.web_demo.normalize_extracted_program",
        lambda *_args, **_kwargs: (
            TrainingProgram(
                program_id="program-1",
                user_id="demo-user",
                title="Upload",
                source_type=SourceType.IMAGE,
                weeks=[
                    TrainingWeek(
                        week_number=1,
                        days=[
                            TrainingDay(
                                day_id="day-1",
                                title="Day 1",
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
                                                load_target="185 lb",
                                            )
                                        ],
                                    )
                                ],
                            )
                        ],
                    )
                ],
                needs_user_confirmation=False,
            ),
            "gemini",
        ),
    )

    response = client.post(
        "/process",
        data={
            "user_id": "demo-user",
            "program_file": (BytesIO(b"fake image bytes"), "upload.png"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Docling Output" in html
    assert "Organized Workout Structure" in html
    assert "Gemini" in html
    assert "Block 1" in html
    assert "Back Squat" in html
    assert "185 lb" in html


def test_program_review_demo_requires_upload():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/process",
        data={"user_id": "demo-user"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert "Upload an image or document to process." in response.get_data(as_text=True)


def test_program_review_demo_shows_unassigned_exercises_when_blocks_exist(monkeypatch):
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr(
        "src.app.program_review.web_demo.extract_program_file",
        lambda _path: ExtractedDocument(
            text="Day 1\nBench Press - 3x5 @ 135 lb\nBlock 1\nBack Squat - 3x5 @ 185 lb",
            source_type=SourceType.IMAGE,
            structured_markdown="Day 1\nBench Press - 3x5 @ 135 lb\nBlock 1\nBack Squat - 3x5 @ 185 lb",
        ),
    )
    monkeypatch.setattr(
        "src.app.program_review.web_demo.normalize_extracted_program",
        lambda *_args, **_kwargs: (
            TrainingProgram(
                program_id="program-1",
                user_id="demo-user",
                title="Upload",
                source_type=SourceType.IMAGE,
                weeks=[
                    TrainingWeek(
                        week_number=1,
                        days=[
                            TrainingDay(
                                day_id="day-1",
                                title="Day 1",
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
                                                load_target="185 lb",
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
                                        load_target="185 lb",
                                    ),
                                    ProgramExercise(
                                        exercise_id="bench_press",
                                        display_name="Bench Press",
                                        set_count=3,
                                        rep_target="5",
                                        load_target="135 lb",
                                    ),
                                ],
                            )
                        ],
                    )
                ],
                needs_user_confirmation=False,
            ),
            "gemini",
        ),
    )

    response = client.post(
        "/process",
        data={
            "user_id": "demo-user",
            "program_file": (BytesIO(b"fake image bytes"), "upload.png"),
        },
        content_type="multipart/form-data",
    )

    html = response.get_data(as_text=True)
    assert "Unassigned Section" in html
    assert "Bench Press" in html
