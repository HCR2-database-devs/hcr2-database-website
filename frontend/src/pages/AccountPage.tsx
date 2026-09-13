import { Link } from "react-router-dom";

import { ProfileSettingsSection } from "../components/ProfileSettingsSection";
import { UserAvatar } from "../components/UserAvatar";
import { useAuthStatus } from "../hooks/useAuthStatus";
import { formatMemberSince } from "../lib/format";

export function AccountPage() {
  const { data: authStatus, isLoading } = useAuthStatus();

  if (isLoading) {
    return (
      <div className="account-page">
        <div className="account-card">
          <h1>Your Account</h1>
          <p>Checking access...</p>
        </div>
      </div>
    );
  }

  if (!authStatus?.logged) {
    return (
      <div className="account-page">
        <div className="account-card">
          <h1>Your Account</h1>
          <p className="frontend-error">You need to sign in to access your account.</p>
          <button
            className="button"
            type="button"
            onClick={() => {
              window.location.href = "https://auth.hcr2.xyz/login";
            }}
          >
            Sign in with Discord
          </button>
        </div>
      </div>
    );
  }

  const community = authStatus.community;
  const displayName = community?.discord_username || authStatus.username || authStatus.id || "HCR2 user";
  const avatarUrl = authStatus.avatar ?? community?.discord_avatar ?? null;
  const memberSince = formatMemberSince(community?.created_at);

  return (
    <div className="account-page">
      {community?.admin_disabled && (
        <p className="profile-disabled-notice">
          Your community profile has been disabled by an admin. Other users cannot see it. You can still edit it below;
          contact the admins if you believe this is a mistake.
        </p>
      )}
      <div className="account-card">
        <h1>Your Account</h1>
        <div className="account-profile">
          <UserAvatar avatarUrl={avatarUrl} name={displayName} size={88} />
          <div className="account-profile-copy">
            <p className="account-name">{displayName}</p>
            <p className="account-status">
              <span className="account-check" aria-hidden="true">
                ✓
              </span>{" "}
              Discord connected
            </p>
          </div>
        </div>
        <dl className="account-details">
          <div>
            <dt>Member since</dt>
            <dd>{memberSince ?? "Unknown"}</dd>
          </div>
          <div>
            <dt>Account established</dt>
            <dd>{community ? `hcr2.xyz #${community.id}` : "n/a"}</dd>
          </div>
        </dl>

        {community && (
          <Link className="button account-view-profile" to={`/community/${community.id}`}>
            View my public profile
          </Link>
        )}
      </div>

      {community && <ProfileSettingsSection key={community.id} profile={community} />}
    </div>
  );
}