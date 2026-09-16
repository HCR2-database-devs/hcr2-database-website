import type {
  CommunityNotificationListResponse,
  NotificationReadResult
} from "../types/api";
import { fetchJson } from "./api";

export function getCommunityNotifications(limit = 20, offset = 0) {
  return fetchJson<CommunityNotificationListResponse>(
    `/api/v1/community/notifications?limit=${limit}&offset=${offset}`
  );
}

export function markCommunityNotificationsRead(notificationIds: number[]) {
  return fetchJson<NotificationReadResult>("/api/v1/community/notifications/read", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notification_ids: notificationIds })
  });
}