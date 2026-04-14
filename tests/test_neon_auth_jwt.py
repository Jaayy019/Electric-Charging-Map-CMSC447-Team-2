"""Unit tests for Neon Auth JWT helper (no live JWKS calls)."""

import importlib
import sys
from pathlib import Path

# Repo root on path so `api.neon_auth_jwt` resolves (same as pytest imports from `tests/`)
_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def test_neon_auth_origin_parses_host_only(monkeypatch):
    monkeypatch.setenv(
        "NEON_AUTH_BASE_URL",
        "https://ep-example.neonauth.c-5.us-east-1.aws.neon.tech/neondb/auth",
    )
    import api.neon_auth_jwt as neon_auth_jwt

    importlib.reload(neon_auth_jwt)
    assert (
        neon_auth_jwt.neon_auth_origin()
        == "https://ep-example.neonauth.c-5.us-east-1.aws.neon.tech"
    )
