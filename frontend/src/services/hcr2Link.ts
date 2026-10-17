import type {
  Hcr2AccountLink,
  Hcr2LinkActionResult,
  Hcr2LinkCodeState,
  Hcr2LinkConfig,
  Hcr2LinkPlayerSearchResponse,
  Hcr2LinkRequest,
  Hcr2LinkStatus,
  Hcr2LinkSubmitResult
} from "../types/api";
import { fetchJson } from "./api";

function jsonRequest<T>(path: string, method: "POST" | "DELETE", body?: unknown) {
  return fetchJson<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
}

export function getHcr2LinkConfig() {
  return fetchJson<Hcr2LinkConfig>("/api/v1/community/hcr2-link/config");
}

export function searchHcr2LinkPlayers(search: string, limit = 20, offset = 0) {
  const query = new URLSearchParams();
  if (search) query.set("q", search);
  query.set("limit", String(limit));
  query.set("offset", String(offset));
  return fetchJson<Hcr2LinkPlayerSearchResponse>(`/api/v1/community/hcr2-link/players?${query}`);
}

export function getHcr2LinkStatus() {
  return fetchJson<Hcr2LinkStatus>("/api/v1/community/hcr2-link/status");
}

export function startHcr2LinkRequest(playerName: string) {
  return jsonRequest<Hcr2LinkActionResult>("/api/v1/community/hcr2-link/request/start", "POST", {
    player_name: playerName
  });
}

export function chooseHcr2LinkMethod(verificationMethod: string) {
  return jsonRequest<Hcr2LinkActionResult>("/api/v1/community/hcr2-link/request/method", "POST", {
    verification_method: verificationMethod
  });
}

export function confirmHcr2TeamJoined() {
  return jsonRequest<Hcr2LinkActionResult>(
    "/api/v1/community/hcr2-link/request/team/joined",
    "POST"
  );
}

export function generateHcr2VerificationCode() {
  return jsonRequest<Hcr2LinkCodeState>("/api/v1/community/hcr2-link/request/team/code", "POST");
}

export function confirmHcr2CodeSent(visibilityConfirmed: boolean) {
  return jsonRequest<Hcr2LinkActionResult>(
    "/api/v1/community/hcr2-link/request/team/sent",
    "POST",
    { visibility_confirmed: visibilityConfirmed }
  );
}

export function confirmHcr2DiscordJoined() {
  return jsonRequest<Hcr2LinkActionResult>(
    "/api/v1/community/hcr2-link/request/discord/joined",
    "POST"
  );
}

export function confirmHcr2ContactedOwner() {
  return jsonRequest<Hcr2LinkActionResult>(
    "/api/v1/community/hcr2-link/request/discord/contacted",
    "POST"
  );
}

export function confirmHcr2DiscordReady() {
  return jsonRequest<Hcr2LinkActionResult>(
    "/api/v1/community/hcr2-link/request/discord/ready",
    "POST"
  );
}

export function submitHcr2ChallengeLink(challengeUrl: string) {
  return jsonRequest<Hcr2LinkActionResult>(
    "/api/v1/community/hcr2-link/request/challenge/link",
    "POST",
    { challenge_url: challengeUrl }
  );
}

export function submitHcr2LinkRequest(instructionsFollowed: boolean, methodStepsCompleted: boolean) {
  return jsonRequest<Hcr2LinkSubmitResult>(
    "/api/v1/community/hcr2-link/request/submit",
    "POST",
    {
      instructions_followed: instructionsFollowed,
      method_steps_completed: methodStepsCompleted
    }
  );
}

export function cancelHcr2LinkRequest() {
  return jsonRequest<{ cancelled: number }>(
    "/api/v1/community/hcr2-link/request/cancel",
    "POST"
  );
}

export function unlinkHcr2Player() {
  return jsonRequest<{ link: Hcr2AccountLink }>("/api/v1/community/hcr2-link/link/unlink", "POST");
}

export type { Hcr2LinkRequest };