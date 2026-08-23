import {
  fireEvent,
  render,
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
  fetchDeploymentIdentity,
} from "@/lib/api/browser-status";

vi.mock(
  "@/lib/api/browser-status",
  () => ({
    fetchApiHealth: vi.fn(),
    fetchApiReadiness: vi.fn(),
    fetchDeploymentIdentity: vi.fn(),
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

const deployment = {
  branch: null,
  commit_sha: null,
  dataset_bundle_sha256:
    "4fc9f780253a1234567890",
  deployment_id: null,
  environment: "development",
  provider: "local",
  service: "wc26-api",
  version: "0.2.0",
};

function mockSuccessfulStatus(): void {
  vi.mocked(
    fetchApiHealth,
  ).mockResolvedValue(health);

  vi.mocked(
    fetchApiReadiness,
  ).mockResolvedValue(readiness);

  vi.mocked(
    fetchDeploymentIdentity,
  ).mockResolvedValue(deployment);
}

describe("ApiStatusOverview", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockSuccessfulStatus();
  });

  it("prioritizes user-facing service and player-data readiness", async () => {
    render(<ApiStatusOverview />);

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
      screen.getByText("Scouting API"),
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
  });

  it("keeps deployment information behind a collapsed disclosure", async () => {
    render(<ApiStatusOverview />);

    const summary =
      await screen.findByText(
        "Technical details",
      );

    const details =
      summary.closest("details");

    if (!details) {
      throw new Error(
        "Technical details disclosure not found.",
      );
    }

    expect(details).not.toHaveAttribute(
      "open",
    );

    expect(
      screen.getByText("Deployment"),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Dataset fingerprint",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText("4fc9f780253a"),
    ).toBeInTheDocument();
  });

  it("refreshes all status sources together", async () => {
    render(<ApiStatusOverview />);

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

      expect(
        fetchDeploymentIdentity,
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

    render(<ApiStatusOverview />);

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
});
