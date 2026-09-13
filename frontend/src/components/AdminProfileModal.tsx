import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { BannerImage } from "./BannerImage";
import { UserAvatar } from "./UserAvatar";
import { useBodyScrollLock } from "../hooks/useBodyScrollLock";
import { COUNTRIES } from "../lib/countries";
import {
  adminDisableProfile,
  adminEnableProfile,
  adminResetProfile,
  getAdminCommunityProfile,
  updateAdminCommunityProfile
} from "../services/adminCommunity";
import { getPublicData } from "../services/publicData";
import type { AdminProfileDetail, CommunityProfileUpdate } from "../types/api";

function textValue(row: Record<string, unknown>, camel: string, lower: string): string {
  return String(row[camel] ?? row[lower] ?? "");
}

type AdminProfileFormProps = {
  profile: AdminProfileDetail;
  onChanged: () => void;
  onClose: () => void;
};

function AdminProfileForm({ profile, onChanged, onClose }: AdminProfileFormProps) {
  const queryClient = useQueryClient();
  const [bio, setBio] = useState(profile.bio ?? "");
  const [country, setCountry] = useState(profile.country ?? "");
  const [favoriteVehicleId, setFavoriteVehicleId] = useState(
    profile.favorite_vehicle_id != null ? String(profile.favorite_vehicle_id) : ""
  );
  const [favoriteMapId, setFavoriteMapId] = useState(
    profile.favorite_map_id != null ? String(profile.favorite_map_id) : ""
  );
  const [profilePublic, setProfilePublic] = useState(profile.profile_public);
  const [showCountry, setShowCountry] = useState(profile.show_country);
  const [showBio, setShowBio] = useState(profile.show_bio);
  const [showFavoriteVehicle, setShowFavoriteVehicle] = useState(profile.show_favorite_vehicle);
  const [showFavoriteMap, setShowFavoriteMap] = useState(profile.show_favorite_map);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const vehiclesQuery = useQuery({
    queryKey: ["public-data", "vehicles"],
    queryFn: () => getPublicData("vehicles")
  });
  const mapsQuery = useQuery({
    queryKey: ["public-data", "maps"],
    queryFn: () => getPublicData("maps")
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["admin", "community", "profiles"] });
    queryClient.invalidateQueries({ queryKey: ["admin", "community", "profile", profile.id] });
    queryClient.invalidateQueries({ queryKey: ["admin", "activity-logs"] });
  }

  const saveMutation = useMutation({
    mutationFn: (payload: CommunityProfileUpdate) => updateAdminCommunityProfile(profile.id, payload),
    onSuccess: () => {
      setMessage("Profile changes saved.");
      setError("");
      invalidate();
      onChanged();
    },
    onError: (saveError) => {
      setError(saveError.message);
      setMessage("");
    }
  });

  const actionMutation = useMutation({
    mutationFn: (action: "disable" | "enable" | "reset") => {
      if (action === "disable") return adminDisableProfile(profile.id);
      if (action === "enable") return adminEnableProfile(profile.id);
      return adminResetProfile(profile.id);
    },
    onSuccess: (result, action) => {
      const label = action === "disable" ? "disabled" : action === "enable" ? "enabled" : "reset";
      setMessage(`Profile ${label}.`);
      setError("");
      invalidate();
      onChanged();
    },
    onError: (actionError) => {
      setError(actionError.message);
      setMessage("");
    }
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");
    saveMutation.mutate({
      bio: bio.trim(),
      country: country || null,
      favorite_vehicle_id: favoriteVehicleId ? Number(favoriteVehicleId) : null,
      favorite_map_id: favoriteMapId ? Number(favoriteMapId) : null,
      profile_public: profilePublic,
      show_country: showCountry,
      show_bio: showBio,
      show_favorite_vehicle: showFavoriteVehicle,
      show_favorite_map: showFavoriteMap
    });
  }

  return (
    <div className="modal-overlay">
      <div className="modal-panel form-container" role="dialog" aria-modal="true" aria-labelledby="admin-profile-title">
        <h2 id="admin-profile-title">Edit Community Profile</h2>
        <div className="admin-profile-summary">
          <UserAvatar avatarUrl={profile.discord_avatar} name={profile.discord_username} size={36} />
          <div>
            <p className="admin-profile-name">{profile.discord_username}</p>
            <p className="admin-profile-meta">
              hcr2.xyz #{profile.id} · {profile.admin_disabled ? "Disabled" : "Active"} · {profile.open_reports} open
              report{profile.open_reports === 1 ? "" : "s"}
            </p>
          </div>
        </div>

        <BannerImage
          communityId={profile.id}
          bannerUpdatedAt={profile.banner_updated_at}
          className="admin-profile-banner"
          alt="Profile banner"
        />

        <form onSubmit={handleSubmit}>
          <label>
            Bio
            <textarea
              value={bio}
              onChange={(event) => setBio(event.target.value.slice(0, 500))}
              maxLength={500}
            />
          </label>
          <label>
            Country
            <select value={country} onChange={(event) => setCountry(event.target.value)}>
              <option value="">Not shared</option>
              {COUNTRIES.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <div className="profile-settings-row">
            <label>
              Favorite Vehicle
              <select
                value={favoriteVehicleId}
                onChange={(event) => setFavoriteVehicleId(event.target.value)}
              >
                <option value="">None</option>
                {(vehiclesQuery.data ?? []).map((row) => (
                  <option
                    key={textValue(row, "idVehicle", "idvehicle")}
                    value={textValue(row, "idVehicle", "idvehicle")}
                  >
                    {textValue(row, "nameVehicle", "namevehicle")}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Favorite Map
              <select value={favoriteMapId} onChange={(event) => setFavoriteMapId(event.target.value)}>
                <option value="">None</option>
                {(mapsQuery.data ?? []).map((row) => (
                  <option key={textValue(row, "idMap", "idmap")} value={textValue(row, "idMap", "idmap")}>
                    {textValue(row, "nameMap", "namemap")}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <fieldset className="frontend-fieldset profile-settings-toggles">
            <legend>Visibility</legend>
            <label>
              <input
                type="checkbox"
                checked={profilePublic}
                onChange={(event) => setProfilePublic(event.target.checked)}
              />
              Public profile
            </label>
            <label>
              <input
                type="checkbox"
                checked={showCountry}
                onChange={(event) => setShowCountry(event.target.checked)}
              />
              Show country
            </label>
            <label>
              <input type="checkbox" checked={showBio} onChange={(event) => setShowBio(event.target.checked)} />
              Show bio
            </label>
            <label>
              <input
                type="checkbox"
                checked={showFavoriteVehicle}
                onChange={(event) => setShowFavoriteVehicle(event.target.checked)}
              />
              Show favorite vehicle
            </label>
            <label>
              <input
                type="checkbox"
                checked={showFavoriteMap}
                onChange={(event) => setShowFavoriteMap(event.target.checked)}
              />
              Show favorite map
            </label>
          </fieldset>

          <div className="frontend-modal-actions">
            <button
              type="button"
              disabled={actionMutation.isPending}
              onClick={() => actionMutation.mutate("disable")}
            >
              Disable
            </button>
            <button
              type="button"
              disabled={actionMutation.isPending}
              onClick={() => actionMutation.mutate("enable")}
            >
              Enable
            </button>
            <button
              type="button"
              className="button-ghost"
              disabled={actionMutation.isPending}
              onClick={() => {
                if (window.confirm("Reset this member's bio, banner and favorites?")) {
                  actionMutation.mutate("reset");
                }
              }}
            >
              Reset Customizations
            </button>
            <button type="submit" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? "Saving..." : "Save Changes"}
            </button>
            <button type="button" className="button-ghost" onClick={onClose}>
              Close
            </button>
          </div>
        </form>
        {message && <p className="frontend-message">{message}</p>}
        {error && <p className="frontend-error">{error}</p>}
      </div>
    </div>
  );
}

type AdminProfileModalProps = {
  profileId: number;
  onChanged: () => void;
  onClose: () => void;
};

export function AdminProfileModal({ profileId, onChanged, onClose }: AdminProfileModalProps) {
  useBodyScrollLock();
  const detailQuery = useQuery({
    queryKey: ["admin", "community", "profile", profileId],
    queryFn: () => getAdminCommunityProfile(profileId)
  });

  if (detailQuery.isLoading) {
    return (
      <div className="modal-overlay">
        <div className="modal-panel form-container">
          <p>Loading profile...</p>
        </div>
      </div>
    );
  }

  if (detailQuery.isError || !detailQuery.data) {
    return (
      <div className="modal-overlay">
        <div className="modal-panel form-container">
          <p className="frontend-error">Could not load this profile.</p>
          <div className="frontend-modal-actions">
            <button type="button" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <AdminProfileForm key={detailQuery.data.id} profile={detailQuery.data} onChanged={onChanged} onClose={onClose} />;
}