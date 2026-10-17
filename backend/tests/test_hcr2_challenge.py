"""Tests for the playhcr.com jeep challenge helpers.

The distance draw and the link check are the only parts of method C that are
not a stored claim, so they are tested directly rather than through the wizard.
"""

import pytest

from app.core.hcr2_challenge import (
    CHALLENGE_URL_PREFIX,
    MAX_CHALLENGE_ID_LENGTH,
    MAX_DISTANCE_M,
    MIN_DISTANCE_M,
    normalize_challenge_url,
    random_distance_m,
)


def test_the_accepted_prefix_is_the_challenge_page() -> None:
    assert CHALLENGE_URL_PREFIX == "https://playhcr.com/challenge?id="


def test_random_distance_stays_inside_the_allowed_range() -> None:
    drawn = {random_distance_m() for _ in range(200)}

    assert all(MIN_DISTANCE_M <= value <= MAX_DISTANCE_M for value in drawn)
    # A 2000-value range should not collapse onto one number in 200 draws.
    assert len(drawn) > 1


def test_both_ends_of_the_range_are_reachable() -> None:
    assert random_distance_m(minimum_m=7, maximum_m=7) == 7
    assert all(random_distance_m(minimum_m=5, maximum_m=6) in (5, 6) for _ in range(50))


def test_a_degenerate_range_returns_its_only_value() -> None:
    assert random_distance_m(minimum_m=9, maximum_m=2) == 9


def test_a_valid_link_is_returned_with_its_id() -> None:
    url, challenge_id = normalize_challenge_url(
        "https://playhcr.com/challenge?id=6f1a2b3c4d5e"
    )

    assert url == "https://playhcr.com/challenge?id=6f1a2b3c4d5e"
    assert challenge_id == "6f1a2b3c4d5e"


def test_surrounding_whitespace_and_a_trailing_full_stop_are_trimmed() -> None:
    url, challenge_id = normalize_challenge_url("  https://playhcr.com/challenge?id=abc.  ")

    assert url == "https://playhcr.com/challenge?id=abc"
    assert challenge_id == "abc"


def test_extra_query_parameters_are_kept_as_part_of_the_id() -> None:
    # Nothing after the id is inspected, so the stored id stays exactly what
    # playhcr.com issued rather than being re-assembled here.
    url, challenge_id = normalize_challenge_url("https://playhcr.com/challenge?id=abc&x=1")

    assert url == "https://playhcr.com/challenge?id=abc&x=1"
    assert challenge_id == "abc&x=1"


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        # Wrong scheme.
        "http://playhcr.com/challenge?id=abc",
        # Lookalike host.
        "https://playhcr.com.attacker.example/challenge?id=abc",
        "https://notplayhcr.com/challenge?id=abc",
        # Right host, wrong page.
        "https://playhcr.com/profile/some-player",
        "https://playhcr.com/",
        "https://playhcr.com",
        # Wrong parameter name.
        "https://playhcr.com/challenge?user=abc",
        # No id at all.
        "https://playhcr.com/challenge?id=",
        # The prefix merely appears inside the value.
        "https://evil.example/?next=https://playhcr.com/challenge?id=abc",
        "//playhcr.com/challenge?id=abc",
    ],
)
def test_a_link_that_is_not_a_playhcr_challenge_is_rejected(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_challenge_url(raw)


def test_an_absurdly_long_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        normalize_challenge_url(CHALLENGE_URL_PREFIX + ("a" * (MAX_CHALLENGE_ID_LENGTH + 1)))


def test_an_absurdly_long_link_is_rejected_before_anything_else() -> None:
    with pytest.raises(ValueError):
        normalize_challenge_url(CHALLENGE_URL_PREFIX + ("a" * 600))