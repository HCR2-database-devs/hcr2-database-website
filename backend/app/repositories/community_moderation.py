from typing import Any, Protocol

import psycopg

from app.db.session import DatabaseConfig, open_connection
from app.repositories.community_user import PROFILE_COLUMNS, UsernameConflictError

REPORT_CATEGORIES = (
    "spam",
    "inappropriate_banner",
    "inappropriate_bio",
    "impersonation",
    "harassment",
    "other",
)


class CommunityModerationRepository(Protocol):
    def list_profiles(
        self,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]: ...

    def get_profile(self, user_id: int) -> dict[str, Any] | None: ...

    def admin_update_profile(
        self,
        user_id: int,
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

    def admin_clear_customization(self, user_id: int) -> dict[str, Any] | None: ...

    def set_admin_disabled(self, user_id: int, disabled: bool) -> dict[str, Any] | None: ...

    def admin_set_username(
        self,
        user_id: int,
        username: str,
        username_norm: str,
        admin_username: str,
    ) -> dict[str, Any]: ...

    def admin_reset_username(self, user_id: int, admin_username: str) -> dict[str, Any] | None: ...

    def list_username_history(self, user_id: int) -> list[dict[str, Any]]: ...

    def create_report(
        self,
        target_id: int,
        reporter_id: int,
        category: str,
        reason: str,
    ) -> dict[str, Any] | None: ...

    def list_reports(
        self,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]: ...

    def get_report(self, report_id: int) -> dict[str, Any] | None: ...

    def resolve_report(
        self,
        report_id: int,
        status: str,
        admin_username: str,
        note: str | None,
    ) -> dict[str, Any] | None: ...


class PostgresCommunityModerationRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def list_profiles(
        self,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        where_sql = ""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            where_sql = (
                "WHERE (cu.username_norm ILIKE %(pattern)s ESCAPE '\\'"
                " OR cu.discord_username ILIKE %(pattern)s ESCAPE '\\')"
            )
            params["pattern"] = pattern
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT cu.id, cu.discord_id, cu.username, cu.discord_username,
                           cu.discord_avatar,
                           cu.last_username_change_at, cu.created_at, cu.updated_at,
                           cu.profile_public, cu.admin_disabled,
                           cu.show_discord_username, cu.show_discord_avatar,
                           (SELECT count(*)::int FROM community_profile_report r
                            WHERE r.community_user_id = cu.id AND r.status = 'open') AS open_reports
                    FROM community_user cu
                    {where_sql}
                    ORDER BY cu.created_at DESC, cu.id DESC
                    LIMIT %(limit)s OFFSET %(offset)s
                    """,
                    params,
                )
                profiles = [dict(row) for row in cursor.fetchall()]

                cursor.execute(
                    f"""
                    SELECT count(*)::int AS count
                    FROM community_user cu
                    {where_sql}
                    """,
                    params,
                )
                total = int(cursor.fetchone()["count"])
                return profiles, total

    def get_profile(self, user_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {PROFILE_COLUMNS},
                           (SELECT count(*)::int FROM community_profile_report r
                            WHERE r.community_user_id = community_user.id
                              AND r.status = 'open') AS open_reports
                    FROM community_user
                    WHERE id = %(user_id)s
                    """,
                    {"user_id": user_id},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def admin_update_profile(
        self,
        user_id: int,
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
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %(user_id)s
                    RETURNING {PROFILE_COLUMNS}
                    """,
                    {
                        "user_id": user_id,
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

    def admin_clear_customization(self, user_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE community_user SET
                        bio = '',
                        country = NULL,
                        favorite_vehicle_id = NULL,
                        favorite_map_id = NULL,
                        banner_content = NULL,
                        banner_content_type = NULL,
                        banner_updated_at = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %(user_id)s
                    RETURNING {PROFILE_COLUMNS}
                    """,
                    {"user_id": user_id},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def set_admin_disabled(self, user_id: int, disabled: bool) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE community_user SET
                        admin_disabled = %(disabled)s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %(user_id)s
                    RETURNING {PROFILE_COLUMNS}
                    """,
                    {"user_id": user_id, "disabled": disabled},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def admin_set_username(
        self,
        user_id: int,
        username: str,
        username_norm: str,
        admin_username: str,
    ) -> dict[str, Any]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(
                        f"""
                        UPDATE community_user SET
                            username = %(username)s,
                            username_norm = %(username_norm)s,
                            last_username_change_at = NULL,
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
                    VALUES (%(user_id)s, %(username)s, %(username_norm)s, %(admin_username)s)
                    """,
                    {
                        "user_id": user_id,
                        "username": username,
                        "username_norm": username_norm,
                        "admin_username": admin_username,
                    },
                )
                return dict(row)

    def admin_reset_username(self, user_id: int, admin_username: str) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT username, username_norm FROM community_user WHERE id = %(user_id)s",
                    {"user_id": user_id},
                )
                current = cursor.fetchone()
                if current is None:
                    return None
                cursor.execute(
                    f"""
                    UPDATE community_user SET
                        username = NULL,
                        username_norm = NULL,
                        last_username_change_at = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %(user_id)s
                    RETURNING {PROFILE_COLUMNS}
                    """,
                    {"user_id": user_id},
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                if current["username"]:
                    cursor.execute(
                        """
                        INSERT INTO community_username_history
                            (community_user_id, username, username_norm, changed_by_admin)
                        VALUES (%(user_id)s, %(username)s, %(username_norm)s, %(admin_username)s)
                        """,
                        {
                            "user_id": user_id,
                            "username": current["username"],
                            "username_norm": current["username_norm"],
                            "admin_username": admin_username,
                        },
                    )
                return dict(row)

    def list_username_history(self, user_id: int) -> list[dict[str, Any]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, community_user_id, username, changed_by_admin, changed_at
                    FROM community_username_history
                    WHERE community_user_id = %(user_id)s
                    ORDER BY changed_at DESC, id DESC
                    """,
                    {"user_id": user_id},
                )
                return [dict(row) for row in cursor.fetchall()]

    def create_report(
        self,
        target_id: int,
        reporter_id: int,
        category: str,
        reason: str,
    ) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO community_profile_report
                        (community_user_id, reporter_community_user_id, category, reason)
                    VALUES (%(target_id)s, %(reporter_id)s, %(category)s, %(reason)s)
                    ON CONFLICT (community_user_id, reporter_community_user_id)
                        WHERE status = 'open'
                    DO NOTHING
                    RETURNING id, community_user_id, category, reason, status, created_at
                    """,
                    {
                        "target_id": target_id,
                        "reporter_id": reporter_id,
                        "category": category,
                        "reason": reason,
                    },
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def list_reports(
        self,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        where_sql = ""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            where_sql = "WHERE r.status = %(status)s"
            params["status"] = status
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT r.id, r.community_user_id,
                           COALESCE(cu.username, cu.discord_username) AS target_name,
                           r.reporter_community_user_id,
                           COALESCE(rc.username, rc.discord_username) AS reporter_name,
                           r.category, r.reason, r.status, r.created_at,
                           r.resolved_by, r.resolved_at, r.resolution_note
                    FROM community_profile_report r
                    JOIN community_user cu ON cu.id = r.community_user_id
                    JOIN community_user rc ON rc.id = r.reporter_community_user_id
                    {where_sql}
                    ORDER BY r.created_at DESC, r.id DESC
                    LIMIT %(limit)s OFFSET %(offset)s
                    """,
                    params,
                )
                reports = [dict(row) for row in cursor.fetchall()]

                cursor.execute(
                    f"""
                    SELECT count(*)::int AS count
                    FROM community_profile_report r
                    {where_sql}
                    """,
                    params,
                )
                total = int(cursor.fetchone()["count"])
                return reports, total

    def get_report(self, report_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, community_user_id, reporter_community_user_id,
                           category, reason, status, created_at,
                           resolved_by, resolved_at, resolution_note
                    FROM community_profile_report
                    WHERE id = %(report_id)s
                    """,
                    {"report_id": report_id},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def resolve_report(
        self,
        report_id: int,
        status: str,
        admin_username: str,
        note: str | None,
    ) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE community_profile_report SET
                        status = %(status)s,
                        resolved_by = %(admin_username)s,
                        resolved_at = CURRENT_TIMESTAMP,
                        resolution_note = %(note)s
                    WHERE id = %(report_id)s AND status = 'open'
                    RETURNING id, community_user_id, category, reason, status, created_at,
                              resolved_by, resolved_at, resolution_note
                    """,
                    {
                        "report_id": report_id,
                        "status": status,
                        "admin_username": admin_username,
                        "note": note,
                    },
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None