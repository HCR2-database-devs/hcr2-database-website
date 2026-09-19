import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { COUNTRIES } from "../lib/countries";
import {
  communityBannerUrl,
  compressBannerFile,
  removeCommunityBanner,
  setCommunityUsername,
  updateCommunityProfile,
  uploadCommunityBanner
} from "../services/community";
import { getPublicData } from "../services/publicData";
import type { CommunityAccount } from "../types/api";
import { BannerCropModal } from "./BannerCropModal";
import { BetaBadge } from "./BetaBadge";

const MAX_BIO_LENGTH = 500;

function textValue(row: Record<string, unknown>, camel: string, lower: string): string {
  return String(row[camel] ?? row[lower] ?? "");
}

type ProfileSettingsSectionProps = {
  profile: CommunityAccount;
};

export function ProfileSettingsSection({ profile }: ProfileSettingsSectionProps) {
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
  const [showDiscordUsername, setShowDiscordUsername] = useState(profile.show_discord_username);
  const [showDiscordAvatar, setShowDiscordAvatar] = useState(profile.show_discord_avatar);
  const [newUsername, setNewUsername] = useState("");
  const [pendingBanner, setPendingBanner] = useState<File | null>(null);
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

  const saveMutation = useMutation({
    mutationFn: updateCommunityProfile,
    onSuccess: () => {
      setMessage("Profile updated.");
      setError("");
      queryClient.invalidateQueries({ queryKey: ["auth-status"] });
      queryClient.invalidateQueries({ queryKey: ["community"] });
    },
    onError: (saveError) => {
      setError(saveError.message);
      setMessage("");
    }
  });

  const usernameMutation = useMutation({
    mutationFn: setCommunityUsername,
    onSuccess: () => {
      setMessage("Username updated. You can change it again in 30 days.");
      setError("");
      setNewUsername("");
      queryClient.invalidateQueries({ queryKey: ["auth-status"] });
      queryClient.invalidateQueries({ queryKey: ["community"] });
    },
    onError: (usernameError) => {
      setError(usernameError.message);
      setMessage("");
    }
  });

  const bannerMutation = useMutation({
    mutationFn: uploadCommunityBanner,
    onSuccess: () => {
      setMessage("Banner updated. (WebP, max 2048px per side)");
      setError("");
      queryClient.invalidateQueries({ queryKey: ["auth-status"] });
    },
    onError: (bannerError) => {
      setError(bannerError.message);
      setMessage("");
    }
  });

  const bannerRemoveMutation = useMutation({
    mutationFn: removeCommunityBanner,
    onSuccess: () => {
      setMessage("Banner removed.");
      setError("");
      queryClient.invalidateQueries({ queryKey: ["auth-status"] });
    },
    onError: (bannerError) => {
      setError(bannerError.message);
      setMessage("");
    }
  });

  function handleBannerChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setMessage("");
    setError("");
    setPendingBanner(file);
  }

  async function handleBannerConfirm(selectedFile: File) {
    setPendingBanner(null);
    setMessage("");
    setError("");
    try {
      const prepared = await compressBannerFile(selectedFile);
      bannerMutation.mutate(prepared);
    } catch {
      bannerMutation.mutate(selectedFile);
    }
  }

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
      show_favorite_map: showFavoriteMap,
      show_discord_username: showDiscordUsername,
      show_discord_avatar: showDiscordAvatar
    });
  }

  function handleUsernameSubmit() {
    setMessage("");
    setError("");
    usernameMutation.mutate(newUsername);
  }

  return (
    <div className="account-card">
      <h1>
        Community Profile <BetaBadge feature="profile_customization" />
      </h1>
      <form className="profile-settings-form" onSubmit={handleSubmit}>
        <fieldset className="frontend-fieldset profile-settings-toggles">
          <legend>Community username</legend>
          <p className="profile-settings-hint">
            This is how you appear across the community. Changing it is limited to once every 30 days.
          </p>
          <label>
            Current username
            <input type="text" name="current_username" value={profile.username ?? ""} readOnly disabled />
          </label>
          <label>
            New username
            <input
              type="text"
              name="new_username"
              value={newUsername}
              maxLength={20}
              placeholder="3-20 characters: letters, numbers, spaces, '-' and '_'"
              onChange={(event) => {
                setNewUsername(event.target.value);
                setError("");
              }}
            />
          </label>
          <div className="frontend-modal-actions">
            <button
              type="button"
              className="button-ghost"
              disabled={newUsername.trim().length < 3 || usernameMutation.isPending}
              onClick={handleUsernameSubmit}
            >
              {usernameMutation.isPending ? "Saving..." : "Change username"}
            </button>
          </div>
        </fieldset>

        <label>
          Bio
          <textarea
            name="bio"
            value={bio}
            onChange={(event) => setBio(event.target.value.slice(0, MAX_BIO_LENGTH))}
            maxLength={MAX_BIO_LENGTH}
            placeholder="Tell the community about yourself (max 500 characters)"
          />
        </label>

        <label>
          Country
          <select name="country" value={country} onChange={(event) => setCountry(event.target.value)}>
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
              name="favorite_vehicle_id"
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
            <select name="favorite_map_id" value={favoriteMapId} onChange={(event) => setFavoriteMapId(event.target.value)}>
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
            Public profile (visible to other logged-in users)
          </label>
          <label>
            <input
              type="checkbox"
              checked={showCountry}
              onChange={(event) => setShowCountry(event.target.checked)}
            />
            Show my country
          </label>
          <label>
            <input
              type="checkbox"
              checked={showBio}
              onChange={(event) => setShowBio(event.target.checked)}
            />
            Show my bio
          </label>
          <label>
            <input
              type="checkbox"
              checked={showFavoriteVehicle}
              onChange={(event) => setShowFavoriteVehicle(event.target.checked)}
            />
            Show my favorite vehicle
          </label>
          <label>
            <input
              type="checkbox"
              checked={showFavoriteMap}
              onChange={(event) => setShowFavoriteMap(event.target.checked)}
            />
            Show my favorite map
          </label>
          <label>
            <input
              type="checkbox"
              checked={showDiscordUsername}
              onChange={(event) => setShowDiscordUsername(event.target.checked)}
            />
            Show my Discord username
          </label>
          <label>
            <input
              type="checkbox"
              checked={showDiscordAvatar}
              onChange={(event) => setShowDiscordAvatar(event.target.checked)}
            />
            Show my Discord avatar
          </label>
        </fieldset>

        <fieldset className="frontend-fieldset profile-settings-toggles">
          <legend>Banner</legend>
          {profile.banner_updated_at && (
            <img
              className="profile-banner-preview"
              src={communityBannerUrl(profile.id, profile.banner_updated_at) ?? undefined}
              alt="Current profile banner"
            />
          )}
          <div className="profile-settings-row">
            <label>
              Profile banner (PNG/JPG/WebP, max 2048px, ~3.6:1 ratio after cropping)
              <input
                type="file"
                name="banner"
                accept="image/png,image/jpeg,image/webp,image/gif"
                disabled={bannerMutation.isPending}
                onChange={handleBannerChange}
              />
            </label>
            {profile.banner_updated_at && (
              <button
                type="button"
                className="button-ghost"
                disabled={bannerRemoveMutation.isPending}
                onClick={() => bannerRemoveMutation.mutate()}
              >
                Remove Banner
              </button>
            )}
          </div>
        </fieldset>

        <div className="frontend-modal-actions">
          <button type="submit" disabled={saveMutation.isPending}>
            {saveMutation.isPending ? "Saving..." : "Save Profile"}
          </button>
        </div>
      </form>
      {message && <p className="frontend-message">{message}</p>}
      {error && <p className="frontend-error">{error}</p>}
      {pendingBanner && (
        <BannerCropModal
          file={pendingBanner}
          onCancel={() => setPendingBanner(null)}
          onConfirm={handleBannerConfirm}
        />
      )}
    </div>
  );
}