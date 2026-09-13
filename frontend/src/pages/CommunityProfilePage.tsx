import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { BannerImage } from "../components/BannerImage";
import { BetaBadge } from "../components/BetaBadge";
import { CountryFlag } from "../components/CountryFlag";
import { FeatureGate } from "../components/FeatureGate";
import { ReportProfileModal } from "../components/ReportProfileModal";
import { UserAvatar } from "../components/UserAvatar";
import { useAuthStatus } from "../hooks/useAuthStatus";
import { countryName } from "../lib/countries";
import { useCanUseFeature } from "../lib/features";
import { formatMemberSince } from "../lib/format";
import { getCommunityProfile } from "../services/community";

export function CommunityProfilePage() {
  return (
    <FeatureGate feature="community_profiles">
      <CommunityProfileContent />
    </FeatureGate>
  );
}

function CommunityProfileContent() {
  const { id } = useParams<{ id: string }>();
  const communityId = Number(id);
  const { data: authStatus } = useAuthStatus();
  const canReportFeature = useCanUseFeature("profile_reporting");
  const [reportOpen, setReportOpen] = useState(false);
  const [reported, setReported] = useState(false);

  const profileQuery = useQuery({
    queryKey: ["community", "profile", communityId],
    queryFn: () => getCommunityProfile(communityId),
    enabled: Number.isInteger(communityId) && communityId > 0,
    retry: false
  });

  if (!Number.isInteger(communityId) || communityId <= 0) {
    return (
      <div className="page-container">
        <p className="frontend-error">Invalid profile link.</p>
      </div>
    );
  }

  if (profileQuery.isLoading) {
    return (
      <div className="page-container">
        <p className="community-status">Loading profile...</p>
      </div>
    );
  }

  if (profileQuery.isError || !profileQuery.data) {
    return (
      <div className="page-container">
        <p className="frontend-error">
          This profile is not available. It may be set to private or the link may be wrong.
        </p>
        <Link className="button" to="/community">
          Back to Community
        </Link>
      </div>
    );
  }

  const profile = profileQuery.data;
  const memberSince = formatMemberSince(profile.created_at);
  const isOwner = profile.is_owner || authStatus?.community?.id === profile.id;
  const canReport = authStatus?.logged === true && !isOwner && canReportFeature;
  const lastUpdated = profile.updated_at ? formatMemberSince(profile.updated_at) : null;

  return (
    <div className="page-container community-profile-page">
      {isOwner && profile.admin_disabled && (
        <p className="profile-disabled-notice">
          This profile has been disabled by an admin and is hidden from other users. You can manage it from{" "}
          <Link to="/account">your account page</Link>.
        </p>
      )}

      <BannerImage
        communityId={profile.id}
        bannerUpdatedAt={profile.banner_updated_at}
        className="community-profile-banner"
      />

      <div className="community-profile-card">
        <div className="community-profile-head">
          <UserAvatar avatarUrl={profile.discord_avatar} name={profile.discord_username} size={88} />
          <div className="community-profile-copy">
            <h1>
              {profile.discord_username}
              <BetaBadge feature="community_profiles" />
              {isOwner && <span className="profile-owner-badge">You</span>}
            </h1>
            <p className="community-profile-meta">
              hcr2.xyz #{profile.id} · Member since {memberSince ?? "unknown"}
            </p>
          </div>
          {canReport && (
            <button className="button-ghost community-report-btn" type="button" onClick={() => setReportOpen(true)}>
              Report Profile
            </button>
          )}
        </div>

        <dl className="community-profile-details">
          {profile.show_country && profile.country && (
            <div>
              <dt>Country</dt>
              <dd>
                <CountryFlag code={profile.country} /> {countryName(profile.country)}
              </dd>
            </div>
          )}
          {profile.show_bio && profile.bio && (
            <div className="community-profile-bio-row">
              <dt>Bio</dt>
              <dd>{profile.bio}</dd>
            </div>
          )}
          {profile.show_favorite_vehicle && profile.favorite_vehicle_name && (
            <div>
              <dt>Favorite vehicle</dt>
              <dd>{profile.favorite_vehicle_name}</dd>
            </div>
          )}
          {profile.show_favorite_map && profile.favorite_map_name && (
            <div>
              <dt>Favorite map</dt>
              <dd>{profile.favorite_map_name}</dd>
            </div>
          )}
          {!profile.show_country &&
            !profile.show_bio &&
            !profile.show_favorite_vehicle &&
            !profile.show_favorite_map && (
              <div>
                <dd>This member has not shared any extra details yet.</dd>
              </div>
            )}
        </dl>

        {isOwner && (
          <p className="community-profile-note">
            This is your public profile. Manage it from{" "}
            <Link to="/account">your account page</Link>
            {lastUpdated ? <> · Last updated {lastUpdated}</> : null}.
          </p>
        )}
      </div>

      {reportOpen && (
        <ReportProfileModal
          profileId={profile.id}
          profileName={profile.discord_username}
          onClose={() => setReportOpen(false)}
          onReported={() => setReported(true)}
        />
      )}
      {reported && !reportOpen && <p className="frontend-message">Report submitted. Thank you.</p>}
    </div>
  );
}