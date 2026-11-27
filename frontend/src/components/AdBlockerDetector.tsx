import { useCallback, useEffect, useRef, useState } from "react";

import { useConsent } from "../hooks/useConsent";
import { useDialogAccessibility } from "../hooks/useDialogAccessibility";
import { subscribeAdsenseError } from "../lib/adsenseStatus";
import { shouldSkipOptionalThirdParties } from "../lib/thirdParties";

const CHECK_TIMEOUT_MS = 15_000;
const DISMISSED_KEY = "hcr2-adblock-notice-dismissed";

function wasDismissed(): boolean {
  try {
    return window.sessionStorage.getItem(DISMISSED_KEY) === "1";
  } catch {
    return false;
  }
}

export function AdBlockerDetector() {
  const enabled = import.meta.env.VITE_ADS_ENABLED === "true";
  const { consent } = useConsent();
  const active = enabled && consent?.ads === true && !shouldSkipOptionalThirdParties();
  const [blocked, setBlocked] = useState(false);
  const [dismissed, setDismissed] = useState(wasDismissed);
  const dialogRef = useRef<HTMLDivElement>(null);
  const dismissRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!active || dismissed) return undefined;

    const unsubscribe = subscribeAdsenseError(() => setBlocked(true));
    const timer = window.setTimeout(() => {
      if (window.__adsenseLoaded !== true) setBlocked(true);
    }, CHECK_TIMEOUT_MS);

    return () => {
      unsubscribe();
      window.clearTimeout(timer);
    };
  }, [active, dismissed]);

  const dismiss = useCallback(() => {
    setDismissed(true);
    try {
      window.sessionStorage.setItem(DISMISSED_KEY, "1");
    } catch {
      // The notice stays dismissed for this render even without storage.
    }
  }, []);

  const open = active && blocked && !dismissed;
  useDialogAccessibility({
    open,
    onClose: dismiss,
    containerRef: dialogRef,
    initialFocusRef: dismissRef,
  });

  if (!open) return null;

  return (
    <div
      className="adblock-notice"
      role="dialog"
      aria-modal="false"
      aria-labelledby="adblock-notice-title"
      ref={dialogRef}
      tabIndex={-1}
    >
      <div>
        <h2 id="adblock-notice-title">Ads may be blocked</h2>
        <p>
          Ads help keep this site free. You can keep browsing, or support us another way.
        </p>
      </div>
      <div className="adblock-notice__actions">
        <a
          href="https://en.tipeee.com/hcr2-database"
          target="_blank"
          rel="noopener noreferrer"
        >
          Support us on Tipeee
        </a>
        <button type="button" onClick={() => window.location.reload()}>
          Reload page
        </button>
        <button type="button" ref={dismissRef} onClick={dismiss}>
          Dismiss
        </button>
      </div>
    </div>
  );
}
