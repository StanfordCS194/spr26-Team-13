"""Integration tests for progressive overload and post-workout summary features."""

from src.assistant.models import AssistantAction
from src.assistant.supabase_tools import (
    _build_workout_summary,
    _get_progression,
)
from src.runtime.progression import (
    ProgressionRecommendation,
    estimate_1rm,
    format_progression_reply,
    recommend_next_session,
)


# ---------------------------------------------------------------------------
# progression.py unit tests
# ---------------------------------------------------------------------------

def test_estimate_1rm_single_rep_returns_weight():
    assert estimate_1rm(315, 1) == 315


def test_estimate_1rm_epley_formula():
    result = estimate_1rm(225, 5)
    assert abs(result - 262.5) < 0.1


def test_recommend_next_session_hit_upper_target_adds_five_lbs():
    rows = [
        {
            "session": {"id": "s1", "started_at": "2026-06-04T10:00:00"},
            "log": {},
            "set": {"load_value": 185, "reps": 8},
        }
    ]
    rec = recommend_next_session("bench press", rows, rep_target="6-8")
    assert rec is not None
    assert rec.recommended_load == 190  # 185 + 5 upper body


def test_recommend_next_session_hit_lower_target_adds_ten_lbs():
    rows = [
        {
            "session": {"id": "s1", "started_at": "2026-06-04T10:00:00"},
            "log": {},
            "set": {"load_value": 225, "reps": 6},
        }
    ]
    rec = recommend_next_session("back squat", rows, rep_target="4-6")
    assert rec is not None
    assert rec.recommended_load == 235  # 225 + 10 lower body


def test_recommend_next_session_missed_target_holds_weight():
    rows = [
        {
            "session": {"id": "s1", "started_at": "2026-06-04T10:00:00"},
            "log": {},
            "set": {"load_value": 185, "reps": 3},
        }
    ]
    rec = recommend_next_session("bench press", rows, rep_target="6-8")
    assert rec is not None
    assert rec.recommended_load == 185  # hold — only 1 session at this weight


def test_recommend_next_session_deloads_after_two_missed_sessions():
    rows = [
        {
            "session": {"id": "s1", "started_at": "2026-06-04T10:00:00"},
            "log": {},
            "set": {"load_value": 185, "reps": 3},
        },
        {
            "session": {"id": "s2", "started_at": "2026-05-28T10:00:00"},
            "log": {},
            "set": {"load_value": 185, "reps": 4},
        },
    ]
    rec = recommend_next_session("bench press", rows, rep_target="6-8")
    assert rec is not None
    assert rec.recommended_load == 182.5  # deload by 2.5 upper body


def test_recommend_next_session_trend_based_no_target():
    rows = [
        {
            "session": {"id": "s1", "started_at": "2026-06-04T10:00:00"},
            "log": {},
            "set": {"load_value": 135, "reps": 8},
        },
        {
            "session": {"id": "s2", "started_at": "2026-05-28T10:00:00"},
            "log": {},
            "set": {"load_value": 130, "reps": 8},
        },
    ]
    rec = recommend_next_session("overhead press", rows)
    assert rec is not None
    assert rec.recommended_load == 137.5  # 135 + 2.5 upper body trend


def test_recommend_next_session_returns_none_for_empty_history():
    assert recommend_next_session("bench press", []) is None


def test_recommend_next_session_bodyweight_returns_rep_recommendation():
    rows = [
        {
            "session": {"id": "s1", "started_at": "2026-06-04T10:00:00"},
            "log": {},
            "set": {"load_value": 0, "reps": 12},
        }
    ]
    rec = recommend_next_session("hanging leg raise", rows)
    assert rec is not None
    assert rec.recommended_load is None
    assert "12" in rec.recommended_reps or "rep" in rec.reasoning.lower()


def test_format_progression_reply_includes_1rm_when_load_recommended():
    rec = ProgressionRecommendation(
        exercise_name="Bench Press",
        recommended_load=190,
        recommended_reps="6-8 reps",
        reasoning="You hit your target. Try 190 lbs.",
        estimated_1rm=230.0,
        sessions_used=2,
        confidence=0.85,
    )
    reply = format_progression_reply(rec)
    assert "230" in reply
    assert "190 lbs" in reply


# ---------------------------------------------------------------------------
# _get_progression supabase action handler
# ---------------------------------------------------------------------------

class _FakeProgressionClient:
    """Fake Supabase client with bench press history for two sessions."""

    def auth_user(self):
        return {"id": "user-1"}

    def select(self, table, params):
        if table == "workout_sessions":
            return [
                {"id": "s1", "title": "Push A", "started_at": "2026-06-04T10:00:00"},
                {"id": "s2", "title": "Push A", "started_at": "2026-05-28T10:00:00"},
            ]
        if table == "workout_exercise_logs":
            return [
                {"id": "l1", "session_id": "s1", "exercise_name": "Bench Press"},
                {"id": "l2", "session_id": "s2", "exercise_name": "Bench Press"},
            ]
        if table == "workout_sets":
            return [
                {"exercise_log_id": "l1", "set_number": 1, "reps": 8, "load_value": 185, "load_unit": "lb", "completed_at": "2026-06-04T10:30:00"},
                {"exercise_log_id": "l2", "set_number": 1, "reps": 7, "load_value": 180, "load_unit": "lb", "completed_at": "2026-05-28T10:30:00"},
            ]
        if table == "program_days":
            return []
        return []


