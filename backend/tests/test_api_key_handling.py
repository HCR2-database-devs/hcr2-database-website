from typing import Any

from fastapi.testclient import TestClient

from app.api import dependencies
from app.core.config import Settings, get_settings
from app.main import create_app

API_KEY = "dev-api-key"


class FakePublicDataService:
    def search_records(self, filters: dict[str, Any]) -> dict[str, Any]:
        return {"records": [], "count": 0, "limit": filters.get("limit")}


def _client(api_key_authorized: Any = None) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(API_KEYS=API_KEY)
    app.dependency_overrides[dependencies.get_public_data_service] = FakePublicDataService
    if api_key_authorized is not None:
        app.dependency_overrides[dependencies.api_key_authorized] = api_key_authorized
    return TestClient(app)


def test_record_search_accepts_api_key_header() -> None:
    response = _client().get("/api/v1/records/search", headers={"X-API-Key": API_KEY})

    assert response.status_code == 200


def test_record_search_still_accepts_deprecated_query_parameter() -> None:
    response = _client().get(f"/api/v1/records/search?api_key={API_KEY}")

    assert response.status_code == 200


def test_header_takes_precedence_over_deprecated_query_parameter() -> None:
    client = _client()

    valid_header = client.get(
        "/api/v1/records/search",
        headers={"X-API-Key": API_KEY},
        params={"api_key": "wrong-key"},
    )
    invalid_header = client.get(
        "/api/v1/records/search",
        headers={"X-API-Key": "wrong-key"},
        params={"api_key": API_KEY},
    )

    assert valid_header.status_code == 200
    assert invalid_header.status_code == 401


def test_record_search_uses_shared_constant_time_key_check() -> None:
    client = _client(api_key_authorized=lambda: False)

    response = client.get("/api/v1/records/search", headers={"X-API-Key": API_KEY})

    assert response.status_code == 401
    assert response.json() == {"error": "Unauthorized: invalid API key"}


def test_compat_record_search_uses_shared_key_check() -> None:
    client = _client(api_key_authorized=lambda: False)

    response = client.get("/php/api_records.php", headers={"X-API-Key": API_KEY})

    assert response.status_code == 401


def test_compat_record_search_accepts_api_key_header() -> None:
    response = _client().get("/php/api_records.php", headers={"X-API-Key": API_KEY})

    assert response.status_code == 200
