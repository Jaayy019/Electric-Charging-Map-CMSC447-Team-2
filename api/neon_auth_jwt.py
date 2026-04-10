"""Verify JWTs issued by Neon Auth (Better Auth) using the branch JWKS endpoint."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

import jwt
from jwt import PyJWKClient, PyJWTError

from dotenv import load_dotenv

load_dotenv()


def neon_auth_origin() -> str:
    """Issuer and audience for Neon Auth JWTs: scheme + host only (no path)."""
    base = (os.getenv("NEON_AUTH_BASE_URL") or "").strip().rstrip("/")
    if not base:
        raise RuntimeError("NEON_AUTH_BASE_URL is not set")
    parsed = urlparse(base)
    return f"{parsed.scheme}://{parsed.netloc}"


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    base = (os.getenv("NEON_AUTH_BASE_URL") or "").strip().rstrip("/")
    if not base:
        raise RuntimeError("NEON_AUTH_BASE_URL is not set")
    url = f"{base}/.well-known/jwks.json"
    return PyJWKClient(url, cache_keys=True)


def decode_neon_jwt(token: str) -> dict[str, Any]:
    """
    Validate a Bearer JWT from Neon Auth (EdDSA / Ed25519).
    See https://neon.com/docs/auth/guides/plugins/jwt for more info
    """
    origin = neon_auth_origin()
    jwks = _jwks_client()
    key = jwks.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        key.key,
        algorithms=["EdDSA"],
        issuer=origin,
        audience=origin,
    )


def try_decode_neon_jwt(token: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return decode_neon_jwt(token), None
    except PyJWTError as e:
        return None, str(e)
    except RuntimeError as e:
        return None, str(e)
