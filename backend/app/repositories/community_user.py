from typing import Any, Protocol

import psycopg

from app.db.session import DatabaseConfig, open_connection

PROFILE_COLUMNS = """
    id, discord_id, discord_username, discord_avatar,
    username, last_username_change_at,
    created_at, updated_at,
    bio, country,
    favorite_vehicle_id,
    (SELECT v.name_vehicle FROM vehicle v WHERE v.id_vehicle = community_user.favorite_vehicle_id)
        AS favorite_vehicle_name,
    favorite_map_id,
    (SELECT m.name_map FROM map m WHERE m.id_map = community_user.favorite_map_id)
        AS favorite_map_name,
    profile_public, show_country, show_bio, show_favorite_vehicle, show_favorite_map,
    show_discord_username, show_discord_avatar,
    admin_disabled, banner_content_type, banner_updated_at
"""

_SORT_CLAUSES = {
    "name": "COALESCE(cu.username_norm, '') ASC, cu.id ASC",
    "active": "cu.updated_at DESC, cu.id DESC",
    "new": "cu.created_at DESC, cu.id DESC",
}


class UsernameConflictError(Exception):
    """Raised when a username uniqueness conflict is detected."""


class CommunityUserRepository(Protocol):
    def get_by_discord_id(self, discord_id: str) -> dict[str, Any] | None: ...

    def get_by_id(self, user_id: int) -> dict[str, Any] | None: ...

    def ensure_account(
        self,
        discord_id: str,
        discord_username: str,
        discord_avatar: str | None,
    ) -> dict[str, Any]: ...

    def favorite_names(
        self,
        vehicle_id: int | None,
        map_id: int | None,
    ) -> tuple[str | None, str | None]: ...

    def set_username(
        self,
        user_id: int,
        username: str,
        username_norm: str,
    ) -> dict[str, Any]: ...

    def update_profile(
        self,
        discord_id: str,
        *,
        bio: str,
        country: str | None,
        favorite_vehicle_id: int | None,
        favorite_map_id: int | None,
        profile_public: bool,
        show_country: bool,
        show_bio: bool,
        show_favorite_vehicle: bool,
        show_favorite_map: bool,
        show_discord_username: bool,
        show_discord_avatar: bool,
    ) -> dict[str, Any] | None: ...

    def update_banner(
        self,
        discord_id: str,
        content: bytes,
        content_type: str,
    ) -> dict[str, Any] | None: ...

    def clear_banner(self, discord_id: str) -> dict[str, Any] | None: ...

    def get_banner(self, user_id: int) -> dict[str, Any] | None: ...

    def list_members(
        self,
        *,
        search: str | None,
        sort: str,
        country: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]: ...


