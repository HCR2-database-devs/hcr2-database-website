from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from app.services.admin_service import (
    AdminService,
    AdminServiceError,
    AdminUnsupportedMediaError,
)


def _image_bytes(fmt: str) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format=fmt)
    return buffer.getvalue()


def test_icon_upload_is_required() -> None:
    service = AdminService()

    with pytest.raises(AdminServiceError, match="WebP photo is required"):
        service.validate_icon_upload("map.webp", "image/webp", None)
    with pytest.raises(AdminServiceError, match="WebP photo is required"):
        service.save_icon("map_icons", "Map", "map.webp", "image/webp", None)


def test_icon_upload_rejects_non_webp_filename() -> None:
    service = AdminService()

    with pytest.raises(AdminUnsupportedMediaError, match="Only WebP"):
        service.validate_icon_upload("map.svg", "image/webp", _image_bytes("WEBP"))


def test_icon_upload_rejects_non_webp_content_type() -> None:
    service = AdminService()

    with pytest.raises(AdminUnsupportedMediaError, match="Only WebP"):
        service.validate_icon_upload("map.webp", "image/png", _image_bytes("WEBP"))


def test_icon_upload_rejects_png_bytes_named_webp() -> None:
    service = AdminService()

    with pytest.raises(AdminUnsupportedMediaError, match="does not look like a WebP"):
        service.validate_icon_upload("map.webp", "image/webp", _image_bytes("PNG"))


def test_icon_upload_rejects_invalid_bytes() -> None:
    service = AdminService()

    with pytest.raises(AdminUnsupportedMediaError, match="valid WebP"):
        service.validate_icon_upload("map.webp", "image/webp", b"not an image")


def test_icon_upload_saves_webp_file(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.services.admin_service.REPO_ROOT", tmp_path)
    service = AdminService()
    content = _image_bytes("WEBP")

    message = service.save_icon(
        "map_icons", "Forest Trials", "forest.webp", "image/webp", content
    )

    target = tmp_path / "frontend" / "public" / "img" / "map_icons" / "forest_trials.webp"
    assert target.read_bytes() == content
    assert message == "Icon uploaded: forest_trials.webp"


class FakeAuthService:
    def status_from_cookie(self, cookie: str | None):
        if cookie != "admin":
            return {"logged": False, "allowed": False}
        return {"logged": True, "allowed": True, "username": "admin"}


class FakeAdminService(AdminService):
    def add_map(self, payload, admin_username: str = ""):
        return {"success": True, "idMap": 1}

    def add_vehicle(self, payload, admin_username: str = ""):
        return {"success": True, "idVehicle": 1}

    def add_tuning_part(self, payload, admin_username: str = ""):
        return {"success": True, "idTuningPart": 1}


def _admin_client(tmp_path, monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient

    from app.api import dependencies
    from app.main import create_app

    monkeypatch.setattr("app.services.admin_service.REPO_ROOT", tmp_path)
    app = create_app()
    app.dependency_overrides[dependencies.get_auth_service] = FakeAuthService
    service = FakeAdminService()
    app.dependency_overrides[dependencies.get_admin_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("WC_TOKEN", "admin")
    return client


@pytest.mark.parametrize(
    ("path", "name_field", "name", "folder", "slug"),
    [
        ("/api/v1/admin/maps/form", "mapName", "Forest Trials", "map_icons", "forest_trials"),
        ("/api/v1/admin/vehicles/form", "vehicleName", "Dune Buggy", "vehicle_icons", "dune_buggy"),
        (
            "/api/v1/admin/tuning-parts/form",
            "partName",
            "Winter Tires",
            "tuning_parts_icons",
            "winter_tires",
        ),
    ],
)
def test_admin_catalog_forms_upload_webp(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    name_field: str,
    name: str,
    folder: str,
    slug: str,
) -> None:
    client = _admin_client(tmp_path, monkeypatch)
    content = _image_bytes("WEBP")

    response = client.post(
        path,
        data={name_field: name},
        files={"icon": ("photo.webp", content, "image/webp")},
    )

    assert response.status_code == 200
    assert response.json()["iconMessage"] == f"Icon uploaded: {slug}.webp"
    target = tmp_path / "frontend" / "public" / "img" / folder / f"{slug}.webp"
    assert target.read_bytes() == content


def test_admin_catalog_form_requires_webp(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _admin_client(tmp_path, monkeypatch)

    response = client.post("/api/v1/admin/maps/form", data={"mapName": "Forest Trials"})

    assert response.status_code == 400
    assert response.json()["error"] == "A WebP photo is required."


def test_admin_catalog_form_rejects_svg(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _admin_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/v1/admin/maps/form",
        data={"mapName": "Forest Trials"},
        files={"icon": ("map.svg", b"<svg></svg>", "image/svg+xml")},
    )

    assert response.status_code == 415
    assert response.json()["error"] == "Only WebP icon uploads are supported."
