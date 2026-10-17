"""Country code/name data, loaded from ``shared/countries.json``.

That JSON is the single source of truth. The frontend reads the same file
(``frontend/src/lib/countries.ts``), so the two cannot drift apart. Add or
rename a country there and both sides pick it up.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_FILE = REPO_ROOT / "shared" / "countries.json"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    try:
        raw = DATA_FILE.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Country data is missing: {DATA_FILE}") from exc

    payload = json.loads(raw)
    countries = payload.get("countries")
    if not isinstance(countries, list) or not countries:
        raise RuntimeError(f"Country data is malformed: {DATA_FILE}")

    return payload


@lru_cache(maxsize=1)
def _country_names() -> dict[str, str]:
    return {
        str(entry["code"]).lower(): str(entry["name"])
        for entry in _load()["countries"]
    }


#: Accepted two-letter country codes, used to validate profile submissions.
COUNTRY_CODES: frozenset[str] = frozenset(_country_names())

#: Code to display name.
COUNTRY_NAMES: dict[str, str] = _country_names()


def country_name(code: str | None) -> str | None:
    """Return the display name for a country code.

    Falls back to the uppercased code so an unrecognised value still renders
    something readable rather than an empty field.
    """
    if not code:
        return None
    return COUNTRY_NAMES.get(code.strip().lower(), code.strip().upper())