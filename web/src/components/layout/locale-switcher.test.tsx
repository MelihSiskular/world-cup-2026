import {
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  NextIntlClientProvider,
} from "next-intl";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import englishMessages from "../../../messages/en.json";

import {
  LocaleSwitcher,
} from "./locale-switcher";

const {
  replaceMock,
} = vi.hoisted(
  () => ({
    replaceMock: vi.fn(),
  }),
);

vi.mock(
  "@/i18n/navigation",
  () => ({
    usePathname: () =>
      "/players",
    useRouter: () => ({
      replace: replaceMock,
    }),
  }),
);

describe("LocaleSwitcher", () => {
  beforeEach(() => {
    replaceMock.mockReset();

    window.history.replaceState(
      {},
      "",
      "/players?role=Advanced+Playmaker&country=France",
    );
  });

  it("marks the current locale and exposes both language choices", () => {
    render(
      <NextIntlClientProvider
        locale="en"
        messages={
          englishMessages
        }
      >
        <LocaleSwitcher />
      </NextIntlClientProvider>,
    );

    const languageGroup =
      screen.getByRole(
        "group",
        {
          name: "Language",
        },
      );

    expect(
      within(
        languageGroup,
      ).getByRole(
        "button",
        {
          name:
            "Change language to English",
        },
      ),
    ).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    expect(
      within(
        languageGroup,
      ).getByRole(
        "button",
        {
          name:
            "Change language to Turkish",
        },
      ),
    ).toHaveAttribute(
      "aria-pressed",
      "false",
    );

    expect(
      languageGroup.querySelector(
        '[data-country-code="GBR"]',
      ),
    ).not.toBeNull();

    expect(
      languageGroup.querySelector(
        '[data-country-code="TUR"]',
      ),
    ).not.toBeNull();

    expect(
      languageGroup,
    ).toHaveClass(
      "rounded-lg",
      "p-0.5",
    );

    for (
      const languageButton
      of within(
        languageGroup,
      ).getAllByRole("button")
    ) {
      expect(
        languageButton,
      ).toHaveClass(
        "min-h-8",
        "min-w-8",
        "sm:min-w-11",
      );
    }

    expect(
      languageGroup.querySelector(
        '[data-country-code="GBR"]',
      ),
    ).toHaveClass(
      "!w-4",
    );

    expect(
      languageGroup.querySelector(
        '[data-country-code="TUR"]',
      ),
    ).toHaveClass(
      "!w-4",
    );
  });

  it("preserves the current route and query when changing locale", async () => {
    const user =
      userEvent.setup();

    render(
      <NextIntlClientProvider
        locale="en"
        messages={
          englishMessages
        }
      >
        <LocaleSwitcher />
      </NextIntlClientProvider>,
    );

    await user.click(
      screen.getByRole(
        "button",
        {
          name:
            "Change language to Turkish",
        },
      ),
    );

    await waitFor(() => {
      expect(
        replaceMock,
      ).toHaveBeenCalledWith(
        "/players?role=Advanced+Playmaker&country=France",
        {
          locale: "tr",
        },
      );
    });
  });
});
