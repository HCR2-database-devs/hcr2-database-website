import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { useFeatureAccess } from "../lib/features";
import type { FeatureName } from "../types/api";

type FeatureGateProps = {
  feature: FeatureName;
  children: ReactNode;
  fallback?: ReactNode;
};

export function FeatureGate({ feature, children, fallback }: FeatureGateProps) {
  const { canUse, isLoading } = useFeatureAccess(feature);
  if (isLoading) return null;
  if (canUse) return <>{children}</>;
  return <>{fallback ?? <BetaUnavailableNotice feature={feature} />}</>;
}

export function BetaUnavailableNotice({ feature }: { feature: FeatureName }) {
  const { state } = useFeatureAccess(feature);
  return (
    <div className="page-container">
      <div className="feature-notice">
        <h1>
          {state === "DISABLED" ? "Feature unavailable" : "This feature is currently in beta"}
        </h1>
        <p>
          {state === "DISABLED"
            ? "This feature is not available right now. Please check back later."
            : "This feature is only available to beta testers right now. Please check back later."}
        </p>
        <Link className="button" to="/">
          Back to Home
        </Link>
      </div>
    </div>
  );
}