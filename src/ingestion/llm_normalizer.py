"""LLM-backed normalization from parsed document output into TrainingProgram."""

from __future__ import annotations

import json
import os
import re
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI

from src.contracts import TrainingProgram
from src.ingestion.models import ExtractedDocument
from src.shared.exercise_catalog import EXERCISE_CATALOG


LLMProvider = Literal["gemini", "openai", "groq"]

DEFAULT_PROVIDER: LLMProvider = "gemini"
DEFAULT_MODELS: dict[LLMProvider, str] = {
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-4.1",
    "groq": "openai/gpt-oss-120b",
}
PROVIDER_ENV_KEYS: dict[LLMProvider, str] = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
}
PROVIDER_BASE_URLS: dict[LLMProvider, str | None] = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "openai": None,
    "groq": "https://api.groq.com/openai/v1",
}

load_dotenv()


class LLMNormalizationUnavailableError(RuntimeError):
    """Raised when LLM normalization is requested without a configured API key."""


def llm_normalization_available() -> bool:
    """Return whether the configured provider has a usable API key."""

    provider = get_llm_provider()
    return bool(os.getenv(PROVIDER_ENV_KEYS[provider]))


def normalize_document_with_llm(
    document: ExtractedDocument,
    *,
    user_id: str,
    program_id: str | None = None,
    title: str | None = None,
    client: OpenAI | None = None,
    model: str | None = None,
) -> TrainingProgram:
    """Normalize parsed document output into a TrainingProgram via an LLM."""

    provider = get_llm_provider()
    client = client or _build_client(provider)
    requested_program_id = program_id or _slugify(title or "imported_program")
    requested_title = title or "Imported Program"

    parsed_program = _request_structured_program(
        client=client,
        provider=provider,
        model=model or _get_default_model(provider),
        document=document,
        user_id=user_id,
        program_id=requested_program_id,
        title=requested_title,
    )

    normalized_program = parsed_program.model_copy(
        update={
            "user_id": user_id,
            "program_id": requested_program_id,
            "title": title or parsed_program.title,
            "source_type": document.source_type,
        }
    )
    return TrainingProgram.model_validate(normalized_program.model_dump())


def get_llm_provider() -> LLMProvider:
    raw_provider = os.getenv("LLM_NORMALIZER_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    if raw_provider not in PROVIDER_ENV_KEYS:
        return DEFAULT_PROVIDER
    return raw_provider  # type: ignore[return-value]


def _build_client(provider: LLMProvider) -> OpenAI:
    env_key = PROVIDER_ENV_KEYS[provider]
    api_key = os.getenv(env_key)
    if not api_key:
        raise LLMNormalizationUnavailableError(f"{env_key} is not set.")

    base_url = PROVIDER_BASE_URLS[provider]
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _request_structured_program(
    *,
    client: OpenAI,
    provider: LLMProvider,
    model: str,
    document: ExtractedDocument,
    user_id: str,
    program_id: str,
    title: str,
) -> TrainingProgram:
    if provider in {"gemini", "groq"}:
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": _build_instructions()},
                {
                    "role": "user",
                    "content": _build_input(
                        document=document,
                        user_id=user_id,
                        program_id=program_id,
                        title=title,
                    ),
                },
            ],
            response_format=TrainingProgram,
            temperature=0,
        )
        parsed_program = completion.choices[0].message.parsed
        if parsed_program is None:
            raise ValueError(f"{provider} normalization returned no parsed TrainingProgram.")
        return parsed_program

    response = client.responses.parse(
        model=model,
        instructions=_build_instructions(),
        input=_build_input(
            document=document,
            user_id=user_id,
            program_id=program_id,
            title=title,
        ),
        text_format=TrainingProgram,
        temperature=0,
        max_output_tokens=4000,
    )
    parsed_program = response.output_parsed
    if parsed_program is None:
        raise ValueError("openai normalization returned no parsed TrainingProgram.")
    return parsed_program


def _build_instructions() -> str:
    exercise_catalog = "\n".join(
        f"- {exercise_id}: {details['display_name']}"
        for exercise_id, details in sorted(EXERCISE_CATALOG.items(), key=lambda item: item[1]["display_name"])
    )
    return (
        "Convert the provided parsed workout document into the exact TrainingProgram schema. "
        "Preserve explicit document structure such as week/day boundaries when present. "
        "Preserve grouped sections such as Block 1, Block 2, supersets, and circuits by populating TrainingDay.blocks. "
        "Use block execution_style values of sequential, round_robin, superset, or circuit. "
        "Do not drop exercises from the parsed document. Every exercise line should appear either inside a named block "
        "or in the flat day exercise list. If exercises appear before the first explicit Block heading, preserve their "
        "section title when present, such as Team Prep; otherwise place them in an initial block titled Block 0. "
        "If an exercise title appears immediately before a block header and the reps, intensity, RPE, duration, or notes "
        "that follow clearly belong to that exercise, attach that exercise to the following block rather than leaving it "
        "in Team Prep or Block 0. "
        "If the document has Day sections but no week sections, place all days into week 1. "
        "Do not invent exercises, loads, reps, or RPE values that are not supported by the parsed document. "
        "Keep unresolved ambiguity in ambiguity_flags and set needs_user_confirmation to true when information is incomplete or uncertain. "
        "Use the provided user_id, program_id, title, and source_type exactly as given in the metadata block. "
        "Map exercises to canonical exercise_id values when they clearly match the catalog below. "
        "If no catalog match is clear, generate a snake_case exercise_id from the display name.\n\n"
        "Canonical exercise catalog:\n"
        f"{exercise_catalog}\n\n"
        "Return only a valid TrainingProgram object."
    )


def _build_input(
    *,
    document: ExtractedDocument,
    user_id: str,
    program_id: str,
    title: str,
) -> str:
    metadata = {
        "user_id": user_id,
        "program_id": program_id,
        "title": title,
        "source_type": document.source_type.value,
    }
    return (
        "Metadata:\n"
        f"{json.dumps(metadata, indent=2)}\n\n"
        "Parsed document markdown:\n"
        f"{document.structured_markdown or document.text}"
    )


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "imported_program"


def _get_default_model(provider: LLMProvider) -> str:
    if provider == "gemini":
        return os.getenv("GEMINI_NORMALIZER_MODEL", DEFAULT_MODELS["gemini"])
    if provider == "groq":
        return os.getenv("GROQ_NORMALIZER_MODEL", DEFAULT_MODELS["groq"])
    return os.getenv("OPENAI_NORMALIZER_MODEL", DEFAULT_MODELS["openai"])
