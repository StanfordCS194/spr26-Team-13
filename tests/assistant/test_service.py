from src.assistant.service import handle_message, parse_user_message


def test_parse_user_message_gets_pr_with_local_fallback(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    action = parse_user_message("What's my bench PR?")

    assert action.action == "get_pr"
    assert action.exercise_name == "bench press"


def test_handle_message_gets_squat_pr_with_local_fallback(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    payload = handle_message("What's my squat PR?")

    assert payload["response"] == "Your back squat PR is 315 pounds for 2 reps."
    assert payload["action"]["action"] == "get_pr"
    assert payload["action"]["exercise_name"] == "back squat"


def test_handle_message_reads_pr_from_context(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    payload = handle_message(
        "What's my bench PR?",
        context={
            "personalRecords": [
                {
                    "exercise_name": "Bench Press",
                    "value": 245,
                    "unit": "lb",
                }
            ]
        },
    )

    assert payload["response"] == "Your Bench Press PR is 245 lb."
    assert payload["action"]["action"] == "get_pr"


def test_handle_message_uses_context_for_general_coach_answer(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    payload = handle_message(
        "What should I do?",
        context={
            "activeProgram": {
                "name": "Powerbuilding",
                "exercises": [{"name": "Back Squat"}],
            }
        },
    )

    assert "Back Squat" in payload["response"]
    assert "Powerbuilding" in payload["response"]
    assert payload["action"]["action"] == "unknown"


def test_handle_message_fallback_pr_with_unrelated_context_keeps_exercise_name(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    payload = handle_message(
        "What's my squat PR?",
        context={"activeProgram": {"name": "Powerbuilding"}},
    )

    assert payload["response"] == "Your back squat PR is 315 pounds for 2 reps."
