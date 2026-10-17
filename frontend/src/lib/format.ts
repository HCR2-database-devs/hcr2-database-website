export function formatMemberSince(iso?: string | null): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString(undefined, { month: "long", year: "numeric" });
}

export function formatDateTime(iso?: string | null): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString();
}

/**
 * Parse a timestamp coming from the API.
 *
 * The database stores `timestamp without time zone` in UTC, so older endpoints
 * serialize a value with no timezone designator at all, e.g.
 * `2026-10-16T13:19:01.313462`. `new Date()` and `Date.parse()` interpret such
 * a string as **local** time, which shifts it by the browser's UTC offset.
 * That is invisible for month-granularity labels but fatal for anything with a
 * countdown in it — a 15 minute code expiry read as local time was already
 * three hours in the past for a UTC+3 browser, so the code appeared expired the
 * moment it was generated.
 *
 * Phase 4 returns explicit UTC (`...Z`), so this mainly protects older
 * endpoints and anything that still round-trips a naive value.
 */
export function parseServerDate(iso?: string | null): Date | null {
  if (!iso) return null;
  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(iso.trim());
  const normalized = hasZone ? iso : `${iso.trim()}Z`;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}