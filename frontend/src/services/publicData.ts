import type { DataRow, NewsItem, PaginatedRecordsResponse, PublicDataView, RecordFilters } from "../types/api";
import { fetchJson } from "./api";

const dataEndpoints: Record<Exclude<PublicDataView, "records">, string> = {
  maps: "/api/v1/maps",
  vehicles: "/api/v1/vehicles",
  players: "/api/v1/players",
  "tuning-parts": "/api/v1/tuning-parts",
  "tuning-setups": "/api/v1/tuning-setups"
};

export function getPublicData(view: Exclude<PublicDataView, "records">) {
  return fetchJson<DataRow[]>(dataEndpoints[view]);
}

function addMythicParam(params: URLSearchParams, mythic: boolean | undefined) {
  if (mythic === undefined) return;
  params.set("mythic", mythic ? "true" : "false");
}

export function getRecordsPaginated(filters: RecordFilters, pageParam: number): Promise<PaginatedRecordsResponse> {
  const params = new URLSearchParams();
  params.set("limit", "50");
  params.set("offset", String(pageParam));
  if (filters.search) params.set("q", filters.search);
  filters.maps.forEach((m) => params.append("map", m));
  filters.vehicles.forEach((v) => params.append("vehicle", v));
  filters.tuningParts.forEach((t) => params.append("tuning_part", t));
  if (filters.sort && filters.sort !== "default") params.set("sort", filters.sort);
  if (filters.questionableOnly) params.set("questionable", "1");
  else if (filters.verifiedOnly) params.set("questionable", "0");
  if (filters.distanceOp === "gte" && filters.distance) params.set("min_distance", filters.distance);
  if (filters.distanceOp === "lte" && filters.distance) params.set("max_distance", filters.distance);
  addMythicParam(params, filters.mythic);
  return fetchJson<PaginatedRecordsResponse>(`/api/v1/records?${params}`);
}

export function exportRecords(filters: RecordFilters): Promise<PaginatedRecordsResponse> {
  const params = new URLSearchParams();
  params.set("export", "true");
  if (filters.search) params.set("q", filters.search);
  filters.maps.forEach((m) => params.append("map", m));
  filters.vehicles.forEach((v) => params.append("vehicle", v));
  filters.tuningParts.forEach((t) => params.append("tuning_part", t));
  if (filters.sort && filters.sort !== "default") params.set("sort", filters.sort);
  if (filters.questionableOnly) params.set("questionable", "1");
  else if (filters.verifiedOnly) params.set("questionable", "0");
  if (filters.distanceOp === "gte" && filters.distance) params.set("min_distance", filters.distance);
  if (filters.distanceOp === "lte" && filters.distance) params.set("max_distance", filters.distance);
  addMythicParam(params, filters.mythic);
  return fetchJson<PaginatedRecordsResponse>(`/api/v1/records?${params}`);
}

export function getNews(limit = 10) {
  return fetchJson<{ news: NewsItem[] }>(`/api/v1/news?limit=${limit}`);
}

export function getHcaptchaSitekey() {
  return fetchJson<{ sitekey: string }>("/api/v1/hcaptcha/sitekey");
}
