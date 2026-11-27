import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  MapWithIcon,
  asText,
  formatDistance,
  getCountryCode,
  iconSlug,
  iconUrl,
  setupPartsLabel,
} from "./legacyDisplay";

describe("legacy display helpers", () => {
  it("converts values to display strings", () => {
    expect(asText(null)).toBe("");
    expect(asText(42)).toBe("42");
    expect(formatDistance("1234.5").replace(/\D/g, "")).toBe("1235");
    expect(formatDistance(null)).toBe("");
  });

  it("builds icon slugs and URLs", () => {
    expect(iconSlug("Sky Rock Outpost!")).toBe("sky_rock_outpost");
    expect(iconUrl("map_icons", "Canyon Arena")).toBe("/img/map_icons/canyon_arena.webp");
  });

  it("resolves country codes from names and sub-regions", () => {
    expect(getCountryCode("Finland")).toBe("fi");
    expect(getCountryCode("Scotland")).toBe("gb-sct");
    expect(getCountryCode("")).toBeNull();
  });

  it("joins tuning setup part names", () => {
    expect(setupPartsLabel([{ nameTuningPart: "Nitro" }, { nameTuningPart: "Spoiler" }])).toBe(
      "Nitro, Spoiler",
    );
  });
});

describe("MapWithIcon", () => {
  it("renders the map name with a labelled icon", () => {
    render(<MapWithIcon name="Canyon Arena" />);
    expect(screen.getByText("Canyon Arena")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Canyon Arena icon" })).toHaveAttribute(
      "src",
      "/img/map_icons/canyon_arena.webp",
    );
  });
});
