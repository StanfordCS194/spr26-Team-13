"""Assistant service for parsing messages and executing deterministic tools."""

from __future__ import annotations

import json
import os
import re
from typing import TYPE_CHECKING, Any

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

if TYPE_CHECKING:
    from openai import OpenAI as OpenAIClient

from src.assistant import tools
from src.assistant.backend import DEFAULT_USER_ID, normalize_exercise_name
from src.assistant.models import AssistantAction
from src.assistant.prompts import SYSTEM_PROMPT

if load_dotenv is not None:
    load_dotenv()

DEFAULT_ASSISTANT_MODEL = "gpt-4.1-mini"
CONTEXT_EXERCISE_MARKERS = {"this exercise", "current exercise", "active exercise", "this lift"}


class AssistantUnavailableError(RuntimeError):
    """Raised when the configured LLM assistant cannot return an action."""


def build_openai_client() -> "OpenAIClient | None":
    """Build an OpenAI client when an API key is configured."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def parse_user_message(
    message: str,
    *,
    user_id: str | None = None,
    session_id: str | None = None,
    active_exercise_name: str | None = None,
    context: dict[str, Any] | None = None,
    client: "OpenAIClient | None" = None,
) -> AssistantAction:
    """Parse a user message into a structured assistant action."""

    cleaned_message = message.strip()
    if not cleaned_message:
        return AssistantAction(action="unknown", user_id=user_id, session_id=session_id)

    openai_client = client if client is not None else build_openai_client()
    if openai_client is None:
        return _parse_user_message_locally(
            cleaned_message,
            user_id=user_id,
            session_id=session_id,
            active_exercise_name=active_exercise_name,
        )

    input_payload = {
        "message": cleaned_message,
        "context": {
            "user_id": user_id,
            "session_id": session_id,
            "active_exercise_name": active_exercise_name,
            "app_context": context,
        },
    }
    try:
        response = openai_client.responses.parse(
            model=os.getenv("OPENAI_ASSISTANT_MODEL", DEFAULT_ASSISTANT_MODEL),
            instructions=SYSTEM_PROMPT,
            input=json.dumps(input_payload),
            text_format=AssistantAction,
            temperature=0,
            max_output_tokens=500,
        )
    except Exception as exc:
        raise AssistantUnavailableError(f"Assistant model request failed: {exc}") from exc

    parsed_action = response.output_parsed
    if parsed_action is None:
        raise AssistantUnavailableError("Assistant model returned no structured action.")
    return _with_context(
        parsed_action,
        user_id=user_id,
        session_id=session_id,
        active_exercise_name=active_exercise_name,
    )


def handle_message(
    message: str,
    *,
    user_id: str | None = None,
    session_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse a message, execute the matching tool, and format a response."""

    resolved_user_id = user_id or DEFAULT_USER_ID
    active_exercise_name = tools.get_active_exercise_name(resolved_user_id, session_id)
    try:
        action = parse_user_message(
            message,
            user_id=resolved_user_id,
            session_id=session_id,
            active_exercise_name=active_exercise_name,
            context=context,
        )
    except AssistantUnavailableError as exc:
        action = _parse_user_message_locally(
            message,
            user_id=resolved_user_id,
            session_id=session_id,
            active_exercise_name=active_exercise_name,
        )
        if action.action == "unknown":
            context_result = _answer_from_context(context)
            if context_result is not None:
                return _build_response(
                    response=_format_response(action, context_result, context=context),
                    action=action,
                    tool_result=context_result,
                    display_state=tools.get_display_state(session_id),
                )
            return _build_response(
                response="The assistant model is unavailable, and I could not understand that command locally.",
                action=action,
                tool_result={"ok": False, "status": "assistant_unavailable", "message": str(exc)},
                display_state=tools.get_display_state(session_id),
            )

    action = _with_context(
        action,
        user_id=resolved_user_id,
        session_id=session_id,
        active_exercise_name=active_exercise_name,
    )
    result = _execute_action(action, context=context)
    display_state = result.pop("display_state", None) or tools.get_display_state(action.session_id or session_id)
    return _build_response(
        response=_format_response(action, result, context=context),
        action=action,
        tool_result=result,
        display_state=display_state,
    )


def _build_response(
    *,
    response: str,
    action: AssistantAction,
    tool_result: dict[str, Any],
    display_state: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "response": response,
        "action": action.model_dump(mode="json"),
        "tool_result": tool_result,
        "display_state": display_state,
    }


