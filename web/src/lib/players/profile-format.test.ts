import {
  describe,
  expect,
  it,
} from "vitest";

import {
  formatMarketValue,
  formatPlayerPosition,
  formatProfileNumber,
  formatProfilePercentage,
  formatUnitIntervalPercentage,
} from "./profile-format";

describe("player profile formatters", () => {
  describe("formatProfileNumber", () => {
    it("keeps missing values distinct from zero", () => {
      expect(formatProfileNumber(null)).toBe(
        "Not reported",
      );

      expect(
        formatProfileNumber(undefined),
      ).toBe("Not reported");

      expect(formatProfileNumber(0)).toBe("0");
    });

    it("formats reported numeric values", () => {
      expect(
        formatProfileNumber(650),
      ).toBe("650");

      expect(
        formatProfileNumber(7.456, {
          maximumFractionDigits: 2,
        }),
      ).toBe("7.46");
    });
  });

  describe("formatProfilePercentage", () => {
    it("keeps missing percentages distinct from zero", () => {
      expect(
        formatProfilePercentage(null),
      ).toBe("Not reported");

      expect(
        formatProfilePercentage(undefined),
      ).toBe("Not reported");

      expect(
        formatProfilePercentage(0),
      ).toBe("0%");
    });
  });

  describe("formatUnitIntervalPercentage", () => {
    it("preserves missing values and converts reported zero", () => {
      expect(
        formatUnitIntervalPercentage(null),
      ).toBe("Not reported");

      expect(
        formatUnitIntervalPercentage(undefined),
      ).toBe("Not reported");

      expect(
        formatUnitIntervalPercentage(0),
      ).toBe("0%");

      expect(
        formatUnitIntervalPercentage(0.75),
      ).toBe("75%");
    });
  });

  describe("formatMarketValue", () => {
    it("does not treat missing market evidence as zero", () => {
      expect(
        formatMarketValue(null, "EUR"),
      ).toBe("Not reported");

      expect(
        formatMarketValue(undefined, "EUR"),
      ).toBe("Not reported");

      expect(
        formatMarketValue(10_000_000, null),
      ).toBe("Not reported");

      expect(
        formatMarketValue(
          10_000_000,
          undefined,
        ),
      ).toBe("Not reported");
    });

    it("keeps a reported zero market value as real data", () => {
      const formatted =
        formatMarketValue(0, "EUR");

      expect(formatted).not.toBe(
        "Not reported",
      );

      expect(formatted).toContain("0");
    });
  });

  describe("formatPlayerPosition", () => {
    it("provides a fallback only when position is missing", () => {
      expect(
        formatPlayerPosition(null),
      ).toBe("Position unavailable");

      expect(
        formatPlayerPosition(undefined),
      ).toBe("Position unavailable");

      expect(
        formatPlayerPosition("M"),
      ).toBe("Midfielder");
    });
  });
});
