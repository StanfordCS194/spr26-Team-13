#!/usr/bin/env python3
"""Seed the BYPASS_LOGIN test account with demo data via the Supabase REST API.

Mirrors supabase/seed_demo_callum.sql, but runs as the authenticated test user
(RLS allows a user full CRUD on their own rows), so it needs no service-role key
or DB password — just the account's email/password.

Idempotent: deletes any prior 'Demo seed' rows for this user before inserting.

Usage:
    python supabase/seed_test_account.py [email] [password]
Defaults to the trainar.dev.test account.
"""
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta, timezone

SUPABASE_URL = "https://rcmlbgjqwpfzpiownxfy.supabase.co"
ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJjbWxiZ2pxd3BmenBpb3dueGZ5Iiwicm9sZSI6ImFub24i"
    "LCJpYXQiOjE3NzgyMjU2NzgsImV4cCI6MjA5MzgwMTY3OH0.fKcwQ0Jws91vA9PcHg8PdyWDhP8WXYg4WFU5ll8ubyo"
)

EMAIL = sys.argv[1] if len(sys.argv) > 1 else "trainar.dev.test@example.com"
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else "trainardev123"

NOW = datetime.now(timezone.utc)


def iso(dt):
    return dt.isoformat()


def days_ago(n):
    return NOW - timedelta(days=n)


def request(method, path, token, body=None, params=None, prefer=None):
    url = f"{SUPABASE_URL}{path}"
    if params:
        # Encode values but keep PostgREST's operator dot and like-wildcard '*'.
        url += "?" + "&".join(
            f"{k}={urllib.parse.quote(v, safe='.*')}" for k, v in params.items()
        )
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> HTTP {e.code}: {e.read().decode()}")


