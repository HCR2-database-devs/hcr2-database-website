import json
import re
from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import dependencies
from app.core.config import Settings, get_settings
from app.main import create_app
from app.services.community_account_service import CommunityAccountService
from app.services.community_share_service import CommunityShareService, ProfileNotFound

SITE_URL = "https://hcr2.test"
SHARE_PATH = "/api/v1/share/profiles/1"
SHORT_PATH = "/u/1"

_SECTION_TYPE = 9


def _account(**overrides: Any) -> dict[str, Any]:
    account = {
        "id": 1,
        "discord_id": "10001",
        "discord_username": "Name 10001",
        "discord_avatar": "a_1f2e3a",
        "username": "Nick",
        "created_at": datetime(2026, 9, 5, 10, 0, 0),
        "updated_at": datetime(2026, 9, 5, 10, 0, 0),
        "bio": "I love Countryside",
        "country": "fi",
        "favorite_vehicle_id": 3,
        "favorite_vehicle_name": "Sand Rail",
        "favorite_map_id": 7,
        "favorite_map_name": "Countryside",
        "profile_public": True,
        "show_bio": True,
        "show_country": True,
        "show_favorite_vehicle": True,
        "show_favorite_map": True,
        "show_discord_username": True,
        "show_discord_avatar": True,
        "admin_disabled": False,
        "banner_updated_at": None,
    }
    account.update(overrides)
    return account


class StubRepository:
    def __init__(self, account: dict[str, Any] | None) -> None:
        self.account = account

    def get_by_id(self, user_id: int) -> dict[str, Any] | None:
        if self.account is None or self.account["id"] != user_id:
            return None
        return dict(self.account)


def _service(account: dict[str, Any] | None = None) -> CommunityShareService:
    return CommunityShareService(
        community_service=CommunityAccountService(StubRepository(account or _account())),
        site_url=SITE_URL,
    )


def _app(account: dict[str, Any] | None) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(PUBLIC_SITE_URL=SITE_URL)
    app.dependency_overrides[dependencies.get_community_share_service] = (
        lambda: _service(account)
    )
    return TestClient(app)


@pytest.fixture()
def client() -> TestClient:
    return _app(None)


def _parse_embed(page: str) -> dict[str, Any]:
    match = re.search(
        r'<script id="discord:component-embed" type="application/json">(.*?)</script>',
        page,
        re.DOTALL,
    )
    assert match is not None
    # The service escapes "</" so the payload cannot terminate the element early.
    return json.loads(match.group(1).replace("<\\/", "</"))


def _embed(response: Any) -> dict[str, Any]:
    return _parse_embed(response.text)


def test_share_profile_returns_html(client: TestClient) -> None:
    response = client.get(SHARE_PATH)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_share_profile_includes_open_graph_tags(client: TestClient) -> None:
    response = client.get(SHARE_PATH)

    assert '<meta property="og:title" content="Nick · hcr2.xyz">' in response.text
    assert '<meta property="og:url" content="https://hcr2.test/api/v1/share/profiles/1">' in (
        response.text
    )
    assert '<meta property="og:image" content="https://hcr2.test/img/hcrdatabaselogo.png">' in (
        response.text
    )


def test_share_profile_includes_component_embed(client: TestClient) -> None:
    embed = _embed(client.get(SHARE_PATH))

    assert embed["component"]["type"] == 17
    assert embed["component"]["accent_color"] == 0x0F766E


def test_share_profile_embed_contains_username_and_member_since(client: TestClient) -> None:
    embed = _embed(client.get(SHARE_PATH))
    section = embed["component"]["components"][0]
    text = "\n".join(part["content"] for part in section["components"])

    assert "# Nick" in text
    assert "hcr2.xyz #1" in text
    assert "Member since Sep 2026" in text


def test_share_profile_embed_lists_public_details(client: TestClient) -> None:
    embed = _embed(client.get(SHARE_PATH))
    body = str(embed)

    assert "💬 I love Countryside" in body
    assert "🌍 Finland" in body
    assert "🚗 Favorite vehicle: Sand Rail" in body
    assert "🗺 Favorite map: Countryside" in body


def test_share_profile_embed_links_to_profile_and_community(client: TestClient) -> None:
    embed = _embed(client.get(SHARE_PATH))
    row = embed["component"]["components"][-1]

    urls = [button["url"] for button in row["components"]]
    assert urls == ["https://hcr2.test/community/1", "https://hcr2.test/community"]


def test_share_profile_embed_uses_avatar_thumbnail_when_published(client: TestClient) -> None:
    embed = _embed(client.get(SHARE_PATH))
    accessory = embed["component"]["components"][0]["accessory"]

    assert accessory["type"] == 11
    assert accessory["media"]["url"] == (
        "https://cdn.discordapp.com/avatars/10001/a_1f2e3a.gif"
    )


