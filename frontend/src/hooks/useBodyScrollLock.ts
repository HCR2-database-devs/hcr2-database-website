import { useEffect } from "react";

let lockCount = 0;
let lockedScrollY = 0;
let originalBodyStyles: {
  overflow: string;
  paddingRight: string;
  position: string;
  top: string;
  width: string;
} | null = null;

function getPixelValue(value: string) {
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function useBodyScrollLock(active = true) {
  useEffect(() => {
    if (!active) {
      return undefined;
    }

    const body = document.body;
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;

    if (lockCount === 0) {
      const computedBodyStyle = window.getComputedStyle(body);
      lockedScrollY = window.scrollY;
      originalBodyStyles = {
        overflow: body.style.overflow,
        paddingRight: body.style.paddingRight,
        position: body.style.position,
        top: body.style.top,
        width: body.style.width
      };

      body.style.overflow = "hidden";
      body.style.position = "fixed";
      body.style.top = `-${lockedScrollY}px`;
      body.style.width = "100%";

      if (scrollbarWidth > 0) {
        const currentPadding = getPixelValue(computedBodyStyle.paddingRight);
        body.style.paddingRight = `${currentPadding + scrollbarWidth}px`;
      }
    }

    lockCount += 1;

    return () => {
      lockCount = Math.max(0, lockCount - 1);
      if (lockCount > 0 || !originalBodyStyles) {
        return;
      }

      body.style.overflow = originalBodyStyles.overflow;
      body.style.paddingRight = originalBodyStyles.paddingRight;
      body.style.position = originalBodyStyles.position;
      body.style.top = originalBodyStyles.top;
      body.style.width = originalBodyStyles.width;
      window.scrollTo(0, lockedScrollY);
      originalBodyStyles = null;
    };
  }, [active]);
}
