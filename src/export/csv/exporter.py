"""CSV export for workout sessions and training history."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta
from typing import Any

from src.assistant.supabase_tools import (
    DEFAULT_SUPABASE_KEY,
    DEFAULT_SUPABASE_URL,
    SupabaseConfig,
    SupabaseRestClient,
    SupabaseToolError,
    _in_filter,  # noqa: PLC2701 — shared private helper
    _now_iso,
)


def export_session_to_csv(session_id: str, access_token: str) -> str:
    """Return a CSV string for every set logged in a single workout session.

    Columns: session_id, session_title, started_at, exercise_name,
             set_number, reps, load_value, load_unit, rpe, completed_at
    """
    client = _make_client(access_token)
    sessions = client.select(
        "workout_sessions",
        {"select": "id,title,started_at", "id": f"eq.{session_id}", "limit": "1"},
    )
    if not sessions:
        raise SupabaseToolError(f"Session {session_id} not found.")
    session = sessions[0]

    logs = client.select(
        "workout_exercise_logs",
        {
            "select": "id,exercise_number,exercise_name",
            "session_id": f"eq.{session_id}",
            "order": "exercise_number",
        },
    )
    log_ids = [str(log["id"]) for log in logs if log.get("id")]
    sets = client.select(
        "workout_sets",
        {
            "select": "exercise_log_id,set_number,reps,load_value,load_unit,rpe,completed_at",
            "exercise_log_id": _in_filter(log_ids),
            "order": "set_number",
        },
    ) if log_ids else []

    logs_by_id = {str(log["id"]): log for log in logs if log.get("id")}
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "session_id", "session_title", "started_at",
        "exercise_name", "set_number", "reps",
        "load_value", "load_unit", "rpe", "completed_at",
    ])
    for s in sets:
        log = logs_by_id.get(str(s.get("exercise_log_id")), {})
        writer.writerow([
            session.get("id"),
            session.get("title") or "",
            session.get("started_at") or "",
            log.get("exercise_name") or "",
            s.get("set_number") or "",
            s.get("reps") or "",
            s.get("load_value") or "",
            s.get("load_unit") or "lb",
            s.get("rpe") or "",
            s.get("completed_at") or "",
        ])
    return output.getvalue()


def export_history_to_csv(access_token: str, *, days: int = 90) -> str:
    """Return a CSV string for all sets in the past `days` days.

    Columns: date, session_title, exercise_name, set_number,
             reps, load_value, load_unit, rpe, volume_lbs
    """
    client = _make_client(access_token)
    since = (datetime.now(UTC) - timedelta(days=days)).isoformat()
    sessions = client.select(
        "workout_sessions",
        {
            "select": "id,title,started_at,status",
            "started_at": f"gte.{since}",
            "status": "eq.completed",
            "order": "started_at.desc",
            "limit": "500",
        },
    )
    if not sessions:
        return "date,session_title,exercise_name,set_number,reps,load_value,load_unit,rpe,volume_lbs\n"

    session_ids = [str(s["id"]) for s in sessions if s.get("id")]
    sessions_by_id = {str(s["id"]): s for s in sessions if s.get("id")}

    logs = client.select(
        "workout_exercise_logs",
        {
            "select": "id,session_id,exercise_number,exercise_name",
            "session_id": _in_filter(session_ids),
            "order": "exercise_number",
        },
    )
    log_ids = [str(log["id"]) for log in logs if log.get("id")]
    logs_by_id = {str(log["id"]): log for log in logs if log.get("id")}

    sets = client.select(
        "workout_sets",
        {
            "select": "exercise_log_id,set_number,reps,load_value,load_unit,rpe,completed_at",
            "exercise_log_id": _in_filter(log_ids),
            "order": "completed_at.desc.nullslast,set_number",
            "limit": "5000",
        },
    ) if log_ids else []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "date", "session_title", "exercise_name",
        "set_number", "reps", "load_value", "load_unit", "rpe", "volume_lbs",
    ])
    for s in sets:
        log = logs_by_id.get(str(s.get("exercise_log_id")), {})
        session = sessions_by_id.get(str(log.get("session_id")), {})
        reps = s.get("reps") or 0
        load = s.get("load_value") or 0
        volume = round(float(reps) * float(load), 1) if reps and load else ""
        date_str = _format_date(session.get("started_at") or s.get("completed_at"))
        writer.writerow([
            date_str,
            session.get("title") or "",
            log.get("exercise_name") or "",
            s.get("set_number") or "",
            reps or "",
            load or "",
            s.get("load_unit") or "lb",
            s.get("rpe") or "",
            volume,
        ])
    return output.getvalue()


def register_export_routes(app: Any) -> None:
    """Register CSV download routes on the given Flask app."""
    from flask import Response, request

    @app.get("/api/export/session")
    def export_session_route():
        session_id = request.args.get("session_id", "").strip()
        access_token = (
            request.args.get("access_token")
            or request.headers.get("X-Supabase-Access-Token", "")
        ).strip()
        if not session_id or not access_token:
            return {"error": "session_id and access_token are required"}, 400
        try:
            csv_data = export_session_to_csv(session_id, access_token)
        except SupabaseToolError as exc:
            return {"error": str(exc)}, 404
        filename = f"workout_{session_id[:8]}.csv"
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.get("/api/export/history")
    def export_history_route():
        access_token = (
            request.args.get("access_token")
            or request.headers.get("X-Supabase-Access-Token", "")
        ).strip()
        days = min(int(request.args.get("days", 90)), 365)
        if not access_token:
            return {"error": "access_token is required"}, 400
        try:
            csv_data = export_history_to_csv(access_token, days=days)
        except SupabaseToolError as exc:
            return {"error": str(exc)}, 502
        filename = f"training_history_{_now_iso()[:10]}.csv"
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


def _make_client(access_token: str) -> SupabaseRestClient:
    import os
    config = SupabaseConfig(
        url=os.getenv("SUPABASE_URL") or os.getenv("TRAINAR_SUPABASE_URL") or DEFAULT_SUPABASE_URL,
        anon_key=os.getenv("SUPABASE_ANON_KEY") or os.getenv("TRAINAR_SUPABASE_KEY") or DEFAULT_SUPABASE_KEY,
    )
    return SupabaseRestClient(config, access_token)


def _format_date(value: Any) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return f"{parsed:%Y-%m-%d}"
    except ValueError:
        return str(value)
