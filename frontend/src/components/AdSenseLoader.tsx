import { useEffect } from "react";

const ADSENSE_SRC = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js";

export function AdSenseLoader() {
  const enabled = import.meta.env.VITE_ADS_ENABLED === "true";
  const publisherId = import.meta.env.VITE_ADS_PUBLISHER_ID ?? "";

  useEffect(() => {
    if (!enabled || !publisherId) return;
    if (document.querySelector(`script[src="${ADSENSE_SRC}?client=${publisherId}"]`)) return;

    const script = document.createElement("script");
    script.async = true;
    script.crossOrigin = "anonymous";
    script.src = `${ADSENSE_SRC}?client=${publisherId}`;
    script.onload = () => {
      window.__adsenseLoaded = true;
    };
    document.head.appendChild(script);
  }, [enabled, publisherId]);

  return null;
}
