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


def handle_message(message: str) -> dict[str, Any]:
    """Parse a message, execute the matching tool, and format a response."""

    action = parse_user_message(message)
    result = _execute_action(action)
    return {
        "response": _format_response(action, result),
        "action": action.model_dump(mode="json"),
    }


def _execute_action(action: AssistantAction) -> dict[str, Any]:
    if action.action == "get_pr":
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
    return {
        "ok": False,
        "status": "unknown",
        "message": "I can help with PRs, logging sets, starting exercises, rest timers, and finishing workouts.",
    }


def _format_response(action: AssistantAction, result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return str(result.get("message") or "I could not handle that workout request yet.")

    if action.action == "get_pr":
        return (
            f"Your {result['exercise_name']} PR is "
            f"{_format_weight(result['weight'])} pounds for {result['reps']} reps."
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
