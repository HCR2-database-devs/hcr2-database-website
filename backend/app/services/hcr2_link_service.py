"""Phase 4 HCR2 player account linking.

There is no official Fingersoft API available to this project, so nothing in
this module ever *verifies* an account. Every supported method ends with a
human reading evidence and an administrator making a decision:

Method A ("team")
    The user leaves their own team, joins the configured verification team and
    pastes a generated code into that team's in-game chat. HCR2's automod
    sometimes censors the player name or the code, hence the reroll cooldown.

Method B ("discord screen share")
    The user arranges a voice call with the site owner and screen-shares
    their HCR2 account. No microphone and no speaking required.

Method C ("playhcr challenge")
    The server assigns a random distance between 1 and 2000 metres. The user
    drives it with a jeep in Countryside Adventure, turns the run into a
    challenge on playhcr.com and sends the link to it. The distance is drawn
    server-side and never re-rolled, so it is something the member cannot pick;
    an administrator still opens the challenge and compares its distance with
    the assigned one before approving.

Consequences that shape this module:

* Nothing auto-approves. ``submit_request`` only ever writes ``submitted``.
* Buttons such as "I've joined the team" record the user's *statement*. They
  are stored with ``*_confirmed_at`` timestamps so the admin panel can see
  that a claim was made, and they are labelled as claims everywhere.
* The dropdown proves a name exists in the records database; it does not prove
  the user owns that HCR2 account. The wizard says so out loud.
* Rate limits, the reroll cooldown and code expiry are enforced here, not only
  in the UI.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import Settings
from app.core.hcr2_challenge import (
    CHALLENGE_URL_PREFIX,
    MIN_DISTANCE_M,
    normalize_challenge_url,
    random_distance_m,
)
from app.core.verification_code import (
    build_code,
    contains_censor_character,
    generate_token,
    hash_token,
    normalize_player_name,
    player_name_key,
    verify_token,
)
from app.db.session import DatabaseConfig, open_connection
from app.repositories.hcr2_link import ActiveLinkConflictError, Hcr2LinkRepository
from app.services.activity_log_service import ActivityLogService
from app.services.community_account_service import CommunityProfileError
from app.services.community_notification_service import CommunityNotificationService
from app.services.rate_limit import RATE_LIMIT_TABLE, consume_rate_limit

METHOD_TEAM = "team"
METHOD_DISCORD = "discord_screen_share"
METHOD_CHALLENGE = "playhcr_challenge"

VALID_METHODS = (METHOD_TEAM, METHOD_DISCORD, METHOD_CHALLENGE)

#: Human label per method, shared by the summary payload and the step detail
#: trail so the admin queue never has to guess what a stored step means.
METHOD_LABELS = {
    METHOD_TEAM: "verification team",
    METHOD_DISCORD: "Discord screen-share",
    METHOD_CHALLENGE: "playhcr jeep challenge",
}

STATUS_DRAFT = "draft"
STATUS_IN_PROGRESS = "in_progress"
STATUS_SUBMITTED = "submitted"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_EXPIRED = "expired"
STATUS_CANCELLED = "cancelled"

OPEN_STATUSES = (STATUS_DRAFT, STATUS_IN_PROGRESS)

#: Statuses the owning user is allowed to edit. A submitted request is frozen
#: until an administrator acts on it.
EDITABLE_STATUSES = (STATUS_DRAFT, STATUS_IN_PROGRESS)

#: Statuses that represent an attempt still in play. Anything else is finished
#: and must not be treated as resumable by a client.
LIVE_STATUSES = (STATUS_DRAFT, STATUS_IN_PROGRESS, STATUS_SUBMITTED)

REJECTION_CATEGORIES = (
    "code_not_visible",
    "wrong_player_name",
    "could_not_confirm_account",
    "screen_share_inconclusive",
    "challenge_mismatch",
    "name_already_linked",
    "no_contact",
    "request_cancelled",
    "other",
)

APPOINTMENT_STATUSES = (
    "waiting_contact",
    "awaiting_scheduling",
    "scheduled",
    "awaiting_screen_share",
    "awaiting_decision",
    "cancelled",
)

#: Shown instead of any detail about the conflicting account.
NAME_TAKEN_ERROR = (
    "This player name is already linked to another community account. "
    "Please contact staff if you believe this is a mistake."
)

#: Shown for any name that is not backed by a world record.
INELIGIBLE_NAME_ERROR = (
    "That player name is not available for linking. Pick a name from the "
    "list of names that hold a world record."
)

ACTIVITY_ENTITY_REQUEST = "hcr2_verification_request"
ACTIVITY_ENTITY_LINK = "hcr2_account_link"

#: Steps in wizard order, used to drive the progress indicator.
WIZARD_STEPS: tuple[str, ...] = (
    "select_player",
    "choose_method",
    "team_code",
    "summary",
)


def _naive_utc() -> datetime:
    """Current UTC time as a naive value, matching the naive DB timestamps."""
    return datetime.now(UTC).replace(tzinfo=None)


def _as_naive(value: Any) -> datetime | None:
    """Normalize a DB timestamp (naive) or ISO string to a naive datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed


