import { useEffect, useState } from "react";

const CHECK_DELAY_MS = 600;

export function AdBlockerDetector() {
  const enabled = import.meta.env.VITE_ADS_ENABLED === "true";
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    if (!enabled) return;

    const baits = ["ad", "ads", "ad-slot", "adsbygoogle"].map((cls) => {
      const el = document.createElement("div");
      el.className = cls;
      el.setAttribute("aria-hidden", "true");
      document.body.appendChild(el);
      return el;
    });

    const timer = setTimeout(() => {
      const anyBaitRemoved = baits.some((el) => !document.body.contains(el));
      const scriptBlocked = window.__adsenseLoaded !== true;

      baits.forEach((el) => el.remove());

      if (anyBaitRemoved || scriptBlocked) {
        setBlocked(true);
      }
    }, CHECK_DELAY_MS);

    return () => {
      clearTimeout(timer);
      baits.forEach((el) => el.remove());
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
