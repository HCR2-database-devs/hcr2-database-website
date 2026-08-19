import { useEffect } from "react";

const ADSENSE_SRC = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js";
const FUNDING_SRC = "https://fundingchoicesmessages.google.com/i/pub-";

export function AdSenseLoader() {
  const enabled = import.meta.env.VITE_ADS_ENABLED === "true";
  const publisherId = import.meta.env.VITE_ADS_PUBLISHER_ID ?? "";

  useEffect(() => {
    if (!enabled || !publisherId) return;

    if (!document.querySelector(`script[src="${ADSENSE_SRC}?client=${publisherId}"]`)) {
      const script = document.createElement("script");
      script.async = true;
      script.crossOrigin = "anonymous";
      script.src = `${ADSENSE_SRC}?client=${publisherId}`;
      document.head.appendChild(script);
    }

    const fundingUrl = `${FUNDING_SRC}${publisherId}?ers=1`;
    if (!document.querySelector(`script[src="${fundingUrl}"]`)) {
      const fundingScript = document.createElement("script");
      fundingScript.async = true;
      fundingScript.src = fundingUrl;
      document.head.appendChild(fundingScript);
    }
  }, [enabled, publisherId]);

  return null;
}
