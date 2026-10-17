import { useEffect, useRef, useState } from "react";

type CopyButtonProps = {
  value: string;
  label: string;
  className?: string;
};

/**
 * Copies a short string to the clipboard, mirroring the state machine used by
 * `CopyProfileLinkButton` so the feedback looks the same everywhere.
 */
export function CopyValueButton({ value, label, className = "button-ghost" }: CopyButtonProps) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");
  const timer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timer.current !== null) window.clearTimeout(timer.current);
    };
  }, []);

  async function onClick() {
    try {
      await navigator.clipboard.writeText(value);
      setState("copied");
    } catch {
      setState("failed");
    }
    if (timer.current !== null) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setState("idle"), 2000);
  }

  return (
    <button className={className} type="button" onClick={onClick}>
      {state === "copied" ? "Copied!" : state === "failed" ? "Copy failed" : label}
    </button>
  );
}