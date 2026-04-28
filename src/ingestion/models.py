"""Internal models used by the ingestion pipeline."""

from dataclasses import dataclass, field

from src.contracts import SourceType


@dataclass(slots=True)
class ExtractedDocument:
    text: str
    source_type: SourceType
    extraction_notes: list[str] = field(default_factory=list)
    structured_markdown: str | None = None
    structured_data: dict | None = None


@dataclass(slots=True)
class ParsedExercise:
    raw_name: str
    set_count: int | None = None
    rep_target: str | None = None
    load_target: str | None = None
    rpe_target: float | None = None
    rest_seconds: int | None = None
    notes: str | None = None
    ambiguity_flags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParsedDay:
    title: str
    exercises: list[ParsedExercise] = field(default_factory=list)
    notes: str | None = None


@dataclass(slots=True)
class ParsedWeek:
    week_number: int
    days: list[ParsedDay] = field(default_factory=list)


@dataclass(slots=True)
class ParsedProgram:
    title: str | None = None
    weeks: list[ParsedWeek] = field(default_factory=list)
    parse_confidence: float | None = None
    extraction_notes: list[str] = field(default_factory=list)
