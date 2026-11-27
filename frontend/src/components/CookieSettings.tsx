import { useConsent } from "../hooks/useConsent";

export function CookieSettings() {
  const { consent, setAdsConsent } = useConsent();
  const adsEnabled = consent?.ads === true;

  return (
    <div className="cookie-settings">
      <p>
        Essential cookies and storage cannot be disabled because the site needs them for sign-in and
        interface preferences. Advertising is off unless you allow it.
      </p>
      <p>
        Current choice: <strong>{adsEnabled ? "ads allowed" : "ads not allowed"}</strong>.
      </p>
      <div className="cookie-settings__actions">
        <button type="button" onClick={() => setAdsConsent(false)} disabled={!adsEnabled}>
          Reject ads
        </button>
        <button type="button" onClick={() => setAdsConsent(true)} disabled={adsEnabled}>
          Accept ads
        </button>
      </div>
    </div>
  );
}
