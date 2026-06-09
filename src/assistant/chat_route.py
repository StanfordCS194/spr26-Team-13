"""Glasses coach chat route with contextual chat and simple workout actions.

The route remains the native glasses entry point, but it now consolidates the
plain spoken coach response path with the existing structured assistant action
path. Supported workout commands use deterministic tools; other questions use
the LLM with app context and short-lived conversation memory.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from flask import Flask, jsonify, request

from src.assistant.context_manager import CoachContextManager
from src.assistant.coach_style import style_action_reply, style_prompt_from_context
from src.assistant.evidence import format_evidence_context, response_sources_payload, retrieve_evidence
from src.assistant.models import AssistantAction
from src.assistant.service import DEFAULT_ASSISTANT_MODEL, build_openai_client, handle_action, parse_user_message
from src.assistant.supabase_tools import SupabaseToolError, execute_supabase_action

LOGGER = logging.getLogger(__name__)

TRAINER_SYSTEM_PROMPT = (
    "You are a friendly, knowledgeable personal trainer. Answer questions "
    "about exercise, form, programming, recovery, and nutrition. Keep replies "
    "short and conversational - usually one or two sentences - because they "
    "will be spoken aloud through the user's glasses, not read on a screen. "
    "Adapt tone to the user's coach style and evidence preference when present. "
    "Avoid bullet points, markdown, or long lists. If evidence context is "
    "provided, ground training claims in it and name the source briefly, such "
    "as 'Schoenfeld et al.' Do not imply medical certainty."
)

CHAT_MODEL_ENV = "OPENAI_CHAT_MODEL"
CHAT_MAX_TOKENS = 200
DEFAULT_CHAT_SESSION_ID = "default"

CONTEXT_MANAGER = CoachContextManager()


def register_chat_route(app: Flask) -> None:
    """Register POST /api/chat on the given Flask app."""

    @app.route("/api/chat", methods=["POST", "OPTIONS"])
    def chat_route() -> Any:
        if request.method == "OPTIONS":
            return ("", 204)

        payload = request.get_json(silent=True) or {}
        text = (payload.get("text") or "").strip()
        app_context = payload.get("context") if isinstance(payload.get("context"), dict) else None
        auth_payload = payload.get("auth") if isinstance(payload.get("auth"), dict) else {}
        access_token = (
            auth_payload.get("access_token")
            or request.headers.get("X-Supabase-Access-Token")
        )
        session_id = str(payload.get("session_id") or DEFAULT_CHAT_SESSION_ID)
        if not text:
            return jsonify({"error": "missing 'text' in request body"}), 400

        pending_action = _action_from_pending_log_confirmation(text, app_context)
        if pending_action is not None:
            if pending_action.action == "unknown":
                reply = style_action_reply("Okay, I did not log it.", app_context, action_name="log_set")
                CONTEXT_MANAGER.record_turn(session_id=session_id, user_text=text, assistant_reply=reply)
                return jsonify(
                    {
                        "reply": reply,
                        "response": reply,
                        "mode": "action",
                        "action": pending_action.model_dump(mode="json"),
                        "action_result": {"cleared_pending_confirmation": True},
                        "ui_patch": None,
                    }
                )

            try:
                supabase_payload = execute_supabase_action(pending_action, context=app_context, access_token=access_token)
            except SupabaseToolError as exc:
                LOGGER.exception("Supabase confirmed coach action failed for action=%s", pending_action.action)
                return jsonify({"error": str(exc)}), 502

            if supabase_payload is not None:
                reply = str(supabase_payload.get("message") or "").strip()
                ui_patch = supabase_payload.get("ui_patch")
                action_result = dict(supabase_payload.get("action_result") or {})
            else:
                assistant_payload = handle_action(pending_action, context=app_context)
                reply = str(assistant_payload.get("response") or "").strip()
                ui_patch = _build_ui_patch(assistant_payload.get("action"), app_context)
                action_result = {}

            action_result["cleared_pending_confirmation"] = True
            reply = style_action_reply(reply, app_context, action_name=pending_action.action)
            CONTEXT_MANAGER.record_turn(session_id=session_id, user_text=text, assistant_reply=reply)
            return jsonify(
                {
                    "reply": reply,
                    "response": reply,
                    "mode": "action",
                    "action": pending_action.model_dump(mode="json"),
                    "action_result": action_result,
                    "ui_patch": ui_patch,
                }
            )

        try:
            action = parse_user_message(text)
        except Exception:  # noqa: BLE001 - chat can still answer if action parsing fails
            LOGGER.exception("Assistant action parsing failed for text=%r", text)
            action = None

        if action is not None and action.action != "unknown":
            try:
                supabase_payload = execute_supabase_action(action, context=app_context, access_token=access_token)
            except SupabaseToolError as exc:
                LOGGER.exception("Supabase coach action failed for action=%s", action.action)
                return jsonify({"error": str(exc)}), 502

            if supabase_payload is not None:
                reply = str(supabase_payload.get("message") or "").strip()
                ui_patch = supabase_payload.get("ui_patch")
                action_result = supabase_payload.get("action_result")
                if supabase_payload.get("ok") and not _needs_confirmation(action_result):
                    reply = style_action_reply(reply, app_context, action_name=action.action)
            else:
                assistant_payload = handle_action(action, context=app_context)
                reply = str(assistant_payload.get("response") or "").strip()
                ui_patch = _build_ui_patch(assistant_payload.get("action"), app_context)
                action_result = None
                reply = style_action_reply(reply, app_context, action_name=action.action)

            CONTEXT_MANAGER.record_turn(session_id=session_id, user_text=text, assistant_reply=reply)
            return jsonify(
                {
                    "reply": reply,
                    "response": reply,
                    "mode": "action",
                    "action": action.model_dump(mode="json"),
                    "action_result": action_result,
                    "ui_patch": ui_patch,
                }
            )

        client = build_openai_client()
        if client is None:
            return (
                jsonify(
                    {
                        "error": (
                            "OpenAI client not configured. Set OPENAI_API_KEY in .env "
                            "and install the openai package."
                        )
                    }
                ),
                503,
            )

        model = os.getenv(CHAT_MODEL_ENV, DEFAULT_ASSISTANT_MODEL)
        profile = app_context.get("trainingProfile") if isinstance(app_context, dict) else None
        evidence_sources = retrieve_evidence(text, profile=profile if isinstance(profile, dict) else None)
        evidence_context = format_evidence_context(evidence_sources)
        system_prompt = f"{TRAINER_SYSTEM_PROMPT}\n\n{style_prompt_from_context(app_context)}"
        if evidence_context:
            system_prompt = (
                f"{system_prompt}\n\nRelevant peer-reviewed evidence:\n{evidence_context}"
            )

        try:
            messages = CONTEXT_MANAGER.build_messages(
                session_id=session_id,
                user_text=text,
                app_context=app_context,
                system_prompt=system_prompt,
            )
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=CHAT_MAX_TOKENS,
            )
        except Exception:  # noqa: BLE001 - surface any OpenAI failure as a 500
            LOGGER.exception("OpenAI chat completion failed for text=%r", text)
            return jsonify({"error": "chat completion failed"}), 500

        reply = (completion.choices[0].message.content or "").strip()
        if not reply:
            return jsonify({"error": "empty reply from model"}), 502

        CONTEXT_MANAGER.record_turn(session_id=session_id, user_text=text, assistant_reply=reply)
        return jsonify(
            {
                "reply": reply,
                "response": reply,
                "mode": "chat",
                "sources": response_sources_payload(evidence_sources),
            }
        )


def _build_ui_patch(action: Any, app_context: dict[str, Any] | None) -> dict[str, Any] | None:
    """Translate assistant actions into frontend commands that can touch Supabase."""

    if not isinstance(action, dict):
        return None

    action_name = action.get("action")
    current_workout = app_context.get("currentWorkout") if isinstance(app_context, dict) else None
    active_program_id = app_context.get("activeProgramId") if isinstance(app_context, dict) else None

    if action_name == "start_workout":
        return {
            "type": "start_workout",
            "programId": active_program_id,
            "programName": action.get("program_name"),
            "day": {
                "title": action.get("day_name"),
                "dayNumber": action.get("day_number"),
                "weekNumber": action.get("week_number"),
            } if action.get("day_name") or action.get("day_number") or action.get("week_number") else None,
        }

    if action_name == "finish_workout":
        return {
            "type": "finish_workout",
            "sessionId": current_workout.get("sessionId") if isinstance(current_workout, dict) else None,
            "programId": active_program_id,
        }

    if action_name == "log_set":
        return {
            "type": "log_set",
            "sessionId": current_workout.get("sessionId") if isinstance(current_workout, dict) else None,
            "exerciseName": action.get("exercise_name"),
            "reps": action.get("reps"),
            "weight": action.get("weight"),
        }

    if action_name == "start_rest":
        return {
            "type": "start_rest",
            "durationSeconds": action.get("duration_seconds"),
        }

    if action_name == "start_exercise":
        return {
            "type": "start_exercise",
            "sessionId": current_workout.get("sessionId") if isinstance(current_workout, dict) else None,
            "exerciseName": action.get("exercise_name"),
        }

    if action_name == "advance_set":
        return {
            "type": "advance_set",
            "sessionId": current_workout.get("sessionId") if isinstance(current_workout, dict) else None,
            "exerciseName": action.get("exercise_name"),
        }

    if action_name in {"skip_exercise", "finish_exercise"}:
        return {
            "type": action_name,
            "sessionId": current_workout.get("sessionId") if isinstance(current_workout, dict) else None,
            "exerciseName": action.get("exercise_name"),
        }

    return None


def _needs_confirmation(action_result: Any) -> bool:
    return isinstance(action_result, dict) and bool(action_result.get("needs_confirmation"))


def _action_from_pending_log_confirmation(
    text: str,
    app_context: dict[str, Any] | None,
) -> AssistantAction | None:
    pending_log = _pending_log_confirmation(app_context)
    if pending_log is None:
        return None

    if _looks_negative(text):
        return AssistantAction(action="unknown")

    if not _looks_affirmative(text):
        return None

    reps = _coerce_int(pending_log.get("reps"))
    exercise_name = str(pending_log.get("exerciseName") or pending_log.get("exercise_name") or "").strip()
    if not exercise_name or reps is None:
        return AssistantAction(action="unknown")

    return AssistantAction(
        action="log_set",
        exercise_name=exercise_name,
        reps=reps,
        weight=_coerce_float(pending_log.get("weight")),
        confirmed_off_current=True,
    )


def _pending_log_confirmation(app_context: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(app_context, dict):
        return None

    pending_log = app_context.get("pendingLogConfirmation")
    if not isinstance(pending_log, dict):
        return None

    if not pending_log.get("sessionId"):
        return None

    return pending_log


def _looks_affirmative(text: str) -> bool:
    return bool(
        re.search(
            r"\b(yes|yeah|yep|correct|right|confirm|confirmed|do it|log it|that is right|that's right)\b",
            text.lower(),
        )
    )


def _looks_negative(text: str) -> bool:
    return bool(
        re.search(
            r"\b(no|nope|cancel|do not|don't|nevermind|never mind|not that|stop)\b",
            text.lower(),
        )
    )


def _coerce_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None
