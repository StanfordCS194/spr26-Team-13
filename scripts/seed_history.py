#!/usr/bin/env python3
"""
scripts/seed_history.py

Import Phase 1 and Phase 2 workout history into Supabase.

Reads 'programs/Phase 1.xlsx' and 'programs/Phase 2.xlsx', extracts every
workout day that has at least one exercise with an actual logged weight, assigns
approximate historical dates, and writes workout_sessions, workout_exercise_logs,
workout_sets, and personal_records into the live Supabase project.

Usage:
    # Dry run — shows what would be inserted without writing anything
    python3 scripts/seed_history.py --dry-run

    # Live insert (will prompt for Supabase password)
    python3 scripts/seed_history.py --email chapman.petersen25@gmail.com

    # Only seed one phase
    python3 scripts/seed_history.py --phase 1

    # Skip auth prompt by providing a JWT directly
    python3 scripts/seed_history.py --token <jwt> --user-id <uuid>
"""

from __future__ import annotations

import argparse
import datetime
import getpass
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# openpyxl is a project dependency
try:
    import openpyxl
except ImportError:
    sys.exit("Run: pip install openpyxl")

# ── Paths & Supabase config ────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
PROGRAMS_DIR = REPO_ROOT / "programs"

SUPABASE_URL = "https://rcmlbgjqwpfzpiownxfy.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJjbWxiZ2pxd3BmenBpb3dueGZ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgyMjU2NzgsImV4cCI6MjA5MzgwMTY3OH0."
    "fKcwQ0Jws91vA9PcHg8PdyWDhP8WXYg4WFU5ll8ubyo"
)

# Monday start dates for each phase (estimated from Chapman's training history)
PHASE_START: dict[int, datetime.date] = {
    1: datetime.date(2026, 1, 5),   # Phase 1 started ~Jan 5 2026
    2: datetime.date(2026, 3, 23),  # Phase 2 started ~Mar 23 2026 (after Phase 1 deload)
}

# 5 workout days/week on Mon/Tue/Thu/Fri/Sat
# Map day_number (1-5) → days offset from that week's Monday
DAY_OFFSETS = {1: 0, 2: 1, 3: 3, 4: 4, 5: 5}


# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass
class LoggedSet:
    set_number: int
    reps: int
    weight: float  # lbs; 0.0 = bodyweight


@dataclass
class LoggedExercise:
    name: str
    rep_target: str
    rpe: float | None
    sets: list[LoggedSet]


@dataclass
class WorkoutDay:
    phase: int
    week: int
    day_number: int  # 1–5
    title: str
    exercises: list[LoggedExercise]

    @property
    def date(self) -> datetime.date:
        week_start = PHASE_START[self.phase] + datetime.timedelta(weeks=self.week - 1)
        return week_start + datetime.timedelta(days=DAY_OFFSETS.get(self.day_number, self.day_number - 1))

    @property
    def session_title(self) -> str:
        return f"Phase {self.phase} · Week {self.week} · {self.title}"

    @property
    def total_volume(self) -> float:
        return sum(s.reps * s.weight for ex in self.exercises for s in ex.sets if s.weight > 0)

    @property
    def total_sets(self) -> int:
        return sum(len(ex.sets) for ex in self.exercises)


# ── Supabase helpers ───────────────────────────────────────────────────────────

def supabase_signin(email: str, password: str) -> tuple[str, str]:
    """Sign in via email+password. Returns (access_token, user_id)."""
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    body = json.dumps({"email": email, "password": password}).encode()
    req = Request(url, data=body, headers={
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
    }, method="POST")
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except HTTPError as e:
        raise SystemExit(f"Sign-in failed ({e.code}): {e.read().decode()}") from e

    token = data.get("access_token")
    user_id = (data.get("user") or {}).get("id")
    if not token or not user_id:
        raise SystemExit(f"Unexpected auth response: {data}")
    return token, user_id


