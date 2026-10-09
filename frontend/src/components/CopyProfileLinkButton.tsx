import { useEffect, useRef, useState } from "react";

import { communityProfileShareUrl } from "../services/community";

type CopyState = "idle" | "copied" | "failed";

const RESET_AFTER_MS = 2000;

/**
 * Copies the profile's shareable link. Uses the share page URL, not the SPA
 * route, because that is what renders the Discord embed.
 */
export function CopyProfileLinkButton({
  communityId,
  className = "button-ghost",
  label = "Copy profile link"
}: {
  communityId: number;
  className?: string;
  label?: string;
}) {
  const [state, setState] = useState<CopyState>("idle");
  const timer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timer.current !== null) window.clearTimeout(timer.current);
    };
  }, []);

  const schedule = (next: CopyState) => {
    setState(next);
    if (timer.current !== null) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setState("idle"), RESET_AFTER_MS);
  };

  const onClick = async () => {
    const url = new URL(communityProfileShareUrl(communityId), window.location.origin).toString();
    try {
      await navigator.clipboard.writeText(url);
      schedule("copied");
    } catch {
      schedule("failed");
    }
  };

  return (
    <button
      className={className}
      type="button"
      onClick={onClick}
      title="Copies a link that shows a rich preview when pasted into Discord"
    >
      {state === "copied" ? "Copied!" : state === "failed" ? "Copy failed" : label}
    </button>
  );
}