"""Assistant tools — Supabase-backed when a JWT-scoped client is in context.

If a tool is invoked without ``context['supabase']`` and ``context['user_id']``,
it falls back to the in-memory mock store. The Flask voice-coach route always
supplies the real client; pytest paths that exercise the assistant directly
keep working against the mock.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.assistant.mock_db import EXERCISE_ALIASES, LOGGED_SETS, PERSONAL_RECORDS, WORKOUT_STATE


def _get_supabase(context: dict[str, Any] | None):
    if not context:
        return None, None
    client = context.get("supabase")
    user_id = context.get("user_id")
    if client is None or not user_id:
        return None, None
    return client, user_id


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_exercise_name(exercise_name: str | None) -> str | None:
    """Normalize user-facing exercise names into canonical keys."""

    if exercise_name is None:
        return None

    normalized = " ".join(exercise_name.strip().lower().split())
    return EXERCISE_ALIASES.get(normalized, normalized)


# ---------------------------------------------------------------------------
# PR lookup
# ---------------------------------------------------------------------------


def get_pr(exercise_name: str | None, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized_name = normalize_exercise_name(exercise_name)
    if not normalized_name:
        return {
            "ok": False,
            "status": "missing_exercise",
            "message": "Which exercise PR do you want to check?",
        }

    client, user_id = _get_supabase(context)
    if client is not None and user_id is not None:
        try:
            response = (
                client.table("personal_records")
                .select("exercise_name,value,unit,record_type,achieved_at")
                .eq("user_id", user_id)
                .ilike("exercise_name", normalized_name)
                .order("achieved_at", desc=True)
                .limit(1)
                .execute()
            )
            rows = response.data or []
        except Exception as exc:  # pragma: no cover
            return {
                "ok": False,
                "status": "supabase_error",
                "message": f"Could not read your PR: {exc}",
            }
        if not rows:
            return {
                "ok": False,
                "status": "not_found",
                "exercise_name": normalized_name,
                "message": f"I do not have a PR saved for {normalized_name}.",
            }
        record = rows[0]
        return {
            "ok": True,
            "status": "found",
            "exercise_name": record.get("exercise_name") or normalized_name,
            "display_name": record.get("exercise_name") or normalized_name,
            "weight": float(record["value"]),
            "unit": record.get("unit") or "lb",
        }

    # mock fallback
    record = PERSONAL_RECORDS.get(normalized_name)
    if record is None:
        return {
            "ok": False,
            "status": "not_found",
            "exercise_name": normalized_name,
            "message": f"I do not have a PR saved for {normalized_name}.",
        }
    return {"ok": True, "status": "found", **record}


# ---------------------------------------------------------------------------
# Workout lifecycle (sessions)
# ---------------------------------------------------------------------------


def _find_active_session_id(client, user_id: str) -> str | None:
    response = (
        client.table("workout_sessions")
        .select("id")
        .eq("user_id", user_id)
        .eq("status", "in_progress")
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0]["id"] if rows else None


def _create_session(client, user_id: str, *, title: str = "Voice session") -> str:
    now = _now_iso()
    response = (
        client.table("workout_sessions")
        .insert(
            {
                "user_id": user_id,
                "title": title,
                "status": "in_progress",
                "started_at": now,
            }
        )
        .execute()
    )
    rows = response.data or []
    if not rows:
        raise RuntimeError("workout_sessions insert returned no row")
    return rows[0]["id"]


def start_workout(*, context: dict[str, Any] | None = None) -> dict[str, Any]:
    client, user_id = _get_supabase(context)
    if client is not None and user_id is not None:
        try:
            existing = _find_active_session_id(client, user_id)
            session_id = existing or _create_session(client, user_id)
        except Exception as exc:  # pragma: no cover
            return {
                "ok": False,
                "status": "supabase_error",
                "message": f"Could not start a session: {exc}",
            }
        return {"ok": True, "status": "started", "session_id": session_id}

    WORKOUT_STATE.update({"active": True, "resting": False, "rest_duration_seconds": None})
    return {"ok": True, "status": "started"}


def finish_workout(*, context: dict[str, Any] | None = None) -> dict[str, Any]:
    client, user_id = _get_supabase(context)
    if client is not None and user_id is not None:
        try:
            session_id = _find_active_session_id(client, user_id)
            if session_id is None:
                return {"ok": True, "status": "no_active_session"}

            totals = _session_totals(client, session_id)
            now = _now_iso()
            client.table("workout_sessions").update(
                {
                    "status": "completed",
                    "finished_at": now,
                    "total_volume": totals["total_volume"],
                    "total_sets": totals["total_sets"],
                }
            ).eq("id", session_id).execute()
        except Exception as exc:  # pragma: no cover
            return {
                "ok": False,
                "status": "supabase_error",
                "message": f"Could not finish the session: {exc}",
            }
        return {"ok": True, "status": "finished", "session_id": session_id, **totals}

    WORKOUT_STATE.update(
        {
            "active": False,
            "current_exercise": None,
            "resting": False,
            "rest_duration_seconds": None,
        }
    )
    return {"ok": True, "status": "finished"}


def _session_totals(client, session_id: str) -> dict[str, Any]:
    logs = (
        client.table("workout_exercise_logs")
        .select("id")
        .eq("session_id", session_id)
        .execute()
    )
    log_ids = [row["id"] for row in (logs.data or [])]
    if not log_ids:
        return {"total_volume": 0, "total_sets": 0}

    sets = (
        client.table("workout_sets")
        .select("reps,load_value")
        .in_("exercise_log_id", log_ids)
        .execute()
    )
    rows = sets.data or []
    total_sets = len(rows)
    total_volume = 0.0
    for row in rows:
        reps = row.get("reps") or 0
        load = row.get("load_value") or 0
        try:
            total_volume += float(reps) * float(load)
        except (TypeError, ValueError):
            continue
    return {"total_volume": round(total_volume, 2), "total_sets": total_sets}


# ---------------------------------------------------------------------------
# Exercise + set logging
# ---------------------------------------------------------------------------


def _find_or_create_exercise_log(client, session_id: str, exercise_name: str) -> dict[str, Any]:
    existing = (
        client.table("workout_exercise_logs")
        .select("id,exercise_number")
        .eq("session_id", session_id)
        .ilike("exercise_name", exercise_name)
        .limit(1)
        .execute()
    )
    rows = existing.data or []
    if rows:
        return rows[0]

    count = (
        client.table("workout_exercise_logs")
        .select("exercise_number", count="exact")
        .eq("session_id", session_id)
        .execute()
    )
    next_number = (count.count or 0) + 1

    created = (
        client.table("workout_exercise_logs")
        .insert(
            {
                "session_id": session_id,
                "exercise_number": next_number,
                "exercise_name": exercise_name,
            }
        )
        .execute()
    )
    log_rows = created.data or []
    if not log_rows:
        raise RuntimeError("workout_exercise_logs insert returned no row")
    return log_rows[0]


def start_exercise(
    exercise_name: str | None, *, context: dict[str, Any] | None = None
) -> dict[str, Any]:
    normalized_name = normalize_exercise_name(exercise_name)
    if not normalized_name:
        return {
            "ok": False,
            "status": "missing_exercise",
            "message": "Which exercise should I start?",
        }

    client, user_id = _get_supabase(context)
    if client is not None and user_id is not None:
        try:
            session_id = _find_active_session_id(client, user_id) or _create_session(client, user_id)
            _find_or_create_exercise_log(client, session_id, normalized_name)
        except Exception as exc:  # pragma: no cover
            return {
                "ok": False,
                "status": "supabase_error",
                "message": f"Could not start exercise: {exc}",
            }
        return {
            "ok": True,
            "status": "exercise_started",
            "exercise_name": normalized_name,
            "session_id": session_id,
        }

    WORKOUT_STATE.update(
        {
            "active": True,
            "current_exercise": normalized_name,
            "resting": False,
            "rest_duration_seconds": None,
        }
    )
    return {"ok": True, "status": "exercise_started", "exercise_name": normalized_name}


def log_set(
    exercise_name: str | None,
    reps: int | None,
    weight: float | None,
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_name = normalize_exercise_name(exercise_name)
    if not normalized_name or reps is None or weight is None:
        return {
            "ok": False,
            "status": "missing_fields",
            "message": "To log a set, I need the exercise, reps, and weight.",
        }

    client, user_id = _get_supabase(context)
    if client is not None and user_id is not None:
        try:
            session_id = _find_active_session_id(client, user_id) or _create_session(client, user_id)
            log = _find_or_create_exercise_log(client, session_id, normalized_name)
            set_count = (
                client.table("workout_sets")
                .select("set_number", count="exact")
                .eq("exercise_log_id", log["id"])
                .execute()
            )
            next_set_number = (set_count.count or 0) + 1

            client.table("workout_sets").insert(
                {
                    "exercise_log_id": log["id"],
                    "set_number": next_set_number,
                    "reps": reps,
                    "load_value": float(weight),
                    "load_unit": "lb",
                    "status": "manual",
                    "completed_at": _now_iso(),
                }
            ).execute()
        except Exception as exc:  # pragma: no cover
            return {
                "ok": False,
                "status": "supabase_error",
                "message": f"Could not log the set: {exc}",
            }
        return {
            "ok": True,
            "status": "logged",
            "exercise_name": normalized_name,
            "reps": reps,
            "weight": weight,
            "session_id": session_id,
            "set_number": next_set_number,
        }

    logged_set = {"exercise_name": normalized_name, "reps": reps, "weight": weight}
    LOGGED_SETS.append(logged_set)
    return {"ok": True, "status": "logged", **logged_set}


def start_rest(
    duration_seconds: int | None, *, context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Rest is a UI/timer concept — no Supabase write needed."""

    duration = duration_seconds or 90
    WORKOUT_STATE.update({"resting": True, "rest_duration_seconds": duration})
    return {"ok": True, "status": "rest_started", "duration_seconds": duration}
