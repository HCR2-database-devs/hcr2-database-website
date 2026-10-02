import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 20

GENERIC_UNAVAILABLE = "This username isn't available. Please choose another one."

# Whitelist: letters, numbers, spaces, "-", "_", "|" and "()" .
# "(" and ")" are literal inside a character class, and so is "|".
# Moderation still folds these to separators via _MODERATION_SEPARATOR_RE,
# so "f(u)c(k)" is caught by the exact-term matcher.
_USERNAME_RE = re.compile(r"^[A-Za-z0-9 _\-()|]+$")
_WHITESPACE_RE = re.compile(r"\s+")
_MODERATION_SEPARATOR_RE = re.compile(r"[^a-z0-9]+")
_TERMS_PATH = Path(__file__).with_name("username_terms.json")
_LEET_TRANSLATION = str.maketrans(
    {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "@": "a",
        "$": "s",
        "!": "i",
    }
)


@dataclass(frozen=True, slots=True)
class UsernameRuleMatch:
    category: str
    term: str


def _load_terms() -> dict[str, frozenset[str]]:
    payload = json.loads(_TERMS_PATH.read_text(encoding="utf-8"))
    return {
        category: frozenset(
            str(value).strip()
            for value in payload.get(category, [])
            if str(value).strip()
        )
        for category in ("exact", "phrase", "compound")
    }


_TERMS = _load_terms()
PROFANITY_TERMS = frozenset().union(*_TERMS.values())
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
_RESERVED_NAMES_COMPACT = frozenset(
    name.replace(" ", "").replace("-", "").replace("_", "").casefold()
    for name in RESERVED_NAMES
)


class UsernameValidationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UsernameModerationError(UsernameValidationError):
    pass


def normalize_username(raw: str) -> str:
    value = unicodedata.normalize("NFKC", raw or "").strip()
    return _WHITESPACE_RE.sub(" ", value)


def _norm(raw: str) -> str:
    return normalize_username(raw).casefold()


def _moderation_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").casefold()
    translated = normalized.translate(_LEET_TRANSLATION)
    return _MODERATION_SEPARATOR_RE.sub(" ", translated).strip()


def _moderation_compact(value: str) -> str:
    return _moderation_text(value).replace(" ", "")


def _term_tokens(value: str) -> tuple[str, ...]:
    return tuple(_moderation_text(value).split())


def _term_compact(value: str) -> str:
    return _moderation_compact(value)


# Terms at least this long are unambiguous enough to match anywhere inside the
# compacted username, so "bastardy" is caught by "bastard". Measured against
# /usr/share/dict/words + en_US.dic: at length 4 this also blocks benign names
# (grape, dickens, swank, smartwatch, saltwater, horseshit), so shorter terms stay
# whole-match only and get their derivatives from the curated affixes below.
_MIN_SUBSTRING_TERM_LENGTH = 5

# Affixes combined with the short (<5 char) and long exact terms to form the
# "derived" category, so "fuckyou" and "dumbshit" are caught. Inflections
# (s/es/er/ing/ed) and short affixes are deliberately absent: adding them blocks
# dickens, trapeze, shitzer and yamashita. Every affix below was checked against
# the system dictionary and contributes zero benign collisions.
_DERIVED_SUFFIXES = frozenset(
    """
    you off up out head face wad bag hole ass less lover
    ish ist es tard
    """.split()
)
_DERIVED_PREFIXES = frozenset(
    """
    dumb bull ass bat crap fuck god piece pussy sex dick
    jack cock butt sucky but face head hole stink
    """.split()
)

# Precomputed once at import. Rebuilding these per call made find_bad_word
# re-sort every list for every username, which dominated the admin audit scan.
_EXACT_BY_COMPACT: dict[str, str] = {}
_PHRASE_MATCHERS: tuple[tuple[str, str], ...] = ()
# Merged substring matcher: term -> match, plus a first-character index so a
# lookup only scans forms that can possibly start where we are.
_SUBSTRING_FORMS: dict[str, UsernameRuleMatch] = {}
_SUBSTRING_LENGTHS: tuple[int, ...] = ()
_SUBSTRING_FIRST: frozenset[str] = frozenset()


