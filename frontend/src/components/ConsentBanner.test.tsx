import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConsentBanner } from "./ConsentBanner";
import { readConsent } from "../lib/consent";

function renderBanner() {
  return render(
    <MemoryRouter>
      <ConsentBanner />
    </MemoryRouter>,
  );
}

describe("ConsentBanner", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("stays hidden when ads are disabled", () => {
    renderBanner();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("saves the user's choice and closes the banner", async () => {
    vi.stubEnv("VITE_ADS_ENABLED", "true");
    vi.stubEnv("VITE_ADS_PUBLISHER_ID", "ca-pub-test");
    const user = userEvent.setup();
    renderBanner();

    expect(screen.getByRole("dialog", { name: "Cookie choices" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Accept ads" }));

    expect(readConsent()?.ads).toBe(true);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
