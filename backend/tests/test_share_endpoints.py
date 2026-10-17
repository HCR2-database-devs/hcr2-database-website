import pytest
from fastapi.testclient import TestClient

from app.api import dependencies
from app.core.config import Settings, get_settings
from app.main import create_app
from app.services.share_service import RecordNotFound


class FakeShareService:
    def __init__(self) -> None:
        self.page_hits: list[int] = []
        self.image_hits: list[int] = []

    def share_page(self, record_id: int) -> str:
        self.page_hits.append(record_id)
        if record_id == 404:
            raise RecordNotFound(str(record_id))
        return (
            '<!DOCTYPE html><html><head><meta property="og:title" content="Share">'
            "</head><body>share</body></html>"
        )

    def og_image(self, record_id: int) -> bytes:
        self.image_hits.append(record_id)
        if record_id == 404:
            raise RecordNotFound(str(record_id))
        return b"\x89PNG\r\n\x1a\nfake-png-data"


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(API_KEYS="dev-api-key")
    app.dependency_overrides[dependencies.get_share_service] = FakeShareService
    return TestClient(app)


def test_share_page_returns_html_with_og_head(client: TestClient) -> None:
    response = client.get("/api/v1/share/records/7")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert '<meta property="og:title"' in response.text


def test_share_page_missing_record_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/share/records/404")

    assert response.status_code == 404
    assert response.json() == {"detail": "Record not found"}


def test_share_png_returns_image_with_etag(client: TestClient) -> None:
    response = client.get("/api/v1/share/records/7.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"\x89PNG\r\n\x1a\nfake-png-data"
    assert response.headers["etag"].startswith('"')


def test_share_png_missing_record_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/share/records/404.png")

    assert response.status_code == 404
    assert response.json() == {"detail": "Record not found"}
