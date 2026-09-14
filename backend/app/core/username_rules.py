"""Centralized community username rules: normalization, validation and moderation.

The reserved/profanity lists live here so they can be extended in one place.
Validation is server-side only; the frontend mirrors the format rules for UX,
but the backend is the source of truth.
"""

import re

MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 20

GENERIC_UNAVAILABLE = "This username isn't available. Please choose another one."

# Whitelist: letters, numbers, spaces, "-" and "_".
_USERNAME_RE = re.compile(r"^[A-Za-z0-9 _\-]+$")
_WHITESPACE_RE = re.compile(r"\s+")

# Exact normalized matches (trimmed, lowercased) are blocked. The list is
# intentionally conservative; add reserved/impersonation-related names here.
RESERVED_NAMES = frozenset(
    """
    admin administrator mod moderator staff support
    hcr2 hcr2xyz hcr2records hcr2adventure hrc2 hillclimbracing
    hill-climb-racing hcr2-records hillclimb hcr hrc records
    fingersoft official verified verified-user
    system root owner developer developer-hcr2
    help helpdesk contact info team team-admin
    guest visitor host server banned blocked
    """.split()
)

# Additional blocked matches without spaces/separators (e.g. "hcr2xyz").
_RESERVED_NAMES_COMPACT = frozenset(
    name.replace(" ", "").replace("-", "").replace("_", "").lower()
    for name in RESERVED_NAMES
)

# Profanity/offensive words. Matched as a substring of the compacted
# (no spaces/separators) normalized username, so spacing tricks won't bypass it.
PROFANITY_TERMS = frozenset(
    """
    fuck shit bitch cunt dick pussy asshole ass wipe
    nigger nigga faggot fag homo retard retarded
    whore slut bastard scumbag nazi kkk
    """.split()
)


class UsernameValidationError(Exception):
    """Raised when a username fails format/length rules (specific message)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UsernameModerationError(UsernameValidationError):
    """Raised when a username is blocked by reserved/profanity rules.

    The caller should surface only a generic unavailable message.
    """


def normalize_username(raw: str) -> str:
    """Trim whitespace and collapse consecutive spaces."""

    return _WHITESPACE_RE.sub(" ", (raw or "").strip())


def _norm(raw: str) -> str:
    return normalize_username(raw).lower()


def _compact(value: str) -> str:
    return _WHITESPACE_RE.sub("", value).replace("_", "").replace("-", "")


def is_reserved(username_norm: str) -> bool:
    return username_norm in RESERVED_NAMES or _compact(username_norm) in _RESERVED_NAMES_COMPACT


def is_blocked(username_norm: str) -> bool:
    compact = _compact(username_norm)
    return any(term in compact for term in PROFANITY_TERMS)


def validate_username(raw: str) -> str:
    """Validate and return the normalized display username.

    Raises UsernameModerationError for reserved/profanity (generic message)
    and UsernameValidationError for format/length problems (specific message).
    """

    value = normalize_username(raw)
    if not value:
        raise UsernameValidationError("Please enter a username.")
    if len(value) < MIN_USERNAME_LENGTH or len(value) > MAX_USERNAME_LENGTH:
        raise UsernameValidationError(
            f"Username must be {MIN_USERNAME_LENGTH}-{MAX_USERNAME_LENGTH} characters."
        )
    if not _USERNAME_RE.match(value):
        raise UsernameValidationError(
            "Username may only contain letters, numbers, spaces, \"-\" and \"_\"."
        )
    username_norm = _norm(value)
    if is_reserved(username_norm) or is_blocked(username_norm):
        raise UsernameModerationError(GENERIC_UNAVAILABLE)
    return value


def username_key(raw: str) -> str:
    """Normalized form used for case-insensitive uniqueness."""

    return _norm(raw)