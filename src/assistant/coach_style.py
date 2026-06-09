"""Coach personality helpers shared by chat and deterministic tools."""

from __future__ import annotations

from typing import Any


STYLE_INSTRUCTIONS = {
    "direct": (
        "Coach style: direct. Use short, plain, no-fluff language. Lead with "
        "the action or answer."
    ),
    "encouraging": (
        "Coach style: encouraging. Keep advice practical, but add a calm "
        "confidence-building tone."
    ),
    "analytical": (
        "Coach style: analytical. Give the reason behind recommendations when "
        "space allows, and prefer precise training variables."
    ),
    "high_energy": (
        "Coach style: high energy. Be punchy and upbeat while staying concise "
        "and specific."
    ),
}

EVIDENCE_INSTRUCTIONS = {
    "minimal": "Evidence preference: minimal. Cite only when it directly improves the answer.",
    "concise": "Evidence preference: concise. Mention the strongest source briefly when useful.",
    "detailed": "Evidence preference: detailed. Include a brief rationale and source name when evidence is relevant.",
}


def coach_style_from_context(context: dict[str, Any] | None) -> str:
    profile = _profile_from_context(context)
    style = str((profile or {}).get("coachStyle") or "direct").strip().lower()
    return style if style in STYLE_INSTRUCTIONS else "direct"


def style_prompt_from_context(context: dict[str, Any] | None) -> str:
    profile = _profile_from_context(context)
    style = coach_style_from_context(context)
    evidence = str((profile or {}).get("evidencePreference") or "concise").strip().lower()
    evidence_line = EVIDENCE_INSTRUCTIONS.get(evidence, EVIDENCE_INSTRUCTIONS["concise"])
    return f"{STYLE_INSTRUCTIONS[style]}\n{evidence_line}"


def style_action_reply(message: str, context: dict[str, Any] | None, *, action_name: str | None) -> str:
    """Apply personality to short deterministic success replies."""

    clean = message.strip()
    if not clean:
        return clean

    style = coach_style_from_context(context)
    action = action_name or ""

    if style == "direct":
        return clean

    if style == "encouraging":
        if action in {"log_set", "advance_set", "finish_exercise"}:
            return f"{clean} Good work."
        if action in {"start_workout", "build_workout"}:
            return f"{clean} We will keep it manageable."
        if action == "finish_workout":
            return f"{clean} Solid session."
        return clean

    if style == "analytical":
        if action == "log_set":
            return f"{clean} I will use that for your next progress check."
        if action in {"start_workout", "build_workout"}:
            return f"{clean} I matched it to your profile constraints."
        if action == "start_rest":
            return f"{clean} Keep the next set quality high."
        return clean

    if style == "high_energy":
        if action == "log_set":
            return f"{clean} Keep moving."
        if action in {"start_workout", "build_workout"}:
            return f"{clean} Let's go."
        if action == "finish_workout":
            return f"{clean} Strong finish."
        if action == "start_rest":
            return f"{clean} Breathe, then attack the next set."
        return clean

    return clean


def _profile_from_context(context: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(context, dict):
        return None
    profile = context.get("trainingProfile")
    return profile if isinstance(profile, dict) else None
