"""Hardware-independent audio coaching cue library for compound lifts.

Returns cue text only — no audio playback, no hardware calls.
Plug the output into the glasses audio layer once hardware is ready.
"""

import random
from typing import Optional

from src.contracts.common import TriggerType

# ---------------------------------------------------------------------------
# Alias table: any user-facing string -> canonical exercise_id
# ---------------------------------------------------------------------------

_ALIASES: dict[str, str] = {
    "bench": "bench_press",
    "bench press": "bench_press",
    "barbell bench press": "bench_press",
    "flat bench": "bench_press",
    "squat": "back_squat",
    "back squat": "back_squat",
    "barbell squat": "back_squat",
    "dl": "deadlift",
    "dead lift": "deadlift",
    "conventional deadlift": "deadlift",
    "ohp": "overhead_press",
    "overhead press": "overhead_press",
    "shoulder press": "overhead_press",
    "press": "overhead_press",
    "barbell row": "barbell_row",
    "bent over row": "barbell_row",
    "bent-over row": "barbell_row",
    "row": "barbell_row",
}

# ---------------------------------------------------------------------------
# Cue library: exercise_id -> TriggerType -> list[cue_text]
# ---------------------------------------------------------------------------

_CUES: dict[str, dict[TriggerType, list[str]]] = {
    "bench_press": {
        TriggerType.EXERCISE_START: [
            "Four points of contact: head, upper back, glutes, feet.",
            "Retract and depress your shoulder blades — not just pinch them.",
            "Squeeze the bar hard and take a big belly breath before you unrack.",
            "Feet back and planted. Drive the heels down, butt stays on the bench.",
        ],
        TriggerType.DURING_REP: [
            "Break the board — explode through the sticking point.",
            "Bend the bar in half to keep your lats engaged on the way down.",
            "Soft touch on the chest, no bounce.",
            "Press up and slightly back — bar finishes over the shoulders, not the face.",
            "Hold your breath until halfway up — exhaling off the chest kills tightness.",
        ],
        TriggerType.REST_START: [
            "Rack it and breathe. You earned this rest.",
            "Shake out the chest. Let your upper back recover.",
        ],
        TriggerType.REST_END: [
            "Next set. Reset your setup from scratch — every point of contact.",
            "Get tight before you touch the bar.",
        ],
    },
    "back_squat": {
        TriggerType.EXERCISE_START: [
            "Walkout: one step back, one step to match, one adjustment. No wandering.",
            "Big breath into the belly, brace 360° against your core.",
            "Pull your elbows down to lock the upper back tight.",
            "Tripod foot — heel, big toe, pinky toe all in contact with the floor.",
        ],
        TriggerType.DURING_REP: [
            "Break at hips and knees together — descend as one unit.",
            "Push the floor away through your midfoot, not your heels.",
            "Break parallel — hip crease at or below the knee.",
            "Bar path stays over midfoot — any drift forward and your hips will rise early.",
        ],
        TriggerType.REST_START: [
            "Walk it back and breathe. Good set.",
            "Let your legs recover. Stay loose.",
        ],
        TriggerType.REST_END: [
            "Back under the bar. Brace before you unrack.",
            "Set your feet and get tight. Let's go.",
        ],
    },
    "deadlift": {
        TriggerType.EXERCISE_START: [
            "Bar over midfoot, about one inch from your shins.",
            "Hinge back first with nearly straight knees, then bend to the bar. It's a hinge, not a squat.",
            "Chest up, protect your armpits — get your lats tight before you pull.",
            "Shins vertical, grip just outside the shins.",
        ],
        TriggerType.DURING_REP: [
            "Pull the slack out first — never rip a cold bar off the floor.",
            "Push the floor away — hips and shoulders rise together.",
            "Drag the bar up your legs. Any gap means your lower back is doing the work.",
            "Chest up, hips through at lockout. No shrug, no lean back — just stand tall.",
        ],
        TriggerType.REST_START: [
            "Step back and breathe. Let your posterior chain reset.",
            "Good pull. Recover before the next one.",
        ],
        TriggerType.REST_END: [
            "Step back in. Get your position right before you pull.",
            "Next pull. Set up clean — hinge, brace, slack out.",
        ],
    },
    "overhead_press": {
        TriggerType.EXERCISE_START: [
            "Bar sits low in the palm, close to the wrists — forearms vertical under the bar.",
            "Elbows slightly in front of the bar at the start, not flared to the sides.",
            "Glutes squeezed, abs tight, ribs down. This prevents the lower back arch.",
        ],
        TriggerType.DURING_REP: [
            "Ribs down and glutes tight — don't let it become an incline press.",
            "Move your face out of the way, then drive your head through the window at the top.",
            "Stay vertical — legs are a platform, not an engine.",
            "Shrug and lock at the top to finish the full range of motion.",
        ],
        TriggerType.REST_START: [
            "Rack it and shake out the shoulders.",
            "Good set. Let the traps and delts breathe.",
        ],
        TriggerType.REST_END: [
            "Back to the bar. Ribs down and full-body tension before you press.",
            "Next set. Forearms vertical and get braced.",
        ],
    },
    "barbell_row": {
        TriggerType.EXERCISE_START: [
            "Hinge to roughly parallel — treat it like a deadlift setup before it's a row.",
            "Neutral spine, pre-tension the lats before the first rep.",
            "Big breath, brace, elbows ready to drive down and back.",
        ],
        TriggerType.DURING_REP: [
            "Drive the elbows down and back — lead with the elbows, not the hands.",
            "Pull to your lower chest or upper belly to maximize lat engagement.",
            "Keep the torso locked — if it's rising with the bar, the weight is too heavy.",
            "Full reset on the floor between reps. No bouncing — dead start every rep.",
            "Squeeze the shoulder blades at the top, then control the negative.",
        ],
        TriggerType.REST_START: [
            "Stand up and let your lower back decompress.",
            "Good set. Breathe and let your lats recover.",
        ],
        TriggerType.REST_END: [
            "Hinge back in. Neutral spine and pre-tensioned before you pull.",
            "Next set. Dead start — full reset every rep.",
        ],
    },
}

