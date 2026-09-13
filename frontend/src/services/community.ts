import type {
  CommunityAccount,
  CommunityMemberListResponse,
  CommunityProfileUpdate,
  CommunityReportResult,
  ReportCategory
} from "../types/api";
import { fetchJson } from "./api";

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