import pytest

from app.services.countries import COUNTRY_CODES, COUNTRY_NAMES, country_name


def test_country_names_cover_the_accepted_code_set() -> None:
    assert set(COUNTRY_NAMES) == set(COUNTRY_CODES)


def test_country_codes_still_accepts_valid_codes() -> None:
    for code in ("fi", "us", "in", "de", "gb", "br", "jp"):
        assert code in COUNTRY_CODES


def test_country_codes_still_rejects_invalid_codes() -> None:
    for code in ("zz", "xx", "abc", ""):
        assert code not in COUNTRY_CODES


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("fi", "Finland"),
        ("us", "United States"),
        ("in", "India"),
        ("de", "Germany"),
        ("gb", "United Kingdom"),
        ("br", "Brazil"),
        ("jp", "Japan"),
        ("ru", "Russia"),
        ("za", "South Africa"),
        ("kr", "South Korea"),
    ],
)
def test_country_name_resolves(code: str, expected: str) -> None:
    assert country_name(code) == expected


def test_country_name_is_case_insensitive() -> None:
    assert country_name("FI") == "Finland"
    assert country_name("Fi") == "Finland"


def test_country_name_falls_back_to_uppercased_code() -> None:
    """An unrecognised code must still render something readable."""
    assert country_name("zz") == "ZZ"


def test_country_name_returns_none_for_empty_input() -> None:
    assert country_name(None) is None
    assert country_name("") is None


def test_every_name_is_non_empty_and_title_case() -> None:
    for code, name in COUNTRY_NAMES.items():
        assert name, f"{code} has an empty name"
        assert name == name.strip(), f"{code} name has stray whitespace"
        assert name[0].isupper(), f"{code} name is not capitalised: {name}"


def test_country_list_has_expected_size() -> None:
    assert len(COUNTRY_NAMES) == 250