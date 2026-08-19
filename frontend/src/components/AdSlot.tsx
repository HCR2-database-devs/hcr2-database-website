import { useEffect, useRef } from "react";

interface AdSlotProps {
  slotId: string;
  className?: string;
}

export function AdSlot({ slotId, className }: AdSlotProps) {
  const enabled = import.meta.env.VITE_ADS_ENABLED === "true";
  const publisherId = import.meta.env.VITE_ADS_PUBLISHER_ID ?? "";
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!enabled || !publisherId || !containerRef.current) return;

    const ins = containerRef.current.querySelector(`ins[data-ad-slot="${slotId}"]`);
    if (!ins) return;

    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch {
    }
  }, [enabled, publisherId, slotId]);

  if (!enabled || !publisherId) return null;

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
