#!/usr/bin/env python3
"""Seed the test account with a Push/Pull/Legs program + 10 weeks of history.

WIPES all existing programs/sessions/sets/PRs for the account, then inserts:
- one "Push Pull Legs" program (Push / Pull / Legs days)
- 10 weeks of Mon=Push, Wed=Pull, Fri=Legs sessions, 2x10 per exercise,
  +5 lb per week up to the program weight (light isolation lifts floored at
  5 lb), random RPE 6-10 per set
- a shoulder-soreness note on the most recent Push day
- a PR test day (Saturday ~3 weeks ago): Squat 285, Bench 235, Lat Pulldown 220
  (1 rep each) + matching personal_records

Runs as the authenticated test user via the Supabase REST API (RLS allows a
user full CRUD on their own rows) — no service-role key needed.

Usage: python3 supabase/seed_test_account.py [email] [password]
"""
import json
import random
import sys
import urllib.error
import urllib.parse
import urllib.request
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
random.seed(7)  # stable RPEs across re-runs

WEEKS = 10
WEIGHT_FLOOR = 5
REPS = 10
SETS_PER_EXERCISE = 2
SESSION_HOUR = 17

# day title -> weekday (Mon=0): Push=Mon, Pull=Wed, Legs=Fri
DAY_WEEKDAY = {"Push": 0, "Pull": 2, "Legs": 4}

# day -> [(exercise, rep_target, load_lb)]
PROGRAM = {
    "Push": [
        ("Bench Press", "8-12", 225),
        ("Overhead Machine Press", "8-12", 155),
        ("Dumbbell Side Lateral Raise", "8-15", 20),
    ],
    "Pull": [
        ("Lat Pulldown", "8-12", 200),
        ("Barbell Bent-Over Row", "8-12", 185),
        ("Bicep Curl", "8-12", 30),
    ],
    "Legs": [
        ("Squat", "8-12", 225),
        ("Seated Hamstring Curl", "8-12", 140),
        ("Leg Extension", "8-12", 150),
    ],
}
DAY_ORDER = ["Push", "Pull", "Legs"]
SHOULDER_NOTE = "Right shoulder felt sore on the second set of bench press."

# PR test day: exercise -> (weight, record_type)
PR_LIFTS = [
    ("Squat", 285, "one_rep_max"),
    ("Bench Press", 235, "one_rep_max"),
    ("Lat Pulldown", 220, "one_rep_max"),
]


def iso(dt):
    return dt.isoformat()


def request(method, path, token, body=None, params=None, prefer=None):
    url = f"{SUPABASE_URL}{path}"
    if params:
        url += "?" + "&".join(f"{k}={urllib.parse.quote(v, safe='.*')}" for k, v in params.items())
    headers = {"apikey": ANON_KEY, "Authorization": f"Bearer {token}", "Content-Type": "application/json"}
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
    req = urllib.request.Request(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}).encode(),
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


def weight_for(base, weeks_ago):
    return max(WEIGHT_FLOOR, base - 5 * weeks_ago)


def recent_monday(today):
    wd = today.weekday()  # Mon=0
    monday = today - timedelta(days=wd)
    if wd < 4:  # this week's Friday hasn't happened yet — use last completed week
        monday -= timedelta(weeks=1)
    return monday


def log_exercise(token, session_id, number, exercise_name, weight, sets=SETS_PER_EXERCISE,
                 reps=REPS, when=None):
    log_id = insert("workout_exercise_logs", token, [{
        "session_id": session_id, "exercise_number": number, "exercise_name": exercise_name,
    }], returning=True)[0]["id"]
    rows = []
    rpes = []
    for s in range(1, sets + 1):
        rpe = random.randint(6, 10)
        rpes.append(rpe)
        rows.append({
            "exercise_log_id": log_id, "set_number": s, "reps": reps,
            "load_value": weight, "load_unit": "lb", "rpe": rpe, "status": "manual",
            "completed_at": iso((when or NOW) + timedelta(minutes=5 * s)),
        })
    insert("workout_sets", token, rows)
    return sets, sum(reps * weight for _ in range(sets)), rpes


