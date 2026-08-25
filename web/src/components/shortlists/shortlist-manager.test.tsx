import {
  render,
  screen,
} from "@testing-library/react";
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
  ShortlistManager,
} from "@/components/shortlists/shortlist-manager";
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
  "2026-08-25T03:00:00.000Z";

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
      return value === null
        ? null
        : JSON.parse(
            value,
          ) as ShortlistState;
    },
  };
}

function createPopulatedState():
  ShortlistState {
  let state =
    createShortlist(
      createEmptyShortlistState(),
      {
        id: "list-1",
        name:
          "Summer 2027 — LCB",
        now: NOW,
      },
    );

  state =
    addPlayerToShortlist(
      state,
      {
        shortlistId: "list-1",
        player,
        now: NOW,
      },
    );

  return state;
}

function renderManager({
  storage,
  createId = () => "list-1",
}: Readonly<{
  storage:
    ShortlistStorageAdapter | null;
  createId?: () => string;
}>) {
  function Wrapper({
    children,
  }: Readonly<{
    children: ReactNode;
  }>) {
    return (
      <ShortlistProvider
        storage={storage}
        now={() => NOW}
        createId={createId}
      >
        {children}
      </ShortlistProvider>
    );
  }

  render(
    <ShortlistManager />,
    {
      wrapper: Wrapper,
    },
  );
}

async function waitForWorkspace() {
  expect(
    await screen.findByRole(
      "heading",
      {
        name:
          "Shortlist workspace",
      },
    ),
  ).toBeInTheDocument();
}

describe(
  "ShortlistManager",
  () => {
    it(
      "renders the empty workspace after hydration",
      async () => {
        const storage =
          createMemoryStorage();

        renderManager({
          storage:
            storage.adapter,
        });

        await waitForWorkspace();

        expect(
          screen.getByText(
            "No shortlists yet",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Explore players",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/players",
        );
      },
    );

    it(
      "creates and persists a named shortlist",
      async () => {
        const user =
          userEvent.setup();

        const storage =
          createMemoryStorage();

        renderManager({
          storage:
            storage.adapter,
        });

        await waitForWorkspace();

        await user.type(
          screen.getByRole(
            "textbox",
            {
              name:
                "Create a shortlist",
            },
          ),
          "Summer 2027 — LCB",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Create shortlist",
            },
          ),
        );

        expect(
          await screen.findByRole(
            "heading",
            {
              name:
                "Summer 2027 — LCB",
            },
          ),
        ).toBeInTheDocument();

        expect(
          storage.readState()
            ?.lists[0]?.name,
        ).toBe(
          "Summer 2027 — LCB",
        );
      },
    );

    it(
      "hydrates saved player identity and profile navigation",
      async () => {
        const storage =
          createMemoryStorage(
            createPopulatedState(),
          );

        renderManager({
          storage:
            storage.adapter,
        });

        await waitForWorkspace();

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Michael Olise",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/players/978838",
        );

        expect(
          screen.getByText(
            "Right Half-Space Creator",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "€100M",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "renames a shortlist and removes its player",
      async () => {
        const user =
          userEvent.setup();

        const storage =
          createMemoryStorage(
            createPopulatedState(),
          );

        renderManager({
          storage:
            storage.adapter,
        });

        await waitForWorkspace();

        await user.click(
          screen.getByRole(
            "button",
            {
              name: "Rename",
            },
          ),
        );

        const renameInput =
          screen.getByRole(
            "textbox",
            {
              name:
                "Rename Summer 2027 — LCB",
            },
          );

        await user.clear(
          renameInput,
        );

        await user.type(
          renameInput,
          "Summer 2027 — Defenders",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name: "Save name",
            },
          ),
        );

        expect(
          await screen.findByRole(
            "heading",
            {
              name:
                "Summer 2027 — Defenders",
            },
          ),
        ).toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Remove Michael Olise from Summer 2027 — Defenders",
            },
          ),
        );

        expect(
          screen.queryByRole(
            "link",
            {
              name:
                "Michael Olise",
            },
          ),
        ).not.toBeInTheDocument();

        expect(
          storage.readState()
            ?.lists[0]?.entries,
        ).toEqual([]);
      },
    );

    it(
      "requires confirmation before deleting a shortlist",
      async () => {
        const user =
          userEvent.setup();

        const storage =
          createMemoryStorage(
            createPopulatedState(),
          );

        renderManager({
          storage:
            storage.adapter,
        });

        await waitForWorkspace();

        await user.click(
          screen.getByRole(
            "button",
            {
              name: "Delete",
            },
          ),
        );

        expect(
          screen.getByText(
            "Delete Summer 2027 — LCB?",
          ),
        ).toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Confirm delete Summer 2027 — LCB",
            },
          ),
        );

        expect(
          screen.queryByRole(
            "heading",
            {
              name:
                "Summer 2027 — LCB",
            },
          ),
        ).not.toBeInTheDocument();

        expect(
          storage.readState()
            ?.lists,
        ).toEqual([]);
      },
    );

    it(
      "surfaces unavailable storage without creating transient UI state",
      async () => {
        const user =
          userEvent.setup();

        renderManager({
          storage: null,
        });

        await waitForWorkspace();

        expect(
          screen.getByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "Shortlists cannot access browser storage.",
        );

        await user.type(
          screen.getByRole(
            "textbox",
            {
              name:
                "Create a shortlist",
            },
          ),
          "Recruitment",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Create shortlist",
            },
          ),
        );

        expect(
          screen.queryByRole(
            "heading",
            {
              name:
                "Recruitment",
            },
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "Shortlists cannot access browser storage.",
        );
      },
    );
  },
);
