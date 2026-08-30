import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import {
  NextIntlClientProvider,
} from "next-intl";
import type {
  ComponentProps,
  ReactNode,
} from "react";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import englishMessages from "../../../messages/en.json";
import turkishMessages from "../../../messages/tr.json";

import {
  PlayerProfile,
} from "./player-profile";

const {
  useQueryMock,
} = vi.hoisted(
  () => ({
    useQueryMock: vi.fn(),
  }),
);

vi.mock(
  "@tanstack/react-query",
  () => ({
    useQuery: useQueryMock,
  }),
);

vi.mock(
  "@/i18n/navigation",
  async () => {
    const {
      useLocale: useActualLocale,
    } = await vi.importActual<
      typeof import("next-intl")
    >("next-intl");

    return {
      Link: ({
        href,
        ...properties
      }: ComponentProps<"a"> &
        Readonly<{
          href: string;
        }>) => {
        const locale =
          useActualLocale();

        return (
          <a
            href={
              locale === "tr"
                ? `/tr${href}`
                : href
            }
            {...properties}
          />
        );
      },
    };
  },
);

vi.mock(
  "@/lib/api/browser-client",
  () => ({
    isBrowserApiError: (
      error: unknown,
    ) =>
      typeof error === "object" &&
      error !== null &&
      "status" in error,
  }),
);

vi.mock(
  "@/components/feedback/api-error-reference",
  () => ({
    ApiErrorReference: () => null,
  }),
);

vi.mock(
  "@/components/players/player-profile-view",
  () => ({
    PlayerProfileView: () => (
      <div>Player profile view</div>
    ),
  }),
);

vi.mock(
  "@/components/players/player-spatial-profile",
  () => ({
    PlayerSpatialProfile: () => (
      <div>Player spatial profile</div>
    ),
  }),
);

type TestLocale =
  "en" | "tr";

function renderWithLocale(
  locale: TestLocale,
  children: ReactNode,
) {
  return render(
    <NextIntlClientProvider
      locale={locale}
      messages={
        locale === "tr"
          ? turkishMessages
          : englishMessages
      }
    >
      {children}
    </NextIntlClientProvider>,
  );
}

function prepareQueries(
  profileQuery:
    Readonly<Record<string, unknown>>,
) {
  useQueryMock
    .mockReturnValueOnce(
      profileQuery,
    )
    .mockReturnValueOnce({
      isPending: false,
      isError: false,
      isSuccess: false,
      data: null,
      error: null,
      refetch: vi.fn(),
    });
}

describe(
  "PlayerProfile",
  () => {
    beforeEach(() => {
      useQueryMock.mockReset();
    });

    it(
      "localizes the loading state in Turkish",
      () => {
        prepareQueries({
          isPending: true,
          isError: false,
          isSuccess: false,
          data: null,
          error: null,
          refetch: vi.fn(),
        });

        renderWithLocale(
          "tr",
          <PlayerProfile
            playerId={978838}
          />,
        );

        expect(
          screen.getByRole(
            "status",
            {
              name:
                "Oyuncu scouting profili yükleniyor…",
            },
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "localizes the not-found state and link in Turkish",
      () => {
        prepareQueries({
          isPending: false,
          isError: true,
          isSuccess: false,
          data: null,
          error: {
            status: 404,
          },
          refetch: vi.fn(),
        });

        renderWithLocale(
          "tr",
          <PlayerProfile
            playerId={978838}
          />,
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Bu oyuncu mevcut katalogda bulunmuyor",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Oyuncu aramasına dön",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/tr/players",
        );
      },
    );

    it(
      "retries an unavailable profile",
      () => {
        const refetch =
          vi.fn();

        prepareQueries({
          isPending: false,
          isError: true,
          isSuccess: false,
          data: null,
          error: {
            status: 500,
          },
          refetch,
        });

        renderWithLocale(
          "en",
          <PlayerProfile
            playerId={978838}
          />,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Retry profile",
            },
          ),
        );

        expect(
          refetch,
        ).toHaveBeenCalledOnce();
      },
    );
  },
);
