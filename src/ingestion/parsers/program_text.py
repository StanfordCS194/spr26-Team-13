"""Parse extracted workout text into a loose structured program."""

from __future__ import annotations

import re

from src.ingestion.models import ParsedDay, ParsedExercise, ParsedProgram, ParsedWeek


TITLE_PATTERN = re.compile(r"^(?:program|title)\s*:\s*(?P<title>.+)$", re.IGNORECASE)
WEEK_PATTERN = re.compile(r"^week\s+(?P<number>\d+)(?:\s*[:\-]\s*(?P<title>.+))?$", re.IGNORECASE)
DAY_PATTERN = re.compile(
    r"^(?:(?:day\s*(?P<day_number>\d+))|(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))"
    r"(?:\s*[:\-]\s*(?P<title>.+))?$",
    re.IGNORECASE,
)
SETS_REPS_PATTERN = re.compile(
    r"(?P<sets>\d+)\s*[xX]\s*(?P<reps>[^@,;]+?)\s*(?=(?:@|rpe\b|rest\b|notes?\b|$))",
    re.IGNORECASE,
)
SETS_OF_PATTERN = re.compile(
    r"(?P<sets>\d+)\s+sets?\s+of\s+(?P<reps>[^@,;]+?)\s*(?=(?:@|rpe\b|rest\b|notes?\b|$))",
    re.IGNORECASE,
)
LOAD_PATTERN = re.compile(
    r"(?:@|load\s*[:=]?\s*)(?P<load>[^,;]+?)\s*(?=(?:rpe\b|rest\b|notes?\b|$))",
    re.IGNORECASE,
)
RPE_PATTERN = re.compile(r"rpe\s*[:=]?\s*(?P<rpe>\d+(?:\.\d+)?)", re.IGNORECASE)
REST_PATTERN = re.compile(
    r"rest\s*[:=]?\s*(?P<value>\d+)\s*(?P<unit>s|sec|secs|second|seconds|min|mins|minute|minutes)?",
    re.IGNORECASE,
)
NOTES_PATTERN = re.compile(r"notes?\s*[:=]?\s*(?P<notes>.+)$", re.IGNORECASE)
SETS_SLASH_PATTERN = re.compile(
    r"(?P<sets>\d+)\s*sets?\s*/\s*(?P<reps>\d+\s*(?:reps?)?)",
    re.IGNORECASE,
)
INLINE_PRESCRIPTION_PATTERN = re.compile(
    r"\b\d+\s*(?:x|sets?\s*/|sets?\s+of)\s*\d+",
    re.IGNORECASE,
)


def parse_program_text(
    text: str,
    *,
    fallback_title: str | None = None,
    prefer_multiline_grouping: bool = False,
) -> ParsedProgram:
    """Parse program text into a structured intermediate representation."""

    parsed_program = ParsedProgram(title=fallback_title)
    current_week: ParsedWeek | None = None
    current_day: ParsedDay | None = None
    exercise_lines = 0
    parsed_exercises = 0
    ambiguity_count = 0

    pending_name_lines: list[str] = []

    for raw_line in text.splitlines():
        line = _clean_line(raw_line)
        if not line:
            continue
        if _looks_like_noise_line(line):
            continue

        title_match = TITLE_PATTERN.match(line)
        if title_match:
            _flush_pending_name_lines(current_day, pending_name_lines)
            parsed_program.title = title_match.group("title").strip()
            continue

        week_match = WEEK_PATTERN.match(line)
        if week_match:
            _flush_pending_name_lines(current_day, pending_name_lines)
            week_number = int(week_match.group("number"))
            current_week = ParsedWeek(week_number=week_number)
            parsed_program.weeks.append(current_week)
            current_day = None
            pending_name_lines = []
            continue

        day_match = DAY_PATTERN.match(line)
        if day_match:
            _flush_pending_name_lines(current_day, pending_name_lines)
            current_week = current_week or _append_default_week(parsed_program)
            title = day_match.group("title")
            if title:
                day_title = title.strip()
            elif day_match.group("day_number"):
                day_title = f"Day {day_match.group('day_number')}"
            else:
                day_title = line.strip()
            current_day = ParsedDay(title=day_title)
            current_week.days.append(current_day)
            pending_name_lines = []
            continue

        exercise_lines += 1
        current_week = current_week or _append_default_week(parsed_program)
        current_day = current_day or _append_default_day(current_week)

        if prefer_multiline_grouping and _looks_like_name_fragment(line) and not INLINE_PRESCRIPTION_PATTERN.search(line):
            pending_name_lines.append(line)
            pending_name_lines = pending_name_lines[-3:]
            continue

        if _is_prescription_only_line(line) and pending_name_lines:
            line = f"{' '.join(pending_name_lines)} - {line}"
            pending_name_lines = []

        exercise = _parse_exercise_line(line)
        if exercise is None:
            if _looks_like_name_fragment(line):
                pending_name_lines.append(line)
                pending_name_lines = pending_name_lines[-3:]
                continue
            current_day.notes = _append_note(current_day.notes, line)
            ambiguity_count += 1
            continue

        pending_name_lines = []
        parsed_exercises += 1
        ambiguity_count += len(exercise.ambiguity_flags)
        current_day.exercises.append(exercise)

    _flush_pending_name_lines(current_day, pending_name_lines)

    if parsed_exercises == 0:
        raise ValueError("No exercises could be parsed from the provided input.")

    parsed_program.parse_confidence = _estimate_confidence(
        total_exercise_lines=exercise_lines or parsed_exercises,
        parsed_exercises=parsed_exercises,
        ambiguity_count=ambiguity_count,
    )
    parsed_program.title = parsed_program.title or fallback_title or "Imported Program"
    return parsed_program


