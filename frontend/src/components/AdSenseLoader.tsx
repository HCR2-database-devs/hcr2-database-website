import { useEffect } from "react";

const ADSENSE_SRC = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js";
const FUNDING_SRC = "https://fundingchoicesmessages.google.com/i/pub-";
const ERROR_PROTECTION_SRC = "/js/ad-error-protection.js";

function loadScript(src: string, async = true): Promise<void> {
  return new Promise((resolve) => {
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.async = async;
    script.src = src;
    script.addEventListener("load", () => resolve());
    script.addEventListener("error", () => resolve());
    document.head.appendChild(script);
  });
}

export function AdSenseLoader() {
  const enabled = import.meta.env.VITE_ADS_ENABLED === "true";
  const publisherId = import.meta.env.VITE_ADS_PUBLISHER_ID ?? "";

  useEffect(() => {
    if (!enabled || !publisherId) return;

    loadScript(`${ADSENSE_SRC}?client=${publisherId}`);
    loadScript(`${FUNDING_SRC}${publisherId}?ers=1`).then(() => {
      loadScript(ERROR_PROTECTION_SRC);
    });
  }, [enabled, publisherId]);

  return null;
}
