import { useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { useAuthStatus } from "../hooks/useAuthStatus";
import { COMMUNITY_LAUNCH_ANNOUNCEMENT_ID } from "../lib/communityInfo";
import { useCanUseFeature } from "../lib/features";

const storageKey = `announcement:${COMMUNITY_LAUNCH_ANNOUNCEMENT_ID}`;

const LOGIN_URL = "https://auth.hcr2.xyz/login";

function keyFor(loggedIn: boolean): string {
  return loggedIn ? `${storageKey}:logged-in` : `${storageKey}:logged-out`;
}

function readDismissed(loggedIn: boolean): boolean {
  try {
    const store = loggedIn ? window.localStorage : window.sessionStorage;
    return store.getItem(keyFor(loggedIn)) === "dismissed";
  } catch {
    return false;
  }
}

function writeDismissed(loggedIn: boolean): void {
  try {
    const store = loggedIn ? window.localStorage : window.sessionStorage;
    store.setItem(keyFor(loggedIn), "dismissed");
  } catch {
  }
}

export function CommunityAnnouncement() {
  const { data: authStatus, isLoading } = useAuthStatus();
  const canUseCommunity = useCanUseFeature("community_members");
  const location = useLocation();
  const [hidden, setHidden] = useState(false);

  const loggedIn = authStatus?.logged === true;

  if (isLoading || !canUseCommunity || hidden) return null;
  if (readDismissed(loggedIn)) return null;
  if (location.pathname === "/onboarding") return null;

  return (
    <div className="site-announcement">
      <div className="site-announcement__copy">
        <p className="site-announcement__title">The community section is open to everyone</p>
        <p>
          {loggedIn ? (
            <>
              Profiles, the member directory and notifications used to be limited to testers. You can
              now browse the directory, claim a community username and customise your profile.
            </>
          ) : (
            <>
              Profiles, the member directory and notifications used to be limited to testers. Sign in
              with Discord to browse the directory, claim a community username and customise your
              profile.
            </>
          )}
        </p>
      </div>
      <div className="site-announcement__actions">
        {loggedIn ? (
          <>
            <Link className="button button--primary" to="/community">
              Explore Community
            </Link>
            <Link className="button button--secondary" to="/account">
              Set up my profile
            </Link>
          </>
        ) : (
          <>
            <button
              className="button button--primary"
              type="button"
              onClick={() => {
                window.location.href = LOGIN_URL;
              }}
            >
              Sign in with Discord
            </button>
            <Link className="button button--secondary" to="/community">
              Explore Community
            </Link>
          </>
        )}
        <button
          className="site-announcement__dismiss"
          type="button"
          aria-label="Dismiss this announcement"
          onClick={() => {
            writeDismissed(loggedIn);
            setHidden(true);
          }}
        >
          &times;
        </button>
      </div>
    </div>
  );
}