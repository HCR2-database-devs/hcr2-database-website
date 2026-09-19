import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getTippers } from "../services/tippers";

const STATIC_LIMIT = 8;

export function DonatorBanner() {
  const { data } = useQuery({
    queryKey: ["tippers"],
    queryFn: getTippers,
    refetchInterval: 3_600_000,
  });

  const names = data?.tippers?.map((t) => t.pseudo) ?? [];

  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  const [duration, setDuration] = useState(25);
  const trackRef = useRef<HTMLDivElement | null>(null);
  const namesRef = useRef<HTMLSpanElement | null>(null);

  useEffect(() => {
    const mql = window.matchMedia("(prefers-reduced-motion: reduce)");
    const handle = (event: MediaQueryListEvent) => setPrefersReducedMotion(event.matches);
    mql.addEventListener("change", handle);
    return () => mql.removeEventListener("change", handle);
  }, []);

  useEffect(() => {
    if (prefersReducedMotion) return;
    const namesEl = namesRef.current;
    const trackEl = trackRef.current;
    if (!namesEl || !trackEl) return;
    const measure = () => {
      const width = namesEl.scrollWidth;
      if (width <= 0) return;
      setDuration(Math.min(60, Math.max(18, Math.round(width / 30))));
    };
    measure();
    const timer = window.setTimeout(measure, 300);
    return () => window.clearTimeout(timer);
  }, [names.length, prefersReducedMotion]);

  if (names.length === 0) return null;

  const list = names.join(" \u2022 ");
  const staticList = prefersReducedMotion || names.length <= STATIC_LIMIT;
  const className = staticList
    ? "donator-banner donator-banner--static"
    : "donator-banner donator-banner--marquee";

  return (
    <div className={className} aria-label="Supporters">
      <span className="donator-banner__label">Supporters</span>
      <div className="donator-banner__track" ref={trackRef}>
        <span
          ref={namesRef}
          className="donator-banner__names"
          style={staticList ? undefined : { animationDuration: `${duration}s` }}
        >
          {staticList ? (
            list
          ) : (
            <>
              {list}
              {" \u2022 "}
              {list}
            </>
          )}
        </span>
      </div>
    </div>
  );
}