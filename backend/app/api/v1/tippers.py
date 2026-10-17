import time

import httpx
from fastapi import APIRouter

router = APIRouter(tags=["tippers"])

TIPEEE_URL = (
    "https://api.tipeee.com/v2.0/projects/hcr2-database/top/tippers"
    "?perPage=50&page=1"
)
_CACHE_TTL = 21600

_cache: dict = {"data": None, "fetched_at": 0.0}


@router.get("/tippers")
async def get_tippers() -> dict:
    now = time.time()
    if _cache["data"] is not None and now - _cache["fetched_at"] < _CACHE_TTL:
        return _cache["data"]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(TIPEEE_URL)
            resp.raise_for_status()

        items = resp.json().get("items", [])
        result = {"tippers": [{"pseudo": item["pseudo"]} for item in items]}
        _cache["data"] = result
        _cache["fetched_at"] = now
        return result
    except httpx.HTTPError:
        # Keep serving the last known list when Tipeee is unavailable or slow;
        # fall back to an empty list only if we never fetched successfully.
        if _cache["data"] is not None:
            return _cache["data"]
        return {"tippers": []}