class Supabase:
    """Minimal REST client mirroring the pattern in supabase_tools.py."""

    def __init__(self, token: str) -> None:
        self._h = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        req = Request(
            f"{SUPABASE_URL}/rest/v1/{table}",
            data=json.dumps(payload).encode(),
            headers={**self._h, "Prefer": "return=representation"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=15) as r:
                rows = json.loads(r.read())
        except HTTPError as e:
            raise RuntimeError(f"INSERT {table} failed: {e.read().decode()}") from e
        if isinstance(rows, list) and rows:
            return rows[0]
        raise RuntimeError(f"INSERT {table} returned no row")

    def select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        qs = urlencode(params)
        req = Request(f"{SUPABASE_URL}/rest/v1/{table}?{qs}", headers=self._h, method="GET")
        try:
            with urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except HTTPError as e:
            raise RuntimeError(f"SELECT {table} failed: {e.read().decode()}") from e


# ── 1RM estimation ─────────────────────────────────────────────────────────────

def estimate_1rm(weight: float, reps: int) -> float:
    """Epley formula. Returns weight when reps=1."""
    if reps <= 1:
        return weight
    return weight * (1 + reps / 30)


# ── Load string parsing ────────────────────────────────────────────────────────

def _parse_reps(val: Any) -> int | None:
    """Parse a cell value into a rep count. Returns None if unparseable."""
    if val is None:
        return None
    if isinstance(val, datetime.datetime):
        return None  # openpyxl sometimes reads small integers as dates
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        v = int(val)
        return v if 1 <= v <= 100 else None
    s = str(val).strip().upper()
    if s in ("", "N/A", "AMRAP", "=", "WORKING SETS", "REPS"):
        return None
    m = re.match(r"(\d+)", s)
    return int(m.group(1)) if m else None


def _parse_rpe(val: Any) -> float | None:
    if val is None:
        return None
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float)) and 0 < val <= 10:
        return float(val)
    s = str(val).strip()
    if s.upper() == "N/A":
        return None
    m = re.match(r"(\d+(?:\.\d+)?)", s)
    return float(m.group(1)) if m else None


def _parse_weight_string(s: str) -> list[tuple[int | None, float]]:
    """
    Parse a load string into a list of (reps, weight_lbs) tuples.
    Returns [] for prescribed-only ranges like "265-285".

    Handles:
      "250"               → [(None, 250)]       — specific weight, reps from context
      "35, 45, 60"        → per-set weights
      "315*2"             → [(2, 315)]
      "175*6,170,170"     → per-set with mixed formats
      "0lbs: 6, 5, 6"    → bodyweight per set
      "machine curl 160"  → text with embedded weight
      "265-285"           → []                  — prescribed range only, skip
    """
    s = s.strip()
    if not s or s.upper() in ("NONE", "N/A", "=", ""):
        return []

    # Pure "low-high" range → prescribed only, no actual weight logged
    if re.match(r"^\d+\s*[-–]\s*\d+\s*(%|$)", s):
        return []

    # Comma-separated (may mix "175*6" and bare numbers)
    if "," in s:
        results: list[tuple[int | None, float]] = []
        for part in re.split(r",\s*", s):
            part = part.strip()
            if not part:
                continue
            # "175*6" or "175x6"
            m = re.match(r"(\d+(?:\.\d+)?)\s*[x*×]\s*(\d+)", part)
            if m:
                w, r = float(m.group(1)), int(m.group(2))
                if 5 <= w <= 1500:
                    results.append((r, w))
                continue
            # bare number or "175 lbs"
            m = re.match(r"(\d+(?:\.\d+)?)", part)
            if m:
                w = float(m.group(1))
                if 5 <= w <= 1500:
                    results.append((None, w))
        return results

    # "315*2" or "315x2" — explicit reps × weight
    m = re.match(r"^(\d+(?:\.\d+)?)\s*[x*×]\s*(\d+)", s)
    if m:
        w, r = float(m.group(1)), int(m.group(2))
        return [(r, w)] if 5 <= w <= 1500 else []

    # "3 sets x 8 reps at 225" or "3x8 225"
    m = re.match(r"^(\d+)\s*[x*×]\s*(\d+)\s+(?:at\s+)?(\d+(?:\.\d+)?)", s)
    if m:
        n_sets, reps, w = int(m.group(1)), int(m.group(2)), float(m.group(3))
        return [(reps, w)] * n_sets if 5 <= w <= 1500 else []

    # "0lbs: 6, 5, 6" — bodyweight with per-set reps
    m = re.match(r"^0\s*lbs?\s*:\s*([\d,\s]+)", s, re.IGNORECASE)
    if m:
        reps_list = [int(r.strip()) for r in m.group(1).split(",") if r.strip().isdigit()]
        return [(r, 0.0) for r in reps_list]

    # Embedded "N lbs" or "N kg" in a note (e.g., "machine curl 160 lbs")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(lbs?|kg)", s, re.IGNORECASE)
    if m:
        w = float(m.group(1))
        return [(None, w)] if 5 <= w <= 1500 else []

    # Bare number that looks like a plausible weight
    m = re.match(r"^(\d+(?:\.\d+)?)\s*$", s)
    if m:
        w = float(m.group(1))
        return [(None, w)] if 20 <= w <= 1000 else []

    return []


