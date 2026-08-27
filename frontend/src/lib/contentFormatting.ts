export const INTERNAL_ROUTES = [
  "/maps",
  "/vehicles",
  "/players",
  "/tuning-parts",
  "/tuning-setups",
  "/records",
  "/records/mythic",
  "/stats",
  "/changelog",
  "/privacy",
  "/terms"
];

export function isInternalPath(href: string): boolean {
  if (!href.startsWith("/")) {
    return false;
  }
  const path = href.split(/[?#]/, 1)[0];
  return INTERNAL_ROUTES.some((route) => path === route || path.startsWith(`${route}/`));
}

export const MENTION_MAP: { label: string; to: string }[] = [
  { label: "maps", to: "/maps" },
  { label: "vehicles", to: "/vehicles" },
  { label: "players", to: "/players" },
  { label: "tuning", to: "/tuning-parts" },
  { label: "tuning parts", to: "/tuning-parts" },
  { label: "setups", to: "/tuning-setups" },
  { label: "tuning setups", to: "/tuning-setups" },
  { label: "records", to: "/records" },
  { label: "mythic", to: "/records/mythic" },
  { label: "mythic records", to: "/records/mythic" },
  { label: "stats", to: "/stats" },
  { label: "statistics", to: "/stats" },
  { label: "changelog", to: "/changelog" },
  { label: "privacy", to: "/privacy" },
  { label: "privacy policy", to: "/privacy" },
  { label: "terms", to: "/terms" },
  { label: "terms of service", to: "/terms" }
];

export function mentionTarget(raw: string): string | undefined {
  return MENTION_MAP.find((entry) => entry.label === raw.trim().toLowerCase())?.to;
}