import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";

import { useAuthStatus } from "../hooks/useAuthStatus";
import { useCanUseFeature } from "../lib/features";
import { setCommunityUsername } from "../services/community";

const MIN_USERNAME_LENGTH = 3;
const MAX_USERNAME_LENGTH = 20;

export function OnboardingPage() {
  const { data: authStatus, isLoading } = useAuthStatus();
  const canUseDiscordAccounts = useCanUseFeature("discord_accounts");
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [error, setError] = useState("");

  const usernameMutation = useMutation({
    mutationFn: setCommunityUsername,
    onSuccess: async () => {
      setError("");
      await queryClient.invalidateQueries({ queryKey: ["auth-status"] });
      navigate("/account", { replace: true });
    },
    onError: (mutationError) => {
      setError(mutationError.message);
    }
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    usernameMutation.mutate(username);
  }

  if (isLoading) {
    return (
      <div className="page-container">
        <p className="frontend-message">Checking access...</p>
      </div>
    );
  }

  if (!authStatus?.logged) {
    return (
      <div className="page-container">
        <div className="account-card">
          <h1>Choose your username</h1>
          <p className="frontend-error">You need to sign in to choose a username.</p>
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

  if (!canUseDiscordAccounts || !authStatus.community) {
    return (
      <div className="page-container">
        <div className="account-card">
          <h1>Community usernames</h1>
          <p className="frontend-message">
            Community usernames are not available to you yet. Visit the{" "}
            <Link to="/account">account page</Link> to check your access.
          </p>
        </div>
      </div>
    );
  }

  if (authStatus.community.username) {
    return (
      <div className="page-container">
        <div className="account-card">
          <h1>You&apos;re all set</h1>
          <p className="frontend-message">
            Your community username is <strong>{authStatus.community.username}</strong>.
          </p>
          <Link className="button" to="/account">
            Go to your account
          </Link>
        </div>
      </div>
    );
  }

  const canSubmit = username.trim().length >= MIN_USERNAME_LENGTH;

  return (
    <div className="page-container">
      <div className="account-card onboarding-card">
        <h1>Choose your community username</h1>
        <p className="onboarding-intro">
          Your username is how you&apos;ll appear in the HCR2 community: the member directory, on
          your public profile and next to your reports. You can change it once every 30 days.
        </p>
        <form className="profile-settings-form" onSubmit={handleSubmit}>
          <label>
            Username
            <input
              type="text"
              name="username"
              value={username}
              autoFocus
              maxLength={MAX_USERNAME_LENGTH}
              placeholder="e.g. HillClimbPro"
              onChange={(event) => {
                setUsername(event.target.value);
                setError("");
              }}
            />
          </label>
          <p className="onboarding-hint">
            {MIN_USERNAME_LENGTH}-{MAX_USERNAME_LENGTH} characters. Letters, numbers, spaces,
            &quot;-&quot; and &quot;_&quot; only. Choose something respectful — it can be changed,
            but not very often.
          </p>
          <div className="frontend-modal-actions">
            <button type="submit" disabled={!canSubmit || usernameMutation.isPending}>
              {usernameMutation.isPending ? "Saving..." : "Choose username"}
            </button>
          </div>
        </form>
        {error && <p className="frontend-error">{error}</p>}
      </div>
    </div>
  );
}