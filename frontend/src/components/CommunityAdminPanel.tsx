import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AdminProfileModal } from "./AdminProfileModal";
import { UserAvatar } from "./UserAvatar";
import {
  adminRejectReport,
  adminResolveReport,
  getAdminCommunityProfiles,
  getAdminCommunityReports
} from "../services/adminCommunity";
import { formatMemberSince } from "../lib/format";
import { discordAvatarUrl } from "../services/community";

const PAGE_SIZE = 20;

type SubTab = "profiles" | "reports";

const REPORT_STATUSES = [
  { value: "open", label: "Open" },
  { value: "resolved", label: "Resolved" },
  { value: "rejected", label: "Rejected" }
];

export function CommunityAdminPanel() {
  const queryClient = useQueryClient();
  const [subTab, setSubTab] = useState<SubTab>("profiles");
  const [search, setSearch] = useState("");
  const [submittedSearch, setSubmittedSearch] = useState("");
  const [profilesOffset, setProfilesOffset] = useState(0);
  const [reportsStatus, setReportsStatus] = useState("");
  const [reportsOffset, setReportsOffset] = useState(0);
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null);

  const profilesQuery = useQuery({
    queryKey: ["admin", "community", "profiles", submittedSearch, profilesOffset],
    queryFn: () =>
      getAdminCommunityProfiles({
        search: submittedSearch || undefined,
        limit: PAGE_SIZE,
        offset: profilesOffset
      })
  });

  const reportsQuery = useQuery({
    queryKey: ["admin", "community", "reports", reportsStatus, reportsOffset],
    queryFn: () =>
      getAdminCommunityReports({
        status: reportsStatus || undefined,
        limit: PAGE_SIZE,
        offset: reportsOffset
      })
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["admin", "community"] });
    queryClient.invalidateQueries({ queryKey: ["admin", "activity-logs"] });
  }

  const reportAction = useMutation({
    mutationFn: (params: { id: number; action: "resolve" | "reject" }) =>
      params.action === "resolve"
        ? adminResolveReport(params.id)
        : adminRejectReport(params.id),
    onSuccess: () => {
      invalidate();
    },
    onError: () => {
      // surface via query refetch errors silently
    }
  });

  function handleProfileSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmittedSearch(search.trim());
    setProfilesOffset(0);
  }

  const profiles = profilesQuery.data?.profiles ?? [];
  const profileCount = profilesQuery.data?.count ?? 0;
  const hasMoreProfiles = profilesOffset + profiles.length < profileCount;

  const reports = reportsQuery.data?.reports ?? [];
  const reportCount = reportsQuery.data?.count ?? 0;
  const hasMoreReports = reportsOffset + reports.length < reportCount;

  return (
    <div className="admin-community-panel">
      <nav className="admin-subtabs" aria-label="Community admin sections">
        <button
          type="button"
          className={`admin-subtab${subTab === "profiles" ? " admin-subtab--active" : ""}`}
          onClick={() => setSubTab("profiles")}
        >
          Profiles
        </button>
        <button
          type="button"
          className={`admin-subtab${subTab === "reports" ? " admin-subtab--active" : ""}`}
          onClick={() => setSubTab("reports")}
        >
          Reports
          <span className="admin-subtab-count">{reportsStatus === "" ? "all" : reportsStatus}</span>
        </button>
      </nav>

      {subTab === "profiles" && (
        <div className="admin-section">
          <form className="community-filters" onSubmit={handleProfileSearch}>
            <label>
              Search
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Find a member..."
                maxLength={50}
              />
            </label>
            <button className="button" type="submit">
              Search
            </button>
          </form>

          {profilesQuery.isLoading && <p className="community-status">Loading profiles...</p>}
          {!profilesQuery.isLoading && profiles.length === 0 && (
            <p className="community-status">No members found.</p>
          )}

          {profiles.length > 0 && (
            <>
              <div className="admin-profile-table">
                {profiles.map((profile) => (
                  <button
                    key={profile.id}
                    type="button"
                    className="admin-profile-row"
                    onClick={() => setSelectedProfileId(profile.id)}
                  >
                    <UserAvatar
                      avatarUrl={discordAvatarUrl(profile.discord_avatar)}
                      name={profile.username ?? profile.discord_username}
                      size={32}
                    />
                    <span className="admin-profile-row-name">
                      {profile.username ?? profile.discord_username}
                      {profile.username != null && profile.username !== profile.discord_username && (
                        <span className="admin-profile-row-sub"> ({profile.discord_username})</span>
                      )}
                    </span>
                    <span className="admin-profile-row-meta">#{profile.id}</span>
                    <span className="admin-profile-row-meta">
                      {profile.admin_disabled ? "Disabled" : profile.profile_public ? "Public" : "Private"}
                    </span>
                    <span
                      className={`admin-profile-row-meta${profile.open_reports > 0 ? " admin-open-reports" : ""}`}
                    >
                      {profile.open_reports} open report{profile.open_reports === 1 ? "" : "s"}
                    </span>
                  </button>
                ))}
              </div>
              <div className="community-pagination">
                <button
                  className="button-ghost"
                  type="button"
                  disabled={profilesOffset === 0}
                  onClick={() => setProfilesOffset((current) => Math.max(0, current - PAGE_SIZE))}
                >
                  Previous
                </button>
                <span className="community-pagination-info">
                  {profileCount === 0
                    ? "0 profiles"
                    : `${profilesOffset + 1}-${Math.min(profilesOffset + profiles.length, profileCount)} of ${profileCount} profiles`}
                </span>
                <button
                  className="button-ghost"
                  type="button"
                  disabled={!hasMoreProfiles}
                  onClick={() => setProfilesOffset((current) => current + PAGE_SIZE)}
                >
                  Next
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {subTab === "reports" && (
        <div className="admin-section">
          <div className="community-filters">
            <label>
              Status
              <select
                value={reportsStatus}
                onChange={(event) => {
                  setReportsStatus(event.target.value);
                  setReportsOffset(0);
                }}
              >
                <option value="">All statuses</option>
                {REPORT_STATUSES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {reportsQuery.isLoading && <p className="community-status">Loading reports...</p>}
          {!reportsQuery.isLoading && reports.length === 0 && (
            <p className="community-status">No reports found.</p>
          )}

          {reports.length > 0 && (
            <>
              <div className="admin-report-list">
                {reports.map((report) => (
                  <div className="admin-report-card" key={report.id}>
                    <div className="admin-report-header">
                      <span className="activity-log-action-badge">{report.category}</span>
                      <span className="admin-report-title">
                        <button
                          className="admin-link-button"
                          type="button"
                          onClick={() => setSelectedProfileId(report.community_user_id)}
                        >
                          {report.target_name}
                        </button>{" "}
                        #{report.community_user_id}
                      </span>
                      <span className="admin-report-meta">
                        Reported by {report.reporter_name} · {formatMemberSince(report.created_at)}
                      </span>
                    </div>
                    {report.reason && <p className="admin-report-reason">{report.reason}</p>}
                    {report.resolution_note && (
                      <p className="admin-report-resolution">Note: {report.resolution_note}</p>
                    )}
                    {report.status === "open" && (
                      <div className="admin-report-actions">
                        <button
                          type="button"
                          className="button"
                          disabled={reportAction.isPending}
                          onClick={() => reportAction.mutate({ id: report.id, action: "resolve" })}
                        >
                          Resolve
                        </button>
                        <button
                          type="button"
                          className="button-ghost"
                          disabled={reportAction.isPending}
                          onClick={() => reportAction.mutate({ id: report.id, action: "reject" })}
                        >
                          Reject
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div className="community-pagination">
                <button
                  className="button-ghost"
                  type="button"
                  disabled={reportsOffset === 0}
                  onClick={() => setReportsOffset((current) => Math.max(0, current - PAGE_SIZE))}
                >
                  Previous
                </button>
                <span className="community-pagination-info">
                  {reportCount === 0 ? 0 : reportsOffset + 1}-{Math.min(reportsOffset + reports.length, reportCount)} of{" "}
                  {reportCount}
                </span>
                <button
                  className="button-ghost"
                  type="button"
                  disabled={!hasMoreReports}
                  onClick={() => setReportsOffset((current) => current + PAGE_SIZE)}
                >
                  Next
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {selectedProfileId != null && (
        <AdminProfileModal
          profileId={selectedProfileId}
          onChanged={() => invalidate()}
          onClose={() => setSelectedProfileId(null)}
        />
      )}
    </div>
  );
}