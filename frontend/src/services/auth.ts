import type { AuthStatus } from "../types/api";
import { fetchJson } from "./api";

export function getAuthStatus() {
  return fetchJson<AuthStatus>("/api/v1/auth/status");
}
