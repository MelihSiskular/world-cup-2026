import {
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  TransferAnalysisResults,
} from "@/components/transfer-intelligence/transfer-analysis-results";
import {
  BrowserApiError,
} from "@/lib/api/browser-client";
import {
  runTransferAnalysis,
} from "@/lib/api/browser-transfer-intelligence";
import type {
  TransferAnalysisResponse,
} from "@/lib/api/types";
import {
  DEFAULT_TRANSFER_ANALYSIS_VALUES,
} from "@/lib/transfer-intelligence/analysis-form";
import {
  renderWithQueryClient,
} from "@/test/render-with-query-client";

vi.mock(
  "@/lib/api/browser-transfer-intelligence",
  () => ({
    runTransferAnalysis:
      vi.fn(),
  }),
);

const runTransferAnalysisMock =
  vi.mocked(
    runTransferAnalysis,
  );

function createAnalysisResponse():
  TransferAnalysisResponse {
  return {
    target: {
      player_id: 978838,
      player_name:
        "Michael Olise",
      national_team_name:
        "France",
      country_name:
        "France",
      position: "M",
      age: 24.6,
      appearances: 8,
      starts: 8,
      minutes: 650,
      weighted_rating:
        7.35,
      market_value:
        144_000_000,
      market_value_currency:
        "EUR",
      archetype:
        "Wide Creator",
      final_role:
        "Central Half-Space Creator",
      role_confidence_pct:
        87.2,
      player_quality_score:
        85.5,
    },

    modes: {
      immediate: {
        mode:
          "immediate",
        recommendations: [],
      },
      development: {
        mode:
          "development",
        recommendations: [],
      },
      value: {
        mode: "value",
        recommendations: [],
      },
      short_term: {
        mode:
          "short_term",
        recommendations: [],
      },
    },
  } as unknown as TransferAnalysisResponse;
}

describe(
  "TransferAnalysisResults",
  () => {
    beforeEach(() => {
      runTransferAnalysisMock
        .mockReset();
    });

    it(
      "shows an API request reference and recovers after retry",
      async () => {
        runTransferAnalysisMock
          .mockRejectedValueOnce(
            new BrowserApiError({
              status: 400,
              code:
                "invalid_analysis",
              message:
                "Analysis failed.",
              requestId:
                "analysis-request-1",
            }),
          )
          .mockResolvedValueOnce(
            createAnalysisResponse(),
          );

        const user =
          userEvent.setup();

        renderWithQueryClient(
          <TransferAnalysisResults
            playerId={978838}
            values={{
              ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
            }}
            initialMode="immediate"
          />,
        );

        expect(
          await screen.findByText(
            "The transfer analysis could not be completed",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "analysis-request-1",
          ),
        ).toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Retry analysis",
            },
          ),
        );

        expect(
          await screen.findByText(
            "Michael Olise",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "No eligible candidates",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
