import { fetchJson } from "./api";

export interface Tipper {
  pseudo: string;
}

export function getTippers() {
  return fetchJson<{ tippers: Tipper[] }>("/api/v1/tippers");
}
