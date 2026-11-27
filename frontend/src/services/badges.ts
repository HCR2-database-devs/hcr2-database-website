import type {
  BadgeCatalogResponse,
  BadgeHistoryResponse,
  BadgeProfileResponse,
  FeaturedBadge,
  ProgressionSummary,
  XpTransactionResponse
} from "../types/api";
import { fetchJson } from "./api";

function jsonRequest<T>(path: string, method: "POST" | "PATCH" | "PUT", body?: unknown) {
  return fetchJson<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
}

export function getBadgeCatalog(params: {
  category?: string;
  badgeType?: string;
  scope?: "all" | "owned" | "locked";
} = {}) {
  const query = new URLSearchParams();
  if (params.category) query.set("category", params.category);
  if (params.badgeType) query.set("badgeType", params.badgeType);
  if (params.scope) query.set("scope", params.scope);
  const suffix = query.toString();
  return fetchJson<BadgeCatalogResponse>(
    `/api/v1/badges/catalog${suffix ? `?${suffix}` : ""}`
  );
}

export function getBadgeCategories() {
  return fetchJson<{ categories: BadgeCatalogResponse["categories"] }>(
    "/api/v1/badges/categories"
  );
}

export function getBadgeDetail(identifier: string) {
  return fetchJson<BadgeCatalogResponse["badges"][number]>(
    `/api/v1/badges/detail/${encodeURIComponent(identifier)}`
  );
}

export function getMemberBadges(userId: number) {
  return fetchJson<BadgeProfileResponse>(`/api/v1/badges/members/${userId}`);
}

export function getOwnFeaturedBadges() {
  return fetchJson<{ featured: FeaturedBadge[] }>("/api/v1/badges/me/featured");
}

export function setOwnFeaturedBadges(badgeIds: number[]) {
  return jsonRequest<{ featured: FeaturedBadge[] }>("/api/v1/badges/me/featured", "PUT", {
    badge_ids: badgeIds
  });
}

export function getAdminBadgeDefinitions(includeAdmin = true) {
  return fetchJson<{ badges: BadgeCatalogResponse["badges"]; categories: BadgeCatalogResponse["categories"] }>(
    `/api/v1/badges/admin/definitions?include_admin=${includeAdmin}`
  );
}

export function createBadgeDefinition(payload: Record<string, unknown>) {
  return jsonRequest<Record<string, unknown>>("/api/v1/badges/admin/definitions", "POST", payload);
}

export function updateBadgeDefinition(badgeId: number, payload: Record<string, unknown>) {
  return jsonRequest<Record<string, unknown>>(
    `/api/v1/badges/admin/definitions/${badgeId}`,
    "PATCH",
    payload
  );
}

export function archiveBadgeDefinition(badgeId: number) {
  return jsonRequest<Record<string, unknown>>(
    `/api/v1/badges/admin/definitions/${badgeId}/archive`,
    "POST"
  );
}

export function uploadBadgeIcon(badgeId: number, file: File) {
  const body = new FormData();
  body.append("upload", file);
  return fetchJson<{ icon_path: string }>(
    `/api/v1/badges/admin/definitions/${badgeId}/icon`,
    { method: "POST", body }
  );
}

export function createBadgeCategory(payload: Record<string, unknown>) {
  return jsonRequest<Record<string, unknown>>("/api/v1/badges/admin/categories", "POST", payload);
}

export function updateBadgeCategory(categoryId: number, payload: Record<string, unknown>) {
  return jsonRequest<Record<string, unknown>>(
    `/api/v1/badges/admin/categories/${categoryId}`,
    "PATCH",
    payload
  );
}

export function awardBadge(payload: {
  badge_id?: number;
  badge_identifier?: string;
  user_ids: number[];
  reason?: string;
  public_reason?: string;
}) {
  return jsonRequest<{ awarded_count: number }>("/api/v1/badges/admin/award", "POST", payload);
}

export function revokeBadge(userBadgeId: number, reason: string) {
  return jsonRequest<Record<string, unknown>>(
    `/api/v1/badges/admin/user-badges/${userBadgeId}/revoke`,
    "POST",
    { reason }
  );
}

export function getBadgeHistory(params: {
  communityUserId?: number;
  badgeId?: number;
  limit?: number;
  offset?: number;
} = {}) {
  const query = new URLSearchParams();
  if (params.communityUserId) query.set("community_user_id", String(params.communityUserId));
  if (params.badgeId) query.set("badge_id", String(params.badgeId));
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  return fetchJson<BadgeHistoryResponse>(`/api/v1/badges/admin/history?${query}`);
}

export function getOwnProgression() {
  return fetchJson<ProgressionSummary>("/api/v1/progression/me");
}

export function getMemberProgression(userId: number) {
  return fetchJson<ProgressionSummary>(`/api/v1/progression/members/${userId}`);
}

export function getOwnXpTransactions(limit = 20, offset = 0) {
  return fetchJson<XpTransactionResponse>(
    `/api/v1/progression/me/transactions?limit=${limit}&offset=${offset}`
  );
}

export function getAdminXpTransactions(userId: number, limit = 20, offset = 0) {
  const query = new URLSearchParams({
    community_user_id: String(userId),
    limit: String(limit),
    offset: String(offset)
  });
  return fetchJson<XpTransactionResponse>(`/api/v1/progression/admin/transactions?${query}`);
}

export function adjustXp(userId: number, amount: number, reason: string) {
  return jsonRequest<Record<string, unknown>>(
    `/api/v1/progression/admin/adjust?community_user_id=${userId}`,
    "POST",
    { amount, reason }
  );
}

export function refreshBadges(userId: number) {
  return jsonRequest<{ awarded: unknown[]; revoked: unknown[] }>(
    `/api/v1/progression/admin/refresh/${userId}`,
    "POST"
  );
}
