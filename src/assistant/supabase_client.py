"""Per-request Supabase client factory for the voice coach API.

Tools call into Supabase under the authenticated user's JWT so RLS policies
that key off ``auth.uid()`` apply. This module returns a fresh client whose
PostgREST headers carry the caller's access token.
"""

from __future__ import annotations

import os
from typing import Any

try:
    from supabase import Client, create_client
except ModuleNotFoundError:  # pragma: no cover - import guard for environments without the dep
    Client = Any  # type: ignore[assignment]
    create_client = None  # type: ignore[assignment]


class SupabaseConfigError(RuntimeError):
    """Raised when the Supabase URL/anon key are not configured."""


class SupabaseAuthError(RuntimeError):
    """Raised when a request lacks a usable JWT."""


def build_user_client(jwt: str) -> "Client":
    """Return a Supabase client whose requests run as the JWT's user.

    The anon key authorizes the request at the API gateway; the JWT in the
    ``Authorization`` header is what Postgres sees as ``auth.uid()``.
    """

    if create_client is None:
        raise SupabaseConfigError(
            "supabase python package is not installed. Add `supabase` to requirements."
        )

    url = os.getenv("SUPABASE_URL", "").strip()
    anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    if not url or not anon_key:
        raise SupabaseConfigError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set for the voice coach API."
        )

    token = (jwt or "").strip()
    if not token:
        raise SupabaseAuthError(
            "Missing Supabase JWT. Pass it as 'Authorization: Bearer <token>'."
        )

    client = create_client(url, anon_key)
    client.postgrest.auth(token)
    return client


def extract_user_id(jwt: str) -> str:
    """Decode the JWT (no signature check) to read its ``sub`` claim.

    Supabase guarantees the JWT was already verified before our request lands
    here only when we re-issue calls through PostgREST under that token, so
    treat this purely as a hint for code that needs the user id before any
    PostgREST round-trip. RLS is still the source of truth.
    """

    try:
        import jwt as pyjwt  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise SupabaseAuthError("PyJWT is required to extract the user id.") from exc

    if not jwt:
        raise SupabaseAuthError("Empty JWT.")

    try:
        claims = pyjwt.decode(jwt, options={"verify_signature": False})
    except Exception as exc:  # pragma: no cover - defensive
        raise SupabaseAuthError(f"Could not decode JWT: {exc}") from exc

    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        raise SupabaseAuthError("JWT is missing the 'sub' claim.")
    return sub
