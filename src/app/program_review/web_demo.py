"""Local Flask demo for Docling parsing and LLM-backed workout normalization."""

from __future__ import annotations

import hashlib
import json
import logging
import tempfile
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

from src.assistant.service import AssistantUnavailableError, handle_message
from src.assistant.tools import get_display_state
from src.contracts import TrainingProgram
from src.ingestion import UnsupportedProgramSourceError, extract_program_file, normalize_extracted_program
from src.ingestion.llm_normalizer import (
    get_llm_provider,
    llm_normalization_available,
    normalize_document_with_llm,
)

DESKTOP_LLM_ATTEMPTS = 4
DESKTOP_PARSE_CACHE_DIR = Path(".cache/program_review")
DESKTOP_CACHE_HIT_DELAY_SECONDS = 7.0
IOS_APP_DIR = Path(__file__).resolve().parents[3] / "ios"
LOGGER = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create the local demo app."""

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).with_name("templates")),
    )

    @app.after_request
    def add_api_cors_headers(response):
        if request.path.startswith("/api/"):
            response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.get("/")
    def index():
        return _render_demo()

    @app.get("/ios/")
    def ios_index():
        return send_from_directory(IOS_APP_DIR, "index.html")

    @app.get("/ios/<path:path>")
    def ios_asset(path: str):
        return send_from_directory(IOS_APP_DIR, path)

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

    @app.route("/api/programs/parse", methods=["POST", "OPTIONS"])
    def parse_program_api():
        if request.method == "OPTIONS":
            return ("", 204)

        upload = request.files.get("program_file")
        user_id = request.form.get("user_id", "demo-user").strip() or "demo-user"

        try:
            if not upload or not upload.filename:
                raise ValueError("Upload an image or document to process.")

            program, extracted_preview = _ingest_uploaded_file(upload, user_id, require_llm=False, use_cache=True)
            return jsonify(
                {
                    "program": program.model_dump(mode="json"),
                    "extracted_preview": extracted_preview,
                }
            )
        except (UnsupportedProgramSourceError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        except BrokenPipeError:
            LOGGER.warning("Client disconnected while parsing uploaded program.", exc_info=True)
            return jsonify({"error": "The upload connection was interrupted. Try again."}), 499
        except Exception:
            LOGGER.exception("Unexpected error while parsing uploaded program.")
            return jsonify({"error": "Program parsing failed. Try a clearer file or a text export."}), 500

    @app.post("/api/assistant/chat")
    def assistant_chat_api():
        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()
        user_id = str(payload.get("user_id", "demo-user")).strip() or "demo-user"
        session_id = payload.get("session_id")
        session_id = str(session_id).strip() if session_id else None
        context = payload.get("context") if isinstance(payload.get("context"), dict) else None
        if not message:
            return jsonify({"error": "Message is required."}), 400

        try:
            return jsonify(handle_message(message, user_id=user_id, session_id=session_id, context=context))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except AssistantUnavailableError as exc:
            return jsonify({"error": str(exc)}), 503
        except Exception:
            LOGGER.exception("Unexpected error while handling assistant message.")
            return jsonify({"error": "Coach assistant failed. Try again."}), 500

    @app.get("/api/display-state")
    def display_state_api():
        session_id = request.args.get("session_id")
        if not session_id:
            return jsonify({"error": "session_id is required."}), 400

        display_state = get_display_state(session_id)
        if display_state is None:
            return jsonify({"error": "No display state found for that session."}), 404
        return jsonify({"display_state": display_state})

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


def _ingest_uploaded_file(
    upload,
    user_id: str,
    *,
    require_llm: bool = False,
    use_cache: bool = False,
) -> tuple[TrainingProgram, dict[str, str | None]]:
    suffix = Path(upload.filename).suffix
    title = Path(upload.filename).stem.replace("_", " ").replace("-", " ").title()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir="/tmp") as handle:
        upload.save(handle)
        temp_path = Path(handle.name)

    try:
        cache_key = _build_cache_key(temp_path, user_id=user_id, title=title) if use_cache else None
        if cache_key:
            cached = _read_desktop_parse_cache(cache_key)
            if cached is not None:
                time.sleep(DESKTOP_CACHE_HIT_DELAY_SECONDS)
                return cached

        extracted = extract_program_file(temp_path)
        if require_llm:
            program, normalization_mode = _normalize_extracted_program_for_desktop(
                extracted,
                user_id=user_id,
                title=title,
            )
        else:
            program, normalization_mode = normalize_extracted_program(
                extracted,
                user_id=user_id,
                title=title,
            )
        extracted_preview = {
            "markdown": extracted.structured_markdown or extracted.text,
            "normalization_mode": normalization_mode,
        }
        if cache_key:
            _write_desktop_parse_cache(
                cache_key,
                program=program,
                extracted_preview=extracted_preview,
            )
        return program, extracted_preview
    finally:
        temp_path.unlink(missing_ok=True)


def _normalize_extracted_program_for_desktop(
    extracted,
    *,
    user_id: str,
    title: str,
) -> tuple[TrainingProgram, str]:
    if not llm_normalization_available():
        raise ValueError("Gemini normalization is not configured. Set GEMINI_API_KEY for the desktop demo.")

    provider = get_llm_provider()
    last_error: Exception | None = None

    for attempt in range(DESKTOP_LLM_ATTEMPTS):
        try:
            return (
                normalize_document_with_llm(
                    extracted,
                    user_id=user_id,
                    title=title,
                ),
                provider,
            )
        except Exception as exc:
            last_error = exc
            if attempt < DESKTOP_LLM_ATTEMPTS - 1 and _is_retryable_llm_error(exc):
                time.sleep(1.5 * (attempt + 1))
                continue
            break

    raise ValueError(
        f"{provider} normalization failed. Desktop demo is not using local fallback output: {last_error}"
    )


def _build_cache_key(path: Path, *, user_id: str, title: str) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    identity = json.dumps(
        {
            "file_sha256": digest.hexdigest(),
            "user_id": user_id,
            "title": title,
            "version": 2,
        },
        sort_keys=True,
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _read_desktop_parse_cache(
    cache_key: str,
) -> tuple[TrainingProgram, dict[str, str | None]] | None:
    cache_path = _desktop_parse_cache_path(cache_key)
    if not cache_path.exists():
        return None

    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        program = TrainingProgram.model_validate(payload["program"])
        extracted_preview = payload["extracted_preview"]
        return program, {
            "markdown": extracted_preview.get("markdown"),
            "normalization_mode": extracted_preview.get("normalization_mode", "gemini_cache"),
            "cache_status": "hit",
        }
    except (OSError, KeyError, TypeError, ValueError):
        return None


def _write_desktop_parse_cache(
    cache_key: str,
    *,
    program: TrainingProgram,
    extracted_preview: dict[str, str | None],
) -> None:
    if extracted_preview.get("normalization_mode") != "gemini":
        return

    DESKTOP_PARSE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _desktop_parse_cache_path(cache_key)
    payload = {
        "program": program.model_dump(mode="json"),
        "extracted_preview": {
            **extracted_preview,
            "cache_status": "miss",
        },
    }
    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _desktop_parse_cache_path(cache_key: str) -> Path:
    return DESKTOP_PARSE_CACHE_DIR / f"{cache_key}.json"


def _is_retryable_llm_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code in {408, 409, 500, 502, 503, 504}:
        return True

    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "temporarily unavailable",
            "high demand",
            "connection error",
        )
    )
