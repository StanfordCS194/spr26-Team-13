"""Progressive overload recommendations from workout history."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProgressionRecommendation:
    exercise_name: str
    recommended_load: float | None
    recommended_reps: str
    reasoning: str
    estimated_1rm: float | None
    sessions_used: int
    confidence: float  # 0.0 to 1.0


def estimate_1rm(weight: float, reps: int) -> float:
    """Epley formula: 1RM = weight × (1 + reps/30)."""
    if reps <= 0:
        return weight
    if reps == 1:
        return weight
    return weight * (1 + reps / 30)


def recommend_next_session(
    exercise_name: str,
    history_rows: list[dict[str, Any]],
    *,
    rep_target: str | None = None,
) -> ProgressionRecommendation | None:
    """Recommend load and reps for the next session of an exercise.

    Uses linear progression: if the user hit their target reps last session,
    add a small increment. If they missed, hold or deload. Falls back to a
    trend-based approach when no explicit target is available.
    """
    if not history_rows:
        return None

    # Group rows by session
    sessions: dict[str, list[dict[str, Any]]] = {}
    for row in history_rows:
        session_id = str((row.get("session") or {}).get("id") or "unknown")
        sessions.setdefault(session_id, []).append(row)

    def _session_date(rows: list[dict[str, Any]]) -> str:
        return str((rows[0].get("session") or {}).get("started_at") or "")

    sorted_sessions = sorted(sessions.values(), key=_session_date, reverse=True)

    # Best set from the most recent session (highest weight, then reps)
    last_sets = [row["set"] for row in sorted_sessions[0]]
    best_last = max(
        last_sets,
        key=lambda s: (float(s.get("load_value") or 0), int(s.get("reps") or 0)),
    )
    last_weight = float(best_last.get("load_value") or 0)
    last_reps = int(best_last.get("reps") or 0)

    if last_weight == 0 and last_reps == 0:
        return None

    estimated_1rm = estimate_1rm(last_weight, last_reps) if last_weight > 0 and last_reps > 0 else None
    is_lower = _is_lower_body(exercise_name)
    base_increment = 10.0 if is_lower else 5.0
    small_increment = 5.0 if is_lower else 2.5

    # Bodyweight / unweighted movement
    if last_weight == 0:
        return ProgressionRecommendation(
            exercise_name=exercise_name,
            recommended_load=None,
            recommended_reps=rep_target or f"{last_reps} reps",
            reasoning=(
                f"You got {last_reps} reps last session. "
                "Maintain form and try to add a rep or reduce rest."
            ),
            estimated_1rm=None,
            sessions_used=len(sorted_sessions),
            confidence=0.5,
        )

    target_low, target_high = _parse_rep_target(rep_target)

    # Hit or exceeded target rep ceiling → add load
    if target_high is not None and last_reps >= target_high:
        new_load = last_weight + base_increment
        return ProgressionRecommendation(
            exercise_name=exercise_name,
            recommended_load=new_load,
            recommended_reps=rep_target or f"{last_reps} reps",
            reasoning=(
                f"You hit {last_reps} reps at {_fmt(last_weight)} lbs last session, "
                f"matching your target. Add load and try {_fmt(new_load)} lbs."
            ),
            estimated_1rm=estimated_1rm,
            sessions_used=len(sorted_sessions),
            confidence=0.85,
        )

    # Fell short of target rep floor → hold or deload
    if target_low is not None and last_reps < target_low:
        sessions_at_weight = sum(
            1 for s_rows in sorted_sessions
            if any(float(r["set"].get("load_value") or 0) >= last_weight for r in s_rows)
        )
        if sessions_at_weight >= 2:
            new_load = last_weight - small_increment
            reasoning = (
                f"You've missed the {target_low}-rep target at {_fmt(last_weight)} lbs "
                f"across {sessions_at_weight} sessions. "
                f"Try {_fmt(new_load)} lbs and focus on hitting {target_low}+ reps with clean form."
            )
        else:
            new_load = last_weight
            reasoning = (
                f"You hit {last_reps} of {target_low} target reps at {_fmt(last_weight)} lbs. "
                "Repeat the weight and aim for the full rep target before adding load."
            )
        return ProgressionRecommendation(
            exercise_name=exercise_name,
            recommended_load=new_load,
            recommended_reps=rep_target or f"{target_low} reps",
            reasoning=reasoning,
            estimated_1rm=estimated_1rm,
            sessions_used=len(sorted_sessions),
            confidence=0.75,
        )

    # No explicit target — use trend across the two most recent sessions
    if len(sorted_sessions) >= 2:
        prev_sets = [row["set"] for row in sorted_sessions[1]]
        prev_best = max(prev_sets, key=lambda s: float(s.get("load_value") or 0))
        prev_weight = float(prev_best.get("load_value") or 0)
        if prev_weight > 0 and last_weight >= prev_weight and last_reps >= 4:
            new_load = last_weight + small_increment
            return ProgressionRecommendation(
                exercise_name=exercise_name,
                recommended_load=new_load,
                recommended_reps=f"{last_reps} reps",
                reasoning=(
                    f"You moved from {_fmt(prev_weight)} to {_fmt(last_weight)} lbs. "
                    f"Progression is on track — try {_fmt(new_load)} lbs next."
                ),
                estimated_1rm=estimated_1rm,
                sessions_used=len(sorted_sessions),
                confidence=0.7,
            )

    # Default: repeat last session
    return ProgressionRecommendation(
        exercise_name=exercise_name,
        recommended_load=last_weight,
        recommended_reps=f"{last_reps} reps",
        reasoning=(
            f"Last session: {last_reps} reps at {_fmt(last_weight)} lbs. "
            "Repeat the weight and hit consistent reps before adding load."
        ),
        estimated_1rm=estimated_1rm,
        sessions_used=len(sorted_sessions),
        confidence=0.6,
    )


def format_progression_reply(rec: ProgressionRecommendation) -> str:
    """Format a progression recommendation for the voice coach to speak."""
    parts = [rec.reasoning]
    if rec.estimated_1rm and rec.estimated_1rm > 0 and rec.recommended_load:
        parts.append(f"Estimated 1RM: {_fmt(rec.estimated_1rm)} lbs.")
    return " ".join(parts)


def _parse_rep_target(rep_target: str | None) -> tuple[int | None, int | None]:
    """Parse '4-6', '5', '8-10' into (low, high) inclusive bounds."""
    if not rep_target:
        return None, None
    m = re.match(r"(\d+)\s*[-–]\s*(\d+)", str(rep_target).strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r"(\d+)", str(rep_target).strip())
    if m:
        v = int(m.group(1))
        return v, v
    return None, None


_LOWER_BODY_KEYWORDS = (
    "squat", "deadlift", "lunge", "leg press", "leg curl", "leg extension",
    "hip thrust", "romanian", "rdl", "step up", "calf", "glute bridge",
    "hack squat", "front squat", "bulgarian", "split squat",
)


def _is_lower_body(exercise_name: str) -> bool:
    normalized = exercise_name.lower()
    return any(kw in normalized for kw in _LOWER_BODY_KEYWORDS)


def _fmt(value: float) -> str:
    return str(int(value)) if value == int(value) else str(round(value, 1))
