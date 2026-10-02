import hashlib
import hmac
import inspect
import math
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.core.network import canonicalize_client_ip
from app.db.session import open_connection
from app.services.hcaptcha import verify_hcaptcha
from app.services.submission_identity import SubmissionIdentity

MAX_PUBLIC_DISTANCE = 1_000_000
MAX_PUBLIC_PLAYER_NAME_LENGTH = 20
MAX_PUBLIC_COUNTRY_LENGTH = 20
SUBMISSION_RATE_LIMIT = 5
SUBMISSION_RATE_WINDOW_SECONDS = 3_600
GLOBAL_SUBMISSION_RATE_LIMIT = 1_000
GLOBAL_SUBMISSION_RATE_WINDOW_SECONDS = 3_600

ECHO_EXCLUDED_PART_IDS: frozenset[int] = frozenset({26, 2, 14, 13, 7, 18, 16, 17, 25})
DISABLED_SUBMISSION_ERROR = "Your community account is disabled and cannot submit records."


@dataclass(frozen=True, slots=True)
class SubmissionResult:
    status_code: int
    payload: dict[str, Any]
    retry_after: int | None = None


@dataclass(frozen=True, slots=True)
class _RateLimitResult:
    allowed: bool
    retry_after: int = 0


@dataclass(frozen=True, slots=True)
class PublicSubmissionService:
    settings: Settings

    def submit(
        self,
        data: dict[str, Any],
        submitter_ip: str | None,
        identity: SubmissionIdentity | None = None,
    ) -> SubmissionResult:
        if identity is not None and getattr(identity, "admin_disabled", False):
            return self._error(DISABLED_SUBMISSION_ERROR, 403)
        canonical_ip = canonicalize_client_ip(submitter_ip)
        if identity is None and canonical_ip is None:
            return self._error("Unable to determine your IP address.", 400)
        if not self._verify_submission_hcaptcha(
            str(data.get("h_captcha_response") or ""),
            canonical_ip,
        ):
            return self._error("hCaptcha verification failed. Please try again.", 400)

        map_id = self._optional_int(data.get("mapId"))
        vehicle_id = self._optional_int(data.get("vehicleId"))
        distance = self._optional_int(data.get("distance"))
        player_name = str(data.get("playerName") or "").strip()
        player_country = str(data.get("playerCountry") or "").strip()
        tuning_parts = self._normalize_tuning_parts(data.get("tuningParts"))
        echo_affected_part_id = self._optional_int(data.get("echo_affected_part_id"))

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
        if distance > MAX_PUBLIC_DISTANCE:
            return self._error("Distance must be 1000000 or less.", 400)
        if len(player_name) > MAX_PUBLIC_PLAYER_NAME_LENGTH:
            return self._error("Player name must be 20 characters or fewer.", 400)
        if len(player_country) > MAX_PUBLIC_COUNTRY_LENGTH:
            return self._error("Country must be 20 characters or fewer.", 400)
        if len(tuning_parts) < 3 or len(tuning_parts) > 4:
            return self._error("Please provide 3 or 4 tuning parts for the record.", 400)

        has_echo = "Echo" in tuning_parts
        if has_echo and not echo_affected_part_id:
            return self._error(
                'Echo requires selecting an affected part. Please select a part from '
                'the "Echo Affected Part" dropdown.',
                400,
            )
        if not has_echo and echo_affected_part_id:
            return self._error("You cannot select an affected part without Echo.", 400)
        if has_echo and echo_affected_part_id and echo_affected_part_id in ECHO_EXCLUDED_PART_IDS:
            return self._error("The selected affected part cannot be affected by Echo.", 400)

        identity_id = None
        if identity is not None:
            try:
                identity_id = int(identity.community_user_id)
            except (TypeError, ValueError, AttributeError):
                return self._error(DISABLED_SUBMISSION_ERROR, 403)
            if identity_id <= 0:
                return self._error(DISABLED_SUBMISSION_ERROR, 403)
        elif canonical_ip is None:
            return self._error("Unable to determine your IP address.", 400)

        with open_connection() as connection:
            with connection.cursor() as cursor:
                if identity_id is not None:
                    cursor.execute(
                        """
                        SELECT id
                        FROM community_user
                        WHERE id = %s
                          AND admin_disabled = FALSE
                        FOR UPDATE
                        """,
                        (identity_id,),
                    )
                    if cursor.fetchone() is None:
                        return self._error(DISABLED_SUBMISSION_ERROR, 403)
                else:
                    cursor.execute(
                        "SELECT pg_advisory_xact_lock(hashtext(%s))",
                        (canonical_ip,),
                    )
                    cursor.execute(
                        """
                        SELECT id
                        FROM ip_ban
                        WHERE banned_ip = %s
                          AND active = TRUE
                          AND (expires_at IS NULL OR expires_at > NOW())
                        ORDER BY id DESC
                        LIMIT 1
                        """,
                        (canonical_ip,),
                    )
                    if cursor.fetchone() is not None:
                        return self._error(
                            "Your IP address is banned from submitting records.",
                            403,
                        )

                global_rate = self._consume_rate_limit(
                    cursor,
                    self._rate_limit_key("global", "captcha"),
                    GLOBAL_SUBMISSION_RATE_LIMIT,
                    GLOBAL_SUBMISSION_RATE_WINDOW_SECONDS,
                )
                if not global_rate.allowed:
                    return self._error(
                        "Rate limit exceeded. Please try again later.",
                        429,
                        global_rate.retry_after,
                    )

                if identity_id is not None:
                    rate_key = self._rate_limit_key("account", str(identity_id))
                else:
                    rate_key = self._rate_limit_key("ip", canonical_ip or "unknown")
                submitter_rate = self._consume_rate_limit(
                    cursor,
                    rate_key,
                    SUBMISSION_RATE_LIMIT,
                    SUBMISSION_RATE_WINDOW_SECONDS,
                )
                if not submitter_rate.allowed:
                    return self._error(
                        "Rate limit exceeded. Please try again later.",
                        429,
                        submitter_rate.retry_after,
                    )

                is_mythic = self._parts_contain_mythic(tuning_parts)
                cursor.execute(
                    """
                    SELECT MAX(distance) AS best_distance
                    FROM world_record
                    WHERE id_map = %(map_id)s
                      AND id_vehicle = %(vehicle_id)s
                      AND is_mythic = %(mythic)s
                      AND current = 1
                    """,
                    {
                        "map_id": map_id,
                        "vehicle_id": vehicle_id,
                        "mythic": is_mythic,
                    },
                )
                best = cursor.fetchone()
                best_distance = best["best_distance"] if best else None
                if best_distance is not None and distance <= int(best_distance):
                    return self._error(
                        "This distance is not higher than the current record "
                        f"for this map and vehicle ({best_distance}).",
                        400,
                    )

                cursor.execute(
                    """
                    INSERT INTO pending_submission
                        (id_map, id_vehicle, distance, player_name, player_country,
                         tuning_parts, echo_affected_part_id, submitter_ip,
                         submitter_community_user_id, status)
                    VALUES
                        (%(map_id)s, %(vehicle_id)s, %(distance)s, %(player_name)s,
                         %(player_country)s, %(tuning_parts)s, %(echo_affected_part_id)s,
                         %(submitter_ip)s, %(submitter_community_user_id)s, 'pending')
                    """,
                    {
                        "map_id": map_id,
                        "vehicle_id": vehicle_id,
                        "distance": distance,
                        "player_name": player_name,
                        "player_country": player_country,
                        "tuning_parts": ", ".join(tuning_parts),
                        "echo_affected_part_id": echo_affected_part_id,
                        "submitter_ip": canonical_ip if identity_id is None else None,
                        "submitter_community_user_id": identity_id,
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

    def submit_with_identity(
        self,
        data: dict[str, Any],
        submitter_ip: str | None,
        identity: SubmissionIdentity | None,
    ) -> SubmissionResult:
        return self.submit(data, submitter_ip, identity=identity)

    def _verify_submission_hcaptcha(self, token: str, remote_ip: str | None) -> bool:
        verifier = self._verify_hcaptcha
        try:
            parameters = inspect.signature(verifier).parameters
        except (TypeError, ValueError):
            parameters = {}
        accepts_remote_ip = "remote_ip" in parameters or any(
            parameter.kind == inspect.Parameter.VAR_POSITIONAL for parameter in parameters.values()
        )
        if accepts_remote_ip:
            return verifier(token, remote_ip)
        return verifier(token)

    def _verify_hcaptcha(self, token: str, remote_ip: str | None = None) -> bool:
        return verify_hcaptcha(
            token,
            self.settings.hcaptcha_secret_key,
            site_key=self.settings.hcaptcha_site_key,
            remote_ip=remote_ip,
        )

    def _rate_limit_key(self, scope: str, value: str) -> str:
        material = f"{scope}:{value}".encode()
        secret = self.settings.submission_rate_limit_hmac_secret or self.settings.auth_shared_secret
        if secret:
            digest = hmac.new(secret.encode(), material, hashlib.sha256).hexdigest()
        else:
            digest = hashlib.sha256(material).hexdigest()
        return f"{scope}:{digest}"

    @staticmethod
    def _consume_rate_limit(
        cursor: Any,
        rate_key: str,
        limit: int,
        window_seconds: int,
    ) -> _RateLimitResult:
        cursor.execute(
            """
            INSERT INTO public_submission_rate_limit
                (rate_key, request_count, window_started_at)
            VALUES (%(rate_key)s, 1, CURRENT_TIMESTAMP)
            ON CONFLICT (rate_key) DO UPDATE SET
                request_count = CASE
                    WHEN public_submission_rate_limit.window_started_at <=
                        CURRENT_TIMESTAMP - (%(window_seconds)s * INTERVAL '1 second')
                    THEN 1
                    ELSE public_submission_rate_limit.request_count + 1
                END,
                window_started_at = CASE
                    WHEN public_submission_rate_limit.window_started_at <=
                        CURRENT_TIMESTAMP - (%(window_seconds)s * INTERVAL '1 second')
                    THEN CURRENT_TIMESTAMP
                    ELSE public_submission_rate_limit.window_started_at
                END
            RETURNING request_count, window_started_at,
                EXTRACT(
                    EPOCH FROM (
                        window_started_at + (%(window_seconds)s * INTERVAL '1 second')
                        - CURRENT_TIMESTAMP
                    )
                ) AS retry_after_seconds
            """,
            {"rate_key": rate_key, "window_seconds": window_seconds},
        )
        row = cursor.fetchone()
        if row is None:
            return _RateLimitResult(allowed=False, retry_after=window_seconds)
        request_count = int(row["request_count"])
        if request_count <= limit:
            return _RateLimitResult(allowed=True)
        retry_after = _row_value(row, "retry_after_seconds", window_seconds)
        retry_after = max(1, min(window_seconds, int(math.ceil(float(retry_after)))))
        return _RateLimitResult(allowed=False, retry_after=retry_after)

    @staticmethod
    def _parts_contain_mythic(value: Any) -> bool:
        parts = PublicSubmissionService._normalize_tuning_parts(value)
        names = [part.lower() for part in parts]
        return "echo" in names or "amplifier" in names

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
    def _error(message: str, status_code: int, retry_after: int | None = None) -> SubmissionResult:
        return SubmissionResult(
            status_code=status_code,
            payload={"error": message},
            retry_after=retry_after,
        )


def _row_value(row: Any, key: str, default: Any) -> Any:
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return getattr(row, key, default)