# ---------------------------------------------------------------------------
# General motivational cues (not exercise-specific)
# ---------------------------------------------------------------------------

_MOTIVATIONAL: list[str] = [
    "Next set is ready. Lock in.",
    "Good work. Stay focused for the next one.",
    "One set at a time. Reset and execute.",
    "You put in the work. Now finish it.",
    "Stay present. One rep at a time.",
    "Trust the process. Keep moving.",
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_exercise_name(exercise_name: str) -> Optional[str]:
    """Return canonical exercise_id for a name or alias, or None if unknown."""
    key = exercise_name.strip().lower()
    if key in _CUES:
        return key
    return _ALIASES.get(key)


def get_audio_cues(exercise_name: str, phase: TriggerType) -> list[str]:
    """Return all cue texts for an exercise + phase. Empty list if unknown."""
    exercise_id = normalize_exercise_name(exercise_name)
    if exercise_id is None:
        return []
    return list(_CUES.get(exercise_id, {}).get(phase, []))


def choose_audio_cue(
    exercise_name: str,
    phase: TriggerType,
    seed: Optional[int] = None,
) -> Optional[str]:
    """Return one cue text chosen randomly. None if no cues exist."""
    cues = get_audio_cues(exercise_name, phase)
    if not cues:
        return None
    return random.Random(seed).choice(cues)


def build_next_set_prompt(
    exercise_name: str,
    set_number: int,
    target_reps: int,
    target_load: Optional[float] = None,
    load_unit: str = "lb",
) -> str:
    """Build a spoken next-set announcement string."""
    display = exercise_name.replace("_", " ").title()
    text = f"Set {set_number}: {target_reps} reps of {display}"
    if target_load is not None:
        text += f" at {target_load} {load_unit}"
    return text + "."


def choose_motivational_cue(seed: Optional[int] = None) -> str:
    """Return a random general motivational cue."""
    return random.Random(seed).choice(_MOTIVATIONAL)
