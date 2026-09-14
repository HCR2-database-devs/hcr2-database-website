import type {
  CommunityAccount,
  CommunityMember,
  CommunityMemberListResponse,
  CommunityProfileUpdate,
  CommunityReportResult,
  ReportCategory,
  UsernameUpdate
} from "../types/api";
import { fetchJson } from "./api";

export function communityDisplayName(
  profile: Pick<CommunityAccount | CommunityMember, "username" | "discord_username"> | null | undefined
): string {
  return profile?.username || profile?.discord_username || "hcr2 user";
}

export function communityAvatar(
  profile: Pick<CommunityAccount | CommunityMember, "discord_avatar"> | null | undefined
): string | null {
  return profile?.discord_avatar ?? null;
}

function jsonRequest<T>(path: string, method: "PATCH" | "POST" | "DELETE", body?: unknown) {
  return fetchJson<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
}

export function getCommunityMe() {
  return fetchJson<CommunityAccount>("/api/v1/community/me");
}

export function setCommunityUsername(username: string) {
  const payload: UsernameUpdate = { username };
  return jsonRequest<CommunityAccount>("/api/v1/community/profile/username", "POST", payload);
}

export function updateCommunityProfile(payload: CommunityProfileUpdate) {
  return jsonRequest<CommunityAccount>("/api/v1/community/profile", "PATCH", payload);
}

export function uploadCommunityBanner(file: File) {
  const body = new FormData();
  body.append("banner", file);
  return fetchJson<CommunityAccount>("/api/v1/community/profile/banner", {
    method: "POST",
    body
  });
}

export function removeCommunityBanner() {
  return jsonRequest<CommunityAccount>("/api/v1/community/profile/banner", "DELETE");
}

export type CommunityMembersParams = {
  search?: string;
  sort?: string;
  country?: string;
  limit?: number;
  offset?: number;
};

export function getCommunityMembers(params: CommunityMembersParams) {
  const query = new URLSearchParams();
  if (params.search) query.set("q", params.search);
  if (params.sort) query.set("sort", params.sort);
  if (params.country) query.set("country", params.country);
  query.set("limit", String(params.limit ?? 24));
  query.set("offset", String(params.offset ?? 0));
  return fetchJson<CommunityMemberListResponse>(`/api/v1/community/members?${query}`);
}

export function getCommunityProfile(id: number) {
  return fetchJson<CommunityAccount>(`/api/v1/community/${id}`);
}

export function reportCommunityProfile(id: number, category: ReportCategory, reason: string, hCaptchaResponse: string) {
  return jsonRequest<CommunityReportResult>(`/api/v1/community/${id}/report`, "POST", {
    category,
    reason,
    h_captcha_response: hCaptchaResponse
  });
}

export function communityBannerUrl(communityId: number, bannerUpdatedAt?: string | null): string | null {
  if (!bannerUpdatedAt) return null;
  return `/api/v1/community/${communityId}/banner?v=${encodeURIComponent(bannerUpdatedAt)}`;
}