def _append_default_week(parsed_program: ParsedProgram) -> ParsedWeek:
    week = ParsedWeek(week_number=len(parsed_program.weeks) + 1)
    parsed_program.weeks.append(week)
    return week


def _append_default_day(week: ParsedWeek) -> ParsedDay:
    day = ParsedDay(title=f"Imported Day {len(week.days) + 1}")
    week.days.append(day)
    return day


def _clean_line(line: str) -> str:
    cleaned = line.strip()
    cleaned = re.sub(r"^[\-\*\u2022]+\s*", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _parse_exercise_line(line: str) -> ParsedExercise | None:
    sets_reps_match = SETS_REPS_PATTERN.search(line) or SETS_OF_PATTERN.search(line) or SETS_SLASH_PATTERN.search(line)
    if not sets_reps_match:
        if not re.search(r"[A-Za-z]", line):
            return None
        if not _looks_like_name_fragment(line):
            return None
        return ParsedExercise(
            raw_name=line,
            set_count=1,
            ambiguity_flags=["missing_prescription"],
        )

    exercise_name = line[: sets_reps_match.start()].strip(" :-|")
    if not exercise_name:
        return None

    rep_target = sets_reps_match.group("reps").strip(" -")
    exercise = ParsedExercise(
        raw_name=exercise_name,
        set_count=int(sets_reps_match.group("sets")),
        rep_target=rep_target or None,
    )

    load_match = LOAD_PATTERN.search(line)
    if load_match:
        exercise.load_target = load_match.group("load").strip(" ,;")

    rpe_match = RPE_PATTERN.search(line)
    if rpe_match:
        exercise.rpe_target = float(rpe_match.group("rpe"))

    rest_match = REST_PATTERN.search(line)
    if rest_match:
        rest_value = int(rest_match.group("value"))
        rest_unit = (rest_match.group("unit") or "s").lower()
        exercise.rest_seconds = rest_value * 60 if rest_unit.startswith("min") else rest_value

    notes_match = NOTES_PATTERN.search(line)
    if notes_match:
        exercise.notes = notes_match.group("notes").strip()

    if exercise.rep_target is None:
        exercise.ambiguity_flags.append("missing_rep_target")

    if exercise.load_target is None and exercise.rpe_target is None:
        exercise.ambiguity_flags.append("missing_intensity_target")

    return exercise


def _looks_like_noise_line(line: str) -> bool:
    if _is_prescription_only_line(line):
        return False
    stripped = line.strip()
    if len(stripped) <= 2:
        return True
    alpha_count = sum(char.isalpha() for char in stripped)
    digit_count = sum(char.isdigit() for char in stripped)
    useful_count = alpha_count + digit_count
    symbol_count = sum(not char.isalnum() and not char.isspace() for char in stripped)
    if useful_count < 4:
        return True
    if digit_count >= 2 and alpha_count < 10 and any(symbol in stripped for symbol in {":", ")", "(", "="}):
        return True
    return (alpha_count < 3 and digit_count < 2) or symbol_count > useful_count


def _looks_like_name_fragment(line: str) -> bool:
    if _is_prescription_only_line(line):
        return False
    alpha_count = sum(char.isalpha() for char in line)
    return alpha_count >= 5


def _is_prescription_only_line(line: str) -> bool:
    return bool(
        SETS_REPS_PATTERN.fullmatch(line)
        or SETS_OF_PATTERN.fullmatch(line)
        or SETS_SLASH_PATTERN.fullmatch(line)
        or re.fullmatch(r"\d+\s*(?:reps?|sec|seconds|mins?|minutes)", line, re.IGNORECASE)
    )


def _flush_pending_name_lines(current_day: ParsedDay | None, pending_name_lines: list[str]) -> None:
    if current_day is None or not pending_name_lines:
        pending_name_lines.clear()
        return

    combined_name = " ".join(pending_name_lines).strip()
    if combined_name:
        current_day.exercises.append(
            ParsedExercise(
                raw_name=combined_name,
                set_count=1,
                ambiguity_flags=["missing_prescription"],
            )
        )
    pending_name_lines.clear()


def _append_note(existing: str | None, addition: str) -> str:
    return addition if not existing else f"{existing}; {addition}"


def _estimate_confidence(*, total_exercise_lines: int, parsed_exercises: int, ambiguity_count: int) -> float:
    base_score = parsed_exercises / max(total_exercise_lines, 1)
    ambiguity_penalty = min(0.6, ambiguity_count * 0.08)
    score = max(0.1, min(0.99, base_score - ambiguity_penalty))
    return round(score, 2)