def _execute_action(
    action: AssistantAction,
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if action.action == "get_pr":
        contextual_pr = _get_contextual_pr(action.exercise_name, context=context)
        if contextual_pr is not None:
            return contextual_pr
        return tools.get_pr(action.user_id, action.exercise_name)
    if action.action == "get_recent_exercise_history":
        return tools.get_recent_exercise_history(action.user_id, action.exercise_name)
    if action.action == "log_set":
        return tools.log_set(
            action.user_id,
            action.session_id,
            action.exercise_name,
            action.reps,
            action.weight,
            unit=action.unit,
            notes=action.notes,
            target_rpe=action.target_rpe,
        )
    if action.action == "start_workout":
        return tools.start_workout(action.user_id, program_id=action.program_id)
    if action.action == "start_next_set":
        return tools.start_next_set(action.user_id, action.session_id)
    if action.action == "start_next_exercise":
        return tools.start_next_exercise(action.user_id, action.session_id)
    if action.action == "start_exercise":
        return tools.start_exercise(action.user_id, action.session_id, action.exercise_name)
    if action.action == "add_exercise":
        return tools.add_exercise(
            action.user_id,
            action.session_id,
            action.exercise_name,
            sets=action.sets,
            reps=action.reps,
            weight=action.weight,
            unit=action.unit,
            notes=action.notes,
            target_rpe=action.target_rpe,
        )
    if action.action == "start_rest":
        return tools.start_rest(action.user_id, action.session_id, action.duration_seconds)
    if action.action == "finish_workout":
        return tools.finish_workout(action.user_id, action.session_id)
    context_result = _answer_from_context(context)
    if context_result is not None:
        return context_result
    return {
        "ok": False,
        "status": "unknown",
        "message": "I can help with PRs, recent exercise history, logging sets, starting exercises, rest timers, and finishing workouts.",
    }


def _format_response(
    action: AssistantAction,
    result: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> str:
    if not result.get("ok"):
        return str(result.get("message") or "I could not handle that workout request yet.")

    if result.get("status") == "context_answer":
        return str(result["message"])
    if action.action == "get_pr":
        display_name = result.get("display_name") or result["exercise_name"]
        unit = result.get("unit") or action.unit or "lb"
        return (
            f"Your {display_name} PR is "
            f"{_format_weight(result['weight'])} {unit}"
            f"{_format_reps_tail(result)}."
        )
    if action.action == "get_recent_exercise_history":
        latest = result["history"][0]
        unit = latest.get("unit") or "lb"
        return (
            f"Last time for {result['exercise_name']}, you did "
            f"{latest['reps']} reps at {_format_weight(latest['weight'])} {unit}."
        )
    if action.action == "log_set":
        unit = result.get("unit") or action.unit or "lb"
        weight_text = f" at {_format_weight(result['weight'])} {unit}" if result.get("weight") is not None else ""
        return f"Logged {result['reps']} reps of {result['exercise_name']}{weight_text}."
    if action.action == "start_workout":
        return "Workout started."
    if action.action == "start_next_set":
        return f"Starting set {result['set_number']} of {result['exercise_name']}."
    if action.action == "start_next_exercise":
        return f"Starting your next exercise: {result['exercise_name']}."
    if action.action == "start_exercise":
        return f"Starting {result['exercise_name']}."
    if action.action == "add_exercise":
        return f"Added {result['exercise_name']} to this workout."
    if action.action == "start_rest":
        return f"Starting a {result['duration_seconds']}-second rest."
    if action.action == "finish_workout":
        return "Workout finished."
    return "I can help with that once the action is supported."


def _get_contextual_pr(
    exercise_name: str | None,
    *,
    context: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not context:
        return None

    prs = context.get("personalRecords")
    if not isinstance(prs, list):
        return None

    normalized_query = tools.normalize_exercise_name(exercise_name)
    candidates = []
    for record in prs:
        if not isinstance(record, dict):
            continue
        name = str(record.get("exercise_name") or record.get("exerciseName") or "").strip()
        if not name:
            continue
        normalized_name = tools.normalize_exercise_name(name) or name.lower()
        if normalized_query and normalized_query not in normalized_name and normalized_name not in normalized_query:
            continue
        candidates.append(record)

    if not candidates and normalized_query:
        return {
            "ok": False,
            "status": "not_found",
            "exercise_name": normalized_query,
            "message": f"I do not see a saved PR for {normalized_query} in your account yet.",
        }
    if not candidates:
        return None

    record = candidates[0]
    value = record.get("value") or record.get("weight")
    if value is None:
        return None

    return {
        "ok": True,
        "status": "found",
        "exercise_name": str(record.get("exercise_name") or record.get("exerciseName") or normalized_query),
        "display_name": str(record.get("exercise_name") or record.get("exerciseName") or normalized_query),
        "weight": float(value),
        "unit": str(record.get("unit") or "lb"),
        "reps": record.get("reps"),
    }


def _answer_from_context(context: dict[str, Any] | None) -> dict[str, Any] | None:
    if not context:
        return None

    active_program = context.get("activeProgram") if isinstance(context.get("activeProgram"), dict) else None
    current_workout = context.get("currentWorkout") if isinstance(context.get("currentWorkout"), dict) else None
    programs = context.get("programs") if isinstance(context.get("programs"), list) else []
    sessions = context.get("recentSessions") if isinstance(context.get("recentSessions"), list) else []

    if current_workout:
        title = current_workout.get("title") or current_workout.get("programName") or "this workout"
        return {
            "ok": True,
            "status": "context_answer",
            "message": f"You are in {title}. Keep the next set controlled and tell me the reps and weight when you finish.",
        }

    if active_program:
        name = active_program.get("name") or active_program.get("title") or "your active program"
        exercises = active_program.get("exercises") if isinstance(active_program.get("exercises"), list) else []
        first = exercises[0].get("name") if exercises and isinstance(exercises[0], dict) else None
        if first:
            message = f"Your next programmed move is {first} from {name}. Start it when you are ready."
        else:
            message = f"{name} is loaded. Start the workout when you are ready and I will track the flow."
        return {"ok": True, "status": "context_answer", "message": message}

    if programs:
        names = [str(program.get("name") or program.get("title")) for program in programs[:3] if isinstance(program, dict)]
        return {
            "ok": True,
            "status": "context_answer",
            "message": f"You have {len(programs)} saved program{'s' if len(programs) != 1 else ''}. I see {', '.join(names)}.",
        }

    if sessions:
        return {
            "ok": True,
            "status": "context_answer",
            "message": f"I see {len(sessions)} recent workout{'s' if len(sessions) != 1 else ''}. Ask me about a PR or start a workout when ready.",
        }

    return {
        "ok": True,
        "status": "context_answer",
        "message": "I do not see saved training data for this account yet. Add a program, then I can coach from it.",
    }


def _parse_user_message_locally(
    message: str,
    *,
    user_id: str | None = None,
    session_id: str | None = None,
    active_exercise_name: str | None = None,
) -> AssistantAction:
    """Small deterministic fallback for local demos without an API key."""

    text = message.lower().strip()
    exercise_name = _extract_exercise_name(text)
    if _mentions_current_exercise(text):
        exercise_name = active_exercise_name

    base = {
        "user_id": user_id,
        "session_id": session_id,
        "exercise_name": exercise_name,
        "unit": _extract_unit(text),
    }

    if _looks_like_recent_history_query(text):
        return AssistantAction(action="get_recent_exercise_history", **base)
    if _looks_like_pr_query(text):
        return AssistantAction(action="get_pr", **base)
    if "finish" in text and "workout" in text:
        return AssistantAction(action="finish_workout", user_id=user_id, session_id=session_id)
    if "start" in text and "workout" in text:
        return AssistantAction(action="start_workout", user_id=user_id, session_id=session_id)
    if "next set" in text:
        return AssistantAction(action="start_next_set", user_id=user_id, session_id=session_id)
    if "next exercise" in text or "next lift" in text:
        return AssistantAction(action="start_next_exercise", user_id=user_id, session_id=session_id)
    if _looks_like_rest_request(text):
        return AssistantAction(
            action="start_rest",
            user_id=user_id,
            session_id=session_id,
            duration_seconds=_extract_duration_seconds(text),
        )
    if _looks_like_add_exercise(text):
        return AssistantAction(
            action="add_exercise",
            user_id=user_id,
            session_id=session_id,
            exercise_name=exercise_name,
            sets=_extract_sets(text),
            reps=_extract_reps(text),
            weight=_extract_weight(text),
            unit=_extract_unit(text),
        )
    if _looks_like_log_set(text):
        return AssistantAction(
            action="log_set",
            user_id=user_id,
            session_id=session_id,
            exercise_name=exercise_name,
            reps=_extract_reps(text),
            weight=_extract_weight(text),
            unit=_extract_unit(text),
        )
    if "start" in text and exercise_name:
        return AssistantAction(action="start_exercise", **base)

    return AssistantAction(action="unknown", user_id=user_id, session_id=session_id)


def _with_context(
    action: AssistantAction,
    *,
    user_id: str | None,
    session_id: str | None,
    active_exercise_name: str | None,
) -> AssistantAction:
    exercise_name = action.exercise_name
    if exercise_name and exercise_name.strip().lower() in CONTEXT_EXERCISE_MARKERS:
        exercise_name = active_exercise_name
    if not exercise_name and action.action in {"get_pr", "get_recent_exercise_history", "log_set"}:
        exercise_name = active_exercise_name
    if exercise_name:
        exercise_name = normalize_exercise_name(exercise_name)

    unit = action.unit
    if unit is None and action.weight is not None:
        unit = "lb"

    return action.model_copy(
        update={
            "user_id": action.user_id or user_id,
            "session_id": action.session_id or session_id,
            "exercise_name": exercise_name,
            "unit": unit,
        }
    )


def _looks_like_pr_query(text: str) -> bool:
    return "pr" in text or "personal record" in text or "max" in text


def _looks_like_recent_history_query(text: str) -> bool:
    return any(phrase in text for phrase in ("last time", "last week", "recent", "what weight did i use"))


def _looks_like_rest_request(text: str) -> bool:
    return "rest" in text or "timer" in text


def _looks_like_log_set(text: str) -> bool:
    return any(term in text for term in ("log", "record", "got", "completed")) and (
        "set" in text or _extract_reps(text) is not None
    )


def _looks_like_add_exercise(text: str) -> bool:
    return "add" in text and ("exercise" in text or "lift" in text or _extract_exercise_name(text) is not None)


def _mentions_current_exercise(text: str) -> bool:
    return any(marker in text for marker in CONTEXT_EXERCISE_MARKERS)


def _extract_exercise_name(text: str) -> str | None:
    for alias, canonical in sorted(tools.EXERCISE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return canonical
    return None


def _extract_duration_seconds(text: str) -> int | None:
    minute_match = re.search(r"(\d+)\s*(?:minute|minutes|min|mins)\b", text)
    if minute_match:
        return int(minute_match.group(1)) * 60

    second_match = re.search(r"(\d+)\s*(?:second|seconds|sec|secs|s)\b", text)
    if second_match:
        return int(second_match.group(1))

    bare_rest_match = re.search(r"rest(?:\s+for)?\s+(\d+)\b", text)
    if bare_rest_match:
        return int(bare_rest_match.group(1))

    return None


def _extract_sets(text: str) -> int | None:
    sets_match = re.search(r"(\d+)\s*(?:set|sets)\b", text)
    if sets_match:
        return int(sets_match.group(1))
    return None


def _extract_reps(text: str) -> int | None:
    reps_match = re.search(r"(\d+)\s*(?:rep|reps)\b", text)
    if reps_match:
        return int(reps_match.group(1))

    sets_of_match = re.search(r"\bsets?\s+of\s+(\d+)\b", text)
    if sets_of_match:
        return int(sets_of_match.group(1))

    by_match = re.search(r"(?:sets?\s+of\s+)?(\d+)\s*(?:by|x)\b", text)
    if by_match:
        return int(by_match.group(1))

    compact_match = re.search(r"\bx\s*(\d+)\b", text)
    if compact_match:
        return int(compact_match.group(1))

    return None


def _extract_weight(text: str) -> float | None:
    weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lb|lbs|pound|pounds|kg|kgs|kilogram|kilograms)\b", text)
    if weight_match:
        return float(weight_match.group(1))

    at_match = re.search(r"\bat\s+(\d+(?:\.\d+)?)\b", text)
    if at_match:
        return float(at_match.group(1))

    return None


def _extract_unit(text: str) -> str | None:
    if re.search(r"\b(?:kg|kgs|kilogram|kilograms)\b", text):
        return "kg"
    if re.search(r"\b(?:lb|lbs|pound|pounds)\b", text):
        return "lb"
    return None


def _format_weight(weight: float | int) -> str:
    return str(int(weight)) if float(weight).is_integer() else str(weight)


def _format_reps_tail(result: dict[str, Any]) -> str:
    reps = result.get("reps")
    if reps is None:
        return ""
    suffix = "rep" if reps == 1 else "reps"
    return f" for {reps} {suffix}"
