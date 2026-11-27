import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { CopyProfileLinkButton } from "../components/CopyProfileLinkButton";
import { LinkedHcr2AccountSection } from "../components/hcr2Link/LinkedHcr2AccountSection";
import { ProfileSettingsSection } from "../components/ProfileSettingsSection";
import { ProgressionSummaryCard } from "../components/ProgressionSummaryCard";
import { UserAvatar } from "../components/UserAvatar";
import { useAuthStatus } from "../hooks/useAuthStatus";
import { useCanUseFeature } from "../lib/features";
import { formatMemberSince } from "../lib/format";
import { getMemberBadges, getOwnProgression } from "../services/badges";
import { communityAvatar, communityDisplayName, discordAvatarUrl } from "../services/community";

export function AccountPage() {
  const { data: authStatus, isLoading } = useAuthStatus();
  const canViewProfile = useCanUseFeature("community_profiles");
  const canCustomizeProfile = useCanUseFeature("profile_customization");
  const canLinkHcr2Account = useCanUseFeature("hcr2_account_linking");
  const canUseBadges = useCanUseFeature("community_badges");
  const canUseXp = useCanUseFeature("community_xp");
  const progressionQuery = useQuery({
    queryKey: ["progression", "me"],
    queryFn: getOwnProgression,
    enabled: authStatus?.logged === true && canUseXp,
    retry: false
  });
  const badgesQuery = useQuery({
    queryKey: ["badges", "profile", authStatus?.community?.id],
    queryFn: () => getMemberBadges(Number(authStatus?.community?.id)),
    enabled: authStatus?.logged === true && canUseBadges && Boolean(authStatus?.community?.id),
    retry: false
  });

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
  const displayName = communityDisplayName(community) || authStatus.username || authStatus.id || "HCR2 user";
  const avatarUrl = discordAvatarUrl(authStatus.avatar ?? communityAvatar(community), authStatus.id);
  const memberSince = formatMemberSince(community?.created_at);
  const needsOnboarding = community !== undefined && community !== null && !community.username;

  return (
    <div className="account-page">
      {community?.admin_disabled && (
        <p className="profile-disabled-notice">
          Your community profile has been disabled by an admin. Other users cannot see it. You can still edit it below;
          contact the admins if you believe this is a mistake.
        </p>
      )}
      {needsOnboarding && (
        <div className="account-card">
          <h1>Choose a community username</h1>
          <p className="frontend-message">
            You need a username before you can take part in the community — the member directory,
            your public profile and reports are hidden until you choose one.
          </p>
          <Link className="button" to="/onboarding">
            Choose my username
          </Link>
        </div>
      )}
      <div className="account-card">
        <h1>Your Account</h1>
        <div className="account-profile">
          <UserAvatar avatarUrl={avatarUrl} name={displayName} size={88} />
          <div className="account-profile-copy">
            <p className="account-name">{displayName}</p>
            {community?.username && (
              <p className="account-username">@{community.username}</p>
            )}
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
          {community?.hcr2_player_name && (
            <div className="account-details-linked">
              <dt>Linked HCR2 player name</dt>
              <dd>
                <span className="status-pill status-pill--verified">Verified</span>{" "}
                <span className="account-details-linked-name">{community.hcr2_player_name}</span>
                {community.hcr2_link_verified_at && (
                  <span className="account-details-linked-since">
                    {formatMemberSince(community.hcr2_link_verified_at)}
                  </span>
                )}
              </dd>
            </div>
          )}
        </dl>

        {community && canViewProfile && (
          <div className="account-profile-actions">
            <Link className="button account-view-profile" to={`/community/${community.id}`}>
              View my public profile
            </Link>
            <CopyProfileLinkButton communityId={community.id} />
          </div>
        )}
      </div>

      {(canUseBadges || canUseXp) && community && !needsOnboarding && (
        <div className="account-card account-progression">
          <h2>Community progression</h2>
          <div className="account-progression__grid">
            {canUseXp && progressionQuery.data && (
              <ProgressionSummaryCard progression={progressionQuery.data} />
            )}
            {canUseBadges && badgesQuery.data && (
              <div className="account-progression__badges">
                <div>
                  <strong>{badgesQuery.data.count}</strong>
                  <span>badges unlocked</span>
                </div>
                <Link className="button" to="/badges">
                  Open badge collection
                </Link>
              </div>
            )}
          </div>
        </div>
      )}

      {community && !needsOnboarding && canCustomizeProfile && (
        <ProfileSettingsSection key={community.id} profile={community} />
      )}

      {community && !needsOnboarding && canLinkHcr2Account && (
        <LinkedHcr2AccountSection
          key={community.id}
          communityUsername={community.username}
          discordUsername={community.discord_username}
        />
      )}
    </div>
  );
}