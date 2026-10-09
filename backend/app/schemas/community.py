from datetime import datetime

from pydantic import BaseModel


class CommunityAccount(BaseModel):
    id: int
    discord_id: str
    discord_username: str
    discord_avatar: str | None = None
    username: str | None = None
    last_username_change_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    bio: str = ""
    country: str | None = None
    favorite_vehicle_id: int | None = None
    favorite_vehicle_name: str | None = None
    favorite_map_id: int | None = None
    favorite_map_name: str | None = None
    profile_public: bool = True
    show_country: bool = False
    show_bio: bool = False
    show_favorite_vehicle: bool = False
    show_favorite_map: bool = False
    show_discord_username: bool = False
    show_discord_avatar: bool = False
    admin_disabled: bool = False
    banner_updated_at: datetime | None = None


class CommunityProfileUpdate(BaseModel):
    bio: str = ""
    country: str | None = None
    favorite_vehicle_id: int | None = None
    favorite_map_id: int | None = None
    profile_public: bool = True
    show_country: bool = False
    show_bio: bool = False
    show_favorite_vehicle: bool = False
    show_favorite_map: bool = False
    show_discord_username: bool = False
    show_discord_avatar: bool = False


class UsernameUpdate(BaseModel):
    username: str = ""


class CommunityReportCreate(BaseModel):
    category: str
    reason: str = ""
    h_captcha_response: str = ""


class AdminProfileUpdate(BaseModel):
    bio: str = ""
    country: str | None = None
    favorite_vehicle_id: int | None = None
    favorite_map_id: int | None = None
    profile_public: bool = True
    show_country: bool = False
    show_bio: bool = False
    show_favorite_vehicle: bool = False
    show_favorite_map: bool = False
    show_discord_username: bool = False
    show_discord_avatar: bool = False
    username: str | None = None
    override_bad_words: bool = False
    note: str | None = None


class AdminUsernameRequest(BaseModel):
    username: str = ""
    override_bad_words: bool = False
    note: str | None = None


class AdminNote(BaseModel):
    note: str | None = None