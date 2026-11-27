import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  adjustXp,
  awardBadge,
  getAdminBadgeDefinitions,
  getBadgeHistory,
  refreshBadges
} from "../services/badges";

export function BadgeAdminPanel() {
  const queryClient = useQueryClient();
  const [badgeIdentifier, setBadgeIdentifier] = useState("");
  const [userIds, setUserIds] = useState("");
  const [badgeReason, setBadgeReason] = useState("");
  const [xpUserId, setXpUserId] = useState("");
  const [xpAmount, setXpAmount] = useState("");
  const [xpReason, setXpReason] = useState("");
  const [message, setMessage] = useState("");

  const definitionsQuery = useQuery({
    queryKey: ["admin", "badges", "definitions"],
    queryFn: () => getAdminBadgeDefinitions(true)
  });
  const historyQuery = useQuery({
    queryKey: ["admin", "badges", "history"],
    queryFn: () => getBadgeHistory({ limit: 20 })
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["admin", "badges"] });
    queryClient.invalidateQueries({ queryKey: ["badges"] });
    queryClient.invalidateQueries({ queryKey: ["progression"] });
    queryClient.invalidateQueries({ queryKey: ["community", "profile"] });
  }

  const awardMutation = useMutation({
    mutationFn: awardBadge,
    onSuccess: (result) => {
      setMessage(`Awarded ${result.awarded_count} badge(s).`);
      invalidate();
    },
    onError: (error: Error) => setMessage(error.message)
  });
  const xpMutation = useMutation({
    mutationFn: () => adjustXp(Number(xpUserId), Number(xpAmount), xpReason.trim()),
    onSuccess: () => {
      setMessage("XP adjustment applied.");
      setXpAmount("");
      setXpReason("");
      invalidate();
    },
    onError: (error: Error) => setMessage(error.message)
  });
  const refreshMutation = useMutation({
    mutationFn: refreshBadges,
    onSuccess: (result) => {
      setMessage(`Refreshed badges: ${result.awarded.length} awarded, ${result.revoked.length} revoked.`);
      invalidate();
    },
    onError: (error: Error) => setMessage(error.message)
  });

  function handleAward(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const ids = userIds
      .split(/[\s,]+/)
      .map((value) => Number(value))
      .filter((value) => Number.isInteger(value) && value > 0);
    if (!badgeIdentifier || ids.length === 0) {
      setMessage("Choose a badge and at least one community ID.");
      return;
    }
    awardMutation.mutate({
      badge_identifier: badgeIdentifier,
      user_ids: ids,
      reason: badgeReason.trim()
    });
  }

  function handleXp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!Number.isInteger(Number(xpUserId)) || !Number.isInteger(Number(xpAmount))) {
      setMessage("Enter a valid community ID and XP amount.");
      return;
    }
    xpMutation.mutate();
  }

  return (
    <div className="badge-admin-panel">
      {message && <p className="frontend-message">{message}</p>}
      <div className="badge-admin-grid">
        <section className="admin-section">
          <h3>Award a badge</h3>
          <form className="admin-form" onSubmit={handleAward}>
            <label>
              Badge
              <select value={badgeIdentifier} onChange={(event) => setBadgeIdentifier(event.target.value)}>
                <option value="">Choose…</option>
                {(definitionsQuery.data?.badges ?? []).map((badge) => (
                  <option key={badge.id} value={badge.identifier}>
                    {badge.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Community user IDs
              <input
                value={userIds}
                onChange={(event) => setUserIds(event.target.value)}
                placeholder="12, 34, 56"
              />
            </label>
            <label>
              Internal reason
              <input value={badgeReason} onChange={(event) => setBadgeReason(event.target.value)} />
            </label>
            <button className="button" type="submit" disabled={awardMutation.isPending}>
              Award badge
            </button>
          </form>
        </section>

        <section className="admin-section">
          <h3>Adjust XP</h3>
          <form className="admin-form" onSubmit={handleXp}>
            <label>
              Community user ID
              <input value={xpUserId} onChange={(event) => setXpUserId(event.target.value)} />
            </label>
            <label>
              XP amount
              <input
                type="number"
                value={xpAmount}
                onChange={(event) => setXpAmount(event.target.value)}
                placeholder="-50 or 100"
              />
            </label>
            <label>
              Reason
              <input value={xpReason} onChange={(event) => setXpReason(event.target.value)} />
            </label>
            <button className="button" type="submit" disabled={xpMutation.isPending}>
              Apply adjustment
            </button>
          </form>
        </section>
      </div>

      <section className="admin-section">
        <div className="admin-section__head">
          <h3>Recent badge history</h3>
          <label>
            Recalculate user
            <input id="badge-refresh-user" type="number" placeholder="Community user ID" />
          </label>
          <button
            className="button-ghost"
            type="button"
            disabled={refreshMutation.isPending}
            onClick={() => {
              const value = document.querySelector<HTMLInputElement>("#badge-refresh-user")?.value;
              if (value) refreshMutation.mutate(Number(value));
            }}
          >
            Refresh badges
          </button>
        </div>
        {historyQuery.data && historyQuery.data.history.length > 0 ? (
          <table className="admin-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Member</th>
                <th>Badge</th>
                <th>Action</th>
                <th>Actor</th>
              </tr>
            </thead>
            <tbody>
              {historyQuery.data.history.map((entry) => (
                <tr key={entry.id}>
                  <td>{new Date(entry.created_at).toLocaleString()}</td>
                  <td>#{entry.community_user_id}</td>
                  <td>{entry.badge_name}</td>
                  <td>{entry.action}</td>
                  <td>{entry.actor || "system"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="frontend-muted">No badge history yet.</p>
        )}
      </section>
    </div>
  );
}
