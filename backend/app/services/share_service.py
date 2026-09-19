from __future__ import annotations

import html
import io
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.db.session import DatabaseConfig, open_connection

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
_FONT_BOLD = _ASSETS_DIR / "fonts" / "DejaVuSans-Bold.ttf"
_FONT_REGULAR = _ASSETS_DIR / "fonts" / "DejaVuSans.ttf"

_SYSTEM_FONT_FALLBACKS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)

_CANVAS_WIDTH = 1200
_CANVAS_HEIGHT = 700

_BG_TOP = (13, 17, 27)
_BG_BOTTOM = (7, 10, 16)
_ACCENT = (95, 232, 255)
_GOLD = (255, 211, 77)
_TEXT = (226, 232, 240)
_MUTED = (148, 163, 184)
_GREEN = (74, 222, 128)
_ORANGE = (251, 146, 60)
_RED = (248, 113, 113)


class RecordNotFound(ValueError):
    pass


def _resolve_font() -> tuple[str, str]:
    bold = _FONT_BOLD if _FONT_BOLD.exists() else _SYSTEM_FONT_FALLBACKS[0]
    regular = _FONT_REGULAR if _FONT_REGULAR.exists() else _SYSTEM_FONT_FALLBACKS[1]
    return str(bold), str(regular)


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _fit_text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    ellipsis: str = "\u2026",
) -> str:
    if draw.textlength(text, font=font) <= max_width:
        return text
    while text and draw.textlength(text + ellipsis, font=font) > max_width:
        text = text[:-1]
    return text + ellipsis if text else ""


def _truncate_parts(parts: list[str], max_items: int = 4) -> str:
    if not parts:
        return ""
    if len(parts) <= max_items:
        return " \u00b7 ".join(parts)
    return " \u00b7 ".join(parts[:max_items]) + " \u2026"


@dataclass(frozen=True, slots=True)
class ShareService:
    config: DatabaseConfig | None = None
    cache_dir: Path | None = None

    def get_record(self, record_id: int) -> dict[str, Any] | None:
        rows = self._fetch_all(
            """
            SELECT
                wr.id_record AS "idRecord",
                wr.distance,
                wr.current,
                wr.is_mythic AS "isMythic",
                wr.questionable,
                COALESCE(wr.questionable_reason, '') AS questionable_reason,
                m.name_map AS map_name,
                v.name_vehicle AS vehicle_name,
                p.name_player AS player_name,
                COALESCE(p.country, '') AS player_country,
                string_agg(
                    tp.name_tuning_part, ', ' ORDER BY tp.name_tuning_part
                ) AS tuning_parts,
                echo_part.name_tuning_part AS "echoAffectedPart"
            FROM world_record AS wr
            JOIN map AS m ON wr.id_map = m.id_map
            JOIN vehicle AS v ON wr.id_vehicle = v.id_vehicle
            LEFT JOIN player AS p ON wr.id_player = p.id_player
            LEFT JOIN tuning_setup_part tsp ON wr.id_tuning_setup = tsp.id_tuning_setup
            LEFT JOIN tuning_part tp ON tsp.id_tuning_part = tp.id_tuning_part
            LEFT JOIN tuning_setup ts ON wr.id_tuning_setup = ts.id_tuning_setup
            LEFT JOIN tuning_part echo_part ON ts.echo_affected_part_id = echo_part.id_tuning_part
            WHERE wr.id_record = %(id)s
            GROUP BY wr.id_record, wr.distance, wr.current, wr.is_mythic,
                wr.questionable, wr.questionable_reason,
                m.name_map, v.name_vehicle, p.name_player, p.country,
                echo_part.name_tuning_part
            """,
            {"id": record_id},
        )
        return rows[0] if rows else None

    def share_page(self, record_id: int) -> str:
        row = self.get_record(record_id)
        if row is None:
            raise RecordNotFound(str(record_id))
        distance = self._format_distance(row.get("distance"))
        map_name = str(row.get("map_name") or "")
        vehicle_name = str(row.get("vehicle_name") or "")
        player_name = str(row.get("player_name") or "")
        mythic = bool(row.get("isMythic"))
        questionable = str(row.get("questionable")) == "1"

        title = f"{distance} m \u2014 {map_name} / {vehicle_name}"
        description_parts: list[str] = []
        if player_name:
            description_parts.append(f"Held by {player_name}")
        if mythic:
            description_parts.append("Mythic record")
        if questionable:
            description_parts.append("Questionable run")
        description = " \u00b7 ".join(description_parts) or "HCR2 adventure world record"

        safe_title = html.escape(title, quote=True)
        safe_description = html.escape(description, quote=True)
        safe_url = html.escape(f"/api/v1/share/records/{record_id}", quote=True)
        safe_image = html.escape(f"/api/v1/share/records/{record_id}.png", quote=True)
        target = html.escape(f"/records?map={map_name}&vehicle={vehicle_name}", quote=True)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{safe_title}</title>
