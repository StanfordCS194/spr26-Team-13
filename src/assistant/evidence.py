"""Small curated exercise-science evidence library for coach grounding."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class EvidenceSource:
    key: str
    title: str
    authors: str
    journal: str
    year: int
    url: str
    topics: tuple[str, ...]
    summary: str
    coach_note: str

    @property
    def citation(self) -> str:
        return f"{self.authors} ({self.year})"


EVIDENCE_LIBRARY: tuple[EvidenceSource, ...] = (
    EvidenceSource(
        key="schoenfeld_2017_volume",
        title="Dose-response relationship between weekly resistance training volume and increases in muscle mass",
        authors="Schoenfeld, Ogborn, and Krieger",
        journal="Journal of Sports Sciences",
        year=2017,
        url="https://pubmed.ncbi.nlm.nih.gov/27433992/",
        topics=("hypertrophy", "volume", "sets", "muscle", "weekly", "growth"),
        summary=(
            "A systematic review and meta-analysis found a dose-response pattern "
            "between weekly resistance-training volume and muscle-mass gains."
        ),
        coach_note=(
            "Use weekly hard-set volume as a main hypertrophy lever; start modestly "
            "and add volume only when recovery and performance support it."
        ),
    ),
    EvidenceSource(
        key="schoenfeld_2016_frequency",
        title="Effects of Resistance Training Frequency on Measures of Muscle Hypertrophy",
        authors="Schoenfeld, Ogborn, and Krieger",
        journal="Sports Medicine",
        year=2016,
        url="https://pubmed.ncbi.nlm.nih.gov/27102172/",
        topics=("frequency", "hypertrophy", "weekly", "split", "days", "muscle"),
        summary=(
            "This systematic review and meta-analysis examined training frequency "
            "as a hypertrophy variable."
        ),
        coach_note=(
            "Frequency is useful for distributing weekly volume into recoverable "
            "sessions; it should match schedule and recovery."
        ),
    ),
    EvidenceSource(
        key="acsm_2009_progression",
        title="Progression Models in Resistance Training for Healthy Adults",
        authors="American College of Sports Medicine",
        journal="Medicine & Science in Sports & Exercise",
        year=2009,
        url="https://pubmed.ncbi.nlm.nih.gov/19204579/",
        topics=("progression", "strength", "program", "load", "reps", "rest"),
        summary=(
            "This ACSM position stand outlines progression models for load, volume, "
            "rest, and exercise selection in healthy adults."
        ),
        coach_note=(
            "Progress training by changing one or two variables at a time, such as "
            "load, reps, sets, or rest, instead of changing everything at once."
        ),
    ),
    EvidenceSource(
        key="grgic_2021_failure",
        title="Effects of resistance training performed to repetition failure or non-failure",
        authors="Grgic, Schoenfeld, Orazem, and Sabol",
        journal="Journal of Sport and Health Science",
        year=2021,
        url="https://pubmed.ncbi.nlm.nih.gov/33497853/",
        topics=("failure", "rir", "rpe", "intensity", "hypertrophy", "strength"),
        summary=(
            "This systematic review and meta-analysis compared training to failure "
            "with stopping before failure for strength and hypertrophy."
        ),
        coach_note=(
            "Most sets do not need true failure; leave a few reps in reserve for "
            "heavy compounds and use closer-to-failure work selectively."
        ),
    ),
    EvidenceSource(
        key="grgic_2017_rest_hypertrophy",
        title="Short versus long inter-set rest intervals and muscle hypertrophy",
        authors="Grgic, Lazinica, Mikulic, Krieger, and Schoenfeld",
        journal="European Journal of Sport Science",
        year=2017,
        url="https://pubmed.ncbi.nlm.nih.gov/28641044/",
        topics=("rest", "interval", "hypertrophy", "sets", "fatigue"),
        summary=(
            "This systematic review examined short and longer inter-set rest "
            "intervals in resistance training studies measuring hypertrophy."
        ),
        coach_note=(
            "Use enough rest to keep performance high, especially on compound lifts; "
            "short rests can still fit isolation or conditioning blocks."
        ),
    ),
    EvidenceSource(
        key="morton_2018_protein",
        title="Effect of protein supplementation on resistance training-induced gains",
        authors="Morton et al.",
        journal="British Journal of Sports Medicine",
        year=2018,
        url="https://pubmed.ncbi.nlm.nih.gov/28698222/",
        topics=("protein", "nutrition", "muscle", "strength", "diet", "recovery"),
        summary=(
            "This systematic review, meta-analysis, and meta-regression studied "
            "protein supplementation alongside resistance exercise training."
        ),
        coach_note=(
            "Protein supports training adaptations, but workout advice should still "
            "prioritize consistent training, recovery, and total daily intake."
        ),
    ),
    EvidenceSource(
        key="pallares_2021_rom",
        title="Effects of range of motion on resistance training adaptations",
        authors="Pallares et al.",
        journal="Scandinavian Journal of Medicine & Science in Sports",
        year=2021,
        url="https://pubmed.ncbi.nlm.nih.gov/34170576/",
        topics=("range", "rom", "depth", "technique", "mobility", "hypertrophy", "strength"),
        summary=(
            "This systematic review and meta-analysis compared resistance-training "
            "adaptations from different ranges of motion."
        ),
        coach_note=(
            "Default to controlled, full usable range of motion unless the user's "
            "anthropometrics, pain, or sport goal justify a partial range."
        ),
    ),
)


def retrieve_evidence(query: str, *, profile: dict[str, Any] | None = None, limit: int = 3) -> list[EvidenceSource]:
    """Return the most relevant evidence records for a coach query."""

    terms = set(_tokenize(query))
    if isinstance(profile, dict):
        profile_text = " ".join(
            str(value)
            for value in [
                profile.get("trainingGoal"),
                profile.get("trainingExperience"),
                profile.get("coachStyle"),
                profile.get("evidencePreference"),
                profile.get("movementConstraints"),
                " ".join(profile.get("availableEquipment") or []),
            ]
            if value
        )
        terms.update(_tokenize(profile_text))

    scored: list[tuple[int, EvidenceSource]] = []
    for source in EVIDENCE_LIBRARY:
        score = len(terms.intersection(source.topics))
        if any(topic in query.lower() for topic in source.topics):
            score += 1
        if score > 0:
            scored.append((score, source))

    scored.sort(key=lambda item: (-item[0], item[1].year, item[1].key))
    return [source for _, source in scored[:limit]]


def format_evidence_context(sources: list[EvidenceSource]) -> str:
    """Format evidence for an LLM system message without long quotations."""

    lines = []
    for source in sources:
        lines.append(
            "- "
            f"{source.citation()}, {source.journal}: {source.summary} "
            f"Coach use: {source.coach_note} URL: {source.url}"
        )
    return "\n".join(lines)


def response_sources_payload(sources: list[EvidenceSource]) -> list[dict[str, Any]]:
    return [
        {
            "key": source.key,
            "title": source.title,
            "authors": source.authors,
            "journal": source.journal,
            "year": source.year,
            "url": source.url,
        }
        for source in sources
    ]


def _tokenize(value: str) -> list[str]:
    return [part for part in re.split(r"[^a-z0-9]+", value.lower()) if part]
