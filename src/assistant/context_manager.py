"""Context assembly for the glasses coach chat route."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


MAX_HISTORY_MESSAGES = 8


@dataclass
class ConversationState:
    """Short-lived in-memory chat history for one coach session."""

    messages: list[dict[str, str]] = field(default_factory=list)


class CoachContextManager:
    """Build compact LLM messages from app state and recent coach turns."""

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationState] = {}

    def build_messages(
        self,
        *,
        session_id: str,
        user_text: str,
        app_context: dict[str, Any] | None,
        system_prompt: str,
    ) -> list[dict[str, str]]:
        state = self._sessions.setdefault(session_id, ConversationState())
        return [
            {"role": "system", "content": self._build_system_message(system_prompt, app_context)},
            *state.messages[-MAX_HISTORY_MESSAGES:],
            {"role": "user", "content": user_text},
        ]

    def record_turn(self, *, session_id: str, user_text: str, assistant_reply: str) -> None:
        state = self._sessions.setdefault(session_id, ConversationState())
        state.messages.extend(
            [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": assistant_reply},
            ]
        )
        state.messages = state.messages[-MAX_HISTORY_MESSAGES:]

    def _build_system_message(self, base_prompt: str, app_context: dict[str, Any] | None) -> str:
        context_summary = self._summarize_app_context(app_context)
        if not context_summary:
            return base_prompt
        return f"{base_prompt}\n\nCurrent TrainAR context:\n{context_summary}"

    def _summarize_app_context(self, app_context: dict[str, Any] | None) -> str:
        if not isinstance(app_context, dict):
            return ""

        lines: list[str] = []
        current_workout = app_context.get("currentWorkout")
        active_program = app_context.get("activeProgram")
        programs = app_context.get("programs")
        records = app_context.get("personalRecords")
        sessions = app_context.get("recentSessions")
        glasses = app_context.get("glasses")
        profile = app_context.get("trainingProfile")

        if isinstance(profile, dict):
            profile_parts = []
            if profile.get("trainingGoal"):
                profile_parts.append(f"goal {profile['trainingGoal']}")
            if profile.get("trainingExperience"):
                profile_parts.append(f"experience {profile['trainingExperience']}")
            if profile.get("workoutDaysPerWeek"):
                profile_parts.append(f"{profile['workoutDaysPerWeek']} days/week")
            if profile.get("workoutSessionMinutes"):
                profile_parts.append(f"{profile['workoutSessionMinutes']} min/session")
            equipment = profile.get("availableEquipment")
            if isinstance(equipment, list) and equipment:
                profile_parts.append(f"equipment {', '.join(str(item) for item in equipment[:6])}")
            if profile.get("coachStyle"):
                profile_parts.append(f"coach style {profile['coachStyle']}")
            if profile.get("evidencePreference"):
                profile_parts.append(f"evidence preference {profile['evidencePreference']}")
            if profile.get("movementConstraints"):
                profile_parts.append(f"constraints {profile['movementConstraints']}")
            if profile_parts:
                lines.append(f"- Training profile: {'; '.join(profile_parts)}.")

        if isinstance(current_workout, dict):
            title = current_workout.get("title") or current_workout.get("programName") or "active workout"
            lines.append(f"- Current workout: {title}.")

        if isinstance(active_program, dict):
            name = active_program.get("name") or active_program.get("title")
            exercises = active_program.get("exercises") if isinstance(active_program.get("exercises"), list) else []
            exercise_names = [
                str(exercise.get("name") or exercise.get("exercise_name"))
                for exercise in exercises[:5]
                if isinstance(exercise, dict) and (exercise.get("name") or exercise.get("exercise_name"))
            ]
            if name:
                suffix = f" Exercises: {', '.join(exercise_names)}." if exercise_names else ""
                lines.append(f"- Active program: {name}.{suffix}")

        if isinstance(programs, list) and programs:
            names = [
                str(program.get("name") or program.get("title"))
                for program in programs[:3]
                if isinstance(program, dict) and (program.get("name") or program.get("title"))
            ]
            if names:
                lines.append(f"- Saved programs: {', '.join(names)}.")

        if isinstance(records, list) and records:
            record_lines = []
            for record in records[:5]:
                if not isinstance(record, dict):
                    continue
                exercise = record.get("exercise_name") or record.get("exerciseName")
                value = record.get("value") or record.get("weight")
                unit = record.get("unit") or "lb"
                if exercise and value:
                    record_lines.append(f"{exercise} {value} {unit}")
            if record_lines:
                lines.append(f"- Recent PRs: {', '.join(record_lines)}.")

        if isinstance(sessions, list) and sessions:
            lines.append(f"- Recent workouts available: {len(sessions)}.")

        if isinstance(glasses, dict) and glasses:
            connected = bool(glasses.get("connected"))
            device = glasses.get("deviceName") or "glasses"
            lines.append(f"- Glasses: {device} {'connected' if connected else 'not connected'}.")

        return "\n".join(lines)