<meta property="og:type" content="website">
<meta property="og:title" content="{safe_title}">
<meta property="og:description" content="{safe_description}">
<meta property="og:url" content="{safe_url}">
<meta property="og:image" content="{safe_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="700">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{safe_title}">
<meta name="twitter:description" content="{safe_description}">
<meta name="twitter:image" content="{safe_image}">
<script>window.location.replace('{target}');</script>
</head>
<body>
<p><a href="{target}">hcr2.xyz \u2014 {safe_title}</a></p>
</body>
</html>"""

    def og_image(self, record_id: int) -> bytes:
        row = self.get_record(record_id)
        if row is None:
            raise RecordNotFound(str(record_id))

        cache_dir = self.cache_dir
        if cache_dir is not None:
            cached = cache_dir / self._cache_filename(record_id, row)
            if cached.exists():
                return cached.read_bytes()

        png = self._render_image(row)

        if cache_dir is not None:
            try:
                cache_dir.mkdir(parents=True, exist_ok=True)
                target = cache_dir / self._cache_filename(record_id, row)
                target.write_bytes(png)
            except OSError:
                pass

        return png

    def _cache_filename(self, record_id: int, row: dict[str, Any]) -> str:
        fingerprint = self._fingerprint(row)
        return f"{record_id}.{fingerprint}.png"

    @staticmethod
    def _fingerprint(row: dict[str, Any]) -> str:
        values = (
            "v2-700px-canvas",
            str(row.get("distance")),
            str(row.get("vehicle_name") or ""),
            str(row.get("player_name") or ""),
            str(row.get("player_country") or ""),
            "1" if row.get("isMythic") else "0",
            "1" if str(row.get("questionable")) == "1" else "0",
            str(row.get("questionable_reason") or ""),
            str(row.get("tuning_parts") or ""),
            str(row.get("echoAffectedPart") or ""),
        )
        return sha1("|".join(values).encode("utf-8")).hexdigest()[:12]

    def _render_image(self, row: dict[str, Any]) -> bytes:
        bold_path, regular_path = _resolve_font()
        font_hero = _load_font(bold_path, 96)
        font_h1 = _load_font(bold_path, 56)
        font_sub = _load_font(bold_path, 30)
        font_body = _load_font(regular_path, 28)
        font_label = _load_font(bold_path, 22)
        font_small = _load_font(bold_path, 18)

        image = self._gradient(_CANVAS_WIDTH, _CANVAS_HEIGHT, _BG_TOP, _BG_BOTTOM)
        draw = ImageDraw.Draw(image)

        draw.text((64, 42), "hcr2.xyz", font=font_sub, fill=_ACCENT)

        distance = self._format_distance(row.get("distance"))
        draw.text((64, 150), distance, font=font_hero, fill=_GOLD)
        draw.text((64, 262), "METERS", font=font_label, fill=_MUTED)

        draw.line((64, 330, _CANVAS_WIDTH - 64, 330), fill=(38, 46, 61), width=2)

        y = 372
        draw.text((64, y), "MAP", font=font_label, fill=_MUTED)
        map_text = _fit_text_width(
            draw, str(row.get("map_name") or "\u2014"), font_h1, _CANVAS_WIDTH - 128
        )
        draw.text((64, y + 32), map_text, font=font_h1, fill=_TEXT)
        y += 150
        draw.text((64, y), "VEHICLE", font=font_label, fill=_MUTED)
        vehicle_text = _fit_text_width(
            draw, str(row.get("vehicle_name") or "\u2014"), font_body, _CANVAS_WIDTH - 128
        )
        draw.text((64, y + 32), vehicle_text, font=font_body, fill=_TEXT)
        y += 72
        country_raw = str(row.get("player_country") or "").strip()
        country_text = f"({country_raw})" if country_raw else ""
        player_line = str(row.get("player_name") or "\u2014")
        if country_text:
            player_line = f"{player_line} {country_text}"
        draw.text((64, y), "PLAYER", font=font_label, fill=_MUTED)
        draw.text(
            (64, y + 30),
            _fit_text_width(draw, player_line, font_body, _CANVAS_WIDTH - 700),
            font=font_body,
            fill=_TEXT,
        )

        parts = [p.strip() for p in str(row.get("tuning_parts") or "").split(",") if p.strip()]
        metadata = " \u00b7 ".join(
            filter(
                bool,
                [
                    _truncate_parts(parts),
                    f"Echo \u2192 {row.get('echoAffectedPart')}"
                    if row.get("echoAffectedPart")
                    else "",
                ],
            )
        )
        if metadata:
            draw.text(
                (64, y + 72),
                _fit_text_width(draw, metadata, font_small, _CANVAS_WIDTH - 700),
                font=font_small,
                fill=_MUTED,
            )

        self._draw_badge(draw, row, bold_path)

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def _gradient(
        width: int,
        height: int,
        top: tuple[int, int, int],
        bottom: tuple[int, int, int],
    ) -> Image.Image:
        image = Image.new("RGB", (width, height))
        for y in range(height):
            ratio = y / max(height - 1, 1)
            color = tuple(
                int(top_channel + (bottom_channel - top_channel) * ratio)
                for top_channel, bottom_channel in zip(top, bottom, strict=True)
            )
            image.paste(color, (0, y, width, y + 1))
        return image

    @staticmethod
    def _badge(row: dict[str, Any]) -> dict[str, Any] | None:
        if row.get("isMythic"):
            return {"label": "MYTHIC", "color": _GOLD, "fill": (46, 40, 8), "outline": _GOLD}
        if str(row.get("questionable")) == "1":
            return {
                "label": "QUESTIONABLE",
                "color": _ORANGE,
                "fill": (46, 30, 10),
                "outline": _ORANGE,
            }
        return {"label": "VERIFIED", "color": _GREEN, "fill": (8, 42, 28), "outline": _GREEN}

    def _draw_badge(
        self,
        draw: ImageDraw.ImageDraw,
        row: dict[str, Any],
        bold_font_path: str,
    ) -> None:
        badge = self._badge(row)
        if badge is None:
            return
        badge_height = 46
        text_font = _load_font(bold_font_path, 24)
        label = badge["label"]
        text_w = draw.textlength(label, font=text_font)
        pad_x = 28
        badge_width = int(text_w) + pad_x * 2
        bx = _CANVAS_WIDTH - 64 - badge_width
        by = 150
        draw.rounded_rectangle(
            (bx, by, bx + badge_width, by + badge_height),
            radius=badge_height // 2,
            fill=badge["fill"],
            outline=badge["outline"],
            width=2,
        )
        draw.text(
            (bx + pad_x, by + (badge_height - 28) / 2),
            label,
            font=text_font,
            fill=badge["color"],
        )

    @staticmethod
    def _format_distance(value: Any) -> str:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return str(value or "")
        return f"{number:,}".replace(",", " ")

    def _fetch_all(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        with open_connection(self.config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or {})
                return [dict(row) for row in cursor.fetchall()]