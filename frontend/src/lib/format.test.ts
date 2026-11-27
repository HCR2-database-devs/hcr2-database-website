import { describe, expect, it } from "vitest";

import { formatDateTime, formatMemberSince, parseServerDate } from "./format";

describe("parseServerDate", () => {
  it("treats naive API timestamps as UTC", () => {
    const date = parseServerDate("2026-10-16T13:19:01.313462");
    expect(date?.toISOString()).toBe("2026-10-16T13:19:01.313Z");
  });

  it("preserves an explicit offset", () => {
    const date = parseServerDate("2026-10-16T13:19:01+02:00");
    expect(date?.toISOString()).toBe("2026-10-16T11:19:01.000Z");
  });

  it("rejects missing and invalid values", () => {
    expect(parseServerDate()).toBeNull();
    expect(parseServerDate("not-a-date")).toBeNull();
  });
});

describe("date display helpers", () => {
  it("returns null for missing or invalid values", () => {
    expect(formatMemberSince()).toBeNull();
    expect(formatMemberSince("invalid")).toBeNull();
    expect(formatDateTime("invalid")).toBeNull();
  });

  it("formats a member-since month and year", () => {
    expect(formatMemberSince("2026-10-16T13:19:01Z")).toMatch(/2026/);
  });
});
