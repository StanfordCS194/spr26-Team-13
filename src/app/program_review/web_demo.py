"""Local Flask demo for Docling parsing and LLM-backed workout normalization."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from flask import Flask, render_template, request

from src.contracts import TrainingProgram
from src.ingestion import UnsupportedProgramSourceError, extract_program_file, normalize_extracted_program


def create_app() -> Flask:
    """Create the local demo app."""

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).with_name("templates")),
    )

    @app.get("/")
    def index():
        return _render_demo()

    @app.post("/process")
    def process_program():
        upload = request.files.get("program_file")
        user_id = request.form.get("user_id", "demo-user").strip() or "demo-user"

        try:
            if not upload or not upload.filename:
                raise ValueError("Upload an image or document to process.")

            program, extracted_preview = _ingest_uploaded_file(upload, user_id)
            return _render_demo(
                program=program,
                extracted_preview=extracted_preview,
            )
        except (UnsupportedProgramSourceError, ValueError) as exc:
            return _render_demo(error=str(exc))

    return app


def _render_demo(
    *,
    error: str | None = None,
    program: TrainingProgram | None = None,
    extracted_preview: dict | None = None,
):
    return render_template(
        "program_review_demo.html",
        error=error,
        program=program,
        program_json=program.model_dump_json(indent=2) if program else None,
        extracted_preview=extracted_preview,
    )


def _ingest_uploaded_file(upload, user_id: str) -> tuple[TrainingProgram, dict[str, str | None]]:
    suffix = Path(upload.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir="/tmp") as handle:
        upload.save(handle)
        temp_path = Path(handle.name)

    try:
        extracted = extract_program_file(temp_path)
        program, normalization_mode = normalize_extracted_program(
            extracted,
            user_id=user_id,
            title=temp_path.stem.replace("_", " ").replace("-", " ").title(),
        )
        return program, {
            "markdown": extracted.structured_markdown or extracted.text,
            "json": None if extracted.structured_data is None else json.dumps(extracted.structured_data, indent=2),
            "normalization_mode": normalization_mode,
        }
    finally:
        temp_path.unlink(missing_ok=True)
