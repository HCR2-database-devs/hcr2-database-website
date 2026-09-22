import type {
  AdminLongestRecordResponse,
  AdminRecord,
  BackupItem,
  BanEntry,
  IntegrityStatus,
  MaintenanceStatus,
  PendingSubmission
} from "../types/api";
import { fetchJson } from "./api";

type SuccessResponse = {
  success: boolean;
  [key: string]: unknown;
};

function jsonRequest<T>(path: string, method: string, body?: unknown) {
  return fetchJson<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
}

function formRequest<T>(path: string, body: FormData) {
  return fetchJson<T>(path, {
    method: "POST",
    body
  });
}

function withOptionalIcon(nameKey: string, name: string, icon?: File | null) {
  const body = new FormData();
  body.append(nameKey, name);
  if (icon && icon.size > 0) {
    body.append("icon", icon);
  }
  return body;
}

export function getAdminRecords() {
  return fetchJson<AdminRecord[]>("/api/v1/admin/records");
}

export function submitAdminRecord(body: unknown) {
  return jsonRequest<SuccessResponse>("/api/v1/admin/records", "POST", body);
}

export function deleteAdminRecord(recordId: number) {
  return jsonRequest<SuccessResponse>("/api/v1/admin/records/delete", "POST", { recordId });
}

export function setRecordQuestionable(body: unknown) {
  return jsonRequest<SuccessResponse>("/api/v1/admin/records/questionable", "PATCH", body);
}

export function assignTuningSetup(body: unknown) {
  return jsonRequest<SuccessResponse>("/api/v1/admin/records/tuning-setup", "PATCH", body);
}

export function addMap(name: string, icon?: File | null, special: boolean = false) {
  const body = withOptionalIcon("mapName", name, icon);
  body.append("special", special ? "1" : "0");
  return formRequest<SuccessResponse>("/api/v1/admin/maps/form", body);
}

export function addVehicle(name: string, icon?: File | null) {
  return formRequest<SuccessResponse>("/api/v1/admin/vehicles/form", withOptionalIcon("vehicleName", name, icon));
}

export function addTuningPart(name: string, icon?: File | null) {
  return formRequest<SuccessResponse>("/api/v1/admin/tuning-parts/form", withOptionalIcon("partName", name, icon));
}

export function addTuningSetup(partIds: number[], echoAffectedPartId?: number | null) {
  return jsonRequest<SuccessResponse>("/api/v1/admin/tuning-setups", "POST", {
    partIds,
    echoAffectedPartId: echoAffectedPartId ?? null,
  });
}

export function getPendingSubmissions() {
  return fetchJson<{ pending: PendingSubmission[] }>("/api/v1/admin/pending");
}

export function approvePendingSubmission(id: number) {
  return jsonRequest<SuccessResponse>("/api/v1/admin/pending/approve", "POST", { id });
}

export function rejectPendingSubmission(id: number) {
  return jsonRequest<SuccessResponse>("/api/v1/admin/pending/reject", "POST", { id });
}

export function postAdminNews(title: string, content: string) {
  return jsonRequest<SuccessResponse & { id?: number }>("/api/v1/admin/news", "POST", { title, content });
}

export function updateAdminNews(id: number, title: string, content: string) {
  return jsonRequest<SuccessResponse>(`/api/v1/admin/news/${id}`, "PUT", { title, content });
}

export function deleteAdminNews(id: number) {
  return fetchJson<SuccessResponse>(`/api/v1/admin/news/${id}`, {
    method: "DELETE"
  });
}

export function postAdminChangelog(body: {
  version: string;
  title?: string | null;
  added?: string[];
  changed?: string[];
  fixed?: string[];
}) {
  return jsonRequest<SuccessResponse & { id?: number }>("/api/v1/admin/changelog", "POST", body);
}

export function updateAdminChangelog(
  id: number,
  body: {
    version: string;
    title?: string | null;
    added?: string[];
    changed?: string[];
    fixed?: string[];
  }
) {
  return jsonRequest<SuccessResponse>(`/api/v1/admin/changelog/${id}`, "PUT", body);
}

export function deleteAdminChangelog(id: number) {
  return fetchJson<SuccessResponse>(`/api/v1/admin/changelog/${id}`, {
    method: "DELETE"
  });
}

export function getMaintenanceStatus() {
  return fetchJson<MaintenanceStatus>("/api/v1/admin/maintenance");
}

export function setMaintenance(action: "enable" | "disable") {
  return jsonRequest<SuccessResponse>("/api/v1/admin/maintenance", "PATCH", { action });
}

export function runIntegrityCheck() {
  return fetchJson<IntegrityStatus>("/api/v1/admin/integrity");
}

export function listBackups() {
  return fetchJson<{ backups: BackupItem[] }>("/api/v1/admin/backups");
}

export function createBackup() {
  return jsonRequest<{ success: boolean; filename: string; backup: BackupItem }>("/api/v1/admin/backups", "POST");
}

export function deleteBackup(filename: string) {
  return fetchJson<SuccessResponse>(`/api/v1/admin/backups/${encodeURIComponent(filename)}`, {
    method: "DELETE"
  });
}

export function backupDownloadUrl(filename: string) {
  return `/api/v1/admin/backups/${encodeURIComponent(filename)}/download`;
}

export function listBans() {
  return fetchJson<{ bans: BanEntry[] }>("/api/v1/admin/bans");
}

export function createBan(body: { ip: string; reason: string; expiresAt?: string | null }) {
  return jsonRequest<SuccessResponse & { id?: number }>("/api/v1/admin/bans", "POST", body);
}

export function unbanPlayer(banId: number) {
  return fetchJson<SuccessResponse>(`/api/v1/admin/bans/${banId}`, {
    method: "DELETE"
  });
}

export function getAdminLongestRecord() {
  return fetchJson<AdminLongestRecordResponse>("/api/v1/admin/longest-record");
}

export function setLongestRecord(recordId: number) {
  return jsonRequest<SuccessResponse & { recordId?: number }>("/api/v1/admin/longest-record", "POST", { recordId });
}

export function clearLongestRecord() {
  return fetchJson<SuccessResponse>("/api/v1/admin/longest-record", {
    method: "DELETE"
  });
}
