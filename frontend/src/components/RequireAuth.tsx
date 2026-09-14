import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { useAuthStatus } from "../hooks/useAuthStatus";

type RequireAuthProps = {
  children: ReactNode;
};

export function RequireAuth({ children }: RequireAuthProps) {
  const { data: authStatus, isLoading } = useAuthStatus();
  if (isLoading) return null;
  if (authStatus?.logged) return <>{children}</>;
  return (
    <div className="page-container">
      <div className="account-card">
        <h1>Community is members only</h1>
        <p className="frontend-message">
          The community section is only visible to signed-in members. Sign in with
          Discord to browse player profiles and the member directory.
        </p>
        <div className="frontend-modal-actions">
          <button
            className="button"
            type="button"
            onClick={() => {
              window.location.href = "https://auth.hcr2.xyz/login";
            }}
          >
            Sign in with Discord
          </button>
          <Link className="button-ghost" to="/">
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}