"""
Neon Auth (Better Auth) — backend-only integration.

Proxies sign-in / sign-up to the managed Neon Auth service and validates JWTs for
protected routes. No UI; clients call these endpoints and store the session/JWT
as needed.
"""

from __future__ import annotations

import os
from typing import Annotated, Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from starlette.responses import JSONResponse

from neon_auth_jwt import try_decode_neon_jwt

router = APIRouter(prefix="/api/auth", tags=["Auth"])
_bearer = HTTPBearer(auto_error=False)


def _neon_auth_base() -> str:
    return (os.getenv("NEON_AUTH_BASE_URL") or "").strip().rstrip("/")


def _require_configured() -> str:
    base = _neon_auth_base()
    if not base:
        raise HTTPException(
            status_code=503,
            detail="Neon Auth is not configured. Set NEON_AUTH_BASE_URL in the environment.",
        )
    return base


def _origin_for_neon_auth(request: Request) -> str:
    """
    Better Auth requires an Origin header on sign-up unless callbackURL is absolute.
    Browsers send Origin when calling our API from Swagger or the frontend; server-side
    clients can set NEON_AUTH_ORIGIN (e.g. http://localhost:5000).
    """
    origin = (request.headers.get("origin") or "").strip()
    if origin:
        return origin
    return (os.getenv("NEON_AUTH_ORIGIN") or "http://localhost:5000").strip()


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: Optional[str] = None


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


def _json_with_neon_cookies(r: httpx.Response) -> JSONResponse:
    """Forward JSON body and all Set-Cookie headers from Neon (session cookie for /me)."""
    try:
        data = r.json()
    except Exception:
        data = {"message": r.text or r.reason_phrase}
    resp = JSONResponse(content=data, status_code=r.status_code)
    for cookie in r.headers.get_list("set-cookie"):
        resp.headers.append("set-cookie", cookie)
    return resp


@router.post("/sign-up")
async def sign_up(request: Request, body: SignUpRequest) -> JSONResponse:
    """Proxy to Neon Auth `POST /sign-up/email` (Better Auth)."""
    base = _require_configured()
    # Neon Auth requires `name` default to the email local-part if omitted.
    display_name = (body.name or "").strip() or body.email.split("@", 1)[0]
    payload: dict[str, Any] = {
        "email": body.email,
        "password": body.password,
        "name": display_name,
    }
    origin = _origin_for_neon_auth(request)

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{base}/sign-up/email",
            json=payload,
            headers={"Origin": origin},
        )

    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = {"message": r.text or r.reason_phrase}
        raise HTTPException(status_code=r.status_code, detail=detail)

    return _json_with_neon_cookies(r)


@router.post("/sign-in")
async def sign_in(request: Request, body: SignInRequest) -> JSONResponse:
    """Proxy to Neon Auth `POST /sign-in/email` (Better Auth)."""
    base = _require_configured()
    payload = {"email": body.email, "password": body.password}
    origin = _origin_for_neon_auth(request)

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{base}/sign-in/email",
            json=payload,
            headers={"Origin": origin},
        )

    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = {"message": r.text or r.reason_phrase}
        raise HTTPException(status_code=r.status_code, detail=detail)

    return _json_with_neon_cookies(r)


def _looks_like_jwt(value: str) -> bool:
    return len(value.split(".")) == 3


async def get_current_user(
    request: Request,
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)],
) -> dict[str, Any]:
    """
    Current user from either:
    - `Authorization: Bearer <jwt>` (three dot-separated segments, verified with JWKS), or
    - Session cookies set by Neon on sign-in/sign-up (forwarded in our JSON response).

    The opaque `token` string in the JSON body is **not** a JWT; it cannot be used as Bearer.
    """
    base = _neon_auth_base()
    if not base:
        raise HTTPException(
            status_code=503,
            detail="Neon Auth is not configured. Set NEON_AUTH_BASE_URL in the environment.",
        )

    if creds is not None and creds.scheme.lower() == "bearer":
        raw = creds.credentials.strip()
        if _looks_like_jwt(raw):
            payload, err = try_decode_neon_jwt(raw)
            if payload is None:
                raise HTTPException(status_code=401, detail=f"Invalid JWT: {err}")
            return {"user": payload}

        raise HTTPException(
            status_code=401,
            detail=(
                "Bearer token is not a JWT (expected three segments like eyJ...). "
                "The sign-in `token` field is an opaque session id. "
                "Clear Authorization in Swagger; call GET /api/auth/me with cookies from sign-in, "
                "or use a JWT if Neon Auth JWT plugin is enabled."
            ),
        )

    cookie = (request.headers.get("cookie") or "").strip()
    if not cookie:
        raise HTTPException(
            status_code=401,
            detail=(
                "Missing session. Sign in first, then GET /api/auth/me without Bearer (cookies), "
                "or use Authorization: Bearer <jwt>."
            ),
        )

    origin = _origin_for_neon_auth(request)
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            f"{base}/get-session",
            headers={"Origin": origin, "Cookie": cookie},
        )

    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    data = r.json()
    if not data or not isinstance(data, dict):
        raise HTTPException(status_code=401, detail="No session")

    user = data.get("user")
    if user is None:
        raise HTTPException(status_code=401, detail="No user in session")

    out: dict[str, Any] = {"user": user}
    if data.get("session") is not None:
        out["session"] = data["session"]
    return out


@router.get("/me")
async def me(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
    """Session user (cookie) or JWT claims (Bearer), depending on how you authenticated."""
    return user


@router.post("/sign-out")
async def sign_out() -> dict[str, str]:
    """
    Sign-out clears server-side session cookies on Neon Auth; for Bearer/JWT
    clients the client should discard the token.

    TODO(backend): forward Cookie to Neon Auth /sign-out when using cookie sessions.
    """
    return {
        "status": "ok",
        "message": ("Discard client-side token. Cookie sign-out can be added with the frontend."),
    }