def iso_utc(value: Any) -> str | None:
    """Serialize a timestamp as an unambiguous UTC ISO-8601 string.

    The database stores ``timestamp without time zone`` and psycopg therefore
    hands back naive datetimes. Those serialize without a timezone designator,
    and JavaScript's ``Date.parse`` interprets such a string as *local* time --
    which made every countdown in the wizard wrong by the browser's UTC offset
    (a code appeared expired the moment it was generated, on any machine east
    of UTC). Tagging the value as UTC removes the ambiguity entirely.

    ``Z`` is emitted rather than ``+00:00`` because it is unambiguous in every
    JavaScript engine and readable to humans.
    """
    moment = _as_naive(value)
    if moment is None:
        return None
    return moment.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")


def _seconds_until(value: Any) -> int:
    target = _as_naive(value)
    if target is None:
        return 0
    return max(int((target - _naive_utc()).total_seconds()), 0)


#: Timestamp columns on ``hcr2_account_link``.
_LINK_TIMESTAMPS = ("requested_at", "approved_at", "revoked_at")


def _link_view(link: dict[str, Any]) -> dict[str, Any]:
    """Serialize a link row with unambiguous UTC timestamps."""
    view = dict(link)
    for column in _LINK_TIMESTAMPS:
        view[column] = iso_utc(link.get(column))
    return view


#: Timestamp columns on a request row, for admin payloads.
_REQUEST_TIMESTAMPS = (
    "created_at",
    "updated_at",
    "expires_at",
    "submitted_at",
    "player_confirmed_at",
    "team_joined_at",
    "code_generated_at",
    "code_expires_at",
    "code_last_generated_at",
    "code_sent_confirmed_at",
    "discord_joined_at",
    "contacted_owner_at",
    "challenge_confirmed_at",
    "appointment_at",
    "decided_at",
)


def _admin_request_view(request: dict[str, Any]) -> dict[str, Any]:
    """Serialize an admin request row with unambiguous UTC timestamps."""
    view = dict(request)
    for column in _REQUEST_TIMESTAMPS:
        view[column] = iso_utc(request.get(column))
    return view


def _admin_step_view(step: dict[str, Any]) -> dict[str, Any]:
    view = dict(step)
    view["reached_at"] = iso_utc(step.get("reached_at"))
    return view


def _admin_history_view(row: dict[str, Any]) -> dict[str, Any]:
    view = dict(row)
    for column in ("created_at", "submitted_at", "decided_at"):
        view[column] = iso_utc(row.get(column))
    return view


