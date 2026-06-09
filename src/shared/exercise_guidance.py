"""
exercise_guidance.py — static coaching cues for the audio coach.

Single source of truth for per-exercise form cues, keyed to the canonical
exercise ids in exercise_catalog.py. Consumed by:
  - the live coaching reply (_format_step_message in supabase_tools.py)
  - the demo-overlay audio (speak_phrase in glasses/audio/motivational.py)

Design:
  - cues are static and deterministic: the same lift gives the same cue every
    time, because form guidance doesn't change between sets. No LLM call ->
    no latency, no hallucination.
  - keyed to catalog canonical ids; name/alias resolution is delegated to
    exercise_catalog.resolve_exercise_name so this module owns no name list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.shared.exercise_catalog import resolve_exercise_name


@dataclass(frozen=True)
class ExerciseGuidance:
    canonical_id: str
    cue: str

    @property
    def short_cue(self) -> str:
        """First sentence only — for the live spoken reply, where brevity matters."""
        return first_sentence(self.cue)


def first_sentence(text: str) -> str:
    """Return the first sentence of `text` (up to and including its period)."""
    match = re.search(r"\.\s", text)
    return text[: match.start() + 1] if match else text


GUIDANCE: dict[str, ExerciseGuidance] = {
    "back_squat": ExerciseGuidance(
        "back_squat",
        "Big breath, brace hard, and sit straight down between your hips. "
        "Keep your midfoot rooted and drive your hips and chest up together.",
    ),
    "bench_press": ExerciseGuidance(
        "bench_press",
        "Set your upper back first — shoulder blades back and down, feet planted, "
        "bar over your wrists. Control the touch, then drive the bar up and slightly back.",
    ),
    "deadlift": ExerciseGuidance(
        "deadlift",
        "Pull the slack out of the bar, brace, and push the floor away. "
        "Keep the bar close and let your hips and chest rise together.",
    ),
    "overhead_press": ExerciseGuidance(
        "overhead_press",
        "Squeeze your glutes, brace your abs, and keep the bar stacked over your midfoot. "
        "Press straight up, then bring your head through once the bar clears your face.",
    ),
    "barbell_row": ExerciseGuidance(
        "barbell_row",
        "Hinge into a strong position and lock your torso in. Pull your elbows back "
        "toward your hips, pause briefly, and don't let the lower back take over.",
    ),
    "romanian_deadlift": ExerciseGuidance(
        "romanian_deadlift",
        "Soft knees, hips back, and keep the bar close the whole way down. "
        "Feel the hamstrings load, then drive the hips through without overextending.",
    ),
    "pull_up": ExerciseGuidance(
        "pull_up",
        "Start from a dead hang, pull your shoulder blades down first, then drive your "
        "elbows toward your ribs. Keep the reps clean and avoid kicking.",
    ),
    "lat_pulldown": ExerciseGuidance(
        "lat_pulldown",
        "Lean back slightly, chest tall, and pull your elbows down into your sides. "
        "Don't yank with the hands — think about driving through the lats.",
    ),
    "split_squat": ExerciseGuidance(
        "split_squat",
        "Lock in your front foot and control the descent. Stay balanced, let the front "
        "leg do the work, and drive up through the midfoot.",
    ),
}


def get_guidance(name_or_id: str | None) -> ExerciseGuidance | None:
    canonical = resolve_exercise_name(name_or_id)
    return GUIDANCE.get(canonical) if canonical else None


def get_cue_for(name_or_id: str | None) -> str | None:
    """Full coaching cue for a display name / alias / id. None if unknown."""
    g = get_guidance(name_or_id)
    return g.cue if g else None


def get_short_cue_for(name_or_id: str | None) -> str | None:
    """First-sentence cue, for the live spoken reply. None if unknown."""
    g = get_guidance(name_or_id)
    return g.short_cue if g else None


def coaching_cue_for(name_or_id: str | None, notes: str | None = None) -> str | None:
    """Layered cue for the spoken reply, shortened for speech.

    Precedence: program-specific notes > static catalog cue > None.
    """
    if isinstance(notes, str) and notes.strip():
        return first_sentence(notes.strip())
    return get_short_cue_for(name_or_id)


if __name__ == "__main__":
    # Runnable smoke test: python -m src.shared.exercise_guidance
    print("== resolution ==")
    for probe in [
        "Back Squat", "bench", "Romanian Deadlift", "Pull-Up", "pull up",
        "Barbell Back Squat", "Back Squat (Top Single)", "Lat Pulldown",
        "Overhead Press", "Split Squat", "Deadlift", "Barbell Row", "nonsense lift",
    ]:
        print(f"  {probe!r:28} -> {resolve_exercise_name(probe)}")

    print("\n== short cues (what the glasses speak) ==")
    for cid, g in GUIDANCE.items():
        print(f"  {cid:20} -> {g.short_cue}")

    print("\n== notes override ==")
    print("  notes present ->", coaching_cue_for("Back Squat", notes="Brace hard and move fast."))
    print("  notes empty   ->", coaching_cue_for("Back Squat", notes=None))

    print("\n== catalog consistency ==")
    bad = [cid for cid in GUIDANCE if resolve_exercise_name(cid) != cid]
    print("  guidance keys not in catalog:", bad or "none ✓")
