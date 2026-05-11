"""Backend adapter for assistant history and live workout state.

The repo's Supabase folder currently provides SQL schema/migrations rather than
a Python service module, so this file is the Python boundary for assistant calls.
When Supabase credentials are configured it uses the committed schema tables:
workout_sessions, workout_exercise_logs, workout_sets, and personal_records.
Live display state is mirrored locally until a persisted current-state table or
realtime channel exists.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from math import ceil
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.assistant import mock_db
from src.assistant.mock_db import EXERCISE_ALIASES
from src.contracts import DisplayState

DEFAULT_USER_ID = "demo-user"
DEFAULT_UNIT = "lb"


class BackendUnavailableError(RuntimeError):
    """Raised when a configured backend cannot be reached."""


def normalize_exercise_name(exercise_name: str | None) -> str | None:
    """Normalize user-facing exercise names into backend lookup keys."""

    if exercise_name is None:
        return None

    normalized = " ".join(exercise_name.strip().lower().split())
    return EXERCISE_ALIASES.get(normalized, normalized)


def get_backend() -> "AssistantBackend":
    """Return the configured assistant backend."""

    if _supabase_configured():
        return SupabaseRestBackend()
    return InMemoryAssistantBackend()


def _supabase_configured() -> bool:
    return bool(os.getenv("SUPABASE_URL") and _supabase_key())


def _supabase_key() -> str | None:
    return (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_KEY")
    )


class AssistantBackend:
    """Small backend interface used by deterministic assistant tools."""

    def get_pr(self, user_id: str, exercise_name: str) -> dict[str, Any]:
        raise NotImplementedError

    def get_recent_exercise_history(self, user_id: str, exercise_name: str, limit: int = 5) -> dict[str, Any]:
        raise NotImplementedError

    def log_set(
        self,
        user_id: str,
        session_id: str | None,
        exercise_name: str,
        reps: int,
        weight: float | None,
        *,
        unit: str | None = None,
        notes: str | None = None,
        target_rpe: float | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def start_workout(self, user_id: str, program_id: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def start_next_set(self, user_id: str, session_id: str) -> dict[str, Any]:
        raise NotImplementedError

    def start_next_exercise(self, user_id: str, session_id: str) -> dict[str, Any]:
        raise NotImplementedError

    def start_exercise(self, user_id: str, session_id: str | None, exercise_name: str) -> dict[str, Any]:
        raise NotImplementedError

    def add_exercise(
        self,
        user_id: str,
        session_id: str | None,
        exercise_name: str,
        *,
        sets: int | None = None,
        reps: int | None = None,
        weight: float | None = None,
        unit: str | None = None,
        notes: str | None = None,
        target_rpe: float | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def start_rest(self, user_id: str, session_id: str | None, duration_seconds: int | None) -> dict[str, Any]:
        raise NotImplementedError

    def finish_workout(self, user_id: str, session_id: str | None) -> dict[str, Any]:
        raise NotImplementedError

    def get_active_exercise_name(self, user_id: str, session_id: str | None) -> str | None:
        raise NotImplementedError

    def get_display_state(self, session_id: str | None) -> DisplayState | None:
        raise NotImplementedError


class InMemoryAssistantBackend(AssistantBackend):
    """Local backend used when Supabase credentials are not configured."""

    def get_pr(self, user_id: str, exercise_name: str) -> dict[str, Any]:
        normalized_name = normalize_exercise_name(exercise_name)
        record = mock_db.PERSONAL_RECORDS.get(normalized_name or "")
        if record is None:
            return {
                "ok": False,
                "status": "not_found",
                "exercise_name": normalized_name,
                "message": f"I do not have a PR saved for {normalized_name}.",
            }
        return {"ok": True, "status": "found", "source": "mock", **record}

    def get_recent_exercise_history(self, user_id: str, exercise_name: str, limit: int = 5) -> dict[str, Any]:
        normalized_name = normalize_exercise_name(exercise_name)
        history = mock_db.EXERCISE_HISTORY.get(user_id, {}).get(normalized_name or "", [])[:limit]
        if not history:
            return {
                "ok": False,
                "status": "not_found",
                "exercise_name": normalized_name,
                "history": [],
                "message": f"I do not have recent history for {normalized_name}.",
            }
        return {
            "ok": True,
            "status": "found",
            "source": "mock",
            "exercise_name": normalized_name,
            "history": history,
        }

    def log_set(
        self,
        user_id: str,
        session_id: str | None,
        exercise_name: str,
        reps: int,
        weight: float | None,
        *,
        unit: str | None = None,
        notes: str | None = None,
        target_rpe: float | None = None,
    ) -> dict[str, Any]:
        session = self._get_or_create_session(user_id, session_id)
        normalized_name = normalize_exercise_name(exercise_name)
        exercise = self._ensure_exercise(session, normalized_name or exercise_name)
        set_number = len(exercise["completed_sets"]) + 1
        logged_set = {
            "user_id": user_id,
            "session_id": session["session_id"],
            "exercise_name": exercise["exercise_name"],
            "set_number": set_number,
            "reps": reps,
            "weight": weight,
            "unit": unit or DEFAULT_UNIT,
            "notes": notes,
            "target_rpe": target_rpe,
            "completed_at": _now_iso(),
        }
        exercise["completed_sets"].append(logged_set)
        mock_db.LOGGED_SETS.append(logged_set)
        if exercise.get("sets") and set_number >= exercise["sets"]:
            session["current_set_index"] = max(exercise["sets"] - 1, 0)
        else:
            session["current_set_index"] = set_number
        session["rest_duration_seconds"] = None
        session["rest_started_at"] = None
        return {
            "ok": True,
            "status": "logged",
            "session_id": session["session_id"],
            **logged_set,
            "display_state": self.get_display_state(session["session_id"]).model_dump(mode="json"),
        }

    def start_workout(self, user_id: str, program_id: str | None = None) -> dict[str, Any]:
        session = self._create_session(user_id, program_id=program_id)
        return {
            "ok": True,
            "status": "started",
            "session_id": session["session_id"],
            "display_state": self.get_display_state(session["session_id"]).model_dump(mode="json"),
        }

    def start_next_set(self, user_id: str, session_id: str) -> dict[str, Any]:
        session = self._require_session(session_id)
        exercise = self._active_exercise(session)
        if exercise is None:
            return {"ok": False, "status": "missing_exercise", "message": "There is no active exercise yet."}
        max_index = max((exercise.get("sets") or 1) - 1, 0)
        session["current_set_index"] = min(session["current_set_index"] + 1, max_index)
        session["rest_duration_seconds"] = None
        session["rest_started_at"] = None
        return {
            "ok": True,
            "status": "set_started",
            "session_id": session_id,
            "exercise_name": exercise["exercise_name"],
            "set_number": session["current_set_index"] + 1,
            "display_state": self.get_display_state(session_id).model_dump(mode="json"),
        }

    def start_next_exercise(self, user_id: str, session_id: str) -> dict[str, Any]:
        session = self._require_session(session_id)
        if not session["exercises"]:
            return {"ok": False, "status": "missing_exercise", "message": "There is no next exercise planned yet."}
        session["current_exercise_index"] = min(session["current_exercise_index"] + 1, len(session["exercises"]) - 1)
        session["current_set_index"] = 0
        session["rest_duration_seconds"] = None
        session["rest_started_at"] = None
        exercise = self._active_exercise(session)
        return {
            "ok": True,
            "status": "exercise_started",
            "session_id": session_id,
            "exercise_name": exercise["exercise_name"],
            "display_state": self.get_display_state(session_id).model_dump(mode="json"),
        }

    def start_exercise(self, user_id: str, session_id: str | None, exercise_name: str) -> dict[str, Any]:
        session = self._get_or_create_session(user_id, session_id)
        normalized_name = normalize_exercise_name(exercise_name) or exercise_name
        exercise = self._ensure_exercise(session, normalized_name)
        session["current_exercise_index"] = session["exercises"].index(exercise)
        session["current_set_index"] = 0
        session["rest_duration_seconds"] = None
        session["rest_started_at"] = None
        return {
            "ok": True,
            "status": "exercise_started",
            "session_id": session["session_id"],
            "exercise_name": normalized_name,
            "display_state": self.get_display_state(session["session_id"]).model_dump(mode="json"),
        }

    def add_exercise(
        self,
        user_id: str,
        session_id: str | None,
        exercise_name: str,
        *,
        sets: int | None = None,
        reps: int | None = None,
        weight: float | None = None,
        unit: str | None = None,
        notes: str | None = None,
        target_rpe: float | None = None,
    ) -> dict[str, Any]:
        session = self._get_or_create_session(user_id, session_id)
        normalized_name = normalize_exercise_name(exercise_name) or exercise_name
        exercise = {
            "exercise_name": normalized_name,
            "sets": sets or 1,
            "reps": reps,
            "weight": weight,
            "unit": unit or DEFAULT_UNIT,
            "notes": notes,
            "target_rpe": target_rpe,
            "completed_sets": [],
        }
        session["exercises"].append(exercise)
        session["current_exercise_index"] = len(session["exercises"]) - 1
        session["current_set_index"] = 0
        session["rest_duration_seconds"] = None
        session["rest_started_at"] = None
        return {
            "ok": True,
            "status": "exercise_added",
            "session_id": session["session_id"],
            **{key: value for key, value in exercise.items() if key != "completed_sets"},
            "display_state": self.get_display_state(session["session_id"]).model_dump(mode="json"),
        }

    def start_rest(self, user_id: str, session_id: str | None, duration_seconds: int | None) -> dict[str, Any]:
        session = self._get_or_create_session(user_id, session_id)
        duration = duration_seconds or 90
        session["rest_duration_seconds"] = duration
        session["rest_started_at"] = _now_iso()
        return {
            "ok": True,
            "status": "rest_started",
            "session_id": session["session_id"],
            "duration_seconds": duration,
            "display_state": self.get_display_state(session["session_id"]).model_dump(mode="json"),
        }

    def finish_workout(self, user_id: str, session_id: str | None) -> dict[str, Any]:
        session = self._get_or_create_session(user_id, session_id)
        session["status"] = "completed"
        session["rest_duration_seconds"] = None
        session["rest_started_at"] = None
        completed_sets = [
            completed_set
            for exercise in session.get("exercises", [])
            for completed_set in exercise.get("completed_sets", [])
        ]
        return {
            "ok": True,
            "status": "finished",
            "session_id": session["session_id"],
            "completed_sets": len(completed_sets),
            "exercises": [exercise["exercise_name"] for exercise in session.get("exercises", [])],
            "display_state": self.get_display_state(session["session_id"]).model_dump(mode="json"),
        }

    def get_active_exercise_name(self, user_id: str, session_id: str | None) -> str | None:
        session = self._get_session(session_id) if session_id else self._latest_session_for_user(user_id)
        if session is None:
            return None
        exercise = self._active_exercise(session)
        return exercise["exercise_name"] if exercise else None

    def get_display_state(self, session_id: str | None) -> DisplayState | None:
        session = self._get_session(session_id) if session_id else None
        if session is None:
            return None
        exercise = self._active_exercise(session)
        if exercise is None:
            rest_remaining, rest_total = _rest_remaining(session)
            return DisplayState(
                exercise_name="Workout",
                set_progress="No exercise selected",
                rep_progress=None,
                target_summary="Add or start an exercise",
                rest_remaining_seconds=rest_remaining,
                rest_total_seconds=rest_total,
                next_action="Choose your first exercise",
                warning_message=None,
            )

        sets = exercise.get("sets") or 1
        current_set = min(session.get("current_set_index", 0) + 1, sets)
        reps = exercise.get("reps")
        weight = exercise.get("weight")
        unit = exercise.get("unit") or DEFAULT_UNIT
        target_parts = []
        if weight is not None:
            target_parts.append(f"{_format_weight(weight)} {unit}")
        if reps is not None:
            target_parts.append(f"x {reps}")
        target_summary = " ".join(target_parts) if target_parts else "No target set"
        rest_remaining, rest_total = _rest_remaining(session)
        return DisplayState(
            exercise_name=exercise["exercise_name"],
            set_progress=f"Set {current_set} of {sets}",
            rep_progress=f"0 / {reps} reps" if reps is not None else None,
            target_summary=target_summary,
            rest_remaining_seconds=rest_remaining,
            rest_total_seconds=rest_total,
            next_action="Rest, then start your next set" if rest_remaining else "Get set and start lifting",
            warning_message="Workout complete" if session.get("status") == "completed" else None,
        )

    def _create_session(
        self,
        user_id: str,
        program_id: str | None = None,
        *,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        session_id = session_id or f"session-{uuid.uuid4().hex[:8]}"
        session = {
            "user_id": user_id,
            "session_id": session_id,
            "program_id": program_id,
            "status": "in_progress",
            "current_exercise_index": 0,
            "current_set_index": 0,
            "rest_duration_seconds": None,
            "rest_started_at": None,
            "exercises": [],
            "started_at": _now_iso(),
        }
        mock_db.WORKOUT_SESSIONS[session_id] = session
        return session

    def _get_or_create_session(self, user_id: str, session_id: str | None) -> dict[str, Any]:
        if session_id and session_id in mock_db.WORKOUT_SESSIONS:
            return mock_db.WORKOUT_SESSIONS[session_id]
        if session_id:
            return self._create_session(user_id, session_id=session_id)
        latest = self._latest_session_for_user(user_id)
        if latest is not None and session_id is None:
            return latest
        return self._create_session(user_id)

    def _require_session(self, session_id: str) -> dict[str, Any]:
        session = self._get_session(session_id)
        if session is None:
            raise ValueError("No active workout session was found.")
        return session

    def _get_session(self, session_id: str | None) -> dict[str, Any] | None:
        if session_id is None:
            return None
        return mock_db.WORKOUT_SESSIONS.get(session_id)

    def _latest_session_for_user(self, user_id: str) -> dict[str, Any] | None:
        for session in reversed(list(mock_db.WORKOUT_SESSIONS.values())):
            if session["user_id"] == user_id and session.get("status") != "completed":
                return session
        return None

    def _active_exercise(self, session: dict[str, Any]) -> dict[str, Any] | None:
        exercises = session.get("exercises") or []
        if not exercises:
            return None
        index = min(session.get("current_exercise_index", 0), len(exercises) - 1)
        return exercises[index]

    def _ensure_exercise(self, session: dict[str, Any], exercise_name: str) -> dict[str, Any]:
        for exercise in session["exercises"]:
            if exercise["exercise_name"] == exercise_name:
                return exercise
        exercise = {
            "exercise_name": exercise_name,
            "sets": 1,
            "reps": None,
            "weight": None,
            "unit": DEFAULT_UNIT,
            "notes": None,
            "target_rpe": None,
            "completed_sets": [],
        }
        session["exercises"].append(exercise)
        return exercise


class SupabaseRestBackend(InMemoryAssistantBackend):
    """Supabase REST adapter with in-memory live-state fallback.

    The SQL schema lives in supabase/migrations/20260508074148_ios_backend_schema.sql.
    """

    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = _supabase_key() or ""

    def get_pr(self, user_id: str, exercise_name: str) -> dict[str, Any]:
        normalized_name = normalize_exercise_name(exercise_name)
        rows = self._select_personal_records(user_id, normalized_name)
        if not rows:
            return super().get_pr(user_id, exercise_name)
        best = rows[0]
        return {
            "ok": True,
            "status": "found",
            "source": "supabase",
            "exercise_name": best.get("exercise_name") or normalized_name,
            "record_type": best.get("record_type"),
            "weight": best.get("value"),
            "reps": best.get("reps") or 1,
            "unit": best.get("unit") or DEFAULT_UNIT,
            "achieved_at": best.get("achieved_at"),
        }

    def get_recent_exercise_history(self, user_id: str, exercise_name: str, limit: int = 5) -> dict[str, Any]:
        normalized_name = normalize_exercise_name(exercise_name)
        rows = self._select_exercise_logs_with_sets(user_id, normalized_name, limit=limit)
        if not rows:
            return super().get_recent_exercise_history(user_id, exercise_name, limit=limit)
        history = self._flatten_exercise_history(rows, normalized_name, limit)
        return {
            "ok": True,
            "status": "found",
            "source": "supabase",
            "exercise_name": normalized_name,
            "history": history,
        }

    def log_set(
        self,
        user_id: str,
        session_id: str | None,
        exercise_name: str,
        reps: int,
        weight: float | None,
        *,
        unit: str | None = None,
        notes: str | None = None,
        target_rpe: float | None = None,
    ) -> dict[str, Any]:
        try:
            remote_session_id = self._ensure_remote_session(user_id, session_id)
            exercise_log_id = self._ensure_remote_exercise_log(remote_session_id, exercise_name, notes=notes)
            set_number = self._next_remote_set_number(exercise_log_id)
            self._insert(
                "workout_sets",
                {
                    "exercise_log_id": exercise_log_id,
                    "set_number": set_number,
                    "reps": reps,
                    "load_value": weight,
                    "load_unit": unit or DEFAULT_UNIT,
                    "rpe": target_rpe,
                    "status": "manual",
                    "completed_at": _now_iso(),
                },
            )
            result = super().log_set(
                user_id,
                remote_session_id,
                exercise_name,
                reps,
                weight,
                unit=unit,
                notes=notes,
                target_rpe=target_rpe,
            )
            result["source"] = "supabase"
            result["exercise_log_id"] = exercise_log_id
        except BackendUnavailableError:
            result = super().log_set(
                user_id,
                session_id,
                exercise_name,
                reps,
                weight,
                unit=unit,
                notes=notes,
                target_rpe=target_rpe,
            )
            result["source"] = "mock"
            result["warning"] = "Backend unavailable; set was logged in local demo state."
        return result

    def start_workout(self, user_id: str, program_id: str | None = None) -> dict[str, Any]:
        try:
            remote_session = self._insert(
                "workout_sessions",
                {
                    "user_id": user_id,
                    "program_id": program_id,
                    "title": "Live workout",
                    "status": "in_progress",
                    "started_at": _now_iso(),
                    "notes": "Assistant-created session",
                },
            )[0]
            result = super().start_workout(user_id, program_id=program_id)
            old_session_id = result["session_id"]
            session = mock_db.WORKOUT_SESSIONS.pop(old_session_id)
            session["session_id"] = remote_session["id"]
            mock_db.WORKOUT_SESSIONS[remote_session["id"]] = session
            result["session_id"] = remote_session["id"]
            result["source"] = "supabase"
            result["display_state"] = self.get_display_state(remote_session["id"]).model_dump(mode="json")
            return result
        except BackendUnavailableError:
            result = super().start_workout(user_id, program_id=program_id)
            result["source"] = "mock"
            result["warning"] = "Backend unavailable; workout was started in local demo state."
            return result

    def add_exercise(
        self,
        user_id: str,
        session_id: str | None,
        exercise_name: str,
        *,
        sets: int | None = None,
        reps: int | None = None,
        weight: float | None = None,
        unit: str | None = None,
        notes: str | None = None,
        target_rpe: float | None = None,
    ) -> dict[str, Any]:
        try:
            remote_session_id = self._ensure_remote_session(user_id, session_id)
            self._ensure_remote_exercise_log(remote_session_id, exercise_name, notes=notes)
            result = super().add_exercise(
                user_id,
                remote_session_id,
                exercise_name,
                sets=sets,
                reps=reps,
                weight=weight,
                unit=unit,
                notes=notes,
                target_rpe=target_rpe,
            )
            result["source"] = "supabase"
            return result
        except BackendUnavailableError:
            result = super().add_exercise(
                user_id,
                session_id,
                exercise_name,
                sets=sets,
                reps=reps,
                weight=weight,
                unit=unit,
                notes=notes,
                target_rpe=target_rpe,
            )
            result["source"] = "mock"
            result["warning"] = "Backend unavailable; exercise was added in local demo state."
            return result

    def start_rest(self, user_id: str, session_id: str | None, duration_seconds: int | None) -> dict[str, Any]:
        result = super().start_rest(user_id, session_id, duration_seconds)
        result["source"] = "supabase" if _supabase_configured() else "mock"
        return result

    def finish_workout(self, user_id: str, session_id: str | None) -> dict[str, Any]:
        try:
            remote_session_id = self._ensure_remote_session(user_id, session_id)
            result = super().finish_workout(user_id, remote_session_id)
            session = mock_db.WORKOUT_SESSIONS.get(remote_session_id, {})
            completed_sets = [
                completed_set
                for exercise in session.get("exercises", [])
                for completed_set in exercise.get("completed_sets", [])
            ]
            total_volume = sum(
                (completed_set.get("weight") or 0) * (completed_set.get("reps") or 0)
                for completed_set in completed_sets
            )
            self._update(
                "workout_sessions",
                remote_session_id,
                {
                    "status": "completed",
                    "finished_at": _now_iso(),
                    "duration_seconds": _duration_seconds(session.get("started_at")),
                    "total_sets": len(completed_sets),
                    "total_volume": total_volume,
                },
            )
            result["source"] = "supabase"
            return result
        except BackendUnavailableError:
            result = super().finish_workout(user_id, session_id)
            result["source"] = "mock"
            result["warning"] = "Backend unavailable; workout was finished in local demo state."
            return result

    def _select_personal_records(self, user_id: str, exercise_name: str | None) -> list[dict[str, Any]]:
        params = [
            f"user_id=eq.{quote(user_id)}",
            "order=value.desc",
            "limit=1",
        ]
        if exercise_name:
            params.append(f"exercise_name=ilike.*{quote(exercise_name)}*")
        return self._request("GET", f"personal_records?{'&'.join(params)}")

    def _select_exercise_logs_with_sets(self, user_id: str, exercise_name: str | None, limit: int) -> list[dict[str, Any]]:
        params = [
            "select=id,exercise_name,created_at,workout_sessions!inner(user_id),workout_sets(set_number,reps,load_value,load_unit,rpe,completed_at)",
            f"workout_sessions.user_id=eq.{quote(user_id)}",
            "order=created_at.desc",
            f"limit={limit}",
        ]
        if exercise_name:
            params.append(f"exercise_name=ilike.*{quote(exercise_name)}*")
        return self._request("GET", f"workout_exercise_logs?{'&'.join(params)}")

    def _flatten_exercise_history(
        self,
        rows: list[dict[str, Any]],
        exercise_name: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        history: list[dict[str, Any]] = []
        for row in rows:
            for set_row in row.get("workout_sets") or []:
                history.append(
                    {
                        "exercise_name": row.get("exercise_name") or exercise_name,
                        "weight": set_row.get("load_value"),
                        "reps": set_row.get("reps"),
                        "unit": set_row.get("load_unit") or DEFAULT_UNIT,
                        "rpe": set_row.get("rpe"),
                        "completed_at": set_row.get("completed_at") or row.get("created_at"),
                    }
                )
        history.sort(key=lambda item: item.get("completed_at") or "", reverse=True)
        return history[:limit]

    def _ensure_remote_session(self, user_id: str, session_id: str | None) -> str:
        if session_id:
            rows = self._request("GET", f"workout_sessions?id=eq.{quote(session_id)}&user_id=eq.{quote(user_id)}&limit=1")
            if rows:
                return rows[0]["id"]
        row = self._insert(
            "workout_sessions",
            {
                "user_id": user_id,
                "title": "Live workout",
                "status": "in_progress",
                "started_at": _now_iso(),
                "notes": "Assistant-created session",
            },
        )[0]
        return row["id"]

    def _ensure_remote_exercise_log(
        self,
        session_id: str,
        exercise_name: str,
        *,
        notes: str | None = None,
    ) -> str:
        rows = self._request(
            "GET",
            f"workout_exercise_logs?session_id=eq.{quote(session_id)}&exercise_name=eq.{quote(exercise_name)}&limit=1",
        )
        if rows:
            return rows[0]["id"]
        existing = self._request(
            "GET",
            f"workout_exercise_logs?session_id=eq.{quote(session_id)}&select=exercise_number&order=exercise_number.desc&limit=1",
        )
        next_number = (existing[0].get("exercise_number") or 0) + 1 if existing else 1
        row = self._insert(
            "workout_exercise_logs",
            {
                "session_id": session_id,
                "exercise_number": next_number,
                "exercise_name": exercise_name,
                "notes": notes,
            },
        )[0]
        return row["id"]

    def _next_remote_set_number(self, exercise_log_id: str) -> int:
        rows = self._request(
            "GET",
            f"workout_sets?exercise_log_id=eq.{quote(exercise_log_id)}&select=set_number&order=set_number.desc&limit=1",
        )
        return (rows[0].get("set_number") or 0) + 1 if rows else 1

    def _insert(self, table: str, row: dict[str, Any]) -> list[dict[str, Any]]:
        return self._request("POST", table, row)

    def _update(self, table: str, row_id: str, row: dict[str, Any]) -> list[dict[str, Any]]:
        return self._request("PATCH", f"{table}?id=eq.{quote(row_id)}", row)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not self.url or not self.key:
            raise BackendUnavailableError("Supabase credentials are not configured.")
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.url}/rest/v1/{path}",
            data=body,
            method=method,
            headers={
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
        )
        try:
            with urlopen(request, timeout=6) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else []
        except (HTTPError, URLError, TimeoutError) as exc:
            raise BackendUnavailableError(str(exc)) from exc


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _duration_seconds(started_at: str | None) -> int | None:
    started = _parse_iso(started_at)
    if started is None:
        return None
    return max(0, int(round((datetime.now(timezone.utc) - started).total_seconds())))


def _rest_remaining(session: dict[str, Any]) -> tuple[int | None, int | None]:
    total = session.get("rest_duration_seconds")
    if total is None:
        return None, None

    started = _parse_iso(session.get("rest_started_at"))
    if started is None:
        return int(total), int(total)

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    remaining = max(0, int(ceil(total - elapsed)))
    if remaining <= 0:
        session["rest_duration_seconds"] = None
        session["rest_started_at"] = None
        return None, None
    return remaining, int(total)


def _format_weight(weight: float | int) -> str:
    return str(int(weight)) if float(weight).is_integer() else str(weight)
