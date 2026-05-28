from src.assistant.service import handle_message, parse_user_message
from src.assistant.models import AssistantAction
from src.assistant.supabase_tools import (
    _advance_from_current_step,
    _get_rep_record,
    _query_history,
    _query_workout,
    _resolve_program_day,
    _resolve_program,
    _skip_exercise,
)


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


def test_parse_user_message_advances_next_set_with_local_fallback(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    action = parse_user_message("Advance to the next set")

    assert action.action == "advance_set"


def test_parse_user_message_extracts_named_workout_with_local_fallback(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    action = parse_user_message("Start my upper body workout")

    assert action.action == "start_workout"
    assert action.program_name == "upper body"


def test_parse_user_message_extracts_day_specific_workout(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    action = parse_user_message("Start week 1 day 3 workout")

    assert action.action == "start_workout"
    assert action.week_number == 1
    assert action.day_number == 3


def test_parse_user_message_extracts_rep_specific_record_with_local_fallback(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    action = parse_user_message("What is my record for 5 reps of bench?")

    assert action.action == "query_history"
    assert action.exercise_name == "bench press"
    assert action.reps == 5
    assert action.history_metric == "max_weight"


def test_advance_from_current_step_moves_to_next_set_before_next_exercise():
    current = {"exerciseName": "Bench Press", "setNumber": 1, "setCount": 3}

    step = _advance_from_current_step(current, [])

    assert step["exerciseName"] == "Bench Press"
    assert step["setNumber"] == 2


def test_advance_from_current_step_moves_to_next_program_exercise():
    current = {"exerciseName": "Bench Press", "setNumber": 3, "setCount": 3}

    step = _advance_from_current_step(
        current,
        [
            {"id": "exercise-1", "exercise_number": 1, "exercise_name": "Bench Press", "set_count": 3},
            {"id": "exercise-2", "exercise_number": 2, "exercise_name": "Lat Pulldown", "set_count": 2},
        ],
    )

    assert step["exerciseName"] == "Lat Pulldown"
    assert step["setNumber"] == 1
    assert step["setCount"] == 2


def test_resolve_program_prefers_requested_program_name():
    class FakeClient:
        def select(self, table, params):
            assert table == "programs"
            return [
                {"id": "program-a", "title": "Lower Body"},
                {"id": "program-b", "title": "Upper Body Strength"},
            ]

    program = _resolve_program(
        FakeClient(),
        AssistantAction(action="start_workout", program_name="upper body"),
        context={"activeProgramId": "program-a"},
    )

    assert program["id"] == "program-b"


def test_resolve_program_day_prefers_requested_week_and_day():
    class FakeClient:
        def select(self, table, params):
            assert table == "program_days"
            return [
                {"id": "day-1", "week_number": 1, "day_number": 1, "title": "Lower"},
                {"id": "day-2", "week_number": 1, "day_number": 2, "title": "Upper"},
                {"id": "day-3", "week_number": 2, "day_number": 1, "title": "Lower"},
            ]

    day = _resolve_program_day(
        FakeClient(),
        "program-1",
        action=AssistantAction(action="start_workout", week_number=1, day_number=2),
        context={},
    )

    assert day["id"] == "day-2"


def test_get_rep_record_uses_logged_sets_instead_of_one_rep_pr():
    class FakeClient:
        def select(self, table, params):
            if table == "workout_sessions":
                return [{"id": "session-1", "title": "Bench Day", "started_at": "2026-05-20T00:00:00Z"}]
            if table == "workout_exercise_logs":
                return [{"id": "log-1", "session_id": "session-1", "exercise_name": "Bench Press"}]
            if table == "workout_sets":
                return [
                    {"exercise_log_id": "log-1", "set_number": 1, "reps": 5, "load_value": 185, "load_unit": "lb"},
                    {"exercise_log_id": "log-1", "set_number": 2, "reps": 5, "load_value": 205, "load_unit": "lb"},
                ]
            return []

    result = _get_rep_record(
        FakeClient(),
        AssistantAction(action="get_pr", exercise_name="bench press", reps=5),
    )

    assert result["ok"] is True
    assert "best 5-rep Bench Press is 205 lb" in result["message"]


def test_parse_user_message_extracts_max_reps_above_weight_query(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    action = parse_user_message("What's the most reps I've ever hit on bench with 200 pounds or more?")

    assert action.action == "query_history"
    assert action.exercise_name == "bench press"
    assert action.history_metric == "max_reps"
    assert action.min_weight == 200


def test_query_history_answers_max_reps_above_weight():
    class FakeClient:
        def select(self, table, params):
            if table == "workout_sessions":
                return [{"id": "session-1", "title": "Bench Day", "started_at": "2026-05-20T00:00:00Z"}]
            if table == "workout_exercise_logs":
                return [{"id": "log-1", "session_id": "session-1", "exercise_name": "Bench Press"}]
            if table == "workout_sets":
                return [
                    {"exercise_log_id": "log-1", "set_number": 1, "reps": 8, "load_value": 185, "load_unit": "lb"},
                    {"exercise_log_id": "log-1", "set_number": 2, "reps": 6, "load_value": 205, "load_unit": "lb"},
                    {"exercise_log_id": "log-1", "set_number": 3, "reps": 4, "load_value": 225, "load_unit": "lb"},
                ]
            return []

    result = _query_history(
        FakeClient(),
        AssistantAction(
            action="query_history",
            exercise_name="bench press",
            history_metric="max_reps",
            min_weight=200,
        ),
    )

    assert result["ok"] is True
    assert "is 6 reps at 205 lb" in result["message"]


def test_query_history_answers_most_reps_in_one_set_without_weight():
    class FakeClient:
        def select(self, table, params):
            if table == "workout_sessions":
                return [{"id": "session-1", "title": "Core Day", "started_at": "2026-05-20T00:00:00Z"}]
            if table == "workout_exercise_logs":
                return [{"id": "log-1", "session_id": "session-1", "exercise_name": "Hanging Leg Raise"}]
            if table == "workout_sets":
                return [
                    {"exercise_log_id": "log-1", "set_number": 1, "reps": 12, "load_value": None, "load_unit": "bodyweight"},
                    {"exercise_log_id": "log-1", "set_number": 2, "reps": 18, "load_value": None, "load_unit": "bodyweight"},
                ]
            return []

    result = _query_history(
        FakeClient(),
        AssistantAction(
            action="query_history",
            exercise_name="leg raise",
            history_metric="max_reps",
        ),
    )

    assert result["ok"] is True
    assert "is 18" in result["message"]


def test_parse_user_message_extracts_live_workout_query(monkeypatch):
    monkeypatch.setattr("src.assistant.service.build_openai_client", lambda: None)

    action = parse_user_message("What is the current exercise?")

    assert action.action == "query_workout"
    assert action.workout_query_type == "current_exercise"


def test_query_workout_answers_last_set_in_current_session():
    class FakeClient:
        def select(self, table, params):
            if table == "workout_exercise_logs":
                return [{"id": "log-1", "session_id": "session-1", "exercise_name": "Back Squat"}]
            if table == "workout_sets":
                return [
                    {"exercise_log_id": "log-1", "set_number": 2, "reps": 5, "load_value": 225, "load_unit": "lb"},
                ]
            return []

    result = _query_workout(
        FakeClient(),
        AssistantAction(action="query_workout", exercise_name="back squat", workout_query_type="last_set"),
        context={"currentWorkout": {"sessionId": "session-1", "step": {"exerciseName": "Back Squat"}}},
    )

    assert result["ok"] is True
    assert "5 reps at 225 lb" in result["message"]


def test_skip_exercise_moves_to_next_program_exercise():
    class FakeClient:
        def select(self, table, params):
            if table == "program_days":
                return [{"id": "day-1"}]
            if table == "program_blocks":
                return [{"id": "block-1", "day_id": "day-1", "block_number": 1}]
            if table == "program_exercises":
                return [
                    {"id": "exercise-1", "block_id": "block-1", "exercise_number": 1, "exercise_name": "Bench Press", "set_count": 3},
                    {"id": "exercise-2", "block_id": "block-1", "exercise_number": 2, "exercise_name": "Lat Pulldown", "set_count": 2},
                ]
            return []

    result = _skip_exercise(
        FakeClient(),
        AssistantAction(action="skip_exercise"),
        context={
            "activeProgramId": "program-1",
            "currentWorkout": {"sessionId": "session-1", "step": {"exerciseName": "Bench Press", "setNumber": 1, "setCount": 3}},
        },
    )

    assert result["ok"] is True
    assert result["ui_patch"]["step"]["exerciseName"] == "Lat Pulldown"
