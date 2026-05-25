"""Thin /api/chat route: one-shot trainer-flavored LLM round-trip.

This is intentionally independent of `src.assistant.service.handle_message`
(which does tool-calling, parses workout actions, and writes to Supabase).
The glasses chat demo needs none of that — just *say something, hear a reply*.

Lives under src/assistant/ so it sits next to the existing assistant code,
but it shares nothing beyond `build_openai_client()`.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from flask import Flask, jsonify, request

from src.assistant.service import DEFAULT_ASSISTANT_MODEL, build_openai_client

LOGGER = logging.getLogger(__name__)

TRAINER_SYSTEM_PROMPT = (
    "You are a friendly, knowledgeable personal trainer. Answer questions "
    "about exercise, form, programming, recovery, and nutrition. Keep replies "
    "short and conversational — usually one or two sentences — because they "
    "will be spoken aloud through the user's glasses, not read on a screen. "
    "Avoid bullet points, markdown, or long lists."
)

CHAT_MODEL_ENV = "OPENAI_CHAT_MODEL"
CHAT_MAX_TOKENS = 200


def register_chat_route(app: Flask) -> None:
    """Register POST /api/chat on the given Flask app."""

    @app.route("/api/chat", methods=["POST", "OPTIONS"])
    def chat_route() -> Any:
        if request.method == "OPTIONS":
            return ("", 204)

        payload = request.get_json(silent=True) or {}
        text = (payload.get("text") or "").strip()
        if not text:
            return jsonify({"error": "missing 'text' in request body"}), 400

        client = build_openai_client()
        if client is None:
            return (
                jsonify(
                    {
                        "error": (
                            "OpenAI client not configured. Set OPENAI_API_KEY in .env "
                            "and install the openai package."
                        )
                    }
                ),
                503,
            )

        model = os.getenv(CHAT_MODEL_ENV, DEFAULT_ASSISTANT_MODEL)

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": TRAINER_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                temperature=0.7,
                max_tokens=CHAT_MAX_TOKENS,
            )
        except Exception:  # noqa: BLE001 — surface any OpenAI failure as a 500
            LOGGER.exception("OpenAI chat completion failed for text=%r", text)
            return jsonify({"error": "chat completion failed"}), 500

        reply = (completion.choices[0].message.content or "").strip()
        if not reply:
            return jsonify({"error": "empty reply from model"}), 502

        return jsonify({"reply": reply})
