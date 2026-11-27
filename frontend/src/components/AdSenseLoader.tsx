import { useEffect } from "react";

import { useConsent } from "../hooks/useConsent";
import { reportAdsenseError } from "../lib/adsenseStatus";
import { shouldSkipOptionalThirdParties } from "../lib/thirdParties";

const ADSENSE_SRC = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js";

export function AdSenseLoader() {
  const enabled = import.meta.env.VITE_ADS_ENABLED === "true";
  const publisherId = import.meta.env.VITE_ADS_PUBLISHER_ID ?? "";
  const { consent } = useConsent();

  useEffect(() => {
    if (!enabled || !publisherId || !consent?.ads) return;
    if (shouldSkipOptionalThirdParties()) return;
    if (document.querySelector(`script[src="${ADSENSE_SRC}?client=${publisherId}"]`)) return;

    const script = document.createElement("script");
    script.async = true;
    script.crossOrigin = "anonymous";
    script.src = `${ADSENSE_SRC}?client=${publisherId}`;
    script.onload = () => {
      window.__adsenseLoaded = true;
    };
    script.onerror = () => {
      reportAdsenseError();
    };
    document.head.appendChild(script);
  }, [enabled, publisherId, consent?.ads]);

  return null;
}