def sign_in():
    body = {"email": EMAIL, "password": PASSWORD}
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        data=data,
        headers={"apikey": ANON_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        d = json.loads(resp.read().decode())
    return d["access_token"], d["user"]["id"]


def insert(table, token, rows, returning=False, upsert=False):
    prefer = "return=representation" if returning else "return=minimal"
    if upsert:
        prefer += ",resolution=merge-duplicates"
    return request("POST", f"/rest/v1/{table}", token, body=rows, prefer=prefer)


def delete(table, token, params):
    request("DELETE", f"/rest/v1/{table}", token, params=params, prefer="return=minimal")


# 5-day program-day exercise breakdown (matches the SQL seed).
DAY_EXERCISES = {
    1: [
        (1, "Back Squat (Top Single)", 1, "1", "365 lb", 240, "Brace hard and move fast."),
        (2, "Back Squat", 5, "3", "320 lb", 180, "Full depth, consistent bar path."),
        (3, "Barbell Overhead Press", 3, "8", "115 lb", 120, "Press up and back."),
        (4, "Pin Good Morning", 2, "8-10", "155 lb", 120, "Controlled hinge."),
        (5, "Chest-Supported Row", 4, "8-10", "90 lb", 90, "Pause at top."),
    ],
    2: [
        (1, "Barbell Bench Press", 4, "6", "210 lb", 180, "Quick pause."),
        (2, "Pull-Up", 4, "8", "BW", 120, "Full hang."),
        (3, "Incline Dumbbell Press", 3, "10", "70 lb", 120, "Smooth eccentric."),
        (4, "Tricep Pushdown", 3, "12", "60 lb", 90, "Lock elbows."),
        (5, "Dumbbell Curl", 3, "12", "35 lb", 90, "No swing."),
    ],
    3: [
        (1, "Deadlift", 3, "3", "315 lb", 240, "Pull slack first."),
        (2, "Romanian Deadlift", 3, "10", "185 lb", 120, "Hamstring stretch."),
        (3, "Barbell Row", 4, "8", "155 lb", 120, "Pull to lower chest."),
        (4, "Hanging Leg Raise", 3, "12", "BW", 60, "Controlled reps."),
    ],
    4: [
        (1, "Front Squat", 4, "5", "225 lb", 180, "Tall torso."),
        (2, "Close-Grip Bench Press", 4, "8", "185 lb", 150, "Elbows tucked."),
        (3, "Lat Pulldown", 4, "10", "130 lb", 90, "Drive elbows down."),
        (4, "Standing Calf Raise", 3, "15", "180 lb", 90, "Pause at top."),
    ],
    5: [
        (1, "Paused Bench Press", 5, "3", "225 lb", 180, "Long pause."),
        (2, "Back Squat", 4, "6", "275 lb", 180, "Volume work."),
        (3, "Seated Cable Row", 4, "10", "140 lb", 90, "Neutral grip."),
        (4, "Face Pull", 3, "15", "45 lb", 60, "Rear delts."),
    ],
}
DAY_NAMES = ["Full Body 1", "Full Body 2", "Full Body 3", "Full Body 4", "Full Body 5"]
OFFSETS = [1, 3, 5, 8, 10, 12, 15, 17, 19, 22, 24, 26, 29, 31, 33, 36, 38, 40,
           43, 45, 47, 50, 52, 54, 57, 59, 61, 64, 66, 68, 71, 73, 75, 78, 80, 82]


def main():
    print(f"Signing in as {EMAIL} ...")
    token, uid = sign_in()
    print(f"  user id: {uid}")

    print("Clearing any prior demo seed rows ...")
    delete("personal_records", token, {"user_id": f"eq.{uid}", "record_type": "like.demo_*"})
    delete("workout_sessions", token, {"user_id": f"eq.{uid}", "notes": "eq.Demo seed"})
    delete("programs", token, {"user_id": f"eq.{uid}", "source_label": "eq.Demo seed"})
    delete("devices", token, {"user_id": f"eq.{uid}", "serial_number": "eq.8E40-B7C2"})

    print("Profile + device ...")
    insert("profiles", token, [{
        "id": uid, "email": EMAIL, "display_name": "Test Lifter",
        "units": "imperial", "timezone": "America/Los_Angeles",
        "onboarded_at": iso(days_ago(90)),
    }], upsert=True)
    insert("devices", token, [{
        "user_id": uid, "name": "TrainAR", "model": "M2", "serial_number": "8E40-B7C2",
        "firmware_version": "1.4.2", "battery_percent": 78,
        "connection_status": "connected", "last_seen_at": iso(NOW - timedelta(minutes=8)),
    }])

    print("Programs ...")
    p_power = insert("programs", token, [{
        "user_id": uid, "title": "Powerbuilding 5x", "author": "J. Nippard",
        "kind": "Powerbuilding", "source_type": "spreadsheet", "source_label": "Demo seed",
        "color": "#C5F23E",
        "description": "10-week powerbuilding cycle blending heavy strength singles with hypertrophy accessories.",
        "weeks": 10, "days_per_week": 5, "active_week": 6, "progress": 0.58,
        "parse_confidence": 0.94, "canonical": {"demo": True}, "created_at": iso(days_ago(82)),
    }], returning=True)[0]["id"]
    insert("programs", token, [{
        "user_id": uid, "title": "nSuns 5/3/1 LP", "author": "nSuns",
        "kind": "Strength", "source_type": "text", "source_label": "Demo seed",
        "color": "#7DD3FC",
        "description": "High-frequency linear progression based on 5/3/1 percentages.",
        "weeks": 0, "days_per_week": 5, "active_week": 0, "progress": 0,
        "parse_confidence": 0.89, "canonical": {"demo": True}, "created_at": iso(days_ago(68)),
    }])
    insert("programs", token, [{
        "user_id": uid, "title": "PPL - Arnold Split", "author": "Custom",
        "kind": "Hypertrophy", "source_type": "photo", "source_label": "Demo seed",
        "color": "#FFC462",
        "description": "Push-pull-legs hypertrophy emphasis. 6 days per week, 8-week block.",
        "weeks": 8, "days_per_week": 6, "active_week": 2, "progress": 0.18,
        "parse_confidence": 0.86, "canonical": {"demo": True}, "created_at": iso(days_ago(35)),
    }])

    print("Program days / blocks / exercises ...")
    for i in range(1, 6):
        day_id = insert("program_days", token, [{
            "program_id": p_power, "week_number": 1, "day_number": i,
            "title": DAY_NAMES[i - 1], "notes": "Demo program day",
        }], returning=True)[0]["id"]
        block_id = insert("program_blocks", token, [{
            "day_id": day_id, "block_number": 1, "title": "Main lifts",
            "execution_style": "sequential",
        }], returning=True)[0]["id"]
        insert("program_exercises", token, [{
            "block_id": block_id, "exercise_number": n, "exercise_name": name,
            "set_count": sets, "rep_target": reps, "load_target": load,
            "rest_seconds": rest, "notes": note,
        } for (n, name, sets, reps, load, rest, note) in DAY_EXERCISES[i]])

    print(f"Workout history ({len(OFFSETS)} sessions) ...")
    for i in OFFSETS:
        wd = days_ago(i)
        insert("workout_sessions", token, [{
            "user_id": uid, "program_id": p_power, "title": DAY_NAMES[i % 5],
            "status": "completed", "started_at": iso(wd),
            "finished_at": iso(wd + timedelta(minutes=74)),
            "duration_seconds": 4440 + (i % 7) * 120,
            "total_volume": 12000 + (i % 9) * 1240, "total_sets": 14 + (i % 6),
            "avg_rpe": round(7.2 + (i % 8) * 0.2, 2),
            "auto_tracked_ratio": round(0.82 + (i % 10) * 0.012, 3),
            "notes": "Demo seed", "created_at": iso(wd),
        }])

    print("Detailed most-recent session (with sets + PRs) ...")
    wd = days_ago(1)
    s_id = insert("workout_sessions", token, [{
        "user_id": uid, "program_id": p_power, "title": "Full Body 1",
        "status": "completed", "started_at": iso(wd),
        "finished_at": iso(wd + timedelta(minutes=78)), "duration_seconds": 4680,
        "total_volume": 21640, "total_sets": 18, "avg_rpe": 8.4,
        "auto_tracked_ratio": 0.94, "notes": "Demo seed", "created_at": iso(wd),
    }], returning=True)[0]["id"]

    def log_with_sets(num, name, sets):
        log_id = insert("workout_exercise_logs", token, [{
            "session_id": s_id, "exercise_number": num, "exercise_name": name,
        }], returning=True)[0]["id"]
        insert("workout_sets", token, [{
            "exercise_log_id": log_id, "set_number": sn, "reps": reps,
            "load_value": load, "load_unit": "lb", "rpe": rpe, "status": status,
            "completed_at": iso(wd + timedelta(minutes=mins)),
        } for (sn, reps, load, rpe, status, mins) in sets])

    log_with_sets(1, "Back Squat (Top Single)", [(1, 1, 365, 8, "auto", 10)])
    log_with_sets(2, "Back Squat", [
        (1, 3, 320, 6, "auto", 18), (2, 3, 320, 6, "auto", 23),
        (3, 3, 320, 7, "auto", 28), (4, 3, 320, 7, "auto", 33),
        (5, 3, 320, 7, "manual", 38),
    ])
    log_with_sets(3, "Barbell Overhead Press", [
        (1, 8, 115, 6, "auto", 45), (2, 8, 115, 6, "auto", 49), (3, 8, 115, 7, "auto", 53),
    ])
    log_with_sets(4, "Chest-Supported Row", [
        (1, 9, 90, 9, "auto", 60), (2, 9, 90, 9, "auto", 64),
        (3, 8, 90, 9, "auto", 68), (4, 8, 90, 9, "auto", 72),
    ])

    insert("personal_records", token, [
        {"user_id": uid, "session_id": s_id, "exercise_name": "Back Squat top single",
         "record_type": "demo_weight_pr", "value": 365, "unit": "lb",
         "achieved_at": iso(wd + timedelta(minutes=10))},
        {"user_id": uid, "session_id": s_id, "exercise_name": "Total workout volume",
         "record_type": "demo_volume_pr", "value": 21640, "unit": "lb",
         "achieved_at": iso(wd + timedelta(minutes=78))},
    ])

    print("\nDone. Seeded 3 programs, "
          f"{len(OFFSETS) + 1} workout sessions, sets, and 2 PRs for {EMAIL}.")


if __name__ == "__main__":
    main()