def _build_match_tables() -> None:
    global _EXACT_BY_COMPACT, _PHRASE_MATCHERS
    global _SUBSTRING_FORMS, _SUBSTRING_LENGTHS, _SUBSTRING_FIRST

    exact: dict[str, str] = {}
    phrases: list[tuple[str, str]] = []
    for term in _TERMS["phrase"]:
        tokens = " ".join(_term_tokens(term))
        if tokens:
            phrases.append((tokens, term))

    # Curated categories are inserted first so they win the reported category
    # when a form appears in more than one list. All that matters for blocking
    # is that a match exists.
    substring: dict[str, UsernameRuleMatch] = {}
    for term in _TERMS["compound"]:
        compacted = _term_compact(term)
        if compacted:
            substring.setdefault(compacted, UsernameRuleMatch("compound", term))

    derived: set[str] = set()
    for term in _TERMS["exact"]:
        compacted = _term_compact(term)
        if not compacted:
            continue
        # Prefer the longest reviewed spelling when several normalize alike.
        if compacted not in exact or len(term) > len(exact[compacted]):
            exact[compacted] = term
        if len(compacted) >= _MIN_SUBSTRING_TERM_LENGTH:
            substring.setdefault(compacted, UsernameRuleMatch("stem", term))
        for suffix in _DERIVED_SUFFIXES:
            derived.add(compacted + suffix)
        if len(compacted) < _MIN_SUBSTRING_TERM_LENGTH:
            for prefix in _DERIVED_PREFIXES:
                derived.add(prefix + compacted)

    for form in derived:
        if form and form not in substring:
            substring[form] = UsernameRuleMatch("derived", form)

    _EXACT_BY_COMPACT = exact
    _PHRASE_MATCHERS = tuple(sorted(phrases, key=lambda item: len(item[0]), reverse=True))
    _SUBSTRING_FORMS = substring
    _SUBSTRING_LENGTHS = tuple(sorted({len(form) for form in substring}, reverse=True))
    _SUBSTRING_FIRST = frozenset(form[0] for form in substring)


_build_match_tables()


def _substring_match(compact: str) -> UsernameRuleMatch | None:
    """First substring hit, using the first-character index to skip misses."""
    length = len(compact)
    for start in range(length):
        if compact[start] not in _SUBSTRING_FIRST:
            continue
        for size in _SUBSTRING_LENGTHS:
            if size > length - start:
                continue
            found = _SUBSTRING_FORMS.get(compact[start : start + size])
            if found is not None:
                return found
    return None


def _rule_match(value: str) -> UsernameRuleMatch | None:
    tokens = _moderation_text(value)
    compact = tokens.replace(" ", "")

    # Whole-username match. O(1) via the precomputed table.
    whole = _EXACT_BY_COMPACT.get(compact)
    if whole is not None:
        return UsernameRuleMatch("exact", whole)

    padded_tokens = f" {tokens} "
    for phrase_tokens, term in _PHRASE_MATCHERS:
        if f" {phrase_tokens} " in padded_tokens:
            return UsernameRuleMatch("phrase", term)

    return _substring_match(compact)


def find_bad_word(value: str) -> UsernameRuleMatch | None:
    return _rule_match(value)


def is_reserved(username_norm: str) -> bool:
    normalized = _norm(username_norm)
    return (
        normalized in RESERVED_NAMES
        or _moderation_compact(normalized) in _RESERVED_NAMES_COMPACT
    )


def is_blocked(username_norm: str) -> bool:
    return find_bad_word(username_norm) is not None


def validate_username(raw: str, *, override_bad_words: bool = False) -> str:
    value = normalize_username(raw)
    if not value:
        raise UsernameValidationError("Please enter a username.")
    if len(value) < MIN_USERNAME_LENGTH or len(value) > MAX_USERNAME_LENGTH:
        raise UsernameValidationError(
            f"Username must be {MIN_USERNAME_LENGTH}-{MAX_USERNAME_LENGTH} characters."
        )
    if not _USERNAME_RE.match(value):
        raise UsernameValidationError(
            "Username may only contain letters, numbers, spaces, \"-\", \"_\", \"|\" and \"()\"."
        )
    username_norm = _norm(value)
    if is_reserved(username_norm) or (not override_bad_words and is_blocked(username_norm)):
        raise UsernameModerationError(GENERIC_UNAVAILABLE)
    return value


def username_key(raw: str) -> str:
    return _norm(raw)
