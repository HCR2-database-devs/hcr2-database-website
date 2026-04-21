import type { AdminRecord, BackupItem, IntegrityStatus, MaintenanceStatus, PendingSubmission } from "../types/api";
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

export function addMap(name: string, icon?: File | null) {
  return formRequest<SuccessResponse>("/api/v1/admin/maps/form", withOptionalIcon("mapName", name, icon));
}

export function addVehicle(name: string, icon?: File | null) {
  return formRequest<SuccessResponse>("/api/v1/admin/vehicles/form", withOptionalIcon("vehicleName", name, icon));
}

export function addTuningPart(name: string, icon?: File | null) {
  return formRequest<SuccessResponse>("/api/v1/admin/tuning-parts/form", withOptionalIcon("partName", name, icon));
}

export function addTuningSetup(partIds: number[]) {
  return jsonRequest<SuccessResponse>("/api/v1/admin/tuning-setups", "POST", { partIds });
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
  return jsonRequest<SuccessResponse>("/api/v1/admin/news", "POST", { title, content });
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
