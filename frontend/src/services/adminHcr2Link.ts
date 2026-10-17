import type {
  AdminHcr2LinkDetail,
  AdminHcr2LinkList,
  AdminHcr2LinkListResponse,
  Hcr2AccountLink
} from "../types/api";
import { fetchJson } from "./api";

function jsonRequest<T>(path: string, method: "PATCH" | "POST", body?: unknown) {
  return fetchJson<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
}

export type AdminHcr2LinkParams = {
  status?: string;
  method?: string;
  search?: string;
  limit?: number;
  offset?: number;
};

export function getAdminHcr2LinkRequests(params: AdminHcr2LinkParams) {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  if (params.method) query.set("method", params.method);
  if (params.search) query.set("q", params.search);
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  return fetchJson<AdminHcr2LinkListResponse>(`/api/v1/admin/hcr2-link/requests?${query}`);
}

export function getAdminHcr2LinkRequest(id: number) {
  return fetchJson<AdminHcr2LinkDetail>(`/api/v1/admin/hcr2-link/requests/${id}`);
}

export function adminApproveHcr2LinkRequest(id: number, note?: string) {
  return jsonRequest<{ link: Hcr2AccountLink }>(
    `/api/v1/admin/hcr2-link/requests/${id}/approve`,
    "POST",
    { note: note || null }
  );
}

export function adminRejectHcr2LinkRequest(
  id: number,
  category: string,
  reason: string,
  note?: string
) {
  return jsonRequest<{ id: number; status: string }>(
    `/api/v1/admin/hcr2-link/requests/${id}/reject`,
    "POST",
    { category, reason, note: note || null }
  );
}

export function adminRequestHcr2LinkRetry(id: number, note?: string) {
  return jsonRequest<unknown>(`/api/v1/admin/hcr2-link/requests/${id}/retry`, "POST", {
    note: note || null
  });
}

export function adminSetHcr2Appointment(
  id: number,
  appointmentStatus: string,
  appointmentAt?: string | null,
  note?: string
) {
  return jsonRequest<unknown>(`/api/v1/admin/hcr2-link/requests/${id}/appointment`, "POST", {
    appointment_status: appointmentStatus,
    appointment_at: appointmentAt || null,
    note: note || null
  });
}

function adminRequestStatusAction(id: number, action: "cancel" | "expire", note?: string) {
  return jsonRequest<unknown>(`/api/v1/admin/hcr2-link/requests/${id}/${action}`, "POST", {
    note: note || null
  });
}

export function adminCancelHcr2LinkRequest(id: number, note?: string) {
  return adminRequestStatusAction(id, "cancel", note);
}

export function adminExpireHcr2LinkRequest(id: number, note?: string) {
  return adminRequestStatusAction(id, "expire", note);
}

export function getAdminHcr2Links(params: { status?: string; search?: string; limit?: number; offset?: number }) {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  if (params.search) query.set("q", params.search);
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  return fetchJson<AdminHcr2LinkList>(`/api/v1/admin/hcr2-link/links?${query}`);
}

export function adminSetHcr2LinkStatus(linkId: number, status: string, reason?: string) {
  return jsonRequest<{ link: Hcr2AccountLink }>(
    `/api/v1/admin/hcr2-link/links/${linkId}/status`,
    "POST",
    { status, reason: reason || null }
  );
}

export function getAdminHcr2Conflicts(playerName: string) {
  const query = new URLSearchParams({ player_name: playerName });
  return fetchJson<{ active_links: number; open_requests: number; competing_claimants: number }>(
    `/api/v1/admin/hcr2-link/conflicts?${query}`
  );
}