"""Pure helpers for HCR2 player-name verification codes.

Phase 4 (see ``docs/hcr2-account-linking.md``) has no official Fingersoft API,
so verification is always reviewed by a human. Method A ("join the
verification team") asks the user to paste a code into the team's in-game
chat; an administrator then reads that chat and compares the code against the
one shown in the admin review queue.

Because the code is typed by hand into a game client it has to survive
autocorrect, and because the player name is arbitrary database text the
separator has to be unambiguous even when the name contains the separator
character itself. The format below handles both:

    <exact player name>:<8 char token, grouped as XXXX-XXXX>

* The token alphabet deliberately omits ``I``, ``O``, ``0`` and ``1`` so a
  mistyped or autocorrected character cannot produce a different valid token.
* The token alphabet also omits every punctuation character, including the
  ``:`` delimiter, so a token can never contain the delimiter.
* Splitting uses ``rsplit(":", 1)``, so a player name may contain spaces,
  ``:``, Unicode or other punctuation without making the code ambiguous.

Nothing here reads configuration or touches the database; the HMAC pepper is
resolved by the caller and passed in.
"""

import hashlib
import hmac
import secrets
import unicodedata
from dataclasses import dataclass

#: Crockford-style base32. Excludes I, O, 0 and 1 to survive hand-typing and
#: in-game autocorrect, and excludes every delimiter/punctuation character so
#: the ``:`` separator can always be split unambiguously.
TOKEN_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

#: Number of random characters in a token. 31 ** 8 is roughly 40 bits, which is
#: ample for a single-use code that is bound to one authenticated account, one
#: player name, one request, and expires after a configurable short window.
DEFAULT_TOKEN_LENGTH = 8

#: Characters per dash-separated group in the displayed token.
TOKEN_GROUP_SIZE = 4

#: Intra-token separator. Not part of the alphabet, so it can never be confused
#: with a token character.
TOKEN_SEPARATOR = "-"

#: Separator between the exact player name and the random token.
CODE_DELIMITER = ":"

#: Character that HCR2's in-game automoderation substitutes for censored text.
#: Codes containing this character are never accepted as sent.
CENSOR_CHARACTER = "*"


def normalize_player_name(raw: str) -> str:
    """Canonicalize a player name for matching, keying and uniqueness.

    Mirrors ``app.core.username_rules.normalize_username`` (NFKC + collapsed
    whitespace) and then casefolds, because ``player.name_player`` is unique
    case-sensitively in the database: ``Bob`` and ``bob`` are two distinct
    rows. Linking keys and the active-link uniqueness index use this value so
    the two spellings can never both be linked at once.
    """
    value = unicodedata.normalize("NFKC", raw or "").strip()
    return " ".join(value.split())


def player_name_key(raw: str) -> str:
    """Return the case-folded key used for player-name matching."""
    return normalize_player_name(raw).casefold()


def generate_token(length: int = DEFAULT_TOKEN_LENGTH) -> str:
    """Return a cryptographically secure random token of ungrouped characters."""
    if length <= 0:
        raise ValueError("Token length must be positive.")
    return "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(length))


def format_token(token: str) -> str:
    """Group an ungrouped token into ``XXXX-XXXX`` form for display."""
    groups = [
        token[index : index + TOKEN_GROUP_SIZE]
        for index in range(0, len(token), TOKEN_GROUP_SIZE)
    ]
    return TOKEN_SEPARATOR.join(groups)


def build_code(player_name: str, token: str) -> str:
    """Build the full code shown to the user and sent in team chat."""
    return f"{player_name}{CODE_DELIMITER}{format_token(token)}"


@dataclass(frozen=True, slots=True)
class ParsedCode:
    """The two halves of a verification code."""

    player_name: str
    token: str


def split_code(code: str, *, expected_length: int = DEFAULT_TOKEN_LENGTH) -> ParsedCode | None:
    """Split a code back into its player name and token.

    Returns ``None`` for anything that is not a well-formed code: no
    delimiter, an empty name, or a token whose length or characters do not
    match what :func:`generate_token` produces. The token shape is validated
    rather than merely split so a player name containing ``:`` still yields
    exactly one unambiguous reading.
    """
    if not isinstance(code, str):
        return None
    raw_name, delimiter, token_part = code.rpartition(CODE_DELIMITER)
    if not delimiter:
        return None
    name = raw_name.strip()
    if not name:
        return None

    compact = token_part.replace(TOKEN_SEPARATOR, "")
    if len(compact) != expected_length:
        return None
    if any(character not in TOKEN_ALPHABET for character in compact):
        return None
    if token_part.count(TOKEN_SEPARATOR) > 1:
        return None
    if TOKEN_SEPARATOR in token_part and len(token_part.split(TOKEN_SEPARATOR)[0]) != (
        TOKEN_GROUP_SIZE
    ):
        return None
    return ParsedCode(player_name=name, token=compact)


def contains_censor_character(value: str) -> bool:
    """True when HCR2 automoderation is likely to have censored ``value``.

    The team-chat instruction tells the user to reroll if either the player
    name or the token comes back full of asterisks. This backs the same check
    server-side, so a censored name cannot be recorded as a completed request
    without the user having rerolled.
    """
    return CENSOR_CHARACTER in (value or "")


def hash_token(token: str, secret: str | None) -> str:
    """Return a keyed hash of ``token`` for storage in ``code_token_hash``.

    Uses HMAC-SHA256 with ``secret`` as the key so a database dump alone
    cannot be used to confirm a guessed token. When no secret is configured
    the function still returns a stable SHA-256 digest, which keeps local
    development working; production should always configure a secret.
    """
    if not token:
        raise ValueError("Cannot hash an empty token.")
    if secret:
        return hmac.new(secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(token: str, stored_hash: str | None, secret: str | None) -> bool:
    """Constant-time comparison of ``token`` against a stored hash."""
    if not token or not stored_hash:
        return False
    return hmac.compare_digest(hash_token(token, secret), stored_hash)