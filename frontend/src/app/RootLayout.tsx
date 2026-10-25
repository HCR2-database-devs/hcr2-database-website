import { useEffect, useLayoutEffect, useRef } from "react";
import { Outlet, useLocation, useNavigationType } from "react-router-dom";

const POSITIONS_KEY = "hcr2-scroll-positions";

function readPositions(): Record<string, number> {
  try {
    return JSON.parse(sessionStorage.getItem(POSITIONS_KEY) || "{}");
  } catch {
    return {};
  }
}

function writePositions(positions: Record<string, number>) {
  try {
    sessionStorage.setItem(POSITIONS_KEY, JSON.stringify(positions));
  } catch {
    return;
  }
}

export function RootLayout() {
  const { pathname } = useLocation();
  const navigationType = useNavigationType();
  const positions = useRef<Record<string, number> | null>(null);
  const activePath = useRef(pathname);

  activePath.current = pathname;

  if (positions.current === null) {
    positions.current = readPositions();
  }

  useEffect(() => {
    const current = positions.current;
    if (!current) {
      return undefined;
    }

    const save = () => {
      if (activePath.current === pathname) {
        current[pathname] = window.scrollY;
      }
    };
    const persist = () => writePositions(current);

    window.addEventListener("scroll", save, { passive: true });
    window.addEventListener("pointerdown", save, { passive: true });
    window.addEventListener("keydown", save);
    window.addEventListener("pagehide", persist);

    return () => {
      window.removeEventListener("scroll", save);
      window.removeEventListener("pointerdown", save);
      window.removeEventListener("keydown", save);
      window.removeEventListener("pagehide", persist);
      persist();
    };
  }, [pathname]);

  useEffect(() => {
    const previous = window.history.scrollRestoration;
    window.history.scrollRestoration = "manual";
    return () => {
      window.history.scrollRestoration = previous;
    };
  }, []);

  useLayoutEffect(() => {
    const current = positions.current;
    const target = navigationType === "POP" ? current?.[pathname] ?? 0 : 0;

    if (target <= 0) {
      window.scrollTo(0, 0);
      return undefined;
    }

    let attempts = 0;
    let stopped = false;
    let timer: ReturnType<typeof setInterval> | undefined;
    let observer: ResizeObserver | null = null;

    const stop = () => {
      stopped = true;
      if (timer) {
        window.clearInterval(timer);
      }
      observer?.disconnect();
      window.removeEventListener("wheel", stop);
      window.removeEventListener("touchstart", stop);
      window.removeEventListener("keydown", stop);
    };

    const restore = () => {
      if (stopped) {
        return;
      }
      window.scrollTo(0, target);
      attempts += 1;
      if (Math.abs(window.scrollY - target) <= 1 || attempts >= 100) {
        stop();
      }
    };

    if (typeof ResizeObserver !== "undefined") {
      observer = new ResizeObserver(restore);
      observer.observe(document.documentElement);
    }
    window.addEventListener("wheel", stop, { passive: true });
    window.addEventListener("touchstart", stop, { passive: true });
    window.addEventListener("keydown", stop);

    restore();
    timer = window.setInterval(restore, 50);

    return stop;
  }, [pathname, navigationType]);

  return <Outlet />;
}
