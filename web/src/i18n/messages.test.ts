import {
  describe,
  expect,
  it,
} from "vitest";

import englishMessages from "../../messages/en.json";
import turkishMessages from "../../messages/tr.json";

import {
  routing,
} from "./routing";

function collectMessageEntries(
  value: Record<string, unknown>,
  prefix = "",
): ReadonlyArray<
  readonly [
    string,
    string,
  ]
> {
  const entries:
    Array<
      readonly [
        string,
        string,
      ]
    > = [];

  for (
    const [
      key,
      child,
    ] of Object.entries(value)
  ) {
    const messagePath =
      prefix
        ? `${prefix}.${key}`
        : key;

    if (typeof child === "string") {
      entries.push([
        messagePath,
        child,
      ]);

      continue;
    }

    if (
      typeof child === "object"
      && child !== null
      && !Array.isArray(child)
    ) {
      entries.push(
        ...collectMessageEntries(
          child as Record<
            string,
            unknown
          >,
          messagePath,
        ),
      );

      continue;
    }

    throw new TypeError(
      `Unsupported message at ${messagePath}.`,
    );
  }

  return entries;
}

describe("localization foundation", () => {
  it("keeps English as the default locale", () => {
    expect(
      routing.defaultLocale,
    ).toBe("en");

    expect([
      ...routing.locales,
    ]).toEqual([
      "en",
      "tr",
    ]);
  });

  it("keeps English and Turkish message keys aligned", () => {
    const englishEntries =
      collectMessageEntries(
        englishMessages,
      );

    const turkishEntries =
      collectMessageEntries(
        turkishMessages,
      );

    expect(
      englishEntries.map(
        ([key]) => key,
      ),
    ).toEqual(
      turkishEntries.map(
        ([key]) => key,
      ),
    );
  });

  it("does not allow empty localized messages", () => {
    for (
      const [
        key,
        message,
      ] of [
        ...collectMessageEntries(
          englishMessages,
        ),
        ...collectMessageEntries(
          turkishMessages,
        ),
      ]
    ) {
      expect(
        message.trim(),
        key,
      ).not.toBe("");
    }
  });
});