def main():
    print(f"Signing in as {EMAIL} ...")
    token, uid = sign_in()
    print(f"  user id: {uid}")

    print("Wiping existing programs / sessions / sets / PRs ...")
    delete("personal_records", token, {"user_id": f"eq.{uid}"})
    delete("workout_sessions", token, {"user_id": f"eq.{uid}"})   # cascades logs + sets
    delete("programs", token, {"user_id": f"eq.{uid}"})           # cascades days/blocks/exercises

    insert("profiles", token, [{
        "id": uid, "email": EMAIL, "display_name": "Test Lifter",
        "units": "imperial", "timezone": "America/Los_Angeles",
        "onboarded_at": iso(NOW - timedelta(days=90)),
    }], upsert=True)

    print("Creating Push Pull Legs program ...")
    program_id = insert("programs", token, [{
        "user_id": uid, "title": "Push Pull Legs", "author": "Custom",
        "kind": "Hypertrophy", "source_type": "manual", "source_label": "PPL seed",
        "color": "#C5F23E", "description": "Push / Pull / Legs split, 3 days per week.",
        "weeks": 0, "days_per_week": 3, "active_week": 1, "progress": 0.5,
        "parse_confidence": 1.0, "canonical": {"seed": "ppl"}, "created_at": iso(NOW - timedelta(weeks=WEEKS)),
    }], returning=True)[0]["id"]

    for day_index, day_title in enumerate(DAY_ORDER, start=1):
        day_id = insert("program_days", token, [{
            "program_id": program_id, "week_number": 1, "day_number": day_index,
            "title": day_title, "notes": None,
        }], returning=True)[0]["id"]
        block_id = insert("program_blocks", token, [{
            "day_id": day_id, "block_number": 1, "title": "Main", "execution_style": "sequential",
        }], returning=True)[0]["id"]
        insert("program_exercises", token, [{
            "block_id": block_id, "exercise_number": n, "exercise_name": name,
            "set_count": SETS_PER_EXERCISE, "rep_target": rep_target,
            "load_target": f"{load} lb", "rest_seconds": 120, "notes": None,
        } for n, (name, rep_target, load) in enumerate(PROGRAM[day_title], start=1)])

    anchor_monday = recent_monday(NOW.date())
    print(f"Seeding {WEEKS} weeks of history (most recent week of Mon={anchor_monday}) ...")
    for weeks_ago in range(WEEKS):
        monday = anchor_monday - timedelta(weeks=weeks_ago)
        for day_title in DAY_ORDER:
            d = monday + timedelta(days=DAY_WEEKDAY[day_title])
            started = datetime(d.year, d.month, d.day, SESSION_HOUR, tzinfo=timezone.utc)
            note = SHOULDER_NOTE if (weeks_ago == 0 and day_title == "Push") else None
            session_id = insert("workout_sessions", token, [{
                "user_id": uid, "program_id": program_id, "title": day_title, "status": "completed",
                "started_at": iso(started), "finished_at": iso(started + timedelta(minutes=45)),
                "duration_seconds": 2700, "notes": note, "created_at": iso(started),
            }], returning=True)[0]["id"]

            total_sets, total_volume, all_rpes = 0, 0, []
            for n, (name, _rep_target, base) in enumerate(PROGRAM[day_title], start=1):
                s, vol, rpes = log_exercise(token, session_id, n, name, weight_for(base, weeks_ago), when=started)
                total_sets += s
                total_volume += vol
                all_rpes += rpes
            avg_rpe = round(sum(all_rpes) / len(all_rpes), 1) if all_rpes else None
            request("PATCH", "/rest/v1/workout_sessions", token,
                    body={"total_sets": total_sets, "total_volume": total_volume, "avg_rpe": avg_rpe},
                    params={"id": f"eq.{session_id}"}, prefer="return=minimal")

    print("Seeding PR test day (Saturday ~3 weeks ago) ...")
    pr_sat = anchor_monday - timedelta(weeks=3) + timedelta(days=5)
    pr_started = datetime(pr_sat.year, pr_sat.month, pr_sat.day, SESSION_HOUR, tzinfo=timezone.utc)
    pr_session = insert("workout_sessions", token, [{
        "user_id": uid, "program_id": program_id, "title": "PR Test", "status": "completed",
        "started_at": iso(pr_started), "finished_at": iso(pr_started + timedelta(minutes=40)),
        "duration_seconds": 2400, "notes": "PR test day.", "created_at": iso(pr_started),
    }], returning=True)[0]["id"]
    for n, (name, weight, _rt) in enumerate(PR_LIFTS, start=1):
        log_exercise(token, pr_session, n, name, weight, sets=1, reps=1, when=pr_started)
    insert("personal_records", token, [{
        "user_id": uid, "session_id": pr_session, "exercise_name": name,
        "record_type": rt, "value": weight, "unit": "lb",
        "achieved_at": iso(pr_started + timedelta(minutes=10 * i)),
    } for i, (name, weight, rt) in enumerate(PR_LIFTS, start=1)])

    print(f"\nDone. Push Pull Legs program + {WEEKS} weeks (Mon/Wed/Fri) + PR day seeded for {EMAIL}.")


if __name__ == "__main__":
    main()
