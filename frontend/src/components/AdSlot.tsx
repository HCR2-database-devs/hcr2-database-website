import { useEffect, useRef, useState } from "react";

interface AdSlotProps {
  slotId: string;
  className?: string;
}

const AD_LOAD_CHECK_MS = 2000;

export function AdSlot({ slotId, className }: AdSlotProps) {
  const enabled = import.meta.env.VITE_ADS_ENABLED === "true";
  const publisherId = import.meta.env.VITE_ADS_PUBLISHER_ID ?? "";
  const containerRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (!enabled || !publisherId || !containerRef.current) return;

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
  }, [enabled, publisherId, slotId]);

  if (!enabled || !publisherId || !visible) return null;

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
