from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import Settings
from app.db.session import open_connection


@dataclass(frozen=True, slots=True)
class SubmissionResult:
    status_code: int
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class PublicSubmissionService:
    settings: Settings

    def submit(self, data: dict[str, Any], submitter_ip: str) -> SubmissionResult:
        if not self._verify_hcaptcha(str(data.get("h_captcha_response") or "")):
            return self._error("hCaptcha verification failed. Please try again.", 400)

        map_id = self._optional_int(data.get("mapId"))
        vehicle_id = self._optional_int(data.get("vehicleId"))
        distance = self._optional_int(data.get("distance"))
        player_name = str(data.get("playerName") or "").strip()
        player_country = str(data.get("playerCountry") or "").strip()
        tuning_parts = self._normalize_tuning_parts(data.get("tuningParts"))

        if not map_id or not vehicle_id or not distance or not player_name:
            return self._error(
                "Missing required fields (map, vehicle, distance, or player name).",
                400,
            )

        if any(str(data.get(field) or "").strip() for field in self._honeypot_fields()):
            return self._error("Spam detected", 400)

        form_load_time = self._optional_int(data.get("form_load_time")) or 0
        submission_time = self._optional_int(data.get("submission_time")) or 0
        if form_load_time > 0 and submission_time > 0:
            time_spent = submission_time - form_load_time
            if time_spent < 2000:
                return self._error(
                    "Please take your time to fill out the form. "
                    "Submissions that are too fast are rejected.",
                    429,
                )
            if time_spent < 1000:
                return self._error("Spam detected", 400)

        if distance <= 0:
            return self._error("Distance must be a positive number.", 400)
        if len(tuning_parts) < 3 or len(tuning_parts) > 4:
            return self._error("Please provide 3 or 4 tuning parts for the record.", 400)

        with open_connection() as connection:
            with connection.cursor() as cursor:
                if submitter_ip:
                    cursor.execute(
                        """
                        SELECT COUNT(1) AS c
                        FROM pendingsubmission
                        WHERE submitterip = %(ip)s
                          AND submitted_at >= NOW() - INTERVAL '1 hour'
                        """,
                        {"ip": submitter_ip},
                    )
                    rate = cursor.fetchone()
                    if rate and int(rate["c"]) >= 5:
                        return self._error("Rate limit exceeded. Please try again later.", 429)

                cursor.execute(
                    """
                    INSERT INTO pendingsubmission
                        (idmap, idvehicle, distance, playername, playercountry,
                         tuningparts, submitterip)
                    VALUES
                        (%(map_id)s, %(vehicle_id)s, %(distance)s, %(player_name)s,
                         %(player_country)s, %(tuning_parts)s, %(submitter_ip)s)
                    """,
                    {
                        "map_id": map_id,
                        "vehicle_id": vehicle_id,
                        "distance": distance,
                        "player_name": player_name,
                        "player_country": player_country,
                        "tuning_parts": ", ".join(tuning_parts),
                        "submitter_ip": submitter_ip,
                    },
                )
                connection.commit()

        return SubmissionResult(
            status_code=200,
            payload={
                "success": True,
                "message": "Submission received and is pending review by admins.",
            },
        )

    def _verify_hcaptcha(self, token: str) -> bool:
        if not token or not self.settings.hcaptcha_secret_key:
            return False
        try:
            response = httpx.post(
                "https://hcaptcha.com/siteverify",
                data={"secret": self.settings.hcaptcha_secret_key, "response": token},
                timeout=5.0,
            )
        except httpx.HTTPError:
            return False
        if response.status_code != 200:
            return False
        payload = response.json()
        return bool(payload.get("success") is True)

    @staticmethod
    def _normalize_tuning_parts(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return []

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _honeypot_fields() -> tuple[str, str, str, str]:
        return ("hp_email", "hp_website", "hp_phone", "hp_comments")

    @staticmethod
    def _error(message: str, status_code: int) -> SubmissionResult:
        return SubmissionResult(status_code=status_code, payload={"error": message})
