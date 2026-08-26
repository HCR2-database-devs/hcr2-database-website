import type { ActivityLogResponse } from "../types/api";
import { fetchJson } from "./api";

type AdminsResponse = {
  admins: string[];
};

type CleanupResponse = {
  success: boolean;
  deleted: number;
};

function buildQueryString(params: Record<string, string | number | null | undefined>): string {
  const entries = Object.entries(params).filter(
    ([, value]) => value !== null && value !== undefined && value !== ""
  );
  if (entries.length === 0) return "";
  return "?" + entries.map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`).join("&");
}

export function getActivityLogs(filters: {
  admin_username?: string | null;
  action?: string | null;
  entity_type?: string | null;
  date_from?: string | null;
  date_to?: string | null;
  limit?: number;
  offset?: number;
}) {
  const query = buildQueryString(filters);
  return fetchJson<ActivityLogResponse>(`/api/v1/activity-logs${query}`);
}

export function getActivityLogAdmins() {
  return fetchJson<AdminsResponse>("/api/v1/activity-logs/admins");
}

export function cleanupActivityLogs(days: number = 90) {
  return fetchJson<CleanupResponse>(`/api/v1/activity-logs/cleanup?days=${days}`, {
    method: "POST"
  });
}
