import { useEffect, useState } from "react";

const BAIT_CLASS = "ad-banner";
const CHECK_DELAY_MS = 500;

export function AdBlockerDetector() {
  const enabled = import.meta.env.VITE_ADS_ENABLED === "true";
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    if (!enabled) return;

    const bait = document.createElement("div");
    bait.className = BAIT_CLASS;
    bait.setAttribute("aria-hidden", "true");
    document.body.appendChild(bait);

    const timer = setTimeout(() => {
      const baitRemoved = !document.body.contains(bait);
      const scriptBlocked = typeof window.adsbygoogle === "undefined";

      bait.remove();

      if (baitRemoved || scriptBlocked) {
        setBlocked(true);
      }
    }, CHECK_DELAY_MS);

    return () => {
      clearTimeout(timer);
      bait.remove();
    };
  }, [enabled]);

  if (!enabled || !blocked) return null;

  return (
    <div className="adblock-overlay" role="alert">
      <div className="adblock-overlay__card">
        <img
          className="adblock-overlay__icon"
          src="/img/hcrdatabaselogo.png"
          alt=""
        />
        <h2>Ad blocker detected</h2>
        <p>
          Ads help keep this site free for everyone. Please disable your ad
          blocker and reload the page to continue.
        </p>
        <p className="adblock-overlay__alt">
          Alternatively, if we get enough donations to cover hosting costs we will disable ads.
          {" "}
          <a
            href="https://en.tipeee.com/hcr2-database"
            target="_blank"
            rel="noopener noreferrer"
          >
            Support us on Tipeee
          </a>
        </p>
        <button
          className="adblock-overlay__refresh"
          type="button"
          onClick={() => window.location.reload()}
        >
          Reload page
        </button>
      </div>
    </div>
  );
}
