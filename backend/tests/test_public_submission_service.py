from typing import Any

import pytest

from app.core.config import Settings
from app.services.public_submission_service import PublicSubmissionService


def _valid_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "h_captcha_response": "ok",
        "mapId": "1",
        "vehicleId": "1",
        "distance": "12345",
        "playerName": "Demo Driver",
        "playerCountry": "FI",
        "tuningParts": ["Wings", "Coin Boost", "Magnet"],
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> PublicSubmissionService:
    monkeypatch.setattr(PublicSubmissionService, "_verify_hcaptcha", lambda self, token: True)
    return PublicSubmissionService(Settings())


def test_public_submission_rejects_distance_above_main_form_limit(
    service: PublicSubmissionService,
) -> None:
    result = service.submit(_valid_payload(distance="1000001"), "127.0.0.1")

    assert result.status_code == 400
    assert result.payload == {"error": "Distance must be 1000000 or less."}


def test_public_submission_rejects_player_name_above_main_form_limit(
    service: PublicSubmissionService,
) -> None:
    result = service.submit(_valid_payload(playerName="x" * 21), "127.0.0.1")

    assert result.status_code == 400
    assert result.payload == {"error": "Player name must be 20 characters or fewer."}


def test_public_submission_rejects_country_above_main_form_limit(
    service: PublicSubmissionService,
) -> None:
    result = service.submit(_valid_payload(playerCountry="x" * 21), "127.0.0.1")

    assert result.status_code == 400
    assert result.payload == {"error": "Country must be 20 characters or fewer."}
