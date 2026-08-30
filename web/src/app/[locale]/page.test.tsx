import {
  render,
  screen,
} from "@testing-library/react";
import {
  NextIntlClientProvider,
} from "next-intl";
import type {
  ReactNode,
} from "react";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import englishMessages from "../../../messages/en.json";
import turkishMessages from "../../../messages/tr.json";

import {
  HomePageContent as HomePage,
} from "./page";

vi.mock(
  "@/i18n/navigation",
  () => ({
    Link: ({
      children,
      href,
      className,
    }: Readonly<{
      children: ReactNode;
      href: string;
      className?: string;
    }>) => (
      <a
        href={href}
        className={className}
      >
        {children}
      </a>
    ),
  }),
);

function renderHomePage(
  locale: "en" | "tr",
) {
  const messages =
    locale === "en"
      ? englishMessages
      : turkishMessages;

  render(
    <NextIntlClientProvider
      locale={locale}
      messages={messages}
    >
      <HomePage />
    </NextIntlClientProvider>,
  );
}

describe("HomePage", () => {
  it("renders the English product journey", () => {
    renderHomePage("en");

    expect(
      screen.getByRole(
        "heading",
        {
          level: 1,
          name:
            "Find the right replacement. Not just the most similar player.",
        },
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole(
        "link",
        {
          name:
            "Search players",
        },
      ),
    ).toHaveAttribute(
      "href",
      "/players",
    );

    expect(
      screen.getByText(
        "Analyze replacements",
      ),
    ).toBeInTheDocument();
  });

  it("renders the Turkish product journey", () => {
    renderHomePage("tr");

    expect(
      screen.getByRole(
        "heading",
        {
          level: 1,
          name:
            "Doğru alternatifi bulun. Yalnızca en benzer oyuncuyu değil.",
        },
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole(
        "link",
        {
          name:
            "Oyuncu ara",
        },
      ),
    ).toHaveAttribute(
      "href",
      "/players",
    );

    expect(
      screen.getByText(
        "Alternatifleri analiz edin",
      ),
    ).toBeInTheDocument();
  });
});
