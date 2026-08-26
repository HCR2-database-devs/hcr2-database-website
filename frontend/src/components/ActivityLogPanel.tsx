import { useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { cleanupActivityLogs, getActivityLogAdmins, getActivityLogs } from "../services/activityLog";
import type { ActivityLogEntry } from "../types/api";

const ACTION_LABELS: Record<string, string> = {
  created: "Created",
  updated: "Updated",
  deleted: "Deleted",
  approved: "Approved",
  rejected: "Rejected"
};

const ENTITY_LABELS: Record<string, string> = {
  record: "Record",
  map: "Map",
  vehicle: "Vehicle",
  tuning_part: "Tuning Part",
  tuning_setup: "Tuning Setup",
  submission: "Submission",
  news: "News",
  backup: "Backup",
  maintenance: "Maintenance"
};

const ACTION_COLORS: Record<string, string> = {
  created: "var(--accent)",
  updated: "var(--accent-cyan)",
  deleted: "var(--danger)",
  approved: "var(--success)",
  rejected: "var(--accent-orange)"
};

function formatTimestamp(ts: string): string {
  try {
    const date = new Date(ts);
    return date.toLocaleString();
  } catch {
    return ts;
  }
}

type Props = {
  isOpen: boolean;
  onClose: () => void;
};

export function ActivityLogPanel({ isOpen, onClose }: Props) {
  const queryClient = useQueryClient();
  const [adminFilter, setAdminFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [entityFilter, setEntityFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const logsQuery = useQuery({
    queryKey: ["admin", "activity-logs", adminFilter, actionFilter, entityFilter, dateFrom, dateTo, offset],
    queryFn: () =>
      getActivityLogs({
        admin_username: adminFilter || null,
        action: actionFilter || null,
        entity_type: entityFilter || null,
        date_from: dateFrom || null,
        date_to: dateTo || null,
        limit,
        offset
      }),
    enabled: isOpen
  });

  const adminsQuery = useQuery({
    queryKey: ["admin", "activity-log-admins"],
    queryFn: getActivityLogAdmins,
    enabled: isOpen
  });

  const total = logsQuery.data?.total ?? 0;
  const entries = logsQuery.data?.entries ?? [];
  const hasMore = offset + limit < total;

  useEffect(() => {
    if (isOpen) {
      setOffset(0);
    }
  }, [isOpen, adminFilter, actionFilter, entityFilter, dateFrom, dateTo]);

  function handleResetFilters() {
    setAdminFilter("");
    setActionFilter("");
    setEntityFilter("");
    setDateFrom("");
    setDateTo("");
    setOffset(0);
  }

  async function handleCleanup() {
    if (!window.confirm("Delete activity logs older than 90 days?")) return;
    try {
      await cleanupActivityLogs(90);
      await logsQuery.refetch();
    } catch {
      // silently fail
    }
  }

  if (!isOpen) return null;

  return (
    <>
      <div className="activity-log-overlay" onClick={onClose} />
      <div className="activity-log-panel">
        <div className="activity-log-header">
          <h2>Activity Log</h2>
          <button type="button" className="activity-log-close" onClick={onClose}>
            &times;
          </button>
        </div>

        <div className="activity-log-filters">
          <label>
            Admin
            <select value={adminFilter} onChange={(e) => setAdminFilter(e.target.value)}>
              <option value="">All admins</option>
              {(adminsQuery.data?.admins ?? []).map((admin) => (
                <option key={admin} value={admin}>
                  {admin}
                </option>
              ))}
            </select>
          </label>
          <label>
            Action
            <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}>
              <option value="">All actions</option>
              <option value="created">Created</option>
              <option value="updated">Updated</option>
              <option value="deleted">Deleted</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </label>
          <label>
            Entity
            <select value={entityFilter} onChange={(e) => setEntityFilter(e.target.value)}>
              <option value="">All entities</option>
              <option value="record">Record</option>
              <option value="map">Map</option>
              <option value="vehicle">Vehicle</option>
              <option value="tuning_part">Tuning Part</option>
              <option value="tuning_setup">Tuning Setup</option>
              <option value="submission">Submission</option>
              <option value="news">News</option>
              <option value="backup">Backup</option>
              <option value="maintenance">Maintenance</option>
            </select>
          </label>
          <div className="activity-log-date-row">
            <label>
              From
              <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            </label>
            <label>
              To
              <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
            </label>
          </div>
          <div className="activity-log-filter-actions">
            <button type="button" onClick={handleResetFilters} className="button-ghost">
              Reset Filters
            </button>
            <button type="button" onClick={handleCleanup} className="button-ghost">
              Cleanup Old Logs
            </button>
          </div>
        </div>

        <div className="activity-log-list">
          {logsQuery.isLoading && <p className="activity-log-loading">Loading...</p>}
          {!logsQuery.isLoading && entries.length === 0 && (
            <p className="activity-log-empty">No activity logs found.</p>
          )}
          {entries.map((entry: ActivityLogEntry) => (
            <div className="activity-log-entry" key={entry.id}>
              <div className="activity-log-entry-header">
                <span
                  className="activity-log-action-badge"
                  style={{ background: ACTION_COLORS[entry.action] ?? "var(--muted)" }}
                >
                  {ACTION_LABELS[entry.action] ?? entry.action}
                </span>
                <span className="activity-log-entity-type">
                  {ENTITY_LABELS[entry.entity_type] ?? entry.entity_type}
                </span>
                <span className="activity-log-timestamp">{formatTimestamp(entry.created_at)}</span>
              </div>
              <div className="activity-log-entry-body">
                <span className="activity-log-admin">{entry.admin_username}</span>
                {entry.entity_name && (
                  <span className="activity-log-entity-name">{entry.entity_name}</span>
                )}
                {entry.entity_id != null && (
                  <span className="activity-log-entity-id">#{entry.entity_id}</span>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="activity-log-footer">
          <span className="activity-log-count">
            {total} total entries
          </span>
          <div className="activity-log-pagination">
            {offset > 0 && (
              <button
                type="button"
                onClick={() => setOffset(Math.max(0, offset - limit))}
                className="button-ghost"
              >
                Previous
              </button>
            )}
            {hasMore && (
              <button
                type="button"
                onClick={() => setOffset(offset + limit)}
                className="button-ghost"
              >
                Next
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
