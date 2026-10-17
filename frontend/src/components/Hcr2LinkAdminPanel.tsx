import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  adminApproveHcr2LinkRequest,
  adminCancelHcr2LinkRequest,
  adminExpireHcr2LinkRequest,
  adminRejectHcr2LinkRequest,
  adminRequestHcr2LinkRetry,
  adminSetHcr2Appointment,
  adminSetHcr2LinkStatus,
  getAdminHcr2LinkRequest,
  getAdminHcr2LinkRequests,
  getAdminHcr2Links
} from "../services/adminHcr2Link";
import { formatMemberSince } from "../lib/format";
import {
  HCR2_APPOINTMENT_STATUSES,
  HCR2_REJECTION_CATEGORIES,
  type AdminHcr2LinkDetail
} from "../types/api";

const PAGE_SIZE = 20;

type SubTab = "queue" | "links";

const REQUEST_STATUSES = [
  { value: "", label: "All statuses" },
  { value: "submitted", label: "Submitted (awaiting review)" },
  { value: "in_progress", label: "In progress" },
  { value: "draft", label: "Draft" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "expired", label: "Expired" },
  { value: "cancelled", label: "Cancelled" }
];

const METHOD_FILTERS = [
  { value: "", label: "All methods" },
  { value: "team", label: "Verification team" },
  { value: "discord_screen_share", label: "Discord screen-share" },
  { value: "playhcr_challenge", label: "playhcr jeep challenge" }
];

const METHOD_LABELS: Record<string, string> = {
  team: "A. Verification team",
  discord_screen_share: "B. Discord screen-share",
  playhcr_challenge: "C. playhcr jeep challenge"
};

const METHOD_BADGES: Record<string, string> = {
  team: "team",
  discord_screen_share: "discord",
  playhcr_challenge: "challenge"
};

function CopyCode({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      className="admin-link-button"
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(value);
          setCopied(true);
          window.setTimeout(() => setCopied(false), 2000);
        } catch {
          setCopied(false);
        }
      }}
    >
      <code>{value}</code> {copied ? "(copied)" : "(copy)"}
    </button>
  );
}

