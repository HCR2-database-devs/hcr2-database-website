import { useCallback, useEffect, useState } from "react";

import { readConsent, saveConsent, subscribeConsent, type ConsentState } from "../lib/consent";

export function useConsent() {
  const [consent, setConsent] = useState<ConsentState | null>(readConsent);

  useEffect(() => subscribeConsent(() => setConsent(readConsent())), []);

  const setAdsConsent = useCallback((ads: boolean) => saveConsent(ads), []);

  return { consent, setAdsConsent };
}
