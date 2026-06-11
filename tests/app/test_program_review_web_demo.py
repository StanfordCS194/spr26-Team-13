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
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    response = client.post(
        "/api/assistant/chat",
        json={"message": "What's my squat PR?"},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "response": "Your back squat PR is 315 pounds for 2 reps.",
        "action": {
            "action": "get_pr",
            "exercise_name": "back squat",
            "program_name": None,
            "day_name": None,
            "day_number": None,
            "week_number": None,
            "weight": None,
            "reps": None,
            "duration_seconds": None,
            "date_range": None,
            "history_metric": None,
            "min_weight": None,
            "max_weight": None,
            "min_reps": None,
            "max_reps": None,
            "workout_query_type": None,
        },
    }


def test_assistant_chat_api_requires_message():
    app = create_app()
    client = app.test_client()

    response = client.post("/api/assistant/chat", json={})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Message is required."}


def test_glasses_chat_route_uses_action_path_for_supported_commands(monkeypatch):
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    response = client.post(
        "/api/chat",
        json={
            "text": "What's my bench PR?",
            "session_id": "test-session",
            "context": {
                "personalRecords": [
                    {
                        "exercise_name": "Bench Press",
                        "value": 245,
                        "unit": "lb",
                    }
                ]
            },
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "action"
    assert payload["reply"] == "Your Bench Press PR is 245 lb."
    assert payload["action"]["action"] == "get_pr"
    assert payload["ui_patch"] is None


def test_glasses_chat_route_returns_ui_patch_for_log_set(monkeypatch):
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    response = client.post(
        "/api/chat",
        json={
            "text": "Log a set of bench press for 8 reps at 185 pounds",
            "session_id": "workout:test-session",
            "context": {
                "activeProgramId": "program-1",
                "currentWorkout": {
                    "sessionId": "session-1",
                    "title": "Bench Day",
                },
            },
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "action"
    assert payload["action"]["action"] == "log_set"
    assert payload["ui_patch"] == {
        "type": "log_set",
        "sessionId": "session-1",
        "exerciseName": "bench press",
        "reps": 8,
        "weight": 185.0,
    }


def test_glasses_chat_route_executes_supabase_action_with_user_token(monkeypatch):
    app = create_app()
    client = app.test_client()
    captured = {}

    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    def fake_execute(action, *, context, access_token):
        captured["action"] = action
        captured["context"] = context
        captured["access_token"] = access_token
        return {
            "ok": True,
            "message": "Logged 8 reps of bench press at 185 pounds.",
            "action_result": {"set": {"id": "set-1"}},
            "ui_patch": {
                "type": "set_logged",
                "sessionId": "session-1",
                "exerciseName": "bench press",
                "setNumber": 1,
            },
        }

    monkeypatch.setattr("src.assistant.chat_route.execute_supabase_action", fake_execute)

    response = client.post(
        "/api/chat",
        json={
            "text": "Log a set of bench press for 8 reps at 185 pounds",
            "session_id": "workout:test-session",
            "auth": {"access_token": "user-jwt"},
            "context": {
                "currentWorkout": {
                    "sessionId": "session-1",
                    "title": "Bench Day",
                },
            },
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["reply"] == "Logged 8 reps of bench press at 185 pounds."
    assert payload["action_result"] == {"set": {"id": "set-1"}}
    assert payload["ui_patch"]["type"] == "set_logged"
    assert captured["access_token"] == "user-jwt"
    assert captured["action"].action == "log_set"
    assert captured["context"]["currentWorkout"]["sessionId"] == "session-1"


def test_glasses_chat_route_executes_supabase_history_search(monkeypatch):
    app = create_app()
    client = app.test_client()
    captured = {}

    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    def fake_execute(action, *, context, access_token):
        captured["action"] = action
        captured["access_token"] = access_token
        return {
            "ok": True,
            "message": "Last time I see bench press was May 20: 8 reps at 185 lb.",
            "action_result": {"sets": [{"reps": 8, "load_value": 185}]},
            "ui_patch": None,
        }

    monkeypatch.setattr("src.assistant.chat_route.execute_supabase_action", fake_execute)

    response = client.post(
        "/api/chat",
        json={
            "text": "What did I do on bench last week?",
            "auth": {"access_token": "user-jwt"},
            "context": {},
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "action"
    assert payload["action"]["action"] == "search_history"
    assert payload["action"]["date_range"] == "last_week"
    assert payload["reply"] == "Last time I see bench press was May 20: 8 reps at 185 lb."
    assert captured["access_token"] == "user-jwt"


def test_glasses_chat_route_executes_supabase_start_exercise(monkeypatch):
    app = create_app()
    client = app.test_client()
    captured = {}

    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    def fake_execute(action, *, context, access_token):
        captured["action"] = action
        captured["context"] = context
        captured["access_token"] = access_token
        return {
            "ok": True,
            "message": "Starting bench press.",
            "action_result": {"exercise_log": {"id": "log-1"}},
            "ui_patch": {
                "type": "exercise_started",
                "sessionId": "session-1",
                "exerciseName": "bench press",
                "exerciseLogId": "log-1",
                "step": {"exerciseName": "bench press", "setNumber": 1, "setCount": 3},
            },
        }

    monkeypatch.setattr("src.assistant.chat_route.execute_supabase_action", fake_execute)

    response = client.post(
        "/api/chat",
        json={
            "text": "Start bench press",
            "auth": {"access_token": "user-jwt"},
            "context": {
                "currentWorkout": {
                    "sessionId": "session-1",
                    "title": "Bench Day",
                },
            },
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["reply"] == "Starting bench press."
    assert payload["ui_patch"]["type"] == "exercise_started"
    assert captured["action"].action == "start_exercise"
    assert captured["access_token"] == "user-jwt"


def test_glasses_chat_route_executes_supabase_advance_set(monkeypatch):
    app = create_app()
    client = app.test_client()
    captured = {}

    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    def fake_execute(action, *, context, access_token):
        captured["action"] = action
        captured["context"] = context
        captured["access_token"] = access_token
        return {
            "ok": True,
            "message": "Next up is bench press, set 2 of 3.",
            "action_result": {"exerciseName": "bench press", "setNumber": 2, "setCount": 3},
            "ui_patch": {
                "type": "workout_step_updated",
                "sessionId": "session-1",
                "step": {"exerciseName": "bench press", "setNumber": 2, "setCount": 3},
            },
        }

    monkeypatch.setattr("src.assistant.chat_route.execute_supabase_action", fake_execute)

    response = client.post(
        "/api/chat",
        json={
            "text": "Next set",
            "auth": {"access_token": "user-jwt"},
            "context": {
                "currentWorkout": {
                    "sessionId": "session-1",
                    "title": "Bench Day",
                },
            },
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["reply"] == "Next up is bench press, set 2 of 3."
    assert payload["action"]["action"] == "advance_set"
    assert payload["ui_patch"]["type"] == "workout_step_updated"
    assert captured["access_token"] == "user-jwt"


def test_glasses_chat_route_uses_contextual_llm_for_general_questions(monkeypatch):
    captured = {}

    class FakeMessage:
        content = "Keep the squat warmup short and start with the empty bar."

    class FakeChoice:
        message = FakeMessage()

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return type("FakeCompletion", (), {"choices": [FakeChoice()]})()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    app = create_app()
    client = app.test_client()

    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)
    monkeypatch.setattr("src.assistant.chat_route.build_openai_client", lambda: FakeClient())

    response = client.post(
        "/api/chat",
        json={
            "text": "What warmup should I do?",
            "session_id": "chat-test-session",
            "context": {
                "activeProgram": {
                    "name": "Powerbuilding",
                    "exercises": [{"name": "Back Squat"}],
                }
            },
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "chat"
    assert payload["reply"] == "Keep the squat warmup short and start with the empty bar."
    assert "Powerbuilding" in captured["messages"][0]["content"]
    assert "Back Squat" in captured["messages"][0]["content"]


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
