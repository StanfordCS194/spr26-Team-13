"""Motivational phrases for in-ear audio coaching cues."""

import random
import subprocess
import threading

from src.contracts.common import TriggerType

SET_START_PHRASES = [
    "Let's go, own this set.",
    "Dial it in, you've got this.",
    "Stay tight, stay focused.",
    "Strong reps only.",
]

REST_PHRASES = [
    "Breathe deep, reset.",
    "Shake it out, recover.",
    "Good work. Rest up.",
]

SET_COMPLETE_PHRASES = [
    "Set down. Nice work.",
    "That's one in the bank.",
    "Clean finish.",
]

DURING_REP_PHRASES = [
    "Keep pushing.",
    "Stay strong.",
    "Almost there.",
]

WORKOUT_COMPLETE_PHRASES = [
    "Workout complete. Great effort today.",
    "That's a wrap. Well done.",
    "Finished. Go recover.",
]

_PHRASES_BY_TRIGGER = {
    TriggerType.EXERCISE_START: SET_START_PHRASES,
    TriggerType.REST_START: REST_PHRASES,
    TriggerType.REST_END: SET_START_PHRASES,
    TriggerType.SET_COMPLETE: SET_COMPLETE_PHRASES,
    TriggerType.DURING_REP: DURING_REP_PHRASES,
    TriggerType.WORKOUT_COMPLETE: WORKOUT_COMPLETE_PHRASES,
}


def pick_phrase(trigger: TriggerType) -> str | None:
    """Return a random motivational phrase for the given trigger, or None."""
    phrases = _PHRASES_BY_TRIGGER.get(trigger)
    if not phrases:
        return None
    return random.choice(phrases)


def speak_phrase(
    trigger: TriggerType,
    *,
    exercise_name: str | None = None,
    rest_seconds: int | None = None,
    enabled: bool = True,
) -> None:
    """Speak a motivational phrase for the given trigger in a background thread.

    Uses macOS `say` if available, falls back to pyttsx3, then print.
    Never raises — audio failures are silent.
    """
    if not enabled:
        return
    phrase = pick_phrase(trigger)
    if not phrase:
        return

    if trigger == TriggerType.EXERCISE_START and exercise_name:
        phrase = f"{exercise_name}. {phrase}"
    elif trigger == TriggerType.REST_START and rest_seconds:
        phrase = f"{phrase} {rest_seconds} seconds."

    def _speak() -> None:
        try:
            subprocess.Popen(["say", phrase])
            return
        except FileNotFoundError:
            pass
        except Exception:
            pass
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(phrase)
            engine.runAndWait()
            return
        except Exception:
            pass
        print(f"[audio cue] {phrase}")

    threading.Thread(target=_speak, daemon=True).start()
