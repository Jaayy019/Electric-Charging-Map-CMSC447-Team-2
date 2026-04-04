#!/usr/bin/env python3
"""Fail if requirements.txt is not plain UTF-8 (e.g. UTF-16 from PowerShell redirection)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / "requirements.txt"


def main() -> int:
    if not REQ.is_file():
        print(f"error: missing {REQ.relative_to(ROOT)}", file=sys.stderr)
        return 1

    raw = REQ.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        print(
            "error: requirements.txt has a UTF-16 BOM; save as UTF-8 "
            "(e.g. in Cursor: status bar encoding → UTF-8).",
            file=sys.stderr,
        )
        return 1

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"error: requirements.txt is not valid UTF-8: {e}", file=sys.stderr)
        return 1

    if "\x00" in text:
        print(
            "error: requirements.txt contains NUL bytes (common when the file is UTF-16). "
            'Re-save as UTF-8 or run: python -c "from pathlib import Path; '
            "p=Path('requirements.txt'); "
            "p.write_text(p.read_text(encoding='utf-16-le'), encoding='utf-8')\"",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
