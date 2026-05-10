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
