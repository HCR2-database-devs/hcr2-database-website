const CONSENT_EVENT = "hcr2:consentchange";

export const CONSENT_STORAGE_KEY = "hcr2-consent";

export interface ConsentState {
  ads: boolean;
  updatedAt: number;
}

export function readConsent(): ConsentState | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(CONSENT_STORAGE_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return null;
    const value = parsed as Partial<ConsentState>;
    if (typeof value.ads !== "boolean" || typeof value.updatedAt !== "number") return null;
    return { ads: value.ads, updatedAt: value.updatedAt };
  } catch {
    return null;
  }
}

export function saveConsent(ads: boolean): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(
      CONSENT_STORAGE_KEY,
      JSON.stringify({ ads, updatedAt: Date.now() } satisfies ConsentState),
    );
  } catch {
    // Storage may be disabled; the in-memory state still applies for this tab.
  }
  window.dispatchEvent(new Event(CONSENT_EVENT));
}

export function subscribeConsent(listener: () => void): () => void {
  if (typeof window === "undefined") return () => undefined;
  window.addEventListener(CONSENT_EVENT, listener);
  window.addEventListener("storage", listener);
  return () => {
    window.removeEventListener(CONSENT_EVENT, listener);
    window.removeEventListener("storage", listener);
  };
}
