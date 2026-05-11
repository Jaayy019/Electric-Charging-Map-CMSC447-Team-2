"""Map Neon Auth session/JWT users to local SQLAlchemy User rows for vehicle CRUD."""

from __future__ import annotations

import hashlib
import os
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ExternalIdentity, User


def neon_user_dict(current: dict[str, Any]) -> dict[str, Any]:
    """Normalize get_current_user payload to the inner user object."""
    u = current.get("user")
    if isinstance(u, dict):
        return u
    return current


def _extract_identity(session_dict: dict[str, Any]) -> tuple[str, str | None, str | None]:
    """
    Returns (external_subject, email, suggested_username).

    external_subject is stable for ExternalIdentity (JWT sub, session user id, or email).
    """
    email = session_dict.get("email")
    if email is not None:
        email = str(email).strip() or None

    raw_sub = session_dict.get("sub") or session_dict.get("id")
    if raw_sub is not None:
        subject = str(raw_sub).strip()
    elif email:
        subject = email
    else:
        subject = ""

    name = session_dict.get("name")
    if name is not None:
        name = str(name).strip() or None

    return subject, email, name


def _placeholder_password_hash() -> str:
    """Not used for Neon login; satisfies NOT NULL on users.password_hash."""
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", b"__neon_external__", salt, iterations=600_000)
    return salt.hex() + ":" + hashed.hex()


def _sanitize_username_base(email: str | None, name: str | None) -> str:
    if email and "@" in email:
        local = email.split("@", 1)[0]
        base = re.sub(r"[^a-zA-Z0-9_\-]", "", local)[:40]
        if base:
            return base
    if name:
        base = re.sub(r"[^a-zA-Z0-9_\-]", "", name.replace(" ", "_"))[:40]
        if base:
            return base
    return "neon_user"


async def ensure_local_user_for_neon(
    session: AsyncSession,
    current_user_payload: dict[str, Any],
    *,
    provider: str = "neon_auth",
) -> User:
    """
    Find or create a local User linked to the Neon Auth identity.

    `current_user_payload` is the dict returned by get_current_user (contains \"user\").
    """
    inner = neon_user_dict(current_user_payload)
    subject, email, name = _extract_identity(inner)

    if not subject and not email:
        raise ValueError("Neon user payload has no id/sub and no email")

    sub_key = subject or (email or "")

    # Existing link by external identity
    q = await session.execute(
        select(ExternalIdentity).where(
            ExternalIdentity.provider == provider,
            ExternalIdentity.external_subject == sub_key,
        )
    )
    existing_link = q.scalar_one_or_none()
    if existing_link is not None:
        u = await session.get(User, existing_link.user_id)
        if u is not None:
            return u

    # Match user by email if present
    if email:
        q2 = await session.execute(select(User).where(User.email == email))
        by_email = q2.scalar_one_or_none()
        if by_email is not None:
            session.add(
                ExternalIdentity(
                    provider=provider,
                    external_subject=sub_key,
                    user_id=by_email.id,
                )
            )
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                q_link = await session.execute(
                    select(ExternalIdentity).where(
                        ExternalIdentity.provider == provider,
                        ExternalIdentity.external_subject == sub_key,
                    )
                )
                link = q_link.scalar_one_or_none()
                if link is not None:
                    u = await session.get(User, link.user_id)
                    if u is not None:
                        return u
                raise
            await session.refresh(by_email)
            return by_email

    # Create new local user + identity
    base_username = _sanitize_username_base(email, name)
    username = base_username
    suffix = 0
    while True:
        q3 = await session.execute(select(User).where(User.username == username))
        if q3.scalar_one_or_none() is None:
            break
        suffix += 1
        username = f"{base_username}_{suffix}"

    if not email:
        # Rare: synthesize a placeholder email for uniqueness
        email = f"{sub_key.replace('/', '_')}@neon-auth.local"

    user = User(
        username=username,
        email=email,
        password_hash=_placeholder_password_hash(),
    )
    session.add(user)
    await session.flush()

    session.add(
        ExternalIdentity(
            provider=provider,
            external_subject=sub_key,
            user_id=user.id,
        )
    )
    await session.commit()
    await session.refresh(user)
    return user