def test_get_progression_returns_load_recommendation():
    result = _get_progression(
        _FakeProgressionClient(),
        AssistantAction(action="get_progression", exercise_name="bench press"),
        context={},
    )
    assert result["ok"] is True
    assert result["action_result"]["exercise_name"] is not None
    assert result["action_result"]["recommended_load"] is not None
    # 8 reps at 185 — no explicit target, trend up from 180 → should add 2.5
    assert result["action_result"]["recommended_load"] == 187.5
    assert "187.5" in result["message"] or "185" in result["message"]


def test_get_progression_missing_exercise_name_asks():
    result = _get_progression(
        _FakeProgressionClient(),
        AssistantAction(action="get_progression"),
        context={},
    )
    assert result["ok"] is False
    assert "Which exercise" in result["message"]


def test_get_progression_uses_program_rep_target():
    class ClientWithProgramDay(_FakeProgressionClient):
        def select(self, table, params):
            if table == "program_days":
                return [{"id": "day-1"}]
            if table == "program_blocks":
                return [{"id": "block-1", "day_id": "day-1", "block_number": 1}]
            if table == "program_exercises":
                return [
                    {
                        "id": "ex-1", "block_id": "block-1", "exercise_number": 1,
                        "exercise_name": "Bench Press", "set_count": 3, "rep_target": "6-8",
                    }
                ]
            return super().select(table, params)

    result = _get_progression(
        ClientWithProgramDay(),
        AssistantAction(action="get_progression", exercise_name="bench press"),
        context={"activeProgramId": "program-1"},
    )
    assert result["ok"] is True
    # With rep_target="6-8" and 8 reps hit → should recommend 185 + 5 = 190
    assert result["action_result"]["recommended_load"] == 190


# ---------------------------------------------------------------------------
# _build_workout_summary
# ---------------------------------------------------------------------------

class _FakeSummaryClient:
    """Fake client returning 2 exercises, 5 sets, with one new PR."""

    def auth_user(self):
        return {"id": "user-1"}

    def select(self, table, params):
        if table == "workout_exercise_logs":
            return [
                {"id": "l1", "exercise_name": "Bench Press"},
                {"id": "l2", "exercise_name": "Back Squat"},
            ]
        if table == "workout_sets":
            return [
                {"exercise_log_id": "l1", "set_number": 1, "reps": 5, "load_value": 225},
                {"exercise_log_id": "l1", "set_number": 2, "reps": 5, "load_value": 225},
                {"exercise_log_id": "l1", "set_number": 3, "reps": 4, "load_value": 225},
                {"exercise_log_id": "l2", "set_number": 1, "reps": 5, "load_value": 315},
                {"exercise_log_id": "l2", "set_number": 2, "reps": 5, "load_value": 315},
            ]
        if table == "personal_records":
            # Back Squat has no existing PR → should trigger a new PR write
            if "Back Squat" in params.get("exercise_name", ""):
                return []
            return [{"id": "pr-1", "value": 250, "record_type": "max_weight"}]
        return []

    def insert(self, table, payload):
        return {"id": "new-pr", **payload}

    def update(self, table, filters, payload):
        return payload


def test_build_workout_summary_computes_totals():
    summary = _build_workout_summary(
        _FakeSummaryClient(),
        session_id="session-1",
        session={"id": "session-1", "title": "Push Day"},
    )
    assert summary["total_sets"] == 5
    assert summary["total_volume"] > 0
    assert len(summary["exercises"]) == 2


def test_build_workout_summary_detects_new_pr():
    summary = _build_workout_summary(
        _FakeSummaryClient(),
        session_id="session-1",
        session={"id": "session-1", "title": "Leg Day"},
    )
    assert "Back Squat" in summary["new_prs"]
    assert "Back Squat" in summary["message"] or "PR" in summary["message"]


def test_build_workout_summary_message_includes_volume():
    summary = _build_workout_summary(
        _FakeSummaryClient(),
        session_id="session-1",
        session={"id": "session-1", "title": "Full Body"},
    )
    assert "lbs" in summary["message"].lower() or "volume" in summary["message"].lower()


def test_build_workout_summary_empty_session():
    class EmptyClient:
        def auth_user(self):
            return {"id": "user-1"}

        def select(self, table, params):
            return []

    summary = _build_workout_summary(
        EmptyClient(),
        session_id="empty-session",
        session={"id": "empty-session", "title": "Empty"},
    )
    assert "No sets" in summary["message"]
    assert summary["exercises"] == []
