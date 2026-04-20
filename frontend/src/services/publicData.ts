import type { LegacyRow, NewsItem, PublicDataView } from "../types/api";
import { fetchJson } from "./api";

const dataEndpoints: Record<PublicDataView, string> = {
  maps: "/api/v1/maps",
  vehicles: "/api/v1/vehicles",
  players: "/api/v1/players",
  "tuning-parts": "/api/v1/tuning-parts",
  "tuning-setups": "/api/v1/tuning-setups",
  records: "/api/v1/records"
};

export function getPublicData(view: PublicDataView) {
  return fetchJson<LegacyRow[]>(dataEndpoints[view]);
}

export function getNews(limit = 10) {
  return fetchJson<{ news: NewsItem[] }>(`/api/v1/news?limit=${limit}`);
}
