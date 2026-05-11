from datetime import datetime, timedelta, timezone
from io import BytesIO

from src.assistant import mock_db
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


def test_program_review_api_returns_parsed_program(monkeypatch, tmp_path):
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr("src.app.program_review.web_demo.DESKTOP_PARSE_CACHE_DIR", tmp_path)
    monkeypatch.setattr(
        "src.app.program_review.web_demo.extract_program_file",
        lambda _path: ExtractedDocument(
            text="Day 1\nBack Squat - 3x5 @ 185 lb",
            source_type=SourceType.IMAGE,
            structured_markdown="Day 1\nBack Squat - 3x5 @ 185 lb",
            structured_data={"doc": "structured"},
        ),
    )
    monkeypatch.setattr("src.app.program_review.web_demo.llm_normalization_available", lambda: True)
    monkeypatch.setattr("src.app.program_review.web_demo.get_llm_provider", lambda: "gemini")
    monkeypatch.setattr(
        "src.app.program_review.web_demo.normalize_document_with_llm",
        lambda *_args, **_kwargs: TrainingProgram(
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
            needs_user_confirmation=False,
        ),
    )

    response = client.post(
        "/api/programs/parse",
        data={
            "user_id": "demo-user",
            "program_file": (BytesIO(b"fake image bytes"), "upload.png"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["program"]["title"] == "Upload"
    assert payload["program"]["weeks"][0]["days"][0]["exercises"][0]["display_name"] == "Back Squat"
    assert payload["extracted_preview"]["normalization_mode"] == "gemini"
    assert "Back Squat" in payload["extracted_preview"]["markdown"]


def test_program_review_api_caches_successful_gemini_parse(monkeypatch, tmp_path):
    app = create_app()
    client = app.test_client()
    calls = {"normalize": 0}

    monkeypatch.setattr("src.app.program_review.web_demo.DESKTOP_PARSE_CACHE_DIR", tmp_path)
    monkeypatch.setattr("src.app.program_review.web_demo.DESKTOP_CACHE_HIT_DELAY_SECONDS", 0)
    monkeypatch.setattr(
        "src.app.program_review.web_demo.extract_program_file",
        lambda _path: ExtractedDocument(
            text="Day 1\nBack Squat - 3x5 @ 185 lb",
            source_type=SourceType.IMAGE,
            structured_markdown="Day 1\nBack Squat - 3x5 @ 185 lb",
        ),
    )
    monkeypatch.setattr("src.app.program_review.web_demo.llm_normalization_available", lambda: True)
    monkeypatch.setattr("src.app.program_review.web_demo.get_llm_provider", lambda: "gemini")

    def normalize_once(*_args, **_kwargs):
        calls["normalize"] += 1
        return TrainingProgram(
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
            needs_user_confirmation=False,
        )

    monkeypatch.setattr("src.app.program_review.web_demo.normalize_document_with_llm", normalize_once)

    for _ in range(2):
        response = client.post(
            "/api/programs/parse",
            data={
                "user_id": "demo-user",
                "program_file": (BytesIO(b"same image bytes"), "upload.png"),
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert response.get_json()["program"]["title"] == "Upload"

    assert calls["normalize"] == 1
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_program_review_api_rejects_missing_llm(monkeypatch, tmp_path):
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr("src.app.program_review.web_demo.DESKTOP_PARSE_CACHE_DIR", tmp_path)
    monkeypatch.setattr(
        "src.app.program_review.web_demo.extract_program_file",
        lambda _path: ExtractedDocument(
            text="Day 1\nBack Squat - 3x5 @ 185 lb",
            source_type=SourceType.IMAGE,
            structured_markdown="Day 1\nBack Squat - 3x5 @ 185 lb",
        ),
    )
    monkeypatch.setattr("src.app.program_review.web_demo.llm_normalization_available", lambda: False)

    response = client.post(
        "/api/programs/parse",
        data={
            "user_id": "demo-user",
            "program_file": (BytesIO(b"fake image bytes"), "upload.png"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "Gemini normalization is not configured" in response.get_json()["error"]


def test_program_review_api_requires_upload():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/programs/parse",
        data={"user_id": "demo-user"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Upload an image or document to process."}


def test_assistant_chat_api_returns_response(monkeypatch):
    mock_db.reset_mock_state()
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    response = client.post(
        "/api/assistant/chat",
        json={"message": "What's my squat PR?"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["response"] == "Your Back Squat PR is 315 lb for 2 reps."
    assert payload["action"]["action"] == "get_pr"
    assert payload["action"]["exercise_name"] == "back squat"
    assert payload["tool_result"]["source"] == "mock"
    assert payload["display_state"] is None


def test_display_state_api_returns_updated_state(monkeypatch):
    mock_db.reset_mock_state()
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    assistant_response = client.post(
        "/api/assistant/chat",
        json={
            "user_id": "demo-user",
            "message": "Add 3 sets of 10 back squat at 225",
        },
    )

    session_id = assistant_response.get_json()["tool_result"]["session_id"]
    response = client.get(f"/api/display-state?session_id={session_id}")

    assert response.status_code == 200
    assert response.get_json()["display_state"]["exercise_name"] == "back squat"
    assert response.get_json()["display_state"]["set_progress"] == "Set 1 of 3"
    assert "display_state" not in assistant_response.get_json()["tool_result"]


def test_display_state_api_returns_live_rest_countdown(monkeypatch):
    mock_db.reset_mock_state()
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    assistant_response = client.post(
        "/api/assistant/chat",
        json={
            "user_id": "demo-user",
            "message": "start a set of 10 pushups",
        },
    )
    session_id = assistant_response.get_json()["tool_result"]["session_id"]

    client.post(
        "/api/assistant/chat",
        json={
            "user_id": "demo-user",
            "session_id": session_id,
            "message": "start rest for 10 seconds",
        },
    )

    first_payload = client.get(f"/api/display-state?session_id={session_id}").get_json()
    mock_db.WORKOUT_SESSIONS[session_id]["rest_started_at"] = (
        datetime.now(timezone.utc) - timedelta(seconds=5)
    ).isoformat()
    second_payload = client.get(f"/api/display-state?session_id={session_id}").get_json()

    assert first_payload["display_state"]["rest_total_seconds"] == 10
    assert first_payload["display_state"]["rest_remaining_seconds"] <= 10
    assert second_payload["display_state"]["rest_remaining_seconds"] <= 5


def test_assistant_chat_api_requires_message():
    app = create_app()
    client = app.test_client()

    response = client.post("/api/assistant/chat", json={})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Message is required."}


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
