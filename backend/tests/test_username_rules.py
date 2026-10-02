import pytest

from app.core.username_rules import (
    GENERIC_UNAVAILABLE,
    UsernameModerationError,
    UsernameValidationError,
    find_bad_word,
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


def test_validate_username_accepts_pipe_and_parentheses() -> None:
    for value in (
        "Racer|GT",
        "Racer | GT",
        "|CoolRacer",
        "CoolRacer|",
        "(Cool)Racer",
        "Cool(Racer)",
        "(x)",
        "Racer|GT(2)",
    ):
        assert validate_username(value) == value


def test_validate_username_rejects_characters_adjacent_to_the_allowed_ones() -> None:
    for value in ("Racer[GT]", "Racer{GT}", "Racer<GT>", "Racer\\GT", "Racer/GT"):
        with pytest.raises(UsernameValidationError):
            validate_username(value)


def test_pipe_and_parentheses_are_folded_before_moderation_matching() -> None:
    for value in ("f(u)c(k)", "f|u|c|k", "f(u)c(k)e|r", "sh(i)t", "sh|it"):
        with pytest.raises(UsernameModerationError):
            validate_username(value)


def test_reserved_names_are_still_blocked_when_padded_with_pipes_or_parentheses() -> None:
    for value in ("(admin)", "admin|", "|hcr2|", "(staff)"):
        with pytest.raises(UsernameModerationError):
            validate_username(value)


def test_username_key_keeps_pipe_and_parentheses_distinct() -> None:
    assert username_key("Racer|GT") == "racer|gt"
    assert username_key("(Cool)Racer") == "(cool)racer"


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
    for value in ("Admin", "ADMIN", "Hill Climb Racing", "HCR2 Records", "4dm1n"):
        with pytest.raises(UsernameModerationError):
            validate_username(value)


def test_validate_username_rejects_curated_exact_phrase_and_compound_terms() -> None:
    for value in ("fuck", "f u c k", "ass hole", "piece of shit", "BadFuck", "shithead", "sh1t"):
        with pytest.raises(UsernameModerationError):
            validate_username(value)


def test_validate_username_allows_benign_names_containing_short_words() -> None:
    for value in ("shitzer", "xshitsx", "class", "assassin", "Christian", "Blackbird", "Jewel"):
        assert validate_username(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "fuckyou",
        "fuckoff",
        "dumbshit",
        "cuntface",
        "slutbag",
        "twatface",
        "nazihead",
        "wankyou",
        "faghead",
        "sh1thead",
        "dickwad",
        "bitchplease",
        "bitchhead",
        "niggardick",
    ],
)
def test_validate_username_rejects_profanity_glued_to_other_text(value: str) -> None:
    """Regression: profanity must not slip through by prefix/suffix padding."""
    with pytest.raises(UsernameModerationError):
        validate_username(value)


@pytest.mark.parametrize(
    "value",
    [
        "classic",
        "assistant",
        "passage",
        "Scunthorpe",
        "grape",
        "drape",
        "crape",
        "rapeseed",
        "swank",
        "smartwatch",
        "saltwater",
        "meltwater",
        "nightwatchman",
        "dickens",
        "dickybird",
        "horseshit",
        "chickenshit",
        "mishit",
        "trapeze",
        "yamashita",
        "antofagasta",
        "therapeutic",
        "cameraperson",
        "witwatersrand",
    ],
)
def test_validate_username_allows_names_that_only_embed_a_short_term(value: str) -> None:
    """Substring matching must not reintroduce the Scunthorpe problem."""
    assert validate_username(value) == value


def test_glued_profanity_reports_its_own_category() -> None:
    assert find_bad_word("fuckyou").category == "derived"
    assert find_bad_word("bitchplease").category == "stem"


def test_match_tables_are_precomputed_at_import() -> None:
    """Regression: per-call sorting made the admin username audit unusable."""
    from app.core import username_rules

    assert username_rules._SUBSTRING_FORMS
    assert username_rules._SUBSTRING_LENGTHS
    assert username_rules._EXACT_BY_COMPACT


def test_find_bad_word_is_fast_enough_for_a_full_table_scan() -> None:
    import time

    names = [f"racer_{index}" for index in range(20_000)]
    started = time.monotonic()
    for name in names:
        find_bad_word(name)
    elapsed = time.monotonic() - started
    # The previous implementation needed ~7.5s for this batch. The bound is loose
    # enough to avoid flakiness on a slow machine but still catches a regression
    # to per-call rebuilding of the match tables.
    assert elapsed < 5.0, f"20k find_bad_word calls took {elapsed:.2f}s"


def test_override_bypasses_only_bad_word_matching() -> None:
    assert validate_username("fuck", override_bad_words=True) == "fuck"
    with pytest.raises(UsernameModerationError):
        validate_username("admin", override_bad_words=True)


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


def test_find_bad_word_reports_reviewed_category() -> None:
    assert find_bad_word("piece of shit").category == "phrase"
    assert find_bad_word("BadFuck").category == "compound"
    assert find_bad_word("f u c k").category == "exact"
    assert find_bad_word("shitzer") is None


def test_username_key_is_lowercase_normalized_without_moderation_compaction() -> None:
    assert username_key("  Cool   Racer  ") == "cool racer"
    assert username_key("ADMIN") == "admin"
    assert username_key("F U C K") == "f u c k"
