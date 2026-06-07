"""Canonical exercise IDs used across ingestion, sensing, and logging."""

from __future__ import annotations

from functools import lru_cache
import re


EXERCISE_CATALOG = {
    "back_squat": {
        "display_name": "Back Squat",
        "detection_mode": "imu",
        "aliases": ["squat", "barbell back squat"],
    },
    "bench_press": {
        "display_name": "Bench Press",
        "detection_mode": "imu",
        "aliases": ["barbell bench press", "bench"],
    },
    "deadlift": {
        "display_name": "Deadlift",
        "detection_mode": "imu",
        "aliases": ["conventional deadlift"],
    },
    "overhead_press": {
        "display_name": "Overhead Press",
        "detection_mode": "imu",
        "aliases": ["strict press", "shoulder press"],
    },
    "barbell_row": {
        "display_name": "Barbell Row",
        "detection_mode": "imu",
        "aliases": ["bent over row", "barbell bent over row"],
    },
    "romanian_deadlift": {
        "display_name": "Romanian Deadlift",
        "detection_mode": "manual",
        "aliases": ["rdl"],
    },
    "pull_up": {
        "display_name": "Pull-Up",
        "detection_mode": "manual",
        "aliases": ["pull up", "chin up"],
    },
    "lat_pulldown": {
        "display_name": "Lat Pulldown",
        "detection_mode": "manual",
        "aliases": ["lat pull down"],
    },
    "split_squat": {
        "display_name": "Split Squat",
        "detection_mode": "manual",
        "aliases": ["bulgarian split squat"],
    },
}


# ---------------------------------------------------------------------------
# Name resolution
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _name_index() -> dict[str, str]:
    """Build {recognized_name (lowercased): canonical_id} from the catalog, once."""
    index: dict[str, str] = {}
    for canonical_id, entry in EXERCISE_CATALOG.items():
        index[canonical_id.lower()] = canonical_id
        display = (entry.get("display_name") or "").strip().lower()
        if display:
            index[display] = canonical_id
        for alias in entry.get("aliases", []) or []:
            index[str(alias).strip().lower()] = canonical_id
    return index


def _norm(raw: str) -> str:
    return " ".join(raw.strip().lower().split())


def resolve_exercise_name(raw: str | None) -> str | None:
    """Map any display name, alias, or id to its canonical catalog id.

    Returns a canonical id (e.g. "back_squat") or None if there is no confident
    match. Unknown input returns None so callers fall back gracefully.
    """
    if not raw:
        return None
    index = _name_index()
    base = _norm(raw)
    candidates = [base, base.replace("-", " "), base.replace(" ", "-")]
    stripped = _norm(re.sub(r"\(.*?\)", "", base))
    if stripped and stripped != base:
        candidates += [stripped, stripped.replace("-", " "), stripped.replace(" ", "-")]
    for cand in candidates:
        if cand in index:
            return index[cand]
    return None