def parse_sets(
    load_val: Any,
    actual_note: Any,
    working_sets: int,
    default_reps: int,
) -> list[LoggedSet]:
    """
    Build the set list for an exercise row.
    Tries actual_note (Phase 2 col M) first, falls back to load_val (col G).
    Expands to working_sets count if only one weight parsed.
    """
    candidates = [str(actual_note or "").strip(), str(load_val or "").strip()]

    for src in candidates:
        parsed = _parse_weight_string(src)
        if not parsed:
            continue
        # Expand a single weight entry to cover all working sets
        if len(parsed) == 1 and working_sets > 1:
            parsed = parsed * working_sets
        sets: list[LoggedSet] = []
        for i, (reps, weight) in enumerate(parsed, 1):
            sets.append(LoggedSet(
                set_number=i,
                reps=reps if reps is not None else default_reps,
                weight=weight,
            ))
        return sets

    return []


# ── Excel file parser ──────────────────────────────────────────────────────────

# Patterns that mark a workout-day row in col B
_DAY_PAT = re.compile(
    r"(Full\s*Body|FULL\s*BODY|Arm\s*&?\s*Pump|ARM\s*&?\s*PUMP|PUMP\s*DAY|Pump\s*Day)",
    re.IGNORECASE,
)
# Max-test and pure-deload weeks — skip (no logged working sets)
_SKIP_WEEK_PAT = re.compile(
    r"(MAX\s*TEST|OPTION\s*[AB]|Full\s*Deload|full\s*deload)",
    re.IGNORECASE,
)


def parse_excel(phase: int, path: Path) -> list[WorkoutDay]:
    wb = openpyxl.load_workbook(str(path), data_only=True)
    ws = wb.worksheets[0]

    days: list[WorkoutDay] = []
    current_week = 0
    current_day_num = 0
    current_day_title = ""
    current_exercises: list[LoggedExercise] = []
    skip_week = False

    def _flush() -> None:
        nonlocal current_exercises
        filled = [e for e in current_exercises if e.sets]
        if current_week > 0 and current_day_num > 0 and filled:
            days.append(WorkoutDay(
                phase=phase,
                week=current_week,
                day_number=current_day_num,
                title=current_day_title,
                exercises=filled,
            ))
        current_exercises = []

    for row in ws.iter_rows(min_row=1, values_only=True):
        b = str(row[1] or "").strip()
        c = str(row[2] or "").strip()

        # ── Week header ──
        if "Week" in b and re.search(r"\d", b):
            if _SKIP_WEEK_PAT.search(b):
                _flush()
                current_day_num = 0
                skip_week = True
                continue
            m = re.search(r"(\d+)", b)
            if not m:
                continue
            wk = int(m.group(1))
            if wk < 1 or wk > 12:
                continue
            _flush()
            current_day_num = 0
            current_week = wk
            skip_week = False
            continue

        if skip_week:
            continue

        # ── Day header ──
        if _DAY_PAT.search(b):
            _flush()
            current_day_num += 1
            current_day_title = b.strip()
            continue

        # ── Exercise row ──
        # Col C: exercise name (skip header rows and non-exercise rows)
        if not c or c in ("Exercise", "Warm-up Sets") or "REST" in b.upper():
            continue

        # Col E (index 4): working sets count — must be a positive integer
        e_val = row[4]
        if not isinstance(e_val, (int, float)) or isinstance(e_val, bool) or e_val <= 0:
            continue
        working_sets = int(e_val)

        reps_val = row[5]   # col F
        load_val = row[6]   # col G (prescribed or actual for Phase 1)
        rpe_val  = row[8]   # col I
        # col M (index 12) is only present in Phase 2 — actual performance notes
        actual_note = row[12] if len(row) > 12 else None

        default_reps = _parse_reps(reps_val) or 5
        rpe = _parse_rpe(rpe_val)
        rep_target = str(reps_val).strip() if reps_val else str(default_reps)

        sets = parse_sets(load_val, actual_note, working_sets, default_reps)
        if sets:
            current_exercises.append(LoggedExercise(
                name=c,
                rep_target=rep_target,
                rpe=rpe,
                sets=sets,
            ))

    _flush()
    return days


