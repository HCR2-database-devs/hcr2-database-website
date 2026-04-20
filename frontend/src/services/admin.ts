import type { AdminRecord, IntegrityStatus, MaintenanceStatus, PendingSubmission } from "../types/api";
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

export function addMap(name: string) {
  return jsonRequest<SuccessResponse>("/api/v1/admin/maps", "POST", { mapName: name });
}

export function addVehicle(name: string) {
  return jsonRequest<SuccessResponse>("/api/v1/admin/vehicles", "POST", { vehicleName: name });
}

export function addTuningPart(name: string) {
  return jsonRequest<SuccessResponse>("/api/v1/admin/tuning-parts", "POST", { partName: name });
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
