"""User-scoped Supabase tools for coach actions.

These helpers call Supabase's REST API with the signed-in user's JWT. That keeps
row-level security in force while letting the Flask coach route own tool
execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
import json
import os
import re
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from src.assistant.coach_style import style_prompt_from_context
from src.assistant.evidence import format_evidence_context, retrieve_evidence
from src.assistant.models import AssistantAction
from src.assistant.tools import normalize_exercise_name
from src.shared.exercise_guidance import coaching_cue_for


DEFAULT_SUPABASE_URL = "https://rcmlbgjqwpfzpiownxfy.supabase.co"
DEFAULT_SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJjbWxiZ2pxd3BmenBpb3dueGZ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgyMjU2NzgsImV4cCI6MjA5MzgwMTY3OH0."
    "fKcwQ0Jws91vA9PcHg8PdyWDhP8WXYg4WFU5ll8ubyo"
)

DEFAULT_WORKOUT_GENERATOR_MODEL = "gpt-4.1-mini"
APP_TIME_ZONE = ZoneInfo("America/Los_Angeles")


class GeneratedWorkoutExercise(BaseModel):
    name: str = Field(description="Exercise name.")
    set_count: int = Field(ge=1, le=8, description="Number of working sets.")
    rep_target: str = Field(description="Rep target, such as 3-5, 8-10, or 30 sec.")
    load_target: str | None = Field(default=None, description="Load target, such as RPE 7, bodyweight, or moderate.")
    rest_seconds: int | None = Field(default=None, ge=0, le=600, description="Rest after each set.")
    notes: str | None = Field(default=None, description="Short coaching note.")


class GeneratedWorkoutBlock(BaseModel):
    title: str = Field(default="Main", description="Block title.")
    execution_style: str = Field(default="sequential", description="sequential, superset, circuit, or warmup.")
    exercises: list[GeneratedWorkoutExercise] = Field(min_length=1, max_length=8)


class GeneratedWorkoutDay(BaseModel):
    title: str = Field(description="Workout day title.")
    week_number: int = Field(default=1, ge=1, le=12)
    day_number: int = Field(default=1, ge=1, le=7)
    notes: str | None = None
    blocks: list[GeneratedWorkoutBlock] = Field(min_length=1, max_length=5)


class GeneratedWorkoutPlan(BaseModel):
    title: str = Field(description="Short title for the saved workout.")
    description: str = Field(description="One sentence summary of the workout.")
    weeks: int = Field(default=1, ge=1, le=12)
    days: list[GeneratedWorkoutDay] = Field(min_length=1, max_length=7)


class SupabaseToolError(RuntimeError):
    """Raised when a user-scoped Supabase tool cannot complete."""


@dataclass
class SupabaseConfig:
    url: str
    anon_key: str


def supabase_configured() -> bool:
    return bool(_get_supabase_config().url and _get_supabase_config().anon_key)


def execute_supabase_action(
    action: AssistantAction,
    *,
    context: dict[str, Any] | None,
    access_token: str | None,
) -> dict[str, Any] | None:
    """Execute supported actions in Supabase as the authenticated user.

    Returns None when the action is not backend-executable or auth/config is
    missing, allowing callers to fall back to the local demo implementation.
    """

    if not access_token or not supabase_configured():
        return None

    client = SupabaseRestClient(_get_supabase_config(), access_token)

    if action.action == "get_pr":
        return _get_pr(client, action)
    if action.action == "get_progression":
        return _get_progression(client, action, context=context)
    if action.action == "search_history":
        return _search_history(client, action)
    if action.action == "query_history":
        return _query_history(client, action)
    if action.action == "build_workout":
        return _build_workout(client, action, context=context)
    if action.action == "start_workout":
        return _start_workout(client, action, context=context)
    if action.action == "start_exercise":
        return _start_exercise(client, action, context=context)
    if action.action == "finish_workout":
        return _finish_workout(client, context=context)
    if action.action == "log_set":
        return _log_set(client, action, context=context)
    if action.action == "start_rest":
        return _start_rest(action, context=context)
    if action.action == "advance_set":
        return _advance_set(client, action, context=context)
    if action.action == "skip_exercise":
        return _skip_exercise(client, action, context=context)
    if action.action == "finish_exercise":
        return _skip_exercise(client, action, context=context, finished=True)
    if action.action == "query_workout":
        return _query_workout(client, action, context=context)

    return None


class SupabaseRestClient:
    def __init__(self, config: SupabaseConfig, access_token: str) -> None:
        self.config = config
        self.access_token = access_token

    def auth_user(self) -> dict[str, Any]:
        return self._request("GET", "/auth/v1/user")

    def select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        result = self._request("GET", f"/rest/v1/{table}", params=params)
        return result if isinstance(result, list) else []

    def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        result = self._request("POST", f"/rest/v1/{table}", payload=payload, prefer="return=representation")
        if isinstance(result, list) and result:
            return result[0]
        raise SupabaseToolError(f"Supabase insert into {table} returned no row.")

    def update(self, table: str, filters: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
        result = self._request(
            "PATCH",
            f"/rest/v1/{table}",
            params=filters,
            payload=payload,
            prefer="return=representation",
        )
        if isinstance(result, list) and result:
            return result[0]
        raise SupabaseToolError(f"Supabase update to {table} returned no row.")

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        prefer: str | None = None,
    ) -> Any:
        query = f"?{urlencode(params or {})}" if params else ""
        url = f"{self.config.url.rstrip('/')}{path}{query}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "apikey": self.config.anon_key,
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        if prefer:
            headers["Prefer"] = prefer

        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=10) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SupabaseToolError(f"Supabase {method} {path} failed: {exc.code} {detail}") from exc

        if not raw:
            return None
        return json.loads(raw)


def _get_pr(client: SupabaseRestClient, action: AssistantAction) -> dict[str, Any]:
    if action.reps is not None:
        return _get_rep_record(client, action)

    records = client.select(
        "personal_records",
        {
            "select": "id,exercise_name,record_type,value,unit,achieved_at",
            "order": "achieved_at.desc",
            "limit": "50",
        },
    )
    query = normalize_exercise_name(action.exercise_name)
    matches = []
    for record in records:
        name = str(record.get("exercise_name") or "")
        normalized_name = normalize_exercise_name(name) or name.lower()
        if query and not _names_compatible(query, normalized_name):
            continue
        matches.append(record)

    if not matches:
        exercise = query or action.exercise_name or "that exercise"
        return {
            "ok": False,
            "message": f"I do not see a saved PR for {exercise} yet.",
            "action_result": None,
            "ui_patch": None,
        }

    record = matches[0]
    display_name = str(record.get("exercise_name") or query or "that exercise")
    value = record.get("value")
    unit = record.get("unit") or "lb"
    return {
        "ok": True,
        "message": f"Your {display_name} PR is {_format_number(value)} {unit}.",
        "action_result": record,
        "ui_patch": None,
    }


def _get_rep_record(client: SupabaseRestClient, action: AssistantAction) -> dict[str, Any]:
    return _query_history(
        client,
        action.model_copy(update={"action": "query_history", "history_metric": "max_weight"}),
    )


def _get_progression(
    client: SupabaseRestClient,
    action: AssistantAction,
    *,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    from src.runtime.progression import format_progression_reply, recommend_next_session

    exercise_query = normalize_exercise_name(action.exercise_name) or action.exercise_name
    if not exercise_query:
        return {
            "ok": False,
            "message": "Which exercise do you want a progression recommendation for?",
            "action_result": None,
            "ui_patch": None,
        }

    rows = _history_set_rows(client, exercise_query=exercise_query)
    if not rows:
        return {
            "ok": False,
            "message": (
                f"I don't have enough history for {exercise_query} yet. "
                "Log a few sessions first and I'll give you a progression recommendation."
            ),
            "action_result": None,
            "ui_patch": None,
        }

    # Pull the prescribed rep target from the active program if available
    rep_target: str | None = None
    program_exercise = _find_program_exercise(
        client,
        _active_program_id(context),
        exercise_query,
        day_id=_active_day_id(context),
    )
    if program_exercise:
        rep_target = program_exercise.get("rep_target")

    rec = recommend_next_session(exercise_query, rows, rep_target=rep_target)
    if rec is None:
        return {
            "ok": False,
            "message": f"I couldn't compute a progression for {exercise_query} from your history.",
            "action_result": None,
            "ui_patch": None,
        }

    return {
        "ok": True,
        "message": format_progression_reply(rec),
        "action_result": {
            "exercise_name": rec.exercise_name,
            "recommended_load": rec.recommended_load,
            "recommended_reps": rec.recommended_reps,
            "estimated_1rm": rec.estimated_1rm,
            "sessions_used": rec.sessions_used,
            "confidence": rec.confidence,
        },
        "ui_patch": None,
    }


def _start_workout(
    client: SupabaseRestClient,
    action: AssistantAction,
    *,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    user = client.auth_user()
    user_id = user.get("id")
    if not user_id:
        raise SupabaseToolError("Supabase auth user response did not include an id.")

    program = _resolve_program(client, action, context=context)
    program_id = program.get("id") if program else _active_program_id(context)
    selected_day = _resolve_program_day(client, program_id, action=action, context=context)
    title = (program.get("title") if program else None) or _active_program_title(context) or "Workout"
    if selected_day and selected_day.get("title"):
        title = f"{title} - {selected_day['title']}"
    session = client.insert(
        "workout_sessions",
        {
            "user_id": user_id,
            "program_id": program_id,
            "title": title,
            "status": "in_progress",
            "started_at": _now_iso(),
        },
    )
    return {
        "ok": True,
        "message": f"Starting {title}.",
        "action_result": session,
        "ui_patch": {
            "type": "workout_started",
            "sessionId": session.get("id"),
            "programId": program_id,
            "day": _day_payload(selected_day),
            "step": _first_program_step(client, program_id, day_id=selected_day.get("id") if selected_day else None),
        },
    }


def _start_exercise(
    client: SupabaseRestClient,
    action: AssistantAction,
    *,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    session_id = _current_session_id(context)
    if not session_id:
        return {
            "ok": False,
            "message": "Start a workout before starting an exercise.",
            "action_result": None,
            "ui_patch": None,
        }

    day_id = _active_day_id(context)
    exercises = _program_exercises(client, _active_program_id(context), day_id=day_id)
    exercise = _find_program_exercise(client, _active_program_id(context), action.exercise_name, day_id=day_id)
    exercise_name = action.exercise_name or (exercise.get("exercise_name") if exercise else None)
    if not exercise_name:
        return {
            "ok": False,
            "message": "Which exercise should I start?",
            "action_result": None,
            "ui_patch": None,
        }
    if exercises and exercise is None:
        return {
            "ok": False,
            "message": f"I do not see {exercise_name} in the current workout. The current step is {_current_step_name(context) or exercises[0].get('exercise_name')}.",
            "action_result": {"requested_exercise": exercise_name},
            "ui_patch": None,
        }

    log = _get_or_create_exercise_log(
        client,
        session_id=session_id,
        exercise_name=str(exercise_name),
        program_exercise=exercise,
    )
    step = _step_from_exercise(log, exercise=exercise, set_number=_next_set_number(client, log["id"]))
    return {
        "ok": True,
        "message": f"Starting {log['exercise_name']}.",
        "action_result": {"exercise_log": log, "program_exercise": exercise},
        "ui_patch": {
            "type": "exercise_started",
            "sessionId": session_id,
            "exerciseName": log["exercise_name"],
            "exerciseLogId": log["id"],
            "step": step,
        },
    }


def _start_rest(action: AssistantAction, *, context: dict[str, Any] | None) -> dict[str, Any]:
    duration = action.duration_seconds or _current_rest_seconds(context) or 90
    return {
        "ok": True,
        "message": f"Starting a {duration}-second rest.",
        "action_result": {"duration_seconds": duration},
        "ui_patch": {
            "type": "rest_started",
            "durationSeconds": duration,
            "step": _current_step(context),
        },
    }


def _search_history(client: SupabaseRestClient, action: AssistantAction) -> dict[str, Any]:
    exercise_query = normalize_exercise_name(action.exercise_name) or action.exercise_name
    if not exercise_query:
        return {
            "ok": False,
            "message": "Which exercise should I search your history for?",
            "action_result": None,
            "ui_patch": None,
        }

    sessions = client.select(
        "workout_sessions",
        {
            "select": "id,title,started_at,created_at",
            "started_at": f"gte.{(datetime.now(UTC) - timedelta(days=14)).isoformat()}",
            "order": "started_at.desc",
            "limit": "25",
        },
    )
    if not sessions:
        return {
            "ok": False,
            "message": f"I do not see recent workouts for {exercise_query}.",
            "action_result": None,
            "ui_patch": None,
        }

    session_ids = [str(session["id"]) for session in sessions if session.get("id")]
    logs = client.select(
        "workout_exercise_logs",
        {
            "select": "id,session_id,exercise_number,exercise_name",
            "session_id": _in_filter(session_ids),
            "order": "exercise_number",
        },
    )
    matching_logs = [
        log for log in logs
        if _names_compatible(exercise_query, str(log.get("exercise_name") or ""))
    ]
    if not matching_logs:
        return {
            "ok": False,
            "message": f"I do not see {exercise_query} in your recent workouts.",
            "action_result": {"sessions_searched": len(sessions)},
            "ui_patch": None,
        }

    log_ids = [str(log["id"]) for log in matching_logs if log.get("id")]
    sets = client.select(
        "workout_sets",
        {
            "select": "exercise_log_id,set_number,reps,load_value,load_unit,rpe,status,completed_at",
            "exercise_log_id": _in_filter(log_ids),
            "order": "set_number",
        },
    )
    sets_by_log: dict[str, list[dict[str, Any]]] = {}
    for logged_set in sets:
        sets_by_log.setdefault(str(logged_set.get("exercise_log_id")), []).append(logged_set)

    latest_log = matching_logs[0]
    latest_session = next((session for session in sessions if session.get("id") == latest_log.get("session_id")), sessions[0])
    latest_sets = sets_by_log.get(str(latest_log.get("id")), [])
    if not latest_sets:
        return {
            "ok": False,
            "message": f"I found {latest_log.get('exercise_name')}, but no sets were logged for it.",
            "action_result": {"exercise_log": latest_log},
            "ui_patch": None,
        }

    set_summary = ", ".join(_format_set_summary(logged_set) for logged_set in latest_sets)
    session_title = latest_session.get("title") or "your recent workout"
    session_date = _format_date(latest_session.get("started_at") or latest_session.get("created_at"))
    return {
        "ok": True,
        "message": f"Last time I see {latest_log.get('exercise_name')} was {session_date} in {session_title}: {set_summary}.",
        "action_result": {
            "session": latest_session,
            "exercise_log": latest_log,
            "sets": latest_sets,
        },
        "ui_patch": None,
    }


def _query_history(client: SupabaseRestClient, action: AssistantAction) -> dict[str, Any]:
    exercise_query = normalize_exercise_name(action.exercise_name) or action.exercise_name
    if not exercise_query:
        return {
            "ok": False,
            "message": "Which exercise should I search your history for?",
            "action_result": None,
            "ui_patch": None,
        }

    rows = _history_set_rows(client, exercise_query=exercise_query)
    if not rows:
        return {
            "ok": False,
            "message": f"I do not see matching sets for {exercise_query} yet.",
            "action_result": None,
            "ui_patch": None,
        }

    filtered = _filter_history_sets(rows, action)
    if not filtered:
        return {
            "ok": False,
            "message": _format_no_history_match(exercise_query, action),
            "action_result": {"sets_searched": len(rows)},
            "ui_patch": None,
        }

    metric = action.history_metric or "recent_sets"
    if metric == "max_reps":
        best = max(filtered, key=lambda row: (int(row["set"].get("reps") or 0), float(row["set"].get("load_value") or 0)))
        message = _format_max_reps_answer(best, action)
    elif metric == "max_volume":
        best = max(filtered, key=_set_volume)
        message = _format_max_volume_answer(best)
    elif metric == "last_time":
        best = max(filtered, key=lambda row: _sort_date(row["set"].get("completed_at") or row["session"].get("started_at")))
        message = _format_last_time_answer(best)
    elif metric == "max_weight":
        best = max(filtered, key=lambda row: float(row["set"].get("load_value") or 0))
        message = _format_max_weight_answer(best, action)
    else:
        best = max(filtered, key=lambda row: _sort_date(row["set"].get("completed_at") or row["session"].get("started_at")))
        message = _format_recent_sets_answer(best)

    return {
        "ok": True,
        "message": message,
        "action_result": {
            "metric": metric,
            "session": best["session"],
            "exercise_log": best["log"],
            "set": best["set"],
            "sets_searched": len(rows),
            "sets_matched": len(filtered),
        },
        "ui_patch": None,
    }


def _build_workout(
    client: SupabaseRestClient,
    action: AssistantAction,
    *,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    user = client.auth_user()
    user_id = user.get("id")
    if not user_id:
        raise SupabaseToolError("Supabase auth user response did not include an id.")

    goal = action.workout_goal or "Build a balanced strength workout."
    plan = _generate_workout_plan(goal, context=context)
    program = _save_generated_workout_plan(client, user_id=user_id, plan=plan)
    program_detail = _program_detail_payload(client, program)
    first_day = _program_days(client, str(program["id"]))[0] if program.get("id") else None
    first_step = _first_program_step(
        client,
        str(program["id"]) if program.get("id") else None,
        day_id=first_day.get("id") if first_day else None,
    )

    ui_patch: dict[str, Any] = {
        "type": "program_created",
        "programId": program.get("id"),
        "programName": program.get("title") or plan.title,
        "program": _program_list_payload(program, program_detail),
        "detail": program_detail,
        "day": _day_payload(first_day),
        "step": first_step,
    }

    message = f"I built and saved {program.get('title') or plan.title}."
    action_result: dict[str, Any] = {"program": program, "plan": plan.model_dump(mode="json")}

    if action.start_immediately:
        session = client.insert(
            "workout_sessions",
            {
                "user_id": user_id,
                "program_id": program.get("id"),
                "title": program.get("title") or plan.title,
                "status": "in_progress",
                "started_at": _now_iso(),
            },
        )
        ui_patch = {
            "type": "workout_started",
            "sessionId": session.get("id"),
            "programId": program.get("id"),
            "program": _program_list_payload(program, program_detail),
            "detail": program_detail,
            "day": _day_payload(first_day),
            "step": first_step,
            "createdProgram": {
                "programId": program.get("id"),
                "programName": program.get("title") or plan.title,
            },
        }
        action_result["session"] = session
        message = f"I built and saved {program.get('title') or plan.title}, and started it."

    return {
        "ok": True,
        "message": message,
        "action_result": action_result,
        "ui_patch": ui_patch,
    }


def _generate_workout_plan(goal: str, *, context: dict[str, Any] | None) -> GeneratedWorkoutPlan:
    try:
        from src.assistant.service import build_openai_client
    except Exception:  # noqa: BLE001
        build_openai_client = None

    client = build_openai_client() if build_openai_client is not None else None
    if client is None:
        return _fallback_generated_workout_plan(goal)

    context_summary = _workout_generation_context(context)
    profile = context.get("trainingProfile") if isinstance(context, dict) else None
    evidence_context = format_evidence_context(
        retrieve_evidence(goal, profile=profile if isinstance(profile, dict) else None)
    )
    instructions = (
        "Create a practical workout plan for the TrainAR app. Return only the "
        "structured plan. Keep it realistic for one user to perform in a gym or "
        "home setting based on the request. Prefer 4-7 exercises per day, clear "
        "set counts, rep targets, load targets, and rest times. If the user asks "
        "for one workout, create one day. If they ask for multiple days, create "
        "that many days. Use the user's training profile and the evidence notes "
        "when available, but do not include medical claims."
    )
    input_text = f"User request: {goal}"
    if context_summary:
        input_text += f"\n\nAvailable user context:\n{context_summary}"
        input_text += f"\n\nCoach style rules:\n{style_prompt_from_context(context)}"
    if evidence_context:
        input_text += f"\n\nRelevant peer-reviewed evidence notes:\n{evidence_context}"

    try:
        response = client.responses.parse(
            model=os.getenv("OPENAI_WORKOUT_BUILDER_MODEL", DEFAULT_WORKOUT_GENERATOR_MODEL),
            instructions=instructions,
            input=input_text,
            text_format=GeneratedWorkoutPlan,
            temperature=0.4,
            max_output_tokens=1200,
        )
    except Exception as exc:  # noqa: BLE001
        raise SupabaseToolError("Workout generation failed.") from exc

    plan = response.output_parsed
    if plan is None:
        raise SupabaseToolError("Workout generation returned no structured plan.")
    return _normalize_generated_workout_plan(plan)


def _save_generated_workout_plan(
    client: SupabaseRestClient,
    *,
    user_id: str,
    plan: GeneratedWorkoutPlan,
) -> dict[str, Any]:
    days = _normalized_plan_days(plan)
    weeks = max(int(plan.weeks or 1), max((int(day.week_number or 1) for day in days), default=1))
    days_per_week = max(
        (
            sum(1 for candidate in days if int(candidate.week_number or 1) == int(day.week_number or 1))
            for day in days
        ),
        default=len(days) or 1,
    )
    total_exercises = sum(len(block.exercises) for day in days for block in day.blocks)
    program = client.insert(
        "programs",
        {
            "user_id": user_id,
            "title": plan.title.strip()[:80] or "Generated workout",
            "author": "TrainAR Coach",
            "kind": "Generated",
            "source_type": "generated",
            "source_label": "Coach",
            "color": "#C5F23E",
            "description": plan.description.strip()[:280] if plan.description else f"{total_exercises} generated exercises.",
            "weeks": weeks,
            "days_per_week": days_per_week,
            "active_week": 1,
            "progress": 0,
            "parse_confidence": 1,
            "canonical": plan.model_dump(mode="json"),
        },
    )

    for day_index, day in enumerate(days, start=1):
        day_row = client.insert(
            "program_days",
            {
                "program_id": program["id"],
                "week_number": int(day.week_number or 1),
                "day_number": int(day.day_number or day_index),
                "title": day.title.strip()[:80] or f"Day {day_index}",
                "notes": day.notes,
            },
        )
        for block_index, block in enumerate(day.blocks, start=1):
            block_row = client.insert(
                "program_blocks",
                {
                    "day_id": day_row["id"],
                    "block_number": block_index,
                    "title": block.title.strip()[:80] if block.title else "Main",
                    "execution_style": block.execution_style or "sequential",
                },
            )
            for exercise_index, exercise in enumerate(block.exercises, start=1):
                client.insert(
                    "program_exercises",
                    {
                        "block_id": block_row["id"],
                        "exercise_number": exercise_index,
                        "exercise_name": exercise.name.strip()[:120] or "Untitled exercise",
                        "set_count": int(exercise.set_count or 1),
                        "rep_target": exercise.rep_target,
                        "load_target": exercise.load_target,
                        "rest_seconds": exercise.rest_seconds,
                        "notes": exercise.notes,
                        "ambiguity_flags": [],
                        "raw": exercise.model_dump(mode="json"),
                    },
                )

    return program


def _program_list_payload(program: dict[str, Any], detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": program.get("id"),
        "name": program.get("title"),
        "author": program.get("author") or "Imported",
        "weeks": program.get("weeks") or 0,
        "daysPerWeek": program.get("days_per_week") or (detail or {}).get("dayCount") or 0,
        "type": program.get("kind") or program.get("source_type") or "Program",
        "color": program.get("color") or "#C5F23E",
        "sourceLabel": program.get("source_label") or "Imported",
        "activeWeek": program.get("active_week") or 1,
        "progress": float(program.get("progress") or 0),
        "description": program.get("description") or "",
    }


def _program_detail_payload(client: SupabaseRestClient, program: dict[str, Any]) -> dict[str, Any]:
    program_id = str(program.get("id") or "")
    days = _program_days(client, program_id) if program_id else []
    day_ids = [str(day["id"]) for day in days if day.get("id")]

    blocks = client.select(
        "program_blocks",
        {
            "select": "id,day_id,block_number,title,execution_style",
            "day_id": _in_filter(day_ids),
            "order": "block_number",
        },
    ) if day_ids else []
    block_ids = [str(block["id"]) for block in blocks if block.get("id")]

    exercises = client.select(
        "program_exercises",
        {
            "select": "id,block_id,exercise_number,exercise_name,set_count,rep_target,load_target,rest_seconds,notes,ambiguity_flags",
            "block_id": _in_filter(block_ids),
            "order": "exercise_number",
        },
    ) if block_ids else []

    blocks_by_day: dict[str, list[dict[str, Any]]] = {}
    for block in blocks:
        blocks_by_day.setdefault(str(block.get("day_id")), []).append(block)

    exercises_by_block: dict[str, list[dict[str, Any]]] = {}
    for exercise in exercises:
        exercises_by_block.setdefault(str(exercise.get("block_id")), []).append(exercise)

    detail_days = []
    for day in days:
        day_blocks = []
        for block in blocks_by_day.get(str(day.get("id")), []):
            day_blocks.append(
                {
                    "id": block.get("id"),
                    "title": block.get("title"),
                    "executionStyle": block.get("execution_style"),
                    "exercises": [
                        _exercise_detail_payload(exercise)
                        for exercise in exercises_by_block.get(str(block.get("id")), [])
                    ],
                }
            )
        detail_days.append(
            {
                "id": day.get("id"),
                "title": day.get("title"),
                "weekNumber": day.get("week_number"),
                "dayNumber": day.get("day_number"),
                "blocks": day_blocks,
            }
        )

    flat_exercises = [
        exercise
        for day in detail_days
        for block in day.get("blocks", [])
        for exercise in block.get("exercises", [])
    ]
    return {
        "programId": program.get("id"),
        "name": program.get("title"),
        "sourceType": program.get("source_type"),
        "confidence": program.get("parse_confidence"),
        "dayCount": len(detail_days),
        "weeks": program.get("weeks"),
        "totalSets": sum(_payload_set_count(exercise.get("sets")) for exercise in flat_exercises),
        "days": detail_days,
        "exercises": flat_exercises,
        "canonical": program.get("canonical") or {},
    }


def _exercise_detail_payload(exercise: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": exercise.get("id"),
        "name": exercise.get("exercise_name"),
        "sets": exercise.get("set_count") if exercise.get("set_count") is not None else "-",
        "reps": exercise.get("rep_target") or "-",
        "load": exercise.get("load_target") or "-",
        "rest": _format_rest_payload(exercise.get("rest_seconds")),
        "note": " - ".join(
            str(part)
            for part in [exercise.get("notes"), *(exercise.get("ambiguity_flags") or [])]
            if part
        ),
    }


def _payload_set_count(value: Any) -> int:
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return 0


def _format_rest_payload(seconds: Any) -> str:
    try:
        value = int(seconds)
    except (TypeError, ValueError):
        return "-"
    if value <= 0:
        return "-"
    if value % 60 == 0:
        return f"{value // 60} min"
    return f"{value} sec"


def _normalize_generated_workout_plan(plan: GeneratedWorkoutPlan) -> GeneratedWorkoutPlan:
    days = _normalized_plan_days(plan)
    return plan.model_copy(
        update={
            "title": (plan.title or "Generated workout").strip()[:80],
            "description": (plan.description or "Coach-generated workout.").strip()[:280],
            "weeks": max(int(plan.weeks or 1), 1),
            "days": days,
        }
    )


def _normalized_plan_days(plan: GeneratedWorkoutPlan) -> list[GeneratedWorkoutDay]:
    normalized: list[GeneratedWorkoutDay] = []
    for index, day in enumerate(plan.days or [], start=1):
        blocks = []
        for block in day.blocks or []:
            exercises = [
                exercise.model_copy(
                    update={
                        "name": (exercise.name or "Untitled exercise").strip(),
                        "set_count": max(int(exercise.set_count or 1), 1),
                        "rep_target": str(exercise.rep_target or "8-10").strip(),
                        "rest_seconds": exercise.rest_seconds if exercise.rest_seconds is not None else 90,
                    }
                )
                for exercise in block.exercises
                if exercise.name
            ]
            if exercises:
                blocks.append(
                    block.model_copy(
                        update={
                            "title": (block.title or "Main").strip(),
                            "execution_style": (block.execution_style or "sequential").strip().lower(),
                            "exercises": exercises[:8],
                        }
                    )
                )
        if not blocks:
            blocks = _fallback_generated_workout_plan(day.title or "balanced workout").days[0].blocks
        normalized.append(
            day.model_copy(
                update={
                    "title": (day.title or f"Day {index}").strip(),
                    "week_number": max(int(day.week_number or 1), 1),
                    "day_number": max(int(day.day_number or index), 1),
                    "blocks": blocks[:5],
                }
            )
        )
    return normalized or _fallback_generated_workout_plan(plan.title or "balanced workout").days


def _fallback_generated_workout_plan(goal: str) -> GeneratedWorkoutPlan:
    text = goal.lower()
    if any(term in text for term in ("leg", "lower", "squat", "glute")):
        title = "Lower Body Strength"
        exercises = [
            ("Back Squat", 4, "5", "RPE 7-8", 150, "Brace hard and keep depth consistent."),
            ("Romanian Deadlift", 3, "8", "moderate", 120, "Control the eccentric."),
            ("Walking Lunge", 3, "10 each leg", "bodyweight or light dumbbells", 90, None),
            ("Leg Curl", 3, "10-12", "moderate", 75, None),
            ("Standing Calf Raise", 3, "12-15", "moderate", 60, None),
        ]
    elif any(term in text for term in ("upper", "chest", "bench", "push", "pull", "arms", "shoulder")):
        title = "Upper Body Strength"
        exercises = [
            ("Bench Press", 4, "5", "RPE 7-8", 150, "Pause the first rep of each set."),
            ("Chest-Supported Row", 4, "8-10", "moderate", 120, None),
            ("Overhead Press", 3, "6-8", "moderate", 120, None),
            ("Lat Pulldown", 3, "10-12", "moderate", 90, None),
            ("Incline Dumbbell Press", 3, "8-10", "moderate", 90, None),
        ]
    else:
        title = "Full Body Strength"
        exercises = [
            ("Back Squat", 3, "5", "RPE 7", 150, None),
            ("Bench Press", 3, "6", "RPE 7", 120, None),
            ("Romanian Deadlift", 3, "8", "moderate", 120, None),
            ("Lat Pulldown", 3, "10", "moderate", 90, None),
            ("Hanging Leg Raise", 3, "10-12", "bodyweight", 60, None),
        ]

    return GeneratedWorkoutPlan(
        title=title,
        description=f"Coach-generated workout based on: {goal[:160]}",
        weeks=1,
        days=[
            GeneratedWorkoutDay(
                title="Day 1",
                week_number=1,
                day_number=1,
                notes=None,
                blocks=[
                    GeneratedWorkoutBlock(
                        title="Main",
                        execution_style="sequential",
                        exercises=[
                            GeneratedWorkoutExercise(
                                name=name,
                                set_count=sets,
                                rep_target=reps,
                                load_target=load,
                                rest_seconds=rest,
                                notes=notes,
                            )
                            for name, sets, reps, load, rest, notes in exercises
                        ],
                    )
                ],
            )
        ],
    )


def _workout_generation_context(context: dict[str, Any] | None) -> str:
    if not isinstance(context, dict):
        return ""

    lines: list[str] = []
    profile = context.get("trainingProfile")
    if isinstance(profile, dict):
        profile_lines = []
        mapping = [
            ("trainingGoal", "goal"),
            ("trainingExperience", "experience"),
            ("workoutDaysPerWeek", "days per week"),
            ("workoutSessionMinutes", "minutes per workout"),
            ("coachStyle", "coach style"),
            ("movementConstraints", "movement constraints"),
        ]
        for key, label in mapping:
            if profile.get(key):
                profile_lines.append(f"{label}: {profile[key]}")
        equipment = profile.get("availableEquipment")
        if isinstance(equipment, list) and equipment:
            profile_lines.append(f"equipment: {', '.join(str(item) for item in equipment)}")
        if profile_lines:
            lines.append(f"Training profile: {'; '.join(profile_lines)}")

    records = context.get("personalRecords")
    if isinstance(records, list) and records:
        prs = []
        for record in records[:8]:
            if not isinstance(record, dict):
                continue
            exercise = record.get("exercise_name") or record.get("exerciseName")
            value = record.get("value") or record.get("weight")
            unit = record.get("unit") or "lb"
            if exercise and value:
                prs.append(f"{exercise}: {value} {unit}")
        if prs:
            lines.append(f"Recent PRs: {', '.join(prs)}")

    programs = context.get("programs")
    if isinstance(programs, list) and programs:
        names = [
            str(program.get("name") or program.get("title"))
            for program in programs[:5]
            if isinstance(program, dict) and (program.get("name") or program.get("title"))
        ]
        if names:
            lines.append(f"Saved programs: {', '.join(names)}")

    return "\n".join(lines)


def _finish_workout(client: SupabaseRestClient, *, context: dict[str, Any] | None) -> dict[str, Any]:
    session_id = _current_session_id(context)
    if not session_id:
        return {
            "ok": False,
            "message": "I do not see an active workout to finish.",
            "action_result": None,
            "ui_patch": None,
        }

    session = client.update(
        "workout_sessions",
        {"id": f"eq.{session_id}"},
        {
            "status": "completed",
            "finished_at": _now_iso(),
        },
    )
    summary = _build_workout_summary(client, session_id=session_id, session=session)
    return {
        "ok": True,
        "message": summary["message"],
        "action_result": {**session, "summary": summary},
        "ui_patch": {
            "type": "workout_finished",
            "sessionId": session_id,
            "programId": session.get("program_id") or _active_program_id(context),
            "summary": summary,
        },
    }


def _build_workout_summary(
    client: SupabaseRestClient,
    *,
    session_id: str,
    session: dict[str, Any],
) -> dict[str, Any]:
    """Compute a post-workout summary: volume, sets, exercises, PRs, 1RM estimates."""
    from src.runtime.progression import estimate_1rm

    logs = client.select(
        "workout_exercise_logs",
        {
            "select": "id,exercise_name",
            "session_id": f"eq.{session_id}",
            "order": "exercise_number",
        },
    )
    if not logs:
        return {"message": "Workout finished. No sets were logged.", "exercises": [], "new_prs": []}

    log_ids = [str(log["id"]) for log in logs if log.get("id")]
    sets = client.select(
        "workout_sets",
        {
            "select": "exercise_log_id,set_number,reps,load_value,load_unit",
            "exercise_log_id": _in_filter(log_ids),
            "order": "set_number",
        },
    ) if log_ids else []

    sets_by_log: dict[str, list[dict[str, Any]]] = {}
    for s in sets:
        sets_by_log.setdefault(str(s.get("exercise_log_id")), []).append(s)

    total_sets = 0
    total_volume = 0.0
    exercise_summaries: list[dict[str, Any]] = []
    pr_candidates: list[dict[str, Any]] = []

    for log in logs:
        log_sets = sets_by_log.get(str(log.get("id")), [])
        if not log_sets:
            continue
        total_sets += len(log_sets)
        ex_volume = sum(
            float(s.get("reps") or 0) * float(s.get("load_value") or 0)
            for s in log_sets
        )
        total_volume += ex_volume
        best_set = max(
            log_sets,
            key=lambda s: (float(s.get("load_value") or 0), int(s.get("reps") or 0)),
        )
        best_weight = float(best_set.get("load_value") or 0)
        best_reps = int(best_set.get("reps") or 0)
        est_1rm = estimate_1rm(best_weight, best_reps) if best_weight > 0 and best_reps > 0 else None
        ex_name = str(log.get("exercise_name") or "Unknown")
        exercise_summaries.append({
            "name": ex_name,
            "sets": len(log_sets),
            "best_weight": best_weight if best_weight > 0 else None,
            "best_reps": best_reps if best_reps > 0 else None,
            "estimated_1rm": round(est_1rm, 1) if est_1rm else None,
            "volume": round(ex_volume, 1),
        })
        if best_weight > 0:
            pr_candidates.append({"name": ex_name, "weight": best_weight, "reps": best_reps, "est_1rm": est_1rm})

    # PR detection: compare each exercise's best weight to personal_records
    new_prs: list[str] = []
    for candidate in pr_candidates:
        ex_name = candidate["name"]
        existing = client.select(
            "personal_records",
            {
                "select": "id,value,record_type",
                "exercise_name": f"eq.{ex_name}",
                "record_type": "eq.max_weight",
                "limit": "1",
            },
        )
        current_pr = float(existing[0].get("value") or 0) if existing else 0.0
        if candidate["weight"] > current_pr:
            new_prs.append(ex_name)
            pr_payload: dict[str, Any] = {
                "exercise_name": ex_name,
                "record_type": "max_weight",
                "value": candidate["weight"],
                "unit": "lb",
                "achieved_at": _now_iso(),
            }
            try:
                if existing:
                    client.update(
                        "personal_records",
                        {"id": f"eq.{existing[0]['id']}"},
                        pr_payload,
                    )
                else:
                    user = client.auth_user()
                    if user.get("id"):
                        client.insert("personal_records", {"user_id": user["id"], **pr_payload})
            except Exception:  # noqa: BLE001
                pass  # PR write is best-effort; don't fail the summary

    # Build the spoken summary message
    n_exercises = len(exercise_summaries)
    parts: list[str] = []
    if n_exercises == 1:
        parts.append(f"Workout done — {total_sets} sets of {exercise_summaries[0]['name']}.")
    else:
        parts.append(f"Workout done! {n_exercises} exercises, {total_sets} sets.")
    if total_volume > 0:
        parts.append(f"Total volume: {_format_number(total_volume)} lbs.")
    if new_prs:
        pr_text = " and ".join(new_prs) if len(new_prs) <= 2 else f"{len(new_prs)} new PRs"
        parts.append(f"New PR on {pr_text}!")
    best_1rm = max(
        (ex for ex in exercise_summaries if ex.get("estimated_1rm")),
        key=lambda ex: ex["estimated_1rm"],
        default=None,
    )
    if best_1rm:
        parts.append(
            f"Estimated {best_1rm['name']} 1RM: {_format_number(best_1rm['estimated_1rm'])} lbs."
        )

    return {
        "message": " ".join(parts),
        "exercises": exercise_summaries,
        "total_sets": total_sets,
        "total_volume": round(total_volume, 1),
        "new_prs": new_prs,
    }


def _advance_set(
    client: SupabaseRestClient,
    action: AssistantAction,
    *,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    session_id = _current_session_id(context)
    if not session_id:
        return {
            "ok": False,
            "message": "Start a workout before advancing sets.",
            "action_result": None,
            "ui_patch": None,
        }

    step = _next_workout_step(
        client,
        session_id=session_id,
        program_id=_active_program_id(context),
        day_id=_active_day_id(context),
        action=action,
        context=context,
    )
    if step is None:
        return {
            "ok": True,
            "message": "That looks like the end of the planned workout.",
            "action_result": None,
            "ui_patch": {
                "type": "workout_step_updated",
                "sessionId": session_id,
                "step": None,
            },
        }

    return {
        "ok": True,
        "message": _format_step_message(step, include_coaching_cue=True),
        "action_result": step,
        "ui_patch": {
            "type": "workout_step_updated",
            "sessionId": session_id,
            "step": step,
        },
    }


def _skip_exercise(
    client: SupabaseRestClient,
    action: AssistantAction,
    *,
    context: dict[str, Any] | None,
    finished: bool = False,
) -> dict[str, Any]:
    session_id = _current_session_id(context)
    if not session_id:
        return {
            "ok": False,
            "message": "Start a workout before changing exercises.",
            "action_result": None,
            "ui_patch": None,
        }

    step = _next_exercise_step(client, program_id=_active_program_id(context), day_id=_active_day_id(context), context=context)
    if step is None:
        return {
            "ok": True,
            "message": "That was the last planned exercise.",
            "action_result": None,
            "ui_patch": {"type": "workout_step_updated", "sessionId": session_id, "step": None},
        }

    verb = "Finished" if finished else "Skipped"
    return {
        "ok": True,
        "message": f"{verb}. Next up is {step.get('exerciseName')}, set 1 of {step.get('setCount') or 1}.",
        "action_result": step,
        "ui_patch": {
            "type": "workout_step_updated",
            "sessionId": session_id,
            "step": step,
        },
    }


def _query_workout(
    client: SupabaseRestClient,
    action: AssistantAction,
    *,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    session_id = _current_session_id(context)
    if not session_id:
        return {"ok": False, "message": "I do not see an active workout.", "action_result": None, "ui_patch": None}

    query_type = action.workout_query_type or "current_exercise"
    if query_type == "last_set":
        return _query_last_workout_set(client, action, context=context)

    current = _current_step(context)
    if query_type == "next_exercise":
        step = _next_exercise_step(client, program_id=_active_program_id(context), day_id=_active_day_id(context), context=context)
        if step is None:
            return {"ok": True, "message": "I do not see another planned exercise after this one.", "action_result": None, "ui_patch": None}
        return {
            "ok": True,
            "message": f"Next exercise is {step.get('exerciseName')}, set 1 of {step.get('setCount') or 1}.",
            "action_result": step,
            "ui_patch": None,
        }

    if not current:
        first = _first_program_step(client, _active_program_id(context), day_id=_active_day_id(context))
        if first is None:
            return {"ok": False, "message": "I do not see the current exercise yet.", "action_result": None, "ui_patch": None}
        current = first

    return {
        "ok": True,
        "message": _format_step_message(current).replace("Next up is", "You are on"),
        "action_result": current,
        "ui_patch": None,
    }


def _query_last_workout_set(
    client: SupabaseRestClient,
    action: AssistantAction,
    *,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    session_id = _current_session_id(context)
    exercise_query = normalize_exercise_name(action.exercise_name) or action.exercise_name or _current_step_name(context)
    logs = client.select(
        "workout_exercise_logs",
        {
            "select": "id,session_id,exercise_name",
            "session_id": f"eq.{session_id}",
            "order": "exercise_number",
        },
    )
    matching_logs = [
        log for log in logs
        if not exercise_query or _names_compatible(exercise_query, str(log.get("exercise_name") or ""))
    ]
    if not matching_logs:
        return {"ok": False, "message": f"I do not see logged sets for {exercise_query or 'this exercise'} in this workout.", "action_result": None, "ui_patch": None}

    log_ids = [str(log["id"]) for log in matching_logs if log.get("id")]
    sets = client.select(
        "workout_sets",
        {
            "select": "exercise_log_id,set_number,reps,load_value,load_unit,rpe,status,completed_at",
            "exercise_log_id": _in_filter(log_ids),
            "order": "completed_at.desc.nullslast,set_number.desc",
            "limit": "50",
        },
    )
    if not sets:
        return {"ok": False, "message": f"No sets are logged for {exercise_query or 'this exercise'} yet.", "action_result": None, "ui_patch": None}

    latest = sets[0]
    latest_log = next((log for log in matching_logs if log.get("id") == latest.get("exercise_log_id")), matching_logs[0])
    return {
        "ok": True,
        "message": f"Your last {latest_log.get('exercise_name')} set was {_format_set_summary(latest)}.",
        "action_result": {"exercise_log": latest_log, "set": latest},
        "ui_patch": None,
    }


def _log_set(client: SupabaseRestClient, action: AssistantAction, *, context: dict[str, Any] | None) -> dict[str, Any]:
    session_id = _current_session_id(context)
    requested_exercise_name = action.exercise_name
    exercise_name = requested_exercise_name or _current_step_name(context)
    if not session_id:
        return {"ok": False, "message": "Start a workout before logging sets.", "action_result": None, "ui_patch": None}
    if not exercise_name or action.reps is None:
        return {
            "ok": False,
            "message": "To log a set, I need the exercise and reps.",
            "action_result": None,
            "ui_patch": None,
        }

    program_exercise = _find_program_exercise(client, _active_program_id(context), exercise_name, day_id=_active_day_id(context))
    current_step = _current_step(context)
    current_exercise = _find_program_exercise(
        client,
        _active_program_id(context),
        _current_step_name(context),
        day_id=_active_day_id(context),
    ) if current_step else None

    current_step_name = _current_step_name(context)
    if (
        not action.confirmed_off_current
        and requested_exercise_name
        and current_step_name
        and not _names_compatible(requested_exercise_name, current_step_name)
    ):
        current_name = (current_exercise or {}).get("exercise_name") or current_step_name
        planned_name = (program_exercise or {}).get("exercise_name") or exercise_name
        return {
            "ok": False,
            "message": f"You are currently on {current_name}. Did you mean to log {planned_name} instead?",
            "action_result": {
                "requested_exercise": planned_name,
                "current_exercise": current_name,
                "reps": action.reps,
                "weight": action.weight,
                "needs_confirmation": True,
            },
            "ui_patch": None,
        }

    if not action.confirmed_off_current and requested_exercise_name and current_exercise:
        requested_id = str((program_exercise or {}).get("id") or "")
        current_id = str(current_exercise.get("id") or "")
        requested_matches_current = (
            requested_id
            and current_id
            and requested_id == current_id
        ) or _names_compatible(requested_exercise_name, str(current_exercise.get("exercise_name") or ""))
        if not requested_matches_current:
            current_name = current_exercise.get("exercise_name") or _current_step_name(context) or "the current exercise"
            planned_name = (program_exercise or {}).get("exercise_name") or exercise_name
            return {
                "ok": False,
                "message": f"You are currently on {current_name}. Did you mean to log {planned_name} instead?",
                "action_result": {
                    "requested_exercise": planned_name,
                    "current_exercise": current_name,
                    "reps": action.reps,
                    "weight": action.weight,
                    "needs_confirmation": True,
                },
                "ui_patch": None,
            }

    if program_exercise:
        exercise_name = str(program_exercise.get("exercise_name") or exercise_name)

    log = _get_or_create_exercise_log(
        client,
        session_id=session_id,
        exercise_name=exercise_name,
        program_exercise=program_exercise,
    )
    existing_sets = client.select(
        "workout_sets",
        {
            "select": "set_number",
            "exercise_log_id": f"eq.{log['id']}",
            "order": "set_number",
        },
    )
    set_number = max([int(row.get("set_number") or 0) for row in existing_sets] or [0]) + 1
    logged_set = client.insert(
        "workout_sets",
        {
            "exercise_log_id": log["id"],
            "set_number": set_number,
            "reps": action.reps,
            "load_value": action.weight,
            "load_unit": "lb" if action.weight is not None else "other",
            "status": "manual",
            "completed_at": _now_iso(),
        },
    )
    _increment_session_totals(client, session_id=session_id, reps=action.reps, weight=action.weight)

    message = f"Logged {action.reps} reps of {exercise_name}"
    if action.weight is not None:
        message += f" at {_format_number(action.weight)} pounds"
    message += "."
    next_step = _step_after_logged_set(
        client,
        session_id=session_id,
        program_id=_active_program_id(context),
        day_id=_active_day_id(context),
        logged_exercise_name=exercise_name,
        context=context,
        action=action,
    )
    return {
        "ok": True,
        "message": message,
        "action_result": {"exercise_log": log, "set": logged_set},
        "ui_patch": {
            "type": "set_logged",
            "sessionId": session_id,
            "exerciseName": exercise_name,
            "setNumber": set_number,
            "loggedSet": {
                "exerciseName": exercise_name,
                "setNumber": set_number,
                "reps": action.reps,
                "weight": action.weight,
            },
            "step": next_step,
        },
    }


def _step_after_logged_set(
    client: SupabaseRestClient,
    *,
    session_id: str,
    program_id: str | None,
    day_id: str | None,
    logged_exercise_name: str,
    context: dict[str, Any] | None,
    action: AssistantAction,
) -> dict[str, Any] | None:
    current_step = _current_step(context)
    current_name = _current_step_name(context)
    if current_step and current_name:
        if _names_compatible(logged_exercise_name, current_name):
            return _advance_from_current_step(current_step, _program_exercises(client, program_id, day_id=day_id))
        return current_step

    return _next_workout_step(
        client,
        session_id=session_id,
        program_id=program_id,
        day_id=day_id,
        action=action,
        context=context,
    )


def _get_or_create_exercise_log(
    client: SupabaseRestClient,
    *,
    session_id: str,
    exercise_name: str,
    program_exercise: dict[str, Any] | None = None,
) -> dict[str, Any]:
    logs = client.select(
        "workout_exercise_logs",
        {
            "select": "id,program_exercise_id,exercise_number,exercise_name",
            "session_id": f"eq.{session_id}",
            "order": "exercise_number",
        },
    )
    normalized = _normalize_name(exercise_name)
    for log in logs:
        if (
            _normalize_name(str(log.get("exercise_name") or "")) == normalized
            or (
                program_exercise
                and log.get("program_exercise_id")
                and str(log.get("program_exercise_id")) == str(program_exercise.get("id"))
            )
        ):
            return log

    next_number = max([int(log.get("exercise_number") or 0) for log in logs] or [0]) + 1
    return client.insert(
        "workout_exercise_logs",
        {
            "session_id": session_id,
            "exercise_number": next_number,
            "exercise_name": exercise_name,
            "program_exercise_id": program_exercise.get("id") if program_exercise else None,
        },
    )


def _increment_session_totals(
    client: SupabaseRestClient,
    *,
    session_id: str,
    reps: int,
    weight: float | None,
) -> None:
    rows = client.select(
        "workout_sessions",
        {
            "select": "id,total_sets,total_volume",
            "id": f"eq.{session_id}",
            "limit": "1",
        },
    )
    if not rows:
        return
    current = rows[0]
    added_volume = reps * weight if weight is not None else 0
    client.update(
        "workout_sessions",
        {"id": f"eq.{session_id}"},
        {
            "total_sets": int(current.get("total_sets") or 0) + 1,
            "total_volume": float(current.get("total_volume") or 0) + added_volume,
        },
    )


def _first_program_step(
    client: SupabaseRestClient,
    program_id: str | None,
    *,
    day_id: str | None = None,
) -> dict[str, Any] | None:
    exercises = _program_exercises(client, program_id, day_id=day_id)
    if not exercises:
        return None
    return _step_from_program_exercise(exercises[0], set_number=1)


def _resolve_program(
    client: SupabaseRestClient,
    action: AssistantAction,
    *,
    context: dict[str, Any] | None,
) -> dict[str, Any] | None:
    requested_name = action.program_name
    programs = client.select(
        "programs",
        {
            "select": "id,title,color,created_at",
            "archived_at": "is.null",
            "order": "created_at.desc",
            "limit": "50",
        },
    )

    if requested_name:
        match = _best_named_match(requested_name, programs, name_keys=("title",))
        if match is not None:
            return match

    active_program_id = _active_program_id(context)
    if active_program_id:
        active = next((program for program in programs if program.get("id") == active_program_id), None)
        if active is not None:
            return active

    context_program = _active_program_title(context)
    if context_program:
        match = _best_named_match(context_program, programs, name_keys=("title",))
        if match is not None:
            return match

    return programs[0] if programs else None


def _resolve_program_day(
    client: SupabaseRestClient,
    program_id: str | None,
    *,
    action: AssistantAction,
    context: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not program_id:
        return None

    days = _program_days(client, program_id)
    if not days:
        return None

    requested_day_id = _active_day_id(context)
    if requested_day_id and not (action.day_name or action.day_number or action.week_number):
        active = next((day for day in days if day.get("id") == requested_day_id), None)
        if active is not None:
            return active

    candidates = days
    if action.week_number is not None:
        candidates = [day for day in candidates if int(day.get("week_number") or 1) == action.week_number]

    if action.day_number is not None:
        numbered = next((day for day in candidates if int(day.get("day_number") or 0) == action.day_number), None)
        if numbered is not None:
            return numbered
        if 1 <= action.day_number <= len(candidates):
            return candidates[action.day_number - 1]

    if action.day_name:
        match = _best_named_match(action.day_name, candidates, name_keys=("title",))
        if match is not None:
            return match

    return candidates[0] if candidates else days[0]


def _program_days(client: SupabaseRestClient, program_id: str) -> list[dict[str, Any]]:
    return client.select(
        "program_days",
        {
            "select": "id,week_number,day_number,title",
            "program_id": f"eq.{program_id}",
            "order": "week_number,day_number",
        },
    )


def _day_payload(day: dict[str, Any] | None) -> dict[str, Any] | None:
    if not day:
        return None
    return {
        "id": day.get("id"),
        "title": day.get("title"),
        "weekNumber": day.get("week_number"),
        "dayNumber": day.get("day_number"),
    }


def _next_workout_step(
    client: SupabaseRestClient,
    *,
    session_id: str,
    program_id: str | None,
    day_id: str | None = None,
    action: AssistantAction,
    context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    exercises = _program_exercises(client, program_id, day_id=day_id)
    if action.action == "advance_set":
        current_step = _current_step(context)
        advanced_step = _advance_from_current_step(current_step, exercises)
        if advanced_step is not None:
            return advanced_step

    logs = client.select(
        "workout_exercise_logs",
        {
            "select": "id,program_exercise_id,exercise_number,exercise_name",
            "session_id": f"eq.{session_id}",
            "order": "exercise_number",
        },
    )

    if not exercises:
        if action.exercise_name:
            log = _get_or_create_exercise_log(
                client,
                session_id=session_id,
                exercise_name=action.exercise_name,
            )
            return _step_from_exercise(log, exercise=None, set_number=_next_set_number(client, log["id"]))
        if not logs:
            return None
        latest_log = logs[-1]
        return _step_from_exercise(latest_log, exercise=None, set_number=_next_set_number(client, latest_log["id"]))

    logs_by_program_id = {
        str(log.get("program_exercise_id")): log
        for log in logs
        if log.get("program_exercise_id")
    }
    logs_by_name = {
        _normalize_name(str(log.get("exercise_name") or "")): log
        for log in logs
        if log.get("exercise_name")
    }
    query = normalize_exercise_name(action.exercise_name) or action.exercise_name
    selected_index = 0

    for index, exercise in enumerate(exercises):
        if query and not _names_compatible(query, str(exercise.get("exercise_name") or "")):
            continue
        log = logs_by_program_id.get(str(exercise.get("id"))) or logs_by_name.get(
            _normalize_name(str(exercise.get("exercise_name") or ""))
        )
        completed_sets = _completed_set_count(client, log["id"]) if log else 0
        target_sets = _target_set_count(exercise)
        if completed_sets < target_sets:
            return _step_from_program_exercise(exercise, set_number=completed_sets + 1)
        selected_index = index + 1

    if query:
        return None

    if selected_index < len(exercises):
        return _step_from_program_exercise(exercises[selected_index], set_number=1)
    return None


def _advance_from_current_step(
    current_step: dict[str, Any] | None,
    exercises: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not isinstance(current_step, dict):
        return None

    set_number = int(current_step.get("setNumber") or 1)
    set_count = int(current_step.get("setCount") or 1)
    if set_number < set_count:
        return {**current_step, "setNumber": set_number + 1}

    current_name = str(current_step.get("exerciseName") or "")
    if not exercises or not current_name:
        return current_step

    for index, exercise in enumerate(exercises):
        if _names_compatible(current_name, str(exercise.get("exercise_name") or "")):
            next_index = index + 1
            if next_index >= len(exercises):
                return None
            return _step_from_program_exercise(exercises[next_index], set_number=1)

    return None


def _next_exercise_step(
    client: SupabaseRestClient,
    *,
    program_id: str | None,
    day_id: str | None = None,
    context: dict[str, Any] | None,
) -> dict[str, Any] | None:
    exercises = _program_exercises(client, program_id, day_id=day_id)
    current = _current_step(context)
    if not exercises:
        return None
    if not current:
        return _step_from_program_exercise(exercises[0], set_number=1)

    current_name = str(current.get("exerciseName") or "")
    for index, exercise in enumerate(exercises):
        if _names_compatible(current_name, str(exercise.get("exercise_name") or "")):
            next_index = index + 1
            if next_index >= len(exercises):
                return None
            return _step_from_program_exercise(exercises[next_index], set_number=1)
    return _step_from_program_exercise(exercises[0], set_number=1)


def _program_exercises(
    client: SupabaseRestClient,
    program_id: str | None,
    *,
    day_id: str | None = None,
) -> list[dict[str, Any]]:
    if not program_id:
        return []

    days = _program_days(client, program_id)
    day_ids = [str(day_id)] if day_id else [str(day["id"]) for day in days if day.get("id")]
    if not day_ids:
        return []

    blocks = client.select(
        "program_blocks",
        {
            "select": "id,day_id,block_number,title,execution_style",
            "day_id": _in_filter(day_ids),
            "order": "block_number",
        },
    )
    block_ids = [str(block["id"]) for block in blocks if block.get("id")]
    if not block_ids:
        return []

    exercises = client.select(
        "program_exercises",
        {
            "select": "id,block_id,exercise_number,exercise_name,set_count,rep_target,load_target,rest_seconds,notes",
            "block_id": _in_filter(block_ids),
            "order": "exercise_number",
        },
    )
    block_order = {str(block["id"]): index for index, block in enumerate(blocks) if block.get("id")}
    return sorted(
        exercises,
        key=lambda exercise: (
            block_order.get(str(exercise.get("block_id")), 9999),
            int(exercise.get("exercise_number") or 0),
        ),
    )


def _find_program_exercise(
    client: SupabaseRestClient,
    program_id: str | None,
    exercise_name: str | None,
    *,
    day_id: str | None = None,
) -> dict[str, Any] | None:
    exercises = _program_exercises(client, program_id, day_id=day_id)
    if not exercises:
        return None
    if not exercise_name:
        return exercises[0]

    query = normalize_exercise_name(exercise_name) or exercise_name
    return next(
        (
            exercise
            for exercise in exercises
            if _names_compatible(query, str(exercise.get("exercise_name") or ""))
        ),
        None,
    )


def _best_named_match(
    query: str,
    rows: list[dict[str, Any]],
    *,
    name_keys: tuple[str, ...],
) -> dict[str, Any] | None:
    normalized_query = _normalize_name(query)
    if not normalized_query:
        return None

    best_row: dict[str, Any] | None = None
    best_score = 0.0
    for row in rows:
        for key in name_keys:
            name = _normalize_name(str(row.get(key) or ""))
            if not name:
                continue
            if normalized_query == name:
                return row
            if normalized_query in name or name in normalized_query:
                score = 0.95
            else:
                score = SequenceMatcher(None, normalized_query, name).ratio()
            if score > best_score:
                best_score = score
                best_row = row

    return best_row if best_score >= 0.68 else None


def _completed_set_count(client: SupabaseRestClient, exercise_log_id: str) -> int:
    rows = client.select(
        "workout_sets",
        {
            "select": "id",
            "exercise_log_id": f"eq.{exercise_log_id}",
        },
    )
    return len(rows)


def _next_set_number(client: SupabaseRestClient, exercise_log_id: str) -> int:
    rows = client.select(
        "workout_sets",
        {
            "select": "set_number",
            "exercise_log_id": f"eq.{exercise_log_id}",
            "order": "set_number",
        },
    )
    return max([int(row.get("set_number") or 0) for row in rows] or [0]) + 1


def _target_set_count(exercise: dict[str, Any] | None) -> int:
    if not exercise:
        return 1
    return max(int(exercise.get("set_count") or 1), 1)


def _step_from_program_exercise(exercise: dict[str, Any], *, set_number: int) -> dict[str, Any]:
    return _step_from_exercise(
        {
            "program_exercise_id": exercise.get("id"),
            "exercise_number": exercise.get("exercise_number"),
            "exercise_name": exercise.get("exercise_name"),
        },
        exercise=exercise,
        set_number=set_number,
    )


def _step_from_exercise(
    log: dict[str, Any],
    *,
    exercise: dict[str, Any] | None,
    set_number: int,
) -> dict[str, Any]:
    target_sets = _target_set_count(exercise)
    return {
        "exerciseLogId": log.get("id"),
        "programExerciseId": log.get("program_exercise_id") or (exercise.get("id") if exercise else None),
        "exerciseNumber": log.get("exercise_number") or (exercise.get("exercise_number") if exercise else None),
        "exerciseName": log.get("exercise_name") or (exercise.get("exercise_name") if exercise else None),
        "setNumber": set_number,
        "setCount": target_sets,
        "repTarget": exercise.get("rep_target") if exercise else None,
        "loadTarget": exercise.get("load_target") if exercise else None,
        "restSeconds": exercise.get("rest_seconds") if exercise else None,
        "notes": exercise.get("notes") if exercise else None,
    }


def _format_prescription(rep_target: Any, load_target: Any) -> str:
    """Spoken prescription fragment from freeform rep/load targets. Both optional."""
    reps = str(rep_target).strip() if rep_target not in (None, "") else ""
    load = str(load_target).strip() if load_target not in (None, "") else ""
    fragments: list[str] = []
    if reps:
        if re.fullmatch(r"\d+(\s*[-–]\s*\d+)?", reps):
            fragments.append(f"{reps} reps")
        else:
            fragments.append(reps)
    if load:
        spoken = "bodyweight" if load.lower() in {"bw", "bodyweight"} else load
        fragments.append(f"at {spoken}")
    return " ".join(fragments)


def _format_step_message(step: dict[str, Any], include_coaching_cue: bool = False) -> str:
    exercise = step.get("exerciseName") or "the next exercise"
    set_number = step.get("setNumber")
    set_count = step.get("setCount")

    if set_number and set_count:
        base = f"Next up is {exercise}, set {set_number} of {set_count}"
    else:
        base = f"Next up is {exercise}"

    if not include_coaching_cue:
        return base + "."

    prescription = _format_prescription(step.get("repTarget"), step.get("loadTarget"))
    if prescription:
        base = f"{base}, {prescription}"
    base += "."

    cue = coaching_cue_for(step.get("exerciseName"), step.get("notes"))
    return f"{base} {cue}" if cue else base


def _current_step(context: dict[str, Any] | None) -> dict[str, Any] | None:
    current = context.get("currentWorkout") if isinstance(context, dict) else None
    if isinstance(current, dict) and isinstance(current.get("step"), dict):
        return current["step"]
    return None


def _current_step_name(context: dict[str, Any] | None) -> str | None:
    step = _current_step(context)
    if not step:
        return None
    return step.get("exerciseName") or step.get("exercise_name")


def _current_rest_seconds(context: dict[str, Any] | None) -> int | None:
    step = _current_step(context)
    if not step:
        return None
    rest_seconds = step.get("restSeconds")
    return int(rest_seconds) if rest_seconds is not None else None


def _history_set_rows(client: SupabaseRestClient, *, exercise_query: str) -> list[dict[str, Any]]:
    sessions = client.select(
        "workout_sessions",
        {
            "select": "id,title,started_at,created_at",
            "order": "started_at.desc.nullslast,created_at.desc",
            "limit": "200",
        },
    )
    session_ids = [str(session["id"]) for session in sessions if session.get("id")]
    if not session_ids:
        return []

    logs = client.select(
        "workout_exercise_logs",
        {
            "select": "id,session_id,exercise_name",
            "session_id": _in_filter(session_ids),
        },
    )
    matching_logs = [
        log for log in logs
        if _names_compatible(exercise_query, str(log.get("exercise_name") or ""))
    ]
    log_ids = [str(log["id"]) for log in matching_logs if log.get("id")]
    if not log_ids:
        return []

    sets = client.select(
        "workout_sets",
        {
            "select": "exercise_log_id,set_number,reps,load_value,load_unit,rpe,status,completed_at",
            "exercise_log_id": _in_filter(log_ids),
            "order": "completed_at.desc.nullslast,set_number.desc",
            "limit": "500",
        },
    )
    sessions_by_id = {str(session["id"]): session for session in sessions if session.get("id")}
    logs_by_id = {str(log["id"]): log for log in matching_logs if log.get("id")}
    rows = []
    for logged_set in sets:
        log = logs_by_id.get(str(logged_set.get("exercise_log_id")))
        if not log:
            continue
        session = sessions_by_id.get(str(log.get("session_id"))) or {}
        rows.append({"session": session, "log": log, "set": logged_set})
    return rows


def _filter_history_sets(rows: list[dict[str, Any]], action: AssistantAction) -> list[dict[str, Any]]:
    filtered = []
    for row in rows:
        logged_set = row["set"]
        reps = logged_set.get("reps")
        load = logged_set.get("load_value")
        if action.reps is not None and reps != action.reps:
            continue
        if action.min_reps is not None and (reps is None or int(reps) < action.min_reps):
            continue
        if action.max_reps is not None and (reps is None or int(reps) > action.max_reps):
            continue
        if action.weight is not None and (load is None or float(load) != float(action.weight)):
            continue
        if action.min_weight is not None and (load is None or float(load) < action.min_weight):
            continue
        if action.max_weight is not None and (load is None or float(load) > action.max_weight):
            continue
        filtered.append(row)
    return filtered


def _format_no_history_match(exercise_query: str, action: AssistantAction) -> str:
    filters = []
    if action.reps is not None:
        filters.append(f"{action.reps} reps")
    if action.min_weight is not None:
        filters.append(f"{_format_number(action.min_weight)} pounds or more")
    if action.weight is not None:
        filters.append(f"{_format_number(action.weight)} pounds")
    suffix = f" matching {' and '.join(filters)}" if filters else ""
    return f"I do not see {exercise_query} sets{suffix} yet."


def _format_max_reps_answer(row: dict[str, Any], action: AssistantAction) -> str:
    logged_set = row["set"]
    exercise = row["log"].get("exercise_name") or action.exercise_name or "that exercise"
    load = logged_set.get("load_value")
    unit = logged_set.get("load_unit") or "lb"
    date = _format_date(logged_set.get("completed_at") or row["session"].get("started_at"))
    if load is None:
        return f"The most reps I see for {exercise} in one set is {logged_set.get('reps')}, from {date}."
    return (
        f"The most reps I see for {exercise}"
        f"{_format_weight_filter_tail(action)} is {logged_set.get('reps')} reps"
        f" at {_format_number(load)} {unit}, from {date}."
    )


def _format_max_weight_answer(row: dict[str, Any], action: AssistantAction) -> str:
    logged_set = row["set"]
    exercise = row["log"].get("exercise_name") or action.exercise_name or "that exercise"
    unit = logged_set.get("load_unit") or "lb"
    date = _format_date(logged_set.get("completed_at") or row["session"].get("started_at"))
    reps_tail = f" for {logged_set.get('reps')} reps" if logged_set.get("reps") is not None else ""
    if action.reps is not None:
        return f"Your best {action.reps}-rep {exercise} is {_format_number(logged_set.get('load_value'))} {unit}, from {date}."
    return f"The heaviest {exercise} set I see is {_format_number(logged_set.get('load_value'))} {unit}{reps_tail}, from {date}."


def _format_max_volume_answer(row: dict[str, Any]) -> str:
    logged_set = row["set"]
    exercise = row["log"].get("exercise_name") or "that exercise"
    unit = logged_set.get("load_unit") or "lb"
    volume = _set_volume(row)
    date = _format_date(logged_set.get("completed_at") or row["session"].get("started_at"))
    return (
        f"Your highest-volume {exercise} set is {_format_number(volume)} {unit}-reps: "
        f"{logged_set.get('reps')} reps at {_format_number(logged_set.get('load_value'))} {unit}, from {date}."
    )


def _format_last_time_answer(row: dict[str, Any]) -> str:
    logged_set = row["set"]
    exercise = row["log"].get("exercise_name") or "that exercise"
    return f"Last time I see {exercise}: {_format_set_summary(logged_set)} on {_format_date(logged_set.get('completed_at') or row['session'].get('started_at'))}."


def _format_recent_sets_answer(row: dict[str, Any]) -> str:
    logged_set = row["set"]
    exercise = row["log"].get("exercise_name") or "that exercise"
    return f"Most recently for {exercise}, I see {_format_set_summary(logged_set)}."


def _format_weight_filter_tail(action: AssistantAction) -> str:
    if action.min_weight is not None:
        return f" with at least {_format_number(action.min_weight)} pounds"
    if action.weight is not None:
        return f" at {_format_number(action.weight)} pounds"
    return ""


def _set_volume(row: dict[str, Any]) -> float:
    logged_set = row["set"]
    return float(logged_set.get("reps") or 0) * float(logged_set.get("load_value") or 0)


def _sort_date(value: Any) -> str:
    return str(value or "")


def _get_supabase_config() -> SupabaseConfig:
    return SupabaseConfig(
        url=os.getenv("SUPABASE_URL") or os.getenv("TRAINAR_SUPABASE_URL") or DEFAULT_SUPABASE_URL,
        anon_key=os.getenv("SUPABASE_ANON_KEY") or os.getenv("TRAINAR_SUPABASE_KEY") or DEFAULT_SUPABASE_KEY,
    )


def _current_session_id(context: dict[str, Any] | None) -> str | None:
    current = context.get("currentWorkout") if isinstance(context, dict) else None
    if isinstance(current, dict):
        return current.get("sessionId") or current.get("session_id")
    return None


def _active_program_id(context: dict[str, Any] | None) -> str | None:
    return context.get("activeProgramId") if isinstance(context, dict) else None


def _active_day_id(context: dict[str, Any] | None) -> str | None:
    current = context.get("currentWorkout") if isinstance(context, dict) else None
    if isinstance(current, dict):
        day = current.get("day")
        if isinstance(day, dict):
            return day.get("id") or day.get("dayId") or day.get("day_id")
        return current.get("dayId") or current.get("day_id")
    return None


def _active_program_title(context: dict[str, Any] | None) -> str | None:
    program = context.get("activeProgram") if isinstance(context, dict) else None
    if isinstance(program, dict):
        return program.get("name") or program.get("title")
    current = context.get("currentWorkout") if isinstance(context, dict) else None
    if isinstance(current, dict):
        return current.get("title") or current.get("programName")
    return None


def _normalize_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _names_compatible(query: str, value: str) -> bool:
    left = _normalize_name(query)
    right = _normalize_name(value)
    if not left or not right:
        return False
    if left in right or right in left:
        return True
    return SequenceMatcher(None, left, right).ratio() >= 0.72


def _in_filter(values: list[str]) -> str:
    return f"in.({','.join(values)})"


def _format_set_summary(logged_set: dict[str, Any]) -> str:
    reps = logged_set.get("reps")
    load = logged_set.get("load_value")
    unit = logged_set.get("load_unit") or "lb"
    if load is None:
        return f"{reps} reps"
    return f"{reps} reps at {_format_number(load)} {unit}"


def _format_date(value: Any) -> str:
    if not value:
        return "recently"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    local = parsed.astimezone(APP_TIME_ZONE)
    return f"{local:%b} {local.day}"


def _format_number(value: Any) -> str:
    numeric = float(value)
    return str(int(numeric)) if numeric.is_integer() else str(numeric)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
