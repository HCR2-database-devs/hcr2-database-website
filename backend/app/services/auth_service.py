from dataclasses import dataclass
from typing import Any

from app.core.security import is_allowed_admin, verify_wc_token


@dataclass(frozen=True, slots=True)
class AuthService:
    shared_secret: str | None
    allowed_discord_ids: list[str]

    def status_from_cookie(self, token: str | None) -> dict[str, Any]:
        if not token or not self.shared_secret:
            return {"logged": False, "allowed": False}

        payload = verify_wc_token(token, self.shared_secret)
        if payload is None:
            return {"logged": False, "allowed": False}

        discord_id = str(payload["sub"])
        return {
            "logged": True,
            "allowed": is_allowed_admin(discord_id, self.allowed_discord_ids),
            "id": discord_id,
            "username": payload.get("username"),
        }
