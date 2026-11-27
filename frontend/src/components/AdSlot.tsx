import { useEffect, useRef, useState } from "react";

import { useConsent } from "../hooks/useConsent";
import { shouldSkipOptionalThirdParties } from "../lib/thirdParties";

interface AdSlotProps {
  slotId: string;
  className?: string;
}

const AD_LOAD_CHECK_MS = 2000;

export function AdSlot({ slotId, className }: AdSlotProps) {
  const enabled = import.meta.env.VITE_ADS_ENABLED === "true";
  const publisherId = import.meta.env.VITE_ADS_PUBLISHER_ID ?? "";
  const { consent } = useConsent();
  const allowed = enabled && Boolean(publisherId) && consent?.ads === true;
  const containerRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (!allowed || shouldSkipOptionalThirdParties() || !containerRef.current) return;

    const ins = containerRef.current.querySelector(`ins[data-ad-slot="${slotId}"]`);
    if (!ins) return;

    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch {
      // AdSense not yet loaded or blocked
    }

    const timer = setTimeout(() => {
      if (ins.children.length === 0) {
        setVisible(false);
      }
    }, AD_LOAD_CHECK_MS);

    return () => clearTimeout(timer);
  }, [allowed, slotId]);

  if (!allowed || shouldSkipOptionalThirdParties() || !visible) return null;

  return (
    <div className={`ad-container${className ? ` ${className}` : ""}`}>
      <ins
        className="adsbygoogle"
        style={{ display: "block" }}
        data-ad-client={publisherId}
        data-ad-slot={slotId}
        data-ad-format="auto"
        data-full-width-responsive="true"
      />
    </div>
  );
}