@dataclass(frozen=True, slots=True)
class Hcr2LinkService:
    repository: Hcr2LinkRepository
    settings: Settings
    activity_log: ActivityLogService | None = None
    notification_service: CommunityNotificationService | None = None
    config: DatabaseConfig | None = None

    # -- configuration ------------------------------------------------------

    @property
    def team_method_available(self) -> bool:
        return bool(self.settings.hcr2_link_verification_team_name.strip())

    @property
    def discord_method_available(self) -> bool:
        return bool(self.settings.hcr2_link_discord_invite_url.strip()) or bool(
            self.settings.hcr2_link_owner_handles
        )

    @property
    def challenge_method_available(self) -> bool:
        return bool(self.settings.hcr2_link_challenge_enabled)

    @property
    def challenge_max_distance_m(self) -> int:
        """Upper bound of the distance draw, never below the 1 m minimum."""
        return max(int(self.settings.hcr2_link_challenge_max_distance_m), MIN_DISTANCE_M)

    def get_config(self) -> dict[str, Any]:
        """Configuration the wizard needs, for an already-authenticated user.

        The team password is returned here and nowhere else: it is not stored,
        not logged, and never appears in an admin payload or an activity-log
        entry. Anyone who can open the wizard can read it, which is inherent
        to HCR2 team joining - rotating it is an env change, documented in
        ``docs/hcr2-account-linking.md``.
        """
        return {
            "team": {
                "available": self.team_method_available,
                "team_name": self.settings.hcr2_link_verification_team_name,
                "team_password": self.settings.hcr2_link_verification_team_password,
                "details": self.settings.hcr2_link_verification_team_details,
                "requires_leaving_current_team": True,
                "supports_chinese_version": False,
                "review": "manual",
            },
            "discord": {
                "available": self.discord_method_available,
                "invite_url": self.settings.hcr2_link_discord_invite_url,
                "owner_handles": list(self.settings.hcr2_link_owner_handles),
                "requires_leaving_current_team": False,
                "requires_microphone": False,
                "requires_speaking": False,
                "review": "manual",
            },
            "challenge": {
                "available": self.challenge_method_available,
                "instructions": self.settings.hcr2_link_challenge_instructions,
                "min_distance_m": MIN_DISTANCE_M,
                "max_distance_m": self.challenge_max_distance_m,
                # Sent to the wizard so the input can show the exact prefix the
                # backend will accept. The backend still validates it itself.
                "link_prefix": CHALLENGE_URL_PREFIX,
                "requires_leaving_current_team": False,
                "review": "manual",
            },
            "code_ttl_seconds": self.settings.hcr2_link_code_ttl_seconds,
            "code_reroll_cooldown_seconds": (
                self.settings.hcr2_link_code_reroll_cooldown_seconds
            ),
            "request_ttl_days": self.settings.hcr2_link_request_ttl_days,
            "automatic_verification": False,
        }

    # -- player name dropdown ----------------------------------------------

    def search_players(
        self,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        normalized = (search or "").strip()[:50] or None
        players, total = self.repository.search_eligible_players(
            search=normalized,
            limit=limit,
            offset=offset,
        )
        return {
            "players": [
                {
                    "id_player": player["id_player"],
                    "name_player": player["name_player"],
                    "record_count": player.get("record_count", 0),
                }
                for player in players
            ],
            "count": total,
            "limit": limit,
            "offset": offset,
            "search": normalized,
        }

    # -- helpers ------------------------------------------------------------

    def _log(
        self,
        admin_username: str,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        entity_name: str | None = None,
        note: str | None = None,
    ) -> None:
        if self.activity_log:
            self.activity_log.log_action(
                admin_username,
                action,
                entity_type,
                entity_id,
                entity_name,
                note=note,
            )

    def _notify(self, community_user_id: int, notification_type: str, message: str) -> None:
        if self.notification_service:
            self.notification_service.notify(community_user_id, notification_type, message)

    def _rate_limit(self, scope: str, value: str, limit: int, window: int) -> int:
        """Consume one unit of the caller's window. Returns retry-after seconds.

        Returns 0 when allowed, otherwise the number of seconds to wait. A
        database failure must not become an outage, so a connection error
        fails open and is logged by the caller's error handling.
        """
        if limit <= 0:
            return 0
        try:
            with open_connection(self.config) as connection:
                with connection.cursor() as cursor:
                    result = consume_rate_limit(
                        cursor,
                        table=RATE_LIMIT_TABLE,
                        scope=scope,
                        value=value,
                        limit=limit,
                        window_seconds=window,
                        secret=self.settings.hcr2_link_code_secret or None,
                    )
                connection.commit()
        except Exception:  # noqa: BLE001 - never let rate limiting break the flow
            return 0
        if result.allowed:
            return 0
        return result.retry_after

    def _resolve_eligible_player(self, player_name: str) -> dict[str, Any]:
        """Resolve a selected name against the records database.

        Called again on submit and again on approve, so a name that was
        eligible when it was picked but no longer is cannot slip through by
        posting to the API directly.
        """
        player = self.repository.find_eligible_player(player_name)
        if player is None:
            raise CommunityProfileError(INELIGIBLE_NAME_ERROR)
        return player

    def _expire_if_stale(self, request: dict[str, Any] | None) -> dict[str, Any] | None:
        if request is None:
            return None
        if request.get("status") not in EDITABLE_STATUSES:
            return request
        expires_at = _as_naive(request.get("expires_at"))
        if expires_at is None or expires_at > _naive_utc():
            return request
        updated = self.repository.set_request_status(int(request["id"]), STATUS_EXPIRED)
        return updated if updated is not None else request

    def _require_editable_request(
        self,
        community_user_id: int,
        *,
        expected_step: str | None = None,
    ) -> dict[str, Any]:
        request = self._expire_if_stale(self.repository.get_active_request(community_user_id))
        if request is None:
            raise CommunityProfileError(
                "Start a linking request before continuing.",
                409,
            )
        if request.get("status") == STATUS_SUBMITTED:
            raise CommunityProfileError(
                "This request is already awaiting admin review.",
                409,
            )
        if request.get("status") not in EDITABLE_STATUSES:
            raise CommunityProfileError(
                f"This request is {request.get('status')} and can no longer be edited.",
                409,
            )
        if expected_step is not None and request.get("step") != expected_step:
            raise CommunityProfileError(
                "Finish the previous step first.",
                409,
            )
        return request

    # -- status -------------------------------------------------------------

    def get_status(self, community_user_id: int) -> dict[str, Any]:
        """Link status, current request and recent attempts.

        ``request`` is the most recent attempt whether or not it is still
        editable, while ``request_is_live`` says which. The distinction matters:
        after an admin revokes a link the latest attempt is still ``approved``,
        and a client that treats any returned request as resumable gets stuck
        holding a finished wizard it cannot restart. Only a draft, in-progress
        or submitted request is resumable.
        """
        candidate = self._expire_if_stale(
            self.repository.get_active_request(community_user_id)
        )
        # Liveness follows the status, not merely "a row came back": a request
        # that only just crossed its expiry is returned by the sweep with status
        # 'expired', and treating that as live would hand the client a dead
        # wizard to resume.
        is_live = candidate is not None and candidate.get("status") in LIVE_STATUSES
        request = candidate if is_live else self.repository.get_latest_request(community_user_id)
        link = self.repository.get_active_link_for_user(community_user_id)
        return {
            "link": _link_view(link) if link else None,
            "request": self._user_view(request) if request else None,
            "request_is_live": is_live,
            "history": [
                self._user_view(item)
                for item in self.repository.list_requests_for_user(community_user_id)
            ],
            "automatic_verification": False,
        }

    def _user_view(self, request: dict[str, Any]) -> dict[str, Any]:
        """Shape a request row for its owner.

        Never includes ``code_token_hash``, ``admin_note``, the raw rejection
        text chosen by an administrator, ``decided_by_admin`` or any Discord
        identifier. The user sees their own code value (they generated it) and
        the category of a rejection, not the internal note.
        """
        return {
            "id": request["id"],
            "player_name": request["player_name"],
            "player_name_norm": request["player_name_norm"],
            "verification_method": request["verification_method"],
            "status": request["status"],
            "step": request["step"],
            "attempt_count": request.get("attempt_count", 1),
            "is_resubmission": bool(request.get("is_resubmission")),
            "supersedes_request_id": request.get("supersedes_request_id"),
            "created_at": iso_utc(request.get("created_at")),
            "updated_at": iso_utc(request.get("updated_at")),
            "expires_at": iso_utc(request.get("expires_at")),
            "submitted_at": iso_utc(request.get("submitted_at")),
            "team_joined_claimed": request.get("team_joined_at") is not None,
            "code": request.get("code_value"),
            "code_expires_at": iso_utc(request.get("code_expires_at")),
            "code_last_generated_at": iso_utc(request.get("code_last_generated_at")),
            "code_roll_count": request.get("code_roll_count", 0),
            "code_sent_claimed": request.get("code_sent_confirmed_at") is not None,
            "discord_joined_claimed": request.get("discord_joined_at") is not None,
            "contacted_owner_claimed": request.get("contacted_owner_at") is not None,
            "challenge_distance_m": request.get("challenge_distance_m"),
            "challenge_url": request.get("challenge_url"),
            "challenge_id": request.get("challenge_id"),
            "challenge_link_claimed": request.get("challenge_confirmed_at") is not None,
            "appointment_status": request.get("appointment_status"),
            "appointment_at": iso_utc(request.get("appointment_at")),
            "decided_at": iso_utc(request.get("decided_at")),
            "rejection_category": request.get("rejection_category"),
        }

    def code_state(self, request: dict[str, Any]) -> dict[str, Any]:
        """Cooldown/expiry counters the UI uses to gate the reroll button."""
        expires_in = _seconds_until(request.get("code_expires_at"))
        last_generated = _as_naive(request.get("code_last_generated_at"))
        cooldown = self.settings.hcr2_link_code_reroll_cooldown_seconds
        if last_generated is None:
            reroll_in = 0
        else:
            reroll_in = max(
                int((last_generated + timedelta(seconds=cooldown) - _naive_utc()).total_seconds()),
                0,
            )
        return {
            "code": request.get("code_value"),
            "code_expires_at": iso_utc(request.get("code_expires_at")),
            "code_last_generated_at": iso_utc(request.get("code_last_generated_at")),
            "code_expired": request.get("code_value") is not None and expires_in == 0,
            # Seconds rather than only a timestamp: this is what the UI counts
            # down from, so it stays correct regardless of the browser's clock
            # or timezone.
            "code_expires_in_seconds": expires_in,
            "reroll_available_in_seconds": reroll_in,
            "reroll_cooldown_seconds": cooldown,
            "code_roll_count": request.get("code_roll_count", 0),
        }

    # -- wizard -------------------------------------------------------------

    def start_request(self, community_user_id: int, player_name: str) -> dict[str, Any]:
        retry_after = self._rate_limit(
            f"hcr2-link-start:{community_user_id}",
            str(community_user_id),
            self.settings.hcr2_link_request_rate_limit,
            self.settings.hcr2_link_request_rate_window_seconds,
        )
        if retry_after:
            raise CommunityProfileError(
                "You have started several linking requests recently. "
                f"Please try again in {retry_after} seconds.",
                429,
            )

        exact_name = normalize_player_name(player_name or "")
        if not exact_name:
            raise CommunityProfileError(INELIGIBLE_NAME_ERROR)

        player = self._resolve_eligible_player(exact_name)
        name_norm = player_name_key(str(player["name_player"]))

        active_link = self.repository.get_active_link_for_user(community_user_id)
        if active_link is not None:
            if active_link["player_name_norm"] == name_norm:
                raise CommunityProfileError(
                    "This player name is already linked to your account.",
                    409,
                )
            raise CommunityProfileError(
                "Unlink your current player name before linking a different one.",
                409,
            )

        if self.repository.get_active_link_for_player(name_norm) is not None:
            raise CommunityProfileError(NAME_TAKEN_ERROR, 409)

        existing = self.repository.get_active_request(community_user_id)
        if existing is not None and existing.get("player_name_norm") == name_norm:
            return {"request": self._user_view(existing), "resumed": True}

        open_ids = self.repository.list_open_request_ids(community_user_id)
        if len(open_ids) >= self.settings.hcr2_link_max_open_requests:
            raise CommunityProfileError(
                "You already have an unfinished request in progress. "
                "Finish or cancel it before starting another.",
                409,
            )

        previous = self.repository.get_latest_request(community_user_id)
        supersedes = None
        attempt = 1
        is_resubmission = False
        if previous is not None and previous["player_name_norm"] == name_norm:
            attempt = int(previous.get("attempt_count") or 1) + 1
            is_resubmission = True
            supersedes = int(previous["id"])

        if open_ids:
            self.repository.cancel_open_requests_for_user(community_user_id)
        self.repository.clear_codes_for_user(community_user_id)

        created = self.repository.create_request(
            {
                "community_user_id": community_user_id,
                "player_id": player["id_player"],
                "player_name": player["name_player"],
                "player_name_norm": name_norm,
                "verification_method": METHOD_TEAM,
                "status": STATUS_DRAFT,
                # The name has already been validated and selected by the time a
                # request exists, so the wizard has moved past that step.
                # Recording a truthful step is what lets an unfinished request
                # resume in the right place instead of one step behind.
                "step": "choose_method",
                "attempt_count": attempt,
                "is_resubmission": is_resubmission,
                "supersedes_request_id": supersedes,
                "expires_at": _naive_utc()
                + timedelta(days=self.settings.hcr2_link_request_ttl_days),
            }
        )
        return {"request": self._user_view(created), "resumed": False}

    def choose_method(self, community_user_id: int, method: str) -> dict[str, Any]:
        if method not in VALID_METHODS:
            raise CommunityProfileError("Unknown verification method.")
        if method == METHOD_TEAM and not self.team_method_available:
            raise CommunityProfileError(
                "The verification team method is not configured yet. Please contact staff.",
                503,
            )
        if method == METHOD_DISCORD and not self.discord_method_available:
            raise CommunityProfileError(
                "The Discord verification method is not configured yet. "
                "Please contact staff.",
                503,
            )
        if method == METHOD_CHALLENGE and not self.challenge_method_available:
            raise CommunityProfileError(
                "The challenge verification method is not configured yet. "
                "Please contact staff.",
                503,
            )
        request = self._require_editable_request(community_user_id)
        # The name is already chosen by the time a request exists, so the
        # request starts past that step. Keeping the stored step truthful is what
        # lets the wizard resume in the right place for the user.
        step = {
            METHOD_TEAM: "team_join",
            METHOD_DISCORD: "discord_join",
            METHOD_CHALLENGE: "challenge_assign",
        }[method]
        fields: dict[str, Any] = {"verification_method": method}
        if method == METHOD_CHALLENGE:
            # One distance per request, drawn on the server, never re-rolled. A
            # request that already has one keeps it, so going back a step and
            # choosing the method again cannot be used to keep drawing until a
            # 1 m roll comes up.
            if request.get("challenge_distance_m") is None:
                fields["challenge_distance_m"] = random_distance_m(
                    maximum_m=self.challenge_max_distance_m
                )
        updated = self.repository.mark_request_step(
            int(request["id"]),
            step=step,
            fields=fields,
            detail=f"Verification method set to {METHOD_LABELS[method]}",
        )
        return {"request": self._user_view(updated or request)}

    def confirm_team_joined(self, community_user_id: int) -> dict[str, Any]:
        request = self._require_editable_request(community_user_id)
        if request["verification_method"] != METHOD_TEAM:
            raise CommunityProfileError("Choose the verification team method first.", 409)
        updated = self.repository.mark_request_step(
            int(request["id"]),
            step="team_join",
            fields={"team_joined_at": _naive_utc(), "code_token_hash": None},
            detail="User states they joined the verification team",
        )
        return {"request": self._user_view(updated or request)}

    def generate_code(self, community_user_id: int) -> dict[str, Any]:
        """Generate a fresh single-use verification code.

        Enforces the reroll cooldown server-side: the repository's ``UPDATE``
        matches zero rows while the cooldown is still running, so a client that
        ignores the countdown cannot obtain a second code.
        """
        request = self._require_editable_request(community_user_id)
        if request["verification_method"] != METHOD_TEAM:
            raise CommunityProfileError("Choose the verification team method first.", 409)

        cooldown = self.settings.hcr2_link_code_reroll_cooldown_seconds
        retry_after = self._rate_limit(
            "hcr2-link-code",
            str(community_user_id),
            self.settings.hcr2_link_code_rate_limit,
            self.settings.hcr2_link_code_rate_window_seconds,
        )
        if retry_after:
            raise CommunityProfileError(
                f"Too many code requests. Please try again in {retry_after} seconds.",
                429,
            )

        if contains_censor_character(str(request["player_name"])):
            raise CommunityProfileError(
                "This player name contains a censored character and cannot be used in a "
                "verification code. Please pick a different name.",
            )

        token = generate_token()
        code = build_code(str(request["player_name"]), token)
        cutoff = _naive_utc() - timedelta(seconds=max(cooldown, 0))
        issued = self.repository.issue_code(
            {
                "request_id": int(request["id"]),
                "code_token_hash": hash_token(token, self.settings.hcr2_link_code_secret),
                "code_value": code,
                "code_expires_at": _naive_utc()
                + timedelta(seconds=self.settings.hcr2_link_code_ttl_seconds),
                "cooldown_cutoff": cutoff,
            }
        )
        if issued is None:
            wait = max(
                cooldown - _seconds_since(request.get("code_last_generated_at")),
                1,
            )
            raise CommunityProfileError(
                f"You can request a new code in {wait} seconds.",
                429,
            )

        state = self.code_state(issued)
        state["player_name"] = request["player_name"]
        state["previous_code_invalidated"] = True
        state["single_use"] = True
        return state

    def confirm_code_sent(
        self,
        community_user_id: int,
        *,
        visibility_confirmed: bool,
    ) -> dict[str, Any]:
        request = self._require_editable_request(community_user_id)
        if request["verification_method"] != METHOD_TEAM:
            raise CommunityProfileError("Choose the verification team method first.", 409)
        if not request.get("code_value"):
            raise CommunityProfileError("Generate a verification code first.", 409)
        if not visibility_confirmed:
            raise CommunityProfileError(
                "Confirm that the full player name and code were visible in team chat.",
            )
        code = str(request["code_value"])
        token_part = code.rsplit(":", 1)[-1].replace("-", "")
        if contains_censor_character(str(request["player_name"])) or contains_censor_character(
            code
        ):
            raise CommunityProfileError(
                "That code contains censored characters. Reroll the code and try again.",
            )
        if not verify_token(
            token_part,
            request.get("code_token_hash"),
            self.settings.hcr2_link_code_secret,
        ):
            raise CommunityProfileError(
                "This code is no longer valid. Generate a new code and try again.",
                409,
            )

        updated = self.repository.mark_request_step(
            int(request["id"]),
            step="team_sent",
            fields={
                "code_sent_confirmed_at": _naive_utc(),
                "code_visibility_confirmed": True,
            },
            detail="User states the code was sent visibly in team chat",
        )
        return {"request": self._user_view(updated or request)}

    def confirm_discord_joined(self, community_user_id: int) -> dict[str, Any]:
        request = self._require_editable_request(community_user_id)
        if request["verification_method"] != METHOD_DISCORD:
            raise CommunityProfileError("Choose the Discord screen share method first.", 409)
        updated = self.repository.mark_request_step(
            int(request["id"]),
            step="discord_join",
            fields={"discord_joined_at": _naive_utc()},
            detail="User states they joined the Discord server",
        )
        return {"request": self._user_view(updated or request)}

    def confirm_contacted_owner(self, community_user_id: int) -> dict[str, Any]:
        request = self._require_editable_request(community_user_id)
        if request["verification_method"] != METHOD_DISCORD:
            raise CommunityProfileError("Choose the Discord screen share method first.", 409)
        updated = self.repository.mark_request_step(
            int(request["id"]),
            step="discord_contact",
            fields={"contacted_owner_at": _naive_utc()},
            detail="User states they contacted the site owner",
        )
        return {"request": self._user_view(updated or request)}

    def confirm_discord_ready(self, community_user_id: int) -> dict[str, Any]:
        request = self._require_editable_request(community_user_id)
        if request["verification_method"] != METHOD_DISCORD:
            raise CommunityProfileError("Choose the Discord screen share method first.", 409)
        updated = self.repository.mark_request_step(
            int(request["id"]),
            step="discord_schedule",
            detail="User reached the screen share step",
        )
        return {"request": self._user_view(updated or request)}

    def confirm_challenge_link(
        self,
        community_user_id: int,
        *,
        challenge_url: str,
    ) -> dict[str, Any]:
        """Record the playhcr.com challenge the member made for the assignment.

        The link is validated here, not only in the browser, because a direct
        API caller skips the form entirely. Storing the URL and its id does not
        make the challenge genuine: an administrator still opens it and compares
        the distance with the assigned one.
        """
        request = self._require_editable_request(community_user_id)
        if request["verification_method"] != METHOD_CHALLENGE:
            raise CommunityProfileError("Choose the jeep challenge method first.", 409)
        if request.get("challenge_distance_m") is None:
            raise CommunityProfileError(
                "Your distance has not been assigned yet. Choose the method again.",
                409,
            )
        try:
            normalized, challenge_id = normalize_challenge_url(challenge_url)
        except ValueError as exc:
            raise CommunityProfileError(str(exc)) from exc

        updated = self.repository.mark_request_step(
            int(request["id"]),
            step="challenge_link",
            fields={
                "challenge_url": normalized,
                "challenge_id": challenge_id,
                "challenge_confirmed_at": _naive_utc(),
            },
            detail=(
                f"User states they drove {request['challenge_distance_m']} m and sent "
                f"challenge {challenge_id}"
            ),
        )
        return {"request": self._user_view(updated or request)}

    def submit_request(
        self,
        community_user_id: int,
        *,
        instructions_followed: bool,
        method_steps_completed: bool,
    ) -> dict[str, Any]:
        """Hand the request to the admin review queue.

        There is deliberately no branch here that can produce an approval.
        """
        request = self._require_editable_request(community_user_id)
        if not instructions_followed:
            raise CommunityProfileError(
                "Confirm that you have followed the verification instructions.",
            )
        if not method_steps_completed:
            raise CommunityProfileError("Complete the verification steps first.", 409)

        if request["verification_method"] == METHOD_TEAM:
            if not request.get("team_joined_at"):
                raise CommunityProfileError(
                    "Confirm that you joined the verification team first.",
                    409,
                )
            if not request.get("code_value"):
                raise CommunityProfileError("Generate a verification code first.", 409)
            if not request.get("code_sent_confirmed_at"):
                raise CommunityProfileError(
                    "Confirm that you sent the code in team chat first.",
                    409,
                )
        elif request["verification_method"] == METHOD_CHALLENGE:
            if request.get("challenge_distance_m") is None:
                raise CommunityProfileError(
                    "Choose the jeep challenge method to get your distance first.",
                    409,
                )
            if not request.get("challenge_confirmed_at") or not request.get("challenge_url"):
                raise CommunityProfileError(
                    "Send the link to your playhcr.com challenge first.",
                    409,
                )
        elif request["verification_method"] == METHOD_DISCORD:
            if not request.get("discord_joined_at"):
                raise CommunityProfileError(
                    "Confirm that you joined the Discord server first.",
                    409,
                )
            if not request.get("contacted_owner_at"):
                raise CommunityProfileError(
                    "Confirm that you contacted the site owner first.",
                    409,
                )
        else:
            # A stored method outside VALID_METHODS can only come from a bad
            # write. Refusing here keeps such a request out of the admin queue.
            raise CommunityProfileError("Unknown verification method.", 409)

        # Re-validate eligibility at submit time: the dropdown may have been
        # answered from an old page, and a direct API caller skips it entirely.
        self._resolve_eligible_player(str(request["player_name"]))
        if self.repository.get_active_link_for_player(str(request["player_name_norm"])) is not None:
            raise CommunityProfileError(NAME_TAKEN_ERROR, 409)

        updated = self.repository.mark_request_step(
            int(request["id"]),
            step="summary",
            status=STATUS_SUBMITTED,
            fields={"submitted_at": _naive_utc()},
            detail="Submitted for admin review",
        )
        return {
            "request": self._user_view(updated or request),
            "message": "Submitted — awaiting admin review",
            "automatic_verification": False,
        }

    def cancel_request(self, community_user_id: int) -> dict[str, Any]:
        cancelled = self.repository.cancel_open_requests_for_user(community_user_id)
        if not cancelled:
            raise CommunityProfileError("There is no request in progress to cancel.", 404)
        return {"cancelled": cancelled}

    def unlink(self, community_user_id: int) -> dict[str, Any]:
        """Immediately revoke the caller's own active link.

        Self-service and instant, but still audited, because a link is a
        verified claim about an account. Linking a different name afterwards
        requires a fresh request and a fresh admin review.
        """
        link = self.repository.get_active_link_for_user(community_user_id)
        if link is None:
            raise CommunityProfileError("There is no linked player name to unlink.", 404)
        revoked = self.repository.set_link_status(
            {
                "link_id": int(link["id"]),
                "status": "revoked",
                "revoked_at": _naive_utc(),
                "revoked_by_admin": "",
                "revocation_reason": "Unlinked by the member",
            }
        )
        self._log(
            "self",
            "link_revoked",
            ACTIVITY_ENTITY_LINK,
            int(link["id"]),
            str(link["player_name"]),
            note="Unlinked by the member from their account page",
        )
        self._notify(
            community_user_id,
            "hcr2_link_revoked",
            "You unlinked your HCR2 player name from your community profile.",
        )
        return {"link": revoked}

    # -- admin --------------------------------------------------------------

    def list_requests(
        self,
        *,
        status: str | None,
        method: str | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        self.repository.expire_stale_requests()
        if method is not None and method not in VALID_METHODS:
            method = None
        requests, total = self.repository.list_admin_requests(
            status=status,
            method=method,
            search=(search or "").strip()[:50] or None,
            limit=limit,
            offset=offset,
        )
        return {
            "requests": [_admin_request_view(request) for request in requests],
            "count": total,
            "limit": limit,
            "offset": offset,
            "status": status,
            "method": method,
        }

    def get_request_detail(self, request_id: int) -> dict[str, Any] | None:
        request = self.repository.get_request(request_id)
        if request is None:
            return None
        history = self.repository.list_request_history(
            community_user_id=int(request["community_user_id"]),
            player_name_norm=str(request["player_name_norm"]),
        )
        return {
            "request": _admin_request_view(request),
            "steps": [
                _admin_step_view(step) for step in self.repository.list_request_steps(request_id)
            ],
            "history": [_admin_history_view(row) for row in history],
            "conflicts": self.repository.find_conflicts(str(request["player_name_norm"])),
        }

    def _require_submitted(self, request_id: int) -> dict[str, Any]:
        request = self.repository.get_request(request_id)
        if request is None:
            raise CommunityProfileError("Request not found.", 404)
        if request["status"] != STATUS_SUBMITTED:
            raise CommunityProfileError(
                "Only a submitted request can be reviewed.",
                409,
            )
        return request

    def approve_request(
        self,
        request_id: int,
        *,
        admin_username: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        request = self._require_submitted(request_id)
        # Revalidated a third time, at the moment of approval: the record may
        # have been deleted, or the name claimed by someone else in between.
        self._resolve_eligible_player(str(request["player_name"]))

        try:
            link = self.repository.approve_request(
                {
                    "request_id": request_id,
                    "community_user_id": int(request["community_user_id"]),
                    "player_id": int(request["player_id"]),
                    "player_name": request["player_name"],
                    "player_name_norm": request["player_name_norm"],
                    "verification_method": request["verification_method"],
                    "requested_at": request.get("submitted_at"),
                    "admin_username": admin_username,
                    "note": (note or "").strip() or None,
                }
            )
        except ActiveLinkConflictError:
            raise CommunityProfileError(NAME_TAKEN_ERROR, 409) from None

        if link is None:
            raise CommunityProfileError("Request not found.", 404)

        self._log(
            admin_username,
            "request_approved",
            ACTIVITY_ENTITY_REQUEST,
            request_id,
            str(request["player_name"]),
            note=note,
        )
        self._notify(
            int(request["community_user_id"]),
            "hcr2_link_approved",
            f"Your HCR2 player name {link['player_name']} was verified by an admin.",
        )
        return {"link": link}

    def reject_request(
        self,
        request_id: int,
        *,
        admin_username: str,
        category: str,
        reason: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        if category not in REJECTION_CATEGORIES:
            raise CommunityProfileError("Unknown rejection category.")
        clean_reason = (reason or "").strip()
        if not clean_reason:
            raise CommunityProfileError("Please give the user a reason.")
        if len(clean_reason) > 500:
            raise CommunityProfileError("Reason must be at most 500 characters.")

        request = self._require_submitted(request_id)
        updated = self.repository.reject_request(
            {
                "request_id": request_id,
                "admin_username": admin_username,
                "category": category,
                "reason": clean_reason,
                "note": (note or "").strip() or None,
            }
        )
        if updated is None:
            raise CommunityProfileError("Request not found.", 404)
        self._log(
            admin_username,
            "request_rejected",
            ACTIVITY_ENTITY_REQUEST,
            request_id,
            str(request["player_name"]),
            note=f"{category}: {clean_reason}",
        )
        self._notify(
            int(request["community_user_id"]),
            "hcr2_link_rejected",
            "Your HCR2 account linking request was not approved. "
            f"Reason: {clean_reason}",
        )
        return updated

    def request_retry(self, request_id: int, *, admin_username: str, note: str | None = None):
        """Send the request back for another attempt without deciding it."""
        request = self.repository.get_request(request_id)
        if request is None:
            raise CommunityProfileError("Request not found.", 404)
        if request["status"] not in (STATUS_SUBMITTED, STATUS_REJECTED):
            raise CommunityProfileError(
                "Only a submitted or rejected request can be sent back.",
                409,
            )
        updated = self.repository.set_request_status(request_id, STATUS_IN_PROGRESS)
        if updated is None:
            raise CommunityProfileError("Request not found.", 404)
        self._log(
            admin_username,
            "request_retry_requested",
            ACTIVITY_ENTITY_REQUEST,
            request_id,
            str(request["player_name"]),
            note=note,
        )
        self._notify(
            int(request["community_user_id"]),
            "hcr2_link_retry_requested",
            "An admin asked you to try your HCR2 account linking again."
            + (f" Note: {note}" if note else ""),
        )
        return {"request": updated}

    def set_appointment(
        self,
        request_id: int,
        *,
        admin_username: str,
        appointment_status: str,
        appointment_at: datetime | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        if appointment_status not in APPOINTMENT_STATUSES:
            raise CommunityProfileError("Unknown appointment status.")
        request = self.repository.get_request(request_id)
        if request is None:
            raise CommunityProfileError("Request not found.", 404)
        if request["verification_method"] != METHOD_DISCORD:
            raise CommunityProfileError(
                "Appointments only apply to the Discord screen share method.",
                409,
            )
        updated = self.repository.set_appointment(
            {
                "request_id": request_id,
                "appointment_status": appointment_status,
                "appointment_at": appointment_at,
                "appointment_note": (note or "").strip() or None,
            }
        )
        if updated is None:
            raise CommunityProfileError("Request not found.", 404)
        self._log(
            admin_username,
            "appointment_updated",
            ACTIVITY_ENTITY_REQUEST,
            request_id,
            str(request["player_name"]),
            note=f"{appointment_status}" + (f" at {appointment_at}" if appointment_at else ""),
        )
        self._notify(
            int(request["community_user_id"]),
            "hcr2_appointment_updated",
            f"Your verification appointment status is now: {appointment_status.replace('_', ' ')}.",
        )
        return updated

    def set_terminal_status(
        self,
        request_id: int,
        *,
        status: str,
        admin_username: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        if status not in (STATUS_CANCELLED, STATUS_EXPIRED):
            raise CommunityProfileError("Unsupported status.")
        request = self.repository.get_request(request_id)
        if request is None:
            raise CommunityProfileError("Request not found.", 404)
        updated = self.repository.set_request_status(request_id, status)
        if updated is None:
            raise CommunityProfileError("Request not found.", 404)
        self._log(
            admin_username,
            f"request_{status}",
            ACTIVITY_ENTITY_REQUEST,
            request_id,
            str(request["player_name"]),
            note=note,
        )
        self._notify(
            int(request["community_user_id"]),
            f"hcr2_link_{status}",
            f"Your HCR2 account linking request was {status} by an admin."
            + (f" Note: {note}" if note else ""),
        )
        return updated

    def list_links(
        self,
        *,
        status: str | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        links, total = self.repository.list_links(
            status=status,
            search=(search or "").strip()[:50] or None,
            limit=limit,
            offset=offset,
        )
        return {
            "links": [_link_view(link) for link in links],
            "count": total,
            "limit": limit,
            "offset": offset,
        }

    def set_link_status(
        self,
        link_id: int,
        *,
        status: str,
        admin_username: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        if status not in ("active", "revoked", "suspended"):
            raise CommunityProfileError("Unsupported link status.")
        link = self.repository.get_link(link_id)
        if link is None:
            raise CommunityProfileError("Link not found.", 404)
        if status != "active":
            clean_reason = (reason or "").strip()
            if not clean_reason:
                raise CommunityProfileError("Please give a reason for changing the link.")
            if len(clean_reason) > 500:
                raise CommunityProfileError("Reason must be at most 500 characters.")
        else:
            clean_reason = None

        updated = self.repository.set_link_status(
            {
                "link_id": link_id,
                "status": status,
                "revoked_at": _naive_utc() if status != "active" else None,
                "revoked_by_admin": admin_username if status != "active" else "",
                "revocation_reason": clean_reason,
            }
        )
        if updated is None:
            raise CommunityProfileError("Link not found.", 404)
        self._log(
            admin_username,
            f"link_{status}",
            ACTIVITY_ENTITY_LINK,
            link_id,
            str(link["player_name"]),
            note=clean_reason,
        )
        message = {
            "revoked": "An admin revoked the HCR2 player name linked to your profile.",
            "suspended": "An admin suspended the HCR2 player name linked to your profile.",
            "active": "An admin restored the HCR2 player name linked to your profile.",
        }[status]
        self._notify(
            int(link["community_user_id"]),
            f"hcr2_link_{status}",
            message + (f" Reason: {clean_reason}" if clean_reason else ""),
        )
        return {"link": updated}

    def find_conflicts(self, player_name: str) -> dict[str, Any]:
        return self.repository.find_conflicts(player_name_key(player_name or ""))


def _seconds_since(value: Any) -> int:
    moment = _as_naive(value)
    if moment is None:
        return 0
    return max(int((_naive_utc() - moment).total_seconds()), 0)