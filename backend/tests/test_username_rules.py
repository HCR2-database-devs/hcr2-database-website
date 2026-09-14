import pytest

from app.core.username_rules import (
    GENERIC_UNAVAILABLE,
    UsernameModerationError,
    UsernameValidationError,
    is_blocked,
    is_reserved,
    normalize_username,
    username_key,
    validate_username,
)


def test_normalize_username_trims_and_collapses_spaces() -> None:
    assert normalize_username("  Racer   One  ") == "Racer One"
    assert normalize_username("") == ""
    assert normalize_username("   ") == ""


def test_validate_username_accepts_letters_numbers_spaces_separators() -> None:
    for value in ("CoolRacer", "Cool Racer", "Cool-Racer_7", "abc123"):
        assert validate_username(value) == value


def test_validate_username_returns_normalized_value() -> None:
    assert validate_username("  Cool   Racer  ") == "Cool Racer"


def test_validate_username_rejects_empty() -> None:
    for value in ("", "   "):
        with pytest.raises(UsernameValidationError):
            validate_username(value)


def test_validate_username_rejects_too_short_or_long() -> None:
    with pytest.raises(UsernameValidationError):
        validate_username("ab")
    with pytest.raises(UsernameValidationError):
        validate_username("a" * 21)


@pytest.mark.parametrize(
    "value",
    ["https://evil.example", "evil.com", "has@symbol", "double..dots", "uni\u00f6code"],
)
def test_validate_username_rejects_disallowed_characters(value: str) -> None:
    with pytest.raises(UsernameValidationError):
        validate_username(value)


def test_validate_username_rejects_reserved_names() -> None:
    for value in ("admin", "administrator", "mod", "staff", "support", "hcr2"):
        with pytest.raises(UsernameModerationError):
            validate_username(value)


def test_validate_username_rejects_reserved_insensitive_to_case_and_spacing() -> None:
    for value in ("Admin", "ADMIN", "Hill Climb Racing", "HCR2 Records"):
        with pytest.raises(UsernameModerationError):
            validate_username(value)


def test_validate_username_rejects_profanity_substrings() -> None:
    for value in ("shitzer", "BadFuck", "xshitsx"):
        with pytest.raises(UsernameModerationError):
            validate_username(value)


def test_moderation_error_carries_generic_message() -> None:
    with pytest.raises(UsernameModerationError) as exc_info:
        validate_username("admin")
    assert exc_info.value.message == GENERIC_UNAVAILABLE
    assert str(exc_info.value) == GENERIC_UNAVAILABLE


def test_is_reserved_handles_compact_forms() -> None:
    assert is_reserved("admin")
    assert is_reserved("hcr2xyz")
    assert not is_reserved("racer")


def test_is_blocked_finds_terms_within_compacted_string() -> None:
    assert is_blocked("f u c k e r")
    assert not is_blocked("flare")


def test_username_key_is_lowercase_normalized() -> None:
    assert username_key("  Cool   Racer  ") == "cool racer"
    assert username_key("ADMIN") == "admin"