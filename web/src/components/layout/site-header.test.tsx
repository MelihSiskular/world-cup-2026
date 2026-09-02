import type {
  AnchorHTMLAttributes,
  ReactNode,
} from "react";
import {
  render,
  screen,
} from "@testing-library/react";
import {
  NextIntlClientProvider,
} from "next-intl";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import englishMessages from "../../../messages/en.json";
import {
  SiteHeader,
} from "@/components/layout/site-header";

vi.mock("next/image", () => ({
  default: function MockImage() {
    return (
      <span data-testid="brand-image" />
    );
  },
}));

vi.mock(
  "@/components/layout/locale-switcher",
  () => ({
    LocaleSwitcher:
      function MockLocaleSwitcher() {
        return (
          <span data-testid="locale-switcher" />
        );
      },
  }),
);

vi.mock(
  "@/components/layout/page-container",
  () => ({
    PageContainer: ({
      children,
      className,
    }: Readonly<{
      children: ReactNode;
      className?: string;
    }>) => (
      <div className={className}>
        {children}
      </div>
    ),
  }),
);

vi.mock(
  "@/components/layout/site-navigation",
  () => ({
    SiteNavigation:
      function MockSiteNavigation() {
        return (
          <nav data-testid="site-navigation" />
        );
      },
  }),
);

vi.mock("@/i18n/navigation", () => ({
  Link: ({
    children,
    href,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement> &
    Readonly<{
      children: ReactNode;
      href: string;
    }>) => (
    <a
      href={href}
      {...props}
    >
      {children}
    </a>
  ),
}));

function renderHeader() {
  return render(
    <NextIntlClientProvider
      locale="en"
      messages={englishMessages}
    >
      <SiteHeader />
    </NextIntlClientProvider>,
  );
}

describe("SiteHeader", () => {
  it(
    "keeps product navigation without exposing API status",
    () => {
      renderHeader();

      expect(
        screen.getByRole("banner"),
      ).toBeInTheDocument();

      expect(
        screen.getByRole("link", {
          name: "WC26 Transfer Intelligence home",
        }),
      ).toHaveAttribute("href", "/");

      expect(
        screen.getByTestId(
          "site-navigation",
        ),
      ).toBeInTheDocument();

      expect(
        screen.getByTestId(
          "locale-switcher",
        ),
      ).toBeInTheDocument();

      expect(
        document.querySelector(
          'header a[href="/status"]',
        ),
      ).not.toBeInTheDocument();

      expect(
        screen.queryByText(
          "API ready",
        ),
      ).not.toBeInTheDocument();
    },
  );
});
