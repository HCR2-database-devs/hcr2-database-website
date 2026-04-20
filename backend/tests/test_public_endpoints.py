from typing import Any

from fastapi.testclient import TestClient

from app.api import dependencies
from app.core.config import Settings, get_settings
from app.main import create_app
from app.services.news_service import normalize_legacy_news_limit
from app.services.public_data_service import InvalidLoadDataType, MissingLoadDataType


class FakePublicDataService:
    def load_data(self, data_type: str | None) -> list[dict[str, Any]]:
        if data_type is None:
            raise MissingLoadDataType("No data type specified")
        if data_type == "maps":
            return [{"idMap": 1, "nameMap": "Countryside", "special": 0}]
        if data_type == "records":
            return [{"idRecord": 1, "distance": 1234, "map_name": "Countryside"}]
        raise InvalidLoadDataType("Invalid data type")


class FakeNewsService:
    def list_news(self, raw_limit: str | int | None = None) -> dict[str, list[dict[str, Any]]]:
        return {"news": [{"id": 1, "title": "News", "limit": raw_limit}]}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[dependencies.get_public_data_service] = FakePublicDataService
    app.dependency_overrides[dependencies.get_news_service] = FakeNewsService
    return TestClient(app)


def test_clean_public_maps_endpoint_uses_migrated_service() -> None:
    response = _client().get("/api/v1/maps")

    assert response.status_code == 200
    assert response.json() == [{"idMap": 1, "nameMap": "Countryside", "special": 0}]


def test_legacy_load_data_maps_preserves_legacy_contract() -> None:
    response = _client().get("/php/load_data.php?type=maps")

    assert response.status_code == 200
    assert response.json()[0]["nameMap"] == "Countryside"


def test_legacy_load_data_missing_type_preserves_legacy_error() -> None:
    response = _client().get("/php/load_data.php")

    assert response.status_code == 200
    assert response.json() == {"error": "No data type specified"}


def test_legacy_load_data_invalid_type_preserves_legacy_error() -> None:
    response = _client().get("/php/load_data.php?type=unknown")

    assert response.status_code == 200
    assert response.json() == {"error": "Invalid data type"}


def test_legacy_news_route_keeps_raw_limit_query_for_service() -> None:
    response = _client().get("/php/get_news.php?limit=20")

    assert response.status_code == 200
    assert response.json()["news"][0]["limit"] == "20"


def test_legacy_news_limit_normalization_matches_php_behavior() -> None:
    assert normalize_legacy_news_limit(None) == 10
    assert normalize_legacy_news_limit("20") == 20
    assert normalize_legacy_news_limit("abc") == 10
    assert normalize_legacy_news_limit("0") == 10
    assert normalize_legacy_news_limit("101") == 10


def test_hcaptcha_sitekey_route_returns_configured_key() -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(HCAPTCHA_SITE_KEY="site-key")
    response = TestClient(app).get("/php/get_hcaptcha_sitekey.php")

    assert response.status_code == 200
    assert response.json() == {"sitekey": "site-key"}


def test_auth_status_without_cookie_matches_legacy_logged_out_shape() -> None:
    response = _client().get("/auth/status.php")

    assert response.status_code == 200
    assert response.json() == {"logged": False, "allowed": False}