def test_share_profile_embed_falls_back_to_logo_when_avatar_hidden() -> None:
    """A Section requires an accessory; omitting it makes Discord drop the embed."""
    embed = _parse_embed(_service(_account(show_discord_avatar=False)).profile_page(1))
    section = _sections(embed)[0]

    assert section["accessory"]["type"] == 11
    assert section["accessory"]["media"]["url"] == f"{SITE_URL}/img/hcrdatabaselogo.png"


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"show_discord_avatar": False},
        {"show_discord_avatar": False, "discord_avatar": None},
        {"show_discord_avatar": True, "discord_avatar": None},
        {"show_discord_avatar": False, "show_bio": False},
    ],
    ids=["avatar-public", "avatar-hidden", "no-avatar-value", "hidden-and-no-value", "minimal"],
)
def test_every_share_embed_section_carries_an_accessory(overrides: dict[str, Any]) -> None:
    """Regression: Discord rejects the payload if any Section lacks an accessory."""
    embed = _parse_embed(_service(_account(**overrides)).profile_page(1))
    sections = _sections(embed)

    assert sections, "expected at least one Section"
    assert all("accessory" in section for section in sections)


def _sections(embed: dict[str, Any]) -> list[dict[str, Any]]:
    return [c for c in embed["component"]["components"] if c["type"] == _SECTION_TYPE]


def test_share_profile_never_leaks_a_hidden_avatar_into_the_embed() -> None:
    embed = _parse_embed(
        _service(_account(show_discord_avatar=False, discord_avatar="a_1f2e3a")).profile_page(1)
    )

    assert "cdn.discordapp.com" not in json.dumps(embed)


def test_share_profile_renders_country_name_not_code() -> None:
    embed = _parse_embed(_service(_account(country="fi")).profile_page(1))

    assert "🌍 Finland" in json.dumps(embed, ensure_ascii=False)
    assert "🌍 FI" not in json.dumps(embed, ensure_ascii=False)


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
    ],
)
def test_country_names_render_in_the_embed(code: str, expected: str) -> None:
    embed = _parse_embed(_service(_account(country=code)).profile_page(1))

    assert f"🌍 {expected}" in json.dumps(embed, ensure_ascii=False)


def test_unknown_country_code_still_renders_readably() -> None:
    embed = _parse_embed(_service(_account(country="zz")).profile_page(1))

    assert "🌍 ZZ" in json.dumps(embed, ensure_ascii=False)


def test_embed_falls_back_to_logo_when_avatar_hash_is_stale() -> None:
    """A rotated Discord avatar hash 404s; embedding it breaks the card."""
    service = CommunityShareService(
        community_service=CommunityAccountService(StubRepository(_account())),
        site_url=SITE_URL,
        avatar_check=lambda url: False,
    )
    embed = _parse_embed(service.profile_page(1))
    accessory = _sections(embed)[0]["accessory"]

    assert accessory["media"]["url"] == f"{SITE_URL}/img/hcrdatabaselogo.png"


def test_embed_uses_avatar_when_it_still_resolves() -> None:
    service = CommunityShareService(
        community_service=CommunityAccountService(StubRepository(_account())),
        site_url=SITE_URL,
        avatar_check=lambda url: True,
    )
    embed = _parse_embed(service.profile_page(1))

    assert "cdn.discordapp.com" in _sections(embed)[0]["accessory"]["media"]["url"]


def test_avatar_check_runs_only_once_per_url() -> None:
    """Discord's crawler triggers renders; the probe must not stampede the CDN."""
    calls: list[str] = []

    def counting_check(url: str) -> bool:
        calls.append(url)
        return True

    service = CommunityShareService(
        community_service=CommunityAccountService(StubRepository(_account())),
        site_url=SITE_URL,
        avatar_check=counting_check,
    )

    for _ in range(5):
        service.profile_page(1)

    assert len(calls) == 1


def test_avatar_check_failure_falls_back_instead_of_raising() -> None:
    def exploding_check(url: str) -> bool:
        raise RuntimeError("network down")

    service = CommunityShareService(
        community_service=CommunityAccountService(StubRepository(_account())),
        site_url=SITE_URL,
        avatar_check=exploding_check,
    )

    embed = _parse_embed(service.profile_page(1))

    assert _sections(embed)[0]["accessory"]["media"]["url"].endswith(
        "/img/hcrdatabaselogo.png"
    )


def test_service_without_a_probe_assumes_avatar_is_good() -> None:
    embed = _parse_embed(_service().profile_page(1))

    assert "cdn.discordapp.com" in _sections(embed)[0]["accessory"]["media"]["url"]


def test_share_profile_hides_fields_the_member_marked_private() -> None:
    service = _service(
        _account(
            show_bio=False,
            show_country=False,
            show_favorite_vehicle=False,
            show_favorite_map=False,
        )
    )
    page = service.profile_page(1)

    assert "I love Countryside" not in page
    assert "Sand Rail" not in page
    assert "Countryside" not in page


def test_share_profile_hides_discord_username_when_private() -> None:
    service = _service(_account(show_discord_username=False))
    page = service.profile_page(1)

    assert "Name 10001" not in page


