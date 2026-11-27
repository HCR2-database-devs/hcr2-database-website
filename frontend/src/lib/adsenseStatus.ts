export const ADSENSE_ERROR_EVENT = "hcr2:adsense-error";

export function reportAdsenseError(): void {
  window.dispatchEvent(new Event(ADSENSE_ERROR_EVENT));
}

export function subscribeAdsenseError(listener: () => void): () => void {
  window.addEventListener(ADSENSE_ERROR_EVENT, listener);
  return () => window.removeEventListener(ADSENSE_ERROR_EVENT, listener);
}