def _escape_like(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _public_filters(country: str | None, search: str | None) -> tuple[str, dict[str, Any]]:
    clauses = [
        "cu.profile_public = TRUE",
        "cu.admin_disabled = FALSE",
        "cu.username IS NOT NULL",
    ]
    params: dict[str, Any] = {}
    if country:
        clauses.append("cu.country = %(country)s")
        params["country"] = country
    if search:
        clauses.append("cu.username_norm ILIKE %(pattern)s ESCAPE '\\'")
        params["pattern"] = _escape_like(search)
    return " AND ".join(clauses), params


class PostgresCommunityUserRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def get_by_discord_id(self, discord_id: str) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {PROFILE_COLUMNS}
                    FROM community_user
                    WHERE discord_id = %(discord_id)s
                    """,
                    {"discord_id": discord_id},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def get_by_id(self, user_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {PROFILE_COLUMNS}
                    FROM community_user
                    WHERE id = %(user_id)s
                    """,
                    {"user_id": user_id},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def ensure_account(
        self,
        discord_id: str,
        discord_username: str,
        discord_avatar: str | None,
    ) -> dict[str, Any]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO community_user (discord_id, discord_username, discord_avatar)
                    VALUES (%(discord_id)s, %(discord_username)s, %(discord_avatar)s)
                    ON CONFLICT (discord_id) DO UPDATE SET
                        discord_username = EXCLUDED.discord_username,
                        discord_avatar = EXCLUDED.discord_avatar,
                        updated_at = CASE
                            WHEN community_user.discord_username IS DISTINCT FROM
                                 EXCLUDED.discord_username
                              OR community_user.discord_avatar IS DISTINCT FROM
                                 EXCLUDED.discord_avatar
                            THEN CURRENT_TIMESTAMP
                            ELSE community_user.updated_at
                        END
                    RETURNING {PROFILE_COLUMNS}
                    """,
                    {
                        "discord_id": discord_id,
                        "discord_username": discord_username or "",
                        "discord_avatar": discord_avatar,
                    },
                )
                return dict(cursor.fetchone())

    def favorite_names(
        self,
        vehicle_id: int | None,
        map_id: int | None,
    ) -> tuple[str | None, str | None]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                vehicle_name = None
                map_name = None
                if vehicle_id is not None:
                    cursor.execute(
                        "SELECT name_vehicle FROM vehicle WHERE id_vehicle = %s",
                        (vehicle_id,),
                    )
                    row = cursor.fetchone()
                    vehicle_name = str(row["name_vehicle"]) if row else None
                if map_id is not None:
                    cursor.execute(
                        "SELECT name_map FROM map WHERE id_map = %s",
                        (map_id,),
                    )
                    row = cursor.fetchone()
                    map_name = str(row["name_map"]) if row else None
                return vehicle_name, map_name

    def set_username(
        self,
        user_id: int,
        username: str,
        username_norm: str,
    ) -> dict[str, Any]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(
                        f"""
                        UPDATE community_user SET
                            username = %(username)s,
                            username_norm = %(username_norm)s,
                            last_username_change_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %(user_id)s
                        RETURNING {PROFILE_COLUMNS}
                        """,
                        {
                            "user_id": user_id,
                            "username": username,
                            "username_norm": username_norm,
                        },
                    )
                    row = cursor.fetchone()
                except psycopg.errors.UniqueViolation:
                    raise UsernameConflictError("Username is already taken.") from None
                if row is None:
                    return None
                cursor.execute(
                    """
                    INSERT INTO community_username_history
                        (community_user_id, username, username_norm, changed_by_admin)
                    VALUES (%(user_id)s, %(username)s, %(username_norm)s, '')
                    """,
                    {"user_id": user_id, "username": username, "username_norm": username_norm},
                )
                return dict(row)

    def update_profile(
        self,
        discord_id: str,
        *,
        bio: str,
        country: str | None,
        favorite_vehicle_id: int | None,
        favorite_map_id: int | None,
        profile_public: bool,
        show_country: bool,
        show_bio: bool,
        show_favorite_vehicle: bool,
        show_favorite_map: bool,
        show_discord_username: bool,
        show_discord_avatar: bool,
    ) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE community_user SET
                        bio = %(bio)s,
                        country = %(country)s,
                        favorite_vehicle_id = %(favorite_vehicle_id)s,
                        favorite_map_id = %(favorite_map_id)s,
                        profile_public = %(profile_public)s,
                        show_country = %(show_country)s,
                        show_bio = %(show_bio)s,
                        show_favorite_vehicle = %(show_favorite_vehicle)s,
                        show_favorite_map = %(show_favorite_map)s,
                        show_discord_username = %(show_discord_username)s,
                        show_discord_avatar = %(show_discord_avatar)s,
                        updated_at = CASE
                            WHEN community_user.bio IS DISTINCT FROM %(bio)s
                              OR community_user.country IS DISTINCT FROM %(country)s
                              OR community_user.favorite_vehicle_id IS DISTINCT FROM
                                 %(favorite_vehicle_id)s
                              OR community_user.favorite_map_id IS DISTINCT FROM
                                 %(favorite_map_id)s
                              OR community_user.profile_public IS DISTINCT FROM %(profile_public)s
                              OR community_user.show_country IS DISTINCT FROM %(show_country)s
                              OR community_user.show_bio IS DISTINCT FROM %(show_bio)s
                              OR community_user.show_favorite_vehicle IS DISTINCT FROM
                                 %(show_favorite_vehicle)s
                              OR community_user.show_favorite_map IS DISTINCT FROM
                                 %(show_favorite_map)s
                              OR community_user.show_discord_username IS DISTINCT FROM
                                 %(show_discord_username)s
                              OR community_user.show_discord_avatar IS DISTINCT FROM
                                 %(show_discord_avatar)s
                            THEN CURRENT_TIMESTAMP
                            ELSE community_user.updated_at
                        END
                    WHERE discord_id = %(discord_id)s
                    RETURNING {PROFILE_COLUMNS}
                    """,
                    {
                        "discord_id": discord_id,
                        "bio": bio,
                        "country": country,
                        "favorite_vehicle_id": favorite_vehicle_id,
                        "favorite_map_id": favorite_map_id,
                        "profile_public": profile_public,
                        "show_country": show_country,
                        "show_bio": show_bio,
                        "show_favorite_vehicle": show_favorite_vehicle,
                        "show_favorite_map": show_favorite_map,
                        "show_discord_username": show_discord_username,
                        "show_discord_avatar": show_discord_avatar,
                    },
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def update_banner(
        self,
        discord_id: str,
        content: bytes,
        content_type: str,
    ) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE community_user SET
                        banner_content = %(content)s,
                        banner_content_type = %(content_type)s,
                        banner_updated_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE discord_id = %(discord_id)s
                    RETURNING {PROFILE_COLUMNS}
                    """,
                    {"content": content, "content_type": content_type, "discord_id": discord_id},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def clear_banner(self, discord_id: str) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE community_user SET
                        banner_content = NULL,
                        banner_content_type = NULL,
                        banner_updated_at = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE discord_id = %(discord_id)s
                    RETURNING {PROFILE_COLUMNS}
                    """,
                    {"discord_id": discord_id},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def get_banner(self, user_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT banner_content, banner_content_type, profile_public, admin_disabled,
                           discord_id
                    FROM community_user
                    WHERE id = %(user_id)s
                    """,
                    {"user_id": user_id},
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                banner = dict(row)
                content = banner.get("banner_content")
                if not content or not banner.get("banner_content_type"):
                    return None
                return {
                    "content": bytes(content),
                    "content_type": str(banner["banner_content_type"]),
                    "public": bool(banner["profile_public"]) and not bool(banner["admin_disabled"]),
                    "discord_id": str(banner["discord_id"]),
                }

    def list_members(
        self,
        *,
        search: str | None,
        sort: str,
        country: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        where_sql, params = _public_filters(country, search)
        order_clause = _SORT_CLAUSES.get(sort, _SORT_CLAUSES["new"])
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT cu.id, cu.username, cu.discord_username, cu.discord_avatar,
                           cu.created_at, cu.updated_at, cu.bio, cu.country,
                           cu.favorite_vehicle_id,
                           (SELECT v.name_vehicle FROM vehicle v
                            WHERE v.id_vehicle = cu.favorite_vehicle_id) AS favorite_vehicle_name,
                           cu.favorite_map_id,
                           (SELECT m.name_map FROM map m
                            WHERE m.id_map = cu.favorite_map_id) AS favorite_map_name,
                           cu.show_country, cu.show_bio,
                           cu.show_favorite_vehicle, cu.show_favorite_map,
                           cu.show_discord_username, cu.show_discord_avatar,
                           cu.banner_updated_at
                    FROM community_user cu
                    WHERE {where_sql}
                    ORDER BY {order_clause}
                    LIMIT %(limit)s OFFSET %(offset)s
                    """,
                    {**params, "limit": limit, "offset": offset},
                )
                members = [dict(row) for row in cursor.fetchall()]

                cursor.execute(
                    f"""
                    SELECT count(*)::int AS count
                    FROM community_user cu
                    WHERE {where_sql}
                    """,
                    params,
                )
                total = int(cursor.fetchone()["count"])
                return members, total