from dataclasses import dataclass

from fastapi import Request

from app.services.auth_service import AuthService
from app.services.community_account_service import CommunityAccountService

UNRESOLVED_IDENTITY_ERROR = "Your session could not be verified. Please sign in again."


class SubmissionIdentityError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SubmissionIdentity:
    community_user_id: int
    discord_id: str
    admin_disabled: bool = False


def resolve_submission_identity(
    request: Request,
    auth_service: AuthService,
    community_service: CommunityAccountService,
) -> SubmissionIdentity | None:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    if not status.get("logged"):
        return None

    discord_id = status.get("id")
    if isinstance(discord_id, int) and not isinstance(discord_id, bool):
        discord_id = str(discord_id)
    if not isinstance(discord_id, str) or not discord_id.strip():
        raise SubmissionIdentityError("Authenticated identity is missing a Discord ID")

    username = status.get("username")
    avatar = status.get("avatar")
    account = community_service.get_or_create(
        discord_id=discord_id,
        discord_username=username if isinstance(username, str) else None,
        discord_avatar=avatar if isinstance(avatar, str) else None,
    )
    if not isinstance(account, dict):
        raise SubmissionIdentityError("Community identity lookup returned no account")
    try:
        community_user_id = int(account["id"])
    except (KeyError, TypeError, ValueError):
        raise SubmissionIdentityError("Community identity lookup returned an invalid ID") from None
    if community_user_id <= 0:
        raise SubmissionIdentityError("Community identity lookup returned an invalid ID")
    return SubmissionIdentity(
        community_user_id=community_user_id,
        discord_id=discord_id,
        admin_disabled=account.get("admin_disabled") is True,
    )
