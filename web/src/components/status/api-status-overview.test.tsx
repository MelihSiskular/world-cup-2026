import {
  fireEvent,
  screen,
  waitFor,
} from "@testing-library/react";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  ApiStatusOverview,
} from "@/components/status/api-status-overview";
import {
  fetchApiHealth,
  fetchApiReadiness,
} from "@/lib/api/browser-status";
import {
  renderWithQueryClient,
} from "@/test/render-with-query-client";

vi.mock(
  "@/lib/api/browser-status",
  () => ({
    fetchApiHealth: vi.fn(),
    fetchApiReadiness: vi.fn(),
  }),
);

const health = {
  environment: "development",
  service: "wc26-api",
  started_at: "2026-08-23T12:00:00Z",
  status: "ok" as const,
  uptime_seconds: 3600,
  version: "0.2.0",
};

const readiness = {
  catalog_loaded_at:
    "2026-08-23T12:30:00Z",
  environment: "development",
  service: "wc26-api",
  started_at: "2026-08-23T12:00:00Z",
  status: "ready" as const,
  uptime_seconds: 3600,
  version: "0.2.0",
};

function mockSuccessfulStatus(): void {
  vi.mocked(
    fetchApiHealth,
  ).mockResolvedValue(health);

  vi.mocked(
    fetchApiReadiness,
  ).mockResolvedValue(readiness);
}

describe("ApiStatusOverview", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockSuccessfulStatus();
  });

  it("prioritizes user-facing service and player-data readiness", async () => {
    renderWithQueryClient(
      <ApiStatusOverview />,
    );

    expect(
      await screen.findByRole(
        "heading",
        {
          name:
            "All scouting services operational",
        },
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Analysis service",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Player data"),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /Last loaded Aug 23, 2026/,
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(/Last checked/),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(
        "Technical details",
      ),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByText(
        "Dataset fingerprint",
      ),
    ).not.toBeInTheDocument();
  });

  it("refreshes public status sources together", async () => {
    renderWithQueryClient(
      <ApiStatusOverview />,
    );

    fireEvent.click(
      await screen.findByRole(
        "button",
        {
          name: "Refresh status",
        },
      ),
    );

    await waitFor(() => {
      expect(
        fetchApiHealth,
      ).toHaveBeenCalledTimes(2);

      expect(
        fetchApiReadiness,
      ).toHaveBeenCalledTimes(2);
    });
  });

  it("surfaces catalogue attention without exposing technical copy", async () => {
    vi.mocked(
      fetchApiReadiness,
    ).mockResolvedValue({
      ...readiness,
      status: "not_ready",
    });

    renderWithQueryClient(
      <ApiStatusOverview />,
    );

    expect(
      await screen.findByRole(
        "heading",
        {
          name:
            "Player data requires attention",
        },
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Not ready"),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(
        /Next.js server layer/,
      ),
    ).not.toBeInTheDocument();
  });
  it(
    "localizes service readiness and timestamps in Turkish",
    async () => {
      renderWithQueryClient(
        <ApiStatusOverview />,
        "tr",
      );

      expect(
        await screen.findByRole(
          "heading",
          {
            name:
              "Tüm scouting servisleri çalışıyor",
          },
        ),
      ).toBeInTheDocument();

      expect(
        screen.getByText(
          "Analiz servisi",
        ),
      ).toBeInTheDocument();

      expect(
        screen.getByText(
          "Oyuncu verisi",
        ),
      ).toBeInTheDocument();

      expect(
        screen.getByText(
          /Son yükleme 23 Ağu 2026/,
        ),
      ).toBeInTheDocument();

      expect(
        screen.getByText(
          /Son kontrol/,
        ),
      ).toBeInTheDocument();

      expect(
        screen.queryByText(
          "Teknik ayrıntılar",
        ),
      ).not.toBeInTheDocument();
    },
  );
});
