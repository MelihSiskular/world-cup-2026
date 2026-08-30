import {
  fireEvent,
  render as renderTestingLibrary,
  screen,
} from "@testing-library/react";
import {
  NextIntlClientProvider,
} from "next-intl";
import type {
  ReactElement,
  ReactNode,
} from "react";

import englishMessages from "../../../messages/en.json";
import turkishMessages from "../../../messages/tr.json";
import {
  describe,
  expect,
  it,
} from "vitest";

import { PlayerImage, getPlayerImageSrc } from "./player-image";

type TestLocale =
  "en" | "tr";

function createIntlWrapper(
  locale: TestLocale,
) {
  const messages =
    locale === "tr"
      ? turkishMessages
      : englishMessages;

  return function IntlTestProvider({
    children,
  }: Readonly<{
    children: ReactNode;
  }>) {
    return (
      <NextIntlClientProvider
        locale={locale}
        messages={messages}
      >
        {children}
      </NextIntlClientProvider>
    );
  };
}

function render(
  element: ReactElement,
  locale: TestLocale = "en",
) {
  return renderTestingLibrary(
    element,
    {
      wrapper:
        createIntlWrapper(
          locale,
        ),
    },
  );
}

describe("PlayerImage", () => {
  it("builds a deterministic player-image path", () => {
    expect(getPlayerImageSrc(978838)).toBe("/player-images/978838.png");
  });

  it("renders the player photo with accessible identity", () => {
    render(
      <PlayerImage
        playerId={978838}
        playerName="Michael Olise"
        size="profile"
      />,
    );

    const image = screen.getByRole("img", {
      name: "Michael Olise player photo",
    });

    expect(
      new URL(image.getAttribute("src") ?? "", "http://localhost").pathname,
    ).toBe("/player-images/978838.png");

    expect(image).toHaveAttribute("alt", "Michael Olise player photo");
  });

  it("falls back to initials when the image cannot load", () => {
    render(<PlayerImage playerId={978838} playerName="Michael Olise" />);

    fireEvent.error(
      screen.getByRole("img", {
        name: "Michael Olise player photo",
      }),
    );

    const fallback = screen.getByRole("img", {
      name: "Michael Olise player photo unavailable",
    });

    expect(fallback).toHaveTextContent("MO");
  });

  it("localizes photo and fallback accessibility labels in Turkish", () => {
    render(
      <PlayerImage
        playerId={978838}
        playerName="Michael Olise"
      />,
      "tr",
    );

    const image = screen.getByRole("img", {
      name: "Michael Olise oyuncu fotoğrafı",
    });

    expect(image).toHaveAttribute(
      "alt",
      "Michael Olise oyuncu fotoğrafı",
    );

    fireEvent.error(image);

    expect(
      screen.getByRole("img", {
        name:
          "Michael Olise oyuncu fotoğrafı mevcut değil",
      }),
    ).toHaveTextContent("MO");
  });

  it("tries a new image when the player changes after a failure", () => {
    const { rerender } = render(
      <PlayerImage playerId={978838} playerName="Michael Olise" />,
    );

    fireEvent.error(
      screen.getByRole("img", {
        name: "Michael Olise player photo",
      }),
    );

    rerender(<PlayerImage playerId={12345} playerName="Another Player" />);

    const nextImage = screen.getByRole("img", {
      name: "Another Player player photo",
    });

    expect(
      new URL(nextImage.getAttribute("src") ?? "", "http://localhost").pathname,
    ).toBe("/player-images/12345.png");
  });
});
