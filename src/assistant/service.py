"""Assistant service for parsing messages and executing deterministic tools."""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING
from typing import Any

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

from src.assistant.models import AssistantAction
from src.assistant.prompts import SYSTEM_PROMPT
from src.assistant import tools

if load_dotenv is not None:
    load_dotenv()

DEFAULT_ASSISTANT_MODEL = "gpt-4.1-mini"


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
    client: "OpenAIClient | None" = None,
) -> AssistantAction:
    """Parse a user message into a structured assistant action."""

    cleaned_message = message.strip()
    if not cleaned_message:
        return AssistantAction(action="unknown")

    openai_client = client if client is not None else build_openai_client()
    if openai_client is None:
        return _parse_user_message_locally(cleaned_message)

    response = openai_client.responses.parse(
        model=os.getenv("OPENAI_ASSISTANT_MODEL", DEFAULT_ASSISTANT_MODEL),
        instructions=SYSTEM_PROMPT,
        input=cleaned_message,
        text_format=AssistantAction,
        temperature=0,
        max_output_tokens=400,
    )
    parsed_action = response.output_parsed
    if parsed_action is None:
        raise AssistantUnavailableError("OpenAI assistant returned no structured action.")
    return parsed_action


def handle_message(message: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Parse a message, execute the matching tool, and format a response."""

    action = parse_user_message(message)
    result = _execute_action(action, context=context)
    return {
        "response": _format_response(action, result, context=context),
        "action": action.model_dump(mode="json"),
    }


def _execute_action(action: AssistantAction, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    if action.action == "get_pr":
        contextual_pr = _get_contextual_pr(action.exercise_name, context=context)
        if contextual_pr is not None:
            return contextual_pr
        return tools.get_pr(action.exercise_name)
    if action.action == "log_set":
        return tools.log_set(action.exercise_name, action.reps, action.weight)
    if action.action == "start_workout":
        return tools.start_workout()
    if action.action == "start_exercise":
        return tools.start_exercise(action.exercise_name)
    if action.action == "start_rest":
        return tools.start_rest(action.duration_seconds)
    if action.action == "finish_workout":
        return tools.finish_workout()
    if context:
        return _answer_from_context(context)
    return {
        "ok": False,
        "status": "unknown",
        "message": "I can help with PRs, logging sets, starting exercises, rest timers, and finishing workouts.",
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
        display_name = (result.get("display_name") if result.get("unit") else None) or result["exercise_name"]
        return (
            f"Your {display_name} PR is "
            f"{_format_weight(result['weight'])} {result.get('unit') or 'pounds'}"
            f"{_format_reps_tail(result)}."
        )
    if action.action == "log_set":
        return (
            f"Logged {result['reps']} reps of {result['exercise_name']} "
            f"at {_format_weight(result['weight'])} pounds."
        )
    if action.action == "start_workout":
        return "Workout started."
    if action.action == "start_exercise":
        return f"Starting {result['exercise_name']}."
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


def _answer_from_context(context: dict[str, Any]) -> dict[str, Any]:
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


def _parse_user_message_locally(message: str) -> AssistantAction:
    """Small deterministic fallback for local demos without an API key."""

    text = message.lower().strip()
    exercise_name = _extract_exercise_name(text)

    if _looks_like_pr_query(text):
        return AssistantAction(action="get_pr", exercise_name=exercise_name)
    if "finish" in text and "workout" in text:
        return AssistantAction(action="finish_workout")
    if "start" in text and "workout" in text:
        return AssistantAction(action="start_workout")
    if _looks_like_rest_request(text):
        return AssistantAction(action="start_rest", duration_seconds=_extract_duration_seconds(text))
    if _looks_like_log_set(text):
        return AssistantAction(
            action="log_set",
            exercise_name=exercise_name,
            reps=_extract_reps(text),
            weight=_extract_weight(text),
        )
    if "start" in text and exercise_name:
        return AssistantAction(action="start_exercise", exercise_name=exercise_name)

    return AssistantAction(action="unknown")


def _looks_like_pr_query(text: str) -> bool:
    return "pr" in text or "personal record" in text or "max" in text


def _looks_like_rest_request(text: str) -> bool:
    return "rest" in text or "timer" in text


def _looks_like_log_set(text: str) -> bool:
    return any(term in text for term in ("log", "record", "add")) and "set" in text


def _extract_exercise_name(text: str) -> str | None:
    for alias, canonical in tools.EXERCISE_ALIASES.items():
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

    return None


def _extract_reps(text: str) -> int | None:
    reps_match = re.search(r"(\d+)\s*(?:rep|reps)\b", text)
    if reps_match:
        return int(reps_match.group(1))

    compact_match = re.search(r"\bx\s*(\d+)\b", text)
    if compact_match:
        return int(compact_match.group(1))

    return None


def _extract_weight(text: str) -> float | None:
    weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lb|lbs|pound|pounds)\b", text)
    if weight_match:
        return float(weight_match.group(1))

    at_match = re.search(r"\bat\s+(\d+(?:\.\d+)?)\b", text)
    if at_match:
        return float(at_match.group(1))

    return None


def _format_weight(weight: float | int) -> str:
    return str(int(weight)) if float(weight).is_integer() else str(weight)


def _format_reps_tail(result: dict[str, Any]) -> str:
    reps = result.get("reps")
    if reps is None:
        return ""
    return f" for {reps} reps"