function RequestDetail({
  requestId,
  onChanged
}: {
  requestId: number;
  onChanged: () => void;
}) {
  const [note, setNote] = useState("");
  const [reason, setReason] = useState("");
  const [category, setCategory] = useState("code_not_visible");
  const [appointmentStatus, setAppointmentStatus] = useState("scheduled");
  const [appointmentAt, setAppointmentAt] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const detailQuery = useQuery({
    queryKey: ["admin", "hcr2-link", "request", requestId],
    queryFn: () => getAdminHcr2LinkRequest(requestId)
  });

  const mutation = useMutation({
    mutationFn: (run: () => Promise<unknown>) => run(),
    onSuccess: async (result: unknown) => {
      setError("");
      setNote("");
      setReason("");
      setMessage(typeof result === "object" && result && "status" in result ? "Done." : "Done.");
      onChanged();
    },
    onError: (mutationError) => {
      setMessage("");
      setError(mutationError instanceof Error ? mutationError.message : "Action failed.");
    }
  });

  if (detailQuery.isLoading) {
    return <p className="community-status">Loading request...</p>;
  }
  if (detailQuery.isError || !detailQuery.data) {
    return <p className="community-status">Could not load this request.</p>;
  }

  const detail: AdminHcr2LinkDetail = detailQuery.data;
  const request = detail.request;
  const method = request.verification_method;
  const isTeam = method === "team";
  const isChallenge = method === "playhcr_challenge";
  const isDiscord = method === "discord_screen_share";

  return (
    <div className="admin-hcr2-detail">
      <dl className="hcr2-admin-facts">
        <div>
          <dt>Community user</dt>
          <dd>
            {request.community_username ?? `(no username)`} #{request.community_user_id}
          </dd>
        </div>
        <div>
          <dt>Discord</dt>
          <dd>
            {request.discord_username ?? "unknown"} · ID {request.discord_id ?? "unknown"}
          </dd>
        </div>
        <div>
          <dt>Player name</dt>
          <dd>
            <strong>{request.player_name}</strong> (normalized: {request.player_name_norm})
          </dd>
        </div>
        <div>
          <dt>Method</dt>
          <dd>{METHOD_LABELS[method] ?? method}</dd>
        </div>
        <div>
          <dt>Created</dt>
          <dd>{formatMemberSince(request.created_at)}</dd>
        </div>
        <div>
          <dt>Submitted</dt>
          <dd>{request.submitted_at ? formatMemberSince(request.submitted_at) : "not submitted"}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{request.status}</dd>
        </div>
        <div>
          <dt>Wizard step</dt>
          <dd>
            {request.step} · {request.status === "submitted" ? "submitted" : "not submitted"}
          </dd>
        </div>
        <div>
          <dt>Attempt</dt>
          <dd>
            #{request.attempt_count}
            {request.is_resubmission ? " (resubmission)" : ""}
            {request.supersedes_request_id ? ` of #${request.supersedes_request_id}` : ""}
          </dd>
        </div>
        {isTeam && (
          <>
            <div>
              <dt>Verification code</dt>
              <dd>{request.code_value ? <CopyCode value={request.code_value} /> : "none generated"}</dd>
            </div>
            <div>
              <dt>Claims by the user</dt>
              <dd>
                joined team: {request.team_joined_claimed ? "yes" : "no"} · sent code:{" "}
                {request.code_sent_claimed ? "yes" : "no"} · code fully visible:{" "}
                {request.code_visibility_confirmed ? "yes" : "no"}
              </dd>
            </div>
            <div>
              <dt>Code</dt>
              <dd>
                generated {request.code_roll_count}x ·{" "}
                {request.code_expires_at ? `expires ${formatMemberSince(request.code_expires_at)}` : "n/a"}
              </dd>
            </div>
          </>
        )}
        {isDiscord && (
          <>
            <div>
              <dt>Claims by the user</dt>
              <dd>
                joined Discord: {request.discord_joined_claimed ? "yes" : "no"} · contacted owner:{" "}
                {request.contacted_owner_claimed ? "yes" : "no"}
              </dd>
            </div>
            <div>
              <dt>Appointment</dt>
              <dd>
                {request.appointment_status}
                {request.appointment_at ? ` · ${formatMemberSince(request.appointment_at)}` : ""}
              </dd>
            </div>
          </>
        )}
        {isChallenge && (
          <>
            <div>
              <dt>Assigned distance</dt>
              <dd>
                {request.challenge_distance_m ? `${request.challenge_distance_m} m` : "not assigned"}
              </dd>
            </div>
            <div>
              <dt>Challenge link</dt>
              <dd>
                {request.challenge_url ? (
                  <a href={request.challenge_url} target="_blank" rel="noreferrer noopener">
                    {request.challenge_url}
                  </a>
                ) : (
                  "not sent"
                )}
              </dd>
            </div>
            <div>
              <dt>Challenge id</dt>
              <dd>{request.challenge_id ?? "(none)"}</dd>
            </div>
            <div>
              <dt>Claims by the user</dt>
              <dd>link sent: {request.challenge_link_claimed ? "yes" : "no"}</dd>
            </div>
          </>
        )}
      </dl>

      <p className="admin-report-reason">
        Everything above is the user&apos;s own claim plus generated data. Confirm it yourself in
        team chat or on the screen-share before approving. The site cannot verify it
        automatically.
      </p>

      {detail.conflicts.active_links > 0 && detail.conflicts.competing_claimants > 0 && (
        <p className="hcr2-admin-warning">
          Competing claims detected: {detail.conflicts.active_links} active link(s) and{" "}
          {detail.conflicts.competing_claimants} account(s) claiming this player name. Resolve
          before approving.
        </p>
      )}

      <div className="hcr2-admin-note-fields">
        <label>
          Private admin note (never shown to the member)
          <input
            type="text"
            value={note}
            maxLength={500}
            onChange={(event) => setNote(event.target.value)}
          />
        </label>
      </div>

      {message && <p className="admin-notice">{message}</p>}
      {error && <p className="frontend-error">{error}</p>}

      <div className="admin-report-actions">
        <button
          className="button"
          type="button"
          disabled={mutation.isPending}
          onClick={() => mutation.mutate(() => adminApproveHcr2LinkRequest(request.id, note))}
        >
          Approve and link
        </button>
        <button
          className="button-ghost"
          type="button"
          disabled={mutation.isPending}
          onClick={() => mutation.mutate(() => adminRequestHcr2LinkRetry(request.id, note))}
        >
          Ask to retry
        </button>
        <button
          className="button-ghost"
          type="button"
          disabled={mutation.isPending}
          onClick={() => {
            if (!window.confirm("Cancel this request?")) return;
            mutation.mutate(() => adminCancelHcr2LinkRequest(request.id, note));
          }}
        >
          Cancel
        </button>
        <button
          className="button-ghost"
          type="button"
          disabled={mutation.isPending}
          onClick={() => mutation.mutate(() => adminExpireHcr2LinkRequest(request.id, note))}
        >
          Expire
        </button>
      </div>

      <div className="hcr2-admin-reject">
        <h4>Reject</h4>
        <label>
          Reason category
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            {HCR2_REJECTION_CATEGORIES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Reason shown to the member
          <input
            type="text"
            value={reason}
            maxLength={500}
            onChange={(event) => setReason(event.target.value)}
          />
        </label>
        <button
          className="button-ghost"
          type="button"
          disabled={mutation.isPending}
          onClick={() =>
            mutation.mutate(() =>
              adminRejectHcr2LinkRequest(request.id, category, reason, note)
            )
          }
        >
          Reject request
        </button>
      </div>

      {isDiscord && (
        <div className="hcr2-admin-appointment">
          <h4>Screen-share appointment</h4>
          <div className="profile-settings-row">
            <label>
              Status
              <select
                value={appointmentStatus}
                onChange={(event) => setAppointmentStatus(event.target.value)}
              >
                {HCR2_APPOINTMENT_STATUSES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Scheduled time
              <input
                type="text"
                value={appointmentAt}
                placeholder="2026-10-20 18:30"
                onChange={(event) => setAppointmentAt(event.target.value)}
              />
            </label>
          </div>
          <button
            className="button-ghost"
            type="button"
            disabled={mutation.isPending}
            onClick={() =>
              mutation.mutate(() =>
                adminSetHcr2Appointment(
                  request.id,
                  appointmentStatus,
                  appointmentAt ? new Date(appointmentAt).toISOString() : null,
                  note
                )
              )
            }
          >
            Save appointment
          </button>
        </div>
      )}

      <details className="hcr2-admin-history">
        <summary>Step history ({detail.steps.length})</summary>
        <ul>
          {detail.steps.map((step) => (
            <li key={step.id}>
              <strong>{step.step}</strong> · {formatMemberSince(step.reached_at)} · {step.detail}
            </li>
          ))}
        </ul>
      </details>

      <details className="hcr2-admin-history">
        <summary>Previous / competing attempts ({detail.history.length})</summary>
        <ul>
          {detail.history.map((item) => (
            <li key={item.id}>
              #{item.id} · {item.community_username ?? "unknown"} · {item.status} ·{" "}
              {formatMemberSince(item.created_at)}
              {item.rejection_reason ? ` · ${item.rejection_reason}` : ""}
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}

export function Hcr2LinkAdminPanel() {
  const queryClient = useQueryClient();
  const [subTab, setSubTab] = useState<SubTab>("queue");
  const [search, setSearch] = useState("");
  const [submittedSearch, setSubmittedSearch] = useState("");
  const [status, setStatus] = useState("submitted");
  const [method, setMethod] = useState("");
  const [offset, setOffset] = useState(0);
  const [linksOffset, setLinksOffset] = useState(0);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [linkStatus, setLinkStatus] = useState("");

  const requestsQuery = useQuery({
    queryKey: ["admin", "hcr2-link", "requests", status, method, submittedSearch, offset],
    queryFn: () =>
      getAdminHcr2LinkRequests({
        status: status || undefined,
        method: method || undefined,
        search: submittedSearch || undefined,
        limit: PAGE_SIZE,
        offset
      })
  });

  const linksQuery = useQuery({
    queryKey: ["admin", "hcr2-link", "links", linkStatus, linksOffset],
    queryFn: () =>
      getAdminHcr2Links({
        status: linkStatus || undefined,
        limit: PAGE_SIZE,
        offset: linksOffset
      })
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["admin", "hcr2-link"] });
    queryClient.invalidateQueries({ queryKey: ["admin", "activity-logs"] });
    queryClient.invalidateQueries({ queryKey: ["hcr2-link"] });
    queryClient.invalidateQueries({ queryKey: ["community"] });
  }

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmittedSearch(search.trim());
    setOffset(0);
  }

  const requests = requestsQuery.data?.requests ?? [];
  const requestCount = requestsQuery.data?.count ?? 0;
  const hasMoreRequests = offset + requests.length < requestCount;

  const links = linksQuery.data?.links ?? [];
  const linkCount = linksQuery.data?.count ?? 0;
  const hasMoreLinks = linksOffset + links.length < linkCount;

  const linkMutation = useMutation({
    mutationFn: (params: { linkId: number; status: string; reason: string }) =>
      adminSetHcr2LinkStatus(params.linkId, params.status, params.reason),
    onSuccess: invalidate
  });

  return (
    <div className="admin-hcr2-panel">
      <nav className="admin-subtabs" aria-label="HCR2 linking admin sections">
        <button
          type="button"
          className={`admin-subtab${subTab === "queue" ? " admin-subtab--active" : ""}`}
          onClick={() => setSubTab("queue")}
        >
          Review queue
          <span className="admin-subtab-count">{requestCount}</span>
        </button>
        <button
          type="button"
          className={`admin-subtab${subTab === "links" ? " admin-subtab--active" : ""}`}
          onClick={() => setSubTab("links")}
        >
          Linked accounts
          <span className="admin-subtab-count">{linkCount}</span>
        </button>
      </nav>

      {subTab === "queue" && (
        <div className="admin-section">
          <form className="community-filters" onSubmit={handleSearch}>
            <label>
              Status
              <select
                value={status}
                onChange={(event) => {
                  setStatus(event.target.value);
                  setOffset(0);
                }}
              >
                {REQUEST_STATUSES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Method
              <select
                value={method}
                onChange={(event) => {
                  setMethod(event.target.value);
                  setOffset(0);
                }}
              >
                {METHOD_FILTERS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Search
              <input
                type="search"
                value={search}
                maxLength={50}
                placeholder="Player name or member..."
                onChange={(event) => setSearch(event.target.value)}
              />
            </label>
            <button className="button" type="submit">
              Search
            </button>
          </form>

          {requestsQuery.isLoading && <p className="community-status">Loading requests...</p>}
          {!requestsQuery.isLoading && requests.length === 0 && (
            <p className="community-status">No verification requests match these filters.</p>
          )}

          {requests.length > 0 && (
            <>
              <div className="admin-report-list">
                {requests.map((request) => (
                  <div className="admin-report-card" key={request.id}>
                    <div className="admin-report-header">
                      <span className="activity-log-action-badge">
                        {METHOD_BADGES[request.verification_method] ??
                          request.verification_method}
                      </span>
                      <span className="admin-report-title">
                        <button
                          className="admin-link-button"
                          type="button"
                          onClick={() => setSelectedId(selectedId === request.id ? null : request.id)}
                        >
                          {request.player_name}
                        </button>{" "}
                        #{request.id}
                      </span>
                      <span className="admin-report-meta">
                        {request.community_username ?? "unknown"} · {request.status} ·{" "}
                        {formatMemberSince(request.submitted_at ?? request.created_at)}
                      </span>
                    </div>

                    <div className="admin-report-actions">
                      <button
                        className="admin-link-button"
                        type="button"
                        onClick={() =>
                          setSelectedId(selectedId === request.id ? null : request.id)
                        }
                      >
                        {selectedId === request.id ? "Hide details" : "Review"}
                      </button>
                    </div>

                    {selectedId === request.id && (
                      <RequestDetail requestId={request.id} onChanged={invalidate} />
                    )}
                  </div>
                ))}
              </div>

              <div className="community-pagination">
                <button
                  className="button-ghost"
                  type="button"
                  disabled={offset === 0}
                  onClick={() => setOffset((current) => Math.max(0, current - PAGE_SIZE))}
                >
                  Previous
                </button>
                <span className="community-pagination-info">
                  {requestCount === 0
                    ? "0 requests"
                    : `${offset + 1}-${Math.min(offset + requests.length, requestCount)} of ${requestCount}`}
                </span>
                <button
                  className="button-ghost"
                  type="button"
                  disabled={!hasMoreRequests}
                  onClick={() => setOffset((current) => current + PAGE_SIZE)}
                >
                  Next
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {subTab === "links" && (
        <div className="admin-section">
          <div className="community-filters">
            <label>
              Status
              <select
                value={linkStatus}
                onChange={(event) => {
                  setLinkStatus(event.target.value);
                  setLinksOffset(0);
                }}
              >
                <option value="">All statuses</option>
                <option value="active">Active</option>
                <option value="revoked">Revoked</option>
                <option value="suspended">Suspended</option>
              </select>
            </label>
          </div>

          {linksQuery.isLoading && <p className="community-status">Loading links...</p>}
          {!linksQuery.isLoading && links.length === 0 && (
            <p className="community-status">No linked accounts found.</p>
          )}

          {links.map((link) => (
            <div className="admin-report-card" key={link.id}>
              <div className="admin-report-header">
                <span className="activity-log-action-badge">{link.status}</span>
                <span className="admin-report-title">{link.player_name}</span>
                <span className="admin-report-meta">
                  {link.community_username ?? "unknown"} · approved{" "}
                  {link.approved_at ? formatMemberSince(link.approved_at) : "unknown"}
                  {link.revocation_reason ? ` · ${link.revocation_reason}` : ""}
                </span>
              </div>
              <div className="admin-report-actions">
                {link.status !== "active" && (
                  <button
                    className="button-ghost"
                    type="button"
                    disabled={linkMutation.isPending}
                    onClick={() =>
                      linkMutation.mutate({ linkId: link.id, status: "active", reason: "" })
                    }
                  >
                    Restore
                  </button>
                )}
                {link.status === "active" && (
                  <>
                    <button
                      className="button-ghost"
                      type="button"
                      disabled={linkMutation.isPending}
                      onClick={() => {
                        const reason = window.prompt("Reason for suspending this link?");
                        if (!reason) return;
                        linkMutation.mutate({ linkId: link.id, status: "suspended", reason });
                      }}
                    >
                      Suspend
                    </button>
                    <button
                      className="button-ghost"
                      type="button"
                      disabled={linkMutation.isPending}
                      onClick={() => {
                        const reason = window.prompt("Reason for revoking this link?");
                        if (!reason) return;
                        linkMutation.mutate({ linkId: link.id, status: "revoked", reason });
                      }}
                    >
                      Revoke
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}

          {links.length > 0 && (
            <div className="community-pagination">
              <button
                className="button-ghost"
                type="button"
                disabled={linksOffset === 0}
                onClick={() => setLinksOffset((current) => Math.max(0, current - PAGE_SIZE))}
              >
                Previous
              </button>
              <span className="community-pagination-info">
                {linkCount === 0
                  ? "0 links"
                  : `${linksOffset + 1}-${Math.min(linksOffset + links.length, linkCount)} of ${linkCount}`}
              </span>
              <button
                className="button-ghost"
                type="button"
                disabled={!hasMoreLinks}
                onClick={() => setLinksOffset((current) => current + PAGE_SIZE)}
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}