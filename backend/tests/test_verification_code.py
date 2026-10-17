from app.core.verification_code import (
    CODE_DELIMITER,
    DEFAULT_TOKEN_LENGTH,
    TOKEN_ALPHABET,
    build_code,
    contains_censor_character,
    format_token,
    generate_token,
    hash_token,
    normalize_player_name,
    player_name_key,
    split_code,
    verify_token,
)


def test_token_alphabet_excludes_ambiguous_and_delimiter_characters() -> None:
    # I/O/0/1 are dropped so a mistyped or autocorrected code cannot turn into
    # a different valid token. Punctuation is dropped so the ":" delimiter can
    # never appear inside a token.
    assert set(TOKEN_ALPHABET) & set("IO01") == set()
    assert set(TOKEN_ALPHABET) & set(":-_ .,|()") == set()
    assert CODE_DELIMITER not in TOKEN_ALPHABET
    assert len(set(TOKEN_ALPHABET)) == len(TOKEN_ALPHABET)


def test_generated_tokens_are_unpredictable_and_well_formed() -> None:
    tokens = {generate_token() for _ in range(200)}

    assert len(tokens) == 200
    for token in tokens:
        assert len(token) == DEFAULT_TOKEN_LENGTH
        assert set(token) <= set(TOKEN_ALPHABET)


def test_generate_token_rejects_non_positive_length() -> None:
    import pytest

    with pytest.raises(ValueError):
        generate_token(0)


def test_format_token_groups_into_fours() -> None:
    assert format_token("K7M4X9Q2") == "K7M4-X9Q2"


def test_build_code_uses_the_documented_example_shape() -> None:
    assert build_code("PlayerName", "K7M4X9Q2") == "PlayerName:K7M4-X9Q2"


def test_split_code_round_trips_a_simple_name() -> None:
    parsed = split_code("PlayerName:K7M4-X9Q2")

    assert parsed is not None
    assert parsed.player_name == "PlayerName"
    assert parsed.token == "K7M4X9Q2"


def test_split_code_handles_names_with_spaces_and_unicode() -> None:
    parsed = split_code("Ørn Bø 玩家:K7M4-X9Q2")

    assert parsed is not None
    assert parsed.player_name == "Ørn Bø 玩家"
    assert parsed.token == "K7M4X9Q2"


def test_split_code_is_unambiguous_when_the_name_contains_the_delimiter() -> None:
    # "A:B" contains the delimiter, so a naive split(":") would read the player
    # name as "A" and the token as "B:XXXX-XXXX". Splitting from the right and
    # validating the token shape resolves it.
    parsed = split_code("A:B:K7M4-X9Q2")

    assert parsed is not None
    assert parsed.player_name == "A:B"
    assert parsed.token == "K7M4X9Q2"


def test_split_code_handles_names_with_punctuation() -> None:
    parsed = split_code("f(u)c(k)|x_1:K7M4-X9Q2")

    assert parsed is not None
    assert parsed.player_name == "f(u)c(k)|x_1"
    assert parsed.token == "K7M4X9Q2"


def test_split_code_rejects_malformed_input() -> None:
    assert split_code("") is None
    assert split_code("NoDelimiterHere") is None
    assert split_code(":K7M4-X9Q2") is None
    assert split_code("Name:") is None
    assert split_code("Name:K7M4-X9") is None
    # Characters outside the alphabet are refused, including lowercase and the
    # censored asterisk HCR2's automoderation inserts.
    assert split_code("Name:k7m4-x9q2") is None
    assert split_code("Name:****-****") is None
    assert split_code("Name:K7M4-X9Q2-EXTRA") is None
    assert split_code(None) is None  # type: ignore[arg-type]


def test_contains_censor_character_matches_asterisk() -> None:
    assert contains_censor_character("Pl***r") is True
    assert contains_censor_character("Player:K7M4-X9Q2") is False
    assert contains_censor_character("") is False


def test_player_name_key_is_case_and_whitespace_insensitive() -> None:
    # player.name_player is UNIQUE case-sensitively, so "Bob" and "bob" are two
    # rows. The link key must fold them together so only one can ever be active.
    assert player_name_key("Bob") == player_name_key("bob")
    assert player_name_key("  Bob   Smith ") == player_name_key("Bob Smith")
    assert player_name_key("Bob") != player_name_key("Bobby")


def test_normalize_player_name_collapses_internal_whitespace() -> None:
    assert normalize_player_name("  Bob\t\nSmith  ") == "Bob Smith"
    assert normalize_player_name("") == ""


def test_hash_token_is_keyed_and_not_reversible() -> None:
    first = hash_token("K7M4X9Q2", "pepper")
    second = hash_token("K7M4X9Q2", "pepper")
    other = hash_token("K7M4X9Q2", "different-pepper")

    assert first == second
    assert first != other
    assert "K7M4X9Q2" not in first
    assert len(first) == 64


def test_hash_token_falls_back_to_unkeyed_sha256_without_a_secret() -> None:
    assert hash_token("K7M4X9Q2", None) == hash_token("K7M4X9Q2", "")


def test_hash_token_rejects_empty_token() -> None:
    import pytest

    with pytest.raises(ValueError):
        hash_token("", "pepper")


def test_verify_token_is_exact() -> None:
    stored = hash_token("K7M4X9Q2", "pepper")

    assert verify_token("K7M4X9Q2", stored, "pepper") is True
    assert verify_token("K7M4X9Q3", stored, "pepper") is False
    assert verify_token("K7M4X9Q2", stored, "wrong-pepper") is False
    assert verify_token("", stored, "pepper") is False
    assert verify_token("K7M4X9Q2", None, "pepper") is False