# ── Supabase insertion ─────────────────────────────────────────────────────────

def seed(
    db: Supabase | None,
    user_id: str,
    days: list[WorkoutDay],
    *,
    dry_run: bool,
) -> dict[str, int]:
    sessions_n = exercises_n = sets_n = prs_n = 0

    # (exercise_name) → (best_1rm, best_weight, best_reps, session_id)
    pr_tracker: dict[str, tuple[float, float, int, str]] = {}

    for day in days:
        dt = day.date
        started = datetime.datetime(dt.year, dt.month, dt.day, 8, 0, tzinfo=datetime.timezone.utc)
        finished = started + datetime.timedelta(hours=1, minutes=30)

        tag = "[DRY] " if dry_run else "      "
        print(f"  {tag}{day.session_title}  ({dt})  "
              f"— {len(day.exercises)} exercises · {day.total_sets} sets · {day.total_volume:.0f} lbs")

        if dry_run:
            for ex in day.exercises:
                print(f"           ↳ {ex.name}: "
                      + ", ".join(f"{s.reps}×{s.weight:.0f}" for s in ex.sets))
            continue

        # Insert session
        session = db.insert("workout_sessions", {
            "user_id": user_id,
            "title": day.session_title,
            "status": "completed",
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "duration_seconds": 90 * 60,
            "total_volume": round(day.total_volume, 2),
            "total_sets": day.total_sets,
        })
        session_id = session["id"]
        sessions_n += 1

        # Insert exercises and sets
        for ex_num, ex in enumerate(day.exercises, 1):
            log = db.insert("workout_exercise_logs", {
                "session_id": session_id,
                "exercise_number": ex_num,
                "exercise_name": ex.name,
            })
            log_id = log["id"]
            exercises_n += 1

            for s in ex.sets:
                db.insert("workout_sets", {
                    "exercise_log_id": log_id,
                    "set_number": s.set_number,
                    "reps": s.reps,
                    "load_value": s.weight if s.weight > 0 else None,
                    "load_unit": "lb",
                    "rpe": ex.rpe,
                    "status": "manual",
                    "completed_at": finished.isoformat(),
                })
                sets_n += 1

                # Track all-time best 1RM per exercise
                if s.weight > 0 and s.reps > 0:
                    orm = estimate_1rm(s.weight, s.reps)
                    current = pr_tracker.get(ex.name)
                    if current is None or orm > current[0]:
                        pr_tracker[ex.name] = (orm, s.weight, s.reps, session_id)

    # Insert personal_records for all-time bests
    if not dry_run and pr_tracker:
        print(f"\n  Inserting {len(pr_tracker)} personal records…")
        for ex_name, (orm, best_w, best_r, session_id) in sorted(pr_tracker.items()):
            db.insert("personal_records", {
                "user_id": user_id,
                "session_id": session_id,
                "exercise_name": ex_name,
                "record_type": "estimated_1rm",
                "value": round(orm, 1),
                "unit": "lb",
                "achieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })
            prs_n += 1
            print(f"    {ex_name}: {best_w:.0f} lbs × {best_r} reps → "
                  f"est. 1RM {orm:.0f} lbs")

    return {"sessions": sessions_n, "exercises": exercises_n, "sets": sets_n, "prs": prs_n}


# ── Guard: check for existing seeded data ──────────────────────────────────────

def check_existing(db: Supabase, user_id: str) -> int:
    """Return count of sessions whose title starts with 'Phase 1 ·' or 'Phase 2 ·'."""
    rows = db.select("workout_sessions", {
        "select": "id",
        "user_id": f"eq.{user_id}",
        "title": "like.Phase%·%",
    })
    return len(rows)


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Seed Phase 1 & 2 workout history into Supabase")
    ap.add_argument("--email", default="chapman.petersen25@gmail.com")
    ap.add_argument("--token", help="Supabase JWT — skips email/password prompt")
    ap.add_argument("--user-id", dest="user_id", help="UUID — required when --token is used")
    ap.add_argument("--phase", choices=["1", "2", "both"], default="both")
    ap.add_argument("--dry-run", action="store_true", help="Preview only, no writes")
    ap.add_argument("--force", action="store_true", help="Insert even if seeded data already exists")
    args = ap.parse_args()

    print("=== TrainAR history seeder ===\n")

    # Auth — skipped for dry-run (no writes needed)
    token: str = ""
    user_id: str = ""
    db: Supabase | None = None

    if not args.dry_run:
        if args.token:
            if not args.user_id:
                sys.exit("--user-id is required with --token")
            token, user_id = args.token, args.user_id
            print(f"Using provided token (user {user_id})\n")
        else:
            pw = getpass.getpass(f"Supabase password for {args.email}: ")
            print("Signing in…", end=" ", flush=True)
            token, user_id = supabase_signin(args.email, pw)
            print(f"OK  (user_id={user_id})\n")
        db = Supabase(token)

    # Warn if data already exists
    if not args.dry_run and db is not None:
        existing = check_existing(db, user_id)
        if existing > 0 and not args.force:
            print(f"WARNING: found {existing} already-seeded session(s) (title starts with 'Phase·').")
            print("Pass --force to insert anyway (creates duplicates) or Ctrl-C to abort.\n")
            try:
                input("Press Enter to continue anyway, Ctrl-C to cancel: ")
            except KeyboardInterrupt:
                print("\nAborted.")
                sys.exit(0)

    # Parse Excel files
    phases = [1, 2] if args.phase == "both" else [int(args.phase)]
    all_days: list[WorkoutDay] = []

    for phase in phases:
        fname = f"Phase {phase}.xlsx"
        path = PROGRAMS_DIR / fname
        if not path.exists():
            print(f"WARNING: {path} not found — skipping Phase {phase}")
            continue
        print(f"Parsing Phase {phase} ({fname})…", end=" ", flush=True)
        days = parse_excel(phase, path)
        print(f"found {len(days)} workout days with logged data")
        all_days.extend(days)

    if not all_days:
        sys.exit("No workout data found in either Excel file.")

    all_days.sort(key=lambda d: d.date)

    total_ex = sum(len(d.exercises) for d in all_days)
    total_sets = sum(d.total_sets for d in all_days)
    print(f"\nTotal to import: {len(all_days)} sessions · {total_ex} exercises · {total_sets} sets")
    print(f"Date range: {all_days[0].date} → {all_days[-1].date}")
    print(f"\n{'[DRY RUN — no writes] ' if args.dry_run else ''}Inserting…\n")

    stats = seed(db, user_id, all_days, dry_run=args.dry_run)  # db is None in dry-run

    if not args.dry_run:
        print(
            f"\n✓  Done: {stats['sessions']} sessions · "
            f"{stats['exercises']} exercises · "
            f"{stats['sets']} sets · "
            f"{stats['prs']} PRs"
        )
    else:
        print("\n[Dry run complete — nothing written]")


if __name__ == "__main__":
    main()
