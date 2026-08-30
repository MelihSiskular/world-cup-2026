import {
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import {
  NextIntlClientProvider,
} from "next-intl";

import englishMessages from "../../../messages/en.json";
import turkishMessages from "../../../messages/tr.json";
import userEvent from "@testing-library/user-event";
import type {
  ReactNode,
} from "react";
import {
  describe,
  expect,
  it,
} from "vitest";

import {
  ShortlistProvider,
} from "@/components/providers/shortlist-provider";
import {
  ShortlistAction,
} from "@/components/shortlists/shortlist-action";
import {
  addPlayerToShortlist,
  createShortlist,
} from "@/lib/shortlists/model";
import type {
  ShortlistStorageAdapter,
} from "@/lib/shortlists/storage";
import {
  createEmptyShortlistState,
  SHORTLIST_STORAGE_KEY,
} from "@/lib/shortlists/types";
import type {
  ShortlistPlayerSnapshot,
  ShortlistState,
} from "@/lib/shortlists/types";

const NOW =
  "2026-08-25T02:00:00.000Z";

const player:
  ShortlistPlayerSnapshot = {
    playerId: 978838,
    playerName: "Michael Olise",
    nationalTeamName: "France",
    countryName: "France",
    countryAlpha3: "FRA",
    position: "M",
    age: 24,
    marketValue: 100_000_000,
    marketValueCurrency: "EUR",
    finalRole:
      "Right Half-Space Creator",
    archetype: "Wide Creator",
    spatialRole:
      "Right Half-Space",
    minutes: 540,
    roleConfidencePct: 82,
    dataReliabilityScore: 78,
    playerQualityScore: 88,
  };

type MemoryStorage =
  Readonly<{
    adapter:
      ShortlistStorageAdapter;
    readState():
      ShortlistState | null;
  }>;

function createMemoryStorage(
  initialState:
    ShortlistState | null = null,
): MemoryStorage {
  let value =
    initialState === null
      ? null
      : JSON.stringify(
          initialState,
        );

  return {
    adapter: {
      getItem(key) {
        return key ===
          SHORTLIST_STORAGE_KEY
          ? value
          : null;
      },
      setItem(key, nextValue) {
        if (
          key ===
          SHORTLIST_STORAGE_KEY
        ) {
          value = nextValue;
        }
      },
    },
    readState() {
      if (value === null) {
        return null;
      }

      return JSON.parse(
        value,
      ) as ShortlistState;
    },
  };
}

function createStateWithList(
  name = "Summer 2027 — LCB",
): ShortlistState {
  return createShortlist(
    createEmptyShortlistState(),
    {
      id: "list-1",
      name,
      now: NOW,
    },
  );
}

function renderAction({
  storage,
  createId = () => "list-1",
  locale = "en",
}: Readonly<{
  storage:
    ShortlistStorageAdapter | null;
  createId?: () => string;
  locale?: "en" | "tr";
}>) {
  function Wrapper({
    children,
  }: Readonly<{
    children: ReactNode;
  }>) {
    const messages =
      locale === "tr"
        ? turkishMessages
        : englishMessages;

    return (
      <NextIntlClientProvider
        locale={locale}
        messages={messages}
      >
        <ShortlistProvider
          storage={storage}
          now={() => NOW}
          createId={createId}
        >
          {children}
        </ShortlistProvider>
      </NextIntlClientProvider>
    );
  }

  render(
    <ShortlistAction
      player={player}
    />,
    {
      wrapper: Wrapper,
    },
  );
}

async function openAction() {
  const disclosure =
    await screen.findByRole(
      "button",
      {
        name:
          "Add to shortlist",
      },
    );

  await waitFor(() => {
    expect(
      disclosure,
    ).toBeEnabled();
  });

  await userEvent.click(
    disclosure,
  );
}

describe(
  "ShortlistAction",
  () => {
    it(
      "creates a shortlist and adds the player atomically from the user flow",
      async () => {
        const user =
          userEvent.setup();

        const storage =
          createMemoryStorage();

        renderAction({
          storage:
            storage.adapter,
        });

        const disclosure =
          await screen.findByRole(
            "button",
            {
              name:
                "Add to shortlist",
            },
          );

        await waitFor(() => {
          expect(
            disclosure,
          ).toBeEnabled();
        });

        await user.click(
          disclosure,
        );

        await user.type(
          screen.getByRole(
            "textbox",
            {
              name:
                "New shortlist",
            },
          ),
          "Summer 2027 — LCB",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Create and add",
            },
          ),
        );

        await waitFor(() => {
          expect(
            screen.getByRole(
              "checkbox",
              {
                name:
                  /Summer 2027 — LCB/i,
              },
            ),
          ).toBeChecked();
        });

        expect(
          screen.getByRole(
            "status",
          ),
        ).toHaveTextContent(
          "Summer 2027 — LCB created and Michael Olise added.",
        );

        expect(
          storage.readState()
            ?.lists[0]?.entries[0]
            ?.player.playerId,
        ).toBe(
          player.playerId,
        );
      },
    );

    it(
      "adds and removes the player from an existing shortlist",
      async () => {
        const user =
          userEvent.setup();

        const storage =
          createMemoryStorage(
            createStateWithList(),
          );

        renderAction({
          storage:
            storage.adapter,
        });

        await openAction();

        const checkbox =
          screen.getByRole(
            "checkbox",
            {
              name:
                /Summer 2027 — LCB/i,
            },
          );

        await user.click(
          checkbox,
        );

        expect(
          checkbox,
        ).toBeChecked();

        expect(
          await screen.findByRole(
            "status",
          ),
        ).toHaveTextContent(
          "Michael Olise added to Summer 2027 — LCB.",
        );

        await user.click(
          checkbox,
        );

        expect(
          checkbox,
        ).not.toBeChecked();

        expect(
          storage.readState()
            ?.lists[0]?.entries,
        ).toEqual([]);
      },
    );

    it(
      "shows how many shortlists already contain the player",
      async () => {
        let state =
          createStateWithList();

        state =
          addPlayerToShortlist(
            state,
            {
              shortlistId:
                "list-1",
              player,
              now: NOW,
            },
          );

        const storage =
          createMemoryStorage(
            state,
          );

        renderAction({
          storage:
            storage.adapter,
        });

        expect(
          await screen.findByRole(
            "button",
            {
              name:
                "Shortlisted (1)",
            },
          ),
        ).toBeEnabled();
      },
    );

    it(
      "surfaces duplicate shortlist names without duplicating state",
      async () => {
        const user =
          userEvent.setup();

        const storage =
          createMemoryStorage(
            createStateWithList(
              "Recruitment",
            ),
          );

        let idIndex = 1;

        renderAction({
          storage:
            storage.adapter,
          createId: () => {
            idIndex += 1;

            return `list-${idIndex}`;
          },
        });

        await openAction();

        await user.type(
          screen.getByRole(
            "textbox",
            {
              name:
                "New shortlist",
            },
          ),
          "  recruitment  ",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Create and add",
            },
          ),
        );

        expect(
          await screen.findByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "Shortlist names must be unique.",
        );

        expect(
          storage.readState()
            ?.lists,
        ).toHaveLength(1);
      },
    );

    it(
      "reports unavailable browser storage without changing membership",
      async () => {
        const user =
          userEvent.setup();

        renderAction({
          storage: null,
        });

        const disclosure =
          await screen.findByRole(
            "button",
            {
              name:
                "Add to shortlist",
            },
          );

        await waitFor(() => {
          expect(
            disclosure,
          ).toBeEnabled();
        });

        await user.click(
          disclosure,
        );

        await user.type(
          screen.getByRole(
            "textbox",
            {
              name:
                "New shortlist",
            },
          ),
          "Recruitment",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Create and add",
            },
          ),
        );

        expect(
          await screen.findByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "Shortlists cannot access browser storage.",
        );

        expect(
          screen.queryByRole(
            "checkbox",
          ),
        ).not.toBeInTheDocument();
      },
    );
    it(
      "localizes shortlist membership actions in Turkish",
      async () => {
        const user =
          userEvent.setup();

        const storage =
          createMemoryStorage(
            createStateWithList(),
          );

        renderAction({
          storage:
            storage.adapter,
          locale: "tr",
        });

        const disclosure =
          await screen.findByRole(
            "button",
            {
              name:
                "Kısa listeye ekle",
            },
          );

        await waitFor(() => {
          expect(
            disclosure,
          ).toBeEnabled();
        });

        await user.click(
          disclosure,
        );

        const checkbox =
          screen.getByRole(
            "checkbox",
            {
              name:
                /Summer 2027 — LCB/i,
            },
          );

        await user.click(
          checkbox,
        );

        expect(
          await screen.findByRole(
            "status",
          ),
        ).toHaveTextContent(
          "Michael Olise, Summer 2027 — LCB listesine eklendi.",
        );

        expect(
          screen.getByRole(
            "region",
            {
              name:
                "Michael Olise için kısa liste seçenekleri",
            },
          ),
        ).toBeInTheDocument();
      },
    );

  },
);
