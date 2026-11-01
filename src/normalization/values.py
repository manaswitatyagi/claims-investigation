"""Stage 6 (part) — NORMALIZE non-date values."""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from src.claim_model import money_value, quantity_value

_MONEY = re.compile(r"^\s*\$?\s*(-?[\d,]+(?:\.\d{1,2})?)\s*$")


def normalise_money(raw: str, currency: str = "USD") -> Optional[Dict[str, Any]]:
    m = _MONEY.match(raw or "")
    if not m:
        return None
    return money_value(float(m.group(1).replace(",", "")), currency)


def normalise_quantity(value: float, unit: str) -> Dict[str, Any]:
    return quantity_value(value, unit)


def normalise_location(raw: str) -> Dict[str, Any]:
    """Locations are carried raw.

    Geocoding would introduce a claim about the world that no source in the
    file asserts, and D-011 (socioeconomic and geographic proxies) is still an
    open decision. `normalised` stays null until that has an answer.
    """
    return {"Location": {"raw": raw, "normalised": None}}
