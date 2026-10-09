"""The shared country file is a cross-language contract.

A malformed or drifted shared/countries.json must fail here rather than
silently degrade the embed or the profile page.
"""

import json

import pytest

from app.services import countries as countries_module
from app.services.countries import COUNTRY_CODES, COUNTRY_NAMES, DATA_FILE, country_name


@pytest.fixture(scope="module")
def raw() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def test_shared_file_exists_at_the_expected_path() -> None:
    assert DATA_FILE.is_file(), f"missing shared data file: {DATA_FILE}"
    assert DATA_FILE.name == "countries.json"
    assert DATA_FILE.parent.name == "shared"


def test_shared_file_is_inside_the_repository() -> None:
    assert DATA_FILE.parent.parent.name not in ("app", "backend", "frontend")


def test_shared_file_declares_a_version(raw: dict) -> None:
    assert raw.get("version") == 1


def test_shared_file_documents_its_purpose(raw: dict) -> None:
    assert "$comment" in raw
    comment = raw["$comment"]
    # Must name both consumers, or the next editor edits the wrong file.
    assert "countries.py" in comment
    assert "countries.ts" in comment


def test_every_entry_has_a_two_letter_code_and_a_name(raw: dict) -> None:
    for entry in raw["countries"]:
        assert len(entry["code"]) == 2, entry
        assert entry["code"].islower(), entry
        assert entry["code"].isalpha(), entry
        assert entry["name"].strip(), entry
        assert entry["name"][0].isupper(), entry


def test_codes_are_unique(raw: dict) -> None:
    codes = [entry["code"] for entry in raw["countries"]]
    assert len(codes) == len(set(codes))


def test_names_are_unique(raw: dict) -> None:
    names = [entry["name"] for entry in raw["countries"]]
    assert len(names) == len(set(names))


def test_entries_are_sorted_by_code(raw: dict) -> None:
    codes = [entry["code"] for entry in raw["countries"]]
    assert codes == sorted(codes)


def test_aliases_are_lowercase_and_non_empty(raw: dict) -> None:
    for entry in raw["countries"]:
        for alias in entry.get("aliases", []):
            assert alias, entry
            assert alias == alias.lower(), (entry, alias)
            assert alias != entry["name"].lower(), (entry, alias)


def test_aliases_do_not_collide_across_countries(raw: dict) -> None:
    seen: dict[str, str] = {}
    for entry in raw["countries"]:
        for alias in [entry["name"].lower(), *entry.get("aliases", [])]:
            assert alias not in seen, f"{alias!r} claimed by {seen.get(alias)} and {entry['code']}"
            seen[alias] = entry["code"]


def test_loader_exposes_exactly_the_file_contents(raw: dict) -> None:
    assert set(COUNTRY_NAMES) == {entry["code"] for entry in raw["countries"]}
    assert COUNTRY_CODES == frozenset(COUNTRY_NAMES)


def test_missing_file_raises_a_clear_error(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    countries_module._load.cache_clear()
    monkeypatch.setattr(countries_module, "DATA_FILE", tmp_path / "nope.json")

    with pytest.raises(RuntimeError, match="Country data is missing"):
        countries_module._load()

    countries_module._load.cache_clear()


def test_malformed_file_raises_a_clear_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    bad = tmp_path / "countries.json"
    bad.write_text('{"countries": []}', encoding="utf-8")
    countries_module._load.cache_clear()
    monkeypatch.setattr(countries_module, "DATA_FILE", bad)

    with pytest.raises(RuntimeError, match="malformed"):
        countries_module._load()

    countries_module._load.cache_clear()


def test_country_name_handles_surrounding_whitespace() -> None:
    assert country_name("  fi  ") == "Finland"


def test_country_name_still_falls_back_for_unknown_codes() -> None:
    assert country_name("zz") == "ZZ"
    assert country_name("") is None
    assert country_name(None) is None