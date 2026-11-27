import { describe, expect, it } from "vitest";

import { applyPageMetadata, getPageMetadata } from "./pageMetadata";

describe("page metadata", () => {
  it("uses specific titles for public routes", () => {
    expect(getPageMetadata("/records/mythic").title).toMatch(/Mythic records/);
    expect(getPageMetadata("/unknown").title).toMatch(/Page not found/);
  });

  it("updates document metadata and canonical URL", () => {
    applyPageMetadata("/privacy");
    expect(document.title).toMatch(/Privacy policy/);
    expect(document.querySelector('link[rel="canonical"]')).toHaveAttribute(
      "href",
      "https://hcr2.xyz/privacy",
    );
    expect(document.querySelector('meta[property="og:title"]')?.getAttribute("content")).toBe(
      document.title,
    );
  });

  it("marks private routes as noindex", () => {
    applyPageMetadata("/admin");
    expect(document.querySelector('meta[name="robots"]')).toHaveAttribute("content", "noindex, follow");
  });
});
