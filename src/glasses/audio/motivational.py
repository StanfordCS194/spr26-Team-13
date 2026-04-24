"""Motivational phrases for in-ear audio coaching cues."""

import random

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

_PHRASES_BY_TRIGGER = {
    TriggerType.EXERCISE_START: SET_START_PHRASES,
    TriggerType.REST_START: REST_PHRASES,
    TriggerType.REST_END: SET_START_PHRASES,
    TriggerType.SET_COMPLETE: SET_COMPLETE_PHRASES,
}


def pick_phrase(trigger: TriggerType) -> str | None:
    """Return a random motivational phrase for the given trigger, or None."""
    phrases = _PHRASES_BY_TRIGGER.get(trigger)
    if not phrases:
        return None
    return random.choice(phrases)
