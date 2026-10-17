from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    get_auth_service,
    get_community_account_service,
    get_hcr2_link_service,
)
from app.core.config import Settings, get_settings
from app.core.features import can_use_feature
from app.schemas.hcr2_link import (
    ChallengeLinkRequest,
    ChooseMethodRequest,
    CodeSentRequest,
    StartLinkRequest,
    SubmitLinkRequest,
)
from app.services.auth_service import AuthService
from app.services.community_account_service import (
    CommunityAccountService,
    CommunityProfileError,
)
from app.services.hcr2_link_service import Hcr2LinkService

router = APIRouter(prefix="/community/hcr2-link", tags=["hcr2 account linking"])
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CommunityAccountServiceDep = Annotated[
    CommunityAccountService,
    Depends(get_community_account_service),
]
Hcr2LinkServiceDep = Annotated[Hcr2LinkService, Depends(get_hcr2_link_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _require_user(request: Request, auth_service: AuthService) -> dict[str, Any]:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    if not status.get("logged"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return status


def _require_feature(
    request: Request,
    auth_service: AuthService,
    settings: Settings,
    feature_name: str,
) -> None:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    discord_id = str(status["id"]) if status.get("logged") else None
    if not can_use_feature(discord_id, feature_name, settings):
        raise HTTPException(status_code=403, detail="This feature is currently disabled")


def _require_linked_account(
    request: Request,
    auth_service: AuthService,
    community_service: CommunityAccountService,
) -> dict[str, Any]:
    """Require a signed-in, onboarded community account.

    The authenticated cookie is the only source of identity here. No endpoint
    accepts a Discord id, an admin flag or a community user id from the client.
    """
    status = _require_user(request, auth_service)
    account = community_service.get_account(str(status["id"]))
    if account is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not account.get("username"):
        raise HTTPException(
            status_code=403,
            detail="You need to choose a username before you can use this feature.",
        )
    return account


def _link_error_response(exc: CommunityProfileError) -> JSONResponse:
    return JSONResponse({"error": exc.message}, status_code=exc.status_code)


def _user_id(account: dict[str, Any]) -> int:
    return int(account["id"])


@router.get("/config", response_model=None)
def hcr2_link_config(
    request: Request,
    auth_service: AuthServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    """Team name, team password, Discord invite and owner handles for the wizard.

    Requires a signed-in user and the ``hcr2_account_linking`` flag. The team
    password is returned here and nowhere else - it is never stored, never
    logged and never included in an admin payload.
    """
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    return link_service.get_config()


@router.get("/players", response_model=None)
def hcr2_link_players(
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
    q: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=25)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Any:
    """Search player names that hold, or have held, an Adventure world record.

    Only the canonical name and the number of current world records are
    returned. Submission data, submitter identities, IP addresses and record
    history are deliberately excluded.
    """
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    _require_linked_account(request, auth_service, community_service)
    return link_service.search_players(search=q, limit=limit, offset=offset)


@router.get("/status", response_model=None)
def hcr2_link_status(
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    """The caller's own link status, current request and recent attempts."""
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    return link_service.get_status(_user_id(account))


@router.post("/request/start", response_model=None)
def hcr2_link_start(
    payload: StartLinkRequest,
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    """Start (or resume) a request for a player name chosen from the dropdown.

    The name is revalidated against the records database here, so posting an
    arbitrary name directly to this endpoint fails exactly as it would in the
    UI.
    """
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    try:
        return link_service.start_request(_user_id(account), payload.player_name)
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/request/method", response_model=None)
def hcr2_link_choose_method(
    payload: ChooseMethodRequest,
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    try:
        return link_service.choose_method(_user_id(account), payload.verification_method)
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/request/team/joined", response_model=None)
def hcr2_link_team_joined(
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    """Record that the user states they joined the verification team.

    This is the user's statement only. It does not prove anything happened in
    game, which is why the admin panel labels it as a claim.
    """
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    try:
        return link_service.confirm_team_joined(_user_id(account))
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/request/team/code", response_model=None)
def hcr2_link_team_code(
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    """Generate a fresh single-use verification code.

    Enforces the reroll cooldown server-side and invalidates the previous code
    in the same statement. Returns the code itself plus its expiry and the
    countdown until the next reroll; never returns the stored hash.
    """
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    try:
        return link_service.generate_code(_user_id(account))
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/request/team/sent", response_model=None)
def hcr2_link_team_sent(
    payload: CodeSentRequest,
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    """Record that the user states they sent the code in team chat.

    Does not and cannot confirm the message exists: there is no official API
    to read team chat. It stores the claim so the admin can act on it.
    """
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    try:
        return link_service.confirm_code_sent(
            _user_id(account),
            visibility_confirmed=payload.visibility_confirmed,
        )
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/request/discord/joined", response_model=None)
def hcr2_link_discord_joined(
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    try:
        return link_service.confirm_discord_joined(_user_id(account))
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/request/discord/contacted", response_model=None)
def hcr2_link_discord_contacted(
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    """Record that the user states they DM'd the site owner. Not proof of a DM."""
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    try:
        return link_service.confirm_contacted_owner(_user_id(account))
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/request/discord/ready", response_model=None)
def hcr2_link_discord_ready(
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    try:
        return link_service.confirm_discord_ready(_user_id(account))
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/request/challenge/link", response_model=None)
def hcr2_link_challenge_link(
    payload: ChallengeLinkRequest,
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    """Store the playhcr.com challenge link for the assigned distance.

    The service checks the link against the accepted prefix and rejects a
    request whose method is not the challenge method. Storing a valid link is
    not approval: an administrator still opens the challenge and compares its
    distance with the one assigned here.
    """
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    try:
        return link_service.confirm_challenge_link(
            _user_id(account),
            challenge_url=payload.challenge_url,
        )
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/request/submit", response_model=None)
def hcr2_link_submit(
    payload: SubmitLinkRequest,
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    """Hand the request to the admin review queue.

    This endpoint cannot approve anything. Success means "queued for a human".
    """
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    try:
        return link_service.submit_request(
            _user_id(account),
            instructions_followed=payload.instructions_followed,
            method_steps_completed=payload.method_steps_completed,
        )
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/request/cancel", response_model=None)
def hcr2_link_cancel(
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    try:
        return link_service.cancel_request(_user_id(account))
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/link/unlink", response_model=None)
def hcr2_link_unlink(
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    link_service: Hcr2LinkServiceDep,
    settings: SettingsDep,
) -> Any:
    """Immediately revoke the caller's own link. Audited to the activity log."""
    _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "hcr2_account_linking")
    account = _require_linked_account(request, auth_service, community_service)
    try:
        return link_service.unlink(_user_id(account))
    except CommunityProfileError as exc:
        return _link_error_response(exc)