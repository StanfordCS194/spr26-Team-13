"""Canonical exercise IDs used across ingestion, sensing, and logging."""

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
