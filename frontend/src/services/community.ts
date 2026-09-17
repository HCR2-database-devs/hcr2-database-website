import type {
  CommunityAccount,
  CommunityMember,
  CommunityMemberListResponse,
  CommunityProfileUpdate,
  CommunityReportResult,
  ReportCategory,
  UsernameUpdate
} from "../types/api";
import { fetchJson } from "./api";

export function communityDisplayName(
  profile: Pick<CommunityAccount | CommunityMember, "username" | "discord_username"> | null | undefined
): string {
  return profile?.username || profile?.discord_username || "hcr2 user";
}

export function communityAvatar(
  profile: Pick<CommunityAccount | CommunityMember, "discord_avatar"> | null | undefined
): string | null {
  return profile?.discord_avatar ?? null;
}

export function discordAvatarUrl(
  avatar: string | null | undefined,
  discordId?: string | null
): string | null {
  if (!avatar) return null;
  if (/^https?:\/\//i.test(avatar)) return avatar;
  if (!discordId || !/^a?_?[0-9a-f]{32}$/i.test(avatar)) return null;
  const ext = avatar.startsWith("a_") ? "gif" : "png";
  return `https://cdn.discordapp.com/avatars/${discordId}/${avatar}.${ext}`;
}

function jsonRequest<T>(path: string, method: "PATCH" | "POST" | "DELETE", body?: unknown) {
  return fetchJson<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
}

export function getCommunityMe() {
  return fetchJson<CommunityAccount>("/api/v1/community/me");
}

export function setCommunityUsername(username: string) {
  const payload: UsernameUpdate = { username };
  return jsonRequest<CommunityAccount>("/api/v1/community/profile/username", "POST", payload);
}

export function updateCommunityProfile(payload: CommunityProfileUpdate) {
  return jsonRequest<CommunityAccount>("/api/v1/community/profile", "PATCH", payload);
}

export function uploadCommunityBanner(file: File) {
  const body = new FormData();
  body.append("banner", file);
  return fetchJson<CommunityAccount>("/api/v1/community/profile/banner", {
    method: "POST",
    body
  });
}

const BANNER_MAX_DIMENSION = 2048;

type DecodedImage = {
  source: CanvasImageSource;
  width: number;
  height: number;
  close?: () => void;
};

async function decodeImage(file: File): Promise<DecodedImage> {
  if ("createImageBitmap" in window) {
    try {
      const bitmap = await createImageBitmap(file);
      return { source: bitmap, width: bitmap.width, height: bitmap.height, close: () => bitmap.close() };
    } catch {
      // fall through to <img> decoding
    }
  }
  return new Promise<DecodedImage>((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve({ source: img, width: img.naturalWidth, height: img.naturalHeight });
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Could not read image file."));
    };
    img.src = url;
  });
}

export async function compressBannerFile(
  file: File,
  maxBytes = 8 * 1024 * 1024
): Promise<File> {
  let decoded: DecodedImage;
  try {
    decoded = await decodeImage(file);
  } catch {
    return file;
  }

  try {
    if (
      decoded.width <= BANNER_MAX_DIMENSION &&
      decoded.height <= BANNER_MAX_DIMENSION &&
      file.size <= maxBytes
    ) {
      return file;
    }

    if (decoded.width <= 0 || decoded.height <= 0) return file;

    const scale = Math.min(1, BANNER_MAX_DIMENSION / Math.max(decoded.width, decoded.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(decoded.width * scale));
    canvas.height = Math.max(1, Math.round(decoded.height * scale));
    const ctx = canvas.getContext("2d");
    if (!ctx) return file;
    ctx.drawImage(decoded.source, 0, 0, canvas.width, canvas.height);

    const type = canvas.toDataURL("image/webp").startsWith("data:image/webp")
      ? "image/webp"
      : "image/jpeg";
    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, type, 0.85)
    );
    if (!blob) return file;

    const name =
      file.name.replace(/\.[^.]+$/, "") + (type === "image/webp" ? ".webp" : ".jpg");
    return new File([blob], name, { type });
  } finally {
    decoded.close?.();
  }
}

export function removeCommunityBanner() {
  return jsonRequest<CommunityAccount>("/api/v1/community/profile/banner", "DELETE");
}

export type CommunityMembersParams = {
  search?: string;
  sort?: string;
  country?: string;
  limit?: number;
  offset?: number;
};

export function getCommunityMembers(params: CommunityMembersParams) {
  const query = new URLSearchParams();
  if (params.search) query.set("q", params.search);
  if (params.sort) query.set("sort", params.sort);
  if (params.country) query.set("country", params.country);
  query.set("limit", String(params.limit ?? 24));
  query.set("offset", String(params.offset ?? 0));
  return fetchJson<CommunityMemberListResponse>(`/api/v1/community/members?${query}`);
}

export function getCommunityProfile(id: number) {
  return fetchJson<CommunityAccount>(`/api/v1/community/${id}`);
}

export function reportCommunityProfile(id: number, category: ReportCategory, reason: string, hCaptchaResponse: string) {
  return jsonRequest<CommunityReportResult>(`/api/v1/community/${id}/report`, "POST", {
    category,
    reason,
    h_captcha_response: hCaptchaResponse
  });
}

export function communityBannerUrl(communityId: number, bannerUpdatedAt?: string | null): string | null {
  if (!bannerUpdatedAt) return null;
  return `/api/v1/community/${communityId}/banner?v=${encodeURIComponent(bannerUpdatedAt)}`;
}