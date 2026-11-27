import { useRef } from "react";
import { Link } from "react-router-dom";

import { useConsent } from "../hooks/useConsent";
import { useDialogAccessibility } from "../hooks/useDialogAccessibility";
import { shouldSkipOptionalThirdParties } from "../lib/thirdParties";

export function ConsentBanner() {
  const enabled = import.meta.env.VITE_ADS_ENABLED === "true";
  const publisherId = import.meta.env.VITE_ADS_PUBLISHER_ID ?? "";
  const { consent, setAdsConsent } = useConsent();
  const containerRef = useRef<HTMLDivElement>(null);
  const open = enabled && Boolean(publisherId) && consent === null && !shouldSkipOptionalThirdParties();

  useDialogAccessibility({
    open,
    onClose: () => setAdsConsent(false),
    containerRef,
  });

  if (!open) return null;

  return (
    <div
      className="consent-banner"
      role="dialog"
      aria-modal="false"
      aria-labelledby="consent-banner-title"
      ref={containerRef}
      tabIndex={-1}
    >
      <div>
        <h2 id="consent-banner-title">Cookie choices</h2>
        <p>
          We use essential storage to run the site. With your permission, Google AdSense may also
          use cookies to show ads. You can change this any time from the{" "}
          <Link to="/privacy#cookie-settings">cookie settings</Link> on the privacy page.
        </p>
      </div>
      <div className="consent-banner__actions">
        <button type="button" onClick={() => setAdsConsent(false)}>
          Reject ads
        </button>
        <button type="button" onClick={() => setAdsConsent(true)}>
          Accept ads
        </button>
      </div>
    </div>
  );
}
