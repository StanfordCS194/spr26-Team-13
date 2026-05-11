from src.assistant import mock_db
from src.assistant.service import handle_message, parse_user_message


def setup_function():
    mock_db.reset_mock_state()


def test_parse_user_message_gets_pr_with_local_fallback(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    action = parse_user_message("What's my bench PR?", user_id="demo-user")

    assert action.action == "get_pr"
    assert action.exercise_name == "bench press"
    assert action.user_id == "demo-user"


def test_handle_message_gets_squat_pr_with_local_fallback(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    payload = handle_message("What's my squat PR?", user_id="demo-user")

    assert payload["response"] == "Your back squat PR is 315 lb for 2 reps."
    assert payload["action"]["action"] == "get_pr"
    assert payload["action"]["exercise_name"] == "back squat"
    assert payload["tool_result"]["source"] == "mock"


def test_start_next_set_updates_session_display_state(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    started = handle_message("start workout", user_id="demo-user")
    session_id = started["tool_result"]["session_id"]
    handle_message("add 3 sets of 10 back squat at 225", user_id="demo-user", session_id=session_id)

    payload = handle_message("start my next set", user_id="demo-user", session_id=session_id)

    assert payload["action"]["action"] == "start_next_set"
    assert payload["tool_result"]["set_number"] == 2
    assert payload["display_state"]["exercise_name"] == "back squat"
    assert payload["display_state"]["set_progress"] == "Set 2 of 3"


def test_add_exercise_creates_current_planned_exercise(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    payload = handle_message("Add 3 sets of 10 back squat at 225", user_id="demo-user")

    assert payload["action"]["action"] == "add_exercise"
    assert payload["action"]["sets"] == 3
    assert payload["action"]["reps"] == 10
    assert payload["action"]["weight"] == 225
    assert payload["display_state"]["exercise_name"] == "back squat"
    assert payload["display_state"]["target_summary"] == "225 lb x 10"
    assert "display_state" not in payload["tool_result"]


def test_log_set_resolves_this_exercise(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    added = handle_message("Add 3 sets of 10 back squat at 225", user_id="demo-user")
    session_id = added["tool_result"]["session_id"]

    payload = handle_message("Log 8 reps at 225", user_id="demo-user", session_id=session_id)

    assert payload["action"]["action"] == "log_set"
    assert payload["action"]["exercise_name"] == "back squat"
    assert payload["tool_result"]["reps"] == 8
    assert payload["tool_result"]["weight"] == 225


def test_this_exercise_history_uses_active_exercise(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    added = handle_message("start bench", user_id="demo-user")
    session_id = added["tool_result"]["session_id"]

    payload = handle_message("What did I do last time for this exercise?", user_id="demo-user", session_id=session_id)

    assert payload["action"]["action"] == "get_recent_exercise_history"
    assert payload["action"]["exercise_name"] == "bench press"
    assert "Last time for bench press" in payload["response"]
