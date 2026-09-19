import type {
  AdminCommunityProfileListResponse,
  AdminCommunityProfile,
  AdminCommunityReport,
  AdminCommunityReportListResponse,
  AdminProfileDetail,
  AdminProfileUpdate,
  CommunityAccount
} from "../types/api";
import { fetchJson } from "./api";

function jsonRequest<T>(path: string, method: "PATCH" | "POST", body?: unknown) {
  return fetchJson<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
}

export function getAdminCommunityProfiles(params: { search?: string; limit?: number; offset?: number }) {
  const query = new URLSearchParams();
  if (params.search) query.set("q", params.search);
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  return fetchJson<AdminCommunityProfileListResponse>(`/api/v1/admin/community/profiles?${query}`);
}

export function getAdminCommunityProfile(id: number) {
  return fetchJson<AdminProfileDetail>(`/api/v1/admin/community/profiles/${id}`);
}

export function updateAdminCommunityProfile(id: number, payload: AdminProfileUpdate) {
  return jsonRequest<CommunityAccount>(`/api/v1/admin/community/profiles/${id}`, "PATCH", payload);
}

function adminProfileAction(id: number, action: string, note?: string) {
  return jsonRequest<CommunityAccount>(`/api/v1/admin/community/profiles/${id}/${action}`, "POST", {
    note: note || null
  });
}

export function adminDisableProfile(id: number, note?: string) {
  return adminProfileAction(id, "disable", note);
}

export function adminEnableProfile(id: number, note?: string) {
  return adminProfileAction(id, "enable", note);
}

export function adminResetProfile(id: number, note?: string) {
  return adminProfileAction(id, "reset", note);
}

export function adminResetBanner(id: number, note?: string) {
  return adminProfileAction(id, "reset-banner", note);
}

export function getAdminCommunityReports(params: { status?: string; limit?: number; offset?: number }) {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  return fetchJson<AdminCommunityReportListResponse>(`/api/v1/admin/community/reports?${query}`);
}

function adminReportAction(id: number, action: "resolve" | "reject", note?: string) {
  return jsonRequest<AdminCommunityReport>(`/api/v1/admin/community/reports/${id}/${action}`, "POST", {
    note: note || null
  });
}

export function adminResolveReport(id: number, note?: string) {
  return adminReportAction(id, "resolve", note);
}

export function adminRejectReport(id: number, note?: string) {
  return adminReportAction(id, "reject", note);
}

export type { AdminCommunityReport };