const CRAWLER_PATTERN =
  /bot|crawler|spider|slurp|bingpreview|facebookexternalhit|twitterbot|discordbot|whatsapp|curl|wget|headlesschrome|playwright|puppeteer/i;

interface NavigatorWithConnection extends Navigator {
  connection?: { saveData?: boolean };
}

export function shouldSkipOptionalThirdParties(): boolean {
  if (typeof window === "undefined") return true;
  if (window.matchMedia?.("(prefers-reduced-data: reduce)").matches) return true;
  if ((navigator as NavigatorWithConnection).connection?.saveData) return true;
  if (navigator.webdriver) return true;
  return CRAWLER_PATTERN.test(navigator.userAgent ?? "");
}
