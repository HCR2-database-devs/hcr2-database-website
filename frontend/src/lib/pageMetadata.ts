import { SITE_URL } from "./siteConfig";

export const SITE_NAME = "HCR2 Adventure Database (unofficial)";

interface PageMetadata {
  title: string;
  description: string;
  indexable?: boolean;
}

const DESCRIPTION =
  "Community-maintained Hill Climb Racing 2 adventure world records, statistics, maps, vehicles and tuning setups.";

const ROUTE_METADATA: Record<string, PageMetadata> = {
  "/": {
    title: SITE_NAME,
    description: `Explore ${DESCRIPTION}`,
  },
  "/maps": {
    title: `Maps | ${SITE_NAME}`,
    description: "Browse Hill Climb Racing 2 adventure maps and their world records.",
  },
  "/vehicles": {
    title: `Vehicles | ${SITE_NAME}`,
    description: "Browse vehicles used in Hill Climb Racing 2 adventure world records.",
  },
  "/players": {
    title: `Players | ${SITE_NAME}`,
    description: "Browse players listed in the Hill Climb Racing 2 adventure records database.",
  },
  "/tuning-parts": {
    title: `Tuning parts | ${SITE_NAME}`,
    description: "Browse Hill Climb Racing 2 tuning parts and their record usage.",
  },
  "/tuning-setups": {
    title: `Tuning setups | ${SITE_NAME}`,
    description: "Browse community tuning setups used for Hill Climb Racing 2 world records.",
  },
  "/records": {
    title: `Records | ${SITE_NAME}`,
    description: "Search and filter community-maintained Hill Climb Racing 2 adventure world records.",
  },
  "/records/mythic": {
    title: `Mythic records | ${SITE_NAME}`,
    description: "Search Hill Climb Racing 2 adventure world records recorded with mythic tuning parts.",
  },
  "/stats": {
    title: `Statistics | ${SITE_NAME}`,
    description: "View Hill Climb Racing 2 adventure record statistics and charts.",
  },
  "/community": {
    title: `Community | ${SITE_NAME}`,
    description: "Meet the Hill Climb Racing 2 records community and browse public profiles.",
  },
  "/changelog": {
    title: `Changelog | ${SITE_NAME}`,
    description: "Recent changes to the HCR2 Adventure Database.",
  },
  "/guidelines": {
    title: `Guidelines | ${SITE_NAME}`,
    description: "Community guidelines for the HCR2 Adventure Database.",
  },
  "/privacy": {
    title: `Privacy policy | ${SITE_NAME}`,
    description: "How the HCR2 Adventure Database handles personal data, cookies and local storage.",
  },
  "/terms": {
    title: `Terms of service | ${SITE_NAME}`,
    description: "Terms for using the HCR2 Adventure Database.",
  },
  "/account": {
    title: `Account | ${SITE_NAME}`,
    description: "Manage your HCR2 Adventure Database community account.",
    indexable: false,
  },
  "/onboarding": {
    title: `Get started | ${SITE_NAME}`,
    description: "Choose your community username.",
    indexable: false,
  },
  "/admin": {
    title: `Admin | ${SITE_NAME}`,
    description: "Administration area.",
    indexable: false,
  },
  "/maintenance": {
    title: `Maintenance | ${SITE_NAME}`,
    description: "The site is temporarily under maintenance.",
    indexable: false,
  },
};

const NOT_FOUND: PageMetadata = {
  title: `Page not found | ${SITE_NAME}`,
  description: "The requested page could not be found on the HCR2 Adventure Database.",
  indexable: false,
};

export function getPageMetadata(pathname: string): PageMetadata {
  if (ROUTE_METADATA[pathname]) return ROUTE_METADATA[pathname];
  if (/^\/community\/[^/]+$/.test(pathname)) {
    return {
      title: `Community profile | ${SITE_NAME}`,
      description: "View a public community profile in the HCR2 Adventure Database.",
    };
  }
  return NOT_FOUND;
}

export function canonicalUrl(pathname: string): string {
  return `${SITE_URL}${pathname}`;
}

function setMeta(attribute: "name" | "property", key: string, content: string): void {
  let element = document.head.querySelector<HTMLMetaElement>(`meta[${attribute}="${key}"]`);
  if (!element) {
    element = document.createElement("meta");
    element.setAttribute(attribute, key);
    document.head.appendChild(element);
  }
  element.content = content;
}

export function applyPageMetadata(pathname: string): void {
  const metadata = getPageMetadata(pathname);
  const url = canonicalUrl(pathname);

  document.title = metadata.title;
  setMeta("name", "description", metadata.description);
  setMeta("property", "og:title", metadata.title);
  setMeta("property", "og:description", metadata.description);
  setMeta("property", "og:url", url);
  setMeta("name", "twitter:title", metadata.title);
  setMeta("name", "twitter:description", metadata.description);
  setMeta("name", "robots", metadata.indexable === false ? "noindex, follow" : "index, follow");

  let canonical = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (!canonical) {
    canonical = document.createElement("link");
    canonical.rel = "canonical";
    document.head.appendChild(canonical);
  }
  canonical.href = url;
}