def test_share_profile_falls_back_to_generic_description_when_nothing_shared() -> None:
    service = _service(
        _account(
            bio="",
            show_bio=False,
            show_country=False,
            show_favorite_vehicle=False,
            show_favorite_map=False,
        )
    )

    assert 'content="HCR2 community profile"' in service.profile_page(1)


def test_share_profile_rejects_private_profiles() -> None:
    service = _service(_account(profile_public=False))

    with pytest.raises(ProfileNotFound):
        service.profile_page(1)


def test_share_profile_rejects_unnamed_profiles() -> None:
    service = _service(_account(username=None))

    with pytest.raises(ProfileNotFound):
        service.profile_page(1)


def test_share_profile_rejects_admin_disabled_profiles() -> None:
    service = _service(_account(admin_disabled=True))

    with pytest.raises(ProfileNotFound):
        service.profile_page(1)


def test_share_profile_missing_profile_raises() -> None:
    service = CommunityShareService(
        community_service=CommunityAccountService(StubRepository(None)),
        site_url=SITE_URL,
    )

    with pytest.raises(ProfileNotFound):
        service.profile_page(1)


def test_share_profile_endpoint_404s_for_private_profile() -> None:
    assert _app(_account(profile_public=False)).get(SHARE_PATH).status_code == 404


def test_share_profile_endpoint_404s_for_unknown_profile() -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(PUBLIC_SITE_URL=SITE_URL)
    app.dependency_overrides[dependencies.get_community_share_service] = (
        lambda: CommunityShareService(
            community_service=CommunityAccountService(StubRepository(None)),
            site_url=SITE_URL,
        )
    )

    assert TestClient(app).get(SHARE_PATH).status_code == 404


def test_share_profile_redirects_to_the_spa_route(client: TestClient) -> None:
    response = client.get(SHARE_PATH)

    assert "window.location.replace('https://hcr2.test/community/1')" in response.text


def test_share_profile_cannot_break_out_of_the_script_element() -> None:
    """Only ``</script`` ends a script element, so that is what must be escaped."""
    service = _service(_account(bio="</script><script>alert(1)</script>"))
    page = service.profile_page(1)

    payload = page.split('type="application/json">')[1].split("</script>")[0]
    assert "</script" not in payload
    assert "<\\/script>" in payload


def test_share_profile_bio_stays_inside_the_json_payload() -> None:
    """A bio containing HTML is inert: it only ever reaches Discord as JSON."""
    hostile = '"><img src=x onerror=alert(1)>'
    service = _service(_account(bio=hostile))

    embed = _parse_embed(service.profile_page(1))
    body = json.dumps(embed, ensure_ascii=False)

    assert hostile in body
    assert '<meta property="og:description" content="' in service.profile_page(1)


def test_share_profile_truncates_long_bio() -> None:
    service = _service(_account(bio="x" * 5000))
    page = service.profile_page(1)

    assert "…" in page
    assert "x" * 500 not in page


def test_share_profile_collapses_whitespace_in_bio() -> None:
    service = _service(_account(bio="line one\n\n   line two"))
    page = service.profile_page(1)

    assert "line one line two" in page


def test_share_url_strips_trailing_slash_from_site_url() -> None:
    service = CommunityShareService(
        community_service=CommunityAccountService(StubRepository(_account())),
        site_url="https://hcr2.test/",
    )

    assert service.share_url(1) == "https://hcr2.test/api/v1/share/profiles/1"
    assert service.profile_url(1) == "https://hcr2.test/community/1"

def test_short_link_redirects_to_canonical_share_url(client: TestClient) -> None:
    # TestClient follows redirects by default; assert on the hop itself.
    response = client.get(SHORT_PATH, follow_redirects=False)

    assert response.status_code == 301
    assert response.headers["location"] == f"{SITE_URL}/api/v1/share/profiles/1"


def test_short_link_redirect_is_permanent(client: TestClient) -> None:
    assert client.get(SHORT_PATH, follow_redirects=False).status_code == 301


def test_short_link_404s_for_private_profile() -> None:
    assert _app(_account(profile_public=False)).get(SHORT_PATH).status_code == 404


def test_short_link_404s_for_unknown_profile() -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(PUBLIC_SITE_URL=SITE_URL)
    app.dependency_overrides[dependencies.get_community_share_service] = (
        lambda: CommunityShareService(
            community_service=CommunityAccountService(StubRepository(None)),
            site_url=SITE_URL,
        )
    )

    assert TestClient(app).get(SHORT_PATH).status_code == 404


def test_short_link_rejects_zero_id(client: TestClient) -> None:
    assert client.get("/u/0").status_code == 422


def test_canonical_page_is_reachable_after_redirect(client: TestClient) -> None:
    """The redirect target must actually render, or the short link is a dead end."""
    target = client.get(SHORT_PATH, follow_redirects=False).headers["location"]

    assert client.get(target).status_code == 200
