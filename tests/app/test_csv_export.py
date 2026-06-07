"""Tests for the CSV workout history exporter."""

import csv
import io

from src.export.csv.exporter import export_history_to_csv, export_session_to_csv
from src.assistant.supabase_tools import SupabaseToolError
import pytest


class _FakeSessionClient:
    def select(self, table, params):
        if table == "workout_sessions":
            return [{"id": "session-1", "title": "Upper Push", "started_at": "2026-06-05T09:00:00"}]
        if table == "workout_exercise_logs":
            return [
                {"id": "l1", "exercise_number": 1, "exercise_name": "Bench Press"},
                {"id": "l2", "exercise_number": 2, "exercise_name": "Overhead Press"},
            ]
        if table == "workout_sets":
            return [
                {"exercise_log_id": "l1", "set_number": 1, "reps": 5, "load_value": 185, "load_unit": "lb", "rpe": 7, "completed_at": "2026-06-05T09:10:00"},
                {"exercise_log_id": "l1", "set_number": 2, "reps": 5, "load_value": 185, "load_unit": "lb", "rpe": 8, "completed_at": "2026-06-05T09:15:00"},
                {"exercise_log_id": "l2", "set_number": 1, "reps": 8, "load_value": 95, "load_unit": "lb", "rpe": None, "completed_at": "2026-06-05T09:25:00"},
            ]
        return []


class _FakeHistoryClient:
    def select(self, table, params):
        if table == "workout_sessions":
            return [
                {"id": "s1", "title": "Push A", "started_at": "2026-06-05T09:00:00", "status": "completed"},
                {"id": "s2", "title": "Leg Day", "started_at": "2026-05-29T09:00:00", "status": "completed"},
            ]
        if table == "workout_exercise_logs":
            return [
                {"id": "l1", "session_id": "s1", "exercise_number": 1, "exercise_name": "Bench Press"},
                {"id": "l2", "session_id": "s2", "exercise_number": 1, "exercise_name": "Back Squat"},
            ]
        if table == "workout_sets":
            return [
                {"exercise_log_id": "l1", "set_number": 1, "reps": 5, "load_value": 185, "load_unit": "lb", "rpe": 7, "completed_at": "2026-06-05T09:10:00"},
                {"exercise_log_id": "l2", "set_number": 1, "reps": 5, "load_value": 275, "load_unit": "lb", "rpe": None, "completed_at": "2026-05-29T09:10:00"},
            ]
        return []


def _parse_csv(csv_string: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(csv_string))
    return list(reader)


def test_export_session_has_correct_headers(monkeypatch):
    monkeypatch.setattr("src.export.csv.exporter._make_client", lambda token: _FakeSessionClient())
    csv_out = export_session_to_csv("session-1", "fake-token")
    rows = _parse_csv(csv_out)
    assert "session_id" in csv_out
    assert "exercise_name" in csv_out
    assert "load_value" in csv_out
    assert len(rows) == 3


def test_export_session_includes_all_sets(monkeypatch):
    monkeypatch.setattr("src.export.csv.exporter._make_client", lambda token: _FakeSessionClient())
    rows = _parse_csv(export_session_to_csv("session-1", "fake-token"))
    exercise_names = [r["exercise_name"] for r in rows]
    assert "Bench Press" in exercise_names
    assert "Overhead Press" in exercise_names


def test_export_session_correct_load_and_reps(monkeypatch):
    monkeypatch.setattr("src.export.csv.exporter._make_client", lambda token: _FakeSessionClient())
    rows = _parse_csv(export_session_to_csv("session-1", "fake-token"))
    bench_rows = [r for r in rows if r["exercise_name"] == "Bench Press"]
    assert len(bench_rows) == 2
    assert bench_rows[0]["load_value"] == "185"
    assert bench_rows[0]["reps"] == "5"


def test_export_session_raises_for_missing_session(monkeypatch):
    class EmptyClient:
        def select(self, table, params):
            return []

    monkeypatch.setattr("src.export.csv.exporter._make_client", lambda token: EmptyClient())
    with pytest.raises(SupabaseToolError):
        export_session_to_csv("nonexistent", "fake-token")


def test_export_history_has_correct_headers(monkeypatch):
    monkeypatch.setattr("src.export.csv.exporter._make_client", lambda token: _FakeHistoryClient())
    csv_out = export_history_to_csv("fake-token", days=90)
    assert "date" in csv_out
    assert "session_title" in csv_out
    assert "volume_lbs" in csv_out


def test_export_history_computes_volume(monkeypatch):
    monkeypatch.setattr("src.export.csv.exporter._make_client", lambda token: _FakeHistoryClient())
    rows = _parse_csv(export_history_to_csv("fake-token", days=90))
    bench = next((r for r in rows if r["exercise_name"] == "Bench Press"), None)
    assert bench is not None
    assert float(bench["volume_lbs"]) == pytest.approx(5 * 185)


def test_export_history_includes_multiple_sessions(monkeypatch):
    monkeypatch.setattr("src.export.csv.exporter._make_client", lambda token: _FakeHistoryClient())
    rows = _parse_csv(export_history_to_csv("fake-token", days=90))
    titles = {r["session_title"] for r in rows}
    assert "Push A" in titles
    assert "Leg Day" in titles


def test_export_history_empty_returns_header_only(monkeypatch):
    class EmptyClient:
        def select(self, table, params):
            return []

    monkeypatch.setattr("src.export.csv.exporter._make_client", lambda token: EmptyClient())
    csv_out = export_history_to_csv("fake-token", days=90)
    rows = _parse_csv(csv_out)
    assert len(rows) == 0
    assert "date" in csv_out
