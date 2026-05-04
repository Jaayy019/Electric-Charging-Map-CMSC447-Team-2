"""Normalize connector labels from OCM / user input for compatibility checks."""

from __future__ import annotations

import re
from typing import Iterable


def _collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def normalize_connector_token(label: str) -> str:
    """
    Map free-form connector titles (e.g. from Open Charge Map) to coarse tokens
    for matching against user-selected vehicle port types.
    """
    s = _collapse_ws(label)
    if not s:
        return ""

    # CCS / Combo
    if "ccs" in s or "combo" in s or "type 2 combo" in s:
        return "ccs"

    # CHAdeMO
    if "chademo" in s.replace(" ", "") or "cha de mo" in s:
        return "chademo"

    # North America AC — J1772 / Type 1
    if "j1772" in s or "type 1" in s or "sae j1772" in s:
        if "ccs" in s:
            return "ccs"
        return "j1772"

    # European AC — Type 2 / Mennekes
    if "type 2" in s or "mennekes" in s:
        if "combo" in s or "ccs" in s:
            return "ccs"
        return "type2"

    # Tesla proprietary (destination / wall / some supercharger wording)
    if "tesla" in s:
        return "tesla"

    # NEMA outlets (Level 1/2)
    if "nema" in s:
        return "nema"

    return re.sub(r"[^a-z0-9]+", "", s)[:48]


def connector_compatible(vehicle_port_type: str, station_port_type: str) -> bool:
    """True if the vehicle's saved port can use this station connector."""
    v = normalize_connector_token(vehicle_port_type)
    t = normalize_connector_token(station_port_type)
    if not v or not t:
        return False
    if v == t:
        return True
    # Substring fallback when one side is a short user label ("CCS") and the other is verbose.
    if len(v) >= 3 and (v in t or t in v):
        return True
    return False


def charge_point_compatible_with_vehicle(
    vehicle_port_type: str,
    station_connection_port_types: Iterable[str],
) -> bool:
    for p in station_connection_port_types:
        if connector_compatible(vehicle_port_type, p):
            return True
    return False
