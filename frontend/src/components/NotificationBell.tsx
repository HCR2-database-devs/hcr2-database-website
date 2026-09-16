import { useEffect, useRef, useState } from "react";

import { useAuthStatus } from "../hooks/useAuthStatus";
import { formatDateTime } from "../lib/format";
import { useCanUseFeature } from "../lib/features";
import { getCommunityNotifications, markCommunityNotificationsRead } from "../services/notifications";
import type { CommunityNotificationListResponse } from "../types/api";

export function NotificationBell() {
  const { data: authStatus } = useAuthStatus();
  const canUse = useCanUseFeature("community_notifications");
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState<CommunityNotificationListResponse | null>(null);
  const [error, setError] = useState(false);
  const [markingRead, setMarkingRead] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const loaded = data !== null;
  const unread = data?.unread ?? 0;

  useEffect(() => {
    if (!canUse || !authStatus?.logged || !authStatus.community) return;
    let cancelled = false;
    getCommunityNotifications()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [canUse, authStatus?.logged, authStatus?.community]);

  useEffect(() => {
    if (!isOpen) return;
    function handleOutsideClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [isOpen]);

  if (!canUse || !authStatus?.logged || !authStatus.community) return null;

  function toggle() {
    setIsOpen((open) => !open);
  }

  function markAllRead() {
    if (markingRead || !data || data.unread === 0) return;
    setMarkingRead(true);
    markCommunityNotificationsRead([])
      .then(() => {
        setData((prev) =>
          prev
            ? {
                ...prev,
                unread: 0,
                notifications: prev.notifications.map((note) =>
                  note.read_at ? note : { ...note, read_at: new Date().toISOString() }
                )
              }
            : prev
        );
      })
      .catch(() => {})
      .finally(() => setMarkingRead(false));
  }

  return (
    <div className="notification-bell" ref={containerRef}>
      <button
        id="notifications-btn"
        type="button"
        className={`nav-action notification-bell__button${isOpen ? " is-open" : ""}`}
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-label="Notifications"
        title="Notifications"
        onClick={toggle}
      >
        <span className="notification-bell__icon" aria-hidden="true">🔔</span>
        {unread > 0 && (
          <span className="notification-badge" aria-label={`${unread} unread notifications`}>
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="notification-panel" role="menu" aria-label="Notifications">
          <div className="notification-panel__header">
            <span>Notifications</span>
            {unread > 0 && (
              <span className="notification-panel__header-right">
                <span className="notification-panel__unread">{unread} unread</span>
                <button
                  type="button"
                  className="notification-mark-all"
                  disabled={markingRead}
                  onClick={markAllRead}
                >
                  {markingRead ? "Marking..." : "Mark all as read"}
                </button>
              </span>
            )}
          </div>
          {error ? (
            <p className="notification-empty">Couldn&apos;t load notifications.</p>
          ) : !loaded ? (
            <p className="notification-empty">Loading&hellip;</p>
          ) : data.notifications.length === 0 ? (
            <p className="notification-empty">No notifications yet.</p>
          ) : (
            <ul className="notification-list">
              {data.notifications.map((note) => (
                <li
                  key={note.id}
                  className={`notification-item${note.read_at ? "" : " is-unread"}`}
                >
                  <p className="notification-message">{note.message}</p>
                  <span className="notification-time">{formatDateTime(note.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}